"""The actual parcel must use reviewed municipal rules, with use conditions."""
from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch

from design.maas.parking_requirements import resolve_candidate_parking_requirement


class UijeongbuParkingTests(SimpleTestCase):
    def requirement(self, area=1026.308149, **kwargs):
        return resolve_candidate_parking_requirement(
            pnu=kwargs.pop("pnu", "4115011300106840001"),
            building_type=kwargs.pop("building_type", "공공업무시설"),
            facility_area_m2=area, **kwargs)

    def test_actual_parcel_uses_municipal_office_rule_and_half_up(self):
        result = self.requirement()
        self.assertEqual(result["selected_rule_id"], "uijeongbu_parking_appendix3_row_02")
        self.assertEqual(result["required_spaces"], 10)
        self.assertAlmostEqual(result["raw_spaces"], 10.26308149)
        self.assertEqual(result["source"]["effective_date"], "2026-01-09")
        self.assertEqual(len(result["source"]["source_sha256"]), 64)

    def test_municipal_boundaries_use_existing_rounding_owner(self):
        for area, expected in ((99, 0), (100, 1), (149.999, 1), (150, 2)):
            with self.subTest(area=area):
                self.assertEqual(self.requirement(area)["required_spaces"], expected)

    def test_explicit_small_public_facility_class_uses_other_row(self):
        result = self.requirement(900, building_type="제1종 근린생활시설",
                                  options={"building_use_code": "appendix1_03_ba"})
        self.assertEqual(result["selected_rule_id"], "uijeongbu_parking_appendix3_row_10")
        self.assertEqual(result["required_spaces"], 4)
        # The ordinary neighborhood row remains distinct from the exception.
        self.assertEqual(self.requirement(900, building_type="근린생활시설")["required_spaces"], 7)

    def test_ambiguous_public_service_label_does_not_silently_choose_other(self):
        result = self.requirement(900, building_type="주민센터")
        self.assertEqual(result["status"], "needs_use_classification")
        self.assertIsNone(result["required_spaces"])

    def test_unreviewed_use_code_is_not_ignored(self):
        result = self.requirement(options={"building_use_code": "invented"})
        self.assertEqual(result["status"], "needs_use_classification")

    def test_accessible_count_requires_facility_applicability(self):
        result = self.requirement(3400)
        self.assertEqual(result["accessible"]["status"], "needs_facility_applicability")
        self.assertEqual(result["accessible"]["conditional_spaces"], 2)
        self.assertIsNone(result["accessible"]["accessible_min"])
        applicable = self.requirement(3400, options={"accessible_parking_applicable": True})
        self.assertEqual(applicable["accessible"]["accessible_min"], 2)
        self.assertEqual(applicable["accessible"]["accessible_max"], 2)
        excluded = self.requirement(3400, options={"accessible_parking_applicable": False})
        self.assertEqual(excluded["accessible"]["accessible_min"], 0)
        self.assertEqual(self.requirement(900)["accessible"]["accessible_min"], 0)

    def test_other_jurisdictions_keep_existing_rules(self):
        self.assertEqual(self.requirement(300, pnu="1168011800104170004")["required_spaces"], 3)
        self.assertEqual(self.requirement(300, pnu="2611010100100010000")["required_spaces"], 2)

    def test_living_accommodation_exception_does_not_use_area_ratio(self):
        result = self.requirement(900, building_type="생활숙박시설")
        self.assertEqual(result["status"], "needs_use_specific_rule")
        self.assertIsNone(result["required_spaces"])

    def test_known_city_unreviewed_row_is_not_a_national_legal_count(self):
        result = self.requirement(900, building_type="창고시설")
        self.assertEqual(result["status"], "needs_local_rule")
        self.assertIsNone(result["required_spaces"])

    def test_conflicting_explicit_rule_and_use_code_are_rejected(self):
        result = self.requirement(900, options={"building_use_code": "appendix1_03_ba",
                                              "parking_rule_id": "parking_appendix1_row_02"})
        self.assertEqual(result["status"], "conflicting_use_classification")

    def test_read_only_graph_enrichment_retains_reviewed_municipal_rule(self):
        from design.maas.parking_requirements import _load_structured_seed_rules
        national = _load_structured_seed_rules()["national"]
        driver = MagicMock()
        with patch("design.maas.parking_requirements.GraphDatabase.driver", return_value=driver), \
             patch("design.maas.parking_requirements._load_rules", return_value={"national": national, "local": []}):
            result = self.requirement(options={"use_neo4j": True})
        self.assertEqual(result["required_spaces"], 10)
        self.assertEqual(result["selected_rule_id"], "uijeongbu_parking_appendix3_row_02")
        self.assertEqual(result["graph_status"], "available")

    def test_sa_category_is_not_mapped_across_jurisdictions(self):
        result = self.requirement(900, pnu="2611010100100010000", building_type="지역아동센터",
                                  options={"building_use_code": "appendix1_03_sa"})
        self.assertEqual(result["status"], "needs_use_classification")
        local = self.requirement(900, building_type="제1종 근린생활시설",
                                 options={"building_use_code": "appendix1_03_sa"})
        self.assertEqual(local["selected_rule_id"], "uijeongbu_parking_appendix3_row_10")

    def test_explicit_general_rule_cannot_bypass_living_accommodation_exception(self):
        result = self.requirement(900, building_type="생활숙박시설",
                                  options={"parking_rule_id": "parking_appendix1_row_11"})
        self.assertEqual(result["status"], "needs_use_specific_rule")

    def test_longer_jurisdiction_prefix_survives_graph_overlay(self):
        from design.maas.parking_requirements import _load_structured_seed_rules
        national = _load_structured_seed_rules()["national"]
        district = {"rule_id": "specific_test_area_office", "base_rule_id": "parking_appendix1_row_02",
                    "pnu_prefix": "41150113", "row_no": "2", "spaces_per": 50}
        with patch("design.maas.parking_requirements.GraphDatabase.driver", return_value=MagicMock()), \
             patch("design.maas.parking_requirements._load_rules", return_value={"national": national, "local": [district]}):
            result = self.requirement(900, options={"use_neo4j": True})
        self.assertEqual(result["selected_rule_id"], "specific_test_area_office")
        self.assertEqual(result["required_spaces"], 18)
