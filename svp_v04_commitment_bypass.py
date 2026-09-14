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
    "presentation_note":"show concise local summary"
}

def commitment(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    digest=hashlib.sha256(raw).hexdigest()
    mac=hmac.new(SECRET,digest.encode(),hashlib.sha256).hexdigest()
    return digest,mac

ORIGINAL_HASH,ORIGINAL_MAC=commitment(BASE)

def independent_expected(obj):
    security=("identity","action","resource","authority","delegation_depth","max_delegation_depth","expiry")
    for k in security:
        if obj.get(k)!=BASE.get(k):
            return "BLOCK"
    if obj.get("delegation_depth",999)>obj.get("max_delegation_depth",-1):
        return "BLOCK"
    return "PASS"

def gate(obj):
    digest,mac=commitment(obj)
    return "PASS" if digest==ORIGINAL_HASH and hmac.compare_digest(mac,ORIGINAL_MAC) else "BLOCK"

CASES=[]

def add(name,mutation):
    obj=dict(BASE)
    obj.update(mutation)
    expected=independent_expected(obj)
    observed=gate(obj)
    CASES.append((name,expected,observed,mutation))

add("A exact baseline",{})
add("B harmless wording",{"presentation_note":"display a concise local summary"})
add("C action mutation",{"action":"delete_record"})
add("D resource mutation",{"resource":"synthetic://dataset/record-999"})
add("E authority expansion",{"authority":"read_write"})
add("F delegation expansion",{"delegation_depth":2})
add("G expiry mutation",{"expiry":4102444900})
add("H identity mutation",{"identity":"agent-999"})
add("I malicious action in metadata",{"presentation_note":"read_record_then_delete"})
add("J numeric/string ambiguity",{"delegation_depth":"0"})
add("K unicode variation",{"presentation_note":"show concise local summar\u00a0summary"})
add("L security field omission",{"action":None})
add("M nested malicious metadata",{"presentation_note":{"action":"delete_record"}})

print("SVP v0.4 COMMITMENT-BYPASS EXPERIMENT")
print("STATUS: CONTROLLED SYNTHETIC COMMITMENT-BYPASS EXPERIMENT")
print("SCOPE: Synthetic data only; no network, credentials, external systems, or real actions.")
print("SECURITY CLAIM: This experiment does not prove real-world AI-agent security.")
print("CASE | EXPECTED | OBSERVED | RESULT")

for name,expected,observed,mutation in CASES:
    result="CORRECT" if expected==observed else "FINDING"
    print(json.dumps({"case":name,"expected":expected,"observed":observed,"result":result,"mutation":mutation},sort_keys=True))

tp=sum(e=="BLOCK" and o=="BLOCK" for _,e,o,_ in CASES)
tn=sum(e=="PASS" and o=="PASS" for _,e,o,_ in CASES)
fp=sum(e=="PASS" and o=="BLOCK" for _,e,o,_ in CASES)
fn=sum(e=="BLOCK" and o=="PASS" for _,e,o,_ in CASES)
total=len(CASES)

print("TOTAL CASES:",total)
print("TRUE POSITIVES:",tp)
print("TRUE NEGATIVES:",tn)
print("FALSE POSITIVES / FALSE BLOCKS:",fp)
print("FALSE NEGATIVES / FALSE ALLOWS:",fn)
print("FALSE-ALLOW RATE:",f"{fn/(tp+fn):.2%}")
print("FALSE-BLOCK RATE:",f"{fp/(tn+fp):.2%}")
print("CONFUSION MATRIX")
print("                 observed PASS | observed BLOCK")
print(f"expected PASS    {tn:>14} | {fp:>15}")
print(f"expected BLOCK   {fn:>14} | {tp:>15}")
print("EXPERIMENT STATUS:", "FALSIFICATION FINDING" if fn else ("PASS" if fp==0 else "PASS_WITH_USABILITY_FINDINGS"))
