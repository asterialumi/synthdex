"""Views for music catalogue and track detail presentation."""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.favorites.models import Favorite
from apps.sources.deezer import enrich_track_from_deezer
from .forms import TrackMetadataForm
from .models import Genre, Track, TrackGenre

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

    # Pre-populate manual edit form
    genre_names_str = ", ".join(g.name for g in genres)
    metadata_form = TrackMetadataForm(initial={
        'bpm': track.bpm,
        'genres': genre_names_str,
    })

    return render(request, 'catalogue/track_detail.html', {
        'track': track,
        'primary_artists': primary_artists,
        'featured_artists': featured_artists,
        'other_credits': other_credits,
        'genres': genres,
        'sources': sources,
        'is_favorite': is_favorite,
        'metadata_form': metadata_form,
    })


@login_required(login_url='login:login')
@require_POST
def edit_track_metadata_view(request, track_id: int):
    """Manually update track BPM and genres."""
    track = get_object_or_404(Track, pk=track_id)
    form = TrackMetadataForm(request.POST)

    if form.is_valid():
        new_bpm = form.cleaned_data.get('bpm')
        track.bpm = new_bpm
        track.save(update_fields=['bpm'])

        raw_genres = form.cleaned_data.get('genres', '')
        new_genre_names = [
            g.strip() for g in raw_genres.split(',')
            if g.strip()
        ]

        # Sync genres without touching existing schema
        current_track_genres = list(TrackGenre.objects.filter(track=track).select_related('genre'))
        current_map = {tg.genre.name.lower(): tg for tg in current_track_genres}
        new_set = {g.lower() for g in new_genre_names}

        # Remove deleted genres
        for low_name, tg in current_map.items():
            if low_name not in new_set:
                tg.delete()

        # Add newly entered genres
        for g_name in new_genre_names:
            if g_name.lower() not in current_map:
                genre_obj, _ = Genre.objects.get_or_create(name=g_name[:100])
                TrackGenre.objects.get_or_create(track=track, genre=genre_obj)

        messages.success(request, f'Updated BPM and genres for "{track.title}".')
    else:
        for err_list in form.errors.values():
            for err in err_list:
                messages.error(request, err)

    return redirect('catalogue:track_detail', track_id=track.id)
