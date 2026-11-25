"""Views for the home dashboard feature."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.favorites.selectors import get_favorites_with_details
from apps.history.utils import get_recent_distinct_searches
from apps.search.models import SearchType
from apps.user_settings.models import UserSettings


def _compute_ring_duration(tracks, base_default: int) -> int:
    """Calculate orbit duration in seconds based on average BPM, clamped to [30, 120]."""
    bpms = [float(item.track.bpm) for item in tracks if item.track.bpm is not None]
    if not bpms:
        return base_default
    avg_bpm = sum(bpms) / len(bpms)
    if avg_bpm <= 0:
        return base_default
    speed = round(base_default * (120.0 / avg_bpm))
    return max(30, min(120, speed))


@login_required(login_url='login:login')
def home_view(request):
    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)

    # Reuse get_favorites_with_details up to 12 favorites (read-only)
    # Preload track_sources for the 4 latest favorites cards in 1 batch query
    favorites_qs = (
        get_favorites_with_details(request.user)
        .prefetch_related('track__track_sources__source')[:12]
    )
    favorites = list(favorites_qs)
    latest_favorites = favorites[:4]

    # Partition favorites into 3 concentric rings (up to 4 per ring, newest on inner ring)
    # Ring 1: favorites[0:4], Ring 2: favorites[4:8], Ring 3: favorites[8:12]
    ring_slices = [
        (1, favorites[0:4], 45),
        (2, favorites[4:8], 70),
        (3, favorites[8:12], 95),
    ]

    orbit_rings = []
    slot_angles = [0, 90, 180, 270]

    for ring_num, ring_tracks, base_speed in ring_slices:
        duration = _compute_ring_duration(ring_tracks, base_speed)
        planets = []
        for idx, fav in enumerate(ring_tracks):
            angle = slot_angles[idx % len(slot_angles)]
            planets.append({
                'fav': fav,
                'angle': angle,
                'slot_index': idx,
            })
        orbit_rings.append({
            'ring_num': ring_num,
            'duration': duration,
            'planets': planets,
            'has_planets': len(planets) > 0,
        })

    recent_searches = get_recent_distinct_searches(request.user, limit=6)

    return render(request, 'home/home.html', {
        'search_types': SearchType.choices,
        'pref_search_type': user_settings.pref_search_type,
        'latest_favorites': latest_favorites,
        'recent_searches': recent_searches,
        'orbit_rings': orbit_rings,
        'total_favorites': len(favorites),
    })
