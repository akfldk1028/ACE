import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator, exceptions, ErrorTree

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))

# Test a single matrix4 node in isolation
matrix4_node = data['programs'][0]['nodes'][2]
node_schema = schema['properties']['programs']['items']['properties']['nodes']['items']

validator = Draft7Validator(node_schema)
errors = list(validator.iter_errors(matrix4_node))
print(f"matrix4 node errors: {len(errors)}")
for err in errors:
    print(f"  path={list(err.path)}: {err.message[:150]}")

print("\n--- Testing book_branch node ---")
branch_node = data['programs'][3]['nodes'][3]
print(f"book_branch node: {json.dumps(branch_node, indent=2)[:400]}")
errors = list(validator.iter_errors(branch_node))
print(f"book_branch node errors: {len(errors)}")
for err in errors:
    all_ctx = []
    e = err
    while e.context:
        all_ctx.append(e.context[0].message[:80])
        e = e.context[0]
    print(f"  path={list(err.path)}: {err.message[:100]}")
    for c in all_ctx:
        print(f"    ctx: {c}")

print("\n--- Testing lift node ---")
lift_node = data['programs'][3]['nodes'][5]
print(f"lift node: {json.dumps(lift_node, indent=2)[:400]}")
errors = list(validator.iter_errors(lift_node))
print(f"lift node errors: {len(errors)}")
for err in errors:
    print(f"  path={list(err.path)}: {err.message[:150]}")
