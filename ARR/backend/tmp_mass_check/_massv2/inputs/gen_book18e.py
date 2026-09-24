"""
gen_book18e.py
Generate 120 BOOK mass candidates for cycle-comp18.
78 path IDs × reuse ≤ 2 = 120 programs.
All schema lessons applied from previous successful run.
"""

import json, math, random
from jsonschema import Draft7Validator

SCHEMA_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json"
OUTPUT_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json"

random.seed(42)

# ── helpers ──────────────────────────────────────────────────────────────────

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
    """Literal-type param — all 5 value fields required."""
    return {"name": name, "value_type": "literal",
            "numeric_value": float(nv),
            "string_value": str(sv),
            "boolean_value": bool(bv),
            "vector_value": list(vv) if vv is not None else [0,0,0],
            "structured_json": sj}

def sjson_p(name, obj):
    return {"name": name, "value_type": "structured_json", "numeric_value": 0.0,
            "string_value": "", "boolean_value": False, "vector_value": [0,0,0],
            "structured_json": obj}

def mat4_p(m):
    return {"name": "matrix4", "value_type": "matrix4",
            "numeric_value": 0.0, "string_value": "", "boolean_value": False,
            "vector_value": [0,0,0], "structured_json": None,
            "matrix4_value": m}

def identity_mat4():
    return [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

def scale_mat4(sx, sy, sz):
    return [[sx,0,0,0],[0,sy,0,0],[0,0,sz,0],[0,0,0,1]]

# ── primitive nodes ──────────────────────────────────────────────────────────

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

def scale_node(nid, inp, sx, sy, sz, role="dominant_mass"):
    return {
        "id": nid, "kind": "transform", "operator": "scale", "inputs": [inp],
        "semantic_role": role,
        "parameters": [vec_p("scale", [sx, sy, sz])]
    }

# ── BOOK macro nodes ─────────────────────────────────────────────────────────

def courtyard_node(nid, inp, margin=0.25, open_side="east"):
    return {
        "id": nid, "kind": "macro", "operator": "courtyard", "inputs": [inp],
        "semantic_role": "public_threshold",
        "parameters": [
            num_p("margin_ratio", margin),
            str_p("open_side", open_side),
        ]
    }

def carve_void_node(nid, inp, margin=0.25, open_side="east"):
    return {
        "id": nid, "kind": "macro", "operator": "carve_void", "inputs": [inp],
        "semantic_role": "public_threshold",
        "parameters": [
            num_p("margin_ratio", margin),
            str_p("open_side", open_side),
        ]
    }

def notch_node(nid, inp, side="east", corner="ne", ratio=0.3, width_ratio=0.4, height_ratio=0.6):
    return {
        "id": nid, "kind": "macro", "operator": "notch", "inputs": [inp],
        "semantic_role": "public_threshold",
        "parameters": [
            str_p("side", side),
            str_p("corner", corner),
            num_p("ratio", ratio),
            num_p("width_ratio", width_ratio),
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
            str_p("access_side", access_side),
            str_p("axis", axis),
            str_p("layout", layout),
            num_p("gap_ratio", gap_ratio),
            num_p("height_ratio", height_ratio),
            bool_p("bridge", bridge),
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
        "parameters": [
            str_p("axis", axis),
            num_p("angle_degrees", angle),
            num_p("subdivisions", subdivisions),
        ]
    }

def taper_node(nid, inp, axis="z", start_scale=None, end_scale=None,
               lower_floor_fraction=0.0, subdivisions=3, role="dominant_mass"):
    if start_scale is None: start_scale = [1.0, 1.0]
    if end_scale is None: end_scale = [0.7, 0.7]
    return {
        "id": nid, "kind": "modifier", "operator": "taper", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            vec_p("start_scale", start_scale),
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
        "parameters": [
            str_p("axis", axis),
            num_p("angle_degrees", angle),
            num_p("subdivisions", subdivisions),
        ]
    }

def shear_node(nid, inp, axis="z", amount=0.3, direction_vec=None, role="dominant_mass"):
    if direction_vec is None:
        direction_vec = [1.0, 0.0, 0.0]
    return {
        "id": nid, "kind": "transform", "operator": "shear", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            num_p("amount", amount),
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
            str_p("axis", axis),
            lit_p("factor", nv=factor),
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
            str_p("axis", axis),
            lit_p("waist_ratio", nv=waist_ratio),
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
            str_p("axis", axis),
            num_p("angle_degrees", angle_degrees),
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
            str_p("axis", axis),
            str_p("face_side", face_side),
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
            str_p("axis", axis),
            str_p("face_side", face_side),
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
            str_p("axis", axis),
            num_p("angle_degrees", angle_degrees),
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
            str_p("axis", axis),
            str_p("face_side", face_side),
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
            str_p("axis", axis),
            str_p("corner", corner),
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
            str_p("axis", axis),
            num_p("angle_degrees", angle_degrees),
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
            str_p("axis", axis),
            num_p("amount", amount),
            lit_p("shoulder_fraction", nv=shoulder_fraction),
        ]
    }

def book_embed_void_node(nid, inp, axis="z", position="east", embedded_ratio=0.35,
                          guest_scale=0.5, outward_sign=1.0, role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "embed_void", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            str_p("position", position),
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
            str_p("axis", axis),
            num_p("count", count),
            str_p("mode", mode),
            lit_p("spacing_ratio", nv=spacing_ratio),
            lit_p("stagger_ratio", nv=stagger_ratio),
            lit_p("unit_scale", nv=unit_scale),
            str_p("vertical_anchor", vertical_anchor),
        ]
    }

def tapered_tower_node(nid, inp, axis="z", start_scale=None, end_scale=None,
                        subdivisions=3, role="dominant_mass"):
    if start_scale is None: start_scale = [1.0, 1.0]
    if end_scale is None: end_scale = [0.6, 0.6]
    return {
        "id": nid, "kind": "macro", "operator": "tapered_tower", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            vec_p("start_scale", start_scale),
            vec_p("end_scale", end_scale),
            num_p("subdivisions", subdivisions),
            lit_p("scale_top", nv=end_scale[0]),
            vec_p("pivot", [0.5, 0.5, 0.0]),
        ]
    }

def leaning_tower_node(nid, inp, direction="x", amount=0.3, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "leaning_tower", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("direction", direction),
            num_p("amount", amount),
        ]
    }

def setback_node(nid, inp, direction="x", levels=3, setback_ratio=0.1,
                  shift_per_level=None, role="dominant_mass"):
    if shift_per_level is None: shift_per_level = [0.0, 0.0, 0.0]
    return {
        "id": nid, "kind": "macro", "operator": "setback", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("direction", direction),
            num_p("levels", levels),
            num_p("setback_ratio", setback_ratio),
            vec_p("shift_per_level", shift_per_level),
        ]
    }

def terrace_node(nid, inp, direction="x", levels=3, setback_ratio=0.1,
                  direction_sign=1.0, shift_per_level=None, role="dominant_mass"):
    if shift_per_level is None: shift_per_level = [0.0, 0.0, 0.0]
    return {
        "id": nid, "kind": "macro", "operator": "terrace", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("direction", direction),
            num_p("levels", levels),
            num_p("setback_ratio", setback_ratio),
            lit_p("direction_sign", nv=direction_sign),
            vec_p("shift_per_level", shift_per_level),
        ]
    }

def stepped_mass_node(nid, inp, direction="x", levels=3, setback_ratio=0.12,
                       podium_height_ratio=0.3, podium_scale=0.9,
                       shift_per_level=None, role="dominant_mass"):
    if shift_per_level is None: shift_per_level = [0.0, 0.0, 0.0]
    return {
        "id": nid, "kind": "macro", "operator": "stepped_mass", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("direction", direction),
            num_p("levels", levels),
            num_p("setback_ratio", setback_ratio),
            lit_p("podium_height_ratio", nv=podium_height_ratio),
            lit_p("podium_scale", nv=podium_scale),
            vec_p("shift_per_level", shift_per_level),
        ]
    }

def cantilever_node(nid, inp, start_ratio=0.55, vector_xyz=None, role="program_space"):
    if vector_xyz is None: vector_xyz = [0.25, 0.0, 0.0]
    return {
        "id": nid, "kind": "macro", "operator": "cantilever", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            lit_p("start_ratio", nv=start_ratio),
            vec_p("vector", vector_xyz),
        ]
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

def merge_related_node(nid, inp, axis="x", gap_ratio=0.08, unit_scale=0.85,
                        role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "merge_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            num_p("gap_ratio", gap_ratio),
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

def interlock_related_node(nid, inp, axis="x", angle_degrees=0.0, bar_ratio=0.4,
                             distance_ratio=0.5, outward_sign=1.0, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "interlock_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            num_p("angle_degrees", angle_degrees),
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
            str_p("axis", axis),
            num_p("angle_degrees", angle_degrees),
            lit_p("bar_ratio", nv=bar_ratio),
            lit_p("unit_scale", nv=unit_scale),
        ]
    }

def join_related_node(nid, inp, bridge_ratio=0.3, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "join_related", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            lit_p("bridge_ratio", nv=bridge_ratio),
        ]
    }

def cross_mass_node(nid, inp, angle_degrees=90.0, role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "cross_mass", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            num_p("angle_degrees", angle_degrees),
        ]
    }

def grid_mass_node(nid, inp, column_offset_ratio=0.25, row_spacing_ratio=1.2,
                   role="dominant_mass"):
    return {
        "id": nid, "kind": "macro", "operator": "grid_mass", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            num_p("column_offset_ratio", column_offset_ratio),
            num_p("row_spacing_ratio", row_spacing_ratio),
        ]
    }

def puncture_node(nid, inp, axis="z", count=2, n=2, ratio=0.15, spacing_ratio=0.5,
                   role="program_space"):
    return {
        "id": nid, "kind": "macro", "operator": "puncture", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("axis", axis),
            num_p("count", count),
            lit_p("n", nv=n),
            num_p("ratio", ratio),
            lit_p("spacing_ratio", nv=spacing_ratio),
        ]
    }

def ellipsoidize_node(nid, inp, segments=16, role="dominant_mass"):
    return {
        "id": nid, "kind": "modifier", "operator": "ellipsoidize", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            num_p("segments", segments),
        ]
    }

def mirror_array_node(nid, inp, normal=None, pivot=None, role="dominant_mass"):
    if normal is None: normal = [0.0, 1.0, 0.0]
    if pivot is None: pivot = [0.0, 0.0, 0.0]
    return {
        "id": nid, "kind": "pattern", "operator": "mirror_array", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            vec_p("normal", normal),
            vec_p("pivot", pivot),
        ]
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
        "parameters": [
            str_p("axis", axis),
            lit_p("fraction", nv=fraction),
            str_p("anchor", anchor),
        ]
    }

def cut_corner_node(nid, inp, corner="ne", ratio=0.2, role="dominant_mass"):
    return {
        "id": nid, "kind": "modifier", "operator": "cut_corner", "inputs": [inp],
        "semantic_role": role,
        "parameters": [
            str_p("corner", corner),
            num_p("ratio", ratio),
        ]
    }

# ── dimensional intent ───────────────────────────────────────────────────────

def dim_intent(storeys=4, storey_h=3.5, target_gfa=None):
    if target_gfa is None:
        target_gfa = storeys * 320.0  # rough
    return {
        "schema_version": "arr.maas.dimensional_intent.v1",
        "storey_count": storeys,
        "storey_height_m": storey_h,
        "target_gfa_m2": float(target_gfa),
        "delivery_policy": "preserve_physical_dimensions",
        "programme_status": "unknown"
    }

# ── seeds: (w,d,h) for box ───────────────────────────────────────────────────

SEEDS = {
    "block": (1.0, 1.0, 1.0),
    "slab":  (2.2, 1.45, 0.28),
    "bar":   (2.8, 0.62, 0.48),
    "tower": (0.68, 0.68, 2.5),
}

# ── 78 template functions ─────────────────────────────────────────────────────
# Each returns (nodes, root_id, name_suffix, base_form_id, base_seed,
#               intent_tags, rationale, dimensional_intent_obj, book_principle_ids_local)

TEMPLATES = []

def template(path_id):
    def decorator(fn):
        TEMPLATES.append((path_id, fn))
        return fn
    return decorator

# PATH IDs from offer – 78 paths
PATH_IDS = [
    "book:path:9bab887f2e519077dcbe8e5977897df8a80deb6d1a280936cccca005d8555719",  # 1/1 long bend
    "book:path:9042c82e97a383fc1f1e97948ac87e0bac17a95d0d8587255d48710c0ac64040",  # 1/1 long fracture
    "book:path:11a0d7a5a51e85d9ec1cf2f3b3eaa086eb6841d1fec6a184077cc5db1851b185",  # 1/1 long embed+embed
    "book:path:dd28b0c53f08a2d1812dc32d7b562ee9b7bc4a1ca98b90a13152bbf534dd27f2",  # 1/1 long branch+expand
    "book:path:c7fcd0c126b7b32471e69e703e7e9022ab3963899ef974c879ec44b4162b197a",  # 1/1 long carve+offset
    "book:path:b95277004fb2b89b21445182aab353c444a4ea7a1e7044f8c2e7e07599226909",  # 1/1 short branch
    "book:path:6bb95e7e0461e1606d4430a1e8a7c4ad2b3dc96d74ff48bced73da05b9df6cf5",  # 1/1 short rotate
    "book:path:2f971be29f0d428a9879b1c00948ac738f8921db4163797414074d894ac8efb9",  # 1/1 short inscribe
    "book:path:e510ad256385b556152790586ff8d15493cf9c1d6cffbd352f8e0d326c4ca71a",  # 1/1 short intersect+split
    "book:path:53c55b4da48903af110459fa120baeaec3b186edf22d6890fa718d0ad6b1f5b5",  # 1/1 short bend+stack
    "book:path:f285f713076b19ee7cc1b58f2d44f85aeec8a11bfe30fc0b77e876a1543a612b",  # 1/1 short lift+extrude
    "book:path:05470e618703ead632e6029bac7312306f05a6f404cb1a84f60043e0fb2b6b5f",  # 1/1 vert interlock
    "book:path:ff644fb6db1684200f7c558764b8298c45bab946fac40c3df9cc090edf479977",  # 1/1 vert shear
    "book:path:61ddaacb14d1ebd0e0c24518a19a9b01f9a48f50fbfd66fd280b92abe59722b7",  # 1/1 vert expand+expand
    "book:path:2e2f65a3f44c510ecfa66c729db4c53684b3cc4033f5844bc980f4fa4bf1ad70",  # 1/1 vert expand+reflect
    "book:path:aadaf4340a4980ec0c691cf6c70bf78936b4b4b1471a6340d384abcae9ee0a2c",  # 1/1 vert overlap+expand
    "book:path:2e24111503e808e954bf437374af114ede99fddb568beab59253edb011273835",  # 3/8 long bend
    "book:path:84d0345cadb3c43a13aa423bc1fddfb175b338b095c86bc9ec4b1eab2952afd0",  # 3/8 long fracture
    "book:path:b96fa24e6b07a0419331b82a471addcf0f980f71d6fee1bffd80a5e1ed1ea126",  # 3/8 long split+split
    "book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e",  # 3/8 long bend+branch
    "book:path:2fcf5f31e6d7ec9acbe02f9c3a6bb20e72df122cf29d989dd630f4d7fc022791",  # 3/8 long split+join
    "book:path:423e633a08a43369b6ccda29d5604fc061c6e20e52e460c9867ddd1e5b13c2c0",  # 3/8 short inflate
    "book:path:6acac573694cb27de1572fd0a9de5fb76aed871fea929c88573a072c95a8bbbb",  # 3/8 short overlap
    "book:path:1dbb96b395ddd04b17719976be7a62b1bdb6256f080c74a7b0de12c908a7915c",  # 3/8 short inscribe
    "book:path:f91a61a346c29c85aa4907c5e5c53d10e00a7530d28316c598fcc29d75f7fb55",  # 3/8 short intersect+split
    "book:path:13fbf6da4b2addf28d4678956f747d8f112740ed2ca07de19e7a4884b2d43956",  # 3/8 short bend+stack
    "book:path:4542c2a1884b1b256fbdea6e3ffd434dac31db9212deb3a328bb168fcfc1a6e4",  # 3/8 short lift+extrude
    "book:path:e1e90099b5d07535d9361727c7d4b028f702499491b0588fdb2c926912013fb5",  # 3/8 vert interlock
    "book:path:f7755521cc02b4d565cddffa435faa30d79095ee7d62ce0588cbc8fc33fa2b6f",  # 3/8 vert shear
    "book:path:def59b665a24ebd51c08a3812668edc1a6131552a8055b2d7cb88de8de90f4f5",  # 3/8 vert branch+branch
    "book:path:3ab1e90c58b2293f63e75df8acabb9308b747cd6304c4511b2a47ed9ce8821c3",  # 3/8 vert notch+twist
    "book:path:cfeca7238d109f8ccf184e9ab42319aadf2d36f2aca116ba295ae47cbb6ca11b",  # 3/8 vert expand+nest
    "book:path:08e14d9ef6f30e7f2700d6e5f895d4911944adbfd16a0477dbfee0afeebfbf70",  # 1/2 long offset
    "book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb",  # 1/2 long compress
    "book:path:60778ae3e99cf12bb7e8461f50ee3332b7a47ed4893d70cb2d8400fd22cc49cf",  # 1/2 long split+split
    "book:path:0b828fd1f09aeb9b5e3096a6cfe15c3cf1d709a475844690e9f3085fbdb9b8b1",  # 1/2 long bend+branch
    "book:path:d2cb499b7d8b00c2ace3d4b6893bc583e2307d3d6cdb0ac96b319253fe0529c4",  # 1/2 long split+join
    "book:path:eccfafc4718361d6aec40a901f53b344d4bff77683f4887715da5adcce05157f",  # 1/2 short inflate
    "book:path:c15ec55248a4fc32d3f15fea2da9b94c5831c48f2dedecef91ddf03a61f04ef1",  # 1/2 short overlap
    "book:path:591a729db54894dfd9449b5e5f08781d509ee6da02353d574828e141854ef1fe",  # 1/2 short inscribe
    "book:path:a34184c51ffd9faa6f4e694bd0df018b4499f561be4b29d1f086e7b8361fd7b7",  # 1/2 short inscribe+intersect
    "book:path:9c9d6d2d18bf525d39eb0c2299651d643b20f3f3e0de68975addd59e346d58d2",  # 1/2 short branch+pack+stack
    "book:path:82e07b845038d9e2c03a74eab9531bfdb2aaa74dd621e9ab21c72eb467b32bd7",  # 1/2 short lift+carve
    "book:path:716df07ca23e72681a3aca19b6a160a3c867f21315b111d0c6ac21a2700be269",  # 1/2 vert twist
    "book:path:7f4ace179d50c15c3a63cd24d5dcb7e3420da79697dcb07afb1a30f73bbed628",  # 1/2 vert pinch
    "book:path:aec174c38f9ed86be822dd7813012953b17a2443337cd862c35837a7c34ab023",  # 1/2 vert branch+branch
    "book:path:4805f5934fe933b3108aeb3a3aa5a567a1a1bd1debe1a625217a979a35f16c24",  # 1/2 vert notch+twist
    "book:path:e688a33bce52391b696ecea5bef1c7926ec4e15d1a02971bebfaf8fcb990c13b",  # 1/2 vert expand+nest
    "book:path:9ff66e145418829ccc5e710634ec50389ce05bc62f6496984bde22110528e383",  # 1/4 long offset
    "book:path:546119cfb82a276ceee53e1eb09d960d054ff4bacd4853bc824ba6ed9ffd8e8f",  # 1/4 long compress
    "book:path:f1440150bbd785859ef88baca5734f8731b6b029da123797ae55c43541ecb398",  # 1/4 long split+split
    "book:path:0bac03a066888497ad4cdc5a727e609bdb620a3ef13ef9cc5394a46de7a09449",  # 1/4 long taper+bend
    "book:path:af83d6add866295511a823d82a17f6d3b2316e11204b251b3c0c6eee90de813f",  # 1/4 long pinch+join+array
    "book:path:f42375c1818d4ccdef5278032d64aa984e673a76b1e44056b286a08f507288d1",  # 1/4 short extrude
    "book:path:89a8d2e071e7dc228815ddab41a199bf7379d5742d861095f20ab2de6fd610f5",  # 1/4 short lodge
    "book:path:bbd403cec5ff6827cf04b266a65afdab72752a8071a42a83017b53f878176551",  # 1/4 short extract
    "book:path:b1dc18f7817ae62db7951887748c90355ffaa9ee10880a1dfaad396c8a5e54e0",  # 1/4 short inscribe+intersect
    "book:path:ea3fdbfddf0a32805dc837821770519d713d02a468fa8e914311a1e122289d20",  # 1/4 short branch+pack+stack
    "book:path:0e3fe6f19fe3fb3b4fdfecd76c496e00141469a5ab4be263385f49ea58ce99b5",  # 1/4 short lift+carve
    "book:path:b161eb4c3bb6230cd34980d091fc44bf52f7d2648e59f55b39dc46e64225dc46",  # 1/4 vert twist
    "book:path:56f69a2038120b9187f1387efee21a6a63cf530d026b6f10dfab37c2db2dc717",  # 1/4 vert pinch
    "book:path:dc50b322c264219be6835f6b50fc2a3e5ffba233fd5e5f9fa3813b14d5523193",  # 1/4 vert branch+branch
    "book:path:0d5b1e3a233d34e16073c222838ee053eabeb8692327fc62ef668c7b75a716d1",  # 1/4 vert shift+notch
    "book:path:bd7cfc87da1811e45875acde3aa82d513fc343204bca6bcd2fb26f3a1d1357e7",  # 1/4 vert embed+overlap
    "book:path:c58193dcc81b7f6fb8a25fd8bb18808d47ae79a9765ff716fd84b09d1befc70b",  # 1/8 long nest
    "book:path:2e91334e6426f5c7ca6a8f4cfce4ca746f1d0f3091273eaf3896fe4900b3f7bd",  # 1/8 long carve
    "book:path:58d160602ccaafb30f737d33723e43a8ae2841eaac7fda840c8f5d8886775abf",  # 1/8 long intersect+intersect
    "book:path:150c3892213b9cc014f2985158abc9905f8c9b2cc1c690a1cc7e41068a044a6f",  # 1/8 long taper+bend
    "book:path:a024d86c2d00b3f85de00140e9b221e1e73de64e83a85c58dc4e52ea478988e0",  # 1/8 long pinch+join+array
    "book:path:a254a71182ed875bbe8102de50270b1e19538916fe00c1a609ea6c5950fbef0b",  # 1/8 short extrude
    "book:path:d138480c1ee6ed85eed95f1cfd921852b69d33e8e412f0f28a7c3194117efa38",  # 1/8 short lodge
    "book:path:42bc62991fbaf0eaa42d48e37ede8e507613abc648a0e32338a19e19862787e2",  # 1/8 short extract
    "book:path:eee048bfdfa8ab2892e3a8a604bd2a302efd5cb77e995014dc28074c5b3811b4",  # 1/8 short inscribe+intersect
    "book:path:9e4457e0a1cf8fa849c73e92abc08b15423426f4949b6225cab08c1034e531a5",  # 1/8 short inflate+pack
    "book:path:71fb46d7af677eb3b5345e94d27f0fa1ef9b257aadc2cd746aec550ba2a0419b",  # 1/8 short embed+taper
    "book:path:dfbf81995ea510ccee2aa31dffbf03a3dd3dfcb167a0153d116724dbf65599f0",  # 1/8 vert split
    "book:path:415615bd85962e057ca3dd17914bf224fa7b6182a09f3f17db371a41b7dcc401",  # 1/8 vert notch
    "book:path:a831f22dee8c36e3a70315fa1ff822eff56f7f0deefcfb3032d54fc585e8a128",  # 1/8 vert bend+bend
]

assert len(PATH_IDS) == 78, f"Expected 78 path IDs, got {len(PATH_IDS)}"

# ── 78 builder functions ──────────────────────────────────────────────────────
# Each returns dict with: nodes, root_id, name, base_form_id, base_seed,
#                         intent_tags, rationale, dim_intent, principle_ids

def build(path_idx, variant=0):
    """Dispatch to one of 78 builders by path_idx (0-based)."""
    pid = PATH_IDS[path_idx]
    fn = BUILDERS[path_idx]
    return fn(pid, variant)

# We define 78 lambdas inline, grouped by path family
# Variant 0 = first call, 1 = second call (minor param tweak)

def _slab_seed():
    return SEEDS["slab"]

def _bar_seed():
    return SEEDS["bar"]

def _block_seed():
    return SEEDS["block"]

def _tower_seed():
    return SEEDS["tower"]

def mkprog(pid, variant, name, base_form, base_seed, tags, rationale,
           nodes, root_id, storeys=4, storey_h=3.5, target_gfa=None,
           principle_ids=None):
    if principle_ids is None:
        principle_ids = [pid]
    if target_gfa is None:
        target_gfa = storeys * 300.0
    return {
        "book_composition_path_id": pid,
        "name": f"{name}_v{variant}",
        "base_form_id": base_form,
        "base_seed": base_seed,
        "intent_tags": tags[:12],
        "nodes": nodes,
        "root_id": root_id,
        "rationale": rationale,
        "dimensional_intent": dim_intent(storeys, storey_h, target_gfa),
        "book_principle_ids": principle_ids,
    }

# ──────────────────────────────────────────────────────────────────────────────
# PATH 0: 1/1 long_axis bend  → bar + bend → courtyard(east)
# ──────────────────────────────────────────────────────────────────────────────
def b0(pid, v):
    w,d,h = _bar_seed()
    angle = 22 + v*8
    margin = 0.22 + v*0.03
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0, 1.0, 1.0)),
        bend_node("bend0", "m0", axis="z", angle=angle, subdivisions=4),
        courtyard_node("result", "bend0", margin=margin, open_side="east"),
    ]
    return mkprog(pid, v, "bent_bar_court", "cube", "bar",
                  ["bend","courtyard","long_axis","public_office"],
                  "A continuously bent bar curves to define an east-facing public court entry zone.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 1: 1/1 long_axis fracture → slab + fracture → notch(east)
def b1(pid, v):
    w,d,h = _slab_seed()
    gap = 0.10 + v*0.04
    angle = 15 + v*10
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0, 1.0, 1.0)),
        book_fracture_node("frac0", "m0", axis="z", angle_degrees=angle,
                           gap_ratio=gap, outward_sign=1.0, retained_back_ratio=0.55+v*0.05),
        notch_node("result", "frac0", side="east", corner="ne", ratio=0.28+v*0.04,
                   width_ratio=0.35, height_ratio=0.5),
    ]
    return mkprog(pid, v, "fractured_slab_notch", "cube", "slab",
                  ["fracture","notch","subtract","long_axis"],
                  "A slab mass receives a diagonal fracture void and an east corner notch marking entry.",
                  nodes, "result", storeys=3, target_gfa=900)

# PATH 2: 1/1 long_axis embed+embed → block + embed_void×2 → carve_void(east)
def b2(pid, v):
    w,d,h = _block_seed()
    er1 = 0.30 + v*0.05
    er2 = 0.25 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        book_embed_void_node("emb1", "m0", axis="z", position="east",
                             embedded_ratio=er1, guest_scale=0.45+v*0.05),
        book_embed_void_node("emb2", "emb1", axis="y", position="center",
                             embedded_ratio=er2, guest_scale=0.40+v*0.04),
        carve_void_node("result", "emb2", margin=0.20+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "double_embed_court", "cube", "block",
                  ["embed","carve_void","subtract","long_axis"],
                  "Two nested embed voids hollow the block; east carve opens the public forecourt.",
                  nodes, "result", storeys=5, target_gfa=1400)

# PATH 3: 1/1 long_axis branch+expand → bar + book_branch + boundary_expand → courtyard(east)
def b3(pid, v):
    w,d,h = _bar_seed()
    angle = 40 + v*15
    tr = 0.55 + v*0.05
    ar = 0.38 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        book_branch_node("br0", "m0", angle_degrees=angle, trunk_ratio=tr, arm_ratio=ar,
                         vertical_anchor="input_base"),
        boundary_expand_node("exp0", "br0", axis="z", amount=0.18+v*0.04,
                             shoulder_fraction=0.45+v*0.05),
        courtyard_node("result", "exp0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "branched_expanded_court", "cube", "bar",
                  ["branch","expand","long_axis","courtyard"],
                  "Arms branch from a bar trunk then expand at shoulder; east court reads as civic threshold.",
                  nodes, "result", storeys=4, target_gfa=1200)

# PATH 4: 1/1 long_axis carve+offset → slab + book_carve + offset_related → notch(east)
def b4(pid, v):
    w,d,h = _slab_seed()
    dr = 0.25 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        book_carve_node("carve0", "m0", axis="z", face_side="east",
                        depth_ratio=dr, outward_sign=1.0, width_ratio=0.40+v*0.05),
        offset_related_node("off0", "carve0", axis="x", distance_ratio=0.45+v*0.05,
                             outward_sign=1.0, unit_scale=0.75+v*0.05),
        notch_node("result", "off0", side="east", corner="se", ratio=0.25+v*0.03,
                   width_ratio=0.35, height_ratio=0.55),
    ]
    return mkprog(pid, v, "carved_offset_notch", "cube", "slab",
                  ["carve","offset","long_axis","notch"],
                  "East face carved and offset duplicated; SE notch gives corner address.",
                  nodes, "result", storeys=4, target_gfa=1000)

# PATH 5: 1/1 short_axis branch → bar + book_branch → courtyard(east)
def b5(pid, v):
    w,d,h = _bar_seed()
    angle = 60 + v*20
    tr = 0.58 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        book_branch_node("br0", "m0", angle_degrees=angle, trunk_ratio=tr,
                         arm_ratio=0.35+v*0.05, vertical_anchor="input_base"),
        courtyard_node("result", "br0", margin=0.24+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "short_branch_court", "cube", "bar",
                  ["branch","short_axis","courtyard"],
                  "Short-axis branching produces a Y-plan; courtyard opens east toward road frontage.",
                  nodes, "result", storeys=4, target_gfa=1150)

# PATH 6: 1/1 short_axis rotate → slab + book_rotate → carve_void(east)
def b6(pid, v):
    w,d,h = _slab_seed()
    ang = 25 + v*10
    rr = 0.45 + v*0.06
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        book_rotate_node("rot0", "m0", axis="z", angle_degrees=ang,
                         outward_sign=1.0, related_ratio=rr),
        carve_void_node("result", "rot0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "rotated_slab_carve", "cube", "slab",
                  ["rotate","short_axis","carve_void"],
                  "A partitioned slab child rotates about a hinge edge; east carve void marks entry.",
                  nodes, "result", storeys=3, target_gfa=870)

# PATH 7: 1/1 short_axis inscribe → block + book_notch (inscribe proxy) → notch(east)
def b7(pid, v):
    w,d,h = _block_seed()
    ratio = 0.22 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="sw",
                        outward_sign=1.0, ratio=ratio),
        notch_node("result", "notch0", side="east", corner="ne",
                   ratio=0.25+v*0.04, width_ratio=0.40, height_ratio=0.55),
    ]
    return mkprog(pid, v, "inscribed_notch_entry", "cube", "block",
                  ["inscribe","notch","short_axis","subtract"],
                  "Block inscribed with corner notch void; east notch delivers civic entrance articulation.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 8: 1/1 short_axis intersect+split → bar + intersect_related + book_split → lift(east)
def b8(pid, v):
    w,d,h = _bar_seed()
    br = 0.38 + v*0.05
    us = 0.75 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        intersect_related_node("inter0", "m0", axis="z", angle_degrees=90.0,
                               bar_ratio=br, unit_scale=us),
        book_split_node("sp0", "inter0", axis="y", angle_degrees=0.0,
                        gap_ratio=0.10+v*0.04, outward_sign=1.0, branch_sign=1.0,
                        split_generation=1.0, terminal_ratio=0.48+v*0.04,
                        access_side_sv="east"),
        lift_node("result", "sp0", access_side="east",
                  rise_ratio=0.22+v*0.04, support_ratio=0.32+v*0.03),
    ]
    return mkprog(pid, v, "intersect_split_lift", "cube", "bar",
                  ["intersect","split","short_axis","lift"],
                  "Cross-bar intersection then split displaces; east lift opens piloti-like threshold.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 9: 1/1 short_axis bend+stack → slab + bend + stack → courtyard(east)
def b9(pid, v):
    w,d,h = _slab_seed()
    angle = 18 + v*7
    cnt = 2 + v
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        bend_node("bend0", "m0", axis="y", angle=angle, subdivisions=4),
        stack_node("stk0", "bend0", count=cnt, shift_per_level=[0.05,0.0,0.0], spacing=0.5),
        courtyard_node("result", "stk0", margin=0.20+v*0.04, open_side="east"),
    ]
    return mkprog(pid, v, "bent_stacked_court", "cube", "slab",
                  ["bend","stack","short_axis","courtyard"],
                  "Bent slab stacked to create stepped section; east courtyard provides civic address.",
                  nodes, "result", storeys=3+v, target_gfa=950+v*150)

# PATH 10: 1/1 short_axis lift+extrude → block + book_lift → split_wing(east)
def b10(pid, v):
    w,d,h = _block_seed()
    dr = 0.28 + v*0.05
    gs = 0.55 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        book_lift_node("lift0", "m0", axis="z", distance_ratio=dr,
                       guest_scale=gs, outward_sign=1.0),
        split_wing_node("result", "lift0", access_side="east", axis="y",
                        layout="parallel", gap_ratio=0.12+v*0.02,
                        height_ratio=0.85+v*0.05, bridge=True,
                        connector_width_ratio=0.28+v*0.03),
    ]
    return mkprog(pid, v, "lifted_split_wing", "cube", "block",
                  ["lift","split_wing","short_axis","east"],
                  "Block lifted and split into parallel wings with east access bridge.",
                  nodes, "result", storeys=4, target_gfa=1200)

# PATH 11: 1/1 vertical interlock → bar + interlock_related → courtyard(east)
def b11(pid, v):
    w,d,h = _bar_seed()
    br = 0.38 + v*0.04
    dr = 0.45 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        interlock_related_node("inter0", "m0", axis="x", angle_degrees=0.0,
                               bar_ratio=br, distance_ratio=dr, outward_sign=1.0),
        courtyard_node("result", "inter0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "interlocked_court", "cube", "bar",
                  ["interlock","vertical","courtyard"],
                  "Two interlocked L-volumes engage through a shared zone; east court organizes entry.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 12: 1/1 vertical shear → tower + shear → notch(east)
def b12(pid, v):
    w,d,h = _tower_seed()
    amount = 0.25 + v*0.06
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        shear_node("shear0", "m0", axis="z", amount=amount,
                   direction_vec=[1.0, 0.0, 0.0]),
        notch_node("result", "shear0", side="east", corner="ne",
                   ratio=0.28+v*0.04, width_ratio=0.38, height_ratio=0.6),
    ]
    return mkprog(pid, v, "sheared_tower_notch", "cube", "tower",
                  ["shear","vertical","notch","oblique"],
                  "Tower sheared obliquely; east notch frames the civic entry recess.",
                  nodes, "result", storeys=5, target_gfa=1300)

# PATH 13: 1/1 vertical expand+expand → block + boundary_expand×2 → carve_void(east)
def b13(pid, v):
    w,d,h = _block_seed()
    a1 = 0.20 + v*0.05
    a2 = 0.15 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        boundary_expand_node("exp1", "m0", axis="z", amount=a1,
                             shoulder_fraction=0.40+v*0.06),
        boundary_expand_node("exp2", "exp1", axis="y", amount=a2,
                             shoulder_fraction=0.55+v*0.04),
        carve_void_node("result", "exp2", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "double_expand_carve", "cube", "block",
                  ["expand","vertical","carve_void","double"],
                  "Double shoulder expansion thickens block; east carve void opens through the face.",
                  nodes, "result", storeys=4, target_gfa=1200)

# PATH 14: 1/1 vertical expand+reflect → slab + boundary_expand + mirror_array → courtyard(east)
def b14(pid, v):
    w,d,h = _slab_seed()
    amount = 0.22 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        boundary_expand_node("exp0", "m0", axis="z", amount=amount,
                             shoulder_fraction=0.5+v*0.04),
        mirror_array_node("mir0", "exp0", normal=[0.0,1.0,0.0], pivot=[0.0,0.0,0.0]),
        courtyard_node("result", "mir0", margin=0.24+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "expanded_reflected_court", "cube", "slab",
                  ["expand","reflect","vertical","courtyard"],
                  "Expanded slab reflected about y-axis creates bilateral symmetry; east court as gateway.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 15: 1/1 vertical overlap+expand → bar + overlap_related + boundary_expand → notch(east)
def b15(pid, v):
    w,d,h = _bar_seed()
    sr = 0.32 + v*0.04
    sl = 0.58 + v*0.04
    vo = 0.25 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(1.0,1.0,1.0)),
        overlap_related_node("ovl0", "m0", axis="x", outward_sign=1.0,
                             shift_ratio=sr, slab_ratio=sl, vertical_overlap=vo),
        boundary_expand_node("exp0", "ovl0", axis="z", amount=0.18+v*0.04,
                             shoulder_fraction=0.48+v*0.04),
        notch_node("result", "exp0", side="east", corner="ne",
                   ratio=0.25+v*0.04, width_ratio=0.38, height_ratio=0.55),
    ]
    return mkprog(pid, v, "overlap_expanded_notch", "cube", "bar",
                  ["overlap","expand","vertical","notch"],
                  "Overlapping bars shift vertically and expand shoulder; east notch addresses the corner.",
                  nodes, "result", storeys=4, target_gfa=1150)

# PATH 16: 3/8 long_axis bend → slab + bend → carve_void(east)
def b16(pid, v):
    w,d,h = _slab_seed()
    angle = 30 + v*10
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        bend_node("bend0", "m0", axis="z", angle=angle, subdivisions=4),
        carve_void_node("result", "bend0", margin=0.22+v*0.04, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_bent_carve", "cube", "slab",
                  ["bend","long_axis","3_8_fraction","carve_void"],
                  "3/8-fraction slab bent to shelter east carve void as the civic approach.",
                  nodes, "result", storeys=3, target_gfa=800)

# PATH 17: 3/8 long_axis fracture → block + fracture → notch(east)
def b17(pid, v):
    w,d,h = _block_seed()
    gap = 0.11 + v*0.04
    angle = 20 + v*12
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        book_fracture_node("frac0", "m0", axis="z", angle_degrees=angle,
                           gap_ratio=gap, outward_sign=1.0, retained_back_ratio=0.58+v*0.04),
        notch_node("result", "frac0", side="east", corner="se",
                   ratio=0.27+v*0.04, width_ratio=0.36, height_ratio=0.5),
    ]
    return mkprog(pid, v, "3_8_fracture_notch", "cube", "block",
                  ["fracture","long_axis","3_8_fraction","notch"],
                  "3/8 block receives angled fissure and SE notch to define east entry corner.",
                  nodes, "result", storeys=3, target_gfa=850)

# PATH 18: 3/8 long_axis split+split → bar + book_split×2 → lift(east)
def b18(pid, v):
    w,d,h = _bar_seed()
    gap1 = 0.08 + v*0.03
    gap2 = 0.10 + v*0.03
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        book_split_node("sp0", "m0", axis="y", angle_degrees=0.0, gap_ratio=gap1,
                        outward_sign=1.0, branch_sign=1.0, split_generation=1.0,
                        terminal_ratio=0.45+v*0.05, access_side_sv="east"),
        book_split_node("sp1", "sp0", axis="x", angle_degrees=5.0+v*5, gap_ratio=gap2,
                        outward_sign=-1.0, branch_sign=-1.0, split_generation=2.0,
                        terminal_ratio=0.5, access_side_sv="east"),
        lift_node("result", "sp1", access_side="east",
                  rise_ratio=0.20+v*0.04, support_ratio=0.30+v*0.03),
    ]
    return mkprog(pid, v, "3_8_split_split_lift", "cube", "bar",
                  ["split","long_axis","3_8_fraction","lift"],
                  "Double split displaces bar children; east lift creates public piloti threshold.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 19: 3/8 long_axis bend+branch → bar + bend + book_branch → courtyard(east)
def b19(pid, v):
    w,d,h = _bar_seed()
    angle = 20 + v*8
    tr = 0.60 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        bend_node("bend0", "m0", axis="z", angle=angle, subdivisions=4),
        book_branch_node("br0", "bend0", angle_degrees=50+v*10, trunk_ratio=tr,
                         arm_ratio=0.36+v*0.04, vertical_anchor="input_base"),
        courtyard_node("result", "br0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_bent_branch_court", "cube", "bar",
                  ["bend","branch","long_axis","3_8_fraction","courtyard"],
                  "Bent bar then branched at arm; east courtyard catches the opening of the curve.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 20: 3/8 long_axis split+join → block + book_split + join_related → carve_void(east)
def b20(pid, v):
    w,d,h = _block_seed()
    gap = 0.09 + v*0.03
    br = 0.28 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        book_split_node("sp0", "m0", axis="y", angle_degrees=0.0, gap_ratio=gap,
                        outward_sign=1.0, branch_sign=1.0, split_generation=1.0,
                        terminal_ratio=0.5, access_side_sv="east"),
        join_related_node("join0", "sp0", bridge_ratio=br),
        carve_void_node("result", "join0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_split_join_carve", "cube", "block",
                  ["split","join","long_axis","3_8_fraction","carve_void"],
                  "Split halves bridge-joined to form a gateway void; east carve void delivers entry.",
                  nodes, "result", storeys=4, target_gfa=1000)

# PATH 21: 3/8 short_axis inflate → slab + inflate → notch(east)
def b21(pid, v):
    w,d,h = _slab_seed()
    factor = 1.12 + v*0.06
    ms = 1.18 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        inflate_node("infl0", "m0", axis="z", factor=factor,
                     middle_scale=ms, profile_power=2.2+v*0.3, subdivisions=4),
        notch_node("result", "infl0", side="east", corner="ne",
                   ratio=0.25+v*0.04, width_ratio=0.38, height_ratio=0.55),
    ]
    return mkprog(pid, v, "3_8_inflated_notch", "cube", "slab",
                  ["inflate","short_axis","3_8_fraction","notch"],
                  "3/8 slab inflated at crown; east notch indents the billowing face for entry.",
                  nodes, "result", storeys=3, target_gfa=820)

# PATH 22: 3/8 short_axis overlap → bar + overlap_related → courtyard(east)
def b22(pid, v):
    w,d,h = _bar_seed()
    sr = 0.30 + v*0.04
    sl = 0.62 + v*0.04
    vo = 0.22 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        overlap_related_node("ovl0", "m0", axis="y", outward_sign=1.0,
                             shift_ratio=sr, slab_ratio=sl, vertical_overlap=vo),
        courtyard_node("result", "ovl0", margin=0.20+v*0.04, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_overlap_court", "cube", "bar",
                  ["overlap","short_axis","3_8_fraction","courtyard"],
                  "Two overlapping bars superpose in plan; east courtyard opens into overlap zone.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 23: 3/8 short_axis inscribe → block + book_notch (inscribed void) → carve_void(east)
def b23(pid, v):
    w,d,h = _block_seed()
    ratio = 0.25 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="nw",
                        outward_sign=1.0, ratio=ratio),
        carve_void_node("result", "notch0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_inscribed_carve", "cube", "block",
                  ["inscribe","short_axis","3_8_fraction","carve_void"],
                  "NW corner notch inscribed into 3/8 block; east carve void defines the civic face.",
                  nodes, "result", storeys=3, target_gfa=870)

# PATH 24: 3/8 short_axis intersect+split → bar + intersect_related + book_split → lift(east)
def b24(pid, v):
    w,d,h = _bar_seed()
    br = 0.36 + v*0.05
    us = 0.78 + v*0.04
    gap = 0.09 + v*0.03
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        intersect_related_node("inter0", "m0", axis="z", angle_degrees=90.0,
                               bar_ratio=br, unit_scale=us),
        book_split_node("sp0", "inter0", axis="x", angle_degrees=0.0, gap_ratio=gap,
                        outward_sign=1.0, branch_sign=1.0, split_generation=1.0,
                        terminal_ratio=0.5, access_side_sv="east"),
        lift_node("result", "sp0", access_side="east",
                  rise_ratio=0.22+v*0.03, support_ratio=0.32+v*0.03),
    ]
    return mkprog(pid, v, "3_8_intersect_split_lift", "cube", "bar",
                  ["intersect","split","short_axis","3_8_fraction","lift"],
                  "Cross intersection split; east lift opens ground level as public passage.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 25: 3/8 short_axis bend+stack → slab + bend + stack → courtyard(east)
def b25(pid, v):
    w,d,h = _slab_seed()
    angle = 20 + v*8
    cnt = 2 + v
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        bend_node("bend0", "m0", axis="y", angle=angle, subdivisions=4),
        stack_node("stk0", "bend0", count=cnt, shift_per_level=[0.04,0.0,0.0], spacing=0.48),
        courtyard_node("result", "stk0", margin=0.20+v*0.04, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_bent_stacked_court", "cube", "slab",
                  ["bend","stack","short_axis","3_8_fraction","courtyard"],
                  "Bent slab stacked in 3/8 fraction; east courtyard exploits stack offset as threshold.",
                  nodes, "result", storeys=3+v, target_gfa=880+v*150)

# PATH 26: 3/8 short_axis lift+extrude → block + book_lift → split_wing(east)
def b26(pid, v):
    w,d,h = _block_seed()
    dr = 0.25 + v*0.05
    gs = 0.58 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        book_lift_node("lift0", "m0", axis="z", distance_ratio=dr,
                       guest_scale=gs, outward_sign=1.0),
        split_wing_node("result", "lift0", access_side="east", axis="y",
                        layout="parallel", gap_ratio=0.12+v*0.03,
                        height_ratio=0.88+v*0.04, bridge=True,
                        connector_width_ratio=0.25+v*0.03),
    ]
    return mkprog(pid, v, "3_8_lift_split_wing", "cube", "block",
                  ["lift","split_wing","short_axis","3_8_fraction"],
                  "3/8 block lifted and wing-split; bridge over east gap forms civic threshold.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 27: 3/8 vertical interlock → bar + interlock_related → courtyard(east)
def b27(pid, v):
    w,d,h = _bar_seed()
    br = 0.40 + v*0.04
    dr = 0.42 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        interlock_related_node("inter0", "m0", axis="x", angle_degrees=5.0+v*5,
                               bar_ratio=br, distance_ratio=dr, outward_sign=1.0),
        courtyard_node("result", "inter0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_interlock_court", "cube", "bar",
                  ["interlock","vertical","3_8_fraction","courtyard"],
                  "Interlocking L-bar pair in 3/8 scale; east courtyard mediates the civic face.",
                  nodes, "result", storeys=4, target_gfa=1000)

# PATH 28: 3/8 vertical shear → tower + shear → notch(east)
def b28(pid, v):
    w,d,h = _tower_seed()
    amount = 0.28 + v*0.06
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        shear_node("shear0", "m0", axis="z", amount=amount,
                   direction_vec=[0.0, 1.0, 0.0]),
        notch_node("result", "shear0", side="east", corner="ne",
                   ratio=0.26+v*0.04, width_ratio=0.36, height_ratio=0.58),
    ]
    return mkprog(pid, v, "3_8_shear_notch", "cube", "tower",
                  ["shear","vertical","3_8_fraction","notch"],
                  "Tower sheared along y-axis; east notch creates angled entry recess.",
                  nodes, "result", storeys=5, target_gfa=1200)

# PATH 29: 3/8 vertical branch+branch → bar + book_branch×2 → carve_void(east)
def b29(pid, v):
    w,d,h = _bar_seed()
    angle1 = 45 + v*12
    angle2 = -30 - v*8
    tr1 = 0.55 + v*0.05
    tr2 = 0.60 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        book_branch_node("br0", "m0", angle_degrees=angle1, trunk_ratio=tr1,
                         arm_ratio=0.36+v*0.04, vertical_anchor="input_base"),
        book_branch_node("br1", "br0", angle_degrees=angle2, trunk_ratio=tr2,
                         arm_ratio=0.32+v*0.04, vertical_anchor="input_base"),
        carve_void_node("result", "br1", margin=0.20+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_double_branch_carve", "cube", "bar",
                  ["branch","vertical","3_8_fraction","carve_void"],
                  "Double branching creates dendritic plan; east carve void occupies the civic notch.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 30: 3/8 vertical notch+twist → block + book_notch + twist → notch(east)
def b30(pid, v):
    w,d,h = _block_seed()
    ratio = 0.22 + v*0.05
    angle = 18 + v*7
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="nw",
                        outward_sign=1.0, ratio=ratio),
        twist_node("twist0", "notch0", axis="z", angle=angle, subdivisions=4),
        notch_node("result", "twist0", side="east", corner="ne",
                   ratio=0.26+v*0.04, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "3_8_notch_twist_entry", "cube", "block",
                  ["notch","twist","vertical","3_8_fraction"],
                  "Notched block twisted about z-axis; east notch marks the rotated civic face.",
                  nodes, "result", storeys=4, target_gfa=950)

# PATH 31: 3/8 vertical expand+nest → slab + boundary_expand + nested_related → carve_void(east)
def b31(pid, v):
    w,d,h = _slab_seed()
    amount = 0.20 + v*0.05
    dr = 0.28 + v*0.04
    us = 0.65 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.85, 0.85, 1.0)),
        boundary_expand_node("exp0", "m0", axis="z", amount=amount,
                             shoulder_fraction=0.45+v*0.05),
        nested_related_node("nest0", "exp0", axis="x", distance_ratio=dr, unit_scale=us),
        carve_void_node("result", "nest0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "3_8_expand_nest_carve", "cube", "slab",
                  ["expand","nest","vertical","3_8_fraction","carve_void"],
                  "Expanded slab with nested inner volume; east carve void opens the layered civic face.",
                  nodes, "result", storeys=3, target_gfa=900)

# PATH 32: 1/2 long_axis offset → slab + offset_related → courtyard(east)
def b32(pid, v):
    w,d,h = _slab_seed()
    dr = 0.45 + v*0.05
    us = 0.78 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        offset_related_node("off0", "m0", axis="x", distance_ratio=dr,
                             outward_sign=1.0, unit_scale=us),
        courtyard_node("result", "off0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_offset_court", "cube", "slab",
                  ["offset","long_axis","half_fraction","courtyard"],
                  "Half-fraction slab offset-duplicated along x; east courtyard in the gap.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 33: 1/2 long_axis compress → block + clip_fraction (compress proxy) → notch(east)
def b33(pid, v):
    w,d,h = _block_seed()
    frac = 0.72 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        clip_fraction_node("clip0", "m0", axis="z", fraction=frac, anchor="high"),
        notch_node("result", "clip0", side="east", corner="ne",
                   ratio=0.28+v*0.04, width_ratio=0.38, height_ratio=0.55),
    ]
    return mkprog(pid, v, "half_compress_notch", "cube", "block",
                  ["compress","long_axis","half_fraction","notch"],
                  "Half block vertically compressed; east notch cuts entry into the compact face.",
                  nodes, "result", storeys=3, target_gfa=820)

# PATH 34: 1/2 long_axis split+split → bar + book_split×2 → carve_void(east)
def b34(pid, v):
    w,d,h = _bar_seed()
    gap1 = 0.09 + v*0.03
    gap2 = 0.10 + v*0.03
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        book_split_node("sp0", "m0", axis="y", angle_degrees=0.0, gap_ratio=gap1,
                        outward_sign=1.0, branch_sign=1.0, split_generation=1.0,
                        terminal_ratio=0.48+v*0.04, access_side_sv="east"),
        book_split_node("sp1", "sp0", axis="x", angle_degrees=4.0+v*4, gap_ratio=gap2,
                        outward_sign=-1.0, branch_sign=-1.0, split_generation=2.0,
                        terminal_ratio=0.5, access_side_sv="east"),
        carve_void_node("result", "sp1", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_double_split_carve", "cube", "bar",
                  ["split","long_axis","half_fraction","carve_void"],
                  "Double split displaces half-fraction bar; east carve void addresses the public side.",
                  nodes, "result", storeys=4, target_gfa=980)

# PATH 35: 1/2 long_axis bend+branch → bar + bend + book_branch → lift(east)
def b35(pid, v):
    w,d,h = _bar_seed()
    angle = 22 + v*8
    tr = 0.58 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        bend_node("bend0", "m0", axis="z", angle=angle, subdivisions=4),
        book_branch_node("br0", "bend0", angle_degrees=48+v*10, trunk_ratio=tr,
                         arm_ratio=0.35+v*0.04, vertical_anchor="input_base"),
        lift_node("result", "br0", access_side="east",
                  rise_ratio=0.22+v*0.04, support_ratio=0.30+v*0.03),
    ]
    return mkprog(pid, v, "half_bent_branch_lift", "cube", "bar",
                  ["bend","branch","long_axis","half_fraction","lift"],
                  "Half-fraction bar bent and branched; east lift opens ground passage below arms.",
                  nodes, "result", storeys=4, target_gfa=1080)

# PATH 36: 1/2 long_axis split+join → block + book_split + join_related → courtyard(east)
def b36(pid, v):
    w,d,h = _block_seed()
    gap = 0.09 + v*0.03
    br = 0.30 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        book_split_node("sp0", "m0", axis="y", angle_degrees=0.0, gap_ratio=gap,
                        outward_sign=1.0, branch_sign=1.0, split_generation=1.0,
                        terminal_ratio=0.50, access_side_sv="east"),
        join_related_node("join0", "sp0", bridge_ratio=br),
        courtyard_node("result", "join0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_split_join_court", "cube", "block",
                  ["split","join","long_axis","half_fraction","courtyard"],
                  "Split halves bridged; east courtyard in the gateway slot becomes civic room.",
                  nodes, "result", storeys=4, target_gfa=1000)

# PATH 37: 1/2 short_axis inflate → slab + inflate → courtyard(east)
def b37(pid, v):
    w,d,h = _slab_seed()
    factor = 1.14 + v*0.06
    ms = 1.20 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        inflate_node("infl0", "m0", axis="z", factor=factor,
                     middle_scale=ms, profile_power=2.0+v*0.3, subdivisions=4),
        courtyard_node("result", "infl0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_inflated_court", "cube", "slab",
                  ["inflate","short_axis","half_fraction","courtyard"],
                  "Half-fraction slab inflated at crown; east courtyard as civic concavity.",
                  nodes, "result", storeys=3, target_gfa=820)

# PATH 38: 1/2 short_axis overlap → bar + overlap_related → notch(east)
def b38(pid, v):
    w,d,h = _bar_seed()
    sr = 0.32 + v*0.04
    sl = 0.60 + v*0.04
    vo = 0.24 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        overlap_related_node("ovl0", "m0", axis="y", outward_sign=1.0,
                             shift_ratio=sr, slab_ratio=sl, vertical_overlap=vo),
        notch_node("result", "ovl0", side="east", corner="ne",
                   ratio=0.26+v*0.03, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "half_overlap_notch", "cube", "bar",
                  ["overlap","short_axis","half_fraction","notch"],
                  "Overlapping half bars; east notch at shifted junction marks building address.",
                  nodes, "result", storeys=4, target_gfa=980)

# PATH 39: 1/2 short_axis inscribe → block + book_notch → carve_void(east)
def b39(pid, v):
    w,d,h = _block_seed()
    ratio = 0.24 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="sw",
                        outward_sign=1.0, ratio=ratio),
        carve_void_node("result", "notch0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_inscribed_carve", "cube", "block",
                  ["inscribe","short_axis","half_fraction","carve_void"],
                  "SW notch inscribed into half block; east carve void as principal address.",
                  nodes, "result", storeys=3, target_gfa=840)

# PATH 40: 1/2 short_axis inscribe+intersect → bar + book_notch + intersect_related → lift(east)
def b40(pid, v):
    w,d,h = _bar_seed()
    ratio = 0.22 + v*0.04
    br = 0.38 + v*0.04
    us = 0.78 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="se",
                        outward_sign=1.0, ratio=ratio),
        intersect_related_node("inter0", "notch0", axis="z", angle_degrees=90.0,
                               bar_ratio=br, unit_scale=us),
        lift_node("result", "inter0", access_side="east",
                  rise_ratio=0.22+v*0.04, support_ratio=0.32+v*0.03),
    ]
    return mkprog(pid, v, "half_inscribe_intersect_lift", "cube", "bar",
                  ["inscribe","intersect","short_axis","half_fraction","lift"],
                  "Notched bar intersected by cross bar; east lift frames the crossing as public passage.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 41: 1/2 short_axis branch+pack+stack → bar + book_branch + related_array → courtyard(east)
def b41(pid, v):
    w,d,h = _bar_seed()
    angle = 50 + v*15
    tr = 0.58 + v*0.04
    cnt = 2
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        book_branch_node("br0", "m0", angle_degrees=angle, trunk_ratio=tr,
                         arm_ratio=0.36+v*0.04, vertical_anchor="input_base"),
        related_array_node("arr0", "br0", axis="x", count=cnt, mode="pack",
                           spacing_ratio=1.1+v*0.05, stagger_ratio=0.0,
                           unit_scale=0.85+v*0.04, vertical_anchor="input_base"),
        courtyard_node("result", "arr0", margin=0.20+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_branch_array_court", "cube", "bar",
                  ["branch","pack","stack","short_axis","half_fraction","courtyard"],
                  "Branched bar packed in array; east courtyard in the arrangement gap.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 42: 1/2 short_axis lift+carve → block + book_lift + book_carve → split_wing(east)
def b42(pid, v):
    w,d,h = _block_seed()
    dr = 0.26 + v*0.05
    gs = 0.58 + v*0.04
    cd = 0.28 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        book_lift_node("lift0", "m0", axis="z", distance_ratio=dr,
                       guest_scale=gs, outward_sign=1.0),
        book_carve_node("carve0", "lift0", axis="z", face_side="east",
                        depth_ratio=cd, outward_sign=1.0, width_ratio=0.42+v*0.04),
        split_wing_node("result", "carve0", access_side="east", axis="y",
                        layout="parallel", gap_ratio=0.12+v*0.02,
                        height_ratio=0.88+v*0.04, bridge=True,
                        connector_width_ratio=0.26+v*0.03),
    ]
    return mkprog(pid, v, "half_lift_carve_wing", "cube", "block",
                  ["lift","carve","short_axis","half_fraction","split_wing"],
                  "Lifted block east-carved then wing-split; east bridge spans the civic gap.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 43: 1/2 vertical twist → tower + twist → notch(east)
def b43(pid, v):
    w,d,h = _tower_seed()
    angle = 25 + v*10
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        twist_node("twist0", "m0", axis="z", angle=angle, subdivisions=4),
        notch_node("result", "twist0", side="east", corner="ne",
                   ratio=0.27+v*0.04, width_ratio=0.36, height_ratio=0.58),
    ]
    return mkprog(pid, v, "half_twisted_tower_notch", "cube", "tower",
                  ["twist","vertical","half_fraction","notch"],
                  "Half tower twisted; east notch cuts into the rotated face for entry.",
                  nodes, "result", storeys=5, target_gfa=1200)

# PATH 44: 1/2 vertical pinch → slab + pinch → carve_void(east)
def b44(pid, v):
    w,d,h = _slab_seed()
    wr = 0.48 + v*0.04
    ws = 0.68 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        pinch_node("pinch0", "m0", axis="z", waist_ratio=wr, waist_scale=ws,
                   profile_power=2.0+v*0.3, subdivisions=4),
        carve_void_node("result", "pinch0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_pinched_carve", "cube", "slab",
                  ["pinch","vertical","half_fraction","carve_void"],
                  "Half slab pinched at waist to form hourglass section; east carve opens civic face.",
                  nodes, "result", storeys=4, target_gfa=900)

# PATH 45: 1/2 vertical branch+branch → bar + book_branch×2 → courtyard(east)
def b45(pid, v):
    w,d,h = _bar_seed()
    angle1 = 45 + v*12
    angle2 = -40 - v*10
    tr1 = 0.55 + v*0.04
    tr2 = 0.58 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        book_branch_node("br0", "m0", angle_degrees=angle1, trunk_ratio=tr1,
                         arm_ratio=0.36+v*0.04, vertical_anchor="input_base"),
        book_branch_node("br1", "br0", angle_degrees=angle2, trunk_ratio=tr2,
                         arm_ratio=0.32+v*0.04, vertical_anchor="input_base"),
        courtyard_node("result", "br1", margin=0.20+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_double_branch_court", "cube", "bar",
                  ["branch","vertical","half_fraction","courtyard"],
                  "Double branching in half-fraction bar; east courtyard in the forking zone.",
                  nodes, "result", storeys=4, target_gfa=1100)

# PATH 46: 1/2 vertical notch+twist → block + book_notch + twist → carve_void(east)
def b46(pid, v):
    w,d,h = _block_seed()
    ratio = 0.24 + v*0.05
    angle = 20 + v*8
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="sw",
                        outward_sign=1.0, ratio=ratio),
        twist_node("twist0", "notch0", axis="z", angle=angle, subdivisions=4),
        carve_void_node("result", "twist0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "half_notch_twist_carve", "cube", "block",
                  ["notch","twist","vertical","half_fraction","carve_void"],
                  "Notched half block twisted; east carve void opens through the rotated face.",
                  nodes, "result", storeys=4, target_gfa=950)

# PATH 47: 1/2 vertical expand+nest → slab + boundary_expand + nested_related → lift(east)
def b47(pid, v):
    w,d,h = _slab_seed()
    amount = 0.22 + v*0.05
    dr = 0.30 + v*0.04
    us = 0.68 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.75, 0.75, 1.0)),
        boundary_expand_node("exp0", "m0", axis="z", amount=amount,
                             shoulder_fraction=0.48+v*0.04),
        nested_related_node("nest0", "exp0", axis="y", distance_ratio=dr, unit_scale=us),
        lift_node("result", "nest0", access_side="east",
                  rise_ratio=0.24+v*0.04, support_ratio=0.32+v*0.03),
    ]
    return mkprog(pid, v, "half_expand_nest_lift", "cube", "slab",
                  ["expand","nest","vertical","half_fraction","lift"],
                  "Expanded and nested slab volumes; east lift provides piloti-style ground access.",
                  nodes, "result", storeys=3, target_gfa=870)

# PATH 48: 1/4 long_axis offset → slab + offset_related → courtyard(east)
def b48(pid, v):
    w,d,h = _slab_seed()
    dr = 0.48 + v*0.05
    us = 0.72 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        offset_related_node("off0", "m0", axis="x", distance_ratio=dr,
                             outward_sign=1.0, unit_scale=us),
        courtyard_node("result", "off0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_offset_court", "cube", "slab",
                  ["offset","long_axis","quarter_fraction","courtyard"],
                  "Quarter-fraction slab offset pair; east courtyard in the gap acts as civic lobby.",
                  nodes, "result", storeys=4, target_gfa=950)

# PATH 49: 1/4 long_axis compress → block + clip_fraction → notch(east)
def b49(pid, v):
    w,d,h = _block_seed()
    frac = 0.70 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        clip_fraction_node("clip0", "m0", axis="z", fraction=frac, anchor="high"),
        notch_node("result", "clip0", side="east", corner="se",
                   ratio=0.26+v*0.04, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "quarter_compress_notch", "cube", "block",
                  ["compress","long_axis","quarter_fraction","notch"],
                  "Quarter-fraction block clipped; SE east notch as compact entry address.",
                  nodes, "result", storeys=3, target_gfa=780)

# PATH 50: 1/4 long_axis split+split → bar + book_split×2 → carve_void(east)
def b50(pid, v):
    w,d,h = _bar_seed()
    gap1 = 0.09 + v*0.03
    gap2 = 0.10 + v*0.03
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        book_split_node("sp0", "m0", axis="y", angle_degrees=0.0, gap_ratio=gap1,
                        outward_sign=1.0, branch_sign=1.0, split_generation=1.0,
                        terminal_ratio=0.48+v*0.04, access_side_sv="east"),
        book_split_node("sp1", "sp0", axis="x", angle_degrees=6.0+v*4, gap_ratio=gap2,
                        outward_sign=-1.0, branch_sign=-1.0, split_generation=2.0,
                        terminal_ratio=0.5, access_side_sv="east"),
        carve_void_node("result", "sp1", margin=0.20+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_double_split_carve", "cube", "bar",
                  ["split","long_axis","quarter_fraction","carve_void"],
                  "Quarter-bar double-split; east carve void addresses the fractured form.",
                  nodes, "result", storeys=4, target_gfa=940)

# PATH 51: 1/4 long_axis taper+bend → tower + taper + bend → courtyard(east)
def b51(pid, v):
    w,d,h = _tower_seed()
    es = [0.65+v*0.05, 0.65+v*0.05]
    angle = 18 + v*8
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        taper_node("tap0", "m0", axis="z", start_scale=[1.0,1.0], end_scale=es,
                   lower_floor_fraction=0.0, subdivisions=3),
        bend_node("bend0", "tap0", axis="y", angle=angle, subdivisions=4),
        courtyard_node("result", "bend0", margin=0.22+v*0.03, open_side="