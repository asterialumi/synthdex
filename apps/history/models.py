"""
Search history (purple table in the ERD).

A personal log of what each user searched. Table name comes out as
history_searchhistory, matching the ERD.
"""
from django.conf import settings
from django.db import models

from apps.search.models import SearchType


class SearchHistory(models.Model):
    """history_searchhistory: one user's personal log of searches.

    `query` is the text exactly as typed. `search_cache` links to the
    cached answer so a history entry can be reopened without an API call;
    it becomes NULL if that cache row is ever deleted.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='search_history',
    )
    search_cache = models.ForeignKey(
        'search.SearchCache',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_entries',
    )
    query = models.CharField(max_length=255)
    search_type = models.CharField(
        max_length=10,
        choices=SearchType.choices,
        default=SearchType.ALL,
    )
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}: {self.query}"
