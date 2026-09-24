import json, sys
sys.stdout.reconfigure(encoding='utf-8')
s=json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
n=s['properties']['programs']['items']['properties']['nodes']
b=n['items']['anyOf']
# Show all operators and their expected kind
for x in b:
    op = x['properties']['operator']['enum'][0]
    kind_enum = x['properties']['kind'].get('enum', ['?'])
    print(f"{op}: kind={kind_enum}")
