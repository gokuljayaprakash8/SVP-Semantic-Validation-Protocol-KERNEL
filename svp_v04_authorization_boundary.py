"""SVP v0.4 authorization-boundary experiment.

This is a controlled synthetic experiment.  It does not contact a network,
invoke an external service, or execute a real database or downstream action.
The semantic-similarity value is recorded as decision metadata only; it is not
used as an authorization mechanism.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any


ISSUER_ID = "synthetic-issuer-v04"
AGENT_ID = "agent-alpha"
ISSUER_KEY = b"v04-controlled-experiment-key"
VERIFICATION_TIME = 1_800_000_000


def canonical_json(value: Any) -> bytes:
    """Return deterministic, compact, key-ordered JSON bytes."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def hmac_sha256_hex(key: bytes, message: str) -> str:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass
class ReplayStore:
    """In-memory nonce store used only by this synthetic process."""

    consumed_nonces: set[str]

    def __init__(self) -> None:
        self.consumed_nonces = set()

    def is_replayed(self, nonce: str) -> bool:
        return nonce in self.consumed_nonces

    def consume(self, nonce: str) -> None:
        self.consumed_nonces.add(nonce)


class CapabilityIssuer:
    """Issuer for signed, explicitly scoped synthetic capabilities."""

    def __init__(self, issuer_id: str, key: bytes) -> None:
        self.issuer_id = issuer_id
        self.key = key

    def _decision_binding(self, decision_hash: str) -> str:
        return hmac_sha256_hex(self.key, f"decision-binding:{decision_hash}")

    def _capability_signature(self, claims: dict[str, Any]) -> str:
        return hmac_sha256_hex(self.key, f"capability:{canonical_json(claims).decode()}")

    def issue(
        self,
        decision: dict[str, Any],
        *,
        allowed_action: str,
        delegation_depth: int,
        max_delegation_depth: int,
    ) -> dict[str, Any]:
        decision_hash = sha256_hex(decision)
        claims = {
            "issuer_id": self.issuer_id,
            "agent_id": decision["agent_id"],
            "allowed_action": allowed_action,
            "resource": decision["resource"],
            "issued_at": decision["issued_at"],
            "expires_at": decision["expires_at"],
            "nonce": decision["nonce"],
            "delegation_depth": delegation_depth,
            "max_delegation_depth": max_delegation_depth,
            "decision_hash": decision_hash,
        }
        capability = {
            "claims": claims,
            "decision_binding": {
                "hash_algorithm": "SHA-256",
                "mac_algorithm": "HMAC-SHA256",
                "decision_hash": decision_hash,
                "mac": self._decision_binding(decision_hash),
            },
        }
        capability["issuer_signature"] = self._capability_signature(claims)
        return capability


def verify_capability(
    capability: dict[str, Any],
    decision: dict[str, Any],
    *,
    issuer: CapabilityIssuer,
    downstream_agent: str,
    downstream_action: str,
    downstream_resource: str,
    verification_time: int,
    replay_store: ReplayStore,
    consume_nonce: bool = True,
) -> dict[str, Any]:
    """Verify binding, authority, expiry, replay, and delegation before gating."""

    claims = capability["claims"]
    decision_binding = capability["decision_binding"]

    expected_signature = issuer._capability_signature(claims)
    signature_valid = hmac.compare_digest(
        capability["issuer_signature"], expected_signature
    )

    current_decision_hash = sha256_hex(decision)
    decision_hash_matches = hmac.compare_digest(
        decision_binding["decision_hash"], current_decision_hash
    ) and hmac.compare_digest(claims["decision_hash"], current_decision_hash)
    expected_mac = issuer._decision_binding(current_decision_hash)
    binding_mac_valid = hmac.compare_digest(decision_binding["mac"], expected_mac)
    binding_valid = (
        signature_valid and decision_hash_matches and binding_mac_valid
    )

    identity_matches = (
        claims["agent_id"] == downstream_agent
        and claims["agent_id"] == decision["agent_id"]
    )
    action_matches = (
        claims["allowed_action"] == downstream_action
        and claims["allowed_action"] == decision["authorized_action"]
    )
    resource_matches = (
        claims["resource"] == downstream_resource
        and claims["resource"] == decision["resource"]
    )
    decision_authorized = decision.get("decision") == "PASS"
    authority_valid = (
        identity_matches
        and action_matches
        and resource_matches
        and decision_authorized
    )

    expiry_valid = verification_time <= claims["expires_at"]
    delegation_valid = (
        claims["delegation_depth"] >= 0
        and claims["max_delegation_depth"] >= 0
        and claims["delegation_depth"] <= claims["max_delegation_depth"]
    )

    replayed = replay_store.is_replayed(claims["nonce"])
    replay_valid = not replayed
    if consume_nonce and not replayed:
        replay_store.consume(claims["nonce"])

    final_execution_decision = (
        "PASS"
        if (
            binding_valid
            and authority_valid
            and expiry_valid
            and delegation_valid
            and replay_valid
        )
        else "BLOCK"
    )

    return {
        "binding_valid": binding_valid,
        "authority_valid": authority_valid,
        "delegation_valid": delegation_valid,
        "expiry_valid": expiry_valid,
        "replay_valid": replay_valid,
        "final_execution_decision": final_execution_decision,
        "diagnostics": {
            "signature_valid": signature_valid,
            "decision_hash_matches": decision_hash_matches,
            "binding_mac_valid": binding_mac_valid,
            "identity_matches": identity_matches,
            "action_matches": action_matches,
            "resource_matches": resource_matches,
            "decision_authorized": decision_authorized,
            "replayed": replayed,
            "semantic_similarity_observed": decision["semantic_similarity"],
            "semantic_similarity_used_for_authorization": False,
        },
    }


def make_decision(
    *,
    action: str = "read_record",
    resource: str = "synthetic://dataset/record-001",
    agent_id: str = AGENT_ID,
    expires_at: int = VERIFICATION_TIME + 3600,
    nonce: str = "nonce-baseline",
    semantic_similarity: float = 0.98,
) -> dict[str, Any]:
    return {
        "decision_id": "decision-v04-001",
        "agent_id": agent_id,
        "authorized_action": action,
        "resource": resource,
        "decision": "PASS",
        "semantic_similarity": semantic_similarity,
        "issued_at": VERIFICATION_TIME - 60,
        "expires_at": expires_at,
        "nonce": nonce,
    }


def run_cases() -> list[dict[str, Any]]:
    issuer = CapabilityIssuer(ISSUER_ID, ISSUER_KEY)
    base_decision = make_decision()

    def capability_for(
        decision: dict[str, Any] = base_decision,
        *,
        allowed_action: str | None = None,
        delegation_depth: int = 0,
        max_delegation_depth: int = 1,
    ) -> dict[str, Any]:
        return issuer.issue(
            decision,
            allowed_action=allowed_action or decision["authorized_action"],
            delegation_depth=delegation_depth,
            max_delegation_depth=max_delegation_depth,
        )

    cases: list[dict[str, Any]] = []

    def add_case(
        name: str,
        expected: str,
        capability: dict[str, Any],
        decision: dict[str, Any],
        *,
        downstream_agent: str = AGENT_ID,
        downstream_action: str = "read_record",
        downstream_resource: str = "synthetic://dataset/record-001",
        replay_store: ReplayStore | None = None,
        notes: str,
    ) -> None:
        result = verify_capability(
            capability,
            decision,
            issuer=issuer,
            downstream_agent=downstream_agent,
            downstream_action=downstream_action,
            downstream_resource=downstream_resource,
            verification_time=VERIFICATION_TIME,
            replay_store=replay_store or ReplayStore(),
        )
        observed = result["final_execution_decision"]
        cases.append(
            {
                "case": name,
                "expected_result": expected,
                "observed_result": observed,
                "binding_valid": result["binding_valid"],
                "authority_valid": result["authority_valid"],
                "delegation_valid": result["delegation_valid"],
                "final_execution_decision": observed,
                "expiry_valid": result["expiry_valid"],
                "replay_valid": result["replay_valid"],
                "correct": observed == expected,
                "notes": notes,
                "diagnostics": result["diagnostics"],
            }
        )

    add_case(
        "authorized baseline",
        "PASS",
        capability_for(),
        base_decision,
        notes="Exact authorized action, agent, resource, and valid authority.",
    )
    add_case(
        "semantic extension",
        "BLOCK",
        capability_for(),
        base_decision,
        downstream_action="read_record_with_summary",
        notes="Similar-looking extension is not authorized by exact action binding.",
    )
    add_case(
        "privilege escalation",
        "BLOCK",
        capability_for(),
        base_decision,
        downstream_action="delete_record",
        notes="Downstream action requests a materially higher privilege.",
    )
    add_case(
        "external export",
        "BLOCK",
        capability_for(),
        base_decision,
        downstream_action="export_record",
        downstream_resource="external://unapproved-destination",
        notes="Export to an external destination is outside the bound resource.",
    )

    mutated_decision = copy.deepcopy(base_decision)
    mutated_decision["semantic_similarity"] = 0.99
    add_case(
        "decision mutation after binding",
        "BLOCK",
        capability_for(),
        mutated_decision,
        notes="Only decision metadata changed after signing; the decision hash no longer matches.",
    )

    add_case(
        "nested delegation exceeding authority",
        "BLOCK",
        capability_for(delegation_depth=2, max_delegation_depth=1),
        base_decision,
        notes="Delegation depth 2 exceeds the explicit maximum depth 1.",
    )

    return cases


def print_report(cases: list[dict[str, Any]]) -> None:
    correct = sum(case["correct"] for case in cases)
    total = len(cases)
    accuracy = (correct / total) if total else 0.0
    status = "PASS" if correct == total else "FAIL"

    print("SVP v0.4 AUTHORIZATION-BOUNDARY EXPERIMENT")
    print("STATUS: CONTROLLED SYNTHETIC EXPERIMENT")
    print("SCOPE: No network, external system, or real action execution.")
    print(
        "SECURITY CLAIM: This experiment does not prove real-world "
        "AI-agent security."
    )
    print("CRYPTOGRAPHY: SHA-256 decision hash + HMAC-SHA256 binding")
    print("AUTHORIZATION: Exact identity/action/resource checks; semantic similarity is not authorization")
    print()

    print("MACHINE_READABLE_RESULTS_BEGIN")
    for case in cases:
        print(json.dumps(case, sort_keys=True, separators=(",", ":")))
    print(
        json.dumps(
            {
                "total_cases": total,
                "correct_cases": correct,
                "accuracy": accuracy,
                "status": status,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    print("MACHINE_READABLE_RESULTS_END")
    print()

    print("HUMAN_READABLE_RESULT_TABLE")
    headers = [
        "case",
        "expected",
        "observed",
        "binding",
        "authority",
        "delegation",
        "final",
        "correct",
    ]
    print(" | ".join(headers))
    print("-" * 118)
    for case in cases:
        print(
            " | ".join(
                [
                    case["case"],
                    case["expected_result"],
                    case["observed_result"],
                    str(case["binding_valid"]),
                    str(case["authority_valid"]),
                    str(case["delegation_valid"]),
                    case["final_execution_decision"],
                    str(case["correct"]),
                ]
            )
        )
    print()
    print(f"TOTAL CASES: {total}")
    print(f"CORRECT CASES: {correct}")
    print(f"ACCURACY: {accuracy:.2%}")
    print(f"EXPERIMENT STATUS: {status}")


def main() -> None:
    cases = run_cases()
    print_report(cases)


if __name__ == "__main__":
    main()