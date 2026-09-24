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

# Find book_branch schema
for i, branch in enumerate(any_of):
    op_enum = branch.get('properties', {}).get('operator', {}).get('enum', ['?'])
    if op_enum[0] == 'book_branch':
        print(f"book_branch branch index: {i}")
        print(f"Required: {branch.get('required', [])}")
        print()
        params = branch['properties']['parameters']
        items = params.get('items', {})
        print(f"Params: minItems={params.get('minItems')}, maxItems={params.get('maxItems')}")
        print()
        for j, pi in enumerate(items.get('anyOf', [])):
            req = pi.get('required', [])
            props = pi.get('properties', {})
            name_enum = props.get('name', {}).get('enum', ['?'])
            vt = props.get('value_type', {})
            print(f"  param[{j}]: required={req}")
            print(f"    name: {name_enum}")
            print(f"    value_type: {json.dumps(vt)[:200]}")
            # Show all properties
            for pname, pval in props.items():
                if pname not in ('name', 'value_type'):
                    print(f"    {pname}: {json.dumps(pval)[:100]}")
            print()
        break

print()
print("Now test if a valid book_branch node passes validation:")
# Test with the exact structure from schema
test_payload = {
    "programs": [{
        "name": "test",
        "base_form_id": "cube",
        "base_seed": "bar",
        "book_composition_path_id": "book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e",
        "intent_tags": [],
        "rationale": "test",
        "dimensional_intent": None,
        "root_id": "acc",
        "nodes": [
            {"id":"b0","kind":"primitive","operator":"box","inputs":[],
             "parameters":[{"name":"width","value_type":"number","numeric_value":1.0},{"name":"depth","value_type":"number","numeric_value":1.0},{"name":"height","value_type":"number","numeric_value":1.0},{"name":"center","value_type":"boolean","boolean_value":True}],
             "semantic_role":"dominant_mass"},
            {"id":"s0","kind":"transform","operator":"scale","inputs":["b0"],
             "parameters":[{"name":"vector","value_type":"vector","vector_value":[2.8,0.62,0.48]}],
             "semantic_role":"dominant_mass"},
            {"id":"m0","kind":"transform","operator":"matrix4","inputs":["s0"],
             "parameters":[{"name":"matrix4","value_type":"matrix4","matrix4_value":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}],
             "semantic_role":"dominant_mass"},
            # Test book_branch with just angle_degrees
            {"id":"brn","kind":"macro","operator":"book_branch","inputs":["m0"],
             "parameters":[{"name":"angle_degrees","value_type":"number","numeric_value":90.0}],
             "semantic_role":"dominant_mass"},
            {"id":"acc","kind":"macro","operator":"notch","inputs":["brn"],
             "parameters":[{"name":"side","value_type":"string","string_value":"east"},
                           {"name":"ratio","value_type":"number","numeric_value":0.22}],
             "semantic_role":"public_threshold"},
        ]
    }],
    "book_principle_ids": ["book:combination:16:bend+branch"]
}
v = Draft7Validator(schema)
errors = list(v.iter_errors(test_payload))
print(f"Test errors: {len(errors)}")
for e in errors:
    print(f"  PATH: {list(e.absolute_path)}")
    print(f"  MSG: {e.message[:200]}")
