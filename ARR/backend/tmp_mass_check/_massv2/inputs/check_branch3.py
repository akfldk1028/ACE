import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib
from jsonschema import Draft7Validator

schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

with open('book-comp19.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

# Extract the failing book_branch nodes
prog3_node4 = payload['programs'][3]['nodes'][4]  # p04 book_branch
prog8_node4 = payload['programs'][8]['nodes'][4]  # p09 book_branch
prog11_node3 = payload['programs'][11]['nodes'][3]  # p12 book_branch1

print("P04 book_branch node:")
print(json.dumps(prog3_node4, indent=2))
print()
print("P12 book_branch1 node:")
print(json.dumps(prog11_node3, indent=2))

# Validate each against the anyOf schema
prog_items = schema['properties']['programs']['items']
nodes_items = prog_items['properties']['nodes']['items']
any_of = nodes_items['anyOf']

# Find book_branch branch
book_branch_schema = None
for branch in any_of:
    op_enum = branch.get('properties', {}).get('operator', {}).get('enum', ['?'])
    if op_enum[0] == 'book_branch':
        book_branch_schema = branch
        break

print("\nValidating P04 book_branch against its schema branch:")
v = Draft7Validator(book_branch_schema)
errors = list(v.iter_errors(prog3_node4))
print(f"Errors: {len(errors)}")
for e in errors:
    print(f"  PATH: {list(e.absolute_path)}, MSG: {e.message[:200]}")

print("\nValidating P12 book_branch1 against its schema branch:")
v = Draft7Validator(book_branch_schema)
errors = list(v.iter_errors(prog11_node3))
print(f"Errors: {len(errors)}")
for e in errors:
    print(f"  PATH: {list(e.absolute_path)}, MSG: {e.message[:200]}")

# Now check against the full nodes anyOf schema
print("\nValidating P04 book_branch against full nodes anyOf schema:")
v = Draft7Validator(nodes_items)
errors = list(v.iter_errors(prog3_node4))
print(f"Errors: {len(errors)}")
for e in errors:
    print(f"  PATH: {list(e.absolute_path)}, MSG: {e.message[:100]}")
