from neo4j import GraphDatabase
import time

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', '11111111'))

# Create fulltext index with CJK analyzer
cypher = """CREATE FULLTEXT INDEX hang_content_fulltext
IF NOT EXISTS
FOR (h:HANG) ON EACH [h.content]
OPTIONS { indexConfig: { `fulltext.analyzer`: 'cjk' } }"""

with driver.session() as s:
    s.run(cypher)
    print("Created hang_content_fulltext with CJK analyzer")

time.sleep(3)

with driver.session() as s:
    idx = s.run("SHOW FULLTEXT INDEXES YIELD name, state WHERE name='hang_content_fulltext'").data()
    print(f"Index state: {idx}")

    # Test Korean fulltext search
    r = s.run("""
        CALL db.index.fulltext.queryNodes('hang_content_fulltext', '건폐율')
        YIELD node, score
        RETURN node.full_id as fid, score
        LIMIT 8
    """).data()
    print(f"\n'건폐율' fulltext: {len(r)} results")
    for row in r:
        print(f"  score={row['score']:.3f} | {row['fid'][:70]}")

    r2 = s.run("""
        CALL db.index.fulltext.queryNodes('hang_content_fulltext', '건축허가')
        YIELD node, score
        RETURN node.full_id as fid, score
        LIMIT 8
    """).data()
    print(f"\n'건축허가' fulltext: {len(r2)} results")
    for row in r2:
        print(f"  score={row['score']:.3f} | {row['fid'][:70]}")

    r3 = s.run("""
        CALL db.index.fulltext.queryNodes('hang_content_fulltext', '농지전용')
        YIELD node, score
        RETURN node.full_id as fid, score
        LIMIT 5
    """).data()
    print(f"\n'농지전용' fulltext: {len(r3)} results")
    for row in r3:
        print(f"  score={row['score']:.3f} | {row['fid'][:70]}")

driver.close()
