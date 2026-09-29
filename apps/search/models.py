"""
Music search cache (orange tables in the ERD).

This slice remembers which searches were already answered, and which
tracks came back, so a repeated search doesn't call the API again.

Table names come out as search_<model>, matching the ERD.
"""
from django.db import models
from django.utils import timezone


class SearchType(models.TextChoices):
    ALL = 'all', 'All'
    SONG = 'song', 'Song'
    ARTIST = 'artist', 'Artist'
    ALBUM = 'album', 'Album'


class SearchCache(models.Model):
    """search_searchcache: remembers that a search was already answered.

    `query_normalized` is the search text lowercased and trimmed, so
    "Get Lucky " and "get lucky" share one row.
    """

    query_normalized = models.CharField(max_length=255)
    search_type = models.CharField(
        max_length=10,
        choices=SearchType.choices,
        default=SearchType.ALL,
    )
    result_count = models.PositiveIntegerField(default=0)
    fetched_at = models.DateTimeField(default=timezone.now)
    # After this moment the entry is stale and the API is called again.
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['query_normalized', 'search_type'],
                name='uniq_searchcache_query_type',
            ),
        ]

    def __str__(self):
        return f"{self.query_normalized} ({self.search_type})"


class SearchCacheResult(models.Model):
    """search_searchcacheresult: which tracks a cached search returned.

    Junction between cached searches and tracks. `result_order` keeps
    the API's ranking (1 = first).
    """

    track = models.ForeignKey(
        'catalogue.Track',
        on_delete=models.CASCADE,
        related_name='cache_results',
    )
    search_cache = models.ForeignKey(
        SearchCache,
        on_delete=models.CASCADE,
        related_name='results',
    )
    result_order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['search_cache', 'track'],
                name='uniq_searchcacheresult_cache_track',
            ),
        ]

    def __str__(self):
        return f"#{self.result_order} {self.track} for {self.search_cache}"
