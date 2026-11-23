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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pref_search_type'].required = False

    def clean_pref_search_type(self):
        val = self.cleaned_data.get('pref_search_type')
        if not val and self.instance and self.instance.pk:
            return self.instance.pref_search_type or UserSettings.SearchType.ALL
        return val
