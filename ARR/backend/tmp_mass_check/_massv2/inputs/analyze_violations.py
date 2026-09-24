import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))

# Build operator->kind map from schema
items = schema['properties']['programs']['items']['properties']['nodes']['items']['anyOf']
op_kind_map = {}
for item in items:
    op = item.get('properties',{}).get('operator',{}).get('enum',['?'])[0]
    kind = item.get('properties',{}).get('kind',{}).get('enum',['?'])[0]
    op_kind_map[op] = kind

v = Draft7Validator(schema)
errors = list(v.iter_errors(data))
print(f'Total errors: {len(errors)}')

# Classify errors by type
matrix4_errors = 0
kind_errors = 0
other_errors = 0

wrong_kinds = {}
for e in errors:
    path = list(e.path)
    if len(path) >= 3 and path[-1] == 'nodes':
        continue
    # Get node if possible
    if len(path) >= 4 and path[0] == 'programs' and path[2] == 'nodes':
        prog_idx = path[1]
        node_idx = path[3]
        node = data['programs'][prog_idx]['nodes'][node_idx]
        op = node.get('operator', '?')
        kind = node.get('kind', '?')
        expected_kind = op_kind_map.get(op, '?')
        
        # Check if matrix4_value is flat
        for p in node.get('parameters', []):
            if p.get('name') == 'matrix4' and isinstance(p.get('matrix4_value'), list) and len(p.get('matrix4_value',[])) == 16:
                matrix4_errors += 1
                break
        else:
            if kind != expected_kind and expected_kind != '?':
                kind_errors += 1
                wrong_kinds[op] = (kind, expected_kind)
            else:
                other_errors += 1

print(f'matrix4 flat errors: {matrix4_errors}')
print(f'kind mismatch errors: {kind_errors}')
print(f'other errors: {other_errors}')
print(f'Wrong kinds: {wrong_kinds}')

# Count unique ops with wrong kinds across all programs
all_wrong = set()
for prog in data['programs']:
    for node in prog.get('nodes', []):
        op = node.get('operator', '?')
        kind = node.get('kind', '?')
        expected = op_kind_map.get(op, '?')
        if expected != '?' and kind != expected:
            all_wrong.add((op, kind, expected))
print(f'\nAll wrong kind combos:')
for combo in sorted(all_wrong):
    print(f'  {combo[0]}: got {combo[1]}, expected {combo[2]}')
