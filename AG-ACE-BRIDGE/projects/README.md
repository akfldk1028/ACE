# Projects Folder

24/7 AI Project Factory의 프로젝트 스펙 디렉토리입니다.

## 폴더 구조

```
projects/
├── queue/        # 대기 중인 프로젝트 스펙 (여기에 파일 드롭)
├── completed/    # 완료된 프로젝트
├── failed/       # 실패한 프로젝트
└── examples/     # 예제 스펙 템플릿
```

## 사용 방법

### 1. 프로젝트 제출

```bash
# 방법 1: 파일 드롭 (권장)
# YAML 또는 JSON 파일을 projects/queue/ 폴더에 드롭
cp my-project.yaml projects/queue/

# 방법 2: CLI 사용
python run_24_7.py submit --spec my-project.yaml

# 방법 3: 직접 생성
python run_24_7.py submit \
  --name "My API" \
  --description "Build a REST API" \
  --goal "Create endpoints" \
  --goal "Add auth"
```

### 2. 24/7 실행

```bash
# 오케스트레이터 시작
python run_24_7.py

# 프로젝트 상태 확인
python run_24_7.py list
python run_24_7.py status <project-id>
```

## 프로젝트 스펙 형식

### 최소 스펙

```yaml
name: "My Project"
description: "What this project does"
goals:
  - "First goal"
  - "Second goal"
```

### 전체 스펙

```yaml
name: "My Project"
description: "What this project does"

goals:
  - "First goal"
  - "Second goal"

requirements:
  functional:
    - "Feature 1"
    - "Feature 2"
  non_functional:
    - "Performance requirement"
  constraints:
    - "Technical constraint"
  dependencies:
    - "External dependency"

tech_stack:
  - "Python 3.11"
  - "FastAPI"

output_path: "./output/my-project"

agents:
  use_auto_claude: true
  use_ag_autogen: true
  use_ag_law: false
  preferred_agents:
    - "auto_claude_coder"
  excluded_agents: []

pipeline:
  pattern: "auto"
  max_iterations: 5
  parallel_limit: 3
  timeout_minutes: 60

priority: "medium"
auto_start: true
```

## 실행 흐름

```
1. 스펙 파일 드롭
   projects/queue/my-project.yaml
         │
         ▼
2. Watcher 감지
   ProjectWatcher가 새 파일 감지
         │
         ▼
3. 태스크 생성
   스펙 → 태스크들로 변환
         │
         ▼
4. 오케스트레이터 실행
   17개 에이전트가 협업
         │
         ▼
5. 결과 저장
   projects/completed/ 로 이동
```

## 에이전트 (17개)

| 그룹 | 에이전트 | 역할 |
|------|---------|------|
| Auto-Claude | Planner | 계획 수립 |
| Auto-Claude | Coder | 코드 구현 |
| Auto-Claude | QA Reviewer | 품질 검증 |
| Auto-Claude | QA Fixer | 이슈 수정 |
| AG Autogen | Research | 정보 수집 |
| AG Autogen | Analyst | 데이터 분석 |
| AG Autogen | Writer | 문서 작성 |
| AG Autogen | Reviewer | 리뷰 |
| AG Autogen | Coordinator | 조율 |
| AG Law | Case Analyzer | 판례 분석 |
| AG Law | Legal Researcher | 법률 조사 |
| AG Law | Risk Assessor | 리스크 평가 |
| AG Law | Compliance Checker | 규정 확인 |
| AG Law | Document Drafter | 문서 작성 |

## 예제

```bash
# 예제 스펙 생성
python run_24_7.py example

# 또는 복사
cp projects/examples/example_api_project.yaml projects/queue/
```
