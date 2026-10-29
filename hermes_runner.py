"""Run local Hermes CLI agents (same pattern as Retirement-app/hermes.ps1)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Callable, Optional


def hermes_available() -> tuple[bool, Optional[str]]:
    path = shutil.which("hermes")
    return (bool(path), path)


def _drain(proc: subprocess.Popen) -> tuple[str, str]:
    try:
        stdout, stderr = proc.communicate(timeout=2)
    except Exception:
        stdout = ""
        stderr = ""
        try:
            proc.kill()
        except OSError:
            pass
    return (stdout or "").strip(), (stderr or "").strip()


def _stop(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
    except OSError:
        pass
    try:
        proc.wait(timeout=1)
    except Exception:
        try:
            proc.kill()
        except OSError:
            pass


def run_process(
    args: list[str],
    *,
    cwd: Optional[str] = None,
    timeout_sec: Optional[int] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    pid_callback: Optional[Callable[[int], None]] = None,
    env: Optional[dict] = None,
) -> dict:
    started = time.perf_counter()
    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            env=env,
            shell=False,
        )
    except OSError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "stdout": "",
            "stderr": "",
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "tokens": None,
            "token_count": None,
            "usage_source": "unknown",
        }

    if pid_callback:
        try:
            pid_callback(proc.pid)
        except Exception:
            pass

    deadline = None if timeout_sec is None else time.monotonic() + timeout_sec
    while True:
        if cancel_check and cancel_check():
            _stop(proc)
            stdout, stderr = _drain(proc)
            return {
                "ok": False,
                "error": "cancelled",
                "stdout": stdout,
                "stderr": stderr,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "tokens": None,
                "token_count": None,
                "usage_source": "unknown",
                "returncode": proc.returncode,
            }
        code = proc.poll()
        if code is not None:
            stdout, stderr = _drain(proc)
            combined = "\n".join(part for part in (stdout, stderr) if part).strip()
            ok = code == 0
            return {
                "ok": ok,
                "error": None if ok else (combined or f"exited {code}"),
                "stdout": stdout or combined,
                "stderr": stderr,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "tokens": None,
                "token_count": None,
                "usage_source": "unknown",
                "returncode": code,
            }
        if deadline is not None and time.monotonic() >= deadline:
            _stop(proc)
            stdout, stderr = _drain(proc)
            return {
                "ok": False,
                "error": f"timed out after {timeout_sec}s",
                "stdout": stdout,
                "stderr": stderr,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "tokens": None,
                "token_count": None,
                "usage_source": "unknown",
            }
        time.sleep(0.05)


def run_hermes_chat(
    goal: str,
    cwd: Optional[str] = None,
    timeout_sec: Optional[int] = None,
    cancel_check=None,
    pid_callback=None,
) -> dict:
    found, path = hermes_available()
    if not found:
        return {
            "ok": False,
            "error": "hermes CLI not found on PATH. Install Hermes and confirm `hermes` works in a terminal.",
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
    result = run_process(
        [path, "chat", "-q", goal],
        cwd=workdir,
        timeout_sec=timeout_sec,
        cancel_check=cancel_check,
        pid_callback=pid_callback,
        env=env,
    )
    if result.get("error") and result["error"].startswith("timed out"):
        result["error"] = f"hermes timed out after {timeout_sec}s"
    elif result.get("error") and result["error"].startswith("exited"):
        result["error"] = f"hermes {result['error']}"
    return result
