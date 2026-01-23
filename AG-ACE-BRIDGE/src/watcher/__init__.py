"""
Pattern Watcher Module

Monitors AutoGen Studio output folders for new patterns.
Auto-imports detected patterns into AG-ACE-BRIDGE Orchestrator.
"""

from .pattern_watcher import PatternWatcher, PatternEvent

__all__ = ["PatternWatcher", "PatternEvent"]
