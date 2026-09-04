# 저작 브리프 — 소유자들에게서 조립됨 (tools/make_brief.py)

출력은 {"schemes":[...]} JSON 하나뿐이다. 정확히 8문장. 각 scheme 키: name,
primary_language, secondary_language, formal_principle(한국어 한 문장),
dominant_gesture, reference_basis(사실만 또는 "저작 신작"), floor_height_m,
ops(각 {"op":..., 파라미터, "why": 입력→연산자→변형→기능→한계}).
모든 파라미터는 비율. 첫 op는 extrude|loop|aggregate|stack.

## 사고 절차 (CoT — 문장마다 이 순서로 why를 전개하라)
1) 이 대지·프로그램의 실제 갈등/질문 하나를 명시한다
2) 그 답이 되는 형태 원리를 한 문장으로 선언한다
3) 보드의 어떤 안과도 그 원리가 다른지 확인한다 (아래 보드 절 참조)
4) 원리를 동사 열로 번역한다 — 각 단어의 한계까지

## 심판 판정 원장 (기계 집계 - 손 복제 없음)
저작할 때 이 목록의 문장을 되풀이하면 같은 축에서 같은 점수를 받는다.

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
- **book:book:inflated:creative-021** — 최약축 CONCEPT 1.3 (전축 C1.3, F3.7, S1.3, E3.0) : Three plain boxes stacked with a step - no idea is claimed. / Three plain stacked boxes; no idea at all.
- **book:book:long_span_bridge:creative-045** — 최약축 FEASIBILITY 1.3 (전축 C2.0, F1.3, S2.0, E2.0) : Each piece stands, but the raised T reads as detached from the ground. / The upper slab hovers with nothing under it — not standable as shown.
- **book:book:notch:creative-037** — 최약축 CONCEPT 1.3 (전축 C1.3, F4.7, S2.0, E4.0) : A single clean box with a small notch - competent, entirely unmemorable. / A plain box with a tiny notch; nothing would be remembered.
- **book:neighborhood__02__program_neighborhood_active_bar__universal_0_8_b99c5ef711__book_case_64_overlap+expand__search_v5** — 최약축 SITE 1.3 (전축 C2.0, F3.3, S1.3, E2.3) : 7% coverage floating mid-parcel - this could stand on any site in the world without changing a line. / 7% coverage, 57% FAR - the parcel is left entirely unclaimed and the mass could stand on any lot.
- **extrude_kite_roof_adjacent_grade_high** — 최약축 CONCEPT 1.3 (전축 C1.3, F5.0, S2.3, E3.7) : A single box with a nearly flat roof plate; the raised corners are invisible at this scale. / A single box with a flat lid; the raised corners the caption promises do not register.
- **book:book:inflated:creative-036** — 최약축 CONCEPT 1.7 (전축 C1.7, F3.7, S1.7, E3.0) : Stacked boxes with a small side fin; the bend never appears. / Three plain boxes stacked; no proposition.
- **book:book:oblique_crystal:creative-057** — 최약축 SITE 1.7 (전축 C2.0, F3.0, S1.7, E3.0) : 8% coverage, centred. / 8% coverage, an object in the middle.

### 라운드 총평
- [vlm-agent06] The set is competent but cautious - the three I would advance, t13, t05 and t02, are the ones whose stated idea is actually present in the white model: a terraced section, a real slot between two bars, a ring draining to its court. I would also carry t14 forward as a wildcard, because it is the only
- [vlm-agent06] I would advance t02, t05 and t13, with t07 and t14 held for a second look - t02 because the court is made by the roofs rather than merely enclosed, t05 and t13 because they are the only schemes whose idea gets stronger as floors, cores and a facade are added, t07 for the one unforgettable silhouette
- [vlm-agent07] Only four schemes argue something the mass itself can say - t10's bar bent to the oblique boundary, t15's roofs draining into the court, t03's ring of gabled wings, and t09's carved monolith - and of those the first three would advance, with t09 carried forward as the memorable outlier despite its i
- [vlm-agent07] Only t15 arrives as a whole building - one operation, the inward-pitched ring, that is simultaneously the section, the roof, the water strategy and the public room, and it is buildable as drawn. I would advance t15, t10 and t02: the first for its idea, the second because its bend is genuinely produc
- [vlm-agent07] Only four schemes state one idea and then actually deliver it in the mass - t10's bar bent onto the oblique boundary, t15's ring of inward-pitching roofs, the folded halls t02/t05, and t09's slotted monolith - and those are what I would advance. A large part of the set fails the simplest test of all
- [vlm-book07] Only three schemes in this set are actually competition entries - t61, t55 and t63 - and t61 is the only one that both occupies its parcel and reaches a civic size, with a ring of inward-pitching bars that produces a court and an image at the same time; it should advance first, with t55's finger pla
- [vlm-book07] Only three schemes on this board propose a building rather than a scale check — t61, t63 and t55 — and t61 is the clear leader: it is the single alternative that occupies its parcel, makes a court, and would be recognised again. Below them sits a competent middle band (t47, t27, t42, t48, t51, t62) 
- [vlm-book07] Only a handful of these are buildings rather than models of buildings - t61 is the one scheme that both fills its parcel and states a single legible idea (a roofed ring around a court), and t55, t63 and t62 follow it with real mass and one clear move each. Below that sits a broad middle of competent


## 발전 챔피언 (부모를 이긴 변형 — 이미 코퍼스에 있음)
이 파라미터는 이미 판정을 받았다. 부모 쪽 값으로 되돌리는 문장은 같은 비교에서 진다.

- **loop_butterfly_open__d07_bar+** — ops[0].bar 0.23 -> 0.265 : 부모 loop_butterfly_open와의 눈먼 쌍비교에서 심판 1인 전원이 이 변형을 골랐다

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

## 현재 보드 (전량) — 아래 전부와 **형태 원리 수준에서** 달라야 한다
(같은 원리의 변주는 보드에 못 오른다 — 가족당 1석, 큐레이터가 계산함)

- O1 (4.07): a four-storey loop ring whose every bar carries a butterfly roof draining toward the court - a basin of roofs over a garden of rain
- O2 (4.04): two parallel four-storey bars split apart with a six-metre gap between them - the gap is a courtyard, not a seam
- O3 (3.99): a four-storey trapezoidal bar bent at its mid-point to follow the parcel's non-orthogonal boundary - the bar is cranked, not straight, its kink aligned with the parcel's oblique edge
- O4 (3.72): a three-tier diminishing stack whose top tier wears a butterfly roof draining toward the open face - a tower whose crown is a V pointing to the park
- O5 (3.69): a wide three-storey body whose entire roof is a smooth public ramp rising from the open face to the back wall - the building is a hill you walk up
- O6 (3.65): book:book:stepped:creative-055
- O7 (3.51): six two-storey wings arranged radially on a ring, each facing inward to a shared court, the ring open at the open-face corner - a Korean 튼ㅁ자 broken at one corner
- O8 (3.50): a five-storey faceted monolith with a full-height slot carved through its short axis - the slot is a room-depth void splitting the body into two flanks connected only above the slot
- O9 (3.47): book:cultural__03__program_cultural_court_bridge__universal_0_6_94e7aa1fb2__book_case_60_carve+offset__search_v5
- O10 (3.22): book:book:carved_void:creative-047
- O11 (3.14): a three-storey loop ring lifted one storey on pilotis - the court and the ground merge into a single public floor below the ring
- O12 (3.13): book:neighborhood__03__program_neighborhood_stepback_corner__universal_2_18_fa2543dcbd__book_combination_11_inscribe+intersect__search_v5
- O13 (3.04): book:book:oblique_crystal:creative-027

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

## 9. 한 켜는 볼륨이고, 볼륨에는 층수 상한이 있다 (2026-08-22 실측)

`fill._settled_to_parcel_height`는 **한 볼륨이라도** 용적률÷건폐율 층수를 넘으면
(의정부 4.2층 ≈ 12.5 m) 도형 **전체**를 그 비율로 되돌린다. 건물 전체 높이 제한이
아니라 **조각 하나의 높이 제한**이다 — 그래서 42 m 탑은 가능하지만, 그 탑이 18 m짜리
볼륨 두 개로 만들어지면 통째로 축소된다.

그러므로 **높은 도형은 더 여러 켜로 말해야 한다.** 같은 문장, 켜 수만 바꿔 실측:

| 문장 | n=2 (18 m 볼륨) | n=3 (12 m) | n=6 (6 m) |
|---|---|---|---|
| via57 (선언 6.25배) | 배달 4.24배 | **5.75배** | 6.25배 |
| kotchujip (선언 6.25배) | 배달 3.12배 | **5.73배** | — |

n=6이면 비율은 온전히 오지만 켜가 거의 같아져 Nishizawa가 거부한 막사가 된다.
n=3·contrast 1.6이 두 문장 모두에서 최선이었다(92% 배달, 켜 구분 유지).

**저작 규칙**: `stack`을 쓸 때 `height × 예산 ÷ n`이 12.5 m를 넘으면 n을 올려라.
`tools/contrast_audit.py <run>`이 선언·상한·기본·배달 네 열로 이걸 검사한다.


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
