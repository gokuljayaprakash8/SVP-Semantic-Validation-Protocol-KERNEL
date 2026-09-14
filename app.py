import logging
import os
import re
import threading
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from svp_kernel.audit.audit_logger import AuditLogger
from svp_kernel.governance import (
    AuditTrail,
    GovernanceEngine,
    GovernanceRequest,
    GovernanceRuntime,
)
from svp_kernel.auth import (
    AUDIT_SCOPE,
    EXECUTION_SCOPE,
    GOVERNANCE_SCOPE,
    AuthConfigurationError,
    AuthenticatedPrincipal,
    BearerTokenAuthenticator,
)
from validator import load_policy_file
from svp_v06_runtime_gate import create_bound_decision, verify_bound_decision, consume_authorization


logger = logging.getLogger("svp.app")

app = FastAPI()

# ---------------------------------------------------------------------------
# API authentication and CORS configuration.
# ---------------------------------------------------------------------------
AUTH_TOKENS_ENV = "SVP_AUTH_TOKENS"
CORS_ORIGINS_ENV = "SVP_CORS_ORIGINS"

try:
    _authenticator = BearerTokenAuthenticator.from_json(
        os.getenv(AUTH_TOKENS_ENV)
    )
    _auth_configuration_error: Exception | None = None
except AuthConfigurationError as exc:
    _authenticator = None
    _auth_configuration_error = exc
    logger.error(
        "API authentication is unavailable: %s",
        exc,
    )


def _load_cors_origins(raw_config: str | None) -> list[str]:
    if not raw_config or not raw_config.strip():
        return []

    origins = [origin.strip() for origin in raw_config.split(",") if origin.strip()]
    if not origins or "*" in origins:
        raise ValueError(
            f"{CORS_ORIGINS_ENV} must contain explicit origins and cannot include '*'"
        )
    if any(origin == "*" or "://" not in origin for origin in origins):
        raise ValueError(
            f"{CORS_ORIGINS_ENV} must contain explicit absolute origins"
        )
    return origins


try:
    CORS_ORIGINS = _load_cors_origins(os.getenv(CORS_ORIGINS_ENV))
    _cors_configuration_error: Exception | None = None
except ValueError as exc:
    CORS_ORIGINS = []
    _cors_configuration_error = exc
    logger.error("CORS is disabled due to invalid configuration: %s", exc)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bearer_scheme = HTTPBearer(auto_error=False)


def _authentication_error(
    status_code: int,
    error: str,
    *,
    required_scope: str | None = None,
) -> HTTPException:
    detail: dict[str, str] = {
        "status": "unauthorized" if status_code == 401 else "forbidden",
        "error": error,
    }
    if required_scope is not None:
        detail["required_scope"] = required_scope
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers,
    )


def authenticate_request(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthenticatedPrincipal:
    """Authenticate a bearer token without granting any permissions."""
    if _auth_configuration_error is not None or _authenticator is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unavailable",
                "error": "AUTH_CONFIGURATION_UNAVAILABLE",
            },
        )
    if credentials is None:
        raise _authentication_error(401, "AUTHENTICATION_REQUIRED")

    principal = _authenticator.authenticate(credentials.credentials)
    if principal is None:
        raise _authentication_error(401, "INVALID_CREDENTIALS")
    return principal


def require_scope(scope: str):
    """Build an authorization dependency for one explicit API scope."""

    def dependency(
        principal: AuthenticatedPrincipal = Depends(authenticate_request),
    ) -> AuthenticatedPrincipal:
        if scope not in principal.scopes:
            raise _authentication_error(403, "INSUFFICIENT_SCOPE", required_scope=scope)
        return principal

    return dependency


require_governance = require_scope(GOVERNANCE_SCOPE)
require_audit = require_scope(AUDIT_SCOPE)
require_execution = require_scope(EXECUTION_SCOPE)

# ---------------------------------------------------------------------------
# Runtime configuration and policy initialization.
# ---------------------------------------------------------------------------
MODEL_NAME = os.getenv("SVP_MODEL_NAME", "BAAI/bge-small-en-v1.5")
MODEL_REPOSITORY = os.getenv(
    "SVP_MODEL_REPOSITORY",
    "qdrant/bge-small-en-v1.5-onnx-q",
)
MODEL_REVISION = os.getenv(
    "SVP_MODEL_REVISION",
    "52398278842ec682c6f32300af41344b1c0b0bb2",
)
MODEL_CACHE_DIR = Path(
    os.getenv("SVP_MODEL_CACHE_DIR", "/tmp/svp-fastembed")
).expanduser()
MODEL_ARTIFACTS = (
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "preprocessor_config.json",
    "model_optimized.onnx",
)

_SUPPORTED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_SUPPORTED_MODEL_REPOSITORY = "qdrant/bge-small-en-v1.5-onnx-q"


class RuntimeInitializationError(RuntimeError):
    """Raised when a dependency required for governance is unavailable."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


try:
    config = load_policy_file("policies/default.yaml")
    POLICIES = config["policies"]
    if not isinstance(POLICIES, list) or not POLICIES:
        raise ValueError("Policy configuration must contain a non-empty policies list")
    _policy_initialization_error: Exception | None = None
except Exception as exc:
    config = {}
    POLICIES = []
    _policy_initialization_error = exc
    logger.exception("Policy initialization failed; governance is unavailable")

audit_logger = AuditLogger()

# ---------------------------------------------------------------------------
# Embedding model — initialized on the first readiness or evaluator request.
# The exact Hugging Face revision is downloaded into an explicit cache directory
# and passed to FastEmbed through its verified specific_model_path API.
# ---------------------------------------------------------------------------
_model = None
_policy_vectors = None
_pattern_meta = None
_model_initialization_error: Exception | None = None
_init_lock = threading.Lock()


def _build_embedding_model():
    """Download the pinned ONNX snapshot and initialize the active model."""
    if MODEL_NAME != _SUPPORTED_MODEL_NAME:
        raise RuntimeInitializationError(
            "MODEL_CONFIGURATION_INVALID",
            f"Unsupported model name: {MODEL_NAME}",
        )
    if MODEL_REPOSITORY != _SUPPORTED_MODEL_REPOSITORY:
        raise RuntimeInitializationError(
            "MODEL_CONFIGURATION_INVALID",
            f"Unsupported model repository: {MODEL_REPOSITORY}",
        )
    if not re.fullmatch(r"[0-9a-f]{40}", MODEL_REVISION):
        raise RuntimeInitializationError(
            "MODEL_CONFIGURATION_INVALID",
            "SVP_MODEL_REVISION must be a 40-character commit hash",
        )

    from fastembed import TextEmbedding  # noqa: PLC0415
    from huggingface_hub import snapshot_download  # noqa: PLC0415

    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    model_path = snapshot_download(
        repo_id=MODEL_REPOSITORY,
        revision=MODEL_REVISION,
        cache_dir=str(MODEL_CACHE_DIR),
        allow_patterns=list(MODEL_ARTIFACTS),
    )
    return TextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=str(MODEL_CACHE_DIR),
        specific_model_path=model_path,
    )


def _ensure_model_loaded() -> None:
    """Initialize the embedding model and policy vectors on first use."""
    global _model, _policy_vectors, _pattern_meta, _model_initialization_error

    if _policy_initialization_error is not None:
        raise RuntimeInitializationError(
            "POLICY_INITIALIZATION_FAILED",
            "Policy configuration is unavailable",
        ) from _policy_initialization_error

    # Fast path — already initialised.
    if _model is not None:
        return

    if _model_initialization_error is not None:
        raise RuntimeInitializationError(
            "MODEL_INITIALIZATION_FAILED",
            "Embedding model initialization previously failed",
        ) from _model_initialization_error

    with _init_lock:
        # Re-check inside the lock to avoid double-init.
        if _model is not None:
            return
        if _model_initialization_error is not None:
            raise RuntimeInitializationError(
                "MODEL_INITIALIZATION_FAILED",
                "Embedding model initialization previously failed",
            ) from _model_initialization_error

        try:
            patterns: list[str] = []
            meta: list[dict] = []

            for policy in POLICIES:
                for pattern in policy["patterns"]:
                    patterns.append(pattern)
                    meta.append(
                        {
                            "id": policy["id"],
                            "description": policy["description"],
                            "threshold": policy["threshold"],
                            "severity": policy["severity"],
                            "action": policy["action"],
                            "pattern": pattern,
                        }
                    )

            model = _build_embedding_model()
            policy_vectors = np.array(list(model.embed(patterns)))

            if not len(patterns) or policy_vectors.size == 0:
                raise RuntimeInitializationError(
                    "POLICY_INITIALIZATION_FAILED",
                    "Policy embeddings could not be initialized",
                )

            # Commit atomically — readers check `_model is not None`.
            _pattern_meta = meta
            _policy_vectors = policy_vectors
            _model = model
        except RuntimeInitializationError as exc:
            _model_initialization_error = exc
            logger.exception("%s: %s", exc.code, exc)
            raise
        except Exception as exc:
            _model_initialization_error = exc
            logger.exception(
                "Embedding model initialization failed for revision %s",
                MODEL_REVISION,
            )
            raise RuntimeInitializationError(
                "MODEL_INITIALIZATION_FAILED",
                "Embedding model initialization failed",
            ) from exc


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------

def svp_kernel(action_text: str) -> dict:
    _ensure_model_loaded()

    from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415

    action_lower = action_text.lower()
    action_vector = np.array(list(_model.embed([action_text])))
    similarities = cosine_similarity(action_vector, _policy_vectors)[0]

    severity_bonus = {"CRITICAL": 0.05, "HIGH": 0.03, "MEDIUM": 0.01, "LOW": 0.00}
    policy_scores: dict = {}

    for i, similarity in enumerate(similarities):
        meta = _pattern_meta[i]
        pid = meta["id"]

        exact_bonus = 0.10 if meta["pattern"].lower() in action_lower else 0.0
        score = float(similarity) + exact_bonus + severity_bonus.get(meta["severity"], 0)

        if pid not in policy_scores or score > policy_scores[pid]["score"]:
            policy_scores[pid] = {"score": score, "similarity": float(similarity), "policy": meta}

    best = max(policy_scores.values(), key=lambda x: x["score"])
    policy = best["policy"]
    margin = 0.05

    sorted_scores = sorted(policy_scores.values(), key=lambda x: x["score"], reverse=True)
    second_score = sorted_scores[1]["score"] if len(sorted_scores) > 1 else 0

    if best["similarity"] >= policy["threshold"] and (best["score"] - second_score) >= margin:
        return {
            "action": action_text,
            "decision": policy["action"],
            "rule_id": policy["id"],
            "matched_policy": policy["description"],
            "severity": policy["severity"],
            "score": round(best["similarity"], 4),
            "threshold": policy["threshold"],
        }

    return {
        "action": action_text,
        "decision": "PASS",
        "rule_id": "SAFE001",
        "matched_policy": "No policy exceeded threshold",
        "severity": "LOW",
        "score": round(best["similarity"], 4),
        "threshold": policy["threshold"],
    }


governance_engine = GovernanceEngine(
    evaluator=lambda request: svp_kernel(request.action),
    policy_version="1.0.0",
)
governance_audit = AuditTrail(legacy_logger=audit_logger)
_v06_execution_capability = object()
governance_runtime = GovernanceRuntime(
    governance_engine,
    governance_audit,
    execution_capability=_v06_execution_capability,
)


def _structured_initialization_error(exc: RuntimeInitializationError) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "status": "unavailable",
            "error": exc.code,
        },
    )


def _readiness_failure(exc: RuntimeInitializationError) -> HTTPException:
    policy_status = (
        "error"
        if _policy_initialization_error is not None
        else "ok"
    )
    model_status = (
        "error"
        if exc.code.startswith("MODEL_")
        else "not_checked"
    )
    return HTTPException(
        status_code=503,
        detail={
            "status": "not_ready",
            "checks": {
                "policy": policy_status,
                "model": model_status,
                "governance": "unavailable",
            },
            "error": exc.code,
        },
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class WorkflowRequest(BaseModel):
    steps: list[str]


class GovernanceRequestPayload(BaseModel):
    principal: str = Field(..., min_length=1)
    agent: str = Field(..., min_length=1)
    delegation: dict[str, Any] = Field(default_factory=dict)
    intent: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    resource: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    state: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = Field(default=None, min_length=1)
    trace_id: str | None = Field(default=None, min_length=1)


@app.get("/")
def root(
    _principal: AuthenticatedPrincipal = Depends(require_audit),
):
    return {"status": "ok", "service": "SVP Kernel"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Report whether policy loading and model inference are available."""
    try:
        _ensure_model_loaded()
        svp_kernel("readiness probe")
    except RuntimeInitializationError as exc:
        raise _readiness_failure(exc) from exc
    except Exception as exc:
        logger.exception("Readiness inference failed")
        initialization_error = RuntimeInitializationError(
            "GOVERNANCE_INITIALIZATION_FAILED",
            "Governance inference is unavailable",
        )
        raise _readiness_failure(initialization_error) from exc

    return {
        "status": "ready",
        "checks": {
            "policy": "ok",
            "model": "ok",
            "governance": "ok",
        },
    }


@app.post("/v1/govern")
def govern(
    req: GovernanceRequestPayload,
    _principal: AuthenticatedPrincipal = Depends(require_governance),
):
    """Evaluate a proposal and return an audit trace without executing it."""

    proposal = GovernanceRequest.from_mapping(
        req.dict(exclude_none=True)
    )
    decision, trace = governance_runtime.govern(proposal)
    return {
        "decision": decision.to_dict(),
        "audit": trace.to_dict(),
    }


@app.post("/v1/audit")
def audit(
    req: WorkflowRequest,
    _principal: AuthenticatedPrincipal = Depends(require_audit),
):
    results = []
    for step in req.steps:
        try:
            decision = svp_kernel(step)
        except RuntimeInitializationError as exc:
            raise _structured_initialization_error(exc) from exc
        except Exception as exc:
            logger.exception("Request-time governance evaluation failed")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unavailable",
                    "error": "GOVERNANCE_UNAVAILABLE",
                },
            ) from exc
        audit_event = audit_logger.create_event(decision, "1.0.0")
        audit_logger.save_event(audit_event)
        results.append(decision)

    blocked = [r for r in results if r["decision"] == "BLOCK"]
    return {
        "overall": "BLOCKED" if blocked else "CLEAR",
        "blocked_count": len(blocked),
        "steps": results,
    }


@app.post("/v1/audit/v06")
def audit_v06(
    req: WorkflowRequest,
    _principal: AuthenticatedPrincipal = Depends(require_audit),
):
    results = []
    for step in req.steps:
        try:
            decision = svp_kernel(step)
        except RuntimeInitializationError as exc:
            raise _structured_initialization_error(exc) from exc
        except Exception as exc:
            logger.exception("Request-time v0.6 governance evaluation failed")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unavailable",
                    "error": "GOVERNANCE_UNAVAILABLE",
                },
            ) from exc
        record = create_bound_decision(step, decision)
        valid, reason = verify_bound_decision(step, record)
        results.append({
            "action": step,
            "decision": decision,
            "binding_valid": valid,
            "binding_outcome": reason,
            "record": record,
        })
    return {"steps": results}


V06_EXECUTED_ACTIONS = []


class V06ExecutionAdapter:
    """Active v0.6 sink; direct execution is rejected."""

    def __init__(self, capability):
        self._capability = capability

    def execute(self, request: GovernanceRequest):
        raise PermissionError("V06 execution requires governance capability")

    def _execute_with_capability(self, request, capability):
        if capability is not self._capability:
            raise PermissionError("V06 execution capability invalid")
        V06_EXECUTED_ACTIONS.append(request.action)
        return {"action": request.action}


v06_execution_adapter = V06ExecutionAdapter(_v06_execution_capability)


def _v06_request(action: str, payload: dict | None = None) -> GovernanceRequest:
    payload = payload or {}
    return GovernanceRequest.from_mapping(
        {
            "principal": payload.get("principal", "legacy-v06-caller"),
            "agent": payload.get("agent", "legacy-v06-agent"),
            "delegation": payload.get("delegation", {}),
            "intent": payload.get("intent", action),
            "action": action,
            "resource": payload.get("resource", "legacy://v06-test"),
            "context": payload.get("context", {}),
            "state": payload.get("state", {}),
        }
    )


def v06_execution_gate(
    action: str,
    record: dict,
    payload: dict | None = None,
):
    if record is None:
        return False, "NO DECISION"

    valid, reason = verify_bound_decision(action, record)

    if not valid:
        return False, reason

    consumed, consume_reason = consume_authorization(record)
    if not consumed:
        return False, consume_reason

    try:
        request = _v06_request(action, payload)
    except (TypeError, ValueError) as exc:
        return False, f"MALFORMED REQUEST: {type(exc).__name__}"

    result = governance_runtime.execute(request, v06_execution_adapter)
    if not result.executed:
        return False, result.decision.reason

    return True, "EXECUTION AUTHORIZED"


@app.post("/v1/execute/v06-test")
def execute_v06_test(
    payload: dict,
    _principal: AuthenticatedPrincipal = Depends(require_execution),
):
    action = payload.get("action")
    record = payload.get("record")

    allowed, reason = v06_execution_gate(action, record, payload)

    if not allowed:
        return {
            "executed": False,
            "reason": reason,
        }

    return {
        "executed": True,
        "reason": reason,
        "action": action,
    }


@app.get("/v1/audit/verify")
def verify_audit(
    _principal: AuthenticatedPrincipal = Depends(require_audit),
):
    return {"valid": audit_logger.verify_chain()}
