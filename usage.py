"""Parse provider usage. Never invent tokens from word counts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ParsedUsage:
    tokens: Optional[int] = None
    cost: Optional[float] = None
    source: str = "unknown"


_TOKEN_LINE = re.compile(
    r"(?i)\btokens?\b\s*[:=]\s*([\d,]+(?:\.\d+)?)"
)
_COST_LINE = re.compile(
    r"(?i)\bcost\b\s*[:=]\s*\$?\s*([\d,]+(?:\.\d+)?)"
)
_USAGE_JSON = re.compile(r"\{[^{}]*\"(?:usage|total_tokens|prompt_tokens)\"[^{}]*\}")


def _to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        number = float(value)
        if number < 0:
            return None
        return int(number)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace("$", "").strip()
        number = float(value)
        if number < 0:
            return None
        return number
    except (TypeError, ValueError):
        return None


def _from_mapping(data: Any) -> ParsedUsage:
    if not isinstance(data, dict):
        return ParsedUsage()
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else data
    tokens = (
        _to_int(usage.get("total_tokens"))
        or _to_int(usage.get("token_count"))
        or _to_int(usage.get("tokens"))
    )
    prompt = _to_int(usage.get("prompt_tokens") or usage.get("input_tokens"))
    completion = _to_int(usage.get("completion_tokens") or usage.get("output_tokens"))
    if tokens is None and prompt is not None and completion is not None:
        tokens = prompt + completion
    elif tokens is None and prompt is not None:
        tokens = prompt
    cost = _to_float(usage.get("cost") or usage.get("total_cost") or data.get("cost"))
    if tokens is None and cost is None:
        return ParsedUsage()
    return ParsedUsage(tokens=tokens, cost=cost, source="parsed")


def parse_usage(text: str = "", provider_usage: Any = None) -> ParsedUsage:
    mapped = _from_mapping(provider_usage)
    if mapped.source == "parsed":
        return mapped

    blob = text or ""
    mapped = _from_mapping(provider_usage if isinstance(provider_usage, dict) else None)
    if mapped.source == "parsed":
        return mapped

    for match in _USAGE_JSON.finditer(blob):
        try:
            parsed = _from_mapping(json.loads(match.group(0)))
        except json.JSONDecodeError:
            continue
        if parsed.source == "parsed":
            return parsed

    tokens = None
    cost = None
    token_match = _TOKEN_LINE.search(blob)
    if token_match:
        tokens = _to_int(token_match.group(1))
    cost_match = _COST_LINE.search(blob)
    if cost_match:
        cost = _to_float(cost_match.group(1))
    if tokens is None and cost is None:
        return ParsedUsage()
    return ParsedUsage(tokens=tokens, cost=cost, source="parsed")
