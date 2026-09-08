# massv2 — 행렬로 놓은 볼륨들

> 다음 세션 AI가 **이 파일만 읽고** 바로 작업할 수 있게 쓴 문서입니다.

## 왜 만들었나

기존 형태 언어는 **덩어리 하나에 면 조작**입니다 (`geometry_language/compiler.py`의 `_book_*_macro` 10종).
40×24×18 기준 박스로 최대 설정까지 밀어 실측한 결과, 자기 볼록껍질 대비 이탈이 **0.2~0.29에서 멈춥니다.**
OMA/SANAA/BIG 수준의 서로 다른 건축 언어는 이 표현으로 도달 불가능합니다.

진단은 저장소에 이미 적혀 있었습니다 — `source_geometry/stacked_volume_bank.py:1-20`:

> 86개 프로그램 중 80개가 **박스 하나 + 모디파이어 하나**다. 참조 경쟁작 매싱은
> **깨끗한 직교 볼륨 서너 개를 쌓고 어긋낸 것**이다. 지오메트리 층은 이걸 막은 적이 없다.
> **없었던 건 공급이다.**

## 무엇이 다른가

| | 기존 | massv2 |
|---|---|---|
| 표현 | 솔리드 1개 + 면 조작 | 프리미티브 N개 + 각자의 4×4 |
| 3D 불리언 | BOOK 매크로 11개에 **23회** | **0회** |
| `decompose()` | 11회 | **0회** |
| 법정 맞춤 | 전역 강체 포즈 1개, 실패 시 CSG로 절삭 | (예정) 볼륨별 행렬 보정 |
| 신원 해시 | 3곳에서 기록 | **기록 안 함** (아래 참조) |

## 파일 (전부 200줄 이하로 유지할 것)

```
form.py      Placement(role, matrix, kind) / MatrixForm / place() — 저작
compile.py   MatrixForm → SourceMass. 밴드 절단 + 2D shapely만
measure.py   볼록도·보이드·밴드 프로파일. 납작하게 안 누름
__init__.py  공개 API 8개
```

**파일이 300줄을 넘으면 쪼개십시오.** 이 폴더가 존재하는 이유의 절반이 그겁니다.

## 핵심 설계 결정 3개 (바꾸기 전에 읽을 것)

### 1. 신원 해시를 안 만든다

`geometry_authority`를 `"matrix_form_analysis"`로 둡니다. authored 3종
(`authored_projected_surface_payload` 등)으로 바꾸거나 `profiled_` 표면을 내보내는 순간
`CertifiedMassArtifact` 인증 계층이 깨어나고, **2026-08-13 하루 종일 p20을 죽인
`final_geometry_hash` 불일치**에 그대로 걸립니다. 형태 언어를 증명하기 전에는 건드리지 마십시오.

### 2. 납작하게 누르지 않는다

오늘 측정 실수를 **두 번** 했고 둘 다 같은 원인입니다:
- 메시 삼각형을 전부 합쳐 실루엣 → **잘라낸 면이 파인 자리를 메움**. 오퍼레이티브 5종을 "죽었다"고 오진
- 볼륨을 높이 무관하게 합집합 → **지붕이 중정을 덮음**. 같은 5종이 보이드 0.000

그래서 `measure.py`는 **밴드마다** 재고 두께로 가중합니다. 분모는 항상
`minimum_rotated_rectangle` — 축정렬 상자를 쓰면 45° 돌린 솔리드가 0.52로 읽힙니다 (방향을 재는 것).

### 3. metadata를 비우면 후보가 통째로 사라진다

`SourceMass.signature()`(`source_geometry/ir.py:113`)가 metadata를 `props["source_signature"]`로 만들고,
`design/maas/selection/` 의 **모든 다양성 쿼터**가 거기서 읽습니다.
`primary_language` / `formal_principle` / `dominant_gesture`를 비우면 전부 "unknown" 한 가족으로
뭉쳐 `refine_final_review_set`에서 잘려나갑니다. `compile._metadata()`가 이걸 채웁니다.

## 문헌 근거

- **BuildingBlock** (SIGGRAPH 2025) — 건물 매싱 SOTA가 축정렬 박스 `[위치,크기,클래스]`의 무순서 집합.
  불리언은 창·문 붙이는 부재 스케일에만
- **PrimitiveAnything** (SIGGRAPH 2025) — 프리미티브마다 `(클래스,이동,회전,스케일)`, CSG 0회.
  ⚠️ GPL-3.0이므로 **코드는 쓰지 말 것**. 아이디어만
- **CoMa** (arXiv 2601.08464) — 표현이 우리와 동일(footprint + bottom/top). 그런데 Site IoU 0.05
  → **VLM에게 형상을 직접 그리게 하면 안 되고 프로그램을 저작하게 해야 한다**

## 아직 안 한 것

- [ ] 법규 컨텍스트 연결 (`book_language/legal_floor_field.py:54 materialize_legal_floor_field`)
- [ ] 볼륨별 법정 맞춤 — 전역 강체 포즈(`whole_solid_affine_fit_infeasible`) 폐기
- [ ] `grammar/legal_interpreter.py:180 interpret_sequence` 뒤에 접속
      (이 함수가 4개 생성 레인 + 비평 루프 전부에 일급 콜러블로 전달됨)
- [ ] LLM 저작 / VLM 쌍별 랭킹

전체 계획: `D:\DevCache\claude-data\plans\ethereal-nibbling-newt.md`
