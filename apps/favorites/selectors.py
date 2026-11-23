"""Database selectors for user favorites and credited artists.

Encapsulates the JOIN and SUBQUERY queries using Django ORM.
"""
from django.db.models import Prefetch, Subquery

from apps.catalogue.models import Artist, TrackArtist
from .models import Favorite


def get_favorites_with_details(user):
    """JOIN: a user's favorites together with each track and its album.

    select_related makes Django fetch the track and album in the SAME query:
      favorites_favorite INNER JOIN catalogue_track
                         LEFT OUTER JOIN catalogue_album
    INNER for the track because every favorite has one; LEFT OUTER for the
    album because Track.album can be NULL (e.g. a YouTube-only song).
    Artist names are loaded by the prefetch below, which is separate
    queries and not part of the JOIN.
    """
    return (
        Favorite.objects
        .filter(user=user)
        .select_related('track', 'track__album')
        .prefetch_related(
            Prefetch('track__credits', queryset=TrackArtist.objects.order_by('id')),
            'track__credits__artist',
        )
        .order_by('-created_at', '-id')
    )


def get_favorite_artists(user):
    """SUBQUERY: artists credited on any track this user has favorited.

    inner  : track ids the user favorited          (favorites_favorite)
    middle : artist ids credited on those tracks   (catalogue_trackartist)
    outer  : the artist records                    (catalogue_artist)
    IN never repeats a row, so an artist with several favorited songs
    appears once.
    """
    favorite_track_ids = Favorite.objects.filter(user=user).values('track_id')
    credited_artist_ids = TrackArtist.objects.filter(
        track_id__in=Subquery(favorite_track_ids)
    ).values('artist_id')
    return Artist.objects.filter(id__in=Subquery(credited_artist_ids)).order_by('name', 'id')


def sql_of(queryset):
    """The SQL Django will run for a queryset (display only; does not execute it)."""
    try:
        return str(queryset.query)
    except Exception as exc:  # e.g. EmptyResultSet
        return f'(SQL unavailable: {exc})'
