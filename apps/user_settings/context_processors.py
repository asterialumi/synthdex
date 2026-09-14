from .models import UserSettings


def theme(request):
    """Makes `dark_mode` available in every template's context.

    Used by templates/common/base.html to render the initial
    data-theme attribute server-side for logged-in users, so the
    correct palette is present before any JavaScript runs.
    """
    if request.user.is_authenticated:
        user_settings, _created = UserSettings.objects.get_or_create(user=request.user)
        return {'dark_mode': user_settings.dark_mode}
    return {'dark_mode': False}
