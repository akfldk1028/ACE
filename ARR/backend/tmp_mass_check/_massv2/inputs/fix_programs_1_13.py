"""
Fix programs 1 and 13 (1-based indices 1 and 13, 0-based 0 and 12) in book-comp18_INVALID.json.
Output: book-comp18.json

Issues in program 1 (index 0): box > scale > matrix4 > bend > courtyard
  1. bend kind='macro' should be 'modifier'
  2. matrix4_value is flat [16 ints] - must be nested [[4],[4],[4],[4]]
  3. bend + courtyard = disconnected mesh (importer error: disconnected_component_budget_exceeded)
  Fix: keep bend (fix kind), replace courtyard with setback (no disconnection)

Issues in program 13 (index 12): box > scale > matrix4 > shear > courtyard
  1. shear kind='macro' should be 'transform'
  2. matrix4_value flat - must be nested
  3. direction param has value_type='literal' (invalid) and structured_json={} (must be string "null")
  4. shear + courtyard = disconnected mesh
  Fix: fix shear kind+params, replace courtyard with setback
"""
import sys, json, copy
sys.stdout.reconfigure(encoding='utf-8')

src = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'
dst = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json'

with open(src, encoding='utf-8') as f:
    data = json.load(f)

progs = data['programs']
print(f'Total programs: {len(progs)}')

# Nested 4x4 identity matrix
IDENTITY4x4 = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

def fix_matrix4_node(node):
    """Fix flat matrix4_value to nested 4x4."""
    for p in node.get('parameters', []):
        if p.get('value_type') == 'matrix4' and 'matrix4_value' in p:
            mv = p['matrix4_value']
            # If flat list of 16 numbers, convert to 4x4
            if isinstance(mv, list) and len(mv) == 16 and not isinstance(mv[0], list):
                p['matrix4_value'] = [mv[0:4], mv[4:8], mv[8:12], mv[12:16]]
                print(f"  Fixed matrix4_value in node {node['id']}")

# ============================================================
# FIX PROGRAM 1 (index 0)
# ============================================================
prog1 = progs[0]
print(f"\n--- Fixing Program 1 (index 0): {prog1['name']} ---")
print(f"  base_seed: {prog1['base_seed']}")

new_nodes_1 = []
for node in prog1['nodes']:
    op = node.get('operator', '')
    
    if op == 'matrix4':
        fix_matrix4_node(node)
        new_nodes_1.append(node)
    elif op == 'bend':
        # Fix kind: macro -> modifier
        if node['kind'] == 'macro':
            print(f"  Fixed bend kind: macro -> modifier")
            node['kind'] = 'modifier'
        new_nodes_1.append(node)
    elif op == 'courtyard':
        # Replace courtyard with setback (keeps connected, gives civic step at east)
        print(f"  Replaced courtyard with setback (east-facing setback, level 1)")
        setback_node = {
            "id": node['id'],  # reuse 'result' id
            "kind": "macro",
            "operator": "setback",
            "inputs": node['inputs'],  # input from bend
            "semantic_role": "public_threshold",
            "parameters": [
                {
                    "name": "direction",
                    "value_type": "string",
                    "string_value": "y"
                },
                {
                    "name": "levels",
                    "value_type": "number",
                    "numeric_value": 1.0
                }
            ]
        }
        new_nodes_1.append(setback_node)
    else:
        new_nodes_1.append(node)

prog1['nodes'] = new_nodes_1
prog1['rationale'] = "Continuously bent slab (modified) with upper-storey setback; east road edge reads as public step."

# ============================================================
# FIX PROGRAM 13 (index 12)
# ============================================================
prog13 = progs[12]
print(f"\n--- Fixing Program 13 (index 12): {prog13['name']} ---")
print(f"  base_seed: {prog13['base_seed']}")

new_nodes_13 = []
for node in prog13['nodes']:
    op = node.get('operator', '')
    
    if op == 'matrix4':
        fix_matrix4_node(node)
        new_nodes_13.append(node)
    elif op == 'shear':
        # Fix kind: macro -> transform
        if node['kind'] == 'macro':
            print(f"  Fixed shear kind: macro -> transform")
            node['kind'] = 'transform'
        # Fix parameters
        new_params = []
        for p in node.get('parameters', []):
            if p['name'] == 'direction':
                # Fix value_type: 'literal' -> 'string' (it's a string value "x")
                # Fix structured_json: {} -> "null" (must be a string)
                # Keep all 5 fields as required by schema (literal kind)
                fixed_dir = {
                    "name": "direction",
                    "value_type": "string",
                    "numeric_value": 0.0,
                    "string_value": "x",
                    "boolean_value": False,
                    "vector_value": [],
                    "structured_json": "null"
                }
                print(f"  Fixed direction param: value_type literal->string, structured_json {{}}->\"null\"")
                new_params.append(fixed_dir)
            else:
                new_params.append(p)
        node['parameters'] = new_params
        new_nodes_13.append(node)
    elif op == 'courtyard':
        # Replace courtyard with setback (shear + courtyard = disconnected)
        print(f"  Replaced courtyard with setback (oblique top, civic step at east)")
        setback_node = {
            "id": node['id'],  # reuse 'result' id
            "kind": "macro",
            "operator": "setback",
            "inputs": node['inputs'],  # input from shear
            "semantic_role": "public_threshold",
            "parameters": [
                {
                    "name": "direction",
                    "value_type": "string",
                    "string_value": "x"
                },
                {
                    "name": "levels",
                    "value_type": "number",
                    "numeric_value": 1.0
                }
            ]
        }
        new_nodes_13.append(setback_node)
    else:
        new_nodes_13.append(node)

prog13['nodes'] = new_nodes_13
prog13['rationale'] = "Oblique shear displaces the top face; east-facing setback steps the civic entry at road level."

# ============================================================
# VALIDATE matrix4 in all programs (make sure none are flat)
# ============================================================
print("\n--- Checking all programs for flat matrix4 ---")
flat_count = 0
for i, prog in enumerate(progs):
    for node in prog.get('nodes', []):
        for p in node.get('parameters', []):
            if p.get('value_type') == 'matrix4' and 'matrix4_value' in p:
                mv = p['matrix4_value']
                if isinstance(mv, list) and len(mv) > 0 and not isinstance(mv[0], list):
                    print(f"  WARNING: flat matrix4 in program {i+1} node {node['id']}")
                    flat_count += 1

if flat_count == 0:
    print("  All matrix4 values are properly nested.")
else:
    print(f"  {flat_count} flat matrix4 values remain - fixing them...")
    for prog in progs:
        for node in prog.get('nodes', []):
            fix_matrix4_node(node)

# Write output
with open(dst, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nWrote fixed file to: {dst}")
print(f"Total programs: {len(progs)}")
