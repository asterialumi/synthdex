"""Tests for user taste summary calculations.

Validates that BPM averages ignore NULLs and are not skewed by multiple genres per track,
coverage counts are accurate, top genres order correctly, and edge cases return safe values.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalogue.models import Genre, Track, TrackGenre
from apps.favorites.models import Favorite
from apps.favorites.taste import format_bpm, get_taste_summary

User = get_user_model()


class TasteSummaryTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='listener1', password='password123')
        self.user2 = User.objects.create_user(username='listener2', password='password123')

        self.genre_synth = Genre.objects.create(name='Synthwave')
        self.genre_ambient = Genre.objects.create(name='Ambient')
        self.genre_disco = Genre.objects.create(name='Disco')
        self.genre_rock = Genre.objects.create(name='Rock')

    def test_unweighted_bpm_average_and_null_handling(self):
        """Test 1: BPM average, min and max ignore NULLs, and a track with multiple genres does NOT skew average."""
        # Track A: 100 BPM, has 3 genres (Synthwave, Ambient, Disco)
        t_a = Track.objects.create(title='Track A', bpm=Decimal('100.00'))
        TrackGenre.objects.create(track=t_a, genre=self.genre_synth)
        TrackGenre.objects.create(track=t_a, genre=self.genre_ambient)
        TrackGenre.objects.create(track=t_a, genre=self.genre_disco)
        Favorite.objects.create(user=self.user1, track=t_a)

        # Track B: 200 BPM, 1 genre
        t_b = Track.objects.create(title='Track B', bpm=Decimal('200.00'))
        TrackGenre.objects.create(track=t_b, genre=self.genre_synth)
        Favorite.objects.create(user=self.user1, track=t_b)

        # Track C: NULL BPM, 1 genre
        t_c = Track.objects.create(title='Track C', bpm=None)
        TrackGenre.objects.create(track=t_c, genre=self.genre_synth)
        Favorite.objects.create(user=self.user1, track=t_c)

        summary = get_taste_summary(self.user1, declared_genre='Synthwave')

        # Total is 3, but with_bpm is 2
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['with_bpm'], 2)
        # Average of 100 and 200 is 150. If genres were joined in FROM clause, Track A would appear 3 times:
        # (100*3 + 200)/4 = 125 (incorrect). Correct is (100 + 200)/2 = 150!
        self.assertEqual(summary['avg_bpm'], 150)
        self.assertEqual(summary['min_bpm'], Decimal('100.00'))
        self.assertEqual(summary['max_bpm'], Decimal('200.00'))
        self.assertEqual(summary['min_bpm_display'], '100')
        self.assertEqual(summary['max_bpm_display'], '200')

    def test_coverage_counts(self):
        """Test 2: Coverage counts (with_bpm, with_genre) are accurate."""
        # Track 1: has both
        t1 = Track.objects.create(title='Track 1', bpm=Decimal('120.00'))
        TrackGenre.objects.create(track=t1, genre=self.genre_synth)
        Favorite.objects.create(user=self.user1, track=t1)

        # Track 2: missing bpm, has genre
        t2 = Track.objects.create(title='Track 2', bpm=None)
        TrackGenre.objects.create(track=t2, genre=self.genre_rock)
        Favorite.objects.create(user=self.user1, track=t2)

        # Track 3: has bpm, missing genre
        t3 = Track.objects.create(title='Track 3', bpm=Decimal('140.00'))
        Favorite.objects.create(user=self.user1, track=t3)

        summary = get_taste_summary(self.user1)
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['with_bpm'], 2)
        self.assertEqual(summary['with_genre'], 2)
        self.assertTrue(summary['has_partial_coverage'])

    def test_top_genres_ordering_and_limit(self):
        """Test 3: Top genres ordered by count desc, then name asc, limited to 3."""
        # 3 tracks with Ambient
        for i in range(3):
            t = Track.objects.create(title=f'Amb {i}')
            TrackGenre.objects.create(track=t, genre=self.genre_ambient)
            Favorite.objects.create(user=self.user1, track=t)

        # 2 tracks with Synthwave
        for i in range(2):
            t = Track.objects.create(title=f'Synth {i}')
            TrackGenre.objects.create(track=t, genre=self.genre_synth)
            Favorite.objects.create(user=self.user1, track=t)

        # 2 tracks with Disco (same count as Synth, but 'Disco' < 'Synthwave' alphabetically)
        for i in range(2):
            t = Track.objects.create(title=f'Disco {i}')
            TrackGenre.objects.create(track=t, genre=self.genre_disco)
            Favorite.objects.create(user=self.user1, track=t)

        # 1 track with Rock (should be excluded by limit 3)
        t_r = Track.objects.create(title='Rock 1')
        TrackGenre.objects.create(track=t_r, genre=self.genre_rock)
        Favorite.objects.create(user=self.user1, track=t_r)

        summary = get_taste_summary(self.user1)
        top = summary['top_genres']
        self.assertEqual(len(top), 3)
        self.assertEqual(top[0]['name'], 'Ambient')
        self.assertEqual(top[0]['count'], 3)
        self.assertEqual(top[1]['name'], 'Disco')
        self.assertEqual(top[1]['count'], 2)
        self.assertEqual(top[2]['name'], 'Synthwave')
        self.assertEqual(top[2]['count'], 2)

    def test_needs_details_filtering(self):
        """Test 4: Needs-details includes tracks missing BPM or genre, excludes complete tracks."""
        # Complete track
        t_complete = Track.objects.create(title='Complete Track', bpm=Decimal('128.00'))
        TrackGenre.objects.create(track=t_complete, genre=self.genre_synth)
        Favorite.objects.create(user=self.user1, track=t_complete)

        # Missing BPM
        t_no_bpm = Track.objects.create(title='No BPM', bpm=None)
        TrackGenre.objects.create(track=t_no_bpm, genre=self.genre_synth)
        f_no_bpm = Favorite.objects.create(user=self.user1, track=t_no_bpm)

        # Missing Genre
        t_no_genre = Track.objects.create(title='No Genre', bpm=Decimal('130.00'))
        f_no_genre = Favorite.objects.create(user=self.user1, track=t_no_genre)

        summary = get_taste_summary(self.user1)
        self.assertEqual(summary['needs_details_count'], 2)
        track_ids = [fav.track.id for fav in summary['needs_details_preview']]
        self.assertIn(t_no_bpm.id, track_ids)
        self.assertIn(t_no_genre.id, track_ids)
        self.assertNotIn(t_complete.id, track_ids)

    def test_genre_matching_case_insensitivity(self):
        """Test 5: Genre match is case-insensitive and whitespace-tolerant, empty never matches."""
        t = Track.objects.create(title='Synth Track')
        TrackGenre.objects.create(track=t, genre=self.genre_synth)  # 'Synthwave'
        Favorite.objects.create(user=self.user1, track=t)

        self.assertTrue(get_taste_summary(self.user1, declared_genre='synthwave')['genre_matched'])
        self.assertTrue(get_taste_summary(self.user1, declared_genre='  SYNTHWAVE  ')['genre_matched'])
        self.assertFalse(get_taste_summary(self.user1, declared_genre='Jazz')['genre_matched'])
        self.assertFalse(get_taste_summary(self.user1, declared_genre='')['genre_matched'])
        self.assertFalse(get_taste_summary(self.user1, declared_genre=None)['genre_matched'])

    def test_user_isolation(self):
        """Test 6: User A's favorites never bleed into User B's summary."""
        t = Track.objects.create(title='User 1 Track', bpm=Decimal('150.00'))
        TrackGenre.objects.create(track=t, genre=self.genre_rock)
        Favorite.objects.create(user=self.user1, track=t)

        summary_user2 = get_taste_summary(self.user2)
        self.assertEqual(summary_user2['total'], 0)
        self.assertEqual(len(summary_user2['top_genres']), 0)
        self.assertIsNone(summary_user2['avg_bpm'])

    def test_empty_favorites_returns_safe_defaults(self):
        """Test 7: Empty favorites returns zero counts, None metrics, and never divides by zero."""
        summary = get_taste_summary(self.user2)
        self.assertEqual(summary['total'], 0)
        self.assertEqual(summary['with_bpm'], 0)
        self.assertEqual(summary['with_genre'], 0)
        self.assertIsNone(summary['avg_bpm'])
        self.assertIsNone(summary['min_bpm'])
        self.assertIsNone(summary['max_bpm'])
        self.assertEqual(summary['top_genres'], [])
        self.assertEqual(summary['needs_details_count'], 0)
        self.assertFalse(summary['genre_matched'])


class FormatBpmHelperTests(TestCase):
    def test_format_bpm_helper(self):
        self.assertEqual(format_bpm(Decimal('205.00')), '205')
        self.assertEqual(format_bpm(Decimal('128.50')), '128.5')
        self.assertEqual(format_bpm(120), '120')
        self.assertEqual(format_bpm(133.7), '133.7')
        self.assertIsNone(format_bpm(None))
