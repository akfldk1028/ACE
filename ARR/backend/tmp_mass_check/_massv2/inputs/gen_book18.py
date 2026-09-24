import json

def box_node(id_, w, d, h):
    return {
        "id": id_,
        "kind": "primitive",
        "operator": "box",
        "inputs": [],
        "parameters": [
            {"name": "width", "value_type": "number", "numeric_value": w},
            {"name": "depth", "value_type": "number", "numeric_value": d},
            {"name": "height", "value_type": "number", "numeric_value": h},
            {"name": "center", "value_type": "boolean", "boolean_value": True}
        ],
        "semantic_role": "dominant_mass"
    }

def identity_matrix():
    return [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

def scale_matrix(s):
    return [[s,0,0,0],[0,s,0,0],[0,0,s,0],[0,0,0,1]]

def matrix_node(id_, inp, mat):
    return {
        "id": id_,
        "kind": "transform",
        "operator": "matrix4",
        "inputs": [inp],
        "parameters": [{"name": "matrix4", "value_type": "matrix4", "matrix4_value": mat}],
        "semantic_role": "dominant_mass"
    }

def courtyard_node(id_, inp, margin, open_side, role="public_threshold"):
    return {
        "id": id_,
        "kind": "composition",
        "operator": "courtyard",
        "inputs": [inp],
        "parameters": [
            {"name": "margin_ratio", "value_type": "number", "numeric_value": margin},
            {"name": "open_side", "value_type": "string", "string_value": open_side}
        ],
        "semantic_role": role
    }

def carve_void_node(id_, inp, margin, open_side):
    return {
        "id": id_,
        "kind": "composition",
        "operator": "carve_void",
        "inputs": [inp],
        "parameters": [
            {"name": "margin_ratio", "value_type": "number", "numeric_value": margin},
            {"name": "open_side", "value_type": "string", "string_value": open_side}
        ],
        "semantic_role": "public_threshold"
    }

def notch_node(id_, inp, side, ratio, width_ratio, height_ratio):
    return {
        "id": id_,
        "kind": "composition",
        "operator": "notch",
        "inputs": [inp],
        "parameters": [
            {"name": "side", "value_type": "string", "string_value": side},
            {"name": "ratio", "value_type": "number", "numeric_value": ratio},
            {"name": "width_ratio", "value_type": "number", "numeric_value": width_ratio},
            {"name": "height_ratio", "value_type": "number", "numeric_value": height_ratio}
        ],
        "semantic_role": "public_threshold"
    }

def lift_node(id_, inp, rise, support, side):
    return {
        "id": id_,
        "kind": "composition",
        "operator": "lift",
        "inputs": [inp],
        "parameters": [
            {"name": "rise_ratio", "value_type": "number", "numeric_value": rise},
            {"name": "support_ratio", "value_type": "number", "numeric_value": support},
            {"name": "access_side", "value_type": "string", "string_value": side}
        ],
        "semantic_role": "public_threshold"
    }

def taper_node(id_, inp, axis, end_scale, subdivisions=4):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "taper",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "end_scale", "value_type": "vector", "vector_value": end_scale},
            {"name": "subdivisions", "value_type": "number", "numeric_value": subdivisions}
        ],
        "semantic_role": "dominant_mass"
    }

def twist_node(id_, inp, axis, angle, subs=4):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "twist",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "angle_degrees", "value_type": "number", "numeric_value": angle},
            {"name": "subdivisions", "value_type": "number", "numeric_value": subs}
        ],
        "semantic_role": "dominant_mass"
    }

def shear_node(id_, inp, amount, axis, direction):
    return {
        "id": id_,
        "kind": "transform",
        "operator": "shear",
        "inputs": [inp],
        "parameters": [
            {"name": "amount", "value_type": "number", "numeric_value": amount},
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "direction", "value_type": "string", "string_value": direction}
        ],
        "semantic_role": "dominant_mass"
    }

def pinch_node(id_, inp, axis, waist_ratio, waist_scale, subs=4):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "pinch",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "waist_ratio", "value_type": "number", "numeric_value": waist_ratio},
            {"name": "waist_scale", "value_type": "number", "numeric_value": waist_scale},
            {"name": "subdivisions", "value_type": "number", "numeric_value": subs}
        ],
        "semantic_role": "dominant_mass"
    }

def bend_node(id_, inp, axis, angle, subs=4):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "bend",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "angle_degrees", "value_type": "number", "numeric_value": angle},
            {"name": "subdivisions", "value_type": "number", "numeric_value": subs}
        ],
        "semantic_role": "dominant_mass"
    }

def inflate_node(id_, inp, axis, factor, mid_scale, subs=4):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "inflate",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "factor", "value_type": "number", "numeric_value": factor},
            {"name": "middle_scale", "value_type": "number", "numeric_value": mid_scale},
            {"name": "subdivisions", "value_type": "number", "numeric_value": subs}
        ],
        "semantic_role": "dominant_mass"
    }

def stack_node(id_, inp, count, shift, spacing=0.02):
    return {
        "id": id_,
        "kind": "pattern",
        "operator": "stack",
        "inputs": [inp],
        "parameters": [
            {"name": "count", "value_type": "number", "numeric_value": count},
            {"name": "shift_per_level", "value_type": "vector", "vector_value": shift},
            {"name": "spacing", "value_type": "number", "numeric_value": spacing}
        ],
        "semantic_role": "program_space"
    }

def split_wing_node(id_, inp, axis, layout, height_ratio, gap_ratio, bridge, access_side):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "split_wing",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "layout", "value_type": "string", "string_value": layout},
            {"name": "height_ratio", "value_type": "number", "numeric_value": height_ratio},
            {"name": "gap_ratio", "value_type": "number", "numeric_value": gap_ratio},
            {"name": "bridge", "value_type": "boolean", "boolean_value": bridge},
            {"name": "access_side", "value_type": "string", "string_value": access_side}
        ],
        "semantic_role": "public_threshold"
    }

def book_notch_node(id_, inp, axis, corner, ratio):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "book_notch",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "corner", "value_type": "string", "string_value": corner},
            {"name": "ratio", "value_type": "number", "numeric_value": ratio},
            {"name": "outward_sign", "value_type": "number", "numeric_value": 1.0}
        ],
        "semantic_role": "dominant_mass"
    }

def book_carve_node(id_, inp, axis, face, width_ratio, depth_ratio, outward_sign=1.0):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "book_carve",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "face_side", "value_type": "string", "string_value": face},
            {"name": "width_ratio", "value_type": "number", "numeric_value": width_ratio},
            {"name": "depth_ratio", "value_type": "number", "numeric_value": depth_ratio},
            {"name": "outward_sign", "value_type": "number", "numeric_value": outward_sign}
        ],
        "semantic_role": "program_space"
    }

def book_grade_node(id_, inp, axis, face, width_ratio, depth_ratio, levels, outward_sign=1.0):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "book_grade",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "face_side", "value_type": "string", "string_value": face},
            {"name": "width_ratio", "value_type": "number", "numeric_value": width_ratio},
            {"name": "depth_ratio", "value_type": "number", "numeric_value": depth_ratio},
            {"name": "levels", "value_type": "number", "numeric_value": levels},
            {"name": "outward_sign", "value_type": "number", "numeric_value": outward_sign}
        ],
        "semantic_role": "dominant_mass"
    }

def offset_related_node(id_, inp, axis, distance_ratio, unit_scale, outward_sign=1.0):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "offset_related",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "distance_ratio", "value_type": "number", "numeric_value": distance_ratio},
            {"name": "unit_scale", "value_type": "number", "numeric_value": unit_scale},
            {"name": "outward_sign", "value_type": "number", "numeric_value": outward_sign}
        ],
        "semantic_role": "program_space"
    }

def merge_related_node(id_, inp, axis, gap_ratio, unit_scale):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "merge_related",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "gap_ratio", "value_type": "number", "numeric_value": gap_ratio},
            {"name": "unit_scale", "value_type": "number", "numeric_value": unit_scale}
        ],
        "semantic_role": "dominant_mass"
    }

def shift_related_node(id_, inp, axis, distance_ratio, split_ratio, outward_sign=1.0):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "shift_related",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "distance_ratio", "value_type": "number", "numeric_value": distance_ratio},
            {"name": "split_ratio", "value_type": "number", "numeric_value": split_ratio},
            {"name": "outward_sign", "value_type": "number", "numeric_value": outward_sign}
        ],
        "semantic_role": "dominant_mass"
    }

def puncture_node(id_, inp, axis, count, ratio, spacing_ratio):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "puncture",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "count", "value_type": "number", "numeric_value": count},
            {"name": "ratio", "value_type": "number", "numeric_value": ratio},
            {"name": "spacing_ratio", "value_type": "number", "numeric_value": spacing_ratio}
        ],
        "semantic_role": "program_space"
    }

def nested_related_node(id_, inp, axis, distance_ratio, unit_scale):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "nested_related",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "distance_ratio", "value_type": "number", "numeric_value": distance_ratio},
            {"name": "unit_scale", "value_type": "number", "numeric_value": unit_scale}
        ],
        "semantic_role": "program_space"
    }

def book_extract_node(id_, inp, axis, face, distance_ratio, guest_scale, outward_sign=1.0):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "book_extract",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "face_side", "value_type": "string", "string_value": face},
            {"name": "distance_ratio", "value_type": "number", "numeric_value": distance_ratio},
            {"name": "guest_scale", "value_type": "number", "numeric_value": guest_scale},
            {"name": "outward_sign", "value_type": "number", "numeric_value": outward_sign}
        ],
        "semantic_role": "program_space"
    }

def book_lodge_node(id_, inp, axis, distance_ratio, guest_scale, outward_sign=1.0):
    return {
        "id": id_,
        "kind": "modifier",
        "operator": "book_lodge",
        "inputs": [inp],
        "parameters": [
            {"name": "axis", "value_type": "string", "string_value": axis},
            {"name": "distance_ratio", "value_type": "number", "numeric_value": distance_ratio},
            {"name": "guest_scale", "value_type": "number", "numeric_value": guest_scale},
            {"name": "outward_sign", "value_type": "number", "numeric_value": outward_sign}
        ],
        "semantic_role": "program_space"
    }

def dim(storeys, storey_h, gfa):
    return {
        "schema_version": "arr.maas.dimensional_intent.v1",
        "storey_count": storeys,
        "storey_height_m": storey_h,
        "target_gfa_m2": gfa,
        "delivery_policy": "preserve_physical_dimensions",
        "programme_status": "unknown"
    }

SLAB = (2.2, 1.45, 0.28)
BAR = (2.8, 0.62, 0.48)
BLOCK = (1.0, 1.0, 1.0)
TOWER = (0.68, 0.68, 2.5)

programs = []

# ===== 1. bend long_axis 1/1 (path 9bab887f) =====
programs.append({
    "name": "bend_bar_east_court_01",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["bent_bar", "arc_plan", "east_court"],
    "book_composition_path_id": "book:path:9bab887f2e519077dcbe8e5977897df8a80deb6d1a280936cccca005d8555719",
    "rationale": "A bar volume bent along its long axis creates a concave face that gathers the public threshold toward the road.",
    "dimensional_intent": dim(4, 3.5, 1100.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"angle_degrees","value_type":"number","numeric_value":28},
            {"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},
        courtyard_node("result","bent",0.22,"east")
    ], "root_id": "result"
})

# ===== 2. fracture long_axis 1/1 (path 9042c82e) =====
programs.append({
    "name": "fracture_slab_north_02",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["fractured_slab", "diagonal_fissure", "east_notch"],
    "book_composition_path_id": "book:path:9042c82e97a383fc1f1e97948ac87e0bac17a95d0d8587255d48710c0ac64040",
    "rationale": "A slab receives a diagonal fracture from its north face revealing structural depth; east notch marks entry.",
    "dimensional_intent": dim(5, 3.3, 1300.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"frac","kind":"modifier","operator":"book_fracture","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.12},
            {"name":"face_side","value_type":"string","string_value":"north"},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"retained_back_ratio","value_type":"number","numeric_value":0.45}],"semantic_role":"dominant_mass"},
        notch_node("result","frac","east",0.22,0.35,0.6)
    ], "root_id": "result"
})

# ===== 3. embed+embed long_axis 1/1 (path 11a0d7a5) =====
programs.append({
    "name": "embed_embed_block_03",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["double_embed", "nested_void", "east_carve"],
    "book_composition_path_id": "book:path:11a0d7a5a51e85d9ec1cf2f3b3eaa086eb6841d1fec6a184077cc5db1851b185",
    "rationale": "Two concentric embedded voids create layered programme zones; east carve opens the public court.",
    "dimensional_intent": dim(4, 3.5, 1050.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"emb1","kind":"modifier","operator":"embed_void","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"guest_scale","value_type":"number","numeric_value":0.6},
            {"name":"embedded_ratio","value_type":"number","numeric_value":0.4},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"position","value_type":"string","string_value":"center"}],"semantic_role":"dominant_mass"},
        {"id":"emb2","kind":"modifier","operator":"embed_void","inputs":["emb1"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"guest_scale","value_type":"number","numeric_value":0.35},
            {"name":"embedded_ratio","value_type":"number","numeric_value":0.6},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"position","value_type":"string","string_value":"center"}],"semantic_role":"program_space"},
        carve_void_node("result","emb2",0.28,"east")
    ], "root_id": "result"
})

# ===== 4. branch+expand long_axis 1/1 (path dd28b0c5) =====
programs.append({
    "name": "branch_expand_block_04",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["branching_arms", "expanded_crown", "east_lift"],
    "book_composition_path_id": "book:path:dd28b0c53f08a2d1812dc32d7b562ee9b7bc4a1ca98b90a13152bbf534dd27f2",
    "rationale": "A block branches into arms which expand outward; east lift opens the ground plane to pedestrians.",
    "dimensional_intent": dim(4, 3.5, 1200.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"br","kind":"modifier","operator":"book_branch","inputs":["m0"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.55},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.4},
            {"name":"angle_degrees","value_type":"number","numeric_value":60},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"dominant_mass"},
        {"id":"exp","kind":"modifier","operator":"boundary_expand","inputs":["br"],"parameters":[
            {"name":"amount","value_type":"number","numeric_value":0.18},
            {"name":"axis","value_type":"string","string_value":"z"}],"semantic_role":"program_space"},
        lift_node("result","exp",0.22,0.18,"east")
    ], "root_id": "result"
})

# ===== 5. carve+offset long_axis 1/1 (path c7fcd0c1) =====
programs.append({
    "name": "carve_offset_slab_05",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["poli_carve", "offset_service", "east_open"],
    "book_composition_path_id": "book:path:c7fcd0c126b7b32471e69e703e7e9022ab3963899ef974c879ec44b4162b197a",
    "rationale": "North carve separates programme zone; east court provides the public threshold. Carve reveals plan depth.",
    "dimensional_intent": dim(5, 3.3, 1380.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", identity_matrix()),
        book_carve_node("carv","m0","y","north",0.45,0.3,-1.0),
        courtyard_node("result","carv",0.18,"east")
    ], "root_id": "result"
})

# ===== 6. branch short_axis 1/1 (path b9527700) =====
programs.append({
    "name": "branch_short_slab_06",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["branching_short", "wing_pair", "east_court"],
    "book_composition_path_id": "book:path:b95277004fb2b89b21445182aab353c444a4ea7a1e7044f8c2e7e07599226909",
    "rationale": "Slab branches laterally into wings flanking an east-facing court. Branch geometry defines three-sided enclosure.",
    "dimensional_intent": dim(4, 3.5, 1150.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"br","kind":"modifier","operator":"book_branch","inputs":["m0"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.5},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.45},
            {"name":"angle_degrees","value_type":"number","numeric_value":90},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"dominant_mass"},
        courtyard_node("result","br",0.25,"east")
    ], "root_id": "result"
})

# ===== 7. rotate short_axis 1/1 (path 6bb95e7e) =====
programs.append({
    "name": "rotate_short_bar_07",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["hinged_rotation", "angled_plan", "east_notch"],
    "book_composition_path_id": "book:path:6bb95e7e0461e1606d4430a1e8a7c4ad2b3dc96d74ff48bced73da05b9df6cf5",
    "rationale": "A bar arm rotates about a hinge on the short axis, producing a wedge-shaped east forecourt naturally.",
    "dimensional_intent": dim(4, 3.5, 1000.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"rot","kind":"modifier","operator":"book_rotate","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"angle_degrees","value_type":"number","numeric_value":22},
            {"name":"related_ratio","value_type":"number","numeric_value":0.45},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        notch_node("result","rot","east",0.28,0.4,0.55)
    ], "root_id": "result"
})

# ===== 8. inscribe short_axis 1/1 (path 2f971be2) =====
programs.append({
    "name": "inscribe_elliptical_block_08",
    "base_form_id": "elliptical", "base_seed": "block",
    "intent_tags": ["inscribed_court", "elliptical_shell", "east_open"],
    "book_composition_path_id": "book:path:2f971be29f0d428a9879b1c00948ac738f8921db4163797414074d894ac8efb9",
    "rationale": "An elliptical block with inscribed inner void creates a ring shell; east carve marks the public entry.",
    "dimensional_intent": dim(4, 3.5, 950.0),
    "nodes": [
        box_node("b0", *BLOCK),
        {"id":"ell","kind":"modifier","operator":"ellipsoidize","inputs":["b0"],"parameters":[
            {"name":"segments","value_type":"number","numeric_value":24}],"semantic_role":"dominant_mass"},
        matrix_node("m0", "ell", identity_matrix()),
        courtyard_node("insc","m0",0.3,"closed","program_space"),
        carve_void_node("result","insc",0.2,"east")
    ], "root_id": "result"
})

# ===== 9. intersect+split short_axis 1/1 (path e510ad25) =====
programs.append({
    "name": "intersect_split_slab_09",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["cross_bars", "split_zones", "east_access"],
    "book_composition_path_id": "book:path:e510ad256385b556152790586ff8d15493cf9c1d6cffbd352f8e0d326c4ca71a",
    "rationale": "Two crossing slabs retain their intersection; split divides into east/west programme zones sharing the crossing hall.",
    "dimensional_intent": dim(4, 3.5, 1080.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"isect","kind":"modifier","operator":"intersect_related","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"y"},
            {"name":"angle_degrees","value_type":"number","numeric_value":30},
            {"name":"bar_ratio","value_type":"number","numeric_value":0.35},
            {"name":"unit_scale","value_type":"number","numeric_value":0.8}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_split","inputs":["isect"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.08},
            {"name":"angle_degrees","value_type":"number","numeric_value":0},
            {"name":"branch_sign","value_type":"number","numeric_value":1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.45},
            {"name":"split_generation","value_type":"number","numeric_value":1},
            {"name":"access_side","value_type":"string","string_value":"east"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 10. bend+stack short_axis 1/1 (path 53c55b4d) =====
programs.append({
    "name": "bend_stack_slab_10",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["bent_stacked", "curved_tiers", "east_court"],
    "book_composition_path_id": "book:path:53c55b4da48903af110459fa120baeaec3b186edf22d6890fa718d0ad6b1f5b5",
    "rationale": "Slab bent then stacked produces shifted curved tiers creating a spiral silhouette readable from east.",
    "dimensional_intent": dim(4, 3.5, 1200.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", identity_matrix()),
        bend_node("bent","m0","y",20),
        stack_node("stk","bent",3,[0.05,0.0,0.0],0.02),
        courtyard_node("result","stk",0.2,"east")
    ], "root_id": "result"
})

# ===== 11. lift+extrude short_axis 1/1 (path f285f713) =====
programs.append({
    "name": "lift_extrude_slab_11",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["lifted_plate", "extruded_core", "east_through"],
    "book_composition_path_id": "book:path:f285f713076b19ee7cc1b58f2d44f85aeec8a11bfe30fc0b77e876a1543a612b",
    "rationale": "Slab lifted above grade with a core descending through clearance; building straddles the ground plane.",
    "dimensional_intent": dim(4, 3.5, 1100.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"lft","kind":"modifier","operator":"book_lift","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"distance_ratio","value_type":"number","numeric_value":0.25},
            {"name":"guest_scale","value_type":"number","numeric_value":0.6},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        lift_node("result","lft",0.2,0.15,"east")
    ], "root_id": "result"
})

# ===== 12. interlock vertical 1/1 (path 05470e61) =====
programs.append({
    "name": "interlock_vertical_block_12",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["L_interlock", "figure8_section", "east_notch"],
    "book_composition_path_id": "book:path:05470e618703ead632e6029bac7312306f05a6f404cb1a84f60043e0fb2b6b5f",
    "rationale": "Two L-volumes engage through a shared zone; east face reads as reciprocal notches marking civic entry.",
    "dimensional_intent": dim(4, 3.5, 1050.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"ilk","kind":"modifier","operator":"interlock_related","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"angle_degrees","value_type":"number","numeric_value":0},
            {"name":"bar_ratio","value_type":"number","numeric_value":0.4},
            {"name":"distance_ratio","value_type":"number","numeric_value":0.3},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        notch_node("result","ilk","east",0.25,0.38,0.5)
    ], "root_id": "result"
})

# ===== 13. shear vertical 1/1 (path ff644fb6) =====
programs.append({
    "name": "shear_vertical_tower_13",
    "base_form_id": "cube", "base_seed": "tower",
    "intent_tags": ["sheared_tower", "oblique_top", "east_notch"],
    "book_composition_path_id": "book:path:ff644fb6db1684200f7c558764b8298c45bab946fac40c3df9cc090edf479977",
    "rationale": "Tower sheared vertically creates clean diagonal silhouette; east notch opens the base to the road.",
    "dimensional_intent": dim(5, 3.3, 900.0),
    "nodes": [
        box_node("b0", *TOWER),
        matrix_node("m0", "b0", identity_matrix()),
        shear_node("sh","m0",0.45,"z","x"),
        notch_node("result","sh","east",0.2,0.5,0.4)
    ], "root_id": "result"
})

# ===== 14. expand+expand vertical 1/1 (path 61ddaacb) =====
programs.append({
    "name": "expand_expand_vertical_14",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["double_flare", "stepped_expansion", "east_carve"],
    "book_composition_path_id": "book:path:61ddaacb14d1ebd0e0c24518a19a9b01f9a48f50fbfd66fd280b92abe59722b7",
    "rationale": "Two successive expansions produce a double-flared section; east carve marks the public entrance.",
    "dimensional_intent": dim(4, 3.5, 1100.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"exp1","kind":"modifier","operator":"boundary_expand","inputs":["m0"],"parameters":[
            {"name":"amount","value_type":"number","numeric_value":0.22},
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"shoulder_fraction","value_type":"number","numeric_value":0.5}],"semantic_role":"dominant_mass"},
        {"id":"exp2","kind":"modifier","operator":"boundary_expand","inputs":["exp1"],"parameters":[
            {"name":"amount","value_type":"number","numeric_value":0.15},
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"shoulder_fraction","value_type":"number","numeric_value":0.75}],"semantic_role":"program_space"},
        carve_void_node("result","exp2",0.22,"east")
    ], "root_id": "result"
})

# ===== 15. expand+reflect vertical 1/1 (path 2e2f65a3) =====
programs.append({
    "name": "expand_reflect_vertical_15",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["reflected_pair", "bilateral_form", "east_notch"],
    "book_composition_path_id": "book:path:2e2f65a3f44c510ecfa66c729db4c53684b3cc4033f5844bc980f4fa4bf1ad70",
    "rationale": "A body expanded on one side and reflected yields bilateral volumes sharing a central spine visible from east.",
    "dimensional_intent": dim(5, 3.3, 1200.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"exp","kind":"modifier","operator":"boundary_expand","inputs":["m0"],"parameters":[
            {"name":"amount","value_type":"number","numeric_value":0.3},
            {"name":"axis","value_type":"string","string_value":"y"}],"semantic_role":"dominant_mass"},
        {"id":"mir","kind":"transform","operator":"mirror_array","inputs":["exp"],"parameters":[
            {"name":"normal","value_type":"vector","vector_value":[1.0,0.0,0.0]},
            {"name":"pivot","value_type":"vector","vector_value":[0.0,0.0,0.0]}],"semantic_role":"program_space"},
        notch_node("result","mir","east",0.3,0.45,0.5)
    ], "root_id": "result"
})

# ===== 16. overlap+expand vertical 1/1 (path aadaf434) =====
programs.append({
    "name": "overlap_expand_vertical_16",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["vertical_overlap", "expanded_zone", "east_lift"],
    "book_composition_path_id": "book:path:aadaf4340a4980ec0c691cf6c70bf78936b4b4b1471a6340d384abcae9ee0a2c",
    "rationale": "Volumes overlap vertically and expand at the overlap zone; mid-height public space from east access.",
    "dimensional_intent": dim(4, 3.5, 1100.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", identity_matrix()),
        {"id":"ovl","kind":"modifier","operator":"overlap_related","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"slab_ratio","value_type":"number","numeric_value":0.5},
            {"name":"shift_ratio","value_type":"number","numeric_value":0.35},
            {"name":"vertical_overlap","value_type":"number","numeric_value":0.3},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        {"id":"exp","kind":"modifier","operator":"boundary_expand","inputs":["ovl"],"parameters":[
            {"name":"amount","value_type":"number","numeric_value":0.18},
            {"name":"axis","value_type":"string","string_value":"z"}],"semantic_role":"program_space"},
        lift_node("result","exp",0.18,0.16,"east")
    ], "root_id": "result"
})

# ===== 17. bend long_axis 3/8 (path 2e241115) =====
programs.append({
    "name": "bend_38_bar_17",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["bent_3_8", "arc_bar", "east_court"],
    "book_composition_path_id": "book:path:2e24111503e808e954bf437374af114ede99fddb568beab59253edb011273835",
    "rationale": "3/8 bar arc curves convex east face toward road; court opens within the concave west face.",
    "dimensional_intent": dim(3, 3.5, 900.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"angle_degrees","value_type":"number","numeric_value":35},
            {"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},
        courtyard_node("result","bent",0.24,"east")
    ], "root_id": "result"
})

# ===== 18. fracture long_axis 3/8 (path 84d0345c) =====
programs.append({
    "name": "fracture_38_bar_18",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["fractured_3_8", "angular_fissure", "east_notch"],
    "book_composition_path_id": "book:path:84d0345cadb3c43a13aa423bc1fddfb175b338b095c86bc9ec4b1eab2952afd0",
    "rationale": "3/8 bar fractured on its south face creates angular structural event; east notch marks entry.",
    "dimensional_intent": dim(3, 3.5, 850.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"frac","kind":"modifier","operator":"book_fracture","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.1},
            {"name":"face_side","value_type":"string","string_value":"south"},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"retained_back_ratio","value_type":"number","numeric_value":0.5}],"semantic_role":"dominant_mass"},
        notch_node("result","frac","east",0.3,0.4,0.6)
    ], "root_id": "result"
})

# ===== 19. split+split long_axis 3/8 (path b96fa24e) =====
programs.append({
    "name": "split_split_38_19",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["double_split", "z_plan", "east_access"],
    "book_composition_path_id": "book:path:b96fa24e6b07a0419331b82a471addcf0f980f71d6fee1bffd80a5e1ed1ea126",
    "rationale": "3/8 bar double-split creates Z-plan with three articulated connected bodies.",
    "dimensional_intent": dim(4, 3.5, 1000.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"sp1","kind":"modifier","operator":"book_split","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.06},
            {"name":"angle_degrees","value_type":"number","numeric_value":20},
            {"name":"branch_sign","value_type":"number","numeric_value":1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.4},
            {"name":"split_generation","value_type":"number","numeric_value":1},
            {"name":"access_side","value_type":"string","string_value":"closed"}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_split","inputs":["sp1"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.06},
            {"name":"angle_degrees","value_type":"number","numeric_value":-20},
            {"name":"branch_sign","value_type":"number","numeric_value":-1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.4},
            {"name":"split_generation","value_type":"number","numeric_value":2},
            {"name":"access_side","value_type":"string","string_value":"east"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 20. bend+branch long_axis 3/8 (path b5ca07c6) =====
programs.append({
    "name": "bend_branch_38_20",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["bent_then_branched", "arc_arm", "east_notch"],
    "book_composition_path_id": "book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e",
    "rationale": "3/8 bar bent then branched at apex; secondary arm points east creating asymmetric urban address.",
    "dimensional_intent": dim(4, 3.5, 980.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"angle_degrees","value_type":"number","numeric_value":25},
            {"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_branch","inputs":["bent"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.6},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.38},
            {"name":"angle_degrees","value_type":"number","numeric_value":70},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 21. split+join long_axis 3/8 (path 2fcf5f31) =====
programs.append({
    "name": "split_join_38_21",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["split_rejoined", "hinged_connector", "east_notch"],
    "book_composition_path_id": "book:path:2fcf5f31e6d7ec9acbe02f9c3a6bb20e72df122cf29d989dd630f4d7fc022791",
    "rationale": "3/8 bar split then rejoined via bridge connector; hinged-open plan with visible seam at mid-length.",
    "dimensional_intent": dim(4, 3.5, 1020.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"sp","kind":"modifier","operator":"book_split","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.12},
            {"name":"angle_degrees","value_type":"number","numeric_value":30},
            {"name":"branch_sign","value_type":"number","numeric_value":1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.45},
            {"name":"split_generation","value_type":"number","numeric_value":1},
            {"name":"access_side","value_type":"string","string_value":"closed"}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"composition","operator":"join_related","inputs":["sp"],"parameters":[
            {"name":"bridge_ratio","value_type":"number","numeric_value":0.3}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 22. inflate short_axis 3/8 (path 423e633a) =====
programs.append({
    "name": "inflate_38_short_22",
    "base_form_id": "elliptical", "base_seed": "slab",
    "intent_tags": ["inflated_crown", "barrel_profile", "east_notch"],
    "book_composition_path_id": "book:path:423e633a08a43369b6ccda29d5604fc061c6e20e52e460c9867ddd1e5b13c2c0",
    "rationale": "3/8 slab inflated at crown produces barrel section; east notch incises the swollen east face.",
    "dimensional_intent": dim(4, 3.5, 900.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        inflate_node("inf","m0","z",1.35,1.4),
        notch_node("result","inf","east",0.28,0.4,0.55)
    ], "root_id": "result"
})

# ===== 23. overlap short_axis 3/8 (path 6acac573) =====
programs.append({
    "name": "overlap_38_short_23",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["slipped_slabs", "cascade_overlap", "east_court"],
    "book_composition_path_id": "book:path:6acac573694cb27de1572fd0a9de5fb76aed871fea929c88573a072c95a8bbbb",
    "rationale": "Two 3/8 slabs slipped in plan create cascading overlap; east court opens the shared zone to the road.",
    "dimensional_intent": dim(4, 3.5, 1050.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"ovl","kind":"modifier","operator":"overlap_related","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"slab_ratio","value_type":"number","numeric_value":0.55},
            {"name":"shift_ratio","value_type":"number","numeric_value":0.4},
            {"name":"vertical_overlap","value_type":"number","numeric_value":0.35},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        courtyard_node("result","ovl",0.22,"east")
    ], "root_id": "result"
})

# ===== 24. inscribe short_axis 3/8 (path 1dbb96b3) =====
programs.append({
    "name": "inscribe_38_short_24",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["inscribed_ring", "inner_light_well", "east_open"],
    "book_composition_path_id": "book:path:1dbb96b395ddd04b17719976be7a62b1bdb6256f080c74a7b0de12c908a7915c",
    "rationale": "3/8 slab with inscribed court creates ring plan; deep inner void visible through east opening.",
    "dimensional_intent": dim(4, 3.5, 1000.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        courtyard_node("insc","m0",0.28,"closed","program_space"),
        carve_void_node("result","insc",0.18,"east")
    ], "root_id": "result"
})

# ===== 25. intersect+split short_axis 3/8 (path f91a61a3) =====
programs.append({
    "name": "intersect_split_38_25",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["cross_split_3_8", "crossing_hall", "east_access"],
    "book_composition_path_id": "book:path:f91a61a346c29c85aa4907c5e5c53d10e00a7530d28316c598fcc29d75f7fb55",
    "rationale": "3/8 slab crossed and split yields two zones sharing crossing hall; asymmetric east/west programme.",
    "dimensional_intent": dim(4, 3.5, 980.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"isct","kind":"modifier","operator":"intersect_related","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"y"},
            {"name":"angle_degrees","value_type":"number","numeric_value":45},
            {"name":"bar_ratio","value_type":"number","numeric_value":0.3},
            {"name":"unit_scale","value_type":"number","numeric_value":0.75}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_split","inputs":["isct"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"y"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.08},
            {"name":"angle_degrees","value_type":"number","numeric_value":0},
            {"name":"branch_sign","value_type":"number","numeric_value":1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.4},
            {"name":"split_generation","value_type":"number","numeric_value":1},
            {"name":"access_side","value_type":"string","string_value":"east"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 26. bend+stack short_axis 3/8 (path 13fbf6da) =====
programs.append({
    "name": "bend_stack_38_26",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["bent_stacked_3_8", "shifted_arc_tiers", "east_court"],
    "book_composition_path_id": "book:path:13fbf6da4b2addf28d4678956f747d8f112740ed2ca07de19e7a4884b2d43956",
    "rationale": "3/8 slab bent and stacked; each shifted arc tier creates a spiraling section tower.",
    "dimensional_intent": dim(4, 3.5, 1050.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        bend_node("bent","m0","y",22),
        stack_node("stk","bent",3,[0.04,0.02,0.0],0.01),
        courtyard_node("result","stk",0.2,"east")
    ], "root_id": "result"
})

# ===== 27. lift+extrude short_axis 3/8 (path 4542c2a1) =====
programs.append({
    "name": "lift_extrude_38_27",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["hovering_plate", "core_through", "east_access"],
    "book_composition_path_id": "book:path:4542c2a1884b1b256fbdea6e3ffd434dac31db9212deb3a328bb168fcfc1a6e4",
    "rationale": "3/8 slab lifted exposes public ground; extruded core descends through clearance for a hovering plate reading.",
    "dimensional_intent": dim(3, 3.5, 800.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"lft","kind":"modifier","operator":"book_lift","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"distance_ratio","value_type":"number","numeric_value":0.28},
            {"name":"guest_scale","value_type":"number","numeric_value":0.55},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        lift_node("result","lft",0.22,0.15,"east")
    ], "root_id": "result"
})

# ===== 28. interlock vertical 3/8 (path e1e90099) =====
programs.append({
    "name": "interlock_38_vertical_28",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["interlock_3_8", "double_L", "east_notch"],
    "book_composition_path_id": "book:path:e1e90099b5d07535d9361727c7d4b028f702499491b0588fdb2c926912013fb5",
    "rationale": "3/8 base: two L-volumes interlock; double-notch east face reads as interlocking civic engagement zone.",
    "dimensional_intent": dim(4, 3.5, 950.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"ilk","kind":"modifier","operator":"interlock_related","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"y"},
            {"name":"angle_degrees","value_type":"number","numeric_value":0},
            {"name":"bar_ratio","value_type":"number","numeric_value":0.38},
            {"name":"distance_ratio","value_type":"number","numeric_value":0.32},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        notch_node("result","ilk","east",0.22,0.35,0.5)
    ], "root_id": "result"
})

# ===== 29. shear vertical 3/8 (path f7755521) =====
programs.append({
    "name": "shear_38_vertical_29",
    "base_form_id": "cube", "base_seed": "tower",
    "intent_tags": ["shear_3_8", "oblique_silhouette", "east_notch"],
    "book_composition_path_id": "book:path:f7755521cc02b4d565cddffa435faa30d79095ee7d62ce0588cbc8fc33fa2b6f",
    "rationale": "3/8 tower sheared vertically; diagonal top plane contrasts with strong base expression.",
    "dimensional_intent": dim(5, 3.3, 850.0),
    "nodes": [
        box_node("b0", *TOWER),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        shear_node("sh","m0",0.5,"z","y"),
        notch_node("result","sh","east",0.22,0.45,0.4)
    ], "root_id": "result"
})

# ===== 30. branch+branch vertical 3/8 (path def59b66) =====
programs.append({
    "name": "branch_branch_38_30",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["double_branch_3_8", "forked_plan", "east_court"],
    "book_composition_path_id": "book:path:def59b665a24ebd51c08a3812668edc1a6131552a8055b2d7cb88de8de90f4f5",
    "rationale": "3/8 bar double-branched creates forked pinwheel plan presenting faces to all cardinal directions.",
    "dimensional_intent": dim(4, 3.5, 1050.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"br1","kind":"modifier","operator":"book_branch","inputs":["m0"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.55},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.42},
            {"name":"angle_degrees","value_type":"number","numeric_value":70},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_branch","inputs":["br1"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.5},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.38},
            {"name":"angle_degrees","value_type":"number","numeric_value":-60},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 31. notch+twist vertical 3/8 (path 3ab1e90c) =====
programs.append({
    "name": "notch_twist_38_31",
    "base_form_id": "cube", "base_seed": "tower",
    "intent_tags": ["notched_tower", "torsion_body", "east_notch"],
    "book_composition_path_id": "book:path:3ab1e90c58b2293f63e75df8acabb9308b747cd6304c4511b2a47ed9ce8821c3",
    "rationale": "3/8 tower notched at base corner then twisted; sculptural torsion rises above notched entry.",
    "dimensional_intent": dim(5, 3.3, 900.0),
    "nodes": [
        box_node("b0", *TOWER),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        book_notch_node("ntch","m0","z","ne",0.28),
        twist_node("result","ntch","z",35)
    ], "root_id": "result"
})

# ===== 32. expand+nest vertical 3/8 (path cfeca723) =====
programs.append({
    "name": "expand_nest_38_32",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["expand_nest_3_8", "double_shell", "east_threshold"],
    "book_composition_path_id": "book:path:cfeca7238d109f8ccf184e9ab42319aadf2d36f2aca116ba295ae47cbb6ca11b",
    "rationale": "3/8 block expanded then nested concentrically creates double-shell plan with layered public/private zones.",
    "dimensional_intent": dim(4, 3.5, 980.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", scale_matrix(0.375)),
        {"id":"exp","kind":"modifier","operator":"boundary_expand","inputs":["m0"],"parameters":[
            {"name":"amount","value_type":"number","numeric_value":0.32},
            {"name":"axis","value_type":"string","string_value":"z"}],"semantic_role":"dominant_mass"},
        nested_related_node("nst","exp","x",0.25,0.55),
        carve_void_node("result","nst",0.2,"east")
    ], "root_id": "result"
})

# ===== 33. offset long_axis 1/2 (path 08e14d9e) =====
programs.append({
    "name": "offset_12_long_33",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["offset_pair", "parallel_bars", "east_court"],
    "book_composition_path_id": "book:path:08e14d9ef6f30e7f2700d6e5f895d4911944adbfd16a0477dbfee0afeebfbf70",
    "rationale": "1/2 bar offset on its long axis produces a parallel bar pair with a shared gap; east court connects them.",
    "dimensional_intent": dim(4, 3.5, 1100.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        offset_related_node("off","m0","y",0.4,0.85),
        courtyard_node("result","off",0.2,"east")
    ], "root_id": "result"
})

# ===== 34. compress long_axis 1/2 (path 1979434c) =====
programs.append({
    "name": "compress_12_long_34",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["compressed_slab", "thin_bar", "east_notch"],
    "book_composition_path_id": "book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb",
    "rationale": "1/2 slab compressed along its long axis creates a thin bar with taller section visible from east.",
    "dimensional_intent": dim(5, 3.3, 1050.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"comp","kind":"modifier","operator":"clip_fraction","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"y"},
            {"name":"fraction","value_type":"number","numeric_value":0.7},
            {"name":"anchor","value_type":"string","string_value":"low"}],"semantic_role":"dominant_mass"},
        notch_node("result","comp","east",0.25,0.4,0.55)
    ], "root_id": "result"
})

# ===== 35. split+split long_axis 1/2 (path 60778ae3) =====
programs.append({
    "name": "split_split_12_35",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["double_split_12", "z_plan_half", "east_access"],
    "book_composition_path_id": "book:path:60778ae3e99cf12bb7e8461f50ee3332b7a47ed4893d70cb2d8400fd22cc49cf",
    "rationale": "1/2 bar double-split creates an articulated Z-plan at half the full-parcel scale.",
    "dimensional_intent": dim(4, 3.5, 980.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"sp1","kind":"modifier","operator":"book_split","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.07},
            {"name":"angle_degrees","value_type":"number","numeric_value":25},
            {"name":"branch_sign","value_type":"number","numeric_value":1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.42},
            {"name":"split_generation","value_type":"number","numeric_value":1},
            {"name":"access_side","value_type":"string","string_value":"closed"}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_split","inputs":["sp1"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.07},
            {"name":"angle_degrees","value_type":"number","numeric_value":-25},
            {"name":"branch_sign","value_type":"number","numeric_value":-1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.42},
            {"name":"split_generation","value_type":"number","numeric_value":2},
            {"name":"access_side","value_type":"string","string_value":"east"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 36. bend+branch long_axis 1/2 (path 0b828fd1) =====
programs.append({
    "name": "bend_branch_12_36",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["bent_branched_12", "arc_arm_east", "east_notch"],
    "book_composition_path_id": "book:path:0b828fd1f09aeb9b5e3096a6cfe15c3cf1d709a475844690e9f3085fbdb9b8b1",
    "rationale": "1/2 bar bent then branched; the arm at mid-arc reaches east to define the civic address.",
    "dimensional_intent": dim(4, 3.5, 1000.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"angle_degrees","value_type":"number","numeric_value":30},
            {"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_branch","inputs":["bent"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.58},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.36},
            {"name":"angle_degrees","value_type":"number","numeric_value":65},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 37. split+join long_axis 1/2 (path d2cb499b) =====
programs.append({
    "name": "split_join_12_37",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["split_joined_12", "connector_seam", "east_notch"],
    "book_composition_path_id": "book:path:d2cb499b7d8b00c2ace3d4b6893bc583e2307d3d6cdb0ac96b319253fe0529c4",
    "rationale": "1/2 bar split and rejoined; hinged seam visible in elevation, connector reads as a threshold event.",
    "dimensional_intent": dim(4, 3.5, 980.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"sp","kind":"modifier","operator":"book_split","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.1},
            {"name":"angle_degrees","value_type":"number","numeric_value":28},
            {"name":"branch_sign","value_type":"number","numeric_value":1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.44},
            {"name":"split_generation","value_type":"number","numeric_value":1},
            {"name":"access_side","value_type":"string","string_value":"closed"}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"composition","operator":"join_related","inputs":["sp"],"parameters":[
            {"name":"bridge_ratio","value_type":"number","numeric_value":0.28}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 38. inflate short_axis 1/2 (path eccfafc4) =====
programs.append({
    "name": "inflate_12_short_38",
    "base_form_id": "elliptical", "base_seed": "slab",
    "intent_tags": ["inflated_12", "swollen_slab", "east_notch"],
    "book_composition_path_id": "book:path:eccfafc4718361d6aec40a901f53b344d4bff77683f4887715da5adcce05157f",
    "rationale": "1/2 elliptical slab inflated creates a swollen body with convex east face addressing the road.",
    "dimensional_intent": dim(4, 3.5, 1000.0),
    "nodes": [
        box_node("b0", *SLAB),
        {"id":"ell","kind":"modifier","operator":"ellipsoidize","inputs":["b0"],"parameters":[
            {"name":"segments","value_type":"number","numeric_value":20}],"semantic_role":"dominant_mass"},
        matrix_node("m0", "ell", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        inflate_node("inf","m0","y",1.4,1.35),
        notch_node("result","inf","east",0.26,0.42,0.55)
    ], "root_id": "result"
})

# ===== 39. overlap short_axis 1/2 (path c15ec552) =====
programs.append({
    "name": "overlap_12_short_39",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["overlap_pair_12", "slipped_slabs", "east_court"],
    "book_composition_path_id": "book:path:c15ec55248a4fc32d3f15fea2da9b94c5831c48f2dedecef91ddf03a61f04ef1",
    "rationale": "Two 1/2 slabs slipped in plan create a cascading public terrace visible from east road.",
    "dimensional_intent": dim(4, 3.5, 1000.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"ovl","kind":"modifier","operator":"overlap_related","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"slab_ratio","value_type":"number","numeric_value":0.52},
            {"name":"shift_ratio","value_type":"number","numeric_value":0.38},
            {"name":"vertical_overlap","value_type":"number","numeric_value":0.32},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        courtyard_node("result","ovl",0.2,"east")
    ], "root_id": "result"
})

# ===== 40. inscribe short_axis 1/2 (path 591a729d) =====
programs.append({
    "name": "inscribe_12_short_40",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["inscribed_1_2", "ring_plan", "east_carve"],
    "book_composition_path_id": "book:path:591a729db54894dfd9449b5e5f08781d509ee6da02353d574828e141854ef1fe",
    "rationale": "1/2 slab with inscribed inner court creates a ring plan; east carve reveals the inner light well.",
    "dimensional_intent": dim(4, 3.5, 950.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        courtyard_node("insc","m0",0.3,"closed","program_space"),
        carve_void_node("result","insc",0.18,"east")
    ], "root_id": "result"
})

# ===== 41. inscribe+intersect short_axis 1/2 (path a34184c5) =====
programs.append({
    "name": "inscribe_intersect_12_41",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["inscribed_then_crossed", "ring_cross", "east_notch"],
    "book_composition_path_id": "book:path:a34184c51ffd9faa6f4e694bd0df018b4499f561be4b29d1f086e7b8361fd7b7",
    "rationale": "1/2 slab inscribed with inner court then intersected by a crossing bar; crossing creates an activated inner ring.",
    "dimensional_intent": dim(4, 3.5, 960.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        courtyard_node("insc","m0",0.28,"closed","dominant_mass"),
        {"id":"isct","kind":"modifier","operator":"intersect_related","inputs":["insc"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"angle_degrees","value_type":"number","numeric_value":0},
            {"name":"bar_ratio","value_type":"number","numeric_value":0.25},
            {"name":"unit_scale","value_type":"number","numeric_value":0.6}],"semantic_role":"program_space"},
        notch_node("result","isct","east",0.25,0.38,0.5)
    ], "root_id": "result"
})

# ===== 42. branch+pack+stack short_axis 1/2 (path 9c9d6d2d) =====
programs.append({
    "name": "branch_pack_stack_12_42",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["packed_branching", "stacked_arms", "east_court"],
    "book_composition_path_id": "book:path:9c9d6d2d18bf525d39eb0c2299651d643b20f3f3e0de68975addd59e346d58d2",
    "rationale": "1/2 block branched then packed and stacked; a dense aggregation of branching arms creates a clustered civic mass.",
    "dimensional_intent": dim(4, 3.5, 1100.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"br","kind":"modifier","operator":"book_branch","inputs":["m0"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.52},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.42},
            {"name":"angle_degrees","value_type":"number","numeric_value":80},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"dominant_mass"},
        {"id":"arr","kind":"pattern","operator":"related_array","inputs":["br"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"count","value_type":"number","numeric_value":2},
            {"name":"mode","value_type":"string","string_value":"pack"},
            {"name":"spacing_ratio","value_type":"number","numeric_value":1.1},
            {"name":"unit_scale","value_type":"number","numeric_value":1.0},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"program_space"},
        courtyard_node("result","arr",0.2,"east")
    ], "root_id": "result"
})

# ===== 43. lift+carve short_axis 1/2 (path 82e07b84) =====
programs.append({
    "name": "lift_carve_12_43",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["lifted_carved", "law_courts_12", "east_threshold"],
    "book_composition_path_id": "book:path:82e07b845038d9e2c03a74eab9531bfdb2aaa74dd621e9ab21c72eb467b32bd7",
    "rationale": "1/2 slab lifted and carved below; public ground freed while programme floats above carved plinth.",
    "dimensional_intent": dim(4, 3.5, 1050.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"lft","kind":"modifier","operator":"book_lift","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"distance_ratio","value_type":"number","numeric_value":0.22},
            {"name":"guest_scale","value_type":"number","numeric_value":0.58},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        book_carve_node("carv","lft","y","east",0.4,0.3,1.0),
        lift_node("result","carv",0.2,0.16,"east")
    ], "root_id": "result"
})

# ===== 44. twist vertical 1/2 (path 716df07c) =====
programs.append({
    "name": "twist_12_vertical_44",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["twisted_block", "torsion_body", "east_notch"],
    "book_composition_path_id": "book:path:716df07ca23e72681a3aca19b6a160a3c867f21315b111d0c6ac21a2700be269",
    "rationale": "1/2 block twisted along its vertical axis; torsion creates diagonal corner emphasis addressing east road.",
    "dimensional_intent": dim(4, 3.5, 1000.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        twist_node("tw","m0","z",40,5),
        notch_node("result","tw","east",0.22,0.4,0.48)
    ], "root_id": "result"
})

# ===== 45. pinch vertical 1/2 (path 7f4ace17) =====
programs.append({
    "name": "pinch_12_vertical_45",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["pinched_waist", "hourglass_section", "east_carve"],
    "book_composition_path_id": "book:path:7f4ace179d50c15c3a63cd24d5dcb7e3420da79697dcb07afb1a30f73bbed628",
    "rationale": "1/2 block pinched at mid-height creates an hourglass section; east carve at the waist marks the public threshold.",
    "dimensional_intent": dim(4, 3.5, 900.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        pinch_node("pnch","m0","z",0.5,0.65),
        carve_void_node("result","pnch",0.22,"east")
    ], "root_id": "result"
})

# ===== 46. branch+branch vertical 1/2 (path aec174c3) =====
programs.append({
    "name": "branch_branch_12_46",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["double_branch_12", "forked_vertical", "east_court"],
    "book_composition_path_id": "book:path:aec174c38f9ed86be822dd7813012953b17a2443337cd862c35837a7c34ab023",
    "rationale": "1/2 block double-branched vertically; forked plan creates diverse orientations with east-facing primary arm.",
    "dimensional_intent": dim(4, 3.5, 1050.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"br1","kind":"modifier","operator":"book_branch","inputs":["m0"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.55},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.42},
            {"name":"angle_degrees","value_type":"number","numeric_value":75},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_branch","inputs":["br1"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.48},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.38},
            {"name":"angle_degrees","value_type":"number","numeric_value":-65},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 47. notch+twist vertical 1/2 (path 4805f593) =====
programs.append({
    "name": "notch_twist_12_47",
    "base_form_id": "cube", "base_seed": "tower",
    "intent_tags": ["notch_twist_12", "corner_torsion", "east_notch"],
    "book_composition_path_id": "book:path:4805f5934fe933b3108aeb3a3aa5a567a1a1bd1debe1a625217a979a35f16c24",
    "rationale": "1/2 tower notched at corner then twisted; sculptural torsion emerges above the corner notch entry zone.",
    "dimensional_intent": dim(5, 3.3, 920.0),
    "nodes": [
        box_node("b0", *TOWER),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        book_notch_node("ntch","m0","z","ne",0.3),
        twist_node("result","ntch","z",38,4)
    ], "root_id": "result"
})

# ===== 48. expand+nest vertical 1/2 (path e688a33b) =====
programs.append({
    "name": "expand_nest_12_48",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["house_n_12", "nested_shells", "east_threshold"],
    "book_composition_path_id": "book:path:e688a33bce52391b696ecea5bef1c7926ec4e15d1a02971bebfaf8fcb990c13b",
    "rationale": "1/2 block expanded then nested; concentric layers read as public outer ring and private inner zone.",
    "dimensional_intent": dim(4, 3.5, 950.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.5,0,0,0],[0,0.5,0,0],[0,0,0.5,0],[0,0,0,1]]),
        {"id":"exp","kind":"modifier","operator":"boundary_expand","inputs":["m0"],"parameters":[
            {"name":"amount","value_type":"number","numeric_value":0.28},
            {"name":"axis","value_type":"string","string_value":"z"}],"semantic_role":"dominant_mass"},
        nested_related_node("nst","exp","y",0.22,0.52),
        carve_void_node("result","nst",0.2,"east")
    ], "root_id": "result"
})

# ===== 49. offset long_axis 1/4 (path 9ff66e14) =====
programs.append({
    "name": "offset_14_long_49",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["offset_bar_14", "parallel_pair", "east_court"],
    "book_composition_path_id": "book:path:9ff66e145418829ccc5e710634ec50389ce05bc62f6496984bde22110528e383",
    "rationale": "1/4 bar offset creates an intimate parallel pair; east court is the main organizing space between them.",
    "dimensional_intent": dim(4, 3.5, 900.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        offset_related_node("off","m0","y",0.42,0.88),
        courtyard_node("result","off",0.22,"east")
    ], "root_id": "result"
})

# ===== 50. compress long_axis 1/4 (path 546119cf) =====
programs.append({
    "name": "compress_14_long_50",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["compressed_14", "thin_profile", "east_notch"],
    "book_composition_path_id": "book:path:546119cfb82a276ceee53e1eb09d960d054ff4bacd4853bc824ba6ed9ffd8e8f",
    "rationale": "1/4 slab compressed to a thin profile stands tall against the east road; notch marks civic entry.",
    "dimensional_intent": dim(5, 3.3, 850.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        {"id":"clip","kind":"modifier","operator":"clip_fraction","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"y"},
            {"name":"fraction","value_type":"number","numeric_value":0.65},
            {"name":"anchor","value_type":"string","string_value":"low"}],"semantic_role":"dominant_mass"},
        notch_node("result","clip","east",0.28,0.42,0.55)
    ], "root_id": "result"
})

# ===== 51. split+split long_axis 1/4 (path f1440150) =====
programs.append({
    "name": "split_split_14_51",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["z_plan_14", "double_split_quarter", "east_access"],
    "book_composition_path_id": "book:path:f1440150bbd785859ef88baca5734f8731b6b029da123797ae55c43541ecb398",
    "rationale": "1/4 bar double-split at different angles creates a compact Z-plan with three legible programme zones.",
    "dimensional_intent": dim(4, 3.5, 880.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        {"id":"sp1","kind":"modifier","operator":"book_split","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.07},
            {"name":"angle_degrees","value_type":"number","numeric_value":22},
            {"name":"branch_sign","value_type":"number","numeric_value":1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.42},
            {"name":"split_generation","value_type":"number","numeric_value":1},
            {"name":"access_side","value_type":"string","string_value":"closed"}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_split","inputs":["sp1"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"gap_ratio","value_type":"number","numeric_value":0.07},
            {"name":"angle_degrees","value_type":"number","numeric_value":-22},
            {"name":"branch_sign","value_type":"number","numeric_value":-1.0},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0},
            {"name":"terminal_ratio","value_type":"number","numeric_value":0.42},
            {"name":"split_generation","value_type":"number","numeric_value":2},
            {"name":"access_side","value_type":"string","string_value":"east"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 52. taper+bend long_axis 1/4 (path 0bac03a0) =====
programs.append({
    "name": "taper_bend_14_52",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["tapered_bent", "wedge_arc", "east_notch"],
    "book_composition_path_id": "book:path:0bac03a066888497ad4cdc5a727e609bdb620a3ef13ef9cc5394a46de7a09449",
    "rationale": "1/4 bar tapered to a wedge then bent; the combination creates an asymmetric arc that opens toward the east.",
    "dimensional_intent": dim(4, 3.5, 880.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        taper_node("tap","m0","z",[0.7,0.55]),
        {"id":"result","kind":"modifier","operator":"bent_bar","inputs":["tap"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"angle_degrees","value_type":"number","numeric_value":25},
            {"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 53. pinch+join+array long_axis 1/4 (path af83d6ad) =====
programs.append({
    "name": "pinch_join_array_14_53",
    "base_form_id": "cube", "base_seed": "bar",
    "intent_tags": ["pinched_arrayed", "waisted_linear", "east_notch"],
    "book_composition_path_id": "book:path:af83d6add866295511a823d82a17f6d3b2316e11204b251b3c0c6eee90de813f",
    "rationale": "1/4 bar pinched at waist then arrayed linearly; pinched rhythm creates alternating narrow/wide sections.",
    "dimensional_intent": dim(4, 3.5, 950.0),
    "nodes": [
        box_node("b0", *BAR),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        pinch_node("pnch","m0","z",0.5,0.7),
        {"id":"arr","kind":"pattern","operator":"linear_array","inputs":["pnch"],"parameters":[
            {"name":"count","value_type":"number","numeric_value":2},
            {"name":"vector","value_type":"vector","vector_value":[0.35,0.0,0.0]},
            {"name":"spacing","value_type":"number","numeric_value":0.0}],"semantic_role":"program_space"},
        notch_node("result","arr","east",0.25,0.4,0.5)
    ], "root_id": "result"
})

# ===== 54. extrude short_axis 1/4 (path f42375c1) =====
programs.append({
    "name": "extrude_14_short_54",
    "base_form_id": "tetrahedral", "base_seed": "block",
    "intent_tags": ["tetrahedral_extrude", "faceted_body", "east_notch"],
    "book_composition_path_id": "book:path:f42375c1818d4ccdef5278032d64aa984e673a76b1e44056b286a08f507288d1",
    "rationale": "1/4 tetrahedral base extruded vertically creates a faceted prism with angled faces addressing east road.",
    "dimensional_intent": dim(4, 3.5, 900.0),
    "nodes": [
        box_node("b0", *BLOCK),
        {"id":"tet","kind":"modifier","operator":"tetrahedralize","inputs":["b0"],"parameters":[],"semantic_role":"dominant_mass"},
        matrix_node("m0", "tet", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        {"id":"ext","kind":"modifier","operator":"boundary_expand","inputs":["m0"],"parameters":[
            {"name":"amount","value_type":"number","numeric_value":0.35},
            {"name":"axis","value_type":"string","string_value":"z"}],"semantic_role":"dominant_mass"},
        notch_node("result","ext","east",0.28,0.42,0.5)
    ], "root_id": "result"
})

# ===== 55. lodge short_axis 1/4 (path 89a8d2e0) =====
programs.append({
    "name": "lodge_14_short_55",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["lodged_guest", "bridging_bar", "east_court"],
    "book_composition_path_id": "book:path:89a8d2e071e7dc228815ddab41a199bf7379d5742d861095f20ab2de6fd610f5",
    "rationale": "A bar is lodged between two 1/4 host volumes; the lodged bar creates a connecting bridge and public gateway from east.",
    "dimensional_intent": dim(4, 3.5, 930.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        book_lodge_node("ldg","m0","x",0.38,0.55),
        courtyard_node("result","ldg",0.2,"east")
    ], "root_id": "result"
})

# ===== 56. extract short_axis 1/4 (path bbd403ce) =====
programs.append({
    "name": "extract_14_short_56",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["extracted_volume", "socket_pair", "east_notch"],
    "book_composition_path_id": "book:path:bbd403cec5ff6827cf04b266a65afdab72752a8071a42a83017b53f878176551",
    "rationale": "1/4 block: a volume extracted from the host leaves a socket; the extracted piece stands alongside creating a socket+piece pair.",
    "dimensional_intent": dim(4, 3.5, 880.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        book_extract_node("ext","m0","x","east",0.32,0.48),
        notch_node("result","ext","east",0.22,0.38,0.5)
    ], "root_id": "result"
})

# ===== 57. inscribe+intersect short_axis 1/4 (path b1dc18f7) =====
programs.append({
    "name": "inscribe_intersect_14_57",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["ring_cross_14", "inscribed_bar_cross", "east_notch"],
    "book_composition_path_id": "book:path:b1dc18f7817ae62db7951887748c90355ffaa9ee10880a1dfaad396c8a5e54e0",
    "rationale": "1/4 slab inscribed with inner court then intersected; bar crossing activates the ring revealing its depth.",
    "dimensional_intent": dim(4, 3.5, 870.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        courtyard_node("insc","m0",0.3,"closed","dominant_mass"),
        {"id":"isct","kind":"modifier","operator":"intersect_related","inputs":["insc"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"x"},
            {"name":"angle_degrees","value_type":"number","numeric_value":0},
            {"name":"bar_ratio","value_type":"number","numeric_value":0.22},
            {"name":"unit_scale","value_type":"number","numeric_value":0.55}],"semantic_role":"program_space"},
        notch_node("result","isct","east",0.25,0.4,0.5)
    ], "root_id": "result"
})

# ===== 58. branch+pack+stack short_axis 1/4 (path ea3fdbfd) =====
programs.append({
    "name": "branch_pack_stack_14_58",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["packed_branch_14", "clustered_civic", "east_court"],
    "book_composition_path_id": "book:path:ea3fdbfddf0a32805dc837821770519d713d02a468fa8e914311a1e122289d20",
    "rationale": "1/4 block branched and packed into a two-unit stack; a dense civic cluster with east court as public space.",
    "dimensional_intent": dim(4, 3.5, 950.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        {"id":"br","kind":"modifier","operator":"book_branch","inputs":["m0"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.52},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.4},
            {"name":"angle_degrees","value_type":"number","numeric_value":80},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"dominant_mass"},
        {"id":"arr","kind":"pattern","operator":"related_array","inputs":["br"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"y"},
            {"name":"count","value_type":"number","numeric_value":2},
            {"name":"mode","value_type":"string","string_value":"pack"},
            {"name":"spacing_ratio","value_type":"number","numeric_value":1.15},
            {"name":"unit_scale","value_type":"number","numeric_value":1.0},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"program_space"},
        courtyard_node("result","arr",0.2,"east")
    ], "root_id": "result"
})

# ===== 59. lift+carve short_axis 1/4 (path 0e3fe6f1) =====
programs.append({
    "name": "lift_carve_14_59",
    "base_form_id": "cube", "base_seed": "slab",
    "intent_tags": ["lifted_carved_14", "courts_section", "east_lift"],
    "book_composition_path_id": "book:path:0e3fe6f19fe3fb3b4fdfecd76c496e00141469a5ab4be263385f49ea58ce99b5",
    "rationale": "1/4 slab lifted above ground then carved below; public ground freed while programme occupies the floating volume.",
    "dimensional_intent": dim(4, 3.5, 870.0),
    "nodes": [
        box_node("b0", *SLAB),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        {"id":"lft","kind":"modifier","operator":"book_lift","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string_value":"z"},
            {"name":"distance_ratio","value_type":"number","numeric_value":0.25},
            {"name":"guest_scale","value_type":"number","numeric_value":0.55},
            {"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"},
        lift_node("result","lft",0.2,0.15,"east")
    ], "root_id": "result"
})

# ===== 60. twist vertical 1/4 (path b161eb4c) =====
programs.append({
    "name": "twist_14_vertical_60",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["twisted_14", "vertical_torsion", "east_notch"],
    "book_composition_path_id": "book:path:b161eb4c3bb6230cd34980d091fc44bf52f7d2648e59f55b39dc46e64225dc46",
    "rationale": "1/4 block twisted on vertical axis creates diagonal corner emphasis; east notch opens the torsion at street level.",
    "dimensional_intent": dim(4, 3.5, 880.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        twist_node("tw","m0","z",45,5),
        notch_node("result","tw","east",0.24,0.4,0.5)
    ], "root_id": "result"
})

# ===== 61. pinch vertical 1/4 (path 56f69a20) =====
programs.append({
    "name": "pinch_14_vertical_61",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["waisted_14", "hourglass_14", "east_carve"],
    "book_composition_path_id": "book:path:56f69a2038120b9187f1387efee21a6a63cf530d026b6f10dfab37c2db2dc717",
    "rationale": "1/4 block pinched at mid-height reads as a waisted tower; east carve at the waist marks the public entrance.",
    "dimensional_intent": dim(4, 3.5, 860.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        pinch_node("pnch","m0","z",0.5,0.62),
        carve_void_node("result","pnch",0.2,"east")
    ], "root_id": "result"
})

# ===== 62. branch+branch vertical 1/4 (path dc50b322) =====
programs.append({
    "name": "branch_branch_14_62",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["double_branch_14", "pinwheel_plan", "east_court"],
    "book_composition_path_id": "book:path:dc50b322c264219be6835f6b50fc2a3e5ffba233fd5e5f9fa3813b14d5523193",
    "rationale": "1/4 block branched twice vertically creates a pinwheel plan readable from all four sides.",
    "dimensional_intent": dim(4, 3.5, 900.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        {"id":"br1","kind":"modifier","operator":"book_branch","inputs":["m0"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.55},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.4},
            {"name":"angle_degrees","value_type":"number","numeric_value":80},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"dominant_mass"},
        {"id":"result","kind":"modifier","operator":"book_branch","inputs":["br1"],"parameters":[
            {"name":"trunk_ratio","value_type":"number","numeric_value":0.5},
            {"name":"arm_ratio","value_type":"number","numeric_value":0.36},
            {"name":"angle_degrees","value_type":"number","numeric_value":-70},
            {"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"public_threshold"}
    ], "root_id": "result"
})

# ===== 63. shift+notch vertical 1/4 (path 0d5b1e3a) =====
programs.append({
    "name": "shift_notch_14_63",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["shifted_notched_14", "displaced_corner", "east_notch"],
    "book_composition_path_id": "book:path:0d5b1e3a233d34e16073c222838ee053eabeb8692327fc62ef668c7b75a716d1",
    "rationale": "1/4 block: one half shifted then notched at the resulting offset corner; the shift exposes a relief face.",
    "dimensional_intent": dim(4, 3.5, 870.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        shift_related_node("sh","m0","x",0.3,0.5),
        book_notch_node("ntch","sh","z","ne",0.25),
        notch_node("result","ntch","east",0.22,0.4,0.5)
    ], "root_id": "result"
})

# ===== 64. embed+overlap vertical 1/4 (path bd7cfc87) =====
programs.append({
    "name": "embed_overlap_14_64",
    "base_form_id": "cube", "base_seed": "block",
    "intent_tags": ["embedded_overlapped", "void_with_slip", "east_notch"],
    "book_composition_path_id": "book:path:bd7cfc87da1811e45875acde3aa82d513fc343204bca6bcd2fb26f3a1d1357e7",
    "rationale": "1/4 block: a guest is embedded creating a void then overlapped; the overlap zone reads as a public canopy.",
    "dimensional_intent": dim(4, 3.5, 860.0),
    "nodes": [
        box_node("b0", *BLOCK),
        matrix_node("m0", "b0", [[0.25,0,0,0],[0,0.25,0,0],[0,0,0.25,0],[0,0,0,1]]),
        {"id":"emb","kind":"modifier","operator":"embed_void","inputs":["m0"],"parameters":[
            {"name":"axis","value_type":"string","string