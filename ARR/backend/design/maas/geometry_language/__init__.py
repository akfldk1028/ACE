"""Extended CSG procedural architectural massing language."""

from .ast import GEOMETRY_PROGRAM_JSON_SCHEMA, GeometryIssue, GeometryNode, GeometryProgram
from .base_seeds import BASE_SEED_SPECS, BaseSeedSpec, base_seed_catalog, base_seed_program, base_seed_programs, box_derived_base_seed_programs
from .book_adapter import apply_book_projection_to_geometry_program
from .compiler import CompilationResult, compile_geometry_program
from .cost import ProgramCost, candidate_sort_key, geometry_equivalent, program_cost
from .dsl import GeometryDslError, parse_geometry_dsl, program_to_dsl
from .gate import GeometryGatePolicy, compilation_gate
from .loop import GeometryLoopCandidate, GeometryLoopResult, run_geometry_program_a2a_loop
from .llm_adapter import GeometryAuthorError, author_geometry_programs_with_openai, geometry_programs_from_author_payload
from .mutation import GeometryEdit, MutationResult, apply_geometry_edits
from .outcome_graph import GeometryOutcomeGraph
from .programs import GeometryProgramBuilder, architectural_shape_programs, l_mass_difference_program, reference_language_programs
from .render import render_compilation_preview
from .source_bridge import compile_geometry_program_to_source_mass, replace_source_dominant_with_geometry_program
from .synthesis import synthesize_architectural_programs, synthesis_requests_from_program_profile
from .vlm_adapter import build_geometry_graph_notes, build_geometry_graph_snapshot, openai_vlm_geometry_critic, score_geometry_program_with_openai_vlm

__all__ = [
    "CompilationResult",
    "BASE_SEED_SPECS",
    "BaseSeedSpec",
    "GEOMETRY_PROGRAM_JSON_SCHEMA",
    "GeometryEdit",
    "GeometryDslError",
    "GeometryAuthorError",
    "GeometryGatePolicy",
    "GeometryIssue",
    "GeometryLoopCandidate",
    "GeometryLoopResult",
    "GeometryNode",
    "GeometryOutcomeGraph",
    "GeometryProgram",
    "GeometryProgramBuilder",
    "MutationResult",
    "ProgramCost",
    "apply_geometry_edits",
    "apply_book_projection_to_geometry_program",
    "architectural_shape_programs",
    "author_geometry_programs_with_openai",
    "base_seed_catalog",
    "base_seed_program",
    "base_seed_programs",
    "box_derived_base_seed_programs",
    "build_geometry_graph_notes",
    "build_geometry_graph_snapshot",
    "candidate_sort_key",
    "compilation_gate",
    "compile_geometry_program",
    "compile_geometry_program_to_source_mass",
    "geometry_equivalent",
    "geometry_programs_from_author_payload",
    "l_mass_difference_program",
    "openai_vlm_geometry_critic",
    "parse_geometry_dsl",
    "program_cost",
    "program_to_dsl",
    "reference_language_programs",
    "render_compilation_preview",
    "replace_source_dominant_with_geometry_program",
    "run_geometry_program_a2a_loop",
    "score_geometry_program_with_openai_vlm",
    "synthesize_architectural_programs",
    "synthesis_requests_from_program_profile",
]
