"""
Maintenance Runner - Master script for running all maintenance checks.

Usage:
    python run_maintenance.py --quick    # health_check only
    python run_maintenance.py --full     # all 5 checks (no health_check)
    python run_maintenance.py --all      # all 6 checks including health_check
    python run_maintenance.py            # same as --full
"""

import sys
import time
import argparse
from pathlib import Path

# Ensure maintenance directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))


def run_check(name: str, module_name: str) -> bool:
    """Run a single maintenance check module."""
    try:
        module = __import__(module_name)
        result = module.main()
        status = "PASS" if result else "FAIL"
        print(f"\n  [{status}] {name}")
        return result
    except Exception as e:
        print(f"\n  [ERROR] {name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="AG-ACE Maintenance Runner")
    parser.add_argument("--quick", action="store_true", help="Health check only")
    parser.add_argument("--full", action="store_true", help="All code checks (no health)")
    parser.add_argument("--all", action="store_true", help="All checks including health")
    args = parser.parse_args()

    # Default to --full if no flag given
    if not args.quick and not args.all:
        args.full = True

    print("=" * 60)
    print("  AG-ACE Maintenance System")
    print("=" * 60)

    start = time.time()
    results = {}

    # Quick mode: health check only
    if args.quick:
        print("\n--- Health Check ---")
        results["health_check"] = run_check("Health Check", "health_check")

    # Full mode: code/registry/doc checks
    if args.full or args.all:
        if args.all:
            print("\n--- Health Check ---")
            results["health_check"] = run_check("Health Check", "health_check")

        print("\n--- Port Map Validator ---")
        results["port_map_validator"] = run_check("Port Map Validator", "port_map_validator")

        print("\n--- Agent Registry Sync ---")
        results["agent_registry_sync"] = run_check("Agent Registry Sync", "agent_registry_sync")

        print("\n--- Model Field Checker ---")
        results["model_field_checker"] = run_check("Model Field Checker", "model_field_checker")

        print("\n--- Doc Sync Checker ---")
        results["doc_sync_checker"] = run_check("Doc Sync Checker", "doc_sync_checker")

    elapsed = time.time() - start

    # Summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, ok in results.items():
        icon = "PASS" if ok else "FAIL"
        print(f"  [{icon}] {name}")

    print(f"\n  {passed}/{total} checks passed ({elapsed:.1f}s)")
    print("=" * 60)

    return all(results.values())


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
