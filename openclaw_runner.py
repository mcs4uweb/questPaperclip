"""Run OpenClaw agent turns through the local OpenClaw Gateway.

Uses the OpenClaw CLI (`openclaw agent --message-file ... --json`), which routes
the turn through the running Gateway (ws://127.0.0.1:18789). The Gateway has no
HTTP chat endpoint, so the old POST /chat/main approach always returned 404.

Each paperclip job gets its own OpenClaw session (paperclip-<job id>) so a run
doesn't drag the whole history of the user's main session into every prompt.
Token usage and the provider-billed cost come from OpenClaw's JSON result.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Optional
from uuid import uuid4

from hermes_runner import run_process

GATEWAY_URL = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789/")
DEFAULT_URL = GATEWAY_URL  # kept for callers that still import DEFAULT_URL
OPENCLAW_AGENT = os.environ.get("OPENCLAW_AGENT", "main")
DEFAULT_TIMEOUT = int(os.environ.get("OPENCLAW_TIMEOUT", "1800"))


def openclaw_available() -> tuple[bool, Optional[str]]:
    path = shutil.which("openclaw")
    return (bool(path), path)


def openclaw_status(url: str = GATEWAY_URL, timeout_sec: int = 5) -> dict:
    """Probe the Gateway's HTTP root (the dashboard); 200 means it is serving."""
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as resp:
            return {
                "available": True,
                "url": url,
                "http_status": getattr(resp, "status", 200),
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }
    except urllib.error.HTTPError as exc:
        return {
            "available": False,
            "url": url,
            "http_status": exc.code,
            "error": f"Gateway answered HTTP {exc.code}",
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:
        return {
            "available": False,
            "url": url,
            "error": f"Gateway not reachable: {exc}. Start it with `oc` or `openclaw gateway status`.",
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }


def _fail(error: str, started: float, stdout: str = "", stderr: str = "") -> dict:
    return {
        "ok": False,
        "error": error,
        "stdout": stdout,
        "stderr": stderr,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "tokens": None,
        "token_count": None,
        "usage_source": "unknown",
    }


def parse_agent_json(text: str) -> dict:
    """Map `openclaw agent --json` output to paperclip's raw result fields."""
    data: Any = json.loads(text)
    result = data.get("result") or {}
    replies = [p.get("text") for p in (result.get("payloads") or []) if isinstance(p, dict) and p.get("text")]
    meta = (result.get("meta") or {}).get("agentMeta") or {}
    usage = meta.get("usage") or {}
    out: dict = {
        "ok": data.get("status") == "ok",
        "stdout": "\n\n".join(replies).strip(),
        "error": None if data.get("status") == "ok" else (data.get("summary") or data.get("status") or "failed"),
        "session_id": meta.get("sessionId"),
        "model": meta.get("model"),
    }
    if usage:
        inp, outp = int(usage.get("input") or 0), int(usage.get("output") or 0)
        cost = (usage.get("cost") or {}).get("total")
        out.update(
            tokens=int(usage.get("total") or inp + outp),
            token_count=int(usage.get("total") or inp + outp),
            input_tokens=inp,
            output_tokens=outp,
            cost=float(cost) if cost is not None else None,
            usage_source="parsed",
        )
    return out


def run_openclaw_chat(
    goal: str,
    url: Optional[str] = None,  # unused; accepted for backward compatibility
    timeout_sec: Optional[int] = None,
    extra: Optional[dict] = None,  # unused; accepted for backward compatibility
    *,
    job_id: Optional[str] = None,
    cwd: Optional[str] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    pid_callback: Optional[Callable[[int], None]] = None,
) -> dict:
    started = time.perf_counter()
    found, path = openclaw_available()
    if not found:
        return _fail("openclaw CLI not found on PATH. Install OpenClaw and confirm `openclaw` works in a terminal.", started)

    timeout = int(timeout_sec or DEFAULT_TIMEOUT)
    session_id = f"paperclip-{job_id or uuid4().hex[:10]}"

    # --message-file: `openclaw` is a .cmd shim, and cmd.exe mangles long or
    # special-character (& | % ^) arguments.
    fd, msg_path = tempfile.mkstemp(prefix="paperclip-openclaw-", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(goal)
        args = [
            path, "agent",
            "--agent", OPENCLAW_AGENT,
            "--session-id", session_id,
            "--message-file", msg_path,
            "--timeout", str(timeout),
            "--json",
        ]
        env = os.environ.copy()
        env.setdefault("NO_COLOR", "1")
        raw = run_process(
            args,
            cwd=cwd if cwd and os.path.isdir(cwd) else None,
            timeout_sec=timeout + 60,  # let OpenClaw's own --timeout fire first
            cancel_check=cancel_check,
            pid_callback=pid_callback,
            env=env,
        )
    finally:
        try:
            os.remove(msg_path)
        except OSError:
            pass

    if raw.get("error") == "cancelled" or (raw.get("error") or "").startswith("timed out"):
        return {**raw, "error": f"openclaw {raw['error']}" if raw["error"] != "cancelled" else "cancelled"}

    stdout = raw.get("stdout") or ""
    stderr = raw.get("stderr") or ""
    try:
        parsed = parse_agent_json(stdout)
    except (ValueError, AttributeError):
        detail = (stderr or stdout or raw.get("error") or "no output")[-800:]
        return _fail(f"OpenClaw run failed: {detail}", started, stdout=stdout, stderr=stderr)

    if parsed["ok"] and not parsed["stdout"]:
        parsed["ok"] = False
        parsed["error"] = "OpenClaw finished but returned no reply text"
    parsed.update(stderr=stderr, latency_ms=raw.get("latency_ms") or int((time.perf_counter() - started) * 1000))
    parsed.setdefault("tokens", None)
    parsed.setdefault("token_count", None)
    parsed.setdefault("usage_source", "unknown")
    return parsed
