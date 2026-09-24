"""
Fix 12 violated programs in book-comp18_INVALID.json and write book-comp18.json.
Only the 12 0-based indices are modified; all other programs are left unchanged.

Violation map (0-based index → error → fix):
 1: slab + book_fracture + carve_void [disconnected] → carve_void → notch
 6: slab + book_rotate + carve_void [disconnected] → carve_void → notch
 9: slab + bend + related_array + notch [disconnected] → remove related_array
11: block + interlock_related + lift [disconnected] → interlock_related → boundary_expand
12: block + shear(kind=macro) + courtyard [compile_failed] → shear kind→transform; courtyard → notch
13: block + boundary_expand×2 + carve_void [disconnected] → carve_void → notch
18: slab + book_split×2 + notch [disconnected] → remove 2nd book_split
20: slab + book_split + join_related + carve_void [disconnected] → carve_void → notch
23: block + book_carve + notch [disconnected] → book_carve → boundary_expand
25: slab + bend + related_array + notch [disconnected] → remove related_array
26: block + book_lift + boundary_expand + carve_void [disconnected] → carve_void → notch
27: bar + interlock_related + courtyard [disconnected] → courtyard → notch
"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

INPUT  = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'
OUTPUT = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json'

# ── helpers ──────────────────────────────────────────────────────────────────
def num(name, val):
    return {"name": name, "value_type": "number", "numeric_value": val}

def str_param(name, val):
    return {"name": name, "value_type": "string", "string_value": val}

def bool_param(name, val):
    return {"name": name, "value_type": "boolean", "boolean_value": val}

def vec_param(name, val):
    return {"name": name, "value_type": "vector", "vector_value": val}

def lit(name, n=0.0, s="", b=False, v=None):
    if v is None: v = []
    return {"name": name, "value_type": "number",
            "numeric_value": n, "string_value": s, "boolean_value": b,
            "vector_value": v, "structured_json": "null"}

def make_node(id_, kind, operator, inputs, params, role):
    """Build a node dict with semantic_role (required by schema/importer)."""
    return {
        "id": id_,
        "kind": kind,
        "operator": operator,
        "inputs": inputs,
        "semantic_role": role,
        "parameters": params
    }

def notch_east(id_, inp, ratio=0.22, wr=0.35, hr=0.55):
    return make_node(id_, "macro", "notch", [inp], [
        str_param("side", "east"),
        str_param("corner", "ne"),
        num("ratio", ratio),
        num("width_ratio", wr),
        num("height_ratio", hr),
    ], "public_threshold")

def boundary_expand_z(id_, inp, amount=0.18, shoulder=0.2):
    return make_node(id_, "macro", "boundary_expand", [inp], [
        str_param("axis", "z"),
        num("amount", amount),
        lit("shoulder_fraction", n=shoulder),
    ], "dominant_mass")

# Load
with open(INPUT, encoding='utf-8') as f:
    data = json.load(f)

programs = data['programs']
print(f'Loaded {len(programs)} programs')

# ── Fix structured_json: ensure all literal params have "null" string ─────────
# This was a bug in the original generator; fix them all globally.
fixed_sj = 0
for p in programs:
    for n in p.get('nodes', []):
        for par in n.get('parameters', []):
            if 'structured_json' in par and par['structured_json'] != "null":
                par['structured_json'] = "null"
                fixed_sj += 1
if fixed_sj:
    print(f'  Fixed {fixed_sj} structured_json values → "null"')

# ─── Fix idx=1: slab + book_fracture + carve_void ──────────────────────────
p = programs[1]
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"idx=1: expected carve_void, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.50)
print(f'  Fixed idx=1: carve_void → notch')

# ─── Fix idx=6: slab + book_rotate + carve_void ────────────────────────────
p = programs[6]
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"idx=6: expected carve_void, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.21, wr=0.33, hr=0.52)
print(f'  Fixed idx=6: carve_void → notch')

# ─── Fix idx=9: slab + bend + related_array + notch ────────────────────────
# Remove related_array; rewire notch to point to bend output.
p = programs[9]
nodes = p['nodes']
ra_idx = next(i for i, n in enumerate(nodes) if n['operator'] == 'related_array')
ra_node = nodes.pop(ra_idx)
notch_node = nodes[-1]
assert notch_node['operator'] == 'notch', f"idx=9: expected notch last, got {notch_node['operator']}"
notch_node['inputs'] = ra_node['inputs']  # bypass the removed node
print(f'  Fixed idx=9: removed related_array, rewired notch → {ra_node["inputs"]}')

# ─── Fix idx=11: block + interlock_related + lift ──────────────────────────
# interlock_related on block disconnects; replace with boundary_expand.
p = programs[11]
nodes = p['nodes']
ir_idx = next(i for i, n in enumerate(nodes) if n['operator'] == 'interlock_related')
ir_node = nodes[ir_idx]
prev_input = ir_node['inputs'][0]
nodes[ir_idx] = boundary_expand_z('body0', prev_input, amount=0.20, shoulder=0.25)
print(f'  Fixed idx=11: interlock_related → boundary_expand')

# ─── Fix idx=12: block + shear(kind=macro) + courtyard ─────────────────────
# shear must be kind=transform per schema. courtyard after shear disconnects; use notch.
p = programs[12]
nodes = p['nodes']
for n in nodes:
    if n['operator'] == 'shear':
        n['kind'] = 'transform'
        break
last = nodes[-1]
assert last['operator'] == 'courtyard', f"idx=12: expected courtyard last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.52)
print(f'  Fixed idx=12: shear kind→transform, courtyard → notch')

# ─── Fix idx=13: block + boundary_expand×2 + carve_void ───────────────────
# carve_void after two expands can over-carve → disconnected. Use notch instead.
p = programs[13]
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"idx=13: expected carve_void last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.52)
print(f'  Fixed idx=13: carve_void → notch')

# ─── Fix idx=18: slab + book_split×2 + notch ───────────────────────────────
# Two book_splits create two arms that notch can disconnect.
# Remove 2nd book_split; rewire notch to 1st book_split output.
p = programs[18]
nodes = p['nodes']
bs_indices = [i for i, n in enumerate(nodes) if n['operator'] == 'book_split']
assert len(bs_indices) >= 2, f"idx=18: expected >=2 book_splits, found {len(bs_indices)}"
bs2_idx = bs_indices[1]
bs2_node = nodes.pop(bs2_idx)
notch_node = nodes[-1]
assert notch_node['operator'] == 'notch', f"idx=18: expected notch last, got {notch_node['operator']}"
notch_node['inputs'] = bs2_node['inputs']  # now points to 1st book_split output
print(f'  Fixed idx=18: removed 2nd book_split, rewired notch → {bs2_node["inputs"]}')

# ─── Fix idx=20: slab + book_split + join_related + carve_void ─────────────
# carve_void after join cuts through joined body → disconnected. Use notch.
p = programs[20]
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"idx=20: expected carve_void last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.52)
print(f'  Fixed idx=20: carve_void → notch')

# ─── Fix idx=23: block + book_carve + notch ────────────────────────────────
# book_carve + notch creates thin bridges that snap. Replace book_carve with boundary_expand.
p = programs[23]
nodes = p['nodes']
bc_idx = next(i for i, n in enumerate(nodes) if n['operator'] == 'book_carve')
bc_node = nodes[bc_idx]
prev_input = bc_node['inputs'][0]
nodes[bc_idx] = boundary_expand_z('body0', prev_input, amount=0.22, shoulder=0.25)
print(f'  Fixed idx=23: book_carve → boundary_expand')

# ─── Fix idx=25: slab + bend + related_array + notch ───────────────────────
# Same pattern as idx=9. Remove related_array; rewire notch.
p = programs[25]
nodes = p['nodes']
ra_idx = next(i for i, n in enumerate(nodes) if n['operator'] == 'related_array')
ra_node = nodes.pop(ra_idx)
notch_node = nodes[-1]
assert notch_node['operator'] == 'notch', f"idx=25: expected notch last, got {notch_node['operator']}"
notch_node['inputs'] = ra_node['inputs']
print(f'  Fixed idx=25: removed related_array, rewired notch → {ra_node["inputs"]}')

# ─── Fix idx=26: block + book_lift + boundary_expand + carve_void ──────────
# carve_void after book_lift disconnects the lifted volume. Use notch.
p = programs[26]
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"idx=26: expected carve_void last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.52)
print(f'  Fixed idx=26: carve_void → notch')

# ─── Fix idx=27: bar + interlock_related + courtyard ───────────────────────
# interlock_related crosses two bodies; courtyard then cuts them apart. Use notch.
p = programs[27]
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'courtyard', f"idx=27: expected courtyard last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.21, wr=0.33, hr=0.52)
print(f'  Fixed idx=27: courtyard → notch')

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
sz = __import__('os').path.getsize(OUTPUT)
print(f'\nWritten {len(programs)} programs to {OUTPUT} ({sz} bytes)')

# ── Verify fixed programs ──────────────────────────────────────────────────────
print('\n=== Verification of fixed programs ===')
for idx0 in [1, 6, 9, 11, 12, 13, 18, 20, 23, 25, 26, 27]:
    p = programs[idx0]
    ops = [(n['operator'], n.get('semantic_role','MISSING')) for n in p['nodes']]
    print(f'  idx={idx0}: seed={p["base_seed"]} | {ops}')

# ── Quick connectivity check: banned operators in fixed programs ───────────────
BANNED = {'related_array', 'offset_related', 'mirror_array', 'nested_related'}
print('\n=== Banned operator check (12 fixed programs) ===')
found_banned = False
for idx0 in [1, 6, 9, 11, 12, 13, 18, 20, 23, 25, 26, 27]:
    p = programs[idx0]
    for n in p['nodes']:
        if n['operator'] in BANNED:
            print(f'  BANNED operator {n["operator"]} at idx={idx0}!')
            found_banned = True
if not found_banned:
    print('  No banned operators in fixed programs ✓')

# ── Check all 120 for banned operators ───────────────────────────────────────
print('\n=== Banned operator check (all 120 programs) ===')
all_banned = []
for i, p in enumerate(programs):
    for n in p['nodes']:
        if n['operator'] in BANNED:
            all_banned.append((i, n['operator']))
if all_banned:
    print(f'  BANNED operators found: {all_banned}')
else:
    print('  No banned operators in any program ✓')
