from .models import Profile


def display_name(request):
    """Makes `profile_display_name` available in every template's context.

    Lets other features (like Home) greet the user by their preferred
    name without importing the Profile model directly.
    """
    if request.user.is_authenticated:
        profile, _created = Profile.objects.get_or_create(user=request.user)
        return {'profile_display_name': profile.display}
    return {'profile_display_name': ''}
