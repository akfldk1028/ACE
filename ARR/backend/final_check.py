import json

path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.json'
rejected_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.rejected.json'

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
with open(rejected_path, 'r', encoding='utf-8') as f:
    rejected = json.load(f)

print("=== COMPARING PROGRAMS ===")
for i in range(6):
    a = data['geometry_programs'][i]
    b = rejected['geometry_programs'][i]
    if a['name'] != b['name']:
        print(f"[{i}] NAME MISMATCH: {a['name']} vs {b['name']}")
    else:
        a_str = json.dumps(a, sort_keys=True)
        b_str = json.dumps(b, sort_keys=True)
        if a_str == b_str:
            print(f"[{i}] {a['name']}: IDENTICAL (no change)")
        else:
            print(f"[{i}] {a['name']}: CHANGED")
            # Find the difference
            for node_a, node_b in zip(a['nodes'], b['nodes']):
                if json.dumps(node_a, sort_keys=True) != json.dumps(node_b, sort_keys=True):
                    print(f"  Changed node: {node_a['operator']}")
                    for pa, pb in zip(node_a['parameters'], node_b['parameters']):
                        if json.dumps(pa, sort_keys=True) != json.dumps(pb, sort_keys=True):
                            print(f"    Param {pa['name']}: {pb.get('bool_value','?')} -> {pa.get('bool_value','?')}")
