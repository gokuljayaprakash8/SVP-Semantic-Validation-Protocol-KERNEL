import hashlib,hmac,json

SECRET=b"svp-v04-test-secret"

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
    "formatting":"standard"
}

SECURITY_FIELDS=(
    "identity",
    "action",
    "resource",
    "authority",
    "delegation_depth",
    "max_delegation_depth",
    "expiry",
)

def canonical_security(obj):
    return json.dumps(
        {k:obj[k] for k in SECURITY_FIELDS},
        sort_keys=True,
        separators=(",",":"),
        ensure_ascii=False,
    ).encode()

def full_commitment(obj):
    raw=json.dumps(
        obj,
        sort_keys=True,
        separators=(",",":"),
        ensure_ascii=False,
    ).encode()
    digest=hashlib.sha256(raw).hexdigest()
    mac=hmac.new(SECRET,digest.encode(),hashlib.sha256).hexdigest()
    return digest,mac

def security_commitment(obj):
    raw=canonical_security(obj)
    digest=hashlib.sha256(raw).hexdigest()
    mac=hmac.new(SECRET,digest.encode(),hashlib.sha256).hexdigest()
    return digest,mac

FULL_HASH,FULL_MAC=full_commitment(BASE)
SEC_HASH,SEC_MAC=security_commitment(BASE)

def independent_expected(obj):
    for k in SECURITY_FIELDS:
        if obj.get(k)!=BASE.get(k):
            return "BLOCK"
    if obj.get("delegation_depth",999)>obj.get("max_delegation_depth",-1):
        return "BLOCK"
    return "PASS"

def full_gate(obj):
    d,m=full_commitment(obj)
    return d==FULL_HASH and hmac.compare_digest(m,FULL_MAC)

def security_gate(obj):
    d,m=security_commitment(obj)
    return d==SEC_HASH and hmac.compare_digest(m,SEC_MAC)

CASES=[]

def add(name,mutation):
    obj=dict(BASE)
    obj.update(mutation)
    expected=independent_expected(obj)
    full=full_gate(obj)
    projected=security_gate(obj)
    CASES.append({
        "case":name,
        "expected":expected,
        "full_commitment":"PASS" if full else "BLOCK",
        "security_projection":"PASS" if projected else "BLOCK",
        "full_correct":("PASS" if full else "BLOCK")==expected,
        "projection_correct":("PASS" if projected else "BLOCK")==expected,
        "mutation":mutation,
    })

add("A exact baseline",{})
add("B harmless wording",{"presentation_note":"different concise summary"})
add("C explanation change",{"explanation":"different explanation"})
add("D formatting change",{"formatting":"compact"})
add("E action mutation",{"action":"delete_record"})
add("F resource mutation",{"resource":"synthetic://dataset/record-999"})
add("G identity mutation",{"identity":"agent-999"})
add("H authority expansion",{"authority":"read_write"})
add("I delegation mutation",{"delegation_depth":2})
add("J maximum delegation mutation",{"max_delegation_depth":2})
add("K expiry mutation",{"expiry":4102444900})
add("L metadata plus malicious-looking note",{"presentation_note":"read_record_then_delete"})
add("M reordered representation",{"presentation_note":"show concise local summary"})

print("SVP v0.4 SECURITY-PROJECTION EVALUATION")
print("STATUS: CONTROLLED SYNTHETIC COMPARISON")
print("SCOPE: Synthetic data only; no network, credentials, external systems, or real actions.")
print("SECURITY CLAIM: This experiment does not prove real-world AI-agent security.")
print("")

for case in CASES:
    print(json.dumps(case,sort_keys=True))

full_false_allow=sum(c["expected"]=="BLOCK" and c["full_commitment"]=="PASS" for c in CASES)
full_false_block=sum(c["expected"]=="PASS" and c["full_commitment"]=="BLOCK" for c in CASES)
proj_false_allow=sum(c["expected"]=="BLOCK" and c["security_projection"]=="PASS" for c in CASES)
proj_false_block=sum(c["expected"]=="PASS" and c["security_projection"]=="BLOCK" for c in CASES)

print("")
print("TOTAL CASES:",len(CASES))
print("FULL COMMITMENT FALSE-ALLOWS:",full_false_allow)
print("FULL COMMITMENT FALSE-BLOCKS:",full_false_block)
print("SECURITY PROJECTION FALSE-ALLOWS:",proj_false_allow)
print("SECURITY PROJECTION FALSE-BLOCKS:",proj_false_block)
print("FULL COMMITMENT FALSE-ALLOW RATE:",f"{full_false_allow/sum(c[expected]==BLOCK for c in CASES):.2%}")
print("FULL COMMITMENT FALSE-BLOCK RATE:",f"{full_false_block/sum(c[expected]==PASS for c in CASES):.2%}")
print("SECURITY PROJECTION FALSE-ALLOW RATE:",f"{proj_false_allow/sum(c[expected]==BLOCK for c in CASES):.2%}")
print("SECURITY PROJECTION FALSE-BLOCK RATE:",f"{proj_false_block/sum(c[expected]==PASS for c in CASES):.2%}")

print("EXPERIMENT STATUS:",
      "SECURITY PROJECTION FALSIFICATION" if proj_false_allow else
      ("SECURITY PROJECTION PASSES" if proj_false_block==0 else
       "SECURITY PROJECTION HAS USABILITY FINDINGS"))
