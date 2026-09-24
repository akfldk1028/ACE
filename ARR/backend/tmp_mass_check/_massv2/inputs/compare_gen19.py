import sys
sys.stdout.reconfigure(encoding='utf-8')
import json

# Compare rejected vs current
with open('gen-comp19.rejected.json', 'r', encoding='utf-8') as f:
    rejected = json.load(f)
with open('gen-comp19.json', 'r', encoding='utf-8') as f:
    current = json.load(f)

rej_schemes = {s['name']: s for s in rejected['schemes']}
cur_schemes = {s['name']: s for s in current['schemes']}

print('Changed schemes (ops differ):')
for name in rej_schemes:
    if name in cur_schemes:
        rej_ops = [o['op'] for o in rej_schemes[name].get('ops',[])]
        cur_ops = [o['op'] for o in cur_schemes[name].get('ops',[])]
        if rej_ops != cur_ops:
            print(f'  {name}:')
            print(f'    rejected: {rej_ops}')
            print(f'    current:  {cur_ops}')

print()
print('Profiles in rejected:')
found_profiles = False
for s in rejected['schemes']:
    for o in s.get('ops', []):
        if 'profile' in o:
            found_profiles = True
            print(f"  {s['name']}: op={o['op']}, profile={o['profile']}")
if not found_profiles:
    print('  (none)')

print()
print('Profiles in current:')
found_profiles = False
for s in current['schemes']:
    for o in s.get('ops', []):
        if 'profile' in o:
            found_profiles = True
            print(f"  {s['name']}: op={o['op']}, profile={o['profile']}")
if not found_profiles:
    print('  (none)')
