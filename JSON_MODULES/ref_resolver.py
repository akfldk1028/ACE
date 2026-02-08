#!/usr/bin/env python3
"""$ref Resolver for JSON_MODULES compact templates.

Resolves $ref references in compact team templates to produce fully-inline
JSON compatible with AutoGen Studio. Enables DRY composition:
  - agents/$ref → load agent file, wrap in AssistantAgent envelope, apply defaults + overrides
  - terminations/$ref → resolve from registry, recurse nested conditions
  - _defaults → injected into every participant unless overridden

Usage:
    python ref_resolver.py <file.json>              # resolve single file, print to stdout
    python ref_resolver.py --all                    # resolve all templates_compact/ → resolved/
    python ref_resolver.py --import                 # resolve + POST to AutoGen Studio
    python ref_resolver.py --diff <file.json>       # resolve and diff against templates/ version
"""

import argparse
import copy
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Core utilities
# ---------------------------------------------------------------------------

def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override wins for leaf values."""
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


def apply_dot_path(target: dict, dot_path: str, value) -> dict:
    """Set a value at a dot-separated path inside target dict.

    Example: apply_dot_path(d, "model_client.config.agent_config", {...})
    creates/overwrites d["model_client"]["config"]["agent_config"].
    """
    result = copy.deepcopy(target)
    keys = dot_path.split(".")
    current = result
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    # Final key: deep-merge if both are dicts, else overwrite
    final_key = keys[-1]
    if final_key in current and isinstance(current[final_key], dict) and isinstance(value, dict):
        current[final_key] = deep_merge(current[final_key], value)
    else:
        current[final_key] = copy.deepcopy(value)
    return result


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_registry_cache: dict[str, dict] = {}

def load_registry(base_dir: Path = BASE_DIR) -> dict:
    """Load and cache registry.json (cached per base_dir)."""
    cache_key = str(base_dir.resolve())
    if cache_key in _registry_cache:
        return _registry_cache[cache_key]
    registry_path = base_dir / "registry.json"
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _registry_cache[cache_key] = data
    return data


def resolve_ref(ref_str: str, registry: dict, base_dir: Path = BASE_DIR) -> dict:
    """Resolve a $ref string like "agents/auto_claude_planner" → loaded JSON.

    Format: "<category>/<id>" where category is agents, models, or terminations.
    """
    parts = ref_str.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid $ref format: {ref_str!r} (expected 'category/id')")
    category, ref_id = parts

    section = registry.get(category, {})
    if ref_id not in section:
        raise KeyError(f"$ref not found: registry[{category}][{ref_id}]")

    entry = section[ref_id]

    # Agents and models have file references
    if "file" in entry:
        file_path = base_dir / entry["file"]
        if not file_path.exists():
            raise FileNotFoundError(f"$ref file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Terminations are inline in registry
    return copy.deepcopy(entry)


# ---------------------------------------------------------------------------
# Defaults resolution (model $ref support)
# ---------------------------------------------------------------------------

def resolve_defaults(defaults: dict, registry: dict, base_dir: Path = BASE_DIR) -> dict:
    """Resolve $ref entries within _defaults dict.

    Supports model_client and other values being $ref dicts:
        "model_client": {"$ref": "models/claude_sonnet", "override": {"config.agent_config": {...}}}

    Returns a new defaults dict with all $ref entries resolved to full inline JSON.
    """
    result = copy.deepcopy(defaults)
    for key, val in result.items():
        if isinstance(val, dict) and "$ref" in val:
            ref_str = val["$ref"]
            overrides = val.get("override", {})
            resolved = resolve_ref(ref_str, registry, base_dir)
            # Apply overrides (flat + dot-path)
            for okey, oval in overrides.items():
                if "." in okey:
                    resolved = apply_dot_path(resolved, okey, oval)
                else:
                    resolved[okey] = copy.deepcopy(oval)
            result[key] = resolved
    return result


# ---------------------------------------------------------------------------
# Agent resolution
# ---------------------------------------------------------------------------

def resolve_agent(participant: dict, defaults: dict, registry: dict, base_dir: Path = BASE_DIR) -> dict:
    """Resolve a single participant entry into a fully-inline agent dict.

    Resolution order for standard agents (later wins):
      1. agent file (from $ref) or inline definition
      2. _defaults (only fills missing keys)
      3. override flat keys (description, system_message)
      4. override dot-paths (model_client.config.agent_config)

    A2A agents (a2a_agents/ refs) are self-contained:
      - No _defaults injection (they don't use model_client, etc.)
      - _source metadata stripped (not for AutoGen Studio)
      - Only flat overrides applied to config (timeout, description, etc.)
    """
    overrides = participant.get("override", {})

    if "$ref" in participant:
        ref_str = participant["$ref"]
        category = ref_str.split("/", 1)[0]
        agent_data = resolve_ref(ref_str, registry, base_dir)

        # A2A agents: self-contained, no _defaults wrapping
        if category == "a2a_agents":
            result = copy.deepcopy(agent_data)
            result.pop("_source", None)  # Strip source metadata
            # Apply flat overrides to config
            for key, val in overrides.items():
                if "." not in key:
                    result.setdefault("config", {})[key] = copy.deepcopy(val)
            return result
    else:
        agent_data = {k: v for k, v in participant.items() if k != "override"}

    # 1. Start with agent file's config
    agent_config = copy.deepcopy(agent_data.get("config", {}))

    # 2. Fill missing keys from _defaults
    for key, val in defaults.items():
        if key not in agent_config:
            agent_config[key] = copy.deepcopy(val)

    # 3. Separate dot-path overrides from flat overrides
    flat_overrides = {}
    dot_overrides = {}
    for key, val in overrides.items():
        if "." in key:
            dot_overrides[key] = val
        else:
            flat_overrides[key] = val

    # Apply flat overrides (description, system_message, etc.)
    for key, val in flat_overrides.items():
        agent_config[key] = copy.deepcopy(val)

    # 4. Apply dot-path overrides
    for dot_path, val in dot_overrides.items():
        agent_config = apply_dot_path(agent_config, dot_path, val)

    # Ensure description is in config (from override > agent_config > agent_data.description)
    if "description" not in agent_config:
        desc = agent_data.get("description", "")
        if desc:
            agent_config["description"] = desc

    return {
        "provider": agent_data.get("provider", "autogen_agentchat.agents.AssistantAgent"),
        "component_type": "agent",
        "config": agent_config,
    }


# ---------------------------------------------------------------------------
# Termination resolution
# ---------------------------------------------------------------------------

def resolve_termination(term_config: dict, registry: dict, base_dir: Path = BASE_DIR,
                        _seen: set | None = None) -> dict:
    """Resolve a termination_condition entry.

    Supports:
      - {"$ref": "terminations/default_or"} → look up in registry
      - Inline termination dicts (pass through)
      - Nested "conditions" arrays (resolve each recursively)
    """
    if _seen is None:
        _seen = set()

    if "$ref" in term_config:
        ref_key = term_config["$ref"]
        if ref_key in _seen:
            raise ValueError(f"Cycle detected in termination refs: {ref_key}")
        _seen.add(ref_key)
        entry = resolve_ref(term_config["$ref"], registry, base_dir)
    else:
        entry = copy.deepcopy(term_config)

    # If it's an Or condition with string condition IDs, resolve them
    if "conditions" in entry and not isinstance(entry.get("config"), dict):
        # Registry-style: { provider, conditions: ["terminate_text", "max_10"] }
        provider = entry["provider"]
        condition_ids = entry["conditions"]
        resolved_conditions = []
        for cid in condition_ids:
            if isinstance(cid, str):
                # Look up in registry.terminations
                term_entry = registry.get("terminations", {}).get(cid)
                if term_entry is None:
                    raise KeyError(f"Termination condition not found: {cid}")
                resolved_conditions.append(resolve_termination(term_entry, registry, base_dir, _seen))
            elif isinstance(cid, dict):
                resolved_conditions.append(resolve_termination(cid, registry, base_dir, _seen))
            else:
                raise ValueError(f"Invalid condition entry: {cid!r}")
        return {
            "provider": provider,
            "component_type": "termination",
            "config": {
                "conditions": resolved_conditions
            }
        }

    # Already a fully-resolved termination with config.conditions
    if "config" in entry and "conditions" in entry.get("config", {}):
        resolved_conditions = []
        for cond in entry["config"]["conditions"]:
            resolved_conditions.append(resolve_termination(cond, registry, base_dir, _seen))
        return {
            "provider": entry["provider"],
            "component_type": "termination",
            "config": {
                "conditions": resolved_conditions
            }
        }

    # Leaf termination (TextMention, MaxMessage, etc.)
    return {
        "provider": entry["provider"],
        "component_type": "termination",
        "config": entry.get("config", {})
    }


# ---------------------------------------------------------------------------
# Team resolution (top-level entry point)
# ---------------------------------------------------------------------------

def resolve_team(compact_json: dict, base_dir: Path = BASE_DIR) -> dict:
    """Resolve a compact team template into a fully-inline AutoGen Studio JSON.

    Args:
        compact_json: The compact team template with $ref entries
        base_dir: Base directory for resolving file paths (default: JSON_MODULES/)

    Returns:
        Fully resolved team JSON compatible with AutoGen Studio
    """
    registry = load_registry(base_dir)
    data = copy.deepcopy(compact_json)
    defaults = data.pop("_defaults", {})
    defaults = resolve_defaults(defaults, registry, base_dir)
    config = data.get("config", {})

    # Resolve participants
    resolved_participants = []
    for participant in config.get("participants", []):
        resolved = resolve_agent(participant, defaults, registry, base_dir)
        resolved_participants.append(resolved)
    config["participants"] = resolved_participants

    # Resolve team-level model_client $ref (e.g. SelectorGroupChat's selector LLM)
    if "model_client" in config and isinstance(config["model_client"], dict) and "$ref" in config["model_client"]:
        ref_entry = config["model_client"]
        resolved_mc = resolve_ref(ref_entry["$ref"], registry, base_dir)
        for okey, oval in ref_entry.get("override", {}).items():
            if "." in okey:
                resolved_mc = apply_dot_path(resolved_mc, okey, oval)
            else:
                resolved_mc[okey] = copy.deepcopy(oval)
        config["model_client"] = resolved_mc

    # Resolve termination_condition
    if "termination_condition" in config:
        config["termination_condition"] = resolve_termination(
            config["termination_condition"], registry, base_dir
        )

    return data


def resolve_file(filepath: Path, base_dir: Path = BASE_DIR) -> dict:
    """Load and resolve a compact template file."""
    with open(filepath, "r", encoding="utf-8") as f:
        compact = json.load(f)
    return resolve_team(compact, base_dir)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="$ref Resolver - Resolve compact team templates to full inline JSON"
    )
    parser.add_argument("file", nargs="?", help="Compact template file to resolve")
    parser.add_argument("--all", action="store_true",
                        help="Resolve all templates_compact/ → resolved/")
    parser.add_argument("--import", dest="do_import", action="store_true",
                        help="Resolve + POST to AutoGen Studio API")
    parser.add_argument("--diff", action="store_true",
                        help="Resolve and show structural diff against templates/ version")
    parser.add_argument("--base-dir", type=str, default=str(BASE_DIR),
                        help="Base directory for JSON_MODULES")
    parser.add_argument("--output", "-o", type=str,
                        help="Output file (default: stdout)")

    args = parser.parse_args()
    base_dir = Path(args.base_dir)

    # Clear cache for fresh run
    global _registry_cache
    _registry_cache = {}

    if args.all:
        compact_dir = base_dir / "templates_compact"
        resolved_dir = base_dir / "resolved"
        resolved_dir.mkdir(exist_ok=True)

        if not compact_dir.exists():
            print(f"Error: {compact_dir} not found", file=sys.stderr)
            return 1

        count = 0
        for f in sorted(compact_dir.glob("*.json")):
            try:
                resolved = resolve_file(f, base_dir)
                out_path = resolved_dir / f.name
                with open(out_path, "w", encoding="utf-8") as fp:
                    json.dump(resolved, fp, indent=2, ensure_ascii=False)
                print(f"  [OK] {f.name} -> resolved/{f.name}")
                count += 1
            except Exception as e:
                print(f"  [FAIL] {f.name}: {e}", file=sys.stderr)

        print(f"\nResolved {count} templates -> {resolved_dir}")
        return 0

    if args.do_import:
        import requests
        api_base = os.environ.get("AUTOGEN_STUDIO_API", "http://localhost:8081/api")
        compact_dir = base_dir / "templates_compact"

        for f in sorted(compact_dir.glob("*.json")):
            try:
                resolved = resolve_file(f, base_dir)
                resp = requests.post(
                    f"{api_base}/teams/",
                    json={"user_id": "guestuser@gmail.com", "component": resolved}
                )
                if resp.status_code == 200:
                    result = resp.json()
                    team_id = result.get("id", "?")
                    print(f"  [OK] {f.name} -> team id={team_id}")
                else:
                    print(f"  [FAIL] {f.name}: {resp.status_code} {resp.text[:200]}")
            except requests.exceptions.ConnectionError:
                print(f"Cannot connect to AutoGen Studio at {api_base}")
                return 1
            except Exception as e:
                print(f"  [FAIL] {f.name}: {e}")

        return 0

    if args.file:
        filepath = Path(args.file)
        if not filepath.is_absolute():
            filepath = base_dir / filepath
        if not filepath.exists():
            # Try templates_compact/
            alt = base_dir / "templates_compact" / filepath.name
            if alt.exists():
                filepath = alt
            else:
                print(f"Error: {filepath} not found", file=sys.stderr)
                return 1

        resolved = resolve_file(filepath, base_dir)

        if args.diff:
            # Compare against templates/ version
            templates_version = base_dir / "templates" / filepath.name
            if templates_version.exists():
                with open(templates_version, "r", encoding="utf-8") as f:
                    expected = json.load(f)
                _print_structural_diff(expected, resolved)
            else:
                print(f"No templates/ version found for diff: {templates_version}")
                print(json.dumps(resolved, indent=2, ensure_ascii=False))
        else:
            output = json.dumps(resolved, indent=2, ensure_ascii=False)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output)
                print(f"Written to {args.output}")
            else:
                print(output)
        return 0

    parser.print_help()
    return 1


def _print_structural_diff(expected: dict, actual: dict, path: str = ""):
    """Print structural differences between two dicts."""
    if type(expected) != type(actual):
        print(f"  TYPE MISMATCH at {path or 'root'}: {type(expected).__name__} vs {type(actual).__name__}")
        return

    if isinstance(expected, dict):
        all_keys = set(expected.keys()) | set(actual.keys())
        for key in sorted(all_keys):
            key_path = f"{path}.{key}" if path else key
            if key not in expected:
                print(f"  + {key_path} (extra in resolved)")
            elif key not in actual:
                print(f"  - {key_path} (missing in resolved)")
            else:
                _print_structural_diff(expected[key], actual[key], key_path)
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            print(f"  LENGTH DIFF at {path}: {len(expected)} vs {len(actual)}")
        for i in range(min(len(expected), len(actual))):
            _print_structural_diff(expected[i], actual[i], f"{path}[{i}]")
    else:
        if expected != actual:
            print(f"  DIFF at {path}: {expected!r} -> {actual!r}")


if __name__ == "__main__":
    sys.exit(main())
