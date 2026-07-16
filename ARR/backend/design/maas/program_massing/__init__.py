"""Program-conditioned architectural massing."""

from .profiles import load_program_profiles, resolve_program_profile
from .research_priors import load_research_search_priors, program_search_prior
from .scoring import attach_program_massing_evidence
from .sequences import creative_archive_sequences, program_archive_sequences, program_seed_sequences
from .creative import attach_creative_mass_evidence, creative_seed_sequences
from .spatial_evaluation import attach_program_spatial_evidence
from .book_projection import book_operation_variants, book_projection_scope, book_sentence_variants, compose_program_with_book_operations
from .book_scope import materialize_book_scope, projection_scope
from .section_graph import (
    ProgramSectionGraphEdit,
    apply_program_section_graph_edits,
    mutate_program_section_sequence,
    program_section_graph_from_sequence,
)

__all__ = ["ProgramSectionGraphEdit", "apply_program_section_graph_edits", "attach_creative_mass_evidence", "attach_program_massing_evidence", "attach_program_spatial_evidence", "book_operation_variants", "book_projection_scope", "book_sentence_variants", "compose_program_with_book_operations", "creative_archive_sequences", "creative_seed_sequences", "load_program_profiles", "load_research_search_priors", "materialize_book_scope", "mutate_program_section_sequence", "program_archive_sequences", "program_search_prior", "program_section_graph_from_sequence", "program_seed_sequences", "projection_scope", "resolve_program_profile"]
