import json, sys
sys.stdout.reconfigure(encoding='utf-8')

# The violations.txt refers to book-comp18.json (the output file, not INVALID)
# The violations must be from the file that WAS submitted but got rejected
# Let's look at what the violations refer to more carefully

# violations.txt says:
# programs/0/nodes/4: parameters [direction:string, levels:number] fails minItems (branch wants 4)
# This means node[4] in program[0] has params with direction and levels -> setback
# But our INVALID file has courtyard at node[4] of program[0]

# So the violations are from a DIFFERENT file than book-comp18_INVALID.json!
# The rejected file was book-comp18.json which no longer exists.
# But book-comp18_INVALID.json has the problems that we need to fix.

# Let me just run the schema validator on book-comp18_INVALID.json and see what errors it gives
try:
    from jsonschema import Draft7Validator
    schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))
    data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    print(f"Total errors in INVALID file: {len(errors)}")
    for err in errors[:30]:
        path = '/'.join(str(p) for p in err.absolute_path)
        print(f"  {path}: {err.message[:120]}")
except Exception as e:
    print(f"Error: {e}")
