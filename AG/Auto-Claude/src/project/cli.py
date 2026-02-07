"""
CLI for project management in AG/Auto-Claude

Provides commands for submitting, listing, and managing projects.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.utils.config import get_settings
from src.utils.logger import Loggers
from src.project.spec import (
    ProjectSpec,
    ProjectStatus,
    ProjectPhase,
    load_project_spec,
    save_project_spec,
    EXAMPLE_SPEC,
)
from src.utils.models import Task, TaskType, Priority
from src.coordinator.task_queue import create_task_queue


def submit_project(
    spec_path: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    goals: Optional[List[str]] = None,
    priority: str = "medium",
) -> str:
    """
    Submit a new project to the queue.

    Args:
        spec_path: Path to spec file (yaml/json)
        name: Project name (if not using spec file)
        description: Project description (if not using spec file)
        goals: Project goals (if not using spec file)
        priority: Priority level

    Returns:
        Project ID
    """
    logger = Loggers.orchestrator()
    settings = get_settings()

    # Load or create spec
    if spec_path:
        spec = load_project_spec(spec_path)
    elif name and description and goals:
        spec = ProjectSpec(
            name=name,
            description=description,
            goals=goals,
            priority=priority,
        )
    else:
        raise ValueError("Either spec_path or (name, description, goals) required")

    # Save to queue folder
    queue_dir = Path(settings.projects_dir) / "queue"
    queue_dir.mkdir(parents=True, exist_ok=True)

    spec_file = queue_dir / f"{spec.id}.yaml"
    save_project_spec(spec, spec_file)

    logger.info(
        "project_submitted",
        project_id=spec.id,
        name=spec.name,
        spec_file=str(spec_file),
    )

    return spec.id


def list_projects(
    status: Optional[str] = None,
    limit: int = 20,
) -> List[dict]:
    """
    List projects in the system.

    Args:
        status: Filter by status
        limit: Max results

    Returns:
        List of project info dicts
    """
    settings = get_settings()
    projects_dir = Path(settings.projects_dir)

    projects = []

    # Scan all folders
    for folder in ["queue", "completed", "failed"]:
        folder_path = projects_dir / folder
        if not folder_path.exists():
            continue

        for spec_file in folder_path.glob("*.yaml"):
            try:
                spec = load_project_spec(spec_file)

                if status and spec.status.value != status:
                    continue

                projects.append({
                    "id": spec.id,
                    "name": spec.name,
                    "status": spec.status.value,
                    "phase": spec.phase.value,
                    "progress": spec.progress_percent,
                    "created_at": spec.created_at.isoformat() if spec.created_at else None,
                    "folder": folder,
                })

            except Exception:
                continue

        for spec_file in folder_path.glob("*.json"):
            try:
                spec = load_project_spec(spec_file)

                if status and spec.status.value != status:
                    continue

                projects.append({
                    "id": spec.id,
                    "name": spec.name,
                    "status": spec.status.value,
                    "phase": spec.phase.value,
                    "progress": spec.progress_percent,
                    "created_at": spec.created_at.isoformat() if spec.created_at else None,
                    "folder": folder,
                })

            except Exception:
                continue

    # Sort by created_at desc
    projects.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    return projects[:limit]


def get_project_status(project_id: str) -> Optional[dict]:
    """
    Get detailed status of a project.

    Args:
        project_id: Project ID

    Returns:
        Project status dict or None
    """
    settings = get_settings()
    projects_dir = Path(settings.projects_dir)

    # Search all folders
    for folder in ["queue", "completed", "failed"]:
        folder_path = projects_dir / folder

        for spec_file in folder_path.glob(f"*{project_id}*.yaml"):
            spec = load_project_spec(spec_file)
            return {
                "id": spec.id,
                "name": spec.name,
                "description": spec.description,
                "status": spec.status.value,
                "phase": spec.phase.value,
                "progress": spec.progress_percent,
                "current_task": spec.current_task,
                "completed_tasks": spec.completed_tasks,
                "goals": spec.goals,
                "artifacts": spec.artifacts,
                "errors": spec.errors,
                "created_at": spec.created_at.isoformat() if spec.created_at else None,
                "started_at": spec.started_at.isoformat() if spec.started_at else None,
                "completed_at": spec.completed_at.isoformat() if spec.completed_at else None,
            }

        for spec_file in folder_path.glob(f"*{project_id}*.json"):
            spec = load_project_spec(spec_file)
            return {
                "id": spec.id,
                "name": spec.name,
                "description": spec.description,
                "status": spec.status.value,
                "phase": spec.phase.value,
                "progress": spec.progress_percent,
                "current_task": spec.current_task,
                "completed_tasks": spec.completed_tasks,
                "goals": spec.goals,
                "artifacts": spec.artifacts,
                "errors": spec.errors,
                "created_at": spec.created_at.isoformat() if spec.created_at else None,
                "started_at": spec.started_at.isoformat() if spec.started_at else None,
                "completed_at": spec.completed_at.isoformat() if spec.completed_at else None,
            }

    return None


def create_example_spec(output_path: Optional[str] = None) -> str:
    """
    Create an example project spec file.

    Args:
        output_path: Output file path

    Returns:
        Created file path
    """
    settings = get_settings()

    if output_path:
        file_path = Path(output_path)
    else:
        file_path = Path(settings.projects_dir) / "examples" / "example_project.yaml"

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(EXAMPLE_SPEC, encoding="utf-8")

    return str(file_path)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="ace-project",
        description="AG/Auto-Claude Project Management CLI",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a project")
    submit_parser.add_argument("spec", nargs="?", help="Path to spec file")
    submit_parser.add_argument("--name", "-n", help="Project name")
    submit_parser.add_argument("--description", "-d", help="Description")
    submit_parser.add_argument("--goal", "-g", action="append", help="Goal (repeatable)")
    submit_parser.add_argument("--priority", "-p", default="medium", help="Priority")

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

    if not args.command:
        parser.print_help()
        return

    # Execute command
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
            print("Error: Provide spec file or --name, --description, --goal")
            sys.exit(1)

        print(f"Project submitted: {project_id}")

    elif args.command == "list":
        projects = list_projects(status=args.status, limit=args.limit)

        if args.json:
            print(json.dumps(projects, indent=2))
        else:
            print(f"{'ID':<10} {'Name':<25} {'Status':<12} {'Progress':<10} {'Phase'}")
            print("-" * 75)
            for p in projects:
                print(f"{p['id']:<10} {p['name'][:24]:<25} {p['status']:<12} {p['progress']:>3}%       {p['phase']}")

    elif args.command == "status":
        status = get_project_status(args.project_id)

        if not status:
            print(f"Project not found: {args.project_id}")
            sys.exit(1)

        if args.json:
            print(json.dumps(status, indent=2))
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

    elif args.command == "example":
        path = create_example_spec(args.output)
        print(f"Example spec created: {path}")


if __name__ == "__main__":
    main()
