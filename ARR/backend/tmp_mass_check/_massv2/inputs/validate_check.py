import json, sys
print("start", flush=True)
try:
    schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json', encoding='utf-8'))
    print("schema loaded", flush=True)
    payload = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json', encoding='utf-8'))
    print(f"payload loaded: {len(payload['programs'])} programs", flush=True)
    from jsonschema import Draft7Validator
    v = Draft7Validator(schema)
    print("validator ready", flush=True)
    errors = list(v.iter_errors(payload))
    print(f"validation complete: {len(errors)} errors", flush=True)
    if errors:
        for e in errors[:5]:
            print(f"  ERROR: {str(e.message)[:300]}")
            print(f"    path: {list(e.absolute_path)[:10]}")
    else:
        print("ALL VALID")
except Exception as ex:
    print(f"EXCEPTION: {ex}", flush=True)
    import traceback
    traceback.print_exc()
print("done", flush=True)
