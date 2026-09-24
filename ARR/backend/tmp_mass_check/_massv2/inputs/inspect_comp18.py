import sys
sys.stdout.reconfigure(encoding='utf-8')
import json

with open('book-comp18.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print('Top-level keys:', list(d.keys()))
print('Number of programs:', len(d.get('programs', [])))
print('book_principle_ids:', d.get('book_principle_ids', [])[:3])
print()

prog = d['programs'][0]
print('Program 0 keys:', list(prog.keys()))
print('name:', prog.get('name'))
print('base_form_id:', prog.get('base_form_id'))
print('base_seed:', prog.get('base_seed'))
print('book_composition_path_id:', prog.get('book_composition_path_id'))
print('root_id:', prog.get('root_id'))
print('dimensional_intent:', prog.get('dimensional_intent'))
print()
print('Nodes count:', len(prog.get('nodes', [])))
print()
for node in prog['nodes'][:4]:
    print(f"  id={node['id']}, kind={node['kind']}, op={node['operator']}")
    print(f"    inputs={node['inputs']}")
    print(f"    params={node['parameters']}")
    print(f"    role={node['semantic_role']}")
    print()
