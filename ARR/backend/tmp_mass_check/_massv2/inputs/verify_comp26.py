import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp26.json', encoding='utf-8') as f:
    d = json.load(f)
sents = d['sentences']
print('Count:', len(sents))
pids = [s['book_composition_path_id'] for s in sents]
names = [s['name'] for s in sents]
print('Unique path_ids:', len(set(pids)))
print('Unique names:', len(set(names)))
gfas = [s['dimensional_intent']['target_gfa_m2'] for s in sents]
print('GFA min:', min(gfas), 'max:', max(gfas))
four = sum(1 for s in sents if s['dimensional_intent']['storey_count'] == 4)
print('4-storey count:', four, ' / 5-storey:', len(sents)-four)
prefixes = [('1/1','one1_'),('1/16','one16_'),('1/2','half_'),('1/4','quarter_'),('1/8','eighth_'),('3/8','three8_')]
for label, p in prefixes:
    subset = [n for n in names if n.startswith(p)]
    la = sum(1 for n in subset if '_la_' in n)
    sa = sum(1 for n in subset if '_sa_' in n)
    v  = sum(1 for n in subset if '_v_' in n)
    print(f'  {label}: LA={la} SA={sa} V={v} total={la+sa+v}')
