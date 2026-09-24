import json, sys
sys.stdout.reconfigure(encoding='utf-8')
fname = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'
with open(fname, encoding='utf-8') as f:
    data = json.load(f)
programs = data['programs']

# Program 13 (index 12, 0-based)
for idx in [9, 13, 25]:
    p = programs[idx-1]
    print(f'--- Program {idx} ---')
    print('label:', p.get('label',''))
    print('base_seed:', p.get('base_seed',''))
    for n in p.get('nodes',[]):
        print(f'  Node: {n["id"]} op={n.get("operator","")} kind={n.get("kind","")}')
        for par in n.get('parameters', []):
            print(f'    param: {json.dumps(par)}')
    print()
