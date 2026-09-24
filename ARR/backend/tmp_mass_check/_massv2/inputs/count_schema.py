import json, sys
sys.stdout.reconfigure(encoding='utf-8')
schema_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'
with open(schema_path, encoding='utf-8') as f:
    s = f.read()
print('semantic_role in schema:', s.count('semantic_role'))
print('additionalProperties in schema:', s.count('additionalProperties'))
print('Schema size:', len(s))
# Find node schema structure
idx = s.find('"semantic_role"')
if idx >= 0:
    print('Found semantic_role at:', idx)
    print(s[max(0,idx-200):idx+300])
else:
    print('semantic_role NOT in schema')
    # Find additionalProperties context
    idx2 = s.find('"additionalProperties"')
    if idx2 >= 0:
        print('additionalProperties at:', idx2)
        print(s[max(0,idx2-100):idx2+200])
