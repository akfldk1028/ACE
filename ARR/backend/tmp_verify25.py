import json
with open('D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/inputs/book-develop-comp25.json', encoding='utf-8') as f:
    d = json.load(f)
lines = [
    'mode: ' + d['mode'],
    'inherit_parent_dimensions: ' + str(d['inherit_parent_dimensions']),
    'parent: ' + d['parent'],
    'parent_shape_id: ' + d['parent_shape_id'],
    'gp_count: ' + str(len(d['geometry_programs'])),
]
for gp in d['geometry_programs']:
    ops = [n['operator'] for n in gp['nodes']]
    lines.append('  ' + gp['name'] + ': ' + str(ops))
with open('D:/tmp_verify25_out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('Done')
