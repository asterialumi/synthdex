"""YouTube Data API v3 client for music metadata retrieval."""
import html
import logging
from typing import Any

from django.conf import settings

try:
    import requests
except ImportError:
    requests = None

from .cleaners import parse_iso_duration

logger = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
REQUEST_TIMEOUT_SECONDS = 10


class YouTubeAPIError(Exception):
    """Base exception for YouTube Data API errors."""


class YouTubeQuotaExceededError(YouTubeAPIError):
    """Exception raised when the YouTube API quota has been exceeded."""


def fetch_youtube_music_videos(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search YouTube for music videos matching query, and batch-fetch their details (duration).

    Does NOT log full request URLs to avoid leaking the API key.
    Returns a list of dicts:
        [{
            'video_id': str,
            'title': str (unescaped),
            'channel_title': str (unescaped),
            'artwork_url': str,
            'duration_ms': int | None,
            'url': str,
        }, ...]
    """
    if requests is None:
        raise YouTubeAPIError("The 'requests' library is not installed. Please run: pip install -r requirements.txt")

    api_key = getattr(settings, 'YOUTUBE_API_KEY', '')
    if not api_key:
        raise YouTubeAPIError("YOUTUBE_API_KEY is not configured in settings or environment.")

    # Step 1: search.list (type=video, videoCategoryId=10 for Music)
    search_params = {
        'part': 'snippet',
        'type': 'video',
        'videoCategoryId': '10',
        'maxResults': max_results,
        'q': query,
        'key': api_key,
    }

    try:
        search_res = requests.get(
            YOUTUBE_SEARCH_URL,
            params=search_params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as exc:
        logger.error("YouTube search request failed: %s", exc.__class__.__name__)
        raise YouTubeAPIError("Could not reach YouTube service. Please check your network connection.") from exc

    if search_res.status_code == 403:
        error_payload = search_res.json().get('error', {})
        reasons = [e.get('reason') for e in error_payload.get('errors', [])]
        if 'quotaExceeded' in reasons or 'dailyLimitExceeded' in reasons:
            raise YouTubeQuotaExceededError("Daily YouTube API quota has been exceeded.")
        raise YouTubeAPIError(f"YouTube API permission error: {error_payload.get('message', 'Forbidden')}")
    elif search_res.status_code != 200:
        raise YouTubeAPIError(f"YouTube search failed with HTTP status {search_res.status_code}.")

    search_items = search_res.json().get('items', [])
    video_ids = [
        item['id']['videoId']
        for item in search_items
        if item.get('id', {}).get('videoId')
    ]

    if not video_ids:
        return []

    # Step 2: One batched videos.list for contentDetails (duration) and snippet
    videos_params = {
        'part': 'contentDetails,snippet',
        'id': ','.join(video_ids),
        'key': api_key,
    }

    try:
        videos_res = requests.get(
            YOUTUBE_VIDEOS_URL,
            params=videos_params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as exc:
        logger.error("YouTube videos.list request failed: %s", exc.__class__.__name__)
        raise YouTubeAPIError("Could not retrieve video details from YouTube.") from exc

    if videos_res.status_code != 200:
        raise YouTubeAPIError(f"YouTube video details failed with HTTP status {videos_res.status_code}.")

    videos_items = videos_res.json().get('items', [])
    videos_map = {item['id']: item for item in videos_items}

    results: list[dict[str, Any]] = []
    # Preserve search result ordering from video_ids
    for vid_id in video_ids:
        vid_data = videos_map.get(vid_id)
        if not vid_data:
            continue

        snippet = vid_data.get('snippet', {})
        content_details = vid_data.get('contentDetails', {})

        raw_title = snippet.get('title', '')
        channel_title = snippet.get('channelTitle', '')

        # Use high quality thumbnail as artwork, fallback to medium/default
        thumbnails = snippet.get('thumbnails', {})
        artwork_url = (
            thumbnails.get('high', {}).get('url')
            or thumbnails.get('medium', {}).get('url')
            or thumbnails.get('default', {}).get('url')
            or ''
        )

        duration_iso = content_details.get('duration', '')
        duration_ms = parse_iso_duration(duration_iso)

        results.append({
            'video_id': vid_id,
            'title': html.unescape(raw_title),
            'channel_title': html.unescape(channel_title),
            'artwork_url': artwork_url,
            'duration_ms': duration_ms,
            'url': f'https://www.youtube.com/watch?v={vid_id}',
        })

    return results
