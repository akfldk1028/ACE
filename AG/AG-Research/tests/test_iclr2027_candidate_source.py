from __future__ import annotations

import io
import logging
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace


class CandidateSourceTests(unittest.TestCase):
    def test_seeded_halton_probes_are_reproducible_and_inside_bbox(self) -> None:
        from iclr2027.candidate_source import BoundingBox, halton_probes

        bbox = BoundingBox(west=0.0, south=0.0, east=10.0, north=9.0)

        probes = halton_probes(bbox=bbox, seed=0, max_probes=3)

        self.assertEqual(
            [(probe.index, probe.longitude, probe.latitude) for probe in probes],
            [
                (1, 5.0, 3.0),
                (2, 2.5, 6.0),
                (3, 7.5, 1.0),
            ],
        )
        self.assertEqual(probes, halton_probes(bbox=bbox, seed=0, max_probes=3))
        self.assertNotEqual(probes, halton_probes(bbox=bbox, seed=1, max_probes=3))

    def test_collection_emits_selector_fields_and_typed_duplicate_exclusion(self) -> None:
        from iclr2027.candidate_source import (
            BoundingBox,
            CandidateObservation,
            ExclusionCode,
            ProbeExclusion,
            collect_candidate_source,
        )

        observations = iter(
            (
                CandidateObservation(
                    pnu="1111010100100000001",
                    district_code="11110",
                    parcel_area_m2=245.5,
                    boundary_available=True,
                    law_available=True,
                    parking_available=True,
                ),
                CandidateObservation(
                    pnu="1111010100100000001",
                    district_code="11110",
                    parcel_area_m2=245.5,
                    boundary_available=True,
                    law_available=True,
                    parking_available=True,
                ),
                ProbeExclusion(ExclusionCode.NO_PARCEL),
            )
        )

        payload = collect_candidate_source(
            bbox=BoundingBox(west=126.0, south=37.0, east=127.0, north=38.0),
            seed=4,
            max_probes=3,
            inspect_probe=lambda _probe: next(observations),
            collector="fixture-readonly-v1",
        )

        self.assertEqual(payload["schema_version"], "ace.iclr2027.candidate_source.v1")
        self.assertEqual(
            payload["candidates"],
            [
                {
                    "pnu": "1111010100100000001",
                    "district_code": "11110",
                    "parcel_area_m2": 245.5,
                    "boundary_available": True,
                    "law_available": True,
                    "parking_available": True,
                }
            ],
        )
        self.assertEqual(
            payload["exclusions"],
            [
                {
                    "probe_index": 6,
                    "code": "duplicate_pnu",
                    "pnu": "1111010100100000001",
                },
                {"probe_index": 7, "code": "no_parcel"},
            ],
        )
        self.assertEqual(
            payload["provenance"],
            {
                "collector": "fixture-readonly-v1",
                "probe_strategy": "seeded_halton",
                "halton_bases": [2, 3],
                "seed": 4,
                "max_probes": 3,
                "bbox": {
                    "west": 126.0,
                    "south": 37.0,
                    "east": 127.0,
                    "north": 38.0,
                    "crs": "EPSG:4326",
                },
                "probes_attempted": 3,
                "unique_candidate_count": 1,
                "exclusion_counts": {"duplicate_pnu": 1, "no_parcel": 1},
            },
        )

    def test_collection_redacts_inspector_exception_details(self) -> None:
        from iclr2027.candidate_source import BoundingBox, collect_candidate_source

        def fail(_probe):
            raise RuntimeError("secret-key and full-address must not escape")

        payload = collect_candidate_source(
            bbox=BoundingBox(west=126.0, south=37.0, east=127.0, north=38.0),
            seed=0,
            max_probes=1,
            inspect_probe=fail,
            collector="fixture-readonly-v1",
        )

        self.assertEqual(
            payload["exclusions"],
            [{"probe_index": 1, "code": "inspection_error"}],
        )
        self.assertNotIn("secret-key", str(payload))
        self.assertNotIn("full-address", str(payload))

    def test_collection_rejects_unbounded_probe_count(self) -> None:
        from iclr2027.candidate_source import BoundingBox, collect_candidate_source

        with self.assertRaisesRegex(ValueError, "max_probes"):
            collect_candidate_source(
                bbox=BoundingBox(west=126.0, south=37.0, east=127.0, north=38.0),
                seed=0,
                max_probes=10_001,
                inspect_probe=lambda _probe: None,
                collector="fixture-readonly-v1",
            )


class ArrCandidateInspectorTests(unittest.TestCase):
    def test_backend_env_loads_missing_values_without_overriding_or_emitting_them(self) -> None:
        from collect_iclr2027_candidates import _load_backend_environment

        loaded_secret = "dotenv-secret-must-not-be-emitted"
        existing_value = "existing-process-value"
        keys = ("VWORLD_API_KEY", "ICLR_ENV_PRECEDENCE_TEST")
        original = {key: os.environ.get(key) for key in keys}
        try:
            os.environ.pop("VWORLD_API_KEY", None)
            os.environ["ICLR_ENV_PRECEDENCE_TEST"] = existing_value
            with tempfile.TemporaryDirectory() as tmp:
                backend = Path(tmp)
                (backend / ".env").write_text(
                    "VWORLD_API_KEY=" + loaded_secret + "\n"
                    "ICLR_ENV_PRECEDENCE_TEST=dotenv-must-not-win\n",
                    encoding="utf-8",
                )
                output = io.StringIO()

                with redirect_stdout(output), redirect_stderr(output):
                    loaded = _load_backend_environment(backend)

            self.assertTrue(loaded)
            self.assertEqual(os.environ["VWORLD_API_KEY"], loaded_secret)
            self.assertEqual(os.environ["ICLR_ENV_PRECEDENCE_TEST"], existing_value)
            self.assertNotIn(loaded_secret, output.getvalue())
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    @staticmethod
    def _dependencies(*, parking_spaces=(10, 11, 12)):
        from collect_iclr2027_candidates import ArrDependencies

        programs = tuple(
            SimpleNamespace(slug=slug, building_type=building_type)
            for slug, building_type in (
                ("neighborhood", "neighborhood-type"),
                ("gymnasium", "gymnasium-type"),
                ("cultural", "cultural-type"),
            )
        )
        spaces = iter(parking_spaces)

        def calculate_all(zone_names, land_info, sigungu_code, use_llm_extraction):
            if use_llm_extraction is not False:
                raise AssertionError("candidate collection must disable LLM extraction")
            if zone_names != ["residential-zone"]:
                raise AssertionError("unexpected zoning input")
            if land_info != {"land_area_m2": 456.7} or sigungu_code != "11110":
                raise AssertionError("unexpected local-law context")
            return {
                "matched_zones": ["residential-zone"],
                "bcr_pct": 60.0,
                "far_pct": 200.0,
            }

        def resolve_parking(**kwargs):
            if kwargs["facility_area_m2"] != 1000.0:
                raise AssertionError("parking probe must use the documented nominal area")
            if kwargs["rules"] != {"national": {}, "local": []}:
                raise AssertionError("parking probe must use injected local structured rules")
            return {"status": "computed", "required_spaces": next(spaces)}

        return ArrDependencies(
            reverse_geocode=lambda _x, _y: {
                "success": True,
                "pnu": "1111010100100000001",
                "address": "must never be persisted",
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]]},
            },
            fetch_land_use_attr=lambda _pnu: {"success": True, "zones": ["residential-zone"]},
            fetch_ladfrl=lambda _pnu: {"success": True, "land_area_m2": 456.7},
            zone_lookup=lambda name: {"zone_name": name},
            calculate_all=calculate_all,
            resolve_parking=resolve_parking,
            parking_rules={"national": {}, "local": []},
            programs=programs,
        )

    def test_arr_inspector_resolves_boundary_law_and_all_program_parking(self) -> None:
        from collect_iclr2027_candidates import inspect_arr_probe
        from iclr2027.candidate_source import CoordinateProbe

        observation = inspect_arr_probe(
            CoordinateProbe(index=1, longitude=126.95, latitude=37.55),
            self._dependencies(),
        )

        self.assertEqual(
            observation.to_candidate_dict(),
            {
                "pnu": "1111010100100000001",
                "district_code": "11110",
                "parcel_area_m2": 456.7,
                "boundary_available": True,
                "law_available": True,
                "parking_available": True,
            },
        )
        self.assertNotIn("address", observation.to_candidate_dict())

    def test_arr_inspector_marks_parking_unavailable_if_any_program_lacks_integer_count(self) -> None:
        from collect_iclr2027_candidates import inspect_arr_probe
        from iclr2027.candidate_source import CoordinateProbe

        observation = inspect_arr_probe(
            CoordinateProbe(index=1, longitude=126.95, latitude=37.55),
            self._dependencies(parking_spaces=(10, None, 12)),
        )

        self.assertFalse(observation.parking_available)

    def test_arr_inspector_requires_all_three_research_programs(self) -> None:
        from collect_iclr2027_candidates import inspect_arr_probe
        from iclr2027.candidate_source import CoordinateProbe

        dependencies = self._dependencies()
        observation = inspect_arr_probe(
            CoordinateProbe(index=1, longitude=126.95, latitude=37.55),
            replace(dependencies, programs=dependencies.programs[:2]),
        )

        self.assertFalse(observation.parking_available)

    def test_arr_inspector_excludes_non_seoul_parcel_at_bbox_edge(self) -> None:
        from collect_iclr2027_candidates import inspect_arr_probe
        from iclr2027.candidate_source import CoordinateProbe, ExclusionCode

        dependencies = self._dependencies()
        observation = inspect_arr_probe(
            CoordinateProbe(index=1, longitude=126.77, latitude=37.42),
            replace(
                dependencies,
                reverse_geocode=lambda _x, _y: {
                    "success": True,
                    "pnu": "4113510100100010001",
                    "address": "must never be persisted",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [0, 1], [0, 0]]],
                    },
                },
            ),
        )

        self.assertEqual(observation.code, ExclusionCode.OUTSIDE_SEOUL)

    def test_httpx_info_logging_is_suppressed(self) -> None:
        from collect_iclr2027_candidates import configure_collection_logging

        logger = logging.getLogger("httpx")
        previous = logger.level
        try:
            logger.setLevel(logging.INFO)
            configure_collection_logging()
            self.assertEqual(logger.level, logging.WARNING)
        finally:
            logger.setLevel(previous)


if __name__ == "__main__":
    unittest.main()
