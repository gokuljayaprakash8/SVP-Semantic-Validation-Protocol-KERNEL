import json
from app import svp_kernel

TESTS = [
    "archive database logs",
    "archive security logs",
    "archive audit logs",
    "archive application logs",
    "archive forensic logs",
    "archive database records",
]

print("=" * 80)
print("SVP LOG/ARCHIVE SEMANTIC BOUNDARY TEST")
print("LOCAL SYNTHETIC INPUTS ONLY")
print("No database/network/action execution")
print("=" * 80)

for text in TESTS:
    result = svp_kernel(text)
    print("\n" + "-" * 80)
    print("INPUT:", repr(text))
    print(json.dumps(result, indent=2, default=str))
