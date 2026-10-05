"""Installed Hermes entry-point, real registry, protocol and secret-boundary tests."""

from importlib.metadata import entry_points
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from threading import Barrier
from urllib.parse import parse_qs, quote, quote_plus, urlsplit

import pytest
import requests

from hermes_fxmacrodata.public_client import FXMacroDataError, list_operations
from hermes_fxmacrodata.plugin import FXMacroDataClient
from hermes_cli.plugins import PluginManager
from hermes_cli.plugins_discovery import discover_entrypoint_manifests
from tools.registry import registry

from transport_fixtures import PAYLOAD, Transport, arguments


@pytest.fixture
def manager(monkeypatch, tmp_path):
    monkeypatch.delenv("FXMACRODATA_API_KEY", raising=False)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    manager = PluginManager(scope_key=str(tmp_path))
    matches = [item for item in discover_entrypoint_manifests() if item.name == "fxmacrodata"]
    assert len(matches) == 1
    manager._load_plugin(matches[0])
    assert manager._plugins["fxmacrodata"].enabled, manager._plugins["fxmacrodata"].error
    yield manager
    manager.unload("fxmacrodata")


@pytest.fixture
def transport(monkeypatch):
    value = Transport()
    monkeypatch.setattr(requests.Session, "request", lambda session, *a, **kw: value.request(session, *a, **kw))
    return value


def test_installed_entrypoint_registers_every_schema_skill_and_command(manager):
    assert len([e for e in entry_points(group="hermes_agent.plugins") if e.name == "fxmacrodata"]) == 1
    expected = {"fxmd_" + operation.name for operation in list_operations()} | {"fxmd_usd_macro_brief"}
    assert set(manager._plugins["fxmacrodata"].tools_registered) == expected
    for operation in list_operations():
        assert registry.get_entry("fxmd_" + operation.name, scope=manager.scope_key).schema["parameters"] == operation.input_schema
    assert "fxmacrodata" in manager._plugin_commands
    assert "fxmacrodata:macro-research" in manager._plugin_skills
    assert Path(manager._plugin_skills["fxmacrodata:macro-research"]["path"]).is_file()


@pytest.mark.parametrize("operation", list_operations(), ids=lambda item: item.name)
def test_every_operation_through_real_native_dispatch(manager, transport, operation):
    output = json.loads(registry.dispatch("fxmd_" + operation.name, arguments(operation), scope=manager.scope_key))
    assert "error" not in output, output
    assert output["operation"] == operation.name
    assert output["citations"] and "fxmacrodata.com" in output["provider_url"]
    assert all(response.closed for response in transport.responses)
    assert all("api_key" not in (options.get("params") or {}) for _, _, options in transport.calls)
    assert all(not {"X-API-Key", "Authorization"} & set(options["headers"]) for _, _, options in transport.calls)
    if operation.name == "stream_events":
        assert output["data"]["events"][0]["data"] == PAYLOAD
    elif operation.method == "MCP":
        assert output["data"]["structuredContent"] == PAYLOAD
        assert transport.calls[-1][2]["json"]["params"]["name"] == operation.name[4:]
    else:
        assert output["data"] == PAYLOAD
    assert output["records"]


def test_brief_command_consumes_three_native_public_queries(manager, transport):
    output = json.loads(manager._plugin_commands["fxmacrodata"]["handler"]("policy_rate"))
    assert output["complete"] and len(output["sections"]) == 3
    assert [item["operation"] for item in output["sections"]] == ["data_catalogue", "indicator_history", "release_calendar"]
    assert len(transport.calls) == 3


@pytest.mark.parametrize("name,status", [("fxmd_ping", 200), ("fxmd_usd_macro_brief", 200), ("fxmd_ping", 429)])
def test_native_runtime_attribution_identifies_hermes(manager, transport, name, status):
    transport.status = status
    output = json.loads(registry.dispatch(name, {}, scope=manager.scope_key))
    for item in [output, *output.get("sections", [])]:
        url = urlsplit(item["provider_url"])
        assert url.scheme == "https" and url.hostname == "fxmacrodata.com"
        assert parse_qs(url.query) == {
            "utm_source": ["hermes"],
            "utm_medium": ["integration"],
            "utm_campaign": ["hermes-fxmacrodata"],
            "utm_content": ["app"],
        }


@pytest.mark.parametrize("operation", ["ping", "mcp_ping", "stream_events"])
def test_response_echo_is_redacted_before_native_output(manager, transport, monkeypatch, operation):
    key = "synthetic/credential+alpha"
    monkeypatch.setenv("FXMACRODATA_API_KEY", key)
    transport.payload = {
        "data": [
            {"apiKey": key, "nested": json.dumps({"authorization": "Bearer " + key}), "text": [key, quote(key, safe=""), quote_plus(key)]}
        ],
        key: "dictionary-key",
        "safe": "preserved",
    }
    args = {"max_events": 1, "max_seconds": 1} if operation == "stream_events" else {}
    result = registry.dispatch("fxmd_" + operation, args, scope=manager.scope_key)
    assert "error" not in json.loads(result)
    assert all(value not in result for value in (key, quote(key, safe=""), quote_plus(key)))
    assert "preserved" in result and "redacted" in result


@pytest.mark.parametrize("status", [301, 401, 403, 404, 429, 500])
def test_remote_failure_is_safe_and_actionable(manager, transport, status):
    transport.status = status
    transport.payload = {"error": "https://example.invalid/?api_key=never-disclose-this"}
    output = registry.dispatch("fxmd_ping", {}, scope=manager.scope_key)
    assert "error" in json.loads(output)
    assert "never-disclose-this" not in output and "example.invalid" not in output


def test_unknown_and_secret_arguments_do_not_reach_network(manager, transport):
    output = json.loads(registry.dispatch("fxmd_data_catalogue", {"currency": "usd", "api_key": "synthetic"}, scope=manager.scope_key))
    assert "error" in output and not transport.calls


def test_session_cleanup_and_credential_rotation(manager, transport, monkeypatch):
    for key in ("synthetic-first", "synthetic-second", ""):
        monkeypatch.setenv("FXMACRODATA_API_KEY", key)
        registry.dispatch("fxmd_ping", {}, scope=manager.scope_key)
        options = transport.calls[-1][2]
        assert options["headers"].get("X-API-Key", "") == key
        assert "api_key" not in (options.get("params") or {})
    assert all(response.closed for response in transport.responses)


@pytest.mark.parametrize("sensitive_value", [True, False, None, 123])
def test_encoded_mcp_text_never_exposes_credentials_in_projected_records(manager, transport, monkeypatch, sensitive_value):
    key = "synthetic/review-key+never-valid"
    monkeypatch.setenv("FXMACRODATA_API_KEY", key)
    encoded = "".join(f"\\u{ord(character):04x}" for character in key)
    payload_text = '{"note":"' + encoded + '","apiKey":' + json.dumps(sensitive_value) + ',"value":1.25,"requires_api_key":false}'
    transport.payload = {"content": [{"type": "text", "text": payload_text}]}
    result = json.loads(registry.dispatch("fxmd_mcp_ping", {}, scope=manager.scope_key))
    assert "error" not in result
    assert key not in json.dumps(result)
    assert result["records"][0]["value"] == 1.25
    assert result["records"][0]["requires_api_key"] is False
    assert result["records"][0]["apiKey"] == "[redacted]"


@pytest.mark.parametrize("operation", ["ping", "mcp_ping"])
@pytest.mark.parametrize("hex_case", ["04x", "04X"])
def test_plain_text_encoded_credential_is_redacted(manager, transport, monkeypatch, operation, hex_case):
    key = "synthetic-review-key-never-valid"
    monkeypatch.setenv("FXMACRODATA_API_KEY", key)
    encoded = "".join("\\u" + format(ord(character), hex_case) for character in key)
    transport.payload = {"data": [{"note": "Public note containing " + encoded + " and preserved context.", "value": None}]}
    result = json.loads(registry.dispatch("fxmd_" + operation, {}, scope=manager.scope_key))
    assert "error" not in result
    rendered = json.dumps(result).replace("\\\\", "\\")
    assert key not in rendered and encoded not in rendered
    assert "preserved context" in rendered and "[redacted]" in rendered


def test_concurrent_native_calls_keep_request_sessions_and_payloads_separate(manager, monkeypatch):
    barrier = Barrier(2)
    sessions = []

    def request(session, *args, **kwargs):
        sessions.append(session)
        barrier.wait(timeout=5)
        payload = {"data": [{"request_currency": args[1].rsplit("/", 1)[-1], "value": None}]}
        return Transport(payload=payload).request(session, *args, **kwargs)

    monkeypatch.setattr(requests.Session, "request", request)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(registry.dispatch, "fxmd_data_catalogue", {"currency": currency}, scope=manager.scope_key)
            for currency in ("usd", "eur")
        ]
        outputs = [json.loads(future.result(timeout=10)) for future in futures]
    assert [output["records"][0]["request_currency"] for output in outputs] == ["usd", "eur"]
    assert len(sessions) == 2 and sessions[0] is not sessions[1]


@pytest.mark.parametrize("depth", [1, 70])
def test_encoded_errors_are_redacted_or_fail_closed_at_native_boundary(manager, monkeypatch, depth):
    key = "synthetic-error-key-never-valid"
    monkeypatch.setenv("FXMACRODATA_API_KEY", key)
    encoded = "".join(f"\\u{ord(character):04x}" for character in key)
    message = "[" * depth + '{"note":"' + encoded + '"}' + "]" * depth

    def fail(*_):
        raise FXMacroDataError(message)

    monkeypatch.setattr(FXMacroDataClient, "execute", fail)
    result = registry.dispatch("fxmd_ping", {}, scope=manager.scope_key)
    assert "error" in json.loads(result)
    assert key not in result and encoded not in result.replace("\\\\", "\\")


def test_mcp_key_travels_as_bearer_header_never_in_the_url(manager, transport, monkeypatch):
    monkeypatch.setenv("FXMACRODATA_API_KEY", "synthetic-mcp-key")
    output = json.loads(registry.dispatch("fxmd_mcp_ping", {}, scope=manager.scope_key))
    assert "error" not in output
    mcp_calls = [options for _, url, options in transport.calls if url.startswith("https://mcp.fxmacrodata.com/")]
    assert mcp_calls
    for options in mcp_calls:
        assert options["headers"]["Authorization"] == "Bearer synthetic-mcp-key"
        assert "X-API-Key" not in options["headers"]
        assert "api_key" not in (options.get("params") or {})


def test_key_is_trimmed_before_use(manager, transport, monkeypatch):
    monkeypatch.setenv("FXMACRODATA_API_KEY", "  synthetic-padded-key\n")
    output = json.loads(registry.dispatch("fxmd_ping", {}, scope=manager.scope_key))
    assert "error" not in output
    assert transport.calls[-1][2]["headers"]["X-API-Key"] == "synthetic-padded-key"


@pytest.mark.parametrize("key", ["synthetic key", "synthetic\rkey", "syntheticékey"])
def test_header_invalid_key_fails_without_echo_or_network(manager, transport, monkeypatch, key):
    monkeypatch.setenv("FXMACRODATA_API_KEY", key)
    result = registry.dispatch("fxmd_ping", {}, scope=manager.scope_key)
    output = json.loads(result)
    assert "FXMACRODATA_API_KEY" in output["error"]
    assert "synthetic" not in result
    assert not transport.calls


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_redirects_are_never_followed(manager, transport, monkeypatch, status):
    monkeypatch.setenv("FXMACRODATA_API_KEY", "synthetic-redirect-key")
    transport.status = status
    output = json.loads(registry.dispatch("fxmd_ping", {}, scope=manager.scope_key))
    assert "redirect" in output["error"]
    assert len(transport.calls) == 1 and transport.calls[0][2]["allow_redirects"] is False


@pytest.mark.parametrize("code", ["api_key_required", "subscription_required", "invalid_api_key"])
@pytest.mark.parametrize("operation", ["data_catalogue", "mcp_data_catalogue"])
def test_success_status_with_access_error_body_is_an_error(manager, transport, code, operation):
    transport.payload = {"error": code, "message": "synthetic"}
    output = json.loads(registry.dispatch("fxmd_" + operation, {"currency": "eur"}, scope=manager.scope_key))
    assert code in output["error"]
    assert "FXMACRODATA_API_KEY" in output["error"] and "fxmacrodata.com/subscribe" in output["error"]
    assert "data" not in output


def test_success_status_with_unknown_error_body_does_not_echo_it(manager, transport):
    transport.payload = {"error": "https://example.invalid/?api_key=never-disclose-this"}
    result = registry.dispatch("fxmd_ping", {}, scope=manager.scope_key)
    assert "error" in json.loads(result)
    assert "never-disclose-this" not in result and "example.invalid" not in result


@pytest.mark.parametrize("payload", [[1, 2], "plain text", 7, None])
def test_unexpected_success_shapes_do_not_crash(manager, transport, payload):
    transport.payload = payload
    output = json.loads(registry.dispatch("fxmd_ping", {}, scope=manager.scope_key))
    assert output["operation"] == "ping"
    assert isinstance(output.get("records", []), list)


def test_non_json_success_body_is_a_clean_error(manager, monkeypatch):
    def request(session, *args, **kwargs):
        response = Transport().request(session, *args, **kwargs)
        response.content = b"<html>not json</html>"
        return response

    monkeypatch.setattr(requests.Session, "request", request)
    output = json.loads(registry.dispatch("fxmd_ping", {}, scope=manager.scope_key))
    assert output["error"] == "FXMacroData returned an unavailable or invalid response."


@pytest.mark.parametrize("operation", ["latest_announcements", "mcp_latest_announcements"])
def test_free_tier_window_and_delay_messages_are_surfaced(manager, transport, operation):
    transport.payload = {
        "data": [{"value": 1.0}],
        "freemium_window": {"message": "Synthetic window notice."},
        "freemium_delay": {"withheld_count": 1, "message": "Synthetic delay notice."},
    }
    output = json.loads(registry.dispatch("fxmd_" + operation, {"currency": "usd"}, scope=manager.scope_key))
    assert "error" not in output
    assert output["notices"] == ["Synthetic window notice.", "Synthetic delay notice."]


def test_no_notices_without_free_tier_fields(manager, transport):
    output = json.loads(registry.dispatch("fxmd_ping", {}, scope=manager.scope_key))
    assert "notices" not in output


@pytest.mark.parametrize("arguments", [{"currency": "us"}, {"currency": "usd1"}, {"currency": ""}])
def test_invalid_currency_codes_do_not_reach_network(manager, transport, arguments):
    output = json.loads(registry.dispatch("fxmd_data_catalogue", arguments, scope=manager.scope_key))
    assert "error" in output and not transport.calls


@pytest.mark.parametrize(
    "operation,arguments",
    [
        ("fxmd_forex", {"base": "eur", "quote": "usd", "start_date": "2026-02-30"}),
        ("fxmd_forex", {"base": "eur", "quote": "usd", "start_date": "2026-1-01"}),
        ("fxmd_forex", {"base": "eur", "quote": "usd", "start_date": "2026-03-02", "end_date": "2026-03-01"}),
        ("fxmd_forex", {"base": "euro", "quote": "usd"}),
        ("fxmd_indicator_history", {"currency": "usd", "indicator": "   "}),
        ("fxmd_mcp_forex", {"base": "eur", "quote": "usd", "end_date": "yesterday"}),
    ],
)
def test_invalid_dates_ranges_and_slugs_do_not_reach_network(manager, transport, operation, arguments):
    output = json.loads(registry.dispatch(operation, arguments, scope=manager.scope_key))
    assert "error" in output and not transport.calls


def test_valid_date_range_and_calendar_pseudo_currency_are_accepted(manager, transport):
    forex = json.loads(registry.dispatch(
        "fxmd_forex", {"base": "EUR", "quote": "usd", "start_date": "2026-01-01", "end_date": "2026-01-01"}, scope=manager.scope_key))
    calendar = json.loads(registry.dispatch("fxmd_release_calendar", {"currency": "comm"}, scope=manager.scope_key))
    assert "error" not in forex and "error" not in calendar
