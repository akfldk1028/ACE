import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Validate with jsonschema
try:
    from jsonschema import Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# ────────────────────────────────────────────────────────────────────────────
# PLAN: 18 groups (6 base_volumes × 3 orientations)
#   1/1-LA, 1/1-SA, 1/1-V   → 7 each = 21
#   1/16-LA, 1/16-SA, 1/16-V → 7 each = 21
#   1/2-LA, 1/2-SA, 1/2-V   → 7 each = 21
#   1/4-LA, 1/4-SA, 1/4-V   → 7 each = 21
#   1/8-LA, 1/8-SA, 1/8-V   → 6 each = 18  (less to balance)
#   3/8-LA, 3/8-SA, 3/8-V   → 6 each = 18  (less to balance)
#   TOTAL: 12*7 + 6*6 = 84 + 36 = 120  ✓
#
# GFA target: 3745–5930 (capacity 6242, ground cap 1498)
# Storey default: 5 (19.0 m), storey_height: 3.8 m
# Access: east (+x); north_side: north (+y) for most
# ────────────────────────────────────────────────────────────────────────────

def di(storey_count, gfa):
    return {
        "schema_version": "arr.maas.dimensional_intent.v1",
        "storey_count": storey_count,
        "storey_height_m": 3.8,
        "target_gfa_m2": round(gfa, 1),
        "delivery_policy": "preserve_physical_dimensions",
        "programme_status": "unknown"
    }

def facing(access="east", north="north"):
    return {"access_side": access, "north_side": north}

def s(name, pid, storey, gfa, rationale, access="east", north="north"):
    return {
        "name": name,
        "book_composition_path_id": pid,
        "dimensional_intent": di(storey, gfa),
        "facing": facing(access, north),
        "rationale": rationale
    }

sentences = []

# ════════════════════════════════════════════════════════════════════════════
# 1/1 LONG_AXIS  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("full_la_taper_array",
      "book:path:b92e455fdf5d5e2998479d09c300b931b578aa4c99475ebd8bacb5369602ec4d",
      5, 5200,
      "Full-parcel long-axis slab tapered along its depth and arrayed in section; each repeat steps back from the east road giving a graduated facade. Storey 5 fills FAR. Access east reads the tapering profile directly from the street.",
      "east","north"),
    s("full_la_split_join",
      "book:path:6948a5e63f915cb0d9bf881fe1d4c736b2190d74af5cd9ba4ef186dbea1024f7",
      5, 4900,
      "Long-axis full-parcel bar split lengthwise then re-joined with a bridging spine; the seam creates a covered interior street. East access enters the joint. North half is lower to honour the sunlight setback taper from 11.4 m up.",
      "east","north"),
    s("full_la_branch_pack_stack",
      "book:path:273b712defeae05e13d5802952a25cc9fed061a2befba5e087e84642c1db4ba8",
      5, 5400,
      "Full-parcel long-axis base with stacked branch arms packing upward; the branching reads as a sequence of horizontal fins. East entry at ground. North branch arm held back one storey to respect the sunlight plane.",
      "east","north"),
    s("full_la_skew_reflect_pack",
      "book:path:dd1ac90918b1417e6ffeba11ef66e0a72277e6b8b33611ece6c251bb536cc06c",
      5, 4800,
      "Long-axis bar skewed diagonally then reflected and packed; the paired wedge volumes create a V-plan reading along the east facade. 5 storeys at target FAR well below capacity ceiling.",
      "east","north"),
    s("full_la_bend_stack",
      "book:path:4480470a13d099cc987dbe36a4c875563e021059447377c7ad06ecaaa8018699",
      5, 5100,
      "Full-parcel long-axis bar bent mid-span and stacked; the upper bent slab oversails the lower producing a canopy above the east entrance. Stack keeps north shoulder lower than south.",
      "east","north"),
    s("full_la_embed_branch",
      "book:path:d7c892248697c06f1c5ea03783e3e1debe3e6648a688f27d22ee40d2e3bd1fcf",
      5, 4750,
      "1/1 long-axis: a secondary volume embedded inside the primary bar, with branches extruding east toward the road as covered loggias. North side of branches stays below 9 m setback threshold.",
      "east","north"),
    s("full_la_expand_nest",
      "book:path:3fa61db5d833e1ecf7fbb1bec06e9d3114cd6c98faf2a4270fc6efac62cf60f7",
      5, 5050,
      "Long-axis full volume expanded outward then nested inner void; the ring section reads as a double-skin building with service zone between layers. East ring thicker for access and lobby.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/1 SHORT_AXIS  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("full_sa_rotate_array_stack",
      "book:path:a6b852ced38ea5ab2c67e54bd82da0b37178d7a6cecf24ebefe1b1c3749ffa7b",
      5, 4950,
      "Full-parcel short-axis bar rotated in plan then arrayed and stacked; the rotation angle opens a diagonal courtyard slot. Access east on the rotated face. North stack kept one storey shorter.",
      "east","north"),
    s("full_sa_taper_array",
      "book:path:e0f93dc218c58122055a5bc717f66c8991e147f1d6168a3b950e9c240c6dd940",
      5, 5000,
      "Short-axis full slab progressively tapered from base to crown and arrayed in plan; produces a fan arrangement when read from east. 5 storeys reaches mid-FAR comfortably.",
      "east","north"),
    s("full_sa_inflate_pack",
      "book:path:4c34832e1e19099ab28a374dbd027cfa019551d1c42eca0fcd1f0479fff5cfa0",
      5, 4600,
      "Full-parcel short-axis volume inflated laterally then packed in pairs; the billowing sides create soft street edges. East inflate face forms the principal entrance bay. Lower FAR justified by wider public ground-floor.",
      "east","north"),
    s("full_sa_expand_reflect",
      "book:path:71ed94b0b98b300d072c44a21e9ccf46ab86d849899a7f4d83ddcec82b9e1b9a",
      5, 5150,
      "Short-axis bar expanded along the x-axis and reflected; the mirrored pair flanks the road with a gate-like silhouette. Both halves share an east threshold. North arm one storey shorter per setback.",
      "east","north"),
    s("full_sa_embed_branch",
      "book:path:b62b518bfc0dcb183b987b9b83968013301e18b4f8d34553ec85cec78feafab1",
      5, 4850,
      "1/1 short-axis: compact transverse bar with embedded service core and east-facing branch loggia. The branch reads from the road as a projecting porch at each storey. North stays flush.",
      "east","north"),
    s("full_sa_intersect_split",
      "book:path:80114e93996817c12e37cfa6f94667869b55aadb4f6d2c1f07a7e7da2832f732",
      5, 4700,
      "Full-parcel short-axis slab intersected with an inclined solid then split; the inclined cut appears as a diagonal slash on the east elevation. North portion is the lower half of the split.",
      "east","north"),
    s("full_sa_bend_branch",
      "book:path:4cefd292f041c34b042bfdeda70c9abceb3451b0fac9698252576b1e211cae31",
      5, 5300,
      "Short-axis full bar bent transversely so the top curves south, then a branch arm reaches east; the curve keeps mass away from the north boundary. Branch defines the public entrance.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/1 VERTICAL  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("full_v_rotate_array_stack",
      "book:path:a494da71378365512d741c12851c4376e39b338c2e18fb77514998dd56125d46",
      5, 5500,
      "Full-parcel vertical tower rotated slightly about z and stacked in section; each storey packet offsets, producing a spiralling elevation. East access at base. North face offset inward on upper floors.",
      "east","north"),
    s("full_v_pinch_join_array",
      "book:path:894edc2da9e335e33366cd7cbce313dcd91446de3225fe2cec5bbc660187b617",
      5, 5350,
      "Vertical full-parcel volume pinched at mid-height then joined to a secondary element and arrayed; pinch creates a waist reading as a transition storey. East face unobstructed for access.",
      "east","north"),
    s("full_v_carve",
      "book:path:fd4f1086483219e401890b2c547f8ed6492bd3d1b018811e3a6323cd77b14b83",
      5, 4650,
      "Vertical compact volume with a large carve on the west face opening a semi-outdoor atrium. East entrance remains solid. Carve reduces massing on the north side above 11 m.",
      "east","north"),
    s("full_v_fracture",
      "book:path:147755525f299a9aca917ee8a0c82f5a5e60be1a1c0fecf9c1e106c51e3807e9",
      5, 5250,
      "Full-parcel vertical bar fractured along a diagonal plane; the two halves tilt apart slightly creating an outdoor slot visible from east. North half is the shorter retained portion.",
      "east","north"),
    s("full_v_overlap",
      "book:path:549875d23d154a1a67557a53c07b29e17a08b2030a61b78babb633cfdad1f533",
      5, 4800,
      "Two full vertical volumes overlapping at the north-east corner; the overlap zone is a shared circulation core. East access reads through the gap between the two bars.",
      "east","north"),
    s("full_v_carve_offset",
      "book:path:fb8b96d1a5505c9044c28a2981030fec7765f40b4c470eb4da00879dffcf84b9",
      5, 4550,
      "Vertical full volume carved on the south face then offset outward; the offset mass creates a shadow band canopy. Lower FAR earned by expanded ground void for public pause.",
      "east","north"),
    s("full_v_lift_extrude",
      "book:path:b2fb7d9d24d1eaaf6a02fcb71f3a5fdee16c936ad450cf9ab4910cddd5b2557a",
      5, 5450,
      "Full-parcel vertical bar lifted off the ground by piloti then extruded in cross-section; the raised floor plane opens a permeable ground level. East access ramp rises to lobby. North face setback above 9 m.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/16 LONG_AXIS  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("thin_la_rotate_array_stack",
      "book:path:691264aabeeefc08b8f946a04e110ebf01857dd4f346cbe0325a28bd38b93ab5",
      5, 4100,
      "Very thin long-axis sliver rotated and arrayed in a stacked fan; the narrow profiles create a layered screen mass readable from east. Compact footprint leaves ground open.",
      "east","north"),
    s("thin_la_pinch_join_array",
      "book:path:6191ea9e054f4e7f1a359968637de59a4a39a3ae3ec99dfee9b5a145c25e8eec",
      5, 3900,
      "1/16 long-axis sliver pinched at waist, joined to a transverse strip, and arrayed; the pinch-and-join repetition forms a folded lattice. East face open for access at each bay.",
      "east","north"),
    s("thin_la_carve",
      "book:path:8557b85d7cd4cfb903274b826961123347f5ab98adc3f2ec8e586a9ef870b7ed",
      5, 3950,
      "Thin long-axis bar carved on its broad face; the recess creates a semi-external corridor along the east road. Slender profile keeps the north shadow to a minimum.",
      "east","north"),
    s("thin_la_overlap",
      "book:path:af41527812b7c7b6eb001a671eacfb152a9304911d801303ad0bc64db6a6dc96",
      5, 4050,
      "1/16 slender bars overlapping in a staggered long-axis arrangement; the overlap zone is a shared stair tower. East access aligns with overlap joint.",
      "east","north"),
    s("thin_la_embed_overlap",
      "book:path:53878f344ed4097fff9e933f715dbb921e0a8133cb8c673d26f195097e6a28db",
      5, 4150,
      "Thin long-axis bar with a narrower volume embedded inside and the assembly shifted to overlap a secondary strip; the layered section reads from east as a deep mullion facade.",
      "east","north"),
    s("thin_la_embed_taper",
      "book:path:bd1b2c9f3e4b0a34dec758a51c7125ddf216b3573c4f391ec330a173371bbd41",
      5, 4200,
      "1/16 long-axis: slim bar with embedded inner spine and tapering crown; the crown taper steps back from the north sky-plane at upper floors. East access at full-height slot.",
      "east","north"),
    s("thin_la_branch_expand",
      "book:path:d6c567d5b7e81f3329d447a05dd4ec0e297b3cbc19ae193c28ed3d2243faba96",
      5, 4300,
      "Slender long-axis bar with a branching east arm that expands into a wider head; the T-silhouette creates an overhang above the east entry. North arm kept below setback height.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/16 SHORT_AXIS  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("thin_sa_taper_array",
      "book:path:1c88520a4e236c41d25760782bdd81abfa179359e272717ed398eb28c33d1117",
      5, 3850,
      "1/16 short-axis thin strip tapered and arrayed; the repeated taper gives an accordion-like east elevation. Minimal footprint maximises separation between strips.",
      "east","north"),
    s("thin_sa_pinch_join_array",
      "book:path:94543b92bbabe1082e1c7f548f7b415c97e654a21aa2e4d9b33b2f254d5b40d4",
      5, 3950,
      "Short-axis slim bar pinched at mid-height, joined longitudinally, and arrayed; the pinches occur at alternating heights creating a diagonal rhythm across the east facade.",
      "east","north"),
    s("thin_sa_branch_pack_stack",
      "book:path:9612269d34b658eab8492ebb46b12de243596b781196f5bece44c86716cc8c05",
      5, 4100,
      "Thin short-axis bar with stacked branch arms packed into a narrow east tower; each branch arm acts as a projecting balcony. Compact depth suits narrow parcel dimension.",
      "east","north"),
    s("thin_sa_skew_reflect_pack",
      "book:path:4d69447b97ebfa218ad07815f73d985cadeb421343b38de41744982915b6ae89",
      5, 4000,
      "1/16 short-axis sliver skewed and reflected then packed; the reflected pair form a narrow V-channel open to the north sky. East access between the two skewed faces.",
      "east","north"),
    s("thin_sa_fracture",
      "book:path:68db4f781cd094154fbf053f1d645ab18eaaa0bb56614dab3f219f09cec17ffd",
      5, 3900,
      "Short-axis thin bar fractured along a near-vertical diagonal; the fracture gap is a covered threshold slot. East face holds the access while north fragment is shorter.",
      "east","north"),
    s("thin_sa_embed_overlap",
      "book:path:f514fd6029620cbd5239701d0d0efebb43c95e733abc75e1c739398cdf83be4e",
      5, 4050,
      "1/16 short-axis sliver: embedded secondary strip overlapping the primary to build depth; the overlap doubles the effective section at the east facade.",
      "east","north"),
    s("thin_sa_bend_bend",
      "book:path:04dc76800cd884790108b1ba4cf215dc5df8371086da995a1608e99da6ec683d",
      5, 4200,
      "Thin short-axis bar bent twice in opposite directions forming a shallow S-curve in plan; the S-plan orients the east face squarely to the road while the north end angles away from the boundary.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/16 VERTICAL  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("thin_v_taper_array",
      "book:path:cfea0e7fc0f6387d76b66c7137a5f2bf5a60f7da51438117dd2411e53356f68e",
      5, 4250,
      "1/16 vertical needle tapered and arrayed around the site centre; the cluster of tapering spires is read as a single sculptural mass from east. Low ground coverage freed for public realm.",
      "east","north"),
    s("thin_v_split_join",
      "book:path:21ef62855e3d3d9327fe20f39af17a8a0558899a34bce6f3086cdd2341959206",
      5, 4000,
      "Slim vertical volume split along the y-axis then re-joined at base and crown; the split body frames a thin north-south slot court visible from east.",
      "east","north"),
    s("thin_v_compress",
      "book:path:6635697450431d5f54e8e8de694ac028c18a8404c03da01d433a315616e2f1e9",
      5, 3800,
      "1/16 vertical bar compressed laterally producing a flattened disc-like profile at mid-height; the compressed waist yields a distinctive two-zone silhouette. East access at the wider base.",
      "east","north"),
    s("thin_v_grade",
      "book:path:a0853c2442690409bdaad584c95bfc9732e2927456a3a118d5b9c740e21b61a8",
      5, 3950,
      "Thin vertical volume graded so that the east face pitches outward; the inclined east face shelters the street entrance below. North face remains vertical.",
      "east","north"),
    s("thin_v_lodge",
      "book:path:5b79a673404719957545e8ae30f4ca2670425d4086f56a0e098661884413a491",
      5, 4100,
      "1/16 vertical bar lodged against a secondary plinth volume; the lodge joint reads as a horizontal datum band at the third storey. East access through plinth.",
      "east","north"),
    s("thin_v_embed_branch",
      "book:path:7e1a3110d44db43856bb809ea4336273e4c18c14bfd1e9fb41665beb365224bf",
      5, 4050,
      "Thin vertical volume with embedded core and east-branching arm at the top two storeys; the cantilevered branch arm creates an observation lookout over the road.",
      "east","north"),
    s("thin_v_expand_shift",
      "book:path:720593e2b2d82c016a8f0a1ac4ea3badb04e01578ffe47094a6017cb4495b147",
      5, 4400,
      "1/16 vertical: top half of the bar expanded in plan and shifted east; the overhanging expanded crown shelters the east entry. North side of crown stays within sunlight envelope.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/2 LONG_AXIS  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("half_la_rotate_array_stack",
      "book:path:51b87ccfefaf2d3360f9a135c557494dd67d845c7cac27e83435010a26ef2f76",
      5, 5000,
      "Half-parcel long-axis bar rotated 15 degrees from the grid and stacked; the rotation aligns the major elevation to the slightly oblique road direction. East access on rotated face.",
      "east","north"),
    s("half_la_taper_array",
      "book:path:5c22950d1a45f19095d1289398d8ca25b8b09ebe0fe01bd81a2487f35fe31b5f",
      5, 5100,
      "Half-parcel long-axis volume tapered in two directions and arrayed; dual taper creates a pointed plan form at the north end. East access at the wider south end.",
      "east","north"),
    s("half_la_compress",
      "book:path:1979434c5e8e807c4be6783d18b4216d8d0ce4ab3b77f08477b5ad7325b525fb",
      4, 3800,
      "Half-parcel long-axis slab compressed in height to 4 storeys; the low profile activates the rooftop as a public terrace accessible from the road. Lower storey count earned by usable roof.",
      "east","north"),
    s("half_la_lodge",
      "book:path:d2d20de87c2b2514982cb2a4d8db63b452561b6d6e9139b7f25c0ff06bef528e",
      5, 4950,
      "Half-parcel long-axis bar lodged against the north boundary producing a L-shaped ground plan with a south-facing court. East access through the shorter east wing.",
      "east","north"),
    s("half_la_expand_nest",
      "book:path:b154828f96309048394e3b02fb9395b484ac9ae93af51020b3898d1e927efd16",
      5, 4800,
      "Half long-axis volume expanded outward then nested; the ring plan reads as a doughnut section with a central open void. East face is the primary occupied ring.",
      "east","north"),
    s("half_la_intersect_intersect",
      "book:path:3542cd6b70d360448789b7065c7209d4af65afa6a0cb5d026d572520f3643303",
      5, 4700,
      "Half-parcel long-axis bar intersected twice with inclined secondary volumes; the cross-cuts appear as diagonal reveals on both east and west elevations.",
      "east","north"),
    s("half_la_taper_bend",
      "book:path:4e8d8c40a580583fd079a346e0e538cd095b94322be73c835c8bdc1b4999667a",
      5, 4900,
      "Half long-axis slab tapered along the z-axis then bent about a horizontal axis; the tapering bent profile gives a gently curved pitched silhouette. East face shows full taper height.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/2 SHORT_AXIS  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("half_sa_rotate_array_stack",
      "book:path:a3a133f11d50dd8fd1cc1fa315ffc24e2d78b46c120d9bad5d108abfe9a27db6",
      5, 5050,
      "Half-parcel short-axis volume rotated and stacked in a pinwheel arrangement; the rotation reads as a dynamic corner condition on the east facade. Access through the rotated slot.",
      "east","north"),
    s("half_sa_pinch_join_array",
      "book:path:d3cbcd58ebe374387bede4e7716db5f3e398434f11b036611eac49bb4120cb31",
      5, 4800,
      "Half short-axis bar pinched at the second storey then joined to an east wing and arrayed; the pinch-wing creates a cruciform section at mid-height visible from road.",
      "east","north"),
    s("half_sa_branch_pack_stack",
      "book:path:4b0cbf788c1a3ba993d8d1bedb672dba224d0ce92fa3d81fab9a37ebc7649e86",
      5, 5150,
      "Half-parcel short-axis base with branch arms stacked and packed east; the stack of branches reads as a stepped balcony system. North arm is lowest in the stack.",
      "east","north"),
    s("half_sa_grade",
      "book:path:4e9726747792a03f7498baa8bebc8832ab0e95878608aadb48b5c8a20b725913",
      5, 4650,
      "Half short-axis slab graded so that its top surface inclines from south to north; the inclined roof directs rainwater and reduces north-side bulk. East entry at the higher south end.",
      "east","north"),
    s("half_sa_carve_offset",
      "book:path:e1aea896a0d7992bca9179c0c2a785752d75bebcaa1461aa3b411422add9ebfb",
      5, 4750,
      "Half-parcel short-axis volume carved on the east face then offset outward; the offset creates a canopy cantilevered over the east entry path. North carve edge respects the sunlight plane.",
      "east","north"),
    s("half_sa_split_split",
      "book:path:3067018bcb0f0cf65e296ba24cba747b253f4d9901725c20752ca32aee003641",
      5, 4550,
      "Half short-axis bar split twice producing three parallel slabs; the triple-slab section frames two covered outdoor passages. East access enters the central passage.",
      "east","north"),
    s("half_sa_shift_notch",
      "book:path:7a96117d7649fdb20aa31d3705f92f49eef54f2f47c6362aa80c3d14a160203a",
      5, 5000,
      "Half short-axis slab shifted laterally then notched at the corners; the shift creates an offset plan while notches soften street corners at the east entry.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/2 VERTICAL  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("half_v_rotate_array_stack",
      "book:path:525b60c7757d53de514af67f203e3d0c57e1fdd55296fe5d5dd76b610e36c1eb",
      5, 5200,
      "Half-parcel vertical tower rotated and stacked in section; each section packet twists slightly producing a spiralling tower. East access constant throughout. North face offset on upper storeys.",
      "east","north"),
    s("half_v_embed",
      "book:path:12d705bc21d40954b3ded4db298d4667d5144dc06fe746732830b6ce5e086681",
      5, 4900,
      "Half-parcel vertical volume with a service core embedded inside producing a hollow-core section; the core aligns north-south and its shadow relief is visible on east facade.",
      "east","north"),
    s("half_v_inflate",
      "book:path:4e4e0f0970031f03a01c753d893a5cb32f76e5b67af0d7e26a8e610cf3d59d0f",
      5, 5050,
      "Half vertical bar inflated along the y-axis to create a lens-shaped section; the east face remains flat for access while the west bulge pushes toward the interior.",
      "east","north"),
    s("half_v_puncture",
      "book:path:ca68ebf6a3ebd02eb3a303a46aad5687581296aa75a5106aca8f3b1aa63056fd",
      5, 4700,
      "Half-parcel vertical volume punctured through its depth creating a horizontal tunnel at mid-height; the tunnel opens north-south providing a shaded view corridor from east street.",
      "east","north"),
    s("half_v_carve_offset",
      "book:path:59b49d04a61c202a874259b7d219a59c6b0a4d85547056f89f353f021a128e0d",
      5, 4800,
      "Half vertical volume carved on the south face and the carved piece offset to the east; the offset element forms an entrance canopy. North face kept flush with setback line.",
      "east","north"),
    s("half_v_split_split",
      "book:path:255eafd74bd64b32effb7b0ecaf18ca749272683f6c77219332f89fde8436e79",
      5, 4600,
      "Half vertical tower split twice along vertical planes producing a three-finger plan; each finger has its own east-facing facade bay. North finger is set back from the boundary.",
      "east","north"),
    s("half_v_taper_bend",
      "book:path:00c9eb232904b1191008b0436eaf9d2eb51d262b9eab7f23cfcf9332fe163398",
      5, 5100,
      "Half-parcel vertical: taper narrows the top then a bend leans the crown east; the lean brings the upper floors closer to the east road while maintaining north setback.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/4 LONG_AXIS  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("qtr_la_taper_array",
      "book:path:845fbb8750794f7ede15714dac3cb9bb7f2235885e8671a0579654faecd8c474",
      5, 4400,
      "Quarter-parcel long-axis bar tapered in plan and arrayed as a stepped cascade along the east road; each array element steps back creating a terraced east elevation.",
      "east","north"),
    s("qtr_la_split_join",
      "book:path:d9b61c8bea5df2677dc89f85e95f57c259843349273645a2a6e4a82f3954806c",
      5, 4200,
      "Quarter long-axis bar split and rejoined with a narrow bridge element; the bridge is glass, allowing the east entry light to penetrate to the north court behind.",
      "east","north"),
    s("qtr_la_embed",
      "book:path:bca1c21b43ffa296db5ab0bb6e7a2958d000a834296623991fceed5189e7511e",
      5, 4100,
      "1/4 long-axis: a thin secondary bar embedded in the primary creating a double-layer east facade; the outer layer is open access, the inner layer is occupied offices.",
      "east","north"),
    s("qtr_la_inflate",
      "book:path:97d2077f026b88d50689a9ba36da1ca0b6befd74c6b83ad11dd61cff1a5e164a",
      5, 4500,
      "Quarter long-axis bar inflated vertically; the inflated midsection gives a barrel-vaulted cross-section visible from east. Access enters at the wider mid-height base.",
      "east","north"),
    s("qtr_la_overlap_expand",
      "book:path:4f138a790ee3e26afe5524540c05ec92276a4781a0b90ed3e78f56e308ceb7b8",
      5, 4350,
      "Quarter long-axis volume overlapping with an expanded secondary element; overlap junction is the circulation core, and the expanded outer forms east-facing offices.",
      "east","north"),
    s("qtr_la_split_split",
      "book:path:cc37a31a2c751f95e9b338b7e0a36114352e707ad7296191736f623b53d3a186",
      5, 4050,
      "Quarter-parcel long-axis bar split twice in cross-section; three nested slabs create a deep-ribbed east facade. Each rib gap is an open-air planting corridor.",
      "east","north"),
    s("qtr_la_shift_notch",
      "book:path:6f9c44e5b8ecd00778ee4830e5dc7acea348d231d9e0449b6d9e3677e71a2e0d",
      5, 4300,
      "Quarter long-axis slab shifted north then notched at its east corners; the shift reduces the ground floor shadow on the south neighbour. Notches form the east entry bay.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/4 SHORT_AXIS  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("qtr_sa_taper_array",
      "book:path:453214b3e18725fabe90aafa6332583bc1ac8e4627e7589c15acca8fadbe2a02",
      5, 4250,
      "Quarter-parcel short-axis strip tapered in plan and arrayed along x; the array forms a comb of fins pointing east. Each fin tip is a double-height lobby.",
      "east","north"),
    s("qtr_sa_expand",
      "book:path:1c2b97b2858e14f6281b5e0c16f9f64f6d1bae53e00ac105b30e747e0066c025",
      5, 4450,
      "1/4 short-axis volume expanded east to fill the legal ground plan envelope then held at 5 storeys; the expansion gives maximum ground activation. East face is a flush wall with recessed entry.",
      "east","north"),
    s("qtr_sa_inscribe",
      "book:path:8dd2889c69159a429aedddb75486742412823c07b0ed8c5488676404a62f23d0",
      5, 4100,
      "Quarter short-axis bar inscribed within a cylindrical envelope producing a curved east facade; the curved surface reflects the road curve and opens a crescent-shaped entry plaza.",
      "east","north"),
    s("qtr_sa_rotate",
      "book:path:0aa0869ea17d10d9cf05c6a479f542b3862e16415b527bdd4b99f3ee11c450a6",
      5, 4300,
      "Quarter-parcel short-axis bar rotated 30 degrees to face the road obliquely; the angled facade creates a funnel toward the east access and a shaded north recess.",
      "east","north"),
    s("qtr_sa_embed_branch",
      "book:path:60ba843060f10325a546168b371604ceffa6cec828c3a22d084a15454d786cae",
      5, 4200,
      "1/4 short-axis: embedded secondary core with east-facing branch arms at each storey; the branches read as a projecting bay window system from the road.",
      "east","north"),
    s("qtr_sa_bend_branch",
      "book:path:3778420e185740f55f65634660d1391bd797f1d86b878f3c6b37de58f36b9e18",
      5, 4500,
      "Quarter short-axis bar bent toward north then a branch arm reaches east; the bend shifts mass away from the north boundary while the branch presents the east facade to the road.",
      "east","north"),
    s("qtr_sa_notch_twist",
      "book:path:d19226a38aff5b3fee9b62ea906047c13e47183869ff72142b224ad724b499cd",
      5, 4150,
      "Quarter short-axis bar notched at the north-east corner then twisted slightly in section; the notch carves an entry recess and the twist angles the upper floors away from the neighbour.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/4 VERTICAL  (7 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("qtr_v_rotate_array_stack",
      "book:path:7bfea166963d710db6786ef373c8decbcf4047dd90becfe327d197d47c5d115f",
      5, 4600,
      "Quarter-parcel vertical tower rotated 45 degrees and stacked in groups; the diamond plan at each level produces corner conditions equally open to east and south.",
      "east","north"),
    s("qtr_v_pinch_join_array",
      "book:path:4a8c1ccd0f8f70e8dddc74aee66e2b844838d1fc2cddf3321609d761bdf3e1a1",
      5, 4400,
      "1/4 vertical bar pinched at two storey heights, joined into a second element and arrayed; the double pinch creates three distinct tower zones. East face is main access zone.",
      "east","north"),
    s("qtr_v_split_join",
      "book:path:e5f0a3c05d2c04cb085bc839dce7b70344c5ac3b61822a92290018095944286a",
      5, 4300,
      "Quarter vertical volume split then rejoined by a thin bridge at the fourth storey; the split creates a north–south gap that opens views through from east to west.",
      "east","north"),
    s("qtr_v_expand",
      "book:path:005e4cf05286b2b9cc89acf8bdc0704e8a611d51bf718ffc31498bcc7ef55046",
      5, 4550,
      "1/4 vertical bar expanded outward at upper floors to reach the legal plan limit; the expanding crown maximises upper-floor area without exceeding ground coverage. East face remains straight.",
      "east","north"),
    s("qtr_v_inscribe",
      "book:path:fb82d336564770571a0f55c1e20d70909353d22f416b222c23a160b02ebaf84f",
      5, 4200,
      "Quarter vertical bar inscribed in an ellipse producing a curved tower shaft; the ellipse plan aligns with the east access axis. North arc kept within setback.",
      "east","north"),
    s("qtr_v_embed_branch",
      "book:path:1121aa074b05a9a51d64d44c7062696d3550e5a98b035e6948c7fb62e497a029",
      5, 4100,
      "1/4 vertical: compact tower with embedded service core and two east-facing branch meeting pods at levels 3 and 5. The cantilevered pods create a distinctive stepped east elevation.",
      "east","north"),
    s("qtr_v_intersect_split",
      "book:path:b9ab99eabe125ad5fde9d3b33a28fe668e0bbd452835775b8d067f22e0c90600",
      5, 4350,
      "Quarter vertical tower intersected with an inclined plane then split; the intersected portion becomes a skew-cut top on the north face that respects the sunlight envelope.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/8 LONG_AXIS  (6 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("eighth_la_rotate_array_stack",
      "book:path:afbe2a98c31a6af69cd6fc8e955b91630a05e41cc59f1e9c118fb82d3b05787f",
      5, 3900,
      "1/8 long-axis blade rotated and stacked in a vertical array; the stacked blades form a layered screen tower read as a single mass from east. Thin plan maximises north-south air flow.",
      "east","north"),
    s("eighth_la_pack_inflate",
      "book:path:d4fcd3ceb60c3a4f3e4faee01d890dac72c5d897f4aa366e529de568f6e4fde3",
      5, 4000,
      "1/8 long-axis bar with inflated pairs packed side-by-side; the inflation creates a convex profile on east and west. East inflated face is the access elevation.",
      "east","north"),
    s("eighth_la_expand",
      "book:path:895ce0f32f2d2e05159224bf3d1c1a8d3dbd16d64d737a18a81f494ecb64a207",
      5, 4100,
      "Eighth long-axis blade expanded at upper floors to widen the plan; the expanded top is the primary occupied floor while the slender base is open colonnade. East colonnade is the entrance.",
      "east","north"),
    s("eighth_la_twist",
      "book:path:411818c1e11d8538f85491c3cbcf4871cf970f7ade5f8b736433c7c615485a85",
      5, 3950,
      "1/8 long-axis bar twisted along its vertical axis; the twist rotates the top 45 degrees from the base giving a dynamic silhouette. East face at base aligns to road.",
      "east","north"),
    s("eighth_la_embed_branch",
      "book:path:5f3271167fe252e9370cab5eb922ea564be3c7494d10abfa7d7b061efe7273df",
      5, 4050,
      "Eighth long-axis bar with embedded spine and east-branching wing at upper floors; the branch reads as a projecting canopy over the east entry. North side stays within the upper setback.",
      "east","north"),
    s("eighth_la_intersect_split",
      "book:path:c31cdf02e2b6fbbb9c171ff047d1338617a341ead8cf037fd66cef53b78c46ae",
      5, 4150,
      "1/8 long-axis: inclined intersecting volume cuts through the bar then splits; the cut appears as a diagonal slash on the east and west faces simultaneously.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/8 SHORT_AXIS  (6 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("eighth_sa_taper_array",
      "book:path:c3ebbb0f49f66dad508e86fb3c088d69cc95b56d7c3de91f7b8075d9a6d6fcb4",
      5, 3800,
      "1/8 short-axis thin strip tapered progressively and arrayed forming a wedge cascade. The cascade reads from east as an inclined staircase of rooflines.",
      "east","north"),
    s("eighth_sa_bend",
      "book:path:1dba3be4a513204213ae2c068ead61e13a54d1af472b01c8c891210355a56ba0",
      5, 3900,
      "Eighth short-axis bar bent about its long axis; the bent cross-section creates a curved lateral profile. East face of the bent bar becomes the convex entry facade.",
      "east","north"),
    s("eighth_sa_interlock",
      "book:path:d5a3caf8a8c1ccea0024eeffbbca0120705bb5a16b46507eabdde4924259cf35",
      5, 4000,
      "Two 1/8 short-axis bars interlocked at right angles; the interlocking creates a cruciform plan read from east as a plus-sign silhouette. East arm is the access branch.",
      "east","north"),
    s("eighth_sa_shear",
      "book:path:e7d979f6a9b87e1cde4a41d4b24efadb07372e151bab7518f70aa0bfa136ac38",
      5, 3950,
      "1/8 short-axis bar sheared so that upper floors slide east; the shear produces a parallelogram section and the east face overhangs the entry level creating a canopy.",
      "east","north"),
    s("eighth_sa_embed_overlap",
      "book:path:fc9f9ec3f2f9555ce600b2efc4ae42ce827e7d7b590729f07dbc7ee3a80e12da",
      5, 4100,
      "Eighth short-axis bar with embedded inner strip and overlapping east volume; the overlap zone doubles as a circulation bridge between the two elements.",
      "east","north"),
    s("eighth_sa_shift_embed",
      "book:path:029f6b79e2f17218dedb9b3b2a9c79e9f8fcc6423e61ea7d6c60d0c6a43bb93e",
      5, 4050,
      "1/8 short-axis bar with split halves embedded in one another; the result is a compact T-section that reads as a deep column from east.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 1/8 VERTICAL  (6 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("eighth_v_taper_array",
      "book:path:ac2724a0b2f7aad64c88b31ee882b7ba6a6f4259dcd213ec2aa057473f23cbc7",
      5, 3900,
      "1/8 vertical needle tapered and arrayed around the parcel perimeter; the clustered needles read as a thicket of slender towers from east. Ground level remains open between bases.",
      "east","north"),
    s("eighth_v_bend",
      "book:path:d63518fa22ddaa8f0a3bd35091bc2d1dc7f43f5d3f5f1f6f530d98959cb9d3d1",
      5, 3950,
      "Eighth vertical needle bent mid-height so the top half leans east over the road; the lean reads as a dramatic overhang from the street. North face of the bend is the tightest face.",
      "east","north"),
    s("eighth_v_notch",
      "book:path:d4ed4b6ed7e43ed48315fc7fdb2bfd29caab36bd3a8f8595df8aad12d15ab467",
      5, 4050,
      "1/8 vertical bar notched at the north-east corner creating a chamfered entry recess; the notch frames the east access and reduces the abrupt corner to the north side.",
      "east","north"),
    s("eighth_v_shear",
      "book:path:1a3f7d4acafe70b9852732b184e6e2d6ba6ebb52034d7ddbf11d84550dc587e7",
      5, 3850,
      "Eighth vertical needle sheared so upper floors slide east; the parallelogram section overhangs the entry and gives a distinctive inclined east face.",
      "east","north"),
    s("eighth_v_embed_overlap",
      "book:path:a8f4d9eadffe962faa3373da3695eb43e77654b30cf7b479ade60c62975e2c3e",
      5, 4000,
      "1/8 vertical slender volume with embedded core overlapping a secondary plinth element; the plinth grounds the needle and provides the east access.",
      "east","north"),
    s("eighth_v_branch_expand",
      "book:path:59bd226d241bdd77d3105ec7927b490118452f3b246dc200ad075b656b0515cf",
      5, 4200,
      "Eighth vertical tower with a branching east arm that expands into a wider head; the branch-head overhangs the road as an observation deck above the east entry.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 3/8 LONG_AXIS  (6 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("lshape_la_rotate_array_stack",
      "book:path:0f261048327ffa129d2cbe845d2d768378049ed625fa5eb25c9c1b534e188dbd",
      5, 5100,
      "L-shaped three-octant long-axis mass rotated and stacked; the L-rotation places the short wing at north and the long wing faces east. Access through east long wing.",
      "east","north"),
    s("lshape_la_taper_array",
      "book:path:07aba53cd27dbefa1522b5118e618772862890357c70fe5d1dd116e4c3fa5d81",
      5, 5000,
      "L-plan 3/8 long-axis volume tapered in section and arrayed horizontally; each array element is one storey shorter on the north arm.",
      "east","north"),
    s("lshape_la_bend",
      "book:path:fd4a2a48b1d285f0848d4fa63cc6ab2fc5503d36b27848d4f0a8d2ffbe7d95bf",
      5, 4900,
      "3/8 long-axis L-volume bent at the junction of its two arms; the bend opens the internal angle producing a concave east courtyard. North arm shorter per sunlight setback.",
      "east","north"),
    s("lshape_la_notch",
      "book:path:b7459f1e4435a3019e765035728dd0debb79c3d6fd9c5fe775dbe274e7e18b09",
      5, 5150,
      "L-plan long-axis 3/8 volume with notches at each internal and external corner; notches create sheltered entry recesses at the east arm tip and the internal angle.",
      "east","north"),
    s("lshape_la_overlap_expand",
      "book:path:60af486124399b3c00d56b4fdd8a931ec1d15accca7c1eba25d50c4afc838bb1",
      5, 5200,
      "3/8 long-axis: two arms of the L overlap at the corner and the overlapping section expands to span the gap; the expanded corner is a communal space visible from east.",
      "east","north"),
    s("lshape_la_bend_bend",
      "book:path:c3bfa058537ec3aea2d1f7c0a6e06b7257cd2daf2619e190b6406571975fba08",
      5, 4800,
      "3/8 long-axis L bent twice: first at mid-arm, then at the elbow; the double bend creates a gently curved L-plan that follows the parcel's oblique east boundary.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 3/8 SHORT_AXIS  (6 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("lshape_sa_rotate_array_stack",
      "book:path:888183c8ca4c194f381e4549ad6c7ac5ff89801f183785e6d8b276c878053b52",
      5, 4850,
      "L-shaped 3/8 short-axis volume rotated so the short arm faces the road and stacked; the east short arm frames an entry porch at each storey.",
      "east","north"),
    s("lshape_sa_pinch_join_array",
      "book:path:98d2810f4681f29f2fdde09c6a8cbdda31da835f632df9e6715beb656fdb34c3",
      5, 5050,
      "3/8 short-axis L pinched at the elbow, joined to a spine strip and arrayed; the pinch-and-join creates a double-L plan that opens a slot court between repetitions.",
      "east","north"),
    s("lshape_sa_extrude",
      "book:path:9674bf4eb426c7c8c19a7a8d7cda7d3466870fc684bfcf2ddc562edebc799c02",
      5, 5200,
      "3/8 short-axis L extruded vertically with varying floor heights; the taller short arm reads as a tower on the east side while the long arm is a lower podium.",
      "east","north"),
    s("lshape_sa_shift",
      "book:path:88c4d673f3a1e6a0f1c1351e01f548ad6b836c9b99433d308077a97518380175",
      5, 4950,
      "3/8 short-axis L-volume shifted east so the elbow aligns with the road setback; the shift exposes the internal angle as a semi-public recess visible from the east access.",
      "east","north"),
    s("lshape_sa_lift_carve",
      "book:path:d10f846490c2cb6c812a1bb3a7bf87fcf76105d03cfbca386fb1586e3d711a80",
      5, 4700,
      "3/8 short-axis L lifted off the ground on piloti and carved on its inner face; the lift opens the ground and the carve reveals a covered internal passage from east.",
      "east","north"),
    s("lshape_sa_embed_taper",
      "book:path:d31fb44bb285133560c00675de475238ee68bf4e76765b84f63fc748f876fb7b",
      5, 4600,
      "3/8 short-axis L-volume with embedded service core in the long arm and tapering crown on the short arm; east entry at the short arm below the taper.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# 3/8 VERTICAL  (6 sentences)
# ════════════════════════════════════════════════════════════════════════════
sentences += [
    s("lshape_v_rotate_array_stack",
      "book:path:751814e9e234ffd537e56273db75c6a8c786fc37361268ac223fca3f93aecb77",
      5, 5300,
      "L-shaped 3/8 vertical volume rotated so both arms rise equally and stacked as section cuts; the stacked L reads as a layered pinwheel from east.",
      "east","north"),
    s("lshape_v_pinch_join_array",
      "book:path:b72d90027ccb86bdfcb3afd9cf586dd88082c8b8ba3e42b67e2a4e3c36a976c3",
      5, 5000,
      "3/8 vertical L pinched at the elbow, joined with a transverse bridge, and arrayed vertically; the bridge at the elbow creates a covered horizontal connection visible from east.",
      "east","north"),
    s("lshape_v_branch",
      "book:path:8f3ac97aa2a4f587dba83aff048d84248320155f2bcb82e25456fe8e3cba2c8e",
      5, 5150,
      "3/8 vertical L with east-facing branch arm at the top of the short arm; the branch creates a T at the crown that reads as a wide roof from the road.",
      "east","north"),
    s("lshape_v_intersect",
      "book:path:9d269eb9d2380375581164bd6776ed161da606a213f0724925638af2ad30bf64",
      5, 5000,
      "3/8 vertical L intersected at its elbow with an inclined solid; the intersection cuts a diagonal chunk from the elbow creating a triangular recess at the east face.",
      "east","north"),
    s("lshape_v_bend_shift",
      "book:path:de3d27548e0e839bedf02a5d84e0a594df6c2634ca7ff4affb6b868e9d9191fd",
      5, 4950,
      "3/8 vertical L bent at the elbow then one arm shifted east; the bend and shift open the internal angle to north light while the east arm presents a straight access face.",
      "east","north"),
    s("lshape_v_intersect_intersect",
      "book:path:714a2c5a8c3512c30d7d83140787dbeae9569036d0e247a812d268051adb59b9",
      5, 5100,
      "3/8 vertical L intersected twice with perpendicular inclined volumes; the double cut creates a bevelled L silhouette. Each cut face is an inclined glazed surface on the east and north arms.",
      "east","north"),
]

# ════════════════════════════════════════════════════════════════════════════
# VERIFY COUNT
# ════════════════════════════════════════════════════════════════════════════
assert len(sentences) == 120, f"Expected 120 sentences, got {len(sentences)}"

# Check unique path IDs
pids = [s["book_composition_path_id"] for s in sentences]
assert len(set(pids)) == 120, f"Duplicate path IDs: {len(pids) - len(set(pids))} duplicates"

# Check unique names
names = [s["name"] for s in sentences]
assert len(set(names)) == 120, f"Duplicate names: {len(names) - len(set(names))} duplicates"

payload = {"sentences": sentences}

# ════════════════════════════════════════════════════════════════════════════
# VALIDATE
# ════════════════════════════════════════════════════════════════════════════
import json as _json
schema_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp23\book-author\schema.json"
with open(schema_path, encoding="utf-8") as f:
    schema = _json.load(f)

if HAS_JSONSCHEMA:
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(payload))
    if errors:
        for e in errors:
            print(f"SCHEMA ERROR: {e.message} at {list(e.path)}", flush=True)
        sys.exit(1)
    else:
        print(f"Validation PASSED. {len(sentences)} sentences, 0 schema errors.", flush=True)
else:
    print("jsonschema not available; skipping validation.", flush=True)

# ════════════════════════════════════════════════════════════════════════════
# WRITE OUTPUT
# ════════════════════════════════════════════════════════════════════════════
out_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp23.json"
with open(out_path, "w", encoding="utf-8") as f:
    _json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Written to {out_path}", flush=True)
