"""Call a local OpenClaw chat proxy (default http://127.0.0.1:18789/chat/main)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Optional

DEFAULT_URL = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789/chat/main")
DEFAULT_TIMEOUT = int(os.environ.get("OPENCLAW_TIMEOUT", "90"))


def _extract_text(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, list):
        return "\n".join(part for part in (_extract_text(item) for item in payload) if part)
    if not isinstance(payload, dict):
        return str(payload)

    for key in ("output", "response", "text", "content", "message", "reply", "result", "completion"):
        if key in payload and payload[key] not in (None, ""):
            value = payload[key]
            if key == "message" and isinstance(value, dict):
                return _extract_text(value.get("content") or value.get("text") or value)
            if key == "content" and isinstance(value, list):
                chunks = []
                for item in value:
                    if isinstance(item, dict):
                        chunks.append(str(item.get("text") or item.get("content") or ""))
                    else:
                        chunks.append(str(item))
                return "\n".join(chunk for chunk in chunks if chunk).strip()
            if isinstance(value, (dict, list)):
                return _extract_text(value)
            return str(value).strip()

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        return _extract_text(first.get("message") or first.get("text") or first)

    return ""


def _post(url: str, body: dict, timeout_sec: int) -> tuple[int, Any, str]:
    raw = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            status = getattr(resp, "status", 200)
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return exc.code, _maybe_json(text), text
    except urllib.error.URLError as exc:
        raise ConnectionError(str(exc.reason or exc)) from exc

    return status, _maybe_json(text), text


def _maybe_json(text: str) -> Any:
    try:
        return json.loads(text) if text else {}
    except json.JSONDecodeError:
        return text


def openclaw_status(url: str = DEFAULT_URL, timeout_sec: int = 5) -> dict:
    started = time.perf_counter()
    try:
        req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json, text/plain"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {
                "available": True,
                "url": url,
                "method": "GET",
                "http_status": getattr(resp, "status", 200),
                "body": body[:1000],
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "available": exc.code < 500,
            "url": url,
            "method": "GET",
            "http_status": exc.code,
            "body": body[:1000],
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "note": "Proxy responded. POST /chat/main to send a message.",
        }
    except Exception as exc:
        return {
            "available": False,
            "url": url,
            "error": str(exc),
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }


def run_openclaw_chat(
    goal: str,
    url: str = DEFAULT_URL,
    timeout_sec: int = DEFAULT_TIMEOUT,
    extra: Optional[dict] = None,
) -> dict:
    body = extra if extra and isinstance(extra, dict) else {"message": goal}
    if "message" not in body:
        body = {**body, "message": goal}

    started = time.perf_counter()
    try:
        status, parsed, raw = _post(url, body, timeout_sec)
    except ConnectionError as exc:
        return {
            "ok": False,
            "error": f"Cannot reach OpenClaw at {url}: {exc}",
            "stdout": "",
            "stderr": "",
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "tokens": None,
            "token_count": None,
            "usage_source": "unknown",
            "url": url,
        }

    if not (200 <= status < 300):
        snippet = (raw or "")[:500]
        return {
            "ok": False,
            "error": f"HTTP {status}: {snippet}",
            "stdout": "",
            "stderr": snippet,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "tokens": None,
            "token_count": None,
            "usage_source": "unknown",
            "url": url,
            "request": body,
            "http_status": status,
        }

    text = _extract_text(parsed)
    if not text:
        snippet = (raw or "")[:500]
        return {
            "ok": False,
            "error": f"OpenClaw returned unrecognized JSON: {snippet}",
            "stdout": "",
            "stderr": snippet,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "tokens": None,
            "token_count": None,
            "usage_source": "unknown",
            "url": url,
            "request": body,
            "http_status": status,
        }

    usage = None
    if isinstance(parsed, dict):
        if isinstance(parsed.get("usage"), dict):
            usage = parsed["usage"]
        elif any(key in parsed for key in ("total_tokens", "prompt_tokens", "token_count", "cost")):
            usage = parsed

    return {
        "ok": True,
        "error": None,
        "stdout": text,
        "stderr": "",
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "tokens": None,
        "token_count": None,
        "usage": usage,
        "usage_source": "unknown",
        "url": url,
        "request": body,
        "http_status": status,
    }
