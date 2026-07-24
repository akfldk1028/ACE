"""Deterministic MASS-to-elevation execution adapter.

The shared agent repository owns identity and long-lived private memory. This
MAAS-owned adapter is the deployable geometry boundary used by the compiler
pipeline, so a checkout of ARR never depends on an unpinned nested repository.
"""

from .facade_strategy import select_facade_strategy
from .image_proposal import generate_elevation_image_proposal
from .runtime import generate_elevation_bundle

__all__ = [
    "generate_elevation_bundle",
    "generate_elevation_image_proposal",
    "select_facade_strategy",
]
