from django.conf import settings
from django.db import models


class UserSettings(models.Model):
    """Per-user app preferences.

    Starts with a theme preference and a preferred search type. More
    toggles (notifications, default search source, etc.) can be added
    here later without touching any other feature.
    """

    # Same values as SearchType in apps/search/models.py. Kept as a
    # small local copy so this feature slice does not import from search.
    class SearchType(models.TextChoices):
        ALL = 'all', 'All'
        SONG = 'song', 'Song'
        ARTIST = 'artist', 'Artist'
        ALBUM = 'album', 'Album'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings',
    )
    dark_mode = models.BooleanField(default=False)
    pref_search_type = models.CharField(
        max_length=10,
        choices=SearchType.choices,
        default=SearchType.ALL,
    )

    def __str__(self):
        return f"Settings for {self.user.username}"
