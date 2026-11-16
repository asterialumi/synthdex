from django.contrib import admin

from .models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'search_type', 'searched_at')
    list_filter = ('search_type',)
    search_fields = ('user__username', 'query')
