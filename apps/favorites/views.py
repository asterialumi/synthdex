"""Views for managing user favorite tracks."""
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Exists, F, OuterRef, Q
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.catalogue.models import Track, TrackArtist
from apps.search.models import SearchType
from .models import Favorite
from .selectors import get_favorite_artists, get_favorites_with_details, sql_of

FAVORITES_PER_PAGE = 10
MAX_FAVORITE_ARTISTS = 12
MAX_QUERY_LENGTH = 300

DEFAULT_SORT = 'newest'
SORT_CHOICES = [
    ('newest', 'Date added (newest first)'),
    ('oldest', 'Date added (oldest first)'),
    ('title_asc', 'Title A-Z'),
    ('title_desc', 'Title Z-A'),
    ('bpm_asc', 'BPM low-high'),
    ('bpm_desc', 'BPM high-low'),
]
SORT_ORDERING = {
    'newest': ('-created_at', '-id'),
    'oldest': ('created_at', 'id'),
    'title_asc': (Lower('track__title'), '-created_at', '-id'),
    'title_desc': (Lower('track__title').desc(), '-created_at', '-id'),
    'bpm_asc': (F('track__bpm').asc(nulls_last=True), '-created_at', '-id'),
    'bpm_desc': (F('track__bpm').desc(nulls_last=True), '-created_at', '-id'),
}


@login_required(login_url='login:login')
@require_POST
def toggle_favorite_view(request, track_id: int):
    """Toggle favorite status of a track for the authenticated user.

    Creates or deletes a Favorite row with safe redirect.
    """
    track = get_object_or_404(Track, pk=track_id)
    favorite = Favorite.objects.filter(user=request.user, track=track).first()

    if favorite:
        favorite.delete()
        messages.success(request, f'Removed "{track.title}" from your favorites.')
    else:
        Favorite.objects.create(user=request.user, track=track)
        messages.success(request, f'Added "{track.title}" to your favorites.')

    # Safe redirect to next parameter or HTTP_REFERER if allowed
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect('catalogue:track_detail', track_id=track.id)


@login_required(login_url='login:login')
def favorites_list_view(request):
    """List saved tracks (with search, filter, sort, pagination) and credited artists."""
    base_favorites = get_favorites_with_details(request.user)
    base_artists = get_favorite_artists(request.user)
    show_sql = bool(getattr(settings, 'SHOW_SQL_PANEL', False))

    favorites_sql = sql_of(base_favorites) if show_sql else ''
    artists_sql = sql_of(base_artists) if show_sql else ''

    query = request.GET.get('q', '').strip()[:MAX_QUERY_LENGTH]
    filter_type = request.GET.get('type', SearchType.ALL)
    if filter_type not in SearchType.values:
        filter_type = SearchType.ALL

    sort_by = request.GET.get('sort', DEFAULT_SORT)
    if sort_by not in SORT_ORDERING:
        sort_by = DEFAULT_SORT

    filtered_favorites = base_favorites
    if query:
        artist_match = TrackArtist.objects.filter(
            track_id=OuterRef('track_id'),
            artist__name__icontains=query,
        )
        if filter_type == SearchType.SONG:
            filtered_favorites = filtered_favorites.filter(track__title__icontains=query)
        elif filter_type == SearchType.ARTIST:
            filtered_favorites = filtered_favorites.filter(Exists(artist_match))
        elif filter_type == SearchType.ALBUM:
            filtered_favorites = filtered_favorites.filter(track__album__title__icontains=query)
        else:
            filtered_favorites = filtered_favorites.filter(
                Q(track__title__icontains=query)
                | Exists(artist_match)
                | Q(track__album__title__icontains=query)
            )

    if sort_by != DEFAULT_SORT:
        filtered_favorites = filtered_favorites.order_by(*SORT_ORDERING[sort_by])

    paginator = Paginator(filtered_favorites, FAVORITES_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)

    artists_list = list(base_artists)
    favorite_artists = artists_list[:MAX_FAVORITE_ARTISTS]
    extra_artists_count = max(0, len(artists_list) - MAX_FAVORITE_ARTISTS)

    filter_params = {}
    if query:
        filter_params['q'] = query
    if filter_type != SearchType.ALL:
        filter_params['type'] = filter_type
    if sort_by != DEFAULT_SORT:
        filter_params['sort'] = sort_by

    has_active_filters = bool(filter_params)

    context = {
        'favorites': page_obj,
        'page_obj': page_obj,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
        'query': query,
        'filter_type': filter_type,
        'search_types': SearchType.choices,
        'sort_by': sort_by,
        'sort_choices': SORT_CHOICES,
        'has_active_filters': has_active_filters,
        'filter_query_string': urlencode(filter_params),
        'favorite_artists': favorite_artists,
        'extra_artists_count': extra_artists_count,
        'show_sql': show_sql,
    }

    if show_sql:
        context['favorites_sql'] = favorites_sql
        context['artists_sql'] = artists_sql

    return render(request, 'favorites/favorites.html', context)


favorites_list = favorites_list_view
