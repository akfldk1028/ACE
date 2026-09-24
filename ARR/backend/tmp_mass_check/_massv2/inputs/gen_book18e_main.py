"""
gen_book18e_main.py
Self-contained 120-program BOOK mass generator for cycle-comp18.
Includes all 78 builder functions plus main generation logic.
"""

import json, math, random, sys
from pathlib import Path

# ─── add jsonschema if available ────────────────────────────────────────────
try:
    from jsonschema import Draft7Validator
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False
    print("WARNING: jsonschema not available, skipping schema validation")

SCHEMA_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json"
OUTPUT_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json"

random.seed(42)

# ─── parameter helpers ───────────────────────────────────────────────────────

def num_p(name, v):
    return {"name": name, "value_type": "number", "numeric_value": float(v),
            "string_value": "", "boolean_value": False, "vector_value": [0,0,0],
            "structured_json": None}

def str_p(name, v):
    return {"name": name, "value_type": "string", "numeric_value": 0.0,
            "string_value": str(v), "boolean_value": False, "vector_value": [0,0,0],
            "structured_json": None}

def bool_p(name, v):
    return {"name": name, "value_type": "boolean", "numeric_value": 0.0,
            "string_value": "", "boolean_value": bool(v), "vector_value": [0,0,0],
            "structured_json": None}

def vec_p(name, v):
    return {"name": name, "value_type": "vector", "numeric_value": 0.0,
            "string_value": "", "boolean_value": False, "vector_value": list(v),
            "structured_json": None}

def lit_p(name, nv=0.0, sv="", bv=False, vv=None, sj=None):
    """Literal-type param — all 5 value fields."""
    return {"name": name, "value_type": "literal",
            "numeric_value": float(nv),
            "string_value": str(sv),
            "boolean_value": bool(bv),
            "vector_value": list(vv) if vv is not None else [0,0,0],
            "structured_json": sj}

def mat4_p(m):
    return {"name": "matrix4", "value_type": "matrix4",
            "numeric_value": 0.0, "string_value": "", "boolean_value": False,
            "vector_value": [0,0,0], "structured_json": None,
            "matrix4_value": m}

def identity_mat4():
    return [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

def scale_mat4(sx, sy, sz):
    return [[sx,0,0,0],[0,sy,0,0],[0,0,sz,0],[0,0,0,1]]

# ─── node constructors ────────────────────────────────────────────────────────

def box_node(nid, w=1.0, d=1.0, h=1.0, role="dominant_mass"):
    return {
        "id": nid, "kind": "primitive", "operator": "box", "inputs": [],
        "semantic_role": role,
        "parameters": [
            {"name": "width",  "value_type": "number", "numeric_value": float(w)},
            {"name": "depth",  "value_type": "number", "numeric_value": float(d)},
            {"name": "height", "value_type": "number", "numeric_value": float(h)},
            {"name": "center", "value_type": "boolean", "boolean_value": True},
        ]
    }

def mat4_node(nid, inp, m, role="dominant_mass"):
    return {
        "id": nid, "kind": "transform", "operator": "matrix4", "inputs": [inp],
        "semantic_role": role,
        "parameters": [mat4_p(m)]
    }

def courtyard_node(nid, inp, margin=0.25, open_side="east"):
    return {
        "id": nid, "kind": "macro", "operator": "courtyard", "inputs": [inp],
        "semantic_role": "public_threshold",
        "parameters": [num_p("margin_ratio", margin), str_p("open_side", open_side)]
    }

def carve_void_node(nid, inp, margin=0.25, open_side="east"):
    return {
        "id": nid, "kind": "macro", "operator": "carve_void", "inputs": [inp],
        "semantic_role": "public_threshold",
        "parameters": [num_p("margin_ratio", margin), str_p("open_side", open_side)]
    }

def notch_node(nid, inp, side="east", corner="ne", ratio=0.3, width_ratio=0.4, height_ratio=0.6):
    return {
        "id": nid, "kind": "macro", "operator": "notch", "inputs": [inp],
        "semantic_role": "public_threshold",
        "parameters": [
            str_p("side", side), str_p("corner", corner),
            num_p("ratio", ratio), num_p("width_ratio", width_ratio),
            num_p("height_ratio", height_ratio),
        ]
    }

def lift_node(nid, inp, access_side="east", rise_ratio=0.25, support_ratio=0.35):
    return {
        "id": nid, "kind": "macro", "operator": "lift", "inputs": [inp],
        "semantic_role": "public_threshold",
        "parameters": [
            str_p("access_side", access_side),
            lit_p("rise_ratio", nv=rise_ratio),
            lit_p("support_ratio", nv=support_ratio),
        ]
    }

def split_wing_node(nid, inp, access_side="east", axis="y", layout="parallel",
                     gap_ratio=0.12, height_ratio=0.9, bridge=True,
                     connector_width_ratio=0.25, ground_spine=False,
                     ground_spine_height_ratio=0.15, ground_spine_width_ratio=0.2):
    return {
        "id": nid, "kind": "macro", "operator": "split_wing", "inputs": [inp],
        "semantic_role": "public_threshold",
        "parameters": [
            str_p("access_side", access_side), str_p("axis", axis),
            str_p("layout", layout), num_p("gap_ratio", gap_ratio),
            num_p("height_ratio", height_ratio), bool_p("bridge", bridge),
            lit_p("connector_width_ratio", nv=connector_width_ratio),
            bool_p("ground_spine", ground_spine),
            lit_p("ground_spine_height_ratio", nv=ground_spine_height_ratio),
            lit_p("ground_spine_width_ratio", nv=ground_spine_width_ratio),
        ]
    }

def bend_node(nid, inp, axis="z", angle=25, subdivisions=4, role="dominant_mass"):
    return {
        "id": nid, "kind": "transform", "operator": "bend", "inputs": [inp],
        "semantic_role": role,
        "parameters": [str_p("axis", axis), num_p("angle_degrees", angle), num_p("subdivisions", subdivisions)]
    }

def taper_node(nid, inp, axis="z", start_scale=None, end_scale=None,
               lower_floor_fraction=0.0, subdivisions=3, role="dominant_mass"):
    if start_scale is None: start_scale = [1.0, 1.0]
    if end_scale is None: end_scale = [0.7, 0.7]
    return {
        "id": nid, "kind": "modifier", "operator": "taper", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), vec_p("start_scale", start_scale),
            vec_p("end_scale", end_scale),
            num_p("lower_floor_fraction", lower_floor_fraction),
            num_p("subdivisions", subdivisions),
            lit_p("scale_top", nv=end_scale[0]),
        ]
    }

def twist_node(nid, inp, axis="z", angle=20, subdivisions=4, role="dominant_mass"):
    return {
        "id": nid, "kind": "transform", "operator": "twist", "inputs": [inp],
        "semantic_role": role,
        "parameters": [str_p("axis", axis), num_p("angle_degrees", angle), num_p("subdivisions", subdivisions)]
    }

def shear_node(nid, inp, axis="z", amount=0.3, direction_vec=None, role="dominant_mass"):
    if direction_vec is None: direction_vec = [1.0, 0.0, 0.0]
    return {
        "id": nid, "kind": "transform", "operator": "shear", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), num_p("amount", amount),
            lit_p("direction", nv=0.0, sv="x", bv=False, vv=direction_vec),
            vec_p("pivot", [0.0, 0.0, 0.0]),
        ]
    }

def inflate_node(nid, inp, axis="z", factor=1.15, middle_scale=1.2, profile_power=2.0,
                 subdivisions=4, role="dominant_mass"):
    return {
        "id": nid, "kind": "modifier", "operator": "inflate", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), lit_p("factor", nv=factor),
            lit_p("middle_scale", nv=middle_scale),
            lit_p("profile_power", nv=profile_power),
            num_p("subdivisions", subdivisions),
        ]
    }

def pinch_node(nid, inp, axis="z", waist_ratio=0.5, waist_scale=0.7,
               profile_power=2.0, subdivisions=4, role="dominant_mass"):
    return {
        "id": nid, "kind": "modifier", "operator": "pinch", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), lit_p("waist_ratio", nv=waist_ratio),
            lit_p("waist_scale", nv=waist_scale),
            lit_p("profile_power", nv=profile_power),
            num_p("subdivisions", subdivisions),
        ]
    }

def book_branch_node(nid, inp, angle_degrees=45.0, trunk_ratio=0.6, arm_ratio=0.4,
                     vertical_anchor="input_base", role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "book_branch", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            num_p("angle_degrees", angle_degrees),
            lit_p("trunk_ratio", nv=trunk_ratio),
            lit_p("arm_ratio", nv=arm_ratio),
            str_p("vertical_anchor", vertical_anchor),
        ]
    }

def book_split_node(nid, inp, axis="y", angle_degrees=0.0, gap_ratio=0.1,
                    outward_sign=1.0, branch_sign=1.0, split_generation=1.0,
                    terminal_ratio=0.5, access_side_sv="east", role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "book_split", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), num_p("angle_degrees", angle_degrees),
            num_p("gap_ratio", gap_ratio),
            lit_p("outward_sign", nv=outward_sign),
            lit_p("branch_sign", nv=branch_sign),
            lit_p("split_generation", nv=split_generation),
            lit_p("terminal_ratio", nv=terminal_ratio),
            lit_p("access_side", sv=access_side_sv),
        ]
    }

def book_carve_node(nid, inp, axis="z", face_side="east", depth_ratio=0.3,
                    outward_sign=1.0, width_ratio=0.4, role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "book_carve", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), str_p("face_side", face_side),
            lit_p("depth_ratio", nv=depth_ratio),
            lit_p("outward_sign", nv=outward_sign),
            num_p("width_ratio", width_ratio),
        ]
    }

def book_extract_node(nid, inp, axis="z", face_side="east", distance_ratio=0.3,
                      guest_scale=0.5, outward_sign=1.0, role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "book_extract", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), str_p("face_side", face_side),
            lit_p("distance_ratio", nv=distance_ratio),
            lit_p("guest_scale", nv=guest_scale),
            lit_p("outward_sign", nv=outward_sign),
        ]
    }

def book_fracture_node(nid, inp, axis="z", angle_degrees=20.0, gap_ratio=0.12,
                       outward_sign=1.0, retained_back_ratio=0.6, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "book_fracture", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), num_p("angle_degrees", angle_degrees),
            num_p("gap_ratio", gap_ratio),
            lit_p("outward_sign", nv=outward_sign),
            lit_p("retained_back_ratio", nv=retained_back_ratio),
        ]
    }

def book_grade_node(nid, inp, axis="z", face_side="east", depth_ratio=0.25,
                    outward_sign=1.0, width_ratio=0.4, levels=3, role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "book_grade", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), str_p("face_side", face_side),
            lit_p("depth_ratio", nv=depth_ratio),
            lit_p("outward_sign", nv=outward_sign),
            num_p("width_ratio", width_ratio),
            num_p("levels", levels),
        ]
    }

def book_lift_node(nid, inp, axis="z", distance_ratio=0.3, guest_scale=0.6,
                   outward_sign=1.0, role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "book_lift", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            lit_p("distance_ratio", nv=distance_ratio),
            lit_p("guest_scale", nv=guest_scale),
            lit_p("outward_sign", nv=outward_sign),
        ]
    }

def book_lodge_node(nid, inp, axis="z", distance_ratio=0.25, guest_scale=0.5,
                    outward_sign=1.0, role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "book_lodge", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            lit_p("distance_ratio", nv=distance_ratio),
            lit_p("guest_scale", nv=guest_scale),
            lit_p("outward_sign", nv=outward_sign),
        ]
    }

def book_notch_node(nid, inp, axis="z", corner="ne", outward_sign=1.0, ratio=0.25,
                    role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "book_notch", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), str_p("corner", corner),
            lit_p("outward_sign", nv=outward_sign),
            num_p("ratio", ratio),
        ]
    }

def book_rotate_node(nid, inp, axis="z", angle_degrees=30.0, outward_sign=1.0,
                     related_ratio=0.5, role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "book_rotate", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), num_p("angle_degrees", angle_degrees),
            lit_p("outward_sign", nv=outward_sign),
            lit_p("related_ratio", nv=related_ratio),
        ]
    }

def boundary_expand_node(nid, inp, axis="z", amount=0.15, shoulder_fraction=0.5,
                          role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "boundary_expand", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), num_p("amount", amount),
            lit_p("shoulder_fraction", nv=shoulder_fraction),
        ]
    }

def book_embed_void_node(nid, inp, axis="z", position="east", embedded_ratio=0.35,
                          guest_scale=0.5, outward_sign=1.0, role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "embed_void", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), str_p("position", position),
            lit_p("embedded_ratio", nv=embedded_ratio),
            lit_p("guest_scale", nv=guest_scale),
            lit_p("outward_sign", nv=outward_sign),
        ]
    }

def related_array_node(nid, inp, axis="x", count=2, mode="array", spacing_ratio=1.1,
                        stagger_ratio=0.0, unit_scale=1.0, vertical_anchor="input_base",
                        role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "related_array", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), num_p("count", count), str_p("mode", mode),
            lit_p("spacing_ratio", nv=spacing_ratio),
            lit_p("stagger_ratio", nv=stagger_ratio),
            lit_p("unit_scale", nv=unit_scale),
            str_p("vertical_anchor", vertical_anchor),
        ]
    }

def interlock_related_node(nid, inp, axis="x", angle_degrees=0.0, bar_ratio=0.4,
                             distance_ratio=0.5, outward_sign=1.0, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "interlock_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), num_p("angle_degrees", angle_degrees),
            lit_p("bar_ratio", nv=bar_ratio),
            lit_p("distance_ratio", nv=distance_ratio),
            lit_p("outward_sign", nv=outward_sign),
        ]
    }

def intersect_related_node(nid, inp, axis="z", angle_degrees=90.0, bar_ratio=0.4,
                             unit_scale=0.8, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "intersect_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis), num_p("angle_degrees", angle_degrees),
            lit_p("bar_ratio", nv=bar_ratio),
            lit_p("unit_scale", nv=unit_scale),
        ]
    }

def join_related_node(nid, inp, bridge_ratio=0.3, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "join_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [lit_p("bridge_ratio", nv=bridge_ratio)]
    }

def offset_related_node(nid, inp, axis="x", distance_ratio=0.5, outward_sign=1.0,
                          unit_scale=0.8, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "offset_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            lit_p("distance_ratio", nv=distance_ratio),
            lit_p("outward_sign", nv=outward_sign),
            lit_p("unit_scale", nv=unit_scale),
        ]
    }

def nested_related_node(nid, inp, axis="x", distance_ratio=0.3, unit_scale=0.7,
                          role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "nested_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            lit_p("distance_ratio", nv=distance_ratio),
            lit_p("unit_scale", nv=unit_scale),
        ]
    }

def shift_related_node(nid, inp, axis="x", distance_ratio=0.3, outward_sign=1.0,
                        split_ratio=0.5, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "shift_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            lit_p("distance_ratio", nv=distance_ratio),
            lit_p("outward_sign", nv=outward_sign),
            lit_p("split_ratio", nv=split_ratio),
        ]
    }

def overlap_related_node(nid, inp, axis="x", outward_sign=1.0, shift_ratio=0.35,
                           slab_ratio=0.6, vertical_overlap=0.3, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "overlap_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            lit_p("outward_sign", nv=outward_sign),
            lit_p("shift_ratio", nv=shift_ratio),
            lit_p("slab_ratio", nv=slab_ratio),
            lit_p("vertical_overlap", nv=vertical_overlap),
        ]
    }

def mirror_array_node(nid, inp, normal=None, pivot=None, role="dominant_mass"):
    if normal is None: normal = [0.0, 1.0, 0.0]
    if pivot is None: pivot = [0.0, 0.0, 0.0]
    return {
        "id": nid, "kind": "pattern", "operator": "mirror_array", "inputs": [inp],
        "semantic_role": role,
        "parameters": [vec_p("normal", normal), vec_p("pivot", pivot)]
    }

def stack_node(nid, inp, count=2, shift_per_level=None, spacing=0.5, role="dominant_mass"):
    if shift_per_level is None: shift_per_level = [0.0, 0.0, 0.0]
    return {
        "id": nid, "kind": "pattern", "operator": "stack", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            num_p("count", count),
            vec_p("shift_per_level", shift_per_level),
            lit_p("spacing", nv=spacing),
        ]
    }

def clip_fraction_node(nid, inp, axis="z", fraction=0.6, anchor="high", role="dominant_mass"):
    return {
        "id": nid, "kind": "modifier", "operator": "clip_fraction", "inputs": [inp],
        "semantic_role": role,
        "parameters": [str_p("axis", axis), lit_p("fraction", nv=fraction), str_p("anchor", anchor)]
    }

def cut_corner_node(nid, inp, corner="ne", ratio=0.2, role="dominant_mass"):
    return {
        "id": nid, "kind": "modifier", "operator": "cut_corner", "inputs": [inp],
        "semantic_role": role,
        "parameters": [str_p("corner", corner), num_p("ratio", ratio)]
    }

# ─── dimensional intent ───────────────────────────────────────────────────────
def dim_intent(storeys=4, storey_h=3.5, target_gfa=None):
    if target_gfa is None: target_gfa = storeys * 300.0
    return {
        "schema_version": "arr.maas.dimensional_intent.v1",
        "storey_count": storeys,
        "storey_height_m": storey_h,
        "target_gfa_m2": float(target_gfa),
        "delivery_policy": "preserve_physical_dimensions",
        "programme_status": "unknown"
    }

def mkprog(pid, v, name, base_form, base_seed, tags, rationale,
           nodes, root_id, storeys=4, storey_h=3.5, target_gfa=None,
           principle_ids=None):
    if principle_ids is None: principle_ids = [pid]
    if target_gfa is None: target_gfa = storeys * 300.0
    return {
        "book_composition_path_id": pid,
        "name": f"{name}_v{v}",
        "base_form_id": base_form,
        "base_seed": base_seed,
        "intent_tags": tags[:12],
        "nodes": nodes,
        "root_id": root_id,
        "rationale": rationale,
        "dimensional_intent": dim_intent(storeys, storey_h, target_gfa),
        "book_principle_ids": principle_ids,
    }

# ─── 78 path IDs (must match offer exactly) ──────────────────────────────────
PATH_IDS = [
    "book:path:9bab887f2e519077dcbe8e5977897df8a80deb6d1a280936cccca005d8555719",
    "book:path:9042c82e97a383fc1f1e97948ac87e0bac17a95d0d8587255d48710c0ac64040",
    "book:path:11a0d7a5a51e85d9ec1cf2f3b3eaa086eb6841d1fec6a184077cc5db1851b185",
    "book:path:dd28b0c53f08a2d1812dc32d7b562ee9b7bc4a1ca98b90a13152bbf534dd27f2",
    "book:path:c7fcd0c126b7b32471e69e703e7e9022ab3963899ef974c879ec44b4162b197a",
    "book:path:b95277004fb2b89b21445182aab353c444a4ea7a1e7044f8c2e7e07599226909",
    "book:path:6bb95e7e0461e1606d4430a1e8a7c4ad2b3dc96d74ff48bced73da05b9df6cf5",
    "book:path:2f971be29f0d428a9879b1c00948ac738f8921db4163797414074d894ac8efb9",
    "book:path:e510ad256385b556152790586ff8d15493cf9c1d6cffbd352f8e0d326c4ca71a",
    "book:path:53c55b4da48903af110459fa120baeaec3b186edf22d6890fa718d0ad6b1f5b5",
    "book:path:f285f713076b19ee7cc1b58f2d44f85aeec8a11bfe30fc0b77e876a1543a612b",
    "book:path:05470e618703ead632e6029bac7312306f05a6f404cb1a84f60043e0fb2b6b5f",
    "book:path:ff644fb6db1684200f7c558764b8298c45bab946fac40c3df9cc090edf479977",
    "book:path:61ddaacb14d1ebd0e0c24518a19a9b01f9a48f50fbfd66fd280b92abe59722b7",
    "book:path:2e2f65a3f44c510ecfa66c729db4c53684b3cc4033f5844bc980f4fa4bf1ad70",
    "book:path:aadaf4340a4980ec0c691cf6c70bf78936b4b4b1471a6340d384abcae9ee0a2c",
    "book:path:2e24111503e808e954bf437374af114ede99fddb568beab59253edb011273835",
    "book:path:84d0345cadb3c43a13aa423bc1fddfb175b338b095c86bc9ec4b1eab2952afd0",
    "book:path:b96fa24e6b07a0419331b82a471addcf0f980f71d6fee1bffd80a5e1ed1ea126",
    "book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e",
    "book:path:2fcf5f31e6d7ec9acbe02f9c3a6bb20e72df122cf29d989dd630f4d7fc022791",
    "book:path:423e633a08a43369b6ccda29d5604fc061c6e20e52e460c9867ddd1e5b13c2c0",
    "book:path:6acac573694cb27de1572fd0a9de5fb76aed871fea929c88573a072c95a8bbbb",
    "book:path:1dbb96b395ddd04b17719976be7a62b1bdb6256f080c74a7b0de12c908a7915c",
    "book:path:f91a61a346c29c85aa4907c5e5c53d10e00a7530d28316c598fcc29d75f7fb55",
    "book:path:13fbf6da4b2addf28d4678956f747d8f112740ed2ca07de19e7a4884b2d43956",
    "book:path:4542c2a1884b1b256fbdea6e3ffd434dac31db9212deb3a328bb168fcfc1a6e4",
    "book:path:e1e90099b5d07535d9361727c7d4b028f702499491b0588fdb2c926912013fb5",
    "book:path:f7755521cc02b4d565cddffa435faa30d79095ee7d62ce0588cbc8fc33fa2b6f",
    "book:path:def59b665a24ebd51c08a3812668edc1a6131552a8055b2d7cb88de8de90f4f5",
    "book:path:3ab1e90c58b2293f63e75df8acabb9308b747cd6304c4511b2a47ed9ce8821c3",
    "book:path:cfeca7238d109f8ccf184e9ab42319aadf2d36f2aca116ba295ae47cbb6ca11b",
    "book:path:08e14d9ef6f30e7f2700d6e5f895d4911944adbfd16a0477dbfee0afeebfbf70",
    "book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb",
    "book:path:60778ae3e99cf12bb7e8461f50ee3332b7a47ed4893d70cb2d8400fd22cc49cf",
    "book:path:0b828fd1f09aeb9b5e3096a6cfe15c3cf1d709a475844690e9f3085fbdb9b8b1",
    "book:path:d2cb499b7d8b00c2ace3d4b6893bc583e2307d3d6cdb0ac96b319253fe0529c4",
    "book:path:eccfafc4718361d6aec40a901f53b344d4bff77683f4887715da5adcce05157f",
    "book:path:c15ec55248a4fc32d3f15fea2da9b94c5831c48f2dedecef91ddf03a61f04ef1",
    "book:path:591a729db54894dfd9449b5e5f08781d509ee6da02353d574828e141854ef1fe",
    "book:path:a34184c51ffd9faa6f4e694bd0df018b4499f561be4b29d1f086e7b8361fd7b7",
    "book:path:9c9d6d2d18bf525d39eb0c2299651d643b20f3f3e0de68975addd59e346d58d2",
    "book:path:82e07b845038d9e2c03a74eab9531bfdb2aaa74dd621e9ab21c72eb467b32bd7",
    "book:path:716df07ca23e72681a3aca19b6a160a3c867f21315b111d0c6ac21a2700be269",
    "book:path:7f4ace179d50c15c3a63cd24d5dcb7e3420da79697dcb07afb1a30f73bbed628",
    "book:path:aec174c38f9ed86be822dd7813012953b17a2443337cd862c35837a7c34ab023",
    "book:path:4805f5934fe933b3108aeb3a3aa5a567a1a1bd1debe1a625217a979a35f16c24",
    "book:path:e688a33bce52391b696ecea5bef1c7926ec4e15d1a02971bebfaf8fcb990c13b",
    "book:path:9ff66e145418829ccc5e710634ec50389ce05bc62f6496984bde22110528e383",
    "book:path:546119cfb82a276ceee53e1eb09d960d054ff4bacd4853bc824ba6ed9ffd8e8f",
    "book:path:f1440150bbd785859ef88baca5734f8731b6b029da123797ae55c43541ecb398",
    "book:path:0bac03a066888497ad4cdc5a727e609bdb620a3ef13ef9cc5394a46de7a09449",
    "book:path:af83d6add866295511a823d82a17f6d3b2316e11204b251b3c0c6eee90de813f",
    "book:path:f42375c1818d4ccdef5278032d64aa984e673a76b1e44056b286a08f507288d1",
    "book:path:89a8d2e071e7dc228815ddab41a199bf7379d5742d861095f20ab2de6fd610f5",
    "book:path:bbd403cec5ff6827cf04b266a65afdab72752a8071a42a83017b53f878176551",
    "book:path:b1dc18f7817ae62db7951887748c90355ffaa9ee10880a1dfaad396c8a5e54e0",
    "book:path:ea3fdbfddf0a32805dc837821770519d713d02a468fa8e914311a1e122289d20",
    "book:path:0e3fe6f19fe3fb3b4fdfecd76c496e00141469a5ab4be263385f49ea58ce99b5",
    "book:path:b161eb4c3bb6230cd34980d091fc44bf52f7d2648e59f55b39dc46e64225dc46",
    "book:path:56f69a2038120b9187f1387efee21a6a63cf530d026b6f10dfab37c2db2dc717",
    "book:path:dc50b322c264219be6835f6b50fc2a3e5ffba233fd5e5f9fa3813b14d5523193",
    "book:path:0d5b1e3a233d34e16073c222838ee053eabeb8692327fc62ef668c7b75a716d1",
    "book:path:bd7cfc87da1811e45875acde3aa82d513fc343204bca6bcd2fb26f3a1d1357e7",
    "book:path:c58193dcc81b7f6fb8a25fd8bb18808d47ae79a9765ff716fd84b09d1befc70b",
    "book:path:2e91334e6426f5c7ca6a8f4cfce4ca746f1d0f3091273eaf3896fe4900b3f7bd",
    "book:path:58d160602ccaafb30f737d33723e43a8ae2841eaac7fda840c8f5d8886775abf",
    "book:path:150c3892213b9cc014f2985158abc9905f8c9b2cc1c690a1cc7e41068a044a6f",
    "book:path:a024d86c2d00b3f85de00140e9b221e1e73de64e83a85c58dc4e52ea478988e0",
    "book:path:a254a71182ed875bbe8102de50270b1e19538916fe00c1a609ea6c5950fbef0b",
    "book:path:d138480c1ee6ed85eed95f1cfd921852b69d33e8e412f0f28a7c3194117efa38",
    "book:path:42bc62991fbaf0eaa42d48e37ede8e507613abc648a0e32338a19e19862787e2",
    "book:path:eee048bfdfa8ab2892e3a8a604bd2a302efd5cb77e995014dc28074c5b3811b4",
    "book:path:9e4457e0a1cf8fa849c73e92abc08b15423426f4949b6225cab08c1034e531a5",
    "book:path:71fb46d7af677eb3b5345e94d27f0fa1ef9b257aadc2cd746aec550ba2a0419b",
    "book:path:dfbf81995ea510ccee2aa31dffbf03a3dd3dfcb167a0153d116724dbf65599f0",
    "book:path:415615bd85962e057ca3dd17914bf224fa7b6182a09f3f17db371a41b7dcc401",
    "book:path:a831f22dee8c36e3a70315fa1ff822eff56f7f0deefcfb3032d54fc585e8a128",
]

assert len(PATH_IDS) == 78

# ─── 78 builder functions ─────────────────────────────────────────────────────

def b0(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             bend_node("bend0","m0","z",22+v*8,4),
             courtyard_node("result","bend0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"bent_bar_court","cube","bar",["bend","courtyard","long_axis"],
                  "Continuously bent bar curves to define an east-facing civic court.",nodes,"result",4,3.5,1100)

def b1(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             book_fracture_node("frac0","m0","z",15+v*10,0.10+v*0.04,1.0,0.55+v*0.05),
             notch_node("result","frac0","east","ne",0.28+v*0.04,0.35,0.5)]
    return mkprog(pid,v,"fractured_slab_notch","cube","slab",["fracture","notch","long_axis"],
                  "Slab receives diagonal fracture and east corner notch marking entry.",nodes,"result",3,3.5,900)

def b2(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             book_embed_void_node("emb1","m0","z","east",0.30+v*0.05,0.45+v*0.05),
             book_embed_void_node("emb2","emb1","y","center",0.25+v*0.04,0.40+v*0.04),
             carve_void_node("result","emb2",0.20+v*0.03,"east")]
    return mkprog(pid,v,"double_embed_court","cube","block",["embed","carve_void","long_axis"],
                  "Two nested embed voids hollow block; east carve opens the civic forecourt.",nodes,"result",5,3.5,1400)

def b3(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             book_branch_node("br0","m0",40+v*15,0.55+v*0.05,0.38+v*0.04,"input_base"),
             boundary_expand_node("exp0","br0","z",0.18+v*0.04,0.45+v*0.05),
             courtyard_node("result","exp0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"branched_expanded_court","cube","bar",["branch","expand","courtyard","long_axis"],
                  "Arms branch from bar trunk then shoulder-expand; east court as civic threshold.",nodes,"result",4,3.5,1200)

def b4(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             book_carve_node("carve0","m0","z","east",0.25+v*0.05,1.0,0.40+v*0.05),
             offset_related_node("off0","carve0","x",0.45+v*0.05,1.0,0.75+v*0.05),
             notch_node("result","off0","east","se",0.25+v*0.03,0.35,0.55)]
    return mkprog(pid,v,"carved_offset_notch","cube","slab",["carve","offset","notch","long_axis"],
                  "East face carved and offset-duplicated; SE notch gives the corner address.",nodes,"result",4,3.5,1000)

def b5(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             book_branch_node("br0","m0",60+v*20,0.58+v*0.05,0.35+v*0.05,"input_base"),
             courtyard_node("result","br0",0.24+v*0.03,"east")]
    return mkprog(pid,v,"short_branch_court","cube","bar",["branch","short_axis","courtyard"],
                  "Short-axis branching produces Y-plan; east courtyard opens toward road frontage.",nodes,"result",4,3.5,1150)

def b6(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             book_rotate_node("rot0","m0","z",25+v*10,1.0,0.45+v*0.06),
             carve_void_node("result","rot0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"rotated_slab_carve","cube","slab",["rotate","short_axis","carve_void"],
                  "Partitioned slab child rotates about hinge edge; east carve void marks entry.",nodes,"result",3,3.5,870)

def b7(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             book_notch_node("notch0","m0","z","sw",1.0,0.22+v*0.05),
             notch_node("result","notch0","east","ne",0.25+v*0.04,0.40,0.55)]
    return mkprog(pid,v,"inscribed_notch_entry","cube","block",["inscribe","notch","short_axis"],
                  "Block inscribed with corner notch void; east notch delivers civic entrance.",nodes,"result",4,3.5,1050)

def b8(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             intersect_related_node("inter0","m0","z",90.0,0.38+v*0.05,0.75+v*0.05),
             book_split_node("sp0","inter0","y",0.0,0.10+v*0.04,1.0,1.0,1.0,0.48+v*0.04,"east"),
             lift_node("result","sp0","east",0.22+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"intersect_split_lift","cube","bar",["intersect","split","short_axis","lift"],
                  "Cross-bar intersection then split; east lift opens piloti-style threshold.",nodes,"result",4,3.5,1100)

def b9(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             bend_node("bend0","m0","y",18+v*7,4),
             stack_node("stk0","bend0",2+v,[0.05,0.0,0.0],0.5),
             courtyard_node("result","stk0",0.20+v*0.04,"east")]
    return mkprog(pid,v,"bent_stacked_court","cube","slab",["bend","stack","short_axis","courtyard"],
                  "Bent slab stacked; east courtyard exploits stack offset as civic threshold.",nodes,"result",3+v,3.5,950+v*150)

def b10(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             book_lift_node("lift0","m0","z",0.28+v*0.05,0.55+v*0.05,1.0),
             split_wing_node("result","lift0","east","y","parallel",0.12+v*0.02,0.85+v*0.05,True,0.28+v*0.03,False,0.15,0.2)]
    return mkprog(pid,v,"lifted_split_wing","cube","block",["lift","split_wing","short_axis"],
                  "Block lifted and split into parallel wings with east-access bridge.",nodes,"result",4,3.5,1200)

def b11(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             interlock_related_node("inter0","m0","x",0.0,0.38+v*0.04,0.45+v*0.05,1.0),
             courtyard_node("result","inter0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"interlocked_court","cube","bar",["interlock","vertical","courtyard"],
                  "Two interlocked L-volumes engage through shared zone; east court organizes entry.",nodes,"result",4,3.5,1100)

def b12(pid, v):
    w,d,h = 0.68, 0.68, 2.5
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             shear_node("shear0","m0","z",0.25+v*0.06,[1.0,0.0,0.0]),
             notch_node("result","shear0","east","ne",0.28+v*0.04,0.38,0.6)]
    return mkprog(pid,v,"sheared_tower_notch","cube","tower",["shear","vertical","notch"],
                  "Tower sheared obliquely; east notch frames the civic entry recess.",nodes,"result",5,3.5,1300)

def b13(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             boundary_expand_node("exp1","m0","z",0.20+v*0.05,0.40+v*0.06),
             boundary_expand_node("exp2","exp1","y",0.15+v*0.04,0.55+v*0.04),
             carve_void_node("result","exp2",0.22+v*0.03,"east")]
    return mkprog(pid,v,"double_expand_carve","cube","block",["expand","vertical","carve_void"],
                  "Double shoulder expansion thickens block; east carve void opens through face.",nodes,"result",4,3.5,1200)

def b14(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             boundary_expand_node("exp0","m0","z",0.22+v*0.05,0.5+v*0.04),
             mirror_array_node("mir0","exp0",[0.0,1.0,0.0],[0.0,0.0,0.0]),
             courtyard_node("result","mir0",0.24+v*0.03,"east")]
    return mkprog(pid,v,"expanded_reflected_court","cube","slab",["expand","reflect","vertical","courtyard"],
                  "Expanded slab reflected about y creates bilateral symmetry; east court as gateway.",nodes,"result",4,3.5,1100)

def b15(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(1,1,1)),
             overlap_related_node("ovl0","m0","x",1.0,0.32+v*0.04,0.58+v*0.04,0.25+v*0.04),
             boundary_expand_node("exp0","ovl0","z",0.18+v*0.04,0.48+v*0.04),
             notch_node("result","exp0","east","ne",0.25+v*0.04,0.38,0.55)]
    return mkprog(pid,v,"overlap_expanded_notch","cube","bar",["overlap","expand","vertical","notch"],
                  "Overlapping bars shift vertically and expand shoulder; east notch addresses corner.",nodes,"result",4,3.5,1150)

def b16(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             bend_node("bend0","m0","z",30+v*10,4),
             carve_void_node("result","bend0",0.22+v*0.04,"east")]
    return mkprog(pid,v,"38_bent_carve","cube","slab",["bend","long_axis","3_8"],
                  "3/8 slab bent to shelter east carve void as civic approach.",nodes,"result",3,3.5,800)

def b17(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             book_fracture_node("frac0","m0","z",20+v*12,0.11+v*0.04,1.0,0.58+v*0.04),
             notch_node("result","frac0","east","se",0.27+v*0.04,0.36,0.5)]
    return mkprog(pid,v,"38_fracture_notch","cube","block",["fracture","long_axis","3_8","notch"],
                  "3/8 block receives angled fissure; SE notch defines east entry corner.",nodes,"result",3,3.5,850)

def b18(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             book_split_node("sp0","m0","y",0.0,0.08+v*0.03,1.0,1.0,1.0,0.45+v*0.05,"east"),
             book_split_node("sp1","sp0","x",5.0+v*5,0.10+v*0.03,-1.0,-1.0,2.0,0.5,"east"),
             lift_node("result","sp1","east",0.20+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"38_split_split_lift","cube","bar",["split","long_axis","3_8","lift"],
                  "Double split displaces bar children; east lift creates public piloti threshold.",nodes,"result",4,3.5,1050)

def b19(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             bend_node("bend0","m0","z",20+v*8,4),
             book_branch_node("br0","bend0",50+v*10,0.60+v*0.04,0.36+v*0.04,"input_base"),
             courtyard_node("result","br0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_bent_branch_court","cube","bar",["bend","branch","long_axis","3_8"],
                  "Bent bar then branched; east courtyard catches the opening of the curve.",nodes,"result",4,3.5,1100)

def b20(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             book_split_node("sp0","m0","y",0.0,0.09+v*0.03,1.0,1.0,1.0,0.5,"east"),
             join_related_node("join0","sp0",0.28+v*0.05),
             carve_void_node("result","join0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_split_join_carve","cube","block",["split","join","long_axis","3_8"],
                  "Split halves bridge-joined; east carve void delivers the gateway entry.",nodes,"result",4,3.5,1000)

def b21(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             inflate_node("infl0","m0","z",1.12+v*0.06,1.18+v*0.05,2.2+v*0.3,4),
             notch_node("result","infl0","east","ne",0.25+v*0.04,0.38,0.55)]
    return mkprog(pid,v,"38_inflated_notch","cube","slab",["inflate","short_axis","3_8","notch"],
                  "3/8 slab inflated at crown; east notch indents the billowing face for entry.",nodes,"result",3,3.5,820)

def b22(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             overlap_related_node("ovl0","m0","y",1.0,0.30+v*0.04,0.62+v*0.04,0.22+v*0.04),
             courtyard_node("result","ovl0",0.20+v*0.04,"east")]
    return mkprog(pid,v,"38_overlap_court","cube","bar",["overlap","short_axis","3_8","courtyard"],
                  "Two overlapping bars superpose in plan; east courtyard in the overlap zone.",nodes,"result",4,3.5,1050)

def b23(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             book_notch_node("notch0","m0","z","nw",1.0,0.25+v*0.05),
             carve_void_node("result","notch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_inscribed_carve","cube","block",["inscribe","short_axis","3_8","carve_void"],
                  "NW corner notch inscribed; east carve void defines the civic face.",nodes,"result",3,3.5,870)

def b24(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             intersect_related_node("inter0","m0","z",90.0,0.36+v*0.05,0.78+v*0.04),
             book_split_node("sp0","inter0","x",0.0,0.09+v*0.03,1.0,1.0,1.0,0.5,"east"),
             lift_node("result","sp0","east",0.22+v*0.03,0.32+v*0.03)]
    return mkprog(pid,v,"38_intersect_split_lift","cube","bar",["intersect","split","short_axis","3_8"],
                  "Cross intersection split; east lift opens ground as public passage.",nodes,"result",4,3.5,1100)

def b25(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             bend_node("bend0","m0","y",20+v*8,4),
             stack_node("stk0","bend0",2+v,[0.04,0.0,0.0],0.48),
             courtyard_node("result","stk0",0.20+v*0.04,"east")]
    return mkprog(pid,v,"38_bent_stacked_court","cube","slab",["bend","stack","short_axis","3_8"],
                  "Bent 3/8 slab stacked; east courtyard exploits stack offset as threshold.",nodes,"result",3+v,3.5,880+v*150)

def b26(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             book_lift_node("lift0","m0","z",0.25+v*0.05,0.58+v*0.04,1.0),
             split_wing_node("result","lift0","east","y","parallel",0.12+v*0.03,0.88+v*0.04,True,0.25+v*0.03,False,0.15,0.2)]
    return mkprog(pid,v,"38_lift_split_wing","cube","block",["lift","split_wing","short_axis","3_8"],
                  "3/8 block lifted and wing-split; bridge over east gap forms civic threshold.",nodes,"result",4,3.5,1050)

def b27(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             interlock_related_node("inter0","m0","x",5.0+v*5,0.40+v*0.04,0.42+v*0.05,1.0),
             courtyard_node("result","inter0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_interlock_court","cube","bar",["interlock","vertical","3_8","courtyard"],
                  "Interlocking L-bar pair at 3/8 scale; east courtyard mediates the civic face.",nodes,"result",4,3.5,1000)

def b28(pid, v):
    w,d,h = 0.68, 0.68, 2.5
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             shear_node("shear0","m0","z",0.28+v*0.06,[0.0,1.0,0.0]),
             notch_node("result","shear0","east","ne",0.26+v*0.04,0.36,0.58)]
    return mkprog(pid,v,"38_shear_notch","cube","tower",["shear","vertical","3_8","notch"],
                  "Tower sheared along y-axis; east notch creates angled entry recess.",nodes,"result",5,3.5,1200)

def b29(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             book_branch_node("br0","m0",45+v*12,0.55+v*0.05,0.36+v*0.04,"input_base"),
             book_branch_node("br1","br0",-30-v*8,0.60+v*0.04,0.32+v*0.04,"input_base"),
             carve_void_node("result","br1",0.20+v*0.03,"east")]
    return mkprog(pid,v,"38_double_branch_carve","cube","bar",["branch","vertical","3_8","carve_void"],
                  "Double branching creates dendritic plan; east carve void in the civic notch.",nodes,"result",4,3.5,1100)

def b30(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             book_notch_node("notch0","m0","z","nw",1.0,0.22+v*0.05),
             twist_node("twist0","notch0","z",18+v*7,4),
             notch_node("result","twist0","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"38_notch_twist_entry","cube","block",["notch","twist","vertical","3_8"],
                  "Notched block twisted about z; east notch marks the rotated civic face.",nodes,"result",4,3.5,950)

def b31(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.85,0.85,1.0)),
             boundary_expand_node("exp0","m0","z",0.20+v*0.05,0.45+v*0.05),
             nested_related_node("nest0","exp0","x",0.28+v*0.04,0.65+v*0.05),
             carve_void_node("result","nest0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_expand_nest_carve","cube","slab",["expand","nest","vertical","3_8"],
                  "Expanded slab with nested inner volume; east carve void opens layered civic face.",nodes,"result",3,3.5,900)

def b32(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             offset_related_node("off0","m0","x",0.45+v*0.05,1.0,0.78+v*0.04),
             courtyard_node("result","off0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_offset_court","cube","slab",["offset","long_axis","half"],
                  "Half-fraction slab offset-duplicated along x; east courtyard in the gap.",nodes,"result",4,3.5,1050)

def b33(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             clip_fraction_node("clip0","m0","z",0.72+v*0.05,"high"),
             notch_node("result","clip0","east","ne",0.28+v*0.04,0.38,0.55)]
    return mkprog(pid,v,"half_compress_notch","cube","block",["compress","long_axis","half","notch"],
                  "Half block vertically clipped; east notch cuts entry into the compact face.",nodes,"result",3,3.5,820)

def b34(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             book_split_node("sp0","m0","y",0.0,0.09+v*0.03,1.0,1.0,1.0,0.48+v*0.04,"east"),
             book_split_node("sp1","sp0","x",4.0+v*4,0.10+v*0.03,-1.0,-1.0,2.0,0.5,"east"),
             carve_void_node("result","sp1",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_double_split_carve","cube","bar",["split","long_axis","half","carve_void"],
                  "Double split displaces half-fraction bar; east carve addresses the public side.",nodes,"result",4,3.5,980)

def b35(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             bend_node("bend0","m0","z",22+v*8,4),
             book_branch_node("br0","bend0",48+v*10,0.58+v*0.04,0.35+v*0.04,"input_base"),
             lift_node("result","br0","east",0.22+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"half_bent_branch_lift","cube","bar",["bend","branch","long_axis","half","lift"],
                  "Half bar bent and branched; east lift opens ground passage below arms.",nodes,"result",4,3.5,1080)

def b36(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             book_split_node("sp0","m0","y",0.0,0.09+v*0.03,1.0,1.0,1.0,0.50,"east"),
             join_related_node("join0","sp0",0.30+v*0.04),
             courtyard_node("result","join0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_split_join_court","cube","block",["split","join","long_axis","half","courtyard"],
                  "Split halves bridged; east courtyard in gateway slot becomes civic room.",nodes,"result",4,3.5,1000)

def b37(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             inflate_node("infl0","m0","z",1.14+v*0.06,1.20+v*0.05,2.0+v*0.3,4),
             courtyard_node("result","infl0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_inflated_court","cube","slab",["inflate","short_axis","half","courtyard"],
                  "Half slab inflated at crown; east courtyard as civic concavity.",nodes,"result",3,3.5,820)

def b38(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             overlap_related_node("ovl0","m0","y",1.0,0.32+v*0.04,0.60+v*0.04,0.24+v*0.04),
             notch_node("result","ovl0","east","ne",0.26+v*0.03,0.36,0.55)]
    return mkprog(pid,v,"half_overlap_notch","cube","bar",["overlap","short_axis","half","notch"],
                  "Overlapping half bars; east notch at shifted junction marks building address.",nodes,"result",4,3.5,980)

def b39(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             book_notch_node("notch0","m0","z","sw",1.0,0.24+v*0.05),
             carve_void_node("result","notch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_inscribed_carve","cube","block",["inscribe","short_axis","half","carve_void"],
                  "SW notch inscribed into half block; east carve as principal address.",nodes,"result",3,3.5,840)

def b40(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             book_notch_node("notch0","m0","z","se",1.0,0.22+v*0.04),
             intersect_related_node("inter0","notch0","z",90.0,0.38+v*0.04,0.78+v*0.04),
             lift_node("result","inter0","east",0.22+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"half_inscribe_intersect_lift","cube","bar",["inscribe","intersect","short_axis","half"],
                  "Notched bar cross-intersected; east lift frames crossing as public passage.",nodes,"result",4,3.5,1050)

def b41(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             book_branch_node("br0","m0",50+v*15,0.58+v*0.04,0.36+v*0.04,"input_base"),
             related_array_node("arr0","br0","x",2,"pack",1.1+v*0.05,0.0,0.85+v*0.04,"input_base"),
             courtyard_node("result","arr0",0.20+v*0.03,"east")]
    return mkprog(pid,v,"half_branch_array_court","cube","bar",["branch","pack","short_axis","half"],
                  "Branched bar packed in array; east courtyard in the arrangement gap.",nodes,"result",4,3.5,1100)

def b42(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             book_lift_node("lift0","m0","z",0.26+v*0.05,0.58+v*0.04,1.0),
             book_carve_node("carve0","lift0","z","east",0.28+v*0.04,1.0,0.42+v*0.04),
             split_wing_node("result","carve0","east","y","parallel",0.12+v*0.02,0.88+v*0.04,True,0.26+v*0.03,False,0.15,0.2)]
    return mkprog(pid,v,"half_lift_carve_wing","cube","block",["lift","carve","short_axis","half"],
                  "Lifted block east-carved then wing-split; east bridge spans the civic gap.",nodes,"result",4,3.5,1050)

def b43(pid, v):
    w,d,h = 0.68, 0.68, 2.5
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             twist_node("twist0","m0","z",25+v*10,4),
             notch_node("result","twist0","east","ne",0.27+v*0.04,0.36,0.58)]
    return mkprog(pid,v,"half_twisted_tower_notch","cube","tower",["twist","vertical","half","notch"],
                  "Half tower twisted; east notch cuts into rotated face for entry.",nodes,"result",5,3.5,1200)

def b44(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             pinch_node("pinch0","m0","z",0.48+v*0.04,0.68+v*0.05,2.0+v*0.3,4),
             carve_void_node("result","pinch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_pinched_carve","cube","slab",["pinch","vertical","half","carve_void"],
                  "Half slab pinched at waist to form hourglass section; east carve opens civic face.",nodes,"result",4,3.5,900)

def b45(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             book_branch_node("br0","m0",45+v*12,0.55+v*0.04,0.36+v*0.04,"input_base"),
             book_branch_node("br1","br0",-40-v*10,0.58+v*0.04,0.32+v*0.04,"input_base"),
             courtyard_node("result","br1",0.20+v*0.03,"east")]
    return mkprog(pid,v,"half_double_branch_court","cube","bar",["branch","vertical","half","courtyard"],
                  "Double branching in half-fraction bar; east courtyard at the forking zone.",nodes,"result",4,3.5,1100)

def b46(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             book_notch_node("notch0","m0","z","sw",1.0,0.24+v*0.05),
             twist_node("twist0","notch0","z",20+v*8,4),
             carve_void_node("result","twist0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_notch_twist_carve","cube","block",["notch","twist","vertical","half"],
                  "Notched half block twisted; east carve void opens through the rotated face.",nodes,"result",4,3.5,950)

def b47(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.75,0.75,1.0)),
             boundary_expand_node("exp0","m0","z",0.22+v*0.05,0.48+v*0.04),
             nested_related_node("nest0","exp0","y",0.30+v*0.04,0.68+v*0.05),
             lift_node("result","nest0","east",0.24+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"half_expand_nest_lift","cube","slab",["expand","nest","vertical","half","lift"],
                  "Expanded and nested slab volumes; east lift provides piloti-style ground access.",nodes,"result",3,3.5,870)

def b48(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             offset_related_node("off0","m0","x",0.48+v*0.05,1.0,0.72+v*0.05),
             courtyard_node("result","off0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_offset_court","cube","slab",["offset","long_axis","quarter"],
                  "Quarter-fraction slab offset pair; east courtyard in gap as civic lobby.",nodes,"result",4,3.5,950)

def b49(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             clip_fraction_node("clip0","m0","z",0.70+v*0.05,"high"),
             notch_node("result","clip0","east","se",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"qtr_compress_notch","cube","block",["compress","long_axis","quarter","notch"],
                  "Quarter block clipped; SE east notch as compact entry address.",nodes,"result",3,3.5,780)

def b50(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             book_split_node("sp0","m0","y",0.0,0.09+v*0.03,1.0,1.0,1.0,0.48+v*0.04,"east"),
             book_split_node("sp1","sp0","x",6.0+v*4,0.10+v*0.03,-1.0,-1.0,2.0,0.5,"east"),
             carve_void_node("result","sp1",0.20+v*0.03,"east")]
    return mkprog(pid,v,"qtr_double_split_carve","cube","bar",["split","long_axis","quarter","carve_void"],
                  "Quarter-bar double-split; east carve void addresses the fractured form.",nodes,"result",4,3.5,940)

def b51(pid, v):
    w,d,h = 0.68, 0.68, 2.5
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             taper_node("tap0","m0","z",[1.0,1.0],[0.65+v*0.05,0.65+v*0.05],0.0,3),
             bend_node("bend0","tap0","y",18+v*8,4),
             courtyard_node("result","bend0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_taper_bend_court","cube","tower",["taper","bend","long_axis","quarter"],
                  "Quarter tower tapered then bent; east courtyard below the curved crown.",nodes,"result",5,3.5,1250)

def b52(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             pinch_node("pinch0","m0","z",0.48+v*0.04,0.70+v*0.04,2.0+v*0.3,4),
             related_array_node("arr0","pinch0","x",2,"array",1.15+v*0.05,0.0,0.88+v*0.04,"input_base"),
             notch_node("result","arr0","east","ne",0.26+v*0.03,0.36,0.55)]
    return mkprog(pid,v,"qtr_pinch_array_notch","cube","slab",["pinch","join","array","long_axis","quarter"],
                  "Pinched slab arrayed in pair; east notch at pinch joint marks civic entry.",nodes,"result",4,3.5,970)

def b53(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             boundary_expand_node("exp0","m0","z",0.18+v*0.05,0.42+v*0.06),
             lift_node("result","exp0","east",0.24+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"qtr_extrude_lift","cube","block",["extrude","short_axis","quarter","lift"],
                  "Quarter-block expanded upward and lifted; east lift exposes public ground.",nodes,"result",4,3.5,930)

def b54(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             book_lodge_node("lodge0","m0","z",0.28+v*0.04,0.55+v*0.04,1.0),
             courtyard_node("result","lodge0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_lodge_court","cube","bar",["lodge","short_axis","quarter","courtyard"],
                  "Guest bar lodged in host interval; east courtyard uses lodged gap as entry.",nodes,"result",3,3.5,820)

def b55(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             book_extract_node("ext0","m0","z","east",0.28+v*0.04,0.50+v*0.04,1.0),
             carve_void_node("result","ext0",0.20+v*0.03,"east")]
    return mkprog(pid,v,"qtr_extract_carve","cube","slab",["extract","short_axis","quarter","carve_void"],
                  "Quarter slab extraction channel through east face; carve deepens civic recess.",nodes,"result",3,3.5,840)

def b56(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             book_notch_node("notch0","m0","z","nw",1.0,0.22+v*0.04),
             intersect_related_node("inter0","notch0","z",90.0,0.40+v*0.04,0.76+v*0.04),
             notch_node("result","inter0","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"qtr_inscribe_intersect_notch","cube","bar",["inscribe","intersect","short_axis","quarter"],
                  "Bar notched then cross-intersected; east notch completes entry articulation.",nodes,"result",4,3.5,1000)

def b57(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             book_branch_node("br0","m0",55+v*15,0.60+v*0.04,0.35+v*0.04,"input_base"),
             related_array_node("arr0","br0","y",2,"pack",1.12+v*0.05,0.0,0.88+v*0.04,"input_base"),
             carve_void_node("result","arr0",0.20+v*0.03,"east")]
    return mkprog(pid,v,"qtr_branch_pack_carve","cube","bar",["branch","pack","short_axis","quarter"],
                  "Branched bar packed in pair; east carve void in arrangement front gap.",nodes,"result",4,3.5,1050)

def b58(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             book_lift_node("lift0","m0","z",0.28+v*0.04,0.56+v*0.04,1.0),
             book_carve_node("carve0","lift0","z","east",0.26+v*0.04,1.0,0.42+v*0.04),
             lift_node("result","carve0","east",0.24+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"qtr_lift_carve_lift","cube","block",["lift","carve","short_axis","quarter"],
                  "Lifted block east-carved; terminal lift opens east ground as civic passage.",nodes,"result",4,3.5,980)

def b59(pid, v):
    w,d,h = 0.68, 0.68, 2.5
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             twist_node("twist0","m0","z",28+v*10,4),
             courtyard_node("result","twist0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_twisted_court","cube","tower",["twist","vertical","quarter","courtyard"],
                  "Quarter tower twisted; east courtyard as civic space below twist.",nodes,"result",5,3.5,1250)

def b60(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             pinch_node("pinch0","m0","z",0.50+v*0.04,0.65+v*0.05,2.0+v*0.3,4),
             carve_void_node("result","pinch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_pinched_carve","cube","slab",["pinch","vertical","quarter","carve_void"],
                  "Quarter slab pinched at waist; east carve opens the narrowed civic face.",nodes,"result",4,3.5,880)

def b61(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             book_branch_node("br0","m0",48+v*12,0.56+v*0.04,0.36+v*0.04,"input_base"),
             book_branch_node("br1","br0",-38-v*10,0.60+v*0.04,0.32+v*0.04,"input_base"),
             notch_node("result","br1","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"qtr_double_branch_notch","cube","bar",["branch","vertical","quarter","notch"],
                  "Double branching in quarter bar; east notch at fork junction marks entry.",nodes,"result",4,3.5,1050)

def b62(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             shift_related_node("sh0","m0","x",0.32+v*0.04,1.0,0.50+v*0.04),
             book_notch_node("notch0","sh0","z","ne",1.0,0.24+v*0.04),
             carve_void_node("result","notch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_shift_notch_carve","cube","block",["shift","notch","vertical","quarter"],
                  "Shifted related volume with corner notch; east carve marks public threshold.",nodes,"result",4,3.5,960)

def b63(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.65,0.65,1.0)),
             book_embed_void_node("emb0","m0","z","center",0.30+v*0.05,0.50+v*0.04),
             overlap_related_node("ovl0","emb0","x",1.0,0.30+v*0.04,0.62+v*0.04,0.22+v*0.04),
             lift_node("result","ovl0","east",0.22+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"qtr_embed_overlap_lift","cube","slab",["embed","overlap","vertical","quarter"],
                  "Embedded void slab then overlapped; east lift creates ground passage below.",nodes,"result",3,3.5,870)

def b64(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             nested_related_node("nest0","m0","x",0.25+v*0.04,0.68+v*0.05),
             courtyard_node("result","nest0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_nested_court","cube","slab",["nest","long_axis","eighth"],
                  "Eighth slab with nested inner volume; east courtyard as layered civic court.",nodes,"result",3,3.5,780)

def b65(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             book_carve_node("carve0","m0","z","east",0.28+v*0.05,1.0,0.42+v*0.04),
             notch_node("result","carve0","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"eighth_carved_notch","cube","bar",["carve","long_axis","eighth","notch"],
                  "Eighth bar east-carved then NE-notched; compact civic address on small share.",nodes,"result",4,3.5,900)

def b66(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             intersect_related_node("inter0","m0","z",90.0,0.38+v*0.04,0.78+v*0.04),
             intersect_related_node("inter1","inter0","y",45.0,0.36+v*0.04,0.72+v*0.04),
             carve_void_node("result","inter1",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_double_intersect_carve","cube","bar",["intersect","long_axis","eighth"],
                  "Double cross-bar intersection creates figure-8 plan; east carve opens address.",nodes,"result",4,3.5,960)

def b67(pid, v):
    w,d,h = 0.68, 0.68, 2.5
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             taper_node("tap0","m0","z",[1.0,1.0],[0.68+v*0.04,0.68+v*0.04],0.0,3),
             bend_node("bend0","tap0","y",20+v*8,4),
             lift_node("result","bend0","east",0.24+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"eighth_taper_bend_lift","cube","tower",["taper","bend","long_axis","eighth"],
                  "Eighth tower tapered and bent; east lift opens public passage at tower base.",nodes,"result",5,3.5,1150)

def b68(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             pinch_node("pinch0","m0","z",0.46+v*0.04,0.68+v*0.05,2.0+v*0.3,4),
             related_array_node("arr0","pinch0","y",2,"array",1.15+v*0.05,0.0,0.88+v*0.04,"input_base"),
             courtyard_node("result","arr0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_pinch_array_court","cube","slab",["pinch","join","array","long_axis","eighth"],
                  "Pinched slab arrayed; east courtyard at pinch waist between units.",nodes,"result",4,3.5,930)

def b69(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             boundary_expand_node("exp0","m0","z",0.20+v*0.05,0.44+v*0.05),
             notch_node("result","exp0","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"eighth_extrude_notch","cube","block",["extrude","short_axis","eighth","notch"],
                  "Eighth block expanded and profiled; east notch at entry corner.",nodes,"result",4,3.5,920)

def b70(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             book_lodge_node("lodge0","m0","z",0.26+v*0.04,0.52+v*0.04,1.0),
             carve_void_node("result","lodge0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_lodge_carve","cube","bar",["lodge","short_axis","eighth","carve_void"],
                  "Eighth bar lodged with guest; east carve void in the gap below guest.",nodes,"result",3,3.5,800)

def b71(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             book_extract_node("ext0","m0","z","east",0.26+v*0.04,0.52+v*0.04,1.0),
             lift_node("result","ext0","east",0.22+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"eighth_extract_lift","cube","slab",["extract","short_axis","eighth","lift"],
                  "Eighth slab extraction channel; east lift opens subtracted volume as passage.",nodes,"result",3,3.5,820)

def b72(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             book_notch_node("notch0","m0","z","sw",1.0,0.24+v*0.04),
             intersect_related_node("inter0","notch0","z",90.0,0.38+v*0.04,0.76+v*0.04),
             courtyard_node("result","inter0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_inscribe_intersect_court","cube","bar",["inscribe","intersect","short_axis","eighth"],
                  "Notched bar cross-intersected; east courtyard at the interlocking junction.",nodes,"result",4,3.5,980)

def b73(pid, v):
    w,d,h = 2.2, 1.45, 0.28
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             inflate_node("infl0","m0","z",1.14+v*0.05,1.20+v*0.05,2.2+v*0.3,4),
             related_array_node("arr0","infl0","x",2,"pack",1.10+v*0.05,0.0,0.90+v*0.04,"input_base"),
             notch_node("result","arr0","east","ne",0.26+v*0.03,0.36,0.55)]
    return mkprog(pid,v,"eighth_inflate_pack_notch","cube","slab",["inflate","pack","short_axis","eighth"],
                  "Eighth inflated slab packed in pair; east notch at billowing public face.",nodes,"result",3,3.5,820)

def b74(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             book_embed_void_node("emb0","m0","z","center",0.30+v*0.05,0.50+v*0.04),
             taper_node("tap0","emb0","z",[1.0,1.0],[0.72+v*0.04,0.72+v*0.04],0.0,3),
             carve_void_node("result","tap0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_embed_taper_carve","cube","block",["embed","taper","short_axis","eighth"],
                  "Eighth block embed-voided then tapered; east carve at tapered public face.",nodes,"result",4,3.5,940)

def b75(pid, v):
    w,d,h = 0.68, 0.68, 2.5
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             book_split_node("sp0","m0","y",0.0,0.10+v*0.03,1.0,1.0,1.0,0.50+v*0.04,"east"),
             courtyard_node("result","sp0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_split_court","cube","tower",["split","vertical","eighth","courtyard"],
                  "Eighth tower split displaces one wing; east courtyard in hinge gap.",nodes,"result",5,3.5,1150)

def b76(pid, v):
    w,d,h = 1.0, 1.0, 1.0
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             book_notch_node("notch0","m0","z","nw",1.0,0.25+v*0.05),
             notch_node("result","notch0","east","ne",0.28+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"eighth_notch_entry","cube","block",["notch","vertical","eighth"],
                  "Eighth block corner-notched; east notch as minimal civic entry.",nodes,"result",4,3.5,900)

def b77(pid, v):
    w,d,h = 2.8, 0.62, 0.48
    nodes = [box_node("box0",w,d,h), mat4_node("m0","box0",scale_mat4(0.55,0.55,1.0)),
             bend_node("bend0","m0","z",22+v*8,4),
             bend_node("bend1","bend0","y",-16-v*6,4),
             carve_void_node("result","bend1",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_double_bent_carve","cube","bar",["bend","vertical","eighth","carve_void"],
                  "Eighth bar double-bent in two axes; east carve at curved civic face.",nodes,"result",4,3.5,960)

# ─── builder dispatch table ──────────────────────────────────────────────────
BUILDERS = [
    b0,b1,b2,b3,b4,b5,b6,b7,b8,b9,
    b10,b11,b12,b13,b14,b15,b16,b17,b18,b19,
    b20,b21,b22,b23,b24,b25,b26,b27,b28,b29,
    b30,b31,b32,b33,b34,b35,b36,b37,b38,b39,
    b40,b41,b42,b43,b44,b45,b46,b47,b48,b49,
    b50,b51,b52,b53,b54,b55,b56,b57,b58,b59,
    b60,b61,b62,b63,b64,b65,b66,b67,b68,b69,
    b70,b71,b72,b73,b74,b75,b76,b77,
]

assert len(BUILDERS) == 78

# ─── global principle IDs from the offer ────────────────────────────────────
ALL_PRINCIPLE_IDS = [
    "book:operative:bend", "book:operative:fracture", "book:combination:04:embed+embed",
    "book:combination:17:branch+expand", "book:case:60:carve+offset",
    "book:operative:branch", "book:operative:rotate", "book:operative:inscribe",
    "book:combination:12:intersect+split", "book:aggregation:stack:bend",
    "book:case:68:lift+extrude", "book:operative:interlock", "book:operative:shear",
    "book:combination:08:expand+expand", "book:aggregation:reflect:expand",
    "book:case:64:overlap+expand", "book:operative:bend", "book:operative:fracture",
    "book:combination:03:split+split", "book:combination:16:bend+branch",
    "book:aggregation:join:split", "book:operative:inflate", "book:operative:overlap",
    "book:operative:inscribe", "book:combination:12:intersect+split",
    "book:aggregation:stack:bend", "book:case:68:lift+extrude",
    "book:operative:interlock", "book:operative:shear",
    "book:combination:07:branch+branch", "book:combination:20:notch+twist",
    "book:case:63:expand+nest", "book:operative:offset", "book:operative:compress",
    "book:combination:03:split+split", "book:combination:16:bend+branch",
    "book:aggregation:join:split", "book:operative:inflate", "book:operative:overlap",
    "book:operative:inscribe", "book:combination:11:inscribe+intersect",
    "book:aggregation:pack+stack:branch", "book:case:67:lift+carve",
    "book:operative:twist", "book:operative:pinch",
    "book:combination:07:branch+branch", "book:combination:20:notch+twist",
    "book:case:63:expand+nest", "book:operative:offset", "book:operative:compress",
    "book:combination:03:split+split", "book:combination:15:taper+bend",
    "book:aggregation:join+array:pinch", "book:operative:extrude",
    "book:operative:lodge", "book:operative:extract",
    "book:combination:11:inscribe+intersect", "book:aggregation:pack+stack:branch",
    "book:case:67:lift+carve", "book:operative:twist", "book:operative:pinch",
    "book:combination:07:branch+branch", "book:combination:19:shift+notch",
    "book:case:62:embed+overlap", "book:operative:nest", "book:operative:carve",
    "book:combination:02:intersect+intersect", "book:combination:15:taper+bend",
    "book:aggregation:join+array:pinch", "book:operative:extrude",
    "book:operative:lodge", "book:operative:extract",
    "book:combination:11:inscribe+intersect", "book:aggregation:pack:inflate",
    "book:case:66:embed+taper", "book:operative:split", "book:operative:notch",
    "book:combination:06:bend+bend",
]

assert len(ALL_PRINCIPLE_IDS) == 78

# ─── generate 120 programs ───────────────────────────────────────────────────
def generate():
    # Strategy: each path gets called once (v=0), then we call 42 paths again (v=1)
    # to reach 120 total, keeping max reuse = 2 per path
    
    # First pass: all 78 paths, variant 0
    programs = []
    for idx in range(78):
        pid = PATH_IDS[idx]
        prog = BUILDERS[idx](pid, 0)
        programs.append(prog)
    
    # Second pass: 42 more, pick paths that benefit most from a second variant
    # Use indices 0..41 for the second variant
    for idx in range(42):
        pid = PATH_IDS[idx]
        prog = BUILDERS[idx](pid, 1)
        # Make name unique
        prog["name"] = prog["name"].replace("_v1", "_v1b") if "_v1" in prog["name"] else prog["name"] + "b"
        programs.append(prog)
    
    assert len(programs) == 120, f"Expected 120 programs, got {len(programs)}"
    
    # Collect all unique principle IDs used
    all_pids = set()
    for p in programs:
        all_pids.update(p.get("book_principle_ids", []))
    
    return {
        "programs": programs,
        "book_principle_ids": sorted(list(all_pids)),
    }

# ─── validation ──────────────────────────────────────────────────────────────
def validate(payload):
    if not HAS_SCHEMA:
        print("Skipping schema validation (jsonschema not installed)")
        return True
    
    schema = json.loads(Path(SCHEMA_PATH).read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(payload))
    if errors:
        for e in errors[:20]:
            print(f"SCHEMA ERROR: {e.path} → {e.message}")
        print(f"Total errors: {len(errors)}")
        return False
    else:
        print(f"Schema validation PASSED: {len(payload['programs'])} programs, 0 errors")
        return True

# ─── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating 120 BOOK programs for cycle-comp18...")
    payload = generate()
    
    # Quick stats
    seeds = {}
    forms = {}
    for p in payload["programs"]:
        s = p["base_seed"]; seeds[s] = seeds.get(s,0) + 1
        f = p["base_form_id"]; forms[f] = forms.get(f,0) + 1
    print(f"Seeds: {seeds}")
    print(f"Forms: {forms}")
    print(f"Unique path IDs: {len(set(p['book_composition_path_id'] for p in payload['programs']))}")
    
    ok = validate(payload)
    if not ok:
        print("VALIDATION FAILED - check errors above")
        sys.exit(1)
    
    out = json.dumps(payload, ensure_ascii=False, indent=2)
    Path(OUTPUT_PATH).write_text(out, encoding="utf-8")
    print(f"Written {len(out)//1024}KB to {OUTPUT_PATH}")
    print("Done.")
