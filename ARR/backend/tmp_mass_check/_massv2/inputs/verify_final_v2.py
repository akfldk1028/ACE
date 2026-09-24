import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

SCHEMA_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json"
OUTPUT_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json"

schema = json.load(open(SCHEMA_PATH, encoding='utf-8'))
data = json.load(open(OUTPUT_PATH, encoding='utf-8'))

# Basic checks
progs = data['programs']
print(f"Programs: {len(progs)}")
print(f"book_principle_ids at root: {len(data.get('book_principle_ids', []))}")

# No programs should have book_principle_ids
has_prog_bpi = [p['name'] for p in progs if 'book_principle_ids' in p]
print(f"Programs with book_principle_ids (should be 0): {has_prog_bpi}")

# Schema validation
validator = Draft7Validator(schema)
errors = list(validator.iter_errors(data))
print(f"Schema errors: {len(errors)}")

# Check kinds
kind_counts = {}
for p in progs:
    for n in p['nodes']:
        op = n['operator']
        kind = n['kind']
        kind_counts[(op, kind)] = kind_counts.get((op, kind), 0) + 1

# Show operators with unexpected kinds
bad_kinds = [(op, kind, cnt) for (op, kind), cnt in kind_counts.items()
             if (op == 'bend' and kind != 'modifier') or
                (op == 'shear' and kind != 'transform') or
                (op == 'mirror_array' and kind != 'pattern') or
                (op in ['taper','twist','pinch','inflate','ellipsoidize'] and kind != 'modifier')]
print(f"\nOperators with unexpected kinds: {bad_kinds}")

# Check structured_json fields
bad_sj = []
for pi, p in enumerate(progs):
    for ni, n in enumerate(p['nodes']):
        for param in n.get('parameters', []):
            if 'structured_json' in param:
                sj = param['structured_json']
                if not isinstance(sj, str):
                    bad_sj.append((pi, ni, param['name'], type(sj).__name__))
print(f"Params with non-string structured_json: {bad_sj[:10]}")

# Check matrix4_value flat
bad_m4 = []
for pi, p in enumerate(progs):
    for ni, n in enumerate(p['nodes']):
        for param in n.get('parameters', []):
            if param.get('value_type') == 'matrix4':
                mv = param.get('matrix4_value', [])
                if isinstance(mv, list) and len(mv) > 0 and not isinstance(mv[0], list):
                    bad_m4.append((pi, ni))
print(f"Nodes with flat matrix4_value: {bad_m4[:10]}")

# Check no 'literal' value_type
bad_vt = []
for pi, p in enumerate(progs):
    for ni, n in enumerate(p['nodes']):
        for param in n.get('parameters', []):
            if param.get('value_type') == 'literal':
                bad_vt.append((pi, ni, param['name']))
print(f"Params with value_type='literal': {bad_vt[:10]}")

print("\nAll checks passed!" if not (errors or has_prog_bpi or bad_kinds or bad_sj or bad_m4 or bad_vt) else "SOME CHECKS FAILED")
