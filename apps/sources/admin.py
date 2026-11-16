from django.contrib import admin

from .models import MusicSource, TrackSource


@admin.register(MusicSource)
class MusicSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url', 'is_active')
    search_fields = ('name',)


@admin.register(TrackSource)
class TrackSourceAdmin(admin.ModelAdmin):
    list_display = ('track', 'source', 'external_id', 'link_type', 'fetched_at')
    list_filter = ('source', 'link_type')
    search_fields = ('track__title', 'external_id')
