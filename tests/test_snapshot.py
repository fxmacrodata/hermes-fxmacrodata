"""Owned plugin handlers with fixture queries; no Hermes host or API execution."""
import copy
import pytest
from hermes_fxmacrodata import plugin


def payload(offset, version="fixture-version", more=False):
    return {"dataset_version": version, "data": [{"announcement_id": f"fixture-{offset}", "date": "2020-01-01", "val": None,
            "publication_time_status": "unknown", "source_url": "https://example.org/fixture"}],
            "pagination": {"offset": offset, "returned_count": 1, "has_more": more, "next_offset": offset + 1 if more else None}}


def test_native_snapshot_pins_and_preserves_all_metadata(monkeypatch):
    calls = []
    def query(name, args, timeout):
        calls.append(copy.deepcopy(args))
        return {"data": payload(args["offset"], more=args["offset"] == 0)}
    monkeypatch.setattr(plugin, "query", query)
    result = plugin.history_snapshot({"currency": "USD", "indicator": "policy_rate"})
    assert len(result["data"]["data"]) == 2
    assert calls[1]["dataset_version"] == "fixture-version"
    assert result["data"]["snapshot"]["complete"] is True
    assert result["data"]["data"][0]["publication_time_status"] == "unknown"
    assert any(item["url"] == "https://example.org/fixture" for item in result["citations"])


@pytest.mark.parametrize("failure", ["changed", "error", "missing"])
def test_partial_or_changed_snapshot_never_claims_complete(monkeypatch, failure):
    def query(name, args, timeout):
        if not args["offset"]:
            return {"data": payload(0, more=True)}
        if failure == "error":
            return {"error": "Fixture denial"}
        return {"data": payload(1, version="changed" if failure == "changed" else None)}
    monkeypatch.setattr(plugin, "query", query)
    result = plugin.history_snapshot({"currency": "USD", "indicator": "policy_rate"})
    assert "error" in result and "data" not in result


def test_brief_scope_means_section_success_not_full_history(monkeypatch):
    monkeypatch.setattr(plugin, "query", lambda *args: {"data": {"data": []}})
    result = plugin.usd_brief({})
    assert result["complete"] is True
    assert result["scope"]["history_complete"] is False
    assert result["scope"]["history_limit"] == 10
