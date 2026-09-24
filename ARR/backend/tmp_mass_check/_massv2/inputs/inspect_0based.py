import json, sys
sys.stdout.reconfigure(encoding='utf-8')
fname = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'
with open(fname, encoding='utf-8') as f:
    data = json.load(f)
programs = data['programs']
print('Total programs:', len(programs))
# 0-based indices from error message
violated = [1, 6, 9, 11, 12, 13, 18, 20, 23, 25, 26, 27]
for idx0 in violated:
    p = programs[idx0]
    print(f'--- 0-based idx={idx0} (1-based={idx0+1}) ---')
    print('label:', p.get('label',''))
    print('base_seed:', p.get('base_seed',''))
    for n in p.get('nodes',[]):
        params_summary = []
        for par in n.get('parameters',[]):
            vt = par.get('value_type','')
            if vt == 'number': params_summary.append(f'{par["name"]}={par.get("numeric_value")}')
            elif vt == 'string': params_summary.append(f'{par["name"]}={par.get("string_value")}')
            elif vt == 'boolean': params_summary.append(f'{par["name"]}={par.get("boolean_value")}')
            elif vt == 'literal': params_summary.append(f'{par["name"]}(lit)={par.get("string_value")}')
            elif vt == 'vector': params_summary.append(f'{par["name"]}={par.get("vector_value")}')
        print(f'  {n["id"]} {n.get("operator","")} kind={n.get("kind","")} | {" | ".join(params_summary)}')
    print()
