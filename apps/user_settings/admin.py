from django.contrib import admin

from .models import UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'dark_mode', 'pref_search_type')
    search_fields = ('user__username',)
