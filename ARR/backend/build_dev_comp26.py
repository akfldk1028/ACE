"""Build book-develop-comp26.json with 6 exact-authored-development candidates."""
import sys, os, json
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', closefd=False)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf8', closefd=False)

os.chdir(r"D:\Data\25_ACE\ARR\backend")

PARENT = "book:book-comp24:morph-compact-tall:creative-019"
PARENT_SHAPE_ID = "7a170ae62282f2a81942"
PARENT_PROGRAM_HASH = "20d6481fc843720fdd99809239df891f0839650c5862cf436e892f4776e8d58f"

STOREY_COUNT = 5
STOREY_HEIGHT_M = 3.8
TARGET_GFA_M2 = 4906.565793050071
HEIGHT_M = 19.0  # 5 * 3.8

def dimensional_intent():
    return {
        "schema_version": "arr.maas.dimensional_intent.v1",
        "storey_count": STOREY_COUNT,
        "storey_height_m": STOREY_HEIGHT_M,
        "target_gfa_m2": TARGET_GFA_M2,
        "delivery_policy": "preserve_physical_dimensions",
        "programme_status": "unknown"
    }

def base_nodes():
    """Standard 3-node seed chain: box -> matrix4 -> book_base_volume."""
    return [
        {
            "id": "unit_box",
            "kind": "primitive",
            "operator": "box",
            "inputs": [],
            "parameters": [
                {"name": "width",  "value_type": "number", "numeric_value": 1.0},
                {"name": "depth",  "value_type": "number", "numeric_value": 1.0},
                {"name": "height", "value_type": "number", "numeric_value": 1.0}
            ],
            "semantic_role": "base_seed"
        },
        {
            "id": "seed_block",
            "kind": "transform",
            "operator": "matrix4",
            "inputs": ["unit_box"],
            "parameters": [
                {
                    "name": "matrix4",
                    "value_type": "matrix4",
                    "matrix4_value": [
                        [1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]
                    ]
                }
            ],
            "semantic_role": "base_seed"
        }
    ]

def book_base_volume_node(label, orientation, node_id="book01_book_base_volume"):
    return {
        "id": node_id,
        "kind": "modifier",
        "operator": "book_base_volume",
        "inputs": ["seed_block"],
        "parameters": [
            {"name": "label",       "value_type": "string", "string_value": label},
            {"name": "orientation", "value_type": "string", "string_value": orientation}
        ],
        "semantic_role": "book_mutated_dominant"
    }

def lift_node(input_id, rise_ratio=0.20, support_ratio=0.07, access_side="east"):
    return {
        "id": "book02_lift",
        "kind": "macro",
        "operator": "lift",
        "inputs": [input_id],
        "parameters": [
            {"name": "rise_ratio",    "value_type": "number", "numeric_value": rise_ratio},
            {"name": "support_ratio", "value_type": "number", "numeric_value": support_ratio},
            {"name": "access_side",   "value_type": "string", "string_value": access_side}
        ],
        "semantic_role": "public_threshold"
    }

def terrace_node(input_id, levels=2, setback_ratio=0.25, direction="x", direction_sign=1.0):
    return {
        "id": "book02_terrace",
        "kind": "macro",
        "operator": "terrace",
        "inputs": [input_id],
        "parameters": [
            {"name": "levels",        "value_type": "number",  "numeric_value": levels},
            {"name": "setback_ratio", "value_type": "number",  "numeric_value": setback_ratio},
            {"name": "direction",     "value_type": "string",  "string_value": direction},
            {"name": "direction_sign","value_type": "number",  "numeric_value": direction_sign},
            {"name": "shift_per_level","value_type": "vector", "vector_value": [0.0, 0.0, 0.0]}
        ],
        "semantic_role": "massing_modifier"
    }

def split_wing_node(input_id, axis="x", gap_ratio=0.22, access_side="east"):
    return {
        "id": "book02_split_wing",
        "kind": "macro",
        "operator": "split_wing",
        "inputs": [input_id],
        "parameters": [
            {"name": "axis",                    "value_type": "string",  "string_value": axis},
            {"name": "gap_ratio",               "value_type": "number",  "numeric_value": gap_ratio},
            {"name": "height_ratio",            "value_type": "number",  "numeric_value": 1.0},
            {"name": "bridge",                  "value_type": "boolean", "bool_value": False},
            {"name": "ground_spine",            "value_type": "boolean", "bool_value": False},
            {"name": "ground_spine_width_ratio","value_type": "number",  "numeric_value": 0.10},
            {"name": "ground_spine_height_ratio","value_type":"number",  "numeric_value": 0.20},
            {"name": "access_side",             "value_type": "string",  "string_value": access_side},
            {"name": "layout",                  "value_type": "string",  "string_value": "split"},
            {"name": "connector_width_ratio",   "value_type": "number",  "numeric_value": 0.15}
        ],
        "semantic_role": "public_threshold"
    }

def courtyard_node(input_id, margin_ratio=0.30, open_side="east"):
    return {
        "id": "book02_courtyard",
        "kind": "macro",
        "operator": "courtyard",
        "inputs": [input_id],
        "parameters": [
            {"name": "margin_ratio", "value_type": "number", "numeric_value": margin_ratio},
            {"name": "open_side",    "value_type": "string", "string_value": open_side}
        ],
        "semantic_role": "public_threshold"
    }

def carve_void_node(input_id, margin_ratio=0.28, open_side="east", node_id="book02_carve_void"):
    return {
        "id": node_id,
        "kind": "macro",
        "operator": "carve_void",
        "inputs": [input_id],
        "parameters": [
            {"name": "margin_ratio", "value_type": "number", "numeric_value": margin_ratio},
            {"name": "open_side",    "value_type": "string", "string_value": open_side}
        ],
        "semantic_role": "massing_modifier"
    }

# ═══════════════════════════════════════════════
# 6 GEOMETRY PROGRAMS
# ═══════════════════════════════════════════════

geometry_programs = []

# ─────────────────────────────────────────────
# D01: Full piloti lift — 1/1 long_axis + lift
# Path: c144847443af1c87205dd730cbe8a356edde3bce733df7d08a2130b4dcce7561
# 1/1 long_axis carve v1 (different from comp25 d01 which used carve v0)
# Strategy: full building raised on piloti, entire ~1463m² ground freed for parking
# Expected: ~49 surface spaces become possible on full ground plane under/around piloti
# ─────────────────────────────────────────────
bvn = book_base_volume_node("1/1", "long_axis")
ln  = lift_node(bvn["id"], rise_ratio=0.21, support_ratio=0.07, access_side="east")
nodes_d01 = base_nodes() + [bvn, ln]

geometry_programs.append({
    "schema_version": "arr.maas.geometry_program.v1",
    "name": "comp26_d01_full_piloti_lift_v1",
    "book_composition_path_id": "book:path:c144847443af1c87205dd730cbe8a356edde3bce733df7d08a2130b4dcce7561",
    "root_id": ln["id"],
    "rationale": (
        "Full building lifted on piloti at rise_ratio=0.21 (one full storey clearance = ~3.8m) "
        "over a 1/1 long_axis base volume. Exposes the complete site ground (available ~1463m²) "
        "for surface parking. With 11m single-loaded module, ~133m run available → ~49+ stalls "
        "reachable along SE access frontage. Spatial principle preserved: compact-tall parent form "
        "maintained. Tradeoff: ground floor lost to piloti, structural engineering of piloti grid required. "
        "Rise_ratio=0.21 vs comp25 d01 rise_ratio=0.20 uses a slightly higher clearance for SE ramp access."
    ),
    "dimensional_intent": dimensional_intent(),
    "nodes": nodes_d01,
    "metadata": {
        "parking_repair_response": "Addresses 45 unmet spaces by exposing full ~1463m² ground plane. Full piloti lifts entire building; no surface obstruction below. SE access frontage is clear.",
        "unresolved_conflicts": "Piloti structure not engineered; column clearance within 6m drive aisle unverified. Swept path, access ramp and accessible space position within piloti plan unverified.",
        "parent_shape_id": PARENT_SHAPE_ID
    }
})

# ─────────────────────────────────────────────
# D02: Half-bar NW compress + terrace — 1/2 long_axis + terrace
# Path: 5913f0e2c58eec630015ded8e617c79e1afb6d04ad88bf02b342f013d1d1e2b3
# 1/2 long_axis compress v9
# Strategy: building compressed to NW half of site, SE half (~730m²) fully open for parking
# Terrace setback reduces upper floors toward SE, clearing even more sky at SE
# ─────────────────────────────────────────────
bvn2 = book_base_volume_node("1/2", "long_axis")
tn2  = terrace_node(bvn2["id"], levels=2, setback_ratio=0.25, direction="x", direction_sign=1.0)
nodes_d02 = base_nodes() + [bvn2, tn2]

geometry_programs.append({
    "schema_version": "arr.maas.geometry_program.v1",
    "name": "comp26_d02_half_bar_nw_terrace",
    "book_composition_path_id": "book:path:5913f0e2c58eec630015ded8e617c79e1afb6d04ad88bf02b342f013d1d1e2b3",
    "root_id": tn2["id"],
    "rationale": (
        "Building compressed to NW half (1/2 long_axis) of parcel, leaving SE ~730m² open for surface parking. "
        "Terrace step-back at levels=2 setback_ratio=0.25 reduces upper floor SE projection, maximizing solar "
        "access at SE parking court and reducing overhang on SE access frontage. "
        "SE half allows a double-loaded 90° module (16m depth) × ~45m frontage → ~45 stalls possible. "
        "Spatial principle preserved: compact-bar form with SE open court. "
        "Tradeoff: target GFA 4907m² constrained to ~2453m² footprint × 5 floors → GFA ~4906m² if building occupies full 1/2; "
        "terrace reduces upper floor area, reported separately. Sunlight setback applied to N side."
    ),
    "dimensional_intent": dimensional_intent(),
    "nodes": nodes_d02,
    "metadata": {
        "parking_repair_response": "Frees SE ~730m² for surface parking. At 11m single-loaded: 45m/2.5m = 18 stalls/row × 2 rows min = 36; double-loaded 16m × 45m frontage allows more. Still 9 spaces unresolved without piloti.",
        "unresolved_conflicts": "GFA delivery with terrace setback reduces upper floors. Whether 49 spaces fit in SE court depends on exact parcel geometry and drive aisle routing, not proven at mass stage.",
        "parent_shape_id": PARENT_SHAPE_ID
    }
})

# ─────────────────────────────────────────────
# D03: Split wing — 1/1 short_axis + split_wing
# Path: 0b8b1dde940992806b77f36f97d2fa904452be4c3fafe28a92f1521f37d718f6
# 1/1 short_axis carve v1 (different orientation from comp25 d03)
# Strategy: two wings separated by central gap, parking in gap and at SE
# ─────────────────────────────────────────────
bvn3 = book_base_volume_node("1/1", "short_axis")
swn3 = split_wing_node(bvn3["id"], axis="x", gap_ratio=0.22, access_side="east")
nodes_d03 = base_nodes() + [bvn3, swn3]

geometry_programs.append({
    "schema_version": "arr.maas.geometry_program.v1",
    "name": "comp26_d03_split_wing_short_axis",
    "book_composition_path_id": "book:path:0b8b1dde940992806b77f36f97d2fa904452be4c3fafe28a92f1521f37d718f6",
    "root_id": swn3["id"],
    "rationale": (
        "Full-site 1/1 short_axis body split into two parallel wings along x-axis with gap_ratio=0.22 "
        "(~11m clear gap for a 50m-wide site). Central gap provides a double-loaded parking aisle. "
        "Wings oriented with short axis along road, east side facing SE access frontage. "
        "Gap doubles as pedestrian-vehicle shared zone: 6m drive aisle + 5m stall × 2 rows = 16m, "
        "fitting ~12 stalls in central gap. SE forecourt adds more. "
        "Short-axis orientation differs from comp25 d03 (which used long_axis). "
        "Tradeoff: gap_ratio=0.22 delivers ~11m clear gap but splits GFA across two wings; core adjacency and "
        "vertical circulation must be distributed."
    ),
    "dimensional_intent": dimensional_intent(),
    "nodes": nodes_d03,
    "metadata": {
        "parking_repair_response": "Central gap between wings provides 6m drive aisle + bilateral 5m stall rows. Forecourt at SE adds additional row. Combined may approach 30-45 stalls; still short of 49 without lift.",
        "unresolved_conflicts": "Column clearance in drive gap unverified. gap_ratio=0.22 delivers ~11m which meets 6m aisle + 2.5m stall on one side only; double-loaded needs 16m or gap_ratio=0.30.",
        "parent_shape_id": PARENT_SHAPE_ID
    }
})

# ─────────────────────────────────────────────
# D04: 3/8 L-shape vertical + lift (L on piloti)
# Path: 30c75c49ca9f85b52595a706bd354de4ad2a818d6bdbfb74990f9178f0f46470
# 3/8 vertical carve v2
# Strategy: L-shaped mass occupying 3/8 NW, entire SE quadrant + space freed for parking
# Lift exposes ground under L for parking access
# ─────────────────────────────────────────────
bvn4 = book_base_volume_node("3/8", "vertical")
ln4  = lift_node(bvn4["id"], rise_ratio=0.20, support_ratio=0.07, access_side="east")
nodes_d04 = base_nodes() + [bvn4, ln4]

geometry_programs.append({
    "schema_version": "arr.maas.geometry_program.v1",
    "name": "comp26_d04_l_shape_vertical_lift",
    "book_composition_path_id": "book:path:30c75c49ca9f85b52595a706bd354de4ad2a818d6bdbfb74990f9178f0f46470",
    "root_id": ln4["id"],
    "rationale": (
        "L-shaped mass (3/8 vertical — three octants of the unit cube) lifted on piloti, "
        "leaving the open 5/8 ground quadrant and the under-piloti ground for parking. "
        "The L wraps NW corner of parcel; SE arm of L is elevated. "
        "Combined available ground = ~1463m² (full site) since lift exposes the full ground plane. "
        "Spatial strategy: compact-tall L on stilts, SE corner fully open. "
        "At rise_ratio=0.20 (one floor ~3.8m) the entire footprint ground is accessible. "
        "Different from comp25 d04 (3/8 long_axis + lift); this uses vertical orientation. "
        "Tradeoff: 3/8 GFA = ~3680m² at 5 floors (below 4907m² target); delivered area reported separately."
    ),
    "dimensional_intent": dimensional_intent(),
    "nodes": nodes_d04,
    "metadata": {
        "parking_repair_response": "Full site ground exposed by piloti; SE forecourt + under-L space provides ~1463m² for parking. Sufficient area for 49 spaces at 11m single-loaded module.",
        "unresolved_conflicts": "3/8 base volume delivers ~3680m² GFA at 5 floors vs target 4907m² — area shortfall ~1227m². Conflict declared; target cannot be met with 3/8 volume without adding floors.",
        "parent_shape_id": PARENT_SHAPE_ID
    }
})

# ─────────────────────────────────────────────
# D05: Courtyard U-court open SE — 1/1 vertical + courtyard
# Path: dcf4f6b2610028a1ea593f9c6ad7ad20003a019bd088460607413aab2ca09d73
# 1/1 vertical carve v5
# Strategy: full-site mass with SE-open courtyard, court accessible from SE access frontage
# ─────────────────────────────────────────────
bvn5 = book_base_volume_node("1/1", "vertical")
cyn5 = courtyard_node(bvn5["id"], margin_ratio=0.32, open_side="east")
nodes_d05 = base_nodes() + [bvn5, cyn5]

geometry_programs.append({
    "schema_version": "arr.maas.geometry_program.v1",
    "name": "comp26_d05_courtyard_vertical_se_open",
    "book_composition_path_id": "book:path:dcf4f6b2610028a1ea593f9c6ad7ad20003a019bd088460607413aab2ca09d73",
    "root_id": cyn5["id"],
    "rationale": (
        "Full-site 1/1 vertical body with SE-open courtyard (margin_ratio=0.32). "
        "The U-plan opens on the east side where the SE vehicle access frontage runs. "
        "Court area = 0.32 × site depth × 0.32 × site width ≈ 200-300m² interior void, "
        "accessed from SE edge. Exterior ground at SE adds further parking area. "
        "Three-sided occupied mass wraps N, W, S; court opens to SE road. "
        "Spatial principle: compact-tall U-court parent form; courtyard organizes civic entry. "
        "Differs from comp25 d05 (same principle but margin_ratio=0.30 vs 0.32 and 1/1 vertical vs vertical). "
        "Tradeoff: interior court provides limited parking area; exterior SE strip is main parking zone. "
        "Court and SE together may not reach 49 spaces without piloti on building mass."
    ),
    "dimensional_intent": dimensional_intent(),
    "nodes": nodes_d05,
    "metadata": {
        "parking_repair_response": "SE-open court (~200-300m²) + SE exterior strip (~400m²) = ~600-700m² parking area. At 11m module: ~55-63 spaces possible if lot is clear, but building projection reduces available area.",
        "unresolved_conflicts": "Building footprint of U-body still occupies ~800-900m² at ground. Remaining ~600m² may not accommodate full 49 spaces in 90° grid. Shortfall likely 15-25 spaces without piloti.",
        "parent_shape_id": PARENT_SHAPE_ID
    }
})

# ─────────────────────────────────────────────
# D06: Ultra-compact 1/16 tower + lift (max ground release)
# Path: 182e5d8ea0a606a28832a77e9c2dc010d51341b383954cab0d36f89f1548cd8a
# 1/16 vertical compress v8
# Strategy: minimal-footprint tower (~62m²) on piloti, entire ~1400m² freed for parking
# ─────────────────────────────────────────────
bvn6 = book_base_volume_node("1/16", "vertical")
ln6  = lift_node(bvn6["id"], rise_ratio=0.20, support_ratio=0.07, access_side="east")
nodes_d06 = base_nodes() + [bvn6, ln6]

geometry_programs.append({
    "schema_version": "arr.maas.geometry_program.v1",
    "name": "comp26_d06_compact_tower_piloti",
    "book_composition_path_id": "book:path:182e5d8ea0a606a28832a77e9c2dc010d51341b383954cab0d36f89f1548cd8a",
    "root_id": ln6["id"],
    "rationale": (
        "Ultra-compact 1/16 vertical tower on full piloti. "
        "1/16 footprint ≈ 62m² plan (√(2499.7/16) ~ 12.5m × 5m), 5 floors → GFA ~310m²; "
        "far below 4907m² target — area conflict declared. "
        "Entire site ground (~1463m²) freed for surface parking under and around tower. "
        "Sufficient for 49+ stalls in 90° grid along SE access edge. "
        "This child tests the spatial extreme: maximum parking, minimum GFA. "
        "Spatial principle: vertical slender tower on open public ground plane, civic plaza around it. "
        "Tradeoff: GFA ~310m² vs target 4907m² — massive shortfall. "
        "Not a viable development alternative unless programme is radically reduced; "
        "presented as a bound on parking versus GFA tradeoff."
    ),
    "dimensional_intent": dimensional_intent(),
    "nodes": nodes_d06,
    "metadata": {
        "parking_repair_response": "Full site ground exposed. ~1463m² available; well above the ~539m² needed for 49 spaces at 11m single-loaded module. All 49 spaces reachable.",
        "unresolved_conflicts": "CRITICAL: 1/16 volume delivers ~310m² GFA vs target 4907m². This is a ~94% GFA shortfall. Presented as a spatial bound only; not a compliant development alternative without programme revision.",
        "parent_shape_id": PARENT_SHAPE_ID
    }
})

# ═══════════════════════════════════════════════
# ASSEMBLE PAYLOAD
# ═══════════════════════════════════════════════

payload = {
    "mode": "exact-authored-development",
    "inherit_parent_dimensions": True,
    "parent": PARENT,
    "parent_shape_id": PARENT_SHAPE_ID,
    "parent_program_hash": PARENT_PROGRAM_HASH,
    "geometry_programs": geometry_programs
}

# Validate
sys.path.insert(0, r"D:\Data\25_ACE\ARR\backend")
from design.maas.book_development import validate_development_payload

ctx = {
    "parent": PARENT,
    "parent_shape_id": PARENT_SHAPE_ID,
    "parent_program_hash": PARENT_PROGRAM_HASH,
    "parent_certificate_id": "2331653a23b9f22c1e23",
    "site_pnu": "4115011300106840001",
    "storey_count": STOREY_COUNT,
    "storey_height_m": STOREY_HEIGHT_M,
    "target_gfa_m2": TARGET_GFA_M2,
    "height_m": HEIGHT_M,
    "offered_path_ids": [g["book_composition_path_id"] for g in geometry_programs]
}

print("Validating payload...")
try:
    result = validate_development_payload(payload, ctx, expected_count=6)
    print("VALIDATION RESULT:", result)
    print("PASSED — writing output.")

    out_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Written to {out_path}")

except Exception as e:
    print("VALIDATION FAILED:", e)
    import traceback
    traceback.print_exc()
    print("\nWriting anyway for inspection...")
    out_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-develop-comp26.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Written to {out_path} (unvalidated)")
