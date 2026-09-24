import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

schema_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'
data_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json'

print('Schema file size (bytes):', os.path.getsize(schema_path))
print('Data file size (bytes):', os.path.getsize(data_path))

with open(schema_path, encoding='utf-8') as f:
    schema = json.load(f)
with open(data_path, encoding='utf-8') as f:
    data = json.load(f)

print('Programs:', len(data['programs']))

# Check if semantic_role is in schema
import json as j
schema_str = j.dumps(schema)
print('semantic_role in schema:', schema_str.count('semantic_role'))
print('additionalProperties in schema:', schema_str.count('additionalProperties'))

try:
    import jsonschema
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    print(f'Schema errors: {len(errors)}')
    for e in errors[:5]:
        path = list(e.absolute_path)
        print(f'  path={path}: {e.message[:200]}')
except Exception as ex:
    print('Validation exception:', ex)
