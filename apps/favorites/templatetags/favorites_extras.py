"""Template filters and tags for favorites presentation."""
from django import template

register = template.Library()


@register.filter
def duration_mss(duration_ms):
    """Format milliseconds into m:ss, returning '—' for None or non-positive values."""
    if duration_ms is None:
        return "—"
    try:
        total_ms = int(duration_ms)
        if total_ms <= 0:
            return "—"
        total_seconds = total_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    except (ValueError, TypeError):
        return "—"


@register.filter
def format_bpm_or_dash(value):
    """Format BPM without trailing zeroes (e.g. 205.00 -> '205'), returning '—' if None."""
    if value is None:
        return "—"
    try:
        val_float = float(value)
        if val_float.is_integer():
            return str(int(val_float))
        return f"{val_float:.2f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(value)


@register.filter
def artist_names_joined(track):
    """Format all artist names credited on a track as a comma-separated string."""
    if not track:
        return "—"
    credits = list(track.credits.all())
    names = [c.artist.name for c in credits if c.artist and c.artist.name]
    return ", ".join(names) if names else "—"
