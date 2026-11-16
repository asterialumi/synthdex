"""Helper utilities for search history."""
from .models import SearchHistory


def get_recent_distinct_searches(user, limit: int = 6) -> list[SearchHistory]:
    """Retrieve the user's latest searches, deduplicating queries in Python.

    Avoids Postgres .distinct('query') with .order_by('-searched_at') limitations.
    """
    if not user or not user.is_authenticated:
        return []

    raw_entries = (
        SearchHistory.objects.filter(user=user)
        .select_related('search_cache')
        .order_by('-searched_at')[:30]
    )

    seen: set[tuple[str, str]] = set()
    distinct_entries: list[SearchHistory] = []

    for entry in raw_entries:
        key = (entry.query.strip().lower(), entry.search_type)
        if key not in seen:
            seen.add(key)
            distinct_entries.append(entry)
            if len(distinct_entries) >= limit:
                break

    return distinct_entries
