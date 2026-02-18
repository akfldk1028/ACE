"""
Global configuration for Multi-Agent Termination Study.
13 patterns across 4 categories, model settings, paths.
"""

import os
import sys
from pathlib import Path

# ========================================
# Paths
# ========================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent  # 25_ACE/
AUTOGEN_KIT_PATH = PROJECT_ROOT / "AG" / "autogen_a2a_kit"
JSON_MODULES_PATH = PROJECT_ROOT / "JSON_MODULES"
RESULTS_DIR = BASE_DIR / "results"

# Ensure autogen_a2a_kit is importable
if str(AUTOGEN_KIT_PATH) not in sys.path:
    sys.path.insert(0, str(AUTOGEN_KIT_PATH))

# ========================================
# Model Settings
# ========================================

MODEL = "claude-haiku-4-5-20251001"           # Experiment runs (low cost)
MODEL_JUDGE = "claude-sonnet-4-5-20250929"    # G-Eval scoring
MODEL_SELECTOR = "claude-haiku-4-5-20251001"  # SelectorGroupChat LLM

# ========================================
# Experiment Parameters
# ========================================

MAX_MESSAGES_DEFAULT = 10
MAX_MESSAGES_HIGH = 25      # exp02 (extended runs)
REPEAT_COUNT = 1            # v2: no repeats (200 = 8 patterns x 25 tasks)
REPEAT_COUNT_LEGACY = 3     # v1: 780 = 13 patterns x 20 tasks x 3 repeats

# ========================================
# 13 Patterns - 4 Categories
# ========================================

# Category S: Single-Agent Baseline
PATTERNS_BASELINE = ["solo"]

# Category A: Flat Sequential
PATTERNS_FLAT = ["rr2", "rr3", "rr4"]

# Category B1: Centralized Routing (Star/Hub-and-Spoke topology)
PATTERNS_CENTRALIZED = ["sel3", "sel4"]

# Category B2: Decentralized Handoff (Mesh/Swarm topology)
PATTERNS_DECENTRALIZED = ["swm3", "swm4"]

# Legacy alias for backward compatibility
PATTERNS_DYNAMIC = PATTERNS_CENTRALIZED + PATTERNS_DECENTRALIZED

# Category C: Structured Feedback
PATTERNS_FEEDBACK = ["refl2", "refl3", "debate3", "debate4"]

# Category D: Composed/Nested
PATTERNS_COMPOSED = ["pipe", "moa"]

PATTERNS_ALL = PATTERNS_BASELINE + PATTERNS_FLAT + PATTERNS_DYNAMIC + PATTERNS_FEEDBACK + PATTERNS_COMPOSED

# Category map for easy lookup
PATTERN_CATEGORY = {}
for p in PATTERNS_BASELINE:
    PATTERN_CATEGORY[p] = "S"
for p in PATTERNS_FLAT:
    PATTERN_CATEGORY[p] = "A"
for p in PATTERNS_CENTRALIZED:
    PATTERN_CATEGORY[p] = "B1"
for p in PATTERNS_DECENTRALIZED:
    PATTERN_CATEGORY[p] = "B2"
for p in PATTERNS_FEEDBACK:
    PATTERN_CATEGORY[p] = "C"
for p in PATTERNS_COMPOSED:
    PATTERN_CATEGORY[p] = "D"

# Agent count per pattern
PATTERN_AGENT_COUNT = {
    "solo": 1,
    "rr2": 2, "rr3": 3, "rr4": 4,
    "sel3": 3, "sel4": 4, "swm3": 3, "swm4": 4,
    "refl2": 2, "refl3": 3, "debate3": 3, "debate4": 4,
    "pipe": 5, "moa": 4,
}

# Max messages per pattern
PATTERN_MAX_MESSAGES = {
    "solo": 5,
    "rr2": 10, "rr3": 10, "rr4": 12,
    "sel3": 10, "sel4": 12, "swm3": 10, "swm4": 12,
    "refl2": 8, "refl3": 10, "debate3": 10, "debate4": 12,
    "pipe": 14, "moa": 11,  # pipe: 8+6, moa: 3*3+2
}

# Representative patterns (1-2 per category, B1/B2 both represented)
# A=rr3, B1=sel3+sel4, B2=swm3+swm4, C=refl2+debate3, D=pipe
PATTERNS_REPRESENTATIVE = ["rr3", "sel3", "sel4", "swm3", "swm4", "refl2", "debate3", "pipe"]

# exp05: Lambda values for adaptive termination
LAMBDA_VALUES = [0.0, 0.1, 0.5]

# ========================================
# Category metadata
# ========================================

CATEGORY_NAMES = {
    "S": "Single-Agent Baseline",
    "A": "Flat Sequential (Chain)",
    "B1": "Centralized Routing (Star)",
    "B2": "Decentralized Handoff (Mesh)",
    "C": "Structured Feedback",
    "D": "Composed/Nested",
}

CATEGORY_COLORS = {
    "S": "#999999",   # gray
    "A": "#4C78A8",   # blue
    "B1": "#F58518",  # orange
    "B2": "#EECA3B",  # yellow
    "C": "#E45756",   # red
    "D": "#72B7B2",   # teal
}
