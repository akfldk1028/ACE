import json, sys, copy
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

INVALID_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json"
SCHEMA_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json"
IDENTITY_4X4 = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

schema = json.load(open(SCHEMA_PATH, encoding='utf-8'))
data = json.load(open(INVALID_PATH, encoding='utf-8'))

def fix_node(node):
    node = copy.deepcopy(node)
    for param in node.get('parameters', []):
        if param.get('value_type') == 'matrix4':
            mv = param.get('matrix4_value', [])
            if isinstance(mv, list) and len(mv) == 16 and not isinstance(mv[0], list):
                param['matrix4_value'] = [mv[0:4], mv[4:8], mv[8:12], mv[12:16]]
        if param.get('value_type') == 'literal':
            param['value_type'] = 'number'
    return node

# Test book_fracture node after fix
prog1 = data['programs'][1]
node3 = fix_node(prog1['nodes'][3])
print(f"book_fracture node (fixed):")
print(json.dumps(node3, indent=2))

# Validate against node schema
node_schema = schema['properties']['programs']['items']['properties']['nodes']['items']
validator = Draft7Validator(node_schema)
errors = list(validator.iter_errors(node3))
print(f"\nErrors for book_fracture after fix: {len(errors)}")
for err in errors:
    print(f"  path={list(err.path)}: {err.message[:150]}")
    for ctx in err.context:
        print(f"    ctx: {ctx.message[:100]}")
