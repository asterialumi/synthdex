from django.contrib import admin

from .models import Album, Artist, Genre, Track, TrackArtist, TrackGenre


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'release_date')
    search_fields = ('title', 'artist__name')


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'album', 'duration_ms', 'bpm', 'release_year', 'isrc', 'last_fetched_at')
    search_fields = ('title', 'isrc')
    list_filter = ('release_year',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(TrackArtist)
class TrackArtistAdmin(admin.ModelAdmin):
    list_display = ('track', 'artist', 'role')
    list_filter = ('role',)
    search_fields = ('track__title', 'artist__name')


@admin.register(TrackGenre)
class TrackGenreAdmin(admin.ModelAdmin):
    list_display = ('track', 'genre')
    search_fields = ('track__title', 'genre__name')
