---
name: fxmacrodata-macro-research
description: Research macroeconomic releases, indicator history and calendars with FXMacroData's native tools and source citations.
---

Use `fxmd_data_catalogue` to discover supported currency/indicator combinations. Public USD discovery, history and calendar work without a key. For a first USD brief, call `fxmd_usd_macro_brief`, then query individual tools for any additional detail or pagination.

Preserve the public response's timestamps, units, source links and availability indicators. Cite the returned `source_url` and the publisher links present in the records. Do not infer future release times from a recurring cadence or treat a schedule as an observed publication. Distinguish market consensus, official forecasts and FXMacroData-generated predictions.

Every REST operation and hosted MCP tool has an `fxmd_` tool. Use its native input schema; never supply credentials as tool arguments. Empty results are unavailable for the selected window. A partial brief must retain failed sections rather than silently removing them. Streaming tools return a bounded capture, not an ongoing subscription. MCP resource content is available as structured results; interactive Apps are not rendered.

Provider and documentation: https://fxmacrodata.com/documentation/reference
