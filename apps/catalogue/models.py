"""
Music catalogue models (the core of the SynthDex ERD, blue tables).

This slice owns the music data itself: artists, albums, tracks, genres,
and the two junction tables that connect tracks to artists and genres.
Other slices (sources, search, favorites) point at Track from their own
models, so this app depends on none of them.

Table names come out as catalogue_<model>, matching the ERD.
"""
from django.db import models
from django.utils import timezone


class ArtistRole(models.TextChoices):
    PRIMARY = 'primary', 'Primary'
    FEATURED = 'featured', 'Featured'
    COMPOSER = 'composer', 'Composer'
    PRODUCER = 'producer', 'Producer'


class Artist(models.Model):
    """catalogue_artist: one row per musician or band."""

    name = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name


class Album(models.Model):
    """catalogue_album: one row per album. Each album has one main artist."""

    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='albums',
    )
    title = models.CharField(max_length=255)
    release_date = models.DateField(null=True, blank=True)
    artwork_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.title


class Track(models.Model):
    """catalogue_track: one row per song, the centre of the diagram.

    Favorites, cached search results, credits, genres and source links
    all point at this table.
    """

    # NULL for singles, or when the source (e.g. YouTube) has no album.
    # Deleting an album keeps its tracks and just clears this link.
    album = models.ForeignKey(
        Album,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tracks',
    )
    title = models.CharField(max_length=255)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    bpm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    release_year = models.PositiveSmallIntegerField(null=True, blank=True)
    # unique + null: any number of tracks may have NO isrc (NULL), but two
    # tracks can never share one. Always store None, never '', for
    # "unknown": several NULLs are allowed under a unique rule, several
    # empty strings are not.
    isrc = models.CharField(max_length=12, unique=True, null=True, blank=True)
    artwork_url = models.URLField(max_length=500, null=True, blank=True)
    # When any API response last touched this row. Set by our code, so it
    # is a default and not auto_now (which would also change on manual edits).
    last_fetched_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class Genre(models.Model):
    """catalogue_genre: each genre name is stored once."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class TrackArtist(models.Model):
    """catalogue_trackartist: junction between tracks and artists.

    `role` says what the artist did on the track (primary, featured, ...).
    """

    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        related_name='credits',
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='credits',
    )
    role = models.CharField(
        max_length=20,
        choices=ArtistRole.choices,
        default=ArtistRole.PRIMARY,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['track', 'artist', 'role'],
                name='uniq_trackartist_track_artist_role',
            ),
        ]

    def __str__(self):
        return f"{self.artist} ({self.role}) on {self.track}"


class TrackGenre(models.Model):
    """catalogue_trackgenre: junction between tracks and genres."""

    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        related_name='track_genres',
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        related_name='track_genres',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['track', 'genre'],
                name='uniq_trackgenre_track_genre',
            ),
        ]

    def __str__(self):
        return f"{self.track} - {self.genre}"
