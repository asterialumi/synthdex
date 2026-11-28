# SynthDex UI Overhaul: Handover (updated Nov 28, 2026)

**Project:** SynthDex (personal music metadata catalogue)
**Stack:** Django 6.1.x, Supabase PostgreSQL, Bootstrap 5.3 (CDN) + modular custom CSS, vanilla JS. Windows, VS Code, PowerShell, `.venv`.
**Branch:** `main`. Local `main` was at `d5471ec` when this file was updated. The user pushes; confirm what is on the remote with `git log --oneline --decorate -5`.

## 0. Read this first

You are continuing work on SynthDex in a new session. You have no memory of earlier work, so everything you need is in this file. **No phase is queued.** Don't start any work until the user gives you a prompt, and when a prompt conflicts with this file, the prompt wins.

**Status.** The phased UI overhaul and Polish Round 2 (2A, 2B, 2C labels/covers/drag) are **done and committed locally**:
- Phases 1-4, the Phase 3 amendment and the JOIN/SUBQUERY work (section 2 has the hashes)
- Phase 4.5 (`94e6e50`), Phase 5 (`b9dd345`), Phase 6 (`194e0da`)
- Polish Batch 1 (`12751ed`), Polish Batch 2 (`d3f10a0`)
- Polish Round 2A (`4e37b54`), 2B (`b2ba81e`), 2C (`d77a557`), and orbit label visibility fix (`d5471ec`)

Per the last report, `manage.py check`, template compilation, the filter sanity checks and `makemigrations --check --dry-run` passed after `d5471ec`. The unit tests (`apps/favorites/test_taste.py`, and any tests added with the JOIN/SUBQUERY work) are **written but have not been run against a test database**, because that is unsafe on live Supabase. Never claim they passed.

**Not built / still pending:**
1. Panning the whole orbit (Batch C4). Spec: dragging empty space in the sky panel, or the sun, pans the whole system so its origin can sit off-center (planets may clip); clamp so the sun never leaves the panel entirely; the Reset button resets both zoom and pan; mouse and pen only, so touch scrolling keeps working; ring-drag angles and the shared label must use the system's current on-screen center, so they stay correct after zoom and pan; keyboard behavior and reduced-motion rules stay intact.
2. An animated "visualizer rings" background (subtle bar rings behind every page — deferred, last).

After each piece of work: verify, commit, report (section 12), then **stop and wait**.

---

## 1. Project goal and design

SynthDex is a **personal-use** app: a user searches a song once and gets listen links plus metadata (BPM, genre, album, artist, year). Profiles are never shown to other users. The UI overhaul aims for visual cohesion, light/dark parity and responsive layouts **without changing behavior**: database schema, URL names, view context variable names and endpoints all stay as they are.

Design language: Fraunces headings, Inter UI text, warm cream surfaces, amber accent, rounded cards, and a deep surface (`--deep`, espresso brown in light mode, aubergine in dark mode) used for the header, the login/register brand panel, the track-details hero and the home "sky" panel.

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
| `2003981` | docs | Update handover for completed polish batches |
| `4e37b54` | Polish Round 2A | Login name removal, warm light palette, whole-row clickable rows |
| `b2ba81e` | Polish Round 2B | Favorites pagination, search/filter/sort, artist limit, 900px+ columns |
| `d77a557` | Polish Round 2C | Orbit shared top-layer label, cover crop-zoom fill, ring drag fix |
| `d5471ec` | Polish Round 2C fix | Fix orbit label visibility (delegated hover/focus, `left`/`top`, `lostpointercapture`) |

**About `3fc7cce`:** it was requested while the user was looking at **stale cached CSS**, so it "fixed" problems that Phase 3 and Phase 4 had already fixed. It was reverted in `779fa09`. **Don't reapply it.** The search layout and cover-art handling are whatever existed at `6f83349`.

---

## 3. What was built (Phases 1-4)

### Phase 1: tokens, layout, header
- `static/css/common/tokens.css`: CSS variables for both themes (`--bg`, `--surface`, `--surface-raised`, `--ink`, `--ink-muted`, `--border`, `--accent`, `--accent-ink`, `--deep`, `--deep-surface`, `--deep-ink`, `--deep-border`, `--danger`, `--focus-ring`, spacing, radius, shadows).
- `layout.css` (`.app-container` 1200px, `.grid-two-col` 65/35 collapsing at 991px, `.skip-link`), `components.css` (`.btn`, `.icon-btn`, `.pill`, `.card`, `.cover`, `.track-row`, `.empty-state`, `.toolbar`), `base.css` (aubergine header, dark-mode border, mobile nav, flash messages).
- `static/js/common/theme.js`: theme toggle (localStorage for anonymous users, AJAX save to `user_settings` for logged-in users) and the mobile menu.
- `templates/common/_icons.html`: inline SVG sprite, originally **20 symbols** (heart, heart-fill, search, external-link, sun, moon, pencil, refresh, history, user, settings, music-note, trash, chevron, check, x, menu, arrow-left, youtube, deezer). The `synthdex-logo` symbol (`#i-synthdex-logo`) was added in Polish Batch 1, making **21**.

### Phase 2: forms
- `forms.css` (44px controls, selects with `@supports (appearance: base-select)`, switches), reusable `templates/common/_field.html`, applied to profile, settings (3 forms), login, register and the track metadata edit form.

### Phase 3: search, favorites, history, time zone
- Search: one centered 860px column shared by title, search card, toolbar and results; 2-line title clamp; optimistic AJAX heart; double-submit prevention with a loading state.
- History: consecutive identical searches grouped with `×N` (display only, in `apps/history/views.py`), `<dialog>` confirmation for "Clear history".
- `config/settings.py`: `TIME_ZONE = 'Asia/Manila'`, `USE_TZ = True`.
- Favorites: *originally* a card grid, then a table (section 4), now a `.track-row` list (section 7). The grid used `repeat(auto-fill, minmax(340px, 1fr))`, which squished text at some window widths, so don't bring it back.

### Phase 3 amendment: personal-use copy and taste summary
- Copy now says the profile is private. Bio and favorite genre show on the profile header; the bio is the home subtitle (fallback text if empty).
- `apps/favorites/taste.py`: `get_taste_summary(user, declared_genre='')` (max 3 read-only queries) and `format_bpm(value)`. `test_taste.py`: 7 test cases (**unrun**, see section 0).

### Phase 4: track details and results rail
- `apps/catalogue/views.py`: rail context from `?q=<query>&type=<type>` (300-char cap, `type` validated against `SearchType.values`). Read-only lookup of `SearchCache` and `SearchCacheResult`, ignoring `expires_at`, no API calls, no writes.
- `apps/catalogue/templatetags/catalogue_tags.py`: `format_bpm`, `source_display_name` (`youtube` to `YouTube`, etc.), `duration_display`.
- `track_detail.html` / `track_detail.css`: 65/35 grid with a sticky, independently scrolling rail (`.is-current` highlight), single-column fallback without params, aubergine hero with prominent BPM and genre, balanced info grid, brand icons on Listen buttons, collapsible edit panel. The back link is conditional since Polish Batch 1 (section 9).

---

## 4. JOIN and SUBQUERY work (database class activity, commit `7532578`)

This is a **graded deliverable**. Treat it as protected.

- **Where:** `apps/favorites/selectors.py` (new), `apps/favorites/views.py`, `templates/favorites/favorites.html`, plus whatever tests were added with it. **Confirm the function and variable names below in the code before relying on them.** They come from the brief that requested the work.
- **JOIN:** `get_favorites_with_details(user)`: `Favorite` filtered by user with `select_related('track', 'track__album')` (INNER JOIN on the track, LEFT OUTER JOIN on the album, because `Track.album` can be NULL), plus a prefetch of credits and artists, ordered newest first. Total: 3 queries for the selector on its own (the paginated favorites page runs more, see section 7).
- **SUBQUERY:** `get_favorite_artists(user)`: the artists credited on any favorited track, written as **explicitly nested `Subquery(...)`** (inner: favorited track ids; middle: credited artist ids; outer: artists). One query. `IN` never repeats a row.
- **`sql_of(queryset)`:** returns `str(queryset.query)` for display.
- **Page now:** "Your Favorites" with a responsive list of `.track-row` items (Title, Artists, Album, BPM, Duration, Date added, heart), an "Artists in your favorites" row of pills (limited to 12), pagination and search/filter/sort (section 7), and a collapsed "SQL used (debug only)" block gated by `settings.SHOW_SQL_PANEL` (not `settings.DEBUG`; context vars `show_sql`, `favorites_sql`, `artists_sql`).
- **Reuse:** the home orbit also calls `get_favorites_with_details(user)` (sliced), read-only.
- **Rules:**
  - Don't edit `selectors.py`, don't turn the nested `Subquery` into a join or `distinct()`, and don't remove `sql_of`.
  - Changing `settings.DEBUG` is **not** an option: with `DEBUG = False`, `runserver` stops serving static files and Django requires `ALLOWED_HOSTS`. The panel is gated with `SHOW_SQL_PANEL` instead.

---

## 5. File inventory (current)

Paths marked "(confirm)" were reported by Antigravity but not checked against the repo here.

```
apps/
  catalogue/   templatetags/catalogue_tags.py (format_bpm, source_display_name, duration_display); views.py (rail context)
  favorites/   selectors.py (JOIN + SUBQUERY, protected); taste.py (get_taste_summary, format_bpm); views.py (pagination, search/filter/sort, artist limit); test_taste.py (+ any tests from the DB activity)
  history/     views.py (consecutive search grouping)
  home/        views.py (orbit data via get_favorites_with_details(user)[:MAX_ORBIT_PLANETS], taste summary) (confirm path and where MAX_ORBIT_PLANETS lives)
  profile/     context_processors.py (profile_bio, profile_favorite_genre); views.py (taste summary)
  user_settings/ forms.py (pref_search_type optional in ThemeForm); views.py (JsonResponse for AJAX theme save)
config/settings.py            (TIME_ZONE = 'Asia/Manila'; SHOW_SQL_PANEL, default off)
static/css/common/            tokens.css (light-mode espresso deep block), layout.css, components.css (.row-clickable), base.css, forms.css
static/css/{catalogue,favorites,history,home,profile,search}/   per-feature CSS (track_detail.css, favorites.css, history.css, home.css, profile.css, search.css)
static/js/common/theme.js; static/js/search/search.js; static/js/user_settings/user_settings.js
static/js/home/orbit.js       (orbit: pause/play, zoom, ring dragging, shared top-layer tooltip)
templates/common/             base.html, _field.html, _icons.html, _taste_summary.html (shared by profile and home), _auth_brand.html (login/register brand panel) (confirm the two partial paths)
templates/{catalogue,favorites,history,home,login,profile,register,search,user_settings}/   page templates
```

---

## 6. Known issues and deviations (don't "fix" these unless asked)

**Deviations from the original brief (intentional, needed for the header toggle):** `apps/user_settings/forms.py` (made `pref_search_type` optional in `ThemeForm`) and `apps/user_settings/views.py` (JSON response for AJAX theme saves). Leave them alone.

**Remaining minor notes:**
- `format_bpm` exists twice (`taste.py` and `catalogue_tags.py`). Keep or consolidate carefully if touched later. Check whether duration helpers are duplicated too.
- Confirm the heart toggle still degrades to a working POST form without JavaScript.

---

## 7. Phase 4.5 & Polish Round 2B: Favorites page (done)

Replaced the Favorites `<table>` with a responsive `<ul>` of `.track-row` / `.favorite-item` items using shared components (`.cover`, `.pill`, `.icon-btn`, `.row-clickable`) and theme tokens in `favorites.css`. Original artist casing is preserved and `selectors.py` is untouched. Polish Round 2B (`b2ba81e`) added in `apps/favorites/views.py` by chaining onto `get_favorites_with_details(user)`:
- **Pagination:** `FAVORITES_PER_PAGE = 10`, `"Showing X-Y of N"` counter, elided page navigation (`aria-label`, `aria-current="page"`), invalid pages clamped.
- **Search, filter & sort (GET, no API calls):** `q` (300-char cap, case-insensitive contains), `type` (whitelisted `all`/`song`/`artist`/`album` via `SearchType`; `All` and `Artist` use `Exists` so multi-artist tracks appear once), `sort` (whitelisted `newest`, `oldest`, `title_asc`, `title_desc`, `bpm_asc`, `bpm_desc` with missing BPM always last), `Clear` link when active, and a separate `"No favorites match"` empty state.
- **Artists limit:** `MAX_FAVORITE_ARTISTS = 12` evaluated once into a `list()` and sliced in Python with a muted `"+N more"` suffix. The heading is **intentionally still "Artists in your favorites"**, not "Top Artists": the nested subquery returns every credited artist and does not rank them.
- **900px+ columns:** Fixed-width BPM/duration/date columns and ellipsis-truncated album (blank when missing; no `"— —"`). Below 900px unchanged.
- **Query count:** 5 favorites-data queries (`COUNT(*)`, `LIMIT 10` favorites JOIN, 2 visible-page prefetches, 1 artists SUBQUERY) plus 3 base-template/context-processor queries (8 total on render, zero N+1).
- **SQL debug panel:** `favorites_sql` and `artists_sql` are captured before filtering/pagination/slicing, so the collapsed `<details>` panel (gated behind `SHOW_SQL_PANEL`) still shows the **original** selector queries.

**Rules still in force:**
- Keep the view's context variable names (`favorites`, `favorite_artists`, `show_sql`, `favorites_sql`, `artists_sql`). Avoid N+1 queries and prefetch only the visible page.
- Every color in `favorites.css` comes from tokens. Text stays at least 4.5:1 in both themes, including hover and focus-visible. Rows have no horizontal scroll at 360px.
- The `<details>` panel stays collapsed and legible in dark mode.
- **Don't open or edit `.env`.** To see the panel, the user adds `SHOW_SQL_PANEL=1` to `.env` themselves and restarts the server.
- If tests from the DB activity needed the panel on, they use `SHOW_SQL_PANEL=True` (not `DEBUG=True`). Don't run them against live Supabase.

---

## 8. Phase 5 and Polish Batch 2: Home with orbit (done)

- **Layout:** greeting and search card (with recent-search chips) on top. Below, a two-column `stretch` grid: left is the full-height deep "sky" panel with the orbit; right is "Latest Favorites" and the shared `_taste_summary.html` partial (`get_taste_summary(user, declared_genre)`, the same data as the profile). The old "Recent searches" panel and the three quick-link cards are gone.
- **Orbit:** up to `MAX_ORBIT_PLANETS = 24` favorites across up to 5 concentric rings (newest on the inner ring). Covers are circular. Inner rings fill the panel at the default `1.0x` zoom; outer rings sit beyond the panel edge and come into view when zooming out.
- **Data:** reuse `get_favorites_with_details(user)[:MAX_ORBIT_PLANETS]` from `apps/favorites/selectors.py`. Read-only: **don't modify it** and **don't call `sql_of`** from the home view. It already joins the track and album and prefetches artists, so no N+1 queries. (`Favorite` has no `album` field, so `select_related('album')` would raise `FieldError`.)
- **Speed & Cover Fill:** each ring's orbit speed follows the **average BPM of its tracks** (clamped, with a default when BPM is unknown). Each cover also **spins on its own axis** at a speed based on its own track BPM; `img.orbit-cover` is crop-zoomed inside its circular clip via `--orbit-cover-crop: 1.36` on `.orbit-sky-panel` so letterboxed YouTube thumbnails fill the circle.
- **Interaction (`static/js/home/orbit.js`):**
  - No pause on hover. A keyboard-accessible Pause/Play button (default playing).
  - Zoom `0.6x-1.6x` with `+` / `-` / reset buttons and `Ctrl/Cmd+wheel` only (plain scroll is never hijacked).
  - Pointer-based ring dragging: native link/image dragging is disabled (`draggable="false"`, `-webkit-user-drag: none`, `dragstart` prevented); dragging one planet rotates its whole ring around `getSystemCenter()` (live `stage.getBoundingClientRect()`). A 6px threshold keeps normal clicks working; auto-rotation resumes from the new angle on release.
  - Each planet is a link to the track details page with `aria-label="{title} by {artist}"` (no native `title` attribute). One shared upright `#orbit-shared-tooltip` sits at the top layer of `#orbit-sky-panel` (`z-index: 40`), positioned via `left`/`top` on delegated `pointerover`/`pointermove`/`focusin` and updated during `tick()`, hidden on leave, blur, and drag (`d77a557`, `d5471ec`).
  - **Not built / still pending:** panning the whole orbit (Batch C4).
- **Fallbacks:** `prefers-reduced-motion` gives a static arrangement (dragging disabled). With 0 favorites, ghost dashed planets and a call to action. With 1 to 3, the inner ring fills first. Narrow-screen scaling was specified in Phase 5 and has not been re-verified against the 5-ring layout.
- **Performance:** covers use `loading="lazy"` and `decoding="async"`; animation pauses when the tab is hidden or the panel is offscreen.

---

## 9. Phase 6, Polish Batches 1-2 and Polish Round 2: accessibility, branding and layout (done except as noted)

**Phase 6 (`194e0da`):** contrast audit (4.5:1 for text, 3:1 for UI icons), keyboard-only walkthrough, responsive checks at 1440, 1024, 768 and 390px in both themes, and removal of dead and duplicate CSS.

**Polish Batch 1 (`12751ed`) and Batch 2 (`d3f10a0`):**
- **Header and branding:** removed the `Search` nav link from desktop and mobile nav (the search URL and all other links to it still work). Fixed desktop header symmetry by hiding `.header-actions--mobile` at `>= 992px`, so `Logout` sits at the same inset from the right edge as the logo does from the left, and `#header-theme-toggle` sits immediately left of `Logout`. Page content containers stay narrower than the header **on purpose**. Added the `#i-synthdex-logo` SVG symbol in `templates/common/_icons.html`, shown beside "SynthDex" in the header and in `_auth_brand.html` (login and register).
- **Auth and details:** fixed login/register left brand-panel contrast in dark mode using `--deep` and `--deep-ink`. The track-details back link reads `Back to Results` when opened with the search rail params and `Back to Home` (`home:home`) otherwise.
- **Home:** taste summary replaced Recent searches; orbit changes are in section 8.

**Polish Round 2A (`4e37b54`), 2B (`b2ba81e`), 2C (`d77a557`, `d5471ec`):**
- **Warm light-mode palette:** replaced light-mode purple/aubergine deep tokens (`--deep`, `--deep-surface`, `--deep-ink-muted`, `--deep-border`, `--deep-overlay`, `--color-brand-line`, `--shadow-*`) with dark espresso brown in one clearly commented block in `static/css/common/tokens.css` (previous purple values kept in inline comments for one-block revert; dark mode unchanged; replaced hard-coded `rgba(26, 24, 32, 0.88)` in `home.css` with `var(--deep-overlay)`).
- **Login/register:** removed the duplicate `SynthDex` wordmark from `templates/common/_auth_brand.html` (header already shows it); kept heading, subtext, and logo mark.
- **Whole-row clickable:** added `.row-clickable` / `.row-clickable-link` / `.row-clickable-action` in `static/css/common/components.css` (one anchor per row, full-row hover & `:has(.row-clickable-link:focus-visible)` ring, action buttons elevated above). Applied to search results, favorites, home "Latest Favorites", profile "Your Favorites" & "Recent Searches", and history. (`track_detail.html` `.rail-item` was already a full-row anchor and left as-is.)
- **Favorites & Orbit:** documented in sections 7 and 8.
- **Not built / still pending:** panning the whole orbit (C4), and the animated visualizer-rings background (deferred, last).

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

## 12. Report format (after each piece of work, then stop)

1. Files created and changed.
2. What changed visibly, in plain language.
3. **Screens to screenshot:** URL, state and theme, because the user needs a screenshot of every modified screen for progress evidence.
4. Checks run and their results, and anything not verified.
5. Decisions you made where this file was ambiguous (pick the simplest option consistent with it).
6. The commit hash, plus a reminder that the user pushes.
