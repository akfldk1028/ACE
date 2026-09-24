import json, sys

path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

child = data['geometry_programs'][2]
print('Child name:', child['name'])

for node in child['nodes']:
    if node['operator'] == 'split_wing':
        print('split_wing params:')
        for p in node['parameters']:
            val = p.get('bool_value', p.get('numeric_value', p.get('string_value', '?')))
            print(' ', p['name'], '=', val)
        # Fix: set ground_spine=True to connect the two wings into one solid
        for p in node['parameters']:
            if p['name'] == 'ground_spine':
                print('Changing ground_spine from', p['bool_value'], 'to True')
                p['bool_value'] = True
        break

# Write back
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Fixed and written.')
