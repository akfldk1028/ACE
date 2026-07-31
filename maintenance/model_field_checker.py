"""
Model Field Checker - Detects known invalid field access patterns on Task/Result models.

Targeted checks:
- task.input_data (should be task.input)
- Result(success=...) without status (allowed via model_validator)
- Task(..., input_data=...) constructor calls (should be input=)
- Task(..., status=...) constructor calls (Task has no status field)

This checker focuses on high-confidence issues to avoid false positives
from generic variable names like 'task' and 'result'.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Set, List

BASE = Path(__file__).resolve().parent.parent
AG_ACE_BRIDGE = BASE / "AG-ACE-BRIDGE"


def extract_model_fields(model_name: str) -> Set[str]:
    """Extract field names from a Pydantic model in models.py."""
    path = AG_ACE_BRIDGE / "src" / "utils" / "models.py"
    if not path.exists():
        return set()

    content = path.read_text(encoding="utf-8")

    pattern = rf'class {model_name}\(BaseModel\):\s*\n(.*?)(?=\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return set()

    block = match.group(1)
    fields = set()

    for m in re.finditer(r'^\s+(\w+)\s*:', block, re.MULTILINE):
        name = m.group(1)
        if not name.startswith('_') and name != 'Config':
            fields.add(name)

    for m in re.finditer(r'@property\s+def\s+(\w+)', block):
        fields.add(m.group(1))

    return fields


# Known invalid patterns that indicate real bugs (not false positives)
KNOWN_BAD_PATTERNS = [
    # task.input_data should be task.input
    {
        "pattern": r'task\.input_data\b',
        "message": "task.input_data should be task.input",
        "severity": "error",
    },
    # Task(..., input_data=...) constructor
    {
        "pattern": r'Task\([^)]*input_data\s*=',
        "message": "Task() constructor: input_data= should be input=",
        "severity": "error",
    },
    # Task(..., status=...) — Task model has no status field
    {
        "pattern": r'(?<!\w)Task\([^)]*\bstatus\s*=',
        "message": "Task() constructor: Task has no 'status' field",
        "severity": "warning",
    },
    # result.success as setter (it's a @property, read-only)
    {
        "pattern": r'result\.success\s*=',
        "message": "result.success is a read-only @property, use status= instead",
        "severity": "warning",
    },
]


def scan_known_patterns(search_dir: Path) -> List[Dict]:
    """Scan for known bad patterns in Python files."""
    issues = []

    for py_file in search_dir.rglob("*.py"):
        rel = str(py_file.relative_to(BASE))
        if any(skip in rel for skip in ["__pycache__", ".venv", "maintenance"]):
            continue

        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comments and docstrings
            if stripped.startswith("#"):
                continue

            for bad in KNOWN_BAD_PATTERNS:
                if re.search(bad["pattern"], line):
                    # Skip if it's inside a string literal or comment
                    code_part = line.split("#")[0]  # Remove inline comments
                    if re.search(bad["pattern"], code_part):
                        issues.append({
                            "file": str(py_file.relative_to(BASE)),
                            "line": line_num,
                            "message": bad["message"],
                            "severity": bad["severity"],
                            "code": stripped[:100],
                        })

    return issues


def validate() -> List[Dict]:
    """Validate model field usage across the codebase."""
    all_issues = []

    print("=== Model Field Checker ===")

    task_fields = extract_model_fields("Task")
    result_fields = extract_model_fields("Result")

    print(f"\n  Task fields:   {sorted(task_fields)}")
    print(f"  Result fields: {sorted(result_fields)}")

    src_dir = AG_ACE_BRIDGE / "src"

    # Scan for known bad patterns
    all_issues = scan_known_patterns(src_dir)

    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]

    if all_issues:
        print(f"\n  Issues found: {len(errors)} errors, {len(warnings)} warnings")
        for issue in all_issues:
            tag = issue["severity"].upper()[:4]
            print(f"    [{tag}] {issue['file']}:{issue['line']} - {issue['message']}")
    else:
        print(f"\n  All model field access valid!")

    return errors  # Only errors cause failure; warnings are informational


def main() -> bool:
    issues = validate()
    return len(issues) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
