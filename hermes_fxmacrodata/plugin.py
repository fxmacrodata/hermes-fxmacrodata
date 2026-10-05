"""Hermes registration and JSON handlers for the public FXMacroData contracts."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Any

from fxmacrodata_public import FXMacroDataClient as _PublicClient
from fxmacrodata_public import FXMacroDataError, Result, list_operations

from .response_safety import sanitize_response


class FXMacroDataClient(_PublicClient):
    """Apply JSON-aware redaction before the pinned client's record projection."""

    def _safe(self, value: Any) -> Any:
        return sanitize_response(value, self._api_key)


SITE_URL = "https://fxmacrodata.com/?utm_source=hermes&utm_medium=integration&utm_campaign=hermes-fxmacrodata&utm_content=app"
GUIDANCE = (
    "Discover indicator slugs with fxmd_data_catalogue before requesting history. "
    "Public USD catalogue, indicator history and calendar need no API key. "
    "Keep source URLs and timestamp fields in answers. Distinguish observed releases, "
    "scheduled releases, market consensus and FXMacroData-generated predictions. "
    "Empty records mean unavailable; never invent data. MCP resources are preserved "
    "as structured results; this plugin does not render MCP Apps."
)
BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "indicator": {"type": "string", "default": "policy_rate", "description": "USD indicator slug from catalogue discovery."}
    },
    "additionalProperties": False,
}


def _envelope(result: Result) -> dict[str, Any]:
    output = result.as_dict()
    output["provider_url"] = SITE_URL
    output["citations"] = [{"title": "FXMacroData", "url": result.source_url}]
    return output


def query(operation: str, arguments: dict[str, Any], timeout: float = 30) -> dict[str, Any]:
    """Execute with a per-call client so secrets and sessions are never persisted."""
    key = os.getenv("FXMACRODATA_API_KEY") or os.getenv("FXMD_API_KEY") or ""
    try:
        with FXMacroDataClient(api_key=key, timeout=timeout) as client:
            result = client.execute(operation, arguments)
            safe_result = Result(operation, sanitize_response(result.payload, key), sanitize_response(result.source_url, key))
            return _envelope(safe_result)
    except FXMacroDataError as exc:
        try:
            message = sanitize_response(str(exc), key)
        except ValueError:
            message = "FXMacroData could not safely decode the response. Retry the request."
        return {"operation": operation, "error": message, "provider_url": SITE_URL}
    except Exception:
        return {
            "operation": operation,
            "error": "FXMacroData request failed. Check parameters and access, then retry.",
            "provider_url": SITE_URL,
        }


def usd_brief(arguments: dict[str, Any], timeout: float = 30) -> dict[str, Any]:
    """Compose catalogue, history and calendar without introducing derived facts."""
    import jsonschema

    try:
        jsonschema.Draft202012Validator(BRIEF_SCHEMA).validate(arguments)
    except (jsonschema.ValidationError, TypeError):
        return {"error": "Use an optional indicator slug; credentials are not tool arguments.", "provider_url": SITE_URL}
    today = datetime.now(timezone.utc).date()
    requests = (
        ("data_catalogue", {"currency": "usd"}),
        ("indicator_history", {"currency": "usd", "indicator": arguments.get("indicator", "policy_rate"), "limit": 10}),
        (
            "release_calendar",
            {"currency": "usd", "start_date": today.isoformat(), "end_date": (today + timedelta(days=7)).isoformat(), "timezone": "UTC"},
        ),
    )
    sections = [query(name, args, timeout) for name, args in requests]
    return {
        "title": "USD macro research brief",
        "sections": sections,
        "complete": all("error" not in section for section in sections),
        "instructions": GUIDANCE,
        "provider_url": SITE_URL,
    }


def register(ctx) -> None:
    """Register every operation through Hermes' native scoped tool registry."""
    ctx.register_skill(
        "macro-research", Path(__file__).parent / "skills/macro-research/SKILL.md", "Sourced macro research using FXMacroData tools"
    )
    ctx.register_system_prompt_section("fxmacrodata-research", GUIDANCE)

    def timeout():
        return ctx.get_config("timeout_seconds", 30)

    for operation in list_operations():
        name = "fxmd_" + operation.name

        def handler(args, _operation=operation.name, **kwargs):
            try:
                return json.dumps(query(_operation, args, timeout()), ensure_ascii=False)
            except Exception:
                return json.dumps({"error": "FXMacroData settings are invalid. Check the request timeout."})

        ctx.register_tool(
            name=name,
            toolset="fxmacrodata",
            schema={"name": name, "description": operation.description, "parameters": deepcopy(operation.input_schema)},
            handler=handler,
            description="FXMacroData public API and MCP research tools",
        )

    def brief_handler(args, **kwargs):
        try:
            return json.dumps(usd_brief(args, timeout()), ensure_ascii=False)
        except Exception:
            return json.dumps({"error": "FXMacroData settings are invalid. Check the request timeout."})

    ctx.register_tool(
        name="fxmd_usd_macro_brief",
        toolset="fxmacrodata",
        schema={
            "name": "fxmd_usd_macro_brief",
            "description": "Build a sourced USD catalogue, indicator history and release-calendar brief without an API key. " + GUIDANCE,
            "parameters": deepcopy(BRIEF_SCHEMA),
        },
        handler=brief_handler,
        description="Sourced USD macro research workflow",
    )

    def brief_command(raw_args: str):
        return brief_handler({"indicator": raw_args.strip()} if raw_args.strip() else {})

    ctx.register_command("fxmacrodata", brief_command, description="USD macro brief with source citations", args_hint="[indicator]")
