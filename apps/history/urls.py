"""URL configuration for the history feature."""
from django.urls import path

from . import views

app_name = 'history'

urlpatterns = [
    path('', views.history_list_view, name='list'),
    path('clear/', views.clear_history_view, name='clear'),
]
