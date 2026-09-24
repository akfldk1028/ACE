import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib
from jsonschema import Draft7Validator

# Load files
with open('book-comp19.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)
schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

# Validate
v = Draft7Validator(schema)
errors = list(v.iter_errors(payload))
print(f"Schema validation: {len(errors)} errors")

print()
print(f"Top-level keys: {list(payload.keys())}")
print(f"Program count: {len(payload['programs'])}")
print(f"book_principle_ids count: {len(payload['book_principle_ids'])}")
print(f"book_principle_ids: {payload['book_principle_ids']}")
print()

# Check per-program
seeds = {}
paths = set()
for i, p in enumerate(payload['programs']):
    name = p['name']
    seed = p['base_seed']
    path = p['book_composition_path_id']
    nodes = p['nodes']
    ops = [n['operator'] for n in nodes]
    form = p['base_form_id']
    di = p['dimensional_intent']
    
    if seed not in seeds:
        seeds[seed] = 0
    seeds[seed] += 1
    
    if path in paths:
        print(f"  DUPLICATE PATH: {path}")
    paths.add(path)
    
    print(f"[{i+1:02d}] {name}")
    print(f"      seed={seed}, form={form}, path_short=...{path[-16:]}")
    print(f"      ops={ops}")
    print(f"      di=storeys={di['storey_count'] if di else None}, gfa={di['target_gfa_m2'] if di else None}")
    print()

print(f"Seeds distribution: {seeds}")
print(f"Unique paths: {len(paths)}")
print(f"All paths unique: {len(paths) == len(payload['programs'])}")

# Check body rule budget
print()
print("Body rule budget check (max 2 body ops + 1 access):")
BODY_OPS = {'bend','taper','twist','pinch','inflate','shear','book_branch','book_fracture',
            'book_split','book_carve','book_extract','book_grade','book_lift','book_lodge',
            'book_notch','book_rotate','overlap_related','interlock_related','boundary_expand',
            'split_wing','profiled_hall'}
ACCESS_OPS = {'courtyard','carve_void','notch','lift','split_wing','book_notch'}
for i, p in enumerate(payload['programs']):
    nodes = p['nodes']
    body = [n['operator'] for n in nodes if n['operator'] in BODY_OPS and n['semantic_role'] == 'dominant_mass']
    access = [n['operator'] for n in nodes if n['semantic_role'] == 'public_threshold']
    if len(body) > 2:
        print(f"  [{i+1}] OVER BODY BUDGET: {body}")
    if len(access) > 1:
        print(f"  [{i+1}] OVER ACCESS BUDGET: {access}")
print("  Budget check done.")
