"""
External sources (the "where to listen" part of the ERD, blue tables).

This slice owns the list of providers we pull from (YouTube, Deezer, ...)
and the link between a track and each provider. The API client code for
each provider will live in this app later.

Table names come out as sources_<model>, matching the ERD.
"""
from django.db import models
from django.utils import timezone


class LinkType(models.TextChoices):
    LISTEN = 'listen', 'Listen'
    PURCHASE = 'purchase', 'Purchase'
    ARTIST_PAGE = 'artist_page', 'Artist page'


class MusicSource(models.Model):
    """sources_musicsource: the providers we pull from (YouTube, Deezer, ...)."""

    name = models.CharField(max_length=50, unique=True)
    base_url = models.URLField(max_length=200)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TrackSource(models.Model):
    """sources_tracksource: "this track is on this provider at this link".

    Junction between tracks and music sources, carrying the provider's
    own id and the link a user clicks.
    """

    track = models.ForeignKey(
        'catalogue.Track',
        on_delete=models.CASCADE,
        related_name='track_sources',
    )
    source = models.ForeignKey(
        MusicSource,
        on_delete=models.CASCADE,
        related_name='track_sources',
    )
    external_id = models.CharField(max_length=100)
    url = models.URLField(max_length=500)
    link_type = models.CharField(
        max_length=20,
        choices=LinkType.choices,
        default=LinkType.LISTEN,
    )
    fetched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['track', 'source', 'link_type'],
                name='uniq_tracksource_track_source_linktype',
            ),
        ]

    def __str__(self):
        return f"{self.track} on {self.source} ({self.link_type})"
