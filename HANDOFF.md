# HANDOFF — 2026-05-09 (Session 5 최종 종결: NGII 5m DEM + §119② 본래 임계값)

> 8 commit 누적 (Session 4+5 + 오늘) push 완료. origin/DK-BB 최신 `dee2e1f`.

## 최종 상태

✅ **사용자 원래 문제 다 해결**:
- envelope 한쪽으로 비스듬 (img_28~30 / img_31) → Phase C revert
- 대지 레벨 부정확 (90m DEM ±11m) → NGII 1:5,000 자체 호스팅
- §119② 임계값 8m 위반 → **본래 0.5/3.0m 복귀**
- §86 다이어그램 부합 (img_32) → 정사각형 4 vertex H=10m 균일
- envelope 시각 비대칭 → Step 3 ringTerrainMean

## 8 Commits (origin/DK-BB)

```
dee2e1f fix(tools): verify_envelope_profile slope_top H를 backend actual value로
5d3fc5e feat(land): NGII 5m DEM 도입 + §119② 임계값 본래(0.5/3.0m) 복귀
60bf607 fix(envelope): Phase C revert — north_mls.distance 복귀 (§86 다이어그램 부합)
5858f6b fix(tools): verify_envelope_coords / profile — LOCKED SPEC 실제 반영
da6cafc feat(land): NGII 수치지형도 SHP → 자체 DEM raster (Step 4 code)
84fdaf4 feat(frontend): §119 datum 시각화 + envelope LOCKED SPEC datum z 통일 (Step 3)
f548708 feat(land): datum 알고리즘 — edge sub-sample + median filter (Step 1)
d2ddb9d feat(land): NGII opentopodata sidecar + /elevation-grid endpoint
```

## 라이브 검증 (NGII 5m DEM, 4 강남 PNU)

| 주소 | NGII 5m | OM 90m | 효과 |
|------|---|---|---|
| 도곡동 467-3 (5 vert) | 15.00m ±0 | 18.00m ±0 | -3m 정확 |
| 도곡동 960 (29 vert) | 24.54m ±2.44 | 27.07m ±**4.00** | 노이즈 61%↓ |
| 개포동 660-11 (산기슭) | 25.39m ±11.30 | 28.47m ±11.00 | 실제 경사 정확 |
| **대치동 1028 (12 vert)** | **15.00m ±0** | 16.08m ±**8.00** | **90m noise 100% 흡수** |

→ NGII 5m가 도시 평탄지에서 90m 격자 노이즈 완전 흡수. §119② 본래 임계값 복귀.

## CLI 회귀 (전부 PASS)

| CLI | 결과 |
|-----|------|
| verify_envelope_coords (도곡동) | ✅ 5/5 (walls/slope/방향/H range/profile) |
| verify_envelope_profile (도곡동) | ✅ 2/2 ((0,10) + (25, 11.3 actual)) |
| verify_dynamic (BuildingContext 26) | ✅ ALL |
| **verify_all (9 PNU 5 zone)** | ✅ **9/9** (두 번 재현) |
| verify_datum_119 (도곡동, NGII 5m) | ✅ midpoint_elev_m=15.0 |
| datum unit tests (24) | ✅ 24/24 |

## NGII 1:5,000 SHP → DEM 변환 결과

```
입력:  D:/Data/NGII_DEM/seoul/ (4 도엽 37709002~005, 175 SHP)
출력:  D:/Data/NGII_DEM/seoul_dem.tif
크기:  1.2MB (1770×557 px @ 5m, 982,481/985,890 valid 99.7%)
영역:  EPSG:5186 bbox (lng 127.025~127.125, lat 37.475~37.500, 9×2.8km 강남 도곡 일대)
점군:  218,541 (등고선 N3L_F0010000 '등고수치' + 표고점 N3P_H0020000 '표고')
```

## 메모리 박제 (모두 갱신됨)

```
arr/datum-elevation/
├── README.md                     ✏️ Step 1~4 progress
├── data/
│   ├── glo30-srtm30-not-fit.md  🆕 글로벌 30m DEM 도시 부적합 검증
│   ├── no-free-5m-path.md       🆕 무료 5m DEM path 없음 (자체 호스팅 필요)
│   ├── contour-to-dem-path.md   🆕 SHP→DEM 학술 path + 라이브 4 PNU 결과
│   ├── vworld-no-elevation.md   ✏️ 2026-05-08 재확인
│   ├── ngii-5m-plan.md          (이전 박제, 90m 한계 박제됨)
│   └── open-meteo.md            (이전 박제)
├── tuning/
│   ├── algorithm-improvements.md 🆕 Step 1 + 임계값 복귀 (NGII 5m 4 PNU 결과)
│   ├── thresholds.md            ✏️ §119② 본래 0.5/3.0m 복귀
│   ├── known-issues.md          (이전 박제)
│   └── locked-spec.md           (이전 박제)
session14/
├── envelope-locked-spec.md      ✏️ Step 3 + Phase C revert 박제
└── auto-verify-cli.md           ✏️ verify CLI 검증식 갱신
```

## 다음 세션 작업 (선택)

### 우선순위 1 — 사용자 시각 검증
- chromium F5 → 도곡동 467-3 검색 → envelope이 NGII 5m datum (H=15m) 위에서 솟는지 확인
- 다이어그램(이재인 §86 그림) 모양 부합 확인

### 우선순위 2 — 추가 도엽 다운로드 (정확도 확장)
현재 NGII raster 영역: 강남 도곡동 일대 9×2.8km만 cover. 다른 PNU 영역은 자동 Open-Meteo fallback 작동.

추가 영역:
- 잠실/송파 (1171): 도엽 37710 또는 37711 sub
- 성북/한남/평창: 도엽 37708 등
- 여의도/합정: 도엽 37708 또는 37707
- 부산 우동, 대관령: 별도 도엽

map.ngii.go.kr → 영역 사각형 → 추가 도엽 다운로드 → `D:/Data/NGII_DEM/seoul/` 폴더에 압축 풀기 → `python tools/ngii_contour_to_dem.py` 다시 실행.

### 우선순위 3 — Session 3에서 이월된 보류 옵션
- §119① 5호 도로 datum 활성화 (~150줄, road_centerline_wgs 전달)
- §86 인접대지 평균 활성화 (~150줄, Vworld 인접 polygon)
- Phase B sunlight slope per-floor clip (~100줄)
- TRELLIS Day 1 마무리 (B200, transform=None)

## 시작 명령 (다음 세션)

```
이 HANDOFF.md 위치: D:\Data\25_ACE\HANDOFF.md
origin/DK-BB 최신: dee2e1f

★ 즉시 권장: chromium 시각 검증 + 사용자 결과 보고
보조 1: 추가 도엽 다운로드 → 다른 PNU 영역도 NGII 5m
보조 2: Session 3 이월 옵션 (§119① 5호 도로 / §86 인접지)
```

## 측정값

| 지표 | 값 |
|------|-----|
| 코드 변경 누적 | 21 modified + 3 new (frontend + tools) |
| 라인 변화 | +1187 / -100 |
| commit | 8 (origin/DK-BB push) |
| 신규 메모리 | 4 파일 + 6 갱신 |
| 라이브 PNU 검증 | 4 강남 (NGII) + 8 batch (회귀) |
| verify CLI PASS | 5/5 + 2/2 + 26/26 + 9/9 |
| unit tests | 24 datum + 173 land 전체 |
