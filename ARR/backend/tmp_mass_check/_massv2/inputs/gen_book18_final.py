# -*- coding: utf-8 -*-
"""
gen_book18_final.py
120-program BOOK generator for cycle-comp18.
Fixes importer violations:
  1. All compositions produce ONE connected solid:
     - REMOVED: related_array, offset_related, mirror_array, nested_related
       (these spread copies apart → disconnected)
     - KEPT: interlock_related (crossing bodies share material),
             overlap_related (bodies overlap in space),
             intersect_related (intersection = single connected solid),
             shift_related (split halves hinged),
             join_related (explicit bridge connector),
             book_branch (arm stays attached to trunk),
             split_wing with bridge=True (bridge connects the wings)
  2. base_seed matches the scale node proportions:
     - SLAB  scale=(2.2, 1.45, 0.28)
     - BAR   scale=(2.8, 0.62, 0.48)
     - BLOCK scale=(1.0,  1.0,  1.0)
     - TOWER scale=(0.68, 0.68, 2.5)
  3. Parameter format matches schema (additionalProperties:false):
     - number params: {name, value_type:"number", numeric_value}
     - string params: {name, value_type:"string", string_value}
     - boolean params: {name, value_type:"boolean", boolean_value}
     - vector params: {name, value_type:"vector", vector_value:[...]}
     - matrix4 params: {name, value_type:"matrix4", matrix4_value:[[...]]}
     - literal params: {name, value_type:"number", numeric_value} (schema has no 'literal')
"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

try:
    from jsonschema import Draft7Validator
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False

SCHEMA_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json"
OUTPUT_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json"

# ── parameter constructors (match schema exactly) ────────────────────────────
def NP(name, val):
    return {"name": name, "value_type": "number", "numeric_value": float(val)}
def SP(name, val):
    return {"name": name, "value_type": "string", "string_value": str(val)}
def BP(name, val):
    return {"name": name, "value_type": "boolean", "boolean_value": bool(val)}
def VP(name, val):
    return {"name": name, "value_type": "vector", "vector_value": list(val)}
def MP(m):  # matrix4 param
    return {"name": "matrix4", "value_type": "matrix4", "matrix4_value": m}
def LP(name, val):  # literal param - requires ALL 5 value fields, structured_json is a string "null"
    return {"name": name, "value_type": "number", "numeric_value": float(val),
            "string_value": "", "boolean_value": False, "vector_value": [], "structured_json": "null"}

def N(id_, kind, op, inputs, params, role):
    return {"id": id_, "kind": kind, "operator": op, "inputs": inputs,
            "parameters": params, "semantic_role": role}

# ── seed scale vectors ────────────────────────────────────────────────────────
def I(): return [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
# Scale node is the importer's seed detector - must match declared seed exactly
SLAB_SCALE  = [2.2, 1.45, 0.28]
BAR_SCALE   = [2.8, 0.62, 0.48]
BLOCK_SCALE = [1.0,  1.0,  1.0]
TOWER_SCALE = [0.68, 0.68, 2.5]

# ── primitive nodes ───────────────────────────────────────────────────────────
def box(id_, w=1.0, d=1.0, h=1.0, role="dominant_mass"):
    return N(id_,"primitive","box",[],[
        NP("width",w), NP("depth",d), NP("height",h),
        BP("center",True)
    ],role)

def scale(id_, inp, sv, role="dominant_mass"):
    return N(id_,"transform","scale",[inp],[
        VP("vector", sv)
    ],role)

def m4(id_, inp, m=None, role="dominant_mass"):
    if m is None: m = I()
    return N(id_,"transform","matrix4",[inp],[MP(m)],role)

# ── deformation nodes ─────────────────────────────────────────────────────────
def bend(id_, inp, axis, deg, subs=4, role="dominant_mass"):
    return N(id_,"modifier","bend",[inp],[
        SP("axis",axis), NP("angle_degrees",deg), NP("subdivisions",subs)
    ],role)

def taper(id_, inp, axis, es, ss=None, subs=3, role="dominant_mass"):
    if ss is None: ss=[1.0,1.0]
    return N(id_,"modifier","taper",[inp],[
        SP("axis",axis), VP("end_scale",es), VP("start_scale",ss), NP("subdivisions",subs)
    ],role)

def twist(id_, inp, axis, deg, subs=4, role="dominant_mass"):
    return N(id_,"modifier","twist",[inp],[
        SP("axis",axis), NP("angle_degrees",deg), NP("subdivisions",subs)
    ],role)

def shear(id_, inp, axis, amt, role="dominant_mass"):
    return N(id_,"transform","shear",[inp],[
        NP("amount",amt), SP("axis",axis),
        # direction is literal type - use number with all-zero numeric value
        {"name":"direction","value_type":"number",
         "numeric_value":0.0,"string_value":"","boolean_value":False,
         "vector_value":[],"structured_json":"null"}
    ],role)

def inflate(id_, inp, axis, fac, ms, subs=4, role="dominant_mass"):
    return N(id_,"modifier","inflate",[inp],[
        SP("axis",axis), LP("factor",fac), LP("middle_scale",ms), NP("subdivisions",subs)
    ],role)

def pinch(id_, inp, axis, wr, pp=2.0, subs=4, role="dominant_mass"):
    return N(id_,"modifier","pinch",[inp],[
        SP("axis",axis), LP("waist_ratio",wr), LP("profile_power",pp), NP("subdivisions",subs)
    ],role)

def clip_frac(id_, inp, axis, frac, anchor="high", role="dominant_mass"):
    return N(id_,"modifier","clip_fraction",[inp],[
        SP("axis",axis), LP("fraction",frac), SP("anchor",anchor)
    ],role)

def cut_corner(id_, inp, corner, ratio, role="dominant_mass"):
    return N(id_,"modifier","cut_corner",[inp],[
        SP("corner",corner), NP("ratio",ratio)
    ],role)

# ── access / threshold nodes ──────────────────────────────────────────────────
def courtyard(id_, inp, mr, os="east", role="public_threshold"):
    return N(id_,"macro","courtyard",[inp],[
        NP("margin_ratio",mr), SP("open_side",os)
    ],role)

def carve_void(id_, inp, mr, os="east", role="public_threshold"):
    return N(id_,"macro","carve_void",[inp],[
        NP("margin_ratio",mr), SP("open_side",os)
    ],role)

def notch(id_, inp, side, corner, ratio, wr, hr, role="public_threshold"):
    return N(id_,"macro","notch",[inp],[
        SP("side",side), SP("corner",corner),
        NP("ratio",ratio), NP("width_ratio",wr), NP("height_ratio",hr)
    ],role)

def lift_acc(id_, inp, acc="east", rr=0.30, sr=0.25, role="public_threshold"):
    return N(id_,"macro","lift",[inp],[
        SP("access_side",acc), LP("rise_ratio",rr), LP("support_ratio",sr)
    ],role)

def split_wing(id_, inp, axis, layout, gr, hr, acc_s,
               bridge=True, cwr=0.25, gs=False, gshr=0.2, gswr=0.2,
               role="public_threshold"):
    return N(id_,"macro","split_wing",[inp],[
        SP("axis",axis), SP("layout",layout),
        NP("gap_ratio",gr), NP("height_ratio",hr),
        SP("access_side",acc_s), BP("bridge",bridge),
        LP("connector_width_ratio",cwr),
        BP("ground_spine",gs), LP("ground_spine_height_ratio",gshr),
        LP("ground_spine_width_ratio",gswr)
    ],role)

# ── BOOK macro nodes ──────────────────────────────────────────────────────────
def bexpand(id_, inp, axis, amt, sf, role="dominant_mass"):
    return N(id_,"macro","boundary_expand",[inp],[
        SP("axis",axis), NP("amount",amt), LP("shoulder_fraction",sf)
    ],role)

def bnotch(id_, inp, axis, corner, ratio, role="dominant_mass"):
    return N(id_,"macro","book_notch",[inp],[
        SP("axis",axis), SP("corner",corner),
        NP("ratio",ratio), LP("outward_sign",1.0)
    ],role)

def bcarve(id_, inp, axis, fs, dr, wr, role="dominant_mass"):
    return N(id_,"macro","book_carve",[inp],[
        SP("axis",axis), SP("face_side",fs),
        LP("depth_ratio",dr), NP("width_ratio",wr),
        LP("outward_sign",1.0)
    ],role)

def bfrac(id_, inp, axis, gr, deg, rbr, role="dominant_mass"):
    return N(id_,"macro","book_fracture",[inp],[
        SP("axis",axis), NP("gap_ratio",gr), NP("angle_degrees",deg),
        LP("retained_back_ratio",rbr), LP("outward_sign",1.0)
    ],role)

def bextract(id_, inp, axis, fs, dr, gs, role="dominant_mass"):
    return N(id_,"macro","book_extract",[inp],[
        SP("axis",axis), SP("face_side",fs),
        LP("distance_ratio",dr), LP("guest_scale",gs),
        LP("outward_sign",1.0)
    ],role)

def blift(id_, inp, axis, dr, gs, role="dominant_mass"):
    return N(id_,"macro","book_lift",[inp],[
        SP("axis",axis), LP("distance_ratio",dr),
        LP("guest_scale",gs), LP("outward_sign",1.0)
    ],role)

def blodge(id_, inp, axis, dr, gs, role="dominant_mass"):
    return N(id_,"macro","book_lodge",[inp],[
        SP("axis",axis), LP("distance_ratio",dr),
        LP("guest_scale",gs), LP("outward_sign",1.0)
    ],role)

def bbranch(id_, inp, deg, tr, ar, va="input_base", role="dominant_mass"):
    return N(id_,"macro","book_branch",[inp],[
        NP("angle_degrees",deg), LP("trunk_ratio",tr),
        LP("arm_ratio",ar), SP("vertical_anchor",va)
    ],role)

def bsplit(id_, inp, axis, gr, deg, bsign, sgen, tr, role="dominant_mass"):
    """book_split - keeps connected (split halves stay hinged at generation 1)"""
    return N(id_,"macro","book_split",[inp],[
        SP("axis",axis), NP("gap_ratio",gr), NP("angle_degrees",deg),
        LP("branch_sign",bsign), LP("split_generation",sgen),
        LP("terminal_ratio",tr), LP("outward_sign",1.0),
        LP("access_side",0.0)
    ],role)

def brotate(id_, inp, axis, deg, rr, role="dominant_mass"):
    return N(id_,"macro","book_rotate",[inp],[
        SP("axis",axis), NP("angle_degrees",deg),
        LP("related_ratio",rr), LP("outward_sign",1.0)
    ],role)

def bgrade(id_, inp, axis, fs, dr, wr, levels=3, role="dominant_mass"):
    return N(id_,"macro","book_grade",[inp],[
        SP("axis",axis), SP("face_side",fs),
        LP("depth_ratio",dr), NP("width_ratio",wr),
        NP("levels",levels), LP("outward_sign",1.0)
    ],role)

# ── CONNECTED related operators ───────────────────────────────────────────────
def interlock(id_, inp, axis, deg, br, dr, role="dominant_mass"):
    """Crossing bodies share material zone → one connected solid"""
    return N(id_,"macro","interlock_related",[inp],[
        SP("axis",axis), NP("angle_degrees",deg),
        LP("bar_ratio",br), LP("distance_ratio",dr),
        LP("outward_sign",1.0)
    ],role)

def intersect_rel(id_, inp, axis, deg, br, us, role="dominant_mass"):
    """Intersection produces a single volume → connected"""
    return N(id_,"macro","intersect_related",[inp],[
        SP("axis",axis), NP("angle_degrees",deg),
        LP("bar_ratio",br), LP("unit_scale",us)
    ],role)

def overlap_rel(id_, inp, axis, sr, shR, vo, role="dominant_mass"):
    """Overlapping bodies stay physically joined at overlap zone → connected"""
    return N(id_,"macro","overlap_related",[inp],[
        SP("axis",axis), LP("slab_ratio",sr),
        LP("shift_ratio",shR), LP("vertical_overlap",vo),
        LP("outward_sign",1.0)
    ],role)

def join_related(id_, inp, br, role="dominant_mass"):
    """Explicit bridge connector → one connected solid"""
    return N(id_,"macro","join_related",[inp],[
        LP("bridge_ratio",br)
    ],role)

def shift_related(id_, inp, axis, dr, sr, role="dominant_mass"):
    """Split halves shift but remain hinged → connected"""
    return N(id_,"macro","shift_related",[inp],[
        SP("axis",axis), LP("distance_ratio",dr),
        LP("split_ratio",sr), LP("outward_sign",1.0)
    ],role)

def embed_void(id_, inp, axis, pos, er, gs, role="dominant_mass"):
    """Void carved into a single body → connected"""
    return N(id_,"macro","embed_void",[inp],[
        SP("axis",axis), SP("position",pos),
        LP("embedded_ratio",er), LP("guest_scale",gs),
        LP("outward_sign",1.0)
    ],role)

# ── dimensional intent ────────────────────────────────────────────────────────
def dim_intent(storeys=4, storey_h=3.5, gfa=None):
    if gfa is None: gfa = storeys * 300.0
    return {"schema_version": "arr.maas.dimensional_intent.v1",
            "storey_count": storeys, "storey_height_m": storey_h,
            "target_gfa_m2": float(gfa),
            "delivery_policy": "preserve_physical_dimensions",
            "programme_status": "unknown"}

def mkprog(pid, name, seed, nodes, root, tags, rationale,
           storeys=4, storey_h=3.5, gfa=None, base_form="cube"):
    if gfa is None: gfa = storeys * 300.0
    return {"book_composition_path_id": pid,
            "name": name,
            "base_form_id": base_form,
            "base_seed": seed,
            "intent_tags": tags[:12],
            "nodes": nodes,
            "root_id": root,
            "rationale": rationale,
            "dimensional_intent": dim_intent(storeys, storey_h, gfa)}

# ── 78 path IDs ───────────────────────────────────────────────────────────────
PATH_IDS = [
    "book:path:9bab887f2e519077dcbe8e5977897df8a80deb6d1a280936cccca005d8555719",  # 0
    "book:path:9042c82e97a383fc1f1e97948ac87e0bac17a95d0d8587255d48710c0ac64040",  # 1
    "book:path:11a0d7a5a51e85d9ec1cf2f3b3eaa086eb6841d1fec6a184077cc5db1851b185",  # 2
    "book:path:dd28b0c53f08a2d1812dc32d7b562ee9b7bc4a1ca98b90a13152bbf534dd27f2",  # 3
    "book:path:c7fcd0c126b7b32471e69e703e7e9022ab3963899ef974c879ec44b4162b197a",  # 4
    "book:path:b95277004fb2b89b21445182aab353c444a4ea7a1e7044f8c2e7e07599226909",  # 5
    "book:path:6bb95e7e0461e1606d4430a1e8a7c4ad2b3dc96d74ff48bced73da05b9df6cf5",  # 6
    "book:path:2f971be29f0d428a9879b1c00948ac738f8921db4163797414074d894ac8efb9",  # 7
    "book:path:e510ad256385b556152790586ff8d15493cf9c1d6cffbd352f8e0d326c4ca71a",  # 8
    "book:path:53c55b4da48903af110459fa120baeaec3b186edf22d6890fa718d0ad6b1f5b5",  # 9
    "book:path:f285f713076b19ee7cc1b58f2d44f85aeec8a11bfe30fc0b77e876a1543a612b",  # 10
    "book:path:05470e618703ead632e6029bac7312306f05a6f404cb1a84f60043e0fb2b6b5f",  # 11
    "book:path:ff644fb6db1684200f7c558764b8298c45bab946fac40c3df9cc090edf479977",  # 12
    "book:path:61ddaacb14d1ebd0e0c24518a19a9b01f9a48f50fbfd66fd280b92abe59722b7",  # 13
    "book:path:2e2f65a3f44c510ecfa66c729db4c53684b3cc4033f5844bc980f4fa4bf1ad70",  # 14
    "book:path:aadaf4340a4980ec0c691cf6c70bf78936b4b4b1471a6340d384abcae9ee0a2c",  # 15
    "book:path:2e24111503e808e954bf437374af114ede99fddb568beab59253edb011273835",  # 16
    "book:path:84d0345cadb3c43a13aa423bc1fddfb175b338b095c86bc9ec4b1eab2952afd0",  # 17
    "book:path:b96fa24e6b07a0419331b82a471addcf0f980f71d6fee1bffd80a5e1ed1ea126",  # 18
    "book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e",  # 19
    "book:path:2fcf5f31e6d7ec9acbe02f9c3a6bb20e72df122cf29d989dd630f4d7fc022791",  # 20
    "book:path:423e633a08a43369b6ccda29d5604fc061c6e20e52e460c9867ddd1e5b13c2c0",  # 21
    "book:path:6acac573694cb27de1572fd0a9de5fb76aed871fea929c88573a072c95a8bbbb",  # 22
    "book:path:1dbb96b395ddd04b17719976be7a62b1bdb6256f080c74a7b0de12c908a7915c",  # 23
    "book:path:f91a61a346c29c85aa4907c5e5c53d10e00a7530d28316c598fcc29d75f7fb55",  # 24
    "book:path:13fbf6da4b2addf28d4678956f747d8f112740ed2ca07de19e7a4884b2d43956",  # 25
    "book:path:4542c2a1884b1b256fbdea6e3ffd434dac31db9212deb3a328bb168fcfc1a6e4",  # 26
    "book:path:e1e90099b5d07535d9361727c7d4b028f702499491b0588fdb2c926912013fb5",  # 27
    "book:path:f7755521cc02b4d565cddffa435faa30d79095ee7d62ce0588cbc8fc33fa2b6f",  # 28
    "book:path:def59b665a24ebd51c08a3812668edc1a6131552a8055b2d7cb88de8de90f4f5",  # 29
    "book:path:3ab1e90c58b2293f63e75df8acabb9308b747cd6304c4511b2a47ed9ce8821c3",  # 30
    "book:path:cfeca7238d109f8ccf184e9ab42319aadf2d36f2aca116ba295ae47cbb6ca11b",  # 31
    "book:path:08e14d9ef6f30e7f2700d6e5f895d4911944adbfd16a0477dbfee0afeebfbf70",  # 32
    "book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb",  # 33
    "book:path:60778ae3e99cf12bb7e8461f50ee3332b7a47ed4893d70cb2d8400fd22cc49cf",  # 34
    "book:path:0b828fd1f09aeb9b5e3096a6cfe15c3cf1d709a475844690e9f3085fbdb9b8b1",  # 35
    "book:path:d2cb499b7d8b00c2ace3d4b6893bc583e2307d3d6cdb0ac96b319253fe0529c4",  # 36
    "book:path:eccfafc4718361d6aec40a901f53b344d4bff77683f4887715da5adcce05157f",  # 37
    "book:path:c15ec55248a4fc32d3f15fea2da9b94c5831c48f2dedecef91ddf03a61f04ef1",  # 38
    "book:path:591a729db54894dfd9449b5e5f08781d509ee6da02353d574828e141854ef1fe",  # 39
    "book:path:a34184c51ffd9faa6f4e694bd0df018b4499f561be4b29d1f086e7b8361fd7b7",  # 40
    "book:path:9c9d6d2d18bf525d39eb0c2299651d643b20f3f3e0de68975addd59e346d58d2",  # 41
    "book:path:82e07b845038d9e2c03a74eab9531bfdb2aaa74dd621e9ab21c72eb467b32bd7",  # 42
    "book:path:716df07ca23e72681a3aca19b6a160a3c867f21315b111d0c6ac21a2700be269",  # 43
    "book:path:7f4ace179d50c15c3a63cd24d5dcb7e3420da79697dcb07afb1a30f73bbed628",  # 44
    "book:path:aec174c38f9ed86be822dd7813012953b17a2443337cd862c35837a7c34ab023",  # 45
    "book:path:4805f5934fe933b3108aeb3a3aa5a567a1a1bd1debe1a625217a979a35f16c24",  # 46
    "book:path:e688a33bce52391b696ecea5bef1c7926ec4e15d1a02971bebfaf8fcb990c13b",  # 47
    "book:path:9ff66e145418829ccc5e710634ec50389ce05bc62f6496984bde22110528e383",  # 48
    "book:path:546119cfb82a276ceee53e1eb09d960d054ff4bacd4853bc824ba6ed9ffd8e8f",  # 49
    "book:path:f1440150bbd785859ef88baca5734f8731b6b029da123797ae55c43541ecb398",  # 50
    "book:path:0bac03a066888497ad4cdc5a727e609bdb620a3ef13ef9cc5394a46de7a09449",  # 51
    "book:path:af83d6add866295511a823d82a17f6d3b2316e11204b251b3c0c6eee90de813f",  # 52
    "book:path:f42375c1818d4ccdef5278032d64aa984e673a76b1e44056b286a08f507288d1",  # 53
    "book:path:89a8d2e071e7dc228815ddab41a199bf7379d5742d861095f20ab2de6fd610f5",  # 54
    "book:path:bbd403cec5ff6827cf04b266a65afdab72752a8071a42a83017b53f878176551",  # 55
    "book:path:b1dc18f7817ae62db7951887748c90355ffaa9ee10880a1dfaad396c8a5e54e0",  # 56
    "book:path:ea3fdbfddf0a32805dc837821770519d713d02a468fa8e914311a1e122289d20",  # 57
    "book:path:0e3fe6f19fe3fb3b4fdfecd76c496e00141469a5ab4be263385f49ea58ce99b5",  # 58
    "book:path:b161eb4c3bb6230cd34980d091fc44bf52f7d2648e59f55b39dc46e64225dc46",  # 59
    "book:path:56f69a2038120b9187f1387efee21a6a63cf530d026b6f10dfab37c2db2dc717",  # 60
    "book:path:dc50b322c264219be6835f6b50fc2a3e5ffba233fd5e5f9fa3813b14d5523193",  # 61
    "book:path:0d5b1e3a233d34e16073c222838ee053eabeb8692327fc62ef668c7b75a716d1",  # 62
    "book:path:bd7cfc87da1811e45875acde3aa82d513fc343204bca6bcd2fb26f3a1d1357e7",  # 63
    "book:path:c58193dcc81b7f6fb8a25fd8bb18808d47ae79a9765ff716fd84b09d1befc70b",  # 64
    "book:path:2e91334e6426f5c7ca6a8f4cfce4ca746f1d0f3091273eaf3896fe4900b3f7bd",  # 65
    "book:path:58d160602ccaafb30f737d33723e43a8ae2841eaac7fda840c8f5d8886775abf",  # 66
    "book:path:150c3892213b9cc014f2985158abc9905f8c9b2cc1c690a1cc7e41068a044a6f",  # 67
    "book:path:a024d86c2d00b3f85de00140e9b221e1e73de64e83a85c58dc4e52ea478988e0",  # 68
    "book:path:a254a71182ed875bbe8102de50270b1e19538916fe00c1a609ea6c5950fbef0b",  # 69
    "book:path:d138480c1ee6ed85eed95f1cfd921852b69d33e8e412f0f28a7c3194117efa38",  # 70
    "book:path:42bc62991fbaf0eaa42d48e37ede8e507613abc648a0e32338a19e19862787e2",  # 71
    "book:path:eee048bfdfa8ab2892e3a8a604bd2a302efd5cb77e995014dc28074c5b3811b4",  # 72
    "book:path:9e4457e0a1cf8fa849c73e92abc08b15423426f4949b6225cab08c1034e531a5",  # 73
    "book:path:71fb46d7af677eb3b5345e94d27f0fa1ef9b257aadc2cd746aec550ba2a0419b",  # 74
    "book:path:dfbf81995ea510ccee2aa31dffbf03a3dd3dfcb167a0153d116724dbf65599f0",  # 75
    "book:path:415615bd85962e057ca3dd17914bf224fa7b6182a09f3f17db371a41b7dcc401",  # 76
    "book:path:a831f22dee8c36e3a70315fa1ff822eff56f7f0deefcfb3032d54fc585e8a128",  # 77
]
assert len(PATH_IDS) == 78

# ── 78 builder functions ──────────────────────────────────────────────────────
# ALL produce ONE connected solid.
# Connectivity guarantees:
#   book_branch: arm stays attached to trunk → connected ✓
#   bsplit: halves stay hinged at generation edge → connected ✓
#   interlock_related: bodies cross each other (shared material) → connected ✓
#   intersect_related: returns intersection solid → single solid ✓
#   overlap_related: bodies overlap in space → connected at overlap ✓
#   shift_related: split halves shift but remain hinged → connected ✓
#   join_related: explicit bridge connector → connected ✓
#   embed_void: void carved in body → single body ✓
#   bcarve/bfrac/blift/blodge/bextract: BOOK ops on single body → connected ✓
#   bnotch/brotate/bgrade/bexpand: BOOK ops on single body → connected ✓
#   split_wing(bridge=True): wings connected via bridge → connected ✓
#   courtyard/carve_void/notch/lift_acc: access ops on single body → connected ✓
#   bend/taper/twist/shear/inflate/pinch/clip_frac: deform single body → connected ✓

def b(pid, name, seed, nodes, root, tags, rationale, s=4, h=3.5, gfa=None, bf="cube"):
    return mkprog(pid, name, seed, nodes, root, tags, rationale, s, h, gfa, bf)

def p00(pid, v):
    # bend: slab bent to curve, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bend("bnd","m0","x",18+v*10,4),
           courtyard("acc","bnd",0.15+v*0.04)]
    return b(pid,f"p00_slab_bend_court_v{v}","slab",nodes,"acc",
             ["bend","courtyard","slab"],"Slab continuously bent; east courtyard below curve.",4,3.5,1100)

def p01(pid, v):
    # fracture: slab with diagonal fissure, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bfrac("frac","m0","z",0.10+v*0.04,12+v*8,0.55+v*0.05),
           carve_void("acc","frac",0.20+v*0.03)]
    return b(pid,f"p01_slab_fracture_carve_v{v}","slab",nodes,"acc",
             ["fracture","carve_void","slab"],"Slab diagonal fracture; east carve void as civic recess.",3,3.5,900)

def p02(pid, v):
    # embed+embed: block with two nested voids, east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           embed_void("emb1","m0","z","east",0.30+v*0.05,0.45+v*0.05),
           embed_void("emb2","emb1","y","center",0.25+v*0.04,0.40+v*0.04),
           notch("acc","emb2","east","ne",0.26+v*0.04,0.38,0.55)]
    return b(pid,f"p02_block_dual_embed_notch_v{v}","block",nodes,"acc",
             ["embed","notch","block"],"Block doubly hollowed with embed voids; east notch entry.",5,3.5,1400)

def p03(pid, v):
    # branch+expand: bar branches then expands, east lift
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bbranch("br0","m0",40+v*15,0.55+v*0.05,0.38+v*0.04),
           bexpand("exp","br0","z",0.18+v*0.04,0.45+v*0.05),
           lift_acc("acc","exp")]
    return b(pid,f"p03_bar_branch_expand_lift_v{v}","bar",nodes,"acc",
             ["branch","expand","lift","bar"],"Bar branched and shoulder-expanded; east lift opens passage.",4,3.5,1200)

def p04(pid, v):
    # carve+offset: slab dual-carved (east+south face), east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bcarve("cv1","m0","z","east",0.25+v*0.05,0.40+v*0.05),
           bcarve("cv2","cv1","z","south",0.20+v*0.04,0.35+v*0.04),
           notch("acc","cv2","east","se",0.25+v*0.03,0.35,0.55)]
    return b(pid,f"p04_slab_dual_carved_notch_v{v}","slab",nodes,"acc",
             ["carve","notch","slab"],"Slab carved east and south; SE notch gives corner civic address.",4,3.5,1000)

def p05(pid, v):
    # branch: bar Y-branch, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bbranch("br0","m0",60+v*20,0.58+v*0.05,0.35+v*0.05),
           courtyard("acc","br0",0.24+v*0.03)]
    return b(pid,f"p05_bar_ybranch_court_v{v}","bar",nodes,"acc",
             ["branch","courtyard","bar"],"Bar Y-branch; east courtyard opens at fork.",4,3.5,1150)

def p06(pid, v):
    # rotate: slab with rotated child, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           brotate("rot","m0","z",25+v*10,0.45+v*0.06),
           carve_void("acc","rot",0.22+v*0.03)]
    return b(pid,f"p06_block_rotate_carve_v{v}","block",nodes,"acc",
             ["rotate","carve_void","block"],"Block with rotated child volume; east carve void marks entry.",3,3.5,870)

def p07(pid, v):
    # inscribe: block corner-notched (book_notch as inscribed void), east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","sw",0.22+v*0.05),
           carve_void("acc","bnt",0.22+v*0.03)]
    return b(pid,f"p07_block_inscribed_carve_v{v}","block",nodes,"acc",
             ["inscribe","carve_void","block"],"Block inscribed with SW corner notch; east carve delivers entry.",4,3.5,1050)

def p08(pid, v):
    # intersect+split: bar cross-intersected (connected intersection) then split+lift
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           intersect_rel("int","m0","z",90.0,0.38+v*0.05,0.75+v*0.05),
           bsplit("sp","int","y",0.10+v*0.04,0.0,1.0,1.0,0.48+v*0.04),
           lift_acc("acc","sp")]
    return b(pid,f"p08_bar_intersect_split_lift_v{v}","bar",nodes,"acc",
             ["intersect","split","lift","bar"],"Cross intersection then split; east lift opens piloti threshold.",4,3.5,1100)

def p09(pid, v):
    # bend+stack (stack with small shift, not separate): slab bent and stacked
    # Use bsplit instead of related_array to stay connected
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bend("bnd","m0","y",18+v*7,4),
           bsplit("sp","bnd","y",0.04+v*0.01,0.0,1.0,1.0,0.5),
           notch("acc","sp","east","ne",0.22+v*0.04,0.36,0.55)]
    return b(pid,f"p09_slab_bend_split_notch_v{v}","slab",nodes,"acc",
             ["bend","split","notch","slab"],"Slab bent then split (hinged); east notch articulates entry.",3+v,3.5,950+v*150)

def p10(pid, v):
    # lift+extrude: block book_lifted then wing-split with bridge
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           blift("bl","m0","z",0.28+v*0.05,0.55+v*0.05),
           split_wing("acc","bl","y","parallel",0.12+v*0.02,0.85+v*0.05,"east",True,0.28+v*0.03,False,0.15,0.2)]
    return b(pid,f"p10_block_lift_wing_v{v}","block",nodes,"acc",
             ["lift","split_wing","block"],"Block book-lifted and wing-split; bridge=True ensures solid.",4,3.5,1200)

def p11(pid, v):
    # interlock: bar interlocked (crossing → connected), east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           interlock("int","m0","x",0.0,0.38+v*0.04,0.45+v*0.05),
           courtyard("acc","int",0.22+v*0.03)]
    return b(pid,f"p11_bar_interlock_court_v{v}","bar",nodes,"acc",
             ["interlock","courtyard","bar"],"Interlocked L-volumes share material zone; east court organizes entry.",4,3.5,1100)

def p12(pid, v):
    # shear: tower sheared obliquely, east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",TOWER_SCALE), m4("m0","s0"),
           shear("shr","m0","z",0.25+v*0.06),
           notch("acc","shr","east","ne",0.28+v*0.04,0.38,0.6)]
    return b(pid,f"p12_tower_shear_notch_v{v}","tower",nodes,"acc",
             ["shear","notch","tower"],"Tower sheared obliquely; east notch frames civic entry recess.",5,3.5,1300)

def p13(pid, v):
    # expand+expand: block double-expanded, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bexpand("ex1","m0","z",0.20+v*0.05,0.40+v*0.06),
           bexpand("ex2","ex1","y",0.15+v*0.04,0.55+v*0.04),
           carve_void("acc","ex2",0.22+v*0.03)]
    return b(pid,f"p13_block_double_expand_carve_v{v}","block",nodes,"acc",
             ["expand","carve_void","block"],"Block double shoulder-expanded; east carve opens through face.",4,3.5,1200)

def p14(pid, v):
    # expand+reflect: slab expanded then overlap (connected), east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bexpand("ex","m0","z",0.22+v*0.05,0.5+v*0.04),
           overlap_rel("ovl","ex","y",0.60+v*0.04,0.28+v*0.04,0.35+v*0.04),
           courtyard("acc","ovl",0.24+v*0.03)]
    return b(pid,f"p14_slab_expand_overlap_court_v{v}","slab",nodes,"acc",
             ["expand","overlap","courtyard","slab"],"Expanded slab overlapped (connected); east court as gateway.",4,3.5,1100)

def p15(pid, v):
    # overlap+expand: bar overlapped then expanded, east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           overlap_rel("ovl","m0","x",0.58+v*0.04,0.32+v*0.04,0.25+v*0.04),
           bexpand("ex","ovl","z",0.18+v*0.04,0.48+v*0.04),
           notch("acc","ex","east","ne",0.25+v*0.04,0.38,0.55)]
    return b(pid,f"p15_bar_overlap_expand_notch_v{v}","bar",nodes,"acc",
             ["overlap","expand","notch","bar"],"Overlapping bars expand shoulder; east notch addresses corner.",4,3.5,1150)

def p16(pid, v):
    # bend: slab bent (3/8 variant), east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bend("bnd","m0","z",30+v*10,4),
           carve_void("acc","bnd",0.22+v*0.04)]
    return b(pid,f"p16_slab_bend_z_carve_v{v}","slab",nodes,"acc",
             ["bend","carve_void","slab"],"Slab bent in plan; east carve void as civic approach.",3,3.5,800)

def p17(pid, v):
    # fracture: bar fracture then twist, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bfrac("frac","m0","z",0.11+v*0.04,18+v*10,0.58+v*0.04),
           twist("twst","frac","z",15+v*6,4),
           carve_void("acc","twst",0.22+v*0.03)]
    return b(pid,f"p17_bar_fracture_twist_carve_v{v}","bar",nodes,"acc",
             ["fracture","twist","carve_void","bar"],"Bar fractured and twisted; east carve in distorted civic face.",4,3.5,1050)

def p18(pid, v):
    # split+split: bar double-split (hinged at each generation), east split_wing
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bsplit("sp1","m0","y",0.08+v*0.03,0.0,1.0,1.0,0.45+v*0.05),
           bsplit("sp2","sp1","x",0.10+v*0.03,5.0+v*5,-1.0,2.0,0.5),
           split_wing("acc","sp2","y","parallel",0.12+v*0.02,0.88+v*0.04,"east",True,0.25+v*0.03,False,0.15,0.2)]
    return b(pid,f"p18_bar_double_split_wing_v{v}","bar",nodes,"acc",
             ["split","split_wing","bar"],"Double split displaces bar; east split_wing with bridge spans gap.",4,3.5,1100)

def p19(pid, v):
    # bend+branch: bar bent then branched, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bend("bnd","m0","z",20+v*8,4),
           bbranch("br","bnd",50+v*10,0.60+v*0.04,0.36+v*0.04),
           carve_void("acc","br",0.22+v*0.03)]
    return b(pid,f"p19_bar_bend_branch_carve_v{v}","bar",nodes,"acc",
             ["bend","branch","carve_void","bar"],"Bent bar then branched; east carve in curved civic face.",4,3.5,1100)

def p20(pid, v):
    # split+join: bar split then joined via bridge (one solid), east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bsplit("sp","m0","y",0.09+v*0.03,0.0,1.0,1.0,0.5),
           join_related("jn","sp",0.28+v*0.05),
           carve_void("acc","jn",0.22+v*0.03)]
    return b(pid,f"p20_bar_split_join_carve_v{v}","bar",nodes,"acc",
             ["split","join","carve_void","bar"],"Split halves bridge-joined (one solid); east carve delivers gateway.",4,3.5,1000)

def p21(pid, v):
    # inflate: slab inflated at crown, east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           inflate("infl","m0","z",1.12+v*0.06,1.18+v*0.05,4),
           notch("acc","infl","east","ne",0.25+v*0.04,0.38,0.55)]
    return b(pid,f"p21_slab_inflated_notch_v{v}","slab",nodes,"acc",
             ["inflate","notch","slab"],"Slab inflated at crown; east notch indents billowing face for entry.",3,3.5,820)

def p22(pid, v):
    # overlap: bar overlapped (connected at overlap zone), east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           overlap_rel("ovl","m0","y",0.62+v*0.04,0.30+v*0.04,0.22+v*0.04),
           courtyard("acc","ovl",0.20+v*0.04)]
    return b(pid,f"p22_bar_overlap_court_v{v}","bar",nodes,"acc",
             ["overlap","courtyard","bar"],"Two overlapping bars (connected at zone); east courtyard in overlap.",4,3.5,1050)

def p23(pid, v):
    # inscribe: block NW corner notch, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","nw",0.25+v*0.05),
           carve_void("acc","bnt",0.22+v*0.03)]
    return b(pid,f"p23_block_inscribed_nw_carve_v{v}","block",nodes,"acc",
             ["inscribe","carve_void","block"],"NW corner notch inscribed into block; east carve void defines civic face.",3,3.5,870)

def p24(pid, v):
    # intersect+split: bar cross-intersected then split
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           intersect_rel("int","m0","z",90.0,0.36+v*0.05,0.78+v*0.04),
           bsplit("sp","int","x",0.09+v*0.03,0.0,1.0,1.0,0.5),
           lift_acc("acc","sp")]
    return b(pid,f"p24_bar_intersect_split_lift_v{v}","bar",nodes,"acc",
             ["intersect","split","lift","bar"],"Cross intersection → connected solid; split+east lift as passage.",4,3.5,1100)

def p25(pid, v):
    # bend+stack: slab bent, bsplit keeps connected
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bend("bnd","m0","y",20+v*8,4),
           bsplit("sp","bnd","x",0.04+v*0.01,0.0,1.0,1.0,0.5),
           courtyard("acc","sp",0.20+v*0.04)]
    return b(pid,f"p25_slab_bend_split_court_v{v}","slab",nodes,"acc",
             ["bend","split","courtyard","slab"],"Bent slab split (hinged); east courtyard as threshold.",3+v,3.5,880+v*150)

def p26(pid, v):
    # lift+extrude: block book_lifted then wing-split
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           blift("bl","m0","z",0.25+v*0.05,0.58+v*0.04),
           split_wing("acc","bl","y","parallel",0.12+v*0.03,0.88+v*0.04,"east",True,0.25+v*0.03,False,0.15,0.2)]
    return b(pid,f"p26_block_blift_wing_v{v}","block",nodes,"acc",
             ["lift","split_wing","block"],"Block lifted; wing-split with bridge ensures connected solid.",4,3.5,1050)

def p27(pid, v):
    # interlock: bar interlocked angled (crossing), east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           interlock("int","m0","x",5.0+v*5,0.40+v*0.04,0.42+v*0.05),
           courtyard("acc","int",0.22+v*0.03)]
    return b(pid,f"p27_bar_interlock_angled_court_v{v}","bar",nodes,"acc",
             ["interlock","courtyard","bar"],"Interlocking L-bar pair (angled); east courtyard mediates civic face.",4,3.5,1000)

def p28(pid, v):
    # shear: tower sheared (y-direction), east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",TOWER_SCALE), m4("m0","s0"),
           shear("shr","m0","z",0.28+v*0.06),
           notch("acc","shr","east","ne",0.26+v*0.04,0.36,0.58)]
    return b(pid,f"p28_tower_shear_y_notch_v{v}","tower",nodes,"acc",
             ["shear","notch","tower"],"Tower sheared; east notch creates angled entry recess.",5,3.5,1200)

def p29(pid, v):
    # branch+branch: bar double branched (each arm stays connected to trunk)
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bbranch("br1","m0",45+v*12,0.55+v*0.05,0.36+v*0.04),
           bbranch("br2","br1",-30-v*8,0.60+v*0.04,0.32+v*0.04),
           carve_void("acc","br2",0.20+v*0.03)]
    return b(pid,f"p29_bar_double_branch_carve_v{v}","bar",nodes,"acc",
             ["branch","carve_void","bar"],"Double branching (each arm stays connected); east carve void.",4,3.5,1100)

def p30(pid, v):
    # notch+twist: block corner-notched then twisted
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","nw",0.22+v*0.05),
           twist("twst","bnt","z",18+v*7,4),
           notch("acc","twst","east","ne",0.26+v*0.04,0.36,0.55)]
    return b(pid,f"p30_block_notch_twist_entry_v{v}","block",nodes,"acc",
             ["notch","twist","block"],"Block notched then twisted; east notch marks rotated civic face.",4,3.5,950)

def p31(pid, v):
    # expand+nest: slab expanded then lodge (connected nest equivalent)
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bexpand("ex","m0","z",0.20+v*0.05,0.45+v*0.05),
           blodge("ld","ex","z",0.28+v*0.04,0.65+v*0.05),
           carve_void("acc","ld",0.22+v*0.03)]
    return b(pid,f"p31_slab_expand_lodge_carve_v{v}","slab",nodes,"acc",
             ["expand","nest","carve_void","slab"],"Expanded slab with lodged inner volume; east carve opens face.",3,3.5,900)

def p32(pid, v):
    # offset: slab east-extracted (offset operative), east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bextract("ext","m0","z","north",0.35+v*0.05,0.55+v*0.05),
           carve_void("acc","ext",0.22+v*0.03)]
    return b(pid,f"p32_slab_extract_carve_v{v}","slab",nodes,"acc",
             ["offset","carve_void","slab"],"Slab with north extraction (offset); east carve as civic lobby.",4,3.5,1050)

def p33(pid, v):
    # compress: block clip_fraction (compress), east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           clip_frac("cl","m0","z",0.72+v*0.05),
           notch("acc","cl","east","ne",0.28+v*0.04,0.38,0.55)]
    return b(pid,f"p33_block_compress_notch_v{v}","block",nodes,"acc",
             ["compress","notch","block"],"Block vertically clipped (compressed); east notch entry.",3,3.5,820)

def p34(pid, v):
    # split+split: bar double-split
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bsplit("sp1","m0","y",0.09+v*0.03,0.0,1.0,1.0,0.48+v*0.04),
           bsplit("sp2","sp1","x",0.10+v*0.03,4.0+v*4,-1.0,2.0,0.5),
           carve_void("acc","sp2",0.22+v*0.03)]
    return b(pid,f"p34_bar_double_split_carve_v{v}","bar",nodes,"acc",
             ["split","carve_void","bar"],"Double split displaces bar; east carve addresses public side.",4,3.5,980)

def p35(pid, v):
    # bend+branch: bar bent then branched, east lift
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bend("bnd","m0","z",22+v*8,4),
           bbranch("br","bnd",48+v*10,0.58+v*0.04,0.35+v*0.04),
           lift_acc("acc","br")]
    return b(pid,f"p35_bar_bent_branch_lift_v{v}","bar",nodes,"acc",
             ["bend","branch","lift","bar"],"Bar bent and branched; east lift opens ground passage below arms.",4,3.5,1080)

def p36(pid, v):
    # split+join: block split then join_related, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bsplit("sp","m0","y",0.09+v*0.03,0.0,1.0,1.0,0.50),
           join_related("jn","sp",0.30+v*0.04),
           courtyard("acc","jn",0.22+v*0.03)]
    return b(pid,f"p36_block_split_join_court_v{v}","block",nodes,"acc",
             ["split","join","courtyard","block"],"Split halves bridged (join_related); east courtyard in gateway slot.",4,3.5,1000)

def p37(pid, v):
    # inflate: slab inflated at crown, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           inflate("infl","m0","z",1.14+v*0.06,1.20+v*0.05,4),
           courtyard("acc","infl",0.22+v*0.03)]
    return b(pid,f"p37_slab_inflated_court_v{v}","slab",nodes,"acc",
             ["inflate","courtyard","slab"],"Slab inflated at crown; east courtyard as civic concavity.",3,3.5,820)

def p38(pid, v):
    # overlap: bar overlapped (connected), east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           overlap_rel("ovl","m0","y",0.60+v*0.04,0.32+v*0.04,0.24+v*0.04),
           notch("acc","ovl","east","ne",0.26+v*0.03,0.36,0.55)]
    return b(pid,f"p38_bar_overlap_notch_v{v}","bar",nodes,"acc",
             ["overlap","notch","bar"],"Overlapping bars (connected); east notch addresses junction.",4,3.5,980)

def p39(pid, v):
    # inscribe: block SW notch, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","sw",0.24+v*0.05),
           carve_void("acc","bnt",0.22+v*0.03)]
    return b(pid,f"p39_block_inscribed_sw_carve_v{v}","block",nodes,"acc",
             ["inscribe","carve_void","block"],"SW notch inscribed into block; east carve as principal address.",3,3.5,840)

def p40(pid, v):
    # inscribe+intersect: bar corner-notched then intersected (intersection → connected solid)
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","se",0.22+v*0.04),
           intersect_rel("int","bnt","z",90.0,0.38+v*0.04,0.78+v*0.04),
           lift_acc("acc","int")]
    return b(pid,f"p40_bar_inscribe_intersect_lift_v{v}","bar",nodes,"acc",
             ["inscribe","intersect","lift","bar"],"Notched bar cross-intersected (intersection solid); east lift.",4,3.5,1050)

def p41(pid, v):
    # branch+pack: bar branched then overlap (connected)
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bbranch("br","m0",50+v*15,0.58+v*0.04,0.36+v*0.04),
           overlap_rel("ovl","br","x",0.62+v*0.04,0.25+v*0.04,0.30+v*0.04),
           courtyard("acc","ovl",0.20+v*0.03)]
    return b(pid,f"p41_bar_branch_overlap_court_v{v}","bar",nodes,"acc",
             ["branch","overlap","courtyard","bar"],"Branched bar with overlapping (connected) arrangement; east court.",4,3.5,1100)

def p42(pid, v):
    # lift+carve: block lifted then carved east, split_wing
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           blift("bl","m0","z",0.26+v*0.05,0.58+v*0.04),
           bcarve("cv","bl","z","east",0.28+v*0.04,0.42+v*0.04),
           split_wing("acc","cv","y","parallel",0.12+v*0.02,0.88+v*0.04,"east",True,0.26+v*0.03,False,0.15,0.2)]
    return b(pid,f"p42_block_lift_carve_wing_v{v}","block",nodes,"acc",
             ["lift","carve","split_wing","block"],"Lifted block east-carved; wing-split with bridge spans civic gap.",4,3.5,1050)

def p43(pid, v):
    # twist: tower twisted, east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",TOWER_SCALE), m4("m0","s0"),
           twist("twst","m0","z",25+v*10,4),
           notch("acc","twst","east","ne",0.27+v*0.04,0.36,0.58)]
    return b(pid,f"p43_tower_twist_notch_v{v}","tower",nodes,"acc",
             ["twist","notch","tower"],"Tower twisted about vertical; east notch into rotated face.",5,3.5,1200)

def p44(pid, v):
    # pinch: slab pinched at waist, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           pinch("pnch","m0","z",0.48+v*0.04,2.0+v*0.3,4),
           carve_void("acc","pnch",0.22+v*0.03)]
    return b(pid,f"p44_slab_pinched_carve_v{v}","slab",nodes,"acc",
             ["pinch","carve_void","slab"],"Slab pinched at waist (hourglass section); east carve opens civic face.",4,3.5,900)

def p45(pid, v):
    # branch+branch: bar double branched, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bbranch("br1","m0",45+v*12,0.55+v*0.04,0.36+v*0.04),
           bbranch("br2","br1",-40-v*10,0.58+v*0.04,0.32+v*0.04),
           courtyard("acc","br2",0.20+v*0.03)]
    return b(pid,f"p45_bar_double_branch_court_v{v}","bar",nodes,"acc",
             ["branch","courtyard","bar"],"Double branching (arms connected to trunk); east courtyard at fork.",4,3.5,1100)

def p46(pid, v):
    # notch+twist: block notched then twisted, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","sw",0.24+v*0.05),
           twist("twst","bnt","z",20+v*8,4),
           carve_void("acc","twst",0.22+v*0.03)]
    return b(pid,f"p46_block_notch_twist_carve_v{v}","block",nodes,"acc",
             ["notch","twist","carve_void","block"],"Notched block twisted; east carve opens through rotated face.",4,3.5,950)

def p47(pid, v):
    # expand+nest: slab expanded then lodge, east lift
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bexpand("ex","m0","z",0.22+v*0.05,0.48+v*0.04),
           blodge("ld","ex","y",0.28+v*0.04,0.62+v*0.04),
           lift_acc("acc","ld")]
    return b(pid,f"p47_slab_expand_lodge_lift_v{v}","slab",nodes,"acc",
             ["expand","nest","lift","slab"],"Expanded slab with lodged inner volume; east lift provides access.",3,3.5,870)

def p48(pid, v):
    # offset: slab with north-face extraction, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bextract("ext","m0","z","north",0.40+v*0.05,0.52+v*0.05),
           courtyard("acc","ext",0.22+v*0.03)]
    return b(pid,f"p48_slab_extract_court_v{v}","slab",nodes,"acc",
             ["offset","courtyard","slab"],"Slab with north extraction (offset); east courtyard as civic lobby.",4,3.5,950)

def p49(pid, v):
    # compress: block clip_fraction, SE notch
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           clip_frac("cl","m0","z",0.70+v*0.05),
           notch("acc","cl","east","se",0.26+v*0.04,0.36,0.55)]
    return b(pid,f"p49_block_compress_se_notch_v{v}","block",nodes,"acc",
             ["compress","notch","block"],"Block compressed; SE east notch as compact entry.",3,3.5,780)

def p50(pid, v):
    # split+split: bar double-split, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bsplit("sp1","m0","y",0.09+v*0.03,0.0,1.0,1.0,0.48+v*0.04),
           bsplit("sp2","sp1","x",0.10+v*0.03,6.0+v*4,-1.0,2.0,0.5),
           carve_void("acc","sp2",0.20+v*0.03)]
    return b(pid,f"p50_bar_double_split_x_carve_v{v}","bar",nodes,"acc",
             ["split","carve_void","bar"],"Quarter-bar double-split; east carve void addresses fractured form.",4,3.5,940)

def p51(pid, v):
    # taper+bend: tower tapered then bent
    nodes=[box("b0",1,1,1), scale("s0","b0",TOWER_SCALE), m4("m0","s0"),
           taper("tap","m0","z",[0.65+v*0.05,0.65+v*0.05],[1.0,1.0],3),
           bend("bnd","tap","y",18+v*8,4),
           courtyard("acc","bnd",0.22+v*0.03)]
    return b(pid,f"p51_tower_taper_bend_court_v{v}","tower",nodes,"acc",
             ["taper","bend","courtyard","tower"],"Tower tapered then bent; east courtyard below curved crown.",5,3.5,1250)

def p52(pid, v):
    # pinch+join: slab pinched then join_related for connectivity
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           pinch("pnch","m0","z",0.48+v*0.04,2.0+v*0.3,4),
           join_related("jn","pnch",0.32+v*0.04),
           notch("acc","jn","east","ne",0.26+v*0.03,0.36,0.55)]
    return b(pid,f"p52_slab_pinch_join_notch_v{v}","slab",nodes,"acc",
             ["pinch","join","notch","slab"],"Pinched slab with bridge join (connected); east notch at waist marks entry.",4,3.5,970)

def p53(pid, v):
    # extrude: block boundary-expanded (extrude-like) then lifted
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bexpand("ex","m0","z",0.18+v*0.05,0.42+v*0.06),
           lift_acc("acc","ex")]
    return b(pid,f"p53_block_extrude_lift_v{v}","block",nodes,"acc",
             ["extrude","lift","block"],"Block shoulder-expanded (extruded) and lifted; east lift exposes ground.",4,3.5,930)

def p54(pid, v):
    # lodge: bar with lodged guest volume, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           blodge("ld","m0","z",0.28+v*0.04,0.55+v*0.04),
           courtyard("acc","ld",0.22+v*0.03)]
    return b(pid,f"p54_bar_lodge_court_v{v}","bar",nodes,"acc",
             ["lodge","courtyard","bar"],"Guest bar lodged in host interval; east courtyard uses lodged gap.",3,3.5,820)

def p55(pid, v):
    # extract: slab east-extracted then carve
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bextract("ext","m0","z","east",0.28+v*0.04,0.50+v*0.04),
           carve_void("acc","ext",0.20+v*0.03)]
    return b(pid,f"p55_slab_extract_e_carve_v{v}","slab",nodes,"acc",
             ["extract","carve_void","slab"],"Slab extraction channel through east face; carve deepens civic recess.",3,3.5,840)

def p56(pid, v):
    # inscribe+intersect: bar notched then cross-intersected (intersection solid)
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","nw",0.22+v*0.04),
           intersect_rel("int","bnt","z",90.0,0.40+v*0.04,0.76+v*0.04),
           notch("acc","int","east","ne",0.26+v*0.04,0.36,0.55)]
    return b(pid,f"p56_bar_inscribe_intersect_notch_v{v}","bar",nodes,"acc",
             ["inscribe","intersect","notch","bar"],"Bar notched then cross-intersected; east notch articulates entry.",4,3.5,1000)

def p57(pid, v):
    # branch+pack: bar branched then overlap (connected)
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bbranch("br","m0",55+v*15,0.60+v*0.04,0.35+v*0.04),
           overlap_rel("ovl","br","y",0.62+v*0.04,0.28+v*0.04,0.28+v*0.04),
           carve_void("acc","ovl",0.20+v*0.03)]
    return b(pid,f"p57_bar_branch_overlap_carve_v{v}","bar",nodes,"acc",
             ["branch","overlap","carve_void","bar"],"Branched bar overlapped (connected); east carve in front gap.",4,3.5,1050)

def p58(pid, v):
    # lift+carve: block lifted then carved, lift access
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           blift("bl","m0","z",0.28+v*0.04,0.56+v*0.04),
           bcarve("cv","bl","z","east",0.26+v*0.04,0.42+v*0.04),
           lift_acc("acc","cv")]
    return b(pid,f"p58_block_blift_carve_lift_v{v}","block",nodes,"acc",
             ["lift","carve","block"],"Lifted block east-carved; terminal lift opens east ground as passage.",4,3.5,980)

def p59(pid, v):
    # twist: tower twisted, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",TOWER_SCALE), m4("m0","s0"),
           twist("twst","m0","z",28+v*10,4),
           courtyard("acc","twst",0.22+v*0.03)]
    return b(pid,f"p59_tower_twist_court_v{v}","tower",nodes,"acc",
             ["twist","courtyard","tower"],"Tower twisted; east courtyard as civic space below twist.",5,3.5,1250)

def p60(pid, v):
    # pinch: slab pinched, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           pinch("pnch","m0","z",0.50+v*0.04,2.0+v*0.3,4),
           carve_void("acc","pnch",0.22+v*0.03)]
    return b(pid,f"p60_slab_pinched_y_carve_v{v}","slab",nodes,"acc",
             ["pinch","carve_void","slab"],"Slab pinched at waist; east carve opens the narrowed civic face.",4,3.5,880)

def p61(pid, v):
    # branch+branch: bar double branched, east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bbranch("br1","m0",48+v*12,0.56+v*0.04,0.36+v*0.04),
           bbranch("br2","br1",-38-v*10,0.60+v*0.04,0.32+v*0.04),
           notch("acc","br2","east","ne",0.26+v*0.04,0.36,0.55)]
    return b(pid,f"p61_bar_double_branch_notch_v{v}","bar",nodes,"acc",
             ["branch","notch","bar"],"Double branching (arms connected); east notch at fork marks entry.",4,3.5,1050)

def p62(pid, v):
    # shift+notch: block shift_related (hinged) then book_notch + carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           shift_related("sh","m0","x",0.32+v*0.04,0.50+v*0.04),
           bnotch("bnt","sh","z","ne",0.24+v*0.04),
           carve_void("acc","bnt",0.22+v*0.03)]
    return b(pid,f"p62_block_shift_notch_carve_v{v}","block",nodes,"acc",
             ["shift","notch","carve_void","block"],"Shift_related (hinged halves) with corner notch; east carve threshold.",4,3.5,960)

def p63(pid, v):
    # embed+overlap: slab embed_void then overlap_related (connected)
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           embed_void("emb","m0","z","center",0.30+v*0.05,0.50+v*0.04),
           overlap_rel("ovl","emb","x",0.62+v*0.04,0.30+v*0.04,0.22+v*0.04),
           lift_acc("acc","ovl")]
    return b(pid,f"p63_slab_embed_overlap_lift_v{v}","slab",nodes,"acc",
             ["embed","overlap","lift","slab"],"Embedded void slab overlapped (connected); east lift as ground passage.",3,3.5,870)

def p64(pid, v):
    # nest: slab with lodge (nest-like), east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           blodge("ld","m0","x",0.28+v*0.04,0.60+v*0.05),
           courtyard("acc","ld",0.22+v*0.03)]
    return b(pid,f"p64_slab_lodged_nest_court_v{v}","slab",nodes,"acc",
             ["nest","courtyard","slab"],"Slab with lodged inner volume (nest); east courtyard as layered civic court.",3,3.5,780)

def p65(pid, v):
    # carve: bar east-carved, NE notch
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bcarve("cv","m0","z","east",0.28+v*0.05,0.42+v*0.04),
           notch("acc","cv","east","ne",0.26+v*0.04,0.36,0.55)]
    return b(pid,f"p65_bar_carved_notch_v{v}","bar",nodes,"acc",
             ["carve","notch","bar"],"Bar east-carved then NE-notched; compact civic address.",4,3.5,900)

def p66(pid, v):
    # intersect+intersect: bar double cross-intersection (each produces connected solid)
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           intersect_rel("in1","m0","z",90.0,0.38+v*0.04,0.78+v*0.04),
           intersect_rel("in2","in1","y",45.0,0.36+v*0.04,0.72+v*0.04),
           carve_void("acc","in2",0.22+v*0.03)]
    return b(pid,f"p66_bar_double_intersect_carve_v{v}","bar",nodes,"acc",
             ["intersect","carve_void","bar"],"Double cross-bar intersection (each step → connected solid); east carve.",4,3.5,960)

def p67(pid, v):
    # taper+bend: tower tapered then bent, east lift
    nodes=[box("b0",1,1,1), scale("s0","b0",TOWER_SCALE), m4("m0","s0"),
           taper("tap","m0","z",[0.68+v*0.04,0.68+v*0.04],[1.0,1.0],3),
           bend("bnd","tap","y",20+v*8,4),
           lift_acc("acc","bnd")]
    return b(pid,f"p67_tower_taper_bend_lift_v{v}","tower",nodes,"acc",
             ["taper","bend","lift","tower"],"Tower tapered and bent; east lift opens public passage at base.",5,3.5,1150)

def p68(pid, v):
    # pinch+join: slab pinched then join_related, east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           pinch("pnch","m0","z",0.46+v*0.04,2.0+v*0.3,4),
           join_related("jn","pnch",0.30+v*0.04),
           courtyard("acc","jn",0.22+v*0.03)]
    return b(pid,f"p68_slab_pinch_join_court_v{v}","slab",nodes,"acc",
             ["pinch","join","courtyard","slab"],"Pinched slab joined via bridge; east courtyard at pinch waist.",4,3.5,930)

def p69(pid, v):
    # extrude: block boundary-expanded (extrude), east notch
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bexpand("ex","m0","z",0.20+v*0.05,0.44+v*0.05),
           notch("acc","ex","east","ne",0.26+v*0.04,0.36,0.55)]
    return b(pid,f"p69_block_extrude_notch_v{v}","block",nodes,"acc",
             ["extrude","notch","block"],"Block expanded (extruded); east notch at entry corner.",4,3.5,920)

def p70(pid, v):
    # lodge: bar with lodged guest, east carve
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           blodge("ld","m0","z",0.26+v*0.04,0.52+v*0.04),
           carve_void("acc","ld",0.22+v*0.03)]
    return b(pid,f"p70_bar_lodge_carve_v{v}","bar",nodes,"acc",
             ["lodge","carve_void","bar"],"Bar lodged with guest; east carve void in gap below guest.",3,3.5,800)

def p71(pid, v):
    # extract: slab extraction then lift
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           bextract("ext","m0","z","east",0.26+v*0.04,0.52+v*0.04),
           lift_acc("acc","ext")]
    return b(pid,f"p71_slab_extract_lift_v{v}","slab",nodes,"acc",
             ["extract","lift","slab"],"Slab extraction channel; east lift opens subtracted volume as passage.",3,3.5,820)

def p72(pid, v):
    # inscribe+intersect: bar SW-notched then cross-intersected (connected), east courtyard
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","sw",0.24+v*0.04),
           intersect_rel("int","bnt","z",90.0,0.38+v*0.04,0.76+v*0.04),
           courtyard("acc","int",0.22+v*0.03)]
    return b(pid,f"p72_bar_inscribed_intersect_court_v{v}","bar",nodes,"acc",
             ["inscribe","intersect","courtyard","bar"],"Notched bar cross-intersected (intersection solid); east courtyard.",4,3.5,980)

def p73(pid, v):
    # inflate+pack: slab inflated then overlap (connected)
    nodes=[box("b0",1,1,1), scale("s0","b0",SLAB_SCALE), m4("m0","s0"),
           inflate("infl","m0","z",1.14+v*0.05,1.20+v*0.05,4),
           overlap_rel("ovl","infl","x",0.62+v*0.04,0.25+v*0.04,0.28+v*0.04),
           notch("acc","ovl","east","ne",0.26+v*0.03,0.36,0.55)]
    return b(pid,f"p73_slab_inflate_overlap_notch_v{v}","slab",nodes,"acc",
             ["inflate","overlap","notch","slab"],"Inflated slab overlapped (connected at zone); east notch as entry.",3,3.5,820)

def p74(pid, v):
    # embed+taper: block embed_void then tapered
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           embed_void("emb","m0","z","center",0.30+v*0.05,0.50+v*0.04),
           taper("tap","emb","z",[0.72+v*0.04,0.72+v*0.04],[1.0,1.0],3),
           carve_void("acc","tap",0.22+v*0.03)]
    return b(pid,f"p74_block_embed_taper_carve_v{v}","block",nodes,"acc",
             ["embed","taper","carve_void","block"],"Block embed-voided then tapered; east carve at tapered face.",4,3.5,940)

def p75(pid, v):
    # split: tower book_split (single split, generation stays connected)
    nodes=[box("b0",1,1,1), scale("s0","b0",TOWER_SCALE), m4("m0","s0"),
           bsplit("sp","m0","y",0.10+v*0.03,0.0,1.0,1.0,0.50+v*0.04),
           courtyard("acc","sp",0.22+v*0.03)]
    return b(pid,f"p75_tower_split_court_v{v}","tower",nodes,"acc",
             ["split","courtyard","tower"],"Tower split displaces one wing; east courtyard in hinge gap.",5,3.5,1150)

def p76(pid, v):
    # notch: block corner-notched (book_notch), east notch entry
    nodes=[box("b0",1,1,1), scale("s0","b0",BLOCK_SCALE), m4("m0","s0"),
           bnotch("bnt","m0","z","nw",0.25+v*0.05),
           notch("acc","bnt","east","ne",0.28+v*0.04,0.36,0.55)]
    return b(pid,f"p76_block_double_notch_entry_v{v}","block",nodes,"acc",
             ["notch","block"],"Block corner-notched; east notch as minimal civic entry.",4,3.5,900)

def p77(pid, v):
    # bend+bend: bar double-bent in two axes
    nodes=[box("b0",1,1,1), scale("s0","b0",BAR_SCALE), m4("m0","s0"),
           bend("bnd1","m0","z",22+v*8,4),
           bend("bnd2","bnd1","y",-16-v*6,4),
           carve_void("acc","bnd2",0.22+v*0.03)]
    return b(pid,f"p77_bar_double_bent_carve_v{v}","bar",nodes,"acc",
             ["bend","carve_void","bar"],"Bar double-bent in two axes; east carve at curved civic face.",4,3.5,960)

# ── dispatch table ────────────────────────────────────────────────────────────
BUILDERS = [
    p00,p01,p02,p03,p04,p05,p06,p07,p08,p09,
    p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,
    p20,p21,p22,p23,p24,p25,p26,p27,p28,p29,
    p30,p31,p32,p33,p34,p35,p36,p37,p38,p39,
    p40,p41,p42,p43,p44,p45,p46,p47,p48,p49,
    p50,p51,p52,p53,p54,p55,p56,p57,p58,p59,
    p60,p61,p62,p63,p64,p65,p66,p67,p68,p69,
    p70,p71,p72,p73,p74,p75,p76,p77,
]
assert len(BUILDERS) == 78

def generate():
    programs = []
    # Pass 1: all 78 paths, variant 0
    for i in range(78):
        programs.append(BUILDERS[i](PATH_IDS[i], 0))
    # Pass 2: 42 more, variant 1 (paths 0..41)
    for i in range(42):
        programs.append(BUILDERS[i](PATH_IDS[i], 1))
    assert len(programs) == 120

    # Top-level principle IDs from path offers
    pids = sorted(set([
        "book:operative:bend", "book:operative:fracture",
        "book:combination:04:embed+embed", "book:combination:17:branch+expand",
        "book:case:60:carve+offset", "book:operative:branch", "book:operative:rotate",
        "book:operative:inscribe", "book:combination:12:intersect+split",
        "book:aggregation:stack:bend", "book:case:68:lift+extrude",
        "book:operative:interlock", "book:operative:shear",
        "book:combination:08:expand+expand", "book:aggregation:reflect:expand",
        "book:case:64:overlap+expand", "book:combination:03:split+split",
        "book:combination:16:bend+branch", "book:aggregation:join:split",
        "book:operative:inflate", "book:operative:overlap",
        "book:combination:11:inscribe+intersect", "book:aggregation:pack+stack:branch",
        "book:case:67:lift+carve", "book:operative:twist", "book:operative:pinch",
        "book:combination:07:branch+branch", "book:combination:20:notch+twist",
        "book:case:63:expand+nest", "book:operative:offset", "book:operative:compress",
        "book:combination:15:taper+bend", "book:aggregation:join+array:pinch",
        "book:operative:extrude", "book:operative:lodge", "book:operative:extract",
        "book:combination:02:intersect+intersect", "book:aggregation:pack:inflate",
        "book:case:66:embed+taper", "book:operative:split", "book:operative:notch",
        "book:combination:06:bend+bend", "book:combination:19:shift+notch",
        "book:case:62:embed+overlap", "book:operative:nest", "book:operative:carve",
    ]))
    return {"programs": programs, "book_principle_ids": pids}

def validate(payload):
    if not HAS_SCHEMA:
        print("Skipping schema validation (jsonschema not installed)")
        return True
    schema = json.loads(open(SCHEMA_PATH, encoding='utf-8').read())
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(payload))
    if errors:
        for e in errors[:30]:
            print(f"  ERROR [{list(e.path)[:3]}]: {e.message[:120]}")
        print(f"  Total: {len(errors)} errors")
        return False
    print(f"  PASSED: {len(payload['programs'])} programs, 0 schema errors")
    return True

if __name__ == "__main__":
    print("Generating 120 BOOK programs (gen_book18_final)...")
    payload = generate()
    seeds = {}
    for p in payload['programs']:
        s = p['base_seed']; seeds[s] = seeds.get(s,0)+1
    print(f"Seeds: {seeds}")
    print(f"Unique path IDs: {len(set(p['book_composition_path_id'] for p in payload['programs']))}")
    ok = validate(payload)
    if not ok:
        sys.exit(1)
    out = json.dumps(payload, ensure_ascii=False, indent=2)
    open(OUTPUT_PATH, 'w', encoding='utf-8').write(out)
    print(f"Written {len(out)//1024}KB to {OUTPUT_PATH}")
    print("Done.")
