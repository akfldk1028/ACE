import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib
from jsonschema import Draft7Validator

schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

# Test with full literal format for arm_ratio and trunk_ratio
# arm_ratio schema: required=['name', 'value_type', 'numeric_value', 'string_value', 'boolean_value', 'vector_value', 'structured_json']
# The structured_json field type must be "string" (not null/object)

# Test: arm_ratio with structured_json as "null" string
arm_ratio_test = {
    "name": "arm_ratio",
    "value_type": "number",
    "numeric_value": 0.42,
    "string_value": "",
    "boolean_value": False,
    "vector_value": [],
    "structured_json": "null"   # STRING "null"
}

# Validate just the parameter
prog_items = schema['properties']['programs']['items']
nodes_items = prog_items['properties']['nodes']['items']
any_of = nodes_items['anyOf']
for branch in any_of:
    op_enum = branch.get('properties', {}).get('operator', {}).get('enum', ['?'])
    if op_enum[0] == 'book_branch':
        param_schema = branch['properties']['parameters']['items']['anyOf'][1]  # arm_ratio
        v = Draft7Validator(param_schema)
        errors = list(v.iter_errors(arm_ratio_test))
        print(f"arm_ratio errors: {len(errors)}")
        for e in errors:
            print(f"  {e.message}")
        break

# Also test the full node:
test_node = {
    "id": "brn",
    "kind": "macro",
    "operator": "book_branch",
    "inputs": ["m0"],
    "parameters": [
        {"name": "angle_degrees", "value_type": "number", "numeric_value": 90.0},
        {"name": "arm_ratio", "value_type": "number", "numeric_value": 0.42,
         "string_value": "", "boolean_value": False, "vector_value": [], "structured_json": "null"},
        {"name": "trunk_ratio", "value_type": "number", "numeric_value": 0.58,
         "string_value": "", "boolean_value": False, "vector_value": [], "structured_json": "null"},
        {"name": "vertical_anchor", "value_type": "string", "string_value": "input_base"},
    ],
    "semantic_role": "dominant_mass"
}

for branch in any_of:
    op_enum = branch.get('properties', {}).get('operator', {}).get('enum', ['?'])
    if op_enum[0] == 'book_branch':
        v = Draft7Validator(branch)
        errors = list(v.iter_errors(test_node))
        print(f"\nbook_branch node errors: {len(errors)}")
        for e in errors:
            print(f"  PATH: {list(e.absolute_path)}")
            print(f"  MSG: {e.message[:200]}")
        break
