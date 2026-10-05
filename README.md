# FXMacroData for Hermes

Bring your FXMacroData subscription into Hermes for cross-currency macro research, full available indicator histories and release-calendar analysis. Native research tools keep source citations attached to the data in your conversations.

**[Subscribe to FXMacroData](https://fxmacrodata.com/subscribe?utm_source=github&utm_medium=referral&utm_campaign=hermes-fxmacrodata&utm_content=subscribe)** for access to non-USD datasets, FX rates, commodities, positioning and full available history.

You can evaluate the plugin before subscribing. Without a key, the REST tools serve the data catalogue for every currency, the USD release calendar and the most recent 90 days of USD announcements on a 15-minute delay, with a fair-use limit of 100 requests a day. Through the hosted MCP tools, USD releases, the USD calendar and the USD catalogue work without a key; other currencies, FX rates and the rest need a key.

The full inventory contains 23 public REST operations and 49 hosted MCP tools, plus a `/fxmacrodata` USD macro brief command. Every operation has its own native tool and original input schema. See [the operation matrix](CAPABILITIES.md).

## Install

```bash
hermes plugins install fxmacrodata/hermes-fxmacrodata
hermes plugins enable fxmacrodata
```

Hermes installs the plugin's PyPI dependencies (`requests`, `urllib3`, `jsonschema`, `referencing`) with bounded version ranges. The FXMacroData client ships inside the plugin, so nothing is downloaded from outside PyPI.

Restart Hermes after enabling the plugin. Ask: "Use FXMacroData to discover USD indicators, inspect policy-rate history, and show the upcoming release calendar with source citations." Or enter `/fxmacrodata policy_rate`.

You can also install the package into the Python environment Hermes runs in (`uv pip install .`) and enable it through its `hermes_agent.plugins` entry point. Validate a checkout with `hermes plugins validate /path/to/hermes-fxmacrodata --install-deps`.

## Connect your subscription

Set `FXMACRODATA_API_KEY` in the process environment or a configured Hermes secret source. It is the only credential the plugin reads, and it is optional. Do not place keys in prompts, tool arguments, plugin settings, shared files or command history.

The key is read when a call starts, trimmed, and refused (without being repeated) if it contains spaces or control characters. REST calls send it as an `X-API-Key` header and MCP calls as an `Authorization: Bearer` header; it never appears in a URL. Redirects are never followed, so the key cannot be forwarded to another host. Each call closes its own HTTP/MCP session.

The only plugin setting is `plugins.entries.fxmacrodata.settings.timeout_seconds` (default 30, clamped to 1-120 seconds).

## Network, files and processes

- Tool calls make HTTPS requests to `api.fxmacrodata.com` (REST) and `mcp.fxmacrodata.com` (hosted MCP) only, carrying the tool arguments and, when set, your `FXMACRODATA_API_KEY`. Nothing else is contacted.
- Registering the tools makes no network calls. The tool list is packaged with the plugin; it is not fetched at runtime and the plugin never updates itself.
- The plugin writes no files, runs no shell commands, starts no background processes and stores no credentials. `fxmd_stream_events` captures a finite number of events within a finite timeout and then closes.
- No telemetry or usage reporting. Static campaign tags appear only on fxmacrodata.com website links in tool output.

## Results and research

Tool results contain the original response in `data`, an additive `records` view, the operation name and source citations. Pagination and date filters keep their public API meanings: list endpoints return 20 rows by default, and calendar `date` is the reference period while `announcement_datetime` is the release time.

Keyless responses can carry free-tier window and delay messages. The plugin copies them into a `notices` list so the agent can say that data is delayed or limited instead of presenting it as current. A successful HTTP status whose body is an error (for example `api_key_required`) is reported as an error with the subscribe link. Currency codes, YYYY-MM-DD dates, date ranges and indicator slugs are validated before any request is made.

`fxmd_usd_macro_brief` composes catalogue discovery, recent history and the release calendar. Failed sections remain explicit and `complete` is false; empty records are unavailable data. Keep observed releases, scheduled events, market consensus and FXMacroData-generated predictions distinct. MCP text, structured content and resource links are preserved; interactive MCP Apps are not rendered by this plugin.

[FXMacroData](https://fxmacrodata.com/?utm_source=github&utm_medium=referral&utm_campaign=hermes-fxmacrodata&utm_content=readme) · [Public API reference](https://fxmacrodata.com/documentation/reference?utm_source=github&utm_medium=referral&utm_campaign=hermes-fxmacrodata&utm_content=docs)
