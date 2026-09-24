import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Plan: 18 groups (6 base volumes x 3 orientations)
# 12 groups of 7 + 6 groups of 6 = 84+36 = 120
# Groups of 7: 1/1-LA, 1/1-SA, 1/1-V, 1/16-LA, 1/16-SA, 1/16-V, 1/2-LA, 1/2-SA, 1/2-V, 1/4-LA, 1/4-SA, 1/4-V
# Groups of 6: 1/8-LA, 1/8-SA, 1/8-V, 3/8-LA, 3/8-SA, 3/8-V
# Total = 12*7 + 6*6 = 84+36 = 120

DI = lambda s, g, t: {
    "schema_version": "arr.maas.dimensional_intent.v1",
    "storey_count": s,
    "storey_height_m": 3.8,
    "target_gfa_m2": float(t),
    "delivery_policy": "preserve_physical_dimensions",
    "programme_status": "unknown"
}
FA = {"access_side": "east", "north_side": "north"}
FB = {"access_side": "east", "north_side": "south"}
FC = {"access_side": "south", "north_side": "west"}

def s(name, pid, di, facing, rationale):
    return {"name": name, "book_composition_path_id": pid, "dimensional_intent": di, "facing": facing, "rationale": rationale}

sentences = []

# ─── 1/1 long_axis (7) ────────────────────────────────────────────────────────
sentences += [
    s("one_la_split_join_a", "book:path:e2ff3489e22b64fd51fd7dac8d3c9059e28193dcda7843c8a22a7e1202684824",
      DI(5,3.8,4800), FA,
      "1/1 cube long-axis: split the bar east–west and rejoin with a bridged shift; east half aligns the road front, north half steps back under the sunlight plane. Programme: main lobby east, support offices west."),
    s("one_la_split_join_b", "book:path:29b1dcd954546fe1c627bc7260389b8efdeca2840cf35f8ae8553db108ed6b3b",
      DI(5,3.8,4600), FA,
      "1/1 long-axis split+join variation: two volumes offset vertically so the taller east wing receives road address and the recessed west wing tucks under the north setback. Stepped section responds to daylight constraint."),
    s("one_la_branch_a", "book:path:8f96b3645f40504b6781baef559e41354489914527b6c0b20a710409786426d8",
      DI(5,3.8,4500), FA,
      "1/1 long-axis branch: trunk runs north–south along the west side; east arm projects toward the road and provides covered entry. L-plan keeps north side lower."),
    s("one_la_embed_branch", "book:path:6698000c0156563eb9b6f487b2e5537c8162cc298066a4b1b8ec6fe5e6d0fb3d",
      DI(5,3.8,5100), FA,
      "1/1 long-axis embed+branch case: courtyard volume embedded at centre then a branch cantilevered east over the entry court. Public office programme uses court as light well; branch contains meeting floors."),
    s("one_la_embed_overlap_a", "book:path:2d0808fd6e0f5230daf4726922feeb332b45364e746f4f95208d7cd66e15746b",
      DI(5,3.8,5000), FA,
      "1/1 long-axis embed+overlap: inner void overlaps the outer skin on the north face to cut a recessed loggia; road-facing east elevation stays full-height. GFA targets upper FAR band."),
    s("one_la_embed_embed_a", "book:path:ac8ebf7584b7f749acb10295f79d05acdf0bb46ba0411a044c3e772a968bada1",
      DI(5,3.8,4700), FA,
      "1/1 long-axis embed+embed: two nested voids subtract a cross-shaped atrium at mid-plan; perimeter offices ring the void on all five floors. East entry void is wider to signal public address."),
    s("one_la_bend_bend", "book:path:59a4c65f9eb733b1fd91665019eb7618246210703a6ab56242135b39efb0c257",
      DI(5,3.8,4400), FA,
      "1/1 long-axis bend+bend: double curvature bends the bar first in plan (curving south flank toward entry plaza) then in section (upper floors tip north to reduce sunlight shadow). Continuous deformation, no discrete setback."),
]

# ─── 1/1 short_axis (7) ───────────────────────────────────────────────────────
sentences += [
    s("one_sa_rotate_array_stack_a", "book:path:99438cc48216d25d3f776e5057e9e3ba0529751902e037024044c0d7d620651c",
      DI(5,3.8,4600), FA,
      "1/1 short-axis rotate+array+stack: floor plates rotate slightly at each level and stack to produce a spiralling prismatic tower; compact footprint keeps coverage well below 60%."),
    s("one_sa_rotate_array_stack_b", "book:path:6914467c9db8568094a64e2c1fbe1ed4e8235f04866aae8d058c60eee6cbf3d1",
      DI(5,3.8,4400), FA,
      "1/1 short-axis rotate+array+stack variant: wider inter-floor rotation angle creates more pronounced helix, shading the south face with successive overhangs."),
    s("one_sa_taper_array", "book:path:e7e899b351175422a6a564e1b36c8627cfa375f20299201717cb9b8d5a04c2fb",
      DI(5,3.8,4300), FA,
      "1/1 short-axis taper+array: tapered section narrows toward the top; arrayed along short axis to create a colonnaded base layer. Ground floor open to public circulation."),
    s("one_sa_carve_a", "book:path:e1085d42ea1641d73c5c3cf048ba765291bc487e8611b8b84a5f8b4457022dd3",
      DI(5,3.8,4800), FA,
      "1/1 short-axis carve: large arched carve on the east face creates a covered arrival space; volume above carve spans full width for continuous office floor plates."),
    s("one_sa_carve_offset_a", "book:path:2522b24a37a2d3ce1c65f00c39b5747b834bda0e133a3bb113d7c378bfa6430d",
      DI(5,3.8,4900), FA,
      "1/1 short-axis carve+offset: lower body carved at north-east corner for sunlight; upper body offset southward to keep full floor plate on upper storeys. Two-part silhouette reads as stacked solids."),
    s("one_sa_inscribe_inscribe_a", "book:path:588856471ed4311f9449daa8d7c6e2e53de5b1053cd7e3ae1fc4b9fc860f078b",
      DI(5,3.8,4200), FA,
      "1/1 short-axis inscribe+inscribe: outer shell inscribes an inner volume rotated 15 degrees; gap between rings expressed as a continuous glazed slot on all four facades. Office floor plates within the inner prism."),
    s("one_sa_inscribe_inscribe_b", "book:path:bd6b6e393630c79a3426969e7e0c8ab39b34f675da4c4b70fefb2775cb868848",
      DI(5,3.8,4100), FA,
      "1/1 short-axis inscribe+inscribe second variation: inner volume is an ellipse inscribed in the rectangular outer; gap widens on north and south to create planted buffer zones."),
]

# ─── 1/1 vertical (7) ─────────────────────────────────────────────────────────
sentences += [
    s("one_v_split_join_a", "book:path:df3abd0d2d79b8b9aae6ae7587c31f07764db60c5ffa0dbb7dd51e9dd9149c63",
      DI(5,3.8,5200), FA,
      "1/1 vertical split+join: tower split horizontally at mid-height and rejoined with a horizontal bridge slab; lower podium faces east entry, upper tower rotated 10 degrees for views. Public hall on bridge level."),
    s("one_v_split_join_b", "book:path:fd6f14a8c7a53518c7b27c266aa6fe285048a538d365903af989d31eb1bf1206",
      DI(5,3.8,5000), FA,
      "1/1 vertical split+join variant: split at 3/5 height; lower volume thicker footprint, upper tapered. Sunlight setback absorbed by tapering upper body toward north."),
    s("one_v_carve_a", "book:path:22098fdac9c87c4564a3dce72c38897c6a1d1497ef8573fd1eac17ee38f21533",
      DI(5,3.8,4600), FA,
      "1/1 vertical carve: cylindrical void carved vertically through the full tower height creates an interior atrium; upper glazed roof admits zenithal light. Carve centred near north, maintaining solid south face."),
    s("one_v_carve_offset_a", "book:path:b76e1485e254651300a4127d6dda0b66edf012ae6b89342830a5d8cd1e9ed959",
      DI(5,3.8,4800), FA,
      "1/1 vertical carve+offset: vertical carve on the north face then the body offset westward at mid-height to comply with the sunlight setback while preserving FAR near capacity ceiling."),
    s("one_v_carve_offset_b", "book:path:dbef513716f2ebb7fdfe247362b81f24c56f73525066c1c12e46dd47b9045388",
      DI(5,3.8,5100), FA,
      "1/1 vertical carve+offset second variation: twin carves — one east entry notch, one north light channel — with the whole upper body offset toward the road to maximise floor plate efficiency."),
    s("one_v_inscribe_inscribe_a", "book:path:564cd63f992f9d3c424e68b044601dd2490e2aed54515c09bb52edad64e11ea6",
      DI(5,3.8,4700), FA,
      "1/1 vertical inscribe+inscribe: outer rectilinear prism inscribes an inner cylinder; annular gap used as circulatory ring on each floor. Vertical orientation emphasises tower reading with minimum footprint."),
    s("one_v_inscribe_inscribe_b", "book:path:42797808269753cfa4ebf6091b1ccb7b39eedec79d9acc26fa6f0848fb3fb9d9",
      DI(5,3.8,4500), FA,
      "1/1 vertical inscribe+inscribe variant: inner volume scaled differently per floor, creating progressive inscribed depths — taller at base, narrower at top — for a sculptural profile."),
]

# ─── 1/16 long_axis (7) ───────────────────────────────────────────────────────
sentences += [
    s("one16_la_split_join_a", "book:path:ab47485303178ce1222ee54cdca9a674e42b8880bc85ab2d6e90dbbb0131e49e",
      DI(5,3.8,4200), FA,
      "1/16 slab long-axis split+join: thin bar split at east–west centre and rejoined offset north; creates a dogleg plan that addresses the road with its full narrow face. Slab occupies maximum east-west run."),
    s("one16_la_split_join_b", "book:path:18e38e8edd976ffc42245323bde7b8c05e8833141428fa7844cce55e9e5fe117",
      DI(5,3.8,4400), FA,
      "1/16 slab long-axis split+join variation: the offset brings the north half forward, screening a service yard to the south. Both halves share the same five-storey height."),
    s("one16_la_carve_a", "book:path:a3405613dbe20ce685401e866f8aeed07bbd1d450f9a9e7279dc0e5c1c3d6201",
      DI(5,3.8,4000), FA,
      "1/16 slab long-axis carve: east face of the slab carved to recess the entry lobby; volume reads as a horizontal bar with a punched portal at ground level. Low BCR, high linear span."),
    s("one16_la_compress", "book:path:7c609f3386fab13c568e56221dbef67977e69a5d07671f018e3321d328149292",
      DI(5,3.8,3900), FA,
      "1/16 slab long-axis compress: thinnest possible floor plate compressed further along the depth axis to create a knife-edge building. Lower GFA justified by maximising north daylighting through minimum obstruction depth."),
    s("one16_la_carve_offset_a", "book:path:2e59a8f2aacc39815b8f0bd7b34f6b1445d3f7da35dc0acfd01dd835275306e0",
      DI(5,3.8,4100), FA,
      "1/16 slab long-axis carve+offset: east end carved and the slab body offset upward at mid-point to form a raised west segment that captures morning light on its underside."),
    s("one16_la_embed_branch", "book:path:1dbae251ee21885ed2a6c456671dcde522b7bc2d04a7a2b1753ffe8cdaf3a1bc",
      DI(5,3.8,4600), FA,
      "1/16 slab long-axis embed+branch: branch arm perpendicular to the main slab, creating an L or T condition; embedded void at junction acts as an open light court bridging programme zones."),
    s("one16_la_intersect_intersect_a", "book:path:3eda7a121da7524949ae91174c775e54d40acef39c6d145b02b27312de9257d8",
      DI(5,3.8,4800), FA,
      "1/16 slab long-axis intersect+intersect: two slabs cross at angles; intersection volume is the usable office core while the projecting arms house open-plan floors. Aggregation reads as a cruciform."),
]

# ─── 1/16 short_axis (7) ──────────────────────────────────────────────────────
sentences += [
    s("one16_sa_split_join_a", "book:path:a11848e543dc2337cb66f1526c0a3f872e503a07847bc00601a4a908baa40a9f",
      DI(5,3.8,4000), FA,
      "1/16 slab short-axis split+join: slab split transversally and one half lowered to create a cascade; east high half at five storeys holds the road presence, west lower half is three storeys."),
    s("one16_sa_split_join_b", "book:path:b1b02f12be187933f4c0c294ee484bff1d5eeded4f97f504154d0b09c39c4076",
      DI(5,3.8,3900), FA,
      "1/16 slab short-axis split+join variation: the two halves are the same height but laterally displaced to create a staggered plan; covered walk links them at ground level."),
    s("one16_sa_compress_a", "book:path:dfaf29dcf45ffca827c75bc859a89a8f32bcbfcd729fc47953bcf18f4154f183",
      DI(5,3.8,4200), FA,
      "1/16 slab short-axis compress: slab compressed along the short axis to near-minimum depth; result is a very flat bar whose east face becomes an almost-curtain-wall public facade."),
    s("one16_sa_compress_b", "book:path:5c43f4c7465ace001a1148203a69057b5ff39bf67cef6d25b5dba13017e6ff8f",
      DI(5,3.8,4300), FA,
      "1/16 slab short-axis compress variant: compressed bar lifted off ground on piloti; ground floor is semi-public open space. Five storeys of office above the piloti band."),
    s("one16_sa_embed_branch", "book:path:c390b2a83a83727bfd24e399ba3931136d75b092780cfc4db25d9774f9c94c48",
      DI(5,3.8,4700), FA,
      "1/16 slab short-axis embed+branch: branch projects perpendicular to the slab's short face (eastward toward road); creates a T-plan with branch as lobby tower and slab as office wing."),
    s("one16_sa_embed_overlap_a", "book:path:13afab49332f5e1bf56c67b422352c9940f940833a91cd995ec1cbcd060bcbc4",
      DI(5,3.8,4500), FA,
      "1/16 slab short-axis embed+overlap: inner office slab overlaps a secondary volume on the south end, forming a thickened anchor. East face of the main slab remains the slim public face."),
    s("one16_sa_intersect_intersect_a", "book:path:75320deff0c451e8f3da8b20bb8211fcfc6ea0b6a7b717699a4009cffd9b58e7",
      DI(5,3.8,4600), FA,
      "1/16 slab short-axis intersect+intersect: two thin slabs intersect at 90 degrees to yield a plus-plan; intersection is structural core and vertical circulation. Each arm addresses a different site orientation."),
]

# ─── 1/16 vertical (7) ────────────────────────────────────────────────────────
sentences += [
    s("one16_v_split_join_a", "book:path:9c161303b0a6f1c1b9fd119aabc7fa883d9396105964a2b9156ee901816905ad",
      DI(5,3.8,4000), FA,
      "1/16 slab vertical orientation split+join: the vertically oriented slab is split horizontally and rejoined with a gap; gap floor acts as an accessible sky garden between office zones."),
    s("one16_v_split_join_b", "book:path:37c441d0294e9b84f7984e8620efff91ddaf51153d9efb903c98e1d6807475ed",
      DI(5,3.8,3900), FA,
      "1/16 slab vertical split+join variant: split at 40% height; lower volume is wider footprint for public programme, upper volume thin slab continues to full height."),
    s("one16_v_compress_a", "book:path:942c521026c6d81265a78807917de6e1b871f931b3b2f6abc474330e8c071225",
      DI(5,3.8,4200), FA,
      "1/16 slab vertical compress: vertically oriented slab compressed radially to approach an elliptic cross section; thin oval prism reduces wind load and maximises perimeter glazing for all offices."),
    s("one16_v_compress_b", "book:path:a714a48a3e769be8af7c8ac7a6d8acf0ae62eefba5d2c9a1ccdbba0400276f0e",
      DI(5,3.8,4400), FA,
      "1/16 slab vertical compress variant: compressed to a wider oval and then tilted slightly off vertical — a leaning slab tower that shifts its mass northward at the top to shed sunlight from the south plaza."),
    s("one16_v_embed_branch_a", "book:path:eaa432331503455e75fb6757b50da460714c050f9564a30eab561dbc67910da4",
      DI(5,3.8,4600), FA,
      "1/16 slab vertical embed+branch: upright slab with a branch arm at mid-height spanning east over the entry court; branch is a single-storey canopy volume that shades the lobby."),
    s("one16_v_embed_branch_b", "book:path:312c2d4bb55190e2eba8c277727992ea2f879f73cc37f676d544ee0b2968c42c",
      DI(5,3.8,4800), FA,
      "1/16 slab vertical embed+branch case 2: deeper branch at upper floors creates an asymmetric silhouette; embedded void below branch provides a two-storey atrium at public floor."),
    s("one16_v_intersect_intersect_a", "book:path:d3416d3d1115766003370b6e26e7d4ac28e5893c9f2bd96b16941f813f85af5d",
      DI(5,3.8,4500), FA,
      "1/16 slab vertical intersect+intersect: vertical slab intersected by a second rotated volume producing a compound silhouette; the intersection core is reinforced concrete and the projecting wings are steel frame."),
]

# ─── 1/2 long_axis (7) ────────────────────────────────────────────────────────
sentences += [
    s("half_la_rotate_stack", "book:path:ede197af18e9fed1800666b986634106304712540fa82e63ff4bbfe98aa295f5",
      DI(5,3.8,5000), FA,
      "1/2 half-cube long-axis rotate+array+stack: floor plates rotated incrementally and stacked; east face presents a faceted vertical expression. Public office programme fills continuously stacked floor plates."),
    s("half_la_taper_array", "book:path:00a64eeaaba888173bd0e20152d4ee4acbaec902327c33c4c8ca54c970513bd7",
      DI(5,3.8,4900), FA,
      "1/2 long-axis taper+array: tapered body widening from east (road) to west; arrayed as a repetitive bay system. Wider west end provides deeper floor plates for back-office functions."),
    s("half_la_compress_a", "book:path:098d164f2dac1c44c5c33f388d1b2d94709de0fb3384379578d44d870b24f3fa",
      DI(5,3.8,4600), FA,
      "1/2 long-axis compress: half-cube compressed into a squat bar; broad east face presents the public frontage. Compact depth reduces corridor travel distances for an efficient office layout."),
    s("half_la_embed_a", "book:path:e46c958587f693626dbecc89989d3c7e5afedf24da1cdec3280059d4084bedab",
      DI(5,3.8,5200), FA,
      "1/2 long-axis embed: secondary volume embedded in the south-west corner; creates a covered loggia at ground level and a recessed conference floor at level 3. Embedding subtracted from main mass without disconnecting."),
    s("half_la_embed_overlap_a", "book:path:1979381bcd2fd4aa4b2cee18451bdc220cc267392230f63e56a3cb561daf9abf",
      DI(5,3.8,5100), FA,
      "1/2 long-axis embed+overlap: embedded void overlaps the main body on the north elevation; overlap creates a thick north wall with interstitial service zone, keeping the south and east faces fully glazed."),
    s("half_la_embed_embed_a", "book:path:dea2102f6abd2b1db1f502aa1f3d9ee647e999251ccb4ed4e82745fb696bad6c",
      DI(5,3.8,4800), FA,
      "1/2 long-axis embed+embed: two sequential voids embedded concentrically; inner void is a sky garden at the building centre, outer void is a buffer ring of service cores. Programme wrapped around both voids."),
    s("half_la_intersect_intersect", "book:path:204d9a61bd963583b0138aebec122b8f1ef9510df879dec5c925f4d46f5283c6",
      DI(5,3.8,5300), FA,
      "1/2 long-axis intersect+intersect: two volumes at oblique plan angles intersect; primary volume aligned east–west for road access, secondary rotated 30 degrees to follow solar angle. Intersection core is shared circulation."),
]

# ─── 1/2 short_axis (7) ───────────────────────────────────────────────────────
sentences += [
    s("half_sa_rotate_stack", "book:path:4c46ac778b206310c13d4c00bd1144d8c646c855a3b7cbc7ea1a567336745fc1",
      DI(5,3.8,4700), FA,
      "1/2 half-cube short-axis rotate+array+stack: each floor plate rotated and stacked along the short axis; produces a spiralling compact block. North facade benefits from reduced solar exposure due to plate rotation."),
    s("half_sa_taper_array", "book:path:eef0ad1af65f6a10c034b7aba30d0b74956bfb2c55b553cd2941f5d688dde6e5",
      DI(5,3.8,4500), FA,
      "1/2 short-axis taper+array: body tapers along the short axis toward the north to yield a wedge-profile building; lower north edge respects the sunlight setback without a discrete step."),
    s("half_sa_embed_a", "book:path:b07511e1179f9125c4698ce1015b8f4fe0edc7f849a4f310af39b9c6e50615e4",
      DI(5,3.8,4800), FA,
      "1/2 short-axis embed: void embedded in the east face of the half-cube to create a recessed arcade at ground and first floors; upper three floors are continuous office plates projecting over the arcade."),
    s("half_sa_carve_offset_a", "book:path:c1e62670012fcb8579fbcffa7319dec624625ce39e6a1a6f310ffa7b7da846f3",
      DI(5,3.8,4600), FA,
      "1/2 short-axis carve+offset: north-east corner carved and the upper mass offset south-west; double move reduces bulk at the sunlight setback zone while keeping floors large on the south side."),
    s("half_sa_carve_offset_b", "book:path:3ff50595ebbea39bdd3a4841919b734cce67e6da3f75e1f1b1fb8522f32eadf1",
      DI(5,3.8,4400), FA,
      "1/2 short-axis carve+offset variant: shallower carve, larger offset; the overhanging south block creates a semi-sheltered courtyard below."),
    s("half_sa_embed_embed_a", "book:path:3462a911efbac2ac018ec4146d026d31dd79096092c54012fb3e57cc5a27f6c9",
      DI(5,3.8,5000), FA,
      "1/2 short-axis embed+embed: two voids at different scales embedded in the block; large west void is a full-height atrium, small east void is the entry alcove. Together they give a clear hierarchy between public and private realms."),
    s("half_sa_embed_embed_b", "book:path:b67729990b32e8828ab4df5636d3dcfc8ccb74e1fa6adcad32bb57b52cb9d973",
      DI(5,3.8,5100), FA,
      "1/2 short-axis embed+embed variant: voids embedded on opposing faces (east and west) producing a figure-eight hollow section; structural walls between voids carry load while each void is a distinct amenity space."),
]

# ─── 1/2 vertical (7) ────────────────────────────────────────────────────────
sentences += [
    s("half_v_split_join_a", "book:path:7acedec61890ab52c9a5bf814cfa3d854205a6596b3f8c0b692040a7a867ef4f",
      DI(5,3.8,5000), FA,
      "1/2 half-cube vertical split+join: tower volume split vertically into two wings bridged at floors 3 and 5; east wing faces road, west wing faces interior court. Bridge floors are shared meeting rooms."),
    s("half_v_split_join_b", "book:path:52fef3c7846a81bbad54d33f7da91066d0d2cdbee2b6711daf0f230372a61e89",
      DI(5,3.8,4800), FA,
      "1/2 vertical split+join variation: wings diverge in plan rather than just separating vertically; divergence opens a triangular courtyard facing east toward the road."),
    s("half_v_embed_a", "book:path:c69513870dfc7db31f90001d4da13e9ab27684b4bcd70ee98898013035c52a27",
      DI(5,3.8,5200), FA,
      "1/2 vertical embed: cylindrical void embedded vertically at the building's heart; five-storey atrium lit from above. Floor plates in a doughnut ring around the void, 5 floors."),
    s("half_v_embed_b", "book:path:608855d7f94aa40af3bee1fedc20bebfc87d20c70fdf7e6dc2e51a3052404dff",
      DI(5,3.8,5000), FA,
      "1/2 vertical embed variant: rectangular void embedded off-centre toward the north face; asymmetric plan creates a deeper south wing and a shallow north service strip."),
    s("half_v_carve_offset_a", "book:path:5aa35fa1d4f5bc3c2a49d9656fcb7f0aa9b93d544093e3d5c33486046f6588a3",
      DI(5,3.8,4600), FB,
      "1/2 vertical carve+offset: carve on the south face then offset upper floors northward; north_side=south because programme benefits from open south court at the access zone; sunlight setback still honoured by offset geometry."),
    s("half_v_embed_embed_a", "book:path:f5c66e2dcd5f773cc9a18ee553b9323018a595b7d5c5e95a5830b7f50593b717",
      DI(5,3.8,5300), FA,
      "1/2 vertical embed+embed: stacked pair of voids — lower is a double-height lobby void, upper is a roof garden void. Each embedded volume is distinct in size; together they articulate public from office storeys."),
    s("half_v_embed_embed_b", "book:path:c287dfcbb563c6a2a6db23e318f9ecea549d347f33e4215f58cd3b7dd8e93523",
      DI(5,3.8,4900), FA,
      "1/2 vertical embed+embed variant: voids on east and west faces simultaneously; east void is the lobby cut, west void is an enclosed garden. Section reads as a bow-tie between two outdoor moments."),
]

# ─── 1/4 long_axis (7) ────────────────────────────────────────────────────────
sentences += [
    s("qtr_la_split_join_a", "book:path:d9b61c8bea5df2677dc89f85e95f57c259843349273645a2a6e4a82f3954806c",
      DI(5,3.8,4500), FA,
      "1/4 quarter-cube long-axis split+join: bar split at mid-length and offset vertically to create a stepped section; lower east half at road level, upper west half stepped up as a roof terrace element."),
    s("qtr_la_split_join_b", "book:path:a9b38795629766ab5d77b1ad4531bd17e6fafe23b3989d6790e3a3c036a9060f",
      DI(5,3.8,4300), FA,
      "1/4 long-axis split+join variation: the two halves are sheared past each other and bridged; produces a Z-plan occupying the east–west parcel width efficiently."),
    s("qtr_la_embed_a", "book:path:07e8c58c376787e718d7e18839f4ac5660d533d655daac6640393c7263341f6c",
      DI(5,3.8,4600), FA,
      "1/4 long-axis embed: rounded void embedded in the north face of the bar to create a recessed garden at the sunlight setback; upper floors bridge over the void without interrupting the floor plate."),
    s("qtr_la_expand_a", "book:path:2438c10dab519c4f34ab4a73dfd9220260f24728764314829ec871fe509fd8f6",
      DI(5,3.8,4800), FA,
      "1/4 long-axis expand: bar expanded outward on the east face to create a thickened public frontage; expansion is bell-shaped, widest at ground level and tapering to match the standard section above floor 2."),
    s("qtr_la_embed_branch_a", "book:path:8d3aedd4fdbb3a7f6d1964ab1f5315247a3d1b2964bd456a2096c79ce90f7dfa",
      DI(5,3.8,5000), FA,
      "1/4 long-axis embed+branch: branch cantilevered from mid-bar toward the road creates an east wing canopy; void embedded at junction provides daylit atrium between bar and branch."),
    s("qtr_la_embed_overlap_a", "book:path:c0bc6e82e134e727587e2377bc6e3245998c81f1638d907c65b314b4e102ff36",
      DI(5,3.8,4900), FA,
      "1/4 long-axis embed+overlap: second volume overlaps the bar on the south, creating a shared floor zone; overlap is expressed as a glazed connector between the two masses in section."),
    s("qtr_la_embed_embed_a", "book:path:2b82937f12fb1fdf74d7b8c144d3d2c0032700b0b794ea8c19b5b8b6cdba0c66",
      DI(5,3.8,5200), FA,
      "1/4 long-axis embed+embed: dual embedded voids at the east and west ends of the bar; east void is the public lobby, west void is a utility recess. Together they give the bar a clear public–service hierarchy."),
]

# ─── 1/4 short_axis (7) ───────────────────────────────────────────────────────
sentences += [
    s("qtr_sa_rotate_stack_a", "book:path:de37fd9b0af79255387baff99879effc957882f2402dc3b42e6d29b7ea93a245",
      DI(5,3.8,4400), FA,
      "1/4 quarter-cube short-axis rotate+array+stack: compact floor plates rotated 5 degrees per floor and stacked; produces a slight helix that reduces shadow on the north neighbour."),
    s("qtr_sa_split_join_a", "book:path:6b8c3aa53e5224647eff9cc60ee8f9a050e9ce9942105b768488c05170a26d9a",
      DI(5,3.8,4200), FA,
      "1/4 short-axis split+join: the quarter-cube split along its short axis and each half shifted east–west; plan becomes a pinwheel around a shared stair core."),
    s("qtr_sa_expand_a", "book:path:ba1c8d39589e217399ef78008da12899d947d962eada6bd9316ab617af50be75",
      DI(5,3.8,4600), FA,
      "1/4 short-axis expand: body expanded northward to absorb unused setback area at lower floors while respecting the top-floor legal plan. Expansion is graded — maximum at ground, minimal at floor 5."),
    s("qtr_sa_expand_b", "book:path:36168087153f7d5b092fb04ab7a81b63d8c38d44a2f84716c9e17d62385d5148",
      DI(5,3.8,4800), FA,
      "1/4 short-axis expand variant: expansion on the east face only, creating a tapered bay that widens toward the road and signals the entry from the street."),
    s("qtr_sa_embed_branch_a", "book:path:32dc59b7b0604bda065a92bd57e5b99cccf0017dd3eb60642d2395c8c9209c8f",
      DI(5,3.8,5000), FA,
      "1/4 short-axis embed+branch: branch arm extends south from the main body; embedded void at the junction serves as a two-storey public gallery linking the two volumes."),
    s("qtr_sa_embed_overlap_a", "book:path:f9c06ddf25399f7007121ffa336d7949e3d19b77efac5be8d4d4797327216a11",
      DI(5,3.8,4700), FA,
      "1/4 short-axis embed+overlap: overlapping secondary volume on the west creates a thick west wall housing service cores; east and south faces remain slim and fully glazed for offices."),
    s("qtr_sa_embed_embed_a", "book:path:42e39ceeec6e5e198efe0381b6b87d312ba9c17d9abcdfa0c0cd342c91d6aa7c",
      DI(5,3.8,4500), FA,
      "1/4 short-axis embed+embed: two voids embedded diagonally opposite in the block; creates a diagonal transparency through the building from the road to the rear garden."),
]

# ─── 1/4 vertical (7) ────────────────────────────────────────────────────────
sentences += [
    s("qtr_v_split_join_a", "book:path:5eb3dcb66dae36c47adcefecc20736a797ec89ec05cbdb04cbed28e6b8fb6d95",
      DI(5,3.8,4400), FA,
      "1/4 quarter-cube vertical split+join: compact tower split horizontally at floor 3; lower podium expands to maximum BCR, upper office tower is setback from north to comply with sunlight constraint."),
    s("qtr_v_split_join_b", "book:path:d2524d54ac1e56b4c5bea1183b9c6bc55a7505997858aaf76c778e0f969601eb",
      DI(5,3.8,4200), FA,
      "1/4 vertical split+join variation: lower and upper parts are bridged by a single-storey skybridge at level 4; bridge is a transparent link with shared amenity for both office zones."),
    s("qtr_v_expand_a", "book:path:b802aafa114efb8dc20748e585dde537c74e6bf56c64dc0c7f3952e841537ad9",
      DI(5,3.8,4600), FA,
      "1/4 vertical expand: compact tower expanded downward at base to form a wider podium; upper tower stays within the sunlight setback envelope. Podium provides covered public drop-off on the east."),
    s("qtr_v_expand_b", "book:path:4cf44ef80cac744d87cad4fe7948d46aede5d1e89192f2bc9a793386220c7a7f",
      DI(5,3.8,4800), FA,
      "1/4 vertical expand variant: expansion on the south face of the tower adds a series of cantilevered balcony pods; section reads as a cactus silhouette with progressive expansions."),
    s("qtr_v_embed_branch_a", "book:path:f882a1e0f6553f17e7a9ab0fae53a2df43979abd65e7750dc27547ade501b57d",
      DI(5,3.8,5000), FA,
      "1/4 vertical embed+branch: branch arm at level 2 extends east over the footpath and provides a canopied arrival. Embedded void at the base of the tower forms the lobby atrium."),
    s("qtr_v_embed_overlap_a", "book:path:07d70191938ae81e266a17572dc057ccf1cb6beab84995e0c766fdbbf1baa43d",
      DI(5,3.8,4700), FA,
      "1/4 vertical embed+overlap: secondary volume overlaps the tower on the west at upper floors; overlap adds rentable area where the sunlight setback is less strict, boosting FAR toward target."),
    s("qtr_v_taper_taper", "book:path:dc60e0828bdb7466c7c34cbf845b47dcb903f6e3b651f847c49d1c93af3bfe3f",
      DI(5,3.8,4300), FA,
      "1/4 vertical taper+taper: double-taper in section — wide at ground, narrowing at mid-height, then flaring again at the top to form a waisted tower silhouette. Narrow waist coincides with the sunlight setback level."),
]

# ─── 1/8 long_axis (6) ────────────────────────────────────────────────────────
sentences += [
    s("eighth_la_rotate_stack", "book:path:0273dabe78b3dba074f499205360f77e82b37903c77e63e6fb5ed4393abd8f59",
      DI(5,3.8,4200), FA,
      "1/8 thin-bar long-axis rotate+array+stack: very slender bar plates rotated and stacked to create a dynamic ribbon tower; east end presents the shortest face to the road for minimum street obstruction."),
    s("eighth_la_taper_array", "book:path:4ee9721e409a384b65c27352a63c59c431bb084087434887aa8e8cf49065c0c6",
      DI(5,3.8,4000), FA,
      "1/8 long-axis taper+array: thin bar tapered along its length so the east (entry) end is narrowest; arrayed as a fin-wall arrangement across the site. Fins provide structural stability and shading."),
    s("eighth_la_expand", "book:path:3b7d285d67971cbdce800eb280a8d20ff6d6ad4fc68569679a1baf63104afd9f",
      DI(5,3.8,4400), FA,
      "1/8 long-axis expand: thin bar expanded at its centre creating a lozenge footprint; east and west ends remain pointed, mid-point is the widest floor plate for shared workstations."),
    s("eighth_la_carve_offset_a", "book:path:5d2d5892fe0b45559745919f7ff75e0d9ca7da5aeb73e9d08404b3e943a41fba",
      DI(5,3.8,4600), FA,
      "1/8 long-axis carve+offset: bar carved on its south face and offset northward; creates a sheltered south court as an outdoor amenity zone accessed from the lobby."),
    s("eighth_la_inscribe_inscribe_a", "book:path:b01029cb7dfe9855e24e62cfa0f9fb1f5b347fddc5c5f3ec31ca33344464c439",
      DI(5,3.8,4300), FA,
      "1/8 long-axis inscribe+inscribe: thin bar with an inscribed secondary bar at 45 degrees; crossing bars form an X-plan building with four sheltered courts at the re-entrant corners."),
    s("eighth_la_extract_a", "book:path:d2716e276c20c40a6b4482bec02189e58f67656a79e16cab1b107591527df594",
      DI(5,3.8,4100), FA,
      "1/8 long-axis extract: a portion of the bar is extracted (pulled outward) to form a separate fin element; extracted wing is an external stair and meeting pod attached at each floor level."),
]

# ─── 1/8 short_axis (6) ───────────────────────────────────────────────────────
sentences += [
    s("eighth_sa_taper_array", "book:path:1b9ebb311f1d5a6f5dea53fd0c7a99344905e0a14ad4b5cba91a2f78e29faf12",
      DI(5,3.8,4200), FA,
      "1/8 thin-bar short-axis taper+array: bars tapered along the short axis and arrayed to create a saw-tooth section; each tooth channels light into the floor plate from north-facing sawtooth glazing."),
    s("eighth_sa_bend_a", "book:path:4590a56c9147d27bafdb471808f63058eafb94b7e06408408ef1832fec75a857",
      DI(5,3.8,4400), FA,
      "1/8 short-axis bend: thin bar bent in plan around the east entry corner; curved east face creates a convex road presence and a concave internal courtyard face. Continuous curved facade in five storeys."),
    s("eighth_sa_bend_b", "book:path:8adb68b80a91f94fc17de857f0cb8508d2e64b8756eb52e3377f0e4a6cd60954",
      DI(5,3.8,4600), FA,
      "1/8 short-axis bend variant: bar bent more aggressively to near 90 degrees; plan reads as a curved L sheltering a south-facing garden from north winds."),
    s("eighth_sa_carve_offset_a", "book:path:c8809ff397ba09d0d8be5c760e9b0fc6e1fc22a27eaa83e7ca36e926b2b9c82d",
      DI(5,3.8,4000), FA,
      "1/8 short-axis carve+offset: bar carved at east entry and offset up at the same time; produces a split-level entry with the public floor half a storey above grade for accessible ramp approach."),
    s("eighth_sa_inscribe_inscribe_a", "book:path:14f118d093e0834eaee9d1c618c89ae4c5dfa0f5c250bac427443a27f5b1a986",
      DI(5,3.8,4500), FA,
      "1/8 short-axis inscribe+inscribe: short bar with a narrower bar inscribed inside at a skewed angle; the angular inscription cuts open the corners to create diagonal sightlines at each end of the building."),
    s("eighth_sa_split_join_a", "book:path:79664d96d36a7ea43678f991f90e38598c8344976c74a6306e129c1ec69ca4ff",
      DI(5,3.8,4300), FA,
      "1/8 short-axis split+join: thin bar split along its short axis creating two narrow parallel bars connected at alternate floors; forms a hollow double-bar section with an open slot between."),
]

# ─── 1/8 vertical (6) ────────────────────────────────────────────────────────
sentences += [
    s("eighth_v_split_join_a", "book:path:a2327b6aef7750332f98bcdd355e6b6122c5420f1b42ee148dfa65cd351875f4",
      DI(5,3.8,4000), FA,
      "1/8 thin-bar vertical split+join: tall thin bar split vertically into two even thinner towers bridged at the top; twin-tower silhouette with a shared skybridge as meeting floor."),
    s("eighth_v_bend_a", "book:path:3f38c40f8f331f32cbed3907465f37dec8ab3a04ef5d07c078376bb2ed3a011d",
      DI(5,3.8,4200), FA,
      "1/8 vertical bend: tower bent in section so the upper floors lean slightly east toward the road; base sits on the legal plan, top overhangs the entry plaza as a welcoming gesture."),
    s("eighth_v_bend_b", "book:path:5b1246347852f2232f1ceb2d5c223263ab6e64828dee0d89728d4f92db44e5f6",
      DI(5,3.8,4400), FA,
      "1/8 vertical bend variant: tower bent northward in section; the lean shifts mass away from the south court and creates a covered north terrace at ground level."),
    s("eighth_v_branch_a", "book:path:1717d404c28b8c7fc4eb07ca640c9749a1bcd30a998535b797359c6a6ffb9f64",
      DI(5,3.8,4600), FA,
      "1/8 vertical branch: thin tower with a branch at floor 3 extending east; branch provides a large meeting room cantilevered over the street-level plaza, creating a covered outdoor space below."),
    s("eighth_v_embed_branch_a", "book:path:67260165ea58020ed92b8bd6bd6b95846ec9d2e6d0caab713c275b6c215bc2c4",
      DI(5,3.8,4500), FA,
      "1/8 vertical embed+branch: embedded void at the base of the thin tower forms a double-height lobby; branch at floor 4 projects south to create a sky garden overlooking the parcel."),
    s("eighth_v_inscribe_intersect", "book:path:7a3189098fa9cf5f9ca246e521c79e417a74b75b8a2b0a81c9af92abda0c5805",
      DI(5,3.8,4300), FA,
      "1/8 vertical intersect+intersect: two thin bars intersecting at high level; ground floors are separate, upper floors merge at the crossing forming a shared floor plate with diagonal structural transfer."),
]

# ─── 3/8 long_axis (6) ────────────────────────────────────────────────────────
sentences += [
    s("lshape_la_rotate_stack", "book:path:09182926fcbe628962f9c95795c3bc25ac39b487847b82ab5b77d88f7e027eec",
      DI(5,3.8,5000), FA,
      "3/8 L-volume long-axis rotate+array+stack: L-shaped plates rotated and stacked; rotation shifts the re-entrant corner outward at each floor, creating a progressively opening courtyard from ground to roof."),
    s("lshape_la_taper_array", "book:path:b1bbe69597a29aa47f8f65c81f71261f0147ed392d1fd3eae4274d800be097fc",
      DI(5,3.8,4800), FA,
      "3/8 L-volume long-axis taper+array: the L-shape is tapered so the spine arm thins toward the south; arrayed in section to create a descending north wing that respects the sunlight setback incrementally."),
    s("lshape_la_branch_a", "book:path:2cf9617102901082c9b234ba251ffb8dc5d1b693bb66a3da38907b6eb106ff2e",
      DI(5,3.8,5200), FA,
      "3/8 L-volume long-axis branch: branch arm added to the L at the inner corner; creates a U-plan that frames a north-facing courtyard. East arm gives road presence, south arm adds office depth, branch links them."),
    s("lshape_la_embed_branch_a", "book:path:e4ce79c5e3365bb0d475861b56772e92226a8b2af57382fbcbdfd6fb87597972",
      DI(5,3.8,5300), FA,
      "3/8 L-volume long-axis embed+branch: embed void at the inner re-entrant corner of the L to form a covered outdoor room; branch arm extends east from the long arm toward the road."),
    s("lshape_la_intersect_intersect_a", "book:path:91192ecaa0256d4a69a36589b3995bf6e4e749bcfc9ff67ecde800da90edff35",
      DI(5,3.8,5100), FA,
      "3/8 L-volume long-axis intersect+intersect: two L-volumes rotated and intersected to form a complex interlocking section; intersection zone is the stairwell and service core shared by both wings."),
    s("lshape_la_carve_a", "book:path:a3c6628aa86e6962b40c7261c2e7a8dca6c03b248f6b27bd92ebfdffd0318b3b",
      DI(5,3.8,4900), FA,
      "3/8 L-volume long-axis carve: large carve on the inner corner of the L opens up the re-entrant to a full-height atrium; both arms of the L are connected at each floor by bridges spanning the carved void."),
]

# ─── 3/8 short_axis (6) ───────────────────────────────────────────────────────
sentences += [
    s("lshape_sa_rotate_stack", "book:path:a47a962ff956ecb36a57853cdd9419aebf58eb54b48982f064a0bf0f30e55839",
      DI(5,3.8,4800), FA,
      "3/8 L-volume short-axis rotate+array+stack: L-plates rotated around the short axis and stacked; short arm of the L rotates into a covered arcade below the long arm at upper floors."),
    s("lshape_sa_branch_a", "book:path:ace93d399c2b0b7898d49e0f95d9617513fbde925227ea3871df810b0758d138",
      DI(5,3.8,5000), FA,
      "3/8 L-volume short-axis branch: branch from the short arm of the L spans east to the road; branch is a glazed connector housing a public stair that ties the street level to the main entry on the upper floor."),
    s("lshape_sa_embed_branch_a", "book:path:bffc0df8678282fb962672e1a61bb850b6b54c33e9fe649e86bebb23c04be210",
      DI(5,3.8,5200), FA,
      "3/8 L-volume short-axis embed+branch: embedded void in the long arm creates a mid-building sky garden; branch from the short arm reaches the road. Together they form a campus-like open public plan."),
    s("lshape_sa_embed_branch_b", "book:path:2713967d70c807ea0232f1a8024f96d460272332526fc4316ffa933845de332c",
      DI(5,3.8,4900), FA,
      "3/8 L-volume short-axis embed+branch variation: branch at the top floor only, creating a roof-level bridge between the arms; roof bridge is a meeting zone with views over the parcel and access to both office wings."),
    s("lshape_sa_intersect_intersect_a", "book:path:95c339db03db10fea5761314a6eb964afe06f580ac4b0a5753af11550a58c5d6",
      DI(5,3.8,5100), FA,
      "3/8 L-volume short-axis intersect+intersect: L-volume intersected with a rectangular bar; intersection at the corner of the L forms a thickened structural joint while the bar extends as an east-facing public wing."),
    s("lshape_sa_carve_a", "book:path:d98b350315f2d544c592a34728243da5e2525214ca928122dd5e4116955169f2",
      DI(5,3.8,4600), FA,
      "3/8 L-volume short-axis carve: the inner concave face of the L is carved further to create a rounded court; the courtyard becomes a garden court lined with office glazing on three sides."),
]

# ─── 3/8 vertical (6) ────────────────────────────────────────────────────────
sentences += [
    s("lshape_v_taper_array_a", "book:path:7d1e6db393b1adfc4f584b64f87e0019bfb63bfbc1b264e95789502a1bd2db34",
      DI(5,3.8,4600), FA,
      "3/8 L-volume vertical taper+array: the upright L is tapered so each arm thins toward the top; arrayed vertically the taper gives the building a sculptural profile and reduces solar gain on upper floors."),
    s("lshape_v_taper_array_b", "book:path:5675f3d163d1f41d2c675a49691ad65b471444dcac4e9cd308ce5de55ea2fef5",
      DI(5,3.8,4800), FA,
      "3/8 L-volume vertical taper+array variant: arms taper at different rates — the long arm tapers quickly while the short arm stays constant; asymmetric profile reduces massing at the north-west corner near the sunlight boundary."),
    s("lshape_v_branch_a", "book:path:ccda86a3ae025f1bf457634b26494c7b9117d029353a61dff5bbfd645dd650b8",
      DI(5,3.8,5000), FA,
      "3/8 L-volume vertical branch: branch extends from the inner corner of the upright L horizontally at level 2; creates a covered ground-level plaza between the two L arms, with the branch as a roof."),
    s("lshape_v_embed_branch_a", "book:path:51c534e3306d88d9e55374662e257f1a07bd324bf275d8ba5b08d8c3d0fddd64",
      DI(5,3.8,5200), FA,
      "3/8 L-volume vertical embed+branch: void embedded at the base of the vertical L forms a public hall; branch at floor 3 projects south from the short arm to add area above the sunlit zone."),
    s("lshape_v_embed_overlap_a", "book:path:d114a1d1f04b3d19c6b7e369269f21fdb174d6236e681ca4ed2e30810087d842",
      DI(5,3.8,5100), FA,
      "3/8 L-volume vertical embed+overlap: secondary volume overlaps at the base of the long arm, thickening the ground-floor public podium; upper floors retain the lean L-profile to stay within the sunlight envelope."),
    s("lshape_v_embed_embed_a", "book:path:fd1f02d0d44ec0d582556a2d9b6e4351e2996ede295cdecdb0fc665ac5f380b3",
      DI(5,3.8,4800), FA,
      "3/8 L-volume vertical embed+embed: two voids embedded in the vertical L — one at the inner corner as a light well, one at the base of the short arm as a piloti-like open passage. Both keep the mass connected."),
]

# ── Verify count ──────────────────────────────────────────────────────────────
assert len(sentences) == 120, f"Expected 120 sentences, got {len(sentences)}"

# ── Verify all path_ids unique ────────────────────────────────────────────────
pids = [s["book_composition_path_id"] for s in sentences]
assert len(pids) == len(set(pids)), "Duplicate path_ids found!"

# ── Validate against schema ───────────────────────────────────────────────────
import jsonschema

with open(r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp25\book-author\schema.json", encoding="utf-8") as f:
    schema = json.load(f)

payload = {"sentences": sentences}

validator = jsonschema.Draft7Validator(schema)
errors = list(validator.iter_errors(payload))
if errors:
    for e in errors:
        print(f"SCHEMA ERROR: {e.path} -> {e.message}")
    sys.exit(1)

print(f"Validation passed. {len(sentences)} sentences, 0 schema errors.")

# ── Write output ──────────────────────────────────────────────────────────────
out_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp25.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Written: {out_path}")
