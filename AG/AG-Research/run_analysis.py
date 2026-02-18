"""
Run All Post-Experiment Analysis
================================
After exp01 (and optionally exp02/exp05) complete, run this to:
1. Generate exp01 plots (analyze.py)
2. Run exp03 convergence analysis (on exp01 data)
3. Run exp04 error attribution (on exp01 data)
4. Merge category results if needed
5. Generate all publication figures

Usage:
  python run_analysis.py                # Run all analysis
  python run_analysis.py --exp01-only   # Only exp01 analysis
  python run_analysis.py --figures      # Only regenerate figures
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RESULTS_DIR


def run_exp01_analysis():
    """Run exp01 analysis and plots."""
    print("\n=== Exp01: Pattern Efficiency Analysis ===")
    try:
        from exp01_pattern_efficiency.analyze import analyze
        analyze()
    except Exception as e:
        print(f"  Error: {e}")


def run_exp03_analysis():
    """Run exp03 convergence analysis (uses exp01 data)."""
    print("\n=== Exp03: Convergence Detection ===")
    raw_path = RESULTS_DIR / "exp01" / "raw.json"
    if not raw_path.exists():
        print(f"  Skipping: No exp01 raw data at {raw_path}")
        return
    try:
        from exp03_convergence_detection.analyze import analyze
        analyze()
    except Exception as e:
        print(f"  Error: {e}")


def run_exp04_analysis():
    """Run exp04 error attribution (uses exp01+exp02 data)."""
    print("\n=== Exp04: Error Attribution ===")
    raw_path = RESULTS_DIR / "exp01" / "raw.json"
    if not raw_path.exists():
        print(f"  Skipping: No exp01 raw data at {raw_path}")
        return
    try:
        from exp04_error_attribution.analyze import analyze
        analyze()
    except Exception as e:
        print(f"  Error: {e}")


def run_merge():
    """Merge category-level results if needed."""
    print("\n=== Merging Category Results ===")
    exp01_dir = RESULTS_DIR / "exp01"
    category_files = list(exp01_dir.glob("summary_*.csv"))
    if len(category_files) > 1 or not (exp01_dir / "summary.csv").exists():
        try:
            from merge_results import merge_exp01
            merge_exp01()
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print("  No merge needed (single run or already merged)")


def run_figures():
    """Generate all publication figures."""
    print("\n=== Generating Publication Figures ===")
    figures_dir = Path(__file__).parent / "figures"

    scripts = [
        "fig1_taxonomy.py",
        "fig4_exp01_main.py",
        "fig_preliminary_catA.py",
        "fig5_quality_trajectories.py",
        "fig6_convergence.py",
        "fig8_pareto.py",
    ]

    for script in scripts:
        script_path = figures_dir / script
        if script_path.exists():
            print(f"\n  Running {script}...")
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    script.replace('.py', ''), str(script_path))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except Exception as e:
                print(f"  Error in {script}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp01-only', action='store_true')
    parser.add_argument('--figures', action='store_true')
    parser.add_argument('--merge', action='store_true')
    args = parser.parse_args()

    t0 = time.monotonic()

    if args.figures:
        run_figures()
    elif args.merge:
        run_merge()
    elif args.exp01_only:
        run_merge()
        run_exp01_analysis()
    else:
        run_merge()
        run_exp01_analysis()
        run_exp03_analysis()
        run_exp04_analysis()
        run_figures()

    elapsed = time.monotonic() - t0
    print(f"\nAll analysis complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
