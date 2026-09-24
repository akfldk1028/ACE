import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator, exceptions

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))

# Check matrix4 schema requirement
node_schema = schema['properties']['programs']['items']['properties']['nodes']['items']['anyOf']
matrix4_branch = None
for b in node_schema:
    if b['properties']['operator']['enum'][0] == 'matrix4':
        matrix4_branch = b
        break

print("matrix4 branch params:")
print(json.dumps(matrix4_branch['properties']['parameters'], indent=2)[:2000])

# Check the actual matrix4 value in the INVALID file
prog0 = data['programs'][0]
for node in prog0['nodes']:
    if node['operator'] == 'matrix4':
        print("\nActual matrix4 node:")
        print(json.dumps(node, indent=2)[:500])
