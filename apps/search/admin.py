from django.contrib import admin

from .models import SearchCache, SearchCacheResult


@admin.register(SearchCache)
class SearchCacheAdmin(admin.ModelAdmin):
    list_display = ('query_normalized', 'search_type', 'result_count', 'fetched_at', 'expires_at')
    list_filter = ('search_type',)
    search_fields = ('query_normalized',)


@admin.register(SearchCacheResult)
class SearchCacheResultAdmin(admin.ModelAdmin):
    list_display = ('search_cache', 'track', 'result_order')
