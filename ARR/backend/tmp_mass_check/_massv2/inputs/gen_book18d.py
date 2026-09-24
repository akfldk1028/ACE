# -*- coding: utf-8 -*-
"""
Generator for book-comp18.json - 120 BOOK programs. Fixed version.
Fixes:
1. book_base_volume NOT in schema - removed
2. literal-type params need ALL 5 value fields
3. shear direction param needs all 5 fields
4. mirror_array kind='pattern'
5. notch 'side' param must be there (schema has corner,height_ratio,ratio,side,width_ratio as params 1..5)
"""
import json, random
random.seed(42)

LIT_DEFAULTS = {"numeric_value": 0.0, "string_value": "", "boolean_value": False, 
                "vector_value": [], "structured_json": "null"}

def lit_param(name, val):
    """Create a 'literal' type parameter with all 5 value fields."""
    p = {"name": name, "value_type": "number",
         "numeric_value": val, "string_value": "", "boolean_value": False,
         "vector_value": [], "structured_json": "null"}
    return p

def num_param(name, val):
    return {"name": name, "value_type": "number", "numeric_value": val}

def str_param(name, val):
    return {"name": name, "value_type": "string", "string_value": val}

def bool_param(name, val):
    return {"name": name, "value_type": "boolean", "boolean_value": val}

def vec_param(name, val):
    return {"name": name, "value_type": "vector", "vector_value": val}

def N(id_, kind, op, inputs, params, role):
    return {"id":id_,"kind":kind,"operator":op,"inputs":inputs,
            "parameters":params,"semantic_role":role}

def box(id_, w, d, h, role="dominant_mass"):
    return N(id_,"primitive","box",[],[
        num_param("width", w), num_param("depth", d), num_param("height", h),
        {"name":"center","value_type":"boolean","boolean_value":True},
    ],role)

def mat4(id_, inp, m, role="dominant_mass"):
    return N(id_,"transform","matrix4",[inp],[
        {"name":"matrix4","value_type":"matrix4","matrix4_value":m}
    ],role)

def I(): return [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

def bend(id_, inp, axis, deg, subs, role="dominant_mass"):
    return N(id_,"modifier","bend",[inp],[
        str_param("axis",axis), num_param("angle_degrees",deg), num_param("subdivisions",subs)
    ],role)

def taper(id_, inp, axis, es, ss, subs, role="dominant_mass"):
    return N(id_,"modifier","taper",[inp],[
        str_param("axis",axis), vec_param("end_scale",es), vec_param("start_scale",ss),
        num_param("subdivisions",subs)
    ],role)

def twist(id_, inp, axis, deg, subs, role="dominant_mass"):
    return N(id_,"modifier","twist",[inp],[
        str_param("axis",axis), num_param("angle_degrees",deg), num_param("subdivisions",subs)
    ],role)

def shear(id_, inp, axis, amt, role="dominant_mass"):
    # direction is a literal type - needs all 5 fields
    return N(id_,"transform","shear",[inp],[
        num_param("amount",amt), str_param("axis",axis),
        {"name":"direction","value_type":"number",
         "numeric_value":0.0,"string_value":"","boolean_value":False,"vector_value":[],"structured_json":"null"}
    ],role)

def inflate(id_, inp, axis, fac, ms, subs, role="dominant_mass"):
    return N(id_,"modifier","inflate",[inp],[
        str_param("axis",axis), lit_param("factor",fac), lit_param("middle_scale",ms),
        num_param("subdivisions",subs)
    ],role)

def pinch(id_, inp, axis, wr, pp, subs, role="dominant_mass"):
    return N(id_,"modifier","pinch",[inp],[
        str_param("axis",axis), lit_param("waist_ratio",wr), lit_param("profile_power",pp),
        num_param("subdivisions",subs)
    ],role)

def courtyard(id_, inp, mr, os="east", role="public_threshold"):
    return N(id_,"macro","courtyard",[inp],[
        num_param("margin_ratio",mr), str_param("open_side",os)
    ],role)

def carve_void(id_, inp, mr, os="east", role="public_threshold"):
    return N(id_,"macro","carve_void",[inp],[
        num_param("margin_ratio",mr), str_param("open_side",os)
    ],role)

def notch(id_, inp, side, corner, ratio, wr, hr, role="public_threshold"):
    return N(id_,"macro","notch",[inp],[
        str_param("side",side), str_param("corner",corner),
        num_param("ratio",ratio), num_param("width_ratio",wr), num_param("height_ratio",hr)
    ],role)

def lift_acc(id_, inp, acc="east", rr=0.30, sr=0.25, role="public_threshold"):
    return N(id_,"macro","lift",[inp],[
        str_param("access_side",acc), lit_param("rise_ratio",rr), lit_param("support_ratio",sr)
    ],role)

def split_wing(id_, inp, axis, layout, gr, hr, acc_s,
               bridge=True, cwr=0.25, gs=False, gshr=0.2, gswr=0.2,
               role="public_threshold"):
    return N(id_,"macro","split_wing",[inp],[
        str_param("axis",axis), str_param("layout",layout),
        num_param("gap_ratio",gr), num_param("height_ratio",hr),
        str_param("access_side",acc_s), bool_param("bridge",bridge),
        lit_param("connector_width_ratio",cwr),
        bool_param("ground_spine",gs), lit_param("ground_spine_height_ratio",gshr),
        lit_param("ground_spine_width_ratio",gswr)
    ],role)

def bexpand(id_, inp, axis, amt, sf, role="dominant_mass"):
    return N(id_,"macro","boundary_expand",[inp],[
        str_param("axis",axis), num_param("amount",amt), lit_param("shoulder_fraction",sf)
    ],role)

def bnotch(id_, inp, axis, corner, ratio, role="dominant_mass"):
    return N(id_,"macro","book_notch",[inp],[
        str_param("axis",axis), str_param("corner",corner),
        num_param("ratio",ratio),
        lit_param("outward_sign",1.0)
    ],role)

def bcarve(id_, inp, axis, fs, dr, wr, role="dominant_mass"):
    return N(id_,"macro","book_carve",[inp],[
        str_param("axis",axis), str_param("face_side",fs),
        lit_param("depth_ratio",dr), num_param("width_ratio",wr),
        lit_param("outward_sign",1.0)
    ],role)

def bfrac(id_, inp, axis, gr, deg, rbr, role="dominant_mass"):
    return N(id_,"macro","book_fracture",[inp],[
        str_param("axis",axis), num_param("gap_ratio",gr), num_param("angle_degrees",deg),
        lit_param("retained_back_ratio",rbr), lit_param("outward_sign",1.0)
    ],role)

def bextract(id_, inp, axis, fs, dr, gs, role="dominant_mass"):
    return N(id_,"macro","book_extract",[inp],[
        str_param("axis",axis), str_param("face_side",fs),
        lit_param("distance_ratio",dr), lit_param("guest_scale",gs),
        lit_param("outward_sign",1.0)
    ],role)

def blift(id_, inp, axis, dr, gs, role="dominant_mass"):
    return N(id_,"macro","book_lift",[inp],[
        str_param("axis",axis), lit_param("distance_ratio",dr),
        lit_param("guest_scale",gs), lit_param("outward_sign",1.0)
    ],role)

def blodge(id_, inp, axis, dr, gs, role="dominant_mass"):
    return N(id_,"macro","book_lodge",[inp],[
        str_param("axis",axis), lit_param("distance_ratio",dr),
        lit_param("guest_scale",gs), lit_param("outward_sign",1.0)
    ],role)

def bbranch(id_, inp, deg, tr, ar, va="input_base", role="dominant_mass"):
    return N(id_,"macro","book_branch",[inp],[
        num_param("angle_degrees",deg), lit_param("trunk_ratio",tr),
        lit_param("arm_ratio",ar), str_param("vertical_anchor",va)
    ],role)

def bsplit(id_, inp, axis, gr, deg, bsign, sgen, tr, acc_s="east", role="dominant_mass"):
    return N(id_,"macro","book_split",[inp],[
        str_param("axis",axis), num_param("gap_ratio",gr), num_param("angle_degrees",deg),
        lit_param("branch_sign",bsign), lit_param("split_generation",sgen),
        lit_param("terminal_ratio",tr), lit_param("outward_sign",1.0),
        lit_param("access_side",0.0)  # literal type
    ],role)

def brotate(id_, inp, axis, deg, rr, role="dominant_mass"):
    return N(id_,"macro","book_rotate",[inp],[
        str_param("axis",axis), num_param("angle_degrees",deg),
        lit_param("related_ratio",rr), lit_param("outward_sign",1.0)
    ],role)

def interlock(id_, inp, axis, deg, br, dr, role="dominant_mass"):
    return N(id_,"macro","interlock_related",[inp],[
        str_param("axis",axis), num_param("angle_degrees",deg),
        lit_param("bar_ratio",br), lit_param("distance_ratio",dr),
        lit_param("outward_sign",1.0)
    ],role)

def intersect_rel(id_, inp, axis, deg, br, us, role="dominant_mass"):
    return N(id_,"macro","intersect_related",[inp],[
        str_param("axis",axis), num_param("angle_degrees",deg),
        lit_param("bar_ratio",br), lit_param("unit_scale",us)
    ],role)

def offset_rel(id_, inp, axis, dr, us, role="dominant_mass"):
    return N(id_,"macro","offset_related",[inp],[
        str_param("axis",axis), lit_param("distance_ratio",dr),
        lit_param("unit_scale",us), lit_param("outward_sign",1.0)
    ],role)

def overlap_rel(id_, inp, axis, sr, shR, vo, role="dominant_mass"):
    return N(id_,"macro","overlap_related",[inp],[
        str_param("axis",axis), lit_param("slab_ratio",sr),
        lit_param("shift_ratio",shR), lit_param("vertical_overlap",vo),
        lit_param("outward_sign",1.0)
    ],role)

def nested_rel(id_, inp, axis, dr, us, role="dominant_mass"):
    return N(id_,"macro","nested_related",[inp],[
        str_param("axis",axis), lit_param("distance_ratio",dr), lit_param("unit_scale",us)
    ],role)

def merge_rel(id_, inp, axis, gr, us, role="dominant_mass"):
    return N(id_,"macro","merge_related",[inp],[
        str_param("axis",axis), num_param("gap_ratio",gr), lit_param("unit_scale",us)
    ],role)

def rel_array(id_, inp, axis, cnt, mode, spr, us, va="input_base", stag=0.0, role="dominant_mass"):
    return N(id_,"macro","related_array",[inp],[
        str_param("axis",axis), num_param("count",cnt), str_param("mode",mode),
        lit_param("spacing_ratio",spr), lit_param("unit_scale",us),
        str_param("vertical_anchor",va), lit_param("stagger_ratio",stag)
    ],role)

def embed_void(id_, inp, axis, pos, er, gs, role="dominant_mass"):
    return N(id_,"macro","embed_void",[inp],[
        str_param("axis",axis), str_param("position",pos),
        lit_param("embedded_ratio",er), lit_param("guest_scale",gs),
        lit_param("outward_sign",1.0)
    ],role)

def lean_tower(id_, inp, direction, amt, role="dominant_mass"):
    return N(id_,"macro","leaning_tower",[inp],[
        str_param("direction",direction), num_param("amount",amt)
    ],role)

def tap_tower(id_, inp, axis, es, ss, subs, role="dominant_mass"):
    return N(id_,"macro","tapered_tower",[inp],[
        str_param("axis",axis), vec_param("end_scale",es), vec_param("start_scale",ss),
        num_param("subdivisions",subs)
    ],role)

def mirror_arr(id_, inp, norm, pivot, role="dominant_mass"):
    return N(id_,"pattern","mirror_array",[inp],[
        vec_param("normal",norm), vec_param("pivot",pivot)
    ],role)

def join_rel(id_, inp, br, role="dominant_mass"):
    return N(id_,"macro","join_related",[inp],[
        lit_param("bridge_ratio",br)
    ],role)

def shift_rel(id_, inp, axis, dr, spr, role="dominant_mass"):
    return N(id_,"macro","shift_related",[inp],[
        str_param("axis",axis), lit_param("distance_ratio",dr),
        lit_param("split_ratio",spr), lit_param("outward_sign",1.0)
    ],role)

def DI(sc, sh, gfa):
    return {"schema_version":"arr.maas.dimensional_intent.v1",
            "storey_count":sc,"storey_height_m":sh,"target_gfa_m2":gfa,
            "delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}

PATHS = [
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
assert len(PATHS)==78


def make_program(i, path_id):
    v = i % 78
    # 78 template lambdas, each returning (info_list, nodes, root_id, tags, rationale)
    # info_list = [base_form, base_seed, storey_count, storey_height_m, target_gfa]
    
    T = [
        # 0: 1/1 long_axis slab - bend + courtyard
        lambda i: (["cube","slab",4,3.6,900],
            [box("b0",2.2,1.45,13.0), mat4("m0","b0",I()),
             bend("bnd","m0","x",18.0+i%5*4,4), courtyard("acc","bnd",0.15)],
            "acc",["bent-bar","east-court","long-axis"],
            "굽힌 슬래브 동측 마당이 공공성을 조직한다"),
        # 1: 1/1 long_axis slab - fracture + notch
        lambda i: (["cube","slab",4,3.3,870],
            [box("b0",2.2,1.45,13.0), mat4("m0","b0",I()),
             bfrac("frac","m0","x",0.10+i%3*0.02,22.0+i%4*5,0.55),
             notch("acc","frac","east","se",0.22,0.35,0.8)],
            "acc",["fractured-bar","east-notch"],
            "균열 절개가 단면을 강조하고 동측 노치가 진입을 연다"),
        # 2: 1/1 long_axis elliptical slab - embed_void x2 + courtyard
        lambda i: (["elliptical","slab",4,3.0,820],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             embed_void("ev1","m0","z","center",0.35+i%3*0.04,0.4),
             embed_void("ev2","ev1","x","east",0.28,0.3),
             courtyard("acc","ev2",0.13)],
            "acc",["dual-void","east-court"],
            "두 공동이 단면을 조직하고 동측 마당이 공공 접근을 담는다"),
        # 3: 1/1 long_axis slab - bbranch + bexpand + carve_void
        lambda i: (["cube","slab",4,3.3,950],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             bbranch("br","m0",30.0+i%4*10,0.55,0.35),
             bexpand("ex","br","x",0.18,0.4),
             carve_void("acc","ex",0.13)],
            "acc",["branch-expand","east-carve"],
            "가지와 확장이 합쳐져 동측 공동이 진입을 조직한다"),
        # 4: 1/1 long_axis slab - bcarve + offset_rel + carve_void
        lambda i: (["cube","slab",5,3.3,1100],
            [box("b0",2.2,1.45,13.5), mat4("m0","b0",I()),
             bcarve("cv","m0","x","east",0.30+i%3*0.04,0.4),
             offset_rel("off","cv","x",0.25,0.65),
             carve_void("acc","off",0.12)],
            "acc",["carved-offset","east-carve"],
            "동측 조각과 오프셋 날개가 공공 진입 켜를 형성한다"),
        # 5: 1/1 short_axis slab - bbranch + carve_void
        lambda i: (["cube","slab",3,3.8,820],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             bbranch("br","m0",35.0+i%3*8,0.58,0.33),
             carve_void("acc","br",0.14)],
            "acc",["short-branch","east-carve"],
            "단축 방향 가지 매스가 동측 공동으로 진입을 연다"),
        # 6: 1/1 short_axis block - brotate + notch
        lambda i: (["cube","block",4,3.5,950],
            [box("b0",1.0,1.0,13.0), mat4("m0","b0",I()),
             brotate("rot","m0","z",25.0+i%4*8,0.45),
             notch("acc","rot","east","ne",0.24,0.38,0.8)],
            "acc",["rotated-block","east-notch"],
            "회전 관계가 블록을 변형하고 동측 노치가 진입을 연다"),
        # 7: 1/1 short_axis slab - nested_rel + courtyard
        lambda i: (["cube","slab",3,3.8,790],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             nested_rel("nst","m0","x",0.22,0.65),
             courtyard("acc","nst",0.14)],
            "acc",["nested-short","east-court"],
            "내부 관련 볼륨이 포개지고 동측 마당이 공공성을 확보한다"),
        # 8: 1/1 short_axis slab - intersect_rel + bsplit + carve_void
        lambda i: (["cube","slab",4,3.3,850],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             intersect_rel("isc","m0","x",30.0+i%4*10,0.45,0.8),
             bsplit("sp","isc","y",0.07,8.0,1.0,1,0.5),
             carve_void("acc","sp",0.12)],
            "acc",["intersect-split","east-carve"],
            "교차 분기가 다각형 단면을 만들고 동측 공동이 진입을 연다"),
        # 9: 1/1 short_axis bar - bend + rel_array + notch
        lambda i: (["cube","bar",4,3.8,880],
            [box("b0",2.8,0.62,15.0), mat4("m0","b0",I()),
             bend("bnd","m0","x",22.0+i%4*5,5),
             rel_array("ra","bnd","y",2,"pack",0.22,0.85),
             notch("acc","ra","east","ne",0.28,0.4,0.9)],
            "acc",["bent-stack","east-notch"],
            "구부러진 바가 쌓이고 동측 노치가 진입을 정의한다"),
        # 10: 1/1 short_axis slab - blift + bextract + lift_acc
        lambda i: (["cube","slab",3,3.8,760],
            [box("b0",2.2,1.45,11.0), mat4("m0","b0",I()),
             blift("lft","m0","z",0.28,0.65),
             bextract("ext","lft","x","east",0.22,0.5),
             lift_acc("acc","ext")],
            "acc",["lift-extract","east-piloti"],
            "들린 매스가 동측에서 추출되고 필로티가 공공 지반을 형성한다"),
        # 11: 1/1 vertical block - interlock + notch
        lambda i: (["cube","block",4,3.5,950],
            [box("b0",1.0,1.0,14.0), mat4("m0","b0",I()),
             interlock("ilk","m0","x",25.0+i%4*8,0.4,0.38),
             notch("acc","ilk","east","se",0.25,0.38,0.75)],
            "acc",["interlock","east-notch"],
            "두 L형이 맞물리고 동측 노치가 공공 진입을 분리한다"),
        # 12: 1/1 vertical block - shear + carve_void
        lambda i: (["cube","block",4,3.4,900],
            [box("b0",1.0,1.0,13.5), mat4("m0","b0",I()),
             shear("shr","m0","z",0.35+i%4*0.05),
             carve_void("acc","shr",0.14)],
            "acc",["sheared-block","east-carve"],
            "블록이 전단되어 경사 단면을 얻고 동측 공동이 진입을 연다"),
        # 13: 1/1 vertical block - bexpand x2 + courtyard
        lambda i: (["cube","block",4,3.3,920],
            [box("b0",1.0,1.0,13.0), mat4("m0","b0",I()),
             bexpand("ex1","m0","x",0.20+i%3*0.03,0.45),
             bexpand("ex2","ex1","y",0.15,0.38),
             courtyard("acc","ex2",0.13)],
            "acc",["double-expand","east-court"],
            "두 방향 확장 블록에 동측 마당이 공공성을 확보한다"),
        # 14: 1/1 vertical block - bexpand + mirror_arr + carve_void
        lambda i: (["cube","block",4,3.3,960],
            [box("b0",1.0,1.0,13.0), mat4("m0","b0",I()),
             bexpand("ex","m0","x",0.22,0.5),
             mirror_arr("mir","ex",[1,0,0],[0,0,0]),
             carve_void("acc","mir",0.14)],
            "acc",["expand-mirror","east-carve"],
            "확장 반사 블록 쌍이 동측 공동으로 진입을 열어준다"),
        # 15: 1/1 vertical block - overlap_rel + bexpand + carve_void
        lambda i: (["cube","block",4,3.4,1000],
            [box("b0",1.0,1.0,13.0), mat4("m0","b0",I()),
             overlap_rel("ovl","m0","y",0.5,0.3+i%3*0.04,0.4),
             bexpand("ex","ovl","x",0.18,0.4),
             carve_void("acc","ex",0.12)],
            "acc",["overlap-expand","east-carve"],
            "겹쳐 확장된 블록이 동측 공동으로 공공 진입을 조직한다"),
        # 16: 3/8 long_axis bar - bend + courtyard
        lambda i: (["cube","bar",4,3.8,880],
            [box("b0",2.8,0.62,15.0), mat4("m0","b0",I()),
             bend("bnd","m0","x",25.0+i%4*5,5),
             courtyard("acc","bnd",0.15)],
            "acc",["bar-bend-3-8","east-court"],
            "3/8 바가 구부러지며 동측 마당이 공공성을 담는다"),
        # 17: 3/8 long_axis bar - bfrac + twist + carve_void
        lambda i: (["cube","bar",4,3.5,820],
            [box("b0",2.8,0.62,14.0), mat4("m0","b0",I()),
             bfrac("frac","m0","y",0.10+i%3*0.02,15.0,0.5),
             twist("twst","frac","z",12.0+i%3*4,5),
             carve_void("acc","twst",0.14)],
            "acc",["fracture-twist","east-carve"],
            "균열과 비틀림이 복합 단면을 만들고 동측 공동이 진입을 연다"),
        # 18: 3/8 long_axis bar - bsplit x2 + split_wing
        lambda i: (["cube","bar",4,3.5,950],
            [box("b0",2.8,0.62,14.0), mat4("m0","b0",I()),
             bsplit("sp1","m0","x",0.08,15.0,1.0,1,0.5),
             bsplit("sp2","sp1","y",0.06,10.0,1.0,2,0.45),
             split_wing("acc","sp2","y","parallel",0.12,0.75,"east",True,0.28)],
            "acc",["double-split","east-wing"],
            "이중 분기 바가 날개를 형성하고 동측 윙 간격이 진입을 연다"),
        # 19: 3/8 long_axis bar - bend + bbranch + carve_void
        lambda i: (["cube","bar",4,3.3,900],
            [box("b0",2.8,0.62,13.0), mat4("m0","b0",I()),
             bend("bnd","m0","x",20.0+i%5*5,4),
             bbranch("br","bnd",35.0+i%3*10,0.6,0.38),
             carve_void("acc","br",0.14)],
            "acc",["bent-branch","east-carve"],
            "구부러진 바에 가지가 자라 동측 공동이 진입을 담는다"),
        # 20: 3/8 long_axis bar - bsplit + join_rel + notch
        lambda i: (["cube","bar",4,3.4,920],
            [box("b0",2.8,0.62,13.0), mat4("m0","b0",I()),
             bsplit("sp","m0","x",0.08,12.0,1.0,1,0.55),
             join_rel("jn","sp",0.35),
             notch("acc","jn","east","ne",0.24,0.38,0.85)],
            "acc",["split-join","east-notch"],
            "분기 브리지가 이어지고 동측 노치가 공공 진입을 연다"),
        # 21: 3/8 short_axis elliptical slab - inflate + courtyard
        lambda i: (["elliptical","slab",3,3.8,780],
            [box("b0",2.2,1.45,11.0), mat4("m0","b0",I()),
             inflate("inf","m0","z",1.15+i%3*0.05,1.3,4),
             courtyard("acc","inf",0.18)],
            "acc",["inflated-slab","east-court"],
            "팽창 정수리 슬래브가 동측 마당과 공공성을 조직한다"),
        # 22: 3/8 short_axis slab - overlap_rel + carve_void
        lambda i: (["cube","slab",3,3.8,820],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             overlap_rel("ovl","m0","x",0.45,0.28+i%3*0.05,0.35),
             carve_void("acc","ovl",0.13)],
            "acc",["overlapping-slabs","east-carve"],
            "겹쳐진 슬래브가 어긋나고 동측 공동이 진입을 연다"),
        # 23: 3/8 short_axis slab - nested_rel + courtyard
        lambda i: (["cube","slab",3,3.8,790],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             nested_rel("nst","m0","y",0.20,0.6),
             courtyard("acc","nst",0.14)],
            "acc",["inscribed-nested","east-court"],
            "포개진 내부 볼륨에 동측 마당이 공공성을 확보한다"),
        # 24: 3/8 short_axis slab - intersect_rel + bsplit + carve_void
        lambda i: (["cube","slab",4,3.3,850],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             intersect_rel("isc","m0","x",30.0+i%4*10,0.45,0.8),
             bsplit("sp","isc","y",0.07,8.0,1.0,1,0.5),
             carve_void("acc","sp",0.12)],
            "acc",["intersect-split-3-8","east-carve"],
            "교차 분기로 사선 단면이 생기고 동측 공동이 진입을 연다"),
        # 25: 3/8 short_axis bar - bend + rel_array + notch
        lambda i: (["cube","bar",4,3.8,880],
            [box("b0",2.8,0.62,15.0), mat4("m0","b0",I()),
             bend("bnd","m0","x",22.0+i%4*5,5),
             rel_array("ra","bnd","y",2,"pack",0.22,0.85),
             notch("acc","ra","east","ne",0.28,0.4,0.9)],
            "acc",["bend-stack-3-8","east-notch"],
            "3/8 바 쌍이 구부러져 쌓이고 동측 노치가 진입을 연다"),
        # 26: 3/8 short_axis slab - blift + bcarve + lift_acc
        lambda i: (["cube","slab",3,3.8,760],
            [box("b0",2.2,1.45,11.0), mat4("m0","b0",I()),
             blift("lft","m0","z",0.26,0.6),
             bcarve("cv","lft","x","east",0.28,0.38),
             lift_acc("acc","cv")],
            "acc",["lift-carve","east-piloti"],
            "들린 3/8 슬래브가 동측에서 조각되고 필로티가 공간을 연다"),
        # 27: 3/8 vertical tower - interlock + courtyard
        lambda i: (["cube","tower",5,3.0,1080],
            [box("b0",0.68,0.68,15.0), mat4("m0","b0",I()),
             interlock("ilk","m0","y",22.0+i%3*7,0.38,0.36),
             courtyard("acc","ilk",0.14)],
            "acc",["tower-interlock","east-court"],
            "타워 두 L형이 맞물리고 동측 마당이 공공성을 담는다"),
        # 28: 3/8 vertical tower - shear + carve_void
        lambda i: (["cube","tower",4,3.8,980],
            [box("b0",0.68,0.68,15.0), mat4("m0","b0",I()),
             shear("shr","m0","z",0.35+i%3*0.05),
             carve_void("acc","shr",0.13)],
            "acc",["sheared-tower","east-carve"],
            "전단 타워가 경사 단면을 얻고 동측 공동이 진입을 연다"),
        # 29: 3/8 vertical tower - bbranch x2 + carve_void
        lambda i: (["cube","tower",5,3.0,1100],
            [box("b0",0.68,0.68,14.0), mat4("m0","b0",I()),
             bbranch("br1","m0",40.0+i%3*10,0.58,0.33),
             bbranch("br2","br1",-28.0-i%2*8,0.52,0.28),
             carve_void("acc","br2",0.13)],
            "acc",["double-branch-tower","east-carve"],
            "이중 분기 타워가 Y형 평면을 이루고 동측 공동이 진입을 연다"),
        # 30: 3/8 vertical tower - bnotch + twist + notch
        lambda i: (["cube","tower",5,3.0,1050],
            [box("b0",0.68,0.68,15.0), mat4("m0","b0",I()),
             bnotch("ntc","m0","z","sw",0.24+i%3*0.04),
             twist("twst","ntc","z",16.0+i%3*4,5),
             notch("acc","twst","east","se",0.24,0.36,0.78)],
            "acc",["notch-twist-tower","east-notch"],
            "노치와 비틀림이 다각 단면을 만들고 동측 노치가 진입을 연다"),
        # 31: 3/8 vertical block - bexpand + nested_rel + courtyard
        lambda i: (["cube","block",4,3.3,880],
            [box("b0",1.0,1.0,13.0), mat4("m0","b0",I()),
             bexpand("ex","m0","z",0.22,0.5),
             nested_rel("nst","ex","x",0.20,0.6),
             courtyard("acc","nst",0.14)],
            "acc",["expand-nest","east-court"],
            "확장된 블록 안에 내부 볼륨이 포개지고 동측 마당이 공공성을 드러낸다"),
        # 32: 1/2 long_axis slab - offset_rel + carve_void
        lambda i: (["cube","slab",4,3.3,880],
            [box("b0",2.2,1.45,13.0), mat4("m0","b0",I()),
             offset_rel("off","m0","y",0.3+i%3*0.05,0.7),
             carve_void("acc","off",0.13)],
            "acc",["offset-slab","east-carve"],
            "슬래브 오프셋 날개가 두 켜를 만들고 동측 공동이 진입을 조직한다"),
        # 33: 1/2 long_axis slab - taper + courtyard
        lambda i: (["cube","slab",4,3.5,860],
            [box("b0",2.2,1.45,14.0), mat4("m0","b0",I()),
             taper("tpr","m0","z",[0.7,0.7],[1.0,1.0],4),
             courtyard("acc","tpr",0.15)],
            "acc",["tapered-slab","east-court"],
            "슬래브 상부가 좁아지며 동측 열린 마당이 공공 진입을 담는다"),
        # 34: 1/2 long_axis slab - bsplit x2 + notch
        lambda i: (["cube","slab",4,3.3,940],
            [box("b0",2.2,1.45,13.0), mat4("m0","b0",I()),
             bsplit("sp1","m0","x",0.09,14.0,1.0,1,0.5),
             bsplit("sp2","sp1","y",0.07,8.0,1.0,2,0.42),
             notch("acc","sp2","east","ne",0.22,0.35,0.8)],
            "acc",["double-split-half","east-notch"],
            "이중 분기 슬래브가 ㄷ형 평면을 이루고 동측 노치가 입구를 연다"),
        # 35: 1/2 long_axis slab - bend + bbranch + carve_void
        lambda i: (["cube","slab",4,3.3,900],
            [box("b0",2.2,1.45,13.0), mat4("m0","b0",I()),
             bend("bnd","m0","x",22.0+i%4*6,4),
             bbranch("br","bnd",30.0,0.55,0.32),
             carve_void("acc","br",0.14)],
            "acc",["bent-branch-half","east-carve"],
            "구부러진 슬래브에 가지가 붙어 동측 공동이 진입을 담는다"),
        # 36: 1/2 long_axis slab - bsplit + join_rel + courtyard
        lambda i: (["cube","slab",4,3.3,920],
            [box("b0",2.2,1.45,13.0), mat4("m0","b0",I()),
             bsplit("sp","m0","x",0.08,12.0,1.0,1,0.55),
             join_rel("jn","sp",0.30),
             courtyard("acc","jn",0.14)],
            "acc",["split-join-half","east-court"],
            "분기 슬래브가 브리지로 이어지고 동측 열린 마당이 진입을 조직한다"),
        # 37: 1/2 short_axis elliptical slab - inflate + carve_void
        lambda i: (["elliptical","slab",3,3.8,780],
            [box("b0",2.2,1.45,11.0), mat4("m0","b0",I()),
             inflate("inf","m0","z",1.2+i%3*0.06,1.4,4),
             carve_void("acc","inf",0.13)],
            "acc",["inflated-half","east-carve"],
            "단축 팽창 슬래브가 부풀고 동측 공동이 진입을 연다"),
        # 38: 1/2 short_axis slab - overlap_rel + notch
        lambda i: (["cube","slab",3,3.8,820],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             overlap_rel("ovl","m0","y",0.48,0.25+i%3*0.05,0.38),
             notch("acc","ovl","east","se",0.24,0.38,0.8)],
            "acc",["overlap-half","east-notch"],
            "슬래브가 단축 어긋나고 동측 노치가 공공 진입을 정의한다"),
        # 39: 1/2 short_axis slab - nested_rel + courtyard
        lambda i: (["cube","slab",3,3.8,790],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             nested_rel("nst","m0","y",0.20,0.6),
             courtyard("acc","nst",0.14)],
            "acc",["nested-half","east-court"],
            "포개진 내부 볼륨에 동측 마당이 공공성을 확보한다"),
        # 40: 1/2 short_axis slab - nested_rel + intersect_rel + carve_void
        lambda i: (["cube","slab",4,3.3,840],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             nested_rel("nst","m0","y",0.18,0.58),
             intersect_rel("isc","nst","x",25.0+i%3*8,0.4,0.75),
             carve_void("acc","isc",0.12)],
            "acc",["inscribe-intersect-half","east-carve"],
            "포개진 볼륨이 교차로 잘려 동측 공동이 진입을 연다"),
        # 41: 1/2 short_axis slab - bbranch + rel_array + notch
        lambda i: (["cube","slab",4,3.3,950],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             bbranch("br","m0",35.0+i%3*10,0.6,0.32),
             rel_array("ra","br","x",2,"pack",0.18,0.82),
             notch("acc","ra","east","ne",0.24,0.38,0.85)],
            "acc",["branch-pack-half","east-notch"],
            "가지 매스가 쌓이고 동북 노치가 공공 진입을 분리한다"),
        # 42: 1/2 short_axis slab - blift + bcarve + lift_acc
        lambda i: (["cube","slab",3,3.8,760],
            [box("b0",2.2,1.45,11.0), mat4("m0","b0",I()),
             blift("lft","m0","z",0.26,0.6),
             bcarve("cv","lft","x","east",0.28,0.38),
             lift_acc("acc","cv")],
            "acc",["lift-carve-half","east-piloti"],
            "들린 슬래브가 동측에서 조각되고 필로티가 공공 지반을 열어준다"),
        # 43: 1/2 vertical block - twist + carve_void
        lambda i: (["cube","block",5,3.2,1000],
            [box("b0",1.0,1.0,16.0), mat4("m0","b0",I()),
             twist("twst","m0","z",18.0+i%4*5,5),
             carve_void("acc","twst",0.14)],
            "acc",["twisted-block","east-carve"],
            "수직 비틀림이 평면을 회전시키고 동측 공동이 공공 접근을 연다"),
        # 44: 1/2 vertical block - pinch + notch
        lambda i: (["cube","block",4,3.8,920],
            [box("b0",1.0,1.0,15.0), mat4("m0","b0",I()),
             pinch("pnc","m0","z",0.45+i%3*0.05,2.0,5),
             notch("acc","pnc","east","se",0.26,0.4,0.8)],
            "acc",["pinched-block","east-notch"],
            "중간부가 조여든 블록에 동측 노치가 공공 접근을 열어준다"),
        # 45: 1/2 vertical block - bbranch x2 + split_wing
        lambda i: (["cube","block",4,3.5,1050],
            [box("b0",1.0,1.0,14.0), mat4("m0","b0",I()),
             bbranch("br1","m0",40.0+i%3*10,0.6,0.35),
             bbranch("br2","br1",-30.0-i%2*10,0.55,0.30),
             split_wing("acc","br2","y","parallel",0.12,0.8,"east",True,0.25)],
            "acc",["double-branch-block","east-wing"],
            "이중 분기 블록이 Y형이 되고 동측 윙이 진입을 담는다"),
        # 46: 1/2 vertical block - bnotch + twist + carve_void
        lambda i: (["cube","block",4,3.5,900],
            [box("b0",1.0,1.0,14.0), mat4("m0","b0",I()),
             bnotch("ntc","m0","z","ne",0.25+i%3*0.04),
             twist("twst","ntc","z",14.0+i%3*4,5),
             carve_void("acc","twst",0.13)],
            "acc",["notch-twist-block","east-carve"],
            "모서리 잘림과 비틀림이 합쳐지고 동측 공동이 진입을 연다"),
        # 47: 1/2 vertical block - bexpand + nested_rel + courtyard
        lambda i: (["cube","block",4,3.3,880],
            [box("b0",1.0,1.0,13.0), mat4("m0","b0",I()),
             bexpand("ex","m0","z",0.22,0.5),
             nested_rel("nst","ex","x",0.20,0.6),
             courtyard("acc","nst",0.14)],
            "acc",["expand-nest-half","east-court"],
            "확장 블록 안에 내부 볼륨이 포개지고 동측 마당이 공공성을 드러낸다"),
        # 48: 1/4 long_axis slab - offset_rel + carve_void
        lambda i: (["cube","slab",3,3.8,750],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             offset_rel("off","m0","y",0.32+i%3*0.05,0.72),
             carve_void("acc","off",0.13)],
            "acc",["offset-quarter","east-carve"],
            "1/4 슬래브 오프셋 날개가 두 켜를 만들고 동측 공동이 진입을 연다"),
        # 49: 1/4 long_axis slab - taper + courtyard
        lambda i: (["cube","slab",3,3.8,720],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             taper("tpr","m0","z",[0.75,0.75],[1.0,1.0],4),
             courtyard("acc","tpr",0.16)],
            "acc",["tapered-quarter","east-court"],
            "1/4 슬래브가 위로 좁아지며 동측 마당이 공공 진입을 확보한다"),
        # 50: 1/4 long_axis slab - bsplit x2 + notch
        lambda i: (["cube","slab",4,3.3,820],
            [box("b0",2.2,1.45,13.0), mat4("m0","b0",I()),
             bsplit("sp1","m0","x",0.08,15.0,1.0,1,0.5),
             bsplit("sp2","sp1","y",0.06,10.0,1.0,2,0.42),
             notch("acc","sp2","east","ne",0.22,0.35,0.8)],
            "acc",["split-split-quarter","east-notch"],
            "1/4 슬래브 이중 분기가 ㄱ형 평면을 이루고 동측 노치가 진입을 연다"),
        # 51: 1/4 long_axis slab - taper + bend + carve_void
        lambda i: (["cube","slab",4,3.3,840],
            [box("b0",2.2,1.45,13.0), mat4("m0","b0",I()),
             taper("tpr","m0","z",[0.72,0.72],[1.0,1.0],4),
             bend("bnd","tpr","x",16.0+i%4*5,4),
             carve_void("acc","bnd",0.13)],
            "acc",["taper-bend-quarter","east-carve"],
            "상부 좁아짐과 굽힘이 연속 변형을 이루고 동측 공동이 진입을 연다"),
        # 52: 1/4 long_axis slab - pinch + join_rel + notch
        lambda i: (["cube","slab",4,3.3,800],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             pinch("pnc","m0","z",0.42+i%3*0.05,2.0,4),
             join_rel("jn","pnc",0.28),
             notch("acc","jn","east","se",0.24,0.38,0.8)],
            "acc",["pinch-join-quarter","east-notch"],
            "허리 조임 슬래브가 브리지로 이어지고 동측 노치가 진입을 연다"),
        # 53: 1/4 short_axis slab - bextract + carve_void
        lambda i: (["cube","slab",3,3.8,740],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             bextract("ext","m0","y","east",0.25,0.55),
             carve_void("acc","ext",0.13)],
            "acc",["extract-quarter","east-carve"],
            "1/4 슬래브 동측 추출 돌출과 공동이 진입을 정의한다"),
        # 54: 1/4 short_axis slab - blodge + courtyard
        lambda i: (["cube","slab",3,3.8,760],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             blodge("ldg","m0","x",0.28+i%3*0.04,0.5),
             courtyard("acc","ldg",0.14)],
            "acc",["lodged-quarter","east-court"],
            "로지된 볼륨이 끼고 동측 마당이 공공성을 확보한다"),
        # 55: 1/4 short_axis slab - bextract + notch
        lambda i: (["cube","slab",3,3.8,740],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             bextract("ext","m0","x","east",0.22,0.45),
             notch("acc","ext","east","ne",0.23,0.35,0.78)],
            "acc",["extract-notch-quarter","east-notch"],
            "1/4 슬래브 추출 채널과 노치가 공공 진입 공간을 분리한다"),
        # 56: 1/4 short_axis slab - nested_rel + intersect_rel + carve_void
        lambda i: (["cube","slab",3,3.8,780],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             nested_rel("nst","m0","y",0.18,0.58),
             intersect_rel("isc","nst","x",28.0+i%3*7,0.38,0.72),
             carve_void("acc","isc",0.12)],
            "acc",["inscribe-intersect-quarter","east-carve"],
            "내부 볼륨이 교차로 잘려 다각형 평면이 생기고 동측 공동이 진입을 연다"),
        # 57: 1/4 short_axis slab - bbranch + rel_array + notch
        lambda i: (["cube","slab",4,3.3,890],
            [box("b0",2.2,1.45,12.0), mat4("m0","b0",I()),
             bbranch("br","m0",38.0+i%3*10,0.58,0.32),
             rel_array("ra","br","x",2,"pack",0.18,0.82),
             notch("acc","ra","east","ne",0.23,0.36,0.82)],
            "acc",["branch-pack-quarter","east-notch"],
            "가지 적층과 동북 노치가 공공 진입을 분리한다"),
        # 58: 1/4 short_axis slab - blift + bcarve + lift_acc
        lambda i: (["cube","slab",3,3.8,720],
            [box("b0",2.2,1.45,11.0), mat4("m0","b0",I()),
             blift("lft","m0","z",0.26,0.58),
             bcarve("cv","lft","x","east",0.26,0.36),
             lift_acc("acc","cv","east",0.28,0.22)],
            "acc",["lift-carve-quarter","east-piloti"],
            "들린 1/4 슬래브가 동측에서 조각되고 필로티가 공공 지반을 연다"),
        # 59: 1/4 vertical block - twist + carve_void
        lambda i: (["cube","block",5,3.0,860],
            [box("b0",1.0,1.0,15.0), mat4("m0","b0",I()),
             twist("twst","m0","z",20.0+i%4*5,5),
             carve_void("acc","twst",0.14)],
            "acc",["twist-quarter","east-carve"],
            "1/4 수직 블록이 비틀리며 동측 공동이 진입을 조직한다"),
        # 60: 1/4 vertical block - pinch + notch
        lambda i: (["cube","block",4,3.8,860],
            [box("b0",1.0,1.0,15.0), mat4("m0","b0",I()),
             pinch("pnc","m0","z",0.42+i%3*0.05,2.2,5),
             notch("acc","pnc","east","se",0.25,0.38,0.78)],
            "acc",["pinch-quarter","east-notch"],
            "1/4 블록 허리가 조여들고 동측 노치가 공공 진입을 연다"),
        # 61: 1/4 vertical block - bbranch x2 + split_wing
        lambda i: (["cube","block",4,3.5,950],
            [box("b0",1.0,1.0,14.0), mat4("m0","b0",I()),
             bbranch("br1","m0",42.0+i%3*10,0.58,0.33),
             bbranch("br2","br1",-32.0-i%2*8,0.52,0.28),
             split_wing("acc","br2","x","parallel",0.12,0.78,"east",True,0.24)],
            "acc",["double-branch-quarter","east-wing"],
            "1/4 블록 이중 분기가 T형 평면을 이루고 동측 윙이 진입을 담는다"),
        # 62: 1/4 vertical block - shift_rel + bnotch + notch
        lambda i: (["cube","block",4,3.5,870],
            [box("b0",1.0,1.0,14.0), mat4("m0","b0",I()),
             shift_rel("shr","m0","x",0.28+i%3*0.05,0.5),
             bnotch("ntc","shr","z","ne",0.24+i%3*0.03),
             notch("acc","ntc","east","ne",0.22,0.34,0.76)],
            "acc",["shift-notch-quarter","east-notch"],
            "이동 블록의 모서리 잘림과 동측 노치가 공공 진입을 연다"),
        # 63: 1/4 vertical block - embed_void + overlap_rel + carve_void
        lambda i: (["cube","block",4,3.5,900],
            [box("b0",1.0,1.0,14.0), mat4("m0","b0",I()),
             embed_void("emb","m0","z","center",0.32+i%3*0.04,0.38),
             overlap_rel("ovl","emb","x",0.45,0.28+i%3*0.05,0.35),
             carve_void("acc","ovl",0.13)],
            "acc",["embed-overlap-quarter","east-carve"],
            "매립 공동과 겹침이 복합 단면을 만들고 동측 공동이 진입을 연다"),
        # 64: 1/8 long_axis bar - nested_rel + courtyard
        lambda i: (["cube","bar",3,3.8,700],
            [box("b0",2.8,0.62,12.0), mat4("m0","b0",I()),
             nested_rel("nst","m0","x",0.25+i%3*0.04,0.62),
             courtyard("acc","nst",0.14)],
            "acc",["nested-bar","east-court"],
            "1/8 바 안에 내부 볼륨이 포개지고 동측 마당이 공공성을 확보한다"),
        # 65: 1/8 long_axis bar - bcarve + notch
        lambda i: (["cube","bar",3,3.8,680],
            [box("b0",2.8,0.62,12.0), mat4("m0","b0",I()),
             bcarve("cv","m0","x","east",0.28+i%3*0.04,0.35),
             notch("acc","cv","east","ne",0.22,0.34,0.76)],
            "acc",["carved-bar","east-notch"],
            "1/8 바 동측이 조각되고 노치가 공공 진입 공간을 정의한다"),
        # 66: 1/8 long_axis bar - intersect_rel x2 + carve_void
        lambda i: (["cube","bar",4,3.3,780],
            [box("b0",2.8,0.62,13.0), mat4("m0","b0",I()),
             intersect_rel("isc1","m0","x",25.0+i%3*8,0.42,0.78),
             intersect_rel("isc2","isc1","y",20.0+i%2*8,0.38,0.72),
             carve_void("acc","isc2",0.13)],
            "acc",["double-intersect","east-carve"],
            "이중 사선 교차가 바를 잘라 복잡한 단면을 만들고 동측 공동이 진입을 연다"),
        # 67: 1/8 long_axis bar - taper + bend + carve_void
        lambda i: (["cube","bar",4,3.3,780],
            [box("b0",2.8,0.62,13.0), mat4("m0","b0",I()),
             taper("tpr","m0","z",[0.7,0.7],[1.0,1.0],4),
             bend("bnd","tpr","x",18.0+i%4*5,4),
             carve_void("acc","bnd",0.12)],
            "acc",["taper-bend-bar","east-carve"],
            "바가 좁아지며 구부러진 연속 변형이 이루어지고 동측 공동이 진입을 연다"),
        # 68: 1/8 long_axis bar - pinch + join_rel + notch
        lambda i: (["cube","bar",3,3.8,700],
            [box("b0",2.8,0.62,12.0), mat4("m0","b0",I()),
             pinch("pnc","m0","z",0.4+i%3*0.05,2.2,4),
             join_rel("jn","pnc",0.26),
             notch("acc","jn","east","se",0.22,0.34,0.76)],
            "acc",["pinch-join-bar","east-notch"],
            "허리 조임 바 쌍이 브리지로 이어지고 동측 노치가 공공 진입을 연다"),
        # 69: 1/8 short_axis bar - bextract + carve_void
        lambda i: (["cube","bar",3,3.8,680],
            [box("b0",2.8,0.62,12.0), mat4("m0","b0",I()),
             bextract("ext","m0","y","east",0.24,0.52),
             carve_void("acc","ext",0.13)],
            "acc",["extract-bar","east-carve"],
            "1/8 짧은 축 바에서 동측 추출 돌출과 공동이 진입을 연다"),
        # 70: 1/8 short_axis bar - blodge + courtyard
        lambda i: (["cube","bar",3,3.8,680],
            [box("b0",2.8,0.62,12.0), mat4("m0","b0",I()),
             blodge("ldg","m0","y",0.26+i%3*0.04,0.48),
             courtyard("acc","ldg",0.13)],
            "acc",["lodged-bar","east-court"],
            "1/8 바에 로지된 볼륨이 끼고 동측 마당이 공공성을 담는다"),
        # 71: 1/8 short_axis bar - bextract + notch
        lambda i: (["cube","bar",3,3.8,660],
            [box("b0",2.8,0.62,12.0), mat4("m0","b0",I()),
             bextract("ext","m0","x","east",0.20,0.42),
             notch("acc","ext","east","ne",0.22,0.34,0.76)],
            "acc",["extract-notch-bar","east-notch"],
            "1/8 바 추출 채널이 생기고 노치가 공공 진입을 분리한다"),
        # 72: 1/8 short_axis bar - nested_rel + intersect_rel + carve_void
        lambda i: (["cube","bar",3,3.8,680],
            [box("b0",2.8,0.62,12.0), mat4("m0","b0",I()),
             nested_rel("nst","m0","y",0.16,0.55),
             intersect_rel("isc","nst","x",22.0+i%3*7,0.36,0.68),
             carve_void("acc","isc",0.12)],
            "acc",["inscribe-intersect-bar","east-carve"],
            "내부 바가 교차로 잘리고 동측 공동이 진입을 조직한다"),
        # 73: 1/8 short_axis elliptical bar - inflate + rel_array + courtyard
        lambda i: (["elliptical","bar",3,3.5,740],
            [box("b0",2.8,0.62,11.0), mat4("m0","b0",I()),
             inflate("inf","m0","z",1.18+i%3*0.05,1.3,4),
             rel_array("ra","inf","y",2,"pack",0.2,0.82),
             courtyard("acc","ra",0.13)],
            "acc",["inflate-pack","east-court"],
            "팽창된 바 한 쌍이 나란하고 동측 마당이 공공성을 담는다"),
        # 74: 1/8 short_axis bar - embed_void + taper + notch
        lambda i: (["cube","bar",3,3.8,700],
            [box("b0",2.8,0.62,12.0), mat4("m0","b0",I()),
             embed_void("emb","m0","z","center",0.30+i%3*0.04,0.38),
             taper("tpr","emb","z",[0.72,0.72],[1.0,1.0],4),
             notch("acc","tpr","east","se",0.24,0.36,0.78)],
            "acc",["embed-taper","east-notch"],
            "공동 매립 바가 좁아지고 동측 노치가 공공 진입을 연다"),
        # 75: 1/8 vertical block - bsplit + split_wing
        lambda i: (["cube","block",4,3.5,860],
            [box("b0",1.0,1.0,14.0), mat4("m0","b0",I()),
             bsplit("sp","m0","x",0.08,14.0,1.0,1,0.5),
             split_wing("acc","sp","y","parallel",0.12,0.8,"east",True,0.26)],
            "acc",["split-wing-18","east-wing"],
            "1/8 수직 분기가 날개가 되고 동측 윙 간격이 진입을 형성한다"),
        # 76: 1/8 vertical block - bnotch + carve_void
        lambda i: (["cube","block",4,3.5,820],
            [box("b0",1.0,1.0,14.0), mat4("m0","b0",I()),
             bnotch("ntc","m0","z","ne",0.26+i%3*0.04),
             carve_void("acc","ntc",0.13)],
            "acc",["notched-vertical","east-carve"],
            "1/8 수직 블록 모서리 잘림에 동측 공동이 공공 진입을 연다"),
        # 77: 1/8 vertical block - bend x2 + carve_void
        lambda i: (["cube","block",4,3.3,830],
            [box("b0",1.0,1.0,13.0), mat4("m0","b0",I()),
             bend("bnd1","m0","x",18.0+i%4*5,4),
             bend("bnd2","bnd1","y",14.0+i%3*4,4),
             carve_void("acc","bnd2",0.13)],
            "acc",["double-bent","east-carve"],
            "두 방향 구부림이 안장형 단면을 만들고 동측 공동이 공공 진입을 조직한다"),
    ]
    
    assert len(T)==78, f"Expected 78 templates, got {len(T)}"
    result = T[v](i)
    info, nodes, root_id, tags, rationale = result
    base_form, base_seed, sc, sh, gfa = info
    
    name = f"comp18_p{i:03d}_{base_seed}_{v:02d}"
    
    return {
        "name": name,
        "base_form_id": base_form,
        "base_seed": base_seed,
        "intent_tags": tags[:12],
        "nodes": nodes,
        "root_id": root_id,
        "rationale": rationale,
        "dimensional_intent": DI(sc, sh, gfa),
        "book_composition_path_id": path_id,
    }


# Build 120 programs: assign paths
path_assignments = list(PATHS) + list(PATHS[:42])
random.shuffle(path_assignments)
assert len(path_assignments) == 120

programs = []
for idx in range(120):
    pid = path_assignments[idx]
    prog = make_program(idx, pid)
    programs.append(prog)

all_principles = [
    "book:operative:bend","book:operative:fracture","book:combination:04:embed+embed",
    "book:combination:17:branch+expand","book:case:60:carve+offset","book:operative:branch",
    "book:operative:rotate","book:operative:inscribe","book:combination:12:intersect+split",
    "book:aggregation:stack:bend","book:case:68:lift+extrude","book:operative:interlock",
    "book:operative:shear","book:combination:08:expand+expand","book:aggregation:reflect:expand",
    "book:case:64:overlap+expand","book:combination:16:bend+branch","book:combination:03:split+split",
    "book:aggregation:join:split","book:operative:inflate","book:operative:overlap",
    "book:combination:07:branch+branch","book:combination:20:notch+twist","book:case:63:expand+nest",
    "book:operative:offset","book:operative:compress","book:combination:15:taper+bend",
    "book:aggregation:join+array:pinch","book:operative:extrude","book:operative:lodge",
    "book:operative:extract","book:combination:11:inscribe+intersect",
    "book:aggregation:pack+stack:branch","book:case:67:lift+carve","book:operative:twist",
    "book:operative:pinch","book:combination:19:shift+notch","book:case:62:embed+overlap",
    "book:operative:nest","book:operative:carve","book:combination:02:intersect+intersect",
    "book:aggregation:pack:inflate","book:case:66:embed+taper","book:operative:split",
    "book:operative:notch","book:combination:06:bend+bend",
]

payload = {
    "programs": programs,
    "book_principle_ids": sorted(list(set(all_principles))),
}

out_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp18.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(programs)} programs to {out_path}")
assert len(programs) == 120

from collections import Counter
cnt = Counter(p["book_composition_path_id"] for p in programs)
print(f"Unique paths: {len(cnt)}, max reuse: {max(cnt.values())}")
print(f"Principles: {len(payload['book_principle_ids'])}")
