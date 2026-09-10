# FXMacroData for Hermes

Bring your FXMacroData subscription into Hermes for cross-currency macro research, full available indicator histories and release-calendar analysis. Native research tools keep source citations attached to the data in your conversations.

**[Subscribe to FXMacroData](https://fxmacrodata.com/subscribe?utm_source=github&utm_medium=referral&utm_campaign=open_source_integrations&utm_content=hermes_subscribe)** for access to covered non-USD datasets and full available history.

Evaluate the plugin before subscribing with public USD catalogue, recent indicator history and release-calendar access, which require no API key or account.

The full inventory contains 23 public REST operations and 49 hosted MCP tools, plus a `/fxmacrodata` USD macro brief command. Every operation has its own native tool and original input schema. Connect your subscription through your own process credentials. See [the operation matrix](CAPABILITIES.md).

## Install

Install the wheel into the same Python environment as Hermes, then enable its native entry point:

```bash
uv pip install ./hermes_fxmacrodata-0.1.0-py3-none-any.whl
hermes plugins enable fxmacrodata
hermes plugins list
```

Installation downloads the shared public client from a SHA-256-pinned GitHub release. You can also run `uv pip install .` from the extracted source package.

Restart Hermes after enabling the plugin. Ask: “Use FXMacroData to discover USD indicators, inspect policy-rate history, and show the upcoming release calendar with source citations.” Or enter `/fxmacrodata policy_rate`.

For a directory-plugin installation, place the extracted plugin directory beneath your Hermes plugins directory, install its Python package in Hermes' environment, then enable `fxmacrodata`. The supplied `plugin.yaml`, `register(ctx)` entry point and bundled skill support the native directory discovery path. Plugin Doctor can validate the extracted directory with `hermes plugins doctor /path/to/hermes-fxmacrodata --ci`.

## Connect your subscription

Provide `FXMACRODATA_API_KEY` or `FXMD_API_KEY` through the process environment or a configured Hermes secret source. Do not place keys in prompts, tool arguments, plugin settings, shared files or command history. Credentials are read when a call starts; each call closes its own HTTP/MCP session.

The only plugin setting is `plugins.entries.fxmacrodata.settings.timeout_seconds` (default 30, clamped by the client to 1–120 seconds). Public USD calls work when both credential variables are absent. Other datasets report an actionable access error when authorization is needed.

## Results and research

Tool results contain the original response in `data`, an additive `records` view, the operation name and source citations. Pagination and date filters retain their public API meanings. `fxmd_stream_events` captures a finite number of events within a finite timeout; it does not start a background watcher.

`fxmd_usd_macro_brief` composes catalogue discovery, recent history and the release calendar. Failed sections remain explicit and `complete` is false; empty records are unavailable data. Keep observed releases, scheduled events, market consensus and FXMacroData-generated predictions distinct. MCP text, structured content and resource links are preserved; interactive MCP Apps are not rendered by this plugin.

Native tool registration uses no network calls and no credentials. Responses are sanitized before their JSON text is projected into records or sent to Hermes. The plugin emits no telemetry; static campaign tags appear only on website links.

[FXMacroData](https://fxmacrodata.com/?utm_source=github&utm_medium=referral&utm_campaign=open_source_integrations&utm_content=hermes_readme) · [Public API reference](https://fxmacrodata.com/documentation/reference?utm_source=github&utm_medium=referral&utm_campaign=open_source_integrations&utm_content=hermes_docs)
