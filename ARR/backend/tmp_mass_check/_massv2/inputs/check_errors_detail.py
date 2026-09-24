import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))
validator = Draft7Validator(schema)
errors = list(validator.iter_errors(data))
print(f"Total errors: {len(errors)}")

# Group errors by type
for err in errors[:20]:
    path = '/'.join(str(p) for p in err.absolute_path)
    ctx = err.context
    if ctx:
        ctx_msg = ctx[0].message if ctx else ''
    else:
        ctx_msg = ''
    print(f"\n{path}:")
    print(f"  MSG: {err.message[:200]}")
    if ctx_msg:
        print(f"  CTX: {ctx_msg[:200]}")
