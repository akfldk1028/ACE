import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('book-comp18_INVALID.json', encoding='utf-8') as f:
    data = json.load(f)

# Check which operators have which semantic_role values in original
role_map = {}
for p in data['programs']:
    for n in p.get('nodes', []):
        op = n.get('operator', '')
        role = n.get('semantic_role', 'MISSING')
        if op not in role_map:
            role_map[op] = set()
        role_map[op].add(role)

print('Operator → semantic_role mapping:')
for op, roles in sorted(role_map.items()):
    print(f'  {op}: {roles}')
