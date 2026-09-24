import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
from jsonschema import Draft7Validator

with open('book-comp19.json','r',encoding='utf-8') as f:
    p = json.load(f)
with open('D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json','r',encoding='utf-8') as f:
    s = json.load(f)

e = list(Draft7Validator(s).iter_errors(p))
print(f'book-comp19: {len(e)} schema errors - {"PASS" if not e else "FAIL"}')
print(f'Programs: {len(p["programs"])}, Principle IDs: {len(p["book_principle_ids"])}')
