import json, sys, os
os.chdir(r"D:\Data\25_ACE\ARR\backend")
sys.path.insert(0, r"D:\Data\25_ACE\ARR\backend")

# Load the fixed payload
payload_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.json'
with open(payload_path, 'r', encoding='utf-8') as f:
    dev = json.load(f)

# Load context
ctx_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp26\book-author\context.json'
with open(ctx_path, 'r', encoding='utf-8') as f:
    ctx = json.load(f)

# Run validation
from design.maas.book_development import validate_development_payload
try:
    result = validate_development_payload(dev, ctx, expected_count=6)
    print("VALIDATION PASSED")
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print("VALIDATION FAILED:", e)
    import traceback
    traceback.print_exc()
