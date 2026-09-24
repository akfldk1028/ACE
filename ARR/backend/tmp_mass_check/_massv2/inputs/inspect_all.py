import json, sys
sys.stdout.reconfigure(encoding='utf-8')
fname = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'
with open(fname, encoding='utf-8') as f:
    data = json.load(f)
programs = data['programs']
print('Total programs:', len(programs))
# Check both 0-based and 1-based for 11 and 27
for idx0 in [10, 11, 26, 27]:
    p = programs[idx0]
    print(f'--- 0-based index {idx0} (1-based {idx0+1}) ---')
    print('label:', p.get('label',''))
    print('base_seed:', p.get('base_seed',''))
    for n in p.get('nodes',[]):
        ops = [par.get('string_value','') or str(par.get('numeric_value','')) for par in n.get('parameters',[]) if par.get('name') in ('operator','layout','access_side','open_side','axis')]
        print(f'  {n["id"]} {n.get("operator","")} kind={n.get("kind","")} | ops={ops}')
    print()
