from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render

from .forms import ThemeForm, UsernameChangeForm
from .models import UserSettings


@login_required(login_url='login:login')
def settings_view(request):
    user_settings, _created = UserSettings.objects.get_or_create(user=request.user)

    theme_form = ThemeForm(instance=user_settings)
    username_form = UsernameChangeForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        form_id = request.POST.get('form_id')

        if form_id == 'theme':
            theme_form = ThemeForm(request.POST, instance=user_settings)
            if theme_form.is_valid():
                theme_form.save()
                messages.success(request, 'Appearance preference saved.')
                return redirect('user_settings:settings')

        elif form_id == 'username':
            username_form = UsernameChangeForm(request.POST, instance=request.user)
            if username_form.is_valid():
                username_form.save()
                messages.success(request, 'Username updated.')
                return redirect('user_settings:settings')

        elif form_id == 'password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # Keep the user logged in after changing their password.
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed.')
                return redirect('user_settings:settings')

    return render(request, 'user_settings/settings.html', {
        'theme_form': theme_form,
        'username_form': username_form,
        'password_form': password_form,
    })
