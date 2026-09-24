import json

fs=open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp22\book-author\schema.json',encoding='utf-8')
schema=json.load(fs); fs.close()
valid_ids=set(schema['properties']['sentences']['items']['properties']['book_composition_path_id']['enum'])

fd=open('book-develop-comp22.json',encoding='utf-8')
dev=json.load(fd); fd.close()

all_valid=True
for p in dev['geometry_programs']:
    pid=p['book_composition_path_id']
    ok=pid in valid_ids
    if not ok: all_valid=False
    print(p['name'][:30], 'path_id_valid:', ok)
print('All path IDs valid:', all_valid)
print('Total programs:', len(dev['geometry_programs']))
print('mode:', dev['mode'])
print('parent:', dev['parent'])
