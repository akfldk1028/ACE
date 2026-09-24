import json, sys
sys.path.insert(0, 'D:/Data/25_ACE/ARR/backend')

from design.maas import book_development

with open('D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/inputs/book-develop-comp25.json', encoding='utf-8') as f:
    payload = json.load(f)

context = {
    "parent": "book:book-comp24:morph-compact-tall:creative-019",
    "parent_shape_id": "7a170ae62282f2a81942",
    "parent_program_hash": "20d6481fc843720fdd99809239df891f0839650c5862cf436e892f4776e8d58f",
    "parent_certificate_id": "2331653a23b9f22c1e23",
    "site_pnu": "4115011300106840001",
    "storey_count": 5,
    "storey_height_m": 3.8,
    "target_gfa_m2": 4906.565793050071,
    "height_m": 19.0
}

try:
    result = book_development.validate_development_payload(payload, context, expected_count=6)
    with open('D:/tmp_final_validate25_out.txt', 'w', encoding='utf-8') as f:
        f.write(f'PASS: {len(result)} programs\n')
        for p in result:
            f.write(f'  {p.name}  root={p.root_id}\n')
    print('PASS')
except Exception as e:
    with open('D:/tmp_final_validate25_out.txt', 'w', encoding='utf-8') as f:
        f.write(f'FAIL: {e}\n')
    print('FAIL:', e)
