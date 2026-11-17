"""Dollar cost for a run, priced with the rates configured in the LiteLLM proxy.

Prices come from the proxy's /model/info (the same per-token rates LiteLLM is
configured with), so paperclip never hard-codes or invents a price. The proxy
URL and key default to the ones Hermes uses; override with
PAPERCLIP_LITELLM_URL / PAPERCLIP_LITELLM_KEY. If no price is known for a
model, cost is None (shown as unknown), never a guess.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any, Optional

CACHE_TTL_SEC = 3600
_cache: dict[str, Any] = {}


def _hermes_proxy_settings() -> tuple[Optional[str], Optional[str]]:
    """(base_url, api_key) of the provider Hermes is configured to use."""
    from hermes_usage import hermes_home

    path = os.path.join(hermes_home(), "config.yaml")
    try:
        import yaml

        with open(path, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh) or {}
    except Exception:
        return None, None
    provider_name = ((cfg.get("model") or {}).get("provider")) or ""
    provider = (cfg.get("providers") or {}).get(provider_name) or {}
    return provider.get("api") or provider.get("base_url"), provider.get("api_key")


def _proxy_settings() -> tuple[Optional[str], Optional[str]]:
    url = os.environ.get("PAPERCLIP_LITELLM_URL")
    key = os.environ.get("PAPERCLIP_LITELLM_KEY")
    if not url or not key:
        h_url, h_key = _hermes_proxy_settings()
        url = url or h_url
        key = key or h_key
    return url, key


def _fetch_model_info() -> Optional[dict]:
    url, key = _proxy_settings()
    if not url:
        return None
    base = url.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    req = urllib.request.Request(base + "/model/info")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _price_table() -> dict[str, dict]:
    now = time.time()
    if _cache.get("table") is not None and now - _cache.get("fetched_at", 0) < CACHE_TTL_SEC:
        return _cache["table"]
    info = _fetch_model_info()
    if info and isinstance(info.get("data"), list):
        table: dict[str, dict] = {}
        for entry in info["data"]:
            mi = entry.get("model_info") or {}
            inp, out = mi.get("input_cost_per_token"), mi.get("output_cost_per_token")
            if inp is None or out is None:
                continue
            table[entry.get("model_name")] = {
                "input": float(inp),
                "output": float(out),
                "cache_read": _opt_float(mi.get("cache_read_input_token_cost")),
                "cache_write": _opt_float(mi.get("cache_creation_input_token_cost")),
            }
        _cache.update(table=table, fetched_at=now)
    elif _cache.get("table") is not None:
        _cache["fetched_at"] = now - CACHE_TTL_SEC + 60  # proxy down: keep last good, retry in 1 min
    return _cache.get("table") or {}


def _opt_float(value: Any) -> Optional[float]:
    return None if value is None else float(value)


def prices_for(model: Optional[str]) -> Optional[dict]:
    if not model:
        return None
    return _price_table().get(model)


def cost_for(usage: dict) -> Optional[float]:
    """USD cost of a session. Hermes's input_tokens include cache reads/writes."""
    prices = prices_for(usage.get("model"))
    if not prices:
        return None
    inp = int(usage.get("input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    cache_read = int(usage.get("cache_read_tokens") or 0)
    cache_write = int(usage.get("cache_write_tokens") or 0)
    read_rate = prices["cache_read"] if prices["cache_read"] is not None else prices["input"]
    write_rate = prices["cache_write"] if prices["cache_write"] is not None else prices["input"]
    uncached = max(0, inp - cache_read - cache_write)
    return (
        uncached * prices["input"]
        + cache_read * read_rate
        + cache_write * write_rate
        + out * prices["output"]
    )
