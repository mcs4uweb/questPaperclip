"""Run the system-wide Nanoclaw CLI (same idea as hermes_runner)."""

from __future__ import annotations

import os
import shutil
from typing import Optional

from hermes_runner import run_process


def nanoclaw_available() -> tuple[bool, Optional[str]]:
    for name in ("nanoclaw", "nano-claw", "nanoclaw.cmd", "nanoclaw.exe"):
        path = shutil.which(name)
        if path:
            return True, path
    return False, None


def _command_variants(path: str, goal: str) -> list[list[str]]:
    return [
        [path, "-p", goal],
        [path, "chat", "-q", goal],
        [path, "chat", "-p", goal],
        [path, goal],
    ]


def run_nanoclaw_chat(
    goal: str,
    cwd: Optional[str] = None,
    timeout_sec: Optional[int] = None,
    cancel_check=None,
    pid_callback=None,
) -> dict:
    found, path = nanoclaw_available()
    if not found:
        return {
            "ok": False,
            "error": "nanoclaw CLI not found on PATH. Confirm `nanoclaw` works in a terminal.",
            "stdout": "",
            "stderr": "",
            "latency_ms": 0,
            "tokens": None,
            "token_count": None,
            "usage_source": "unknown",
        }

    workdir = cwd if cwd and os.path.isdir(cwd) else None
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("NO_COLOR", "1")
    env.setdefault("TERM", "dumb")

    last = {
        "ok": False,
        "error": "nanoclaw failed",
        "stdout": "",
        "stderr": "",
        "latency_ms": 0,
        "token_count": None,
        "tokens": None,
        "usage_source": "unknown",
    }

    for args in _command_variants(path, goal):
        result = run_process(
            args,
            cwd=workdir,
            timeout_sec=timeout_sec,
            cancel_check=cancel_check,
            pid_callback=pid_callback,
            env=env,
        )
        result["argv"] = args[1:]
        if result.get("error") == "cancelled":
            return result
        if result.get("error") and str(result["error"]).startswith("timed out"):
            result["error"] = f"nanoclaw timed out after {timeout_sec}s"
            return result
        if result.get("ok"):
            return result
        hint = ((result.get("stderr") or "") + " " + (result.get("stdout") or "")).lower()
        code = result.get("returncode")
        last = result
        if code in (2, 64) or "usage" in hint or "unknown" in hint:
            last["error"] = result.get("error") or f"nanoclaw exited {code}"
            continue
        if result.get("error") and not str(result["error"]).startswith("nanoclaw"):
            result["error"] = result["error"]
        return result

    return last
