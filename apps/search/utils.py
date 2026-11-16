"""Utility functions for search queries."""


def normalize_query(query: str) -> str:
    """Normalize user search query: strip, collapse whitespace, lowercase, truncate to 255 chars."""
    if not query or not isinstance(query, str):
        return ""
    collapsed = " ".join(query.strip().split())
    return collapsed.lower()[:255]
