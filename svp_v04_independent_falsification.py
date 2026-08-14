"""Independent falsification experiment for the SVP v0.4 boundary.

This is a controlled synthetic independent falsification.  It does not make
network requests, use credentials, contact external systems, or execute real
actions.

The existing v0.4 boundary is loaded only to obtain the observed gate result.
The expected result is produced by IndependentSecurityOracle, which uses a
separate representation of security properties and never calls the gate's
authority-checking function.
"""

from __future__ import annotations

import copy
import json
import runpy
from dataclasses import dataclass
from typing import Any


GATE_PATH = "svp_v04_authorization_boundary.py"
VERIFICATION_TIME = 1_800_000_000
AGENT_ID = "agent-independent-falsification"
AUTHORIZED_ACTION = "read_record"
AUTHORIZED_RESOURCE = "synthetic://dataset/record-001"
AUTHORIZED_REFINEMENT = "read_record_with_summary"


@dataclass
class CaseSpec:
    name: str
    category: str
    original_intent: str
    downstream_action: str
    downstream_resource: str = AUTHORIZED_RESOURCE
    downstream_agent: str = AGENT_ID
    semantic_similarity: float | None = None
    expected_reason: str = ""
    adversarial_false_allow_probe: bool = False
    current_decision: dict[str, Any] | None = None
    issue_decision: dict[str, Any] | None = None
    delegation_depth: int = 0
    max_delegation_depth: int = 1
    replay_attempt: bool = False
    capability_mutation: str | None = None


class IndependentSecurityOracle:
    """Expected-classification model independent of the v0.4 gate."""

    # These are explicit policy facts for this experiment, not similarity
    # thresholds.  The refinement is legitimate because it is a local,
    # non-destructive presentation of the already-authorized record.
    allowed_actions = {AUTHORIZED_ACTION}
    explicitly_authorized_refinements = {AUTHORIZED_REFINEMENT}
    non_security_metadata = {"presentation_note"}

    def classify(
        self,
        case: CaseSpec,
        *,
        original_decision: dict[str, Any],
    ) -> tuple[str, dict[str, bool]]:
        current = case.current_decision or original_decision

        identity_valid = case.downstream_agent == original_decision["agent_id"]
        action_valid = (
            case.downstream_action in self.allowed_actions
            or case.downstream_action in self.explicitly_authorized_refinements
        )
        resource_valid = case.downstream_resource == original_decision["resource"]
        decision_state_valid = current.get("decision") == "PASS"
        scope_valid = current.get("approval_scope") == original_decision["approval_scope"]
        expiry_valid = current.get("expires_at", 0) >= VERIFICATION_TIME
        delegation_valid = (
            case.delegation_depth >= 0
            and case.max_delegation_depth >= 0
            and case.delegation_depth <= case.max_delegation_depth
        )
        replay_valid = not case.replay_attempt
        capability_integrity_valid = case.capability_mutation is None

        # A decision mutation is relevant when it changes an authorization
        # property.  Presentation-only metadata is intentionally ignored by
        # this independent model so the existing gate can be tested for a
        # potential false block on over-binding.
        relevant_fields = {
            "decision_id",
            "agent_id",
            "authorized_action",
            "resource",
            "decision",
            "approval_scope",
            "issued_at",
            "expires_at",
            "nonce",
        }
        decision_properties_unchanged = all(
            current.get(field) == original_decision.get(field)
            for field in relevant_fields
        )

        expected = (
            "PASS"
            if (
                identity_valid
                and action_valid
                and resource_valid
                and decision_state_valid
                and scope_valid
                and expiry_valid
                and delegation_valid
                and replay_valid
                and decision_properties_unchanged
                and capability_integrity_valid
            )
            else "BLOCK"
        )
        return expected, {
            "identity_valid": identity_valid,
            "action_valid": action_valid,
            "resource_valid": resource_valid,
            "decision_state_valid": decision_state_valid,
            "scope_valid": scope_valid,
            "expiry_valid": expiry_valid,
            "delegation_valid": delegation_valid,
            "replay_valid": replay_valid,
            "decision_properties_unchanged": decision_properties_unchanged,
            "capability_integrity_valid": capability_integrity_valid,
            "semantic_similarity_used_for_authorization": False,
        }


def make_base_decision() -> dict[str, Any]:
    return {
        "decision_id": "independent-decision-001",
        "agent_id": AGENT_ID,
        "authorized_action": AUTHORIZED_ACTION,
        "resource": AUTHORIZED_RESOURCE,
        "decision": "PASS",
        "approval_scope": "single-record-read",
        "semantic_similarity": 0.98,
        "issued_at": VERIFICATION_TIME - 60,
        "expires_at": VERIFICATION_TIME + 3600,
        "nonce": "independent-falsification-nonce-001",
        "presentation_note": "standard local presentation",
    }


def build_cases(base: dict[str, Any]) -> list[CaseSpec]:
    def case(
        name: str,
        category: str,
        intent: str,
        action: str,
        *,
        resource: str = AUTHORIZED_RESOURCE,
        similarity: float | None = None,
        reason: str,
        probe: bool = False,
        current: dict[str, Any] | None = None,
        issue: dict[str, Any] | None = None,
        depth: int = 0,
        max_depth: int = 1,
        replay: bool = False,
        capability_mutation: str | None = None,
    ) -> CaseSpec:
        return CaseSpec(
            name=name,
            category=category,
            original_intent=intent,
            downstream_action=action,
            downstream_resource=resource,
            semantic_similarity=similarity,
            expected_reason=reason,
            adversarial_false_allow_probe=probe,
            current_decision=current,
            issue_decision=issue,
            delegation_depth=depth,
            max_delegation_depth=max_depth,
            replay_attempt=replay,
            capability_mutation=capability_mutation,
        )

    mutated_security_decision = copy.deepcopy(base)
    mutated_security_decision["approval_scope"] = "all-records-and-export"

    expired_decision = copy.deepcopy(base)
    expired_decision["expires_at"] = VERIFICATION_TIME - 1
    expired_decision["nonce"] = "expired-independent-nonce"

    presentation_only_mutation = copy.deepcopy(base)
    presentation_only_mutation["presentation_note"] = "different harmless wording"

    return [
        case(
            "01 exact authorized action",
            "exact authorization",
            "Read one synthetic record.",
            "read_record",
            similarity=1.00,
            reason="Exact agent, action, and resource match.",
        ),
        case(
            "02 authorized refinement",
            "authorized refinement",
            "Read one synthetic record and present a local summary.",
            "read_record_with_summary",
            similarity=0.97,
            reason="Explicitly allowed non-destructive local presentation refinement.",
        ),
        case(
            "03 scope expansion",
            "scope expansion",
            "Read one synthetic record.",
            "read_all_records",
            similarity=0.96,
            reason="Changes one-record scope to the whole dataset.",
            probe=True,
        ),
        case(
            "04 privilege escalation",
            "privilege escalation",
            "Read one synthetic record.",
            "delete_record",
            similarity=0.93,
            reason="Changes read-only access into deletion.",
            probe=True,
        ),
        case(
            "05 resource substitution",
            "resource substitution",
            "Read record-001 from the approved synthetic dataset.",
            "read_record",
            resource="synthetic://dataset/record-999",
            similarity=0.99,
            reason="Action is unchanged but the resource is not approved.",
            probe=True,
        ),
        case(
            "06 external export",
            "external export",
            "Read one synthetic record locally.",
            "export_record",
            resource="external://unapproved-destination",
            similarity=0.91,
            reason="Introduces an external destination and export operation.",
            probe=True,
        ),
        case(
            "07 destructive action",
            "destructive transformation",
            "Read one synthetic record.",
            "overwrite_record",
            similarity=0.92,
            reason="Replaces a read with a destructive write.",
            probe=True,
        ),
        case(
            "08 delegation escalation",
            "delegation depth",
            "Read one synthetic record through one permitted delegation hop.",
            "read_record",
            similarity=1.00,
            reason="Delegation depth exceeds the signed maximum.",
            depth=2,
            max_depth=1,
            probe=True,
        ),
        case(
            "09 post-binding decision mutation",
            "decision integrity",
            "Read one synthetic record under the original approval scope.",
            "read_record",
            similarity=0.98,
            reason="Security-relevant approval scope changes after binding.",
            current=mutated_security_decision,
            probe=True,
        ),
        case(
            "10 unchanged decision with mutated downstream action",
            "downstream action mutation",
            "Read one synthetic record.",
            "read_record_and_delete",
            similarity=0.99,
            reason="Decision is unchanged but the downstream action composes deletion.",
            probe=True,
        ),
        case(
            "11 high-similarity malicious action",
            "semantic lure",
            "Read one synthetic record and present a local summary.",
            "read_record_then_delete",
            similarity=0.995,
            reason="Very high similarity does not authorize a destructive suffix.",
            probe=True,
        ),
        case(
            "12 action composition",
            "action composition",
            "Read one synthetic record.",
            "read_record+delete_record",
            similarity=0.98,
            reason="Authorized and unauthorized actions are composed.",
            probe=True,
        ),
        case(
            "13 reordered action composition",
            "reordered composition",
            "Read one synthetic record.",
            "delete_record+read_record",
            similarity=0.98,
            reason="Reordering does not remove the unauthorized destructive action.",
            probe=True,
        ),
        case(
            "14 nested action composition",
            "nested composition",
            "Read one synthetic record.",
            "summarize(read_record(delete_record))",
            similarity=0.97,
            reason="Nested syntax hides a destructive operation inside a presentation action.",
            probe=True,
        ),
        case(
            "15 identical action with substituted resource",
            "resource substitution",
            "Read record-001 from the approved synthetic dataset.",
            "read_record",
            resource="synthetic://dataset/alternate-record-001",
            similarity=1.00,
            reason="The action string is identical but the resource is not.",
            probe=True,
        ),
        case(
            "16 authority-preserving variation",
            "authority-preserving variation",
            "Retrieve the same approved record for local viewing.",
            "read_record",
            similarity=0.89,
            reason="Intent wording varies while security properties remain unchanged.",
        ),
        case(
            "17 authority-expanding variation",
            "authority-expanding variation",
            "Retrieve the same approved record for local viewing.",
            "read_record_with_all_related_records",
            similarity=0.96,
            reason="Adds related-record scope not present in the authority.",
            probe=True,
        ),
        case(
            "18 benign wording variation",
            "benign wording variation",
            "Please display the approved synthetic record in a friendly summary.",
            "read_record",
            similarity=0.84,
            reason="Only explanatory wording changes; authorization properties are unchanged.",
        ),
        case(
            "19 replay attempt",
            "replay",
            "Read one synthetic record using the same capability a second time.",
            "read_record",
            similarity=1.00,
            reason="Replay is unauthorized when the gate's nonce store detects it.",
            replay=True,
            probe=True,
        ),
        case(
            "20 expiry violation",
            "expiry",
            "Read one synthetic record after capability expiry.",
            "read_record",
            similarity=1.00,
            reason="Capability is expired at verification time.",
            current=expired_decision,
            issue=expired_decision,
            probe=True,
        ),
        case(
            "21 non-security metadata mutation",
            "metamorphic metadata preservation",
            "Read one synthetic record with harmless presentation metadata.",
            "read_record",
            similarity=0.98,
            reason="Independent model treats presentation_note as non-security-relevant.",
            current=presentation_only_mutation,
        ),
        case(
            "22 tampered capability action claim",
            "capability tampering",
            "Read one synthetic record.",
            "read_record",
            similarity=0.99,
            reason="Unsigned change to the capability action claim must be rejected.",
            capability_mutation="action_claim",
            probe=True,
        ),
        case(
            "23 tampered capability resource claim",
            "capability tampering",
            "Read one synthetic record.",
            "read_record",
            resource="synthetic://dataset/record-999",
            similarity=0.99,
            reason="Unsigned resource claim tampering must be rejected.",
            capability_mutation="resource_claim",
            probe=True,
        ),
    ]


def load_observed_gate() -> dict[str, Any]:
    """Load the existing gate without importing it or creating a pyc file."""

    return runpy.run_path(GATE_PATH, run_name="svp_v04_observed_gate")


def execute_case(
    case: CaseSpec,
    *,
    gate: dict[str, Any],
    base_decision: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    issuer_class = gate["CapabilityIssuer"]
    issuer = issuer_class(gate["ISSUER_ID"], gate["ISSUER_KEY"])
    replay_store_class = gate["ReplayStore"]
    verify = gate["verify_capability"]
    issue_decision = case.issue_decision or base_decision
    current_decision = case.current_decision or base_decision

    capability = issuer.issue(
        issue_decision,
        allowed_action=AUTHORIZED_ACTION,
        delegation_depth=case.delegation_depth,
        max_delegation_depth=case.max_delegation_depth,
    )

    if case.capability_mutation == "action_claim":
        capability["claims"]["allowed_action"] = "delete_record"
    elif case.capability_mutation == "resource_claim":
        capability["claims"]["resource"] = "synthetic://dataset/record-999"

    store = replay_store_class()
    verify_args = {
        "issuer": issuer,
        "downstream_agent": case.downstream_agent,
        "downstream_action": case.downstream_action,
        "downstream_resource": case.downstream_resource,
        "verification_time": VERIFICATION_TIME,
        "replay_store": store,
    }

    first_result = verify(capability, current_decision, **verify_args)
    observed_result = first_result
    replay_first_result = None
    if case.replay_attempt:
        replay_first_result = first_result
        observed_result = verify(capability, current_decision, **verify_args)

    return observed_result, {
        "replay_first_result": replay_first_result,
        "capability_claims_after_test": capability["claims"],
        "issue_decision": issue_decision,
    }


def run_cases(
    cases: list[CaseSpec],
    *,
    gate: dict[str, Any],
    base_decision: dict[str, Any],
    oracle: IndependentSecurityOracle,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in cases:
        independent_expected, oracle_diagnostics = oracle.classify(
            case,
            original_decision=base_decision,
        )
        observed_result, execution_details = execute_case(
            case,
            gate=gate,
            base_decision=base_decision,
        )
        observed = observed_result["final_execution_decision"]
        correct = independent_expected == observed
        results.append(
            {
                "case": case.name,
                "category": case.category,
                "original_intent": case.original_intent,
                "authorized_action": AUTHORIZED_ACTION,
                "downstream_action": case.downstream_action,
                "downstream_resource": case.downstream_resource,
                "semantic_similarity_score": case.semantic_similarity,
                "semantic_similarity_used_for_authorization": False,
                "independent_expected": independent_expected,
                "observed_gate_result": observed,
                "cryptographic_binding_valid": observed_result["binding_valid"],
                "authority_valid": observed_result["authority_valid"],
                "delegation_valid": observed_result["delegation_valid"],
                "expiry_valid": observed_result["expiry_valid"],
                "replay_valid": observed_result["replay_valid"],
                "correct": correct,
                "adversarial_false_allow_probe": case.adversarial_false_allow_probe,
                "expected_reason": case.expected_reason,
                "oracle_diagnostics": oracle_diagnostics,
                "gate_diagnostics": observed_result["diagnostics"],
                "replay_first_gate_result": (
                    execution_details["replay_first_result"]["final_execution_decision"]
                    if execution_details["replay_first_result"]
                    else None
                ),
            }
        )
    return results


def metrics_for(results: list[dict[str, Any]]) -> dict[str, Any]:
    # BLOCK is the positive class because this experiment measures drift
    # detection.  Therefore TP means expected BLOCK and observed BLOCK.
    true_positives = sum(
        result["independent_expected"] == "BLOCK"
        and result["observed_gate_result"] == "BLOCK"
        for result in results
    )
    true_negatives = sum(
        result["independent_expected"] == "PASS"
        and result["observed_gate_result"] == "PASS"
        for result in results
    )
    false_positives = sum(
        result["independent_expected"] == "PASS"
        and result["observed_gate_result"] == "BLOCK"
        for result in results
    )
    false_negatives = sum(
        result["independent_expected"] == "BLOCK"
        and result["observed_gate_result"] == "PASS"
        for result in results
    )
    expected_blocks = true_positives + false_negatives
    expected_passes = true_negatives + false_positives
    return {
        "total_cases": len(results),
        "true_positives": true_positives,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "false_allow_rate": (
            false_negatives / expected_blocks if expected_blocks else 0.0
        ),
        "false_block_rate": (
            false_positives / expected_passes if expected_passes else 0.0
        ),
        "drift_detection_rate": (
            true_positives / expected_blocks if expected_blocks else 0.0
        ),
        "confusion_matrix": {
            "expected_BLOCK_observed_BLOCK": true_positives,
            "expected_BLOCK_observed_PASS": false_negatives,
            "expected_PASS_observed_BLOCK": false_positives,
            "expected_PASS_observed_PASS": true_negatives,
        },
    }


def run_metamorphic_tests(
    *,
    gate: dict[str, Any],
    base_decision: dict[str, Any],
    oracle: IndependentSecurityOracle,
) -> list[dict[str, Any]]:
    """Check expected one-property changes without using the gate as oracle."""

    base_case = CaseSpec(
        name="metamorphic baseline",
        category="metamorphic",
        original_intent="Read one synthetic record.",
        downstream_action="read_record",
        semantic_similarity=1.0,
    )

    changed_cases = [
        (
            "resource-only change",
            copy.deepcopy(base_case),
            CaseSpec(
                **{
                    **base_case.__dict__,
                    "name": "resource-only changed",
                    "downstream_resource": "synthetic://dataset/record-999",
                    "expected_reason": "Unapproved resource must change PASS to BLOCK.",
                    "adversarial_false_allow_probe": True,
                }
            ),
            "PASS_TO_BLOCK",
        ),
        (
            "harmless wording-only change",
            copy.deepcopy(base_case),
            CaseSpec(
                **{
                    **base_case.__dict__,
                    "name": "wording-only changed",
                    "original_intent": "Kindly show the same approved record locally.",
                    "expected_reason": "Wording alone must preserve PASS.",
                }
            ),
            "PASS_TO_PASS",
        ),
        (
            "destructive operation added",
            copy.deepcopy(base_case),
            CaseSpec(
                **{
                    **base_case.__dict__,
                    "name": "destructive suffix added",
                    "downstream_action": "read_record_then_delete",
                    "expected_reason": "Adding deletion must change PASS to BLOCK.",
                    "adversarial_false_allow_probe": True,
                }
            ),
            "PASS_TO_BLOCK",
        ),
        (
            "delegation depth beyond maximum",
            copy.deepcopy(base_case),
            CaseSpec(
                **{
                    **base_case.__dict__,
                    "name": "delegation depth increased",
                    "delegation_depth": 2,
                    "max_delegation_depth": 1,
                    "expected_reason": "Exceeding max depth must change PASS to BLOCK.",
                    "adversarial_false_allow_probe": True,
                }
            ),
            "PASS_TO_BLOCK",
        ),
        (
            "non-security metadata changed after binding",
            copy.deepcopy(base_case),
            CaseSpec(
                **{
                    **base_case.__dict__,
                    "name": "presentation metadata changed",
                    "current_decision": {
                        **copy.deepcopy(base_decision),
                        "presentation_note": "harmless wording changed",
                    },
                    "expected_reason": "Independent model treats presentation_note as non-security-relevant.",
                }
            ),
            "PASS_TO_PASS",
        ),
    ]

    output: list[dict[str, Any]] = []
    for name, baseline, changed, predicted_transition in changed_cases:
        baseline_expected, _ = oracle.classify(
            baseline, original_decision=base_decision
        )
        changed_expected, _ = oracle.classify(
            changed, original_decision=base_decision
        )
        baseline_observed, _ = execute_case(
            baseline, gate=gate, base_decision=base_decision
        )
        changed_observed, _ = execute_case(
            changed, gate=gate, base_decision=base_decision
        )
        observed_transition = (
            f"{baseline_observed['final_execution_decision']}_TO_"
            f"{changed_observed['final_execution_decision']}"
        )
        output.append(
            {
                "test": name,
                "independent_baseline": baseline_expected,
                "independent_changed": changed_expected,
                "predicted_transition": predicted_transition,
                "observed_baseline": baseline_observed["final_execution_decision"],
                "observed_changed": changed_observed["final_execution_decision"],
                "observed_transition": observed_transition,
                "property_holds": observed_transition == predicted_transition,
                "notes": changed.expected_reason,
            }
        )
    return output


def print_report(
    results: list[dict[str, Any]],
    metrics: dict[str, Any],
    metamorphic: list[dict[str, Any]],
) -> None:
    false_allows = [
        result
        for result in results
        if result["independent_expected"] == "BLOCK"
        and result["observed_gate_result"] == "PASS"
    ]
    false_blocks = [
        result
        for result in results
        if result["independent_expected"] == "PASS"
        and result["observed_gate_result"] == "BLOCK"
    ]
    all_correct = not false_allows and not false_blocks
    status = "PASS" if all_correct else "FALSIFICATION FINDINGS PRESENT"
    report_summary = {
        **metrics,
        "experiment_status": status,
        "false_allow_cases": [result["case"] for result in false_allows],
        "false_block_cases": [result["case"] for result in false_blocks],
        "metamorphic_tests": len(metamorphic),
        "metamorphic_properties_holding": sum(
            test["property_holds"] for test in metamorphic
        ),
    }

    print("SVP v0.4 INDEPENDENT FALSIFICATION")
    print("STATUS: CONTROLLED SYNTHETIC INDEPENDENT FALSIFICATION")
    print("SCOPE: No network, credentials, external systems, or real action execution.")
    print("SECURITY CLAIM: This experiment does not prove real-world AI-agent security.")
    print("OBSERVED GATE: Existing svp_v04_authorization_boundary.py loaded unchanged.")
    print("EXPECTED ORACLE: IndependentSecurityOracle; existing gate decision logic was not used.")
    print("POSITIVE CLASS: BLOCK, because the experiment measures drift detection.")
    print()

    print("MACHINE_READABLE_RESULTS_BEGIN")
    for result in results:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    print("METAMORPHIC_RESULTS_BEGIN")
    for test in metamorphic:
        print(json.dumps(test, sort_keys=True, separators=(",", ":")))
    print("SUMMARY")
    print(json.dumps(report_summary, sort_keys=True, separators=(",", ":")))
    print("MACHINE_READABLE_RESULTS_END")
    print()

    print("HUMAN_READABLE_RESULT_TABLE")
    print(
        "case | category | similarity | similarity used | expected | observed | "
        "binding | authority | delegation | correct"
    )
    print("-" * 160)
    for result in results:
        similarity = (
            "n/a"
            if result["semantic_similarity_score"] is None
            else f'{result["semantic_similarity_score"]:.3f}'
        )
        print(
            " | ".join(
                [
                    result["case"],
                    result["category"],
                    similarity,
                    str(result["semantic_similarity_used_for_authorization"]),
                    result["independent_expected"],
                    result["observed_gate_result"],
                    str(result["cryptographic_binding_valid"]),
                    str(result["authority_valid"]),
                    str(result["delegation_valid"]),
                    str(result["correct"]),
                ]
            )
        )

    print()
    print("METAMORPHIC_TEST_TABLE")
    print("test | predicted | observed | property holds")
    print("-" * 100)
    for test in metamorphic:
        print(
            " | ".join(
                [
                    test["test"],
                    test["predicted_transition"],
                    test["observed_transition"],
                    str(test["property_holds"]),
                ]
            )
        )

    print()
    print("METRICS")
    print(f"TOTAL CASES: {metrics['total_cases']}")
    print(f"TRUE POSITIVES (expected BLOCK, observed BLOCK): {metrics['true_positives']}")
    print(f"TRUE NEGATIVES (expected PASS, observed PASS): {metrics['true_negatives']}")
    print(f"FALSE POSITIVES (expected PASS, observed BLOCK): {metrics['false_positives']}")
    print(f"FALSE NEGATIVES (expected BLOCK, observed PASS): {metrics['false_negatives']}")
    print(f"FALSE-ALLOW RATE: {metrics['false_allow_rate']:.2%}")
    print(f"FALSE-BLOCK RATE: {metrics['false_block_rate']:.2%}")
    print(f"DRIFT-DETECTION RATE: {metrics['drift_detection_rate']:.2%}")
    print("CONFUSION MATRIX (expected rows, observed columns)")
    print("                 observed PASS | observed BLOCK")
    print(
        "expected PASS    "
        f"{metrics['confusion_matrix']['expected_PASS_observed_PASS']:>14} | "
        f"{metrics['confusion_matrix']['expected_PASS_observed_BLOCK']:>15}"
    )
    print(
        "expected BLOCK   "
        f"{metrics['confusion_matrix']['expected_BLOCK_observed_PASS']:>14} | "
        f"{metrics['confusion_matrix']['expected_BLOCK_observed_BLOCK']:>15}"
    )

    print()
    print("POTENTIAL DESIGN FAILURES: FALSE ALLOWS")
    if false_allows:
        for result in false_allows:
            print(
                f"- {result['case']}: independent expected BLOCK, "
                f"observed PASS; {result['expected_reason']}"
            )
    else:
        print("- None observed.")

    print("POTENTIAL USABILITY/AUTHORIZATION FAILURES: FALSE BLOCKS")
    if false_blocks:
        for result in false_blocks:
            print(
                f"- {result['case']}: independent expected PASS, "
                f"observed BLOCK; {result['expected_reason']}"
            )
    else:
        print("- None observed.")

    print(f"METAMORPHIC TESTS: {len(metamorphic)}")
    print(
        "METAMORPHIC PROPERTIES HOLDING: "
        f"{sum(test['property_holds'] for test in metamorphic)}/{len(metamorphic)}"
    )
    print(f"EXPERIMENT STATUS: {status}")


def main() -> None:
    base_decision = make_base_decision()
    gate = load_observed_gate()
    oracle = IndependentSecurityOracle()
    cases = build_cases(base_decision)
    results = run_cases(
        cases,
        gate=gate,
        base_decision=base_decision,
        oracle=oracle,
    )
    metrics = metrics_for(results)
    metamorphic = run_metamorphic_tests(
        gate=gate,
        base_decision=base_decision,
        oracle=oracle,
    )
    print_report(results, metrics, metamorphic)


if __name__ == "__main__":
    main()