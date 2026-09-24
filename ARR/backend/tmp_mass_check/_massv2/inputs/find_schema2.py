import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib

schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

# Navigate the schema structure to find what operators are allowed
# The schema has programs -> items -> nodes -> items -> anyOf
prog_items = schema['properties']['programs']['items']
nodes_items = prog_items['properties']['nodes']['items']
# nodes is anyOf list of different node types
any_of = nodes_items['anyOf']
print(f"Number of anyOf branches: {len(any_of)}")
print()

# Each branch has operator enum
for i, branch in enumerate(any_of):
    kind = branch.get('properties', {}).get('kind', {}).get('enum', ['?'])
    op_enum = branch.get('properties', {}).get('operator', {}).get('enum', ['?'])
    params = branch.get('properties', {}).get('parameters', {})
    params_min = params.get('minItems', '?')
    params_max = params.get('maxItems', '?')
    print(f"[{i}] kind={kind}, op={op_enum}, params min={params_min} max={params_max}")
