"""Every packaged owned REST/MCP route with synthetic HTTP protocol fixtures."""
import requests
import pytest
from hermes_fxmacrodata.public_client import FXMacroDataClient, list_operations
from transport_fixtures import Transport, arguments


@pytest.mark.parametrize("operation", list_operations(), ids=lambda operation: operation.name)
def test_every_public_route_preserves_nulls_and_header_auth(monkeypatch, operation):
    transport = Transport()
    monkeypatch.setattr(requests.Session, "request", lambda session, method, url, **kwargs: transport.request(session, method, url, **kwargs))
    with FXMacroDataClient(api_key="fixture-key") as client:
        result = client.execute(operation.name, arguments(operation))
    assert result.payload is not None
    assert transport.calls
    for method, url, kwargs in transport.calls:
        assert "api_key" not in (kwargs.get("params") or {})
        if url.startswith("https://mcp."):
            assert kwargs["headers"]["Authorization"] == "Bearer fixture-key"
            assert "X-API-Key" not in kwargs["headers"]
        else:
            assert kwargs["headers"]["X-API-Key"] == "fixture-key"
            assert "Authorization" not in kwargs["headers"]
        assert kwargs["allow_redirects"] is False


def test_lowercase_rest_currency_codes_preserve_compatibility(monkeypatch):
    transport = Transport()
    monkeypatch.setattr(requests.Session, "request", lambda session, method, url, **kwargs: transport.request(session, method, url, **kwargs))
    with FXMacroDataClient() as client:
        client.execute("indicator_history", {"currency":"usd", "indicator":"policy_rate"})
    assert transport.calls[0][1].endswith("/announcements/USD/policy_rate")
