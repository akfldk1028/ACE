import json, sys

path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check child 3 split_wing params
child = data['geometry_programs'][2]
print('Child 3:', child['name'])
for node in child['nodes']:
    if node['operator'] == 'split_wing':
        print('split_wing parameters:')
        for p in node['parameters']:
            val = p.get('bool_value', p.get('numeric_value', p.get('string_value', '?')))
            print(f"  {p['name']} = {val}")

print()
print('All programs:')
for i, gp in enumerate(data['geometry_programs']):
    print(f"  [{i}] {gp['name']}  root_id={gp['root_id']}")
