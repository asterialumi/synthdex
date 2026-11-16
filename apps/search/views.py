"""Views for music search feature."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.favorites.models import Favorite
from apps.user_settings.models import UserSettings
from .models import SearchType
from .services import execute_search


@login_required(login_url='login:login')
def search_view(request):
    """Handle music searches, query validation, and result presentation."""
    raw_query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type')
    force_refresh = request.GET.get('refresh') == '1'

    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    if not search_type or search_type not in SearchType.values:
        search_type = user_settings.pref_search_type

    if not raw_query:
        return render(request, 'search/results.html', {
            'query': '',
            'search_type': search_type,
            'search_types': SearchType.choices,
            'tracks': [],
            'has_searched': False,
        })

    result = execute_search(
        query=raw_query,
        search_type=search_type,
        user=request.user,
        force_refresh=force_refresh,
    )

    if result.info_message:
        messages.info(request, result.info_message)
    if result.error_message:
        if result.is_stale and result.tracks:
            messages.warning(request, result.error_message)
        elif not result.tracks:
            messages.error(request, result.error_message)

    user_favorite_ids = set(
        Favorite.objects.filter(user=request.user, track__in=result.tracks).values_list('track_id', flat=True)
    ) if request.user.is_authenticated and result.tracks else set()

    return render(request, 'search/results.html', {
        'query': raw_query,
        'search_type': search_type,
        'search_types': SearchType.choices,
        'tracks': result.tracks,
        'user_favorite_ids': user_favorite_ids,
        'has_searched': True,
        'cache': result.cache,
        'is_stale': result.is_stale,
    })
