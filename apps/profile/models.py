from django.conf import settings
from django.db import models


class Profile(models.Model):
    """A listener's public-facing profile.

    Kept intentionally small for now (display name, favorite genre, a
    short bio). Future catalogue features like favorites and search
    history belong in their own vertical slices, not here.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    display_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Shown instead of your username around the site. Leave blank to just use your username.",
    )
    favorite_genre = models.CharField(max_length=100, blank=True)
    bio = models.TextField(
        max_length=280,
        blank=True,
        help_text="A short note about your taste in music.",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name or self.user.username

    @property
    def display(self):
        """Convenience accessor for templates: falls back to username."""
        return self.display_name or self.user.username
