import json
schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json', encoding='utf-8'))
items_schema = schema['properties']['programs']['items']['properties']['nodes']['items']
any_of = items_schema['anyOf']
check_ops = ['notch', 'carve_void', 'courtyard', 'lift', 'split_wing', 'boundary_expand',
             'embed_void', 'interlock_related', 'intersect_related', 'offset_related',
             'overlap_related', 'nested_related', 'merge_related', 'related_array',
             'join_related', 'shift_related', 'book_branch', 'book_split', 'book_notch',
             'book_carve', 'book_fracture', 'book_extract', 'book_lift', 'book_lodge',
             'book_rotate', 'mirror_array', 'leaning_tower', 'tapered_tower', 'clip_fraction',
             'cut_corner', 'puncture', 'taper', 'twist', 'inflate', 'pinch']
for node_type in any_of:
    props = node_type.get('properties', {})
    op = props.get('operator', {}).get('enum', [])
    kind = props.get('kind', {}).get('enum', [])
    if any(o in check_ops for o in op):
        print(f"OP: {op} KIND: {kind}")
        params_schema = props.get('parameters', {})
        min_p = params_schema.get('minItems', 0)
        max_p = params_schema.get('maxItems', '?')
        param_items = params_schema.get('items', {})
        sub_any = param_items.get('anyOf', [])
        for p in sub_any:
            pprops = p.get('properties', {})
            pname = pprops.get('name', {}).get('enum', ['?'])
            preq = p.get('required', [])
            pvt = pprops.get('value_type', {}).get('enum', ['?'])
            print(f"  param {pname}: vt={pvt} required={preq}")
