"""Environment-configured bearer-token authentication for the active API."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any

GOVERNANCE_SCOPE = "governance:evaluate"
AUDIT_SCOPE = "audit:read"
EXECUTION_SCOPE = "execution:execute"
AUTH_SCOPES = frozenset(
    {
        GOVERNANCE_SCOPE,
        AUDIT_SCOPE,
        EXECUTION_SCOPE,
    }
)


class AuthConfigurationError(ValueError):
    """Raised when the API authentication configuration is unsafe or invalid."""


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    principal_id: str
    scopes: frozenset[str]


@dataclass(frozen=True)
class _ConfiguredToken:
    principal_id: str
    token_digest: str
    scopes: frozenset[str]


class BearerTokenAuthenticator:
    """Compare bearer tokens against a restart-loaded, scope-bearing registry."""

    def __init__(self, configured_tokens: tuple[_ConfiguredToken, ...]):
        if not configured_tokens:
            raise AuthConfigurationError("At least one API token is required")
        self._configured_tokens = configured_tokens

    @classmethod
    def from_json(cls, raw_config: str | None) -> "BearerTokenAuthenticator":
        if not raw_config or not raw_config.strip():
            raise AuthConfigurationError(
                "SVP_AUTH_TOKENS is not configured"
            )

        try:
            decoded = json.loads(raw_config)
        except json.JSONDecodeError as exc:
            raise AuthConfigurationError(
                "SVP_AUTH_TOKENS must be valid JSON"
            ) from exc

        records = _normalize_records(decoded)
        configured_tokens: list[_ConfiguredToken] = []
        seen_ids: set[str] = set()

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise AuthConfigurationError(
                    f"Authentication record {index} must be an object"
                )

            principal_id = record.get("id")
            token = record.get("token")
            scopes = record.get("scopes")
            if (
                not isinstance(principal_id, str)
                or not principal_id.strip()
                or principal_id in seen_ids
            ):
                raise AuthConfigurationError(
                    f"Authentication record {index} has an invalid or duplicate id"
                )
            if not isinstance(token, str) or len(token) < 16:
                raise AuthConfigurationError(
                    f"Authentication record {index} must contain a token of at least 16 characters"
                )
            if not isinstance(scopes, list) or not scopes:
                raise AuthConfigurationError(
                    f"Authentication record {index} must contain a non-empty scopes list"
                )
            if not all(isinstance(scope, str) for scope in scopes):
                raise AuthConfigurationError(
                    f"Authentication record {index} scopes must be strings"
                )

            normalized_scopes = frozenset(scopes)
            unknown_scopes = normalized_scopes - AUTH_SCOPES
            if unknown_scopes:
                raise AuthConfigurationError(
                    f"Authentication record {index} contains unsupported scopes"
                )

            seen_ids.add(principal_id)
            configured_tokens.append(
                _ConfiguredToken(
                    principal_id=principal_id,
                    token_digest=_digest(token),
                    scopes=normalized_scopes,
                )
            )

        return cls(tuple(configured_tokens))

    def authenticate(self, token: str) -> AuthenticatedPrincipal | None:
        if not isinstance(token, str) or not token:
            return None

        presented_digest = _digest(token)
        for configured in self._configured_tokens:
            if secrets.compare_digest(
                presented_digest,
                configured.token_digest,
            ):
                return AuthenticatedPrincipal(
                    principal_id=configured.principal_id,
                    scopes=configured.scopes,
                )
        return None


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalize_records(decoded: Any) -> list[dict[str, Any]]:
    if isinstance(decoded, list):
        return decoded

    # A mapping is accepted for compact operator configuration:
    # {"operator": {"token": "...", "scopes": ["audit:read"]}}
    if isinstance(decoded, dict):
        records = []
        for principal_id, record in decoded.items():
            if not isinstance(record, dict):
                raise AuthConfigurationError(
                    "Mapping authentication records must contain objects"
                )
            normalized = dict(record)
            normalized["id"] = principal_id
            records.append(normalized)
        return records

    raise AuthConfigurationError(
        "SVP_AUTH_TOKENS must be a JSON list or object"
    )