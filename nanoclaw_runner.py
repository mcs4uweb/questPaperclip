"""Run the system-wide Nanoclaw CLI (same idea as hermes_runner)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Optional


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
) -> dict:
    found, path = nanoclaw_available()
    if not found:
        return {
            "ok": False,
            "error": "nanoclaw CLI not found on PATH. Confirm `nanoclaw` works in a terminal.",
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

    last_error = "nanoclaw failed"
    last_stdout = ""
    last_stderr = ""
    last_code = None

    try:
        for args in _command_variants(path, goal):
            completed = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_sec,
                cwd=workdir,
                shell=False,
                env=env,
            )
            stdout = (completed.stdout or "").strip()
            stderr = (completed.stderr or "").strip()
            combined = "\n".join(part for part in (stdout, stderr) if part).strip()
            last_stdout, last_stderr, last_code = stdout, stderr, completed.returncode
            if completed.returncode == 0:
                return {
                    "ok": True,
                    "error": None,
                    "stdout": stdout or combined,
                    "stderr": stderr,
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "token_count": max(1, len(goal.split()) + len((stdout or combined).split())),
                    "returncode": 0,
                    "argv": args[1:],
                }
            hint = (stderr or stdout or "").lower()
            if completed.returncode in (2, 64) or "usage" in hint or "unknown" in hint:
                last_error = combined or f"nanoclaw exited {completed.returncode}"
                continue
            return {
                "ok": False,
                "error": combined or f"nanoclaw exited {completed.returncode}",
                "stdout": stdout,
                "stderr": stderr,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "token_count": 0,
                "returncode": completed.returncode,
                "argv": args[1:],
            }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"nanoclaw timed out after {timeout_sec}s",
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

    return {
        "ok": False,
        "error": last_error or f"nanoclaw exited {last_code}",
        "stdout": last_stdout,
        "stderr": last_stderr,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "token_count": 0,
        "returncode": last_code,
    }
