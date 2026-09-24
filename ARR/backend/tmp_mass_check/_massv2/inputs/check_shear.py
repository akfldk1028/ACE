import json
schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json', encoding='utf-8'))
items_schema = schema['properties']['programs']['items']['properties']['nodes']['items']
any_of = items_schema['anyOf']
for node_type in any_of:
    props = node_type.get('properties', {})
    op = props.get('operator', {}).get('enum', [])
    kind = props.get('kind', {}).get('enum', [])
    if 'shear' in op:
        print(f"SHEAR: kind={kind}")
        params_schema = props.get('parameters', {})
        param_items = params_schema.get('items', {})
        sub_any = param_items.get('anyOf', [])
        for p in sub_any:
            pprops = p.get('properties', {})
            pname = pprops.get('name', {}).get('enum', ['?'])
            preq = p.get('required', [])
            print(f"  param {pname}: required={preq}")
