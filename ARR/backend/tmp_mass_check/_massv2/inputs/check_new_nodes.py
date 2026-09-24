import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('book-comp18.json', encoding='utf-8') as f:
    data_fixed = json.load(f)

for idx0 in [1, 6, 9, 11, 12, 13, 18, 20, 23, 25, 26, 27]:
    p = data_fixed['programs'][idx0]
    print(f'--- idx={idx0} ---')
    for n in p['nodes']:
        role = n.get('semantic_role', 'MISSING')
        print(f'  {n["id"]} {n["operator"]} role={role}')
    print()
