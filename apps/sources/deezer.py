"""Deezer API integration for track metadata enrichment (BPM, ISRC, Album, Genre, Listen Link)."""
from datetime import date
from decimal import Decimal, InvalidOperation
import logging
import re
from typing import Any

from django.utils import timezone

try:
    import requests
except ImportError:
    requests = None

from apps.catalogue.models import Album, ArtistRole, Genre, Track, TrackGenre
from apps.search.utils import normalize_query
from .models import LinkType, TrackSource
from .services import get_source

logger = logging.getLogger(__name__)

DEEZER_SEARCH_URL = "https://api.deezer.com/search"
DEEZER_TRACK_URL = "https://api.deezer.com/track"
DEEZER_ALBUM_URL = "https://api.deezer.com/album"
REQUEST_TIMEOUT_SECONDS = 10


def validate_bpm(raw_bpm: Any) -> Decimal | None:
    """Validate and convert raw BPM into a Decimal fitting Postgres numeric(6,2).

    Treats missing, 0, or out-of-range BPM as unknown (None).
    """
    if raw_bpm is None or raw_bpm == "":
        return None
    try:
        val = Decimal(str(raw_bpm).strip())
        if val <= Decimal('0') or val >= Decimal('10000.00'):
            return None
        return val.quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return None


def match_deezer_candidate(
    candidate: dict[str, Any],
    target_artist: str,
    target_title: str,
    target_duration_ms: int | None = None,
) -> bool:
    """Verify if a Deezer search candidate matches target artist, title, and duration (within 5s)."""
    cand_title = candidate.get('title') or candidate.get('title_short') or ""
    cand_artist = (
        candidate.get('artist', {}).get('name')
        if isinstance(candidate.get('artist'), dict)
        else ""
    )

    norm_cand_title = normalize_query(cand_title)
    norm_target_title = normalize_query(target_title)

    norm_cand_artist = normalize_query(cand_artist)
    norm_target_artist = normalize_query(target_artist)

    # 1. Artist comparison: match or substring containment
    if not (
        norm_cand_artist == norm_target_artist
        or norm_cand_artist in norm_target_artist
        or norm_target_artist in norm_cand_artist
    ):
        return False

    # 2. Title comparison: match or prefix containment
    if not (
        norm_cand_title == norm_target_title
        or norm_cand_title.startswith(norm_target_title)
        or norm_target_title.startswith(norm_cand_title)
    ):
        return False

    # 3. Duration comparison: within ~5 seconds if both exist
    cand_duration_s = candidate.get('duration')
    if target_duration_ms is not None and cand_duration_s is not None:
        target_s = target_duration_ms / 1000.0
        if abs(target_s - float(cand_duration_s)) > 5.0:
            return False

    return True


def search_deezer(artist_name: str, title: str) -> list[dict[str, Any]]:
    """Search Deezer API using advanced syntax with general fallback."""
    if requests is None:
        return []

    # Try advanced search: artist:"X" track:"Y"
    try:
        query = f'artist:"{artist_name}" track:"{title}"'
        res = requests.get(
            DEEZER_SEARCH_URL,
            params={'q': query, 'limit': 5},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if res.status_code == 200:
            data = res.json().get('data', [])
            if data:
                return data
    except Exception as exc:
        logger.warning("Deezer advanced search failed: %s", exc)

    # Fallback to general query
    try:
        fallback_query = f"{artist_name} {title}".strip()
        res = requests.get(
            DEEZER_SEARCH_URL,
            params={'q': fallback_query, 'limit': 5},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if res.status_code == 200:
            return res.json().get('data', [])
    except Exception as exc:
        logger.warning("Deezer fallback search failed: %s", exc)

    return []


def fetch_deezer_track_details(deezer_id: int | str) -> dict[str, Any] | None:
    """Fetch track details from Deezer API /track/<id>."""
    if requests is None:
        return None
    try:
        res = requests.get(
            f"{DEEZER_TRACK_URL}/{deezer_id}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if res.status_code == 200:
            return res.json()
    except Exception as exc:
        logger.warning("Deezer track details call failed: %s", exc)
    return None


def fetch_deezer_album_details(album_id: int | str) -> dict[str, Any] | None:
    """Fetch album details from Deezer API /album/<id> defensively."""
    if requests is None:
        return None
    try:
        res = requests.get(
            f"{DEEZER_ALBUM_URL}/{album_id}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if res.status_code == 200:
            return res.json()
    except Exception as exc:
        logger.warning("Deezer album details call failed: %s", exc)
    return None


def enrich_track_from_deezer(track: Track) -> bool:
    """Enrich a Track from Deezer metadata (BPM, ISRC, release year, album, genre, listen link).

    Only fills fields that are currently empty; never overwrites existing values.
    """
    deezer_source = get_source('deezer')

    # Skip if Deezer source link already exists
    if TrackSource.objects.filter(track=track, source=deezer_source).exists():
        return False

    primary_credit = track.credits.filter(role=ArtistRole.PRIMARY).select_related('artist').first()
    artist_name = primary_credit.artist.name if primary_credit else ""

    candidates = search_deezer(artist_name=artist_name, title=track.title)
    matched_candidate = None
    for cand in candidates:
        if match_deezer_candidate(cand, artist_name, track.title, track.duration_ms):
            matched_candidate = cand
            break

    if not matched_candidate:
        return False

    details = fetch_deezer_track_details(matched_candidate['id'])
    if not details:
        return False

    updated_fields: list[str] = []

    # 1. BPM: validate against numeric(6,2)
    bpm = validate_bpm(details.get('bpm'))
    if not track.bpm and bpm is not None:
        track.bpm = bpm
        updated_fields.append('bpm')

    # 2. ISRC: unique + nullable; skip setting if another track already holds it
    raw_isrc = details.get('isrc')
    if raw_isrc and not track.isrc:
        clean_isrc = str(raw_isrc).strip()[:12]
        if clean_isrc and not Track.objects.filter(isrc=clean_isrc).exclude(pk=track.pk).exists():
            track.isrc = clean_isrc
            updated_fields.append('isrc')

    # 3. Release year: extract from release_date string
    if not track.release_year:
        rel_str = details.get('release_date') or (
            details.get('album', {}).get('release_date') if details.get('album') else None
        )
        if rel_str:
            match = re.match(r'^(\d{4})', str(rel_str))
            if match:
                track.release_year = int(match.group(1))
                updated_fields.append('release_year')

    # 4. Album: find or create linked to primary artist if track has none
    album_data = details.get('album')
    if album_data and not track.album and primary_credit:
        album_title = (album_data.get('title') or '').strip()
        if album_title:
            album_artist = primary_credit.artist
            album = Album.objects.filter(artist=album_artist, title__iexact=album_title).first()
            if not album:
                album_cover = (
                    album_data.get('cover_xl')
                    or album_data.get('cover_big')
                    or album_data.get('cover_medium')
                    or ''
                )
                album_release_date = None
                if album_data.get('release_date'):
                    try:
                        p = [int(x) for x in album_data['release_date'].split('-')]
                        if len(p) == 3:
                            album_release_date = date(p[0], p[1], p[2])
                    except Exception:
                        pass

                album = Album.objects.create(
                    artist=album_artist,
                    title=album_title[:255],
                    artwork_url=album_cover[:500] if album_cover else None,
                    release_date=album_release_date,
                )
            track.album = album
            updated_fields.append('album')

    # 5. Artwork fallback if track currently has none
    if not track.artwork_url and album_data:
        artwork = (
            album_data.get('cover_xl')
            or album_data.get('cover_big')
            or album_data.get('cover_medium')
            or ''
        )
        if artwork:
            track.artwork_url = artwork[:500]
            updated_fields.append('artwork_url')

    if updated_fields:
        track.save(update_fields=updated_fields)

    # 6. Genres (defensively inspect track details and album details)
    genre_items = []
    if 'genres' in details and isinstance(details['genres'], dict):
        genre_items = details['genres'].get('data', [])

    if not genre_items and album_data and album_data.get('id'):
        alb_details = fetch_deezer_album_details(album_data['id'])
        if alb_details and 'genres' in alb_details and isinstance(alb_details['genres'], dict):
            genre_items = alb_details['genres'].get('data', [])

    for g in genre_items:
        g_name = (g.get('name') or '').strip()
        if g_name:
            genre_obj, _ = Genre.objects.get_or_create(name=g_name[:100])
            TrackGenre.objects.get_or_create(track=track, genre=genre_obj)

    # 7. Deezer TrackSource listen link
    deezer_id = str(details.get('id', matched_candidate.get('id')))
    deezer_link = details.get('link') or f"https://www.deezer.com/track/{deezer_id}"
    TrackSource.objects.get_or_create(
        track=track,
        source=deezer_source,
        link_type=LinkType.LISTEN,
        defaults={
            'external_id': deezer_id[:100],
            'url': deezer_link[:500],
            'fetched_at': timezone.now(),
        },
    )

    return True
