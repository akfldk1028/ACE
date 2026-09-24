import sys, os, json
sys.path.insert(0, 'D:/Data/25_ACE/ARR/backend')
os.chdir('D:/Data/25_ACE/ARR/backend')

with open('D:/tmp_check_dev4_out.txt', 'w', encoding='utf-8') as f:
    try:
        from design.maas.geometry_language.llm_adapter import (
            OPERATORS_BY_KIND, OPERATOR_PARAMETER_CONTRACTS, CANONICAL_OPERATOR_KIND
        )
        f.write('=== OPERATORS_BY_KIND ===\n')
        for kind, ops in OPERATORS_BY_KIND.items():
            f.write(f'{kind}: {sorted(ops)}\n')
        f.write('\n=== OPERATOR_PARAMETER_CONTRACTS (sample) ===\n')
        for op in ['lift', 'split_wing', 'terrace', 'stepped_mass', 'courtyard', 'carve_void', 'notch', 'clip', 'book_base_volume']:
            params = OPERATOR_PARAMETER_CONTRACTS.get(op, 'NOT FOUND')
            f.write(f'{op}: {params}\n')
        f.write('\n=== CANONICAL_OPERATOR_KIND (sample) ===\n')
        for op, kind in list(CANONICAL_OPERATOR_KIND.items())[:30]:
            f.write(f'{op}: {kind}\n')
    except Exception as e:
        f.write(f'Error: {e}\n')
        import traceback
        f.write(traceback.format_exc())

print('Done')
