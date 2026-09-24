import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib
from jsonschema import Draft7Validator

with open('book-comp19.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)
schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

v = Draft7Validator(schema)
errors = list(v.iter_errors(payload))
print(f"Total errors: {len(errors)}")
print()
for e in errors:
    path = list(e.absolute_path)
    print(f"PATH: {path}")
    print(f"MSG:  {e.message[:300]}")
    # Try to show the failing value
    try:
        obj = payload
        for k in path:
            obj = obj[k]
        if isinstance(obj, dict):
            print(f"OBJ:  operator={obj.get('operator')}, params={json.dumps(obj.get('parameters',[]))[:200]}")
        else:
            print(f"OBJ:  {str(obj)[:200]}")
    except:
        pass
    print()
