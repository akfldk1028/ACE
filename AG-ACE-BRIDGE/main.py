#!/usr/bin/env python3
"""
AG-ACE-BRIDGE Main Entry Point

24/7 AI Project Factory - Auto-Claude + AG Integration

Usage:
    # Run dashboard only (for monitoring)
    python main.py --dashboard

    # Run orchestrator only (24/7 background service)
    python main.py --orchestrator

    # Run both dashboard and orchestrator together
    python main.py --all

    # Quick start (same as --all)
    python main.py

Commands:
    - Dashboard: http://localhost:8080
    - A2A Agents: ports 8003-8006 (start separately)
    - SharedMemory: port 8101 (AG-CLI, start separately)
"""

import asyncio
import argparse
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     █████╗  ██████╗       █████╗  ██████╗███████╗                ║
║    ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝                ║
║    ███████║██║  ███╗     ███████║██║     █████╗                  ║
║    ██╔══██║██║   ██║     ██╔══██║██║     ██╔══╝                  ║
║    ██║  ██║╚██████╔╝     ██║  ██║╚██████╗███████╗                ║
║    ╚═╝  ╚═╝ ╚═════╝      ╚═╝  ╚═╝ ╚═════╝╚══════╝                ║
║                                                                  ║
║    ██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗                  ║
║    ██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝                  ║
║    ██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗                    ║
║    ██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝                    ║
║    ██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗                  ║
║    ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝                  ║
║                                                                  ║
║            24/7 AI Project Factory                               ║
║     Auto-Claude + AG autogen_a2a_kit Integration                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_info():
    """Print service information"""
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ Services                                                        │
├─────────────────────────────────────────────────────────────────┤
│ Dashboard:        http://localhost:8080                         │
│ SharedMemory:     http://localhost:8101  (AG-CLI)              │
├─────────────────────────────────────────────────────────────────┤
│ A2A Agents (start separately):                                  │
│   poetry_agent:     http://localhost:8003                      │
│   philosophy_agent: http://localhost:8004                      │
│   history_agent:    http://localhost:8005                      │
│   calculator_agent: http://localhost:8006                      │
│   gui_test_agent:   http://localhost:8120                      │
├─────────────────────────────────────────────────────────────────┤
│ Auto-Claude Agents: OAuth-based (Claude Max)                   │
│   Planner, Coder, QA Reviewer, QA Fixer                        │
└─────────────────────────────────────────────────────────────────┘
""")


async def run_orchestrator_task():
    """Run the orchestrator in background"""
    from src.coordinator.orchestrator import Orchestrator

    orchestrator = Orchestrator()
    await orchestrator.start()


def run_dashboard_only():
    """Run dashboard server only"""
    from src.server.dashboard import run_dashboard
    run_dashboard(host="0.0.0.0", port=8080)


async def run_all():
    """Run both orchestrator and dashboard together"""
    import uvicorn
    from src.server.dashboard import app, orchestrator
    from src.coordinator.orchestrator import Orchestrator

    # Create orchestrator
    import src.server.dashboard as dashboard_module
    dashboard_module.orchestrator = Orchestrator()

    # Start orchestrator in background
    orchestrator_task = asyncio.create_task(
        dashboard_module.orchestrator.start()
    )

    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )
    server = uvicorn.Server(config)

    # Run dashboard (this blocks)
    try:
        await server.serve()
    finally:
        if dashboard_module.orchestrator:
            await dashboard_module.orchestrator.stop()
        orchestrator_task.cancel()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AG-ACE-BRIDGE: 24/7 AI Project Factory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run dashboard + orchestrator
  python main.py --dashboard        # Run dashboard only
  python main.py --orchestrator     # Run orchestrator only
  python main.py --all              # Run both (same as default)

Before running:
  1. Ensure A2A agents are running (ports 8003-8006)
  2. Ensure SharedMemory server is running (port 8101)
  3. Check .env configuration
        """
    )

    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Run dashboard server only (http://localhost:8080)"
    )
    parser.add_argument(
        "--orchestrator",
        action="store_true",
        help="Run orchestrator only (24/7 background service)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run both dashboard and orchestrator"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Dashboard port (default: 8080)"
    )

    args = parser.parse_args()

    print_banner()
    print_info()

    try:
        if args.dashboard:
            print("Starting Dashboard Server...")
            run_dashboard_only()

        elif args.orchestrator:
            print("Starting Orchestrator (24/7 mode)...")
            asyncio.run(run_orchestrator_task())

        else:
            # Default: run both
            print("Starting AG-ACE-BRIDGE (Dashboard + Orchestrator)...")
            asyncio.run(run_all())

    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
