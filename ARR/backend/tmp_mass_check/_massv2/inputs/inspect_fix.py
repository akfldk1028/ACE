import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json', encoding='utf-8') as f:
    data = json.load(f)

# Check structure
print('Keys:', list(data.keys()))
progs_key = 'programs' if 'programs' in data else 'authored_programs_from_payload'
progs = data[progs_key]
print('Total programs:', len(progs))

# Programs 1 and 13 (1-based) = indices 0 and 12 (0-based)
for idx in [0, 12]:
    p = progs[idx]
    print(f'\n=== Program {idx+1} (1-based), index {idx} (0-based) ===')
    print('base_seed:', p.get('base_seed'))
    print('brief_label:', p.get('brief_label'))
    nodes = p.get('node_graph', {}).get('nodes', [])
    for n in nodes:
        print(f"  node id={n['id']} op={n['op']} kind={n['kind']}")
        for param in n.get('parameters', []):
            print(f"    param: {param}")
    print('Full JSON:')
    print(json.dumps(p, indent=2))
