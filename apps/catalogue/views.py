"""Views for music catalogue and track detail presentation."""
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.favorites.models import Favorite
from apps.sources.deezer import enrich_track_from_deezer
from .models import Track

logger = logging.getLogger(__name__)


@login_required(login_url='login:login')
def track_detail_view(request, track_id: int):
    """Present track details with external listen links and perform safe Deezer enrichment."""
    track = get_object_or_404(
        Track.objects.select_related('album', 'album__artist').prefetch_related(
            'credits__artist',
            'track_genres__genre',
            'track_sources__source',
        ),
        pk=track_id,
    )

    # Attempt Deezer metadata enrichment if Deezer source link is not yet attached
    has_deezer = any(ts.source.name == 'deezer' for ts in track.track_sources.all())
    if not has_deezer:
        try:
            enriched = enrich_track_from_deezer(track)
            if enriched:
                # Reload track with fresh relations after enrichment
                track = (
                    Track.objects.select_related('album', 'album__artist')
                    .prefetch_related(
                        'credits__artist',
                        'track_genres__genre',
                        'track_sources__source',
                    )
                    .get(pk=track_id)
                )
        except Exception as exc:
            logger.warning("Deezer enrichment failed gracefully for track %s: %s", track_id, exc)

    # Separate primary and featured artists for clean display
    credits = list(track.credits.all())
    primary_artists = [c for c in credits if c.role == 'primary']
    featured_artists = [c for c in credits if c.role == 'featured']
    other_credits = [c for c in credits if c.role not in ('primary', 'featured')]

    # Distinct genres
    genres = [tg.genre for tg in track.track_genres.all()]

    # Source links
    sources = list(track.track_sources.all())

    # Check if user has saved this track as favorite
    is_favorite = Favorite.objects.filter(user=request.user, track=track).exists() if request.user.is_authenticated else False

    return render(request, 'catalogue/track_detail.html', {
        'track': track,
        'primary_artists': primary_artists,
        'featured_artists': featured_artists,
        'other_credits': other_credits,
        'genres': genres,
        'sources': sources,
        'is_favorite': is_favorite,
    })
