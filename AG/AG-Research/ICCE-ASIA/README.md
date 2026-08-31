# ICCE-ASIA 2026 — massv2 논문 작업 폴더

## 확정 사실 (2026-08-31 확인)

- **학회**: IEEE/IEIE ICCE-ASIA 2026, **2026-10-28~30, 강원도 SAINT JOHN'S 호텔**
- **경로**: 서강대 AX대학원 스페셜 세션 (조성인 교수 주관, 박상훈 교수 경유).
  발표자 5명 등록비+출장비 지원. 참여 의사 회신 마감 08-31 23:59.
- **형식**: 2~6쪽, IEEE 2단, A4, ≥10pt. Word/LaTeX 템플릿 학회 사이트 제공
  (교수님이 LaTeX 템플릿 별도 제공 예정). 제출은 EDAS(https://edas.info/N35633),
  초록만 제출 불가 — 풀페이퍼.
- **언어**: **영어** (IEEE Xplore 게재 학회 — 스페셜 세션도 동일). 발표장 질의는
  한국어 가능성 있으나 원고·슬라이드는 영어.
- **미확인**: 논문 마감일 (사업단 공지 대기 — 수신 즉시 이 파일에 추기)

## 논문 계획 (4쪽 단신)

- **전략**: 시스템 단신을 여기, 완전판(건축사 눈먼 평가 + 다필지 + 절제표)은 저널
  (Automation in Construction급)로 확장. IEEE 단신 → 확장 저널은 표준 관행.
- **제목안**
  1. *Training-Free Architectural Massing: LLM Authoring, Computed Gates, and Blind
     VLM Juries over Real Zoning Envelopes*
  2. *The Judge Sees What the Renderer Shows: A Controlled Study of VLM-Juried
     Generative Massing*
- **주장 3 (전부 실측 원장 보유)**
  1. 기하 불변·렌더만 수정 → 심사 +0.9~1.2 — VLM 검증의 상계 = 렌더 충실도
  2. 같은 문장이 두 심사 자에서 4.25 / 2.83 — 매스 품질의 루브릭 상대성
  3. 선언-배달 정직성 게이트 도입 → 심사 통과율 45% → 90%
  - 배경 주장: 매스 전용 학습 가중치 0 (LLM-Modulo의 건축 실증)
- **필수 요건**: base volume 상세 명시 → `BASEVOLUME-SPEC.md` (Method §IR 소절로 조판)
- **Figure 4종** (렌더 산출물 기존 보유)
  1. 파이프라인 다이어그램 (신규 작성)
  2. 선택 보드: `ARR/backend/tmp_mass_check/_massv2/runs/board/sheet_K.png`, `sheet_O.png`
  3. 렌더 수정 전/후 + 점수쌍: `runs/judge-refix/` (winding stack 등)
  4. 깔때기 표: 형태 3,518 → 물리 2,746 → 심사 9/10 (ovs2 기준; ovs3-full 완료 시 갱신)

## 원장 (수치 출처)

- 메모리 정본: `memory/maas-two-tracks-two-juries.md` (실험·드리프트·컷 전부)
- 코드: `ARR/backend/design/maas/massv2/` · 도구: `ARR/backend/tmp_mass_check/_massv2/tools/`
- 커밋 계보(이번 주): 1b06064(렌더 깊이정렬) · 12303a6(볼트 실루엣+nest turn) ·
  a8db19b(canopy) · cf4360e(one-owner) · b0768de(큐레이터) · dd582e6(브리프 조립기)

## TODO

- [ ] 사용자: 참여 의사 회신 (마감 08-31 23:59)
- [ ] 논문 마감일 수신 → 여기 기록
- [ ] LaTeX 템플릿 수신 → `latex/` 폴더에
- [ ] 초안: Abstract → Method(IR·파이프라인) → Experiments(주장 3) → Limitations(사람 평가는
      확장판 예고) — "고" 신호 시 착수
