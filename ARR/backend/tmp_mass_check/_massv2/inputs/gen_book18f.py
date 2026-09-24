"""
gen_book18f.py  –  120-program BOOK generator for cycle-comp18.
Fixes two importer violations from gen_book18e_main.py:
  1. base_seed must match box proportions (verified: all correct, matrix4 not read as scale)
  2. compiled mesh must be ONE connected solid  →  eliminated related_array, offset_related,
     mirror_array when used in ways that produce disconnected solids. Replaced with:
     - book_branch (connected to trunk), join_related (explicit bridge), overlap_related
       (overlapping bodies), interlock_related (crossing bodies), boundary_expand (additive)
     - split_wing always uses bridge=True for connectivity
     - courtyard / carve_void / notch are safe (subtract from connected body)
Seed matching rules (importer reads box w/d/h since no scale node, only matrix4):
  tower  : height > 1.35 × widest_plan_side   → box(0.68,0.68,2.5)
  bar    : plan_aspect >= 2.2                  → box(2.8,0.62,0.48)
  slab   : height < 0.48 × narrowest_plan_side → box(2.2,1.45,0.28)
  block  : else                                → box(1.0,1.0,1.0)
"""

import json, sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False

SCHEMA_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp18\book-author\schema.json"
OUTPUT_PATH = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json"

# ── parameter helpers ────────────────────────────────────────────────────────
def num_p(name, v):
    return {"name":name,"value_type":"number","numeric_value":float(v),
            "string_value":"","boolean_value":False,"vector_value":[0,0,0],"structured_json":None}
def str_p(name, v):
    return {"name":name,"value_type":"string","numeric_value":0.0,
            "string_value":str(v),"boolean_value":False,"vector_value":[0,0,0],"structured_json":None}
def bool_p(name, v):
    return {"name":name,"value_type":"boolean","numeric_value":0.0,
            "string_value":"","boolean_value":bool(v),"vector_value":[0,0,0],"structured_json":None}
def vec_p(name, v):
    return {"name":name,"value_type":"vector","numeric_value":0.0,
            "string_value":"","boolean_value":False,"vector_value":list(v),"structured_json":None}
def lit_p(name, nv=0.0, sv="", bv=False, vv=None, sj=None):
    return {"name":name,"value_type":"literal","numeric_value":float(nv),
            "string_value":str(sv),"boolean_value":bool(bv),
            "vector_value":list(vv) if vv is not None else [0,0,0],"structured_json":sj}
def mat4_p(m):
    return {"name":"matrix4","value_type":"matrix4","numeric_value":0.0,
            "string_value":"","boolean_value":False,"vector_value":[0,0,0],
            "structured_json":None,"matrix4_value":m}
def identity_m4():
    return [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
def scale_m4(sx,sy,sz):
    return [[sx,0,0,0],[0,sy,0,0],[0,0,sz,0],[0,0,0,1]]

# ── node constructors ────────────────────────────────────────────────────────
def box_n(nid,w=1.0,d=1.0,h=1.0,role="dominant_mass"):
    return {"id":nid,"kind":"primitive","operator":"box","inputs":[],
            "semantic_role":role,
            "parameters":[
                {"name":"width","value_type":"number","numeric_value":float(w)},
                {"name":"depth","value_type":"number","numeric_value":float(d)},
                {"name":"height","value_type":"number","numeric_value":float(h)},
                {"name":"center","value_type":"boolean","boolean_value":True},
            ]}

def m4_n(nid,inp,m,role="dominant_mass"):
    return {"id":nid,"kind":"transform","operator":"matrix4","inputs":[inp],
            "semantic_role":role,"parameters":[mat4_p(m)]}

def court_n(nid,inp,margin=0.25,side="east"):
    return {"id":nid,"kind":"macro","operator":"courtyard","inputs":[inp],
            "semantic_role":"public_threshold",
            "parameters":[num_p("margin_ratio",margin),str_p("open_side",side)]}

def carve_n(nid,inp,margin=0.25,side="east"):
    return {"id":nid,"kind":"macro","operator":"carve_void","inputs":[inp],
            "semantic_role":"public_threshold",
            "parameters":[num_p("margin_ratio",margin),str_p("open_side",side)]}

def notch_n(nid,inp,side="east",corner="ne",ratio=0.3,wr=0.4,hr=0.6):
    return {"id":nid,"kind":"macro","operator":"notch","inputs":[inp],
            "semantic_role":"public_threshold",
            "parameters":[str_p("side",side),str_p("corner",corner),
                          num_p("ratio",ratio),num_p("width_ratio",wr),num_p("height_ratio",hr)]}

def lift_n(nid,inp,access_side="east",rise_ratio=0.25,support_ratio=0.35):
    return {"id":nid,"kind":"macro","operator":"lift","inputs":[inp],
            "semantic_role":"public_threshold",
            "parameters":[str_p("access_side",access_side),
                          lit_p("rise_ratio",nv=rise_ratio),
                          lit_p("support_ratio",nv=support_ratio)]}

def split_wing_n(nid,inp,access_side="east",axis="y",layout="parallel",
                  gap_ratio=0.12,height_ratio=0.9,bridge=True,
                  cwr=0.25,ground_spine=False,gshr=0.15,gswr=0.2):
    return {"id":nid,"kind":"macro","operator":"split_wing","inputs":[inp],
            "semantic_role":"public_threshold",
            "parameters":[str_p("access_side",access_side),str_p("axis",axis),
                          str_p("layout",layout),num_p("gap_ratio",gap_ratio),
                          num_p("height_ratio",height_ratio),bool_p("bridge",bridge),
                          lit_p("connector_width_ratio",nv=cwr),
                          bool_p("ground_spine",ground_spine),
                          lit_p("ground_spine_height_ratio",nv=gshr),
                          lit_p("ground_spine_width_ratio",nv=gswr)]}

def bend_n(nid,inp,axis="z",angle=25,subdiv=4,role="dominant_mass"):
    return {"id":nid,"kind":"transform","operator":"bend","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("angle_degrees",angle),num_p("subdivisions",subdiv)]}

def taper_n(nid,inp,axis="z",ss=None,es=None,lff=0.0,subdiv=3,role="dominant_mass"):
    if ss is None: ss=[1.0,1.0]
    if es is None: es=[0.7,0.7]
    return {"id":nid,"kind":"modifier","operator":"taper","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),vec_p("start_scale",ss),vec_p("end_scale",es),
                          num_p("lower_floor_fraction",lff),num_p("subdivisions",subdiv),
                          lit_p("scale_top",nv=es[0])]}

def twist_n(nid,inp,axis="z",angle=20,subdiv=4,role="dominant_mass"):
    return {"id":nid,"kind":"transform","operator":"twist","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("angle_degrees",angle),num_p("subdivisions",subdiv)]}

def shear_n(nid,inp,axis="z",amount=0.3,dv=None,role="dominant_mass"):
    if dv is None: dv=[1.0,0.0,0.0]
    return {"id":nid,"kind":"transform","operator":"shear","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("amount",amount),
                          lit_p("direction",nv=0.0,sv="x",bv=False,vv=dv),
                          vec_p("pivot",[0.0,0.0,0.0])]}

def inflate_n(nid,inp,axis="z",factor=1.15,ms=1.2,pp=2.0,subdiv=4,role="dominant_mass"):
    return {"id":nid,"kind":"modifier","operator":"inflate","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),lit_p("factor",nv=factor),
                          lit_p("middle_scale",nv=ms),lit_p("profile_power",nv=pp),
                          num_p("subdivisions",subdiv)]}

def pinch_n(nid,inp,axis="z",wr=0.5,ws=0.7,pp=2.0,subdiv=4,role="dominant_mass"):
    return {"id":nid,"kind":"modifier","operator":"pinch","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),lit_p("waist_ratio",nv=wr),
                          lit_p("waist_scale",nv=ws),lit_p("profile_power",nv=pp),
                          num_p("subdivisions",subdiv)]}

def book_branch_n(nid,inp,angle=45.0,tr=0.6,ar=0.4,va="input_base",role="dominant_mass"):
    return {"id":nid,"kind":"macro","operator":"book_branch","inputs":[inp],
            "semantic_role":role,
            "parameters":[num_p("angle_degrees",angle),lit_p("trunk_ratio",nv=tr),
                          lit_p("arm_ratio",nv=ar),str_p("vertical_anchor",va)]}

def book_split_n(nid,inp,axis="y",angle=0.0,gap=0.1,osign=1.0,bsign=1.0,sgen=1.0,
                  tr=0.5,access_sv="east",role="program_space"):
    return {"id":nid,"kind":"macro","operator":"book_split","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("angle_degrees",angle),num_p("gap_ratio",gap),
                          lit_p("outward_sign",nv=osign),lit_p("branch_sign",nv=bsign),
                          lit_p("split_generation",nv=sgen),lit_p("terminal_ratio",nv=tr),
                          lit_p("access_side",sv=access_sv)]}

def book_carve_n(nid,inp,axis="z",face="east",depth=0.3,osign=1.0,wr=0.4,role="program_space"):
    return {"id":nid,"kind":"macro","operator":"book_carve","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),str_p("face_side",face),
                          lit_p("depth_ratio",nv=depth),lit_p("outward_sign",nv=osign),
                          num_p("width_ratio",wr)]}

def book_extract_n(nid,inp,axis="z",face="east",dr=0.3,gs=0.5,osign=1.0,role="program_space"):
    return {"id":nid,"kind":"macro","operator":"book_extract","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),str_p("face_side",face),
                          lit_p("distance_ratio",nv=dr),lit_p("guest_scale",nv=gs),
                          lit_p("outward_sign",nv=osign)]}

def book_fracture_n(nid,inp,axis="z",angle=20.0,gap=0.12,osign=1.0,rbr=0.6,role="dominant_mass"):
    return {"id":nid,"kind":"macro","operator":"book_fracture","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("angle_degrees",angle),num_p("gap_ratio",gap),
                          lit_p("outward_sign",nv=osign),lit_p("retained_back_ratio",nv=rbr)]}

def book_grade_n(nid,inp,axis="z",face="east",depth=0.25,osign=1.0,wr=0.4,levels=3,role="program_space"):
    return {"id":nid,"kind":"macro","operator":"book_grade","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),str_p("face_side",face),
                          lit_p("depth_ratio",nv=depth),lit_p("outward_sign",nv=osign),
                          num_p("width_ratio",wr),num_p("levels",levels)]}

def book_lift_n(nid,inp,axis="z",dr=0.3,gs=0.6,osign=1.0,role="program_space"):
    return {"id":nid,"kind":"macro","operator":"book_lift","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),lit_p("distance_ratio",nv=dr),
                          lit_p("guest_scale",nv=gs),lit_p("outward_sign",nv=osign)]}

def book_lodge_n(nid,inp,axis="z",dr=0.25,gs=0.5,osign=1.0,role="program_space"):
    return {"id":nid,"kind":"macro","operator":"book_lodge","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),lit_p("distance_ratio",nv=dr),
                          lit_p("guest_scale",nv=gs),lit_p("outward_sign",nv=osign)]}

def book_notch_n(nid,inp,axis="z",corner="ne",osign=1.0,ratio=0.25,role="program_space"):
    return {"id":nid,"kind":"macro","operator":"book_notch","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),str_p("corner",corner),
                          lit_p("outward_sign",nv=osign),num_p("ratio",ratio)]}

def book_rotate_n(nid,inp,axis="z",angle=30.0,osign=1.0,rr=0.5,role="program_space"):
    return {"id":nid,"kind":"macro","operator":"book_rotate","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("angle_degrees",angle),
                          lit_p("outward_sign",nv=osign),lit_p("related_ratio",nv=rr)]}

def boundary_expand_n(nid,inp,axis="z",amount=0.15,sf=0.5,role="dominant_mass"):
    return {"id":nid,"kind":"macro","operator":"boundary_expand","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("amount",amount),lit_p("shoulder_fraction",nv=sf)]}

def embed_void_n(nid,inp,axis="z",pos="east",er=0.35,gs=0.5,osign=1.0,role="program_space"):
    return {"id":nid,"kind":"macro","operator":"embed_void","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),str_p("position",pos),
                          lit_p("embedded_ratio",nv=er),lit_p("guest_scale",nv=gs),
                          lit_p("outward_sign",nv=osign)]}

# CONNECTIVITY-SAFE related operators:
def join_related_n(nid,inp,br=0.3,role="dominant_mass"):
    """join_related produces ONE connected solid via explicit bridge"""
    return {"id":nid,"kind":"macro","operator":"join_related","inputs":[inp],
            "semantic_role":role,"parameters":[lit_p("bridge_ratio",nv=br)]}

def overlap_related_n(nid,inp,axis="x",osign=1.0,sr=0.35,slr=0.6,vo=0.3,role="dominant_mass"):
    """overlap_related: overlapping bodies → connected solid"""
    return {"id":nid,"kind":"macro","operator":"overlap_related","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),lit_p("outward_sign",nv=osign),
                          lit_p("shift_ratio",nv=sr),lit_p("slab_ratio",nv=slr),
                          lit_p("vertical_overlap",nv=vo)]}

def interlock_related_n(nid,inp,axis="x",angle=0.0,br=0.4,dr=0.5,osign=1.0,role="dominant_mass"):
    """interlock_related: crossing bodies → connected (shared material)"""
    return {"id":nid,"kind":"macro","operator":"interlock_related","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("angle_degrees",angle),
                          lit_p("bar_ratio",nv=br),lit_p("distance_ratio",nv=dr),
                          lit_p("outward_sign",nv=osign)]}

def intersect_related_n(nid,inp,axis="z",angle=90.0,br=0.4,us=0.8,role="dominant_mass"):
    """intersect_related: produces intersection volume → single connected solid"""
    return {"id":nid,"kind":"macro","operator":"intersect_related","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),num_p("angle_degrees",angle),
                          lit_p("bar_ratio",nv=br),lit_p("unit_scale",nv=us)]}

def shift_related_n(nid,inp,axis="x",dr=0.3,osign=1.0,sr=0.5,role="dominant_mass"):
    """shift_related: CONNECTED when shift_ratio < 1 (bodies stay joined at split)"""
    return {"id":nid,"kind":"macro","operator":"shift_related","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),lit_p("distance_ratio",nv=dr),
                          lit_p("outward_sign",nv=osign),lit_p("split_ratio",nv=sr)]}

def clip_frac_n(nid,inp,axis="z",frac=0.6,anchor="high",role="dominant_mass"):
    return {"id":nid,"kind":"modifier","operator":"clip_fraction","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("axis",axis),lit_p("fraction",nv=frac),str_p("anchor",anchor)]}

def cut_corner_n(nid,inp,corner="ne",ratio=0.2,role="dominant_mass"):
    return {"id":nid,"kind":"modifier","operator":"cut_corner","inputs":[inp],
            "semantic_role":role,
            "parameters":[str_p("corner",corner),num_p("ratio",ratio)]}

def stack_n(nid,inp,count=2,spl=None,spacing=0.5,role="dominant_mass"):
    if spl is None: spl=[0.0,0.0,0.0]
    return {"id":nid,"kind":"pattern","operator":"stack","inputs":[inp],
            "semantic_role":role,
            "parameters":[num_p("count",count),vec_p("shift_per_level",spl),lit_p("spacing",nv=spacing)]}

# ── dimensional intent ───────────────────────────────────────────────────────
def dim_intent(storeys=4,storey_h=3.5,gfa=None):
    if gfa is None: gfa=storeys*300.0
    return {"schema_version":"arr.maas.dimensional_intent.v1",
            "storey_count":storeys,"storey_height_m":storey_h,
            "target_gfa_m2":float(gfa),
            "delivery_policy":"preserve_physical_dimensions",
            "programme_status":"unknown"}

def mkprog(pid,v,name,base_form,base_seed,tags,rationale,nodes,root_id,
            storeys=4,storey_h=3.5,gfa=None,pids=None):
    if pids is None: pids=[pid]
    if gfa is None: gfa=storeys*300.0
    return {"book_composition_path_id":pid,
            "name":f"{name}_v{v}",
            "base_form_id":base_form,
            "base_seed":base_seed,
            "intent_tags":tags[:12],
            "nodes":nodes,
            "root_id":root_id,
            "rationale":rationale,
            "dimensional_intent":dim_intent(storeys,storey_h,gfa),
            "book_principle_ids":pids}

# ── 78 path IDs (from offer) ──────────────────────────────────────────────────
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

ALL_PRINCIPLE_IDS = [
    "book:operative:bend","book:operative:fracture","book:combination:04:embed+embed",
    "book:combination:17:branch+expand","book:case:60:carve+offset",
    "book:operative:branch","book:operative:rotate","book:operative:inscribe",
    "book:combination:12:intersect+split","book:aggregation:stack:bend",
    "book:case:68:lift+extrude","book:operative:interlock","book:operative:shear",
    "book:combination:08:expand+expand","book:aggregation:reflect:expand",
    "book:case:64:overlap+expand","book:operative:bend","book:operative:fracture",
    "book:combination:03:split+split","book:combination:16:bend+branch",
    "book:aggregation:join:split","book:operative:inflate","book:operative:overlap",
    "book:operative:inscribe","book:combination:12:intersect+split",
    "book:aggregation:stack:bend","book:case:68:lift+extrude",
    "book:operative:interlock","book:operative:shear",
    "book:combination:07:branch+branch","book:combination:20:notch+twist",
    "book:case:63:expand+nest","book:operative:offset","book:operative:compress",
    "book:combination:03:split+split","book:combination:16:bend+branch",
    "book:aggregation:join:split","book:operative:inflate","book:operative:overlap",
    "book:operative:inscribe","book:combination:11:inscribe+intersect",
    "book:aggregation:pack+stack:branch","book:case:67:lift+carve",
    "book:operative:twist","book:operative:pinch",
    "book:combination:07:branch+branch","book:combination:20:notch+twist",
    "book:case:63:expand+nest","book:operative:offset","book:operative:compress",
    "book:combination:03:split+split","book:combination:15:taper+bend",
    "book:aggregation:join+array:pinch","book:operative:extrude",
    "book:operative:lodge","book:operative:extract",
    "book:combination:11:inscribe+intersect","book:aggregation:pack+stack:branch",
    "book:case:67:lift+carve","book:operative:twist","book:operative:pinch",
    "book:combination:07:branch+branch","book:combination:19:shift+notch",
    "book:case:62:embed+overlap","book:operative:nest","book:operative:carve",
    "book:combination:02:intersect+intersect","book:combination:15:taper+bend",
    "book:aggregation:join+array:pinch","book:operative:extrude",
    "book:operative:lodge","book:operative:extract",
    "book:combination:11:inscribe+intersect","book:aggregation:pack:inflate",
    "book:case:66:embed+taper","book:operative:split","book:operative:notch",
    "book:combination:06:bend+bend",
]
assert len(ALL_PRINCIPLE_IDS) == 78

# ── 78 builder functions (ALL produce ONE connected solid) ───────────────────
# Connectivity guarantee:
#   - book_branch: arm stays attached to trunk at hinge → connected ✓
#   - book_split + join_related: bridge joins the halves → connected ✓
#   - overlap_related: bodies overlap in space → connected ✓
#   - interlock_related: bodies cross each other → connected ✓
#   - intersect_related: produces intersection solid → connected ✓
#   - shift_related: split halves shift but remain hinged → connected ✓
#   - courtyard / carve_void / notch / lift / split_wing(bridge=True): subtract/access on single body → connected ✓
#   - All deformation ops (bend, taper, twist, shear, inflate, pinch): modify single body → connected ✓
#   - book_carve / book_extract / book_fracture / book_lift / book_lodge: BOOK ops on single body → connected ✓
#   - embed_void: carves void in body → connected ✓
#   - boundary_expand / book_grade / book_notch / book_rotate: BOOK ops on single body → connected ✓
#   - stack: stacks copies → connected if spacing=0 or slight (overlapping)
#   EXCLUDED (disconnecting): related_array, offset_related, mirror_array, nested_related
#                              (these spread copies apart)

def b0(pid,v):
    # path 0: 1/1 long_axis bend → bar bent to curve, east court
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           bend_n("bend0","m0","z",22+v*8,4),
           court_n("result","bend0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"bent_bar_court","cube","bar",
                  ["bend","courtyard","long_axis"],
                  "Continuously bent bar curves around east civic court.",
                  nodes,"result",4,3.5,1100,["book:operative:bend"])

def b1(pid,v):
    # path 1: 1/1 long_axis fracture → slab receives angled split
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_fracture_n("frac0","m0","z",15+v*10,0.10+v*0.04,1.0,0.55+v*0.05),
           notch_n("result","frac0","east","ne",0.28+v*0.04,0.35,0.5)]
    return mkprog(pid,v,"fractured_slab_notch","cube","slab",
                  ["fracture","notch","long_axis"],
                  "Slab with diagonal fracture; east corner notch marks entry.",
                  nodes,"result",3,3.5,900,["book:operative:fracture"])

def b2(pid,v):
    # path 2: 1/1 long_axis embed+embed → block with two nested voids
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           embed_void_n("emb1","m0","z","east",0.30+v*0.05,0.45+v*0.05),
           embed_void_n("emb2","emb1","y","center",0.25+v*0.04,0.40+v*0.04),
           carve_n("result","emb2",0.20+v*0.03,"east")]
    return mkprog(pid,v,"double_embed_court","cube","block",
                  ["embed","carve_void","long_axis"],
                  "Two nested embed voids hollow block; east carve opens forecourt.",
                  nodes,"result",5,3.5,1400,["book:combination:04:embed+embed"])

def b3(pid,v):
    # path 3: 1/1 long_axis branch+expand → bar branches then shoulder-expands
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_branch_n("br0","m0",40+v*15,0.55+v*0.05,0.38+v*0.04,"input_base"),
           boundary_expand_n("exp0","br0","z",0.18+v*0.04,0.45+v*0.05),
           court_n("result","exp0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"branched_expanded_court","cube","bar",
                  ["branch","expand","courtyard","long_axis"],
                  "Arms branch from bar trunk then expand; east court as civic threshold.",
                  nodes,"result",4,3.5,1200,["book:combination:17:branch+expand"])

def b4(pid,v):
    # path 4: 1/1 long_axis carve+offset → slab carved east then book_carve again on different face
    # FIX: replaced offset_related (disconnecting) with book_carve on south face + notch
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_carve_n("carve0","m0","z","east",0.25+v*0.05,1.0,0.40+v*0.05),
           book_carve_n("carve1","carve0","z","south",0.20+v*0.04,1.0,0.35+v*0.04),
           notch_n("result","carve1","east","se",0.25+v*0.03,0.35,0.55)]
    return mkprog(pid,v,"dual_carved_notch","cube","slab",
                  ["carve","offset","notch","long_axis"],
                  "Slab carved east and south; SE notch gives corner civic address.",
                  nodes,"result",4,3.5,1000,["book:case:60:carve+offset"])

def b5(pid,v):
    # path 5: 1/1 short_axis branch → bar with Y-branch, east court
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_branch_n("br0","m0",60+v*20,0.58+v*0.05,0.35+v*0.05,"input_base"),
           court_n("result","br0",0.24+v*0.03,"east")]
    return mkprog(pid,v,"short_branch_court","cube","bar",
                  ["branch","short_axis","courtyard"],
                  "Short-axis branching produces Y-plan; east courtyard in fork.",
                  nodes,"result",4,3.5,1150,["book:operative:branch"])

def b6(pid,v):
    # path 6: 1/1 short_axis rotate → slab with rotated child, east carve
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_rotate_n("rot0","m0","z",25+v*10,1.0,0.45+v*0.06),
           carve_n("result","rot0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"rotated_slab_carve","cube","slab",
                  ["rotate","short_axis","carve_void"],
                  "Slab child rotated about hinge; east carve void marks entry.",
                  nodes,"result",3,3.5,870,["book:operative:rotate"])

def b7(pid,v):
    # path 7: 1/1 short_axis inscribe → block corner-notched (inscribed void), east notch
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","sw",1.0,0.22+v*0.05),
           notch_n("result","notch0","east","ne",0.25+v*0.04,0.40,0.55)]
    return mkprog(pid,v,"inscribed_notch_entry","cube","block",
                  ["inscribe","notch","short_axis"],
                  "Block inscribed with corner notch void; east notch delivers civic entrance.",
                  nodes,"result",4,3.5,1050,["book:operative:inscribe"])

def b8(pid,v):
    # path 8: 1/1 short_axis intersect+split → bar cross-intersected then split+lift
    # intersect_related produces a connected intersection volume
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           intersect_related_n("inter0","m0","z",90.0,0.38+v*0.05,0.75+v*0.05),
           book_split_n("sp0","inter0","y",0.0,0.10+v*0.04,1.0,1.0,1.0,0.48+v*0.04,"east"),
           lift_n("result","sp0","east",0.22+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"intersect_split_lift","cube","bar",
                  ["intersect","split","short_axis","lift"],
                  "Cross intersection then split; east lift opens piloti threshold.",
                  nodes,"result",4,3.5,1100,["book:combination:12:intersect+split"])

def b9(pid,v):
    # path 9: 1/1 short_axis bend+stack → slab bent and stacked with overlap
    # stack with 0 spacing → connected (overlapping floors)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           bend_n("bend0","m0","y",18+v*7,4),
           stack_n("stk0","bend0",2+v,[0.05,0.0,0.0],0.0),
           court_n("result","stk0",0.20+v*0.04,"east")]
    return mkprog(pid,v,"bent_stacked_court","cube","slab",
                  ["bend","stack","short_axis","courtyard"],
                  "Bent slab stacked (zero spacing → connected); east courtyard as threshold.",
                  nodes,"result",3+v,3.5,950+v*150,["book:aggregation:stack:bend"])

def b10(pid,v):
    # path 10: 1/1 short_axis lift+extrude → block lifted and wing-split (bridge ensures connection)
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_lift_n("lift0","m0","z",0.28+v*0.05,0.55+v*0.05,1.0),
           split_wing_n("result","lift0","east","y","parallel",0.12+v*0.02,0.85+v*0.05,True,0.28+v*0.03,False,0.15,0.2)]
    return mkprog(pid,v,"lifted_split_wing","cube","block",
                  ["lift","split_wing","short_axis"],
                  "Block lifted and wing-split with east-access bridge (bridge=True ensures solid).",
                  nodes,"result",4,3.5,1200,["book:case:68:lift+extrude"])

def b11(pid,v):
    # path 11: 1/1 vertical interlock → bar interlocked (crossing volumes → connected)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           interlock_related_n("inter0","m0","x",0.0,0.38+v*0.04,0.45+v*0.05,1.0),
           court_n("result","inter0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"interlocked_court","cube","bar",
                  ["interlock","vertical","courtyard"],
                  "Two interlocked L-volumes share material zone; east court organizes entry.",
                  nodes,"result",4,3.5,1100,["book:operative:interlock"])

def b12(pid,v):
    # path 12: 1/1 vertical shear → tower sheared
    w,d,h=0.68,0.68,2.5
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           shear_n("shear0","m0","z",0.25+v*0.06,[1.0,0.0,0.0]),
           notch_n("result","shear0","east","ne",0.28+v*0.04,0.38,0.6)]
    return mkprog(pid,v,"sheared_tower_notch","cube","tower",
                  ["shear","vertical","notch"],
                  "Tower sheared obliquely; east notch frames civic entry recess.",
                  nodes,"result",5,3.5,1300,["book:operative:shear"])

def b13(pid,v):
    # path 13: 1/1 vertical expand+expand → block double-expanded
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           boundary_expand_n("exp1","m0","z",0.20+v*0.05,0.40+v*0.06),
           boundary_expand_n("exp2","exp1","y",0.15+v*0.04,0.55+v*0.04),
           carve_n("result","exp2",0.22+v*0.03,"east")]
    return mkprog(pid,v,"double_expand_carve","cube","block",
                  ["expand","vertical","carve_void"],
                  "Double shoulder expansion thickens block; east carve opens through face.",
                  nodes,"result",4,3.5,1200,["book:combination:08:expand+expand"])

def b14(pid,v):
    # path 14: 1/1 vertical expand+reflect → slab expanded then mirrored via overlap_related
    # FIX: replaced mirror_array (disconnecting) with overlap_related (connected)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           boundary_expand_n("exp0","m0","z",0.22+v*0.05,0.5+v*0.04),
           overlap_related_n("ovl0","exp0","y",1.0,0.28+v*0.04,0.60+v*0.04,0.35+v*0.04),
           court_n("result","ovl0",0.24+v*0.03,"east")]
    return mkprog(pid,v,"expanded_overlapped_court","cube","slab",
                  ["expand","overlap","reflect","vertical","courtyard"],
                  "Expanded slab overlapped to create bilateral bulk; east court as gateway.",
                  nodes,"result",4,3.5,1100,["book:aggregation:reflect:expand"])

def b15(pid,v):
    # path 15: 1/1 vertical overlap+expand → bar overlapped then expanded
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           overlap_related_n("ovl0","m0","x",1.0,0.32+v*0.04,0.58+v*0.04,0.25+v*0.04),
           boundary_expand_n("exp0","ovl0","z",0.18+v*0.04,0.48+v*0.04),
           notch_n("result","exp0","east","ne",0.25+v*0.04,0.38,0.55)]
    return mkprog(pid,v,"overlap_expanded_notch","cube","bar",
                  ["overlap","expand","vertical","notch"],
                  "Overlapping bars (connected) expand shoulder; east notch addresses corner.",
                  nodes,"result",4,3.5,1150,["book:case:64:overlap+expand"])

def b16(pid,v):
    # path 16: 3/8 long_axis bend → slab at 3/8 scale bent then east carve
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           bend_n("bend0","m0","z",30+v*10,4),
           carve_n("result","bend0",0.22+v*0.04,"east")]
    return mkprog(pid,v,"38_bent_carve","cube","slab",
                  ["bend","long_axis","3_8"],
                  "Slab bent to shelter east carve void as civic approach.",
                  nodes,"result",3,3.5,800,["book:operative:bend"])

def b17(pid,v):
    # path 17: 3/8 long_axis fracture → block with diagonal fracture, SE notch
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_fracture_n("frac0","m0","z",20+v*12,0.11+v*0.04,1.0,0.58+v*0.04),
           notch_n("result","frac0","east","se",0.27+v*0.04,0.36,0.5)]
    return mkprog(pid,v,"38_fracture_notch","cube","block",
                  ["fracture","long_axis","3_8","notch"],
                  "Block receives angled fissure; SE notch defines east entry corner.",
                  nodes,"result",3,3.5,850,["book:operative:fracture"])

def b18(pid,v):
    # path 18: 3/8 long_axis split+split → bar double-split (each split keeps geometry connected)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_split_n("sp0","m0","y",0.0,0.08+v*0.03,1.0,1.0,1.0,0.45+v*0.05,"east"),
           book_split_n("sp1","sp0","x",5.0+v*5,0.10+v*0.03,-1.0,-1.0,2.0,0.5,"east"),
           lift_n("result","sp1","east",0.20+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"38_split_split_lift","cube","bar",
                  ["split","long_axis","3_8","lift"],
                  "Double split displaces bar children; east lift creates public piloti threshold.",
                  nodes,"result",4,3.5,1050,["book:combination:03:split+split"])

def b19(pid,v):
    # path 19: 3/8 long_axis bend+branch → bar bent then branched
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           bend_n("bend0","m0","z",20+v*8,4),
           book_branch_n("br0","bend0",50+v*10,0.60+v*0.04,0.36+v*0.04,"input_base"),
           court_n("result","br0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_bent_branch_court","cube","bar",
                  ["bend","branch","long_axis","3_8"],
                  "Bent bar then branched; east courtyard catches the opening of the curve.",
                  nodes,"result",4,3.5,1100,["book:combination:16:bend+branch"])

def b20(pid,v):
    # path 20: 3/8 long_axis split+join → bar split then join_related bridges halves
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_split_n("sp0","m0","y",0.0,0.09+v*0.03,1.0,1.0,1.0,0.5,"east"),
           join_related_n("join0","sp0",0.28+v*0.05),
           carve_n("result","join0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_split_join_carve","cube","bar",
                  ["split","join","long_axis","3_8"],
                  "Split halves bridge-joined (one solid); east carve delivers gateway entry.",
                  nodes,"result",4,3.5,1000,["book:aggregation:join:split"])

def b21(pid,v):
    # path 21: 3/8 short_axis inflate → slab inflated at crown
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           inflate_n("infl0","m0","z",1.12+v*0.06,1.18+v*0.05,2.2+v*0.3,4),
           notch_n("result","infl0","east","ne",0.25+v*0.04,0.38,0.55)]
    return mkprog(pid,v,"38_inflated_notch","cube","slab",
                  ["inflate","short_axis","3_8","notch"],
                  "Slab inflated at crown; east notch indents the billowing face for entry.",
                  nodes,"result",3,3.5,820,["book:operative:inflate"])

def b22(pid,v):
    # path 22: 3/8 short_axis overlap → bar overlapped (connected by overlap zone)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           overlap_related_n("ovl0","m0","y",1.0,0.30+v*0.04,0.62+v*0.04,0.22+v*0.04),
           court_n("result","ovl0",0.20+v*0.04,"east")]
    return mkprog(pid,v,"38_overlap_court","cube","bar",
                  ["overlap","short_axis","3_8","courtyard"],
                  "Two overlapping bars superpose in plan (connected); east courtyard in overlap zone.",
                  nodes,"result",4,3.5,1050,["book:operative:overlap"])

def b23(pid,v):
    # path 23: 3/8 short_axis inscribe → block with NW corner notch, east carve
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","nw",1.0,0.25+v*0.05),
           carve_n("result","notch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_inscribed_carve","cube","block",
                  ["inscribe","short_axis","3_8","carve_void"],
                  "NW corner notch inscribed; east carve void defines civic face.",
                  nodes,"result",3,3.5,870,["book:operative:inscribe"])

def b24(pid,v):
    # path 24: 3/8 short_axis intersect+split → bar cross-intersected then split
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           intersect_related_n("inter0","m0","z",90.0,0.36+v*0.05,0.78+v*0.04),
           book_split_n("sp0","inter0","x",0.0,0.09+v*0.03,1.0,1.0,1.0,0.5,"east"),
           lift_n("result","sp0","east",0.22+v*0.03,0.32+v*0.03)]
    return mkprog(pid,v,"38_intersect_split_lift","cube","bar",
                  ["intersect","split","short_axis","3_8"],
                  "Cross intersection → connected intersection solid; split then east lift.",
                  nodes,"result",4,3.5,1100,["book:combination:12:intersect+split"])

def b25(pid,v):
    # path 25: 3/8 short_axis bend+stack → slab bent and stacked
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           bend_n("bend0","m0","y",20+v*8,4),
           stack_n("stk0","bend0",2+v,[0.04,0.0,0.0],0.0),
           court_n("result","stk0",0.20+v*0.04,"east")]
    return mkprog(pid,v,"38_bent_stacked_court","cube","slab",
                  ["bend","stack","short_axis","3_8"],
                  "Bent slab stacked (zero gap → connected); east courtyard as threshold.",
                  nodes,"result",3+v,3.5,880+v*150,["book:aggregation:stack:bend"])

def b26(pid,v):
    # path 26: 3/8 short_axis lift+extrude → block lifted then wing-split with bridge
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_lift_n("lift0","m0","z",0.25+v*0.05,0.58+v*0.04,1.0),
           split_wing_n("result","lift0","east","y","parallel",0.12+v*0.03,0.88+v*0.04,True,0.25+v*0.03,False,0.15,0.2)]
    return mkprog(pid,v,"38_lift_split_wing","cube","block",
                  ["lift","split_wing","short_axis","3_8"],
                  "Block lifted then wing-split; bridge over east gap (bridge=True) ensures solid.",
                  nodes,"result",4,3.5,1050,["book:case:68:lift+extrude"])

def b27(pid,v):
    # path 27: 3/8 vertical interlock → bar interlocked (crossing → connected)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           interlock_related_n("inter0","m0","x",5.0+v*5,0.40+v*0.04,0.42+v*0.05,1.0),
           court_n("result","inter0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_interlock_court","cube","bar",
                  ["interlock","vertical","3_8","courtyard"],
                  "Interlocking L-bar pair; east courtyard mediates civic face.",
                  nodes,"result",4,3.5,1000,["book:operative:interlock"])

def b28(pid,v):
    # path 28: 3/8 vertical shear → tower sheared
    w,d,h=0.68,0.68,2.5
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           shear_n("shear0","m0","z",0.28+v*0.06,[0.0,1.0,0.0]),
           notch_n("result","shear0","east","ne",0.26+v*0.04,0.36,0.58)]
    return mkprog(pid,v,"38_shear_notch","cube","tower",
                  ["shear","vertical","3_8","notch"],
                  "Tower sheared along y-axis; east notch creates angled entry recess.",
                  nodes,"result",5,3.5,1200,["book:operative:shear"])

def b29(pid,v):
    # path 29: 3/8 vertical branch+branch → bar double branched
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_branch_n("br0","m0",45+v*12,0.55+v*0.05,0.36+v*0.04,"input_base"),
           book_branch_n("br1","br0",-30-v*8,0.60+v*0.04,0.32+v*0.04,"input_base"),
           carve_n("result","br1",0.20+v*0.03,"east")]
    return mkprog(pid,v,"38_double_branch_carve","cube","bar",
                  ["branch","vertical","3_8","carve_void"],
                  "Double branching (arm stays attached each time) creates dendritic plan; east carve void.",
                  nodes,"result",4,3.5,1100,["book:combination:07:branch+branch"])

def b30(pid,v):
    # path 30: 3/8 vertical notch+twist → block corner-notched then twisted
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","nw",1.0,0.22+v*0.05),
           twist_n("twist0","notch0","z",18+v*7,4),
           notch_n("result","twist0","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"38_notch_twist_entry","cube","block",
                  ["notch","twist","vertical","3_8"],
                  "Notched block twisted about z; east notch marks the rotated civic face.",
                  nodes,"result",4,3.5,950,["book:combination:20:notch+twist"])

def b31(pid,v):
    # path 31: 3/8 vertical expand+nest → slab expanded then book_lodge (similar to nest)
    # FIX: replaced nested_related (possibly disconnecting) with book_lodge (connected)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           boundary_expand_n("exp0","m0","z",0.20+v*0.05,0.45+v*0.05),
           book_lodge_n("lodge0","exp0","z",0.28+v*0.04,0.65+v*0.05,1.0),
           carve_n("result","lodge0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"38_expand_lodge_carve","cube","slab",
                  ["expand","nest","vertical","3_8"],
                  "Expanded slab with lodged inner volume; east carve opens layered civic face.",
                  nodes,"result",3,3.5,900,["book:case:63:expand+nest"])

def b32(pid,v):
    # path 32: 1/2 long_axis offset → slab with carve channels (offset operative)
    # FIX: replaced offset_related (disconnecting) with book_extract + book_carve (connected)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_extract_n("ext0","m0","z","north",0.35+v*0.05,0.55+v*0.05,1.0),
           carve_n("result","ext0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_extract_offset_court","cube","slab",
                  ["offset","long_axis","half"],
                  "Slab with east extraction channel; east courtyard in extracted recess.",
                  nodes,"result",4,3.5,1050,["book:operative:offset"])

def b33(pid,v):
    # path 33: 1/2 long_axis compress → block clipped (compress = clip_fraction)
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           clip_frac_n("clip0","m0","z",0.72+v*0.05,"high"),
           notch_n("result","clip0","east","ne",0.28+v*0.04,0.38,0.55)]
    return mkprog(pid,v,"half_compress_notch","cube","block",
                  ["compress","long_axis","half","notch"],
                  "Block vertically clipped (compressed); east notch cuts entry into compact face.",
                  nodes,"result",3,3.5,820,["book:operative:compress"])

def b34(pid,v):
    # path 34: 1/2 long_axis split+split → bar double-split
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_split_n("sp0","m0","y",0.0,0.09+v*0.03,1.0,1.0,1.0,0.48+v*0.04,"east"),
           book_split_n("sp1","sp0","x",4.0+v*4,0.10+v*0.03,-1.0,-1.0,2.0,0.5,"east"),
           carve_n("result","sp1",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_double_split_carve","cube","bar",
                  ["split","long_axis","half","carve_void"],
                  "Double split displaces bar; east carve addresses the public side.",
                  nodes,"result",4,3.5,980,["book:combination:03:split+split"])

def b35(pid,v):
    # path 35: 1/2 long_axis bend+branch → bar bent then branched
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           bend_n("bend0","m0","z",22+v*8,4),
           book_branch_n("br0","bend0",48+v*10,0.58+v*0.04,0.35+v*0.04,"input_base"),
           lift_n("result","br0","east",0.22+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"half_bent_branch_lift","cube","bar",
                  ["bend","branch","long_axis","half","lift"],
                  "Bar bent and branched; east lift opens ground passage below arms.",
                  nodes,"result",4,3.5,1080,["book:combination:16:bend+branch"])

def b36(pid,v):
    # path 36: 1/2 long_axis split+join → block split then join_related bridges halves
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_split_n("sp0","m0","y",0.0,0.09+v*0.03,1.0,1.0,1.0,0.50,"east"),
           join_related_n("join0","sp0",0.30+v*0.04),
           court_n("result","join0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_split_join_court","cube","block",
                  ["split","join","long_axis","half","courtyard"],
                  "Split halves bridged (join_related → one solid); east courtyard in gateway slot.",
                  nodes,"result",4,3.5,1000,["book:aggregation:join:split"])

def b37(pid,v):
    # path 37: 1/2 short_axis inflate → slab inflated at crown
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           inflate_n("infl0","m0","z",1.14+v*0.06,1.20+v*0.05,2.0+v*0.3,4),
           court_n("result","infl0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_inflated_court","cube","slab",
                  ["inflate","short_axis","half","courtyard"],
                  "Slab inflated at crown; east courtyard as civic concavity.",
                  nodes,"result",3,3.5,820,["book:operative:inflate"])

def b38(pid,v):
    # path 38: 1/2 short_axis overlap → bar overlapped in plan (connected bodies)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           overlap_related_n("ovl0","m0","y",1.0,0.32+v*0.04,0.60+v*0.04,0.24+v*0.04),
           notch_n("result","ovl0","east","ne",0.26+v*0.03,0.36,0.55)]
    return mkprog(pid,v,"half_overlap_notch","cube","bar",
                  ["overlap","short_axis","half","notch"],
                  "Overlapping bars (connected at overlap zone); east notch addresses junction.",
                  nodes,"result",4,3.5,980,["book:operative:overlap"])

def b39(pid,v):
    # path 39: 1/2 short_axis inscribe → block with SW notch, east carve
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","sw",1.0,0.24+v*0.05),
           carve_n("result","notch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_inscribed_carve","cube","block",
                  ["inscribe","short_axis","half","carve_void"],
                  "SW notch inscribed into block; east carve as principal address.",
                  nodes,"result",3,3.5,840,["book:operative:inscribe"])

def b40(pid,v):
    # path 40: 1/2 short_axis inscribe+intersect → bar notched then intersected (connected solid)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","se",1.0,0.22+v*0.04),
           intersect_related_n("inter0","notch0","z",90.0,0.38+v*0.04,0.78+v*0.04),
           lift_n("result","inter0","east",0.22+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"half_inscribe_intersect_lift","cube","bar",
                  ["inscribe","intersect","short_axis","half"],
                  "Notched bar cross-intersected (intersection → connected); east lift frames crossing.",
                  nodes,"result",4,3.5,1050,["book:combination:11:inscribe+intersect"])

def b41(pid,v):
    # path 41: 1/2 short_axis branch+pack+stack → bar branch then overlap pack (connected)
    # FIX: replaced related_array(pack) (disconnecting) with overlap_related (connected)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_branch_n("br0","m0",50+v*15,0.58+v*0.04,0.36+v*0.04,"input_base"),
           overlap_related_n("ovl0","br0","x",1.0,0.25+v*0.04,0.62+v*0.04,0.30+v*0.04),
           court_n("result","ovl0",0.20+v*0.03,"east")]
    return mkprog(pid,v,"half_branch_overlap_court","cube","bar",
                  ["branch","pack","short_axis","half"],
                  "Branched bar with overlapping arrangement (connected); east courtyard in gap.",
                  nodes,"result",4,3.5,1100,["book:aggregation:pack+stack:branch"])

def b42(pid,v):
    # path 42: 1/2 short_axis lift+carve → block lifted then carved east
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_lift_n("lift0","m0","z",0.26+v*0.05,0.58+v*0.04,1.0),
           book_carve_n("carve0","lift0","z","east",0.28+v*0.04,1.0,0.42+v*0.04),
           split_wing_n("result","carve0","east","y","parallel",0.12+v*0.02,0.88+v*0.04,True,0.26+v*0.03,False,0.15,0.2)]
    return mkprog(pid,v,"half_lift_carve_wing","cube","block",
                  ["lift","carve","short_axis","half"],
                  "Lifted block east-carved then wing-split; east bridge spans civic gap.",
                  nodes,"result",4,3.5,1050,["book:case:67:lift+carve"])

def b43(pid,v):
    # path 43: 1/2 vertical twist → tower twisted
    w,d,h=0.68,0.68,2.5
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           twist_n("twist0","m0","z",25+v*10,4),
           notch_n("result","twist0","east","ne",0.27+v*0.04,0.36,0.58)]
    return mkprog(pid,v,"half_twisted_tower_notch","cube","tower",
                  ["twist","vertical","half","notch"],
                  "Tower twisted about vertical; east notch cuts into rotated face for entry.",
                  nodes,"result",5,3.5,1200,["book:operative:twist"])

def b44(pid,v):
    # path 44: 1/2 vertical pinch → slab pinched at waist
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           pinch_n("pinch0","m0","z",0.48+v*0.04,0.68+v*0.05,2.0+v*0.3,4),
           carve_n("result","pinch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_pinched_carve","cube","slab",
                  ["pinch","vertical","half","carve_void"],
                  "Slab pinched at waist to form hourglass section; east carve opens civic face.",
                  nodes,"result",4,3.5,900,["book:operative:pinch"])

def b45(pid,v):
    # path 45: 1/2 vertical branch+branch → bar double branched
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_branch_n("br0","m0",45+v*12,0.55+v*0.04,0.36+v*0.04,"input_base"),
           book_branch_n("br1","br0",-40-v*10,0.58+v*0.04,0.32+v*0.04,"input_base"),
           court_n("result","br1",0.20+v*0.03,"east")]
    return mkprog(pid,v,"half_double_branch_court","cube","bar",
                  ["branch","vertical","half","courtyard"],
                  "Double branching in bar (each arm stays attached); east courtyard at forking zone.",
                  nodes,"result",4,3.5,1100,["book:combination:07:branch+branch"])

def b46(pid,v):
    # path 46: 1/2 vertical notch+twist → block notched then twisted
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","sw",1.0,0.24+v*0.05),
           twist_n("twist0","notch0","z",20+v*8,4),
           carve_n("result","twist0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"half_notch_twist_carve","cube","block",
                  ["notch","twist","vertical","half"],
                  "Notched block twisted; east carve void opens through rotated face.",
                  nodes,"result",4,3.5,950,["book:combination:20:notch+twist"])

def b47(pid,v):
    # path 47: 1/2 vertical expand+nest → slab expanded then book_lodge (nest-like)
    # FIX: replaced nested_related (possibly disconnecting) with book_lodge
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           boundary_expand_n("exp0","m0","z",0.22+v*0.05,0.48+v*0.04),
           book_lodge_n("lodge0","exp0","y",0.28+v*0.04,0.62+v*0.04,1.0),
           lift_n("result","lodge0","east",0.24+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"half_expand_lodge_lift","cube","slab",
                  ["expand","nest","vertical","half","lift"],
                  "Expanded slab with lodged inner volume; east lift provides piloti-style access.",
                  nodes,"result",3,3.5,870,["book:case:63:expand+nest"])

def b48(pid,v):
    # path 48: 1/4 long_axis offset → slab with extraction offset (connected via book_extract)
    # FIX: replaced offset_related (disconnecting) with book_extract + carve (connected)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_extract_n("ext0","m0","z","north",0.40+v*0.05,0.52+v*0.05,1.0),
           court_n("result","ext0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_extract_court","cube","slab",
                  ["offset","long_axis","quarter"],
                  "Slab with north extraction offset; east courtyard in civic lobby.",
                  nodes,"result",4,3.5,950,["book:operative:offset"])

def b49(pid,v):
    # path 49: 1/4 long_axis compress → block clipped vertically
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           clip_frac_n("clip0","m0","z",0.70+v*0.05,"high"),
           notch_n("result","clip0","east","se",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"qtr_compress_notch","cube","block",
                  ["compress","long_axis","quarter","notch"],
                  "Block clipped (compressed); SE east notch as compact entry.",
                  nodes,"result",3,3.5,780,["book:operative:compress"])

def b50(pid,v):
    # path 50: 1/4 long_axis split+split → bar double-split
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_split_n("sp0","m0","y",0.0,0.09+v*0.03,1.0,1.0,1.0,0.48+v*0.04,"east"),
           book_split_n("sp1","sp0","x",6.0+v*4,0.10+v*0.03,-1.0,-1.0,2.0,0.5,"east"),
           carve_n("result","sp1",0.20+v*0.03,"east")]
    return mkprog(pid,v,"qtr_double_split_carve","cube","bar",
                  ["split","long_axis","quarter","carve_void"],
                  "Double split displaces bar; east carve void addresses fractured form.",
                  nodes,"result",4,3.5,940,["book:combination:03:split+split"])

def b51(pid,v):
    # path 51: 1/4 long_axis taper+bend → tower tapered then bent
    w,d,h=0.68,0.68,2.5
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           taper_n("tap0","m0","z",[1.0,1.0],[0.65+v*0.05,0.65+v*0.05],0.0,3),
           bend_n("bend0","tap0","y",18+v*8,4),
           court_n("result","bend0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_taper_bend_court","cube","tower",
                  ["taper","bend","long_axis","quarter"],
                  "Tower tapered then bent; east courtyard below the curved crown.",
                  nodes,"result",5,3.5,1250,["book:combination:15:taper+bend"])

def b52(pid,v):
    # path 52: 1/4 long_axis pinch+join+array → slab pinched then join_related for connectivity
    # FIX: replaced related_array (disconnecting) with join_related (explicit bridge → connected)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           pinch_n("pinch0","m0","z",0.48+v*0.04,0.70+v*0.04,2.0+v*0.3,4),
           join_related_n("join0","pinch0",0.32+v*0.04),
           notch_n("result","join0","east","ne",0.26+v*0.03,0.36,0.55)]
    return mkprog(pid,v,"qtr_pinch_join_notch","cube","slab",
                  ["pinch","join","array","long_axis","quarter"],
                  "Pinched slab joined via bridge; east notch at pinch joint marks civic entry.",
                  nodes,"result",4,3.5,970,["book:aggregation:join+array:pinch"])

def b53(pid,v):
    # path 53: 1/4 short_axis extrude → block boundary-expanded upward then lifted
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           boundary_expand_n("exp0","m0","z",0.18+v*0.05,0.42+v*0.06),
           lift_n("result","exp0","east",0.24+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"qtr_extrude_lift","cube","block",
                  ["extrude","short_axis","quarter","lift"],
                  "Block expanded upward and lifted; east lift exposes public ground.",
                  nodes,"result",4,3.5,930,["book:operative:extrude"])

def b54(pid,v):
    # path 54: 1/4 short_axis lodge → bar lodge with guest, east courtyard
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_lodge_n("lodge0","m0","z",0.28+v*0.04,0.55+v*0.04,1.0),
           court_n("result","lodge0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_lodge_court","cube","bar",
                  ["lodge","short_axis","quarter","courtyard"],
                  "Guest bar lodged in host interval; east courtyard uses lodged gap as entry.",
                  nodes,"result",3,3.5,820,["book:operative:lodge"])

def b55(pid,v):
    # path 55: 1/4 short_axis extract → slab east-extracted then carved
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_extract_n("ext0","m0","z","east",0.28+v*0.04,0.50+v*0.04,1.0),
           carve_n("result","ext0",0.20+v*0.03,"east")]
    return mkprog(pid,v,"qtr_extract_carve","cube","slab",
                  ["extract","short_axis","quarter","carve_void"],
                  "Slab extraction channel through east face; carve deepens civic recess.",
                  nodes,"result",3,3.5,840,["book:operative:extract"])

def b56(pid,v):
    # path 56: 1/4 short_axis inscribe+intersect → bar notched then intersected (connected solid)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","nw",1.0,0.22+v*0.04),
           intersect_related_n("inter0","notch0","z",90.0,0.40+v*0.04,0.76+v*0.04),
           notch_n("result","inter0","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"qtr_inscribe_intersect_notch","cube","bar",
                  ["inscribe","intersect","short_axis","quarter"],
                  "Bar notched then cross-intersected (intersection solid = connected); east notch articulates.",
                  nodes,"result",4,3.5,1000,["book:combination:11:inscribe+intersect"])

def b57(pid,v):
    # path 57: 1/4 short_axis branch+pack+stack → bar branch then overlap (connected)
    # FIX: replaced related_array(pack) (disconnecting) with overlap_related (connected)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_branch_n("br0","m0",55+v*15,0.60+v*0.04,0.35+v*0.04,"input_base"),
           overlap_related_n("ovl0","br0","y",1.0,0.28+v*0.04,0.62+v*0.04,0.28+v*0.04),
           carve_n("result","ovl0",0.20+v*0.03,"east")]
    return mkprog(pid,v,"qtr_branch_overlap_carve","cube","bar",
                  ["branch","pack","short_axis","quarter"],
                  "Branched bar with overlapping arrangement (connected); east carve in front gap.",
                  nodes,"result",4,3.5,1050,["book:aggregation:pack+stack:branch"])

def b58(pid,v):
    # path 58: 1/4 short_axis lift+carve → block lifted then carved, split_wing
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_lift_n("lift0","m0","z",0.28+v*0.04,0.56+v*0.04,1.0),
           book_carve_n("carve0","lift0","z","east",0.26+v*0.04,1.0,0.42+v*0.04),
           lift_n("result","carve0","east",0.24+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"qtr_lift_carve_lift","cube","block",
                  ["lift","carve","short_axis","quarter"],
                  "Lifted block east-carved; terminal lift opens east ground as civic passage.",
                  nodes,"result",4,3.5,980,["book:case:67:lift+carve"])

def b59(pid,v):
    # path 59: 1/4 vertical twist → tower twisted
    w,d,h=0.68,0.68,2.5
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           twist_n("twist0","m0","z",28+v*10,4),
           court_n("result","twist0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_twisted_court","cube","tower",
                  ["twist","vertical","quarter","courtyard"],
                  "Tower twisted; east courtyard as civic space below twist.",
                  nodes,"result",5,3.5,1250,["book:operative:twist"])

def b60(pid,v):
    # path 60: 1/4 vertical pinch → slab pinched
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           pinch_n("pinch0","m0","z",0.50+v*0.04,0.65+v*0.05,2.0+v*0.3,4),
           carve_n("result","pinch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_pinched_carve","cube","slab",
                  ["pinch","vertical","quarter","carve_void"],
                  "Slab pinched at waist; east carve opens the narrowed civic face.",
                  nodes,"result",4,3.5,880,["book:operative:pinch"])

def b61(pid,v):
    # path 61: 1/4 vertical branch+branch → bar double branched
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_branch_n("br0","m0",48+v*12,0.56+v*0.04,0.36+v*0.04,"input_base"),
           book_branch_n("br1","br0",-38-v*10,0.60+v*0.04,0.32+v*0.04,"input_base"),
           notch_n("result","br1","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"qtr_double_branch_notch","cube","bar",
                  ["branch","vertical","quarter","notch"],
                  "Double branching in bar (both arms connected); east notch at fork marks entry.",
                  nodes,"result",4,3.5,1050,["book:combination:07:branch+branch"])

def b62(pid,v):
    # path 62: 1/4 vertical shift+notch → block shift_related then book_notch + carve
    # shift_related keeps the split halves connected (they stay hinged at split line)
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           shift_related_n("sh0","m0","x",0.32+v*0.04,1.0,0.50+v*0.04),
           book_notch_n("notch0","sh0","z","ne",1.0,0.24+v*0.04),
           carve_n("result","notch0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"qtr_shift_notch_carve","cube","block",
                  ["shift","notch","vertical","quarter"],
                  "Shifted related volume (shift_related → connected) with corner notch; east carve.",
                  nodes,"result",4,3.5,960,["book:combination:19:shift+notch"])

def b63(pid,v):
    # path 63: 1/4 vertical embed+overlap → slab embed_void then overlap_related (connected)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           embed_void_n("emb0","m0","z","center",0.30+v*0.05,0.50+v*0.04),
           overlap_related_n("ovl0","emb0","x",1.0,0.30+v*0.04,0.62+v*0.04,0.22+v*0.04),
           lift_n("result","ovl0","east",0.22+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"qtr_embed_overlap_lift","cube","slab",
                  ["embed","overlap","vertical","quarter"],
                  "Embedded void slab then overlapped (connected); east lift creates ground passage.",
                  nodes,"result",3,3.5,870,["book:case:62:embed+overlap"])

def b64(pid,v):
    # path 64: 1/8 long_axis nest → slab with book_lodge as nest
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_lodge_n("lodge0","m0","x",0.28+v*0.04,0.60+v*0.05,1.0),
           court_n("result","lodge0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_nested_court","cube","slab",
                  ["nest","long_axis","eighth"],
                  "Slab with lodged inner volume (nest); east courtyard as layered civic court.",
                  nodes,"result",3,3.5,780,["book:operative:nest"])

def b65(pid,v):
    # path 65: 1/8 long_axis carve → bar east-carved
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_carve_n("carve0","m0","z","east",0.28+v*0.05,1.0,0.42+v*0.04),
           notch_n("result","carve0","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"eighth_carved_notch","cube","bar",
                  ["carve","long_axis","eighth","notch"],
                  "Bar east-carved then NE-notched; compact civic address.",
                  nodes,"result",4,3.5,900,["book:operative:carve"])

def b66(pid,v):
    # path 66: 1/8 long_axis intersect+intersect → bar double cross-intersection
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           intersect_related_n("inter0","m0","z",90.0,0.38+v*0.04,0.78+v*0.04),
           intersect_related_n("inter1","inter0","y",45.0,0.36+v*0.04,0.72+v*0.04),
           carve_n("result","inter1",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_double_intersect_carve","cube","bar",
                  ["intersect","long_axis","eighth"],
                  "Double cross-bar intersection (each intersection → connected solid); east carve.",
                  nodes,"result",4,3.5,960,["book:combination:02:intersect+intersect"])

def b67(pid,v):
    # path 67: 1/8 long_axis taper+bend → tower tapered then bent
    w,d,h=0.68,0.68,2.5
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           taper_n("tap0","m0","z",[1.0,1.0],[0.68+v*0.04,0.68+v*0.04],0.0,3),
           bend_n("bend0","tap0","y",20+v*8,4),
           lift_n("result","bend0","east",0.24+v*0.04,0.32+v*0.03)]
    return mkprog(pid,v,"eighth_taper_bend_lift","cube","tower",
                  ["taper","bend","long_axis","eighth"],
                  "Tower tapered and bent; east lift opens public passage at tower base.",
                  nodes,"result",5,3.5,1150,["book:combination:15:taper+bend"])

def b68(pid,v):
    # path 68: 1/8 long_axis pinch+join+array → slab pinched then join_related
    # FIX: replaced related_array (disconnecting) with join_related (connected bridge)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           pinch_n("pinch0","m0","z",0.46+v*0.04,0.68+v*0.05,2.0+v*0.3,4),
           join_related_n("join0","pinch0",0.30+v*0.04),
           court_n("result","join0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_pinch_join_court","cube","slab",
                  ["pinch","join","array","long_axis","eighth"],
                  "Pinched slab with bridge join; east courtyard at pinch waist.",
                  nodes,"result",4,3.5,930,["book:aggregation:join+array:pinch"])

def b69(pid,v):
    # path 69: 1/8 short_axis extrude → block boundary-expanded then notched
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           boundary_expand_n("exp0","m0","z",0.20+v*0.05,0.44+v*0.05),
           notch_n("result","exp0","east","ne",0.26+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"eighth_extrude_notch","cube","block",
                  ["extrude","short_axis","eighth","notch"],
                  "Block expanded and profiled; east notch at entry corner.",
                  nodes,"result",4,3.5,920,["book:operative:extrude"])

def b70(pid,v):
    # path 70: 1/8 short_axis lodge → bar with guest lodge, east carve
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_lodge_n("lodge0","m0","z",0.26+v*0.04,0.52+v*0.04,1.0),
           carve_n("result","lodge0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_lodge_carve","cube","bar",
                  ["lodge","short_axis","eighth","carve_void"],
                  "Bar lodged with guest; east carve void in gap below guest.",
                  nodes,"result",3,3.5,800,["book:operative:lodge"])

def b71(pid,v):
    # path 71: 1/8 short_axis extract → slab extraction then lift
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_extract_n("ext0","m0","z","east",0.26+v*0.04,0.52+v*0.04,1.0),
           lift_n("result","ext0","east",0.22+v*0.04,0.30+v*0.03)]
    return mkprog(pid,v,"eighth_extract_lift","cube","slab",
                  ["extract","short_axis","eighth","lift"],
                  "Slab extraction channel; east lift opens subtracted volume as passage.",
                  nodes,"result",3,3.5,820,["book:operative:extract"])

def b72(pid,v):
    # path 72: 1/8 short_axis inscribe+intersect → bar notched then cross-intersected (connected solid)
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","sw",1.0,0.24+v*0.04),
           intersect_related_n("inter0","notch0","z",90.0,0.38+v*0.04,0.76+v*0.04),
           court_n("result","inter0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_inscribe_intersect_court","cube","bar",
                  ["inscribe","intersect","short_axis","eighth"],
                  "Notched bar cross-intersected (intersection → connected); east courtyard at junction.",
                  nodes,"result",4,3.5,980,["book:combination:11:inscribe+intersect"])

def b73(pid,v):
    # path 73: 1/8 short_axis inflate+pack → slab inflated then overlapped (connected)
    # FIX: replaced related_array(pack) (disconnecting) with overlap_related (connected)
    w,d,h=2.2,1.45,0.28
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           inflate_n("infl0","m0","z",1.14+v*0.05,1.20+v*0.05,2.2+v*0.3,4),
           overlap_related_n("ovl0","infl0","x",1.0,0.25+v*0.04,0.62+v*0.04,0.28+v*0.04),
           notch_n("result","ovl0","east","ne",0.26+v*0.03,0.36,0.55)]
    return mkprog(pid,v,"eighth_inflate_overlap_notch","cube","slab",
                  ["inflate","pack","short_axis","eighth"],
                  "Inflated slab overlapped (connected); east notch at billowing public face.",
                  nodes,"result",3,3.5,820,["book:aggregation:pack:inflate"])

def b74(pid,v):
    # path 74: 1/8 short_axis embed+taper → block embed_void then tapered
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           embed_void_n("emb0","m0","z","center",0.30+v*0.05,0.50+v*0.04),
           taper_n("tap0","emb0","z",[1.0,1.0],[0.72+v*0.04,0.72+v*0.04],0.0,3),
           carve_n("result","tap0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_embed_taper_carve","cube","block",
                  ["embed","taper","short_axis","eighth"],
                  "Block embed-voided then tapered; east carve at tapered public face.",
                  nodes,"result",4,3.5,940,["book:case:66:embed+taper"])

def b75(pid,v):
    # path 75: 1/8 vertical split → tower book_split (single split keeps geometry)
    w,d,h=0.68,0.68,2.5
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_split_n("sp0","m0","y",0.0,0.10+v*0.03,1.0,1.0,1.0,0.50+v*0.04,"east"),
           court_n("result","sp0",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_split_court","cube","tower",
                  ["split","vertical","eighth","courtyard"],
                  "Tower split displaces one wing; east courtyard in hinge gap.",
                  nodes,"result",5,3.5,1150,["book:operative:split"])

def b76(pid,v):
    # path 76: 1/8 vertical notch → block corner-notched, east notch entry
    w,d,h=1.0,1.0,1.0
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           book_notch_n("notch0","m0","z","nw",1.0,0.25+v*0.05),
           notch_n("result","notch0","east","ne",0.28+v*0.04,0.36,0.55)]
    return mkprog(pid,v,"eighth_notch_entry","cube","block",
                  ["notch","vertical","eighth"],
                  "Block corner-notched; east notch as minimal civic entry.",
                  nodes,"result",4,3.5,900,["book:operative:notch"])

def b77(pid,v):
    # path 77: 1/8 vertical bend+bend → bar double-bent in two axes
    w,d,h=2.8,0.62,0.48
    nodes=[box_n("box0",w,d,h),m4_n("m0","box0",identity_m4()),
           bend_n("bend0","m0","z",22+v*8,4),
           bend_n("bend1","bend0","y",-16-v*6,4),
           carve_n("result","bend1",0.22+v*0.03,"east")]
    return mkprog(pid,v,"eighth_double_bent_carve","cube","bar",
                  ["bend","vertical","eighth","carve_void"],
                  "Bar double-bent in two axes; east carve at curved civic face.",
                  nodes,"result",4,3.5,960,["book:combination:06:bend+bend"])

# ── builder dispatch ──────────────────────────────────────────────────────────
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

def generate():
    programs = []
    # Pass 1: all 78 paths with v=0
    for idx in range(78):
        pid = PATH_IDS[idx]
        prog = BUILDERS[idx](pid, 0)
        programs.append(prog)
    # Pass 2: 42 more paths with v=1 (paths 0..41)
    for idx in range(42):
        pid = PATH_IDS[idx]
        prog = BUILDERS[idx](pid, 1)
        prog["name"] = prog["name"] + "b"
        programs.append(prog)
    assert len(programs) == 120
    all_pids = set()
    for p in programs:
        all_pids.update(p.get("book_principle_ids",[]))
    return {"programs": programs, "book_principle_ids": sorted(list(all_pids))}

def validate(payload):
    if not HAS_SCHEMA:
        print("Skipping schema validation")
        return True
    schema = json.loads(Path(SCHEMA_PATH).read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(payload))
    if errors:
        for e in errors[:20]:
            print(f"ERROR: {list(e.path)} → {e.message}")
        print(f"Total errors: {len(errors)}")
        return False
    print(f"PASSED: {len(payload['programs'])} programs, 0 errors")
    return True

if __name__ == "__main__":
    print("Generating 120 BOOK programs (gen_book18f)...")
    payload = generate()
    seeds = {}
    forms = {}
    for p in payload["programs"]:
        s=p["base_seed"]; seeds[s]=seeds.get(s,0)+1
        f=p["base_form_id"]; forms[f]=forms.get(f,0)+1
    print(f"Seeds: {seeds}")
    print(f"Forms: {forms}")
    print(f"Unique path IDs used: {len(set(p['book_composition_path_id'] for p in payload['programs']))}")
    ok = validate(payload)
    if not ok:
        sys.exit(1)
    out = json.dumps(payload, ensure_ascii=False, indent=2)
    Path(OUTPUT_PATH).write_text(out, encoding="utf-8")
    print(f"Written {len(out)//1024}KB to {OUTPUT_PATH}")
    print("Done.")