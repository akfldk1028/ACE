import json
schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json', encoding='utf-8'))
text = json.dumps(schema)
if 'book_base_volume' in text:
    print('book_base_volume FOUND in schema')
    idx = text.find('book_base_volume')
    print(text[max(0,idx-100):idx+300])
else:
    print('book_base_volume NOT in schema - MUST OMIT')
    
# check what operators exist
ops = set()
items_schema = schema['properties']['programs']['items']['properties']['nodes']['items']
any_of = items_schema['anyOf']
for node_type in any_of:
    props = node_type.get('properties', {})
    op = props.get('operator', {}).get('enum', [])
    ops.update(op)
print('All operators:', sorted(ops))
