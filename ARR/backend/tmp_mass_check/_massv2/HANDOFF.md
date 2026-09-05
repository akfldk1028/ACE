# massv2 HANDOFF — 이걸 읽으면 바로 이어서 할 수 있다

대상: 다음 세션의 Claude, Codex 에이전트, MassAgent. 코드보다 이 파일과 `FLOW.md`를 먼저 읽는다.
갱신: 2026-09-05 밤.

## 지금 상태 한 문단

효돈동 필지(PNU 4115011300106840001, 건폐율 60% = 1,497.877 ㎡, 용적률 250% = 6,241.962 ㎡)에
매스 보드 **35석**(저작 7 + BOOK 28)이 새 시대(20260904-2107)로 앉아 있고 같은 URL에 발행돼 있다.
BOOK은 서브에이전트가 저작한 40개(`c260-book/payload-llm01.json`)를 필지 크기로 수입해 게이트를
통과한 것이고, 저작 라운드는 `agent08`이다. 이전 판은 `runs/board-archive-20260904-2107`에 통째로 있다.

## 읽을 파일 — 이 순서로, 빠짐없이

경로는 `D:/Data/25_ACE/` 기준. 굵은 것은 건너뛰면 사고가 난다.

### 0. 문서 (코드 전에)

| 순서 | 파일 | 왜 |
|---|---|---|
| 1 | **`ARR/backend/tmp_mass_check/_massv2/HANDOFF.md`** | 이 파일. 상태·오늘 바뀐 것·남은 일·함정 |
| 2 | **`ARR/backend/tmp_mass_check/_massv2/FLOW.md`** | 12단계, 반드시 같이 도는 다섯, BOOK 규칙, 만지면 안 되는 것 |
| 3 | `ARR/backend/tmp_mass_check/_massv2/README.md` | 작업장 구조(inputs/tools/runs), BIG/OMA/SANAA 32작품 |
| 4 | `ARR/backend/tmp_mass_check/_massv2/inputs/AUTHORING-CANON.md` | 저작 규범 8패턴. 문장을 쓰기 전에 |
| 5 | `ARR/backend/design/maas/massv2/REGULATING_ELEMENTS.md` | 규제 요소(Akin & Moustapha)와 `about:` 설계 |
| 6 | 메모리 `D:/DevCache/claude-data/projects/D--Data-25-ACE/memory/massing-study/README.md` → `definition.md` `practice.md` `korea.md` `literature.md` **`our-gap.md`** | 매스 스터디가 무엇인지. 우리 전제와의 간극(규모검토를 만들어 구성으로 채점받음) |
| 7 | 메모리 `massv2-triple-review-2026-09-02.md` 끝 절 · `maas-two-tracks-two-juries.md` §0 | 세션별 결함·수리 원장, 플로우 v3 확정 근거 |

### 1. 파이프라인 오케스트레이션 (사이클이 무엇을 부르는가)

| 파일 | 소유 |
|---|---|
| **`agents/MassAgent/skills/mass-cycle/scripts/cycle.sh`** | 12단계 한 명령. `--from=N`. 여기서 아래 스킬을 순서대로 부른다 |
| `agents/MassAgent/config/massagent.env` | `MASSV2_WS` `PY` `JUROR_MODEL` `BOOK_COUNT` `GROUND_CAPACITY_M2` |
| `agents/MassAgent/skills/mass-{author,validate,run,judge,curate,board,sweep}/SKILL.md` + `scripts/*.sh` | 단계별 스킬. **judge.sh**는 심사원 3인 + `--verify` |
| `agents/MassAgent/skills/lib.sh` | 스킬 공통 |

MassAgent는 **git 서브모듈**이다. 바깥 저장소에서 `git add`가 안 된다. `cd agents/MassAgent && git commit`. origin은 업스트림, **푸시 금지**.

### 2. 문장 → 매스 (massv2 패키지, `ARR/backend/design/maas/massv2/`) — 데이터 흐름 순

| 파일 | 소유 |
|---|---|
| `grammar.py` | 문장 = 사이트 파생 시드 위 조작 목록. `declared_height_m` |
| `seeds.py` · `profiles.py` | 필지 한계로 크기 잡은 매싱 가족 · 사각형이 아닌 평면 10가족 |
| `form.py` | 매스 = 4×4 아핀이 나르는 배치 볼륨(`MatrixForm`, `Placement`) |
| **`execute.py`** | 파티 → 배치 볼륨. 동사 44개. **`delivered()`** = `realign`(문장이 이름 붙인 선) → `regulated`. `_aggregate` pack/radial/pinwheel |
| **`regulate.py`** | 근접 정렬 스냅(방위 4°·면 1.2 m·층선 0.2층). 캐리어 겹침 90% 가드, 캐리어 위는 층선 스냅 제외 |
| `program.py` | 실별 소요면적표 → `resized_to` |
| `variations.py` | 건폐율 밴드별 복제(`spread_across_coverage`, full_ground 등) |
| `siting.py` | 열린 변 방향, `place_on_site` |
| `fill.py` · `legal_fit.py` | 법정 상한까지 성장 · 볼륨을 움직여 맞춤(`_BODY_SEPARATION_M`, 캐리어 불변) |
| `legal.py` | 필지 한계 한 번 가져와 넘김(`load_legal_site`, `plan_at`, 봉투) |
| **`compile.py`** | 밴드 → `SourceMass`. `_EDGE_TOLERANCE_M`, `_sheets_settled`, `_without_clip_waste`(구조 면제), **`_own_figure`**(12% 미만 깎임이면 자기 도형 유지) |
| `../source_geometry/ir.py` | `SourceMass`/`SourceVolume` IR. `warp` 6항, `top_walkable`, `body_height_m()`(datum 차감). **IR이 천장** |
| `plausibility.py` | 방이 되는가(`assess`, `slenderness_limit`) |
| `structure.py` | 서는가(`assess_standing`, `connectivity`) |
| **`composition.py`** | 구성됐는가: 규제선 최소 피복·지배도·tiers·lifted. `COMPOSITION_BANDS` 6자리(격자 2축) |
| `family.py` | `family_key`(opener·지배 조작·자세) — 검증기·큐레이터·스윕이 같은 키 |
| `measure.py` · `postcondition.py` · `ablation.py` | 측정 · 문장이 말한 대로 됐는가 · 단어 하나 빼보기(침묵/틈 게이트) |
| `select.py` | leximin·격자 셀 선발. `spoken_force = 0.75·lead + 0.25·support` |
| `render.py` | 액소노 PIL. `_ruled_faces` `_correspondence`(밴드 연속 → 루드 솔리드), datum 흙, 걷는 경사 |
| `author.py` · `llm.py` · `sampler.py` | LLM 저작·전송·표본(생산 저작은 서브에이전트 경로) |
| **`../../management/commands/generate_massv2.py`** | 런 명령. 실행→변형→성장→법규→게이트→선발→시퀀스 시트. 파티 생존 게이트, `_CELL_COUNT` |

### 3. BOOK 탐색 (`ARR/backend/design/maas/`)

| 파일 | 소유 |
|---|---|
| **`../../management/commands/generate_maas_creative_100.py`** | 명령. `--author-mode payload/llm/recipe_fixture/cache_pool` |
| **`creative_floor_portfolio.py`** | `build_creative_floor_portfolio_report`: 정규화→소스 컴파일→**슬롯 증가경로 매칭**→물리 후보→중복→형태 |
| `creative_program_author.py` | `authored_programs_from_payload`(페이로드 형식·검증), 캐시 풀 |
| `book_exploration_graph.py` | 카탈로그 134항목 · 경로 13,662 그래프 |
| **`geometry_language/llm_adapter.py`** | 저자 계약: `GEOMETRY_AUTHOR_PROMPT_CONTRACT` `BASE_SEED_SPECS` `BASE_FORM_SPECS` `AUTHOR_GEOMETRY_GATE_POLICY` |
| `geometry_language/affine_normalization.py` | 아핀 권위: 유닛 박스 기저 사슬 위 matrix4 **하나 이상** |
| `ARR/backend/tmp_mass_check/c260-book/payload-llm01.json` | 서브에이전트 저작 40 프로그램(정본 예시) |

### 4. 작업장 도구 (`ARR/backend/tmp_mass_check/_massv2/tools/`)

| 파일 | 소유 |
|---|---|
| `make_brief.py` | verdict_ledger → 저작 브리프 |
| `validate_authored.py` | 모르는 단어·범위 밖·**같은 책 같은 가족 두 번** 거부. `VERBS`가 실행기에서 파생 |
| `sweep_generate.py` | 넓게 생성, 검증기로 거름, 가족 중복 제거 |
| `band_probe.py` | `corpus()` — 모든 책(inputs/gen-*.json + runs/sweeps/*.json) 로드 |
| `finalists.py` | `rebuild()` — 좌석을 심사받은 그대로 재건(**`delivered_form` 경유**). `PNU` `BUILDING_TYPE` |
| **`vlm_shortlist.py`** | 스테이지·**`shape_id`**·`ride_anchors`(정체성 일치·자기 라운드 제외)·`--verify`·`--score`(앵커 중앙값 보정, 스프레드>1이면 raw) |
| `judge_tiles.py` | 경쟁 타일 렌더 + key.json |
| **`book_import.py`** | BOOK → 필지 크기(`_to_parcel_size`) → 서는가·방이 되는가 게이트 → 스테이지 |
| **`board_curate.py`** | 원장(shape_id 포함)·가족 1석·부분-전체 자리 예약·눈 동일군·**`--new-era`** |
| `pool_sheets.py` · `study_sheet.py` | 가족×출처 작업대 시트 · 3안 납품 시트 |
| `develop.py` | 1위 변이 → 쌍비교 → 챔피언(`why`에 바뀐 값 명시) → `inputs/gen-develop.json` |
| `contrast_audit.py` | 선언한 대비 4열(선언/상한/기본/배달) |

### 5. 데이터 (읽기만, 손으로 고치지 않는다)

| 경로 | 무엇 |
|---|---|
| `inputs/gen-agent0N.json` · `inputs/corpus-{big,oma,sanaa,korea}.json` · `inputs/authored-*.json` | 문장 책. 라운드=gen-agentNN |
| `runs/sweeps/*.json` | 스윕 책(코퍼스에 포함됨) |
| `runs/<round>/massv2-summary.json` · `parti-*.png` | 런 결과·시퀀스 시트 |
| `runs/vlm-<round>/{key.json,t*.png,r1..r3.txt,vlm-shortlist.json}` | 스테이지·판정·점수 |
| **`runs/board/{board-key.json,ledger.json,era.json,O*.png}`** | 보드 정본. 덮기 전 백업 |
| `runs/board-archive-<stamp>/` | 이전 시대 |
| `runs/study-<name>/study.html` | 납품 시트 |

## 한 사이클을 돌리는 법

```
cd D:/Data/25_ACE/agents/MassAgent
bash skills/mass-cycle/scripts/cycle.sh <라운드명> [문장수]     # 12단계, 실패 시 정지
bash skills/mass-cycle/scripts/cycle.sh <라운드명> --from=8      # 재개
```

BOOK 저작만 예외다. `--author-mode llm`은 OpenAI 크레딧이 없어 막혀 있으니 **서브에이전트가
저자**가 된다: `geometry_language/llm_adapter.py`의 GEOMETRY_AUTHOR_PROMPT_CONTRACT ·
BASE_SEED_SPECS · BASE_FORM_SPECS · AUTHOR_GEOMETRY_GATE_POLICY와
`creative_program_author.authored_programs_from_payload`를 읽고 페이로드 JSON을 쓴 뒤

```
cd D:/Data/25_ACE/ARR/backend
python -X utf8 manage.py generate_maas_creative_100 --count 40 --pnu 4115011300106840001 \
  --capacity-ceiling-m2 1497.877 --output-root tmp_mass_check/c260-book --run-id <id> \
  --author-mode payload --author-payload <payload.json>
cd tmp_mass_check/_massv2 && python -X utf8 tools/book_import.py <c260-book/id 절대경로> <id>
```

`recipe_fixture`는 데모용이다. 그걸로 돌리면 십자·L·중정만 나온다.

## 오늘(09-05) 무엇이 바뀌었나 — 커밋 순

| 커밋 | 내용 | 검증 |
|---|---|---|
| 78467be | FLOW.md 신설. BOOK이 필지 크기로 오고(`book_import._to_parcel_size`) 서는가·방이 되는가 게이트 통과 | 40 중 5 탈락(떠 있는 판 등) |
| 5cc1caf | BOOK 좌석 복귀(퇴거는 오답이었다) | 통과 16/42 → 25/38 |
| b245dbd | FLOW: 저자는 서브에이전트, 전후는 시대로 가른다 | — |
| d10629b | 서브에이전트 저작 40 프로그램 페이로드 | 40/40 게이트 통과 |
| 6dde677 | `execute.delivered()` = realign → regulated(캐리어 가드). `compile._own_figure` | massv2 26 테스트 통과, 7석 전부 섬 |
| 59f592c | **점수는 그림의 것**: `shape_id`가 key→shortlist→ledger→board, 앵커는 정체성 일치·자기 라운드 제외 | 보정 `median_drift` 작동, 11/11 |
| 다음 커밋 | 저작 BOOK 경로가 책 슬롯에 **증가경로 매칭**으로 붙는다(`creative_floor_portfolio.build_creative_floor_portfolio_report`, 픽스처 경로의 `augment`와 같은 원리) | 포트폴리오 30 테스트 통과. 순서 의존 실증: 로테이션 전 35/40 → **40/40**, 커밋 순서 40/40 그대로, 2초 |

## 왜 그렇게 했나 — 세 문장

1. BOOK이 못생겼던 건 언어가 아니라 **필지 없이·게이트 없이** 심사대에 올린 것이었다.
2. 덩어리로 읽히는 건 봉투 팔각형(꼭짓점 5.98→5.86, 무시할 만함)이 아니라 **정렬**이었고, `regulate.py`는 있었는데 아무도 안 불렀다.
3. **앵커가 부러져 있었다**: 엔진 변경으로 그림이 바뀐 좌석이 옛 점수로 앵커를 타 델타 스프레드 1.32, 자가 안 움직여 한 라운드가 raw로 기록됐다. 안 바뀐 그림이 0.4~1.0 떨어졌다.

## 남은 일 — 결과에 미치는 순

1. **IR 일반화**(가장 큼): 볼륨 = 다각형 × 높이라 곡선 평면·경사 지반·2축 곡면·아트리움을 못 말한다. 당선작 발화 상위 5가 전부 이것. 지붕 동사·datum은 특수 튜플.
2. 평면 어휘 10가족뿐. 곡선은 1 없이는 못 온다.
3. ~~BOOK 슬롯 배정이 순서 의존~~ → 증가경로 매칭으로 수정(위 표).
4. `full_ground` 변형이 비스듬한 필지에서 필지 모양 판이 된다(O12). 깨끗한 도형으로 바꿀지, 배심이 낮게 주는 걸로 둘지 **사용자 결정**.
5. 절대 점수 → **쌍비교**. 같은 그림도 타일당 ±0.5 흔들린다(cascade 4.33→3.75). develop은 이미 쌍비교.
6. ~~`judge.sh`가 TILE 줄 개수만 센다~~ → `--verify`(채점기와 같은 읽기)로 검사, 거부되면 같은 심사원을 한 번 더 앉힌다.
7. 배심 취향 검증 없음(문헌: VLM≈전문가 52%).
8. ~~develop이 심은 문장의 `why`가 변이값과 안 맞음~~ → 챔피언의 바뀐 op `why` 끝에 `Developed: gap 3.0 -> 4.5, …` 명시(`develop._with_developed_why`).
9. ~~스윕에 책 단위 중복 가족 검사 없음~~ → `family_key`로 같은 가족 두 번 안 뽑음(실측 16/14 → 16/16).
10. 한국 트랙 K0(보류).

## 함정 — 반드시

- `--new-era`로 보드를 비우면 BOOK부터 재수입. 스테이지는 심사원 파일을 지운다(`--from=N`).
- **엔진(실행기·컴파일·렌더)이 바뀌면**: 굽기 → 픽셀 diff → 바뀐 라운드만 재스테이지·재심사·재채점. 안 바뀐 좌석 점수만 유효.
- 커밋은 바깥 저장소(`D:/Data/25_ACE`)에서. `ARR/backend`에서 커밋하면 안쪽 저장소로 들어간다.
- `.gitignore:130`이 `tmp_mass_check/*/`를 무시한다. 페이로드는 `git add -f`.
- 레거시 maas stage 테스트 12건(`test_maas_mass_stage`·`test_maas_program_massing`)은 **클린 HEAD에서도 실패**(7F+5E). 오늘 작업과 무관.
- pytest는 Django 픽스처 에러가 난다. `python -X utf8 manage.py test <module>`로.

## 산출물

- 보드·시트: `runs/board/`, `runs/study-after/study.html`
- 아티팩트(같은 URL): https://claude.ai/code/artifact/4ca086d7-f893-4034-9d3d-d37f5d6901a0
- 메모리 정본: `D:/DevCache/claude-data/projects/D--Data-25-ACE/memory/massv2-triple-review-2026-09-02.md` 끝 절
