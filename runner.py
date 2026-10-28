"""Shared run contract for Hermes, OpenClaw, and Nanoclaw."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional

from usage import parse_usage

RUNNABLE_KINDS = frozenset({"hermes", "openclaw", "nanoclaw"})

RunnerImpl = Callable[..., "Result"]
_impl: Optional[RunnerImpl] = None


@dataclass
class Result:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    tokens: Optional[int] = None
    cost: Optional[float] = None
    latency_ms: int = 0
    model: Optional[str] = None
    usage_source: str = "unknown"


def set_runner_impl(fn: Optional[RunnerImpl]) -> None:
    global _impl
    _impl = fn


def apply_result(result: Result) -> dict[str, Any]:
    data = asdict(result)
    return data


def is_runnable_kind(kind: Optional[str]) -> bool:
    return (kind or "").strip().lower() in RUNNABLE_KINDS


def _attach_usage(result: Result, text: str = "", provider_usage: Any = None) -> Result:
    parsed = parse_usage(text, provider_usage=provider_usage)
    result.tokens = parsed.tokens
    result.cost = parsed.cost
    result.usage_source = parsed.source
    return result


def run_agent(
    agent: dict,
    goal: str,
    cwd: Optional[str] = None,
    timeout_sec: Optional[int] = None,
    job_id: Optional[str] = None,
    url: Optional[str] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    pid_callback: Optional[Callable[[int], None]] = None,
) -> Result:
    if _impl is not None:
        return _impl(
            agent,
            goal,
            cwd=cwd,
            timeout_sec=timeout_sec,
            job_id=job_id,
            url=url,
            cancel_check=cancel_check,
            pid_callback=pid_callback,
        )

    kind = (agent.get("kind") or "").strip().lower()
    if kind == "hermes":
        from hermes_runner import run_hermes_chat

        raw = run_hermes_chat(
            goal,
            cwd=cwd,
            timeout_sec=timeout_sec,
            cancel_check=cancel_check,
            pid_callback=pid_callback,
        )
        return _from_raw(raw, model=agent.get("model") or "hermes")
    if kind == "nanoclaw":
        from nanoclaw_runner import run_nanoclaw_chat

        raw = run_nanoclaw_chat(
            goal,
            cwd=cwd,
            timeout_sec=timeout_sec,
            cancel_check=cancel_check,
            pid_callback=pid_callback,
        )
        return _from_raw(raw, model=agent.get("model") or "nanoclaw")
    if kind == "openclaw":
        from openclaw_runner import DEFAULT_URL, run_openclaw_chat

        raw = run_openclaw_chat(
            goal,
            url=url or DEFAULT_URL,
            timeout_sec=timeout_sec or 90,
        )
        return _from_raw(raw, model=agent.get("model") or "openclaw")

    return Result(
        ok=False,
        error=f"Agent kind {kind or agent.get('kind')!r} is display-only and is not routed through a CLI",
        usage_source="unknown",
    )


def _from_raw(raw: dict, model: str) -> Result:
    text = "\n".join(
        part for part in (raw.get("stdout") or "", raw.get("stderr") or "") if part
    )
    result = Result(
        ok=bool(raw.get("ok")),
        stdout=raw.get("stdout") or "",
        stderr=raw.get("stderr") or "",
        error=raw.get("error"),
        latency_ms=int(raw.get("latency_ms") or 0),
        model=model,
    )
    provider_usage = raw.get("usage") or raw.get("provider_usage")
    if raw.get("usage_source") == "parsed" and (raw.get("tokens") is not None or raw.get("cost") is not None):
        result.tokens = raw.get("tokens")
        result.cost = raw.get("cost")
        result.usage_source = "parsed"
        return result
    return _attach_usage(result, text, provider_usage=provider_usage)
