import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp23.json', encoding='utf-8') as f:
    data = json.load(f)
sentences = data['sentences']
pids = [s['book_composition_path_id'] for s in sentences]
names = [s['name'] for s in sentences]
gfas = [s['dimensional_intent']['target_gfa_m2'] for s in sentences]
storeys = [s['dimensional_intent']['storey_count'] for s in sentences]
accesses = [s['facing']['access_side'] for s in sentences]
print(f'Count: {len(sentences)}')
print(f'Unique path IDs: {len(set(pids))}')
print(f'Unique names: {len(set(names))}')
print(f'GFA range: {min(gfas):.1f} - {max(gfas):.1f}')
print(f'Storey range: {min(storeys)}-{max(storeys)}')
print(f'Access sides: {set(accesses)}')
print(f'North sides: {set(s["facing"]["north_side"] for s in sentences)}')
print(f'First 3 names: {names[:3]}')
print(f'Last 3 names: {names[-3:]}')
