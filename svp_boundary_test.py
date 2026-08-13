import json
from app import svp_kernel

TESTS = [
    "read database",
    "read database logs",
    "review database logs",
    "archive database logs",
    "read database logs for compliance",
    "read database logs and preserve evidence",
    "read database records",
    "read database records for compliance",
    "review database records",
    "archive database records",
]

print("=" * 80)
print("SVP SEMANTIC BOUNDARY TEST")
print("LOCAL SYNTHETIC INPUTS ONLY")
print("No database/network/action execution")
print("=" * 80)

for text in TESTS:
    result = svp_kernel(text)
    print("\n" + "-" * 80)
    print("INPUT:", repr(text))
    print(json.dumps(result, indent=2, default=str))
