"""Run local Hermes CLI agents (same pattern as Retirement-app/hermes.ps1)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Optional


def hermes_available() -> tuple[bool, Optional[str]]:
    path = shutil.which("hermes")
    return (bool(path), path)


def run_hermes_chat(
    goal: str,
    cwd: Optional[str] = None,
    timeout_sec: Optional[int] = None,
) -> dict:
    found, path = hermes_available()
    if not found:
        return {
            "ok": False,
            "error": "hermes CLI not found on PATH. Install Hermes and confirm `hermes` works in a terminal.",
            "stdout": "",
            "stderr": "",
            "latency_ms": 0,
            "token_count": 0,
        }

    workdir = cwd if cwd and os.path.isdir(cwd) else None
    started = time.perf_counter()
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("NO_COLOR", "1")
    env.setdefault("TERM", "dumb")
    try:
        completed = subprocess.run(
            [path, "chat", "-q", goal],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,  # None = wait until Hermes exits (Grok can take a long time)
            cwd=workdir,
            shell=False,
            env=env,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        combined = "\n".join(part for part in (stdout, stderr) if part).strip()
        ok = completed.returncode == 0
        return {
            "ok": ok,
            "error": None if ok else (combined or f"hermes exited {completed.returncode}"),
            "stdout": stdout or combined,
            "stderr": stderr,
            "latency_ms": latency_ms,
            "token_count": max(1, len(goal.split()) + len((stdout or combined).split())),
            "returncode": completed.returncode,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"hermes timed out after {timeout_sec}s",
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "") if isinstance(exc.stderr, str) else "",
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "token_count": 0,
        }
    except OSError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "stdout": "",
            "stderr": "",
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "token_count": 0,
        }
