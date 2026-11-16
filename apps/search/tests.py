"""Unit tests for pure helper functions (no database or external network access)."""
from decimal import Decimal
from django.test import SimpleTestCase

from apps.search.utils import normalize_query
from apps.sources.cleaners import clean_youtube_title, format_duration, parse_iso_duration
from apps.sources.deezer import match_deezer_candidate, validate_bpm


class PureHelperTests(SimpleTestCase):
    """Test suite for query normalization, ISO duration parsing, and YouTube title cleaning."""

    def test_normalize_query_strips_and_lowercases(self):
        self.assertEqual(normalize_query("  Get Lucky  "), "get lucky")
        self.assertEqual(normalize_query("DAFT PUNK"), "daft punk")

    def test_normalize_query_collapses_whitespace(self):
        self.assertEqual(normalize_query("harder    better   faster"), "harder better faster")
        self.assertEqual(normalize_query("\t\n  one   more   time \n"), "one more time")

    def test_normalize_query_empty_or_none(self):
        self.assertEqual(normalize_query(""), "")
        self.assertEqual(normalize_query("   "), "")
        self.assertEqual(normalize_query(None), "")

    def test_normalize_query_truncates_to_255(self):
        long_query = "a" * 300
        result = normalize_query(long_query)
        self.assertEqual(len(result), 255)

    def test_parse_iso_duration_standard(self):
        # 6m 9s = 369s = 369000 ms
        self.assertEqual(parse_iso_duration("PT6M9S"), 369000)

    def test_parse_iso_duration_minutes_only(self):
        # 3m = 180s = 180000 ms
        self.assertEqual(parse_iso_duration("PT3M"), 180000)

    def test_parse_iso_duration_seconds_only(self):
        # 45s = 45000 ms
        self.assertEqual(parse_iso_duration("PT45S"), 45000)

    def test_parse_iso_duration_with_hours(self):
        # 1h 2m 3s = 3600 + 120 + 3 = 3723s = 3723000 ms
        self.assertEqual(parse_iso_duration("PT1H2M3S"), 3723000)

    def test_parse_iso_duration_invalid_or_empty(self):
        self.assertIsNone(parse_iso_duration(""))
        self.assertIsNone(parse_iso_duration("invalid"))
        self.assertIsNone(parse_iso_duration(None))

    def test_format_duration(self):
        self.assertEqual(format_duration(369000), "6:09")
        self.assertEqual(format_duration(45000), "0:45")
        self.assertEqual(format_duration(3723000), "1:02:03")
        self.assertEqual(format_duration(None), "--:--")

    def test_clean_youtube_title_standard_dash_and_noise(self):
        primary, featured, title = clean_youtube_title("Daft Punk - Get Lucky (Official Video)", "DaftPunkVEVO")
        self.assertEqual(primary, "Daft Punk")
        self.assertEqual(featured, [])
        self.assertEqual(title, "Get Lucky")

    def test_clean_youtube_title_en_dash_and_brackets(self):
        primary, featured, title = clean_youtube_title("Queen – Bohemian Rhapsody [Official Audio]", "Queen Official")
        self.assertEqual(primary, "Queen")
        self.assertEqual(featured, [])
        self.assertEqual(title, "Bohemian Rhapsody")

    def test_clean_youtube_title_featured_parenthesized(self):
        primary, featured, title = clean_youtube_title("The Weeknd - Starboy (feat. Daft Punk) (Lyrics)", "The Weeknd")
        self.assertEqual(primary, "The Weeknd")
        self.assertEqual(featured, ["Daft Punk"])
        self.assertEqual(title, "Starboy")

    def test_clean_youtube_title_channel_fallback(self):
        primary, featured, title = clean_youtube_title("Blinding Lights (Visualizer)", "The Weeknd - Topic")
        self.assertEqual(primary, "The Weeknd")
        self.assertEqual(title, "Blinding Lights")

    def test_clean_youtube_title_inline_featured(self):
        primary, featured, title = clean_youtube_title("Calvin Harris ft. Rihanna - This Is What You Came For", "CalvinHarrisVEVO")
        self.assertEqual(primary, "Calvin Harris")
        self.assertEqual(featured, ["Rihanna"])
        self.assertEqual(title, "This Is What You Came For")

    def test_validate_bpm_valid(self):
        self.assertEqual(validate_bpm(120), Decimal("120.00"))
        self.assertEqual(validate_bpm("128.5"), Decimal("128.50"))
        self.assertEqual(validate_bpm(Decimal("95.43")), Decimal("95.43"))

    def test_validate_bpm_invalid_or_zero(self):
        self.assertIsNone(validate_bpm(0))
        self.assertIsNone(validate_bpm("0"))
        self.assertIsNone(validate_bpm(-120))
        self.assertIsNone(validate_bpm(None))
        self.assertIsNone(validate_bpm(""))
        self.assertIsNone(validate_bpm("not-a-number"))
        self.assertIsNone(validate_bpm(10000))  # exceeds numeric(6,2)

    def test_match_deezer_candidate_success(self):
        candidate = {
            "title": "Get Lucky (Radio Edit)",
            "artist": {"name": "Daft Punk"},
            "duration": 248,
        }
        self.assertTrue(
            match_deezer_candidate(
                candidate=candidate,
                target_artist="Daft Punk",
                target_title="Get Lucky",
                target_duration_ms=248000,
            )
        )

    def test_match_deezer_candidate_duration_mismatch(self):
        candidate = {
            "title": "Get Lucky",
            "artist": {"name": "Daft Punk"},
            "duration": 360,  # 360s vs 248s (> 5s difference)
        }
        self.assertFalse(
            match_deezer_candidate(
                candidate=candidate,
                target_artist="Daft Punk",
                target_title="Get Lucky",
                target_duration_ms=248000,
            )
        )

    def test_match_deezer_candidate_artist_mismatch(self):
        candidate = {
            "title": "Get Lucky",
            "artist": {"name": "Pharrell Williams"},
            "duration": 248,
        }
        self.assertFalse(
            match_deezer_candidate(
                candidate=candidate,
                target_artist="Daft Punk",
                target_title="Get Lucky",
                target_duration_ms=248000,
            )
        )
