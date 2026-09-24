# -*- coding: utf-8 -*-
"""
fix_comp18_v2.py
Fix all 330 schema violations in book-comp18_INVALID.json and write book-comp18.json

ROOT CAUSES:
1. matrix4_value is flat [1,0,...,1] needs nested [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
2. value_type="literal" must be "number" (schema enum doesn't include "literal")
"""
import json, sys, copy
sys.stdout.reconfigure(encoding='utf-8')

try:
    from jsonschema import Draft7Validator
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False
    print("WARNING: jsonschema not available")

INVALID_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json"
SCHEMA_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json"
OUTPUT_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json"

IDENTITY_4X4 = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

def fix_node(node):
    """Fix all schema violations in a single node."""
    node = copy.deepcopy(node)
    
    # Fix 1: matrix4_value flat -> nested 4x4
    for param in node.get('parameters', []):
        if param.get('value_type') == 'matrix4':
            mv = param.get('matrix4_value', [])
            if isinstance(mv, list) and len(mv) == 16 and not isinstance(mv[0], list):
                # Flat 16-element array -> reshape to 4x4
                param['matrix4_value'] = [
                    mv[0:4], mv[4:8], mv[8:12], mv[12:16]
                ]
        
        # Fix 2: value_type="literal" -> "number"
        if param.get('value_type') == 'literal':
            param['value_type'] = 'number'
    
    return node

def fix_program(prog):
    """Fix all nodes in a program."""
    prog = copy.deepcopy(prog)
    prog['nodes'] = [fix_node(n) for n in prog.get('nodes', [])]
    return prog

def main():
    # Load INVALID file
    with open(INVALID_PATH, encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data['programs'])} programs from INVALID file")
    
    # Apply fixes to all programs
    data['programs'] = [fix_program(p) for p in data['programs']]
    
    # Validate
    if HAS_SCHEMA:
        schema = json.load(open(SCHEMA_PATH, encoding='utf-8'))
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        print(f"Schema errors after fix: {len(errors)}")
        for err in errors[:30]:
            path = '/'.join(str(p) for p in err.absolute_path)
            print(f"  {path}: {err.message[:120]}")
        
        if errors:
            print("\nFix incomplete - still has errors")
            return False
        else:
            print("VALID - 0 errors!")
    
    # Write output
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    import os
    size = os.path.getsize(OUTPUT_PATH)
    print(f"Written to {OUTPUT_PATH} ({size:,} bytes)")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
