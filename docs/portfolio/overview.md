---
name: Page 1 — Overview & Demo
description: 한눈에 보는 25_ACE 프로젝트. 무엇을 만들었나 + 데모 시나리오 + 검증 결과.
type: project
originSessionId: 5fb8be34-8660-4347-81b7-6bf5ae10ee85
---
## 무엇을 만들었나

**도시 필지 건축법 자동 분석 + 매스 최적화 통합 시스템.**

사용자는 "서울특별시 강남구 역삼동 677" 주소만 입력하면 AI 파이프라인이:

- **42개 건축 규제 수치** (BCR, FAR, 정북일조, 채광사선, 가각전제, 인접대지 이격 등)
- **§119 지반 레벨** (시행령 §119 가중평균 datum 평면, Open-Meteo 90m DEM)
- **8종 규제선** (3D Cesium envelope: 정북일조 사선 + buildable_area + 도로 후퇴 등)
- **GA 매스 최적화** (NSGA-II 10종 알고리즘, Pareto front)

## 핵심 데모 (8 step)

```
[1] 주소 입력          서울특별시 강남구 역삼동 674-38
       ↓
[2] PNU 자동 추출      Vworld geocode → 1168010100106740038
       ↓
[3] 토지 데이터        Vworld Data API ×4 (용도지역, 면적, 공시지가, 폴리곤)
       ↓
[4] 법규 분석          42 규제 (Neo4j 31K nodes, 7-stage hybrid search)
       ↓
[5] §119 지반 datum    Open-Meteo 90m DEM → 6 케이스 분류 → 가중평균면
       ↓
[6] 규제선 8종 + 3D    정북일조 envelope (slope 2:1, H = 2d)
       ↓
[7] GA 매스 최적화     NSGA-II 10 알고리즘 → Pareto front
       ↓
[8] Frontend 시각화    Cesium 3D + DatumInfoCard + ConstraintSummary
```

## 검증 결과 (라이브)

| 항목 | 수치 |
|---|---|
| 라이브 검증 PNU | 8개 (강남/성북/한남/여의도/우동/평창/대관령) |
| 정확도 (18 landmark) | **도시 11m, 해안 3.7m, 산 63m** |
| 자동 테스트 | **178+ pass** (39 datum + 167 land 회귀) |
| LOCKED SPEC | Session 14 envelope 12회+ 검증 박제 |
| Git commits | 9 commits (datum 시리즈) |
| 배포 서비스 | 4서비스 라이브 |

## 진짜 건축설계처럼 ✅

1. PNU/주소 입력 → §119 datum 자동 (Vworld + Open-Meteo)
2. Cesium 3D envelope이 terrain 위 정확히 위치 (Z축 일치)
3. 6 케이스 자동 분류 (FLAT / SLOPE_LE3M / SLOPE_GT3M / ROAD / NEIGHBOR_AVG)
4. 사용자 시각 확인 (DatumInfoCard 카드 — H=48m 등)
5. 상업지/녹지 등 정북일조 미적용 zone에서도 datum 노출
6. Playwright 자동화 검증 통과

## 사용자 워크플로 (실제)

1. http://localhost:5173/design 접속
2. PNU 입력 또는 3D 지적도에서 클릭
3. 자동 로드: 대지면적, 용도지역, 42 규제, 지반 레벨, 규제선
4. OPTIMIZE 버튼 → NSGA-II 매스 최적화
5. Pareto front에서 Design 선택 → 3D 매스 시각화
