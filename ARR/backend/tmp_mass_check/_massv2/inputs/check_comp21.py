import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter

data = json.load(open('book-comp21.json', encoding='utf-8'))
sentences = data['sentences']
print('Count:', len(sentences))

names = [s['name'] for s in sentences]
path_ids = [s['book_composition_path_id'] for s in sentences]
print('Unique path IDs:', len(set(path_ids)))
print('Unique names:', len(set(names)))

gfas = [s['dimensional_intent']['target_gfa_m2'] for s in sentences]
print('GFA range:', min(gfas), '-', max(gfas))

storeys = Counter(s['dimensional_intent']['storey_count'] for s in sentences)
print('Storey counts:', dict(storeys))

faces = Counter((s['facing']['access_side'], s['facing']['north_side']) for s in sentences)
print('Facing combos:', dict(faces))

prefixes = Counter(n.split('_')[0] for n in names)
print('Base volume groups:', dict(sorted(prefixes.items())))

print('First 5 names:', names[:5])
print('Last 5 names:', names[-5:])
