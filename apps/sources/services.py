"""Service helpers and external API integration for the sources app."""
from .models import MusicSource

KNOWN_SOURCES = {
    'youtube': {
        'name': 'youtube',
        'base_url': 'https://www.youtube.com',
        'is_active': True,
    },
    'deezer': {
        'name': 'deezer',
        'base_url': 'https://www.deezer.com',
        'is_active': True,
    },
}


def get_source(name: str) -> MusicSource:
    """Retrieve or create a MusicSource row by name.

    Normalizes the source name and sets default base_url and active status.
    """
    clean_name = name.strip().lower()
    defaults = KNOWN_SOURCES.get(
        clean_name,
        {
            'base_url': f'https://www.{clean_name}.com',
            'is_active': True,
        },
    )
    source, _ = MusicSource.objects.get_or_create(
        name=clean_name,
        defaults={
            'base_url': defaults['base_url'],
            'is_active': defaults.get('is_active', True),
        },
    )
    return source
