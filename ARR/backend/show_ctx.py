import json
ctx_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp26\book-author\context.json'
with open(ctx_path, 'r', encoding='utf-8') as f:
    ctx = json.load(f)
print('Keys:', list(ctx.keys()))
