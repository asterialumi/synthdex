# SynthDex

SynthDex is a personal music metadata catalogue built for students or avid music listeners who likes to keep track of their music collection. I initially built this as a rhythm gamer who wanted a centralized application to search for song BPM. Well... turns out APIs are hard to come by, so I don't know if I fullfilled that. I plan on rebuilding this sometime.

SynthDex lets users search for a track once, persist and cache normalized metadata in a relational database, and browse consolidated song details—including BPM, genre, album, artist credits, release year, ISRC, duration, and direct listen links—alongside personal favorites, search history, and an interactive cosmic orbit dashboard.



## Architecture: Vertical Slicing

The project is structured using **vertical slicing (package-by-feature)** rather than grouping files globally by technical layer. Each business feature lives in its own self-contained Django app under `apps/`, with matching feature directories in `templates/` and `static/`:

- **Feature isolation:** Each slice owns its own `models.py`, `views.py`, `urls.py`, `forms.py`, templates, CSS, and JavaScript.
- **Centralized wiring:** `config/urls.py` only includes each feature's URLconf, and `config/settings.py` registers the feature apps.
- **Shared primitives:** Cross-cutting UI elements (base layout, design tokens, SVG icon sprite, form field partial, theme toggle, and background visualizer) live under `common/` in `templates/` and `static/`.

### Folder Structure

```text
synthdex/
├── config/                         # Project configuration (settings.py, urls.py, wsgi.py, asgi.py)
├── apps/                           # Vertical feature slices
│   ├── catalogue/                  # Core music entities (Artist, Album, Track, Genre) & track detail/edit
│   ├── favorites/                  # Saved tracks, JOIN/Subquery selectors, taste summary, SQL debug view
│   ├── history/                    # Per-user search log with consecutive search grouping
│   ├── home/                       # Dashboard with taste summary, latest favorites, and cosmic orbit
│   ├── login/                      # User authentication (login/logout)
│   ├── profile/                    # Private user profile (display name, bio, favorite genre)
│   ├── register/                   # User registration
│   ├── search/                     # Normalized search cache, TTL handling, and search results
│   ├── sources/                    # External API clients (YouTube, Deezer) and provider link models
│   └── user_settings/              # Per-user preferences (dark mode, default search type)
├── templates/
│   ├── common/                     # Shared base.html, _icons.html, _field.html, _auth_brand.html, _taste_summary.html
│   ├── catalogue/                  # track_detail.html
│   ├── favorites/                  # favorites.html
│   ├── history/                    # history.html
│   ├── home/                       # home.html
│   ├── login/                      # login.html
│   ├── profile/                    # profile.html
│   ├── register/                   # register.html
│   ├── search/                     # results.html
│   └── user_settings/              # settings.html
├── static/
│   ├── css/
│   │   ├── common/                 # tokens.css, layout.css, components.css, forms.css, base.css, auth.css, visualizer.css
│   │   └── <feature>/              # Per-feature stylesheets (home, favorites, track_detail, search, history, etc.)
│   ├── js/
│   │   ├── common/                 # theme.js, visualizer.js
│   │   ├── home/                   # orbit.js (interactive orbit, zoom, pan, ring dragging, tooltips)
│   │   ├── search/                 # search.js (optimistic favorite toggle, loading states)
│   │   └── user_settings/          # user_settings.js
│   └── images/                     # Feature-specific image assets
├── manage.py
└── requirements.txt
```



## Database Models & Schema Design

`catalogue.Track` sits at the center of the Entity-Relationship Diagram. Other slices reference `Track` via foreign keys so `catalogue` remains decoupled from user-facing features.

### `apps.catalogue`
- **`Artist`** (`catalogue_artist`): `name`, `image_url`.
- **`Album`** (`catalogue_album`): `artist` (FK to `Artist`, `CASCADE`), `title`, `release_date`, `artwork_url`.
- **`Track`** (`catalogue_track`): `album` (nullable FK to `Album`, `SET_NULL`), `title`, `duration_ms`, `bpm` (`Decimal(6, 2)`), `release_year`, `isrc` (nullable unique `CharField(12)`), `artwork_url`, `last_fetched_at`.
- **`Genre`** (`catalogue_genre`): `name` (unique).
- **`TrackArtist`** (`catalogue_trackartist`): junction between `Track` and `Artist` with `role` (`primary`, `featured`, `composer`, `producer`); unique constraint on `(track, artist, role)`.
- **`TrackGenre`** (`catalogue_trackgenre`): junction between `Track` and `Genre`; unique constraint on `(track, genre)`.

### `apps.sources`
- **`MusicSource`** (`sources_musicsource`): provider registry (`name`, `base_url`, `is_active`).
- **`TrackSource`** (`sources_tracksource`): links a `Track` to a `MusicSource` with `external_id`, `url`, `link_type` (`listen`, `purchase`, `artist_page`), and `fetched_at`; unique constraint on `(track, source, link_type)`.

### `apps.search`
- **`SearchCache`** (`search_searchcache`): stores `query_normalized`, `search_type` (`all`, `song`, `artist`, `album`), `result_count`, `fetched_at`, and `expires_at`; unique constraint on `(query_normalized, search_type)`.
- **`SearchCacheResult`** (`search_searchcacheresult`): ordered junction (`result_order`) linking `SearchCache` to `Track`; unique constraint on `(search_cache, track)`.

### `apps.favorites`
- **`Favorite`** (`favorites_favorite`): junction between `AUTH_USER_MODEL` and `catalogue.Track` with `created_at`; unique constraint on `(user, track)`.

### `apps.history`
- **`SearchHistory`** (`history_searchhistory`): logs `user`, optional `search_cache` (nullable FK, `SET_NULL`), raw `query`, `search_type`, and `searched_at`.

### `apps.profile` & `apps.user_settings`
- **`Profile`** (`profile_profile`): one-to-one with `AUTH_USER_MODEL`; stores `display_name`, `favorite_genre`, `bio`, `joined_at`.
- **`UserSettings`** (`user_settings_usersettings`): one-to-one with `AUTH_USER_MODEL`; stores `dark_mode` and `pref_search_type`.

### Information Management Highlights
- **Read-Through Search Caching:** Repeated queries matching `(query_normalized, search_type)` before `expires_at` are served from `SearchCache` and `SearchCacheResult` without calling external APIs.
- **Explicit JOIN & Nested Subquery Selectors (`apps/favorites/selectors.py`):**
  - `get_favorites_with_details(user)` uses `select_related('track', 'track__album')` (INNER JOIN on `Track`, LEFT OUTER JOIN on nullable `Album`) and `prefetch_related` for credits and artists.
  - `get_favorite_artists(user)` uses an explicit three-level nested `Subquery` (`Favorite` -> `TrackArtist` -> `Artist`), which the Favorites view annotates and ranks by favorite count.
  - When `SHOW_SQL_PANEL=1` is set in `.env`, the Favorites page renders a collapsible debug `<details>` panel displaying the generated SQL (`favorites_sql` and `artists_sql`).


## Tech Stack & External APIs

### Stack
- **Backend:** Python 3.12, Django 6.1.3
- **Database:** PostgreSQL (Supabase), connected via `dj-database-url` and `psycopg` 3.3.9 with SSL required
- **Configuration & HTTP:** `python-dotenv`, `requests`
- **Frontend:** Django Templates, Bootstrap 5.3 (CDN), Google Fonts (`Fraunces` and `Inter`), modular CSS with custom design tokens (light and dark themes), vanilla JavaScript, and native HTML5 Canvas 2D API (visualizer rings background)

### External APIs
- **YouTube Data API v3** (`apps/sources/youtube.py`):
  - Endpoints: `https://www.googleapis.com/youtube/v3/search` and `https://www.googleapis.com/youtube/v3/videos`
  - Purpose: Primary track/music-video search, channel/artist attribution, thumbnail artwork, ISO 8601 duration parsing, and YouTube listen URLs. Requires `YOUTUBE_API_KEY`.
- **Deezer Public API** (`apps/sources/deezer.py`):
  - Endpoints: `https://api.deezer.com/search`, `https://api.deezer.com/track`, and `https://api.deezer.com/album`
  - Purpose: Metadata enrichment for matched tracks, including BPM, ISRC, album details, genres, and Deezer listen links.



## How to Run

> *I will deploy this eventually, so this is more of a "future me" note on how to run this.*

### 1. Prerequisites
- Python 3.12+
- A PostgreSQL database URL (e.g., Supabase PostgreSQL connection string)
- A YouTube Data API v3 key

### 2. Setup Environment
Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure `.env`
Create a `.env` file in the project root (do not commit it):

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
YOUTUBE_API_KEY=your_youtube_data_api_v3_key
SHOW_SQL_PANEL=0
```

Set `SHOW_SQL_PANEL=1` to enable the collapsible SQL debug panel on the Favorites page.

### 4. Apply Migrations & Start the Server
```powershell
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

### 5. Verification Commands
To verify system configuration and schema state without modifying the database:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

> **Note:** Avoid running `manage.py test` against a live Supabase database, as Django's test runner attempts to create and tear down a separate test database.
