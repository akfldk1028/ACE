import sys, json, traceback
sys.path.insert(0, r'D:\Data\25_ACE\ARR\backend')

from design.maas.book_development import validate_development_payload

dev = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp22.json', encoding='utf-8'))
ctx = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp22\book-development-parent-contract.json', encoding='utf-8'))

try:
    programs = validate_development_payload(dev, ctx, expected_count=6)
    print(f'PASSED: {len(programs)} programs validated')
    for p in programs:
        print(f'  - {p.name}')
except Exception as e:
    print(f'FAILED: {type(e).__name__}: {e}')
    traceback.print_exc()
