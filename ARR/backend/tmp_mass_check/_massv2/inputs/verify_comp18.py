import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json'))

print(f"Programs: {len(data['programs'])}")
print(f"Root-level keys: {list(data.keys())}")

# Check no program has book_principle_ids
prog_pids = [(i, p) for i, prog in enumerate(data['programs']) for p in [] if 'book_principle_ids' in prog]
print(f"Programs with book_principle_ids: {len(prog_pids)}")

# Check program 0 nodes
prog0 = data['programs'][0]
print(f"\nProgram 0 ({prog0['name']}):")
print(f"  base_seed: {prog0['base_seed']}")
print(f"  base_form_id: {prog0['base_form_id']}")
print(f"  book_composition_path_id: {prog0['book_composition_path_id'][:60]}")
print(f"  Nodes:")
for n in prog0['nodes']:
    print(f"    {n['id']}: op={n['operator']} kind={n['kind']}")
    for p in n['parameters']:
        vt = p.get('value_type')
        pval = p.get('numeric_value', p.get('string_value', p.get('boolean_value', p.get('vector_value', p.get('matrix4_value', '?')))))
        print(f"      param {p['name']} vtype={vt} val={str(pval)[:50]}")

# Validate schema
v = Draft7Validator(schema)
errors = list(v.iter_errors(data))
print(f"\nSchema validation errors: {len(errors)}")
if errors:
    for e in errors[:5]:
        print(f"  {list(e.path)}: {e.message[:200]}")

# Check root-level book_principle_ids
print(f"\nRoot book_principle_ids count: {len(data.get('book_principle_ids', []))}")
