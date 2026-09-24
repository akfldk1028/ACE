import sys, json
sys.path.insert(0, r'D:\Data\25_ACE\ARR\backend')
from design.maas.geometry_language.llm_adapter import _program_from_structured_author_item

dev = json.load(open(r'book-develop-comp22.json', encoding='utf-8'))

for pi, prog in enumerate(dev['geometry_programs']):
    name = prog['name']
    try:
        p = _program_from_structured_author_item(prog, index=pi)
        issues = list(p.issues())
        if issues:
            print(f'[{pi}] {name}: ISSUES: {[str(i) for i in issues]}')
        else:
            print(f'[{pi}] {name}: OK - {len(p.nodes)} nodes')
    except Exception as e:
        print(f'[{pi}] {name}: ERROR: {type(e).__name__}: {e}')
