"""Materialise the citation and delegation layer of the statute graph.

The graph stores 31,123 article nodes joined by CONTAINS and NEXT, so a reader
can walk one instrument in order.  What it did not store is the layer that makes
a requirement complete: a provision that says "「건축법」 제61조에 따라" or
"대통령령으로 정한다" points at another instrument, and until that pointer is an
edge the graph cannot answer "what else must I read".  The text carries those
pointers already; this command turns them into edges.

Every edge records the phrase that produced it and the resolution method, so a
citation can be audited back to the sentence it came from.  References that
cannot be resolved to a node are counted and reported, never silently dropped -
the resolution rate is part of the result, not a detail to hide.

    python manage.py build_statute_citations              # dry run, reports only
    python manage.py build_statute_citations --write      # persist the edges
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand, CommandError


CITES = "CITES"
DELEGATES = "DELEGATES_TO"
METHOD = "regex_v1"

# 「건축법」 제61조 / 『주차장법』 제6조제1항 - a named instrument then an article
NAMED_REF = re.compile(r"[「『]\s*([^」』]{2,40}?)\s*[」』]\s*(?:의\s*)?제\s*(\d+)\s*조(?:의\s*(\d+))?")
# A decree does not repeat its parent's name: "법 제21조" means the statute this
# decree hangs from, "영 제86조" its decree, "같은 법" the instrument last named.
# Without these three forms most references in a 시행령 resolve to nothing.
PREFIXED_REF = re.compile(
    r"(같은\s*법|같은\s*영|같은\s*규칙|법|영|규칙)\s*제\s*(\d+)\s*조(?:의\s*(\d+))?"
)
PREFIX_INSTRUMENT = {"법": "법률", "영": "시행령", "규칙": "시행규칙"}
# 제61조 / 제61조의2 - an article with nothing in front of it, i.e. this instrument
BARE_REF = re.compile(r"(?<![」』])\s*제\s*(\d+)\s*조(?:의\s*(\d+))?")
# 「저작권법」에 따라 - an instrument named with no article number. It still
# tells the reader which instrument governs, and a blind annotation found 11 of
# these that the article-bearing pattern above cannot see.
INSTRUMENT_ONLY = re.compile(r"[「『]\s*([^」』]{2,40}?)\s*[」』]\s*(?!제\s*\d+\s*조)")
# 별표 1 제3호하목 / 별지 제46호서식 - appendices carry the requirement tables in
# Korean building regulation, and none were being detected.
APPENDIX_REF = re.compile(r"별(표|지)\s*제?\s*(\d+)\s*(호)?")
# 제7조부터 제9조까지 - a range names every article between its endpoints.
ARTICLE_RANGE = re.compile(
    r"제\s*(\d+)\s*조(?:의\s*\d+)?\s*부터\s*제\s*(\d+)\s*조(?:의\s*\d+)?\s*까지"
)
# 제1항부터 제6항까지 / 제16호부터 제22호까지 - the same construction over
# paragraphs and subparagraphs. These stay inside the provision, so they are
# detected for accounting but produce no edge.
UNIT_RANGE = re.compile(r"제\s*\d+\s*[항호목]\s*부터\s*제\s*\d+\s*[항호목]\s*까지")
MAX_RANGE_SPAN = 30
# 대통령령으로 정한다 / 국토교통부령이 정하는 - the connective varies and the
# ministry list was short.
DELEGATION = re.compile(
    # Enumerating ministries does not survive a cabinet reshuffle: any
    # "<something>부령" is a ministerial rule, and the held-out sample missed
    # 교육부령 and 농림축산식품부령 only because they were not on the list.
    r"(대통령령|총리령|[가-힣]{2,8}부령|조례|규약)\s*(?:으로|이|로|에서|에)\s*정"
)

INSTRUMENT_OF = {
    "대통령령": "시행령",
    "국토교통부령": "시행규칙",
    "행정안전부령": "시행규칙",
    "환경부령": "시행규칙",
}


def article_key(number: str, sub: str | None) -> str:
    return f"제{int(number)}조의{int(sub)}" if sub else f"제{int(number)}조"


class Command(BaseCommand):
    help = (
        "Extract CITES and DELEGATES_TO edges from statute article text and "
        "write them into the Neo4j statute graph."
    )

    def add_arguments(self, parser):
        parser.add_argument("--write", action="store_true",
                            help="persist edges; without it the command only reports")
        parser.add_argument("--limit", default=0, type=int,
                            help="process at most N source nodes (for a quick check)")
        parser.add_argument("--batch", default=2000, type=int)

    def handle(self, *args, **options):
        from graph_db.services.neo4j_service import Neo4jService

        neo4j = Neo4jService()
        if not neo4j.connect():
            raise CommandError("cannot connect to Neo4j")

        # ---- index every article by (instrument, article key) -----------------
        rows = neo4j.execute_query(
            "MATCH (j:JO) RETURN j.full_id AS fid, j.number AS num, j.law_name AS law"
        )
        by_instrument: dict[tuple[str, str], str] = {}
        instruments_of_law: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            fid = str(row["fid"] or "")
            if "::" not in fid:
                continue
            instrument = fid.split("::", 1)[0]          # 건축법(법률)
            number = str(row["num"] or "")              # 106조
            match = re.match(r"(\d+)조(?:의(\d+))?", number)
            if not match:
                continue
            key = article_key(match.group(1), match.group(2))
            by_instrument[(instrument, key)] = fid
            instruments_of_law[str(row["law"] or "")].add(instrument)
        self.stdout.write(f"indexed articles: {len(by_instrument)}")

        law_names = sorted({name for name in instruments_of_law if name}, key=len, reverse=True)

        def resolve_named(name: str, key: str) -> str | None:
            """A 「name」 with no suffix means that law's statute (법률)."""
            for candidate in (f"{name}(법률)", f"{name}(시행령)", f"{name}(시행규칙)"):
                fid = by_instrument.get((candidate, key))
                if fid:
                    return fid
            return None

        # ---- scan every content-bearing node ----------------------------------
        query = (
            "MATCH (n) WHERE n.content IS NOT NULL AND n.full_id IS NOT NULL "
            "AND (n:JO OR n:HANG OR n:HO OR n:MOK) "
            "RETURN n.full_id AS fid, n.law_name AS law, n.content AS content, "
            "head(labels(n)) AS lbl"
        )
        if options["limit"]:
            query += f" LIMIT {int(options['limit'])}"
        nodes = neo4j.execute_query(query)
        self.stdout.write(f"source nodes: {len(nodes)}")

        edges: list[dict] = []
        seen: set[tuple[str, str, str]] = set()
        stats = Counter()
        unresolved_names = Counter()

        for node in nodes:
            src = str(node["fid"] or "")
            if "::" not in src:
                continue
            instrument = src.split("::", 1)[0]
            law = str(node["law"] or "")
            content = str(node["content"] or "")
            slabel = str(node["lbl"] or "JO")

            named_spans = []
            for m in NAMED_REF.finditer(content):
                named_spans.append(m.span())
                name = m.group(1).strip()
                key = article_key(m.group(2), m.group(3))
                if name not in instruments_of_law:
                    # tolerate 「건축법 시행령」 style and abbreviations
                    hit = next((n for n in law_names if name.startswith(n)), None)
                    if hit is None:
                        stats["named_outside_corpus"] += 1
                        unresolved_names[name] += 1
                        continue
                    name = hit
                target = resolve_named(name, key)
                stats["named_seen"] += 1
                if not target:
                    stats["named_unresolved_article"] += 1
                    continue
                triple = (src, CITES, target)
                if triple in seen:
                    continue
                seen.add(triple)
                edges.append({"src": src, "dst": target, "rel": CITES,
                              "evidence": m.group(0).strip()[:120], "scope": "cross_instrument",
                              "slabel": slabel, "dlabel": "JO"})
                stats["cites_cross"] += 1

            # "법 제21조" / "같은 법 제2조" - the instrument is named by role, not
            # by title. "같은 법" refers back to the last 「name」 in this text.
            last_named = None
            for m in NAMED_REF.finditer(content):
                candidate = m.group(1).strip()
                hit = candidate if candidate in instruments_of_law else next(
                    (n for n in law_names if candidate.startswith(n)), None)
                if hit:
                    last_named = hit
            for m in PREFIXED_REF.finditer(content):
                named_spans.append(m.span())
                word = re.sub(r"\s+", "", m.group(1))
                key = article_key(m.group(2), m.group(3))
                stats["prefixed_seen"] += 1
                if word.startswith("같은"):
                    base = last_named or law
                    suffix = {"같은법": "법률", "같은영": "시행령",
                              "같은규칙": "시행규칙"}[word]
                else:
                    base, suffix = law, PREFIX_INSTRUMENT[word]
                target = by_instrument.get((f"{base}({suffix})", key))
                if not target:
                    stats["prefixed_unresolved"] += 1
                    continue
                if target == src:
                    stats["prefixed_self"] += 1
                    continue
                triple = (src, CITES, target)
                if triple in seen:
                    stats["prefixed_duplicate"] += 1
                    continue
                seen.add(triple)
                edges.append({"src": src, "dst": target, "rel": CITES,
                              "evidence": m.group(0).strip()[:120], "scope": "role_reference",
                              "slabel": slabel, "dlabel": "JO"})
                stats["cites_role"] += 1

            # ranges first: they contain article numbers the bare pattern would
            # otherwise read as two unrelated references.
            for m in ARTICLE_RANGE.finditer(content):
                named_spans.append(m.span())
                lo, hi = int(m.group(1)), int(m.group(2))
                stats["range_seen"] += 1
                if hi < lo or hi - lo > MAX_RANGE_SPAN:
                    stats["range_rejected"] += 1
                    continue
                for number in range(lo, hi + 1):
                    target = by_instrument.get((instrument, f"제{number}조"))
                    if not target or target == src:
                        continue
                    triple = (src, CITES, target)
                    if triple in seen:
                        continue
                    seen.add(triple)
                    edges.append({"src": src, "dst": target, "rel": CITES,
                                  "evidence": m.group(0).strip()[:120],
                                  "scope": "range", "slabel": slabel, "dlabel": "JO"})
                    stats["cites_range"] += 1

            # an instrument named without an article still says which instrument
            # governs; the edge targets the instrument node, not a provision.
            for m in INSTRUMENT_ONLY.finditer(content):
                if any(a <= m.start() < b for a, b in named_spans):
                    continue
                name = m.group(1).strip()
                hit = name if name in instruments_of_law else next(
                    (n for n in law_names if name.startswith(n)), None)
                stats["instrument_only_seen"] += 1
                if hit is None:
                    stats["instrument_only_outside_corpus"] += 1
                    continue
                target = f"{hit}(법률)"
                if target not in instruments_of_law.get(hit, set()):
                    stats["instrument_only_target_absent"] += 1
                    continue
                named_spans.append(m.span())
                triple = (src, CITES, target)
                if triple in seen:
                    continue
                seen.add(triple)
                edges.append({"src": src, "dst": target, "rel": CITES,
                              "evidence": m.group(0).strip()[:120],
                              "scope": "instrument_only", "slabel": slabel,
                              "dlabel": "LAW"})
                stats["cites_instrument_only"] += 1

            # 별표 / 별지 are detected so the count is honest, but the corpus holds
            # only two APPENDIX nodes, so almost none of them can be resolved.
            for m in APPENDIX_REF.finditer(content):
                stats["appendix_seen"] += 1
                key = f"별{m.group(1)}{int(m.group(2))}"
                target = by_instrument.get((instrument, key))
                if not target:
                    stats["appendix_unresolved"] += 1
                    continue
                triple = (src, CITES, target)
                if triple in seen:
                    continue
                seen.add(triple)
                edges.append({"src": src, "dst": target, "rel": CITES,
                              "evidence": m.group(0).strip()[:120],
                              "scope": "appendix", "slabel": slabel, "dlabel": "APPENDIX"})
                stats["cites_appendix"] += 1

            for m in BARE_REF.finditer(content):
                # A named or role-prefixed reference already claimed this span;
                # counting it again would inflate the bare resolution rate.
                if any(a <= m.start() < b for a, b in named_spans):
                    continue
                key = article_key(m.group(1), m.group(2))
                target = by_instrument.get((instrument, key))
                stats["bare_seen"] += 1
                if not target or target == src.split("::")[0]:
                    stats["bare_unresolved"] += 1
                    continue
                if target == src:
                    stats["bare_self"] += 1
                    continue
                triple = (src, CITES, target)
                if triple in seen:
                    stats["bare_duplicate"] += 1
                    continue
                seen.add(triple)
                edges.append({"src": src, "dst": target, "rel": CITES,
                              "evidence": m.group(0).strip()[:120], "scope": "same_instrument",
                              "slabel": slabel, "dlabel": "JO"})
                stats["cites_internal"] += 1

            for m in DELEGATION.finditer(content):
                suffix = INSTRUMENT_OF.get(m.group(1))
                stats["delegation_seen"] += 1
                if suffix is None:
                    stats["delegation_to_ordinance"] += 1
                    continue
                target_instrument = f"{law}({suffix})"
                if target_instrument not in instruments_of_law.get(law, set()):
                    stats["delegation_target_absent"] += 1
                    continue
                triple = (src, DELEGATES, target_instrument)
                if triple in seen:
                    continue
                seen.add(triple)
                edges.append({"src": src, "dst": target_instrument, "rel": DELEGATES,
                              "evidence": m.group(0).strip()[:120], "scope": "delegation",
                              "slabel": slabel, "dlabel": "LAW"})
                stats["delegates"] += 1

        self.stdout.write("")
        self.stdout.write("extraction")
        for key in sorted(stats):
            self.stdout.write(f"   {key:30s} {stats[key]:7d}")
        # Report against what the extractor could have resolved: a reference to
        # an instrument outside the 20-law corpus is coverage, not a miss, and a
        # duplicate or self-reference is not a failure either.
        in_corpus = stats["named_seen"]
        if in_corpus:
            self.stdout.write(
                f"   named refs in corpus            {in_corpus:7d}"
                f"  -> resolved {stats['cites_cross']}"
                f" ({100.0*stats['cites_cross']/in_corpus:.1f}%)")
        self.stdout.write(
            f"   named refs outside corpus       {stats['named_outside_corpus']:7d}"
            "  (target instrument not loaded)")
        addressable = stats["bare_seen"] - stats["bare_self"] - stats["bare_duplicate"]
        if addressable > 0:
            self.stdout.write(
                f"   same-instrument addressable     {addressable:7d}"
                f"  -> resolved {stats['cites_internal']}"
                f" ({100.0*stats['cites_internal']/addressable:.1f}%)")
        role_addressable = (stats["prefixed_seen"] - stats["prefixed_self"]
                            - stats["prefixed_duplicate"])
        if role_addressable > 0:
            self.stdout.write(
                f"   role refs addressable           {role_addressable:7d}"
                f"  -> resolved {stats['cites_role']}"
                f" ({100.0*stats['cites_role']/role_addressable:.1f}%)")
        if unresolved_names:
            self.stdout.write("   top unresolved instrument names:")
            for name, count in unresolved_names.most_common(8):
                self.stdout.write(f"      {count:5d}  {name}")
        self.stdout.write("")
        self.stdout.write(f"edges extracted: {len(edges)}")

        if not options["write"]:
            self.stdout.write(self.style.WARNING("dry run - nothing written. pass --write to persist."))
            return

        # full_id is indexed per label, so the write must name the labels or every
        # row costs a full node scan.
        groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
        for edge in edges:
            groups[(edge["slabel"], edge["rel"], edge["dlabel"])].append(edge)

        written = 0
        batch = int(options["batch"])
        for (slabel, rel, dlabel), subset in sorted(groups.items()):
            for start in range(0, len(subset), batch):
                chunk = subset[start:start + batch]
                neo4j.execute_query(
                    f"""
                    UNWIND $rows AS row
                    MATCH (a:{slabel} {{full_id: row.src}})
                    MATCH (b:{dlabel} {{full_id: row.dst}})
                    MERGE (a)-[r:{rel}]->(b)
                    SET r.method = $method, r.evidence = row.evidence, r.scope = row.scope
                    """,
                    {"rows": chunk, "method": METHOD},
                )
                written += len(chunk)
            self.stdout.write(f"   {slabel:5s} -{rel}-> {dlabel:4s} {len(subset):6d}   ({written}/{len(edges)})")
        self.stdout.write(self.style.SUCCESS(f"persisted {written} edges"))
