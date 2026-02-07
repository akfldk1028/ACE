#!/usr/bin/env python3
"""
AG/Auto-Claude CLI - 24/7 Autonomous Coding Hub

Unified entry point for the CLI-Only orchestration system.

Usage:
    # Start 24/7 factory (Watcher + Orchestrator)
    python cli.py

    # Single task execution
    python cli.py run --task "Build a calculator app" --complexity standard

    # Project submission
    python cli.py submit --spec project.yaml

    # List projects
    python cli.py list

    # Check project status
    python cli.py status <id>

    # Start SharedMemory + MessageBus services
    python cli.py services

    # Create example spec
    python cli.py example

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                      cli.py                                  │
    │                                                              │
    │  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
    │  │ProjectWatcher│────▶│ TaskQueue    │────▶│Orchestrator │ │
    │  │(projects/)   │     │ (SQLite)     │     │(20 Agents)  │ │
    │  └──────────────┘     └──────────────┘     └─────────────┘ │
    │                                                              │
    │  WorkflowExecutor: spec_runner.py → run.py pipeline         │
    │  Agents: Planner → Coder → QA Reviewer → QA Fixer          │
    └─────────────────────────────────────────────────────────────┘
"""

import asyncio
import sys
import io
import argparse
import logging
from pathlib import Path
from typing import Optional

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_settings, Settings
from src.utils.logger import configure_logging, Loggers
from src.coordinator.orchestrator import Orchestrator
from src.project.watcher import ProjectWatcher
from src.project.cli import submit_project, list_projects, get_project_status, create_example_spec


def print_banner():
    """Print startup banner"""
    print()
    print("+" + "=" * 62 + "+")
    print("|           AG/Auto-Claude CLI - 24/7 Factory                  |")
    print("|           20 AI Agents | CLI-Only Orchestration              |")
    print("+" + "=" * 62 + "+")
    print()


async def run_24_7(
    projects_dir: Optional[str] = None,
    db_path: Optional[str] = None,
    debug: bool = False,
) -> None:
    """
    Run the 24/7 AI Project Factory.

    1. Starts the project watcher (monitors projects/ folder)
    2. Starts the orchestrator (processes tasks with 20 agents)
    3. Runs forever until Ctrl+C
    """
    configure_logging(level="DEBUG" if debug else "INFO")
    logger = Loggers.orchestrator()

    settings = get_settings()
    projects_dir = projects_dir or settings.projects_dir
    db_path = db_path or settings.queue_db_path

    logger.info("factory_starting", projects_dir=projects_dir, db_path=db_path)

    print_banner()
    print(f"  Drop project specs in: {projects_dir}/queue/")
    print()
    print("  20 AI Agents Ready:")
    print("    - Auto-Claude: Planner, Coder, QA Reviewer, QA Fixer")
    print("    - AG Autogen:  Research, Analyst, Writer, Reviewer, Coordinator")
    print("    - AG Law:      Case Analyzer, Legal Researcher, Risk Assessor...")
    print("    - AG A2A:      Poetry, Philosophy, History, Calculator, GUI Test")
    print("    - Claude CLI:  Plan Agent")
    print()
    print("  Press Ctrl+C to stop")
    print()

    watcher = ProjectWatcher(projects_dir, db_path)
    orchestrator = Orchestrator(db_path)

    try:
        await asyncio.gather(
            watcher.start(),
            orchestrator.start(),
        )
    except KeyboardInterrupt:
        logger.info("factory_shutdown_requested")
        print("\nShutting down...")
        await orchestrator.stop()
        await watcher.stop()

    logger.info("factory_stopped")
    print("Factory stopped.")


def run_single_task(task_description: str, complexity: str = "standard", auto_merge: bool = False):
    """Run a single task through the full pipeline."""
    from src.bridge.workflow_executor import WorkflowExecutor

    settings = get_settings()
    executor = WorkflowExecutor(
        auto_claude_path=str(Path(settings.auto_claude_path).parent.parent),
        project_path=None,
    )

    print_banner()
    print(f"  Task: {task_description}")
    print(f"  Complexity: {complexity}")
    print(f"  Auto-merge: {auto_merge}")
    print()

    result = executor.execute_full_pipeline_sync(
        task_description=task_description,
        complexity=complexity,
        auto_merge=auto_merge,
    )

    print()
    if result.get("success"):
        print(f"  [OK] Task completed successfully")
        if result.get("spec_id"):
            print(f"  Spec ID: {result['spec_id']}")
            print(f"  Review:  cd Auto-Claude && python run.py --spec {result['spec_id']} --review")
            print(f"  Merge:   cd Auto-Claude && python run.py --spec {result['spec_id']} --merge")
    else:
        print(f"  [FAIL] {result.get('error', 'Unknown error')}")

    if result.get("duration_seconds"):
        print(f"  Duration: {result['duration_seconds']:.1f}s")

    return result


def start_services():
    """Start SharedMemory + MessageBus servers."""
    print_banner()
    print("  Starting AG-CLI services...")
    print()

    try:
        from ag_cli.mcp.shared_memory import main as shared_memory_main
        from ag_cli.mcp.message_bus import main as message_bus_main
        import threading

        # Start MessageBus in background
        mb_thread = threading.Thread(target=message_bus_main, daemon=True)
        mb_thread.start()
        print("  [OK] MessageBus started (port 8100)")

        # Start SharedMemory (blocks)
        print("  [OK] SharedMemory starting (port 8101)...")
        shared_memory_main()

    except ImportError as e:
        print(f"  [ERROR] Could not import AG-CLI services: {e}")
        print("  Make sure ag_cli/ modules are available.")
        sys.exit(1)
    except Exception as e:
        print(f"  [ERROR] {e}")
        sys.exit(1)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="AG/Auto-Claude CLI",
        description="24/7 AI Project Factory - Autonomous coding with 20 AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start 24/7 factory
  python cli.py

  # Run a single task
  python cli.py run --task "Build a REST API with user auth"

  # Submit a project spec
  python cli.py submit --spec my-project.yaml

  # List projects
  python cli.py list

  # Check project status
  python cli.py status abc123

  # Start AG-CLI services (SharedMemory + MessageBus)
  python cli.py services

  # Create example spec
  python cli.py example
        """,
    )

    parser.add_argument(
        "--projects-dir", "-p",
        help="Directory to watch for project specs",
    )
    parser.add_argument(
        "--db-path",
        help="Path to task queue database",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command (single task)
    run_parser = subparsers.add_parser("run", help="Run a single task through the pipeline")
    run_parser.add_argument("--task", "-t", required=True, help="Task description")
    run_parser.add_argument(
        "--complexity", "-c",
        choices=["simple", "standard", "complex"],
        default="standard",
        help="Task complexity (default: standard)",
    )
    run_parser.add_argument(
        "--auto-merge",
        action="store_true",
        help="Automatically merge after successful build",
    )

    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a project")
    submit_parser.add_argument("--spec", "-s", help="Path to spec file")
    submit_parser.add_argument("--name", "-n", help="Project name")
    submit_parser.add_argument("--description", "-d", help="Description")
    submit_parser.add_argument("--goal", "-g", action="append", help="Goal (repeatable)")
    submit_parser.add_argument("--priority", default="medium", help="Priority")

    # List command
    list_parser = subparsers.add_parser("list", help="List projects")
    list_parser.add_argument("--status", "-s", help="Filter by status")
    list_parser.add_argument("--limit", "-l", type=int, default=20, help="Max results")
    list_parser.add_argument("--json", "-j", action="store_true", help="JSON output")

    # Status command
    status_parser = subparsers.add_parser("status", help="Get project status")
    status_parser.add_argument("project_id", help="Project ID")
    status_parser.add_argument("--json", "-j", action="store_true", help="JSON output")

    # Services command
    subparsers.add_parser("services", help="Start SharedMemory + MessageBus servers")

    # Example command
    example_parser = subparsers.add_parser("example", help="Create example spec")
    example_parser.add_argument("--output", "-o", help="Output path")

    args = parser.parse_args()

    # Handle subcommands
    if args.command == "run":
        run_single_task(
            task_description=args.task,
            complexity=args.complexity,
            auto_merge=args.auto_merge,
        )
        return

    elif args.command == "submit":
        if args.spec:
            project_id = submit_project(spec_path=args.spec)
        elif args.name and args.description and args.goal:
            project_id = submit_project(
                name=args.name,
                description=args.description,
                goals=args.goal,
                priority=args.priority,
            )
        else:
            print("Error: Provide --spec or (--name, --description, --goal)")
            sys.exit(1)
        print(f"Project submitted: {project_id}")
        print(f"  Drop specs in projects/queue/ or wait for processing")
        return

    elif args.command == "list":
        import json as json_module
        projects = list_projects(status=args.status, limit=args.limit)

        if args.json:
            print(json_module.dumps(projects, indent=2))
        else:
            if not projects:
                print("No projects found")
                return
            print(f"{'ID':<10} {'Name':<25} {'Status':<12} {'Progress':<10} {'Phase'}")
            print("-" * 75)
            for p in projects:
                print(f"{p['id']:<10} {p['name'][:24]:<25} {p['status']:<12} {p['progress']:>3}%       {p['phase']}")
        return

    elif args.command == "status":
        import json as json_module
        status = get_project_status(args.project_id)

        if not status:
            print(f"Project not found: {args.project_id}")
            sys.exit(1)

        if args.json:
            print(json_module.dumps(status, indent=2))
        else:
            print(f"Project: {status['name']} ({status['id']})")
            print(f"Status:  {status['status']}")
            print(f"Phase:   {status['phase']}")
            print(f"Progress: {status['progress']}%")
            print()
            print("Goals:")
            for g in status['goals']:
                print(f"  - {g}")
            if status['current_task']:
                print()
                print(f"Current: {status['current_task']}")
            if status['errors']:
                print()
                print("Errors:")
                for e in status['errors']:
                    print(f"  ! {e}")
        return

    elif args.command == "services":
        start_services()
        return

    elif args.command == "example":
        path = create_example_spec(args.output)
        print(f"Example spec created: {path}")
        print(f"  Edit and move to projects/queue/ to run")
        return

    # Default: run 24/7 factory
    try:
        asyncio.run(run_24_7(
            projects_dir=args.projects_dir,
            db_path=args.db_path,
            debug=args.debug,
        ))
    except KeyboardInterrupt:
        print("\nFactory stopped.")


if __name__ == "__main__":
    main()
