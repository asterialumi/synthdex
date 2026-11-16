"""Pure Python cleaning and parsing helpers for music metadata.

Contains no database access or network calls.
"""
import html
import re

# Common video noise indicators in YouTube titles
NOISE_PATTERNS = [
    r'\[\s*(?:official\s+(?:video|audio|music\s+video|lyric\s+video)|lyrics?|lyric\s+video|visualizer|hd|hq|audio|video|4k|remastered)\s*\]',
    r'\(\s*(?:official\s+(?:video|audio|music\s+video|lyric\s+video)|lyrics?|lyric\s+video|visualizer|hd|hq|audio|video|4k|remastered)\s*\)',
]

# Patterns for featured artists (e.g., "(feat. Artist)", "[ft. Artist]", "feat. Artist")
FEATURED_IN_PARENS = r'[\(\[]\s*(?:feat\.?|ft\.?|featuring)\s+([^\)\]]+)[\)\]]'
FEATURED_INLINE = r'\b(?:feat\.?|ft\.?|featuring)\s+([^-–\(\[]+)'

# Noise patterns in YouTube channel names
CHANNEL_STRIP_PATTERNS = [
    r'(?i)\s*-\s*topic\b',
    r'(?i)(?:\bvevo\b|vevo$)',
    r'(?i)(?:\bofficial\b|official$)',
]


def parse_iso_duration(duration_str: str) -> int | None:
    """Convert an ISO 8601 duration string (e.g., 'PT6M9S') into milliseconds."""
    if not duration_str or not isinstance(duration_str, str):
        return None

    match = re.match(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', duration_str.strip())
    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000
    return total_ms


def format_duration(duration_ms: int | None) -> str:
    """Format milliseconds into a human-readable mm:ss or h:mm:ss string."""
    if duration_ms is None or duration_ms < 0:
        return "--:--"

    total_seconds = int(round(duration_ms / 1000))
    if total_seconds >= 3600:
        hours = total_seconds // 3600
        rem_minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}:{rem_minutes:02d}:{seconds:02d}"
    else:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"


def clean_youtube_title(raw_title: str, channel_title: str = "") -> tuple[str, list[str], str]:
    """Clean and parse YouTube video title and channel into artist, featured artists, and song title.

    Returns:
        (primary_artist, [featured_artists], clean_title)
    """
    text = html.unescape(raw_title or "").strip()

    # 1. Remove bracketed noise
    for pat in NOISE_PATTERNS:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)

    # 2. Extract featured artists from parenthesized notations first
    featured_artists: list[str] = []
    for pat in [FEATURED_IN_PARENS, FEATURED_INLINE]:
        matches = list(re.finditer(pat, text, flags=re.IGNORECASE))
        for m in matches:
            raw_feat = m.group(1).strip()
            # Split multiple featured artists separated by comma, &, or 'and'
            parts = re.split(r'\s*(?:,|&|\band\b)\s*', raw_feat)
            for part in parts:
                clean_name = part.strip().strip(' -–"\'')
                if clean_name and clean_name.lower() not in [f.lower() for f in featured_artists]:
                    featured_artists.append(clean_name)
        text = re.sub(pat, '', text, flags=re.IGNORECASE)

    # 3. Split on the first ' - ' or en dash ' – '
    split_match = re.search(r'\s+[-–]\s+', text)
    if split_match:
        artist_part = text[:split_match.start()].strip()
        title_part = text[split_match.end():].strip()
    else:
        title_part = text.strip()
        artist_part = channel_title or ""
        for pat in CHANNEL_STRIP_PATTERNS:
            artist_part = re.sub(pat, '', artist_part).strip()

    # Clean up whitespace and punctuation
    artist_part = re.sub(r'\s+', ' ', artist_part).strip(' -–"\'')
    title_part = re.sub(r'\s+', ' ', title_part).strip(' -–"\'')

    if not artist_part:
        artist_part = "Unknown Artist"
    if not title_part:
        title_part = "Untitled"

    # Exclude primary artist from featured list if duplicate
    featured_artists = [
        fa[:255] for fa in featured_artists
        if fa and fa.lower() != artist_part.lower()
    ]

    return artist_part[:255], featured_artists, title_part[:255]
