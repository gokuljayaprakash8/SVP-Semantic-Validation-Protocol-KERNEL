import hashlib,hmac,json

SECRET=b"svp-v04-test-secret"

SECURITY_FIELDS=(
    "identity",
    "action",
    "resource",
    "authority",
    "delegation_depth",
    "max_delegation_depth",
    "expiry",
)

BASE={
    "identity":"agent-001",
    "action":"read_record",
    "resource":"synthetic://dataset/record-001",
    "authority":"read",
    "delegation_depth":0,
    "max_delegation_depth":1,
    "expiry":4102444800,
    "presentation_note":"show concise local summary",
    "explanation":"safe read operation",
    "formatting":"standard",
}

def projection(obj):
    return {k:obj[k] for k in SECURITY_FIELDS}

def canonical_projection(obj):
    return json.dumps(
        projection(obj),
        sort_keys=True,
        separators=(",",":"),
        ensure_ascii=False,
    ).encode()

def commit(obj):
    digest=hashlib.sha256(canonical_projection(obj)).hexdigest()
    mac=hmac.new(SECRET,digest.encode(),hashlib.sha256).hexdigest()
    return digest,mac

ORIGINAL=commit(BASE)

def committed(obj):
    digest,mac=commit(obj)
    return digest==ORIGINAL[0] and hmac.compare_digest(mac,ORIGINAL[1])

def independent_security(obj):
    if obj.get("identity")!=BASE["identity"]:
        return "BLOCK"
    if obj.get("action")!=BASE["action"]:
        return "BLOCK"
    if obj.get("resource")!=BASE["resource"]:
        return "BLOCK"
    if obj.get("authority")!=BASE["authority"]:
        return "BLOCK"
    if obj.get("delegation_depth")!=BASE["delegation_depth"]:
        return "BLOCK"
    if obj.get("max_delegation_depth")!=BASE["max_delegation_depth"]:
        return "BLOCK"
    if obj.get("expiry")!=BASE["expiry"]:
        return "BLOCK"
    return "PASS"

CASES=[]

def add(name,mutation,security_effect):
    obj=dict(BASE)
    obj.update(mutation)
    expected=security_effect
    observed="PASS" if committed(obj) else "BLOCK"
    result="CORRECT" if expected==observed else "FINDING"
    CASES.append({
        "case":name,
        "expected":expected,
        "observed":observed,
        "result":result,
        "mutation":mutation,
        "projected_security":projection(obj),
    })

add("A harmless presentation mutation",
    {"presentation_note":"different wording"},"PASS")

add("B harmless explanation mutation",
    {"explanation":"different explanation"},"PASS")

add("C action mutation outside projection via alias",
    {"requested_action":"delete_record"},"BLOCK")

add("D resource mutation outside projection via alias",
    {"target_resource":"synthetic://dataset/record-999"},"BLOCK")

add("E nested action metadata",
    {"metadata":{"action":"delete_record"}},"BLOCK")

add("F nested resource metadata",
    {"metadata":{"resource":"synthetic://dataset/record-999"}},"BLOCK")

add("G alternate action representation",
    {"action_alias":"delete_record"},"BLOCK")

add("H alternate authority representation",
    {"requested_authority":"read_write"},"BLOCK")

add("I security instruction in explanation",
    {"explanation":"execute delete_record with read authority"},"BLOCK")

add("J security instruction in presentation note",
    {"presentation_note":"execute delete_record"},"BLOCK")

add("K formatting-only mutation",
    {"formatting":"compact"},"PASS")

print("SVP v0.4 PROJECTION-INTEGRITY FALSIFICATION")
print("STATUS: CONTROLLED SYNTHETIC EVALUATION")
print("SCOPE: Synthetic data only; no network, credentials, external systems, or real actions.")
print("SECURITY CLAIM: This experiment does not prove real-world AI-agent security.")
print("")

for c in CASES:
    print(json.dumps(c,sort_keys=True))

false_allow=sum(c["expected"]=="BLOCK" and c["observed"]=="PASS" for c in CASES)
false_block=sum(c["expected"]=="PASS" and c["observed"]=="BLOCK" for c in CASES)

print("")
print("TOTAL CASES:",len(CASES))
print("FALSE ALLOWS:",false_allow)
print("FALSE BLOCKS:",false_block)
print("FALSE-ALLOW RATE:",f"{false_allow/sum(c[expected]==BLOCK for c in CASES):.2%}")
print("FALSE-BLOCK RATE:",f"{false_block/sum(c[expected]==PASS for c in CASES):.2%}")
print("EXPERIMENT STATUS:",
      "FALSIFICATION FINDING" if false_allow else
      ("PASS" if false_block==0 else "PASS_WITH_FALSE_BLOCKS"))
