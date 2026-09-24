import sys, json
sys.path.insert(0, r'D:\Data\25_ACE\ARR\backend')
from design.maas.geometry_language.llm_adapter import _program_from_structured_author_item, _canonicalize_program_relation_suffix
from design.maas.geometry_language.ast import GeometryProgram

dev = json.load(open(r'book-develop-comp22.json', encoding='utf-8'))

for pi, prog in enumerate(dev['geometry_programs']):
    name = prog['name']
    try:
        p = _program_from_structured_author_item(prog, index=pi)
        # Try topological_nodes which triggers issues
        try:
            nodes = p.topological_nodes()
            print(f'[{pi}] {name}: OK - topo {len(nodes)} nodes')
        except ValueError as ve:
            print(f'[{pi}] {name}: TOPO ERROR: {ve}')
        # Try canonicalize
        try:
            p2 = _canonicalize_program_relation_suffix(p)
            print(f'[{pi}] {name}: CANONICAL OK')
        except Exception as ce:
            print(f'[{pi}] {name}: CANONICAL ERROR: {type(ce).__name__}: {ce}')
    except Exception as e:
        print(f'[{pi}] {name}: PARSE ERROR: {type(e).__name__}: {e}')
