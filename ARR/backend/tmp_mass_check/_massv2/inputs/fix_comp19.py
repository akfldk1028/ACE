import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp19.json'

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

programs = data['programs']

# --- Fix program index 5 (1-based: 6) ---
# declared_base_form_elliptical_does_not_match_cube
# The scale is [1.0,1.0,1.0] -> cube geometry, but base_form_id was "elliptical"
p6 = programs[5]
print(f"P6 name: {p6['name']}, base_form_id: {p6['base_form_id']}")
assert p6['name'] == 'p06_block_inflate_expand_notch'
p6['base_form_id'] = 'cube'
print(f"  -> Fixed base_form_id to 'cube'")

# --- Fix program index 6 (1-based: 7) ---
# overlap_related -> carve_void = disconnected (2 components)
# Replace carve_void with notch at east
p7 = programs[6]
print(f"P7 name: {p7['name']}")
assert p7['name'] == 'p07_bar_overlap_carve'
nodes = p7['nodes']
# Find and replace the carve_void node
for i, node in enumerate(nodes):
    if node['operator'] == 'carve_void' and node['id'] == 'acc':
        print(f"  Found carve_void at node index {i}, replacing with notch")
        nodes[i] = {
            "id": "acc",
            "kind": "macro",
            "operator": "notch",
            "inputs": node['inputs'],
            "parameters": [
                {
                    "name": "side",
                    "value_type": "string",
                    "string_value": "east"
                },
                {
                    "name": "ratio",
                    "value_type": "number",
                    "numeric_value": 0.25
                },
                {
                    "name": "height_ratio",
                    "value_type": "number",
                    "numeric_value": 0.55
                }
            ],
            "semantic_role": "public_threshold"
        }
        print(f"  -> Replaced carve_void with notch")
        break

# Also update the program name and intent_tags to reflect the change
p7['name'] = 'p07_bar_overlap_notch'
p7['intent_tags'] = ['overlap', 'bar', 'notch', 'public_office']
p7['rationale'] = (
    "Two bar volumes partially overlap on y-axis (shift_ratio 0.38, slab_ratio 0.45) "
    "forming an H-plan as one connected solid. A notch at east signals the public entry "
    "between the overlapping bar ends at the street face."
)
print(f"  -> Updated name and tags")

# --- Fix program index 9 (1-based: 10) ---
# profiled_hall needs 2..12 normalized controls
# Current section_controls = '{"rise": 0.35, "bays": 1}' - wrong format
# Fix: provide {"controls": [[0,0],[0.5,0.35],[1,0]]} - 3 normalized [t,v] pairs for barrel
p10 = programs[9]
print(f"P10 name: {p10['name']}")
assert p10['name'] == 'p10_slab_profiled_hall_notch'
nodes = p10['nodes']
for i, node in enumerate(nodes):
    if node['operator'] == 'profiled_hall':
        print(f"  Found profiled_hall at node index {i}")
        for j, param in enumerate(node['parameters']):
            if param['name'] == 'section_controls':
                print(f"  Old section_controls: {param['structured_json']}")
                # Barrel profile: 3 normalized control points [t, v]
                # t=0 (left edge, v=0), t=0.5 (crown, v=0.35), t=1.0 (right edge, v=0)
                import json as json2
                ctrl_str = json2.dumps({"controls": [[0.0, 0.0], [0.5, 0.35], [1.0, 0.0]]})
                node['parameters'][j]['structured_json'] = ctrl_str
                print(f"  New section_controls: {ctrl_str}")
                break
        break

# Write back
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nDone. File written.")

# Verify
with open(path, 'r', encoding='utf-8') as f:
    data2 = json.load(f)
p = data2['programs']
print(f"P6 base_form_id: {p[5]['base_form_id']}")
print(f"P7 name: {p[6]['name']}, terminal op: {p[6]['nodes'][-1]['operator']}")
p10_nodes = p[9]['nodes']
for n in p10_nodes:
    if n['operator'] == 'profiled_hall':
        for param in n['parameters']:
            if param['name'] == 'section_controls':
                print(f"P10 section_controls: {param['structured_json']}")
