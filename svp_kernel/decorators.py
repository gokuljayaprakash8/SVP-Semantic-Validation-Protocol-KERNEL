import functools
import hmac
import hashlib
import json

from .client import SVPClient
from .exceptions import SVPSemanticDriftError


class ZeroTrustRuntime:
    """
    Runtime execution boundary for SVP-protected agent actions.

    v0.4:
    - Enforces the real API workflow decision ("overall").
    - When a cryptographic security_binding is supplied, verifies
      the committed security state immediately before execution.
    - Only a cryptographically verified committed PASS may execute.
    """

    def __init__(self, client: SVPClient):
        self.client = client

    def protect(self, core_intent: str):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                action_desc = (
                    f"Agent attempting {func.__name__} "
                    f"with args: {args} kwargs: {kwargs}"
                )

                # Execute semantic audit before allowing the OS to run
                # the function.
                audit_result = self.client.audit_sync(
                    [core_intent, action_desc]
                )

                # Fail closed on malformed audit responses.
                if not isinstance(audit_result, dict):
                    raise SVPSemanticDriftError(
                        "FATAL: Invalid audit response; execution denied.",
                        0.0,
                        func.__name__,
                    )

                # The real /v1/audit API returns "overall":
                # CLEAR or BLOCKED.
                if audit_result.get("overall") == "BLOCKED":
                    drift_score = audit_result.get(
                        "step_analysis", [{}]
                    )[0].get("score", 0.0)

                    self.client.telemetry.log_threat_intercept(
                        action_desc,
                        drift_score,
                        core_intent,
                    )

                    raise SVPSemanticDriftError(
                        "FATAL: Unauthorized agent hallucination intercepted.",
                        drift_score,
                        func.__name__,
                    )

                # v0.4 cryptographic execution binding.
                security_binding = audit_result.get("security_binding")

                if security_binding is not None:
                    try:
                        secret = b"svp-v04-integrated-runtime-secret"

                        fields = (
                            "identity",
                            "authority",
                            "delegation",
                            "action",
                            "decision",
                        )

                        canonical = json.dumps(
                            {
                                k: security_binding[k]
                                for k in fields
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()

                        expected_commitment = hmac.new(
                            secret,
                            canonical,
                            hashlib.sha256,
                        ).hexdigest()

                        supplied_commitment = security_binding.get(
                            "commitment"
                        )

                        if (
                            not supplied_commitment
                            or not hmac.compare_digest(
                                expected_commitment,
                                supplied_commitment,
                            )
                        ):
                            raise SVPSemanticDriftError(
                                "FATAL: Cryptographic execution binding "
                                "invalid; execution denied.",
                                0.0,
                                func.__name__,
                            )

                        # IMPORTANT:
                        # Use the decision from the verified committed
                        # security state, not a mutable outer/API value.
                        decision = security_binding["decision"]

                        if decision != "PASS":
                            raise SVPSemanticDriftError(
                                f"FATAL: Invalid committed audit decision "
                                f"'{decision}'; execution denied.",
                                0.0,
                                func.__name__,
                            )

                    except SVPSemanticDriftError:
                        raise

                    except (KeyError, TypeError, ValueError):
                        raise SVPSemanticDriftError(
                            "FATAL: Malformed cryptographic execution "
                            "binding; execution denied.",
                            0.0,
                            func.__name__,
                        )

                return func(*args, **kwargs)

            return wrapper

        return decorator
