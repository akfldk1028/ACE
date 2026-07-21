"""Extended CSG procedural architectural massing language."""

from .ast import GEOMETRY_PROGRAM_JSON_SCHEMA, GeometryIssue, GeometryNode, GeometryProgram
from .base_seeds import BASE_SEED_SPECS, BaseSeedSpec, base_seed_catalog, base_seed_program, base_seed_programs, box_derived_base_seed_programs
from .universal_form_bank import (
    UNIVERSAL_FORM_BANK_SCHEMA,
    universal_form_bank_contract,
    universal_form_program_pages,
    universal_form_programs,
)
from .program_projection import PROGRAM_PROJECTION_SCHEMA, project_program_requirements
from .book_adapter import apply_book_projection_to_geometry_program, recursive_book_projection_evidence
from .book_chassis_compatibility import (
    CHASSIS_RELATION_INVARIANTS,
    SPLIT_WING_RELATION_CONTRACT,
    ChassisRelationInvariant,
    SplitWingRelationContract,
    project_book_split_gap_ratio,
    split_wing_gap_ratio_from_unit,
    validate_book_chassis_compatibility,
)
from .book_parameter_projection import (
    BOOK_KERNEL_PARAMETER_PROJECTIONS,
    BOOK_RELATION_INVARIANTS,
    book_parameter_projection_evidence,
    project_book_parameter,
)
from .compiler import CompilationResult, compile_geometry_program
from .cost import ProgramCost, candidate_sort_key, geometry_equivalent, program_cost
from .dsl import GeometryDslError, parse_geometry_dsl, program_to_dsl
from .execution_passport import MASS_EXECUTION_PASSPORT_SCHEMA, build_mass_execution_passport, enrich_mass_execution_passport, passport_path_for_preview, write_mass_execution_passport
from .execution_agent_context import build_mass_execution_agent_context
from .gate import GeometryGatePolicy, compilation_gate
from .loop import GeometryLoopCandidate, GeometryLoopResult, run_geometry_program_a2a_loop
from .llm_adapter import GeometryAuthorError, author_geometry_programs_with_openai, geometry_programs_from_author_payload
from .mutation import (
    CompilerSafeMutationResult,
    GeometryEdit,
    MutationResult,
    apply_geometry_edits,
    apply_geometry_edits_compiler_safe,
)
from .outcome_graph import GeometryOutcomeGraph
from .programs import GeometryProgramBuilder, architectural_shape_programs, l_mass_difference_program, reference_language_programs
from .render import render_compilation_preview
from .source_bridge import compile_geometry_program_to_source_mass, replace_source_dominant_with_geometry_program
from .system_contract import build_extended_csg_contract
from .synthesis import synthesize_architectural_programs, synthesis_requests_from_program_profile
from .typology_priors import TYPOLOGY_PRIORS, TypologyPrior, typology_prior, typology_priors_for_program
from .vlm_adapter import audit_reference_matches_for_massing, build_geometry_graph_notes, build_geometry_graph_snapshot, openai_vlm_geometry_critic, retrieve_geometry_reference_matches, score_geometry_program_with_openai_vlm

__all__ = [
    "CompilationResult",
    "BASE_SEED_SPECS",
    "BaseSeedSpec",
    "GEOMETRY_PROGRAM_JSON_SCHEMA",
    "GeometryEdit",
    "CompilerSafeMutationResult",
    "GeometryDslError",
    "GeometryAuthorError",
    "GeometryGatePolicy",
    "MASS_EXECUTION_PASSPORT_SCHEMA",
    "GeometryIssue",
    "GeometryLoopCandidate",
    "GeometryLoopResult",
    "GeometryNode",
    "GeometryOutcomeGraph",
    "GeometryProgram",
    "GeometryProgramBuilder",
    "MutationResult",
    "ProgramCost",
    "TYPOLOGY_PRIORS",
    "TypologyPrior",
    "apply_geometry_edits",
    "apply_geometry_edits_compiler_safe",
    "apply_book_projection_to_geometry_program",
    "BOOK_KERNEL_PARAMETER_PROJECTIONS",
    "BOOK_RELATION_INVARIANTS",
    "CHASSIS_RELATION_INVARIANTS",
    "SPLIT_WING_RELATION_CONTRACT",
    "ChassisRelationInvariant",
    "SplitWingRelationContract",
    "book_parameter_projection_evidence",
    "project_book_parameter",
    "project_book_split_gap_ratio",
    "recursive_book_projection_evidence",
    "architectural_shape_programs",
    "audit_reference_matches_for_massing",
    "author_geometry_programs_with_openai",
    "base_seed_catalog",
    "base_seed_program",
    "base_seed_programs",
    "box_derived_base_seed_programs",
    "UNIVERSAL_FORM_BANK_SCHEMA",
    "universal_form_bank_contract",
    "universal_form_program_pages",
    "universal_form_programs",
    "PROGRAM_PROJECTION_SCHEMA",
    "project_program_requirements",
    "build_geometry_graph_notes",
    "build_geometry_graph_snapshot",
    "build_extended_csg_contract",
    "build_mass_execution_passport",
    "build_mass_execution_agent_context",
    "enrich_mass_execution_passport",
    "candidate_sort_key",
    "compilation_gate",
    "compile_geometry_program",
    "compile_geometry_program_to_source_mass",
    "geometry_equivalent",
    "geometry_programs_from_author_payload",
    "l_mass_difference_program",
    "openai_vlm_geometry_critic",
    "retrieve_geometry_reference_matches",
    "parse_geometry_dsl",
    "passport_path_for_preview",
    "program_cost",
    "program_to_dsl",
    "reference_language_programs",
    "render_compilation_preview",
    "replace_source_dominant_with_geometry_program",
    "run_geometry_program_a2a_loop",
    "score_geometry_program_with_openai_vlm",
    "synthesize_architectural_programs",
    "synthesis_requests_from_program_profile",
    "split_wing_gap_ratio_from_unit",
    "typology_prior",
    "typology_priors_for_program",
    "validate_book_chassis_compatibility",
    "write_mass_execution_passport",
]
