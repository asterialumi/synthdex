from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.favorites.models import Favorite
from apps.search.models import SearchType
from apps.user_settings.models import UserSettings


@login_required(login_url='login:login')
def home_view(request):
    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    latest_favorites = (
        Favorite.objects.filter(user=request.user)
        .select_related('track', 'track__album')
        .prefetch_related(
            'track__credits__artist',
            'track__track_sources__source',
        )
        .order_by('-created_at')[:4]
    )
    return render(request, 'home/home.html', {
        'search_types': SearchType.choices,
        'pref_search_type': user_settings.pref_search_type,
        'latest_favorites': latest_favorites,
    })
