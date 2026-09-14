from django.contrib.auth import get_user_model
from django.forms import ModelForm, widgets

from .models import UserSettings

User = get_user_model()


class UsernameChangeForm(ModelForm):
    class Meta:
        model = User
        fields = ['username']


class ThemeForm(ModelForm):
    class Meta:
        model = UserSettings
        fields = ['dark_mode']
        widgets = {
            'dark_mode': widgets.CheckboxInput(attrs={'id': 'theme-toggle'}),
        }
