import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    print("Installing jsonschema...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'jsonschema'], check=True)
    import jsonschema
    from jsonschema import Draft7Validator

schema_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp19\book-author\schema.json'
payload_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp19.json'

with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

with open(payload_path, 'r', encoding='utf-8') as f:
    payload = json.load(f)

validator = Draft7Validator(schema)
errors = list(validator.iter_errors(payload))

if errors:
    print(f"VALIDATION FAILED: {len(errors)} error(s):")
    for e in errors:
        print(f"  Path: {list(e.absolute_path)}")
        print(f"  Message: {e.message}")
        print()
else:
    print(f"VALIDATION PASSED: 0 errors")
    print(f"Programs: {len(payload['programs'])}")
    for i, p in enumerate(payload['programs']):
        print(f"  [{i+1}] {p['name']} | seed={p['base_seed']} | form={p['base_form_id']}")
