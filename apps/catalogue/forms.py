"""Forms for catalogue track metadata editing."""
from decimal import Decimal

from django import forms


class TrackMetadataForm(forms.Form):
    """Form allowing users to manually update BPM and genre tags for a track."""

    bpm = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('9999.99'),
        required=False,
        label='BPM / Tempo',
        help_text='Beats per minute (e.g. 120.00). Leave blank if unknown.',
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'class': 'manual-edit-input',
            'placeholder': 'e.g. 120.00',
        }),
    )
    genres = forms.CharField(
        max_length=500,
        required=False,
        label='Genres',
        help_text='Comma-separated genres (e.g. Synth-pop, Electronic, Disco).',
        widget=forms.TextInput(attrs={
            'class': 'manual-edit-input',
            'placeholder': 'e.g. Synth-pop, Electronic, Disco',
        }),
    )
