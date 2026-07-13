"""Program-conditioned architectural massing."""

from .profiles import load_program_profiles, resolve_program_profile
from .research_priors import load_research_search_priors, program_search_prior
from .scoring import attach_program_massing_evidence
from .sequences import creative_archive_sequences, program_archive_sequences, program_seed_sequences
from .creative import attach_creative_mass_evidence, creative_seed_sequences
from .spatial_evaluation import attach_program_spatial_evidence

__all__ = ["attach_creative_mass_evidence", "attach_program_massing_evidence", "attach_program_spatial_evidence", "creative_archive_sequences", "creative_seed_sequences", "load_program_profiles", "load_research_search_priors", "program_archive_sequences", "program_search_prior", "program_seed_sequences", "resolve_program_profile"]
