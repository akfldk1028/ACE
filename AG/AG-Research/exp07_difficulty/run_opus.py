"""
Exp07 Opus runner — uses `claude -p` (OAuth, no API key needed).
Simulates 5 patterns via prompt engineering, scores with OpenAI G-Eval.

Usage:
  python run_opus.py                # full 75 runs
  python run_opus.py --dry-run      # 5 runs only
  python run_opus.py --score-only   # score existing results
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results" / "exp07_claude_opus"
TASKS_PATH = Path(__file__).resolve().parent.parent / "task_suite_difficulty.json"

PATTERNS = ["solo", "swm3", "sel3", "refl2", "debate3"]

# Pattern-specific system prompts that simulate multi-agent coordination
PATTERN_PROMPTS = {
    "solo": "You are a knowledgeable assistant. Answer the following task directly and comprehensively. When done, end with TERMINATE.",

    "swm3": """You are simulating a 3-agent decentralized swarm team. Three specialists collaborate by handing off to each other:
- Agent 1 (Researcher): Gathers key facts and evidence
- Agent 2 (Analyst): Structures and analyzes the information
- Agent 3 (Writer): Synthesizes into a comprehensive final answer

Simulate this workflow: first research, then analyze, then write the final answer. Show each agent's contribution clearly labeled. End with TERMINATE.""",

    "sel3": """You are simulating a centralized selector team with 3 specialists + 1 coordinator:
- Coordinator: Reads the task, decides which specialist to call next
- Specialist A (Domain Expert): Deep knowledge on the topic
- Specialist B (Critical Thinker): Evaluates claims and identifies gaps
- Specialist C (Synthesizer): Creates the final comprehensive answer

Simulate this workflow: coordinator routes to specialists in sequence. Show each agent's contribution. End with TERMINATE.""",

    "refl2": """You are simulating a 2-agent reflection team:
- Generator: Produces a comprehensive initial response
- Critic: Reviews for accuracy, completeness, and coherence, then provides specific feedback
- Generator: Revises based on feedback to produce the final answer

Simulate this workflow: generate, critique, then revise. Show each agent's contribution. The critic should approve when quality is sufficient. End with TERMINATE.""",

    "debate3": """You are simulating a 3-agent debate team with moderator:
- Debater A: Presents the strongest argument from perspective 1
- Debater B: Presents the strongest counter-argument from perspective 2
- Debater C: Identifies what both miss and adds a third perspective
- Moderator: Synthesizes all arguments into a balanced final answer

Simulate this workflow: three perspectives then synthesis. Show each agent's contribution. End with TERMINATE.""",
}


def load_tasks():
    with open(TASKS_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_single(pattern: str, task: dict, timeout: int = 120) -> dict:
    """Run a single task using claude -p."""
    system_prompt = PATTERN_PROMPTS[pattern]
    full_prompt = f"{system_prompt}\n\nTASK: {task['task']}"

    start = time.time()
    try:
        result = subprocess.run(
            ["claude", "-p", full_prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
        duration = time.time() - start

        if result.returncode != 0:
            return {
                "task_id": task["id"],
                "pattern": pattern,
                "error": f"returncode={result.returncode}: {result.stderr[:200]}",
                "duration_sec": duration,
            }

        try:
            output = json.loads(result.stdout)
            content = output.get("result", result.stdout)
        except json.JSONDecodeError:
            content = result.stdout

        # Estimate tokens (~4 chars per token)
        prompt_tokens = len(full_prompt) // 4
        completion_tokens = len(str(content)) // 4

        return {
            "task_id": task["id"],
            "pattern": pattern,
            "difficulty": task["difficulty"],
            "domain": task["domain"],
            "content": str(content),
            "duration_sec": round(duration, 1),
            "total_tokens": prompt_tokens + completion_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        return {
            "task_id": task["id"],
            "pattern": pattern,
            "error": f"timeout after {timeout}s",
            "duration_sec": timeout,
        }
    except Exception as e:
        return {
            "task_id": task["id"],
            "pattern": pattern,
            "error": str(e),
            "duration_sec": time.time() - start,
        }


def main(dry_run=False):
    tasks = load_tasks()
    patterns = PATTERNS

    if dry_run:
        tasks = tasks[:1]  # 1 task
        patterns = patterns[:1]  # 1 pattern

    total = len(patterns) * len(tasks)
    print(f"Exp07 Opus: {len(patterns)} patterns x {len(tasks)} tasks = {total} runs")
    print(f"Output: {OUTPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    checkpoint_path = OUTPUT_DIR / "checkpoint.json"

    # Resume from checkpoint
    done_keys = set()
    if checkpoint_path.exists():
        with open(checkpoint_path, encoding="utf-8") as f:
            results = json.load(f)
        done_keys = {(r["pattern"], r["task_id"]) for r in results}
        print(f"Resuming: {len(done_keys)} already done")

    idx = 0
    for pattern in patterns:
        for task in tasks:
            key = (pattern, task["id"])
            if key in done_keys:
                idx += 1
                continue

            idx += 1
            print(f"  [{idx}/{total}] {pattern} / {task['id']} ({task['difficulty']})...", flush=True)

            result = run_single(pattern, task)
            results.append(result)

            # Checkpoint after each run
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            if result.get("error"):
                print(f"    ERROR: {result['error']}")
            else:
                print(f"    OK: {result['duration_sec']}s, ~{result['total_tokens']} tokens")

    # Save final
    with open(OUTPUT_DIR / "raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Summary CSV
    import csv
    with open(OUTPUT_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "pattern", "difficulty", "domain", "duration_sec", "total_tokens", "error"])
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k) for k in writer.fieldnames})

    errors = [r for r in results if r.get("error")]
    print(f"\nDone: {len(results)} runs, {len(errors)} errors")
    print(f"Saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
