from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.favorites.models import Favorite
from apps.favorites.taste import get_taste_summary
from apps.history.utils import get_recent_distinct_searches
from .forms import ProfileForm
from .models import Profile


@login_required(login_url='login:login')
def profile_view(request):
    profile, _created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile:profile')
    else:
        form = ProfileForm(instance=profile)

    user_favorites = (
        Favorite.objects.filter(user=request.user)
        .select_related('track', 'track__album')
        .prefetch_related('track__credits__artist')
        .order_by('-created_at')[:5]
    )
    recent_searches = get_recent_distinct_searches(request.user, limit=5)
    taste_summary = get_taste_summary(request.user, declared_genre=profile.favorite_genre or '')

    return render(request, 'profile/profile.html', {
        'form': form,
        'profile': profile,
        'user_favorites': user_favorites,
        'recent_searches': recent_searches,
        'taste_summary': taste_summary,
    })
