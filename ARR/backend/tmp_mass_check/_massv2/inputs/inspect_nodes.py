import sys, json
sys.stdout.reconfigure(encoding='utf-8')
data=json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))
prog=data['programs'][3]
print(json.dumps(prog['nodes'], indent=2))
