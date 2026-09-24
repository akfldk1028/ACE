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

# Load contract
contract_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp26\book-development-parent-contract.json'
with open(contract_path, 'r', encoding='utf-8') as f:
    contract = json.load(f)

print("Contract keys:", list(contract.keys()))

# Augment context with required fields
ctx['parent'] = contract.get('parent', dev['parent'])
ctx['parent_shape_id'] = contract.get('parent_shape_id', dev['parent_shape_id'])
ctx['parent_program_hash'] = contract.get('parent_program_hash', dev['parent_program_hash'])
ctx['parent_certificate_id'] = contract.get('parent_certificate_id', '')
ctx['site_pnu'] = contract.get('site_pnu', ctx.get('pnu', ''))
ctx['storey_count'] = int(contract.get('storey_count', 5))
ctx['storey_height_m'] = float(contract.get('storey_height_m', 3.8))
ctx['target_gfa_m2'] = float(contract.get('target_gfa_m2', 4906.565793050071))
ctx['height_m'] = float(ctx['storey_count']) * float(ctx['storey_height_m'])

print("Augmented context keys:", list(ctx.keys()))
print("height_m:", ctx['height_m'])

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
