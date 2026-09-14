from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'favorite_genre', 'bio']
        widgets = {
            'display_name': forms.TextInput(attrs={'placeholder': 'How should we greet you?'}),
            'favorite_genre': forms.TextInput(attrs={'placeholder': 'e.g. Synthwave, Jazz, Hip-Hop'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'A short note about your taste in music.'}),
        }
