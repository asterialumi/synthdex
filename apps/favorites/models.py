"""
Favorites (purple table in the ERD).

Lets a user save tracks for later. Table name comes out as
favorites_favorite, matching the ERD.
"""
from django.conf import settings
from django.db import models


class Favorite(models.Model):
    """favorites_favorite: "this user saved this track".

    Junction between users and tracks. Deleting a user removes their
    favorites, but never the shared track.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    track = models.ForeignKey(
        'catalogue.Track',
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'track'],
                name='uniq_favorite_user_track',
            ),
        ]

    def __str__(self):
        return f"{self.user} likes {self.track}"
