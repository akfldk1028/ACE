from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from shapely.geometry import box

from design.maas.book_language import candidate_floor_authority
from design.maas.book_language import candidate_generation


class CandidateFloorAuthorityExtractionParityTests(unittest.TestCase):
    def test_pure_authority_names_are_reexported_without_behavior_forks(self):
        for name in (
            "_capacity_pack_retry_eligible",
            "_capacity_retry_required",
            "_candidate_floor_context",
            "_compact_candidate_capacity_evidence",
        ):
            self.assertIs(
                getattr(candidate_generation, name),
                getattr(candidate_floor_authority, name),
            )

    def test_legacy_facade_injects_the_patchable_generation_site_sampler(self):
        site = box(0.0, 0.0, 20.0, 20.0)
        source = SimpleNamespace(metadata={})
        floor_contract = {"hard_pass": True, "plates": []}
        measurement = {"hard_pass": True, "floor_area_m2": 0.0}
        facade_sampler = Mock(return_value=site)
        direct_sampler = Mock(return_value=site)

        with (
            patch.object(
                candidate_generation,
                "generation_site_at_height",
                facade_sampler,
            ),
            patch.object(
                candidate_floor_authority,
                "materialize_shared_floor_contract",
                return_value=floor_contract,
            ),
            patch.object(
                candidate_floor_authority,
                "measure_source_capacity",
                return_value=measurement,
            ),
        ):
            facade_result = (
                candidate_generation._shared_floor_capacity_measurement(
                    source,
                    {},
                    generation_context="context",
                    capacity_site=site,
                    height=6.0,
                    floors=2,
                )
            )
            direct_result = (
                candidate_floor_authority._shared_floor_capacity_measurement(
                    source,
                    {},
                    generation_context="context",
                    capacity_site=site,
                    height=6.0,
                    floors=2,
                    generation_site_sampler=direct_sampler,
                )
            )

        self.assertEqual(facade_result, direct_result)
        self.assertEqual(
            facade_sampler.call_args_list,
            direct_sampler.call_args_list,
        )
        self.assertEqual(
            [call.args[1] for call in facade_sampler.call_args_list],
            [3.0, 6.0],
        )
        self.assertNotIn(
            "generation_site_sampler",
            inspect.signature(
                candidate_generation._shared_floor_capacity_measurement
            ).parameters,
        )


if __name__ == "__main__":
    unittest.main()
