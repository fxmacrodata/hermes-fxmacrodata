# FXMacroData for Hermes

Research a macro question with source-backed data in Hermes: discover the indicator, inspect its history, check the release schedule and carry the evidence into your answer.

## Install and first research workflow

Use Hermes 0.22.5 or newer. The official plugin catalogue points to the FXMacroData-owned plugin.

```bash
hermes plugins install fxmacrodata/hermes-fxmacrodata
hermes plugins enable fxmacrodata
```

Restart Hermes, then ask: “Use FXMacroData to discover USD indicators, inspect policy-rate history and show the upcoming calendar with sources.” `/fxmacrodata policy_rate` builds the native USD brief. This baseline needs no key, account or card.

There are 100 registered tools: 41 REST operations, 57 hosted MCP tools, a USD brief and a version-pinned history snapshot. Original input schemas, source URLs and response envelopes remain available. [OPERATIONS.json](OPERATIONS.json) lists every tool; [CAPABILITIES.md](CAPABILITIES.md) lists the native contract coverage.

## A useful research sequence

1. Call `fxmd_data_catalogue` with `{"currency":"USD"}` and choose a real indicator slug.
2. Call `fxmd_indicator_history_snapshot` with the currency, slug and a YYYY-MM-DD date window when you need all authorised pages. Ordinary `fxmd_indicator_history` is a page query.
3. Call `fxmd_release_calendar` with explicit release dates and `timezone:"UTC"` for a scheduled window.
4. Use predictions, news, FX, sessions, positioning, commodities or seasonality tools for the question you are investigating; keep their data classes and source labels distinct.

The snapshot buffers the entire requested window before returning. It pins the first `dataset_version` on continuation, validates contiguous offsets and row counts and refuses repeated pages, missing metadata, version changes or partial failures. Its `complete` flag applies to the requested authorised window, not all history ever published. The safety ceiling is 10,000 pages.

The brief deliberately requests 10 history rows plus a UTC calendar window from today through seven days ahead. Its `complete` flag means that its three sections succeeded; `scope.history_complete` is false. Empty sections remain empty and failed sections are explicit.

## Connect protected scope

Configure the optional API key through the native plugin settings secret field. Hermes supplies it as the profile-scoped `FXMACRODATA_API_KEY` secret. Never put it in a prompt, tool argument or shared file. REST sends `X-API-Key`; MCP sends Bearer authentication. Redirects are refused and each call closes its session. The timeout setting defaults to 30 seconds and is bounded to 1–120 seconds.

Only `api.fxmacrodata.com` and `mcp.fxmacrodata.com` are contacted for tool calls. Registration performs no network call. The plugin stores no keys, writes no files, starts no background processes and adds no telemetry. Its SSE tool collects a bounded event snapshot, then closes.

## Dates, values and evidence

`date` is an observation/reference period, not proof that the figure was public then. Preserve `announcement_date`, `announcement_datetime`, `time_announced`, `publication_time_status`, `release_time_assumed`, `capture_time_basis`, collection clocks, source links and revisions together. A confirmed publisher time is different from an official future schedule or a collection timestamp. If `time_announced` is false, the calendar provides a date without a confirmed clock. Unknown or assumed times cannot establish an exact historical availability cutoff. Null values stay null. Prediction classes, publisher forecasts, consensus and FXMacroData calculations retain their labels.

Public USD catalogue, history and calendar work without a key, account or card. Returned notices describe the authorised window and any delay. Protected non-USD, FX, COT, commodity and other scope depends on the endpoint and your subscription; an API key is not a guarantee that every dataset exists. See the [API reference](https://fxmacrodata.com/documentation/reference?utm_source=hermes&utm_medium=integration&utm_campaign=hermes-fxmacrodata&utm_content=readme) and [access plans](https://fxmacrodata.com/subscribe?utm_source=hermes&utm_medium=integration&utm_campaign=hermes-fxmacrodata&utm_content=readme).

## Results and troubleshooting

`data` preserves the original result, `records` is an additive projection, and `citations` includes provider and original publisher URLs when present. Free-access notices remain visible. MCP structured content, resource links and artifacts remain in the response; Hermes does not render interactive MCP Apps through this plugin.

If tools do not appear, check the host minimum, enable the plugin and restart Hermes. If a result reports access denied, check the secret and requested scope. If a snapshot fails, rerun its entire window rather than joining different versions. A successful HTTP response with an error body is still a tool error. Do not interpret unknown or assumed release times as confirmed publication.

[Official catalogue](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/fxmacrodata.yaml?utm_source=hermes&utm_medium=integration&utm_campaign=hermes-fxmacrodata&utm_content=readme) · [Source](https://github.com/fxmacrodata/hermes-fxmacrodata?utm_source=hermes&utm_medium=integration&utm_campaign=hermes-fxmacrodata&utm_content=readme) · [API reference](https://fxmacrodata.com/documentation/reference?utm_source=hermes&utm_medium=integration&utm_campaign=hermes-fxmacrodata&utm_content=readme)

MIT covers the adapter and its packaged FXMacroData-owned public client. FXMacroData brand references identify the provider without granting trademark rights.

## Profile-scoped optional credential

Configure the optional API key in the native plugin settings secret field. The plugin reads `FXMACRODATA_API_KEY` through `agent.secret_scope.get_secret`, so profile multiplexing cannot silently use another profile's process key. It does not read environment files, auth files, keychains or a browser login. If the host secret API is unavailable, public no-key access remains available and no process-environment credential fallback is used. The public client receives this value explicitly.

Version 0.3.0 exposes the current public contract inventory, including read-only research-panel POST, and preserves version-pinned history traversal. Research inputs, including user-entered FX positions, are sent to the fixed FXMacroData services. Public USD access needs no account or payment; protected datasets depend on your FXMacroData entitlement, and host/model charges are separate. Official native validation and profile-isolation checks passed on Hermes 0.22.5 and the current development version. The reviewed public catalogue pin may lag the source release.

The refresh targets Hermes 0.22.5 or later for the native optional secret configuration and profile-aware secret API. Earlier Hermes releases are not certified by this update.
