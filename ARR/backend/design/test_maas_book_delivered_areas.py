"""BOOK certificates measure executed placement, and bands retain all parts."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase

from shapely.geometry import box
from design.maas.geometry_language.dsl import parse_geometry_dsl
from design.maas.geometry_language.source_bridge import (
    compile_geometry_program_to_source_mass, _mesh_section_polygon,
    mesh_section_solid, solid_section_polygon,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
import book_import


def bridge_program():
    # One connected solid; two separate occupied parts above the first floor.
    return parse_geometry_dsl(
        'result = union(box(24,12,3), translate(box(6,12,6), vector=[0,0,3]), '
        'translate(box(6,12,6), vector=[18,0,3]))')


def record():
    return {'trace_sequence_name': 'split-upper-floors', 'geometry_artifact': {
        'authoredGeometryProgram': bridge_program().to_dict(),
        'storeyEvidence': {'storey_count': 3, 'typical_storey_height_m': 3,
                          'floor_center_elevations_m': [1.5, 4.5, 7.5],
                          'actual_floor_areas_m2': [288, 144, 144]},
        'projectedVisualCertificate': {'physical_height_m': 9},
        'hardGates': {'projectedMetrics': {'footprint_area_m2': 288,
                                          'floor_area_m2': 576}}}}


def mesh_sections(source):
    vertices = tuple(p for s in source.surfaces for p in s.vertices_m)
    faces = tuple((i, i+1, i+2) for i in range(0, len(vertices), 3))
    return [_mesh_section_polygon(vertices, faces, z) for z in (1/6, 1/2, 5/6)]


class DeliveredBookAreaTests(TestCase):
    def test_coplanar_floor_section_does_not_fill_a_step_cut(self):
        from design.maas.geometry_language.compiler import compile_geometry_program
        program = parse_geometry_dsl('result = difference(box(10,10,9), '
                                     'translate(box(5,10,4.5), vector=[0,0,4.5]))')
        compiled = compile_geometry_program(program)
        solid = mesh_section_solid(compiled.vertices, compiled.triangles)
        self.assertAlmostEqual(solid_section_polygon(solid, 4.5).area,
                               compiled._solid.slice(4.5).area(), places=7)
        self.assertEqual(solid_section_polygon(solid, 4.5).area, 50)

    def test_three_bands_keep_five_parts_and_every_upper_floor(self):
        source = compile_geometry_program_to_source_mass(bridge_program(), box(0, 0, 20, 20))
        self.assertIsNotNone(source)
        for z, section in zip((1/6, 1/2, 5/6), mesh_sections(source)):
            from shapely.ops import unary_union
            proxy = unary_union([v.footprint for v in source.volumes
                                 if v.bottom_fraction < z < v.top_fraction])
            self.assertAlmostEqual(proxy.area, section.area, places=5)
        self.assertEqual(len(source.volumes), 5)

    def test_imported_gfa_uses_delivered_mesh_not_requested_height_scale(self):
        site = SimpleNamespace(pnu='unregistered-unit-fixture', ground_capacity_m2=1500,
                               far_capacity_m2=6000, floor_height_m=3, parcel_area_m2=2500)
        source, entry = book_import._compile_record(record(), box(0, 0, 20, 20), site)
        self.assertIsNotNone(source, entry)
        self.assertAlmostEqual(entry['floor_area_m2'], sum(s.area for s in mesh_sections(source)), places=5)
        self.assertEqual(entry['book_floor_count'], 3)
        for key in ('actual_floor_areas_m2', 'original_transformed_floor_areas_m2',
                    'proxy_floor_areas_m2', 'mesh_floor_area_missing_from_proxy_m2',
                    'export_area_comparison_resolution_m2'):
            self.assertEqual(len(entry['delivered_floor_evidence'][key]), 3, key)

    def test_missing_last_floor_proxy_is_reported(self):
        from dataclasses import replace
        site = SimpleNamespace(pnu='unregistered-unit-fixture', ground_capacity_m2=1500,
                               far_capacity_m2=6000, floor_height_m=3, parcel_area_m2=2500)
        source, entry = book_import._compile_record(record(), box(0, 0, 20, 20), site)
        broken = replace(source, volumes=tuple(v for v in source.volumes if v.top_fraction < 1))
        evidence = book_import.delivered_floor_evidence(broken, record()['geometry_artifact']['storeyEvidence'],
                                                        floor_count=3, storey_m=3)
        self.assertFalse(evidence['measurement_consistent'])
        self.assertTrue(any('floor_3_mesh_area_missing_from_proxy' in issue for issue in evidence['measurement_issues']))

    def test_floor_center_on_horizontal_skin_is_probed_beside_it(self):
        candidate = record()
        candidate['geometry_artifact']['storeyEvidence']['floor_center_elevations_m'] = [1.5, 3, 7.5]
        site = SimpleNamespace(pnu='unregistered-unit-fixture', ground_capacity_m2=1500,
                               far_capacity_m2=6000, floor_height_m=3, parcel_area_m2=2500)
        source, entry = book_import._compile_record(candidate, box(0, 0, 20, 20), site)
        # The probe steps off a skin at a floor's centre plane and records
        # the offset; the book's half-height joint was floor 3's centre on
        # every vertical sentence (comp23), and refusing it was the rule.
        self.assertIsNotNone(source, entry)
        offsets = entry['delivered_floor_evidence'].get('floor_center_probe_offsets') or []
        self.assertTrue(any(abs(offset) > 0 for offset in offsets), offsets)

    def test_certificate_rejects_an_entry_reusing_other_geometry_measurements(self):
        from vlm_shortlist import seat_certificate
        site = SimpleNamespace(pnu='unregistered-unit-fixture', ground_capacity_m2=1500,
                               far_capacity_m2=6000, floor_height_m=3, parcel_area_m2=2500)
        source, entry = book_import._compile_record(record(), box(0, 0, 20, 20), site)
        entry = {**entry, 'floor_area_m2': entry['floor_area_m2'] * 2}
        with self.assertRaisesRegex(ValueError, 'BOOK.*(measurement|floor|evidence)'):
            seat_certificate('book:split-upper-floors', source, {}, site, book_entry=entry)
