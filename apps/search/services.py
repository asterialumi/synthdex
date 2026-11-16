"""Search service orchestrating query normalization, database caching, and YouTube API calls."""
from datetime import timedelta
import logging

from django.db import transaction
from django.utils import timezone

from apps.catalogue.models import Artist, ArtistRole, Track, TrackArtist
from apps.history.models import SearchHistory
from apps.sources.cleaners import clean_youtube_title
from apps.sources.models import LinkType, TrackSource
from apps.sources.services import get_source
from apps.sources.youtube import (
    YouTubeAPIError,
    YouTubeQuotaExceededError,
    fetch_youtube_music_videos,
)
from .models import SearchCache, SearchCacheResult, SearchType
from .utils import normalize_query

logger = logging.getLogger(__name__)

# Cache lifetimes by search type
CACHE_LIFETIMES = {
    SearchType.ALL: timedelta(days=7),
    SearchType.SONG: timedelta(days=7),
    SearchType.ARTIST: timedelta(days=1),
    SearchType.ALBUM: timedelta(days=1),
}

REFRESH_MINIMUM_INTERVAL_SECONDS = 300  # 5 minutes


class SearchResult:
    """Encapsulates the output of a search execution."""

    def __init__(
        self,
        query: str,
        search_type: str,
        tracks: list[Track],
        cache: SearchCache | None = None,
        is_stale: bool = False,
        error_message: str | None = None,
        info_message: str | None = None,
    ):
        self.query = query
        self.search_type = search_type
        self.tracks = tracks
        self.cache = cache
        self.is_stale = is_stale
        self.error_message = error_message
        self.info_message = info_message


def get_tracks_from_cache(cache: SearchCache) -> list[Track]:
    """Retrieve tracks for a given SearchCache row in defined result_order from database."""
    results = (
        SearchCacheResult.objects.filter(search_cache=cache)
        .select_related('track', 'track__album')
        .prefetch_related(
            'track__credits__artist',
            'track__track_sources__source',
            'track__track_genres__genre',
        )
        .order_by('result_order')
    )
    return [item.track for item in results]


def execute_search(
    query: str,
    search_type: str = SearchType.ALL,
    user=None,
    force_refresh: bool = False,
) -> SearchResult:
    """Execute search: check database cache, call YouTube if needed, and log user search history."""
    query_normalized = normalize_query(query)
    if not query_normalized:
        return SearchResult(query=query, search_type=search_type, tracks=[])

    if search_type not in SearchType.values:
        search_type = SearchType.ALL

    now = timezone.now()
    cache = SearchCache.objects.filter(
        query_normalized=query_normalized,
        search_type=search_type,
    ).first()

    info_message = None
    use_cache = False

    if cache:
        cache_is_fresh = cache.expires_at > now
        if cache_is_fresh:
            if force_refresh:
                age_seconds = (now - cache.fetched_at).total_seconds()
                if age_seconds < REFRESH_MINIMUM_INTERVAL_SECONDS:
                    use_cache = True
                    info_message = "Results were refreshed recently (less than 5 minutes ago)."
                else:
                    use_cache = False
            else:
                use_cache = True

    # 1. Serve fresh cache directly from DB
    if cache and use_cache:
        tracks = get_tracks_from_cache(cache)
        if user and user.is_authenticated:
            SearchHistory.objects.create(
                user=user,
                search_cache=cache,
                query=query[:255],
                search_type=search_type,
            )
        return SearchResult(
            query=query,
            search_type=search_type,
            tracks=tracks,
            cache=cache,
            is_stale=False,
            info_message=info_message,
        )

    # 2. Cache miss, expired, or permitted refresh: Call YouTube
    try:
        raw_items = fetch_youtube_music_videos(query=query_normalized, max_results=10)
    except (YouTubeAPIError, YouTubeQuotaExceededError) as exc:
        logger.warning("YouTube API call failed: %s", exc)
        # Fallback to stale cache if available
        if cache:
            tracks = get_tracks_from_cache(cache)
            if user and user.is_authenticated:
                SearchHistory.objects.create(
                    user=user,
                    search_cache=cache,
                    query=query[:255],
                    search_type=search_type,
                )
            return SearchResult(
                query=query,
                search_type=search_type,
                tracks=tracks,
                cache=cache,
                is_stale=True,
                error_message="Results may be out of date (YouTube service temporarily unavailable).",
            )
        return SearchResult(
            query=query,
            search_type=search_type,
            tracks=[],
            error_message=str(exc),
        )

    # 3. Process API items and save inside transaction.atomic()
    youtube_source = get_source('youtube')
    saved_tracks: list[Track] = []

    with transaction.atomic():
        for item in raw_items:
            # Check if this video is already in our catalogue
            existing_ts = TrackSource.objects.filter(
                source=youtube_source,
                external_id=item['video_id'],
                link_type=LinkType.LISTEN,
            ).select_related('track').first()

            if existing_ts:
                track = existing_ts.track
                track.last_fetched_at = now
                update_fields = ['last_fetched_at']
                if not track.artwork_url and item.get('artwork_url'):
                    track.artwork_url = item['artwork_url'][:500]
                    update_fields.append('artwork_url')
                if not track.duration_ms and item.get('duration_ms'):
                    track.duration_ms = item['duration_ms']
                    update_fields.append('duration_ms')
                track.save(update_fields=update_fields)
            else:
                primary_artist_name, featured_names, clean_title = clean_youtube_title(
                    item['title'],
                    item['channel_title'],
                )

                # Look up primary artist case-insensitively, or create
                primary_artist = Artist.objects.filter(name__iexact=primary_artist_name).first()
                if not primary_artist:
                    primary_artist = Artist.objects.create(name=primary_artist_name[:255])

                # Create Track
                track = Track.objects.create(
                    title=clean_title[:255],
                    duration_ms=item.get('duration_ms'),
                    bpm=None,
                    release_year=None,
                    isrc=None,
                    artwork_url=item.get('artwork_url', '')[:500] if item.get('artwork_url') else None,
                    last_fetched_at=now,
                )

                # Primary artist credit
                TrackArtist.objects.create(
                    track=track,
                    artist=primary_artist,
                    role=ArtistRole.PRIMARY,
                )

                # Featured artist credits
                for feat_name in featured_names:
                    clean_feat = feat_name.strip()
                    if clean_feat and clean_feat.lower() != primary_artist_name.lower():
                        feat_artist = Artist.objects.filter(name__iexact=clean_feat).first()
                        if not feat_artist:
                            feat_artist = Artist.objects.create(name=clean_feat[:255])
                        TrackArtist.objects.get_or_create(
                            track=track,
                            artist=feat_artist,
                            role=ArtistRole.FEATURED,
                        )

                # TrackSource record
                TrackSource.objects.create(
                    track=track,
                    source=youtube_source,
                    external_id=item['video_id'][:100],
                    url=item['url'][:500],
                    link_type=LinkType.LISTEN,
                    fetched_at=now,
                )

            saved_tracks.append(track)

        # Deduplicate tracks in Python preserving order
        seen_track_ids: set[int] = set()
        deduped_tracks: list[Track] = []
        for t in saved_tracks:
            if t.id not in seen_track_ids:
                seen_track_ids.add(t.id)
                deduped_tracks.append(t)

        lifetime = CACHE_LIFETIMES.get(search_type, timedelta(days=7))
        expires_at = now + lifetime

        cache, _ = SearchCache.objects.update_or_create(
            query_normalized=query_normalized,
            search_type=search_type,
            defaults={
                'result_count': len(deduped_tracks),
                'fetched_at': now,
                'expires_at': expires_at,
            },
        )

        # Replace cached results
        cache.results.all().delete()
        cache_results = [
            SearchCacheResult(
                search_cache=cache,
                track=track,
                result_order=order,
            )
            for order, track in enumerate(deduped_tracks, start=1)
        ]
        SearchCacheResult.objects.bulk_create(cache_results)

        # Log search history entry for the user
        if user and user.is_authenticated:
            SearchHistory.objects.create(
                user=user,
                search_cache=cache,
                query=query[:255],
                search_type=search_type,
            )

    # 4. Always render directly from the database
    tracks = get_tracks_from_cache(cache)
    return SearchResult(
        query=query,
        search_type=search_type,
        tracks=tracks,
        cache=cache,
        is_stale=False,
    )
