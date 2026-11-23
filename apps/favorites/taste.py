"""Taste summary computations based on a user's favorited tracks.

Computes aggregate BPM metrics, top genres, and coverage metadata
using at most 3 targeted, read-only SQL queries.
"""
from decimal import Decimal
from django.db.models import Avg, Count, Exists, Max, Min, OuterRef, Q

from apps.catalogue.models import TrackGenre
from apps.favorites.models import Favorite


def format_bpm(value):
    """Format BPM without trailing zeros.

    Examples:
        205.00 -> "205"
        128.50 -> "128.5"
        None   -> None
    """
    if value is None:
        return None
    try:
        val_float = float(value)
        if val_float.is_integer():
            return str(int(val_float))
        return f"{val_float:.2f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(value)


def get_taste_summary(user, declared_genre=''):
    """Read-only summary of a user's favorites (max 3 queries).

    Parameters:
        user: Authenticated User model instance.
        declared_genre: Optional string containing user's self-declared favorite genre.

    Returns:
        Dictionary with aggregate stats, formatted strings, top genres,
        and tracks missing details.
    """
    if not user or not user.is_authenticated:
        return _empty_taste_summary(declared_genre)

    # --------------------------------------------------------------------------
    # Query 1: Aggregate over the user's favorited tracks.
    # Exists subquery detects whether each track has at least one genre without
    # joining TrackGenre into the FROM clause, preventing duplicate track rows
    # from skewing the BPM average.
    # --------------------------------------------------------------------------
    has_genre_subquery = Exists(
        TrackGenre.objects.filter(track=OuterRef('track_id'))
    )

    agg = (
        Favorite.objects.filter(user=user)
        .annotate(has_genre=has_genre_subquery)
        .aggregate(
            total=Count('id'),
            with_bpm=Count('track__bpm'),
            with_genre=Count('id', filter=Q(has_genre=True)),
            avg_bpm=Avg('track__bpm'),
            min_bpm=Min('track__bpm'),
            max_bpm=Max('track__bpm'),
        )
    )

    total = agg.get('total') or 0
    if total == 0:
        return _empty_taste_summary(declared_genre)

    with_bpm = agg.get('with_bpm') or 0
    with_genre = agg.get('with_genre') or 0
    avg_bpm = agg.get('avg_bpm')
    min_bpm = agg.get('min_bpm')
    max_bpm = agg.get('max_bpm')

    # Round average BPM to whole number if present
    avg_bpm_rounded = round(avg_bpm) if avg_bpm is not None else None

    # --------------------------------------------------------------------------
    # Query 2: Top 3 genres among user's favorites
    # --------------------------------------------------------------------------
    top_genres_qs = (
        TrackGenre.objects.filter(track__favorites__user=user)
        .values('genre__name')
        .annotate(n=Count('pk'))
        .order_by('-n', 'genre__name')[:3]
    )
    top_genres = [
        {'name': item['genre__name'], 'count': item['n']}
        for item in top_genres_qs
    ]

    # --------------------------------------------------------------------------
    # Query 3: Favorites missing BPM or Genre (limited to 50, newest first)
    # --------------------------------------------------------------------------
    needs_details_qs = (
        Favorite.objects.filter(user=user)
        .annotate(has_genre=Exists(TrackGenre.objects.filter(track=OuterRef('track_id'))))
        .filter(Q(track__bpm__isnull=True) | Q(has_genre=False))
        .select_related('track')
        .order_by('-created_at')[:50]
    )
    needs_details = list(needs_details_qs)

    # --------------------------------------------------------------------------
    # Genre Match Check
    # Note: strict equality after stripping and casefolding.
    # This will not match variants like "Synth-wave" vs "Synthwave".
    # --------------------------------------------------------------------------
    declared_clean = declared_genre.strip().casefold() if declared_genre else ''
    genre_matched = False
    if declared_clean:
        for g in top_genres:
            if g['name'].strip().casefold() == declared_clean:
                genre_matched = True
                break

    # Calculate percentage offsets for optional CSS range bar
    bpm_range_min_pct = 0
    bpm_range_avg_pct = 50
    bpm_range_max_pct = 100
    if min_bpm is not None and max_bpm is not None and max_bpm > min_bpm and avg_bpm is not None:
        span = float(max_bpm - min_bpm)
        bpm_range_avg_pct = max(0, min(100, round(((float(avg_bpm) - float(min_bpm)) / span) * 100)))

    return {
        'total': total,
        'with_bpm': with_bpm,
        'with_genre': with_genre,
        'has_partial_coverage': total > 0 and (with_bpm < total or with_genre < total),
        'avg_bpm': avg_bpm_rounded,
        'avg_bpm_display': format_bpm(avg_bpm_rounded) if avg_bpm_rounded is not None else None,
        'min_bpm': min_bpm,
        'max_bpm': max_bpm,
        'min_bpm_display': format_bpm(min_bpm),
        'max_bpm_display': format_bpm(max_bpm),
        'bpm_single_value': (min_bpm is not None and min_bpm == max_bpm),
        'bpm_range_avg_pct': bpm_range_avg_pct,
        'top_genres': top_genres,
        'declared_genre': declared_genre.strip() if declared_genre else '',
        'genre_matched': genre_matched,
        'needs_details_count': len(needs_details),
        'needs_details_preview': needs_details[:3],
        'needs_details_more_count': max(0, len(needs_details) - 3),
    }


def _empty_taste_summary(declared_genre=''):
    """Safe defaults when user has zero favorites."""
    return {
        'total': 0,
        'with_bpm': 0,
        'with_genre': 0,
        'has_partial_coverage': False,
        'avg_bpm': None,
        'avg_bpm_display': None,
        'min_bpm': None,
        'max_bpm': None,
        'min_bpm_display': None,
        'max_bpm_display': None,
        'bpm_single_value': False,
        'bpm_range_avg_pct': 50,
        'top_genres': [],
        'declared_genre': declared_genre.strip() if declared_genre else '',
        'genre_matched': False,
        'needs_details_count': 0,
        'needs_details_preview': [],
        'needs_details_more_count': 0,
    }
