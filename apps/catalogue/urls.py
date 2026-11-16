"""URL configuration for the catalogue feature."""
from django.urls import path

from . import views

app_name = 'catalogue'

urlpatterns = [
    path('<int:track_id>/', views.track_detail_view, name='track_detail'),
    path('<int:track_id>/edit/', views.edit_track_metadata_view, name='edit_metadata'),
]
