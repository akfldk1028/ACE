import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib
from jsonschema import Draft7Validator

schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

# Check what's in parameters items for interlock_related (branch 58)
prog_items = schema['properties']['programs']['items']
nodes_items = prog_items['properties']['nodes']['items']
any_of = nodes_items['anyOf']

# Find interlock_related
for i, branch in enumerate(any_of):
    op_enum = branch.get('properties', {}).get('operator', {}).get('enum', ['?'])
    if op_enum[0] in ['interlock_related', 'book_branch', 'inflate', 'boundary_expand', 
                       'overlap_related', 'shear', 'book_split', 'lift', 'split_wing', 'book_fracture']:
        op = op_enum[0]
        params = branch.get('properties', {}).get('parameters', {})
        items = params.get('items', {})
        required = branch.get('required', [])
        print(f"\n=== {op} ===")
        print(f"Branch required: {required}")
        # Check inputs
        inputs = branch.get('properties', {}).get('inputs', {})
        print(f"Inputs: minItems={inputs.get('minItems')}, maxItems={inputs.get('maxItems')}")
        # Check params structure
        if 'anyOf' in items:
            print(f"Parameters anyOf count: {len(items['anyOf'])}")
            for j, pi in enumerate(items['anyOf'][:3]):
                req = pi.get('required', [])
                props = pi.get('properties', {})
                name_enum = props.get('name', {}).get('enum', ['?'])
                vt_enum = props.get('value_type', {}).get('enum', ['?'])
                print(f"  param[{j}]: required={req}, name={name_enum}, value_type={vt_enum}")
        else:
            print(f"Parameters items: {json.dumps(items)[:300]}")
