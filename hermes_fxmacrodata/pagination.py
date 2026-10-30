"""Validate a version-pinned traversal without inventing pagination."""
from __future__ import annotations
import json


class PageTraversal:
    def __init__(self, limit=100, max_pages=10000):
        self.limit = limit
        self.max_pages = max_pages
        self.offset = 0
        self.version = None
        self.pages = 0
        self.fingerprints = set()
        self.done = False

    def parameters(self):
        result = {"limit": self.limit, "offset": self.offset}
        if self.version:
            result["dataset_version"] = self.version
        return result

    def advance(self, payload):
        if self.done or not isinstance(payload, dict):
            raise ValueError("Invalid page traversal state or response envelope.")
        rows = payload.get("data")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("Expected a data array of records.")
        pagination = payload.get("pagination")
        if not isinstance(pagination, dict):
            if not rows and payload.get("requested_window_has_data") is False:
                self.done = True
                return None
            raise ValueError("Missing pagination metadata; completeness is unknown.")
        has_more = pagination.get("has_more")
        if not isinstance(has_more, bool):
            raise ValueError("Missing boolean pagination.has_more.")
        if pagination.get("offset", self.offset) != self.offset:
            raise ValueError("Response offset does not match the requested page.")
        if pagination.get("returned_count", len(rows)) != len(rows):
            raise ValueError("Response row count does not match pagination metadata.")
        version = payload.get("dataset_version")
        if self.version is not None and version != self.version:
            raise ValueError("Dataset version changed or disappeared; restart the traversal.")
        if self.pages == 0 and isinstance(version, str) and version:
            self.version = version
        self.pages += 1
        if rows:
            fingerprint = json.dumps(rows, sort_keys=True, separators=(",", ":"))
            if fingerprint in self.fingerprints:
                raise ValueError("Repeated history page; refusing incomplete extraction.")
            self.fingerprints.add(fingerprint)
        if not has_more:
            self.done = True
            return None
        if self.version is None:
            raise ValueError("Multi-page history needs a dataset version pin.")
        next_offset = pagination.get("next_offset")
        if isinstance(next_offset, bool) or not isinstance(next_offset, int):
            raise ValueError("Missing integer next_offset.")
        if not rows or next_offset != self.offset + len(rows):
            raise ValueError("Pagination failed to advance contiguously.")
        if self.pages >= self.max_pages:
            raise ValueError("Page safety limit reached; extraction is incomplete.")
        self.offset = next_offset
        return self.parameters()
