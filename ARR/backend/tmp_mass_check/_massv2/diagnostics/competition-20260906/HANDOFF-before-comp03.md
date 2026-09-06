# massv2 HANDOFF — 이걸 읽으면 바로 이어서 할 수 있다

대상: 다음 세션의 Claude, Codex 에이전트, MassAgent. 코드보다 이 파일과 `FLOW.md`를 먼저 읽는다.
갱신: 2026-09-06 10:18 comp02 두 트랙 배심·굽기 후 BOOK 실제 메시와 심사 그림의 불일치 발견. step 12 저작을 중단·보존하고 실제 메시 렌더/평단면을 수리 중이다. 다음 생산은 comp03 새 시대에서 전부 재심사한다. 사용자 후속 지시로 자율 반복 개선과 IR 구현 승인됨.
에이전트 폴더 정본: `D:/Data/25_ACE/agents/AGENTS.md` → `README.md` → `MassAgent/AGENTS.md` / `MASSAGENT.md`.

## 09-06 현재 작업 — 다음 승인 질문 없이 이어간다

**10:18 최우선 상태:** 실행 중인 생산 프로세스는 없다. `comp02`는 `step 12 / book-developer` pending으로 보존했으며 BOOK develop payload를 아직 쓰지 않았다. 아래 comp02 명령을 변경된 엔진으로 재개하지 않는다. 실제 원본 BOOK025는 연속 곡선/경사 솔리드인데 기존 렌더러는 5개 분석 band를 계단처럼 그렸다. 이 그림의 4.45점이나 다른 BOOK 점수는 실제 형상의 품질 증거로 사용할 수 없다. `diagnostics/competition-20260906/comp02-pre-exact-book-render-baseline/`에 보드·두 트랙·시트·상태·입력·생성 282파일(8.69MB)과 해시를 보존했다. comp01·comp02 모두 develop/되먹임 완료라고 기록하지 않는다.

현재 수리: solid_ir는 실제 SourceSurface 메시 렌더와 공통 world mesh 좌표 helper, delivery_integrity는 실제 메시 평면/단면 및 study의 원 LegalSite 보존, root는 명시적 growth=plan 저작이 무브리프 FAR 하한에 묻히는 선발 정책, legal_evidence는 공공 길 폭 감소 경로를 순수 함수로 진단한다. 생산 타일/판정/상태는 고치지 않는다. 선택 수정은 확정 면적표·물리·법규 게이트를 유지하며 관련 56검사 통과. 수리 후 같은 52 BOOK을 재수입하고 comp03 새 그림에 새로운 독립 배심·develop·되먹임까지 반복한다.

시트에서 BOOK이 전부 빠진 것은 인증 해시 변동이 아니었다. `study_sheet.py`가 실제 LegalSite를 좌표 없는 축약 객체로 바꿔 등록 건축선 검사에 실패했다. 실제 BOOK025 shape ID·certificate ID·GFA는 재건해도 정확히 같았다. 이 대지 정보 손실을 수리했으며 실제 등록 BOOK 회귀가 통과했다. 최종 그림·평단면 메시 연결 검증을 이어간다.

**현재 생산 정본은 `runs/cycle-comp02/state.json`이다.** comp01의 아래 이력은 보존 기록이며 현재 명령으로 재개할 대상이 아니다. comp02는 `inputs/gen-comp02.json`의 새 공간 저작 4안과 기존 BOOK 저작 52개를 모두 실행한다. baseline은 `diagnostics/competition-20260906/comp01-pre-area-and-frontage-baseline/`의 543파일과 SHA manifest다. 생산 프로세스가 살아 있으면 중복 실행하지 않는다.

실제 생성은 110/110 컴파일·문장 3개 선택, 실제 BOOK 수입은 25개로 전수 감사와 일치했다. 문장 새 배심 3인 검증 후 BOOK 새 배심 3인이 진행 중이다. 낮은 정원 22변형이 모두 법규·사용성·구성에 통과했지만 무브리프 FAR 하한 때문에 심사 전에 제외됐고, 두 동 안의 실제 사이 폭도 1.94m로 부족하다. `agents/MassAgent/docs/reports/comp02-direct-review.md`에 근거와 다음 조건을 적었다. 현재 사이클의 develop·되먹임까지 수행한 다음 선발/공간 의도 보존을 다음 경계에서 고친다.

이번 통합에서 명시적 `growth: plan`을 저작→BaseVolume→4×4→coverage→fill 전 경로에 연결했다. 네 안의 fit 전 실제 높이는 10.8/7.2/10.8/11.16m다(최종 수치 아님). develop은 공통 물리·구성·선언 높이 및 최종 실제 source의 법규를 통과한 자식만 쌍비교한다. 수치 소유자는 `massv2/delivery_gate.py`와 기존 법규 소유자다. 자식 없는 저작 시도는 고정하고 다음 재개에서 `-r2` 입력을 요청한다. root 통합 34검사와 orchestration 32검사 통과. 보고서 `authored-growth-policy.md`, `delivery-gate-extraction.md`.

BOOK 최신 필지 전수 감사는 52개 중 32개 면적·층수·건축선 인증 일치, 그중 구조/방 게이트 25개 통과다. 18개는 불연속 층 단면/메시 불일치, 2개는 층수로 기각한다. 원본 커널↔export 층 면적 최대 차이 6.489e-7㎡, 실제 전체 투영↔인증 최대 차이 1.785e-11㎡. `agents/MassAgent/docs/reports/book-delivered-area-audit-frontage.json`과 실제 생산 수입을 대조해야 한다. 법규는 도면 등록 건축선·차량불허 구간까지 적용했으며 최신 실조회는 `site-evidence-20260906-frontage.json`. 실측·허가용 좌표·실제 차량 출입 설계와 실별 프로그램은 미확인이다.

- 사용자가 현상설계 수준까지 반복 생성·평가·개선을 요청했다. 이전의 IR 착수/4·5·7·10번 결정 대기 상태는 이 지시로 갱신한다. 독립 에이전트 평가는 진행하되 실제 건축가 취향 검증과 동일시하지 않는다.
- 실제 PNU의 주소는 **의정부시 산곡동 684-1 / 공공1**이다. 아래 효돈동 표기는 이전 문서의 오기이며 기존 필지는 교체하지 않는다. 확인된 지구단위계획 규모 제한과 용도 분류는 `design/maas/massv2/parcel_policy.py`가 소유한다. 법정 최고층수와 높이(m)를 분리했으며 실측 표고·정확한 건축선/차량불허 선분·실별 프로그램은 미확인이다. 현행 원문 증거는 `agents/MassAgent/docs/reports/legal-evidence-independent.json`, 적용 후 실제 조회는 `site-evidence-20260906-after-policy.json`.
- 작업 계획/담당 경계: `agents/MassAgent/docs/competition-loop-plan-20260906.md`. MassAgent 브랜치 `codex/mass-competition-20260906`; 상위 저장소는 기존 `DK-BB-massv2`. 기존 사용자 변경을 보존한다.
- baseline은 `diagnostics/competition-20260906/baseline/`에 108개 파일과 해시 manifest로 보존했다. 새 era `20260906-0115`; 직전 보드는 `runs/board-archive-20260906-0115/`에 있다. 아래 명령의 comp01이 생산 중이며 상태 정본은 `runs/cycle-comp01/state.json`이다.
- IR 접촉·점유·중복 면적 결함은 독립 교차 검토 후 수정 완료했다. 법규와 BOOK 축척 면적까지 포함한 통합 121검사 통과, root 추가 13검사 통과. 실패 상태 저장 회귀를 포함해 사이클 23검사 통과. 새 era의 빈 보드 브리프 회귀도 수정·검증했다. 검사는 설계 품질 판정이 아니다. 자세한 기록은 MassAgent `docs/reports/`의 `solid-ir`, `delivery-integrity`, `parcel-policy-gate`, `cycle-repair` 보고서.
- 새 저작: `inputs/gen-comp01.json` 10안(typed shape/곡면·마당 포함), `inputs/book-comp01.json` 12안(연결 솔리드 컴파일 검사 통과). `inputs/book-comp01-with-baseline.json`은 이전 모델 저작 40안을 보존해 합친 52안이다.
- `agents/AGENTS.md`, MassAgent 시작 문서와 스킬 10개 정리 완료. 메인 runtime의 skills allowlist는 매스용 8개다. 링크·명령 경로와 실제 로딩을 검증했다. `mass-author`의 비표준 학습 메타데이터는 기존 런타임 호환을 위해 보존했다.
- 다음 순서: BOOK 전달 메시의 실제 층별 면적·전체 부품 복구와 52개 전수 감사 → 등록된 건축선 적용 → 새 저작으로 comp02 전체 사이클 → 독립 3인 배심·LLM 저작 develop 쌍심사·되먹임 → 실제 그림·평단면 검토와 반복. 생산 단계 수동 호출 금지.
- **현재 실제 상태:** comp01은 LLM 220변형 중 7개 선택, BOOK 생성 52/52·수입 47개, 양쪽 각각 독립 새 배심 3인, 채점·보드 굽기·픽셀 비교·3안 시트까지 수행했다. `step 12 / development-incomplete`: 높이 자동 변이 4개가 모두 같은 형상으로 정규화되어 비교 자식이 없다. `complete.json` 및 되먹임은 없다. 배심 점수 4.45는 공모 제출 수준의 증명이 아니다.
- **BOOK 전달 수치 오류:** 상위 t15의 인증 GFA 2,552.52㎡에 비해 실제 변환된 Manifold와 export 메시의 층 단면 합은 1,026.31㎡다. XY 변환과 다른 높이 배율의 제곱으로 면적을 계승했다. 높이 밴드 수를 부품 수로 잘못 적용해 중층 대리 형상 185.52㎡도 버렸다. `agents/MassAgent/docs/reports/book-comp01-delivered-area-diagnosis.md`. 코드 수리와 52개 전수 측정 중이며 기존 인증·점수를 최종 증거로 쓰지 않는다. 앞서 통과한 개별 검사는 이 실제 전달 경로 오류를 검출하지 못했다.
- 수정 전 현 보드·시트·두 트랙·입력·상태·develop 증거는 `diagnostics/competition-20260906/comp01-pre-area-and-frontage-baseline/`에 543파일 SHA-256 manifest로 보존했다. comp01은 이미 채점했으므로 미채점 restage 옵션으로 고칠 수 없다. 아래 명령은 comp01 기록용이며 변경된 엔진으로 재개하지 않는다. 다음 회차는 이 새 baseline을 지정한다.
- 공식 PDF를 실제 필지에 좌표 등록했다(similarity RMSE 0.0423m). 2m 건축한계선은 북동측·모서리·남동측이며 차량불허는 북동측·모서리 전체와 남동측 일부다. 단일 정책 소유자에 적용 중. 근거는 `agents/MassAgent/docs/reports/public1-coordinate-registration.md/.json`. 도면 등록과 실측 측량·실제 차량 진입 설계 검증을 구분한다.
- 문장 develop도 호스트 LLM이 정확한 부모 variant/shape에 묶인 4개 공간 대안을 저작하도록 연결했다. 외부 입력은 `inputs/parti-develop-<round>.json`, 별도 `development-pairs-authored` 영수증과 `runs/develop-<round>-authored`에 생성한다. 기존 자식 없는 develop 증거를 덮지 않는다. backend/bridge 계약과 검사: `agents/MassAgent/docs/reports/authored-development-contract.md`.
- 실제 동일성 원인 두 곳: 재구성 호출부가 자체 층고 대신 대지 층고로 높이 예산을 미리 올림; 배치 변형을 수동 복제하며 `extra.siting` 표지를 누락해 fit이 다시 배치함. 높이 선언은 `finalists.rebuild`의 자체 층고 계산에 맡기고 배치는 `spread_across_siting` 공통 소유자를 사용한다. 실제 3안의 shape ID·높이·GFA·건축면적이 원본과 정확히 같아졌다. 보고서 `agents/MassAgent/docs/reports/delivery-storey-identity.md`, root의 납품/export/중정/provenance 통합 30검사 통과.
- 미채점 재스테이지는 단일 cycle 안에서 수행한다. 기존 타일·키·private 판정 2개·상태·BOOK registry를 `runs/cycle-comp01/restage-evidence-001/`에 해시와 함께 복사 보존하고 새 jury generation 폴더를 쓴다. 이전 판정은 새 그림에 재사용하지 않는다. 성공한 생성 입력·포트폴리오는 그대로 보존한다. snapshot과 원본 영수증은 매 재개마다 재검증하며 이미 채점한 회차에는 허용하지 않는다. 독립 코드 검토 후 orchestration 31검사 통과. 이후 원래 명령으로 재개해도 되고 같은 이유의 옵션을 유지해도 중복 재스테이지하지 않는다.
- BOOK의 `lifted_court_slab`에서 8자리 export 격자상 정확히 공선인 세 점이 부동소수점 잔여 면적으로 `tiny_face`에 걸렸다. 좌표를 움직이지 않고 인접 두 면만 다시 삼각분할하여 경계·체적·단면·매니폴드를 보존했다. 동일 입력 pure builder 52/52, 기존 51개 메시·해시 불변. root의 export/최종 provenance 통합 10검사 통과. 넓은 기존 모듈 240검사는 수정 전후 동일한 18실패·5오류가 남는다. 상세: `agents/MassAgent/docs/reports/book-export-collinearity-fix-20260906.md`. BOOK 입력이나 게이트는 바꾸지 않았다.
- 첫 VLM 스테이지 전에 중정 내벽의 외벽 관통 표시와 깊이 소실을 수정했다. 내벽과 원래 모서리를 실제 지붕 구멍 투영 안에서만 표시한다. 평지붕·곡면·pit 포함 관련 114검사 통과, 실제 전후 그림 직접 검토, 형상·수치·외곽 실루엣 불변, pit 픽셀 차이 0. 기존 comp01 시트와 3안 원본은 `diagnostics/competition-20260906/pre-courtyard-render/`에 8파일+해시로 보존했다. 상세: `agents/MassAgent/docs/reports/courtyard-render-diagnosis.md`. 새로운 심사 그림은 생산 cycle에서 만든다.
- 사용자가 LLM·VLM·BaseVolume·4×4의 실제 연결을 재강조했다. 독립 감사로 실제 BOOK 52개 UnitBox, 유효·가역 행렬 88개, LLM 10안+기존 develop 1안의 입력 보존을 확인했다. 최종 시퀀스 sidecar에 실제 컴파일 메타데이터를 보존하도록 보완했다(형상·인증·PNG 불변 포함 16검사). 이미 완료된 cycle도 전체 영수증 해시를 확인하도록 빠른 반환 결함을 수정했고 Python 26검사 통과. 보고서 `agents/MassAgent/docs/reports/flow-provenance-audit-20260906.md`.
- 총괄이 실제 3안과 시퀀스를 직접 열어 검토했다. 진입·실 깊이·마당 연결이 아직 약하다. `agents/MassAgent/docs/reports/comp01-direct-visual-review.md`에 다음 수정 조건을 남겼으며 배심원에게 이 문서를 주지 않는다.
- 01:49 현재 comp01은 세 번째 생성 시도다. 앞 시도는 초기 저작 11개 중 10개가 통과했으나, 적합화 변형 220개 중 19개 처리에 약 9분이 걸렸다. 총괄이 해당 생성 프로세스만 확인 후 중단하고, 경계에서 extent·plan mesh 캐시를 적용했다. 두 개선을 함께 비교한 7개 fixture에서 전체 메시·면적·무게중심·접촉·단면·픽셀이 정확히 동일했고 적용 후 통합 검사 125개가 통과했다. 검사·허용오차·탐색 수량은 줄이지 않았다.
- 같은 중단 경계에서 typed shape 2안의 깨진 한글 설명을 UTF-8로 복구했다. 원본은 `diagnostics/competition-20260906/gen-comp01-before-text-repair.json`, 형상 입력은 정확히 동일하다. 위 명령에 `--repair-inputs`를 한 번 추가해 미완료 입력의 검증 영수증을 갱신하고 재시작했다. 이후에는 위 원래 명령으로 이어갈 수 있다. `comp01.failed-1`, `comp01.failed-2`를 보존하며 로그의 과거 FAIL과 현재 실행 상태를 구분한다. 완료·새 배심 산출물은 아직 없다.

```bash
cd D:/Data/25_ACE/agents/MassAgent
bash skills/mass-cycle/scripts/cycle.sh comp02 4 --agent-mode external --book-count 52 --book-payload D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/inputs/book-comp01-with-baseline.json --develop-count 4 --new-era delivered-floor-frontage-and-authored-plan-growth --baseline D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/diagnostics/competition-20260906/comp01-pre-area-and-frontage-baseline
```

exit 75는 `runs/cycle-comp02/pending.json`의 외부 저작/심사를 채운 뒤 **같은 명령**을 재실행한다. `complete.json`이 없으면 완료가 아니다. 현재 실행이 살아 있으면 중복 실행하지 말고 기존 프로세스 종료/상태를 먼저 확인한다. Windows에서는 Git Bash(`C:/Program Files/Git/bin/bash.exe`)를 사용한다.

## 변경 전 baseline — 현재 새 era의 보드 상태가 아님

의정부 산곡동 필지(PNU 4115011300106840001; 최신 면적·상한은 위 실시간 증거 JSON)에
매스 보드 **35석**(저작 7 + BOOK 28)이 새 시대(20260904-2107)로 앉아 있고 같은 URL에 발행돼 있다.
BOOK은 서브에이전트가 저작한 40개(`c260-book/payload-llm01.json`)를 필지 크기로 수입해 게이트를
통과한 것이고, 저작 라운드는 `agent08`이다. 이전 판은 `runs/board-archive-20260904-2107`에 통째로 있다.

## 09-06 최초 검토 기록 — 수정 전 문서와 실행 코드의 불일치

사용자 목표는 **현상설계 초기에 건축가가 선택·발전시킬 수 있는 매스 대안**이다.
문서 0번대, 현재 보드·납품 시트, 관련 코드를 대조하고 아래 문제를 재현했다.
상세 근거·수리 조건·IR 구현 제안은 **`REVIEW-2026-09-06.md`**를 읽는다.

- **사이클 재개 미작동**: `--from=8`을 줘도 앞 단계부터 실행한다. `skip()`은 정의만 있고
  호출되지 않는다. 실제 스테이지는 심사 파일을 삭제하므로 현재 재개 명령을 신뢰하면 안 된다.
- **BOOK 모드 불일치**: 현재 보드는 payload 저작이지만 `cycle.sh`의 다음 BOOK 실행은
  여전히 `recipe_fixture` 고정이다.
- **develop 미완료**: 사이클이 변이 생성 후 쌍심사·채점·코퍼스 반영을 호출하지 않고 완료를
  선언한다. BOOK이 1위면 develop 전체를 생략한다. 챔피언 책도 다음 런에 자동 포함되지 않는다.
- **납품 동일성 불일치**: 현재 추천 1안의 완성 타일은 용적률 125%, 같은 HTML의 시퀀스
  마지막 프레임은 198%다. 문장명으로만 시퀀스를 연결하고 변형/기하 정체성을 검사하지 않는다.
- **BOOK 추천 제외**: 실제 `study_sheet._picks('book-llm01', corpus)` 결과가 빈 목록이다.
  BOOK은 시트 하단에는 나오지만 상단 3안 추천 경로에서는 제외된다.
- **IR 단면 반례**: 처진 지붕 중앙 윗면은 6m인데 8m 수평 단면이 중앙을 포함한다.
  얇은 판의 아랫면도 `plan_at` 계약에 반영되지 않는다. 기존 높이 함수는 이미 있으므로
  일반화 작업은 계약 완성과 소비자 통합에서 시작한다.

재현: `diagnostics/review-20260906/verify_review.py`, 결과 `evidence.json`.
사이클은 격리 스텁 하네스로 제어 흐름만 검사했다. 생산 사이클·새 배심은 실행하지 않았다.
보드·심사·납품 파일의 전후 해시는 동일했다. 아래는 최초 재현 기록이며 현재 수정/검증 상태는 맨 위 진행 절과 담당 보고서를 읽는다.

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
| 8 | **`ARR/backend/tmp_mass_check/_massv2/REVIEW-2026-09-06.md`** | 현재 코드로 재현한 실행/납품 결함, IR 제안, 미확정 사용자 결정 |

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
| `seeds.py` · `profiles.py` | 필지 한계로 크기 잡은 매싱 가족 · 기본 평면 어휘 |
| `form.py` | 매스 = 4×4 아핀이 나르는 배치 볼륨(`MatrixForm`, `Placement`) |
| **`execute.py`** | 파티 → 배치 볼륨. `_VERBS`가 동사 소유자이며 `shape` 외부 저작 포함. **`delivered()`** = `realign` → `regulated` |
| **`regulate.py`** | 근접 정렬 스냅과 캐리어 겹침 가드. 임계값은 코드에서 읽는다 |
| `program.py` | 실별 소요면적표 → `resized_to` |
| `variations.py` | 건폐율 밴드별 복제(`spread_across_coverage`, full_ground 등) |
| `siting.py` | 열린 변 방향, `place_on_site` |
| `fill.py` · `legal_fit.py` | 법정 상한까지 성장 · 볼륨을 움직여 맞춤(`_BODY_SEPARATION_M`, 캐리어 불변) |
| `legal.py` | 필지 한계 한 번 가져와 넘김(`load_legal_site`, `plan_at`, 봉투) |
| `parcel_policy.py` | 원문 증거가 있는 필지별 제한·기본 용도와 보수적 층수 게이트. 법정 높이와 층수 분리 |
| **`compile.py`** | 밴드 → `SourceMass`. `_EDGE_TOLERANCE_M`, `_sheets_settled`, `_without_clip_waste`, `_own_figure` |
| `../source_geometry/ir.py` · `solid.py` | 실제 상·하면/점유/단면/접촉/부피. typed surface와 임의 평면 구멍. 곡면 표본 정책과 지원하지 않는 CSG 범위를 명시 |
| `plausibility.py` | 방이 되는가(`assess`, `slenderness_limit`) |
| `structure.py` | 서는가(`assess_standing`, `connectivity`) |
| **`composition.py`** | 구성됐는가: 규제선 최소 피복·지배도·tiers·lifted. `COMPOSITION_BANDS` |
| `family.py` | `family_key`(opener·지배 조작·자세) — 검증기·큐레이터·스윕이 같은 키 |
| `measure.py` · `postcondition.py` · `ablation.py` | 측정 · 문장이 말한 대로 됐는가 · 단어 하나 빼보기(침묵/틈 게이트) |
| `select.py` | leximin·격자 셀 선발과 spoken_force 계산의 소유자 |
| `render.py` | 액소노 PIL. `_ruled_faces` `_correspondence`(밴드 연속 → 루드 솔리드), datum 흙, 걷는 경사 |
| `author.py` · `llm.py` · `sampler.py` | LLM 저작·전송·표본(생산 저작은 서브에이전트 경로) |
| **`../../management/commands/generate_massv2.py`** | 런 명령. 실행→변형→성장→법규→게이트→선발→시퀀스 시트. 파티 생존 게이트, `_CELL_COUNT` |

### 3. BOOK 탐색 (`ARR/backend/design/maas/`)

| 파일 | 소유 |
|---|---|
| **`../../management/commands/generate_maas_creative_100.py`** | 명령. `--author-mode payload/llm/recipe_fixture/cache_pool` |
| **`creative_floor_portfolio.py`** | `build_creative_floor_portfolio_report`: 정규화→소스 컴파일→**슬롯 증가경로 매칭**→물리 후보→중복→형태 |
| `creative_program_author.py` | `authored_programs_from_payload`(페이로드 형식·검증), 캐시 풀 |
| `book_exploration_graph.py` | 카탈로그와 탐색 경로 그래프의 소유자 |
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
# 재개도 최초의 동일 명령·인자를 사용한다. 현재 comp01 명령은 맨 위에 있다.
```

BOOK도 같은 사이클에 포함한다. **현재 호스트 LLM 또는 지정 에이전트가 저자**가 된다.
`geometry_language/llm_adapter.py`의 GEOMETRY_AUTHOR_PROMPT_CONTRACT ·
BASE_SEED_SPECS · BASE_FORM_SPECS · AUTHOR_GEOMETRY_GATE_POLICY와
`creative_program_author.authored_programs_from_payload`를 읽고 payload JSON을 작성한다.
이미 작성한 payload는 아래처럼 전체 사이클의 입력으로 준다. 저작 대기 상태라면
`pending.json`의 지정 위치에 기록하고 최초 명령으로 재개한다.

```
cd D:/Data/25_ACE/agents/MassAgent
bash skills/mass-cycle/scripts/cycle.sh <라운드명> <문장수> --agent-mode external --book-count <BOOK수> --book-payload <payload.json>
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

1. **실제 생산 검증과 반복 개선**: IR 계약과 R1–R5 수리는 구현·교차 검토 완료. comp01 생성·BOOK·배심·굽기·시트·develop을 끝까지 실행하고 실제 이미지를 본다. 점수나 테스트 수로 현상설계 품질을 대체하지 않는다.
2. **일반화의 다음 범위**: typed 상·하면, 임의 평면/구멍, 실제 점유·접촉은 구현했다. 일반 3D interval CSG, 곡면 표본 오차의 보장, 관측 지형 접합은 미완료다. 새 저작으로 실제 전달을 확인하며 필요한 확장을 이어간다.
3. ~~BOOK 슬롯 배정이 순서 의존~~ → 증가경로 매칭으로 수정(위 표).
4. `full_ground` 변형의 필지 잔여 형상: 원래 논지가 유지되는지 실제 그림으로 평가하고 개선한다. 사용자의 자율 개선 지시에 따라 진행; 법규를 완화하거나 필지 모양을 근거 없이 지우지 않는다.
5. 절대 점수와 **쌍비교**: 독립 3인 develop 쌍심사를 사이클에 연결했다. 실제 생산 완주와 다음 회차 챔피언 반영을 확인해야 한다.
6. ~~`judge.sh`가 TILE 줄 개수만 센다~~ → `--verify`(채점기와 같은 읽기)로 검사, 거부되면 같은 심사원을 한 번 더 앉힌다.
7. 배심 취향 검증: 독립 익명 에이전트 심사는 진행한다. 실제 건축가의 판단과 대조한 검증은 아직 없으며 모델 3회를 인간 3인처럼 표현하지 않는다.
8. ~~develop이 심은 문장의 `why`가 변이값과 안 맞음~~ → 챔피언의 바뀐 op `why` 끝에 `Developed: gap 3.0 -> 4.5, …` 명시(`develop._with_developed_why`).
9. ~~스윕에 책 단위 중복 가족 검사 없음~~ → `family_key`로 같은 가족 두 번 안 뽑음(실측 16/14 → 16/16).
10. 한국 트랙: 공통 엔진·납품·심사 검증 뒤 정확한 과업지시서와 용도 분류를 붙인다. 현재 저작은 실제 산곡동 필지를 쓰는 공공시설 공간 조직 연구이며 효돈동 공모 과업을 이 필지의 사실로 옮기지 않는다.

## 함정 — 반드시

- `--new-era`는 cycle 옵션으로 실행하고 기존 BOOK 저작도 재수입·재심사한다. 재개는 같은 cycle 명령. 스테이지를 수동 재호출하면 심사 파일을 잃을 수 있다.
- **엔진(실행기·컴파일·렌더)이 바뀌면**: 굽기 → 픽셀 diff → 바뀐 라운드만 재스테이지·재심사·재채점. 안 바뀐 좌석 점수만 유효.
- 커밋은 바깥 저장소(`D:/Data/25_ACE`)에서. `ARR/backend`에서 커밋하면 안쪽 저장소로 들어간다.
- `.gitignore:130`이 `tmp_mass_check/*/`를 무시한다. 페이로드는 `git add -f`.
- 레거시 maas stage 테스트 12건(`test_maas_mass_stage`·`test_maas_program_massing`)은 **클린 HEAD에서도 실패**(7F+5E). 오늘 작업과 무관.
- pytest는 Django 픽스처 에러가 난다. `python -X utf8 manage.py test <module>`로.

## 산출물

- 보드·시트: `runs/board/`, `runs/study-after/study.html`
- 아티팩트(같은 URL): https://claude.ai/code/artifact/4ca086d7-f893-4034-9d3d-d37f5d6901a0
- 메모리 정본: `D:/DevCache/claude-data/projects/D--Data-25-ACE/memory/massv2-triple-review-2026-09-02.md` 끝 절
