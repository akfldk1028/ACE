# 선행연구 3축 폴더 및 PPT 구성 설계

## 목적

선행연구 자료를 서로 혼동되지 않는 세 연구 축으로 분리하고, PPT에서는 각 축을 한 장씩 설명한다.

1. `legal`: 건축법규 자동검토와 graph reasoning
2. `mass`: 건물 매싱 생성과 최적화
3. `mas`: Multi-Agent System 협업

## 폴더 구조

```text
collected_papers/
├─ legal/
│  ├─ SGR_BIM_2026.pdf
│  ├─ SELECTED_PRIMARY_PAPER_SGR_BIM_2026.md
│  └─ figures/
├─ mass/
│  ├─ EvoMass_2024.pdf
│  ├─ SELECTED_PRIMARY_PAPER_EVOMASS_2024.md
│  └─ figures/
├─ mas/
│  ├─ Text2BIM_arXiv_2408.08054_v2.pdf
│  ├─ SELECTED_PRIMARY_PAPER_TEXT2BIM_2026.md
│  └─ figures/
├─ PPT_PRIOR_RESEARCH_STORYLINE.md
└─ paper_index.md
```

- 기존 `maas` 폴더의 매싱 관련 자료는 `mass`로 정리한다.
- 기존 `multi_agent` 폴더의 Text2BIM 자료는 `mas`로 정리한다.
- 법규 자료는 기존 `legal` 폴더를 유지한다.
- 논문 Figure는 새로 그리지 않고 PDF 원본 Figure를 추출해 각 폴더의 `figures`에 둔다.
- 이동으로 깨지는 Markdown 상대경로와 색인 경로를 모두 갱신한다.

## PPT 구성

총 3장으로 구성하며 논문 한 편이 슬라이드 한 장을 담당한다.

### 1장 — Legal

- 논문: SGR-BIM
- 초점: 자연어 건축법규, IFC 모델, graph reasoning을 연결한 자동 적합성 검토
- 시각자료: 논문 원본 프레임워크 Figure 1개
- 본문: 핵심 방법 3줄, 정량 결과 1줄, 한계 및 25_ACE 연결 1줄

### 2장 — Mass

- 논문: EvoMass
- 초점: additive/subtractive 매스 생성과 typology-oriented 진화 최적화
- 시각자료: 논문 원본 생성·최적화 과정 Figure 1개
- 본문: 핵심 방법 3줄, 설계 탐색 의의 1줄, 한계 및 25_ACE 연결 1줄

### 3장 — MAS

- 논문: Text2BIM
- 초점: Enhancer·Architect·Programmer·Reviewer의 역할 분담과 오류 수정 환류
- 시각자료: 논문 원본 multi-agent workflow Figure 1개
- 본문: 핵심 방법 3줄, 검증 결과 1줄, 한계 및 25_ACE 연결 1줄

## 슬라이드 공통 형식

- 제목에 연구 축과 논문명을 함께 표시한다.
- 원본 Figure가 슬라이드 면적의 절반 이상을 차지한다.
- 본문은 4개 안팎의 짧은 bullet로 제한한다.
- 하단에는 논문 서지정보와 Figure 번호를 적는다.
- 각 논문별 30초 발표 대본을 Markdown에 제공한다.

## 완료 조건

- `legal`, `mass`, `mas` 세 폴더가 존재한다.
- 각 폴더에 선정 논문의 PDF, 상세 요약 MD, PPT용 원본 Figure가 있다.
- 모든 PDF가 `%PDF-` 서명을 가지며 첫 페이지 제목이 선정 논문과 일치한다.
- 모든 PNG가 정상적으로 열리고 슬라이드 사용에 충분한 해상도를 가진다.
- 통합 PPT Markdown이 정확히 3장의 슬라이드 구성을 제공한다.
- 기존 폴더명을 가리키는 현재 산출물의 Markdown 링크가 남지 않는다.
- PDF 및 논문 Figure의 내용을 임의로 재작성하거나 새로 그리지 않는다.
