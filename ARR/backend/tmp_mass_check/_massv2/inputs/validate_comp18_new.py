"""Validate book-comp18.json against schema."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("jsonschema not available")
    sys.exit(1)

with open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json', encoding='utf-8') as f:
    schema = json.load(f)

with open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json', encoding='utf-8') as f:
    data = json.load(f)

validator = Draft7Validator(schema)
errors = list(validator.iter_errors(data))
print(f"Total validation errors: {len(errors)}")
for i, e in enumerate(errors[:30]):
    print(f"  [{i}] path={list(e.absolute_path)} message={e.message[:200]}")
    
if len(errors) == 0:
    print("SCHEMA VALID")
