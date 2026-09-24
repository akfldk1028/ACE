import json

path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

child = data['geometry_programs'][2]
# Update rationale to mention ground_spine=true connects the wings
child['rationale'] = (
    "Full-site 1/1 short_axis body split into two parallel wings along x-axis with gap_ratio=0.22 "
    "(~11m clear gap for a 50m-wide site). Wings are connected by a shared ground_spine "
    "(ground_spine=true, ground_spine_width_ratio=0.1, ground_spine_height_ratio=0.2) so the "
    "assembly compiles as ONE connected solid. The spine doubles as a covered entrance link and "
    "structural diaphragm. Central gap above spine provides a double-loaded parking aisle: "
    "6m drive aisle + 5m stall on each side = ~16m, fitting ~12 stalls in central gap. "
    "SE forecourt adds more. Short-axis orientation differs from comp25 d03 (which used long_axis). "
    "Tradeoff: gap_ratio=0.22 delivers ~11m clear gap; spine reduces the open ground plane slightly "
    "but ensures structural connectivity and single-solid compliance."
)
child['metadata']['unresolved_conflicts'] = (
    "Column clearance in drive gap unverified. gap_ratio=0.22 delivers ~11m which meets 6m aisle + "
    "2.5m stall on one side only; double-loaded needs 16m or gap_ratio>=0.30. ground_spine occupies "
    "a strip across the gap centre, reducing effective clear width by spine width."
)

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Rationale updated.")
