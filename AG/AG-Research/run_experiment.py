"""
CLI Orchestrator for Multi-Agent Termination Experiments.

Usage:
  python run_experiment.py --exp 01              # Single experiment
  python run_experiment.py --exp 01 02 03        # Multiple
  python run_experiment.py --all                 # All experiments
  python run_experiment.py --exp 01 --dry-run    # Test (1 task × 1 pattern)
  python run_experiment.py --exp 01 --category A # Category A patterns only
"""

import argparse
import asyncio
import importlib
import sys
import time
from pathlib import Path

# Ensure AG-Research is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    PATTERNS_ALL,
    PATTERNS_BASELINE,
    PATTERNS_FLAT,
    PATTERNS_CENTRALIZED,
    PATTERNS_DECENTRALIZED,
    PATTERNS_FEEDBACK,
    PATTERNS_COMPOSED,
    RESULTS_DIR,
)


EXPERIMENT_MODULES = {
    "01": "exp01_pattern_efficiency.runner",
    "02": "exp02_termination_quality.runner",
    "03": "exp03_convergence_detection.analyze",
    "04": "exp04_error_attribution.analyze",
    "05": "exp05_adaptive_termination.runner",
}

CATEGORY_PATTERNS = {
    "S": PATTERNS_BASELINE,
    "A": PATTERNS_FLAT,
    "B1": PATTERNS_CENTRALIZED,
    "B2": PATTERNS_DECENTRALIZED,
    "C": PATTERNS_FEEDBACK,
    "D": PATTERNS_COMPOSED,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run multi-agent termination experiments"
    )
    parser.add_argument(
        "--exp", nargs="+", choices=list(EXPERIMENT_MODULES.keys()),
        help="Experiment numbers to run (e.g., 01 02)",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all experiments",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Test mode: 1 task × 1 pattern only",
    )
    parser.add_argument(
        "--category", choices=["S", "A", "B1", "B2", "C", "D"],
        help="Run only patterns from this category",
    )
    parser.add_argument(
        "--model", default=None,
        help="Override base model (e.g., gpt-4o-mini)",
    )
    parser.add_argument(
        "--pattern", nargs="+",
        help="Run specific pattern(s) (e.g., rr2 sel3)",
    )
    return parser.parse_args()


def get_patterns(args) -> list[str]:
    """Determine which patterns to run based on args."""
    if args.pattern:
        for p in args.pattern:
            if p not in PATTERNS_ALL:
                print(f"Error: Unknown pattern '{p}'. Available: {PATTERNS_ALL}")
                sys.exit(1)
        return args.pattern
    if args.category:
        return CATEGORY_PATTERNS[args.category]
    return PATTERNS_ALL


async def run_experiment(exp_id: str, patterns: list[str], dry_run: bool):
    """Import and run a single experiment."""
    module_name = EXPERIMENT_MODULES[exp_id]

    print(f"\n{'='*60}")
    print(f"  Experiment {exp_id}: {module_name}")
    print(f"  Patterns: {patterns}")
    print(f"  Dry run: {dry_run}")
    print(f"{'='*60}\n")

    # Ensure results directory
    exp_results_dir = RESULTS_DIR / f"exp{exp_id}"
    exp_results_dir.mkdir(parents=True, exist_ok=True)

    try:
        mod = importlib.import_module(module_name)
        if hasattr(mod, "main"):
            await mod.main(patterns=patterns, dry_run=dry_run)
        else:
            print(f"  Warning: {module_name} has no main() function. Running analyze only.")
            if hasattr(mod, "analyze"):
                mod.analyze()
    except Exception as e:
        print(f"  ERROR in exp{exp_id}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def main():
    args = parse_args()

    if not args.exp and not args.all:
        print("Error: Specify --exp or --all")
        sys.exit(1)

    if args.model:
        import config
        config.MODEL = args.model
        config.MODEL_SELECTOR = args.model
        print(f"Model override: {args.model}")

    experiments = list(EXPERIMENT_MODULES.keys()) if args.all else args.exp
    patterns = get_patterns(args)

    print(f"Multi-Agent Termination Study")
    print(f"Experiments: {experiments}")
    print(f"Patterns: {patterns}")
    print(f"Dry run: {args.dry_run}")
    print()

    t0 = time.monotonic()

    for exp_id in experiments:
        await run_experiment(exp_id, patterns, args.dry_run)

    elapsed = time.monotonic() - t0
    print(f"\nAll experiments complete. Total time: {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
