import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib, re

schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    raw = f.read()

# Search for specific operator schemas
ops_to_find = [
    'interlock_related', 'book_branch', 'book_fracture', 'inflate',
    'boundary_expand', 'overlap_related', 'shear', 'book_split',
    'lift', 'split_wing'
]

# Find each operator's schema block in the raw JSON
for op in ops_to_find:
    # Find the enum listing this operator
    pattern = f'"enum": \\["{op}"\\]'
    matches = [m.start() for m in re.finditer(re.escape(f'"enum": ["{op}"]'), raw)]
    print(f"\n=== {op} === ({len(matches)} occurrences)")
    for pos in matches[:3]:
        # Print a chunk around this position
        chunk = raw[max(0, pos-50):pos+2000]
        # Find required/parameters block
        req_match = re.search(r'"required"\s*:', chunk)
        if req_match:
            print(chunk[req_match.start():req_match.start()+500])
            break
