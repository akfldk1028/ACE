import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))

v = Draft7Validator(schema)
errors = list(v.iter_errors(data))
print(f'Total errors: {len(errors)}')
for e in errors[:30]:
    print(f'  PATH: {list(e.path)}')
    print(f'  MSG: {e.message[:200]}')
    print()
