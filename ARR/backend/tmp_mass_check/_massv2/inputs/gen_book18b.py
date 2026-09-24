"""
Generate book-comp18.json with 120 BOOK programs.
Each program is a dict with required keys per schema.
"""
import json

def I(): return [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
def S(s): return [[s,0,0,0],[0,s,0,0],[0,0,s,0],[0,0,0,1]]
def dim(n,h,g): return {"schema_version":"arr.maas.dimensional_intent.v1","storey_count":n,"storey_height_m":h,"target_gfa_m2":g,"delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}
def BOX(id,w,d,h): return {"id":id,"kind":"primitive","operator":"box","inputs":[],"parameters":[{"name":"width","value_type":"number","numeric_value":w},{"name":"depth","value_type":"number","numeric_value":d},{"name":"height","value_type":"number","numeric_value":h},{"name":"center","value_type":"boolean","boolean_value":True}],"semantic_role":"dominant_mass"}
def MAT(id,inp,m): return {"id":id,"kind":"transform","operator":"matrix4","inputs":[inp],"parameters":[{"name":"matrix4","value_type":"matrix4","matrix4_value":m}],"semantic_role":"dominant_mass"}
def CY(id,inp,mg,os,role="public_threshold"): return {"id":id,"kind":"composition","operator":"courtyard","inputs":[inp],"parameters":[{"name":"margin_ratio","value_type":"number","numeric_value":mg},{"name":"open_side","value_type":"string","string_value":os}],"semantic_role":role}
def CV(id,inp,mg,os): return {"id":id,"kind":"composition","operator":"carve_void","inputs":[inp],"parameters":[{"name":"margin_ratio","value_type":"number","numeric_value":mg},{"name":"open_side","value_type":"string","string_value":os}],"semantic_role":"public_threshold"}
def NT(id,inp,side,r,wr,hr): return {"id":id,"kind":"composition","operator":"notch","inputs":[inp],"parameters":[{"name":"side","value_type":"string","string_value":side},{"name":"ratio","value_type":"number","numeric_value":r},{"name":"width_ratio","value_type":"number","numeric_value":wr},{"name":"height_ratio","value_type":"number","numeric_value":hr}],"semantic_role":"public_threshold"}
def LF(id,inp,rise,sup,side): return {"id":id,"kind":"composition","operator":"lift","inputs":[inp],"parameters":[{"name":"rise_ratio","value_type":"number","numeric_value":rise},{"name":"support_ratio","value_type":"number","numeric_value":sup},{"name":"access_side","value_type":"string","string_value":side}],"semantic_role":"public_threshold"}
def SH(id,inp,amt,ax,dr): return {"id":id,"kind":"transform","operator":"shear","inputs":[inp],"parameters":[{"name":"amount","value_type":"number","numeric_value":amt},{"name":"axis","value_type":"string","string_value":ax},{"name":"direction","value_type":"string","string_value":dr}],"semantic_role":"dominant_mass"}
def TW(id,inp,ax,ang,sub=4): return {"id":id,"kind":"modifier","operator":"twist","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"angle_degrees","value_type":"number","numeric_value":ang},{"name":"subdivisions","value_type":"number","numeric_value":sub}],"semantic_role":"dominant_mass"}
def TP(id,inp,ax,es): return {"id":id,"kind":"modifier","operator":"taper","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"end_scale","value_type":"vector","vector_value":es},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"}
def BN(id,inp,ax,ang,sub=4): return {"id":id,"kind":"modifier","operator":"bend","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"angle_degrees","value_type":"number","numeric_value":ang},{"name":"subdivisions","value_type":"number","numeric_value":sub}],"semantic_role":"dominant_mass"}
def IF(id,inp,ax,f,ms,sub=4): return {"id":id,"kind":"modifier","operator":"inflate","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"factor","value_type":"number","numeric_value":f},{"name":"middle_scale","value_type":"number","numeric_value":ms},{"name":"subdivisions","value_type":"number","numeric_value":sub}],"semantic_role":"dominant_mass"}
def STK(id,inp,cnt,shift,sp=0.01): return {"id":id,"kind":"pattern","operator":"stack","inputs":[inp],"parameters":[{"name":"count","value_type":"number","numeric_value":cnt},{"name":"shift_per_level","value_type":"vector","vector_value":shift},{"name":"spacing","value_type":"number","numeric_value":sp}],"semantic_role":"program_space"}
def PN(id,inp,ax,wr,ws,sub=4): return {"id":id,"kind":"modifier","operator":"pinch","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"waist_ratio","value_type":"number","numeric_value":wr},{"name":"waist_scale","value_type":"number","numeric_value":ws},{"name":"subdivisions","value_type":"number","numeric_value":sub}],"semantic_role":"dominant_mass"}
def BR(id,inp,tr,ar,ang): return {"id":id,"kind":"modifier","operator":"book_branch","inputs":[inp],"parameters":[{"name":"trunk_ratio","value_type":"number","numeric_value":tr},{"name":"arm_ratio","value_type":"number","numeric_value":ar},{"name":"angle_degrees","value_type":"number","numeric_value":ang},{"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"dominant_mass"}
def BBNR(id,inp,tr,ar,ang): 
    n = BR(id,inp,tr,ar,ang); n["semantic_role"]="public_threshold"; return n
def FRAC(id,inp,ax,gr,fs,os=1.0,rb=0.5): return {"id":id,"kind":"modifier","operator":"book_fracture","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"gap_ratio","value_type":"number","numeric_value":gr},{"name":"face_side","value_type":"string","string_value":fs},{"name":"outward_sign","value_type":"number","numeric_value":os},{"name":"retained_back_ratio","value_type":"number","numeric_value":rb}],"semantic_role":"dominant_mass"}
def ILK(id,inp,ax,ang,br,dr): return {"id":id,"kind":"modifier","operator":"interlock_related","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"angle_degrees","value_type":"number","numeric_value":ang},{"name":"bar_ratio","value_type":"number","numeric_value":br},{"name":"distance_ratio","value_type":"number","numeric_value":dr},{"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"}
def ISR(id,inp,ax,ang,br,us): return {"id":id,"kind":"modifier","operator":"intersect_related","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"angle_degrees","value_type":"number","numeric_value":ang},{"name":"bar_ratio","value_type":"number","numeric_value":br},{"name":"unit_scale","value_type":"number","numeric_value":us}],"semantic_role":"dominant_mass"}
def OVR(id,inp,ax,sr,shr,vo): return {"id":id,"kind":"modifier","operator":"overlap_related","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"slab_ratio","value_type":"number","numeric_value":sr},{"name":"shift_ratio","value_type":"number","numeric_value":shr},{"name":"vertical_overlap","value_type":"number","numeric_value":vo},{"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"}
def BEXP(id,inp,amt,ax,sf=None):
    p=[{"name":"amount","value_type":"number","numeric_value":amt},{"name":"axis","value_type":"string","string_value":ax}]
    if sf is not None: p.append({"name":"shoulder_fraction","value_type":"number","numeric_value":sf})
    return {"id":id,"kind":"modifier","operator":"boundary_expand","inputs":[inp],"parameters":p,"semantic_role":"dominant_mass"}
def BEXPPS(id,inp,amt,ax,sf=None):
    n = BEXP(id,inp,amt,ax,sf); n["semantic_role"]="program_space"; return n
def EMBV(id,inp,ax,gs,er,pos="center"): return {"id":id,"kind":"modifier","operator":"embed_void","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"guest_scale","value_type":"number","numeric_value":gs},{"name":"embedded_ratio","value_type":"number","numeric_value":er},{"name":"outward_sign","value_type":"number","numeric_value":1.0},{"name":"position","value_type":"string","string_value":pos}],"semantic_role":"dominant_mass"}
def LIFT(id,inp,ax,dr,gs): return {"id":id,"kind":"modifier","operator":"book_lift","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"distance_ratio","value_type":"number","numeric_value":dr},{"name":"guest_scale","value_type":"number","numeric_value":gs},{"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"}
def ROT(id,inp,ax,ang,rr): return {"id":id,"kind":"modifier","operator":"book_rotate","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"angle_degrees","value_type":"number","numeric_value":ang},{"name":"related_ratio","value_type":"number","numeric_value":rr},{"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"}
def BBNOT(id,inp,ax,corner,r): return {"id":id,"kind":"modifier","operator":"book_notch","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"corner","value_type":"string","string_value":corner},{"name":"ratio","value_type":"number","numeric_value":r},{"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"dominant_mass"}
def BCAR(id,inp,ax,fs,wr,dr,os=1.0): return {"id":id,"kind":"modifier","operator":"book_carve","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"face_side","value_type":"string","string_value":fs},{"name":"width_ratio","value_type":"number","numeric_value":wr},{"name":"depth_ratio","value_type":"number","numeric_value":dr},{"name":"outward_sign","value_type":"number","numeric_value":os}],"semantic_role":"program_space"}
def BGRADE(id,inp,ax,fs,wr,dr,lv,os=1.0): return {"id":id,"kind":"modifier","operator":"book_grade","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"face_side","value_type":"string","string_value":fs},{"name":"width_ratio","value_type":"number","numeric_value":wr},{"name":"depth_ratio","value_type":"number","numeric_value":dr},{"name":"levels","value_type":"number","numeric_value":lv},{"name":"outward_sign","value_type":"number","numeric_value":os}],"semantic_role":"dominant_mass"}
def BSPLIT(id,inp,ax,gr,ang,bs,os,tr,sg,side): return {"id":id,"kind":"modifier","operator":"book_split","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"gap_ratio","value_type":"number","numeric_value":gr},{"name":"angle_degrees","value_type":"number","numeric_value":ang},{"name":"branch_sign","value_type":"number","numeric_value":bs},{"name":"outward_sign","value_type":"number","numeric_value":os},{"name":"terminal_ratio","value_type":"number","numeric_value":tr},{"name":"split_generation","value_type":"number","numeric_value":sg},{"name":"access_side","value_type":"string","string_value":side}],"semantic_role":"public_threshold"}
def BSPLITD(id,inp,ax,gr,ang,bs,os,tr,sg): 
    n = BSPLIT(id,inp,ax,gr,ang,bs,os,tr,sg,"closed"); n["semantic_role"]="dominant_mass"; return n
def OFFRR(id,inp,ax,dr,us): return {"id":id,"kind":"modifier","operator":"offset_related","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"distance_ratio","value_type":"number","numeric_value":dr},{"name":"unit_scale","value_type":"number","numeric_value":us},{"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"program_space"}
def MIRR(id,inp,n,p): return {"id":id,"kind":"transform","operator":"mirror_array","inputs":[inp],"parameters":[{"name":"normal","value_type":"vector","vector_value":n},{"name":"pivot","value_type":"vector","vector_value":p}],"semantic_role":"program_space"}
def NEST(id,inp,ax,dr,us): return {"id":id,"kind":"modifier","operator":"nested_related","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"distance_ratio","value_type":"number","numeric_value":dr},{"name":"unit_scale","value_type":"number","numeric_value":us}],"semantic_role":"program_space"}
def ELL(id,inp,seg=20): return {"id":id,"kind":"modifier","operator":"ellipsoidize","inputs":[inp],"parameters":[{"name":"segments","value_type":"number","numeric_value":seg}],"semantic_role":"dominant_mass"}
def TET(id,inp): return {"id":id,"kind":"modifier","operator":"tetrahedralize","inputs":[inp],"parameters":[],"semantic_role":"dominant_mass"}
def PTAPR(id,inp,ax,es): return {"id":id,"kind":"modifier","operator":"tapered_tower","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"end_scale","value_type":"vector","vector_value":es},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"}
def CLIP(id,inp,ax,f,anc): return {"id":id,"kind":"modifier","operator":"clip_fraction","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"fraction","value_type":"number","numeric_value":f},{"name":"anchor","value_type":"string","string_value":anc}],"semantic_role":"dominant_mass"}
def SHREL(id,inp,ax,dr,spr,os=1.0): return {"id":id,"kind":"modifier","operator":"shift_related","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"distance_ratio","value_type":"number","numeric_value":dr},{"name":"split_ratio","value_type":"number","numeric_value":spr},{"name":"outward_sign","value_type":"number","numeric_value":os}],"semantic_role":"dominant_mass"}
def EXTR(id,inp,ax,fs,dr,gs): return {"id":id,"kind":"modifier","operator":"book_extract","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"face_side","value_type":"string","string_value":fs},{"name":"distance_ratio","value_type":"number","numeric_value":dr},{"name":"guest_scale","value_type":"number","numeric_value":gs},{"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"program_space"}
def LODGE(id,inp,ax,dr,gs): return {"id":id,"kind":"modifier","operator":"book_lodge","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"distance_ratio","value_type":"number","numeric_value":dr},{"name":"guest_scale","value_type":"number","numeric_value":gs},{"name":"outward_sign","value_type":"number","numeric_value":1.0}],"semantic_role":"program_space"}
def RELARRAY(id,inp,ax,cnt,mode,spr): return {"id":id,"kind":"pattern","operator":"related_array","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"count","value_type":"number","numeric_value":cnt},{"name":"mode","value_type":"string","string_value":mode},{"name":"spacing_ratio","value_type":"number","numeric_value":spr},{"name":"unit_scale","value_type":"number","numeric_value":1.0},{"name":"vertical_anchor","value_type":"string","string_value":"input_base"}],"semantic_role":"program_space"}
def JOIN(id,inp,br): return {"id":id,"kind":"composition","operator":"join_related","inputs":[inp],"parameters":[{"name":"bridge_ratio","value_type":"number","numeric_value":br}],"semantic_role":"public_threshold"}
def PUNC(id,inp,ax,cnt,r,spr): return {"id":id,"kind":"modifier","operator":"puncture","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"count","value_type":"number","numeric_value":cnt},{"name":"ratio","value_type":"number","numeric_value":r},{"name":"spacing_ratio","value_type":"number","numeric_value":spr}],"semantic_role":"program_space"}
def LINARRAY(id,inp,cnt,vec): return {"id":id,"kind":"pattern","operator":"linear_array","inputs":[inp],"parameters":[{"name":"count","value_type":"number","numeric_value":cnt},{"name":"vector","value_type":"vector","vector_value":vec},{"name":"spacing","value_type":"number","numeric_value":0.0}],"semantic_role":"program_space"}
def BENTSW(id,inp): return {"id":id,"kind":"modifier","operator":"bent_bar","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"angle_degrees","value_type":"number","numeric_value":28},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"}
def SPLITWING(id,inp,ax,layout,hr,gr,bridge,side): return {"id":id,"kind":"modifier","operator":"split_wing","inputs":[inp],"parameters":[{"name":"axis","value_type":"string","string_value":ax},{"name":"layout","value_type":"string","string_value":layout},{"name":"height_ratio","value_type":"number","numeric_value":hr},{"name":"gap_ratio","value_type":"number","numeric_value":gr},{"name":"bridge","value_type":"boolean","boolean_value":bridge},{"name":"access_side","value_type":"string","string_value":side}],"semantic_role":"public_threshold"}
def CANTILEVER(id,inp,vec,sr): return {"id":id,"kind":"modifier","operator":"cantilever","inputs":[inp],"parameters":[{"name":"vector","value_type":"vector","vector_value":vec},{"name":"start_ratio","value_type":"number","numeric_value":sr}],"semantic_role":"public_threshold"}

SLAB=(2.2,1.45,0.28); BAR=(2.8,0.62,0.48); BLOCK=(1.0,1.0,1.0); TOWER=(0.68,0.68,2.5)

programs = []

def add(name,bfi,bs,tags,path,rat,d_intent,nodes):
    programs.append({"name":name,"base_form_id":bfi,"base_seed":bs,"intent_tags":tags,
        "book_composition_path_id":path,"rationale":rat,"dimensional_intent":d_intent,
        "nodes":nodes,"root_id":"result"})

# PATHS available (used one per program, no repeats):
# Path pool (60 unique paths from offer):
paths = [
    "book:path:9bab887f2e519077dcbe8e5977897df8a80deb6d1a280936cccca005d8555719",  # 0 bend long 1/1
    "book:path:9042c82e97a383fc1f1e97948ac87e0bac17a95d0d8587255d48710c0ac64040",  # 1 fracture long 1/1
    "book:path:11a0d7a5a51e85d9ec1cf2f3b3eaa086eb6841d1fec6a184077cc5db1851b185",  # 2 embed+embed long 1/1
    "book:path:dd28b0c53f08a2d1812dc32d7b562ee9b7bc4a1ca98b90a13152bbf534dd27f2",  # 3 branch+expand long 1/1
    "book:path:c7fcd0c126b7b32471e69e703e7e9022ab3963899ef974c879ec44b4162b197a",  # 4 carve+offset long 1/1
    "book:path:b95277004fb2b89b21445182aab353c444a4ea7a1e7044f8c2e7e07599226909",  # 5 branch short 1/1
    "book:path:6bb95e7e0461e1606d4430a1e8a7c4ad2b3dc96d74ff48bced73da05b9df6cf5",  # 6 rotate short 1/1
    "book:path:2f971be29f0d428a9879b1c00948ac738f8921db4163797414074d894ac8efb9",  # 7 inscribe short 1/1
    "book:path:e510ad256385b556152790586ff8d15493cf9c1d6cffbd352f8e0d326c4ca71a",  # 8 intersect+split short 1/1
    "book:path:53c55b4da48903af110459fa120baeaec3b186edf22d6890fa718d0ad6b1f5b5",  # 9 bend+stack short 1/1
    "book:path:f285f713076b19ee7cc1b58f2d44f85aeec8a11bfe30fc0b77e876a1543a612b", # 10 lift+extrude short 1/1
    "book:path:05470e618703ead632e6029bac7312306f05a6f404cb1a84f60043e0fb2b6b5f", # 11 interlock vertical 1/1
    "book:path:ff644fb6db1684200f7c558764b8298c45bab946fac40c3df9cc090edf479977", # 12 shear vertical 1/1
    "book:path:61ddaacb14d1ebd0e0c24518a19a9b01f9a48f50fbfd66fd280b92abe59722b7", # 13 expand+expand vertical 1/1
    "book:path:2e2f65a3f44c510ecfa66c729db4c53684b3cc4033f5844bc980f4fa4bf1ad70", # 14 expand+reflect vertical 1/1
    "book:path:aadaf4340a4980ec0c691cf6c70bf78936b4b4b1471a6340d384abcae9ee0a2c", # 15 overlap+expand vertical 1/1
    "book:path:2e24111503e808e954bf437374af114ede99fddb568beab59253edb011273835", # 16 bend long 3/8
    "book:path:84d0345cadb3c43a13aa423bc1fddfb175b338b095c86bc9ec4b1eab2952afd0", # 17 fracture long 3/8
    "book:path:b96fa24e6b07a0419331b82a471addcf0f980f71d6fee1bffd80a5e1ed1ea126", # 18 split+split long 3/8
    "book:path:b5ca07c63bd9437f0b85f18355a83a85b02d1529169ff6667d786630774fe76e", # 19 bend+branch long 3/8
    "book:path:2fcf5f31e6d7ec9acbe02f9c3a6bb20e72df122cf29d989dd630f4d7fc022791", # 20 split+join long 3/8
    "book:path:423e633a08a43369b6ccda29d5604fc061c6e20e52e460c9867ddd1e5b13c2c0", # 21 inflate short 3/8
    "book:path:6acac573694cb27de1572fd0a9de5fb76aed871fea929c88573a072c95a8bbbb", # 22 overlap short 3/8
    "book:path:1dbb96b395ddd04b17719976be7a62b1bdb6256f080c74a7b0de12c908a7915c", # 23 inscribe short 3/8
    "book:path:f91a61a346c29c85aa4907c5e5c53d10e00a7530d28316c598fcc29d75f7fb55", # 24 intersect+split short 3/8
    "book:path:13fbf6da4b2addf28d4678956f747d8f112740ed2ca07de19e7a4884b2d43956", # 25 bend+stack short 3/8
    "book:path:4542c2a1884b1b256fbdea6e3ffd434dac31db9212deb3a328bb168fcfc1a6e4", # 26 lift+extrude short 3/8
    "book:path:e1e90099b5d07535d9361727c7d4b028f702499491b0588fdb2c926912013fb5", # 27 interlock vertical 3/8
    "book:path:f7755521cc02b4d565cddffa435faa30d79095ee7d62ce0588cbc8fc33fa2b6f", # 28 shear vertical 3/8
    "book:path:def59b665a24ebd51c08a3812668edc1a6131552a8055b2d7cb88de8de90f4f5", # 29 branch+branch vertical 3/8
    "book:path:3ab1e90c58b2293f63e75df8acabb9308b747cd6304c4511b2a47ed9ce8821c3", # 30 notch+twist vertical 3/8
    "book:path:cfeca7238d109f8ccf184e9ab42319aadf2d36f2aca116ba295ae47cbb6ca11b", # 31 expand+nest vertical 3/8
    "book:path:08e14d9ef6f30e7f2700d6e5f895d4911944adbfd16a0477dbfee0afeebfbf70", # 32 offset long 1/2
    "book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb", # 33 compress long 1/2
    "book:path:60778ae3e99cf12bb7e8461f50ee3332b7a47ed4893d70cb2d8400fd22cc49cf", # 34 split+split long 1/2
    "book:path:0b828fd1f09aeb9b5e3096a6cfe15c3cf1d709a475844690e9f3085fbdb9b8b1", # 35 bend+branch long 1/2
    "book:path:d2cb499b7d8b00c2ace3d4b6893bc583e2307d3d6cdb0ac96b319253fe0529c4", # 36 split+join long 1/2
    "book:path:eccfafc4718361d6aec40a901f53b344d4bff77683f4887715da5adcce05157f", # 37 inflate short 1/2
    "book:path:c15ec55248a4fc32d3f15fea2da9b94c5831c48f2dedecef91ddf03a61f04ef1", # 38 overlap short 1/2
    "book:path:591a729db54894dfd9449b5e5f08781d509ee6da02353d574828e141854ef1fe", # 39 inscribe short 1/2
    "book:path:a34184c51ffd9faa6f4e694bd0df018b4499f561be4b29d1f086e7b8361fd7b7", # 40 inscribe+intersect short 1/2
    "book:path:9c9d6d2d18bf525d39eb0c2299651d643b20f3f3e0de68975addd59e346d58d2", # 41 branch+pack+stack short 1/2
    "book:path:82e07b845038d9e2c03a74eab9531bfdb2aaa74dd621e9ab21c72eb467b32bd7", # 42 lift+carve short 1/2
    "book:path:716df07ca23e72681a3aca19b6a160a3c867f21315b111d0c6ac21a2700be269", # 43 twist vertical 1/2
    "book:path:7f4ace179d50c15c3a63cd24d5dcb7e3420da79697dcb07afb1a30f73bbed628", # 44 pinch vertical 1/2
    "book:path:aec174c38f9ed86be822dd7813012953b17a2443337cd862c35837a7c34ab023", # 45 branch+branch vertical 1/2
    "book:path:4805f5934fe933b3108aeb3a3aa5a567a1a1bd1debe1a625217a979a35f16c24", # 46 notch+twist vertical 1/2
    "book:path:e688a33bce52391b696ecea5bef1c7926ec4e15d1a02971bebfaf8fcb990c13b", # 47 expand+nest vertical 1/2
    "book:path:9ff66e145418829ccc5e710634ec50389ce05bc62f6496984bde22110528e383", # 48 offset long 1/4
    "book:path:546119cfb82a276ceee53e1eb09d960d054ff4bacd4853bc824ba6ed9ffd8e8f", # 49 compress long 1/4
    "book:path:f1440150bbd785859ef88baca5734f8731b6b029da123797ae55c43541ecb398", # 50 split+split long 1/4
    "book:path:0bac03a066888497ad4cdc5a727e609bdb620a3ef13ef9cc5394a46de7a09449", # 51 taper+bend long 1/4
    "book:path:af83d6add866295511a823d82a17f6d3b2316e11204b251b3c0c6eee90de813f", # 52 pinch+join+array long 1/4
    "book:path:f42375c1818d4ccdef5278032d64aa984e673a76b1e44056b286a08f507288d1", # 53 extrude short 1/4
    "book:path:89a8d2e071e7dc228815ddab41a199bf7379d5742d861095f20ab2de6fd610f5", # 54 lodge short 1/4
    "book:path:bbd403cec5ff6827cf04b266a65afdab72752a8071a42a83017b53f878176551", # 55 extract short 1/4
    "book:path:b1dc18f7817ae62db7951887748c90355ffaa9ee10880a1dfaad396c8a5e54e0", # 56 inscribe+intersect short 1/4
    "book:path:ea3fdbfddf0a32805dc837821770519d713d02a468fa8e914311a1e122289d20", # 57 branch+pack+stack short 1/4
    "book:path:0e3fe6f19fe3fb3b4fdfecd76c496e00141469a5ab4be263385f49ea58ce99b5", # 58 lift+carve short 1/4
    "book:path:b161eb4c3bb6230cd34980d091fc44bf52f7d2648e59f55b39dc46e64225dc46", # 59 twist vertical 1/4
    "book:path:56f69a2038120b9187f1387efee21a6a63cf530d026b6f10dfab37c2db2dc717", # 60 pinch vertical 1/4
    "book:path:dc50b322c264219be6835f6b50fc2a3e5ffba233fd5e5f9fa3813b14d5523193", # 61 branch+branch vertical 1/4
    "book:path:0d5b1e3a233d34e16073c222838ee053eabeb8692327fc62ef668c7b75a716d1", # 62 shift+notch vertical 1/4
    "book:path:bd7cfc87da1811e45875acde3aa82d513fc343204bca6bcd2fb26f3a1d1357e7", # 63 embed+overlap vertical 1/4
    "book:path:c58193dcc81b7f6fb8a25fd8bb18808d47ae79a9765ff716fd84b09d1befc70b", # 64 nest long 1/8
    "book:path:2e91334e6426f5c7ca6a8f4cfce4ca746f1d0f3091273eaf3896fe4900b3f7bd", # 65 carve long 1/8
    "book:path:58d160602ccaafb30f737d33723e43a8ae2841eaac7fda840c8f5d8886775abf", # 66 intersect+intersect long 1/8
    "book:path:150c3892213b9cc014f2985158abc9905f8c9b2cc1c690a1cc7e41068a044a6f", # 67 taper+bend long 1/8
    "book:path:a024d86c2d00b3f85de00140e9b221e1e73de64e83a85c58dc4e52ea478988e0", # 68 pinch+join+array long 1/8
    "book:path:a254a71182ed875bbe8102de50270b1e19538916fe00c1a609ea6c5950fbef0b", # 69 extrude short 1/8
    "book:path:d138480c1ee6ed85eed95f1cfd921852b69d33e8e412f0f28a7c3194117efa38", # 70 lodge short 1/8
    "book:path:42bc62991fbaf0eaa42d48e37ede8e507613abc648a0e32338a19e19862787e2", # 71 extract short 1/8
    "book:path:eee048bfdfa8ab2892e3a8a604bd2a302efd5cb77e995014dc28074c5b3811b4", # 72 inscribe+intersect short 1/8
    "book:path:9e4457e0a1cf8fa849c73e92abc08b15423426f4949b6225cab08c1034e531a5", # 73 inflate+pack short 1/8
    "book:path:71fb46d7af677eb3b5345e94d27f0fa1ef9b257aadc2cd746aec550ba2a0419b", # 74 embed+taper short 1/8
    "book:path:dfbf81995ea510ccee2aa31dffbf03a3dd3dfcb167a0153d116724dbf65599f0", # 75 split vertical 1/8
    "book:path:415615bd85962e057ca3dd17914bf224fa7b6182a09f3f17db371a41b7dcc401", # 76 notch vertical 1/8
    "book:path:a831f22dee8c36e3a70315fa1ff822eff56f7f0deefcfb3032d54fc585e8a128", # 77 bend+bend vertical 1/8
]
# We have 78 unique paths. We'll cycle through them 2x for 120 programs (using slight variants)

def p(i): return paths[i % len(paths)]

# ---- BUILD ALL 120 PROGRAMS ----

# 1-10: Full 1/1 base, diverse operatives
add("bend_bar_01","cube","bar",["bent_bar","arc_plan","east_court"],p(0),
    "Bar bent along long axis creates concave east court naturally.",dim(4,3.5,1100.0),
    [BOX("b0",*BAR),MAT("m0","b0",I()),
     {"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"angle_degrees","value_type":"number","numeric_value":28},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},
     CY("result","bent",0.22,"east")])

add("fracture_slab_02","cube","slab",["fractured_slab","diagonal_fissure","east_notch"],p(1),
    "Slab fractured diagonally; east notch marks civic entry.",dim(5,3.3,1300.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),FRAC("frac","m0","x",0.12,"north",1.0,0.45),NT("result","frac","east",0.22,0.35,0.6)])

add("embed_embed_03","cube","block",["double_embed","nested_voids","east_carve"],p(2),
    "Two concentric embedded voids create layered programme; east carve opens the public court.",dim(4,3.5,1050.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),EMBV("emb1","m0","z",0.6,0.4),EMBV("emb2","emb1","z",0.35,0.6),CV("result","emb2",0.28,"east")])

add("branch_expand_04","cube","block",["branching_arms","expanded_crown","east_lift"],p(3),
    "Block branches then expands outward; east lift opens the ground plane.",dim(4,3.5,1200.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),BR("br","m0",0.55,0.4,60),BEXPPS("exp","br",0.18,"z"),LF("result","exp",0.22,0.18,"east")])

add("carve_offset_05","cube","slab",["poli_carve","north_offset","east_court"],p(4),
    "Slab carved north face; east court provides the public threshold.",dim(5,3.3,1380.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),BCAR("carv","m0","y","north",0.45,0.3,-1.0),CY("result","carv",0.18,"east")])

add("branch_short_06","cube","slab",["wing_pair","three_sided","east_court"],p(5),
    "Slab branches laterally into wings flanking east-facing court.",dim(4,3.5,1150.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),BR("br","m0",0.5,0.45,90),CY("result","br",0.25,"east")])

add("rotate_short_07","cube","bar",["hinged_arm","angled_plan","east_notch"],p(6),
    "Bar arm rotated on short axis produces wedge-shaped east forecourt.",dim(4,3.5,1000.0),
    [BOX("b0",*BAR),MAT("m0","b0",I()),ROT("rot","m0","z",22,0.45),NT("result","rot","east",0.28,0.4,0.55)])

add("inscribe_elliptical_08","elliptical","block",["inscribed_ring","elliptical_shell","east_open"],p(7),
    "Elliptical block inscribed with inner void creates ring shell; east carve marks entry.",dim(4,3.5,950.0),
    [BOX("b0",*BLOCK),ELL("ell","b0",24),MAT("m0","ell",I()),CY("insc","m0",0.3,"closed","program_space"),CV("result","insc",0.2,"east")])

add("intersect_split_09","cube","slab",["cross_bars","split_zones","east_split"],p(8),
    "Two crossing slabs retain intersection; split divides east/west zones sharing crossing hall.",dim(4,3.5,1080.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),ISR("isct","m0","y",30,0.35,0.8),BSPLIT("result","isct","x",0.08,0,1.0,1.0,0.45,1,"east")])

add("bend_stack_10","cube","slab",["bent_stacked","curved_tiers","east_court"],p(9),
    "Slab bent then stacked; shifted curved tiers create spiraling silhouette.",dim(4,3.5,1200.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),BN("bent","m0","y",20),STK("stk","bent",3,[0.05,0.0,0.0]),CY("result","stk",0.2,"east")])

# 11-20
add("lift_extrude_11","cube","slab",["lifted_plate","core_descending","east_through"],p(10),
    "Slab lifted above grade; core descends through clearance zone.",dim(4,3.5,1100.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),LIFT("lft","m0","z",0.25,0.6),LF("result","lft",0.2,0.15,"east")])

add("interlock_vertical_12","cube","block",["L_interlock","figure8_plan","east_notch"],p(11),
    "Two L-volumes engage through shared zone; east notches mark civic entry.",dim(4,3.5,1050.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),ILK("ilk","m0","x",0,0.4,0.3),NT("result","ilk","east",0.25,0.38,0.5)])

add("shear_tower_13","cube","tower",["sheared_tower","oblique_top","east_notch"],p(12),
    "Tower sheared vertically; diagonal top plane contrasts with grounded base.",dim(5,3.3,900.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),SH("sh","m0",0.45,"z","x"),NT("result","sh","east",0.2,0.5,0.4)])

add("expand_expand_14","cube","block",["double_flare","stepped_splay","east_carve"],p(13),
    "Two successive boundary expansions produce double-flared section.",dim(4,3.5,1100.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),BEXP("exp1","m0",0.22,"z",0.5),BEXPPS("exp2","exp1",0.15,"z",0.75),CV("result","exp2",0.22,"east")])

add("expand_reflect_15","cube","block",["reflected_pair","bilateral_form","east_notch"],p(14),
    "Body expanded on one side and reflected; bilateral volumes sharing central spine.",dim(5,3.3,1200.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),BEXP("exp","m0",0.3,"y"),MIRR("mir","exp",[1.0,0.0,0.0],[0.0,0.0,0.0]),NT("result","mir","east",0.3,0.45,0.5)])

add("overlap_expand_16","cube","block",["vertical_overlap","expanded_zone","east_lift"],p(15),
    "Volumes overlap vertically then expand at overlap zone; mid-height public from east.",dim(4,3.5,1100.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),OVR("ovl","m0","x",0.5,0.35,0.3),BEXPPS("exp","ovl",0.18,"z"),LF("result","exp",0.18,0.16,"east")])

add("bend_38_bar_17","cube","bar",["bent_3_8","arc_bar","east_court"],p(16),
    "3/8 bar arc curves convex east face toward road; court within.",dim(3,3.5,900.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.375)),{"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"angle_degrees","value_type":"number","numeric_value":35},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},CY("result","bent",0.24,"east")])

add("fracture_38_18","cube","bar",["fractured_3_8","angular_fissure","east_notch"],p(17),
    "3/8 bar fractured angularly on south face; structural event with east entry.",dim(3,3.5,850.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.375)),FRAC("frac","m0","x",0.1,"south",1.0,0.5),NT("result","frac","east",0.3,0.4,0.6)])

add("split_split_38_19","cube","bar",["double_split_38","z_plan","east_access"],p(18),
    "3/8 bar double-split creates Z-plan articulation.",dim(4,3.5,1000.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.375)),BSPLITD("sp1","m0","x",0.06,20,1.0,1.0,0.4,1),BSPLIT("result","sp1","x",0.06,-20,-1.0,1.0,0.4,2,"east")])

add("bend_branch_38_20","cube","bar",["bent_branched","arc_arm","east_notch"],p(19),
    "3/8 bar bent then branched at apex; arm reaches east to define civic address.",dim(4,3.5,980.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.375)),{"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"angle_degrees","value_type":"number","numeric_value":25},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},BBNR("result","bent",0.6,0.38,70)])

# 21-30
add("split_join_38_21","cube","bar",["split_rejoined","hinged_connector","east_notch"],p(20),
    "3/8 bar split and rejoined via bridge; hinged seam visible in elevation.",dim(4,3.5,1020.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.375)),BSPLITD("sp","m0","x",0.12,30,1.0,1.0,0.45,1),JOIN("result","sp",0.3)])

add("inflate_38_22","elliptical","slab",["inflated_crown","barrel_profile","east_notch"],p(21),
    "3/8 slab inflated at crown; barrel section reads as weighted top over light base.",dim(4,3.5,900.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.375)),IF("inf","m0","z",1.35,1.4),NT("result","inf","east",0.28,0.4,0.55)])

add("overlap_38_23","cube","slab",["slipped_slabs","cascade_overlap","east_court"],p(22),
    "Two 3/8 slabs slipped in plan; cascading overlap visible from all sides.",dim(4,3.5,1050.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.375)),OVR("ovl","m0","x",0.55,0.4,0.35),CY("result","ovl",0.22,"east")])

add("inscribe_38_24","cube","slab",["ring_plan_38","inner_well","east_open"],p(23),
    "3/8 slab inscribed court creates ring plan; deep void visible through east opening.",dim(4,3.5,1000.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.375)),CY("insc","m0",0.28,"closed","program_space"),CV("result","insc",0.18,"east")])

add("intersect_split_38_25","cube","slab",["cross_split_38","crossing_hall","east_access"],p(24),
    "3/8 slab crossed and split; two zones share crossing hall.",dim(4,3.5,980.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.375)),ISR("isct","m0","y",45,0.3,0.75),BSPLIT("result","isct","y",0.08,0,1.0,1.0,0.4,1,"east")])

add("bend_stack_38_26","cube","slab",["bent_stacked_38","arc_tiers","east_court"],p(25),
    "3/8 slab bent and stacked; shifted arc tiers produce spiraling tower.",dim(4,3.5,1050.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.375)),BN("bent","m0","y",22),STK("stk","bent",3,[0.04,0.02,0.0]),CY("result","stk",0.2,"east")])

add("lift_extrude_38_27","cube","slab",["hovering_plate","core_through","east_access"],p(26),
    "3/8 slab lifted; hovering plate on expressed supports with east access.",dim(3,3.5,800.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.375)),LIFT("lft","m0","z",0.28,0.55),LF("result","lft",0.22,0.15,"east")])

add("interlock_38_28","cube","block",["interlock_38","double_L","east_notch"],p(27),
    "3/8 base: two L-volumes interlock; double-notch east face reads as civic engagement.",dim(4,3.5,950.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.375)),ILK("ilk","m0","y",0,0.38,0.32),NT("result","ilk","east",0.22,0.35,0.5)])

add("shear_38_29","cube","tower",["shear_3_8","diagonal_silhouette","east_notch"],p(28),
    "3/8 tower sheared vertically; oblique top plane contrasts with grounded base.",dim(5,3.3,850.0),
    [BOX("b0",*TOWER),MAT("m0","b0",S(0.375)),SH("sh","m0",0.5,"z","y"),NT("result","sh","east",0.22,0.45,0.4)])

add("branch_branch_38_30","cube","bar",["double_branch_38","forked_plan","east_court"],p(29),
    "3/8 bar double-branched; forked plan presents faces to all cardinal directions.",dim(4,3.5,1050.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.375)),BR("br1","m0",0.55,0.42,70),BBNR("result","br1",0.5,0.38,-60)])

# 31-40
add("notch_twist_38_31","cube","tower",["notched_twisted","torsion_above_entry","east_notch"],p(30),
    "3/8 tower notched at corner then twisted; torsion rises above the notched entry zone.",dim(5,3.3,900.0),
    [BOX("b0",*TOWER),MAT("m0","b0",S(0.375)),BBNOT("ntch","m0","z","ne",0.28),TW("result","ntch","z",35)])

add("expand_nest_38_32","cube","block",["expand_nest_38","double_shell","east_threshold"],p(31),
    "3/8 block expanded then nested concentrically; layered public/private shells.",dim(4,3.5,980.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.375)),BEXP("exp","m0",0.32,"z"),NEST("nst","exp","x",0.25,0.55),CV("result","nst",0.2,"east")])

add("offset_12_33","cube","bar",["offset_pair_12","parallel_bars","east_court"],p(32),
    "1/2 bar offset creates parallel bar pair; east court links them.",dim(4,3.5,1100.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.5)),OFFRR("off","m0","y",0.4,0.85),CY("result","off",0.2,"east")])

add("clip_12_34","cube","slab",["clipped_slab_12","thin_bar_profile","east_notch"],p(33),
    "1/2 slab clipped along long axis creates a thinner bar reading tall against east road.",dim(5,3.3,1050.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.5)),CLIP("clip","m0","y",0.7,"low"),NT("result","clip","east",0.25,0.4,0.55)])

add("split_split_12_35","cube","bar",["z_plan_12","double_split_half","east_access"],p(34),
    "1/2 bar double-split at alternating angles creates Z-plan at half scale.",dim(4,3.5,980.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.5)),BSPLITD("sp1","m0","x",0.07,25,1.0,1.0,0.42,1),BSPLIT("result","sp1","x",0.07,-25,-1.0,1.0,0.42,2,"east")])

add("bend_branch_12_36","cube","bar",["bent_branched_12","arc_arm_12","east_notch"],p(35),
    "1/2 bar bent then branched; arm at mid-arc reaches east to define civic address.",dim(4,3.5,1000.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.5)),{"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"angle_degrees","value_type":"number","numeric_value":30},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},BBNR("result","bent",0.58,0.36,65)])

add("split_join_12_37","cube","bar",["split_joined_12","hinge_seam","east_notch"],p(36),
    "1/2 bar split and rejoined; seam reads as structural threshold visible from east.",dim(4,3.5,980.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.5)),BSPLITD("sp","m0","x",0.1,28,1.0,1.0,0.44,1),JOIN("result","sp",0.28)])

add("inflate_12_38","elliptical","slab",["inflated_12","swollen_ellipse","east_notch"],p(37),
    "1/2 elliptical slab inflated; swollen body with convex east face addressing the road.",dim(4,3.5,1000.0),
    [BOX("b0",*SLAB),ELL("ell","b0",20),MAT("m0","ell",S(0.5)),IF("inf","m0","y",1.4,1.35),NT("result","inf","east",0.26,0.42,0.55)])

add("overlap_12_39","cube","slab",["slipped_12","cascade_slip","east_court"],p(38),
    "Two 1/2 slabs slipped in plan; cascading terrace visible from east road.",dim(4,3.5,1000.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.5)),OVR("ovl","m0","x",0.52,0.38,0.32),CY("result","ovl",0.2,"east")])

add("inscribe_12_40","cube","slab",["ring_12","inner_court_half","east_carve"],p(39),
    "1/2 slab inscribed court creates ring plan; east carve reveals inner light well.",dim(4,3.5,950.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.5)),CY("insc","m0",0.3,"closed","program_space"),CV("result","insc",0.18,"east")])

# 41-50
add("inscribe_intersect_12_41","cube","slab",["ring_cross_12","activated_ring","east_notch"],p(40),
    "1/2 slab ring inscribed then crossed by bar; crossing activates the ring from east.",dim(4,3.5,960.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.5)),CY("insc","m0",0.28,"closed","dominant_mass"),ISR("isct","insc","x",0,0.25,0.6),NT("result","isct","east",0.25,0.38,0.5)])

add("branch_pack_12_42","cube","block",["packed_branch_12","clustered_civic","east_court"],p(41),
    "1/2 block branched and packed; a dense civic cluster with east court as public space.",dim(4,3.5,1100.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.5)),BR("br","m0",0.52,0.42,80),RELARRAY("arr","br","x",2,"pack",1.1),CY("result","arr",0.2,"east")])

add("lift_carve_12_43","cube","slab",["lifted_carved_12","law_courts","east_lift"],p(42),
    "1/2 slab lifted and carved below; public ground freed while programme floats above.",dim(4,3.5,1050.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.5)),LIFT("lft","m0","z",0.22,0.58),BCAR("carv","lft","y","east",0.4,0.3,1.0),LF("result","carv",0.2,0.16,"east")])

add("twist_12_44","cube","block",["twisted_12","vertical_torsion","east_notch"],p(43),
    "1/2 block twisted on vertical axis; diagonal corner addresses east road.",dim(4,3.5,1000.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.5)),TW("tw","m0","z",40,5),NT("result","tw","east",0.22,0.4,0.48)])

add("pinch_12_45","cube","block",["waisted_12","hourglass_body","east_carve"],p(44),
    "1/2 block pinched at mid-height; hourglass section with east carve at the waist.",dim(4,3.5,900.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.5)),PN("pnch","m0","z",0.5,0.65),CV("result","pnch",0.22,"east")])

add("branch_branch_12_46","cube","block",["double_branch_12","forked_vertical","east_court"],p(45),
    "1/2 block double-branched vertically; forked plan with east-facing primary arm.",dim(4,3.5,1050.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.5)),BR("br1","m0",0.55,0.42,75),BBNR("result","br1",0.48,0.38,-65)])

add("notch_twist_12_47","cube","tower",["notch_twist_12","corner_torsion","east_notch"],p(46),
    "1/2 tower notched then twisted; sculptural torsion above corner notch entry.",dim(5,3.3,920.0),
    [BOX("b0",*TOWER),MAT("m0","b0",S(0.5)),BBNOT("ntch","m0","z","ne",0.3),TW("result","ntch","z",38)])

add("expand_nest_12_48","cube","block",["house_n_12","concentric_shells","east_threshold"],p(47),
    "1/2 block expanded then nested; concentric layers with layered public/private zones.",dim(4,3.5,950.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.5)),BEXP("exp","m0",0.28,"z"),NEST("nst","exp","y",0.22,0.52),CV("result","nst",0.2,"east")])

add("offset_14_49","cube","bar",["offset_pair_14","intimate_gap","east_court"],p(48),
    "1/4 bar offset creates intimate parallel pair; east court as organizing space between.",dim(4,3.5,900.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.25)),OFFRR("off","m0","y",0.42,0.88),CY("result","off",0.22,"east")])

add("clip_14_50","cube","slab",["clipped_14","thin_profile","east_notch"],p(49),
    "1/4 slab clipped creates tall thin bar against east road; notch marks entry.",dim(5,3.3,850.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.25)),CLIP("clip","m0","y",0.65,"low"),NT("result","clip","east",0.28,0.42,0.55)])

# 51-60
add("split_split_14_51","cube","bar",["z_plan_14","double_split_quarter","east_access"],p(50),
    "1/4 bar double-split; compact Z-plan with three legible programme zones.",dim(4,3.5,880.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.25)),BSPLITD("sp1","m0","x",0.07,22,1.0,1.0,0.42,1),BSPLIT("result","sp1","x",0.07,-22,-1.0,1.0,0.42,2,"east")])

add("taper_bend_14_52","cube","bar",["tapered_wedge","arc_wedge","east_notch"],p(51),
    "1/4 bar tapered to wedge then bent; asymmetric arc opens toward east.",dim(4,3.5,880.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.25)),TP("tap","m0","z",[0.7,0.55]),{"id":"result","kind":"modifier","operator":"bent_bar","inputs":["tap"],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"angle_degrees","value_type":"number","numeric_value":25},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"public_threshold"}])

add("pinch_array_14_53","cube","bar",["pinched_arrayed","waisted_linear","east_notch"],p(52),
    "1/4 bar pinched then arrayed linearly; alternating narrow/wide sections.",dim(4,3.5,950.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.25)),PN("pnch","m0","z",0.5,0.7),LINARRAY("arr","pnch",2,[0.35,0.0,0.0]),NT("result","arr","east",0.25,0.4,0.5)])

add("extrude_tet_14_54","tetrahedral","block",["tetrahedral_body","faceted_prism","east_notch"],p(53),
    "1/4 tetrahedral base body expanded vertically; faceted prism addresses east road.",dim(4,3.5,900.0),
    [BOX("b0",*BLOCK),TET("tet","b0"),MAT("m0","tet",S(0.25)),BEXP("ext","m0",0.35,"z"),NT("result","ext","east",0.28,0.42,0.5)])

add("lodge_14_55","cube","block",["lodged_bridge","bar_over_gap","east_court"],p(54),
    "Bar lodged between two 1/4 host volumes; bridging bar creates public gateway from east.",dim(4,3.5,930.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.25)),LODGE("ldg","m0","x",0.38,0.55),CY("result","ldg",0.2,"east")])

add("extract_14_56","cube","block",["extracted_socket","socket_pair","east_notch"],p(55),
    "1/4 block: volume extracted leaves socket; extracted piece stands alongside creating duality.",dim(4,3.5,880.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.25)),EXTR("ext","m0","x","east",0.32,0.48),NT("result","ext","east",0.22,0.38,0.5)])

add("inscribe_intersect_14_57","cube","slab",["ring_cross_14","activated_14","east_notch"],p(56),
    "1/4 slab ring inscribed then intersected; bar crossing activates ring revealing depth.",dim(4,3.5,870.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.25)),CY("insc","m0",0.3,"closed","dominant_mass"),ISR("isct","insc","x",0,0.22,0.55),NT("result","isct","east",0.25,0.4,0.5)])

add("branch_pack_14_58","cube","block",["packed_branch_14","dense_cluster","east_court"],p(57),
    "1/4 block branched and packed; dense cluster with east court as public space.",dim(4,3.5,950.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.25)),BR("br","m0",0.52,0.4,80),RELARRAY("arr","br","y",2,"pack",1.15),CY("result","arr",0.2,"east")])

add("lift_carve_14_59","cube","slab",["lifted_14","courts_floating","east_lift"],p(58),
    "1/4 slab lifted then access-lifted; floating programme over freed public ground.",dim(4,3.5,870.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.25)),LIFT("lft","m0","z",0.25,0.55),LF("result","lft",0.2,0.15,"east")])

add("twist_14_60","cube","block",["twisted_14","corner_diagonal","east_notch"],p(59),
    "1/4 block twisted on vertical axis; diagonal east corner reads against road.",dim(4,3.5,880.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.25)),TW("tw","m0","z",45,5),NT("result","tw","east",0.24,0.4,0.5)])

# 61-70
add("pinch_14_61","cube","block",["waisted_14","hourglass_14","east_carve"],p(60),
    "1/4 block pinched at mid-height; waisted tower with east carve at waist.",dim(4,3.5,860.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.25)),PN("pnch","m0","z",0.5,0.62),CV("result","pnch",0.2,"east")])

add("branch_branch_14_62","cube","block",["pinwheel_14","four_arm","east_court"],p(61),
    "1/4 block double-branched; pinwheel plan readable from all four sides.",dim(4,3.5,900.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.25)),BR("br1","m0",0.55,0.4,80),BBNR("result","br1",0.5,0.36,-70)])

add("shift_notch_14_63","cube","block",["shifted_notched","displaced_corner","east_notch"],p(62),
    "1/4 block: half shifted then notched at resulting offset corner; relief face exposed.",dim(4,3.5,870.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.25)),SHREL("sh","m0","x",0.3,0.5),BBNOT("ntch","sh","z","ne",0.25),NT("result","ntch","east",0.22,0.4,0.5)])

add("embed_overlap_14_64","cube","block",["embedded_overlap","canopy_void","east_notch"],p(63),
    "1/4 block: void embedded then overlapped; overlap zone reads as public canopy.",dim(4,3.5,860.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.25)),EMBV("emb","m0","z",0.5,0.3),OVR("ovl","emb","x",0.45,0.3,0.25),NT("result","ovl","east",0.22,0.38,0.5)])

add("nest_18_65","cube","bar",["nested_bar","concentric_linear","east_court"],p(64),
    "1/8 bar with nested inner volume; linear nesting creates double-walled bar section.",dim(4,3.5,900.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.125)),NEST("nst","m0","x",0.2,0.6),CY("result","nst",0.22,"east")])

add("carve_18_66","cube","bar",["carved_bar_18","recessed_face","east_notch"],p(65),
    "1/8 bar carved on its long face; recess creates depth and shadow from east road.",dim(4,3.5,850.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.125)),BCAR("carv","m0","y","north",0.5,0.35),NT("result","carv","east",0.25,0.4,0.55)])

add("intersect_intersect_18_67","cube","bar",["double_cross","crossed_bars_18","east_notch"],p(66),
    "1/8 bar doubly intersected by bars at different angles; layered crossing hall.",dim(4,3.5,880.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.125)),ISR("isct1","m0","y",30,0.3,0.8),ISR("isct2","isct1","x",0,0.25,0.7),NT("result","isct2","east",0.22,0.38,0.5)])

add("taper_bend_18_68","cube","bar",["tapered_bent_18","wedge_arc_18","east_notch"],p(67),
    "1/8 bar tapered then bent; combination creates asymmetric arc section.",dim(4,3.5,870.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.125)),TP("tap","m0","z",[0.65,0.5]),{"id":"result","kind":"modifier","operator":"bent_bar","inputs":["tap"],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"angle_degrees","value_type":"number","numeric_value":22},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"public_threshold"}])

add("pinch_array_18_69","cube","bar",["pinched_linear_18","waisted_array","east_notch"],p(68),
    "1/8 bar pinched then arrayed; alternating pinch creates undulating linear section.",dim(4,3.5,920.0),
    [BOX("b0",*BAR),MAT("m0","b0",S(0.125)),PN("pnch","m0","z",0.5,0.68),LINARRAY("arr","pnch",3,[0.28,0.0,0.0]),NT("result","arr","east",0.22,0.38,0.5)])

add("extrude_18_70","cube","slab",["extruded_18","simple_extrude","east_notch"],p(69),
    "1/8 slab boundary expanded vertically; compact extruded volume occupies quarter parcel.",dim(4,3.5,880.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.125)),BEXP("ext","m0",0.4,"z"),NT("result","ext","east",0.25,0.4,0.5)])

# 71-80
add("lodge_18_71","cube","block",["lodged_18","bridging_guest","east_court"],p(70),
    "1/8 block with lodged guest bar; bridging element connects host sections from east.",dim(4,3.5,860.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.125)),LODGE("ldg","m0","x",0.35,0.55),CY("result","ldg",0.2,"east")])

add("extract_18_72","cube","block",["extracted_18","socket_channel","east_notch"],p(71),
    "1/8 block: extraction creates channel; extracted piece reads as separate public element.",dim(4,3.5,840.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.125)),EXTR("ext","m0","x","east",0.3,0.5),NT("result","ext","east",0.22,0.38,0.5)])

add("inscribe_intersect_18_73","cube","slab",["ring_cross_18","ring_bar_cross","east_notch"],p(72),
    "1/8 slab ring inscribed then intersected; bar crossing activates the ring from east.",dim(4,3.5,850.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.125)),CY("insc","m0",0.28,"closed","dominant_mass"),ISR("isct","insc","x",0,0.2,0.55),NT("result","isct","east",0.22,0.38,0.5)])

add("inflate_pack_18_74","elliptical","slab",["inflated_pack","swollen_array","east_court"],p(73),
    "1/8 elliptical slab inflated then packed; swollen array creates dense civic cluster.",dim(4,3.5,900.0),
    [BOX("b0",*SLAB),ELL("ell","b0",16),MAT("m0","ell",S(0.125)),IF("inf","m0","z",1.3,1.35),RELARRAY("arr","inf","x",2,"pack",1.2),CY("result","arr",0.2,"east")])

add("embed_taper_18_75","cube","slab",["embedded_taper","nursery_type","east_notch"],p(74),
    "1/8 slab embedded then tapered; nested taper creates inclined section above embedded programme.",dim(4,3.5,840.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.125)),EMBV("emb","m0","z",0.5,0.35),TP("tap","emb","z",[0.75,0.7]),NT("result","tap","east",0.22,0.4,0.5)])

add("split_18_76","cube","block",["split_vertical_18","hinged_pair","east_access"],p(75),
    "1/8 block split vertically; hinged pair flanks the east access.",dim(4,3.5,860.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.125)),BSPLIT("result","m0","x",0.08,15,1.0,1.0,0.45,1,"east")])

add("notch_18_77","cube","block",["notched_18","corner_cut","east_notch"],p(76),
    "1/8 block notched at east-facing corner; corner notch reads as an activated civic entry.",dim(4,3.5,840.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.125)),BBNOT("ntch","m0","z","ne",0.3),NT("result","ntch","east",0.25,0.4,0.5)])

add("bend_bend_18_78","cube","block",["double_bend","S_curve","east_court"],p(77),
    "1/8 block bent twice in opposing directions; S-curve plan with east-facing public face.",dim(4,3.5,870.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",S(0.125)),BN("b1","m0","x",25),BN("b2","b1","y",-22),CY("result","b2",0.22,"east")])

# Next 42 programs (79-120) using path cycling and parameter variety
add("taper_tower_79","cube","tower",["tapered_tower_v1","narrowing_top","east_notch"],p(0),
    "Tower tapered to narrow top; civic tower with clearly diminishing section.",dim(5,3.3,950.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),TP("tap","m0","z",[0.6,0.6]),NT("result","tap","east",0.22,0.45,0.45)])

add("grade_slab_80","cube","slab",["graded_face","terraced_east","east_court"],p(1),
    "Slab graded on its east face producing stepped public terraces descending to road.",dim(4,3.5,1150.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),BGRADE("grad","m0","x","east",0.55,0.4,3,1.0),CY("result","grad",0.18,"east")])

add("puncture_slab_81","cube","slab",["punctured_slab","perforated_facade","east_notch"],p(2),
    "Slab punctured by three vertical openings; perforated east facade reads as civic screen.",dim(5,3.3,1250.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),PUNC("punc","m0","z",3,0.15,0.3),NT("result","punc","east",0.22,0.38,0.55)])

add("shear_slab_82","cube","slab",["sheared_slab","parallelogram","east_notch"],p(3),
    "Slab sheared along its long axis creating a parallelogram plan that leans toward east.",dim(5,3.3,1300.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),SH("sh","m0",0.35,"z","x"),NT("result","sh","east",0.25,0.4,0.5)])

add("taper_block_83","cube","block",["tapered_block","pyramidal_base","east_carve"],p(4),
    "Block tapered from wide base to narrow top; pyramidal massing with east carve entry.",dim(4,3.5,1000.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),TP("tap","m0","z",[0.5,0.5]),CV("result","tap",0.2,"east")])

add("twist_slab_84","cube","slab",["twisted_slab","torsional_plate","east_notch"],p(5),
    "Slab twisted along its long axis; torsional plate creates dynamic silhouette from road.",dim(5,3.3,1200.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),TW("tw","m0","x",25,5),NT("result","tw","east",0.25,0.4,0.5)])

add("carve_tower_85","cube","tower",["carved_tower","civic_void","east_carve"],p(6),
    "Tower carved on its east face; public recess reveals inner programme zone.",dim(5,3.3,880.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),BCAR("carv","m0","x","east",0.5,0.35,1.0),CV("result","carv",0.2,"east")])

add("merge_slab_86","cube","slab",["merged_slabs","fused_pair","east_court"],p(7),
    "Two slab volumes merged at their shared face; fused mass with joint visible from east.",dim(4,3.5,1150.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),{"id":"mrg","kind":"modifier","operator":"merge_related","inputs":["m0"],"parameters":[{"name":"axis","value_type":"string","string_value":"y"},{"name":"gap_ratio","value_type":"number","numeric_value":0.1},{"name":"unit_scale","value_type":"number","numeric_value":0.9}],"semantic_role":"dominant_mass"},CY("result","mrg",0.2,"east")])

add("leaning_tower_87","cube","tower",["leaning_form","tilted_tower","east_notch"],p(8),
    "Tower leaning in x-direction; inclined body reads against vertical neighbours.",dim(5,3.3,870.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),{"id":"lean","kind":"modifier","operator":"leaning_tower","inputs":["m0"],"parameters":[{"name":"amount","value_type":"number","numeric_value":0.4},{"name":"direction","value_type":"string","string_value":"x"}],"semantic_role":"dominant_mass"},NT("result","lean","east",0.22,0.42,0.45)])

add("shift_bar_88","cube","bar",["shifted_bar","displaced_wing","east_court"],p(9),
    "Bar shifted transversely creating an offset pair with a shared gap; east court links them.",dim(4,3.5,1050.0),
    [BOX("b0",*BAR),MAT("m0","b0",I()),SHREL("sh","m0","y",0.35,0.5),CY("result","sh",0.2,"east")])

# 89-98
add("taper_slab_89","cube","slab",["tapered_slab","wedge_section","east_notch"],p(10),
    "Slab tapered asymmetrically creating a wedge plan; east face tapers toward road entry.",dim(5,3.3,1150.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),TP("tap","m0","z",[0.7,0.4]),NT("result","tap","east",0.25,0.4,0.55)])

add("inflate_tower_90","cube","tower",["inflated_tower","swollen_shaft","east_notch"],p(11),
    "Tower inflated at crown creates swollen top mass; east notch at base marks civic entry.",dim(5,3.3,920.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),IF("inf","m0","z",1.3,1.4),NT("result","inf","east",0.22,0.4,0.45)])

add("split_wing_bar_91","cube","bar",["split_wing_pair","bridged_wings","east_access"],p(12),
    "Bar split into wing pair bridged at mid-height; east-facing access between wings.",dim(4,3.5,1100.0),
    [BOX("b0",*BAR),MAT("m0","b0",I()),SPLITWING("result","m0","x","split",0.9,0.18,True,"east")])

add("carve_stack_92","cube","slab",["carved_stacked","graded_section","east_court"],p(13),
    "Slab carved on north face then stacked; carved tiers create terraced north profile.",dim(4,3.5,1200.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),BCAR("carv","m0","y","north",0.4,0.3),STK("stk","carv",3,[0.06,0.0,0.0]),CY("result","stk",0.2,"east")])

add("overlap_tower_93","cube","tower",["overlapped_towers","staggered_pair","east_lift"],p(14),
    "Two towers overlapped and staggered creating shared zone at mid-height; east lift.",dim(5,3.3,1000.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),OVR("ovl","m0","x",0.55,0.38,0.35),LF("result","ovl",0.18,0.15,"east")])

add("notch_notch_94","cube","slab",["double_notch","corner_reliefs","east_notch"],p(15),
    "Slab with two corner notches at opposite ends creating asymmetric plan reliefs.",dim(5,3.3,1250.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),BBNOT("nt1","m0","z","ne",0.25),BBNOT("nt2","nt1","z","sw",0.2),NT("result","nt2","east",0.22,0.4,0.5)])

add("fracture_twist_95","cube","tower",["fractured_twisted","cracked_torsion","east_notch"],p(16),
    "Tower fractured at base then twisted; cracked body reveals torsion above the fracture.",dim(5,3.3,900.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),FRAC("frac","m0","z",0.1,"east",1.0,0.4),TW("result","frac","z",30)])

add("embed_taper_96","cube","block",["embed_then_taper","nested_incline","east_notch"],p(17),
    "Block embedded with a guest then tapered; tapering incline above the embedded void.",dim(4,3.5,950.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),EMBV("emb","m0","y",0.45,0.4,"north"),TP("tap","emb","z",[0.72,0.65]),NT("result","tap","east",0.22,0.4,0.5)])

add("grade_tower_97","cube","tower",["graded_tower","cascading_faces","east_notch"],p(18),
    "Tower graded on its east face; cascading face bands create civic rhythm at street.",dim(5,3.3,900.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),BGRADE("grad","m0","x","east",0.6,0.35,3,1.0),NT("result","grad","east",0.22,0.42,0.45)])

add("inflate_stack_98","elliptical","slab",["inflated_stacked","swollen_tiers","east_court"],p(19),
    "Elliptical slab inflated then stacked; swollen tiers create biomorphic civic tower.",dim(4,3.5,1100.0),
    [BOX("b0",*SLAB),ELL("ell","b0",20),MAT("m0","ell",I()),IF("inf","m0","z",1.3,1.35),STK("stk","inf",3,[0.03,0.03,0.0]),CY("result","stk",0.2,"east")])

# 99-108
add("leaning_bar_99","cube","bar",["leaning_bar","inclined_arm","east_notch"],p(20),
    "Bar leaning in y-direction; inclined arm creates oblique plane against east road.",dim(4,3.5,1000.0),
    [BOX("b0",*BAR),MAT("m0","b0",I()),{"id":"lean","kind":"modifier","operator":"leaning_tower","inputs":["m0"],"parameters":[{"name":"amount","value_type":"number","numeric_value":0.35},{"name":"direction","value_type":"string","string_value":"y"}],"semantic_role":"dominant_mass"},NT("result","lean","east",0.22,0.42,0.48)])

add("bend_carve_100","cube","bar",["bent_carved","arc_with_recess","east_court"],p(21),
    "Bar bent into arc then carved on north; arc holds court, north carve reveals section.",dim(4,3.5,1050.0),
    [BOX("b0",*BAR),MAT("m0","b0",I()),{"id":"bent","kind":"modifier","operator":"bent_bar","inputs":["m0"],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"angle_degrees","value_type":"number","numeric_value":22},{"name":"subdivisions","value_type":"number","numeric_value":4}],"semantic_role":"dominant_mass"},BCAR("carv","bent","y","north",0.42,0.28),CY("result","carv",0.2,"east")])

add("twist_carve_101","cube","block",["twisted_carved","torsion_void","east_court"],p(22),
    "Block twisted then carved; torsional body with carved void creating public recess.",dim(4,3.5,980.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),TW("tw","m0","z",35,5),BCAR("carv","tw","y","east",0.45,0.32,1.0),CY("result","carv",0.2,"east")])

add("pinch_split_102","cube","slab",["pinched_split","waist_then_open","east_access"],p(23),
    "Slab pinched at waist then split there; pinch creates the split zone for an opening.",dim(4,3.5,1050.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),PN("pnch","m0","z",0.5,0.7),BSPLIT("result","pnch","x",0.09,0,1.0,1.0,0.45,1,"east")])

add("merge_tower_103","cube","tower",["merged_towers","fused_twin","east_notch"],p(24),
    "Two towers merged creating a fused twin reading as one compound mass from east.",dim(5,3.3,980.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),{"id":"mrg","kind":"modifier","operator":"merge_related","inputs":["m0"],"parameters":[{"name":"axis","value_type":"string","string_value":"x"},{"name":"gap_ratio","value_type":"number","numeric_value":0.12},{"name":"unit_scale","value_type":"number","numeric_value":0.85}],"semantic_role":"dominant_mass"},NT("result","mrg","east",0.22,0.4,0.5)])

add("fracture_stack_104","cube","slab",["fractured_stacked","fissured_tiers","east_court"],p(25),
    "Slab fractured diagonally then stacked; fissured tiers create layered civic reading.",dim(4,3.5,1100.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),FRAC("frac","m0","x",0.1,"north",1.0,0.45),STK("stk","frac",3,[0.04,0.0,0.0]),CY("result","stk",0.2,"east")])

add("embed_split_105","cube","block",["embedded_split","void_then_open","east_access"],p(26),
    "Block with embedded void then split; void is revealed by the split to form public hall.",dim(4,3.5,950.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),EMBV("emb","m0","z",0.5,0.35),BSPLIT("result","emb","x",0.08,0,1.0,1.0,0.44,1,"east")])

add("shear_stack_106","cube","slab",["sheared_stacked","oblique_tiers","east_court"],p(27),
    "Slab sheared then stacked; oblique tiers create diagonal silhouette from road.",dim(4,3.5,1150.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),SH("sh","m0",0.3,"z","x"),STK("stk","sh",3,[0.04,0.02,0.0]),CY("result","stk",0.2,"east")])

add("taper_stack_107","cube","tower",["tapered_stacked","tapering_tiers","east_notch"],p(28),
    "Tower tapered then stacked; tapering tiers create diminishing crown tower.",dim(5,3.3,950.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),TP("tap","m0","z",[0.75,0.75]),STK("stk","tap",2,[0.0,0.0,0.0]),NT("result","stk","east",0.22,0.42,0.45)])

add("carve_twist_108","cube","block",["carved_twisted","void_torsion","east_court"],p(29),
    "Block carved then twisted; torsion carries the carved void through the body.",dim(4,3.5,980.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),BCAR("carv","m0","y","north",0.42,0.28),TW("tw","carv","z",30,4),CY("result","tw",0.2,"east")])

# 109-120
add("offset_tower_109","cube","tower",["offset_twin_towers","shifted_pair","east_notch"],p(30),
    "Tower offset creating a shifted twin pair with shared vertical face from east.",dim(5,3.3,950.0),
    [BOX("b0",*TOWER),MAT("m0","b0",I()),OFFRR("off","m0","x",0.35,0.85),NT("result","off","east",0.22,0.4,0.45)])

add("bend_overlap_110","cube","slab",["bent_overlap","arc_over_plane","east_lift"],p(31),
    "Slab bent then overlapped creating an arc that cantilevers over the base level.",dim(4,3.5,1100.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),BN("bent","m0","y",18),OVR("ovl","bent","x",0.5,0.32,0.28),LF("result","ovl",0.18,0.15,"east")])

add("inscribe_fracture_111","cube","block",["inscribed_fractured","ring_crack","east_carve"],p(32),
    "Block inscribed with inner court then fractured; crack opens the ring to the road.",dim(4,3.5,1000.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),CY("insc","m0",0.28,"closed","dominant_mass"),FRAC("frac","insc","x",0.1,"east",1.0,0.45),CV("result","frac",0.2,"east")])

add("grade_slab_38_112","cube","slab",["graded_38","stepped_east_face","east_court"],p(33),
    "3/8 slab graded on east face; stepped public terraces approach the road.",dim(4,3.5,950.0),
    [BOX("b0",*SLAB),MAT("m0","b0",S(0.375)),BGRADE("grad","m0","x","east",0.55,0.38,3,1.0),CY("result","grad",0.18,"east")])

add("punc_bar_113","cube","bar",["punctured_bar","screened_facade","east_notch"],p(34),
    "Full bar punctured by two vertical openings; perforated screen toward east road.",dim(5,3.3,1200.0),
    [BOX("b0",*BAR),MAT("m0","b0",I()),PUNC("punc","m0","z",2,0.18,0.35),NT("result","punc","east",0.22,0.4,0.55)])

add("nest_block_114","cube","block",["nested_block","concentric_pair","east_notch"],p(35),
    "Block with nested inner volume; concentric pair creates public inner ring.",dim(4,3.5,980.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),NEST("nst","m0","x",0.25,0.6),NT("result","nst","east",0.25,0.4,0.5)])

add("rotate_stack_115","cube","bar",["rotated_stacked","rotating_tiers","east_court"],p(36),
    "Bar rotated at top then stacked; rotating tiers create dynamic stepped silhouette.",dim(4,3.5,1050.0),
    [BOX("b0",*BAR),MAT("m0","b0",I()),ROT("rot","m0","z",20,0.4),STK("stk","rot",3,[0.03,0.03,0.0]),CY("result","stk",0.2,"east")])

add("carve_inflate_116","elliptical","block",["carved_inflated","void_swell","east_court"],p(37),
    "Block carved then inflated; swollen body above carved public void at street.",dim(4,3.5,1000.0),
    [BOX("b0",*BLOCK),ELL("ell","b0",20),MAT("m0","ell",I()),BCAR("carv","m0","y","north",0.4,0.28),IF("inf","carv","z",1.3,1.35),CY("result","inf",0.2,"east")])

add("leaning_slab_117","cube","slab",["leaning_plate","inclined_plate","east_notch"],p(38),
    "Slab leaning in y-direction; inclined plate mass creates dynamic oblique reading.",dim(5,3.3,1150.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),{"id":"lean","kind":"modifier","operator":"leaning_tower","inputs":["m0"],"parameters":[{"name":"amount","value_type":"number","numeric_value":0.38},{"name":"direction","value_type":"string","string_value":"y"}],"semantic_role":"dominant_mass"},NT("result","lean","east",0.25,0.4,0.5)])

add("intersect_stack_118","cube","slab",["crossed_stacked","cross_tiers","east_court"],p(39),
    "Slab intersected then stacked; each tier retains the cross plan creating a layered civic mass.",dim(4,3.5,1100.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),ISR("isct","m0","y",35,0.32,0.78),STK("stk","isct",3,[0.03,0.0,0.0]),CY("result","stk",0.2,"east")])

add("shear_carve_119","cube","slab",["sheared_carved","oblique_void","east_court"],p(40),
    "Slab sheared then carved on north face; oblique body with carved north public zone.",dim(5,3.3,1200.0),
    [BOX("b0",*SLAB),MAT("m0","b0",I()),SH("sh","m0",0.3,"z","x"),BCAR("carv","sh","y","north",0.4,0.3),CY("result","carv",0.2,"east")])

add("overlap_twist_120","cube","block",["overlapped_twisted","slipped_torsion","east_notch"],p(41),
    "Block overlapped with a slip then twisted; torsion animates the slipped plan from east.",dim(4,3.5,1000.0),
    [BOX("b0",*BLOCK),MAT("m0","b0",I()),OVR("ovl","m0","x",0.5,0.35,0.3),TW("tw","ovl","z",28,4),NT("result","tw","east",0.22,0.4,0.5)])

assert len(programs) == 120, f"Got {len(programs)} programs"

PRINCIPLE_IDS = [
    "book:operative:bend","book:operative:fracture","book:combination:04:embed+embed",
    "book:combination:17:branch+expand","book:case:60:carve+offset","book:operative:branch",
    "book:operative:rotate","book:operative:inscribe","book:combination:12:intersect+split",
    "book:aggregation:stack:bend","book:case:68:lift+extrude","book:operative:interlock",
    "book:operative:shear","book:combination:08:expand+expand","book:aggregation:reflect:expand",
    "book:case:64:overlap+expand","book:combination:16:bend+branch","book:aggregation:join:split",
    "book:combination:03:split+split","book:operative:inflate","book:operative:overlap",
    "book:combination:11:inscribe+intersect","book:aggregation:pack+stack:branch",
    "book:case:67:lift+carve","book:operative:twist","book:operative:pinch",
    "book:combination:07:branch+branch","book:combination:20:notch+twist",
    "book:case:63:expand+nest","book:operative:offset","book:operative:compress",
    "book:combination:15:taper+bend","book:aggregation:join+array:pinch",
    "book:operative:extrude","book:operative:lodge","book:operative:extract",
    "book:combination:02:intersect+intersect","book:aggregation:pack:inflate",
    "book:case:66:embed+taper","book:operative:split","book:operative:notch",
    "book:combination:06:bend+bend","book:combination:19:shift+notch",
    "book:case:62:embed+overlap","book:combination:13:split+embed",
    "book:combination:14:embed+taper","book:aggregation:array:taper",
    "book:aggregation:array+stack:rotate","book:case:65:bend+shift",
    "book:combination:09:shift+shift","book:combination:18:expand+shift",
    "book:combination:10:notch+notch","book:combination:01:inscribe+inscribe",
    "book:case:69:overlap+rotate","book:aggregation:reflect+pack:skew",
    "book:combination:05:taper+taper","book:case:61:embed+branch"
]

out = {"book_principle_ids": PRINCIPLE_IDS, "programs": programs}
with open(r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json","w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)
print(f"Written {len(programs)} programs to book-comp18.json")
