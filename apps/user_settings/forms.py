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
        fields = ['dark_mode', 'pref_search_type']
        widgets = {
            'dark_mode': widgets.CheckboxInput(attrs={'id': 'theme-toggle'}),
            'pref_search_type': widgets.Select(),
        }
        labels = {
            'pref_search_type': 'Preferred search type',
        }
        help_texts = {
            'pref_search_type': 'Default search category pre-selected across the app.',
        }
