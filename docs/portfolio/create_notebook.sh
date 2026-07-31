#!/usr/bin/env bash
# 25_ACE NotebookLM 포트폴리오 자동 생성 스크립트
#
# 사용법:
#   1. 먼저 인증: nlm login (Chrome 열려서 Google 로그인)
#   2. 이 스크립트 실행: bash docs/portfolio/create_notebook.sh
#
# 결과:
#   - "25_ACE Portfolio" notebook 생성
#   - 7개 소스 파일 업로드 (memory/portfolio/*.md)
#   - 4페이지 포트폴리오 report 자동 생성
set -e

NLM="/c/Users/SOGANG1/AppData/Roaming/Python/Python313/Scripts/nlm.exe"
SOURCES_DIR="/d/DevCache/claude-data/projects/D--Data-25-ACE/memory/portfolio"

echo "=== Step 1: 인증 확인 ==="
$NLM login --check || { echo "❌ 먼저 'nlm login' 실행"; exit 1; }
echo "✓ 인증 OK"

echo ""
echo "=== Step 2: Notebook 생성 ==="
NOTEBOOK_OUTPUT=$($NLM notebook create "25_ACE Portfolio — 건축법규 AI 파이프라인" 2>&1)
echo "$NOTEBOOK_OUTPUT"
# notebook_id 추출 (출력에서 ID 파싱)
NOTEBOOK_ID=$(echo "$NOTEBOOK_OUTPUT" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
if [ -z "$NOTEBOOK_ID" ]; then
  echo "❌ notebook_id 파싱 실패"
  exit 1
fi
echo "✓ Notebook ID: $NOTEBOOK_ID"

echo ""
echo "=== Step 3: 소스 7개 업로드 ==="
for f in \
  "$SOURCES_DIR/notebooklm-source.md" \
  "$SOURCES_DIR/overview.md" \
  "$SOURCES_DIR/architecture.md" \
  "$SOURCES_DIR/core-modules.md" \
  "$SOURCES_DIR/agent-validation.md" \
  "$SOURCES_DIR/differentiation.md" \
  "$SOURCES_DIR/README.md"
do
  if [ -f "$f" ]; then
    echo "  uploading $(basename $f)..."
    $NLM source add "$NOTEBOOK_ID" "$f" || echo "    ⚠ failed: $(basename $f)"
  fi
done
echo "✓ 소스 업로드 완료"

echo ""
echo "=== Step 4: 4페이지 포트폴리오 리포트 생성 ==="
$NLM report create "$NOTEBOOK_ID" \
  --format "Create Your Own" \
  --language "ko" \
  --confirm \
  --prompt "$(cat <<'EOF'
업로드된 소스를 기반으로 25_ACE 프로젝트의 4페이지 포트폴리오를 생성하세요.

각 페이지는 정확히 약 500단어, 다이어그램(ASCII 또는 mermaid) + 표 + 핵심 수치 포함.

# Page 1 — Overview & Demo
- 한 줄 요약: 주소 한 줄 → 건축법규 42 + §119 지반레벨 + 8종 규제선 + GA 매스 최적화
- 8 step 데모 시나리오 (주소 → PNU → 토지 → 법규 → datum → 규제선 → 매스 → 시각)
- 검증 결과 표 (라이브 8 PNU, 정확도 11m, 178+ tests, 9 commits)
- "진짜 건축설계처럼" 가능한 6 가지 증명

# Page 2 — System Architecture
- 4 라이브 서비스 다이어그램 (CF Pages × 2 + Worker + Railway + Oracle VM)
- Tech Stack 표 (Frontend/Backend/DB/AI/Geometry/Agents/DevOps)
- Data Pipeline 흐름 (datum 예시: 주소 → Vworld → UTM → Open-Meteo → §119 가중평균 → 6 케이스)
- 모노레포 구조 (ARR + AG-light + AG)

# Page 3 — Core Modules
- Module A: Law Pipeline (Neo4j 31K nodes, 58법령, 7-stage hybrid search)
- Module B: §119 Datum Plane (Phase 1~2D-3, 9 commits, 6 케이스 표)
- Module C: 정북일조 Envelope (LOCKED SPEC §86①제2호 H=2d, 3-Layer 보호)
- Module D: NSGA-II Mass Optimization (10 알고리즘, Pareto front)

# Page 4 — Agent System & Validation
- Agent Architecture (Hermes + ACE MCP 57 tools + A2A protocol)
- 9 commits 시퀀스 + Roadmap (NGII 5m, §86 정북인접, Phase 4 분할)
- Validation Framework 표 (178 tests, Playwright, LOCKED SPEC, 정확도)
- 차별화 비교표 + B2B/B2C/B2G 활용 시나리오
EOF
)"

echo ""
echo "=== ✅ 완료 ==="
echo "Notebook URL: https://notebooklm.google.com/notebook/$NOTEBOOK_ID"
echo ""
echo "다음 단계:"
echo "  - 위 URL 열어서 Report 확인"
echo "  - 'Studio' 탭 → '오디오 개요' (팟캐스트 자동 생성)"
echo "  - 'Studio' 탭 → '학습 가이드' / '브리핑 문서' 추가"
echo "  - 'nlm download' 로 PDF/audio 다운로드"
