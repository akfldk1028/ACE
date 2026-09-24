import sys, json, copy
sys.stdout.reconfigure(encoding='utf-8')
from jsonschema import Draft7Validator

# Operator kind map from schema
OP_KIND = {
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
    # macros (all others)
}

def get_correct_kind(op):
    if op in OP_KIND:
        return OP_KIND[op]
    # Default: macro for book_* and other operators
    return 'macro'

def fix_matrix4_value(val):
    """Convert flat 16-element array to 4x4 nested array."""
    if isinstance(val, list) and len(val) == 16 and all(isinstance(x, (int, float)) for x in val):
        return [
            [val[0], val[1], val[2], val[3]],
            [val[4], val[5], val[6], val[7]],
            [val[8], val[9], val[10], val[11]],
            [val[12], val[13], val[14], val[15]]
        ]
    return val

def fix_param(param):
    """Fix a single parameter object."""
    p = copy.deepcopy(param)
    
    # Fix value_type: "literal" -> "number"
    if p.get('value_type') == 'literal':
        p['value_type'] = 'number'
    
    # Fix structured_json: {} -> "null"
    if 'structured_json' in p and not isinstance(p['structured_json'], str):
        p['structured_json'] = 'null'
    
    # Fix matrix4_value flat array
    if p.get('name') == 'matrix4' and p.get('value_type') == 'matrix4':
        p['matrix4_value'] = fix_matrix4_value(p.get('matrix4_value', []))
    
    return p

def fix_node(node):
    """Fix a single node."""
    n = copy.deepcopy(node)
    
    # Fix kind
    op = n.get('operator', '')
    correct_kind = get_correct_kind(op)
    if n.get('kind') != correct_kind:
        n['kind'] = correct_kind
    
    # Fix parameters
    n['parameters'] = [fix_param(p) for p in n.get('parameters', [])]
    
    return n

def fix_program(prog):
    """Fix a single program."""
    p = copy.deepcopy(prog)
    p['nodes'] = [fix_node(n) for n in p.get('nodes', [])]
    return p

# Load
print("Loading invalid file...")
data = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json'))
schema = json.load(open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json'))

# Fix all programs
print(f"Fixing {len(data['programs'])} programs...")
data['programs'] = [fix_program(prog) for prog in data['programs']]

# Validate
print("Validating...")
v = Draft7Validator(schema)
errors = list(v.iter_errors(data))
print(f"Remaining errors: {len(errors)}")
for e in errors[:20]:
    print(f"  PATH: {list(e.path)}")
    print(f"  MSG: {e.message[:200]}")
    print()

if len(errors) == 0:
    # Write output
    out_path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"SUCCESS! Written to {out_path}")
    print(f"File size: {len(json.dumps(data))} bytes")
else:
    print("STILL HAS ERRORS - not writing")
