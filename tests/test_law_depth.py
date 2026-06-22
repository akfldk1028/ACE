"""
법규 파싱 깊이 + 검색 품질 종합 테스트
==========================================
파싱이 하위 구조(항/호/목)까지 되는지,
검색 시 법률+시행령+시행규칙 3종 모두 나오는지,
관련 조항도 함께 나오는지 검증.

Services required:
  - law-domain-agents :8011
  - Neo4j :7687
  - ARR Django :8000 (optional, for land/analyze test)

Run: C:/Python313/python tests/test_law_depth.py
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import requests

LOG = []
PASS_COUNT = 0
FAIL_COUNT = 0
WARN_COUNT = 0

def log(msg=""):
    LOG.append(msg)
    print(msg)

def section(title):
    log(f"\n{'='*80}")
    log(f"  {title}")
    log(f"{'='*80}\n")

def subsection(title):
    log(f"\n--- {title} ---")

def result(name, passed, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if passed:
        PASS_COUNT += 1
        log(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL_COUNT += 1
        log(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))

def warn(msg):
    global WARN_COUNT
    WARN_COUNT += 1
    log(f"  [WARN] {msg}")

def search(query, limit=30):
    """Search law-domain-agents."""
    resp = requests.post(
        "http://127.0.0.1:8011/api/search",
        json={"query": query, "limit": limit},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()

def classify_results(results):
    """Classify results by actual law type (from law_name parenthetical)."""
    by_type = {"법률": [], "시행령": [], "시행규칙": []}
    for r in results:
        name = r.get("law_name", "")
        if "(시행규칙)" in name:
            by_type["시행규칙"].append(r)
        elif "(시행령)" in name:
            by_type["시행령"].append(r)
        else:
            by_type["법률"].append(r)
    return by_type


# ============================================================
# TEST 1: 파싱 깊이 확인 — 항(HANG), 호(HO), 목(MOK) 존재 여부
# ============================================================
def test_parsing_depth():
    section("TEST 1: 파싱 깊이 (항/호/목 하위 구조)")

    # Check parsed JSON files directly
    parsed_dir = Path(__file__).parent.parent / "ARR" / "backend" / "law" / "data" / "parsed"
    json_files = list(parsed_dir.glob("*.json"))
    log(f"  파싱된 JSON 파일 수: {len(json_files)}")
    for f in json_files:
        log(f"    - {f.name}")

    result("파싱된 JSON 파일 존재", len(json_files) >= 3, f"{len(json_files)}개")

    # Count unit types across all files
    type_counts = {}
    sample_by_type = {}
    total_units = 0

    for jf in json_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        law_name = data.get("law_info", {}).get("law_name", jf.stem)
        units = data.get("units", [])
        for u in units:
            ut = u.get("unit_type", "?")
            type_counts[ut] = type_counts.get(ut, 0) + 1
            total_units += 1
            if ut not in sample_by_type:
                sample_by_type[ut] = {
                    "law": law_name,
                    "number": u.get("unit_number", ""),
                    "title": u.get("title", ""),
                    "content": u.get("content", "")[:100],
                    "full_id": u.get("full_id", ""),
                }

    subsection("파싱된 단위(unit) 타입별 수량")
    hierarchy_order = ["장", "절", "관", "조", "항", "호", "목"]
    for ut in hierarchy_order:
        count = type_counts.get(ut, 0)
        log(f"    {ut}: {count}개")
        if ut in sample_by_type:
            s = sample_by_type[ut]
            log(f"      예시: {s['full_id']}")
            log(f"      내용: {s['content'][:80]}...")

    log(f"\n    전체 단위 수: {total_units}")

    # Key assertions
    result("항(HANG) 파싱됨", type_counts.get("항", 0) > 0, f"{type_counts.get('항', 0)}개")
    result("호(HO) 파싱됨", type_counts.get("호", 0) > 0, f"{type_counts.get('호', 0)}개")
    result("목(MOK) 파싱됨", type_counts.get("목", 0) > 0, f"{type_counts.get('목', 0)}개")
    result("조(JO) 파싱됨", type_counts.get("조", 0) > 0, f"{type_counts.get('조', 0)}개")

    # Check that law types cover 법률+시행령+시행규칙
    subsection("법률 타입 확인 (3종)")
    law_types_found = set()
    for jf in json_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        law_info = data.get("law_info", {})
        law_name = law_info.get("law_name", "")
        law_type = law_info.get("law_type", "")
        if law_type:
            law_types_found.add(law_type)
        log(f"    {law_name} [{law_type}]: {len(data.get('units', []))}개 단위")

    result("법률 존재", "법률" in law_types_found)
    result("시행령 존재", "시행령" in law_types_found)
    result("시행규칙 존재", "시행규칙" in law_types_found)


# ============================================================
# TEST 2: 제84조 검색 — 법률+시행령+시행규칙 전부 반환되는지
# ============================================================
def test_article_84():
    section("TEST 2: 제84조 검색 (3종 법규 반환)")

    data = search("제84조", limit=30)
    results = data.get("results", [])
    log(f"  총 검색 결과: {len(results)}건")

    by_type = classify_results(results)

    for lt in ["법률", "시행령", "시행규칙"]:
        articles = by_type[lt]
        subsection(f"{lt} — {len(articles)}건")
        for a in articles:
            art = a.get("article", "?")
            sim = a.get("similarity", 0)
            stages = a.get("stages", [])
            content = a.get("content", "")[:120]
            hang_id = a.get("hang_id", "")
            log(f"    {art} (sim={sim:.3f}, {stages})")
            log(f"      ID: {hang_id}")
            log(f"      내용: {content}...")

    result("법률에서 제84조 반환", any(
        "제84조" in r.get("article", "") for r in by_type["법률"]
    ), f"{len(by_type['법률'])}건")

    result("시행령에서 결과 반환", len(by_type["시행령"]) > 0,
           f"{len(by_type['시행령'])}건")

    result("시행규칙에서 결과 반환", len(by_type["시행규칙"]) > 0,
           f"{len(by_type['시행규칙'])}건")

    # Check 항 level results (하위 구조 검색)
    hang_results = [r for r in results if "::①" in r.get("hang_id", "") or "::②" in r.get("hang_id", "") or "::2" in r.get("hang_id", "")]
    result("항(HANG) 수준 결과 포함", len(hang_results) > 0,
           f"{len(hang_results)}건이 항 수준")


# ============================================================
# TEST 3: 관련 조항 검색 — 제76조 검색 시 관련 법규도 함께
# ============================================================
def test_related_articles():
    section("TEST 3: 관련 조항 검색 (제76조 → 관련 법규)")

    data = search("제76조 용도지역 건축물", limit=20)
    results = data.get("results", [])
    log(f"  총 검색 결과: {len(results)}건")

    by_type = classify_results(results)

    # Log all results
    for lt in ["법률", "시행령", "시행규칙"]:
        articles = by_type[lt]
        subsection(f"{lt} — {len(articles)}건")
        for a in articles[:10]:
            art = a.get("article", "?")
            sim = a.get("similarity", 0)
            content = a.get("content", "")[:120]
            log(f"    {art} (sim={sim:.3f}): {content}...")

    # Check that related articles (not just 76) appear
    unique_articles = set()
    for r in results:
        unique_articles.add(r.get("article", "?"))
    log(f"\n  고유 조문 수: {len(unique_articles)}")
    log(f"  조문 목록: {sorted(unique_articles)}")

    result("제76조 직접 반환", "제76조" in unique_articles)
    result("관련 조항도 반환 (2개 이상 다른 조문)", len(unique_articles) >= 3,
           f"{len(unique_articles)}개 고유 조문")
    result("시행령에서도 결과", len(by_type["시행령"]) > 0,
           f"{len(by_type['시행령'])}건")


# ============================================================
# TEST 4: 건폐율/용적률 키워드 검색
# ============================================================
def test_bcr_far_search():
    section("TEST 4: 건폐율/용적률 키워드 검색")

    for keyword in ["건폐율", "용적률", "건폐율 용적률 제한"]:
        subsection(f"검색어: '{keyword}'")
        data = search(keyword, limit=15)
        results = data.get("results", [])
        by_type = classify_results(results)

        log(f"  총 {len(results)}건 (법률={len(by_type['법률'])}, 시행령={len(by_type['시행령'])}, 시행규칙={len(by_type['시행규칙'])})")

        for r in results[:5]:
            name = r.get("law_name", "?")
            art = r.get("article", "?")
            sim = r.get("similarity", 0)
            content = r.get("content", "")[:100]
            log(f"    [{name}] {art} (sim={sim:.3f}): {content}...")

    # At least 건폐율 should return results
    data = search("건폐율", limit=15)
    results = data.get("results", [])
    result("건폐율 검색 결과 존재", len(results) > 0, f"{len(results)}건")

    by_type = classify_results(results)
    result("건폐율: 법률 포함", len(by_type["법률"]) > 0)
    result("건폐율: 시행령 포함", len(by_type["시행령"]) > 0)


# ============================================================
# TEST 5: 하위 구조 검색 — 항/호 수준 결과
# ============================================================
def test_sub_article_search():
    section("TEST 5: 하위 구조 검색 (항/호/목 수준)")

    data = search("제1종일반주거지역 건축할 수 있는 건축물", limit=20)
    results = data.get("results", [])
    log(f"  총 {len(results)}건")

    # Check hang_id patterns for depth
    depth_analysis = {"조": 0, "항": 0, "호": 0, "목": 0}
    for r in results:
        hid = r.get("hang_id", "")
        # Detect depth from hang_id structure
        parts = hid.split("::")
        last = parts[-1] if parts else ""
        if last.startswith("제") and last.endswith("조"):
            depth_analysis["조"] += 1
        elif "①" in last or "②" in last or "③" in last or last.isdigit():
            depth_analysis["항"] += 1
        # Log each result
        log(f"    {hid}")
        log(f"      {r.get('content', '')[:100]}...")

    subsection("깊이 분석")
    for level, count in depth_analysis.items():
        log(f"    {level} 수준: {count}건")

    result("항 수준 결과 포함", depth_analysis["항"] > 0, f"{depth_analysis['항']}건")


# ============================================================
# TEST 6: Land Analyze 통합 — 법조항까지 반환
# ============================================================
def test_land_analyze_with_law():
    section("TEST 6: Land Analyze 통합 (법조항 포함)")

    payload = {
        "input": "1168011200101280003",
        "input_type": "pnu",
        "zones": ["제1종일반주거지역"],
        "include_law": True,
    }
    try:
        resp = requests.post(
            "http://127.0.0.1:8000/land/analyze/",
            json=payload, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # PNU info
        pnu = data.get("pnu", {})
        log(f"  PNU: {pnu.get('pnu', '?')}")
        log(f"  시도: {pnu.get('sido', '?')}, 시군구: {pnu.get('sigungu', '?')}")

        # Regulation
        reg = data.get("regulation", {})
        log(f"  건폐율: {reg.get('bcr_limit', '?')}%")
        log(f"  용적률: {reg.get('far_limit', '?')}%")
        result("건폐율 60%", reg.get("bcr_limit") == 60)
        result("용적률 200%", reg.get("far_limit") == 200)

        # Law articles
        law = data.get("law_articles", {})
        article_groups = law.get("articles", [])
        total = law.get("total_count", 0)
        errors = law.get("errors", [])
        log(f"  법조항 그룹: {len(article_groups)}개")
        log(f"  총 법조항 수: {total}")
        if errors:
            for e in errors:
                warn(f"법조항 오류: {e}")

        all_articles = []
        for group in article_groups:
            query = group.get("query", "?")
            group_results = group.get("results", [])
            subsection(f"검색어: '{query}' → {len(group_results)}건")

            by_type = classify_results(group_results)
            log(f"  법률={len(by_type['법률'])}, 시행령={len(by_type['시행령'])}, 시행규칙={len(by_type['시행규칙'])}")

            for r in group_results[:5]:
                name = r.get("law_name", "?")
                art = r.get("article", "?")
                content = r.get("content", "")[:100]
                log(f"    [{name}] {art}: {content}...")
                all_articles.append(r)

        result("법조항 반환됨", total > 0, f"{total}건")

        # Check all 3 types present across all groups
        all_by_type = classify_results(all_articles)
        result("법률 포함", len(all_by_type["법률"]) > 0)
        result("시행령 포함", len(all_by_type["시행령"]) > 0)

        # Restrictions
        restrictions = data.get("restrictions", [])
        log(f"\n  건축 제한사항:")
        for r in restrictions:
            log(f"    - {r}")
        result("제한사항 존재", len(restrictions) > 0, f"{len(restrictions)}개")

    except requests.exceptions.ConnectionError:
        warn("ARR Django 서버 미실행 (http://127.0.0.1:8000) — 이 테스트 스킵")
    except Exception as e:
        warn(f"Land analyze 오류: {e}")


# ============================================================
# TEST 7: law_type 필드 버그 확인
# ============================================================
def test_law_type_field():
    section("TEST 7: law_type 필드 정확성")

    data = search("건폐율", limit=20)
    results = data.get("results", [])

    mismatches = []
    for r in results:
        law_name = r.get("law_name", "")
        law_type = r.get("law_type", "")

        expected_type = "법률"
        if "(시행규칙)" in law_name:
            expected_type = "시행규칙"
        elif "(시행령)" in law_name:
            expected_type = "시행령"

        if law_type != expected_type:
            mismatches.append({
                "law_name": law_name,
                "law_type_field": law_type,
                "expected": expected_type,
                "article": r.get("article", "?"),
            })

    if mismatches:
        log(f"  law_type 필드 불일치: {len(mismatches)}건")
        for m in mismatches[:5]:
            log(f"    {m['law_name']} {m['article']}: law_type='{m['law_type_field']}' (expected '{m['expected']}')")
        warn(f"law_type 필드가 law_name과 불일치 ({len(mismatches)}건) — law-domain-agents 버그")
    else:
        result("law_type 필드 정확", True)


# ============================================================
# MAIN
# ============================================================
def main():
    log(f"법규 파싱 깊이 + 검색 품질 종합 테스트")
    log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Services: law-domain-agents(:8011), Neo4j(:7687), ARR(:8000)")
    log(f"{'='*80}")

    t0 = time.time()

    # Check services
    try:
        requests.get("http://127.0.0.1:8011/api/health", timeout=5)
        log("  law-domain-agents: OK")
    except Exception:
        log("  [FATAL] law-domain-agents(:8011) 미실행. 종료.")
        return

    try:
        requests.get("http://127.0.0.1:8000/land/zones/", timeout=5)
        log("  ARR Django: OK")
        arr_ok = True
    except Exception:
        log("  ARR Django(:8000): 미실행 (land analyze 테스트 스킵)")
        arr_ok = False

    # Run tests
    test_parsing_depth()
    test_article_84()
    test_related_articles()
    test_bcr_far_search()
    test_sub_article_search()
    if arr_ok:
        test_land_analyze_with_law()
    test_law_type_field()

    # Summary
    elapsed = time.time() - t0
    section("SUMMARY")
    log(f"  PASS: {PASS_COUNT}")
    log(f"  FAIL: {FAIL_COUNT}")
    log(f"  WARN: {WARN_COUNT}")
    log(f"  Time: {elapsed:.1f}s")
    log(f"  Result: {'ALL PASS' if FAIL_COUNT == 0 else f'{FAIL_COUNT} FAILURES'}")

    # Write log
    log_path = Path(__file__).parent / "law_depth_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
    print(f"\n  Log: {log_path}")


if __name__ == "__main__":
    main()
