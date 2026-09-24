import json, sys
sys.stdout.reconfigure(encoding='utf-8')
s=json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
n=s['properties']['programs']['items']['properties']['nodes']
b=n['items']['anyOf']
for x in b:
    op = x['properties']['operator']['enum'][0]
    params = x['properties']['parameters']
    mn = params.get('minItems', 0)
    mx = params.get('maxItems', 999)
    names = []
    items_schema = params.get('items',{})
    if 'anyOf' in items_schema:
        for item in items_schema['anyOf']:
            if 'properties' in item and 'name' in item['properties']:
                nn = item['properties']['name']
                if 'enum' in nn:
                    names.append(nn['enum'][0])
    print(f'{op}: min={mn} max={mx} params={names}')
