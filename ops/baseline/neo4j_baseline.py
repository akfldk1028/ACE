# -*- coding: utf-8 -*-
"""Record the Neo4j figures the Phase 2 cutover must reproduce (plan: compose step 0).

Reads bolt credentials from Lawagent/server/law-search/.env, writes ops/baseline/neo4j-<date>-<tag>.json.
Run it against Desktop before the dump and against the container after the load; the two files must agree.

    python -X utf8 ops/baseline/neo4j_baseline.py desktop
    python -X utf8 ops/baseline/neo4j_baseline.py container
"""
import json
import sys
from datetime import date
from pathlib import Path

from dotenv import dotenv_values
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[2]
ENV = dotenv_values(ROOT / "agents" / "Lawagent" / "server" / "law-search" / ".env")
URI = ENV.get("NEO4J_URI") or "bolt://localhost:7687"
AUTH = (ENV.get("NEO4J_USER") or "neo4j", ENV["NEO4J_PASSWORD"])

COUNTS = {
    "nodes": "MATCH (n) RETURN count(n) AS c",
    "relationships": "MATCH ()-[r]->() RETURN count(r) AS c",
    "HANG": "MATCH (n:HANG) RETURN count(n) AS c",
    "JO": "MATCH (n:JO) RETURN count(n) AS c",
    "LAW": "MATCH (n:LAW) RETURN count(n) AS c",
    "HANG_with_embedding_local": "MATCH (n:HANG) WHERE n.embedding_local IS NOT NULL RETURN count(n) AS c",
    "JO_with_embedding_local": "MATCH (n:JO) WHERE n.embedding_local IS NOT NULL RETURN count(n) AS c",
    "CONTAINS": "MATCH ()-[r:CONTAINS]->() RETURN count(r) AS c",
    "CITES": "MATCH ()-[r:CITES]->() RETURN count(r) AS c",
    "DELEGATES_TO": "MATCH ()-[r:DELEGATES_TO]->() RETURN count(r) AS c",
}


def main(tag: str) -> None:
    out = {"tag": tag, "date": date.today().isoformat(), "uri": URI, "counts": {}, "labels": {}, "rel_types": {},
           "vector_indexes": [], "all_indexes": [], "smoke": None}
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        with driver.session() as s:
            for key, cypher in COUNTS.items():
                out["counts"][key] = s.run(cypher).single()["c"]
            for rec in s.run("CALL db.labels() YIELD label RETURN label ORDER BY label"):
                label = rec["label"]
                out["labels"][label] = s.run(f"MATCH (n:`{label}`) RETURN count(n) AS c").single()["c"]
            for rec in s.run("CALL db.relationshipTypes() YIELD relationshipType AS t RETURN t ORDER BY t"):
                t = rec["t"]
                out["rel_types"][t] = s.run(f"MATCH ()-[r:`{t}`]->() RETURN count(r) AS c").single()["c"]
            for rec in s.run("SHOW INDEXES YIELD name, type, state, labelsOrTypes, properties, populationPercent "
                             "RETURN name, type, state, labelsOrTypes, properties, populationPercent ORDER BY name"):
                row = dict(rec)
                out["all_indexes"].append(row)
                if row["type"] == "VECTOR":
                    out["vector_indexes"].append(row)
            # vector smoke: the first HANG that has a local vector must find itself at rank 1
            probe = s.run("MATCH (n:HANG) WHERE n.embedding_local IS NOT NULL "
                          "RETURN elementId(n) AS id, n.embedding_local AS v LIMIT 1").single()
            vec_idx = next((i["name"] for i in out["vector_indexes"]
                            if "HANG" in (i["labelsOrTypes"] or []) and "embedding_local" in (i["properties"] or [])), None)
            if probe and vec_idx:
                top = s.run("CALL db.index.vector.queryNodes($idx, 3, $v) YIELD node, score "
                            "RETURN elementId(node) AS id, score", idx=vec_idx, v=probe["v"]).data()
                out["smoke"] = {"index": vec_idx, "self_at_rank_1": bool(top) and top[0]["id"] == probe["id"],
                                "top_scores": [round(t["score"], 6) for t in top]}
    path = Path(__file__).with_name(f"neo4j-{out['date']}-{tag}.json")
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)
    for k, v in out["counts"].items():
        print(f"  {k:<26} {v:>8,}")
    print(f"  vector indexes: {[(i['name'], i['state']) for i in out['vector_indexes']]}")
    print(f"  smoke: {out['smoke']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "desktop")
