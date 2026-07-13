"""Interactive MAAS operation layer.

This package keeps user-facing direct manipulation separate from the legal
MAAS generator. UI gestures become operation specs here, then every accepted
operation is routed through legal review/repair before returning to the client.
"""

from .orchestrator import apply_interactive_mass_operation
from .revision import apply_conversational_graph_revision
from .reference_intent import interpret_reference_intent_with_openai_vlm
from .language_brain import propose_language_mutation
from .revision_learning import build_revision_learning_profile

__all__ = [
    "apply_conversational_graph_revision",
    "apply_interactive_mass_operation",
    "interpret_reference_intent_with_openai_vlm",
    "propose_language_mutation",
    "build_revision_learning_profile",
]
