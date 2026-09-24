import json, sys

try:
    import jsonschema
except ImportError:
    print("jsonschema not installed, skipping schema validation")
    sys.exit(0)

schema_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp26\book-author\schema.json'
payload_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.json'

with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

with open(payload_path, 'r', encoding='utf-8') as f:
    payload = json.load(f)

try:
    jsonschema.validate(payload, schema)
    print("JSON SCHEMA VALIDATION PASSED")
except jsonschema.ValidationError as e:
    print("JSON SCHEMA VALIDATION FAILED:")
    print(e.message)
    print("Path:", list(e.path))
