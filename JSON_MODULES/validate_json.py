#!/usr/bin/env python3
"""JSON Module Validation Script for 25_ACE project.

Validates all JSON module files (agents, models, teams, templates, compact, resolved):
- UTF-8 encoding + JSON parse
- Required fields (provider, component_type, config)
- Provider path validity
- Model reference cross-check
- Team → Agent reference cross-check
- $ref resolution checks (templates_compact/)
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent

KNOWN_PROVIDERS = {
    # Teams
    "autogen_agentchat.teams.RoundRobinGroupChat",
    "autogen_agentchat.teams.SelectorGroupChat",
    "autogen_agentchat.teams.Swarm",
    "autogen_ext.teams.MagenticOneGroupChat",
    # Agents
    "autogen_agentchat.agents.AssistantAgent",
    "autogen_agentchat.agents.UserProxyAgent",
    "autogen_agentchat.agents.CodeExecutorAgent",
    # Models
    "autogen_ext.models.openai.OpenAIChatCompletionClient",
    "autogen_ext.models.openai.AzureOpenAIChatCompletionClient",
    "autogen_ext.models.anthropic.AnthropicChatCompletionClient",
    "AG_Cohub.model_factory.ClaudeCLIChatCompletionClient",
    # Termination
    "autogen_agentchat.conditions.TextMentionTermination",
    "autogen_agentchat.conditions.MaxMessageTermination",
    "autogen_agentchat.conditions.OrTermination",
    "autogen_agentchat.base.OrTerminationCondition",
    # Context
    "autogen_core.model_context.UnboundedChatCompletionContext",
    "autogen_core.model_context.BufferedChatCompletionContext",
    # Workbench
    "autogen_core.tools.StaticStreamWorkbench",
    # A2A
    "autogenstudio.a2a.A2AAgent",
}

REQUIRED_FIELDS = {"provider", "component_type", "config"}

KNOWN_MODELS = {
    "gpt-4o-mini", "gpt-4o", "gpt-4-turbo",
    "claude-sonnet-4-5-20250929", "claude-opus-4-5-20251101",
    "claude-haiku-4-5-20251001", "claude-3-5-sonnet-20241022",
    "mistral:7b-instruct",
}


def collect_json_files(base_dir: Path) -> list[Path]:
    """Collect all .json files recursively."""
    files = []
    for root, _, filenames in os.walk(base_dir):
        for f in filenames:
            if f.endswith(".json"):
                files.append(Path(root) / f)
    return sorted(files)


def validate_file(filepath: Path) -> dict:
    """Validate a single JSON file."""
    result = {
        "file": str(filepath.relative_to(BASE_DIR)),
        "status": "PASS",
        "errors": [],
        "warnings": [],
    }

    # 1. UTF-8 encoding + JSON parse
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except UnicodeDecodeError as e:
        result["status"] = "FAIL"
        result["errors"].append(f"UTF-8 encoding error: {e}")
        return result
    except json.JSONDecodeError as e:
        result["status"] = "FAIL"
        result["errors"].append(f"JSON parse error: {e}")
        return result

    # 2. Check it's a dict
    if not isinstance(data, dict):
        result["status"] = "FAIL"
        result["errors"].append(f"Root is {type(data).__name__}, expected dict")
        return result

    # Skip non-component files (gallery, index, patterns, providers registry, reports)
    # "id" without "provider" = doc/pattern file; "id" with "provider" = API-exported team (validate it)
    if any(k in data for k in ("components", "items", "_README", "_schema", "RoundRobinGroupChat", "patterns", "timestamp", "results")):
        result["warnings"].append("Non-component file (docs/registry) - skipping field checks")
        return result
    if "id" in data and "provider" not in data:
        result["warnings"].append("Non-component file (docs/registry) - skipping field checks")
        return result

    # 3. Required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            result["errors"].append(f"Missing required field: {field}")
            result["status"] = "FAIL"

    # 4. Provider validity
    provider = data.get("provider", "")
    if provider and provider not in KNOWN_PROVIDERS:
        result["warnings"].append(f"Unknown provider: {provider}")

    # 5. Check nested agents for invalid providers
    config = data.get("config", {})
    participants = config.get("participants", [])
    for i, agent in enumerate(participants):
        # Check model references
        agent_config = agent.get("config", {})
        model_client = agent_config.get("model_client", {})
        if model_client:
            model_name = model_client.get("config", {}).get("model", "")
            if model_name and model_name not in KNOWN_MODELS:
                result["warnings"].append(
                    f"Participant[{i}] unknown model: {model_name}"
                )

    # 6. Check model files
    if data.get("component_type") == "model":
        model_name = config.get("model", "")
        if model_name and model_name not in KNOWN_MODELS:
            result["warnings"].append(f"Unknown model: {model_name}")

    # 7. A2A agent-specific validation
    if provider == "autogenstudio.a2a.A2AAgent":
        a2a_url = config.get("a2a_server_url", "")
        if not a2a_url:
            result["errors"].append("A2A agent missing a2a_server_url in config")
            result["status"] = "FAIL"
        timeout = config.get("timeout", 0)
        if timeout is not None and timeout <= 0:
            result["warnings"].append(f"A2A agent timeout={timeout} (should be > 0)")
        # Check port consistency between _source and URL
        source = data.get("_source", {})
        if source and a2a_url:
            source_port = source.get("port")
            url_port_match = re.search(r':(\d+)', a2a_url)
            if source_port and url_port_match:
                url_port = int(url_port_match.group(1))
                if source_port != url_port:
                    result["errors"].append(
                        f"A2A port mismatch: _source.port={source_port} vs URL port={url_port}"
                    )
                    result["status"] = "FAIL"

    # 8. Filename sanity check
    filename = filepath.name
    if any(ord(c) > 0xFFFF for c in filename):
        result["warnings"].append("Filename contains unusual Unicode characters")

    return result


def validate_registry(base_dir: Path) -> list[str]:
    """Validate registry.json: all file paths must exist."""
    warnings = []
    registry_path = base_dir / "registry.json"
    if not registry_path.exists():
        warnings.append("registry.json not found")
        return warnings

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    for section in ("agents", "models", "a2a_agents"):
        entries = registry.get(section, {})
        for rid, entry in entries.items():
            fpath = entry.get("file", "")
            if fpath and not (base_dir / fpath).exists():
                warnings.append(f"registry[{section}][{rid}]: file not found: {fpath}")

    for tid, entry in registry.get("teams", {}).items():
        fpath = entry.get("file", "")
        if fpath and not (base_dir / fpath).exists():
            warnings.append(f"registry[teams][{tid}]: file not found: {fpath}")

    return warnings


def validate_gallery(base_dir: Path) -> list[str]:
    """Validate cohub_gallery.json: agents/models should not be empty."""
    warnings = []
    gallery_path = base_dir / "cohub_gallery.json"
    if not gallery_path.exists():
        warnings.append("cohub_gallery.json not found")
        return warnings

    with open(gallery_path, "r", encoding="utf-8") as f:
        gallery = json.load(f)

    components = gallery.get("components", {})
    if not components.get("agents"):
        warnings.append("gallery agents[] is empty - components not discoverable")
    if not components.get("models"):
        warnings.append("gallery models[] is empty - components not discoverable")

    return warnings


def validate_dry(base_dir: Path) -> list[str]:
    """Check for DRY violations: duplicate model_context blocks in teams."""
    warnings = []

    # Scan team files for repeated model_context blocks
    teams_dir = base_dir / "teams"
    if not teams_dir.exists():
        return warnings

    for tf in sorted(teams_dir.glob("*.json")):
        try:
            with open(tf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        config = data.get("config", {})
        participants = config.get("participants", [])
        if len(participants) < 2:
            continue

        # Collect model_context blocks
        ctx_blocks = []
        for p in participants:
            mc = p.get("config", {}).get("model_context")
            if mc:
                ctx_blocks.append(json.dumps(mc, sort_keys=True))

        if ctx_blocks and len(set(ctx_blocks)) == 1 and len(ctx_blocks) >= 2:
            warnings.append(
                f"{tf.name}: identical model_context repeated {len(ctx_blocks)}x "
                f"(could be team-level default)"
            )

    # Cross-check: inline agents that match agents/ files
    agents_dir = base_dir / "agents"
    if agents_dir.exists():
        agent_names = set()
        for af in agents_dir.glob("*.json"):
            try:
                with open(af, "r", encoding="utf-8") as f:
                    ad = json.load(f)
                name = ad.get("config", {}).get("name", "")
                if name:
                    agent_names.add(name)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

        # Check gallery teams for inline agents that exist in agents/
        gallery_path = base_dir / "cohub_gallery.json"
        if gallery_path.exists():
            with open(gallery_path, "r", encoding="utf-8") as f:
                gallery = json.load(f)
            for i, team in enumerate(gallery.get("components", {}).get("teams", [])):
                label = team.get("label", f"team[{i}]")
                for p in team.get("config", {}).get("participants", []):
                    pname = p.get("config", {}).get("name", "")
                    if pname in agent_names:
                        warnings.append(
                            f"gallery '{label}': inline agent '{pname}' "
                            f"also exists in agents/ (potential DRY violation)"
                        )

    return warnings


def validate_refs(base_dir: Path) -> list[str]:
    """Validate $ref references in templates_compact/ files."""
    warnings = []
    compact_dir = base_dir / "templates_compact"
    if not compact_dir.exists():
        return warnings

    registry_path = base_dir / "registry.json"
    if not registry_path.exists():
        warnings.append("registry.json not found (needed for $ref validation)")
        return warnings

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    for tf in sorted(compact_dir.glob("*.json")):
        try:
            with open(tf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            warnings.append(f"templates_compact/{tf.name}: parse error: {e}")
            continue

        # Check participant $refs
        for i, p in enumerate(data.get("config", {}).get("participants", [])):
            ref = p.get("$ref")
            if ref:
                parts = ref.split("/", 1)
                if len(parts) != 2:
                    warnings.append(f"{tf.name}: participant[{i}] invalid $ref format: {ref}")
                    continue
                category, ref_id = parts
                section = registry.get(category, {})
                if ref_id not in section:
                    warnings.append(f"{tf.name}: participant[{i}] $ref not in registry: {ref}")
                elif "file" in section[ref_id]:
                    fpath = section[ref_id]["file"]
                    if not (base_dir / fpath).exists():
                        warnings.append(f"{tf.name}: participant[{i}] $ref file missing: {fpath}")

        # Check termination $refs (recursive scan)
        _check_term_refs(data.get("config", {}).get("termination_condition", {}),
                         registry, tf.name, warnings)

    # Test-resolve one template if ref_resolver is available
    try:
        from ref_resolver import resolve_file
        test_file = compact_dir / "reflection_team.json"
        if test_file.exists():
            resolved = resolve_file(test_file, base_dir)
            if "config" in resolved and "participants" in resolved["config"]:
                warnings.append(f"[OK] test-resolve reflection_team.json: "
                                f"{len(resolved['config']['participants'])} agents resolved")
    except Exception as e:
        warnings.append(f"test-resolve failed: {e}")

    return warnings


def _check_term_refs(term: dict, registry: dict, filename: str, warnings: list):
    """Recursively check termination $refs."""
    if not isinstance(term, dict):
        return
    ref = term.get("$ref")
    if ref:
        parts = ref.split("/", 1)
        if len(parts) == 2:
            category, ref_id = parts
            if ref_id not in registry.get(category, {}):
                warnings.append(f"{filename}: termination $ref not in registry: {ref}")
    for cond in term.get("config", {}).get("conditions", []):
        _check_term_refs(cond, registry, filename, warnings)


def main():
    print("=" * 60)
    print("  JSON Module Validation - 25_ACE Project")
    print(f"  {datetime.now().isoformat()}")
    print("=" * 60)

    files = collect_json_files(BASE_DIR)
    print(f"\nFound {len(files)} JSON files\n")

    results = []
    pass_count = 0
    fail_count = 0
    warn_count = 0

    for f in files:
        r = validate_file(f)
        results.append(r)

        warn_str = f" ({len(r['warnings'])} warnings)" if r["warnings"] else ""

        if r["status"] == "PASS":
            pass_count += 1
            print(f"  [PASS] {r['file']}{warn_str}")
        else:
            fail_count += 1
            print(f"  [FAIL] {r['file']}")
            for err in r["errors"]:
                print(f"         ERROR: {err}")

        if r["warnings"]:
            warn_count += len(r["warnings"])
            for w in r["warnings"]:
                print(f"         WARN: {w}")

    # Cross-module validation
    print(f"\n--- Cross-Module Checks ---")

    registry_warns = validate_registry(BASE_DIR)
    gallery_warns = validate_gallery(BASE_DIR)
    dry_warns = validate_dry(BASE_DIR)
    ref_warns = validate_refs(BASE_DIR)

    cross_warns = registry_warns + gallery_warns + dry_warns + ref_warns
    if cross_warns:
        for w in cross_warns:
            print(f"  WARN: {w}")
        warn_count += len(cross_warns)
    else:
        print("  All cross-module checks passed")

    print(f"\n{'=' * 60}")
    print(f"  Results: {pass_count} PASS, {fail_count} FAIL, {warn_count} warnings")
    print(f"  Total files: {len(results)}")
    print(f"{'=' * 60}")

    # Write report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(results),
        "pass": pass_count,
        "fail": fail_count,
        "warnings": warn_count,
        "cross_module": {
            "registry": registry_warns,
            "gallery": gallery_warns,
            "dry_violations": dry_warns,
            "ref_checks": ref_warns,
        },
        "results": results,
    }

    report_path = BASE_DIR / "validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nReport saved to: {report_path}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
