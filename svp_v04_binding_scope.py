import hashlib
import hmac
import json
from copy import deepcopy

print("SVP v0.4 BINDING-SCOPE EVALUATION")
print("STATUS: CONTROLLED SYNTHETIC BINDING-SCOPE EVALUATION")
print("SCOPE: Synthetic decisions only; no network, credentials, external systems, or real execution.")
print("SECURITY CLAIM: This experiment does not prove real-world AI-agent security.")
print("")

SECRET = b"synthetic-v04-binding-scope-key"

BASE = {
    "identity": "agent-A",
    "authorized_action": "read_record",
    "resource": "synthetic://dataset/record-001",
    "delegation_depth": 0,
    "max_delegation_depth": 1,
    "expiry": 9999999999,
    "security_policy_constraint": "read-only-local",
    "presentation_note": "local review",
    "description": "Read one synthetic record.",
}

SECURITY_FIELDS = {
    "identity",
    "authorized_action",
    "resource",
    "delegation_depth",
    "max_delegation_depth",
    "expiry",
    "security_policy_constraint",
}

def canonical(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()

def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def bind(obj):
    return hmac.new(
        SECRET,
        digest(obj).encode(),
        hashlib.sha256,
    ).hexdigest()

def verify_binding(obj, expected_hash, expected_mac):
    actual_hash = digest(obj)
    actual_mac = hmac.new(
        SECRET,
        actual_hash.encode(),
        hashlib.sha256,
    ).hexdigest()
    return (
        hmac.compare_digest(actual_hash, expected_hash)
        and hmac.compare_digest(actual_mac, expected_mac)
    )

def independent_authorization(original, downstream):
    security_equal = all(
        original[k] == downstream[k]
        for k in SECURITY_FIELDS
    )

    delegation_valid = (
        downstream["delegation_depth"]
        <= downstream["max_delegation_depth"]
    )

    if not security_equal:
        return False

    if not delegation_valid:
        return False

    return True

def case(name, mutation, mutate):
    original = deepcopy(BASE)
    downstream = deepcopy(BASE)
    mutate(downstream)

    original_hash = digest(original)
    original_mac = bind(original)

    binding_valid = verify_binding(
        downstream,
        original_hash,
        original_mac,
    )

    expected_authorization = independent_authorization(
        original,
        downstream,
    )

    observed_authorization = (
        original["authorized_action"] == downstream["authorized_action"]
        and original["resource"] == downstream["resource"]
        and original["identity"] == downstream["identity"]
        and downstream["delegation_depth"]
            <= downstream["max_delegation_depth"]
        and original["expiry"] == downstream["expiry"]
        and original["security_policy_constraint"]
            == downstream["security_policy_constraint"]
    )

    observed_execution = (
        "PASS"
        if binding_valid and observed_authorization
        else "BLOCK"
    )

    expected_execution = (
        "PASS"
        if expected_authorization
        else "BLOCK"
    )

    binding_expected = mutation not in {
        "presentation_note",
        "description",
        "formatting",
    }

    correct = (
        expected_execution == observed_execution
        and binding_valid == binding_expected
    )

    return {
        "case": name,
        "mutated_property": mutation,
        "security_relevant": mutation in SECURITY_FIELDS,
        "expected_authorization": expected_authorization,
        "expected_binding_validity": binding_expected,
        "observed_authorization": observed_authorization,
        "observed_binding_validity": binding_valid,
        "expected_execution": expected_execution,
        "final_execution_decision": observed_execution,
        "correct": correct,
    }

CASES = [
    ("A baseline authorized decision", "none",
     lambda x: None),

    ("B authorized_action mutation", "authorized_action",
     lambda x: x.update(authorized_action="delete_record")),

    ("C resource mutation", "resource",
     lambda x: x.update(resource="synthetic://dataset/record-999")),

    ("D identity mutation", "identity",
     lambda x: x.update(identity="agent-B")),

    ("E delegation depth increase", "delegation_depth",
     lambda x: x.update(delegation_depth=2)),

    ("F max delegation depth reduction", "max_delegation_depth",
     lambda x: x.update(max_delegation_depth=0)),

    ("G expiry violation", "expiry",
     lambda x: x.update(expiry=0)),

    ("H security policy mutation", "security_policy_constraint",
     lambda x: x.update(security_policy_constraint="delete-allowed")),

    ("I presentation_note mutation", "presentation_note",
     lambda x: x.update(presentation_note="formatted for UI")),

    ("J description mutation", "description",
     lambda x: x.update(description="Read and summarize one record.")),

    ("K formatting-only mutation", "formatting",
     lambda x: x.update(presentation_note="LOCAL REVIEW")),

    ("L high-similarity action mutation", "authorized_action",
     lambda x: x.update(authorized_action="read_record_then_delete")),

    ("M combined security mutation", "authorized_action+resource",
     lambda x: x.update(
         authorized_action="export_record",
         resource="external://destination",
     )),

    ("N combined harmless metadata mutation", "presentation_note+description",
     lambda x: x.update(
         presentation_note="UI view",
         description="Human-readable summary.",
     )),
]

results = []

for name, mutation, mutate in CASES:
    result = case(name, mutation, mutate)
    results.append(result)
    print(json.dumps(result, sort_keys=True))

correct = sum(r["correct"] for r in results)
false_blocks = sum(
    r["expected_execution"] == "PASS"
    and r["final_execution_decision"] == "BLOCK"
    for r in results
)
false_allows = sum(
    r["expected_execution"] == "BLOCK"
    and r["final_execution_decision"] == "PASS"
    for r in results
)

security_cases = [
    r for r in results if r["security_relevant"]
]
security_binding_failures = sum(
    not r["observed_binding_validity"]
    for r in security_cases
)

harmless_cases = [
    r for r in results
    if not r["security_relevant"]
]

harmless_preserved = sum(
    r["expected_execution"] == "PASS"
    and r["final_execution_decision"] == "PASS"
    for r in harmless_cases
)

print("")
print("HUMAN_READABLE_RESULT_TABLE")
print("case | property | security_relevant | expected | observed | binding | correct")
print("-" * 100)

for r in results:
    print(
        f"{r['case']} | "
        f"{r['mutated_property']} | "
        f"{r['security_relevant']} | "
        f"{r['expected_execution']} | "
        f"{r['final_execution_decision']} | "
        f"{r['observed_binding_validity']} | "
        f"{r['correct']}"
    )

print("")
print("METRICS")
print(f"TOTAL CASES: {len(results)}")
print(f"CORRECT CASES: {correct}")
print(f"FALSE ALLOWS: {false_allows}")
print(f"FALSE BLOCKS: {false_blocks}")
print(f"SECURITY-RELEVANT CASES: {len(security_cases)}")
print(f"SECURITY BINDING FAILURES: {security_binding_failures}")
print(f"HARMLESS CASES: {len(harmless_cases)}")
print(f"HARMLESS PASS PRESERVATION: {harmless_preserved}/{len(harmless_cases)}")
print(f"OVERALL ACCURACY: {correct / len(results):.2%}")

if false_allows:
    print("POTENTIAL SECURITY DESIGN FAILURE: FALSE ALLOW OBSERVED.")

if false_blocks:
    print("POTENTIAL OVER-BINDING / USABILITY FAILURE: FALSE BLOCK OBSERVED.")

if false_allows == 0 and false_blocks == 0:
    print("EXPERIMENT STATUS: PASS")
else:
    print("EXPERIMENT STATUS: FINDINGS PRESENT")

print("END OF CONTROLLED SYNTHETIC BINDING-SCOPE EVALUATION")
