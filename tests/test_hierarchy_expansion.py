"""
Law Hierarchy Expansion 테스트
- 법률→시행령→시행규칙 체인 확장 검증
"""
import json
import time
import requests
from datetime import datetime

URL = "http://localhost:8011/api/search"
LOG_FILE = "tests/hierarchy_expansion_verification.log"

QUERIES = [
    # 1. 핵심 테스트: 건축법 제77조 건폐율
    {"query": "건축법 제77조 건폐율", "limit": 15, "expect": "건축법(시행령) or 국토계획법(시행령) 제84조"},
    # 2. 짧은 쿼리: 건폐율만
    {"query": "건폐율", "limit": 15, "expect": "법률+시행령 모두 나와야"},
    # 3. 건축허가
    {"query": "건축허가", "limit": 15, "expect": "건축법(법률)+시행령+시행규칙"},
    # 4. 용도지역 제76조
    {"query": "제76조 용도지역", "limit": 15, "expect": "국토계획법(법률) + (시행령) 인용"},
    # 5. 용적률
    {"query": "용적률", "limit": 15, "expect": "국토계획법+건축법 시행령"},
    # 6. 농지전용 (다른 법)
    {"query": "농지전용", "limit": 15, "expect": "농지법 법률+시행령"},
    # 7. 산지전용허가
    {"query": "산지전용허가", "limit": 10, "expect": "산지관리법 법률+시행령"},
]


def run_test(q_info):
    query = q_info["query"]
    limit = q_info["limit"]
    expect = q_info["expect"]

    start = time.time()
    resp = requests.post(URL, json={"query": query, "limit": limit})
    elapsed = time.time() - start

    data = resp.json()
    results = data.get("results", [])
    stats = data.get("stats", {})

    # stage별 카운트
    stage_counts = {}
    for r in results:
        for s in r.get("stages", [r.get("stage", "unknown")]):
            stage_counts[s] = stage_counts.get(s, 0) + 1

    # law_type별 카운트
    type_counts = {}
    for r in results:
        lt = r.get("law_type", "?")
        type_counts[lt] = type_counts.get(lt, 0) + 1

    # law_name별 카운트
    name_counts = {}
    for r in results:
        ln = r.get("law_name", "?")
        name_counts[ln] = name_counts.get(ln, 0) + 1

    # hierarchy_expansion 결과 상세
    hierarchy_hits = [r for r in results if "hierarchy_expansion" in r.get("stages", [r.get("stage", "")])]

    return {
        "query": query,
        "expect": expect,
        "total": len(results),
        "elapsed_ms": int(elapsed * 1000),
        "stats": stats,
        "stage_counts": stage_counts,
        "type_counts": type_counts,
        "name_counts": name_counts,
        "hierarchy_count": len(hierarchy_hits),
        "hierarchy_hits": [
            {
                "hang_id": h["hang_id"][:80],
                "law_name": h.get("law_name", ""),
                "law_type": h.get("law_type", ""),
                "article": h.get("article", ""),
                "content_preview": (h.get("content", "") or "")[:100],
            }
            for h in hierarchy_hits
        ],
        "all_results_summary": [
            {
                "law_name": r.get("law_name", ""),
                "law_type": r.get("law_type", ""),
                "article": r.get("article", ""),
                "stage": r.get("stages", [r.get("stage", "?")])[0] if r.get("stages") else r.get("stage", "?"),
                "similarity": r.get("similarity", 0),
            }
            for r in results
        ],
    }


def main():
    log_lines = []
    log_lines.append(f"=== Law Hierarchy Expansion Verification ===")
    log_lines.append(f"Date: {datetime.now().isoformat()}")
    log_lines.append(f"Server: {URL}")
    log_lines.append("")

    all_results = []
    total_hierarchy = 0

    for i, q in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] Testing: {q['query']}")
        result = run_test(q)
        all_results.append(result)
        total_hierarchy += result["hierarchy_count"]

        # Console output
        print(f"  Results: {result['total']} | Time: {result['elapsed_ms']}ms")
        print(f"  Stages: {result['stage_counts']}")
        print(f"  Types: {result['type_counts']}")
        print(f"  Laws: {result['name_counts']}")
        print(f"  Hierarchy hits: {result['hierarchy_count']}")
        if result["hierarchy_hits"]:
            for h in result["hierarchy_hits"]:
                try:
                    print(f"    -> [{h['law_type']}] {h['law_name']} {h['article']}")
                    print(f"       {h['content_preview'][:80]}...")
                except UnicodeEncodeError:
                    print(f"    -> [{h['law_type']}] {h['law_name']} {h['article']} (content has special chars)")

        # Log
        log_lines.append(f"--- Test {i}: {q['query']} ---")
        log_lines.append(f"Expected: {q['expect']}")
        log_lines.append(f"Results: {result['total']} | Time: {result['elapsed_ms']}ms")
        log_lines.append(f"Stages: {json.dumps(result['stage_counts'], ensure_ascii=False)}")
        log_lines.append(f"Types: {json.dumps(result['type_counts'], ensure_ascii=False)}")
        log_lines.append(f"Laws: {json.dumps(result['name_counts'], ensure_ascii=False)}")
        log_lines.append(f"Hierarchy expansion hits: {result['hierarchy_count']}")
        log_lines.append("")

        # All results summary
        log_lines.append("  All results:")
        for j, r in enumerate(result["all_results_summary"], 1):
            log_lines.append(
                f"  {j:2d}. [{r['stage']:<20s}] {r['law_type']:<6s} | {r['law_name']:<20s} | {r['article']:<12s} | sim={r['similarity']:.3f}"
            )
        log_lines.append("")

        if result["hierarchy_hits"]:
            log_lines.append("  Hierarchy expansion details:")
            for h in result["hierarchy_hits"]:
                log_lines.append(f"    [{h['law_type']}] {h['law_name']} {h['article']}")
                log_lines.append(f"    Content: {h['content_preview']}")
            log_lines.append("")

        log_lines.append("")

    # Summary
    log_lines.append("=== SUMMARY ===")
    log_lines.append(f"Total queries: {len(QUERIES)}")
    log_lines.append(f"Total hierarchy expansion hits: {total_hierarchy}")
    queries_with_expansion = sum(1 for r in all_results if r["hierarchy_count"] > 0)
    log_lines.append(f"Queries with hierarchy expansion: {queries_with_expansion}/{len(QUERIES)}")
    log_lines.append("")

    for r in all_results:
        status = "OK" if r["hierarchy_count"] > 0 else "NO EXPANSION"
        log_lines.append(f"  [{status:12s}] {r['query']}: {r['hierarchy_count']} hits, {r['type_counts']}")

    # Write log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print(f"\n{'='*60}")
    print(f"Total hierarchy hits: {total_hierarchy}")
    print(f"Queries with expansion: {queries_with_expansion}/{len(QUERIES)}")
    print(f"Log saved: {LOG_FILE}")


if __name__ == "__main__":
    main()
