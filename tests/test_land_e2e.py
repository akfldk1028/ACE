"""
Land Regulation System - End-to-End Integration Test
=====================================================
Tests the full flow: MCP Tools → ARR Django → law-domain-agents → Neo4j

Writes detailed log to tests/log.txt

Services required:
  - ARR Django :8000  (cd ARR/backend && python manage.py runserver 8000)
  - law-domain-agents :8011  (cd AG/agent/law-domain-agents && .venv/Scripts/python server.py)
  - Neo4j :7687  (docker start neo4j-graphiti)

Run: C:/Python313/python tests/test_land_e2e.py
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add MCP server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "AG" / "autogen_a2a_kit" / "AG-cli" / "mcp"))
import autogen_studio_server as srv

LOG_FILE = Path(__file__).parent / "log.txt"

log_lines = []

def log(msg: str):
    line = msg
    log_lines.append(line)
    print(line)

def log_section(title: str):
    separator = "=" * 70
    log("")
    log(separator)
    log(f"  {title}")
    log(separator)

def log_json(data, indent=2):
    """Pretty-print JSON with Korean characters."""
    text = json.dumps(data, ensure_ascii=False, indent=indent)
    for line in text.split("\n"):
        log(f"  {line}")


async def wait_for_services():
    """Wait for ARR and law-domain-agents to be ready."""
    import httpx
    for attempt in range(10):
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r1 = await c.get("http://localhost:8000/land/zones/")
                r2 = await c.get("http://localhost:8011/api/health")
                if r1.status_code == 200 and r2.status_code == 200:
                    return True
        except Exception:
            pass
        await asyncio.sleep(2)
    return False


async def test_1_service_health():
    """Test 1: Service health check."""
    log_section("TEST 1: Service Health Check")

    # ARR Backend
    log("\n[Q] ARR Django 백엔드 (:8000) 상태?")
    r = await srv.arr_law_health()
    d = json.loads(r)
    log("[A]")
    log_json(d)

    # Law agents
    log("\n[Q] Law-domain-agents (:8011) 상태?")
    r = await srv.law_health()
    d = json.loads(r)
    log("[A]")
    log_json(d)

    return "error" not in d


async def test_2_land_zones():
    """Test 2: List all 21 zoning types."""
    log_section("TEST 2: 21개 용도지역 목록 조회")

    log("\n[Q] arr_land_zones() - 전체 용도지역 건폐율/용적률 목록 조회")
    t0 = time.time()
    r = await srv.arr_land_zones()
    elapsed = (time.time() - t0) * 1000
    d = json.loads(r)

    log(f"[A] 응답시간: {elapsed:.0f}ms, zone 수: {d.get('count', '?')}")
    zones = d.get("zones", [])
    log(f"\n  {'용도지역':<20} {'건폐율':>6} {'용적률':>6} {'분류'}")
    log(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*10}")
    for z in zones:
        log(f"  {z['zone_name']:<20} {z['bcr_default']:>5}% {z['far_default']:>5}% {z['category']}")

    return d.get("count") == 21


async def test_3_pnu_resolve():
    """Test 3: PNU code validation."""
    log_section("TEST 3: PNU 코드 검증")

    pnu = "1168011200101280003"
    log(f"\n[Q] arr_land_resolve('{pnu}', 'pnu') - 서울 강남구 PNU 검증")
    t0 = time.time()
    r = await srv.arr_land_resolve(input=pnu, input_type="pnu")
    elapsed = (time.time() - t0) * 1000
    d = json.loads(r)

    log(f"[A] 응답시간: {elapsed:.0f}ms")
    log_json(d)

    return d.get("valid") == True


async def test_4_analyze_single_zone():
    """Test 4: Analyze with single zone (no law search)."""
    log_section("TEST 4: 단일 용도지역 분석 (법조항 검색 OFF)")

    log("\n[Q] arr_land_analyze('1168011200101280003', zones=['제1종일반주거지역'], include_law=False)")
    log("    → 서울 강남구 땅, 제1종일반주거지역으로 건폐율/용적률 확인")
    t0 = time.time()
    r = await srv.arr_land_analyze(
        input="1168011200101280003",
        input_type="pnu",
        zones=["제1종일반주거지역"],
        include_law=False,
    )
    elapsed = (time.time() - t0) * 1000
    d = json.loads(r)

    log(f"\n[A] 응답시간: {elapsed:.0f}ms")
    if "error" in d:
        log(f"  ERROR: {d['error']}")
        return False

    reg = d.get("regulation", {})
    log(f"  건폐율 상한: {reg.get('bcr_limit')}%")
    log(f"  용적률 상한: {reg.get('far_limit')}%")
    log(f"  매칭된 zone 수: {reg.get('matched')}")
    log(f"  제한사항: {d.get('restrictions', [])}")

    return reg.get("bcr_limit") == 60 and reg.get("far_limit") == 200


async def test_5_analyze_multi_zone():
    """Test 5: Analyze with multiple zones (strictest applied)."""
    log_section("TEST 5: 복수 용도지역 분석 (최엄격 적용)")

    zones = ["제1종일반주거지역", "제2종일반주거지역", "제3종일반주거지역"]
    log(f"\n[Q] arr_land_analyze(zones={zones}, include_law=False)")
    log("    → 3개 zone 중 가장 엄격한 건폐율/용적률 적용되는지 확인")
    log("    → 제1종(60/200) vs 제2종(60/250) vs 제3종(50/300) → 최엄격: 50/200")

    t0 = time.time()
    r = await srv.arr_land_analyze(
        input="1168011200101280003",
        input_type="pnu",
        zones=zones,
        include_law=False,
    )
    elapsed = (time.time() - t0) * 1000
    d = json.loads(r)

    log(f"\n[A] 응답시간: {elapsed:.0f}ms")
    reg = d.get("regulation", {})
    log(f"  건폐율 상한: {reg.get('bcr_limit')}% (기대: 50%)")
    log(f"  용적률 상한: {reg.get('far_limit')}% (기대: 200%)")
    log(f"  매칭된 zone 수: {reg.get('matched')}")

    for z in reg.get("zones", []):
        log(f"    - {z['zone_name']}: BCR {z['bcr_default']}% / FAR {z['far_default']}%")

    return reg.get("bcr_limit") == 50 and reg.get("far_limit") == 200


async def test_6_law_search():
    """Test 6: Direct law article search."""
    log_section("TEST 6: 법조항 직접 검색 (law-domain-agents)")

    log("\n[Q] law_search('제76조 용도지역안에서의 건축물의 건축제한', limit=5)")
    log("    → Neo4j에서 국토계획법 제76조 관련 법조항 검색")

    t0 = time.time()
    r = await srv.law_search("제76조 용도지역안에서의 건축물의 건축제한", limit=5)
    elapsed = (time.time() - t0) * 1000
    d = json.loads(r)

    log(f"\n[A] 응답시간: {elapsed:.0f}ms")
    if "error" in d:
        log(f"  ERROR: {d['error']}")
        return False

    results = d.get("results", [])
    log(f"  검색결과 수: {len(results)}")
    for i, r in enumerate(results[:5]):
        log(f"\n  [{i+1}] {r.get('law_name', '?')} {r.get('article', '?')}")
        log(f"      hang_id: {r.get('hang_id', '?')}")
        content = r.get("content", "")[:80]
        log(f"      내용: {content}...")
        log(f"      유사도: {r.get('similarity', 0):.3f}, stages: {r.get('stages', [])}")

    stats = d.get("stats", {})
    log(f"\n  통계: total={stats.get('total')}, vector={stats.get('vector_count')}, "
        f"relationship={stats.get('relationship_count')}")

    return len(results) > 0


async def test_7_analyze_with_law():
    """Test 7: Full analysis with law article search (the main use case)."""
    log_section("TEST 7: 종합 분석 (건폐율 + 용적률 + 법조항) ★ 핵심 시나리오")

    log("\n[Q] arr_land_analyze('1168011200101280003', zones=['제1종일반주거지역'], include_law=True)")
    log("    → 토지 규제 분석 + 관련 법조항 검색까지 전체 파이프라인")
    log("    → 이것이 ACE 에이전트가 최종적으로 사용할 메인 기능")

    t0 = time.time()
    r = await srv.arr_land_analyze(
        input="1168011200101280003",
        input_type="pnu",
        zones=["제1종일반주거지역"],
        include_law=True,
    )
    elapsed = (time.time() - t0) * 1000
    d = json.loads(r)

    log(f"\n[A] 응답시간: {elapsed:.0f}ms")
    if "error" in d:
        log(f"  ERROR: {d['error']}")
        return False

    # PNU info
    pnu = d.get("pnu", {})
    log(f"\n  [PNU 정보]")
    log(f"    PNU: {pnu.get('pnu', '?')}")
    log(f"    시도: {pnu.get('sido', '?')}, 시군구: {pnu.get('sigungu', '?')}")

    # Regulation
    reg = d.get("regulation", {})
    log(f"\n  [규제 결과]")
    log(f"    건폐율 상한: {reg.get('bcr_limit')}%")
    log(f"    용적률 상한: {reg.get('far_limit')}%")

    # Law articles (grouped by query: [{query, results: [{law_name, article, content, ...}]}])
    law = d.get("law_articles", {})
    article_groups = law.get("articles", [])
    errors = law.get("errors", [])
    log(f"\n  [관련 법조항] (총 {law.get('total_count', 0)}건)")
    flat_articles = []
    for group in article_groups:
        query = group.get("query", "?")
        results = group.get("results", [])
        log(f"    검색어: '{query}' → {len(results)}건")
        for r in results[:3]:
            flat_articles.append(r)
            log(f"      - {r.get('law_name', '?')} {r.get('article', '?')}: {r.get('content', '')[:60]}...")
    if errors:
        log(f"    검색 에러: {errors}")

    # Restrictions
    restrictions = d.get("restrictions", [])
    log(f"\n  [건축 제한사항]")
    for r in restrictions:
        log(f"    - {r}")

    return reg.get("bcr_limit") == 60 and len(flat_articles) > 0


async def test_8_collaboration_flow():
    """Test 8: Document the agent collaboration flow."""
    log_section("TEST 8: 에이전트 협업 흐름 (AutoGen Studio Team)")

    log("""
  [협업 흐름 설계 - SelectorGroupChat]

  사용자 질문: "서울 강남구 역삼동의 제1종일반주거지역 건폐율과 용적률은?"

  Step 1: Selector가 Land Analyst 선택
    Land Analyst → analyze_land_regulation(zones=['제1종일반주거지역'])
    결과: 건폐율 60%, 용적률 200%

  Step 2: Selector가 Law Researcher 선택
    Law Researcher → search_law_articles('용도지역 건축물 건축제한 건폐율')
    결과: 국토계획법 제76조, 시행령 제84조, 제85조 등

  Step 3: Selector가 Report Writer 선택
    Report Writer → 종합 보고서 작성:
      1. 토지 정보: 서울 강남구 역삼동, 제1종일반주거지역
      2. 건폐율/용적률: 60% / 200%
      3. 법적 근거: 국토계획법 시행령 제84조제1항제2호, 제85조제1항제3호
      4. 주의사항: 4층 이하, 주거 중심 용도 제한
    → TERMINATE

  [팀 JSON]: JSON_MODULES/teams/038_Land_Regulation_Analysis_Team.json
  [에이전트 3명]: land_analyst, law_researcher, report_writer
  [Tool 4개]: search_land_zones, analyze_land_regulation, resolve_land_pnu, search_law_articles
""")

    # Simulate the collaboration by calling each step
    log("  --- 시뮬레이션: 각 단계별 실제 API 호출 ---\n")

    # Step 1: Land Analyst
    log("  [Step 1] Land Analyst → analyze_land_regulation")
    t0 = time.time()
    r = await srv.arr_land_analyze(
        input="1168011200101280003",
        input_type="pnu",
        zones=["제1종일반주거지역"],
        include_law=False,
    )
    d1 = json.loads(r)
    reg = d1.get("regulation", {})
    log(f"    결과: 건폐율 {reg.get('bcr_limit')}%, 용적률 {reg.get('far_limit')}%")
    log(f"    소요: {(time.time()-t0)*1000:.0f}ms")

    # Step 2: Law Researcher
    log("\n  [Step 2] Law Researcher → search_law_articles")
    t0 = time.time()
    r = await srv.law_search("용도지역 건축물 건축제한 건폐율 용적률", limit=5)
    d2 = json.loads(r)
    articles = d2.get("results", [])
    log(f"    결과: {len(articles)}건 검색")
    for a in articles[:3]:
        log(f"      - {a.get('law_name', '')} {a.get('article', '')} ({a.get('stages', [])})")
    log(f"    소요: {(time.time()-t0)*1000:.0f}ms")

    # Step 3: Report Writer (synthesis)
    log("\n  [Step 3] Report Writer → 종합 보고서 생성")
    log("    (실제 AutoGen Studio 실행 시 LLM이 아래와 같은 보고서 작성)")
    log(f"""
    ┌─────────────────────────────────────────────┐
    │        토지 건축규제 분석 보고서              │
    ├─────────────────────────────────────────────┤
    │ 토지: PNU 1168011200101280003               │
    │       서울특별시 강남구                       │
    │ 용도지역: 제1종일반주거지역                   │
    │                                             │
    │ 건폐율 상한: {reg.get('bcr_limit', '?'):>3}%                            │
    │ 용적률 상한: {reg.get('far_limit', '?'):>3}%                            │
    │                                             │
    │ 법적 근거:                                   │""")
    for a in articles[:3]:
        name = a.get('law_name', '')[:20]
        art = a.get('article', '')
        log(f"    │   - {name} {art:<10}            │")
    log(f"""    │                                             │
    │ 건축 제한:                                   │
    │   - 건폐율 60% 이하                          │
    │   - 용적률 200% 이하                         │
    │   - 4층 이하 권장                            │
    └─────────────────────────────────────────────┘""")

    return True


async def test_9_stats():
    """Test 9: Query statistics after tests."""
    log_section("TEST 9: 쿼리 통계 확인")

    log("\n[Q] arr_land_stats() - 지금까지의 분석 쿼리 통계")
    r = await srv.arr_land_stats()
    d = json.loads(r)
    log("[A]")
    log_json(d)

    return True


async def main():
    log(f"Land Regulation System - E2E Integration Test")
    log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Services: ARR(:8000), law-domain-agents(:8011), Neo4j(:7687)")
    log(f"MCP Server: {srv.__file__}")

    # Wait for services
    log("\nWaiting for services...")
    ok = await wait_for_services()
    if not ok:
        log("FATAL: Services not available. Start ARR(:8000) and law-agents(:8011) first.")
        return

    log("All services ready.\n")

    tests = [
        ("1. Service Health", test_1_service_health),
        ("2. 21 Zones List", test_2_land_zones),
        ("3. PNU Resolve", test_3_pnu_resolve),
        ("4. Single Zone Analysis", test_4_analyze_single_zone),
        ("5. Multi Zone (Strictest)", test_5_analyze_multi_zone),
        ("6. Law Article Search", test_6_law_search),
        ("7. Full Analysis + Law ★", test_7_analyze_with_law),
        ("8. Agent Collaboration Flow", test_8_collaboration_flow),
        ("9. Query Stats", test_9_stats),
    ]

    results = []
    for name, func in tests:
        try:
            passed = await func()
            results.append((name, "PASS" if passed else "FAIL"))
        except Exception as e:
            log(f"\n  EXCEPTION: {e}")
            results.append((name, f"ERROR: {e}"))

    # Summary
    log_section("SUMMARY")
    total = len(results)
    passed = sum(1 for _, r in results if r == "PASS")
    log(f"\n  {passed}/{total} tests passed\n")
    for name, result in results:
        icon = "OK" if result == "PASS" else "FAIL"
        log(f"  [{icon:>4}] {name}")

    log(f"\n  MCP Tools tested: arr_land_zones, arr_land_resolve, arr_land_analyze, arr_land_stats")
    log(f"                    law_search, law_health, arr_law_health")
    log(f"  AutoGen Team: 038_Land_Regulation_Analysis_Team.json")
    log(f"  Agents: land_analyst, law_researcher, report_writer")

    # Write log file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    log(f"\n  Log written to: {LOG_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
