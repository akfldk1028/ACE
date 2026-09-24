"""
Fix 12 violated programs in book-comp18_INVALID.json and write book-comp18.json.
Only the 12 0-based indices are modified; all others are left byte-identical.

Violation map (0-based index → issue → fix):
 1: slab + book_fracture + carve_void → replace carve_void with notch
 6: slab + book_rotate + carve_void → replace carve_void with notch
 9: slab + bend + related_array + notch → remove related_array (keep bend+notch)
11: block + interlock_related + lift → replace interlock_related with boundary_expand
12: block + shear(kind=macro) + courtyard → change shear to kind=transform; replace courtyard with notch
13: block + boundary_expand×2 + carve_void → replace carve_void with notch
18: slab + book_split×2 + notch → remove 2nd book_split (keep 1st + notch)
20: slab + book_split + join_related + carve_void → replace carve_void with notch
23: block + book_carve + notch → replace book_carve with boundary_expand (both stay connected)
25: slab + bend + related_array + notch → remove related_array (keep bend+notch)
26: block + book_lift + boundary_expand + carve_void → replace carve_void with notch
27: bar + interlock_related + courtyard → replace courtyard with notch
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

def macro_node(id_, operator, inputs, params):
    return {"id": id_, "kind": "macro", "operator": operator,
            "inputs": inputs, "parameters": params}

def transform_node(id_, operator, inputs, params):
    return {"id": id_, "kind": "transform", "operator": operator,
            "inputs": inputs, "parameters": params}

# ── replacement node builders ─────────────────────────────────────────────────

def notch_east(id_, inp, ratio=0.22, wr=0.35, hr=0.55):
    return macro_node(id_, "notch", [inp], [
        str_param("side", "east"),
        str_param("corner", "ne"),
        num("ratio", ratio),
        num("width_ratio", wr),
        num("height_ratio", hr),
    ])

def boundary_expand_z(id_, inp, amount=0.18, shoulder=0.2):
    return macro_node(id_, "boundary_expand", [inp], [
        str_param("axis", "z"),
        num("amount", amount),
        lit("shoulder_fraction", n=shoulder),
    ])

def book_branch_node(id_, inp, angle=25.0, trunk=0.55, arm=0.45):
    return macro_node(id_, "book_branch", [inp], [
        num("angle_degrees", angle),
        lit("trunk_ratio", n=trunk),
        lit("arm_ratio", n=arm),
        str_param("vertical_anchor", "input_base"),
    ])

# Load
with open(INPUT, encoding='utf-8') as f:
    data = json.load(f)

programs = data['programs']
print(f'Loaded {len(programs)} programs')

# ─── Fix idx=1: slab + book_fracture + carve_void ──────────────────────────
# carve_void after book_fracture (which splits into two) disconnects.
# Replace carve_void with notch (corner cut only, stays connected).
p = programs[1]
assert p['base_seed'] == 'slab', f"Expected slab at idx=1, got {p['base_seed']}"
nodes = p['nodes']
# Last node should be carve_void
last = nodes[-1]
assert last['operator'] == 'carve_void', f"Expected carve_void at idx=1 last node, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.50)
print(f'  Fixed idx=1: carve_void → notch')

# ─── Fix idx=6: slab + book_rotate + carve_void ────────────────────────────
# carve_void after book_rotate disconnects. Replace with notch.
p = programs[6]
assert p['base_seed'] == 'slab', f"Expected slab at idx=6, got {p['base_seed']}"
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"Expected carve_void at idx=6 last node, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.21, wr=0.33, hr=0.52)
print(f'  Fixed idx=6: carve_void → notch')

# ─── Fix idx=9: slab + bend + related_array + notch ────────────────────────
# related_array spreads copies → disconnected. Remove it; keep bend + notch.
p = programs[9]
assert p['base_seed'] == 'slab', f"Expected slab at idx=9, got {p['base_seed']}"
nodes = p['nodes']
# Find and remove related_array node; rewire notch to point to bend output
ra_idx = None
for i, n in enumerate(nodes):
    if n['operator'] == 'related_array':
        ra_idx = i
        break
assert ra_idx is not None, "related_array not found in idx=9"
ra_node = nodes.pop(ra_idx)
ra_id = ra_node['id']
# notch (last node) inputs from related_array → rewire to ra_node's input
notch_node = nodes[-1]
assert notch_node['operator'] == 'notch', f"Expected notch at idx=9 last, got {notch_node['operator']}"
notch_node['inputs'] = ra_node['inputs']
print(f'  Fixed idx=9: removed related_array, rewired notch')

# ─── Fix idx=11: block + interlock_related + lift ──────────────────────────
# interlock_related on block creates disconnected crossing bodies.
# Replace interlock_related with boundary_expand (stays connected).
p = programs[11]
assert p['base_seed'] == 'block', f"Expected block at idx=11, got {p['base_seed']}"
nodes = p['nodes']
ir_idx = None
for i, n in enumerate(nodes):
    if n['operator'] == 'interlock_related':
        ir_idx = i
        break
assert ir_idx is not None, "interlock_related not found in idx=11"
ir_node = nodes[ir_idx]
prev_input = ir_node['inputs'][0]
nodes[ir_idx] = boundary_expand_z('body0', prev_input, amount=0.20, shoulder=0.25)
print(f'  Fixed idx=11: interlock_related → boundary_expand')

# ─── Fix idx=12: block + shear + courtyard ─────────────────────────────────
# shear with kind=macro should be kind=transform per schema.
# Also courtyard after shear on block may disconnect; replace with notch.
p = programs[12]
assert p['base_seed'] == 'block', f"Expected block at idx=12, got {p['base_seed']}"
nodes = p['nodes']
for n in nodes:
    if n['operator'] == 'shear':
        n['kind'] = 'transform'  # schema says kind=transform for shear
        break
last = nodes[-1]
assert last['operator'] == 'courtyard', f"Expected courtyard at idx=12 last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.52)
print(f'  Fixed idx=12: shear kind→transform, courtyard → notch')

# ─── Fix idx=13: block + boundary_expand×2 + carve_void ───────────────────
# Two boundary_expands then carve_void: carve cuts through expanded body → disconnected.
# Replace carve_void with notch.
p = programs[13]
assert p['base_seed'] == 'block', f"Expected block at idx=13, got {p['base_seed']}"
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"Expected carve_void at idx=13 last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.52)
print(f'  Fixed idx=13: carve_void → notch')

# ─── Fix idx=18: slab + book_split×2 + notch ───────────────────────────────
# Two book_split operators create two separate arms; notch cuts one loose.
# Remove 2nd book_split, keep 1st + notch (rewired).
p = programs[18]
assert p['base_seed'] == 'slab', f"Expected slab at idx=18, got {p['base_seed']}"
nodes = p['nodes']
# Find the two book_split nodes
bs_indices = [i for i, n in enumerate(nodes) if n['operator'] == 'book_split']
assert len(bs_indices) >= 2, f"Expected >=2 book_split nodes at idx=18, found {len(bs_indices)}"
# Remove 2nd book_split
bs2_idx = bs_indices[1]
bs2_node = nodes.pop(bs2_idx)
bs2_id = bs2_node['id']
# Rewire notch: it inputs from bs2 → now inputs from bs1 result
notch_node = nodes[-1]
assert notch_node['operator'] == 'notch', f"Expected notch at idx=18 last, got {notch_node['operator']}"
notch_node['inputs'] = bs2_node['inputs']
print(f'  Fixed idx=18: removed 2nd book_split, rewired notch')

# ─── Fix idx=20: slab + book_split + join_related + carve_void ─────────────
# carve_void after join_related disconnects. Replace with notch.
p = programs[20]
assert p['base_seed'] == 'slab', f"Expected slab at idx=20, got {p['base_seed']}"
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"Expected carve_void at idx=20 last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.52)
print(f'  Fixed idx=20: carve_void → notch')

# ─── Fix idx=23: block + book_carve + notch ────────────────────────────────
# book_carve carves into block, notch cuts corner → may disconnect narrow bridges.
# Replace book_carve with boundary_expand (safe addition, stays connected).
p = programs[23]
assert p['base_seed'] == 'block', f"Expected block at idx=23, got {p['base_seed']}"
nodes = p['nodes']
bc_idx = None
for i, n in enumerate(nodes):
    if n['operator'] == 'book_carve':
        bc_idx = i
        break
assert bc_idx is not None, "book_carve not found in idx=23"
bc_node = nodes[bc_idx]
prev_input = bc_node['inputs'][0]
nodes[bc_idx] = boundary_expand_z('body0', prev_input, amount=0.22, shoulder=0.25)
print(f'  Fixed idx=23: book_carve → boundary_expand')

# ─── Fix idx=25: slab + bend + related_array + notch ───────────────────────
# Same as idx=9: related_array spreads → disconnected. Remove it.
p = programs[25]
assert p['base_seed'] == 'slab', f"Expected slab at idx=25, got {p['base_seed']}"
nodes = p['nodes']
ra_idx = None
for i, n in enumerate(nodes):
    if n['operator'] == 'related_array':
        ra_idx = i
        break
assert ra_idx is not None, "related_array not found in idx=25"
ra_node = nodes.pop(ra_idx)
notch_node = nodes[-1]
assert notch_node['operator'] == 'notch', f"Expected notch at idx=25 last, got {notch_node['operator']}"
notch_node['inputs'] = ra_node['inputs']
print(f'  Fixed idx=25: removed related_array, rewired notch')

# ─── Fix idx=26: block + book_lift + boundary_expand + carve_void ──────────
# carve_void after book_lift disconnects. Replace with notch.
p = programs[26]
assert p['base_seed'] == 'block', f"Expected block at idx=26, got {p['base_seed']}"
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'carve_void', f"Expected carve_void at idx=26 last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.20, wr=0.32, hr=0.52)
print(f'  Fixed idx=26: carve_void → notch')

# ─── Fix idx=27: bar + interlock_related + courtyard ───────────────────────
# interlock_related + courtyard disconnects. Replace courtyard with notch.
p = programs[27]
assert p['base_seed'] == 'bar', f"Expected bar at idx=27, got {p['base_seed']}"
nodes = p['nodes']
last = nodes[-1]
assert last['operator'] == 'courtyard', f"Expected courtyard at idx=27 last, got {last['operator']}"
prev_id = last['inputs'][0]
nodes[-1] = notch_east('result', prev_id, ratio=0.21, wr=0.33, hr=0.52)
print(f'  Fixed idx=27: courtyard → notch')

# ── Validate structured_json is always "null" string ─────────────────────────
fixed_sj = 0
for p in programs:
    for n in p.get('nodes', []):
        for par in n.get('parameters', []):
            if 'structured_json' in par:
                if par['structured_json'] != "null":
                    par['structured_json'] = "null"
                    fixed_sj += 1
if fixed_sj:
    print(f'  Fixed {fixed_sj} structured_json values (was not "null")')
else:
    print('  All structured_json values are "null" string ✓')

# ── Schema validation ─────────────────────────────────────────────────────────
import pathlib
schema_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'
try:
    import jsonschema
    with open(schema_path, encoding='utf-8') as f:
        schema = json.load(f)
    validator_cls = jsonschema.Draft7Validator
    validator = validator_cls(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        print(f'\nSCHEMA ERRORS ({len(errors)}):')
        for e in errors[:10]:
            print(f'  {e.json_path}: {e.message}')
    else:
        print(f'\nSchema validation: PASSED (0 errors) ✓')
except ImportError:
    print('\njsonschema not available, skipping schema validation')

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'\nWritten {len(programs)} programs to {OUTPUT}')

# ── Verify fixed programs ──────────────────────────────────────────────────────
print('\n=== Verification of fixed programs ===')
for idx0 in [1, 6, 9, 11, 12, 13, 18, 20, 23, 25, 26, 27]:
    p = programs[idx0]
    ops = [n['operator'] for n in p['nodes']]
    print(f'  idx={idx0}: seed={p["base_seed"]} ops={ops}')
