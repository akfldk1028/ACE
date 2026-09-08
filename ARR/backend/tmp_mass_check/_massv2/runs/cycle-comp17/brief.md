# Architectural massing author brief - assembled from canonical owners

Return only one {"schemes":[...]} JSON object. Exactly 6 schemes. Required scheme keys: name,
primary_language, secondary_language, formal_principle (one Korean sentence for the final sheet),
dominant_gesture, reference_basis (verified facts or original authorship), floor_height_m,
ops (each with op, supported parameters, and a concise why: input -> operation -> visible change -> function -> limitation).
Use the live grammar's parameter units and ranges. Start with extrude|loop|aggregate|stack.
Operational authoring instructions are in English; user-facing sheet descriptions may be Korean.
Design architectural masses: positive-volume hierarchy, section, articulation, joining/separation and carved voids.
A courtyard is a void organizing building volumes; planting or landscape composition does not substitute for a massing proposition.

## Programme first; compare density as a design decision
Legal upper bounds are hard limits, not automatic design targets.
Meet explicit required programme and area using the supplied definitions and tolerances; disclose infeasibility instead of silently reducing the brief.
If required programme or target area is absent, keep it unknown; do not invent a maximum-FAR target or claim programme compliance.
Compare distinct height, density and solid-void organizations that address the same supplied requirements; do not reduce alternatives to scaled copies.
Lower FAR needs a visible spatial benefit in delivered mass, plan or section; prose alone is not evidence and lower density is not automatically superior.
Initial authored height is revisable when the spatial proposition benefits, while explicit per-alternative growth constraints remain meaningful and must not be silently overridden.
Do not invent rooms, circulation or structural proof from an attractive silhouette. State what the supplied geometry establishes and what remains unverified.
Choose only the supported principles and operations needed for each proposition; operator count is not a quality target.

## Brief design rationale required for each scheme
1) State one conflict supported by the supplied site/programme evidence; label a provisional question when that evidence is missing.
2) State one architectural massing principle that addresses it.
3) Explain how that principle differs from the current board entries below.
4) Express it with supported operators and state the resulting limitations.
Provide concise decisions and evidence, not hidden deliberation.

## Confirmed parcel planning constraints derived from the code owner
Storey count and metric height are different constraints. Do not mark unverified items as passed.
```json
{
  "policy_id": "gosan-public1-molit-2026-334",
  "parcel_label": "경기도 의정부시 산곡동 684-1 / 공공1",
  "max_storeys": 5,
  "max_bcr_pct": 60.0,
  "max_far_pct": 250.0,
  "statutory_max_height_m": null,
  "default_building_type": "업무시설",
  "building_subtype": "공공업무시설",
  "sources": [
    {
      "title": "의정부고산 토지이용계획도 등 관련도면: 가구 및 획지, 건축물 등에 관한 결정도",
      "date": "2026-06-29",
      "download_url": "https://apply.lh.or.kr/lhapply/lhFile.do?fileid=67554543",
      "listing_url": "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?aisTpCd=01&ccrCnntSysDsCd=01&panId=BN-0007713&uppAisTpCd=01",
      "relevant_pdf_pages_1_based": [
        6
      ],
      "sha256": "0225c991a7c2c8ca7dc497c8576eaa1d29668f57b5d78ebd43727e22349bb3cd",
      "bytes": 16093893,
      "pdf_page_count": 6,
      "retrieved_on": "2026-09-06",
      "local_evidence": "agents/MassAgent/docs/reports/legal-sources/gosan-15-drawings.pdf"
    },
    {
      "title": "국토교통부고시 제2022-374호 지구계획 변경(9차)",
      "date": "2022-06-29",
      "download_url": "https://www.ui4u.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_000000000174255&fileSn=0",
      "listing_url": "https://www.ui4u.go.kr/portal/bbs/view.do?bIdx=251846&mId=0114050000&ptIdx=27",
      "relevant_pdf_pages_1_based": [
        13,
        22
      ],
      "sha256": "7b60ffbf4ad20fca7d0b48fe37488c2ec913faf714dd4b7314f29ef2bbb584ca",
      "bytes": 446211,
      "pdf_page_count": 32,
      "retrieved_on": "2026-09-06",
      "local_evidence": "agents/MassAgent/docs/reports/legal-sources/gosan-9-notice.pdf"
    },
    {
      "title": "의정부고산 9차 지구단위계획 시행지침",
      "date": "2022-06-29",
      "download_url": "https://www.ui4u.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_000000000174255&fileSn=3",
      "listing_url": "https://www.ui4u.go.kr/portal/bbs/view.do?bIdx=251846&mId=0114050000&ptIdx=27",
      "relevant_pdf_pages_1_based": [
        47,
        48,
        49,
        50,
        56
      ],
      "sha256": "5708c6bc0854cdba547e0664b05999f23553bf123bee0cb8e392ba356dc1e78e",
      "bytes": 5813648,
      "pdf_page_count": 79,
      "retrieved_on": "2026-09-06",
      "local_evidence": "agents/MassAgent/docs/reports/legal-sources/gosan-9-guidelines-full.pdf"
    },
    {
      "title": "건축법 시행령 별표1, 현행 법령 페이지 시행일2026-07-28",
      "date": "2026-07-28",
      "download_url": "https://www.law.go.kr/LSW/flDownload.do?gubun=&flSeq=168351463&bylClsCd=110201",
      "listing_url": "https://www.law.go.kr/LSW/lsInfoP.do?ancYnChk=0&chrClsCd=010202&efYd=20260728&lsiSeq=288339&urlMode=lsInfoP",
      "relevant_pdf_pages_1_based": [
        3,
        7
      ],
      "sha256": "150e9bafcf6544fdcbd43ab5d3d67691ab56b03193260a24c8ace25882e560fc",
      "bytes": 137824,
      "pdf_page_count": 12,
      "retrieved_on": "2026-09-06",
      "local_evidence": "agents/MassAgent/docs/reports/legal-sources/building-decree-annex1-20260728.pdf"
    }
  ],
  "unverified": [
    "measured_terrain_datum",
    "exact_building_line_geometry",
    "detailed_floor_schedule",
    "access_and_egress"
  ],
  "numeric_status": "direct_revision15_drawing_confirmed; latest_official_revision_obtained",
  "allowed_use_status": "historical_revision9_text_confirmed; current_detailed_change_chain_incomplete",
  "use_classification_status": "current_national_rule_confirmed; actual_program_schedule_unverified",
  "building_line_status": "official_plan_registered; survey_geometry_unverified",
  "vehicle_access_status": "official_plan_prohibited_intervals_registered; actual_access_design_unverified",
  "datum_measured": false,
  "frontage_registration": {
    "registration_id": "gosan-public1-decision15-frontages-20260906",
    "evidence_grade": "official_plan_registered",
    "survey_verified": false,
    "permit_compliance_verified": false,
    "source_pdf_sha256": "0225c991a7c2c8ca7dc497c8576eaa1d29668f57b5d78ebd43727e22349bb3cd",
    "source_pdf_page_1_based": 6,
    "source_pdf_url": "https://apply.lh.or.kr/lhapply/lhFile.do?fileid=67554543",
    "diagnostic_file": "agents/MassAgent/docs/reports/public1-coordinate-registration.json",
    "diagnostic_sha256": "f38717b39191f42601bf0db6b14236763dc1e4f8fa6261e5382eec3b1e08039e",
    "coordinate_frame": "parcel UTM translated by its minimum x,y; metres",
    "reference_parcel_ring_local_m": [
      [
        0.0,
        32.85654268087819
      ],
      [
        11.59371943201404,
        39.50109809124842
      ],
      [
        29.64010443945881,
        50.43758501717821
      ],
      [
        46.434598230640404,
        61.34179168846458
      ],
      [
        76.16706880752463,
        44.32430054806173
      ],
      [
        78.23247281974182,
        36.59896623622626
      ],
      [
        57.298764832085,
        0.0
      ],
      [
        33.13071452913573,
        13.857184919528663
      ]
    ],
    "native_boundary_path_indices": [
      169709,
      169802,
      169859,
      169736
    ],
    "similarity_rmse_m": 0.0422624523558319,
    "similarity_max_residual_m": 0.06730724482142661,
    "pdf_to_local_matrix": [
      [
        1.7632335297180013,
        -0.03870232491089445
      ],
      [
        -0.03870232491089446,
        -1.7632335297180015
      ]
    ],
    "pdf_to_local_translation": [
      -1128.226518104534,
      2717.6559174955923
    ],
    "building_limit": {
      "edge_indices_0_based": [
        3,
        4,
        5
      ],
      "setback_m": 2.0,
      "basis": "written 2m dimension on registered connected frontages; no blanket parcel buffer",
      "native_line_path_indices": [
        153873,
        153874,
        153875,
        153876,
        153877,
        153878,
        153879,
        153880,
        153881,
        153882,
        153883,
        153884,
        153885,
        153886,
        153887,
        153888,
        153889,
        153890,
        153891,
        153892,
        153893,
        153894,
        153895,
        153896,
        153897
      ],
      "native_dimension_path_indices": [
        153087,
        153088,
        153089,
        153090
      ],
      "observed_centerline_local_m": [
        [
          44.56676010658284,
          60.12905534841926
        ],
        [
          74.48117894171324,
          42.985759756271534
        ],
        [
          76.07149158052712,
          36.87602862980489
        ],
        [
          55.52816026433155,
          1.0152078718458881
        ]
      ]
    },
    "road_frontage": {
      "registered_edge_group": "building_limit",
      "basis": "decision15 page6: roads adjoin these registered NE, corner and SE edges",
      "purpose": "pedestrian_address_orientation; vehicle_prohibition_is_separate"
    },
    "vehicle_access_prohibited": {
      "full_edge_indices_0_based": [
        3,
        4
      ],
      "partial_edge_index_0_based": 5,
      "partial_edge_end_chainage_m": 9.272546192997954,
      "end_local_m": [
        73.62868408060275,
        28.550038223959213
      ],
      "native_path_indices": [
        152682,
        152776,
        152778
      ],
      "native_end_tick_midpoint": [
        714.7499694824219,
        1509.4100341796875
      ],
      "endpoint_reading_spread_m": 0.04481685651251688,
      "basis": "registered red symbol endpoints; cartographic estimate, not survey tolerance"
    }
  }
}
```

## 심판 판정 원장 (기계 집계 - 손 복제 없음)
저작할 때 이 목록의 문장을 되풀이하면 같은 축에서 같은 점수를 받는다.

- **book:book-agent08:grid:creative-020** — 최약축 EDITABILITY 1.0 (전축 C1.7, F2.7, S2.3, E1.0) : The cellular fragmentation leaves no clear zone for a standard floor layout or a core; the idea dissolves enti / The compressed cellular aggregate cannot be simplified without dissolving the form entirely.
- **book:book-comp01:morph-voided-low:creative-022** — 최약축 CONCEPT 1.0 (전축 C1.0, F5.0, S2.0, E5.0) : 단순한 직사각형 막대에서 이 안만의 강한 형식 개념을 찾기 어렵다. / 직육면체의 단순 압출 외에 기억될 형상 조작이나 공간적 중심이 보이지 않는다.
- **book:book-comp01:morph-voided-low:creative-034** — 최약축 CONCEPT 1.0 (전축 C1.0, F5.0, S1.3, E3.7) : 작은 단일 직육면체 탑에서 이 안만의 기억할 형식 개념은 보이지 않는다. / 작은 직사각 탑 하나만 있어 경쟁안으로 기억될 조형 개념이 부족하다.
- **book:book-comp01:morph-voided-mid:creative-027** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.0, S1.7, E1.0) : 불연속적인 두 면만 보여 건축 매스의 통일된 개념을 읽기 어렵다. / 위아래로 분리된 얇은 면만 뚜렷해 완결된 건축 매스의 개념을 읽기 어렵다.
- **book:book-comp01:morph-voided-tall:creative-030** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.0, S1.7, E1.0) : 평면 윤곽과 분리된 면만 보여 완성된 덩어리의 개념을 읽을 수 없다. / 큰 지면 윤곽과 떠 있는 작은 면의 관계만 보여 입체 개념이 완결되지 않는다.
- **book:book-comp02:morph-voided-low:creative-022** — 최약축 CONCEPT 1.0 (전축 C1.0, F5.0, S2.0, E5.0) : The almost unmodified rectangular block has no distinguishing formal idea visible in the mass. / The image is essentially an unarticulated rectangular prism with little formal identity.
- **book:book-comp03:morph-voided-low:creative-022** — 최약축 CONCEPT 1.0 (전축 C1.0, F5.0, S2.0, E5.0) : The unmodified rectangular block offers almost no distinctive formal proposition. / The plain rectangular extrusion provides little memorable formal idea.
- **book:book:inflated:creative-006** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.0, S1.0, E1.0) : There is no building - a hairline sliver on an empty field. / Nothing is built; a single sliver on an empty parcel.
- **book:book:interlocking_tilted_discs:creative-014** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.3, S1.0, E1.0) : A thumbnail of interlocking discs, unreadable at building scale. / 1% coverage, a mechanical curio rather than a civic building.
- **book:book:interlocking_tilted_discs:creative-029** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.3, S1.0, E1.0) : A pole with fins; nothing legible as architecture. / A 1% sliver; not a proposal.
- **book:book:interlocking_tilted_discs:creative-044** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.0, S1.0, E1.0) : A thumbnail of tilted discs; illegible at any civic scale. / 1% coverage; a mechanical fragment.
- **book:book:interlocking_tilted_discs:creative-059** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.0, S1.0, E1.0) : A curled fragment at model-fragment scale. / 2% coverage; a curled fragment.
- **book:book:long_span_bridge:creative-030** — 최약축 SITE 1.0 (전축 C1.7, F2.7, S1.0, E2.0) : 7% coverage, a lone pin in an empty field. / 7% coverage, 13% FAR, a token on the plot.
- **book:book:thin_disc_cluster:creative-013** — 최약축 CONCEPT 1.0 (전축 C1.0, F2.0, S1.0, E1.0) : A crumb of half-cylinders; at this size it is a fragment, not a scheme. / A tiny disc fragment at 4% coverage; not a building.
- **book:book:thin_disc_cluster:creative-028** — 최약축 SITE 1.0 (전축 C1.3, F2.0, S1.0, E1.0) : The parcel is left blank. / Vanishes on the plot.
- **book:book:thin_disc_cluster:creative-043** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.0, S1.0, E1.0) : A stub with a mast - not readable as a building. / 2% coverage; a drum with an antenna, not a building.
- **book:book:thin_disc_cluster:creative-058** — 최약축 CONCEPT 1.0 (전축 C1.0, F1.0, S1.0, E1.0) : A pin with a crumb on top; nothing legible. / 1% coverage; a stick and a drum.
- **book:cultural__01__program_cultural_court_bridge__universal_0_0_f772e33305__diagnostic_anchor_prismatic__book_operative_skew__search_v5** — 최약축 CONCEPT 1.0 (전축 C1.0, F5.0, S1.7, E3.3) : An unmodified three-storey bar; nothing has happened to it, and nothing will be remembered. / An extruded bar in three layers - there is no formal idea to remember, only a default.
- **book:cultural__02__program_cultural_split_gallery_ramp__universal_2_8_b99c5ef711__book_case_64_overlap+expand__search_v5** — 최약축 SITE 1.0 (전축 C2.0, F4.0, S1.0, E2.3) : 7% of a 2,500 m2 parcel, dropped in the middle - a model on a board, not a building on a site. / 7% coverage and 43% FAR - the least claim on the parcel of anything on the board, and no relation to its geome
- **aggregate_pack_house_field** — 최약축 CONCEPT 1.3 (전축 C1.3, F1.7, S2.3, E1.7) : The sentence promises six gabled house identities; the mass delivers a flat layered plate on four fins with no / The six gabled houses are simply not there - what is delivered is a flat plate on four blades with the units c

### 라운드 총평
- [vlm-book-comp15] Advance t19 for its integrated stepped masses and connected sectional organization, with t01 and t09 offering strong alternative approaches to defining exterior space. The set is strongest where a few substantial volumes establish a clear void; excessive offsets and local notches tend to weaken both
- [vlm-book-comp15] Advance t19 for its integrated sectional hierarchy, t01 for its coherent enclosing gesture, and t17 for its disciplined and readily developable paired volumes; t12 and t18 also merit further development. The strongest alternatives make the principal void and major volumes legible together, while sev
- [vlm-comp16] I would advance t09 and t07 for their clear courtyard hierarchies and credible development paths, with t06 as a distinct parallel-volume alternative. The elevated-cap and fragmented schemes show interesting gestures but need stronger evidence of usable sections, connections and transfers; across the
- [vlm-comp16] I would advance t09 and t06 for their legible positive volumes, coherent voids, and credible development potential, with t07 and t13 as restrained alternatives; among the equal-scoring courtyard schemes, t04 has the more distinctive roof section. Several lifted and capped compositions remain visuall
- [vlm-comp16] I would advance t09 and t07 for their legible courtyard hierarchies and supported, connected volumes, with t06 offering a strong alternative based on repeated vaulted bars. Several lifted and bridging schemes have distinctive silhouettes but need clearer evidence of transfers and circulation before 
- [vlm-book-comp16] I would advance t16 for its integrated terraced hierarchy, with t13 and t14 as convincing alternatives that balance clear exterior space with developable positive volumes. The more sculptural ring, waist and arch studies warrant further structural and circulation evidence before advancement; all sit
- [vlm-book-comp16] Advance t16 and t14 for their strong positive-volume and sectional hierarchies, with t13 as a restrained, readily developable alternative. The set demonstrates several credible massing ideas, but circulation, structural systems, exact building-line compliance and the statutory height cap remain unve
- [vlm-book-comp16] I would advance t15, t14 and t16 for their combined volumetric hierarchy, legible open spaces and plausible architectural development, with t15 strongest in the relationship between its grounded end masses and elevated connection. The crossed rising bars of t05 also merit further study for their dis


## Development champions already carried into the corpus
These comparisons were judged. Treat them as specific evidence, not a guarantee for a different design.

- **book:book-develop-comp03:exact-authored-development:creative-001** — - : all 3 independent juror sessions preferred this variant to parent book:book-comp03:morph-bridge-low:creative-018 in a blind pairwise comparison
- **sangok_c04_develop_perforated_base** — ops[1].bottom_surface {'type': 'constant', 'height': 0} -> {'type': 'profile', 'points': [[0, 0], [0.4, 0], [0.44, 0.42], [0.56, 0.42], [0.6, 0], [1, 0]], 'axis': [0, 1], 'span': [0, 1]} : all 3 independent juror sessions preferred this variant to parent sangok_c04_two_gardens~full_ground^cross_open in a blind pairwise comparison
- **book:book-develop-comp06:exact-authored-development:creative-002** — - : all 3 independent juror sessions preferred this variant to parent book:book-comp06:morph-curved-low:creative-001 in a blind pairwise comparison
- **book:book-develop-comp08:exact-authored-development:creative-001** — - : all 3 independent juror sessions preferred this variant to parent book:book-comp08:morph-curved-low:creative-001 in a blind pairwise comparison
- **book:book-develop-comp09:exact-authored-development:creative-002** — - : all 3 independent juror sessions preferred this variant to parent book:book-comp09:morph-curved-low:creative-001 in a blind pairwise comparison
- **book:book-develop-comp10:exact-authored-development:creative-001** — - : all 3 independent juror sessions preferred this variant to parent book:book-develop-comp08:exact-authored-development:creative-001 in a blind pairwise comparison
- **book:book-develop-comp12:exact-authored-development:creative-002** — - : all 3 independent juror sessions preferred this variant to parent book:book-comp12:morph-compact-mid:creative-012 in a blind pairwise comparison
- **book:book-develop-comp15:exact-authored-development:creative-002** — - : all 3 independent juror sessions preferred this variant to parent book:book-comp15:morph-compact-mid:creative-008 in a blind pairwise comparison
- **loop_butterfly_open__d07_bar+** — ops[0].bar 0.23 -> 0.265 : all 1 independent juror sessions preferred this variant to parent loop_butterfly_open in a blind pairwise comparison

## Reference sentences: how the reference offices are said in this language
Read these as partis, not as templates: the demand below is to differ from every board entry at the level of formal principle, and these show what a principle looks like when it is stated in one sentence.

### BIG (12)
- **big_via57west** — A perimeter court is held low on three corners and pulled into a single peak on the fourth, so the roof becomes one warped slope falling toward the water. — `loop(bar=0.3, height=0.9, profile=trapezoidal) → split(ratio=0.34, along=cross, first=peak, second=skirt, gap=0) → taper(ratio=0.35, on=skirt) → carve(size=0.45, at=open, reach=0.6)`
- **big_8house** — A single perimeter block is squeezed at its waist into two unequal courtyards and tipped so one corner rises and the opposite sinks to the ground. — `loop(bar=0.3, height=0.75) → split(ratio=0.42, along=cross, first=north_court, second=south_court, gap=0.18) → taper(ratio=0.4, on=south_court) → carve(size=0.4, at=open, reach=0.3)`
- **big_mountain_dwellings** — The mandatory parking is built as an inclined artificial hill and a single-storey layer of housing is draped over its sloping roof. — `stack(n=5, contrast=1.35, height=0.8, align=back) → split(ratio=0.38, along=cross, first=garage, second=homes, gap=0) → shear(ratio=0.3, on=homes, toward=open) → carve(size=0.3, at=back, reach=0.35)`
- **big_79_and_park** — A perimeter block of small modules is given a different height at every module so the roof reads as a hill, low against the park and high against the city. — `loop(bar=0.28, height=0.7) → split(ratio=0.4, along=open, first=park_edge, second=city_edge, gap=0) → taper(ratio=0.38, on=park_edge) → carve(size=0.35, at=open, reach=0.3)`
- **big_the_twist** — One straight gallery bar is thrown across the river and warped about its own axis near midspan, so a horizontal end on the low bank becomes a vertical end on the high bank. — `extrude(height=0.28) → lift(clearance=0.35, on=body) → split(ratio=0.45, along=cross, first=low_end, second=high_end, gap=0) → shear(ratio=0.35, on=high_end, toward=cross)`
- **big_vancouver_house** — A tower is bitten away at its base by the clearance from an elevated bridge ramp, and grows back to a full plate only above the height where that clearance ends. — `extrude(height=1.0) → carve(size=0.55, at=back, reach=0.35) → split(ratio=0.32, along=back, first=podium, second=tower, gap=0.2) → shear(ratio=0.2, on=tower, toward=open)`
- **big_lego_house** — Twenty-one unequal brick volumes are interlocked around and above a covered public room, and one oversized brick locks the pile. — `aggregate(n=6, spread=1.5, height=0.5, tie=0.3) → carve(size=0.5, at=open, reach=0.3) → taper(ratio=0.55, on=object_5) → shear(ratio=0.25, on=object_3, toward=cross)`
- **big_copenhill** — The plant machinery is ordered by its own height and one continuous roof plane is laid over that order, turning the by-product of the section into a public slope. — `extrude(height=0.95) → split(ratio=0.4, along=open, first=furnace, second=slope, gap=0) → taper(ratio=0.35) → carve(size=0.3, at=cross, reach=0.3)`
- **big_kaktus_towers** — Two towers of unequal height rise from a shared plinth and every floor plate is rotated slightly so the facade becomes a field of pointed balconies. — `aggregate(n=2, spread=1.35, height=0.9, tie=0.25, profile=hexagon) → carve(size=0.3, at=open, reach=0.85) → shear(ratio=0.18, on=object_1, toward=cross) → lift(clearance=0.15, on=field_plate)`
- **big_one_high_line** — Two towers of unequal height share one podium and each turns out of the other's way, opening a reciprocal slot of view between them. — `aggregate(n=2, spread=1.4, height=0.95, tie=0.18) → shear(ratio=0.3, on=object_0, toward=open) → shear(ratio=0.25, on=object_1, toward=back) → carve(size=0.4, at=cross, reach=0.2)`
- **big_grove_at_grand_bay** — Two towers stand in one garden and each rotates its plates as it climbs, tuned so neither moves into the other's line of sight. — `aggregate(n=2, spread=1.28, height=0.8, tie=0.14) → shear(ratio=0.32, on=object_0, toward=open) → shear(ratio=0.22, on=object_1, toward=cross) → lift(clearance=0.15, on=field_plate)`
- **big_the_spiral** — The stepped setback is taken one floor at a time and chained so it rotates around all four faces, turning a ziggurat into one continuous green ribbon. — `stack(n=6, contrast=1.28, height=1.0, align=cross) → carve(size=0.3, at=open, reach=0.85) → carve(size=0.4, at=back, reach=0.12) → taper(ratio=0.7)`

### OMA (12)
- **oma_seattle_library** — Five programme platforms of unequal size are stacked and slid past one another so the leftover space between them becomes the public volume. — `stack(n=5, contrast=1.3, height=0.62, align=open) → shear(ratio=0.3, toward=open, on=tier_1) → shear(ratio=0.22, toward=back, on=tier_3) → carve(size=0.34, at=open, reach=0.45)`
- **oma_cctv** — The whole production chain is bent into a continuous loop so the building has no top and no hierarchy of height. — `loop(bar=0.3, height=0.85, profile=concave_l) → shear(ratio=0.22, toward=open, on=bar_w) → carve(size=0.3, at=open, reach=0.35)`
- **oma_de_rotterdam** — Three unequal towers of different programme are shifted against each other and tied down by one common plinth. — `aggregate(n=3, spread=1.35, height=0.85, tie=0.16) → shear(ratio=0.24, toward=open, on=object_1) → shear(ratio=0.3, toward=back, on=object_2) → carve(size=0.28, at=open, reach=0.4)`
- **oma_casa_da_musica** — One white faceted solid stands alone on a square and the concert hall is bored straight through it, glazed at both ends. — `extrude(height=0.6, profile=faceted) → carve(size=0.5, at=open, reach=1.0) → carve(size=0.3, at=cross, reach=0.45)`
- **oma_timmerhuis** — A repeated modular cell is aggregated and set back as it rises, dissolving into two irregular peaks rather than one tower. — `aggregate(n=4, spread=1.45, height=0.75, tie=0.14) → taper(ratio=0.55) → taper(ratio=0.75) → carve(size=0.3, at=back, reach=0.5)`
- **oma_milstein_hall** — A single thin studio plate is raised on supports and pushed across the street so it joins two existing buildings at their second floor. — `extrude(height=0.22) → lift(clearance=0.35, on=body) → carve(size=0.32, at=back, reach=0.45)`
- **oma_kunsthal** — A square block is cut by a road and a ramp into unequal parts held at two different ground levels. — `extrude(height=0.35) → split(ratio=0.45, along=cross, first=dike_hall, second=park_hall, gap=0.18) → lift(clearance=0.2, on=dike_hall) → shear(ratio=0.22, toward=open, on=park_hall)`
- **oma_educatorium** — A single slab is split unequally and one half is pushed out and pulled up so floor, wall and roof are one surface. — `extrude(height=0.4) → split(ratio=0.6, along=open, first=hall_stack, second=canteen_wing, gap=0.0) → shear(ratio=0.26, toward=open, on=hall_stack) → taper(ratio=0.7, on=hall_stack)`
- **oma_shenzhen_stock_exchange** — The podium that should sit on the ground is cut from the shaft and raised high, leaving the whole ground plane to the city. — `extrude(height=0.95) → split(ratio=0.35, along=cross, first=podium_plate, second=tower_shaft, gap=0.0) → lift(clearance=0.3, on=podium_plate) → taper(ratio=0.65)`
- **oma_taipei_performing_arts** — Three theatres of different size are docked into a single central volume raised clear of the ground. — `aggregate(n=3, spread=1.6, height=0.5, tie=0.38, profile=hexagon) → lift(clearance=0.28, on=field_plate) → shear(ratio=0.26, toward=open, on=object_0) → taper(ratio=0.6, on=object_1)`
- **oma_fondazione_prada** — New volumes of deliberately different character are set among retained distillery sheds so the courtyard, not any building, is the centre. — `aggregate(n=5, spread=1.7, height=0.7, tie=0.12) → taper(ratio=0.6, on=object_0) → shear(ratio=0.24, toward=cross, on=object_1) → carve(size=0.35, at=open, reach=0.45)`
- **oma_netherlands_embassy** — The block the city demanded is split into a freestanding cube and a thin wall that keeps the street line, with a route carved through the cube. — `extrude(height=0.55) → split(ratio=0.62, along=back, first=cube, second=wall_wing, gap=0.3) → shear(ratio=0.2, toward=cross, on=wall_wing) → carve(size=0.35, at=open, reach=0.6)`

### SANAA (12)
- **sanaa_kanazawa** — A single low circular boundary holds galleries of unequal size so the building has no front and no back. — `aggregate(n=5, spread=1.9, height=0.5, tie=0.3, profile=oval) → carve(size=0.32, at=cross, reach=0.5) → carve(size=0.28, at=open, reach=0.7)`
- **sanaa_rolex** — One continuous single-storey slab covers the site and is perforated and lifted so the ground never stops. — `extrude(height=0.18, profile=stadium) → carve(size=0.42, at=cross, reach=0.6) → carve(size=0.3, at=open, reach=0.8) → lift(clearance=0.25, on=body)`
- **sanaa_zollverein** — A single full-height cube occupies a fraction of the site and refuses to spread. — `extrude(height=1.0) → carve(size=0.32, at=open, reach=0.3) → carve(size=0.27, at=cross, reach=0.28)`
- **sanaa_toledo_glass** — Rooms are separate glass enclosures inside one low square roof, never sharing a wall. — `aggregate(n=6, spread=1.6, height=0.22, tie=0.12, profile=oval) → carve(size=0.3, at=cross, reach=0.5) → carve(size=0.27, at=open, reach=0.6)`
- **sanaa_new_museum** — Six tiers stack on a narrow mid-block lot and slide off each other, each shift a skylight. — `stack(n=6, contrast=1.3, height=0.85, align=back) → shear(ratio=0.24, toward=open, on=tier_2) → shear(ratio=0.2, toward=cross, on=tier_4)`
- **sanaa_louvre_lens** — Five unequal single-storey volumes touch corner to corner along 300 m. — `aggregate(n=5, spread=1.35, height=0.15, tie=0.08, profile=trapezoidal) → carve(size=0.32, at=open, reach=0.45)`
- **nishizawa_moriyama** — One dwelling is dispersed into unequal detached volumes so the leftover ground becomes a street. — `aggregate(n=6, spread=2.0, height=0.45, tie=0.08) → carve(size=0.3, at=cross, reach=0.7)`
- **sanaa_dior_omotesando** — The trapezoidal plot is extruded to the legal cap at near-full coverage, and only the top is pulled back. — `extrude(height=0.92) → carve(size=0.26, at=open, reach=0.25)`
- **sanaa_grace_farms** — A single continuous roof is the building; unequal glazed rooms hang beneath it down the hillside. — `aggregate(n=5, spread=1.7, height=0.3, tie=0.4, profile=stadium) → carve(size=0.35, at=cross, reach=0.7) → lift(clearance=0.15, on=field_plate)`
- **sanaa_serpentine_2009** — A single thin reflective plate is raised over the clearing and cut around the trees; no walls at all. — `extrude(height=0.12, profile=oval) → carve(size=0.4, at=cross, reach=0.8) → lift(clearance=0.35, on=body)`
- **sanaa_kunstlinie_almere** — A 100 m square plate is cut where the shore ends, the water half on piles, both halves punctured by courts. — `extrude(height=0.2) → split(ratio=0.42, along=cross, first=shore, second=water, gap=0.0) → lift(clearance=0.16, on=water) → carve(size=0.3, at=open, reach=0.6)`
- **sanaa_naoshima_terminal** — A very thin flat roof on a forest of hairline columns covers glass boxes of different sizes. — `aggregate(n=4, spread=1.8, height=0.15, tie=0.35, profile=chamfered) → carve(size=0.3, at=open, reach=0.45) → lift(clearance=0.3, on=field_plate)`

## 거부 함정 원장 (코드 상수에서 생성 — tools/trap_ledger.py)
1. 틈(gap)은 **3.9m 이상**으로 선언하라 — 게이트 문턱 2.4m ÷ (1 − 최악 감쇄 39%).
2. rotate와 선언한 gap을 한 문장에 같이 두지 마라 (회전이 틈을 닫는다).
3. `grade`의 toward는 열거형 — "open"만 산다.
4. gable은 발자국을 넓혀 선언한 틈을 닫는다 — 틈이 논지면 gable 금지.
5. `extract`의 gap은 **호스트폭 비율** 좌표계다 — 미터 규칙과 혼동 금지.
6. stack으로 밴드가 된 몸에 cantilever는 조용하다.
7. 대지 꽉 찬 몸 위에서 cantilever·shear 금지 — 일조 봉투가 먹는다.
8. `cantilever`·`canopy`의 reach 상한 0.40 — 구조 게이트 backspan 1.6의 역산 r/(1+r) × 0.65. 실측 통과값 0.28.
9. `fold`의 낙차는 배달에서 +35%까지 부푼 실측 — 얕게 선언하라. 접힘은 렌더 이음선 상한(점 8개 = 접힘 3개)까지.
10. 방은 유효깊이 2.4m — 그보다 얇은 판을 원하면 canopy(방 면제)로 말하라.
11. 관계·이동 비율의 바닥 0.15 — 그 아래 선언은 침묵 게이트가 잡는다.
12. 물리: 퍼텐셜 우물 -10.0m 아래는 기각 (눈먼 라운드로 캘리브레이션).

## Current board: differ from every entry at the level of formal principle
The common curator reserves one seat per family, not per renamed parameter variation.

No judged and baked seats exist in the current era yet.

---

## Sayable words, derived from the executor (the validator's own table)
Verb: parameters. Ranges are the validator's; enum values are listed. A word not here does not exist, whatever the prose above or below says.

- **aggregate**: arrangement, height 0.1..1.0, levels, method, n 2..12, reach 0.0..1.0, spread 1.05..2.5, tie 0.0..0.4, turn, unit
- **align**: face, to
- **approach**: depth, width
- **bend**: degrees -90.0..90.0, segments
- **branch**: height 0.1..1.0, n 2..6, reach 0.0..1.0
- **butterfly**: along, at, pitch
- **canopy**: at, reach 0.0..1.0, thin, toward
- **cantilever**: levels, reach 0.15..0.4, toward
- **carve**: at, reach 0.0..1.0, size 0.15..0.6, through, up_to
- **compress**: ratio 0.6..1.0, toward
- **crown**: along, form in {dish, dome, saddle}, sag 0.0..0.6
- **embed**: at, depth, first, height 0.1..1.0, level, size 0.1..0.7
- **expand**: ratio 1.0..1.6, toward
- **extract**: gap 0.0..12.0, height 0.1..1.0, level, size 0.1..0.7
- **extrude**: height 0.1..1.0
- **fold**: along, folds, pitch
- **fracture**: degrees -90.0..90.0, n 2..6, slot, turn
- **gable**: along, at, bays, pitch
- **grade**: run, smooth, steps, toward, walk
- **inflate**: ratio 1.0..1.6
- **inscribe**: across, at, depth, size 0.1..0.7
- **interlock**: bite, reach 0.0..1.0, size 0.1..0.7
- **intersect**: climb, degrees -90.0..90.0, first, level, size 0.1..0.7
- **lift**: clearance 0.1..0.4
- **lodge**: at, height 0.1..1.0, over, size 0.1..0.7
- **loop**: bar 0.15..0.4, height 0.1..1.0, step 0.4..1.0
- **mansard**: along, pitch, shoulder
- **merge**: height 0.1..1.0
- **nest**: proud, size 0.1..0.7, turn
- **notch**: at, size 0.15..0.5
- **offset**: ratio 0.15..0.95, toward
- **overlap**: bite, height 0.1..1.0, slip
- **pinch**: ratio 0.15..0.95, segments
- **puncture**: n 1..3, size 0.1..0.45
- **roof**: corners, eave, rise, sag 0.0..0.6, thin
- **rotate**: degrees -90.0..90.0
- **shape**: bottom_surface, plan_region, top_surface
- **shear**: ratio 0.15..0.95, toward
- **shift**: ratio 0.15..0.95, toward
- **sink**: depth
- **skew**: degrees -90.0..90.0, toward
- **split**: along, contrast 1.2..3.5, first, gap 0.0..12.0, ratio 0.3..0.75, second
- **stack**: align, contrast 1.0..3.5, grow, height 0.1..1.0, n 2..6
- **taper**: ratio 0.15..0.95
- **twist**: degrees -90.0..90.0
- **vault**: along, bays, rise

Universal on every verb: about, on, profile, storeys.

---

# massv2 저작 어휘 명세 (2026-08-19, 관계동사 확장판)

문장(parti)은 `{"schemes": [...]}` JSON. 각 scheme:

```json
{
  "name": "office_building_short_slug",
  "primary_language": "solid_body | carved_body | open_figure | porous_field",
  "secondary_language": "one line, what the building is as a body",
  "formal_principle": "한 문장 - 이 매스가 왜 이 형태인가 (시트에 인쇄됨)",
  "dominant_gesture": "한 구절",
  "reference_basis": "실존 건물이면 사실 근거(건축가·위치·연도). 창작이면 '저작 신작'이라 쓰고 거짓 근거 금지",
  "ops": [ {"op": "...", ..., "why": "이 단어가 왜 있는가"} ]
}
```

## 규칙
- **첫 단어는 extrude | loop | aggregate | stack 만** (볼륨을 세우는 말).
- 모든 파라미터는 비율. 좌표·미터 하드코딩 없음.
- `on:` 은 볼륨 role의 접두 매칭 (`aggregate`가 만드는 것들은 `object_0..n-1`).
- 말하지 않은 단어는 침묵 게이트가 잡는다 — 모든 단어는 매스를 실측 가능하게 바꿔야 한다.
- 대지 꽉 찬 몸(bare extrude) 위에 면 밖으로 나가는 관계동사를 쓰면 법규선이 먹는다 — 관계는 여유 있는 몸에서 말할 것.

## 볼륨을 세우는 말 (openers)
- `extrude` — 대지형 프리즘.
- `loop` {bar 0.15-0.4, height} — 마당을 도는 네 바.
- `stack` — 줄어드는 밴드 타워.
- `aggregate` {n 2-12, spread≥1, height, tie 0-0.4, turn(도), method, storeys}
  - `method: "pack"`(기본, 그리드 정착) | `"stack"`(**적층** — 단위들이 서로 위에 엇놓임, 층마다 turn 부호 교대)
  - method stack일 때 `storeys`(1-5, 기본 2) = 단위 한 채의 층수. 총높이의 적법은 법규 클립이 심판.
  - `reach`(0-0.6, 기본 0) = **바 끝이 자기 축으로 교대로 미끄러져 더미 밖으로 낢** (VitraHaus의 나는 끝). 지상층은 고정. 서는지는 캔틸레버 게이트(backspan 1.6)가 심판 — 실측: 0.28은 델리버리까지 통과, 0.35는 성장 후 1.61로 기각.
  - `arrangement: "pack"`(기본, 느슨한 격자) | `"radial"`(**유닛들이 고리에 서서 중심을 바라봄** — 마당을 둘러싼 날개들, 부채꼴, 튼ㅁ자) | `"pinwheel"`(같은 고리에서 각 유닛이 90° 더 돌아 풍차). 격자만 있을 때는 중심을 도는 도형이 원천적으로 불가능했다. `turn`은 유닛을 제자리에서 돌리는 다른 말(정착지의 어긋남).
  - `unit: "slab"`(기본) | `"house"`(**기본 볼륨** BOOK 030 — 단면이 집: 깊이가 자기 높이에서 유도되고 45° 박공이 태생부터 붙는다. gable 단어 불필요. VitraHaus = `method:stack unit:house` 한 단어)

## 관계동사 (신규 — 한 몸이 다른 몸에게 하는 일, 호스트 단위공간)
- `lodge` {size 0.15-0.6, over 0.05-0.6, height 0.2-1.0, at 0-1} — 바가 호스트 지붕 위에 **걸쳐** 양쪽으로 내민다.
- `overlap` {bite 0.15-0.6, slip 0-0.5, height} — 쌍둥이가 밀려 평면을 **겹친다**.
- `interlock` {bite 0.3-0.75, size, reach} — 반대 면에서 온 두 팔이 다른 높이에서 **맞물린다**.
- `nest` {size 0.15-0.6, proud 0.1-1.0, turn ±60°} — 안에 **포갠** 몸이 지붕 위로 솟는다. `turn`이면 포갠 몸이 케이스 안에서 돌아선다(월드 공간에 세워 비균등 스케일 전단 없음) — 플린스 위 돌아선 탑은 intersect(관통 바, 몸 높이 안)가 아니라 이 단어다.
- `merge` {height} — 서 있는 몸들이 **하나로 병합** (선언된 유일한 union).
- `extract` {size, gap, height, level} — 조각을 **빼내** 소켓 옆에 세운다 (보이드+조각 한 쌍).
- `inscribe` {size 0.15-0.6, depth 0.1-0.5} — 지붕에 모서리 안 닿는 도형을 **새긴다** (침강 마당).
- `grade ... walk:true` — **경사 지붕을 걷는 땅으로 선언**(`grade smooth run:0.6 toward:"open" walk:true`). 같은 기울기지만 그림이 지면 톤으로 칠하고, 심판은 오르는 지형으로 읽는다(오슬로 오페라·요코하마·모스고르). 문장의 why에 "walkable"을 말하라 — 캡션은 formal_principle이다.
- `sink` {depth 0.1-0.6(자기 높이 몫), on} — **땅으로 내려앉는다**. 잡힌 몸통을 제 높이의 depth만큼 지반(z=0) 아래로. 침강 마당(loop 뒤 `sink on:"court"`는 아직 — 링 전체가 내려감), 반지하 바(`extrude + sink depth:0.4`), 기단에 박힌 탑(`stack + sink on:"tier_0"`). 지하 밴드는 용적률에서 빠지고(시행령 119조), 건축면적은 지상 투영만, 그림은 대지판에 구덩이를 연다.
- `roof` {rise 0.2-1.5(층고 배수), eave 0-0.5(짧은 변 몫), corners "opposite"|"one"|"adjacent"|"all", sag 0-0.6, thin 0.06-0.35} — **휜 지붕판(날아오르는 처마)**. 잡힌 몸통마다 제 지붕판을 사방 처마로 띄우고, 지정 모서리를 rise만큼 들어 올리며 sag가 처마 선을 곡선으로 만든다(쌍곡포물면·MAD 자싱·쿠마의 지붕). 판은 방 아님(구조 밴드)이고 처마 내밈은 구조 게이트가 심판. `aggregate n:5 + roof`가 지붕 밭, `extrude + roof corners:"adjacent"`가 한쪽으로 쓸리는 정자.
- `canopy` {reach 0.1-0.45, at 0.3-1.0, toward} — 층고보다 얇은 판(0.35층)이 호스트 가장자리를 물고 **밖으로 내민다** — 처마(at 1.0 기본)·마퀴(at 낮게). 방 아님을 스스로 선언(occupiable=False)해 방 게이트를 면제받고, 내밈은 구조 게이트가 그대로 심판하므로 reach 상한이 cantilever와 같은 이유로 0.45.

## 지붕 (낙차는 선언한 만큼 정확히 그려짐 — 한 층 캡 아님)
- `gable` {pitch 0.15-1.2, along, bays 1-6, at 0.15-0.85} — 용마루에서 만나는 두 경사면. **pitch는 기하 경사(run당 rise, 1.0 = 45°)** — 볼륨 높이의 몫이 아니다. 낙차는 몸통 높이 안에서 캡되므로, 가파른 박공을 원하면 몸통부터 집 비례여야 한다(폭 30m 슬래브에 45°는 물리적으로 불가 — `unit:"house"`나 compress로 좁힌 바 위에 쓸 것). along 기본 "long" = 볼륨 자신의 실제 긴 축. `bays: n` = 다련 박공(M지붕·톱니 — 몸통을 능선 직각으로 n등분, 각 스트립이 자기 능선). `at` = 용마루 위치(0.5 대칭 기본, 그 외 saltbox — 같은 경사, 긴 쪽이 낮게 닿음).
- `butterfly` {pitch 0.15-1.2, at 0.2-0.8, along} — 두 면이 안쪽 골짜기로 떨어지는 V지붕 (Breuer Geller). 골짜기 깊이 = 짧은 run 쪽이 선언 경사를 가짐.
- `mansard` {pitch 0.15-1.2, shoulder 0.1-0.4, along} — 가파른 어깨 + 평평한 정수리 (오스만 단면). **낙차는 1.5층 캡** — 어깨 run은 선언 경사로 역산. ⚠️ 넓은 저층 몸통에서는 정수리가 좁아져 텐트에 가깝고 단어도 조용함(0.05 문턱 근처) — 좁고 선 가로벽(고밀 필지)이 제 자리.
- `vault` {rise 0.15-1.2, bays 1-6, along} — 배럴 볼트(곡면 지붕). 프로파일을 16점으로 샘플링한 호. **낙차는 박공·맨사드와 같은 1.5층 캡.** 렌더는 점 6개 초과 프로파일의 이음선을 그리지 않는다(샘플링 아티팩트이지 접힘이 아니므로).
- (IR) 단면 프리미티브 `top_profile` — 윗면 = 한 축 위의 꺾은선 높이 프로파일. shed·박공·saltbox·맨사드·버터플라이가 전부 특수 경우. **볼트는 표현 안이었다**(꺾은선에 점을 충분히 주면 곡선) — 진짜 2축이 필요한 것은 힙뿐.
- `grade` {..., smooth: true} — 연속 경사 (계단이면 smooth 없이).
- `fold` {folds 1-3, pitch 0.15-1.2, along} — 한 축을 따라 여러 번 오르내리는 **접힌 판**(톱니·콘체르티나·folded plate). 볼트와 같은 `top_profile` 프리미티브이고 점만 더 쓴다. **접힘 n개 = 점 2n+1개**이고 렌더는 점이 `MAX_CREASED_PROFILE_POINTS`(8)를 넘으면 이음선을 안 그리므로 folds는 3에서 잘린다 — 넷째 접힘은 볼트로 보인다. **선언 pitch는 한 면(facet)의 경사**라 접힘이 늘면 면당 run이 줄어 낙차가 얕아진다(진짜 접힌 판이 그렇다). 낙차는 박공과 같은 1.5층 캡.
- `cantilever` {reach 0.15-0.40, levels 2-4, toward, on} — 위 켜가 아래 켜를 넘어 **나간다**. 단면 IR에는 평면 내밈을 말할 항이 없어 `shear`처럼 밴드를 미는 동사다. **천장 0.40은 구조 게이트에서 역산** (`structure`가 backspan의 1.6배에서 거부 → 스텝 r/(1+r)의 2/3). 기본 0.28은 `aggregate.reach`가 실측으로 남긴 값(0.28 배달 통과, 0.35는 성장 뒤 1.61로 기각). 밑동은 안 움직이고 켜마다 같은 몫씩 나가므로 levels를 늘려도 부재 비율은 일정하다.

### ⚠️ 단면 저작 규칙 (2026-08-26 실측)
1. **좁히지 말고 잘라라.** `compress`는 최소 0.6이라 55m 씨앗을 35m까지밖에 못 줄이는데 지붕 낙차는 1.5층(4.5m)에서 잘린다 → 35m 폭 위의 볼트는 1:8, 둥근 상자로 보인다. `split`으로 진짜 바를 만들어라. 또는 `bays`/`folds`로 **면당 run**을 줄여라 — 잘 읽힌 킴벨(bays 4)과 톱니(folds 3)가 그 경우다.
2. **`cantilever`는 두 켜가 있어야 말한다.** 한 층짜리 몸에는 할 말이 없어 조용히 통과한다(그건 `lift`가 할 말이다). `split`의 `contrast`가 작은 조각의 높이를 나누므로 자른 뒤에도 켜가 둘 남게 `storeys`를 선언하라.
3. **대지를 꽉 채운 몸 위에서 내밀지 마라.** 일조 봉투가 내밈을 먼저 가져가 그림에 안 남는다. `split`이나 `carve` 뒤 여유가 생긴 자리에 말하라.
4. **이미 밴드로 나뉜 볼륨에 또 단면을 얹지 마라.** `grade`(계단) 뒤에 `fold`를 더했더니 밴드마다 지붕이 생겨 23개 변형 전부가 캔틸레버 초과로 기각됐다. 계단 자체가 그 문장의 단면이다.
5. **`split`의 `gap` 단위는 JOINT_CLEARANCE_M(0.76 m)의 배수다** — `gap: 0.16`은 12 cm라 무조건 닫힌다. 골목 6 m를 원하면 `gap: 8`. 논지가 아닌 틈은 선언하지 마라.** 바를 만들려고 `split`에 `gap`을 붙이면 그 틈이 배달되지 않을 때 문장 전체가 거부된다 — 말하지 않은 틈은 닫혀도 거짓이 아니다.

## 기존 변형·절단 (요약)
split, carve, lift{clearance}, notch, puncture, branch{n,reach,height}, embed{size,depth,at},
shift{toward,ratio}, offset, rotate{degrees}, skew, taper, twist, shear, bend, pinch,
compress/expand/inflate{ratio,toward}, fracture, intersect{size,level,climb,degrees}.

## 좋은 문장의 기준 (박제된 교훈)
- 형태 라벨이 아니라 **논지**: "왜 이 관계인가"가 formal_principle에 서야 한다.
- 방위·좌표계 다양성 (15/16이 단일 방위였던 레고 문제).
- 사무소 저작 정체성: 그 사무소가 그 건물에서 실제로 한 '수'를 동사로.


---

# Architectural massing authorship canon

Current operational contract, updated 2026-09-06. The objective is creative, meaningfully different architectural alternatives within applicable law. Historical stylistic preferences are hypotheses to test, not universal acceptance gates. Numeric limits, supported operations and parameter ranges come from the live code-owned grammar, site evidence and author contract.

## Architectural proposition

Give each alternative a readable spatial proposition and a reason for it. An inhabited edge, a shared court, equivalent pavilions, stacked rooms, a bridge between grounded volumes, a continuous hall or an asymmetric section can each be a valid organizing principle. Use only the operations needed to make that proposition actual.

A plain extrusion, flat roof, centred court or group of equally important volumes is allowed. A dominant tower, asymmetric offset, carved void or sculpted roof is not mandatory. Do not append a roof object or arbitrary cut solely to satisfy a novelty quota. A connected material mesh can contain several legible architectural volumes; connectivity is not architectural part count.

Office references guide questions, never stylistic presets or score bonuses: how does programme organize section; how can conflicting conditions produce a coherent transformation; how can equivalent rooms or volumes connect through shared space? Do not equate creativity with the number of verbs, geometric complexity or resemblance to a named practice.

## Evidence and uncertainty

Separate verified site facts, explicit programme requirements and author hypotheses. Do not invent a neighbour's shadow, noise, access permission, required room or floor-area target when evidence is absent. Under an incomplete brief, state a conditional design question and the information needed to resolve it.

A useful rationale connects an evidenced condition or disclosed hypothesis to an operation, the resulting spatial relation, its potential benefit and its remaining limitation. Explain the actual proposed building, not a landscape competition or decorative site diagram. Outdoor space matters through its relationship to occupied architecture.

## Scale, dimensions and law

Read legal ceilings and available programme requirements from the current supplied evidence. Law and explicit user programme requirements remain binding. Missing programme stays unknown; it is not permission to claim compliance.

Neither maximum FAR nor preservation of the first authored height is a universal objective. Explore different heights, densities, mass distributions and solid-void organizations where they create useful differences. A lower-density alternative should show a spatial benefit; a higher-density alternative should demonstrate that its organization remains legible and developable.

Distinguish dimensionless source geometry, authored metric targets, physical materialization and actual parcel delivery. Do not call a proxy storey count a verified floor schedule, a soft authored target a mandatory programme, or a support screen an engineered structure. Use the live dimensional intent contract only when it is supported; explicitly unsupported policies must not fall back silently. Per-alternative constraints may differ.

## Assemblies and support intent

Use actual BaseVolume transformations and supported constructive joins. Independent rotations, offsets and stacking are legitimate ways to assemble occupied volumes. Their executable placement chains must not be confused with unrelated architectural effects; the shared graph-budget owner governs accounting.

For a branch or parallel assembly intended to retain its incoming base, use the supported explicit anchoring mode when available. An elevated input, bridge or cantilever must not be snapped automatically to world ground. Show actual material connection and bearing; do not hide unintended gaps or invent supporting columns in prose. Existing geometry, floor viability and structural screens remain in force.

## Diversity across the alternative set

Compare alternatives at the level of spatial organization, plan and section, not names or minor dimension changes. Read the supplied previous board to understand what has already been explored. Retaining a useful control is legitimate and must be identified honestly; no all-new-verb quota applies.

The set should test genuinely different architectural relations when the brief supports them, rather than fill every available operator slot. Do not force all alternatives into a rotated stack because one reference illustrated stacking. Likewise, do not force one low courtyard solution because it previously received a high score.

Selection and archive policies are code-owned. A coarse cell label must not erase a distinct eligible authored family before visual evaluation. Do not copy family quotas or acceptance thresholds into this document. Visual scoring does not override legal refusal and cannot by itself certify competition-level quality.

## Inspection before submission

Compile and inspect the actual source, including views that reveal the intended relation. An isometric silhouette can hide an opening; use measured plans and sections as well. Verify that named occupied parts, openings, joins and height relationships exist. Distinguish source inspection from actual-site delivery and the later independent jury.

Before submitting, check that the rationale matches the executable fields; supported operations were used; actual geometry expresses the proposition; facts and hypotheses are labelled; and the set offers meaningful alternatives. Avoid tiny residual fragments unless they have a demonstrated architectural role. Detailed rooms, doors, stairs, accessible routes and structural members are not present merely because a massing image suggests them.

## Full flow and development

Production runs through the single mass-cycle entry point: authored parti, real BOOK payload exploration, BaseVolume geometry, independent visual jury and authored development with paired evaluation and feedback. A source preview or partial generation is not a completed cycle.

Develop the judged parent's consequential spatial weakness while respecting the current parent contract. Keep the parent as a comparison and disclose the area and organization tradeoff. The author never declares its own child the winner. Preserve frozen identities and receipts; changed engines require a preserved baseline, new compliant execution and fresh visual evaluation.

For research evidence and historical findings, read the indexed reports in agents/MassAgent/docs/reports/. The previous version of this canon remains in repository history; its taste-based prohibitions and manually copied numeric rules are superseded by this contract.
