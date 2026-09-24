import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('book-comp18_INVALID.json', encoding='utf-8') as f:
    content = f.read()
print('semantic_role count:', content.count('semantic_role'))
print('File size:', len(content))
# Check program 0 node structure
data = json.loads(content)
p0 = data['programs'][0]
for n in p0['nodes'][:3]:
    print('node keys:', list(n.keys()))
