"""Compiler evidence survives delivery without changing geometry or pixels."""
import hashlib
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
from presentation import write_sequence
from vlm_shortlist import shape_id


class SequenceProvenanceTests(unittest.TestCase):
    def write(self, source, directory):
        certificate = {'name': 'evidence', 'shape_id': shape_id(source),
                       'certificate_id': 'unchanged-numeric-certificate',
                       'coverage_pct': 10, 'far_pct': 20, 'storey_m': 4}
        target = write_sequence('evidence', source, book={},
                                site=SimpleNamespace(shared_edges=()),
                                buildable=box(-5, -5, 25, 25), axis=(1, 0),
                                out_dir=directory, certificate=certificate)
        return target, json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))

    def test_typed_placement_holes_surfaces_and_affine_are_preserved_without_pixel_change(self):
        from design.maas.massv2.form import MatrixForm, place
        from design.maas.massv2.compile import compile_matrix_form
        from design.maas.source_geometry.solid import ConstantSurface, PolynomialSurface
        plan = Polygon(box(0, 0, 1, 1).exterior.coords,
                       [box(.3, .3, .7, .7).exterior.coords])
        placement = replace(place('room', size=(12, 10, 8), at=(2, 3, 0)),
                            plan_region=plan,
                            top_surface=PolynomialSurface(((0, 0, .8), (1, 0, .2))),
                            bottom_surface=ConstantSurface(.1))
        source = compile_matrix_form(MatrixForm('typed', (placement,), 'typed'), storey_height_m=4)
        self.assertIsNotNone(source)
        # The comparison keeps the same IR, certificate and render call while
        # removing only provenance metadata that previously was not exported.
        bare = replace(source, metadata={k: v for k, v in source.metadata.items()
                                         if k not in ('matrix_form', 'geometry_authority')})
        self.assertEqual(shape_id(source), shape_id(bare))
        with tempfile.TemporaryDirectory() as tmp:
            target, record = self.write(source, Path(tmp) / 'with-evidence')
            plain, previous = self.write(bare, Path(tmp) / 'without-evidence')
            self.assertEqual(target.read_bytes(), plain.read_bytes())
            self.assertEqual(record['png_sha256'], hashlib.sha256(target.read_bytes()).hexdigest())
            self.assertEqual(record['certificate_id'], previous['certificate_id'])
            self.assertEqual(record['final_shape_id'], previous['final_shape_id'])
            self.assertIn('source_geometry_evidence', record)
            exported = record['source_geometry_evidence']['metadata']
            self.assertEqual(exported['matrix_form'], json.loads(json.dumps(source.metadata['matrix_form'])))
            self.assertEqual(exported['geometry_authority'], source.metadata['geometry_authority'])
            self.assertEqual(len(exported['matrix_form']['placements'][0]['plan_region']['coordinates']), 2)
            self.assertIn('top_surface', exported['matrix_form']['placements'][0])

    def test_book_exports_real_program_compilation_and_marks_absent_metadata(self):
        from design.maas.geometry_language.ast import GeometryProgram
        from design.maas.geometry_language.source_bridge import compile_geometry_program_to_source_mass
        program = GeometryProgram.from_dict({
            'schema_version': 'arr.maas.geometry_program.v1', 'name': 'unitbook', 'root_id': 'pose',
            'nodes': [
                {'id': 'unit', 'kind': 'primitive', 'operator': 'box', 'inputs': [],
                 'parameters': {'width': 1., 'depth': 1., 'height': 1.}},
                {'id': 'pose', 'kind': 'transform', 'operator': 'matrix4', 'inputs': ['unit'],
                 'parameters': {'matrix4': [[2., 0., 0., 0.], [0., 1., 0., 0.],
                                            [0., 0., 1., 0.], [0., 0., 0., 1.]]}}]})
        source = compile_geometry_program_to_source_mass(program, box(-5, -5, 25, 25),
                                                        target_plan_area=100, minimum_plan_area=100)
        self.assertIsNotNone(source)
        source = replace(source, metadata={**source.metadata, 'authored_height_m': 8})
        with tempfile.TemporaryDirectory() as tmp:
            _, record = self.write(source, tmp)
            self.assertIn('source_geometry_evidence', record)
            evidence = record['source_geometry_evidence']
            for field in ('geometry_program', 'geometry_program_compilation', 'geometry_program_bridge_evidence'):
                self.assertEqual(evidence['metadata'][field], json.loads(json.dumps(source.metadata[field])))
            self.assertIn('matrix_form', evidence['missing_metadata_fields'])
            self.assertIn('matrix4_trace', evidence['missing_metadata_fields'])
            self.assertNotIn('matrix4_trace', evidence['metadata'])
            traces = evidence['metadata']['geometry_program_compilation']['trace']
            self.assertTrue(any('matrix4' in row for row in traces))
