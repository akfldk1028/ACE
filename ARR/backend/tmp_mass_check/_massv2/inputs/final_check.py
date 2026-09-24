import json
from collections import Counter

payload = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json', encoding='utf-8'))
programs = payload['programs']

print(f"Programs: {len(programs)}")
print(f"Principle IDs: {len(payload['book_principle_ids'])}")

# Check path diversity
path_cnt = Counter(p['book_composition_path_id'] for p in programs)
print(f"Unique paths used: {len(path_cnt)}")
print(f"Max path reuse: {max(path_cnt.values())}")

# Check base_form_id distribution
form_cnt = Counter(p['base_form_id'] for p in programs)
print(f"base_form_id: {dict(form_cnt)}")

# Check base_seed distribution  
seed_cnt = Counter(p['base_seed'] for p in programs)
print(f"base_seed: {dict(seed_cnt)}")

# Check all required keys
required = ['name','base_form_id','base_seed','intent_tags','nodes','root_id','rationale','dimensional_intent','book_composition_path_id']
for prog in programs:
    for k in required:
        assert k in prog, f"Missing {k} in {prog['name']}"
print("All required keys present in all programs")

# Check node counts
node_counts = [len(p['nodes']) for p in programs]
print(f"Node counts: min={min(node_counts)}, max={max(node_counts)}, avg={sum(node_counts)/len(node_counts):.1f}")

# Check that root_ids refer to existing nodes
for prog in programs:
    node_ids = {n['id'] for n in prog['nodes']}
    assert prog['root_id'] in node_ids, f"root_id {prog['root_id']} not in nodes for {prog['name']}"
print("All root_ids valid")

# Check DI
di_count = sum(1 for p in programs if p['dimensional_intent'] is not None)
print(f"Programs with dimensional_intent: {di_count}")

# Sample program
p = programs[0]
print(f"\nSample program: {p['name']}")
print(f"  base_form_id: {p['base_form_id']}")
print(f"  base_seed: {p['base_seed']}")
print(f"  root_id: {p['root_id']}")
print(f"  nodes: {[n['operator'] for n in p['nodes']]}")
print(f"  rationale: {p['rationale']}")
print(f"  DI: {p['dimensional_intent']}")
print(f"  path_id: {p['book_composition_path_id']}")
