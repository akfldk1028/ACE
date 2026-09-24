import json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Load the INVALID file and violations
with open(r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18_INVALID.json') as f:
    data = json.load(f)

# Parse violations and show what programs/nodes they refer to
violations = [
    "programs/0/nodes/4: direction:string,levels:number fails minItems (branch wants 4)",
    "programs/1/nodes/3: axis:string,angle_degrees:number,gap_ratio:number,outward_sign:literal,retained_back_ratio:literal fails maxItems (branch wants 4)",
    "programs/2/nodes/3: axis:string,position:string,embedded_ratio:literal,guest_scale:literal,outward_sign:literal fails maxItems (branch wants 4)",
    "programs/2/nodes/4: same",
    "programs/3/nodes/3: angle_degrees:number,trunk_ratio:literal,arm_ratio:literal,vertical_anchor:string fails maxItems (branch wants 1)",
    "programs/3/nodes/4: axis:string,amount:number,shoulder_fraction:literal fails minItems (branch wants 4)",
    "programs/3/nodes/5: access_side:string,rise_ratio:literal,support_ratio:literal fails minItems (branch wants 4)",
    "programs/4/nodes/3: face_side:string,axis:string,width_ratio:number,depth_ratio:literal,outward_sign:literal fails maxItems (branch wants 4)",
    "programs/4/nodes/4: axis:string,distance_ratio:literal,unit_scale:literal,outward_sign:literal fails maxItems (branch wants 1)",
    "programs/5/nodes/3: angle_degrees:number,trunk_ratio:literal,arm_ratio:literal,vertical_anchor:string fails maxItems (branch wants 1)",
]

# Show node info for first 10 violations
for prog_idx in range(10):
    progs = data['programs']
    if prog_idx >= len(progs):
        break
    prog = progs[prog_idx]
    nodes = prog['nodes']
    print(f"\nProgram {prog_idx}: {prog['name']}")
    for ni, node in enumerate(nodes):
        params = node.get('parameters', [])
        param_names = [p['name'] for p in params]
        print(f"  node[{ni}]: {node['operator']} (kind={node['kind']}) params({len(params)})={param_names}")
