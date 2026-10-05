"""Public FXMacroData REST and MCP client used by the Hermes plugin.

Vendored from fxmacrodata-public-client 0.1.0 (MIT, https://github.com/fxmacrodata/fxmacrodata-public-client)
so the plugin installs from PyPI dependencies only. Local changes: credentials travel in request
headers instead of query strings, FXMACRODATA_API_KEY is the only environment variable read, keys are
trimmed and checked for header-safe characters, redirects get an explicit error, and currencies,
dates and slugs are validated before any request.
"""
from .client import FXMacroDataClient, FXMacroDataError, Operation, Result, list_operations

__all__ = ["FXMacroDataClient", "FXMacroDataError", "Operation", "Result", "list_operations"]
