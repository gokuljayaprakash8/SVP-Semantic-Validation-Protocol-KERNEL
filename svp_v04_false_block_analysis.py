import json
import hashlib
import hmac

print("CONTROLLED SYNTHETIC FALSE-BLOCK ANALYSIS")
print("SCOPE: Synthetic analysis only; no network, external systems, credentials, or real actions.")
print("SECURITY CLAIM: This experiment does not prove real-world AI-agent security.")

SECRET=b"synthetic-analysis-key"

base={
    "identity":"agent-001",
    "action":"read_record",
    "resource":"synthetic://dataset/record-001",
    "delegation_depth":0,
    "max_delegation_depth":1,
    "presentation_note":"local summary"
}

SECURITY_FIELDS=("identity","action","resource","delegation_depth","max_delegation_depth")

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"))

def binding(obj):
    payload=canonical({k:obj[k] for k in SECURITY_FIELDS})
    digest=hashlib.sha256(payload.encode()).hexdigest()
    mac=hmac.new(SECRET,digest.encode(),hashlib.sha256).hexdigest()
    return digest,mac

original_hash,original_mac=binding(base)

cases=[]

def add(name,changed,expected,security_relevant):
    x=dict(base)
    if changed:
        x.update(changed)
    h,m=binding(x)
    cases.append({
        "case":name,
        "changed_property":changed,
        "independent_expected":expected,
        "security_relevant":security_relevant,
        "binding_valid_against_original":h==original_hash and m==original_mac,
        "binding_hash_matches":h==original_hash,
        "interpretation":"security-relevant change" if security_relevant else "non-security metadata change"
    })

add("A exact authorized action",{},"PASS",True)
add("B authorized refinement",{"action":"read_record_with_summary"},"PASS",True)
add("C wording-only presentation change",{"presentation_note":"show concise local summary"},"PASS",False)
add("D presentation_note mutation",{"presentation_note":"different presentation text"},"PASS",False)
add("E security-relevant action mutation",{"action":"delete_record"},"BLOCK",True)
add("F unapproved resource",{"resource":"synthetic://dataset/record-999"},"BLOCK",True)
add("G delegation beyond maximum",{"delegation_depth":2},"BLOCK",True)

print("FIELD SENSITIVITY")
for field in base:
    x=dict(base)
    if field=="presentation_note":
        x[field]="mutated presentation metadata"
    elif field=="action":
        x[field]="delete_record"
    elif field=="resource":
        x[field]="synthetic://dataset/record-999"
    elif field=="delegation_depth":
        x[field]=2
    elif field=="max_delegation_depth":
        x[field]=0
    elif field=="identity":
        x[field]="agent-999"
    h,m=binding(x)
    print(json.dumps({"field":field,"binding_changes":not(h==original_hash and m==original_mac),"security_relevant":field in SECURITY_FIELDS}))

print("CASE RESULTS")
for c in cases:
    print(json.dumps(c,sort_keys=True))

print("INTERPRETATION")
print("The independent model treats presentation_note as non-security-relevant.")
print("Therefore a binding that covers presentation_note would be strict but may create an authorization/usability limitation.")
print("Security-relevant action, resource, identity, and delegation changes should affect authorization.")
print("This analysis does not modify or claim to prove the real-world security of the SVP implementation.")
