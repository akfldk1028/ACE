# 법규 Graph DB·멀티에이전트 선행연구 PPT 자료 설계

## 목적

연구계획서와 발표 PPT에서 법규 Graph DB와 멀티에이전트 협업 선행연구를 글 위주가 아닌 논문 원본 도식과 짧은 연구 줄거리로 설명할 수 있도록 자료를 정리한다.

## 선정 논문

### 법규 Graph DB

Xiao, Z., Koh, P. T., Ma, J., & Cheng, J. C. P. (2026). *Automating Geometry-Intensive Compliance Checking in BIM: Graph-Based Semantic Reasoning Framework*. Automation in Construction, 189, 107038. DOI: 10.1016/j.autcon.2026.107038.

- 기존 프랑스 법률 KG 논문은 삭제하지 않고 보조문헌으로 유지한다.
- PPT의 법규 Graph DB 주 논문은 SGR-BIM으로 교체한다.
- 선택 이유: 건축법규, BIM, cross-modal knowledge graph, multi-agent coordination을 직접 결합하고 논문 자체에 전체 구조도가 포함돼 있다.

### 멀티에이전트 협업

Du, C., Esser, S., Nousias, S., & Borrmann, A. (2026). *Text2BIM: Generating Building Models Using a Large Language Model-Based Multiagent Framework*. Journal of Computing in Civil Engineering, 40(2), 04025142. DOI: 10.1061/JCCEE5.CPENG-6386.

- 현재 선정 논문을 유지한다.
- 선택 이유: 건축·BIM에서 전문 에이전트의 역할 분담과 검사–수정 환류를 명시적으로 구현했다.

## 시각자료 원칙

- 새 다이어그램은 제작하지 않는다.
- 논문에 수록된 원본 Figure만 PPT용 이미지로 추출한다.
- 이미지의 내용, 색, 텍스트는 재작성하지 않는다.
- 여백 제거와 해상도 보정만 허용한다.
- 모든 PPT 안내문에 논문명, 저자, 연도, Figure 번호와 DOI 출처를 명시한다.

## 추출할 원본 Figure

### SGR-BIM

- Fig. 1: SGR-BIM 전체 프레임워크
- Fig. 2: cross-modal alignment와 graph construction·reasoning 과정
- Fig. 4: compliance query의 knowledge graph schema와 대표 인스턴스

### Text2BIM

- Fig. 1: 네 전문 에이전트와 BIM 검사·수정 환류의 전체 흐름

## 산출물

### PDF

- `collected_papers/legal/SGR_BIM_2026.pdf`
- 기존 `collected_papers/multi_agent/Text2BIM_arXiv_2408.08054_v2.pdf` 유지

### 논문별 MD

- `collected_papers/legal/SELECTED_PRIMARY_PAPER_SGR_BIM_2026.md`
- 기존 `collected_papers/multi_agent/SELECTED_PRIMARY_PAPER_TEXT2BIM_2026.md`에 원본 Figure 사용 안내 보강

각 MD는 다음 내용을 포함한다.

1. 어떤 논문인지
2. 연구 문제와 필요성
3. 제안 방법과 데이터 흐름
4. Figure별 설명과 PPT에서 사용할 위치
5. 실험 설계와 핵심 수치
6. 연구 결과
7. 한계
8. 25_ACE와의 공통점·차이점
9. 연구계획서용 선행연구 문단
10. PPT용 한 문장·짧은 글머리표
11. 30–60초 발표 대본
12. PDF와 코드 공개 여부

### PPT용 원본 Figure 이미지

- `collected_papers/ppt_assets/legal_sgr_bim_fig1_framework.png`
- `collected_papers/ppt_assets/legal_sgr_bim_fig2_cross_modal_graph.png`
- `collected_papers/ppt_assets/legal_sgr_bim_fig4_kg_schema.png`
- `collected_papers/ppt_assets/mas_text2bim_fig1_workflow.png`

### 통합 줄거리 MD

- `collected_papers/PPT_PRIOR_RESEARCH_STORYLINE.md`

두 논문을 다음 순서로 연결한다.

1. 기존 문제: 법규·BIM·설계 업무가 분절돼 수작업 검토가 필요함
2. SGR-BIM: 법규 의미와 BIM 기하를 그래프로 정렬해 설명 가능한 자동검토 수행
3. Text2BIM: 전문 에이전트와 규칙검사기가 BIM 모델을 생성·검토·수정
4. 공통 한계: 공유상태와 근거·설계변경 이력의 통합, 국내 법규 적용, 분야 간 조정이 부족함
5. 25_ACE: Graph DB를 공통 설계상태로 사용해 대지·법규·주차·매스·평면·입면 에이전트가 근거 기반으로 협업

## PPT 구성

### 슬라이드 1 — 법규 Graph DB 선행연구

- 제목: SGR-BIM — 그래프 기반 건축법규 적합성 검토
- 중심 이미지: 원논문 Fig. 1
- 보조 이미지: Fig. 2 또는 Fig. 4 중 하나
- 본문: 문제, 방법, 결과, 한계를 각각 한 줄로 배치
- 하단 연결문: 국내 법규와 전체 설계상태 공유로 확장 필요

### 슬라이드 2 — 멀티에이전트 선행연구

- 제목: Text2BIM — 전문 에이전트의 BIM 생성·검토·수정 협업
- 중심 이미지: 원논문 Fig. 1
- 본문: 네 에이전트 역할, 검사–수정 환류, 실험 결과, 한계를 짧게 제시
- 하단 연결문: Graph DB 기반 근거·충돌·수정 이력 공유로 확장 필요

### 슬라이드 3 — 선행연구 공백과 제안 연구

- SGR-BIM이 제공한 것: 법규–BIM 그래프 추론
- Text2BIM이 제공한 것: 전문 에이전트의 반복 협업
- 남은 공백: 국내 법규, 설계 전 단계의 공유상태, 에이전트 간 근거 기반 수정 요청
- 제안: Graph DB 공유 설계상태를 사용하는 협업형 멀티에이전트 건축설계

## 검증 기준

- 두 PDF가 `%PDF-` 서명을 갖는지 확인한다.
- 각 Figure가 해당 논문의 정확한 Figure 번호·캡션과 일치하는지 대조한다.
- 추출 PNG가 PPT에서 읽을 수 있는 해상도인지 확인한다.
- MD의 서지정보, DOI, 실험 수치를 PDF 본문과 대조한다.
- 새로 그린 도식이 산출물에 포함되지 않았는지 확인한다.
- placeholder, 깨진 링크, 불균형 코드펜스가 없는지 검사한다.
