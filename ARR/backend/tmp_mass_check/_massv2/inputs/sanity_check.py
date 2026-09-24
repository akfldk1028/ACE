import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json'))

# Final validation
v = Draft7Validator(schema)
errors = list(v.iter_errors(data))
print(f"=== FINAL VALIDATION ===")
print(f"Programs: {len(data['programs'])}")
print(f"Schema errors: {len(errors)}")

# Check flat matrix4 values
flat_m4 = 0
for prog in data['programs']:
    for node in prog.get('nodes', []):
        for p in node.get('parameters', []):
            if p.get('name') == 'matrix4' and isinstance(p.get('matrix4_value'), list):
                mv = p['matrix4_value']
                if len(mv) == 16 and all(isinstance(x, (int, float)) for x in mv):
                    flat_m4 += 1
print(f"Flat matrix4_value (should be 0): {flat_m4}")

# Check literal value_type
literal_vt = 0
for prog in data['programs']:
    for node in prog.get('nodes', []):
        for p in node.get('parameters', []):
            if p.get('value_type') == 'literal':
                literal_vt += 1
print(f"value_type='literal' (should be 0): {literal_vt}")

# Check structured_json as object
sj_obj = 0
for prog in data['programs']:
    for node in prog.get('nodes', []):
        for p in node.get('parameters', []):
            if 'structured_json' in p and not isinstance(p['structured_json'], str):
                sj_obj += 1
print(f"structured_json not string (should be 0): {sj_obj}")

# Check wrong kinds
wrong_kinds_ops = {'bend', 'taper', 'twist', 'pinch', 'inflate', 'ellipsoidize', 'shear', 'mirror_array'}
wrong_k = 0
for prog in data['programs']:
    for node in prog.get('nodes', []):
        op = node.get('operator', '')
        kind = node.get('kind', '')
        if op == 'bend' and kind != 'modifier': wrong_k += 1
        elif op == 'shear' and kind != 'transform': wrong_k += 1
        elif op == 'mirror_array' and kind != 'pattern': wrong_k += 1
        elif op in {'taper','twist','pinch','inflate','ellipsoidize'} and kind != 'modifier': wrong_k += 1
print(f"Wrong kind values (should be 0): {wrong_k}")

# Unique path IDs
path_ids = set()
dupe_paths = []
for prog in data['programs']:
    pid = prog.get('book_composition_path_id', '')
    if pid in path_ids:
        dupe_paths.append(pid[:40])
    path_ids.add(pid)
print(f"Unique path IDs: {len(path_ids)} (out of 120)")
if dupe_paths:
    print(f"  Duplicate paths: {dupe_paths[:5]}")

# Base seeds distribution
seeds = {}
for prog in data['programs']:
    s = prog.get('base_seed', '?')
    seeds[s] = seeds.get(s, 0) + 1
print(f"Base seed distribution: {seeds}")

print("\nAll checks passed!" if errors == 0 and flat_m4 == 0 and literal_vt == 0 and sj_obj == 0 and wrong_k == 0 else "\nSOME CHECKS FAILED!")
