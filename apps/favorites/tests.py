"""Tests for favorites JOIN query, favorite-artists SUBQUERY, and the favorites view."""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalogue.models import Album, Artist, ArtistRole, Track, TrackArtist
from apps.favorites.models import Favorite
from apps.favorites.selectors import (
    get_favorite_artists,
    get_favorites_with_details,
    sql_of,
)

User = get_user_model()


class FavoritesQueryAndSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_a = User.objects.create_user(username='usera', password='password123')
        cls.user_b = User.objects.create_user(username='userb', password='password123')

        # Artists
        cls.artist_alpha = Artist.objects.create(name='Alpha Artist')
        cls.artist_beta = Artist.objects.create(name='Beta Artist')
        cls.artist_gamma = Artist.objects.create(name='Gamma Artist')
        cls.artist_uncredited = Artist.objects.create(name='Uncredited Artist')

        # Albums
        cls.album_one = Album.objects.create(title='First Wave', artist=cls.artist_alpha)

        # Tracks
        # Track 1: Has album, credited to Alpha Artist and Beta Artist
        cls.track_1 = Track.objects.create(
            title='Track One',
            album=cls.album_one,
            bpm=Decimal('120.00'),
            duration_ms=180000,
        )
        TrackArtist.objects.create(track=cls.track_1, artist=cls.artist_alpha, role=ArtistRole.PRIMARY)
        TrackArtist.objects.create(track=cls.track_1, artist=cls.artist_beta, role=ArtistRole.FEATURED)

        # Track 2: Has album, also credited to Alpha Artist (tests deduplication in subquery)
        cls.track_2 = Track.objects.create(
            title='Track Two',
            album=cls.album_one,
            bpm=Decimal('128.00'),
            duration_ms=210000,
        )
        TrackArtist.objects.create(track=cls.track_2, artist=cls.artist_alpha, role=ArtistRole.PRIMARY)

        # Track 3: Null album (YouTube-only single), credited to Gamma Artist
        cls.track_3 = Track.objects.create(
            title='Track Three (No Album)',
            album=None,
            bpm=None,
            duration_ms=None,
        )
        TrackArtist.objects.create(track=cls.track_3, artist=cls.artist_gamma, role=ArtistRole.PRIMARY)

        # Track 4: For User B isolation testing
        cls.track_4 = Track.objects.create(
            title='Track Four (User B Only)',
            album=cls.album_one,
        )
        TrackArtist.objects.create(track=cls.track_4, artist=cls.artist_uncredited, role=ArtistRole.PRIMARY)

        # User A favorites tracks 1, 2, 3
        cls.fav_a1 = Favorite.objects.create(user=cls.user_a, track=cls.track_1)
        cls.fav_a2 = Favorite.objects.create(user=cls.user_a, track=cls.track_2)
        cls.fav_a3 = Favorite.objects.create(user=cls.user_a, track=cls.track_3)

        # User B favorites track 4
        cls.fav_b1 = Favorite.objects.create(user=cls.user_b, track=cls.track_4)

    def test_join_sql_structure(self):
        """1. JOIN SQL: sql_of contains JOIN, catalogue_track, and catalogue_album."""
        sql = sql_of(get_favorites_with_details(self.user_a))
        self.assertIn('JOIN', sql.upper())
        self.assertIn('catalogue_track', sql)
        self.assertIn('catalogue_album', sql)

    def test_no_n_plus_one_queries(self):
        """2. No N+1: touching track, album, and credits evaluates in exactly 3 queries."""
        with self.assertNumQueries(3):
            favorites = list(get_favorites_with_details(self.user_a))
            for fav in favorites:
                _ = fav.track.title
                _ = fav.track.album.title if fav.track.album else None
                for credit in fav.track.credits.all():
                    _ = credit.artist.name

    def test_null_album_included(self):
        """3. Null album: a favorited track with no album is still returned, with track.album is None."""
        favorites = list(get_favorites_with_details(self.user_a))
        null_album_favs = [f for f in favorites if f.track.id == self.track_3.id]
        self.assertEqual(len(null_album_favs), 1)
        self.assertIsNone(null_album_favs[0].track.album)

    def test_user_isolation(self):
        """4. User isolation: one user's favorites and favorite artists never include another user's."""
        user_a_fav_track_ids = {f.track_id for f in get_favorites_with_details(self.user_a)}
        user_b_fav_track_ids = {f.track_id for f in get_favorites_with_details(self.user_b)}
        self.assertNotIn(self.track_4.id, user_a_fav_track_ids)
        self.assertIn(self.track_4.id, user_b_fav_track_ids)

        user_a_artists = set(get_favorite_artists(self.user_a))
        user_b_artists = set(get_favorite_artists(self.user_b))
        self.assertNotIn(self.artist_uncredited, user_a_artists)
        self.assertIn(self.artist_uncredited, user_b_artists)

    def test_subquery_sql_structure(self):
        """5. SUBQUERY SQL: sql_of contains at least 3 SELECT keywords (outer, middle, inner)."""
        sql = sql_of(get_favorite_artists(self.user_a))
        select_count = sql.upper().count('SELECT')
        self.assertGreaterEqual(select_count, 3)

    def test_subquery_results_and_deduplication(self):
        """6. Subquery results: includes only credited artists, deduplicated, ordered by name, empty if no favs."""
        artists = list(get_favorite_artists(self.user_a))
        self.assertEqual(len(artists), 3)
        self.assertEqual([a.name for a in artists], ['Alpha Artist', 'Beta Artist', 'Gamma Artist'])
        self.assertNotIn(self.artist_uncredited, artists)

        empty_user = User.objects.create_user(username='emptyuser', password='password123')
        empty_artists = list(get_favorite_artists(empty_user))
        self.assertEqual(len(empty_artists), 0)

    def test_view_authentication_and_debug_sql(self):
        """7. View: anonymous redirects to login; logged-in gets 200; show_sql reflects DEBUG."""
        url = reverse('favorites:list')

        anon_resp = self.client.get(url)
        self.assertEqual(anon_resp.status_code, 302)
        self.assertIn('/login/', anon_resp.url)

        self.client.force_login(self.user_a)
        with override_settings(DEBUG=False):
            resp_no_debug = self.client.get(url)
            self.assertEqual(resp_no_debug.status_code, 200)
            self.assertFalse(resp_no_debug.context['show_sql'])
            self.assertNotContains(resp_no_debug, 'SQL used (debug only)')

        with override_settings(DEBUG=True):
            resp_debug = self.client.get(url)
            self.assertEqual(resp_debug.status_code, 200)
            self.assertTrue(resp_debug.context['show_sql'])
            self.assertContains(resp_debug, 'SQL used (debug only)')
            self.assertIn('favorites_sql', resp_debug.context)
            self.assertIn('artists_sql', resp_debug.context)
