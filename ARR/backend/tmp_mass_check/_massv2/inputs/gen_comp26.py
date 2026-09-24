import sys
import json
sys.stdout.reconfigure(encoding='utf-8')

# ── SITE FACTS ──────────────────────────────────────────────────────────────
# parcel_area_m2: 2499.7   ground_capacity: 1497.877   FAR_capacity: 6241.962
# storey_cap: 5   storey_height: 3.8 m   access: east   sunlight-setback: north
# GFA band: 3745 – 5930 m²   target: all 5-storey unless idea needs fewer

DI5  = {"schema_version":"arr.maas.dimensional_intent.v1","storey_count":5,
         "storey_height_m":3.8,"target_gfa_m2":4800.0,
         "delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}
DI5b = {"schema_version":"arr.maas.dimensional_intent.v1","storey_count":5,
         "storey_height_m":3.8,"target_gfa_m2":5100.0,
         "delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}
DI5c = {"schema_version":"arr.maas.dimensional_intent.v1","storey_count":5,
         "storey_height_m":3.8,"target_gfa_m2":4500.0,
         "delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}
DI5d = {"schema_version":"arr.maas.dimensional_intent.v1","storey_count":5,
         "storey_height_m":3.8,"target_gfa_m2":4200.0,
         "delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}
DI5e = {"schema_version":"arr.maas.dimensional_intent.v1","storey_count":5,
         "storey_height_m":3.8,"target_gfa_m2":5400.0,
         "delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}
DI5f = {"schema_version":"arr.maas.dimensional_intent.v1","storey_count":5,
         "storey_height_m":3.8,"target_gfa_m2":3900.0,
         "delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}
DI4  = {"schema_version":"arr.maas.dimensional_intent.v1","storey_count":4,
         "storey_height_m":3.8,"target_gfa_m2":4000.0,
         "delivery_policy":"preserve_physical_dimensions","programme_status":"unknown"}

E = {"access_side":"east","north_side":"north"}
ES= {"access_side":"east","north_side":"south"}

# ── 120 SENTENCES ─────────────────────────────────────────────────────────
# Layout: 18 groups (6 base volumes × 3 orientations) of 7/6 each
# 1/1-LA(7), 1/1-SA(7), 1/1-V(7) = 21
# 1/16-LA(7), 1/16-SA(7), 1/16-V(7) = 21
# 1/2-LA(7), 1/2-SA(7), 1/2-V(7) = 21
# 1/4-LA(7), 1/4-SA(7), 1/4-V(7) = 21
# 1/8-LA(6), 1/8-SA(6), 1/8-V(6) = 18
# 3/8-LA(6), 3/8-SA(6), 3/8-V(6) = 18
# TOTAL = 21+21+21+21+18+18 = 120

sentences = [

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 1: 1/1 long_axis (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "one1_la_rotate_array_stack_v0",
  "book_composition_path_id": "book:path:2034cd8f424a365b7f9fe3117419c697ca9e05d18fd7d926b691cac7dcb442f8",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube footprint long-axis: rotate successive floors by 15 deg each, then array and stack to create a spiralling massing whose plan traces twist from east entry podium to recessed north parapet. GFA 4800 sits mid-band."
},
{
  "name": "one1_la_rotate_array_stack_v1",
  "book_composition_path_id": "book:path:2dfebd2d58df20735de62b21681287534c1ff53daa57c4fdd1fa3a8b5033e31c",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Cube long-axis: alternate rotation array-stack at wider increment; upper volumes cantilevered over north boundary with reduced footprint satisfying the stepped setback. GFA 5100, all 5 storeys."
},
{
  "name": "one1_la_taper_array_v1",
  "book_composition_path_id": "book:path:5b70812775329f8732c56286bf752fb207edbe0527ca51a75c9c9c03a3a7273b",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Cube long-axis: tapered bars repeated in horizontal array each shifted north; stacked set uses sunlight setback as formal driver producing a notched north profile. GFA 4500."
},
{
  "name": "one1_la_branch_v7",
  "book_composition_path_id": "book:path:9e69952975f6e588b216c253ef98780c45bbdf1036b83c8047bf4e57c236a27d",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube long-axis: single branch arm angles outward from main trunk toward east road; creates covered ground forecourt under overhanging arm without exceeding coverage limit. GFA 4800."
},
{
  "name": "one1_la_branch_v8",
  "book_composition_path_id": "book:path:bf11ca106f64cc1398e993d2c4626846d40a591653ddf2596f9429b52b93424e",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Cube long-axis: branch at high trunk ratio; secondary arm shorter than trunk, aimed east; lower GFA 4200 reflects the arm reducing floor area to leave room for landscaped forecourt."
},
{
  "name": "one1_la_embed_overlap_v0",
  "book_composition_path_id": "book:path:2d0808fd6e0f5230daf4726922feeb332b45364e746f4f95208d7cd66e15746b",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Cube long-axis: embed a thinner volume inside the main block then overlap it slightly outward; creates a telescoping east facade with deep shadow reveals. GFA 5400, captures upper FAR limit."
},
{
  "name": "one1_la_bend_bend_v0",
  "book_composition_path_id": "book:path:59a4c65f9eb733b1fd91665019eb7618246210703a6ab56242135b39efb0c257",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube long-axis: two consecutive bends produce a gentle S-curve in plan; east entry on inflection point; north face curves away from boundary reducing massing impact. GFA 4800."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 2: 1/1 short_axis (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "one1_sa_rotate_array_stack_v7",
  "book_composition_path_id": "book:path:99438cc48216d25d3f776e5057e9e3ba0529751902e037024044c0d7d620651c",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube short-axis: floors rotated in-plan 12 deg increments producing a pinwheeling silhouette; short-axis orientation keeps each floor within the north setback envelope. GFA 4800."
},
{
  "name": "one1_sa_rotate_array_stack_v9",
  "book_composition_path_id": "book:path:6914467c9db8568094a64e2c1fbe1ed4e8235f04866aae8d058c60eee6cbf3d1",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Cube short-axis: rotation+stack at v9 increment; top floor offset maximises solar access. GFA 4500 preserves BCR headroom while reaching FAR mid-point."
},
{
  "name": "one1_sa_taper_array_v0",
  "book_composition_path_id": "book:path:e7e899b351175422a6a564e1b36c8627cfa375f20299201717cb9b8d5a04c2fb",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Cube short-axis: taper-array produces a stepped ziggurat profile; each repeated tier slightly smaller on north side satisfying the legal-plan reduction from 1922 to 1691 m2. GFA 5100."
},
{
  "name": "one1_sa_carve_v0",
  "book_composition_path_id": "book:path:e1085d42ea1641d73c5c3cf048ba765291bc487e8611b8b84a5f8b4457022dd3",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube short-axis: carve removes one corner void; void opens south light well while the north face stays continuous and thick to absorb service cores. GFA 4800."
},
{
  "name": "one1_sa_carve_offset_v1",
  "book_composition_path_id": "book:path:8e014a703c32eaf84ffed89944bd29f0b5737da3239016c2f831b2d9fb688035",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Cube short-axis: carve plus offset produces a C-shaped plan with shifted inner skin; east-facing court receives road light while north wing steps back for setback compliance. GFA 4500."
},
{
  "name": "one1_sa_inscribe_inscribe_v2",
  "book_composition_path_id": "book:path:bd6b6e393630c79a3426969e7e0c8ab39b34f675da4c4b70fefb2775cb868848",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube short-axis: two concentric inscribed solids produce a box-within-box section; inner solid floated one storey above grade; interstitial volume used as public atrium. GFA 4800."
},
{
  "name": "one1_sa_inscribe_inscribe_v3",
  "book_composition_path_id": "book:path:0bc34246e8fbbe4b48e2ea581cda46a92814dc058c45996022d9642b6f0f0aa3",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Cube short-axis: double-inscribe with offset centres; outer box addresses east street while inner cube rotated 15 deg for diagonal light. GFA 4200, lower density rewards generous atrium void."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 3: 1/1 vertical (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "one1_v_split_join_v0",
  "book_composition_path_id": "book:path:df3abd0d2d79b8b9aae6ae7587c31f07764db60c5ffa0dbb7dd51e9dd9149c63",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube vertical: split body into east-west halves then rejoin with bridge slab; east slab aligns with road, west slab steps back behind north parapet. GFA 4800."
},
{
  "name": "one1_v_split_join_v1",
  "book_composition_path_id": "book:path:fd6f14a8c7a53518c7b27c266aa6fe285048a538d365903af989d31eb1bf1206",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Cube vertical: split+join with bridge at level 3; lower floors continuous, upper floors divided by light slot. GFA 5100, uses full storey count."
},
{
  "name": "one1_v_carve_v4",
  "book_composition_path_id": "book:path:e2c013fbdb205e7b1623ff23a989a428d59bb5918148150dbc035a3784cca3a0",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube vertical: carve through south-east corner creates a recessed entrance canopy; upper floors remain uninterrupted for maximum office floor-plates. GFA 4800."
},
{
  "name": "one1_v_carve_v5",
  "book_composition_path_id": "book:path:dcf4f6b2610028a1ea593f9c6ad7ad20003a019bd088460607413aab2ca09d73",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Cube vertical: deep carve penetrating the north-west quadrant to form a light-well satisfying solar access from both north and west despite BCR headroom. GFA 4500."
},
{
  "name": "one1_v_carve_offset_v5",
  "book_composition_path_id": "book:path:dbef513716f2ebb7fdfe247362b81f24c56f73525066c1c12e46dd47b9045388",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Cube vertical: carve and offset combines subtraction with lateral shift; produces interlocking east-west volumes with exposed inner face. GFA 4800."
},
{
  "name": "one1_v_inscribe_inscribe_v6",
  "book_composition_path_id": "book:path:42797808269753cfa4ebf6091b1ccb7b39eedec79d9acc26fa6f0848fb3fb9d9",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Cube vertical: two inscribed solids stepped vertically; lower inscribed block wider on south, upper inscribed block wider on north to track legal plan reduction. GFA 5400."
},
{
  "name": "one1_v_inscribe_inscribe_v7",
  "book_composition_path_id": "book:path:0d989999b6b424eda4bc2c165cd59bcbeb52513489ab1df9b33561a2610f67d1",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Cube vertical: inscribed double produces T-section; east wing hosts public lobby, north wing steps back as the setback profile narrows from grade to roof. GFA 4500."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 4: 1/16 long_axis (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "one16_la_split_join_v0",
  "book_composition_path_id": "book:path:ab47485303178ce1222ee54cdca9a674e42b8880bc85ab2d6e90dbbb0131e49e",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat long-axis: split horizontally then join at upper storeys; lower half public-access band, upper slab office floors cantilevered slightly. GFA 4800."
},
{
  "name": "one16_la_split_join_v1",
  "book_composition_path_id": "book:path:18e38e8edd976ffc42245323bde7b8c05e8833141428fa7844cce55e9e5fe117",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Thin-flat long-axis: split+join at v1 with wider gap slot; east face reads as two horizontal bands framing a recessed entry level. GFA 5100."
},
{
  "name": "one16_la_carve_v8",
  "book_composition_path_id": "book:path:64b5e542a8417d82eea76a9bb92f33bb390109f0b5381611d66f0764f7e6abbb",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Thin-flat long-axis: carve at east-centre creates a gated drive-through void at grade, leaving a thick horizontal soffit. GFA 4500 leaves BCR headroom for forecourt."
},
{
  "name": "one16_la_compress_v0",
  "book_composition_path_id": "book:path:7c609f3386fab13c568e56221dbef67977e69a5d07671f018e3321d328149292",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat long-axis: compress pinches the slab in the middle; creates a waist cross-section that widens at base and top while the plan reads as a rectangular envelope. GFA 4800."
},
{
  "name": "one16_la_carve_offset_v9",
  "book_composition_path_id": "book:path:21bc2cf38ed9554c62ef978265d15cd9d2cc1445d3cc0cdd974a62d40b7e17b6",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Thin-flat long-axis: carve+offset shifts the carved portion northward exposing an inclined reveal under the slab edge; north setback corridor is revealed as interstitial space. GFA 4200."
},
{
  "name": "one16_la_embed_branch_v7",
  "book_composition_path_id": "book:path:1dbae251ee21885ed2a6c456671dcde522b7bc2d04a7a2b1753ffe8cdaf3a1bc",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat long-axis: embed a vertical fin into the flat slab then branch it outward as a canopy arm; fin punctuates the horizontal profile. GFA 4800, combination principle."
},
{
  "name": "one16_la_intersect_intersect_v0",
  "book_composition_path_id": "book:path:3eda7a121da7524949ae91174c775e54d40acef39c6d145b02b27312de9257d8",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Thin-flat long-axis: two intersecting slabs; the diagonal solid is their boolean intersection, read as a wedge extruding toward east access. GFA 5400 captures upper FAR."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 5: 1/16 short_axis (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "one16_sa_split_join_v0",
  "book_composition_path_id": "book:path:a11848e543dc2337cb66f1526c0a3f872e503a07847bc00601a4a908baa40a9f",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat short-axis: slab split into north and south halves; bridge connector at top creates a U-section open to east road. GFA 4800."
},
{
  "name": "one16_sa_compress_v1",
  "book_composition_path_id": "book:path:5c43f4c7465ace001a1148203a69057b5ff39bf67cef6d25b5dba13017e6ff8f",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Thin-flat short-axis: compress along short axis bows the slab outward on east face; creates a lens plan minimising north boundary intrusion. GFA 4500."
},
{
  "name": "one16_sa_compress_v2",
  "book_composition_path_id": "book:path:c477dacb8129abf84c467761380b6f4723958357f15d96fdb6db242aba5ca75f",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Thin-flat short-axis: compress v2 variant; wider waist and narrower ends produce a barrel-vault plan profile which tracks the legal plan reduction per storey. GFA 5100."
},
{
  "name": "one16_sa_embed_branch_v7",
  "book_composition_path_id": "book:path:c390b2a83a83727bfd24e399ba3931136d75b092780cfc4db25d9774f9c94c48",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat short-axis: embedded spine branching east; branch acts as entrance canopy sheltering pedestrian approach from the road. GFA 4800, combination principle."
},
{
  "name": "one16_sa_embed_overlap_v0",
  "book_composition_path_id": "book:path:13afab49332f5e1bf56c67b422352c9940f940833a91cd995ec1cbcd060bcbc4",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Thin-flat short-axis: embed smaller slab inside main slab, overlap it toward north; produces layered horizontal profile seen in section as staggered plates. GFA 4200."
},
{
  "name": "one16_sa_intersect_intersect_v3",
  "book_composition_path_id": "book:path:a7bb544cf68da0b6c42e5fa560648b38e2cf4205f7f6927ba0549b984bd2582d",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat short-axis: two intersecting solids at oblique angle; intersection solid reads as a sharp diamond plan. GFA 4800, combination+aggregation."
},
{
  "name": "one16_sa_intersect_intersect_v4",
  "book_composition_path_id": "book:path:51be93a433e4d146e9a212613af29596c8cf83918f9a9e788ef9add762e76f59",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Thin-flat short-axis: v4 intersection at wider crossing angle; produces a more equilateral diamond with east apex pointing toward road. GFA 5400 uses full FAR allowance."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 6: 1/16 vertical (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "one16_v_split_join_v0",
  "book_composition_path_id": "book:path:9c161303b0a6f1c1b9fd119aabc7fa883d9396105964a2b9156ee901816905ad",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat vertical orientation: slab split top-bottom; bottom half public podium, top half office slab. Bridge reconnects north ends. GFA 4800."
},
{
  "name": "one16_v_split_join_v1",
  "book_composition_path_id": "book:path:37c441d0294e9b84f7984e8620efff91ddaf51153d9efb903c98e1d6807475ed",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Thin-flat vertical: v1 split+join with the bridge offset toward east face; office floors cantilevered beyond the podium by one bay. GFA 5100."
},
{
  "name": "one16_v_compress_v5",
  "book_composition_path_id": "book:path:a714a48a3e769be8af7c8ac7a6d8acf0ae62eefba5d2c9a1ccdbba0400276f0e",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Thin-flat vertical: compress along vertical axis bows the slab horizontally giving the section a barrel outline; plan remains compact within coverage. GFA 4500."
},
{
  "name": "one16_v_embed_branch_v6",
  "book_composition_path_id": "book:path:312c2d4bb55190e2eba8c277727992ea2f879f73cc37f676d544ee0b2968c42c",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat vertical: embed a horizontal element then branch it at mid-height; branched arm becomes a canopy over east entrance. GFA 4800, combination principle."
},
{
  "name": "one16_v_embed_overlap_v0",
  "book_composition_path_id": "book:path:e5f85d5584996ba2b88041bd1832424bfc838679722dee98120585cb85df89b5",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Thin-flat vertical: embed and overlap; inner volume slides upward and outward toward south; creates a split-level slab visible in section. GFA 4200."
},
{
  "name": "one16_v_intersect_intersect_v7",
  "book_composition_path_id": "book:path:b0e7bcd900559cccf181ff093ca7c80b9722a3d81e314d91319e13ae07d57918",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-flat vertical: two slabs crossed at 30 deg; intersection solid is a rhombic prism; east face is the acute end receiving direct road frontage light. GFA 4800."
},
{
  "name": "one16_v_embed_embed_v0",
  "book_composition_path_id": "book:path:5ce7e173e839406435edd94cc147c11a1eba208c3deb783c64a06cc25f5d9ef8",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Thin-flat vertical: two successive embeds produce a triple-skin section; skins visible on east and south elevations; GFA 5400 achieves maximum FAR for this flat typology."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 7: 1/2 long_axis (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "half_la_rotate_array_stack_v9",
  "book_composition_path_id": "book:path:ede197af18e9fed1800666b986634106304712540fa82e63ff4bbfe98aa295f5",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube long-axis: rotate+array+stack at v9 increment; each stacked floor rotated 10 deg; north corner recessed at each level creating the stepped envelope. GFA 4800."
},
{
  "name": "half_la_taper_array_v5",
  "book_composition_path_id": "book:path:00a64eeaaba888173bd0e20152d4ee4acbaec902327c33c4c8ca54c970513bd7",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Half-cube long-axis: taper+array; tapered bars arrayed stepping toward north setback; each repetition narrower in north dimension matching legal plan tables. GFA 5100."
},
{
  "name": "half_la_split_join_v0",
  "book_composition_path_id": "book:path:f9ec9ea34481b0a8b7dfe3d16136c1fe679689a86c739e9c7d87c1db48535707",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube long-axis: long bar split at mid-length, each half stepped to different heights then rejoined; east entry under the lower half, west half steps up two storeys. GFA 4800."
},
{
  "name": "half_la_embed_v0",
  "book_composition_path_id": "book:path:e46c958587f693626dbecc89989d3c7e5afedf24da1cdec3280059d4084bedab",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Half-cube long-axis: embed a shorter bar at 90 deg within the main bar; creates an L-section building with embedded spine that reads as a slot in the east elevation. GFA 4500."
},
{
  "name": "half_la_embed_overlap_v0",
  "book_composition_path_id": "book:path:1979381bcd2fd4aa4b2cee18451bdc220cc267392230f63e56a3cb561daf9abf",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube long-axis: embed then overlap the embedded volume toward east road; produces a projecting bay at levels 3-5 over a recessed lower podium. GFA 4800, case study."
},
{
  "name": "half_la_embed_embed_v0",
  "book_composition_path_id": "book:path:dea2102f6abd2b1db1f502aa1f3d9ee647e999251ccb4ed4e82745fb696bad6c",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Half-cube long-axis: double embed stacks two inserted volumes in series; creates a compound heterogeneous section bar; GFA 5400 uses all available FAR at this typology."
},
{
  "name": "half_la_compress_v9",
  "book_composition_path_id": "book:path:5913f0e2c58eec630015ded8e617c79e1afb6d04ad88bf02b342f013d1d1e2b3",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Half-cube long-axis: compress waists the bar vertically at mid-length; the waist creates a covered plaza beneath the upper mass. GFA 4200 because waist removes floor area."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 8: 1/2 short_axis (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "half_sa_rotate_array_stack_v9",
  "book_composition_path_id": "book:path:4c46ac778b206310c13d4c00bd1144d8c646c855a3b7cbc7ea1a567336745fc1",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube short-axis: rotated array stacked; compact plan with each floor rotated 8 deg; top floor most rotated, appears cantilevered over north setback strip. GFA 4800."
},
{
  "name": "half_sa_taper_array_v0",
  "book_composition_path_id": "book:path:eef0ad1af65f6a10c034b7aba30d0b74956bfb2c55b553cd2941f5d688dde6e5",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Half-cube short-axis: taper+array; bar tapered from east entry to west, arrayed in height; each level slightly smaller on the north end. GFA 5100."
},
{
  "name": "half_sa_split_join_v0",
  "book_composition_path_id": "book:path:e4c4d939d5a23538c2b046dde69d2431f49218c9fa72127366aa622e1317eb3b",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube short-axis: split east-west then join at level 5 slab; covered atrium between the two wings opened to south sky. GFA 4800."
},
{
  "name": "half_sa_embed_v2",
  "book_composition_path_id": "book:path:9ceb56b37c28be8dfe61314e2568bd2067dd0f94a0b9e10ce5891e223c4df304",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Half-cube short-axis: embed a shallow slab within the bar creating an occupied shelf at level 2; the shelf extends east to form a covered terrace at entry. GFA 4500."
},
{
  "name": "half_sa_carve_offset_v3",
  "book_composition_path_id": "book:path:3ff50595ebbea39bdd3a4841919b734cce67e6da3f75e1f1b1fb8522f32eadf1",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube short-axis: carve+offset creates a slot courtyard open toward east road; the offset portion becomes a secondary wing separated by the slot. GFA 4800."
},
{
  "name": "half_sa_embed_embed_v0",
  "book_composition_path_id": "book:path:3462a911efbac2ac018ec4146d026d31dd79096092c54012fb3e57cc5a27f6c9",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Half-cube short-axis: double embed produces an H-shaped section when viewed from north; east-facing entries on both flanking volumes. GFA 5400, combination principle."
},
{
  "name": "half_sa_embed_embed_v1",
  "book_composition_path_id": "book:path:b67729990b32e8828ab4df5636d3dcfc8ccb74e1fa6adcad32bb57b52cb9d973",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Half-cube short-axis: double embed v1 with offset insertion points; the two embedded volumes cross slightly producing a compound interlock. GFA 4200."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 9: 1/2 vertical (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "half_v_split_join_v0",
  "book_composition_path_id": "book:path:7acedec61890ab52c9a5bf814cfa3d854205a6596b3f8c0b692040a7a867ef4f",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube vertical: taller-than-wide volume split at mid-height; lower half wider footprint, upper half narrower; bridge slab reconnects at storey 3. GFA 4800."
},
{
  "name": "half_v_split_join_v1",
  "book_composition_path_id": "book:path:52fef3c7846a81bbad54d33f7da91066d0d2cdbee2b6711daf0f230372a61e89",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Half-cube vertical: split+join v1; upper volume shifted east; creates a stepping east facade that increases glazing toward road. GFA 5100."
},
{
  "name": "half_v_embed_v6",
  "book_composition_path_id": "book:path:608855d7f94aa40af3bee1fedc20bebfc87d20c70fdf7e6dc2e51a3052404dff",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Half-cube vertical: embed a horizontal fin at level 3; fin extends south as sun-shade and defines the programme threshold between lower public and upper office. GFA 4500."
},
{
  "name": "half_v_carve_offset_v7",
  "book_composition_path_id": "book:path:2b0459fd5564daed5910a6d626083bcb87afbdaff2ea10d2738a5582ba06198a",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube vertical: carve from south-east corner then offset it; exposed inner face reads as an inclined wall doubling as a wind screen at east entry. GFA 4800."
},
{
  "name": "half_v_embed_branch_v4",
  "book_composition_path_id": "book:path:d1d290e2a48b2cb2cc78de569a9cbcc28017ad1660a9618552f4b18b69599846",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Half-cube vertical: embed a narrow slab then branch it at level 2 as east entry canopy arm; programme distinction between trunk and branch. GFA 4800, combination principle."
},
{
  "name": "half_v_embed_embed_v0",
  "book_composition_path_id": "book:path:f5c66e2dcd5f773cc9a18ee553b9323018a595b7d5c5e95a5830b7f50593b717",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Half-cube vertical: double embed at staggered heights; seen in section as a triple thickness wall with two visible embedded voids. GFA 5400 maximises FAR."
},
{
  "name": "half_v_embed_embed_v1",
  "book_composition_path_id": "book:path:c287dfcbb563c6a2a6db23e318f9ecea549d347f33e4215f58cd3b7dd8e93523",
  "dimensional_intent": DI5d,
  "facing": ES,
  "rationale": "Half-cube vertical: double embed v1; north_side=south to orient the sunlight setback face on the south program side, appropriate when building is reversed. GFA 4200 lower density justified by deep embed voids."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 10: 1/4 long_axis (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "quarter_la_split_join_v0",
  "book_composition_path_id": "book:path:d9b61c8bea5df2677dc89f85e95f57c259843349273645a2a6e4a82f3954806c",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube long-axis: slender bar split at mid-span; south half at grade level linked to north half by bridge; creates a pedestrian passage through the building. GFA 4800."
},
{
  "name": "quarter_la_split_join_v1",
  "book_composition_path_id": "book:path:a9b38795629766ab5d77b1ad4531bd17e6fafe23b3989d6790e3a3c036a9060f",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Quarter-cube long-axis: split+join v1; south wing slightly taller, north wing steps back; bridge at top floor connects them over the passage. GFA 5100."
},
{
  "name": "quarter_la_expand_v0",
  "book_composition_path_id": "book:path:2438c10dab519c4f34ab4a73dfd9220260f24728764314829ec871fe509fd8f6",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube long-axis: boundary expand flares the bar at grade level; gives the public entrance a wide shoulder while the upper storeys remain slender. GFA 4800."
},
{
  "name": "quarter_la_expand_v1",
  "book_composition_path_id": "book:path:fcce492cf4e1b0d779ccac8462bbb84bb9d4b24b3b3a1bfde8ed12cad85c46b9",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Quarter-cube long-axis: expand v1; flare stronger on east side toward road; creates a splayed plan that funnels pedestrian flow from the wide base. GFA 4500."
},
{
  "name": "quarter_la_embed_branch_v7",
  "book_composition_path_id": "book:path:8d3aedd4fdbb3a7f6d1964ab1f5315247a3d1b2964bd456a2096c79ce90f7dfa",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube long-axis: embed a vertical element inside the bar then branch it outward; the branch creates an east-facing entry arcade. GFA 4800, combination."
},
{
  "name": "quarter_la_embed_overlap_v0",
  "book_composition_path_id": "book:path:c0bc6e82e134e727587e2377bc6e3245998c81f1638d907c65b314b4e102ff36",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Quarter-cube long-axis: embed+overlap; inner volume overlaps out toward east; produces a projecting east bay that traces the entrance datum. GFA 5400, case study."
},
{
  "name": "quarter_la_embed_embed_v1",
  "book_composition_path_id": "book:path:539f8b89f1670990be8d95a51401bdde262047bb03cdcdebb2c378ae4a5d7abf",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Quarter-cube long-axis: double embed; two inserted volumes create a compound heterogeneous cross section; lower GFA 4200 allows the voids to read as generous interstitial spaces."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 11: 1/4 short_axis (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "quarter_sa_rotate_array_stack_v8",
  "book_composition_path_id": "book:path:de37fd9b0af79255387baff99879effc957882f2402dc3b42e6d29b7ea93a245",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube short-axis: compact block rotated per storey; plan appears to twist; north face pulled inward at top by setback; GFA 4800."
},
{
  "name": "quarter_sa_expand_v3",
  "book_composition_path_id": "book:path:36168087153f7d5b092fb04ab7a81b63d8c38d44a2f84716c9e17d62385d5148",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Quarter-cube short-axis: expand at base creates a wide podium shoulder; the slender bar rises above the expanded plinth. GFA 5100 fills mid-band FAR."
},
{
  "name": "quarter_sa_embed_branch_v7",
  "book_composition_path_id": "book:path:32dc59b7b0604bda065a92bd57e5b99cccf0017dd3eb60642d2395c8c9209c8f",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube short-axis: embed+branch; branched arm perpendicular to main bar projects east toward road as an elevated walkway. GFA 4800, combination."
},
{
  "name": "quarter_sa_embed_overlap_v0",
  "book_composition_path_id": "book:path:f9c06ddf25399f7007121ffa336d7949e3d19b77efac5be8d4d4797327216a11",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Quarter-cube short-axis: embed+overlap; overlapping volume extends north; in plan it reads as a T with the tail pointing toward the setback boundary. GFA 4500."
},
{
  "name": "quarter_sa_embed_embed_v5",
  "book_composition_path_id": "book:path:be0bf454a669423ca4f276b414b1b3a1f940a34b17b6cdf39835aba422e1f75a",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube short-axis: double embed v5; outer and inner solids share a seam on the south face; seen in section as two nested rooms within the bar. GFA 4800."
},
{
  "name": "quarter_sa_embed_embed_v6",
  "book_composition_path_id": "book:path:93ffb44db21964de02e250549ce1802a98c6fb0995a11b6d956f27aa8977fdbd",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Quarter-cube short-axis: double embed v6; alternate embedding angles create an X pattern in section. GFA 5400 near FAR cap for this typology."
},
{
  "name": "quarter_sa_split_join_v0",
  "book_composition_path_id": "book:path:6b8c3aa53e5224647eff9cc60ee8f9a050e9ce9942105b768488c05170a26d9a",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Quarter-cube short-axis: split+join v0; the two halves spread slightly and rejoin at level 5; the gap becomes a vertical slot on east facade. GFA 4200, gap reduces usable floor."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 12: 1/4 vertical (7)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "quarter_v_split_join_v0",
  "book_composition_path_id": "book:path:5eb3dcb66dae36c47adcefecc20736a797ec89ec05cbdb04cbed28e6b8fb6d95",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube vertical: tall prism split at level 2; lower foot wider than upper tower; bridge reconnects at parapet. GFA 4800 mid-range."
},
{
  "name": "quarter_v_split_join_v1",
  "book_composition_path_id": "book:path:d2524d54ac1e56b4c5bea1183b9c6bc55a7505997858aaf76c778e0f969601eb",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Quarter-cube vertical: split+join v1; tall prism split into east and west columns; linked at top by a roof slab creating an arch silhouette. GFA 5100."
},
{
  "name": "quarter_v_expand_v7",
  "book_composition_path_id": "book:path:4cf44ef80cac744d87cad4fe7948d46aede5d1e89192f2bc9a793386220c7a7f",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube vertical: expand v7; base flares outward on all sides for a stable ground-level presence; the upper prism is the legal-plan controlled tower. GFA 4800."
},
{
  "name": "quarter_v_extract_v0",
  "book_composition_path_id": "book:path:39bb49e7311eed08eec69eec8a47ce91c41c32b3c3b72338a6f4e7b78bc34646",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Quarter-cube vertical: extract pulls a sub-volume from the main prism outward; the extracted piece creates a projecting east bay at levels 3-5. GFA 4500."
},
{
  "name": "quarter_v_embed_branch_v8",
  "book_composition_path_id": "book:path:bf5c657b446b9ba38a63ae11ce2548b24efd843cae1cc2210f730b894c97a274",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Quarter-cube vertical: embed+branch v8; branch at level 3 extends east as a bridging arm over the public entry plaza. GFA 4800, combination."
},
{
  "name": "quarter_v_embed_overlap_v0",
  "book_composition_path_id": "book:path:07d70191938ae81e266a17572dc057ccf1cb6beab84995e0c766fdbbf1baa43d",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Quarter-cube vertical: embed+overlap; inner solid overlaps upward and north creating a split cross-section visible in elevation as a stepped silhouette. GFA 5400."
},
{
  "name": "quarter_v_taper_taper_v0",
  "book_composition_path_id": "book:path:dc60e0828bdb7466c7c34cbf845b47dcb903f6e3b651f847c49d1c93af3bfe3f",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Quarter-cube vertical: double-taper; first taper narrows the prism from bottom, second from top; produces a spindle shape whose waist is at level 3. GFA 4200, waist reduces mid-storey floor area."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 13: 1/8 long_axis (6)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "eighth_la_rotate_array_stack_v10",
  "book_composition_path_id": "book:path:5daaf72b3cd1030e145d13e2e831127172956dfb1fcb1e6e7aa72bd299de05ad",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-tower long-axis: rotate+array+stack v10; very slender floors each rotated 5 deg creating a twisted tower form; east entry at base unaffected by rotation. GFA 4800."
},
{
  "name": "eighth_la_taper_array_v1",
  "book_composition_path_id": "book:path:4ee9721e409a384b65c27352a63c59c431bb084087434887aa8e8cf49065c0c6",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Thin-tower long-axis: taper+array; repeated tapered slivers stacked in height; profile narrows on north side tracking the legal plan reduction. GFA 5100."
},
{
  "name": "eighth_la_split_join_v0",
  "book_composition_path_id": "book:path:9a4827b4a4930d9f324a08c3fa43152326df92b92ef1d7d650751856412eb11d",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-tower long-axis: split+join; slim bar divided into two legs, rejoined at top; creates a gateway form over east entry path. GFA 4800."
},
{
  "name": "eighth_la_bend_v0",
  "book_composition_path_id": "book:path:32790f299951f25a73b968418745d084e6a630d9b93b0e2e6ec05e2faa34b82a",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Thin-tower long-axis: bend curves the slim bar in plan; east leg faces road, west leg curves away; the bent plan naturally avoids the north setback zone. GFA 4500."
},
{
  "name": "eighth_la_inscribe_inscribe_v2",
  "book_composition_path_id": "book:path:79b7551bb0a936faa3e7f7cb212408b2d2990e1f1141938a9d6173709fc976a5",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-tower long-axis: double inscribe; outer cylinder encases a smaller inner prism; seen in plan as circle with square core. GFA 4800, combination principle."
},
{
  "name": "eighth_la_carve_offset_v1",
  "book_composition_path_id": "book:path:eea5366be26e96804d93c5461522e25be7ca5a59dde921066f8b43801e5db3e0",
  "dimensional_intent": DI5d,
  "facing": E,
  "rationale": "Thin-tower long-axis: carve+offset on a slim bar creates a recessed notch in the north face; the offset piece emerges as a lower element on north. GFA 4200."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 14: 1/8 short_axis (6)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "eighth_sa_taper_array_v8",
  "book_composition_path_id": "book:path:1b9ebb311f1d5a6f5dea53fd0c7a99344905e0a14ad4b5cba91a2f78e29faf12",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-tower short-axis: taper+array; each tier in the array is tapered toward the east face; successive tiers align to form a raked east facade. GFA 4800."
},
{
  "name": "eighth_sa_split_join_v0",
  "book_composition_path_id": "book:path:79664d96d36a7ea43678f991f90e38598c8344976c74a6306e129c1ec69ca4ff",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Thin-tower short-axis: split+join; compact block split into north and south slabs, joined at roof creating a gateway. GFA 5100."
},
{
  "name": "eighth_sa_bend_v4",
  "book_composition_path_id": "book:path:8adb68b80a91f94fc17de857f0cb8508d2e64b8756eb52e3377f0e4a6cd60954",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-tower short-axis: bend curves the slim short-axis bar to the south-west; east end of the curve aligns to road; the curve avoids north setback. GFA 4800."
},
{
  "name": "eighth_sa_inscribe_inscribe_v6",
  "book_composition_path_id": "book:path:955794b8a38b30637e11bc5de1811a0fe721f28fe8074774e789f04071918d5d",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Thin-tower short-axis: double inscribe; an octagonal prism inscribed in the outer box and a circular core inside the octagon; layered geometry in plan. GFA 4500."
},
{
  "name": "eighth_sa_carve_offset_v5",
  "book_composition_path_id": "book:path:226fb0399d5815832612c6e647bda82401d2d0d29569a8e37a998ea751c51b7d",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Thin-tower short-axis: carve from south-east corner + offset southward; the carved volume reappears as a low plinth element. GFA 4800."
},
{
  "name": "eighth_sa_inscribe_inscribe_v7",
  "book_composition_path_id": "book:path:511f49198805063850cdfb62a07509b1e0115b005c0120c1b0f2b2f69e352cdc",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Thin-tower short-axis: double inscribe v7; alternating rotation of the inscribed solids gives the tower a staggered profile. GFA 5400, combination near FAR cap."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 15: 1/8 vertical (6)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "eighth_v_split_join_v0",
  "book_composition_path_id": "book:path:a2327b6aef7750332f98bcdd355e6b6122c5420f1b42ee148dfa65cd351875f4",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Tower vertical: split top-bottom at storey 3; lower podium wider than upper tower; bridge at parapet links them; north setback applies to upper only. GFA 4800."
},
{
  "name": "eighth_v_split_join_v1",
  "book_composition_path_id": "book:path:2cd0e6c3a9e93c1e784c8153d48ed4299c99d0ad22088a100712e775468e3919",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "Tower vertical: split+join v1; narrow tower with a wider foot slab; roof bridge creates a crown silhouette. GFA 5100."
},
{
  "name": "eighth_v_bend_v8",
  "book_composition_path_id": "book:path:5b1246347852f2232f1ceb2d5c223263ab6e64828dee0d89728d4f92db44e5f6",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Tower vertical: bend curves the slim tower in elevation; base anchored at east road, peak leans slightly south away from the north setback. GFA 4800."
},
{
  "name": "eighth_v_branch_v3",
  "book_composition_path_id": "book:path:1717d404c28b8c7fc4eb07ca640c9749a1bcd30a998535b797359c6a6ffb9f64",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "Tower vertical: branch arm at mid-tower height reaches east over the entry plaza; branch is shorter than trunk; creates a sheltered street-level space. GFA 4500."
},
{
  "name": "eighth_v_embed_branch_v4",
  "book_composition_path_id": "book:path:67260165ea58020ed92b8bd6bd6b95846ec9d2e6d0caab713c275b6c215bc2c4",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "Tower vertical: embed a horizontal deck at level 3 then branch it east; deck+branch form a sky-bridge datum. GFA 4800, combination principle."
},
{
  "name": "eighth_v_intersect_intersect_v0",
  "book_composition_path_id": "book:path:7a3189098fa9cf5f9ca246e521c79e417a74b75b8a2b0a81c9af92abda0c5805",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "Tower vertical: two slender towers crossing at 45 deg; the intersection solid forms the occupied building mass; east access through the wider end. GFA 5400, combination."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 16: 3/8 long_axis (6)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "three8_la_rotate_array_stack_v9",
  "book_composition_path_id": "book:path:09182926fcbe628962f9c95795c3bc25ac39b487847b82ab5b77d88f7e027eec",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume long-axis: L-plan floor rotated and stacked; the concave corner of the L rotates progressively inward reducing north footprint. GFA 4800."
},
{
  "name": "three8_la_taper_array_v1",
  "book_composition_path_id": "book:path:b1bbe69597a29aa47f8f65c81f71261f0147ed392d1fd3eae4274d800be097fc",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "L-volume long-axis: taper+array v1; L-plan tapered on the short leg; array in plan creates a pinwheel of tapered L-shapes. GFA 5100."
},
{
  "name": "three8_la_branch_v5",
  "book_composition_path_id": "book:path:2cf9617102901082c9b234ba251ffb8dc5d1b693bb66a3da38907b6eb106ff2e",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume long-axis: branch from the corner of the L; arm extends east to close the courtyard; creates an enclosed three-sided court open only to south. GFA 4800."
},
{
  "name": "three8_la_embed_branch_v5",
  "book_composition_path_id": "book:path:e4ce79c5e3365bb0d475861b56772e92226a8b2af57382fbcbdfd6fb87597972",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "L-volume long-axis: embed a spine in the L-corner then branch it eastward; the combined figure closes the concave corner. GFA 4500, combination."
},
{
  "name": "three8_la_intersect_intersect_v3",
  "book_composition_path_id": "book:path:786a8a9e13dc1b0994b942bc883fe002f2f25d64475fd5a6af95786bfd9c2ae7",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume long-axis: two L-volumes intersected; the intersection solid is the occupied building mass; reveals a complex figure-eight plan. GFA 4800."
},
{
  "name": "three8_la_intersect_intersect_v4",
  "book_composition_path_id": "book:path:30d71f0ca82f4bc049caa35ac1961a208943ed7ab0851596d6b7e0ff343ceda2",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "L-volume long-axis: v4 intersection at wider rotation; intersection occupies a generous central area with L-shaped notches at corners. GFA 5400."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 17: 3/8 short_axis (6)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "three8_sa_rotate_array_stack_v7",
  "book_composition_path_id": "book:path:a47a962ff956ecb36a57853cdd9419aebf58eb54b48982f064a0bf0f30e55839",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume short-axis: rotate+array+stack v7; the L rotates so that successive floors shift the void corner; creates a helical concave-corner profile. GFA 4800."
},
{
  "name": "three8_sa_taper_array_v2",
  "book_composition_path_id": "book:path:8b334a3c735f42aa9cee85d2c8dcae049a9fc0c5267c269355f03869693bb4ae",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "L-volume short-axis: taper+array on short-axis L; outer leg tapers toward north reducing massing near the setback. GFA 5100."
},
{
  "name": "three8_sa_branch_v5",
  "book_composition_path_id": "book:path:ace93d399c2b0b7898d49e0f95d9617513fbde925227ea3871df810b0758d138",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume short-axis: branch closes the L on the east side; the branch creates a covered public atrium within the L void. GFA 4800."
},
{
  "name": "three8_sa_embed_branch_v6",
  "book_composition_path_id": "book:path:2713967d70c807ea0232f1a8024f96d460272332526fc4316ffa933845de332c",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "L-volume short-axis: embed+branch v6; embedded slab in L-corner branches east to close the void court on one side. GFA 4500, combination."
},
{
  "name": "three8_sa_embed_overlap_v0",
  "book_composition_path_id": "book:path:703683a11f3e0fa625edc895b7c7afafebe7e106d84b20c49e832963b234b688",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume short-axis: embed+overlap; embedded volume overlaps across the L-corner; produces a compact mass with one deep re-entrant face. GFA 4800, case study."
},
{
  "name": "three8_sa_embed_embed_v0",
  "book_composition_path_id": "book:path:9635a063a8424e258fe347f941974a684a1b06fad1b438c66a4c681573cdafa9",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "L-volume short-axis: double embed; two inserts into the L body create a compound hollow-core section. GFA 5400, combination at FAR upper limit."
},

# ──────────────────────────────────────────────────────────────────────────────
# GROUP 18: 3/8 vertical (6)
# ──────────────────────────────────────────────────────────────────────────────
{
  "name": "three8_v_taper_array_v0",
  "book_composition_path_id": "book:path:7d1e6db393b1adfc4f584b64f87e0019bfb63bfbc1b264e95789502a1bd2db34",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume vertical: taper+array v0; L section tapered in elevation; each stacked floor slightly smaller in north dimension producing setback compliance. GFA 4800."
},
{
  "name": "three8_v_taper_array_v1",
  "book_composition_path_id": "book:path:5675f3d163d1f41d2c675a49691ad65b471444dcac4e9cd308ce5de55ea2fef5",
  "dimensional_intent": DI5b,
  "facing": E,
  "rationale": "L-volume vertical: taper+array v1; narrowing L-plan with height; the two legs of the L step back independently giving a varied profile. GFA 5100."
},
{
  "name": "three8_v_branch_v9",
  "book_composition_path_id": "book:path:d509f1b5b39191c510977c28b416491b80655aa852005a0e1b076e719797cbec",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume vertical: branch at the upper elbow of the L reaches east toward road; arm is shorter than the trunk legs. GFA 4800."
},
{
  "name": "three8_v_carve_v0",
  "book_composition_path_id": "book:path:a3c6628aa86e6962b40c7261c2e7a8dca6c03b248f6b27bd92ebfdffd0318b3b",
  "dimensional_intent": DI5c,
  "facing": E,
  "rationale": "L-volume vertical: carve removes the inner corner of the L at grade; creates a chamfered entrance corner open toward east and south. GFA 4500."
},
{
  "name": "three8_v_embed_overlap_v0",
  "book_composition_path_id": "book:path:d114a1d1f04b3d19c6b7e369269f21fdb174d6236e681ca4ed2e30810087d842",
  "dimensional_intent": DI5,
  "facing": E,
  "rationale": "L-volume vertical: embed+overlap; embedded piece slides outward in the vertical direction turning the L into a Z-section in elevation. GFA 4800, case study."
},
{
  "name": "three8_v_embed_embed_v0",
  "book_composition_path_id": "book:path:fd1f02d0d44ec0d582556a2d9b6e4351e2996ede295cdecdb0fc665ac5f380b3",
  "dimensional_intent": DI5e,
  "facing": E,
  "rationale": "L-volume vertical: double embed; two inserts within the L vertical mass create compound voids; the voids act as sky-lit atriums in the taller legs. GFA 5400, combination."
},

]

# ── VALIDATION ────────────────────────────────────────────────────────────────
assert len(sentences) == 120, f"Expected 120 sentences, got {len(sentences)}"

# Check all path_ids are unique
pids = [s["book_composition_path_id"] for s in sentences]
assert len(pids) == len(set(pids)), "Duplicate path_ids found!"

# Check all names are unique
names = [s["name"] for s in sentences]
assert len(names) == len(set(names)), "Duplicate names found!"

payload = {"sentences": sentences}

# ── SCHEMA VALIDATION ─────────────────────────────────────────────────────────
import os
schema_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp26\book-author\schema.json"
with open(schema_path, encoding="utf-8") as f:
    schema = json.load(f)

try:
    from jsonschema import Draft7Validator
    v = Draft7Validator(schema)
    errors = list(v.iter_errors(payload))
    if errors:
        print(f"SCHEMA ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {list(e.absolute_path)}: {e.message[:120]}")
        sys.exit(1)
    else:
        print(f"SCHEMA OK: 0 errors, {len(sentences)} sentences")
except ImportError:
    print("jsonschema not available – skipping schema check")

# ── WRITE OUTPUT ──────────────────────────────────────────────────────────────
out_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp26.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Written: {out_path}")
print(f"Sentences: {len(sentences)}")
