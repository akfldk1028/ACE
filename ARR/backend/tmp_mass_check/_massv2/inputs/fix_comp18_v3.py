# -*- coding: utf-8 -*-
"""
fix_comp18_v3.py
Fix all 330 schema violations in book-comp18_INVALID.json and write book-comp18.json

ROOT CAUSES (3):
1. matrix4_value is flat [1,0,...,1] needs nested [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
2. value_type="literal" must be "number" (schema enum doesn't include "literal")
3. structured_json={} must be "null" (a STRING, not a JSON object)
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

# Operator kind map (from schema)
OP_KINDS = {
    # primitives
    'box': 'primitive', 'cylinder': 'primitive', 'extruded_polygon': 'primitive',
    'loft': 'primitive', 'sweep': 'primitive', 'wedge': 'primitive',
    # transforms
    'matrix4': 'transform', 'mirror': 'transform', 'rotate': 'transform',
    'scale': 'transform', 'shear': 'transform', 'translate': 'transform',
    # modifiers
    'bend': 'modifier', 'bound_surfaces': 'modifier', 'circularize': 'modifier',
    'clip': 'modifier', 'clip_fraction': 'modifier', 'cut_corner': 'modifier',
    'ellipsoidize': 'modifier', 'inflate': 'modifier', 'legal_section_clip': 'modifier',
    'pinch': 'modifier', 'profile_sweep_3d': 'modifier', 'slice': 'modifier',
    'taper': 'modifier', 'tetrahedralize': 'modifier', 'twist': 'modifier',
    # patterns
    'duplicate': 'pattern', 'linear_array': 'pattern', 'matrix_array': 'pattern',
    'mirror_array': 'pattern', 'radial_array': 'pattern', 'stack': 'pattern',
    # booleans
    'difference': 'boolean', 'intersection': 'boolean', 'union': 'boolean',
    # compositions
    'attach': 'composition', 'bridge': 'composition',
    # macros (everything else)
    'attach_volume': 'macro', 'bent_bar': 'macro', 'book_branch': 'macro',
    'book_carve': 'macro', 'book_extract': 'macro', 'book_fracture': 'macro',
    'book_grade': 'macro', 'book_lift': 'macro', 'book_lodge': 'macro',
    'book_notch': 'macro', 'book_rotate': 'macro', 'book_split': 'macro',
    'boundary_expand': 'macro', 'cantilever': 'macro', 'carve_void': 'macro',
    'courtyard': 'macro', 'cross_mass': 'macro', 'cut_corner_macro': 'macro',
    'embed_void': 'macro', 'grid_mass': 'macro', 'interlock_related': 'macro',
    'intersect_related': 'macro', 'join_related': 'macro', 'leaning_tower': 'macro',
    'lift': 'macro', 'merge_related': 'macro', 'nested_related': 'macro',
    'notch': 'macro', 'offset_related': 'macro', 'overlap_related': 'macro',
    'profiled_hall': 'macro', 'puncture': 'macro', 'related_array': 'macro',
    'setback': 'macro', 'shift_related': 'macro', 'split_wing': 'macro',
    'stepped_mass': 'macro', 'tapered_tower': 'macro', 'terrace': 'macro',
}

def fix_param(param):
    """Fix all schema violations in a single parameter."""
    param = copy.deepcopy(param)
    
    # Fix 2: value_type="literal" -> "number"
    if param.get('value_type') == 'literal':
        param['value_type'] = 'number'
    
    # Fix 3: structured_json={} -> "null" (string)
    if 'structured_json' in param:
        sj = param['structured_json']
        if not isinstance(sj, str):
            param['structured_json'] = 'null'
    
    return param

def fix_node(node):
    """Fix all schema violations in a single node."""
    node = copy.deepcopy(node)
    
    # Fix 4: correct kind for operator
    op = node.get('operator', '')
    if op in OP_KINDS:
        node['kind'] = OP_KINDS[op]
    # Note: 'cut_corner' appears as both 'modifier' and 'macro' in schema
    # The schema has two branches for cut_corner - use 'modifier' form
    # Actually bridge appears as both 'composition' and 'macro' - use macro for book bridge
    
    fixed_params = []
    for param in node.get('parameters', []):
        param = fix_param(param)
        
        # Fix 1: matrix4_value flat -> nested 4x4
        if param.get('value_type') == 'matrix4':
            mv = param.get('matrix4_value', [])
            if isinstance(mv, list) and len(mv) == 16 and not isinstance(mv[0], list):
                param['matrix4_value'] = [
                    mv[0:4], mv[4:8], mv[8:12], mv[12:16]
                ]
        
        fixed_params.append(param)
    
    node['parameters'] = fixed_params
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
            # Show first context for first error
            first_err = errors[0]
            print(f"\nFirst error contexts:")
            for ctx in first_err.context[:5]:
                print(f"  ctx: {ctx.message[:100]}")
            print(f"Fix incomplete - still has {len(errors)} errors")
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
