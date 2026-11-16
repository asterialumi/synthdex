"""
URL configuration for the SynthDex project.

Each business feature owns its own URLconf; this file only wires the
feature apps together, so it never needs to change when a feature's
internal routes change.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('apps.login.urls')),
    path('register/', include('apps.register.urls')),
    path('profile/', include('apps.profile.urls')),
    path('settings/', include('apps.user_settings.urls')),
    path('search/', include('apps.search.urls')),
    path('', include('apps.home.urls')),
]
