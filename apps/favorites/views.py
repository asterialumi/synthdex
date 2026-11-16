"""Views for managing user favorite tracks."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.catalogue.models import Track
from .models import Favorite


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
    """List all tracks saved by the authenticated user, ordered newest first."""
    user_favorites = (
        Favorite.objects.filter(user=request.user)
        .select_related('track', 'track__album')
        .prefetch_related(
            'track__credits__artist',
            'track__track_sources__source',
        )
        .order_by('-created_at')
    )

    return render(request, 'favorites/favorites.html', {
        'favorites': user_favorites,
    })
