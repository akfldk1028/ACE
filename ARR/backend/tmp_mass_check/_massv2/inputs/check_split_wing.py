import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib
from jsonschema import Draft7Validator

schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

prog_items = schema['properties']['programs']['items']
nodes_items = prog_items['properties']['nodes']['items']
any_of = nodes_items['anyOf']

for branch in any_of:
    op_enum = branch.get('properties', {}).get('operator', {}).get('enum', ['?'])
    if op_enum[0] == 'split_wing':
        params = branch['properties']['parameters']
        items = params.get('items', {})
        print("split_wing params anyOf:")
        for j, pi in enumerate(items.get('anyOf', [])):
            req = pi.get('required', [])
            props = pi.get('properties', {})
            name_enum = props.get('name', {}).get('enum', ['?'])
            vt_enum = props.get('value_type', {}).get('enum', ['?'])
            add_props = pi.get('additionalProperties', True)
            print(f"  [{j}] name={name_enum}, value_type={vt_enum}, required={req}, additionalProperties={add_props}")
        break

# Also check the specific param that fails (access_side)
print()
print("Testing split_wing with exact params:")
test_sw_node = {
    "id": "sw",
    "kind": "macro",
    "operator": "split_wing",
    "inputs": ["m0"],
    "parameters": [
        {"name": "access_side", "value_type": "string", "string_value": "east"},
        {"name": "axis", "value_type": "string", "string_value": "x"},
        {"name": "bridge", "value_type": "boolean", "boolean_value": True},
        {"name": "connector_width_ratio", "value_type": "number", "numeric_value": 0.22,
         "string_value": "", "boolean_value": False, "vector_value": [], "structured_json": "null"},
        {"name": "gap_ratio", "value_type": "number", "numeric_value": 0.12},
        {"name": "ground_spine", "value_type": "boolean", "boolean_value": False},
        {"name": "height_ratio", "value_type": "number", "numeric_value": 0.95,
         "string_value": "", "boolean_value": False, "vector_value": [], "structured_json": "null"},
        {"name": "layout", "value_type": "string", "string_value": "parallel"},
    ],
    "semantic_role": "dominant_mass"
}

for branch in any_of:
    op_enum = branch.get('properties', {}).get('operator', {}).get('enum', ['?'])
    if op_enum[0] == 'split_wing':
        v = Draft7Validator(branch)
        errors = list(v.iter_errors(test_sw_node))
        print(f"split_wing node errors: {len(errors)}")
        for e in errors:
            ctx = list(e.context) if hasattr(e, 'context') else []
            if ctx:
                for c in ctx[:3]:
                    print(f"  SUBPATH: {list(c.absolute_path)}, MSG: {c.message[:150]}")
            else:
                print(f"  PATH: {list(e.absolute_path)}, MSG: {e.message[:150]}")
        break
