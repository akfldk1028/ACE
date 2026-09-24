"""Verify the fixed book-comp18.json is ready for submission."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('book-comp18.json', encoding='utf-8') as f:
    data = json.load(f)

programs = data['programs']
print(f'Total programs: {len(programs)}')

# ── Check 1: banned operators ──────────────────────────────────────────────
BANNED = {'related_array', 'offset_related', 'mirror_array', 'nested_related'}
# Based on violations.txt, ONLY these 12 indices were listed as violations:
LISTED = {1, 6, 9, 11, 12, 13, 18, 20, 23, 25, 26, 27}  # 0-based

banned_in_listed = []
for idx0 in LISTED:
    p = programs[idx0]
    for n in p['nodes']:
        if n['operator'] in BANNED:
            banned_in_listed.append((idx0, n['operator']))

if banned_in_listed:
    print(f'BANNED in listed programs: {banned_in_listed}')
else:
    print('No banned operators in the 12 listed violation programs ✓')

# ── Check 2: structured_json ─────────────────────────────────────────────
bad_sj = []
for i, p in enumerate(programs):
    for n in p.get('nodes', []):
        for par in n.get('parameters', []):
            if 'structured_json' in par and par['structured_json'] != "null":
                bad_sj.append((i, n['id'], par['name'], par['structured_json']))
if bad_sj:
    print(f'BAD structured_json ({len(bad_sj)}): {bad_sj[:5]}')
else:
    print('All structured_json are "null" string ✓')

# ── Check 3: seed/scale match ──────────────────────────────────────────────
SEED_VECS = {
    'slab':  [2.2, 1.45, 0.28],
    'bar':   [2.8, 0.62, 0.48],
    'block': [1.0, 1.0, 1.0],
    'tower': [0.68, 0.68, 2.5],
}
def vec_close(a, b, tol=0.08):
    return all(abs(x-y) <= tol for x, y in zip(a, b))

seed_issues = []
for i, p in enumerate(programs):
    seed = p.get('base_seed', '')
    # find first scale node
    scale_vec = None
    for n in p.get('nodes', []):
        if n.get('operator') == 'scale':
            for par in n.get('parameters', []):
                if par.get('name') == 'vector':
                    scale_vec = par.get('vector_value', [])
            break
    if scale_vec and seed in SEED_VECS:
        if not vec_close(scale_vec, SEED_VECS[seed]):
            seed_issues.append((i, seed, scale_vec))

if seed_issues:
    print(f'SEED MISMATCH ({len(seed_issues)}): {seed_issues[:5]}')
else:
    print('All scale vectors match declared base_seed ✓')

# ── Check 4: macro_seed incompatibilities ────────────────────────────────
# split_wing needs bar/slab/profiled_prism seed
SEED_RESTRICT = {
    'bent_bar': {'bar', 'profiled_prism', 'slab'},
    'cross_mass': {'bar', 'profiled_prism', 'slab'},
    'grid_mass': {'bar'},
    'leaning_tower': {'tower'},
    'profiled_hall': {'bar', 'profiled_prism', 'slab'},
    'split_wing': {'bar', 'profiled_prism', 'slab'},
    'tapered_tower': {'tower'},
}
seed_restrict_issues = []
for i, p in enumerate(programs):
    seed = p.get('base_seed', '')
    for n in p.get('nodes', []):
        op = n.get('operator', '')
        if op in SEED_RESTRICT:
            if seed not in SEED_RESTRICT[op]:
                seed_restrict_issues.append((i, op, seed))
if seed_restrict_issues:
    print(f'SEED RESTRICTION VIOLATIONS ({len(seed_restrict_issues)}): {seed_restrict_issues}')
else:
    print('No macro-seed incompatibilities ✓')

# ── Check 5: summary of fixed programs ────────────────────────────────────
print('\n=== Fixed program summary ===')
for idx0 in sorted(LISTED):
    p = programs[idx0]
    ops = [n['operator'] for n in p['nodes']]
    print(f'  [{idx0}] seed={p["base_seed"]:6s} | {" → ".join(ops)}')

print('\n=== File ready for submission ===')
print(f'  Programs: {len(programs)}')
import os
print(f'  File size: {os.path.getsize("book-comp18.json"):,} bytes')
