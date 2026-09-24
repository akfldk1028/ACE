import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))

# Build operator->kind map from schema
items = schema['properties']['programs']['items']['properties']['nodes']['items']['anyOf']
op_kind_map = {}
op_params_map = {}
for item in items:
    op = item.get('properties',{}).get('operator',{}).get('enum',['?'])[0]
    kind = item.get('properties',{}).get('kind',{}).get('enum',['?'])[0]
    op_kind_map[op] = kind
    # Get allowed param names
    params_schema = item.get('properties',{}).get('parameters',{})
    param_names = []
    for anyof in params_schema.get('items',{}).get('anyOf',[]):
        pname = anyof.get('properties',{}).get('name',{}).get('enum',['?'])[0]
        param_names.append(pname)
    op_params_map[op] = param_names

v = Draft7Validator(schema)
errors = list(v.iter_errors(data))

# Find "other" errors
seen_ops = {}
for e in errors:
    path = list(e.path)
    if len(path) >= 4 and path[0] == 'programs' and path[2] == 'nodes':
        prog_idx = path[1]
        node_idx = path[3]
        node = data['programs'][prog_idx]['nodes'][node_idx]
        op = node.get('operator', '?')
        kind = node.get('kind', '?')
        expected_kind = op_kind_map.get(op, '?')
        
        # Check matrix4
        has_flat_m4 = any(p.get('name') == 'matrix4' and isinstance(p.get('matrix4_value'), list) and len(p.get('matrix4_value',[])) == 16 for p in node.get('parameters', []))
        has_wrong_kind = kind != expected_kind and expected_kind != '?'
        
        if not has_flat_m4 and not has_wrong_kind:
            key = (op, kind)
            if key not in seen_ops:
                seen_ops[key] = []
            seen_ops[key].append(f'prog{prog_idx}/node{node_idx}')

print("Other errors (not matrix4/kind):")
for (op, kind), locs in sorted(seen_ops.items()):
    print(f"  op={op} kind={kind} at {locs[:3]}")
    # Print the node params
    prog_idx = int(locs[0][4:locs[0].index('/')])
    node_idx = int(locs[0][locs[0].index('node')+4:])
    node = data['programs'][prog_idx]['nodes'][node_idx]
    for p in node.get('parameters', []):
        print(f"    param: name={p.get('name')} vtype={p.get('value_type')}")
    print(f"    allowed params: {op_params_map.get(op, [])}")
