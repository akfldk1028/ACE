"""
gen_book18e_part2.py - continuation of builder functions (paths 51-77) + main entry
"""
# This file is exec'd after gen_book18e.py sets up all helpers and paths 0-50
# Then we append BUILDERS list and run main()

# PATH 51 continuation: taper+bend → tower
def b51_full(pid, v):
    w,d,h = (0.68, 0.68, 2.5)  # tower
    es = [0.65+v*0.05, 0.65+v*0.05]
    angle = 18 + v*8
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        taper_node("tap0", "m0", axis="z", start_scale=[1.0,1.0], end_scale=es,
                   lower_floor_fraction=0.0, subdivisions=3),
        bend_node("bend0", "tap0", axis="y", angle=angle, subdivisions=4),
        courtyard_node("result", "bend0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_taper_bend_court", "cube", "tower",
                  ["taper","bend","long_axis","quarter_fraction","courtyard"],
                  "Quarter tower tapered then bent; east courtyard below the curved crown.",
                  nodes, "result", storeys=5, target_gfa=1250)

# PATH 52: 1/4 long_axis pinch+join+array → slab + pinch + related_array → notch(east)
def b52(pid, v):
    w,d,h = (2.2, 1.45, 0.28)  # slab
    wr = 0.48 + v*0.04
    ws = 0.70 + v*0.04
    cnt = 2
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        pinch_node("pinch0", "m0", axis="z", waist_ratio=wr, waist_scale=ws,
                   profile_power=2.0+v*0.3, subdivisions=4),
        related_array_node("arr0", "pinch0", axis="x", count=cnt, mode="array",
                           spacing_ratio=1.15+v*0.05, stagger_ratio=0.0,
                           unit_scale=0.88+v*0.04, vertical_anchor="input_base"),
        notch_node("result", "arr0", side="east", corner="ne",
                   ratio=0.26+v*0.03, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "quarter_pinch_array_notch", "cube", "slab",
                  ["pinch","join","array","long_axis","quarter_fraction","notch"],
                  "Pinched slab arrayed in pair; east notch at the pinch joint marks civic entry.",
                  nodes, "result", storeys=4, target_gfa=970)

# PATH 53: 1/4 short_axis extrude → block + boundary_expand → lift(east)
def b53(pid, v):
    w,d,h = (1.0, 1.0, 1.0)  # block
    amount = 0.18 + v*0.05
    sf = 0.42 + v*0.06
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        boundary_expand_node("exp0", "m0", axis="z", amount=amount, shoulder_fraction=sf),
        lift_node("result", "exp0", access_side="east",
                  rise_ratio=0.24+v*0.04, support_ratio=0.32+v*0.03),
    ]
    return mkprog(pid, v, "quarter_extrude_lift", "cube", "block",
                  ["extrude","short_axis","quarter_fraction","lift"],
                  "Quarter-block expanded upward and lifted; east lift exposes public ground.",
                  nodes, "result", storeys=4, target_gfa=930)

# PATH 54: 1/4 short_axis lodge → bar + book_lodge → courtyard(east)
def b54(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    dr = 0.28 + v*0.04
    gs = 0.55 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        book_lodge_node("lodge0", "m0", axis="z", distance_ratio=dr,
                        guest_scale=gs, outward_sign=1.0),
        courtyard_node("result", "lodge0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_lodge_court", "cube", "bar",
                  ["lodge","short_axis","quarter_fraction","courtyard"],
                  "Guest bar lodged in host interval; east courtyard uses the lodged gap as entry.",
                  nodes, "result", storeys=3, target_gfa=820)

# PATH 55: 1/4 short_axis extract → slab + book_extract → carve_void(east)
def b55(pid, v):
    w,d,h = (2.2, 1.45, 0.28)  # slab
    dr = 0.28 + v*0.04
    gs = 0.50 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        book_extract_node("ext0", "m0", axis="z", face_side="east",
                          distance_ratio=dr, guest_scale=gs, outward_sign=1.0),
        carve_void_node("result", "ext0", margin=0.20+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_extract_carve", "cube", "slab",
                  ["extract","short_axis","quarter_fraction","carve_void"],
                  "Quarter slab extraction channel through east face; carve void deepens civic recce.",
                  nodes, "result", storeys=3, target_gfa=840)

# PATH 56: 1/4 short_axis inscribe+intersect → bar + book_notch + intersect_related → notch(east)
def b56(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    ratio = 0.22 + v*0.04
    br = 0.40 + v*0.04
    us = 0.76 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="nw",
                        outward_sign=1.0, ratio=ratio),
        intersect_related_node("inter0", "notch0", axis="z", angle_degrees=90.0,
                               bar_ratio=br, unit_scale=us),
        notch_node("result", "inter0", side="east", corner="ne",
                   ratio=0.26+v*0.04, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "quarter_inscribe_intersect_notch", "cube", "bar",
                  ["inscribe","intersect","short_axis","quarter_fraction","notch"],
                  "Bar notched then cross-intersected; east notch completes the entry articulation.",
                  nodes, "result", storeys=4, target_gfa=1000)

# PATH 57: 1/4 short_axis branch+pack+stack → bar + book_branch + related_array → carve_void(east)
def b57(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    angle = 55 + v*15
    tr = 0.60 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        book_branch_node("br0", "m0", angle_degrees=angle, trunk_ratio=tr,
                         arm_ratio=0.35+v*0.04, vertical_anchor="input_base"),
        related_array_node("arr0", "br0", axis="y", count=2, mode="pack",
                           spacing_ratio=1.12+v*0.05, stagger_ratio=0.0,
                           unit_scale=0.88+v*0.04, vertical_anchor="input_base"),
        carve_void_node("result", "arr0", margin=0.20+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_branch_pack_carve", "cube", "bar",
                  ["branch","pack","stack","short_axis","quarter_fraction","carve_void"],
                  "Branched bar packed in pair; east carve void in the arrangement's front gap.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 58: 1/4 short_axis lift+carve → block + book_lift + book_carve → lift(east)
def b58(pid, v):
    w,d,h = (1.0, 1.0, 1.0)  # block
    dr = 0.28 + v*0.04
    gs = 0.56 + v*0.04
    cd = 0.26 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        book_lift_node("lift0", "m0", axis="z", distance_ratio=dr,
                       guest_scale=gs, outward_sign=1.0),
        book_carve_node("carve0", "lift0", axis="z", face_side="east",
                        depth_ratio=cd, outward_sign=1.0, width_ratio=0.42+v*0.04),
        lift_node("result", "carve0", access_side="east",
                  rise_ratio=0.24+v*0.04, support_ratio=0.30+v*0.03),
    ]
    return mkprog(pid, v, "quarter_lift_carve_lift", "cube", "block",
                  ["lift","carve","short_axis","quarter_fraction"],
                  "Lifted block east-carved; terminal lift opens east ground as civic passage.",
                  nodes, "result", storeys=4, target_gfa=980)

# PATH 59: 1/4 vertical twist → tower + twist → courtyard(east)
def b59(pid, v):
    w,d,h = (0.68, 0.68, 2.5)  # tower
    angle = 28 + v*10
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        twist_node("twist0", "m0", axis="z", angle=angle, subdivisions=4),
        courtyard_node("result", "twist0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_twisted_court", "cube", "tower",
                  ["twist","vertical","quarter_fraction","courtyard"],
                  "Quarter tower twisted about z; east courtyard as civic space below twist.",
                  nodes, "result", storeys=5, target_gfa=1250)

# PATH 60: 1/4 vertical pinch → slab + pinch → carve_void(east)
def b60(pid, v):
    w,d,h = (2.2, 1.45, 0.28)  # slab
    wr = 0.50 + v*0.04
    ws = 0.65 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        pinch_node("pinch0", "m0", axis="z", waist_ratio=wr, waist_scale=ws,
                   profile_power=2.0+v*0.3, subdivisions=4),
        carve_void_node("result", "pinch0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_pinched_carve", "cube", "slab",
                  ["pinch","vertical","quarter_fraction","carve_void"],
                  "Quarter slab pinched at waist; east carve void opens the narrowed civic face.",
                  nodes, "result", storeys=4, target_gfa=880)

# PATH 61: 1/4 vertical branch+branch → bar + book_branch×2 → notch(east)
def b61(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    angle1 = 48 + v*12
    angle2 = -38 - v*10
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        book_branch_node("br0", "m0", angle_degrees=angle1, trunk_ratio=0.56+v*0.04,
                         arm_ratio=0.36+v*0.04, vertical_anchor="input_base"),
        book_branch_node("br1", "br0", angle_degrees=angle2, trunk_ratio=0.60+v*0.04,
                         arm_ratio=0.32+v*0.04, vertical_anchor="input_base"),
        notch_node("result", "br1", side="east", corner="ne",
                   ratio=0.26+v*0.04, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "quarter_double_branch_notch", "cube", "bar",
                  ["branch","vertical","quarter_fraction","notch"],
                  "Double branching in quarter bar; east notch at the fork junction marks entry.",
                  nodes, "result", storeys=4, target_gfa=1050)

# PATH 62: 1/4 vertical shift+notch → block + shift_related + book_notch → carve_void(east)
def b62(pid, v):
    w,d,h = (1.0, 1.0, 1.0)  # block
    dr = 0.32 + v*0.04
    ratio = 0.24 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        shift_related_node("sh0", "m0", axis="x", distance_ratio=dr,
                           outward_sign=1.0, split_ratio=0.50+v*0.04),
        book_notch_node("notch0", "sh0", axis="z", corner="ne",
                        outward_sign=1.0, ratio=ratio),
        carve_void_node("result", "notch0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "quarter_shift_notch_carve", "cube", "block",
                  ["shift","notch","vertical","quarter_fraction","carve_void"],
                  "Shifted related volume with corner notch; east carve void marks public threshold.",
                  nodes, "result", storeys=4, target_gfa=960)

# PATH 63: 1/4 vertical embed+overlap → slab + book_embed_void + overlap_related → lift(east)
def b63(pid, v):
    w,d,h = (2.2, 1.45, 0.28)  # slab
    er = 0.30 + v*0.05
    gs = 0.50 + v*0.04
    sr = 0.30 + v*0.04
    sl = 0.62 + v*0.04
    vo = 0.22 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.65, 0.65, 1.0)),
        book_embed_void_node("emb0", "m0", axis="z", position="center",
                             embedded_ratio=er, guest_scale=gs),
        overlap_related_node("ovl0", "emb0", axis="x", outward_sign=1.0,
                             shift_ratio=sr, slab_ratio=sl, vertical_overlap=vo),
        lift_node("result", "ovl0", access_side="east",
                  rise_ratio=0.22+v*0.04, support_ratio=0.30+v*0.03),
    ]
    return mkprog(pid, v, "quarter_embed_overlap_lift", "cube", "slab",
                  ["embed","overlap","vertical","quarter_fraction","lift"],
                  "Embedded void slab then overlapped; east lift creates ground passage below.",
                  nodes, "result", storeys=3, target_gfa=870)

# PATH 64: 1/8 long_axis nest → slab + nested_related → courtyard(east)
def b64(pid, v):
    w,d,h = (2.2, 1.45, 0.28)  # slab
    dr = 0.25 + v*0.04
    us = 0.68 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        nested_related_node("nest0", "m0", axis="x", distance_ratio=dr, unit_scale=us),
        courtyard_node("result", "nest0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "eighth_nested_court", "cube", "slab",
                  ["nest","long_axis","eighth_fraction","courtyard"],
                  "Eighth-fraction slab with nested inner volume; east courtyard as layered civic court.",
                  nodes, "result", storeys=3, target_gfa=780)

# PATH 65: 1/8 long_axis carve → bar + book_carve → notch(east)
def b65(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    dr = 0.28 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        book_carve_node("carve0", "m0", axis="z", face_side="east",
                        depth_ratio=dr, outward_sign=1.0, width_ratio=0.42+v*0.04),
        notch_node("result", "carve0", side="east", corner="ne",
                   ratio=0.26+v*0.04, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "eighth_carved_notch", "cube", "bar",
                  ["carve","long_axis","eighth_fraction","notch"],
                  "Eighth bar east-carved then NE-notched; compact civic address on small parcel share.",
                  nodes, "result", storeys=4, target_gfa=900)

# PATH 66: 1/8 long_axis intersect+intersect → bar + intersect_related×2 → carve_void(east)
def b66(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    br1 = 0.38 + v*0.04
    us1 = 0.78 + v*0.04
    br2 = 0.36 + v*0.04
    us2 = 0.72 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        intersect_related_node("inter0", "m0", axis="z", angle_degrees=90.0,
                               bar_ratio=br1, unit_scale=us1),
        intersect_related_node("inter1", "inter0", axis="y", angle_degrees=45.0,
                               bar_ratio=br2, unit_scale=us2),
        carve_void_node("result", "inter1", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "eighth_double_intersect_carve", "cube", "bar",
                  ["intersect","long_axis","eighth_fraction","carve_void"],
                  "Double cross-bar intersection creates figure-8 plan; east carve void opens address.",
                  nodes, "result", storeys=4, target_gfa=960)

# PATH 67: 1/8 long_axis taper+bend → tower + taper + bend → lift(east)
def b67(pid, v):
    w,d,h = (0.68, 0.68, 2.5)  # tower
    es = [0.68+v*0.04, 0.68+v*0.04]
    angle = 20 + v*8
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        taper_node("tap0", "m0", axis="z", start_scale=[1.0,1.0], end_scale=es,
                   lower_floor_fraction=0.0, subdivisions=3),
        bend_node("bend0", "tap0", axis="y", angle=angle, subdivisions=4),
        lift_node("result", "bend0", access_side="east",
                  rise_ratio=0.24+v*0.04, support_ratio=0.32+v*0.03),
    ]
    return mkprog(pid, v, "eighth_taper_bend_lift", "cube", "tower",
                  ["taper","bend","long_axis","eighth_fraction","lift"],
                  "Eighth tower tapered and bent; east lift opens public passage at tower base.",
                  nodes, "result", storeys=5, target_gfa=1150)

# PATH 68: 1/8 long_axis pinch+join+array → slab + pinch + related_array → courtyard(east)
def b68(pid, v):
    w,d,h = (2.2, 1.45, 0.28)  # slab
    wr = 0.46 + v*0.04
    ws = 0.68 + v*0.05
    cnt = 2
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        pinch_node("pinch0", "m0", axis="z", waist_ratio=wr, waist_scale=ws,
                   profile_power=2.0+v*0.3, subdivisions=4),
        related_array_node("arr0", "pinch0", axis="y", count=cnt, mode="array",
                           spacing_ratio=1.15+v*0.05, stagger_ratio=0.0,
                           unit_scale=0.88+v*0.04, vertical_anchor="input_base"),
        courtyard_node("result", "arr0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "eighth_pinch_array_court", "cube", "slab",
                  ["pinch","join","array","long_axis","eighth_fraction","courtyard"],
                  "Pinched slab arrayed; east courtyard at the pinch waist between units.",
                  nodes, "result", storeys=4, target_gfa=930)

# PATH 69: 1/8 short_axis extrude → block + boundary_expand → notch(east)
def b69(pid, v):
    w,d,h = (1.0, 1.0, 1.0)  # block
    amount = 0.20 + v*0.05
    sf = 0.44 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        boundary_expand_node("exp0", "m0", axis="z", amount=amount, shoulder_fraction=sf),
        notch_node("result", "exp0", side="east", corner="ne",
                   ratio=0.26+v*0.04, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "eighth_extrude_notch", "cube", "block",
                  ["extrude","short_axis","eighth_fraction","notch"],
                  "Eighth block expanded and shoulder-profiled; east notch at entry corner.",
                  nodes, "result", storeys=4, target_gfa=920)

# PATH 70: 1/8 short_axis lodge → bar + book_lodge → carve_void(east)
def b70(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    dr = 0.26 + v*0.04
    gs = 0.52 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        book_lodge_node("lodge0", "m0", axis="z", distance_ratio=dr,
                        guest_scale=gs, outward_sign=1.0),
        carve_void_node("result", "lodge0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "eighth_lodge_carve", "cube", "bar",
                  ["lodge","short_axis","eighth_fraction","carve_void"],
                  "Eighth bar lodged with guest; east carve void in the gap below guest.",
                  nodes, "result", storeys=3, target_gfa=800)

# PATH 71: 1/8 short_axis extract → slab + book_extract → lift(east)
def b71(pid, v):
    w,d,h = (2.2, 1.45, 0.28)  # slab
    dr = 0.26 + v*0.04
    gs = 0.52 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        book_extract_node("ext0", "m0", axis="z", face_side="east",
                          distance_ratio=dr, guest_scale=gs, outward_sign=1.0),
        lift_node("result", "ext0", access_side="east",
                  rise_ratio=0.22+v*0.04, support_ratio=0.30+v*0.03),
    ]
    return mkprog(pid, v, "eighth_extract_lift", "cube", "slab",
                  ["extract","short_axis","eighth_fraction","lift"],
                  "Eighth slab extraction channel; east lift opens the subtracted volume as passage.",
                  nodes, "result", storeys=3, target_gfa=820)

# PATH 72: 1/8 short_axis inscribe+intersect → bar + book_notch + intersect_related → courtyard(east)
def b72(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    ratio = 0.24 + v*0.04
    br = 0.38 + v*0.04
    us = 0.76 + v*0.04
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="sw",
                        outward_sign=1.0, ratio=ratio),
        intersect_related_node("inter0", "notch0", axis="z", angle_degrees=90.0,
                               bar_ratio=br, unit_scale=us),
        courtyard_node("result", "inter0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "eighth_inscribe_intersect_court", "cube", "bar",
                  ["inscribe","intersect","short_axis","eighth_fraction","courtyard"],
                  "Notched bar cross-intersected; east courtyard at the interlocking junction.",
                  nodes, "result", storeys=4, target_gfa=980)

# PATH 73: 1/8 short_axis inflate+pack → slab + inflate + related_array → notch(east)
def b73(pid, v):
    w,d,h = (2.2, 1.45, 0.28)  # slab
    factor = 1.14 + v*0.05
    ms = 1.20 + v*0.05
    cnt = 2
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        inflate_node("infl0", "m0", axis="z", factor=factor,
                     middle_scale=ms, profile_power=2.2+v*0.3, subdivisions=4),
        related_array_node("arr0", "infl0", axis="x", count=cnt, mode="pack",
                           spacing_ratio=1.10+v*0.05, stagger_ratio=0.0,
                           unit_scale=0.90+v*0.04, vertical_anchor="input_base"),
        notch_node("result", "arr0", side="east", corner="ne",
                   ratio=0.26+v*0.03, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "eighth_inflate_pack_notch", "cube", "slab",
                  ["inflate","pack","short_axis","eighth_fraction","notch"],
                  "Eighth inflated slab packed in pair; east notch at the billowing public face.",
                  nodes, "result", storeys=3, target_gfa=820)

# PATH 74: 1/8 short_axis embed+taper → block + book_embed_void + taper → carve_void(east)
def b74(pid, v):
    w,d,h = (1.0, 1.0, 1.0)  # block
    er = 0.30 + v*0.05
    gs = 0.50 + v*0.04
    es = [0.72+v*0.04, 0.72+v*0.04]
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        book_embed_void_node("emb0", "m0", axis="z", position="center",
                             embedded_ratio=er, guest_scale=gs),
        taper_node("tap0", "emb0", axis="z", start_scale=[1.0,1.0], end_scale=es,
                   lower_floor_fraction=0.0, subdivisions=3),
        carve_void_node("result", "tap0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "eighth_embed_taper_carve", "cube", "block",
                  ["embed","taper","short_axis","eighth_fraction","carve_void"],
                  "Eighth block embed-voided then tapered; east carve void at the tapered public face.",
                  nodes, "result", storeys=4, target_gfa=940)

# PATH 75: 1/8 vertical split → tower + book_split → courtyard(east)
def b75(pid, v):
    w,d,h = (0.68, 0.68, 2.5)  # tower
    gap = 0.10 + v*0.03
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        book_split_node("sp0", "m0", axis="y", angle_degrees=0.0, gap_ratio=gap,
                        outward_sign=1.0, branch_sign=1.0, split_generation=1.0,
                        terminal_ratio=0.50+v*0.04, access_side_sv="east"),
        courtyard_node("result", "sp0", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "eighth_split_court", "cube", "tower",
                  ["split","vertical","eighth_fraction","courtyard"],
                  "Eighth tower split displaces one wing; east courtyard in the hinge gap.",
                  nodes, "result", storeys=5, target_gfa=1150)

# PATH 76: 1/8 vertical notch → block + book_notch → notch(east)
def b76(pid, v):
    w,d,h = (1.0, 1.0, 1.0)  # block
    ratio = 0.25 + v*0.05
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        book_notch_node("notch0", "m0", axis="z", corner="nw",
                        outward_sign=1.0, ratio=ratio),
        notch_node("result", "notch0", side="east", corner="ne",
                   ratio=0.28+v*0.04, width_ratio=0.36, height_ratio=0.55),
    ]
    return mkprog(pid, v, "eighth_notch_entry", "cube", "block",
                  ["notch","vertical","eighth_fraction"],
                  "Eighth block corner-notched; east notch as minimal civic entry articulation.",
                  nodes, "result", storeys=4, target_gfa=900)

# PATH 77: 1/8 vertical bend+bend → bar + bend×2 → carve_void(east)
def b77(pid, v):
    w,d,h = (2.8, 0.62, 0.48)  # bar
    angle1 = 22 + v*8
    angle2 = -16 - v*6
    nodes = [
        box_node("box0", w, d, h),
        mat4_node("m0", "box0", scale_mat4(0.55, 0.55, 1.0)),
        bend_node("bend0", "m0", axis="z", angle=angle1, subdivisions=4),
        bend_node("bend1", "bend0", axis="y", angle=angle2, subdivisions=4),
        carve_void_node("result", "bend1", margin=0.22+v*0.03, open_side="east"),
    ]
    return mkprog(pid, v, "eighth_double_bent_carve", "cube", "bar",
                  ["bend","vertical","eighth_fraction","carve_void"],
                  "Eighth bar double-bent in two axes; east carve void at the curved civic face.",
                  nodes, "result", storeys=4, target_gfa=960)
