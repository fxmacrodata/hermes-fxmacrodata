"""Hermes registration and JSON handlers for the public FXMacroData contracts."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
from typing import Any

from .public_client import FXMacroDataClient as _PublicClient
from .public_client import FXMacroDataError, Result, list_operations

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
    "Empty records mean unavailable; never invent data. When a result carries notices, "
    "relay them: free-tier data can be delayed or limited to a recent window. MCP resources are preserved "
    "as structured results; this plugin does not render MCP Apps."
)
BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "indicator": {"type": "string", "default": "policy_rate", "description": "USD indicator slug from catalogue discovery."}
    },
    "additionalProperties": False,
}


SUBSCRIBE_URL = "https://fxmacrodata.com/subscribe"
NOTICE_FIELDS = ("freemium_window", "freemium_delay")
ERROR_CODE_PATTERN = re.compile(r"[a-z0-9_]{1,64}")
ACCESS_ERROR_CODES = frozenset({"api_key_required", "subscription_required", "invalid_api_key"})


def _response_body(payload: Any) -> Any:
    """Return the REST body, or the structured content of an MCP tool result."""
    if isinstance(payload, dict) and isinstance(payload.get("structuredContent"), dict):
        return payload["structuredContent"]
    return payload


def access_notices(payload: Any) -> list[str]:
    """Collect the free-tier window and delay messages so delayed data is never presented as current."""
    body = _response_body(payload)
    if not isinstance(body, dict):
        return []
    notices = []
    for field_name in NOTICE_FIELDS:
        value = body.get(field_name)
        message = value.get("message") if isinstance(value, dict) else value
        if isinstance(message, str) and message.strip():
            notices.append(message.strip())
    return notices


def error_body_message(payload: Any) -> str | None:
    """Turn a successful HTTP status that carries an error body into an actionable error."""
    body = _response_body(payload)
    if not isinstance(body, dict) or "data" in body:
        return None
    code = body.get("error")
    if not isinstance(code, str) or not code.strip():
        return None
    code = code.strip().lower()
    if code in ACCESS_ERROR_CODES:
        return (f"FXMacroData needs an authorized API key for this request ({code}). "
                f"Set FXMACRODATA_API_KEY; keys are available at {SUBSCRIBE_URL}.")
    if ERROR_CODE_PATTERN.fullmatch(code):
        return f"FXMacroData returned an error ({code}). Check parameters and access, then retry."
    return "FXMacroData returned an error. Check parameters and access, then retry."


def _envelope(result: Result) -> dict[str, Any]:
    output = result.as_dict()
    output["provider_url"] = SITE_URL
    output["citations"] = [{"title": "FXMacroData", "url": result.source_url}]
    notices = access_notices(result.payload)
    if notices:
        output["notices"] = notices
    return output


def _error(operation: str, message: str) -> dict[str, Any]:
    return {"operation": operation, "error": message, "provider_url": SITE_URL}


def query(operation: str, arguments: dict[str, Any], timeout: float = 30) -> dict[str, Any]:
    """Execute with a per-call client so secrets and sessions are never persisted."""
    key = os.getenv("FXMACRODATA_API_KEY", "").strip()
    try:
        with FXMacroDataClient(api_key=key, timeout=timeout) as client:
            result = client.execute(operation, arguments)
            payload = sanitize_response(result.payload, key)
            message = error_body_message(payload)
            if message is not None:
                return _error(operation, message)
            return _envelope(Result(operation, payload, sanitize_response(result.source_url, key)))
    except FXMacroDataError as exc:
        try:
            message = sanitize_response(str(exc), key)
        except ValueError:
            message = "FXMacroData could not safely decode the response. Retry the request."
        return _error(operation, message)
    except Exception:
        return _error(operation, "FXMacroData request failed. Check parameters and access, then retry.")


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
