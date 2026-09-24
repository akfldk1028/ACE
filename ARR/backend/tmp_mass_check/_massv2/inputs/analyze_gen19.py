import sys
sys.stdout.reconfigure(encoding='utf-8')
import json

# Load the rejected file
with open('gen-comp19.rejected.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

schemes = d.get('schemes', [])
print(f'Total schemes: {len(schemes)}')
print()
for i, s in enumerate(schemes):
    ops = [o['op'] for o in s.get('ops', [])]
    has_carve = 'carve' in ops
    print(f"[{i}] {s['name']}")
    print(f"     ops: {ops}")
    print(f"     has_carve: {has_carve}")
    print()

has_carve_count = sum(1 for s in schemes if any(o['op'] == 'carve' for o in s.get('ops', [])))
print(f"Carve ratio: {has_carve_count}/{len(schemes)} = {has_carve_count/len(schemes):.2f}")
