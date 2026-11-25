"""Views for managing user favorite tracks."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.catalogue.models import Track
from .models import Favorite
from .selectors import get_favorite_artists, get_favorites_with_details, sql_of


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
    """List all tracks and credited artists saved by the authenticated user."""
    favorites = get_favorites_with_details(request.user)
    favorite_artists = get_favorite_artists(request.user)
    show_sql = bool(getattr(settings, 'SHOW_SQL_PANEL', False))

    context = {
        'favorites': favorites,
        'favorite_artists': favorite_artists,
        'show_sql': show_sql,
    }

    if show_sql:
        context['favorites_sql'] = sql_of(favorites)
        context['artists_sql'] = sql_of(favorite_artists)

    return render(request, 'favorites/favorites.html', context)


favorites_list = favorites_list_view
