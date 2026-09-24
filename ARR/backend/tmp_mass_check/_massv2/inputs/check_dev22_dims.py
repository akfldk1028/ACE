import json, jsonschema

fs=open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp22\book-author\schema.json',encoding='utf-8')
schema=json.load(fs); fs.close()

fd=open('book-develop-comp22.json',encoding='utf-8')
dev=json.load(fd); fd.close()

dim_schema = schema['properties']['sentences']['items']['properties']['dimensional_intent']

for prog in dev['geometry_programs']:
    dim = prog['dimensional_intent']
    errs = list(jsonschema.Draft7Validator(dim_schema).iter_errors(dim))
    print(prog['name'][:30], 'dim_intent_valid:', len(errs)==0, [e.message for e in errs[:2]] if errs else [])
