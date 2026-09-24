import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('book-comp18_INVALID.json', encoding='utf-8') as f:
    data_orig = json.load(f)
with open('book-comp18.json', encoding='utf-8') as f:
    data_fixed = json.load(f)

schema_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'
with open(schema_path, encoding='utf-8') as f:
    schema = json.load(f)

import jsonschema

# Validate original
validator = jsonschema.Draft7Validator(schema)
errors_orig = list(validator.iter_errors(data_orig))
print(f'Original file schema errors: {len(errors_orig)}')
for e in errors_orig[:3]:
    print(f'  {list(e.absolute_path)}: {e.message[:150]}')

print()

# Check mat0 in original vs fixed
p0_orig = data_orig['programs'][0]
p0_fixed = data_fixed['programs'][0]
print('Original p0 mat0:', json.dumps(p0_orig['nodes'][2]))
print('Fixed p0 mat0:', json.dumps(p0_fixed['nodes'][2]))
print()
print('Original p0 body0:', json.dumps(p0_orig['nodes'][3]))
print('Fixed p0 body0:', json.dumps(p0_fixed['nodes'][3]))
