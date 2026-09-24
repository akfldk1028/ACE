import json
from jsonschema import Draft7Validator

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json', encoding='utf-8'))
payload = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json', encoding='utf-8'))

v = Draft7Validator(schema)
errors = list(v.iter_errors(payload))
print(f"Total errors: {len(errors)}")
for e in errors:
    path = list(e.absolute_path)
    print(f"\nPath: {path}")
    print(f"Message: {e.message[:400]}")
    # Get the specific context errors
    for ce in e.context:
        print(f"  Sub: {ce.message[:200]}")
