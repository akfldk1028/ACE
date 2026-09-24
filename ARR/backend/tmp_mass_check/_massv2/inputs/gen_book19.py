"""
Generator for 12 BOOK programs for cycle-comp19.
Site: Uijeongbu Gosan public1, PNU 4115011300106840001
Access: east, 5 storeys, BCR 60%, FAR 250%
capacity_ceiling_m2: 6241.962, ground_capacity_m2: 1497.877
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json

# ── helpers ──────────────────────────────────────────────────────────────────

def n_num(name, val):
    return {"name": name, "value_type": "number", "numeric_value": float(val)}

def n_str(name, val):
    return {"name": name, "value_type": "string", "string_value": str(val)}

def n_bool(name, val):
    return {"name": name, "value_type": "boolean", "boolean_value": bool(val)}

def n_vec(name, val):
    return {"name": name, "value_type": "vector", "vector_value": list(val)}

def n_mat4(name):
    return {"name": name, "value_type": "matrix4",
            "matrix4_value": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}

def n_lit(name, string_val):
    """Literal-kind param: value_type='string' for string literals"""
    return {"name": name, "value_type": "string", "string_value": string_val}

def node(id_, kind, op, inputs, params, role):
    return {"id": id_, "kind": kind, "operator": op,
            "inputs": inputs, "parameters": params, "semantic_role": role}

# ── base seed node triples ───────────────────────────────────────────────────

def box_node(id_="b0"):
    return node(id_, "primitive", "box", [],
                [n_num("width",1.0), n_num("depth",1.0), n_num("height",1.0), n_bool("center",True)],
                "dominant_mass")

def scale_node(id_="s0", inp="b0", vec=None):
    if vec is None:
        vec = [1.0,1.0,1.0]
    return node(id_, "transform", "scale", [inp], [n_vec("vector", vec)], "dominant_mass")

def mat4_node(id_="m0", inp="s0"):
    return node(id_, "transform", "matrix4", [inp], [n_mat4("matrix4")], "dominant_mass")

# Seeds: block=[1,1,1], slab=[2.2,1.45,0.28], bar=[2.8,0.62,0.48], tower=[0.68,0.68,2.5]
SEEDS = {
    "block":  [1.0,  1.0,   1.0],
    "slab":   [2.2,  1.45,  0.28],
    "bar":    [2.8,  0.62,  0.48],
    "tower":  [0.68, 0.68,  2.5],
}

def seed_triple(seed, box_id="b0", sc_id="s0", mat_id="m0"):
    return [box_node(box_id), scale_node(sc_id, box_id, SEEDS[seed]), mat4_node(mat_id, sc_id)]

def dim_intent(storeys, storey_h, gfa):
    return {
        "schema_version": "arr.maas.dimensional_intent.v1",
        "storey_count": storeys,
        "storey_height_m": storey_h,
        "target_gfa_m2": float(gfa),
        "delivery_policy": "preserve_physical_dimensions",
        "programme_status": "unknown"
    }

# ── 12 distinct programs ──────────────────────────────────────────────────────

programs = []

# ─────────────────────────────────────────────────────────────
# P01: slab + bend axis x → courtyard open east
# Path: book:path:53c55b4da48903af110459fa120baeaec3b186edf22d6890fa718d0ad6b1f5b5
# Principle: bend+stack aggregation (short_axis, 3/8)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p01_slab_bend_court",
    "base_form_id": "cube",
    "base_seed": "slab",
    "book_composition_path_id": "book:path:53c55b4da48903af110459fa120baeaec3b186edf22d6890fa718d0ad6b1f5b5",
    "intent_tags": ["bend","courtyard","east_access","public_office"],
    "rationale": "A slab bent on x-axis creates a curved C-arm; a courtyard inscribed open to the east gives the public threshold. Slab proportion 2.2×1.45×0.28 allows the bend to read as a single arc in plan without closing the court.",
    "dimensional_intent": dim_intent(4, 3.5, 1350.0),
    "root_id": "acc",
    "nodes": seed_triple("slab") + [
        node("bnd","modifier","bend",["m0"],
             [n_str("axis","x"), n_num("angle_degrees",24.0), n_num("subdivisions",4.0)],
             "dominant_mass"),
        node("acc","macro","courtyard",["bnd"],
             [n_num("margin_ratio",0.28), n_str("open_side","east")],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P02: bar + interlock axis x → notch east
# Path: book:path:05470e618703ead632e6029bac7312306f05a6f404cb1a84f60043e0fb2b6b5f
# Principle: interlock (vertical, 1/1)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p02_bar_interlock_notch",
    "base_form_id": "cube",
    "base_seed": "bar",
    "book_composition_path_id": "book:path:05470e618703ead632e6029bac7312306f05a6f404cb1a84f60043e0fb2b6b5f",
    "intent_tags": ["interlock","bar","notch","public_office"],
    "rationale": "Two bar volumes interlock at their shared zone (axis x, bar_ratio 0.38); a corner notch at the east face creates the address entry. Interlocking bars at plan level create an L-shaped occupation without discontinuity.",
    "dimensional_intent": dim_intent(4, 3.5, 1200.0),
    "root_id": "acc",
    "nodes": seed_triple("bar") + [
        node("ilk","macro","interlock_related",["m0"],
             [n_str("axis","x"),
              n_num("angle_degrees", 0.0),
              n_num("bar_ratio", 0.38),
              n_num("distance_ratio", 0.22),
              n_num("outward_sign", 1.0)],
             "dominant_mass"),
        node("acc","macro","notch",["ilk"],
             [n_str("side","east"), n_num("ratio", 0.22), n_num("height_ratio", 0.7)],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P03: tower + tapered_tower → carve_void east
# Path: book:path:b161eb4c3bb6230cd34980d091fc44bf52f7d2648e59f55b39dc46e64225dc46
# Principle: twist (vertical, 1/4)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p03_tower_twist_carve",
    "base_form_id": "cube",
    "base_seed": "tower",
    "book_composition_path_id": "book:path:b161eb4c3bb6230cd34980d091fc44bf52f7d2648e59f55b39dc46e64225dc46",
    "intent_tags": ["twist","tower","carve_void","public_office"],
    "rationale": "Tower seed twisted on z-axis 32 degrees (4 subdivisions) produces a continuously rotating plan section that resolves at ground into an east-facing carve void entry. Twist precedes the threshold so the access relation reads against the un-twisted base.",
    "dimensional_intent": dim_intent(5, 3.5, 900.0),
    "root_id": "acc",
    "nodes": seed_triple("tower") + [
        node("twi","modifier","twist",["m0"],
             [n_str("axis","z"), n_num("angle_degrees",32.0), n_num("subdivisions",4.0)],
             "dominant_mass"),
        node("acc","macro","carve_void",["twi"],
             [n_num("margin_ratio",0.30), n_str("open_side","east")],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P04: slab + taper z + book_branch → notch east
# Path: book:path:0bac03a066888497ad4cdc5a727e609bdb620a3ef13ef9cc5394a46de7a09449
# Principle: taper+bend combo (long_axis, 1/4)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p04_slab_taper_branch_notch",
    "base_form_id": "cube",
    "base_seed": "slab",
    "book_composition_path_id": "book:path:0bac03a066888497ad4cdc5a727e609bdb620a3ef13ef9cc5394a46de7a09449",
    "intent_tags": ["taper","branch","notch","slab","public_office"],
    "rationale": "A slab tapered on z-axis (end_scale 0.6×0.6 at top) gives a pyramidal section. A book_branch at 0 degrees with arm_ratio 0.35 extends a compact arm eastward. The notch at east edge signals the entry without interrupting the taper.",
    "dimensional_intent": dim_intent(4, 3.5, 1100.0),
    "root_id": "acc",
    "nodes": seed_triple("slab") + [
        node("tap","modifier","taper",["m0"],
             [n_str("axis","z"), n_vec("end_scale",[0.62, 0.62]),
              n_num("subdivisions", 3.0)],
             "dominant_mass"),
        node("brn","macro","book_branch",["tap"],
             [n_num("angle_degrees", 0.0),
              n_num("arm_ratio", 0.35),
              n_num("trunk_ratio", 0.65),
              n_str("vertical_anchor","input_base")],
             "dominant_mass"),
        node("acc","macro","notch",["brn"],
             [n_str("side","east"), n_num("ratio", 0.20), n_num("height_ratio", 0.6)],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P05: bar + book_fracture → courtyard east
# Path: book:path:9042c82e97a383fc1f1e97948ac87e0bac17a95d0d8587255d48710c0ac64040
# Principle: fracture (long_axis, 1/1)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p05_bar_fracture_court",
    "base_form_id": "cube",
    "base_seed": "bar",
    "book_composition_path_id": "book:path:9042c82e97a383fc1f1e97948ac87e0bac17a95d0d8587255d48710c0ac64040",
    "intent_tags": ["fracture","bar","courtyard","public_office"],
    "rationale": "A bar fractured at 22 degrees creates a wedge gap that opens toward the east; a courtyard at east follows as the public court bounded by the angled fracture face. The fracture's directional bias (outward_sign +1) pushes the break away from the road.",
    "dimensional_intent": dim_intent(4, 3.5, 1280.0),
    "root_id": "acc",
    "nodes": seed_triple("bar") + [
        node("frc","macro","book_fracture",["m0"],
             [n_str("axis","x"),
              n_num("angle_degrees", 22.0),
              n_num("gap_ratio", 0.08),
              n_num("outward_sign", 1.0),
              n_num("retained_back_ratio", 0.55)],
             "dominant_mass"),
        node("acc","macro","courtyard",["frc"],
             [n_num("margin_ratio",0.30), n_str("open_side","east")],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P06: block + inflate z + boundary_expand → notch east
# Path: book:path:423e633a08a43369b6ccda29d5604fc061c6e20e52e460c9867ddd1e5b13c2c0
# Principle: inflate (short_axis, 3/8)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p06_block_inflate_expand_notch",
    "base_form_id": "elliptical",
    "base_seed": "block",
    "book_composition_path_id": "book:path:423e633a08a43369b6ccda29d5604fc061c6e20e52e460c9867ddd1e5b13c2c0",
    "intent_tags": ["inflate","boundary_expand","notch","public_office"],
    "rationale": "A block inflated on z-axis produces a swollen crown section. Boundary_expand on x-axis (+0.18) enlarges the east elevation for the street interface. Notch at east signals the entry within the inflated facade.",
    "dimensional_intent": dim_intent(4, 3.5, 1050.0),
    "root_id": "acc",
    "nodes": seed_triple("block") + [
        node("inf","modifier","inflate",["m0"],
             [n_str("axis","z"), n_num("factor", 1.22),
              n_num("subdivisions", 4.0),
              n_num("profile_power", 1.8),
              n_num("middle_scale", 1.15)],
             "dominant_mass"),
        node("bex","macro","boundary_expand",["inf"],
             [n_str("axis","x"), n_num("amount", 0.18),
              n_num("shoulder_fraction", 0.35)],
             "dominant_mass"),
        node("acc","macro","notch",["bex"],
             [n_str("side","east"), n_num("ratio", 0.25), n_num("height_ratio", 0.55)],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P07: bar + overlap_related x → carve_void east
# Path: book:path:aadaf4340a4980ec0c691cf6c70bf78936b4b4b1471a6340d384abcae9ee0a2c
# Principle: overlap+expand case study (vertical, 1/1)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p07_bar_overlap_carve",
    "base_form_id": "cube",
    "base_seed": "bar",
    "book_composition_path_id": "book:path:aadaf4340a4980ec0c691cf6c70bf78936b4b4b1471a6340d384abcae9ee0a2c",
    "intent_tags": ["overlap","bar","carve_void","public_office"],
    "rationale": "Two bar volumes partially overlap on the y-axis (shift_ratio 0.38, slab_ratio 0.45) forming an H-plan that stays one connected solid. The carve_void at east opens the shared zone as public court between the arms.",
    "dimensional_intent": dim_intent(4, 3.5, 1400.0),
    "root_id": "acc",
    "nodes": seed_triple("bar") + [
        node("ovl","macro","overlap_related",["m0"],
             [n_str("axis","y"),
              n_num("shift_ratio", 0.38),
              n_num("slab_ratio", 0.45),
              n_num("outward_sign", 1.0),
              n_num("vertical_overlap", 0.65)],
             "dominant_mass"),
        node("acc","macro","carve_void",["ovl"],
             [n_num("margin_ratio",0.28), n_str("open_side","east")],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P08: slab + shear z/x + book_split → notch east
# Path: book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb
# Principle: compress (long_axis, 1/2)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p08_slab_shear_split_notch",
    "base_form_id": "cube",
    "base_seed": "slab",
    "book_composition_path_id": "book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb",
    "intent_tags": ["shear","book_split","notch","slab","public_office"],
    "rationale": "A slab is sheared on z-axis in x-direction (amount 0.28) creating an oblique top face; book_split on x-axis opens a hinged gap at the long side. Notch at east edge is the entry within the shear-faced elevation.",
    "dimensional_intent": dim_intent(4, 3.5, 1180.0),
    "root_id": "acc",
    "nodes": seed_triple("slab") + [
        node("shr","transform","shear",["m0"],
             [n_str("axis","z"),
              {"name":"direction","value_type":"string","string_value":"x"},
              n_num("amount", 0.28),
              n_vec("pivot",[0.0, 0.0, 0.0])],
             "dominant_mass"),
        node("spl","macro","book_split",["shr"],
             [n_str("axis","x"),
              n_num("angle_degrees", 18.0),
              n_num("gap_ratio", 0.06),
              n_num("outward_sign", 1.0),
              n_num("terminal_ratio", 0.42),
              n_num("branch_sign", 1.0),
              n_num("split_generation", 1.0),
              {"name":"access_side","value_type":"string","string_value":"east"}],
             "dominant_mass"),
        node("acc","macro","notch",["spl"],
             [n_str("side","east"), n_num("ratio",0.20), n_num("height_ratio",0.55)],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P09: bar + bend+branch combo → lift east
# Path: book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e
# Principle: bend+branch combo (long_axis, 3/8)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p09_bar_bend_branch_lift",
    "base_form_id": "cube",
    "base_seed": "bar",
    "book_composition_path_id": "book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e",
    "intent_tags": ["bend","book_branch","lift","bar","public_office"],
    "rationale": "A bar is bent 20 degrees on x-axis; a branch extends perpendicular at 90 degrees (arm_ratio 0.42) for an L-plan. Lift at east creates a pilotis entry zone under the bend's lower chord. The branch extends away from the road.",
    "dimensional_intent": dim_intent(4, 3.8, 1320.0),
    "root_id": "acc",
    "nodes": seed_triple("bar") + [
        node("bnd","modifier","bend",["m0"],
             [n_str("axis","x"), n_num("angle_degrees",20.0), n_num("subdivisions",4.0)],
             "dominant_mass"),
        node("brn","macro","book_branch",["bnd"],
             [n_num("angle_degrees", 90.0),
              n_num("arm_ratio", 0.42),
              n_num("trunk_ratio", 0.58),
              n_str("vertical_anchor","input_base")],
             "dominant_mass"),
        node("acc","macro","lift",["brn"],
             [n_str("access_side","east"),
              n_num("rise_ratio", 0.25),
              n_num("support_ratio", 0.18)],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P10: slab + profiled_hall barrel + notch east
# Path: book:path:eccfafc4718361d6aec40a901f53b344d4bff77683f4887715da5adcce05157f
# Principle: inflate (short_axis, 1/2)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p10_slab_profiled_hall_notch",
    "base_form_id": "cube",
    "base_seed": "slab",
    "book_composition_path_id": "book:path:eccfafc4718361d6aec40a901f53b344d4bff77683f4887715da5adcce05157f",
    "intent_tags": ["profiled_hall","barrel","slab","notch","public_office"],
    "rationale": "A slab receives a barrel profiled_hall spanning the y-axis: the cross-section is a continuous barrel vault. Notch at east side is the public entry reading as the low point of the vault section against the street.",
    "dimensional_intent": dim_intent(4, 3.5, 1150.0),
    "root_id": "acc",
    "nodes": seed_triple("slab") + [
        node("phl","macro","profiled_hall",["m0"],
             [n_str("section_family","barrel"),
              n_str("span_axis","y"),
              {"name":"section_controls","value_type":"structured_json",
               "structured_json": json.dumps({"rise": 0.35, "bays": 1})}],
             "dominant_mass"),
        node("acc","macro","notch",["phl"],
             [n_str("side","east"), n_num("ratio",0.25), n_num("height_ratio",0.6)],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P11: slab + split_wing x bridge → notch east
# Path: book:path:9c9d6d2d18bf525d39eb0c2299651d643b20f3f3e0de68975addd59e346d58d2
# Principle: branch+pack+stack aggregation (short_axis, 1/2)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p11_slab_split_wing_notch",
    "base_form_id": "cube",
    "base_seed": "slab",
    "book_composition_path_id": "book:path:9c9d6d2d18bf525d39eb0c2299651d643b20f3f3e0de68975addd59e346d58d2",
    "intent_tags": ["split_wing","slab","notch","public_office"],
    "rationale": "A slab split into two parallel wings along the x-axis (gap_ratio 0.10, bridge=true) creates a double-bar plan connected by a bridge spine. Notch at east marks the entry between the wings where the bridge meets the street.",
    "dimensional_intent": dim_intent(4, 3.5, 1250.0),
    "root_id": "acc",
    "nodes": seed_triple("slab") + [
        node("sw","macro","split_wing",["m0"],
             [n_str("axis","x"),
              n_num("gap_ratio", 0.12),
              n_bool("bridge", True),
              n_str("access_side","east"),
              n_str("layout","parallel"),
              n_num("height_ratio", 0.95),
              n_num("connector_width_ratio", 0.22),
              n_bool("ground_spine", False)],
             "dominant_mass"),
        node("acc","macro","notch",["sw"],
             [n_str("side","east"), n_num("ratio",0.22), n_num("height_ratio",0.55)],
             "public_threshold"),
    ]
}
programs.append(p)

# ─────────────────────────────────────────────────────────────
# P12: tower + book_branch x2 combo → carve_void east
# Path: book:path:def59b665a24ebd51c08a3812668edc1a6131552a8055b2d7cb88de8de90f4f5
# Principle: branch+branch combo (vertical, 3/8)
# ─────────────────────────────────────────────────────────────
p = {
    "name": "p12_tower_branch_branch_carve",
    "base_form_id": "cube",
    "base_seed": "tower",
    "book_composition_path_id": "book:path:def59b665a24ebd51c08a3812668edc1a6131552a8055b2d7cb88de8de90f4f5",
    "intent_tags": ["book_branch","tower","carve_void","public_office"],
    "rationale": "A tower receives two sequential branches: first at 90 degrees (arm_ratio 0.38) then at -90 degrees (arm_ratio 0.30), creating a T-plan that steps away from the trunk. Carve_void at east opens the base of the trunk as the public court.",
    "dimensional_intent": dim_intent(5, 3.5, 1050.0),
    "root_id": "acc",
    "nodes": seed_triple("tower") + [
        node("brn1","macro","book_branch",["m0"],
             [n_num("angle_degrees", 90.0),
              n_num("arm_ratio", 0.38),
              n_num("trunk_ratio", 0.62),
              n_str("vertical_anchor","input_base")],
             "dominant_mass"),
        node("brn2","macro","book_branch",["brn1"],
             [n_num("angle_degrees", -90.0),
              n_num("arm_ratio", 0.30),
              n_num("trunk_ratio", 0.70),
              n_str("vertical_anchor","input_base")],
             "dominant_mass"),
        node("acc","macro","carve_void",["brn2"],
             [n_num("margin_ratio",0.28), n_str("open_side","east")],
             "public_threshold"),
    ]
}
programs.append(p)

# ── assemble payload ──────────────────────────────────────────────────────────

# Collect all unique principle ids used
book_principle_ids = list(set(p["book_composition_path_id"] for p in programs))
# The schema wants book_principle_ids at root: use principle_ids from the path offer
# Map path → principle_id
path_to_principle = {
    "book:path:53c55b4da48903af110459fa120baeaec3b186edf22d6890fa718d0ad6b1f5b5": "book:aggregation:stack:bend",
    "book:path:05470e618703ead632e6029bac7312306f05a6f404cb1a84f60043e0fb2b6b5f": "book:operative:interlock",
    "book:path:b161eb4c3bb6230cd34980d091fc44bf52f7d2648e59f55b39dc46e64225dc46": "book:operative:twist",
    "book:path:0bac03a066888497ad4cdc5a727e609bdb620a3ef13ef9cc5394a46de7a09449": "book:combination:15:taper+bend",
    "book:path:9042c82e97a383fc1f1e97948ac87e0bac17a95d0d8587255d48710c0ac64040": "book:operative:fracture",
    "book:path:423e633a08a43369b6ccda29d5604fc061c6e20e52e460c9867ddd1e5b13c2c0": "book:operative:inflate",
    "book:path:aadaf4340a4980ec0c691cf6c70bf78936b4b4b1471a6340d384abcae9ee0a2c": "book:case:64:overlap+expand",
    "book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb": "book:operative:compress",
    "book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e": "book:combination:16:bend+branch",
    "book:path:eccfafc4718361d6aec40a901f53b344d4bff77683f4887715da5adcce05157f": "book:operative:inflate",
    "book:path:9c9d6d2d18bf525d39eb0c2299651d643b20f3f3e0de68975addd59e346d58d2": "book:aggregation:pack+stack:branch",
    "book:path:def59b665a24ebd51c08a3812668edc1a6131552a8055b2d7cb88de8de90f4f5": "book:combination:07:branch+branch",
}

principle_ids = list(set(path_to_principle[p["book_composition_path_id"]] for p in programs))

payload = {
    "programs": programs,
    "book_principle_ids": principle_ids
}

# ── validate ──────────────────────────────────────────────────────────────────

import os, pathlib

schema_path = pathlib.Path("D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/runs/cycle-comp19/book-author/schema.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

try:
    from jsonschema import Draft7Validator
    v = Draft7Validator(schema)
    errors = list(v.iter_errors(payload))
    if errors:
        print(f"SCHEMA ERRORS: {len(errors)}")
        for e in errors[:20]:
            print(f"  PATH: {list(e.absolute_path)}")
            print(f"  MSG:  {e.message[:200]}")
            print()
    else:
        print("SCHEMA: OK - 0 errors")
except ImportError:
    print("jsonschema not available - skipping validation")

# ── write output ──────────────────────────────────────────────────────────────

out_path = "D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/inputs/book-comp19.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

print(f"\nWritten {len(programs)} programs to {out_path}")
print(f"File size: {os.path.getsize(out_path)} bytes")
print(f"book_principle_ids: {principle_ids}")

# Print program summary
for i, p in enumerate(programs):
    nodes_ops = [n['operator'] for n in p['nodes']]
    print(f"[{i+1:02d}] {p['name']}: seed={p['base_seed']}, ops={nodes_ops}")
