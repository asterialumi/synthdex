from .models import Profile


def display_name(request):
    """Makes profile information available in every template's context.

    Exposes `profile_display_name`, `profile_bio`, and `profile_favorite_genre`.
    Uses the single loaded Profile object without adding extra queries.
    """
    if request.user.is_authenticated:
        profile, _created = Profile.objects.get_or_create(user=request.user)
        return {
            'profile_display_name': profile.display,
            'profile_bio': profile.bio or '',
            'profile_favorite_genre': profile.favorite_genre or '',
        }
    return {
        'profile_display_name': '',
        'profile_bio': '',
        'profile_favorite_genre': '',
    }
