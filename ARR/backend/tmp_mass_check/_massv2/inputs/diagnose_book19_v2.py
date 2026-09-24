import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib
from jsonschema import Draft7Validator, ValidationError

schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

with open('book-comp19.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

v = Draft7Validator(schema)
errors = list(v.iter_errors(payload))
print(f"Total errors: {len(errors)}")
print()
for e in errors:
    path = list(e.absolute_path)
    print(f"PATH: {path}")
    # Get the deepest message
    context = list(e.context) if hasattr(e, 'context') else []
    if context:
        for c in context[:5]:
            print(f"  SUBPATH: {list(c.absolute_path)}")
            print(f"  SUBMSG: {c.message[:200]}")
    else:
        print(f"MSG: {e.message[:300]}")
    # Show the offending object
    try:
        obj = payload
        for k in path:
            obj = obj[k]
        if isinstance(obj, dict):
            op = obj.get('operator', '?')
            params = obj.get('parameters', [])
            print(f"  OBJ operator={op}")
            for p in params:
                print(f"    param: name={p.get('name')}, value_type={p.get('value_type')}, extra_keys={[k for k in p if k not in ('name','value_type','numeric_value','string_value','boolean_value','vector_value','structured_json','matrix4_value')]}")
    except:
        pass
    print()
