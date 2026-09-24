#!/usr/bin/env python3
"""Comprehensive E2E Playwright Test for JSON_MODULES + A2A Integration.

Records DETAILED LOGS of every agent interaction:
  - Full conversation transcript per team run
  - Token usage (input/output per agent turn)
  - Duration per agent turn
  - Final result + file creation verification

Usage:
    python e2e_playwright_test.py
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# --- Configuration ---
AUTOGEN_URL = os.environ.get("AUTOGEN_STUDIO_URL", "http://localhost:8081")
AUTOGEN_API = os.environ.get("AUTOGEN_STUDIO_API", f"{AUTOGEN_URL}/api")
USER_ID = "guestuser@gmail.com"
AC247_DIR = os.environ.get("AC247_DIR", "D:\\AC247")
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "e2e_logs"
SCREENSHOT_DIR = BASE_DIR / "test_screenshots"

# Team name -> label mapping for dynamic lookup
TEAM_LABELS = {
    "hybrid_calculator": "Hybrid Calculator Team",
    "auto_claude_dev":   "Auto-Claude Dev Team",
    "debate":            "Debate Team",
    "reflection":        "Reflection Team",
    "sequential":        "Sequential Team",
}

# Resolved at runtime by lookup_team_ids()
TEAMS: dict[str, int] = {}

# --- Results + logs ---
results: list[dict] = []
all_logs: dict[str, list] = {}


async def lookup_team_ids():
    """Dynamically look up team IDs from AutoGen Studio API by label match."""
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{AUTOGEN_API}/teams/", params={"user_id": USER_ID})
        data = resp.json()
        teams_list = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(teams_list, dict):
            teams_list = teams_list.get("teams", [])

    # Build label -> id map from API
    api_map = {}
    for t in teams_list:
        if isinstance(t, dict):
            tid = t.get("id")
            label = t.get("component", {}).get("label", "") or t.get("label", "")
            if tid and label:
                api_map[label] = tid

    # Match our team keys to API labels
    for key, expected_label in TEAM_LABELS.items():
        if expected_label in api_map:
            TEAMS[key] = api_map[expected_label]
        else:
            # Fuzzy match: check if label contains the key
            for api_label, tid in api_map.items():
                if key.replace("_", " ") in api_label.lower() or expected_label.lower() in api_label.lower():
                    TEAMS[key] = tid
                    break

    found = len(TEAMS)
    total = len(TEAM_LABELS)
    if found < total:
        missing = [k for k in TEAM_LABELS if k not in TEAMS]
        print(f"  [WARN] {found}/{total} teams found. Missing: {missing}")
    else:
        print(f"  [OK] All {found} teams resolved: { {k: v for k, v in TEAMS.items()} }")
    return found


def record(name, status, detail="", duration=0):
    results.append({
        "test": name,
        "status": status,
        "detail": detail,
        "duration_s": round(duration, 1),
    })
    icon = "PASS" if status == "PASS" else "FAIL"
    dur = f" ({duration:.1f}s)" if duration else ""
    print(f"  [{icon}] {name}{dur}: {detail}")


def log_entry(team_name, entry):
    """Append a log entry for a team run."""
    all_logs.setdefault(team_name, []).append(entry)


# --- Helper: Run team via API + WebSocket with FULL LOGGING ---
async def run_team_ws(team_id: int, task: str, team_name: str, timeout_s: int = 180) -> dict:
    """Submit a task, monitor via WebSocket, return result with full conversation log."""
    import httpx
    import websockets

    run_log = []
    run_log.append({"event": "task_submitted", "task": task, "team_id": team_id, "time": datetime.now().isoformat()})

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Create session
        resp = await client.post(f"{AUTOGEN_API}/sessions/", json={
            "user_id": USER_ID,
            "team_id": team_id,
        })
        session = resp.json()
        session_id = session.get("data", {}).get("id") or session.get("id")
        if not session_id:
            run_log.append({"event": "error", "detail": f"session creation failed: {resp.text[:300]}"})
            all_logs[team_name] = run_log
            return {"error": f"Failed to create session: {resp.text[:200]}", "log": run_log}

        # 2. Create run
        resp = await client.post(f"{AUTOGEN_API}/runs/", json={
            "user_id": USER_ID,
            "session_id": session_id,
        })
        run_data = resp.json()
        run_id = (run_data.get("data", {}).get("run_id")
                  or run_data.get("data", {}).get("id")
                  or run_data.get("run_id")
                  or run_data.get("id"))
        if not run_id:
            run_log.append({"event": "error", "detail": f"run creation failed: {resp.text[:300]}"})
            all_logs[team_name] = run_log
            return {"error": f"Failed to create run: {resp.text[:200]}", "log": run_log}

    run_log.append({"event": "run_created", "run_id": str(run_id), "session_id": str(session_id)})

    # 3. Get team config
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{AUTOGEN_API}/teams/{team_id}", params={"user_id": USER_ID})
        team_data = resp.json()
        team_config = team_data.get("data", team_data)
        if isinstance(team_config, dict) and "component" in team_config:
            team_config = team_config["component"]

    # 4. WebSocket execution with full message capture
    ws_base = AUTOGEN_URL.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_base}/api/ws/runs/{run_id}"
    final_result = {"run_id": str(run_id), "session_id": str(session_id)}
    conversation = []  # Full conversation log
    agent_stats = {}   # agent_name -> {turns, total_chars, total_tokens_approx}
    turn_number = 0

    try:
        async with websockets.connect(ws_url) as ws:
            start_msg = {
                "type": "start",
                "task": task,
                "team_config": team_config,
            }
            await ws.send(json.dumps(start_msg))
            run_log.append({"event": "ws_start_sent", "time": datetime.now().isoformat()})

            start_time = time.time()
            while time.time() - start_time < timeout_s:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=10)
                    msg = json.loads(raw)
                    msg_type = msg.get("type", "")
                    elapsed = round(time.time() - start_time, 1)

                    if msg_type == "message":
                        turn_number += 1
                        data = msg.get("data", {})
                        source = data.get("source", "unknown")
                        content = str(data.get("content", ""))
                        models_usage = data.get("models_usage", {}) or {}

                        # Token tracking
                        prompt_tokens = 0
                        completion_tokens = 0
                        if models_usage:
                            for model_key, usage in models_usage.items():
                                if isinstance(usage, dict):
                                    prompt_tokens += usage.get("prompt_tokens", 0)
                                    completion_tokens += usage.get("completion_tokens", 0)

                        # Agent stats
                        if source not in agent_stats:
                            agent_stats[source] = {"turns": 0, "total_chars": 0, "prompt_tokens": 0, "completion_tokens": 0}
                        agent_stats[source]["turns"] += 1
                        agent_stats[source]["total_chars"] += len(content)
                        agent_stats[source]["prompt_tokens"] += prompt_tokens
                        agent_stats[source]["completion_tokens"] += completion_tokens

                        # Truncate content for log (first 500 chars)
                        content_preview = content[:500] + ("..." if len(content) > 500 else "")

                        turn_entry = {
                            "turn": turn_number,
                            "agent": source,
                            "content_length": len(content),
                            "content_preview": content_preview,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "elapsed_s": elapsed,
                        }
                        conversation.append(turn_entry)
                        run_log.append({"event": "agent_message", **turn_entry})

                        # Live progress
                        tok_info = f"in={prompt_tokens},out={completion_tokens}" if prompt_tokens else ""
                        print(f"    Turn {turn_number}: {source} ({len(content)} chars{', ' + tok_info if tok_info else ''}) [{elapsed}s]")

                        final_result.setdefault("agents", [])
                        if source not in final_result["agents"]:
                            final_result["agents"].append(source)

                    elif msg_type in ("result", "completion"):
                        final_result["status"] = "completed"
                        # Extract final text from result
                        result_data = msg.get("data", {})
                        if isinstance(result_data, dict):
                            task_result = result_data.get("task_result", {})
                            if isinstance(task_result, dict):
                                final_msgs = task_result.get("messages", [])
                                if final_msgs:
                                    final_result["final_message_source"] = final_msgs[-1].get("source", "?")
                                    final_content = str(final_msgs[-1].get("content", ""))
                                    final_result["final_message_preview"] = final_content[:300]
                                stop_reason = task_result.get("stop_reason", "?")
                                final_result["stop_reason"] = stop_reason
                                run_log.append({"event": "completed", "stop_reason": stop_reason, "elapsed_s": elapsed})
                        break

                    elif msg_type == "error":
                        final_result["status"] = "error"
                        error_data = msg.get("data", str(msg))
                        final_result["error"] = str(error_data)[:500]
                        run_log.append({"event": "error", "detail": str(error_data)[:500], "elapsed_s": elapsed})
                        break

                except asyncio.TimeoutError:
                    continue
                except websockets.ConnectionClosed:
                    run_log.append({"event": "ws_closed", "elapsed_s": round(time.time() - start_time, 1)})
                    break

            total_elapsed = time.time() - start_time
            final_result["elapsed_s"] = round(total_elapsed, 1)
            final_result["turn_count"] = turn_number
            final_result["conversation"] = conversation
            final_result["agent_stats"] = agent_stats

            if "status" not in final_result:
                final_result["status"] = "timeout"
                run_log.append({"event": "timeout", "elapsed_s": round(total_elapsed, 1)})

    except Exception as e:
        final_result["error"] = str(e)
        final_result["status"] = "error"
        run_log.append({"event": "exception", "detail": str(e)[:300]})

    all_logs[team_name] = run_log
    return final_result


# --- Test functions ---

async def test_a2a_calculator_health():
    start = time.time()
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("http://localhost:8006/.well-known/agent.json")
            data = resp.json()
            name = data.get("name", "?")
            skills = [s.get("name", "?") for s in data.get("skills", [])]
            dur = time.time() - start
            record("A2A Calculator Health", "PASS", f"{name}: skills={skills}", dur)
    except Exception as e:
        record("A2A Calculator Health", "FAIL", str(e)[:150], time.time() - start)


async def test_ref_resolver():
    start = time.time()
    try:
        r = subprocess.run(
            [sys.executable, str(BASE_DIR / "ref_resolver.py"), "--all"],
            capture_output=True, timeout=30, cwd=str(BASE_DIR),
        )
        r.stdout = r.stdout.decode("utf-8", errors="replace")
        r.stderr = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""
        ok_count = r.stdout.count("[OK]")
        fail_count = r.stdout.count("[FAIL]")
        dur = time.time() - start
        if fail_count == 0 and ok_count > 0:
            record("ref_resolver --all", "PASS", f"{ok_count} resolved, 0 failed", dur)
        else:
            record("ref_resolver --all", "FAIL", f"{ok_count} OK, {fail_count} FAIL", dur)
    except Exception as e:
        record("ref_resolver --all", "FAIL", str(e)[:150], time.time() - start)


async def test_validate_json():
    start = time.time()
    try:
        r = subprocess.run(
            [sys.executable, str(BASE_DIR / "validate_json.py")],
            capture_output=True, timeout=30, cwd=str(BASE_DIR),
        )
        stdout = r.stdout.decode("utf-8", errors="replace") if isinstance(r.stdout, bytes) else r.stdout
        m = re.search(r'(\d+) PASS, (\d+) FAIL', stdout)
        dur = time.time() - start
        if m:
            passes, fails = int(m.group(1)), int(m.group(2))
            record("validate_json.py", "PASS" if fails == 0 else "FAIL", f"{passes} PASS, {fails} FAIL", dur)
        else:
            record("validate_json.py", "FAIL", "Could not parse output", dur)
    except Exception as e:
        record("validate_json.py", "FAIL", str(e)[:150], time.time() - start)


async def test_a2a_manager_list():
    start = time.time()
    try:
        r = subprocess.run(
            [sys.executable, str(BASE_DIR / "a2a_manager.py"), "--list"],
            capture_output=True, timeout=15, cwd=str(BASE_DIR),
        )
        stdout = r.stdout.decode("utf-8", errors="replace") if isinstance(r.stdout, bytes) else r.stdout
        m = re.search(r'Total: (\d+) agents', stdout)
        dur = time.time() - start
        if m:
            record("a2a_manager --list", "PASS", f"{m.group(1)} agents listed", dur)
        else:
            record("a2a_manager --list", "FAIL", f"Unexpected: {stdout[:100]}", dur)
    except Exception as e:
        record("a2a_manager --list", "FAIL", str(e)[:150], time.time() - start)


async def test_playwright_ui():
    """Test AutoGen Studio UI loads + take screenshots."""
    start = time.time()
    try:
        from playwright.async_api import async_playwright

        SCREENSHOT_DIR.mkdir(exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1400, "height": 900})

            # Main page
            await page.goto(AUTOGEN_URL, timeout=15000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)
            await page.screenshot(path=str(SCREENSHOT_DIR / "01_main_page.png"), full_page=True)

            title = await page.title()
            body = await page.inner_text("body")

            # Navigate to build/teams
            await page.goto(f"{AUTOGEN_URL}/#/build", timeout=15000)
            await page.wait_for_load_state("networkidle", timeout=10000)
            await asyncio.sleep(2)
            await page.screenshot(path=str(SCREENSHOT_DIR / "02_build_page.png"), full_page=True)

            await browser.close()

            dur = time.time() - start
            has_content = len(body) > 100
            record("Playwright UI + Screenshots", "PASS" if has_content else "FAIL",
                   f"Title={title}, body={len(body)} chars, screenshots saved", dur)

    except Exception as e:
        record("Playwright UI + Screenshots", "FAIL", str(e)[:150], time.time() - start)


async def run_team_test(team_key: str, display_name: str, task: str,
                       timeout_s: int = 180, post_check=None):
    """Generic team test runner. Eliminates duplication across test functions.

    Args:
        team_key: Key in TEAMS dict (e.g. "debate")
        display_name: Human-readable name for test record
        task: The task prompt to send
        timeout_s: WebSocket timeout
        post_check: Optional callable(result) -> str for extra detail (e.g. file check)
    """
    if team_key not in TEAMS:
        record(display_name, "FAIL", f"Team '{team_key}' not found in API", 0)
        return

    start = time.time()
    print(f"\n  >> Running {display_name}...")
    result = await run_team_ws(TEAMS[team_key], task, team_key, timeout_s=timeout_s)

    dur = result.get("elapsed_s", time.time() - start)
    status = result.get("status", "unknown")
    agents = result.get("agents", [])
    turns = result.get("turn_count", 0)
    stats = result.get("agent_stats", {})

    stats_str = "; ".join(
        f"{a}: {s['turns']}t/{s['total_chars']}c/in={s['prompt_tokens']}/out={s['completion_tokens']}"
        for a, s in stats.items()
    )
    detail = f"{turns} turns, agents={agents}, [{stats_str}]"

    if post_check:
        extra = post_check(result)
        if extra:
            detail = extra + f" [{stats_str}]"

    if status == "completed":
        record(display_name, "PASS", detail, dur)
    else:
        record(display_name, "FAIL", f"{status}: {result.get('error', '?')[:150]}", dur)


async def test_hybrid_team():
    await run_team_test(
        "hybrid_calculator", "Hybrid Team (Claude+A2A)",
        "100의 팩토리얼을 계산하고, 피보나치 수열의 10번째 수도 알려주세요.",
        timeout_s=300,
    )


async def test_debate():
    await run_team_test(
        "debate", "Debate Team",
        "AI가 인간의 창의성을 대체할 수 있는가?",
        timeout_s=180,
    )


async def test_reflection():
    await run_team_test(
        "reflection", "Reflection Team",
        "Python으로 이진 탐색 알고리즘을 설명하고 구현하세요.",
        timeout_s=180,
    )


async def test_code_generation():
    """Code generation with post-check for file creation + execution."""
    test_file = Path(AC247_DIR) / "e2e_test_calc.py"
    if test_file.exists():
        test_file.unlink()

    def check_file(result):
        file_exists = test_file.exists()
        file_size = test_file.stat().st_size if file_exists else 0
        run_output = ""
        if file_exists and file_size > 10:
            try:
                r = subprocess.run(
                    [sys.executable, str(test_file)],
                    capture_output=True, timeout=10,
                )
                run_output = r.stdout.decode("utf-8", errors="replace").strip()
            except Exception:
                pass
        turns = result.get("turn_count", 0)
        agents = result.get("agents", [])
        detail = f"{turns} turns, file={'YES' if file_exists else 'NO'}({file_size}B), agents={agents}"
        if run_output:
            detail += f", output='{run_output[:100]}'"
        return detail

    await run_team_test(
        "auto_claude_dev", "Code Generation (Dev Team)",
        f"{AC247_DIR} 폴더에 e2e_test_calc.py 파일을 만들어주세요. 간단한 사칙연산 함수(add, sub, mul, div)를 구현하고, if __name__=='__main__' 에서 2+3=5, 10*5=50, 100/4=25.0 을 출력하세요.",
        timeout_s=300,
        post_check=check_file,
    )


# --- Save detailed log file ---
def save_detailed_log():
    """Save the full conversation log as a readable text file."""
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"e2e_run_{timestamp}.md"

    lines = []
    lines.append(f"# E2E Test Run - {datetime.now().isoformat()}")
    lines.append(f"")
    lines.append(f"## Summary")
    lines.append(f"")
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    total_dur = sum(r["duration_s"] for r in results)
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Tests | {len(results)} |")
    lines.append(f"| PASS | {pass_count} |")
    lines.append(f"| FAIL | {fail_count} |")
    lines.append(f"| Total Duration | {total_dur:.1f}s |")
    lines.append(f"")

    lines.append(f"## Test Results")
    lines.append(f"")
    lines.append(f"| # | Test | Status | Duration | Detail |")
    lines.append(f"|---|------|--------|----------|--------|")
    for i, r in enumerate(results, 1):
        lines.append(f"| {i} | {r['test']} | {r['status']} | {r['duration_s']}s | {r['detail'][:80]} |")
    lines.append(f"")

    # Detailed conversation logs for each team run
    for team_name, log_entries in all_logs.items():
        lines.append(f"---")
        lines.append(f"## Conversation Log: {team_name}")
        lines.append(f"")

        for entry in log_entries:
            event = entry.get("event", "?")
            if event == "task_submitted":
                lines.append(f"**Task**: {entry.get('task', '?')}")
                lines.append(f"**Team ID**: {entry.get('team_id', '?')}")
                lines.append(f"**Time**: {entry.get('time', '?')}")
                lines.append(f"")
            elif event == "run_created":
                lines.append(f"**Run ID**: {entry.get('run_id', '?')}")
                lines.append(f"**Session ID**: {entry.get('session_id', '?')}")
                lines.append(f"")
            elif event == "agent_message":
                turn = entry.get("turn", "?")
                agent = entry.get("agent", "?")
                chars = entry.get("content_length", 0)
                in_tok = entry.get("prompt_tokens", 0)
                out_tok = entry.get("completion_tokens", 0)
                elapsed = entry.get("elapsed_s", 0)
                preview = entry.get("content_preview", "")

                lines.append(f"### Turn {turn}: `{agent}` [{elapsed}s]")
                lines.append(f"- Content: {chars} chars | Tokens: in={in_tok}, out={out_tok}")
                lines.append(f"")
                lines.append(f"```")
                lines.append(preview)
                lines.append(f"```")
                lines.append(f"")
            elif event == "completed":
                lines.append(f"**Completed**: stop_reason={entry.get('stop_reason','?')}, elapsed={entry.get('elapsed_s',0)}s")
                lines.append(f"")
            elif event == "error":
                lines.append(f"**ERROR**: {entry.get('detail', '?')}")
                lines.append(f"")

    content = "\n".join(lines)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nDetailed log saved: {log_path}")

    # Also save as JSON for programmatic access
    json_path = LOG_DIR / f"e2e_run_{timestamp}.json"
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "pass": pass_count,
            "fail": fail_count,
            "total_duration_s": round(total_dur, 1),
        },
        "results": results,
        "conversation_logs": all_logs,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"JSON report saved: {json_path}")

    return log_path


# --- Main ---
async def main():
    print("=" * 70)
    print("  JSON_MODULES + A2A Integration - Comprehensive E2E Test")
    print(f"  {datetime.now().isoformat()}")
    print(f"  AutoGen Studio: {AUTOGEN_URL}")
    print(f"  A2A Calculator: http://localhost:8006")
    print("=" * 70)
    print()

    # Phase 1: Quick checks (parallel)
    print("--- Phase 1: Infrastructure Checks ---")
    await asyncio.gather(
        test_a2a_calculator_health(),
        test_ref_resolver(),
        test_validate_json(),
        test_a2a_manager_list(),
    )
    print()

    # Phase 2: Playwright UI tests
    print("--- Phase 2: Playwright UI Tests ---")
    await test_playwright_ui()
    print()

    # Phase 2.5: Resolve team IDs dynamically
    print("--- Resolving Team IDs ---")
    found = await lookup_team_ids()
    if found == 0:
        record("Team ID Lookup", "FAIL", "No teams found via API", 0)
        # Save what we have and exit
        save_detailed_log()
        return 1
    print()

    # Phase 3: WebSocket team runs with full logging
    print("--- Phase 3: WebSocket Team Execution (Full Logging) ---")
    await test_hybrid_team()
    await test_debate()
    await test_reflection()
    await test_code_generation()
    print()

    # Summary
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    total_dur = sum(r["duration_s"] for r in results)

    print("=" * 70)
    print(f"  Results: {pass_count} PASS, {fail_count} FAIL")
    print(f"  Total duration: {total_dur:.1f}s")
    print("=" * 70)

    # Save detailed logs
    log_path = save_detailed_log()

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
