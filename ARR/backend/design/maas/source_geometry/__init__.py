"""ARR-native source geometry compiler for MAAS grammar sequences."""

from .compiler import compile_component_graph_to_source_mass, compile_sequence_to_source_mass, source_mass_to_variant
from .coherence import COHERENCE_SCHEMA_VERSION, evaluate_source_volume_coherence
from .formal_principles import CANONICAL_FORMAL_PRINCIPLES, normalize_formal_principle
from .genome import GENOME_SCHEMA_VERSION, MassingGenome, build_massing_genome
from .ir import SourceMass, SourceVolume, VerbTrace

__all__ = [
    "CANONICAL_FORMAL_PRINCIPLES",
    "COHERENCE_SCHEMA_VERSION",
    "GENOME_SCHEMA_VERSION",
    "MassingGenome",
    "SourceMass",
    "SourceVolume",
    "VerbTrace",
    "build_massing_genome",
    "compile_sequence_to_source_mass",
    "compile_component_graph_to_source_mass",
    "evaluate_source_volume_coherence",
    "normalize_formal_principle",
    "source_mass_to_variant",
]
