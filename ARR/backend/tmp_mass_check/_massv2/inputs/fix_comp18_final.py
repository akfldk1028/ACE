import sys, json, os, copy

sys.stdout = open('fix_comp18_final_out.txt', 'w', encoding='utf-8')
sys.stderr = sys.stdout

SRC = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.rejected.json'
DST = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json'
SCHEMA = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'

print(f"Loading {SRC} ...")
with open(SRC, 'r', encoding='utf-8') as f:
    data = json.load(f)

progs = data['programs']
print(f"Total programs: {len(progs)}")

# Show first program nodes structure
p0 = progs[0]
print(f"Prog 1 base_seed: {p0.get('base_seed')}")
print(f"Prog 1 nodes count: {len(p0.get('nodes', []))}")
if p0.get('nodes'):
    n0 = p0['nodes'][0]
    print(f"Node 0 keys: {list(n0.keys())}")
    print(f"Node 0: {json.dumps(n0, indent=2)[:500]}")

# Check the violated programs
indices_1based = [29,30,32,34,35,41,42,43,45,46,50,51,55,57,61,63,65,67,69,71,73,78,79,84,87,89,91,96,98,101,103,105,106,107,108,110,112,114,119,120]
print(f"\nTotal to fix: {len(indices_1based)}")
for i1 in indices_1based:
    idx = i1 - 1
    p = progs[idx]
    ops = [n['op'] for n in p.get('nodes', [])]
    print(f"Prog {i1}: seed={p.get('base_seed')} ops={ops}")

sys.stdout.flush()
sys.stdout.close()
