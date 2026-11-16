"""URL configuration for the favorites feature."""
from django.urls import path

from . import views

app_name = 'favorites'

urlpatterns = [
    path('', views.favorites_list_view, name='list'),
    path('toggle/<int:track_id>/', views.toggle_favorite_view, name='toggle'),
]
