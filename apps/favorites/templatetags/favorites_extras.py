"""Template filters and tags for favorites presentation."""
from django import template

from apps.favorites.taste import format_bpm as _format_bpm
from apps.sources.cleaners import format_duration

register = template.Library()


@register.filter
def duration_mss(duration_ms):
    """Format milliseconds into m:ss, returning '—' for None or non-positive values."""
    if duration_ms is None or duration_ms <= 0:
        return "—"
    res = format_duration(duration_ms)
    return res if res and res != '--:--' else "—"


@register.filter
def format_bpm_or_dash(value):
    """Format BPM without trailing zeroes (e.g. 205.00 -> '205'), returning '—' if None."""
    formatted = _format_bpm(value)
    return formatted if formatted is not None else "—"


@register.filter
def artist_names_joined(track):
    """Format all artist names credited on a track as a comma-separated string."""
    if not track:
        return "—"
    credits = list(track.credits.all())
    names = [c.artist.name for c in credits if c.artist and c.artist.name]
    return ", ".join(names) if names else "—"
