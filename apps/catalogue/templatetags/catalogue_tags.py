"""Template filters and tags for catalogue models."""
from django import template

from apps.sources.cleaners import format_duration

register = template.Library()


@register.filter
def duration_display(duration_ms):
    """Format milliseconds as mm:ss or h:mm:ss."""
    return format_duration(duration_ms)


@register.filter
def artist_credits_display(track):
    """Format track artists into 'Primary Artist feat. Featured Artist'."""
    if not track:
        return ""

    # Utilize prefetched credits if available
    credits = list(track.credits.all())
    primary = [c.artist.name for c in credits if c.role == 'primary']
    featured = [c.artist.name for c in credits if c.role == 'featured']

    if not primary:
        primary = [c.artist.name for c in credits]

    primary_str = ", ".join(primary) if primary else "Unknown Artist"
    if featured:
        return f"{primary_str} feat. {', '.join(featured)}"
    return primary_str


@register.filter
def track_listen_url(track):
    """Retrieve primary listen URL for a track."""
    if not track:
        return None
    # Check prefetched track_sources if available
    sources = list(track.track_sources.all())
    listen_source = next((s for s in sources if s.link_type == 'listen'), None)
    return listen_source.url if listen_source else None
