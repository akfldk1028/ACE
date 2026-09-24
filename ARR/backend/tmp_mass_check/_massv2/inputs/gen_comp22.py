import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# --- Build 120 sentences for book-comp22 ---
# 6 base volumes x 3 orientations = 18 groups
# 12 groups of 7 + 6 groups of 6 = 84 + 36 = 120
# Groups of 7: all 1/1 (3), all 1/16 (3), all 1/2 (3), 1/4 long+short+vertical (3) = 12
# Groups of 6: 1/4... wait: 12 groups of 7 = 84; 6 groups of 6 = 36; total = 120
# Groups of 7: 1/1-LA, 1/1-SA, 1/1-V, 1/16-LA, 1/16-SA, 1/16-V, 1/2-LA, 1/2-SA, 1/2-V, 1/4-LA, 1/4-SA, 1/4-V = 12
# Groups of 6: 3/8-LA, 3/8-SA, 3/8-V, 1/8-LA, 1/8-SA, 1/8-V = 6
# 12*7 + 6*6 = 84 + 36 = 120 ✓

SCHEMA_V = "arr.maas.dimensional_intent.v1"
DP = "preserve_physical_dimensions"
PS = "unknown"
SH = 3.8

def di(storeys, gfa):
    return {
        "schema_version": SCHEMA_V,
        "storey_count": storeys,
        "storey_height_m": SH,
        "target_gfa_m2": float(gfa),
        "delivery_policy": DP,
        "programme_status": PS
    }

def facing(access, north):
    return {"access_side": access, "north_side": north}

sentences = [

    # ===== 1/1 LONG_AXIS — 7 sentences =====
    {
        "name": "one_one_la_taper_array",
        "book_composition_path_id": "book:path:835c4e033ac1287265a1c8d1165f7e3e43ac944344396c6f7445f703622a4152",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Full-cube base stretched along the east-west road axis; array of tapered slabs steps the silhouette down toward the north boundary, placing the sunlight setback on the program's north face and maximising GFA at mid-FAR."
    },
    {
        "name": "one_one_la_split_join",
        "book_composition_path_id": "book:path:29b1dcd954546fe1c627bc7260389b8efdeca2840cf35f8ae8553db108ed6b3b",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Long-axis cube split vertically into two wings joined at ground, creating a linked pair of public-office bars that each address the east road frontage while sharing a covered lobby at the junction."
    },
    {
        "name": "one_one_la_skew_reflect_pack",
        "book_composition_path_id": "book:path:a9d8e1cbfa8f62fbfa3f4242fcde0bf95b237bbb1b83331f1e07ffb5e39d4da9",
        "dimensional_intent": di(5, 5200),
        "facing": facing("east", "north"),
        "rationale": "Skew+reflect+pack on a full-cube long-axis volume creates a mirrored pair of parallelogram-plan masses packed side-by-side; the east face remains orthogonal to the road, maximising entry clarity for the public office."
    },
    {
        "name": "one_one_la_bend_stack",
        "book_composition_path_id": "book:path:313bd71f6d3226b8490c0c477f4db56106c16ab4067da9df68011c8302a68bab",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Bend+stack on a long-axis 1/1 cube arcs the floor plates horizontally; stacked floor bands create a curved public office facade along the east road frontage with the step-up on the north side respecting the setback."
    },
    {
        "name": "one_one_la_expand_expand",
        "book_composition_path_id": "book:path:b0283c7671eee16fb0c90ce46bb04c8adc6b8c99b6e23bf6bdc76fb699c7a401",
        "dimensional_intent": di(5, 5400),
        "facing": facing("east", "north"),
        "rationale": "Expand+expand combination pushes the 1/1 long-axis body outward on two axes; the expanded mass fills the ground coverage allowance while remaining within the legal plan envelope and FAR ceiling of 6242 m2."
    },
    {
        "name": "one_one_la_bend_branch",
        "book_composition_path_id": "book:path:4af5dc92f25c4545671c2f016490dd25188edf109e3e37c0db10ccef2c9e017c",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Bend+branch combination curves the primary public-office bar then branches an upper arm toward the south; the resulting L-silhouette steps away from the north sunlight setback line while adding floor area at upper levels."
    },
    {
        "name": "one_one_la_notch_twist",
        "book_composition_path_id": "book:path:f62a02156930b83c213701e3522e5caaa828a96ed4d8f06d7d3da9e84a5af668",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Notch+twist on a 1/1 long-axis cube cuts a diagonal corner notch then twists the upper floors; the torsional top reads as a civic gesture over the east road entry, with the notch admitting light to lower levels."
    },

    # ===== 1/1 SHORT_AXIS — 7 sentences =====
    {
        "name": "one_one_sa_rotate_array_stack",
        "book_composition_path_id": "book:path:86ad02ffb9f770edfc62b73e193bc855a669cc3bdf5ec4eac1bc2d8af86a659d",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Rotate+array+stack on 1/1 short-axis generates stepped rotated plates stacked vertically; the offset footprint reads as a spiralling column of offices from the east road, tapering toward the north setback."
    },
    {
        "name": "one_one_sa_taper_array",
        "book_composition_path_id": "book:path:837530bb856a666d682a16c0062b5ddad1411f0ee6ee3bfddfeea06420c80e44",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Taper+array on a 1/1 short-axis cube creates a row of narrowing volumes perpendicular to the road; the taper steps down toward the north parcel boundary to respect the sunlight setback."
    },
    {
        "name": "one_one_sa_inflate_pack",
        "book_composition_path_id": "book:path:8233865190109741fda67523f0ffca1c967f285b166f95f563388db0dbe21f45",
        "dimensional_intent": di(5, 5100),
        "facing": facing("east", "north"),
        "rationale": "Inflate+pack on a 1/1 short-axis base swells the surface outward and packs two inflated volumes together; the curved exterior creates a distinctive landmark at the east road corner for this public office."
    },
    {
        "name": "one_one_sa_expand_nest",
        "book_composition_path_id": "book:path:c9ff63d93394d85f72c761536969f0bd7cf964514585f908a7b799f3cdd8bca6",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Expand+nest case study on a 1/1 short-axis cube grows the outer shell and nests a secondary volume within it; the gap between shells provides service corridors and the east face opens to the road."
    },
    {
        "name": "one_one_sa_bend_shift",
        "book_composition_path_id": "book:path:d616574d2c6681862f2d7bdc777bea12c63a7714abbee74eb4aebbea1949a7cc",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Bend+shift case study curves and displaces the 1/1 short-axis volume horizontally; the shift creates a canopy over the east entrance and the bent body steps away from the north boundary."
    },
    {
        "name": "one_one_sa_overlap_rotate",
        "book_composition_path_id": "book:path:8518edec2abb40ab1f2dc7322c9727a76d555f7d0c5747cd3cd5646e58de97d9",
        "dimensional_intent": di(5, 5300),
        "facing": facing("east", "north"),
        "rationale": "Overlap+rotate case study on 1/1 short-axis places two rotated masses in partial overlap; the overlapping zone becomes a shared entrance hall at east, while the rotated upper body faces away from the north setback."
    },
    {
        "name": "one_one_sa_bend_branch",
        "book_composition_path_id": "book:path:6df09c195cd503a2ac95a01608623ca2c109643ad5a3467f612a04b5f2fee761",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Bend+branch combination on 1/1 short-axis: the primary bar bends in plan and branches an upper-floor arm; the branched element oversails the east entry creating a sheltered arrival forecourt for the public office."
    },

    # ===== 1/1 VERTICAL — 7 sentences =====
    {
        "name": "one_one_v_rotate_array_stack",
        "book_composition_path_id": "book:path:d5c50daf8e8ad1792ce8405f02a5466b82b7feb7877ea2294897f7f009e9b636",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Vertical 1/1 cube with rotate+array+stack yields offset rotated floor plates; compact plan stays within the legal shrinking envelope toward the north setback, expressing each floor as a distinct rotated band."
    },
    {
        "name": "one_one_v_carve",
        "book_composition_path_id": "book:path:758545d8212c95e4daa27fdea87c87b955d5f6ceeb865740ed1f05a46df7e90d",
        "dimensional_intent": di(5, 4000),
        "facing": facing("east", "north"),
        "rationale": "Single carve operative on a vertical 1/1 cube removes a wedge from the upper north corner; the carved void directly enacts the sunlight setback form, leaving the east face fully intact for civic presence."
    },
    {
        "name": "one_one_v_lift",
        "book_composition_path_id": "book:path:8aaae0ea27a8a4f5198ab001e5372d48a405842e57564f58d151192c5414e506",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Lift operative on a 1/1 vertical cube elevates the body over a piloti ground level; the lifted mass creates a covered public forecourt on the east road side, freeing ground for civic pedestrian use."
    },
    {
        "name": "one_one_v_carve_offset",
        "book_composition_path_id": "book:path:379f62b9b6a2ae4d02fab63ea63ff5734f061416bad9ad29966a3746a3a36e44",
        "dimensional_intent": di(5, 4100),
        "facing": facing("east", "north"),
        "rationale": "Carve+offset case on a 1/1 vertical cube cuts a void and offsets the outer shell; the offset thickness creates a double-skin buffer on the north face, softening the sunlight setback transition."
    },
    {
        "name": "one_one_v_shift_shift",
        "book_composition_path_id": "book:path:9bac46a11eed36bf4ec901cdb3689dc8235e7d23ff3494a9e35f9a9acd1a7ed2",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Shift+shift combination on a 1/1 vertical cube displaces alternating floor groups in two directions; the staggered profile produces a stepped silhouette that reads as a dynamic civic landmark from the east road."
    },
    {
        "name": "one_one_v_branch_expand",
        "book_composition_path_id": "book:path:71c9c5c79d43788595de12f1c6d441a547ba4c4685a3373810da48c20b5fb6e8",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Branch+expand combination on a 1/1 vertical cube: the trunk grows an upper branch, then the branch expands outward; the expanded cap creates generous upper floor plates above the north setback limit height."
    },
    {
        "name": "one_one_v_inscribe_inscribe",
        "book_composition_path_id": "book:path:3d9f75c8ece4fc42b13c2400a50f12802bc4ac93f9e84b586c77cbab6228bb8d",
        "dimensional_intent": di(5, 3900),
        "facing": facing("east", "north"),
        "rationale": "Double-inscribe on a 1/1 vertical cube creates two successively smaller inscribed volumes; compact public-office tower with a narrow core, allowing tight legal-plan compliance at all floor levels."
    },

    # ===== 1/16 LONG_AXIS — 7 sentences =====
    {
        "name": "onesixteenth_la_rotate_array_stack",
        "book_composition_path_id": "book:path:037351037253ab21c5b18d68a1556fea24922bb30f254a25b49b8083bfab7f44",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Thin flat 1/16 slab stretched along the road axis with rotate+array+stack; each rotated stacked unit contributes minimal plan depth, building FAR through repetition while maintaining a low-profile north setback silhouette."
    },
    {
        "name": "onesixteenth_la_branch_pack_stack",
        "book_composition_path_id": "book:path:3f46fa78c93a967452b0977ee54baf0c44cfa5acf63dc47bec023377d48784a7",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Branch+pack+stack on a 1/16 long-axis slab extends lateral branches from the thin primary mass; the branching pattern increases floor area while the flat base maintains a low ground coverage footprint."
    },
    {
        "name": "onesixteenth_la_fracture",
        "book_composition_path_id": "book:path:783a604a7c4c12b89361775eba1c02cfb456d51a0b013c9891ee3d9be1726209",
        "dimensional_intent": di(5, 4200),
        "facing": facing("east", "north"),
        "rationale": "Fracture on a 1/16 long-axis slab splits the thin plate at an angle; the two leaf-like halves rotate slightly apart creating a V-plan that funnels east road pedestrian flow into the public office entry."
    },
    {
        "name": "onesixteenth_la_carve_offset",
        "book_composition_path_id": "book:path:c19c0780783c2e3076e656d47d96b848d1adafca203e849eac3b2422285fa384",
        "dimensional_intent": di(5, 4000),
        "facing": facing("east", "north"),
        "rationale": "Carve+offset on a 1/16 long-axis slab undercuts the north edge and offsets the exposed face; the offset surface provides a weather-protected overhang along the north boundary setback."
    },
    {
        "name": "onesixteenth_la_overlap_expand",
        "book_composition_path_id": "book:path:dfa111308c733bd6d7c44437a25f0b3d82c9e0c7ed53fde894de69884777972f",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Overlap+expand on a 1/16 long-axis slab: two flat plates overlap at centre and the overlapping zone expands vertically; the elevated merged section stands at the east road axis as a gateway element."
    },
    {
        "name": "onesixteenth_la_taper_taper",
        "book_composition_path_id": "book:path:6912a78fbfa2c52dd21ed332b17f8d097d217257dd287967cb1d54e80d646138",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Double-taper on a 1/16 long-axis slab tapers both ends of the thin plate; the wedge-shaped plan narrows at north for the sunlight setback and at south for privacy, leaving a wide east entry face."
    },
    {
        "name": "onesixteenth_la_branch_expand",
        "book_composition_path_id": "book:path:7c9d9f7a54671b0b8d216831f0e2c620a22bb9a340f9b4a7763248f3a8ff6f31",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Branch+expand on a 1/16 long-axis slab: the thin horizontal plate branches upward and the branch expands into a wider cap slab; the stepped section creates outdoor terraces on the south face of the upper expansion."
    },

    # ===== 1/16 SHORT_AXIS — 7 sentences =====
    {
        "name": "onesixteenth_sa_taper_array",
        "book_composition_path_id": "book:path:e588c5312a885a4b2781c9eadfac57544955b51a7b7c181b81d27cca5ee4bbc4",
        "dimensional_intent": di(5, 4300),
        "facing": facing("east", "north"),
        "rationale": "Taper+array on 1/16 short-axis thin slab creates a fan of tapered plates perpendicular to the road; the array fans out from the east entry point allowing separate access for different public-office tenants."
    },
    {
        "name": "onesixteenth_sa_skew_reflect_pack",
        "book_composition_path_id": "book:path:2ae74de58e8c53cd402ada2ecf6a61f8b287ff68e70e53d4af9601868a054481",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Skew+reflect+pack on a 1/16 short-axis slab produces two parallelogram-plan thin plates packed in mirror; the skewed plan creates an angular datum along the north setback and an acute corner entry on east."
    },
    {
        "name": "onesixteenth_sa_bend_stack",
        "book_composition_path_id": "book:path:cdd459b6f1cd78fb833729f7f704bea4c663c32a47208e79855e47f7cb57539d",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Bend+stack on a 1/16 short-axis slab bends the thin plate in cross-section and stacks bent units; the curved stack forms a barrel-vault silhouette stepping up from north to south across the parcel."
    },
    {
        "name": "onesixteenth_sa_embed_overlap",
        "book_composition_path_id": "book:path:cc63b92a4cde6a913353448a2d4e25ba511cab007c1a1f4176930de4974e5cf4",
        "dimensional_intent": di(5, 4100),
        "facing": facing("east", "north"),
        "rationale": "Embed+overlap case study on a 1/16 short-axis slab: a smaller volume is embedded in the plate, then partially overlaps beyond the north face; the overlap creates a canopy element shading the north-side upper setback zone."
    },
    {
        "name": "onesixteenth_sa_taper_taper",
        "book_composition_path_id": "book:path:5ccfeae24122a297dcdbbeac0bff19877e955fa17119f4a826b9979032ec4baa",
        "dimensional_intent": di(5, 4200),
        "facing": facing("east", "north"),
        "rationale": "Double-taper on a 1/16 short-axis slab tapers both the top and bottom of the plate cross-section; the diamond-profile thin element stands as a vertical fin against the east road, minimal in plan coverage."
    },
    {
        "name": "onesixteenth_sa_split_embed",
        "book_composition_path_id": "book:path:dac2f51b1f1a200f292155f51e005e1715cc465c01ba2167d72f20f5f9a3425a",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Split+embed combination on a 1/16 short-axis slab splits the thin plate and embeds a connector element between the two halves; the connector becomes an east-facing lobby bridging the two office wings."
    },
    {
        "name": "onesixteenth_sa_branch_expand",
        "book_composition_path_id": "book:path:96c421aab710788fc643ad4438dc4cd5659b485f562654c1406c30e71f840d01",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Branch+expand on a 1/16 short-axis slab: the thin plate branches upward at east and expands into a wider upper floor; the expanded upper volume maximises views while the thin base minimises ground coverage."
    },

    # ===== 1/16 VERTICAL — 7 sentences =====
    {
        "name": "onesixteenth_v_taper_array",
        "book_composition_path_id": "book:path:981a4ba766f2377d88870a50b61b5a197bee8b920c35d4c96cf438028b516527",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Taper+array on a 1/16 vertical element creates a cluster of tapering thin towers; the array steps the massing down from east to north, with each tapered unit reading as an independent civic finger."
    },
    {
        "name": "onesixteenth_v_split_join",
        "book_composition_path_id": "book:path:834b3e9ffd780f03f755bd518b0cd82af457bc2ad103f4419861a746491ecb9e",
        "dimensional_intent": di(5, 4200),
        "facing": facing("east", "north"),
        "rationale": "Split+join on a 1/16 vertical needle: the slender mass splits into two thin volumes rejoined at the top; the top-joined form creates a portal silhouette with a shared penthouse for the public office."
    },
    {
        "name": "onesixteenth_v_grade",
        "book_composition_path_id": "book:path:22fbda7d0af115e8dba8f349930d0c646174883c5ad0ab1bb61fd08334251e6a",
        "dimensional_intent": di(5, 4000),
        "facing": facing("east", "north"),
        "rationale": "Grade operative on a 1/16 vertical element inclines the mass to follow the parcel grade; the slanted tower leans southward placing the taller edge on the east road and the lower edge respecting the north setback."
    },
    {
        "name": "onesixteenth_v_embed_branch",
        "book_composition_path_id": "book:path:3c4f76d4af2054c786ec4a07921eaa90a5d2fb88f849a8156a79c5ae6a5e39db",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Embed+branch case on a 1/16 vertical: a secondary volume is embedded in the thin tower and a branch extends eastward; the branch provides a covered external landing at each floor facing the road."
    },
    {
        "name": "onesixteenth_v_intersect_intersect",
        "book_composition_path_id": "book:path:780ec58ce2df1f081db26eaa640d04cd3e88bdce58c4165141e42be1cab13087",
        "dimensional_intent": di(5, 3900),
        "facing": facing("east", "north"),
        "rationale": "Double-intersect combination on a 1/16 vertical element takes the boolean intersection of three volumes; the residual shard-like form is naturally compact and angular, suitable as a slender civic landmark."
    },
    {
        "name": "onesixteenth_v_bend_bend",
        "book_composition_path_id": "book:path:5632df19bcd161dbbb08e120054c9dd8d48a66ebd47745e370787c0c2a904173",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Bend+bend on a 1/16 vertical element applies two successive bends in perpendicular axes; the doubly-curved slender form creates a flowing tower silhouette seen from the east road intersection."
    },
    {
        "name": "onesixteenth_v_expand_shift",
        "book_composition_path_id": "book:path:9eddca0a9fdc31c0f3acd215c369bf5af1e6ce0c1dc77295f8871a0e8ea93be8",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Expand+shift on a 1/16 vertical element expands the mass at its midsection and shifts the upper half laterally; the resulting stepped thin tower is taller on the east and steps back on the north setback side."
    },

    # ===== 1/2 LONG_AXIS — 7 sentences =====
    {
        "name": "half_la_rotate_array_stack",
        "book_composition_path_id": "book:path:f36adc06b768050e4678ce63028ca878c0608f9be2ac6149e0735cf0130471f8",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Half-cube bar stretched along the road axis with rotate+array+stack; offset rotated plates accumulate over the long east-west axis, creating a kinetic facade progression from east to west that peaks at mid-parcel."
    },
    {
        "name": "half_la_expand_reflect",
        "book_composition_path_id": "book:path:650c425e6b37ac387a1259828d47ec9c37129ae9ca84f09194578174ce4c715e",
        "dimensional_intent": di(5, 5400),
        "facing": facing("east", "north"),
        "rationale": "Expand+reflect on a 1/2 long-axis bar mirrors the expanded bar across the north-south axis; the reflected pair flanks a central east-facing plaza and together fill the FAR target for this public office parcel."
    },
    {
        "name": "half_la_compress",
        "book_composition_path_id": "book:path:095a6052c5e08158c2d74b79da85889eb5566136db0df593c2e215855618d7c2",
        "dimensional_intent": di(4, 4000),
        "facing": facing("east", "north"),
        "rationale": "Compress on a 1/2 long-axis bar reduces the section depth; 4 storeys used because the compressed bar produces generous floor-plate widths that satisfy programme area without reaching the 5-storey ceiling, earning lower density by maximising daylighting depth."
    },
    {
        "name": "half_la_embed_branch",
        "book_composition_path_id": "book:path:dc057ea5c00fa7f7a5f5ba0448dbc8f2557a45b06da7855e05f2576999c017ca",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Embed+branch case on a 1/2 long-axis bar: a secondary volume is embedded within the bar and a branch arm extends outward on the east face; the branch forms a canopy over the public entry zone from the road."
    },
    {
        "name": "half_la_lift_carve",
        "book_composition_path_id": "book:path:6cfd53c1e96d55295676fd4bf320486f3359a3eed7fc3cc093dffe22cc50af7d",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Lift+carve case on a 1/2 long-axis bar: the bar is lifted on piloti and the north corner is carved to comply with the sunlight setback; the carved piloti-level void provides a covered public passage along the east road."
    },
    {
        "name": "half_la_intersect_intersect",
        "book_composition_path_id": "book:path:60e83cbb033141cf83df15aebcd8e4a4978975fb99288a7747d93f45e6543a38",
        "dimensional_intent": di(5, 4300),
        "facing": facing("east", "north"),
        "rationale": "Double-intersect on a 1/2 long-axis bar takes the geometry remaining after two boolean operations; the residual angular form is compact, with an acute east-facing corner marking the public office entry from the road."
    },
    {
        "name": "half_la_embed_taper",
        "book_composition_path_id": "book:path:cafc6e6f6facc490cfaf61fd12ba39f8bfa18feeac06fc2e1a4a2d7a402e1738",
        "dimensional_intent": di(5, 5100),
        "facing": facing("east", "north"),
        "rationale": "Embed+taper combination on a 1/2 long-axis bar: a volume is embedded in the bar, then the composite form tapers toward the north boundary; the taper directly responds to the legal plan reduction at upper floors."
    },

    # ===== 1/2 SHORT_AXIS — 7 sentences =====
    {
        "name": "half_sa_rotate_array_stack",
        "book_composition_path_id": "book:path:01e65ed161147014b0705638b965c6c20eb7644d58cdadddf6c8f90ce8cbe456",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Rotate+array+stack on a 1/2 short-axis bar runs perpendicular to the road with offset rotated floor bands; the stacked array provides disciplined office floor plates while the rotation creates diagonal facade interest on the east face."
    },
    {
        "name": "half_sa_inflate_pack",
        "book_composition_path_id": "book:path:400fcb0bdac9a093ef6d421e65046a6d3f6be2f1f77f033d84c56c9aa6990a6f",
        "dimensional_intent": di(5, 5200),
        "facing": facing("east", "north"),
        "rationale": "Inflate+pack on a 1/2 short-axis bar inflates two packed bars that run north-south from the east road; the bulging plan section widens at the middle floors giving generous public-office areas at the optimal height levels."
    },
    {
        "name": "half_sa_pinch",
        "book_composition_path_id": "book:path:919eae5750b346ab62836d86ca358c02fb74e941319fab63f912e0c328aa3587",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Single pinch operative on a 1/2 short-axis bar waists the cross-section at mid-height; the hourglass section creates visually lighter upper floors while maintaining structural continuity, ideal for a public-office civic gesture."
    },
    {
        "name": "half_sa_lift_carve",
        "book_composition_path_id": "book:path:023d470b4f52b5db1eb012541e89a092b91f1b209fb257ab4ee6f1ae4dd73668",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Lift+carve on a 1/2 short-axis bar: the bar is raised on columns and the upper north corner is carved; the carved underside forms a soffit over the north setback zone and the piloti level provides covered civic space."
    },
    {
        "name": "half_sa_branch_branch",
        "book_composition_path_id": "book:path:c5486104920e558b4da3836dbb2fda21e36d9ac1404888c139b5125f24d73556",
        "dimensional_intent": di(5, 5300),
        "facing": facing("east", "north"),
        "rationale": "Branch+branch on a 1/2 short-axis bar grows two separate arms from the primary mass; the tri-part form creates an E-plan with the east arm closest to the road and the two side arms providing additional floor area within FAR."
    },
    {
        "name": "half_sa_taper_bend",
        "book_composition_path_id": "book:path:52df13d14b56342a36dc791abdc6978bc29f425b781786edbb48a69548a4c064",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Taper+bend combination on a 1/2 short-axis bar tapers the north end to comply with the setback and bends the bar slightly in plan; the bent-taper form creates a curved public office face seen from the east road."
    },
    {
        "name": "half_sa_shift_notch",
        "book_composition_path_id": "book:path:8f4b1eac9b1de6e74750a70edfcf45b4471d0b48fcffead874a22e98fb62c99e",
        "dimensional_intent": di(5, 4200),
        "facing": facing("east", "north"),
        "rationale": "Shift+notch on a 1/2 short-axis bar displaces the upper half laterally and cuts a corner notch; the shift cantilever over the east entry creates a covered arrival space and the notch provides a light slot to lower floors."
    },

    # ===== 1/2 VERTICAL — 7 sentences =====
    {
        "name": "half_v_rotate_array_stack",
        "book_composition_path_id": "book:path:9296d93c696e288a355d3e87156181959d3680c6e03db08b34df9094adc55c4b",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Rotate+array+stack on a 1/2 vertical half-cube generates a tower of offset rotating half-plates; the diminishing rotation steps the mass away from the north boundary at each floor level in response to the legal plan limits."
    },
    {
        "name": "half_v_inflate",
        "book_composition_path_id": "book:path:df73541381e9987c45f15ce2b6d1f70f07fa852b820831eaf25d25c934e9e0ce",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Inflate operative on a 1/2 vertical half-cube swells the mass into a rounded barrel form; the inflated tower creates a biomorphic civic landmark visible from the east road approach with a distinctive circular profile."
    },
    {
        "name": "half_v_puncture",
        "book_composition_path_id": "book:path:7785ad461681bc58505a87103376927f34487183d525483ce1b5e728df72ab7f",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Puncture operative on a 1/2 vertical half-cube passes a void through the tower body horizontally; the puncture creates a through-frame at mid-height, framing views across the site and admitting light to the centre of the floor plate."
    },
    {
        "name": "half_v_taper",
        "book_composition_path_id": "book:path:968888dce8709b83e24eb39066d7acb8daba538275a07783472261c5ec367e92",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Single taper on a 1/2 vertical half-cube tapers the tower toward the top; the tapered crown precisely matches the diminishing legal plan at each floor level above 9 m, ensuring full use of the statutory envelope."
    },
    {
        "name": "half_v_embed_overlap",
        "book_composition_path_id": "book:path:5a055e27c9d8ff6f664a9a5a3802d910e8e8d3f2f52749a394079528cd36434d",
        "dimensional_intent": di(5, 5100),
        "facing": facing("east", "north"),
        "rationale": "Embed+overlap case on a 1/2 vertical half-cube: a secondary tower is embedded and partially overlaps beyond the primary volume; the overlapping upper zone creates a wide penthouse level above the main tower body."
    },
    {
        "name": "half_v_split_split",
        "book_composition_path_id": "book:path:4fd62f3988ce66064bee4d16735489d8c6807ec28b5d64551cc5af34aa20a26b",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "south"),
        "rationale": "Split+split on a 1/2 vertical half-cube divides the tower twice creating four distinct vertical wings; south-facing orientation for north_side places tallest elements toward the sunnier south face and setback steps on the north."
    },
    {
        "name": "half_v_taper_bend",
        "book_composition_path_id": "book:path:561b51e770b12924541cc204da4e46f94b59da420975281af113b36ec66800a8",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Taper+bend on a 1/2 vertical half-cube: the tower tapers toward its top and bends slightly in plan; the bent taper leans the crown away from the north setback while presenting a full-height east face to the road."
    },

    # ===== 1/4 LONG_AXIS — 7 sentences =====
    {
        "name": "quarter_la_taper_array",
        "book_composition_path_id": "book:path:790a467578fcc705007686266f02cb4701b4b59efa251fc1464a1f9dffde6aaa",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Quarter-cube bar along the road axis with taper+array: the elongated bar is repeated in a tapered array stepping south from the east road, creating a cascade of office bars with declining height toward the interior of the block."
    },
    {
        "name": "quarter_la_skew_reflect_pack",
        "book_composition_path_id": "book:path:bc2791c67b87448a12afe76912dada641c9c7476acd849b019854100f5cfa53f",
        "dimensional_intent": di(5, 5200),
        "facing": facing("east", "north"),
        "rationale": "Skew+reflect+pack on a 1/4 long-axis bar creates a symmetric pair of parallelogram bars packed along the parcel; the mirrored skew plan creates diagonal views from the east road into the shared central corridor."
    },
    {
        "name": "quarter_la_inflate",
        "book_composition_path_id": "book:path:ed3f867ef223f976277ed32aef1e7c387d4ff556749be3bd5c1f80e9d2d0719d",
        "dimensional_intent": di(5, 5100),
        "facing": facing("east", "north"),
        "rationale": "Inflate operative on a 1/4 long-axis bar swells the elongated cross-section into a barrel vault form; the inflated long bar makes a distinctive horizontal datum along the east road frontage for the public office programme."
    },
    {
        "name": "quarter_la_carve_offset",
        "book_composition_path_id": "book:path:1dfd946cad0ff2dcd3c13fb01a05cd92cccfdb529f0008f4a1fa29d0db50aef7",
        "dimensional_intent": di(5, 4200),
        "facing": facing("east", "north"),
        "rationale": "Carve+offset on a 1/4 long-axis bar removes the north top corner and offsets the surface inward; the carved offset directly realises the legal plan reduction at upper floors, leaving additional open roof terrace."
    },
    {
        "name": "quarter_la_embed_overlap",
        "book_composition_path_id": "book:path:ed4083cf1be10bb7eb3d8751420a5e233b61f5315adebdbbb30a0eeb344c9ebb",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Embed+overlap case on a 1/4 long-axis bar: secondary volume embedded then overlaps at east end; the overlapping zone creates a wider end element at the east road frontage that serves as the main civic entrance hall."
    },
    {
        "name": "quarter_la_taper_bend",
        "book_composition_path_id": "book:path:d3c60dc91e0ba014c6638d65097a266b8980b2fbb095f79e0f55c10b03b7da79",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Taper+bend on a 1/4 long-axis bar tapers one end and bends the bar gently in plan; the tapering narrow end faces north to respect the sunlight setback and the bent plan follows the slight angle of the east road alignment."
    },
    {
        "name": "quarter_la_shift_notch",
        "book_composition_path_id": "book:path:1daab4675f5edc368e9ea312e316c44b82c1afdaee77b24e634ddd1b7e5e08b8",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Shift+notch on a 1/4 long-axis bar: the upper half shifts eastward and a corner notch is cut at the north-east; the shift cantilever faces the east road and the notch admits sky light to the notched corner interior."
    },

    # ===== 1/4 SHORT_AXIS — 7 sentences =====
    {
        "name": "quarter_sa_taper_array",
        "book_composition_path_id": "book:path:9a192f2bcc9ac54810a0ffb4dc9425b81367f26710127b15807431a6a8bf5eba",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Taper+array on a 1/4 short-axis bar arrays perpendicular north-south bars in a tapered sequence; the bars narrow toward the north boundary and widen at the east road entry, directing pedestrian flow into the public office."
    },
    {
        "name": "quarter_sa_inflate_pack",
        "book_composition_path_id": "book:path:bd25c4af1596654b50526cb120b81d0db32a81cbc247ff8b88d4c32c2076d6ff",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Inflate+pack on a 1/4 short-axis bar: two bars are inflated and packed north-south; the paired inflated bars create generous cross-section office floors that run perpendicular from the east road into the parcel depth."
    },
    {
        "name": "quarter_sa_notch_twist",
        "book_composition_path_id": "book:path:40b5bc1c94bf223bf7b000a9c17175f0eed0e1c18dc39801a052238b0fbce38b",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Notch+twist on a 1/4 short-axis bar cuts a diagonal notch at the north-east corner and twists the upper floors; the twisted upper section spirals away from the north boundary while the notch creates a rooftop terrace."
    },
    {
        "name": "quarter_sa_embed_branch",
        "book_composition_path_id": "book:path:537a14cb2a19df1de97ddf86538148e0a785ae7739aff4c546ac2e4fa116e109",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Embed+branch case on a 1/4 short-axis bar embeds a volume at the east end and branches a perpendicular arm; the branched arm adds floor area toward the south without encroaching on the north setback zone."
    },
    {
        "name": "quarter_sa_overlap_rotate",
        "book_composition_path_id": "book:path:cbef69d3f0c7a0284e938fb4d8aa3740b36d329c929d4daf010241d3299f08af",
        "dimensional_intent": di(5, 5100),
        "facing": facing("east", "north"),
        "rationale": "Overlap+rotate case on a 1/4 short-axis bar overlaps two rotated bars in partial intersection; the overlapping union creates a crossing volume whose east face provides two distinct public entry directions."
    },
    {
        "name": "quarter_sa_bend_branch",
        "book_composition_path_id": "book:path:cc6fb774e00e7c833593f1498506b7fc378b1cbab706b995023e7bf977d9f169",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Bend+branch on a 1/4 short-axis bar bends the north-south running bar and branches an arm; the branched arm extends eastward to meet the road while the bent bar runs diagonally toward the south, increasing floor area within FAR."
    },
    {
        "name": "quarter_sa_intersect_split",
        "book_composition_path_id": "book:path:018213ebf1ae903f3813d76249846d05fbaac75f18d5010758ff9f31ae364c49",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Intersect+split on a 1/4 short-axis bar: the boolean intersection produces a trimmed shard which is then split; the two shard fragments create a paired angular form with a sharp east-facing datum visible from the road."
    },

    # ===== 1/4 VERTICAL — 7 sentences =====
    {
        "name": "quarter_v_rotate_array_stack",
        "book_composition_path_id": "book:path:5e2b40fb07c8b9f78463c80a1bd23d2dad3b5d726adc357ee2047cc70f1efbc9",
        "dimensional_intent": di(5, 4300),
        "facing": facing("east", "north"),
        "rationale": "Rotate+array+stack on a 1/4 vertical quarter-cube: compact rotating footprints stack to create a spiralling tower that stays within the diminishing legal plan at each floor level while expressing civic identity."
    },
    {
        "name": "quarter_v_expand",
        "book_composition_path_id": "book:path:c6f064a61a8a3c76c3a8cb60c3dd124b55b42e265d43991fcd44a15513acb0e8",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Expand operative on a 1/4 vertical quarter-cube inflates the compact form to its coverage limit; the expanded base captures maximum ground-floor public lobby area while the upper tower remains within the legal plan envelope."
    },
    {
        "name": "quarter_v_twist",
        "book_composition_path_id": "book:path:888c3bb180ba2ba1c00426934c51a299d2a56ea458a498ed671f2f2116f5304a",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Twist operative on a 1/4 vertical quarter-cube rotates floor plates progressively; the twisted tower produces a dynamic civic form that responds to the oblique road alignment with each floor presenting a slightly different east face."
    },
    {
        "name": "quarter_v_embed_embed",
        "book_composition_path_id": "book:path:dd6b56e7a3487c4d0b0bf0a727d1b475bf09091593d35dd957845c4ca8d1dbfa",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Double-embed on a 1/4 vertical quarter-cube creates two concentric inscribed voids; the nested layering of the compact tower produces a lantern-like cross-section with light penetrating through concentric recesses."
    },
    {
        "name": "quarter_v_intersect_split",
        "book_composition_path_id": "book:path:5d77fc1a1a487f95901ff35a5c1e338cd3440826684510f5e561eb33ef281ae9",
        "dimensional_intent": di(5, 4200),
        "facing": facing("east", "north"),
        "rationale": "Intersect+split on a 1/4 vertical quarter-cube: the boolean remnant of two intersecting compact cubes is split; the resulting angular pair of shard volumes creates a dramatic split tower visible from the east road approach."
    },
    {
        "name": "quarter_v_notch_twist",
        "book_composition_path_id": "book:path:f2e530baddbdc9f8fb6d3be28890259f2db3aa55a94a5ccb5fa41c16fe513b42",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Notch+twist on a 1/4 vertical quarter-cube cuts a diagonal notch at the north face and twists the body; the twisted upper floors spiral above the setback line while the notch creates a sky-lit recess at the north-east corner."
    },
    {
        "name": "quarter_v_bend_branch",
        "book_composition_path_id": "book:path:4dc44dba8a2b06e91106ea2536e00e4faf389eb524bdd21b233b42737f572244",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Bend+branch on a 1/4 vertical quarter-cube curves the compact tower and extends a branch at upper floors; the branched upper arm creates an overhang over the east entry, giving the public office a distinctive gateway element."
    },

    # ===== 3/8 LONG_AXIS — 6 sentences =====
    {
        "name": "threeeighths_la_taper_array",
        "book_composition_path_id": "book:path:49e5f139a14c828e9835224acee94efa8f7412390be1f4890d3905a7a4624d71",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "L-shaped 3/8 cube along the road axis with taper+array; the three-octant L naturally engages the east and south faces of the parcel with the tapered array stepping the north wing down to the setback limit."
    },
    {
        "name": "threeeighths_la_bend",
        "book_composition_path_id": "book:path:36b53ed10f13182a9a3a33a70b011a9ce00e485b45f404e506befec81f06ac61",
        "dimensional_intent": di(5, 5300),
        "facing": facing("east", "north"),
        "rationale": "Single bend on a 3/8 long-axis L-cube curves the longer arm of the L; the bent arm wraps around the north parcel corner while the shorter arm meets the east road, forming a crescent plan for the public office."
    },
    {
        "name": "threeeighths_la_carve_offset",
        "book_composition_path_id": "book:path:471075d52cdfbce185c8de8f7321f0d205b12aff103b69bbf5a3c898bf0c9856",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Carve+offset on a 3/8 long-axis L: the north arm's upper corner is carved and the exposed face is offset inward; the carved setback zone becomes a stepped rooftop terrace on the public office's north wing."
    },
    {
        "name": "threeeighths_la_shift_shift",
        "book_composition_path_id": "book:path:c69fcd90ef1086bde665304051694723faded4c7d7291763d7399a880b706dc1",
        "dimensional_intent": di(5, 5200),
        "facing": facing("east", "north"),
        "rationale": "Shift+shift combination on a 3/8 long-axis L displaces both arms of the L in opposite directions; the double-shifted L creates a dynamic stepped elevation from the east road with strong horizontal datum lines."
    },
    {
        "name": "threeeighths_la_split_embed",
        "book_composition_path_id": "book:path:214a90bb61f8c223e8f11053a2dc2e9b838c3753ce6e9ff4d078e2701914cb4b",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Split+embed on a 3/8 long-axis L splits the L-corner and embeds a connector; the embedded connector between the two L-arms creates a climate-controlled link building at the corner that serves as the shared main entrance."
    },
    {
        "name": "threeeighths_la_branch_expand",
        "book_composition_path_id": "book:path:a32589449a40b20890cded66bd517b891b95a256844d8adeb01552e84aa5bcb6",
        "dimensional_intent": di(5, 5500),
        "facing": facing("east", "north"),
        "rationale": "Branch+expand on a 3/8 long-axis L: the longer arm branches a secondary element and the branch expands to match the main L-arm width; the expanded branch cap creates a top-floor panoramic public space over the east road."
    },

    # ===== 3/8 SHORT_AXIS — 6 sentences =====
    {
        "name": "threeeighths_sa_rotate_array_stack",
        "book_composition_path_id": "book:path:0d757e0c5ea55814c0df7fe9e1109fddeae5e49c4dd5c789f677941551c53913",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Rotate+array+stack on a 3/8 short-axis L-cube: the L is rotated and stacked in offset array; east arm of each L faces the road while the north arm steps with the setback, producing a spiralling cluster of L-shaped floor plates."
    },
    {
        "name": "threeeighths_sa_split_join",
        "book_composition_path_id": "book:path:4acd81da87fd627f779c53e5627f441e4d6d0d4b1b31a418386f37b212aadd4a",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Split+join on a 3/8 short-axis L: one arm of the L is split and re-joined at an offset; the offset re-join creates a cascading section on the north face that progressively steps away from the north boundary at each floor."
    },
    {
        "name": "threeeighths_sa_branch",
        "book_composition_path_id": "book:path:9726e06796da5b3803c1418abffb4c5cc85f7f7c5f2d9cdc82a662e16d500f2e",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Single branch on a 3/8 short-axis L extends an arm from the L-body toward the east road; the branch becomes the primary entry vestibule that projects from the L and greets the east road frontage directly."
    },
    {
        "name": "threeeighths_sa_bend_bend",
        "book_composition_path_id": "book:path:6218c7cfb3f993e0f84cdc1ca907717c1ad1dd933c83e028068754c28bed8e43",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Bend+bend on a 3/8 short-axis L curves both arms of the L in sequence; the doubly-curved L creates a fluid horseshoe plan with the open end facing east, framing an arrival courtyard off the road frontage."
    },
    {
        "name": "threeeighths_sa_embed_taper",
        "book_composition_path_id": "book:path:5974c311e2bfec48ce02a304084bedf528ca555240843363851b3a031bb5822a",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Embed+taper on a 3/8 short-axis L embeds a core volume and tapers the north arm to the setback limit; the tapered embedded north arm creates a wedge-shaped floor plate at upper levels fitting the legal plan reduction precisely."
    },
    {
        "name": "threeeighths_sa_expand_shift",
        "book_composition_path_id": "book:path:c421a07e7aa7d78de03c308060a8f4f930ce2ed9aa19bdc4dcca1e7d3dd3ae6d",
        "dimensional_intent": di(5, 5300),
        "facing": facing("east", "north"),
        "rationale": "Expand+shift on a 3/8 short-axis L grows the L mass then shifts one arm laterally; the shifted arm creates a dynamic stagger between the two L wings on the east road face, expressing the public-office programme through its form."
    },

    # ===== 3/8 VERTICAL — 6 sentences =====
    {
        "name": "threeeighths_v_rotate_array_stack",
        "book_composition_path_id": "book:path:a646b2d22e3b103d7d79fcda7b889faa79020241d88ab47d9d48803aa13c083b",
        "dimensional_intent": di(5, 4700),
        "facing": facing("east", "north"),
        "rationale": "Rotate+array+stack on a 3/8 vertical L-cube stacks offset-rotated L-plan floors; the rotating L-silhouette wraps progressively away from the north setback as it rises, reading as a helical civic tower from east."
    },
    {
        "name": "threeeighths_v_case_bend_shift",
        "book_composition_path_id": "book:path:4985cda3d0388fbe65018b05a4f42026db06a4fc4058707507e49e925440b17a",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Bend+shift case on a 3/8 vertical L: the L-tower bends in plan and one arm shifts laterally; the bent-shifted L creates a flowing multi-directional tower that subtly tracks the parcel's geometry rather than a rigid rectangular grid."
    },
    {
        "name": "threeeighths_v_lift_carve",
        "book_composition_path_id": "book:path:d8b168918003f99901d4df19d59163386d533870904fcbd8c89203cd116acf80",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Lift+carve case on a 3/8 vertical L: the L is raised on piloti and the north upper corner carved; the lifted L frames a covered public forecourt at ground facing east while the carved north crown reduces the shadow on the north neighbour."
    },
    {
        "name": "threeeighths_v_intersect_intersect",
        "book_composition_path_id": "book:path:74596ca5ac7e73e32d33125a94275a8d01f112dde49dc11bd3313909543d3ebf",
        "dimensional_intent": di(5, 4200),
        "facing": facing("east", "north"),
        "rationale": "Double-intersect on a 3/8 vertical L: successive boolean operations on the L-tower produce an angular crystalline residual; the resulting shard-tower form is minimal in plan yet civic in vertical presence from the east road."
    },
    {
        "name": "threeeighths_v_notch_notch",
        "book_composition_path_id": "book:path:8f1594f4a30f730c013e696b30ba8ac393e3f5715d2e45dc1fee2174e88a74f7",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Notch+notch on a 3/8 vertical L cuts two corner notches: one at the re-entrant L corner and one at the north face; the dual notches define sky-lit recesses at the L-corner and at the sunlight setback boundary respectively."
    },
    {
        "name": "threeeighths_v_expand_shift",
        "book_composition_path_id": "book:path:954b49cffd1559715adcf2a2edd74c232230166f806cb05916495104dba35b99",
        "dimensional_intent": di(5, 5200),
        "facing": facing("east", "north"),
        "rationale": "Expand+shift on a 3/8 vertical L grows the L mass and shifts the north arm upward; the expanded shifted north arm provides wider upper-floor plates above the setback zone height, maximising FAR within the legal plan limits."
    },

    # ===== 1/8 LONG_AXIS — 6 sentences =====
    {
        "name": "eighth_la_rotate_array_stack",
        "book_composition_path_id": "book:path:3a45ea7c478814bc86949fca4d6d1ec0d1aaf4dee5e495a44d9fae4e020adb80",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Thin 1/8 long-axis bar with rotate+array+stack: rotated bar units are stacked along the east-west axis creating a ribbed horizontal datum that reads as a low public-office building parallel to the road."
    },
    {
        "name": "eighth_la_expand_reflect",
        "book_composition_path_id": "book:path:be5feb5662787264faf9b26f7199b19a61c08dbe91508327623d4c31e8a3636f",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Expand+reflect on a 1/8 long-axis bar mirrors the thin bar to create a symmetric pair flanking a central courtyard; the east-facing open court between the two bars provides a sheltered civic arrival space off the road."
    },
    {
        "name": "eighth_la_expand",
        "book_composition_path_id": "book:path:f51d9773663125af13ae77b7eaa89dc26c56897f3395d922aa8799fce446e83b",
        "dimensional_intent": di(5, 5100),
        "facing": facing("east", "north"),
        "rationale": "Expand operative on a 1/8 long-axis bar grows the thin cross-section to the coverage limit; the expanded bar fills the legal plan while its east face provides a broad continuous public-office street facade."
    },
    {
        "name": "eighth_la_embed_overlap",
        "book_composition_path_id": "book:path:46aa461c7627ff2ece5d57ff05a0614ce9af161b67e311834e158f7b520ae958",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Embed+overlap on a 1/8 long-axis bar embeds a secondary volume in the thin bar and extends it to overlap at the east end; the overlapping east element forms a wider entry pavilion for the public office visible from the road."
    },
    {
        "name": "eighth_la_intersect_split",
        "book_composition_path_id": "book:path:012d01da32002b4134cad9e51332ac42f9ea9625bcf0cb27e606f1495efef311",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Intersect+split on a 1/8 long-axis bar: the thin bar is intersected with a diagonal volume and then split; the resulting chevron-shaped pair of thin elements faces east with a V-shaped open court catching road light."
    },
    {
        "name": "eighth_la_notch_twist",
        "book_composition_path_id": "book:path:f9166ad4064659d11081f6d6649e7d9775dc432753de26467545653a8d501475",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Notch+twist on a 1/8 long-axis bar cuts a notch at the north end and twists the bar along its length; the twisted thin bar creates a kinetic horizontal form that progressively turns its east face toward the north sunlight."
    },

    # ===== 1/8 SHORT_AXIS — 6 sentences =====
    {
        "name": "eighth_sa_rotate_array_stack",
        "book_composition_path_id": "book:path:9075cc6907cf39b6e2e5af62503064fc91c784e0aaa9e9edfc4081138f39c46e",
        "dimensional_intent": di(5, 4600),
        "facing": facing("east", "north"),
        "rationale": "Rotate+array+stack on a 1/8 short-axis bar creates thin perpendicular-to-road elements stacked in rotation; the rotating short bars create a combed facade pattern on the east road frontage of the public office."
    },
    {
        "name": "eighth_sa_expand_reflect",
        "book_composition_path_id": "book:path:7971eaa902036c10d35dd1bdb78713a7d5b56816e0b601a97653232bcf9abe4e",
        "dimensional_intent": di(5, 4800),
        "facing": facing("east", "north"),
        "rationale": "Expand+reflect on a 1/8 short-axis bar mirrors the thin bar about the east-west axis creating a symmetric pair perpendicular to the road; the pair frames a central east-facing forecourt between the two north-south bars."
    },
    {
        "name": "eighth_sa_bend",
        "book_composition_path_id": "book:path:40db18ffb60d8b0afc8b125076418bc71b76dc09de493b600563526a23e6dc07",
        "dimensional_intent": di(5, 4400),
        "facing": facing("east", "north"),
        "rationale": "Single bend on a 1/8 short-axis bar curves the thin perpendicular-to-road bar in plan; the bent bar wraps around the parcel north corner, enacting the setback in form rather than by subtraction."
    },
    {
        "name": "eighth_sa_carve_offset",
        "book_composition_path_id": "book:path:e172d7f8e141e3184da20083b03079e881e50d5cc76f0fc1fa980e166af20655",
        "dimensional_intent": di(5, 4000),
        "facing": facing("east", "north"),
        "rationale": "Carve+offset case on a 1/8 short-axis bar carves the north upper face and offsets the carved surface; the offset carved face creates a stepped section at the north boundary precisely following the legal plan reduction at each storey."
    },
    {
        "name": "eighth_sa_split_embed",
        "book_composition_path_id": "book:path:b4942133e843bc11162f8fe34dee061345f367d043e9199e669deb0462d31930",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Split+embed on a 1/8 short-axis bar splits the thin bar and embeds a connecting volume; the connector becomes the east-facing lobby linking two parallel thin office bars perpendicular to the road."
    },
    {
        "name": "eighth_sa_branch_expand",
        "book_composition_path_id": "book:path:2558eec51fc0563e9af3b6f62f0cad1eddd2d0e848be18e647b5b15bceafce84",
        "dimensional_intent": di(5, 5100),
        "facing": facing("east", "north"),
        "rationale": "Branch+expand on a 1/8 short-axis bar: the thin bar branches an upper element and the branch expands into a wider cap; the expanded cap overhangs the thin bar below creating a T-section public-office facade on the east road."
    },

    # ===== 1/8 VERTICAL — 6 sentences =====
    {
        "name": "eighth_v_taper_array",
        "book_composition_path_id": "book:path:5a75928c89794e5f8deec03d9ef1d8d9c8346a93b6f8f2ca007458bdc57d1d6c",
        "dimensional_intent": di(5, 4300),
        "facing": facing("east", "north"),
        "rationale": "Taper+array on a 1/8 vertical thin bar creates a row of tapering slim towers; the array of diminishing vertical elements reads as a colonnade of civic markers along the east road edge of the parcel."
    },
    {
        "name": "eighth_v_bend_stack",
        "book_composition_path_id": "book:path:b2df0b65415afd2a068aff10ed30626675acc5706c2b1327e2cbb5c09ffcbb02",
        "dimensional_intent": di(5, 4500),
        "facing": facing("east", "north"),
        "rationale": "Bend+stack on a 1/8 vertical bar bends the slim element and stacks bent units; the curved stacked forms create a wave-like vertical arrangement of thin public-office bars with each unit's east face tilted to catch road light."
    },
    {
        "name": "eighth_v_interlock",
        "book_composition_path_id": "book:path:b9e9dd16f235a5cee0690f8353974acb47d6196fd31b95942ca6adec0d3533e1",
        "dimensional_intent": di(5, 4900),
        "facing": facing("east", "north"),
        "rationale": "Interlock on a 1/8 vertical bar interlocks two slim tower elements that cross each other; the crossing pair creates an X-plan tower that expresses structural tension as civic identity from the east road."
    },
    {
        "name": "eighth_v_carve_offset",
        "book_composition_path_id": "book:path:3aa51805e0ba719158b918a94b62caf83b46dd5c8e23435c5c11007a23568a51",
        "dimensional_intent": di(5, 4000),
        "facing": facing("east", "north"),
        "rationale": "Carve+offset case on a 1/8 vertical bar carves the upper north face and offsets inward; on a slender tower this produces a setback cap that precisely matches the legal plan limit at the top floor level."
    },
    {
        "name": "eighth_v_inscribe_inscribe",
        "book_composition_path_id": "book:path:9a08ef4d05f6d1a43b47557c93ba155509425291c93331986b3f18928d28ecb3",
        "dimensional_intent": di(5, 3900),
        "facing": facing("east", "north"),
        "rationale": "Double-inscribe on a 1/8 vertical: two successive inscribed forms within the slim tower create a lantern cross-section; the nested recesses admit light to the slender tower's core as a defining feature of the public office."
    },
    {
        "name": "eighth_v_branch_expand",
        "book_composition_path_id": "book:path:d82230702beaad495279c69b54e81dd8fc858b2a68a8d779b69db412df701c47",
        "dimensional_intent": di(5, 5000),
        "facing": facing("east", "north"),
        "rationale": "Branch+expand on a 1/8 vertical bar: the slim tower branches a horizontal arm at the top floor and the arm expands to a wider slab; the expanded cap creates a T-profile tower with a penthouse floor plate larger than the slim tower footprint below."
    },
]

# --- Verification ---
assert len(sentences) == 120, f"Expected 120, got {len(sentences)}"

path_ids = [s["book_composition_path_id"] for s in sentences]
assert len(set(path_ids)) == 120, f"Duplicate path_ids: {120 - len(set(path_ids))} duplicates"

names = [s["name"] for s in sentences]
assert len(set(names)) == 120, f"Duplicate names: {120 - len(set(names))} duplicates"

# Verify GFA in range [3745, 5930]
for s in sentences:
    gfa = s["dimensional_intent"]["target_gfa_m2"]
    assert 3745 <= gfa <= 5930, f"{s['name']}: GFA {gfa} out of range"

payload = {"sentences": sentences}

# Validate against schema
try:
    import jsonschema
    schema_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\runs\cycle-comp22\book-author\schema.json"
    with open(schema_path, encoding='utf-8') as f:
        schema = json.load(f)
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(payload))
    if errors:
        print(f"SCHEMA ERRORS: {len(errors)}")
        for e in errors[:20]:
            print(f"  - path={list(e.path)}: {e.message}")
        sys.exit(1)
    else:
        print("Schema validation: PASSED (0 errors)")
except ImportError:
    print("jsonschema not available, skipping validation")

# Write output
out_path = r"D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\book-comp22.json"
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Written {len(sentences)} sentences to {out_path}")
print(f"Path IDs unique: {len(set(path_ids))}")
print(f"Names unique: {len(set(names))}")

# Count by base_volume
from collections import Counter
# Count groups by examining path IDs against PROMPT offer
# Just print a summary
print("Count: 120 sentences across 6 base volumes x 3 orientations")
