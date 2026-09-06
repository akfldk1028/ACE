import unittest

from design.maas.creative_floor_portfolio import build_creative_floor_portfolio, build_creative_floor_portfolio_report
from design.maas.creative_program_author import normalize_authored_programs
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram


class CreativeOriginalLineageTests(unittest.TestCase):
    def test_raw_author_hash_and_normalized_hash_remain_distinct(self):
        raw = GeometryProgram(
            name="raw_author_corner",
            nodes=(
                GeometryNode(id="body", kind="primitive", operator="box",
                             parameters={"width": 1.0, "depth": 1.0, "height": 1.0}),
                GeometryNode(id="corner", kind="macro", operator="cut_corner",
                             inputs=("body",), parameters={"corner": "ne", "ratio": 0.24}),
            ),
            root_id="corner",
        )
        normalized = normalize_authored_programs((raw,))[0].program
        self.assertNotEqual(raw.program_hash(), normalized.program_hash())
        report = build_creative_floor_portfolio_report(
            target_count=1, capacity_ceiling_m2=332.322, authored_programs=(raw,),
        )
        self.assertEqual({row["candidate_origin"] for row in report.candidates},
                         {"authored_original", "book_exploration"})
        for row in report.candidates:
            self.assertEqual(row["source_program_hash"], raw.program_hash())
            self.assertEqual(row["normalized_source_program_hash"], normalized.program_hash())
            if row["candidate_origin"] == "authored_original":
                self.assertEqual(row["authored_geometry_program"], raw.to_dict())
            else:
                self.assertEqual(row["parent_program_hash"], raw.program_hash())
                self.assertEqual(row["parent_geometry_program"], raw.to_dict())
            physical = GeometryProgram.from_dict(row["geometry_program"])
            self.assertEqual(row["program_hash"], physical.program_hash())
        payload = build_creative_floor_portfolio(
            count=1, capacity_ceiling_m2=332.322, authored_programs=(raw,),
        )
        self.assertEqual(payload["candidate_count"], 2)
        self.assertEqual(payload["exploration_count"], 1)
        self.assertEqual(payload["original_count"], 1)
        self.assertEqual(payload["target_count_scope"], "book_exploration")
        self.assertEqual(payload["book_language_coverage"], report.language_coverage)
