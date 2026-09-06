# Architectural massing author brief - assembled from canonical owners

Return only one {"schemes":[...]} JSON object. Exactly 4 schemes. Required scheme keys: name,
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
- [vlm-book-comp03] I would advance t18, t09, t01 and t22 for their clear outdoor gathering spaces and credible paths to civic construction. The roof court of t21 merits reserve consideration, while the more sculptural alternatives need stronger evidence that occupied floors and circulation can preserve their massing i
- [vlm-book-comp03] Advance t09, t04, t21 and t16 for their clear massing and credible paths to usable civic buildings, with t22 and t25 close reserves. The strongest schemes make courts, terraces or a public threshold integral to the volume; the more sculptural outliers need substantial evidence that their occupied sp
- [vlm-comp04] I would advance t03 for its buildable pavilion ensemble and the visible routes between its volumes, with t02 close behind for the stronger architectural image of its folded courtyard ring. The next review should establish actual entries and circulation, particularly access to t02's enclosed court; t
- [vlm-comp04] Advance t01 for its legible pairing of open and enclosed voids, supported by a simple buildable mass. Retain t03 as the strongest alternative for its connected exterior spaces; t02 needs a clearer ground-level relationship between court and site, while t04 needs a more distinctive spatial propositio
- [vlm-comp04] Advance t01 for its clear relationship between a compact built figure and two distinct voids, supported by straightforward construction. Retain t03 as the strongest alternative for a permeable pavilion arrangement; t04 is robust but less memorable, while t02 needs its folded crown and courtyard acce
- [vlm-book-comp04] I would advance t14 and t23 for their coherent spatial figures, credible support and capacity for further development, with t09 and t22 also meriting another round. I would retain t20 as a more demanding sculptural contender, contingent on resolving its visible transfers and sectional circulation wh
- [vlm-book-comp04] I would advance t14 and t23 for their clear, developable forms, with t09 as the stronger enclosed-court alternative. Across the set, the most convincing proposals give simple grounded volumes a useful relationship to outdoor space; several more sculptural entries still need to demonstrate support or
- [vlm-book-comp04] I would advance t14 and t09 for their clear spatial ideas, credible support, and ability to retain their identity through development, with t23 as a restrained alternative. The set is strongest where one massing operation produces useful external or roof space; narrow wall-like bands, unclear elevat


## Development champions already carried into the corpus
These comparisons were judged. Treat them as specific evidence, not a guarantee for a different design.

- **book:book-develop-comp03:exact-authored-development:creative-001** — - : all 3 independent juror sessions preferred this variant to parent book:book-comp03:morph-bridge-low:creative-018 in a blind pairwise comparison
- **sangok_c04_develop_perforated_base** — ops[1].bottom_surface {'type': 'constant', 'height': 0} -> {'type': 'profile', 'points': [[0, 0], [0.4, 0], [0.44, 0.42], [0.56, 0.42], [0.6, 0], [1, 0]], 'axis': [0, 1], 'span': [0, 1]} : all 3 independent juror sessions preferred this variant to parent sangok_c04_two_gardens~full_ground^cross_open in a blind pairwise comparison
- **loop_butterfly_open__d07_bar+** — ops[0].bar 0.23 -> 0.265 : all 1 independent juror sessions preferred this variant to parent loop_butterfly_open in a blind pairwise comparison

## Canonical reference material (original source language preserved)
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

# 저작 규범 (AUTHORING CANON) — 문장을 쓰기 전에 대조하라

2026-08-21. 근거: 강 9문장 vs 약 10문장 코퍼스 부검 + BIG/diségno("one-liner",
"inevitability") + ArchShapeNet 2025(사람-설계 신호: 공간조직·비례조화·디테일 정련,
saliency는 탑과 실루엣) + Stamps 1998(실루엣이 지각을 지배) + OMA Patents(연산 명시).
이 문서는 어휘(VOCABULARY.md)가 아니라 **어휘를 쓰는 법**이다. 신작·재저작은 아래
체크리스트를 전부 통과해야 한다.

## 8 규칙 (부검 실측)

1. **한 수는 위상을 바꾼다.** 뚫리거나(carve through) 들리거나(lift) 녹거나(merge)
   접히거나(gable/grade/butterfly) 얹혀야(lodge/nest on:) 실루엣이 생긴다.
   twist·shear·expand·taper·compress는 이미 선 상자의 재배치일 뿐 — 단독 주연 금지.
2. **오프너가 이미 형상이어야 한다.** 민짜 `extrude{height}` 금지 — profile(faceted/
   chamfered/hexagon/trapezoidal/…)이나 unit:house, loop{bar}, stack{profile}로 태어나라.
3. **큰 몸에 큰 비율.** 비율 파라미터는 몸의 절대 치수에 곱해진다. h0.35 몸에 over 0.5는
   소멸한다. 극단 대비를 원하면 몸을 세우고(0.85~1.0) 거기에 큰 비율을 걸어라 —
   낮은 몸(0.4대)은 저층 슬롯이라는 논지가 why에 명시될 때만.
4. **compress/expand는 교정 동사다.** 강한 문장은 안 쓴다. 비례는 오프너 파라미터
   (bar·spread·profile·unit)로 태어날 때 정한다. 교정 동사가 형상 동사의 자리를 뺏으면
   문장이 약해진다.
5. **`on:`으로 겨눠라.** 비대칭은 전역 변형이 아니라 한 역할만 달라질 때 생긴다.
   관계동사(lodge/nest)는 host 지정이 없으면 죽은 말이다.
6. **storeys/unit을 선언하라.** 층수가 선언되면 단위가 사람 크기를 얻고, 예산이 열리고,
   눌린 변형이 게이트에 걸린다.
7. **윗면을 말하라.** 약한 문장 10개 전부 평지붕이었다. ArchShapeNet saliency가 보는 곳이
   탑이다. 지붕 어휘(gable/saltbox/butterfly/mansard/grade smooth/top_profile)나
   극단 대비 스택으로 실루엣의 상단을 설계하라 — 잔여물로 두지 마라.
8. **반복하려면 축을 통일하고 대비를 올려라.** split×2는 같은 along + contrast 상승 +
   방 아닌 진짜 골목(gap ≥ 8m)일 때만 계곡이 된다. 직교 재분할은 블록 다지기다.

## BIG 운영 규칙 (문헌)

- **지배 무브는 하나.** 2차 조작은 그 무브의 필연적 귀결만. 무브 둘을 병렬하면
  "필연성(inevitability)"이 깨지고 임의로 읽힌다.
- **극단화.** VIA는 한 코너만 142m, 나머지 셋은 지상. 미지근한 파라미터는 잔여물로 읽힌다.
  극단은 세운 쪽이 아니라 눌린 쪽에서 만들 수도 있다(둘레를 0.16으로).
- **실루엣 판독.** 무브가 한 시점의 외곽선만으로 판독되지 않으면 실패다.
- **위계.** 주 볼륨 하나가 지배하고 보조 볼륨은 그것을 강화한다. 동급 볼륨 경쟁 금지.
- **10초 스케치 환원.** 문장이 10초 다이어그램 하나로 그려지지 않으면 기각.

## why의 형식 (diségno 5칸)

`why`는 수사가 아니라 다이어그램의 서술이다: **입력(제약·프로그램) → 연산자 →
변형(무엇이 어떻게 달라지나) → 기능(그 변형이 사는 이유) → 한계(어디서 멈추나)**
가 한두 문장 안에 읽혀야 한다.

## 체크리스트 (신작/재저작 통과 조건)

- [ ] 위상을 바꾸는 지배 무브가 정확히 하나인가?
- [ ] 오프너에 profile/unit/bar가 있는가?
- [ ] 비율×몸의 절대량을 암산했는가? (m 단위로)
- [ ] compress/expand 없이 말했는가?
- [ ] 비대칭이 필요한 자리에 `on:`이 있는가?
- [ ] storeys(또는 unit)를 선언했는가?
- [ ] 윗면(실루엣 상단)을 설계했는가?
- [ ] 실루엣만으로 무브가 판독되는가? 10초 스케치로 그려지는가?

## 9. 볼륨 높이 휴리스틱과 법정 층수를 구분한다

`fill._settled_to_parcel_height`의 조각 높이 조정은 구성 휴리스틱이다. 용적률÷건폐율로
얻은 평균값은 법정 최고층수가 아니며, 켜를 늘려 법규를 우회하는 저작 지침으로 쓰지 않는다.
과거의 높은 탑 실험은 해당 필지의 최신 지구단위계획을 확인하기 전 기록이었다.

현재 제한은 `design.maas.massv2.parcel_policy.policy_for(PNU)`와 `LegalSite.evidence()`에서
읽는다. `make_brief.py`가 그 증거를 저작 브리프에 넣는다. 최고층수와 미터 높이는 별개이며,
명시한 층수는 형상을 줄여도 사라지지 않는다. BOOK도 원 층수와 자체 층고를 보존한다.

층수 상한·저작 층고·실제 전달 높이·연면적을 함께 확인한다. 코드의 보수적 개념 층수
검사는 실별 평면과 실제 설계층수 검증을 대신하지 않는다. 층판·단면·프로그램이 바뀌면
이를 새 저작으로 기록하고 같은 사이클의 법규·배심·develop 경로로 확인한다.


## 10. 다양성 규약 (2026-08-31 — 수렴 사고의 부검 + 문헌)

한 라운드에서 "플린스+돌아선 탑" 가족이 24문장 중 10곳에 나왔고 심판 둘이
"interchangeable"이라 썼다. 부검: ①브리프가 새 단어 사용을 의무화(쿼터가 단일 재료 강제)
②거장 3인 페르소나 — 문헌이 약하다고 판정한 방식(Deng·Brucks·Toubia 2026: 창의적 유명인
페르소나 < 평범한 페르소나; 페르소나가 여럿이어도 LLM은 하나의 분포라 수렴 — 인간 다양성의
원천은 지식의 분할) ③수렴은 정렬의 전형성 편향이 근본 원인이라 프롬프트만으로 못 없앤다
(Verbalized Sampling, ICML 2026).

**규약 (근거 강도순):**
1. **다양성은 아카이브가 보증한다, 프롬프트가 아니라.** 새 문장의 수락 조건 =
   행동 기술자 칸(자세축×건폐×오프너)이 비었거나 기존 점유자보다 높다.
   유일하게 구조적으로 붕괴 불가능한 방법(QDAIF·In-context QD·ARCH-Elites·Autodesk 선례).
   기계는 이미 있다: `book_language/quality_diversity_archive.py`의 StreamingMapElites.
2. **저작 프롬프트 필수 3요소**: CoT 단계 분해(코사인 0.377→0.255, Meincke 2024) +
   **보드의 기존 채택작 전량 제시 후 "이 전부와 형태 원리 수준에서 달라야 함"**
   (NoveltyBench: in-context regeneration이 프롬프팅 계열 최우수) + 차이 요구는 문장
   표면이 아니라 **Shah 상위 수준**(물리 원리 10점 > 디테일 1점)으로 명시.
3. **페르소나는 칸의 앵커다.** "SANAA처럼"이 아니라 "저층 마당형 칸만 말하는 저자"처럼
   평범-구체 명세로, 저자당 1회 병렬 호출(단일 프롬프트 다페르소나 금지 — Design Science
   2025). 사무소 철학은 형태가 아니라 **질문 절차**로 준다: OMA=프로그램 다이어그램이
   형태를 강제하는가 / BIG=대지의 실제 갈등 하나를 이 무브가 해소하는가 / SANAA=방들의
   관계가 등가인가.
4. **새 단어 쿼터 금지.** 이번 사고의 방아쇠. 새 단어는 어휘 명세에 소개만 하고,
   쓸 곳은 저자가 정한다.
5. **가족 상한**: 라운드당 같은 구성 가족 2안, 보드는 가족당 대표 1안(최고점).


## 11. 캐논 층과 정갈함의 법 (2026-09-01 — 클라이언트 판정 '다양한데 전형이 없고 정갈하지 않다')

**코퍼스는 두 층이다.** ①**캐논 층**(gen-canon*): 건축의 이름난 전형 — 원기둥 탑·판상
슬라브·필로티 슬라브·중정·테라스 — 의 정공법. §10의 차별 요구는 이 층에 적용하지
않는다(전형은 정의상 새롭지 않다 — 그래서 5개월간 아무도 못 썼다). 캐논 층은 모든
런에 항상 포함되는 기본 레퍼토리다. ②**실험 층**(그 외 전부): §10 그대로 — 보드와
형태 원리 수준에서 달라야 한다.

**정갈함의 법** (양 층 공통, BIG/OMA의 규율):
- 한 문장의 사건은 하나다. 두 번째 형태 동사는 첫 동사가 못 다한 말이 있을 때만.
- **부스러기 금지**: 지상의 잔상자·토막 가지·부속 돌기를 발치에 흘리지 마라 — 심판
  12라운드의 최다 감점 사유('산만', '파편', '퇴적')가 전부 이것이다.
- 실루엣 한 줄: 멀리서 윤곽 하나로 기억되는가를 저작 시점에 물어라.
- 동사 1개 문장은 합법이다(검증기 1..6) — 순수 압출은 문장이다.


## 12. 매스 스터디의 기율 (2026-09-01 — 3렌즈 검토의 수렴, 사무소 모방이 아니라 스터디의 기준)

세 렌즈(OMA·BIG·SANAA)가 각자의 말로 같은 결핍을 지적했다. 이는 사무소 취향이 아니라
매스 스터디가 잘 되었는가의 보편 기준이다:

1. **압력이 문장의 주어다.** why의 1칸(입력)은 반드시 명명된 대지 압력 — 이웃의 해,
   가로의 소음, 열린면의 조망, 과대한 홀. "X가 밀고 → Y가 물러선다"로 다시 쓸 수 없는
   캡션은 형태 얘기를 형태에게 하는 것이다. 철학 문장("물러섬은 한 번이면 충분하다")은
   원리이지 압력이 아니다 — 원리는 2칸부터.
2. **동심(centered) 이동은 아무것도 해소하지 않는다.** 스텝·마당·들림은 명명된 압력
   쪽으로 치우쳐라 — 오프셋이 곧 화살표다. 동심 버전은 봉투 잔여물로 읽힌다.
3. **두께는 역할을 따른다.** 사람이 사는 판은 층고를 갖지만, 덮는 판(지붕·처마·차양)은
   지붕 두께다 — canopy의 thin 인자(0.1~0.35 층고 몫)로 말하라. 19장에 한 층보다 얇은
   면이 하나도 없던 것이 이 조항의 이유다.
4. **단면에 갈등 하나.** 압출·적층·들림만으로는 내부가 침묵한다 — 과대한 방 하나가
   봉투를 밀어 변형시키는 문장을 라운드마다 최소 하나 시도하라(현 어휘로는 vault/
   gable의 큰 스팬 + 몸의 물러섬 조합까지; 경사 바닥 동사는 어휘 확장 대기).
