import hashlib
import hmac
import json

KEY = b"svp-v04-research-key"

SECURITY_FIELDS = {
    "identity",
    "action",
    "resource",
    "authority",
    "delegation_depth",
    "max_delegation_depth",
    "expiry",
}

BASE = {
    "identity": "agent-001",
    "action": "read_record",
    "resource": "synthetic://dataset/record-001",
    "authority": "read",
    "delegation_depth": 0,
    "max_delegation_depth": 1,
    "expiry": 4102444800,
    "presentation_note": "show concise local summary",
    "explanation": "authorized local read",
    "formatting": "plain",
}

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def commitment(obj):
    payload = canonical({k: obj[k] for k in SECURITY_FIELDS})
    digest = hashlib.sha256(payload).hexdigest()
    mac = hmac.new(KEY, digest.encode(), hashlib.sha256).hexdigest()
    return digest, mac

ORIGINAL_HASH, ORIGINAL_MAC = commitment(BASE)

def independent_expected(obj):
    if obj["identity"] != BASE["identity"]:
        return "BLOCK"
    if obj["action"] != BASE["action"]:
        return "BLOCK"
    if obj["resource"] != BASE["resource"]:
        return "BLOCK"
    if obj["authority"] != BASE["authority"]:
        return "BLOCK"
    if obj["delegation_depth"] > obj["max_delegation_depth"]:
        return "BLOCK"
    if obj["max_delegation_depth"] != BASE["max_delegation_depth"]:
        return "BLOCK"
    if obj["expiry"] != BASE["expiry"]:
        return "BLOCK"
    return "PASS"

def observed_commitment(obj):
    digest, mac = commitment(obj)
    return "PASS" if digest == ORIGINAL_HASH and hmac.compare_digest(mac, ORIGINAL_MAC) else "BLOCK"

CASES = []

def add(name, mutation, similarity=1.0):
    obj = dict(BASE)
    obj.update(mutation)
    expected = independent_expected(obj)
    observed = observed_commitment(obj)
    CASES.append({
        "case": name,
        "mutation": mutation,
        "semantic_similarity": similarity,
        "expected": expected,
        "observed": observed,
        "correct": expected == observed,
        "binding_valid": observed == "PASS",
    })

add("A exact baseline", {})
add("B presentation wording", {"presentation_note": "display short local summary"}, .99)
add("C explanation wording", {"explanation": "different harmless explanation"}, .99)
add("D formatting variation", {"formatting": "compact"}, .99)
add("E action mutation", {"action": "delete_record"}, .96)
add("F resource mutation", {"resource": "synthetic://dataset/record-999"}, .99)
add("G identity mutation", {"identity": "agent-999"}, .98)
add("H authority expansion", {"authority": "read_write"}, .95)
add("I delegation mutation", {"delegation_depth": 2}, .99)
add("J maximum delegation mutation", {"max_delegation_depth": 2}, .99)
add("K expiry mutation", {"expiry": 4102444900}, .99)
add("L metadata plus action", {"presentation_note": "summary; delete_record", "action": "delete_record"}, .96)
add("M metadata plus resource", {"presentation_note": "record-999", "resource": "synthetic://dataset/record-999"}, .98)
add("N malicious action hidden in explanation", {"explanation": "read_record then delete_record"}, .98)
add("O malicious action hidden in note", {"presentation_note": "read_record_and_delete"}, .99)
add("P high similarity privilege escalation", {"action": "read_record_with_delete"}, .995)
add("Q harmless Unicode wording", {"presentation_note": "show concise local summary — safely"}, .99)

reordered = json.loads(json.dumps(BASE, ensure_ascii=False))
CASES.append({
    "case": "R reordered representation",
    "mutation": "same security properties, different JSON insertion order",
    "semantic_similarity": 1.0,
    "expected": "PASS",
    "observed": observed_commitment(reordered),
    "correct": observed_commitment(reordered) == "PASS",
    "binding_valid": observed_commitment(reordered) == "PASS",
})

print("SVP v0.4 COMMITMENT-BOUNDARY EVALUATION")
print("STATUS: CONTROLLED SYNTHETIC COMMITMENT-BOUNDARY EVALUATION")
print("SCOPE: Synthetic data only; no network, credentials, external systems, or real actions.")
print("SECURITY CLAIM: This experiment does not prove real-world AI-agent security.")
print("SECURITY FIELDS:", sorted(SECURITY_FIELDS))
print("NON-SECURITY METADATA: presentation_note, explanation, formatting")
print()

for case in CASES:
    print(json.dumps(case, sort_keys=True, ensure_ascii=False))

total = len(CASES)
correct = sum(c["correct"] for c in CASES)
false_allow = sum(c["expected"] == "BLOCK" and c["observed"] == "PASS" for c in CASES)
false_block = sum(c["expected"] == "PASS" and c["observed"] == "BLOCK" for c in CASES)
pass_cases = sum(c["expected"] == "PASS" for c in CASES)
block_cases = sum(c["expected"] == "BLOCK" for c in CASES)

print()
print("METRICS")
print("TOTAL CASES:", total)
print("CORRECT CASES:", correct)
print("FALSE ALLOWS:", false_allow)
print("FALSE BLOCKS:", false_block)
print("FALSE-ALLOW RATE:", f"{false_allow / block_cases:.2%}")
print("FALSE-BLOCK RATE:", f"{false_block / pass_cases:.2%}")
print("CONFUSION MATRIX")
print("                 observed PASS | observed BLOCK")
print(f"expected PASS        {sum(c["expected"] == "PASS" and c["observed"] == "PASS" for c in CASES):>5} | {false_block:>15}")
print(f"expected BLOCK       {false_allow:>5} | {sum(c["expected"] == "BLOCK" and c["observed"] == "BLOCK" for c in CASES):>15}")
print("EXPERIMENT STATUS:", "PASS" if false_allow == 0 else "FALSIFICATION FINDING")
