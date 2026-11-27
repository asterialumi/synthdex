# SynthDex UI Overhaul: Handover (updated Nov 27, 2026)

**Project:** SynthDex (personal music metadata catalogue)
**Stack:** Django 6.1.x, Supabase PostgreSQL, Bootstrap 5.3 (CDN) + modular custom CSS, vanilla JS. Windows, VS Code, PowerShell, `.venv`.
**Branch:** `main` (local at `d3f10a0`; `origin/main` at `b9dd345`, user pushes).

## 0. Read this first

Phases 1–6 and Polish Batches 1–2 are **done** and committed locally:
- Phase 4.5 (`94e6e50`), Phase 5 (`b9dd345`), Phase 6 (`194e0da`)
- Polish Batch 1 (`12751ed`), Polish Batch 2 (`d3f10a0`)

`manage.py check`, template compilation, filter sanity checks, and `makemigrations --check --dry-run` were run and passed after Batch 2. The unit tests (`apps/favorites/test_taste.py`, and any tests added with the JOIN/SUBQUERY work) are **written but have not been run against a test database**, because that is unsafe on live Supabase. Never claim they passed.

---

## 1. Project goal and design

SynthDex is a **personal-use** app: a user searches a song once and gets listen links plus metadata (BPM, genre, album, artist, year). Profiles are never shown to other users. The UI overhaul aims for visual cohesion, light/dark parity and responsive layouts **without changing behavior**: database schema, URL names, view context variable names and endpoints all stay as they are.

Design language: Fraunces headings, Inter UI text, warm cream surfaces, amber accent, rounded cards, and a deep aubergine (`--deep`) used for the header, the track-details hero and (Phase 5) the home "sky" panel.

---

## 2. Commit log (oldest to newest)

| Commit | Scope | Message |
|---|---|---|
| `00586f3` | Phase 1 | Add design tokens, aubergine header, theme toggle and SVG icons |
| `c317de4` | Phase 2 | Unify form styling across profile, settings, search and auth |
| `a8edcff` | Phase 3 | Fix search layout and polish results, favorites and history |
| `9a7d29a` | Phase 3 amendment | Show bio and favorite genre, add taste summary to profile |
| `6f83349` | Phase 4 | Add two-column track details with search results rail |
| `3fc7cce` | (reverted) | Recenter search results and refine track detail cover art styling |
| `bee6e45` | docs | Add project handover documentation |
| `7532578` | DB activity | Add favorites JOIN list and favorite-artists SUBQUERY with debug SQL view |
| `779fa09` | revert | Revert recenter polish; Phase 4 was already correct (stale browser cache) |
| `94e6e50` | Phase 4.5 | Restyle favorites page for both themes and gate SQL panel behind SHOW_SQL_PANEL |
| `b9dd345` | Phase 5 | Redesign home with orbit of favorite covers |
| `194e0da` | Phase 6 | Accessibility, responsive and dark mode polish |
| `12751ed` | Polish Batch 1 | Polish header, login branding, home taste panel and orbit sizing |
| `d3f10a0` | Polish Batch 2 | Add orbit zoom, ring dragging and larger favorites cap |

**About `3fc7cce`:** it was requested while the user was looking at **stale cached CSS**, so it "fixed" problems that Phase 3 and Phase 4 had already fixed. It was reverted in `779fa09`. **Don't reapply it.** The search layout and cover-art handling are whatever existed at `6f83349`.

---

## 3. What was built (Phases 1-4)

### Phase 1: tokens, layout, header
- `static/css/common/tokens.css`: CSS variables for both themes (`--bg`, `--surface`, `--surface-raised`, `--ink`, `--ink-muted`, `--border`, `--accent`, `--accent-ink`, `--deep`, `--deep-surface`, `--deep-ink`, `--deep-border`, `--danger`, `--focus-ring`, spacing, radius, shadows).
- `layout.css` (`.app-container` 1200px, `.grid-two-col` 65/35 collapsing at 991px, `.skip-link`), `components.css` (`.btn`, `.icon-btn`, `.pill`, `.card`, `.cover`, `.track-row`, `.empty-state`, `.toolbar`), `base.css` (aubergine header, dark-mode border, mobile nav, flash messages).
- `static/js/common/theme.js`: theme toggle (localStorage for anonymous users, AJAX save to `user_settings` for logged-in users) and the mobile menu.
- `templates/common/_icons.html`: inline SVG sprite, **20 symbols** (heart, heart-fill, search, external-link, sun, moon, pencil, refresh, history, user, settings, music-note, trash, chevron, check, x, menu, arrow-left, youtube, deezer).

### Phase 2: forms
- `forms.css` (44px controls, selects with `@supports (appearance: base-select)`, switches), reusable `templates/common/_field.html`, applied to profile, settings (3 forms), login, register and the track metadata edit form.

### Phase 3: search, favorites, history, time zone
- Search: one centered 860px column shared by title, search card, toolbar and results; 2-line title clamp; optimistic AJAX heart; double-submit prevention with a loading state.
- History: consecutive identical searches grouped with `×N` (display only, in `apps/history/views.py`), `<dialog>` confirmation for "Clear history".
- `config/settings.py`: `TIME_ZONE = 'Asia/Manila'`, `USE_TZ = True`.
- Favorites: *originally* a card grid; it was replaced by the table in section 4 (the grid used `repeat(auto-fill, minmax(340px, 1fr))`, which squished text at some window widths).

### Phase 3 amendment: personal-use copy and taste summary
- Copy now says the profile is private. Bio and favorite genre show on the profile header; the bio is the home subtitle (fallback text if empty).
- `apps/favorites/taste.py`: `get_taste_summary(user, declared_genre='')` (max 3 read-only queries) and `format_bpm(value)`. `test_taste.py`: 7 test cases (**unrun**, see section 0).

### Phase 4: track details and results rail
- `apps/catalogue/views.py`: rail context from `?q=<query>&type=<type>` (300-char cap, `type` validated against `SearchType.values`). Read-only lookup of `SearchCache` and `SearchCacheResult`, ignoring `expires_at`, no API calls, no writes.
- `apps/catalogue/templatetags/catalogue_tags.py`: `format_bpm`, `source_display_name` (`youtube` to `YouTube`, etc.), `duration_display`.
- `track_detail.html` / `track_detail.css`: 65/35 grid with a sticky, independently scrolling rail (`.is-current` highlight), single-column fallback without params, aubergine hero with prominent BPM and genre, balanced info grid, brand icons on Listen buttons, collapsible edit panel, mobile "Back to search results" button.

---

## 4. JOIN and SUBQUERY work (database class activity, commit `7532578`)

This is a **graded deliverable**. Treat it as protected.

- **Where:** `apps/favorites/selectors.py` (new), `apps/favorites/views.py`, `templates/favorites/favorites.html`, plus whatever tests were added with it. **Confirm the function and variable names below in the code before relying on them.** They come from the brief that requested the work.
- **JOIN:** `get_favorites_with_details(user)`: `Favorite` filtered by user with `select_related('track', 'track__album')` (INNER JOIN on the track, LEFT OUTER JOIN on the album, because `Track.album` can be NULL), plus a prefetch of credits and artists, ordered newest first. Total: 3 queries.
- **SUBQUERY:** `get_favorite_artists(user)`: the artists credited on any favorited track, written as **explicitly nested `Subquery(...)`** (inner: favorited track ids; middle: credited artist ids; outer: artists). One query. `IN` never repeats a row.
- **`sql_of(queryset)`:** returns `str(queryset.query)` for display.
- **Page now:** "Your Favorites" with a responsive list of `.track-row` items (Title, Artists, Album, BPM, Duration, Date added, heart), an "Artists in your favorites" row of pills, and a collapsed "SQL used (debug only)" block gated by `settings.SHOW_SQL_PANEL` (not `settings.DEBUG`; context vars `show_sql`, `favorites_sql`, `artists_sql`).
- **Rules:**
  - Don't edit `selectors.py`, don't turn the nested `Subquery` into a join or `distinct()`, and don't remove `sql_of`.
  - Changing `settings.DEBUG` is **not** an option: with `DEBUG = False`, `runserver` stops serving static files and Django requires `ALLOWED_HOSTS`. The panel is gated with `SHOW_SQL_PANEL` instead.

---

## 5. File inventory (current)

```
apps/
  catalogue/   templatetags/catalogue_tags.py (format_bpm, source_display_name, duration_display); views.py (rail context)
  favorites/   selectors.py (JOIN + SUBQUERY, protected); taste.py (get_taste_summary, format_bpm); views.py; test_taste.py (+ any tests from the DB activity)
  history/     views.py (consecutive search grouping)
  profile/     context_processors.py (profile_bio, profile_favorite_genre); views.py (taste summary)
  user_settings/ forms.py (pref_search_type optional in ThemeForm); views.py (JsonResponse for AJAX theme save)
config/settings.py            (TIME_ZONE = 'Asia/Manila')
static/css/common/            tokens.css, layout.css, components.css, base.css, forms.css
static/css/{catalogue,favorites,history,profile,search}/   per-feature CSS (track_detail.css, favorites.css, history.css, profile.css, search.css)
static/js/common/theme.js; static/js/search/search.js; static/js/user_settings/user_settings.js
templates/common/             base.html, _field.html, _icons.html
templates/{catalogue,favorites,history,home,login,profile,register,search,user_settings}/   page templates
```

---

## 6. Known issues and deviations (don't "fix" these unless a phase says to)

**Deviations from the original brief (intentional, needed for the header toggle):** `apps/user_settings/forms.py` (made `pref_search_type` optional in `ThemeForm`) and `apps/user_settings/views.py` (JSON response for AJAX theme saves). Leave them alone.

**Remaining minor notes:**
- `format_bpm` exists twice (`taste.py` and `catalogue_tags.py`). Keep or consolidate carefully if touched later.
- Confirm the heart toggle still degrades to a working POST form without JavaScript.

---

## 7. Phase 4.5: Favorites page restyle (done)

Replaced the Favorites `<table>` with a responsive `<ul>` of `.track-row` items using shared components (`.cover`, `.pill`, `.icon-btn`) and theme tokens in `favorites.css`, preserving original artist casing and `selectors.py` untouched (same 3-query count). Gated the collapsed SQL debug `<details>` panel behind `SHOW_SQL_PANEL` in `config/settings.py` (default off; set `SHOW_SQL_PANEL=1` in `.env` when needed, never `DEBUG`).

---

## 8. Phase 5 & Polish: Home with orbit (done)

- **Layout:** Greeting and search card (with recent-search chips) on top. Below, two-column `stretch` grid: left is the full-height deep aubergine "sky" panel with the orbit; right is "Latest Favorites" and the shared `_taste_summary.html` partial (`get_taste_summary(user, declared_genre)`).
- **Orbit:** Up to `MAX_ORBIT_PLANETS = 24` favorites across up to 5 concentric rings (newest on inner ring), reusing `get_favorites_with_details(user)[:MAX_ORBIT_PLANETS]` (no N+1, no `sql_of`). Inner rings fill the panel at default `1.0x` zoom; outer rings sit beyond the panel edge and appear when zooming out.
- **Controls & Interaction (`static/js/home/orbit.js`):** No pause on hover; keyboard-accessible Pause/Play button (default playing); zoom (`0.6x–1.6x`) via `+`/`−`/`reset` buttons and `Ctrl/Cmd+wheel` only; pointer-based ring dragging with a 6px click threshold (resumes auto-rotation from the new angle on release; disabled under `prefers-reduced-motion`). Ring orbit speed uses the ring's average BPM; each cover spins on its own axis by track BPM while `.orbit-tooltip` labels stay upright. Covers use `loading="lazy"` and `decoding="async"`, and animations pause when the tab is hidden or the panel is offscreen.

---

## 9. Phase 6 & Polish Batches 1–2: Accessibility, branding & layout (done)

- **Header & Branding:** Removed the `Search` nav link from desktop and mobile nav (search URL and all other links still work); fixed desktop header symmetry by hiding `.header-actions--mobile` at `>= 992px` so `Logout` aligns with the right inset and `#header-theme-toggle` sits immediately left of `Logout`. Added the `#i-synthdex-logo` SVG symbol in `templates/common/_icons.html` beside `SynthDex` in the header and on `_auth_brand.html`.
- **Auth & Details:** Fixed login/register left brand panel contrast in dark mode using `--deep` and `--deep-ink`. Updated the track-details back link to `Back to Results` when opened with search rail params and `Back to Home` (`home:home`) otherwise.
- **Deferred:** The animated visualizer-rings background is deferred and not built.

---

## 10. Verification commands

```powershell
# 1. Django system checks
& ".\.venv\Scripts\python.exe" manage.py check

# 2. Compile every template (read-only)
& ".\.venv\Scripts\python.exe" -c "import django, os, glob; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from django.template.loader import get_template; files = glob.glob('templates/**/*.html', recursive=True); [get_template(f.replace('templates\\', '').replace('\\', '/')) for f in files]; print(f'Compiled {len(files)} templates')"

# 3. Template filter sanity check
& ".\.venv\Scripts\python.exe" -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from apps.catalogue.templatetags.catalogue_tags import format_bpm, source_display_name; assert format_bpm(205.0) == '205'; assert format_bpm(128.5) == '128.5'; assert format_bpm(None) is None; assert source_display_name('youtube') == 'YouTube'; print('Filters OK')"

# 4. Schema drift guard (must say no changes)
& ".\.venv\Scripts\python.exe" manage.py makemigrations --check --dry-run
```

---

## 11. Hard constraints and operating rules

1. **No schema changes:** don't edit any `models.py`, and don't create migrations.
2. **The live database is read-only for you:** no inserts, updates or deletes, and **never run `manage.py test` against live Supabase** (it creates a test database).
3. **Secrets:** never open, print or commit `.env`, and don't print `DATABASE_URL`.
4. **Git:** stage files **by name** (never `git add .`). One commit per phase. **Don't push and don't create branches.** Run `git status` first and exclude unrelated uncommitted changes.
5. **Theme-safe styles:** no hard-coded colors in CSS, only tokens, and every component must work in both themes.
6. **No new dependencies:** vanilla JS only, no new pip or npm packages, no new CDN scripts, no inline `style=` or `onclick=`.
7. **Python changes are limited to those named in the active phase.** Report any other Python change you think is needed instead of making it silently.
8. **Preserve behavior:** URL names, view logic, context variable names, form field names and POST endpoints keep working.
9. **Protect `apps/favorites/selectors.py`:** its queries, the explicit nested `Subquery` and `sql_of`.
10. **Preserve each file's existing line endings** (some CRLF, some LF), and don't reformat unrelated files.
11. **Hard refresh (Ctrl+F5) or disable the cache in DevTools before judging any CSS change.** Stale CSS already caused one wasted commit (`3fc7cce`).
12. **Honest verification:** if you can't view authenticated pages in a browser, say so and verify by reading markup and running the commands in section 10. Never claim a visual check or a test run you didn't perform. **Never ask the user for their password.**
13. Keep accessibility basics on every change: visible `:focus-visible`, `aria-pressed` and names on icon-only buttons, `prefers-reduced-motion` respected.

---

## 12. Report format (after each phase, then stop)

1. Files created and changed.
2. What changed visibly, in plain language.
3. **Screens to screenshot:** URL, state and theme, because the user needs a screenshot of every modified screen for progress evidence.
4. Checks run and their results, and anything not verified.
5. Decisions you made where this file was ambiguous (pick the simplest option consistent with it).
6. The commit hash, plus a reminder that the user pushes.
