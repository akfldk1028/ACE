import json, sys
sys.stdout.reconfigure(encoding='utf-8')
s=json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
n=s['properties']['programs']['items']['properties']['nodes']
b=n['items']['anyOf']

# Find specific operators and show full param requirements
ops_of_interest = ['courtyard', 'carve_void', 'notch', 'lift', 'bend', 'embed_void', 
                   'book_branch', 'book_carve', 'book_fracture', 'boundary_expand',
                   'offset_related', 'book_rotate', 'matrix4']

for x in b:
    op = x['properties']['operator']['enum'][0]
    if op in ops_of_interest:
        params = x['properties']['parameters']
        mn = params.get('minItems', 0)
        mx = params.get('maxItems', 999)
        print(f"\n=== {op}: min={mn} max={mx} ===")
        # Show each param's required fields
        items_schema = params.get('items', {})
        if 'anyOf' in items_schema:
            for item in items_schema['anyOf']:
                required = item.get('required', [])
                props = item.get('properties', {})
                name_enum = props.get('name', {}).get('enum', ['?'])
                vt_enum = props.get('value_type', {}).get('enum', ['?'])
                print(f"  param: name={name_enum[0]} value_type={vt_enum} required={required}")
