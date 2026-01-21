#!/usr/bin/env python3
"""
AG-ACE-BRIDGE 24/7 AI Project Factory

Main entry point for running the autonomous project factory.

Usage:
    # Start 24/7 orchestrator (watches projects/ folder)
    python run_24_7.py

    # Start with custom projects directory
    python run_24_7.py --projects-dir /path/to/projects

    # Start with debug logging
    python run_24_7.py --debug

    # Submit a project directly
    python run_24_7.py submit --spec project.yaml

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    run_24_7.py                              │
    │                                                             │
    │  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
    │  │ProjectWatcher│────▶│ TaskQueue    │────▶│Orchestrator │ │
    │  │(projects/)   │     │ (SQLite)     │     │(17 Agents)  │ │
    │  └──────────────┘     └──────────────┘     └─────────────┘ │
    │                                                             │
    │  Agents:                                                    │
    │  - Auto-Claude (4): Planner, Coder, QA Reviewer, QA Fixer  │
    │  - AG Autogen (8): Research, Analyst, Writer, etc.         │
    │  - AG Law (5): Case Analyzer, Legal Researcher, etc.       │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

How it works:
    1. Drop a .yaml/.json spec file in projects/queue/
    2. Watcher detects and creates tasks from spec
    3. Orchestrator processes tasks 24/7
    4. Results saved, new tasks generated
    5. Infinite loop until shutdown

Example spec (projects/queue/my-project.yaml):
    name: "My API"
    description: "Build a REST API"
    goals:
      - "Create user authentication"
      - "Implement CRUD endpoints"
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import get_settings, Settings
from src.utils.logger import configure_logging, Loggers
from src.coordinator.orchestrator import Orchestrator
from src.project.watcher import ProjectWatcher
from src.project.cli import submit_project, list_projects, get_project_status, create_example_spec


async def run_24_7(
    projects_dir: Optional[str] = None,
    db_path: Optional[str] = None,
    debug: bool = False,
) -> None:
    """
    Run the 24/7 AI Project Factory.

    This is the main entry point that:
    1. Starts the project watcher (monitors projects/ folder)
    2. Starts the orchestrator (processes tasks with 17 agents)
    3. Runs forever until Ctrl+C

    Args:
        projects_dir: Directory to watch for project specs
        db_path: Path to task queue database
        debug: Enable debug logging
    """
    # Configure logging
    configure_logging(level="DEBUG" if debug else "INFO")
    logger = Loggers.orchestrator()

    settings = get_settings()

    # Use provided or default paths
    projects_dir = projects_dir or settings.projects_dir
    db_path = db_path or str(settings.task_queue_db)

    logger.info(
        "factory_starting",
        projects_dir=projects_dir,
        db_path=db_path,
    )

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           AG-ACE-BRIDGE 24/7 AI PROJECT FACTORY             ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║                                                              ║")
    print("║  Drop project specs in:                                      ║")
    print(f"║    {projects_dir}/queue/".ljust(62) + "║")
    print("║                                                              ║")
    print("║  17 AI Agents Ready:                                         ║")
    print("║    - Auto-Claude: Planner, Coder, QA Reviewer, QA Fixer     ║")
    print("║    - AG Autogen:  Research, Analyst, Writer, Reviewer...    ║")
    print("║    - AG Law:      Case Analyzer, Legal Researcher...        ║")
    print("║                                                              ║")
    print("║  Press Ctrl+C to stop                                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Create watcher and orchestrator
    watcher = ProjectWatcher(projects_dir, db_path)
    orchestrator = Orchestrator(db_path)

    # Run both concurrently
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


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="AG-ACE-BRIDGE",
        description="24/7 AI Project Factory - Autonomous project execution with 17 AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start 24/7 factory
  python run_24_7.py

  # Submit a project
  python run_24_7.py submit --spec my-project.yaml

  # List projects
  python run_24_7.py list

  # Check project status
  python run_24_7.py status abc123

  # Create example spec
  python run_24_7.py example
        """,
    )

    parser.add_argument(
        "--projects-dir", "-p",
        help="Directory to watch for project specs",
    )
    parser.add_argument(
        "--db-path", "-d",
        help="Path to task queue database",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

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

    # Example command
    example_parser = subparsers.add_parser("example", help="Create example spec")
    example_parser.add_argument("--output", "-o", help="Output path")

    args = parser.parse_args()

    # Handle subcommands
    if args.command == "submit":
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
        print(f"✓ Project submitted: {project_id}")
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

    elif args.command == "example":
        path = create_example_spec(args.output)
        print(f"✓ Example spec created: {path}")
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
