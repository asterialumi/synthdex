# SynthDex UI Overhaul — Handover Documentation

**Project:** SynthDex (Personal Music Metadata Catalogue)  
**Stack:** Django 6.1.x, Supabase PostgreSQL, Bootstrap 5.3 (CDN) + Custom Modular CSS, Vanilla JS  
**Branch:** `main`  
**Current Status:** Phases 1–4 Completed, Verified, and Committed. Ready for Phase 5 when instructed.

---

## 1. Executive Summary

SynthDex underwent a front-end overhaul to achieve visual cohesion, dark/light theme parity, improved typography, unified form controls, and responsive layouts while strictly preserving existing business logic, database schemas, URL patterns, view contexts, and endpoints. 

Key milestones achieved:
- **Phase 1 (Foundation):** Introduced centralized design tokens (`tokens.css`), 1200px container (`layout.css`), shared UI components (`components.css`), inline SVG sprite (`_icons.html`), responsive aubergine header, and zero-flash theme toggle with local + database persistence.
- **Phase 2 (Forms):** Standardized input controls to 44px touch targets (`forms.css`), custom chevron selects with `@supports (appearance: base-select)` enhancement, accessible focus rings, and reusable `_field.html` template across all views.
- **Phase 3 (Search, Favorites, History):** Corrected search alignment, added double-submit prevention + loading states, desktop 2–3 column favorites grid, history entry deduplication (`×N`), confirmation `<dialog>` for clearing history, and set `TIME_ZONE = 'Asia/Manila'`.
- **Phase 3 Amendment (Taste Profile & Personalization):** Reoriented copy for personal cataloguing, displayed bio & favorite genre on the profile header and home hero, and added a 3-query "Your Taste" summary card with aggregate BPM metrics, top genres, and coverage nudges (with comprehensive test suite).
- **Phase 4 (Track Details & Search Results Rail):** Redesigned track inspection into a 65/35 desktop grid with an independently scrolling, sticky search results rail with query state preservation; deep aubergine hero card with prominent BPM and genre highlights; brand icons for YouTube and Deezer; balanced 2-column info grid; and collapsible manual metadata editing panel.
- **Search Alignment & Cover Art Polish:** Centered the search results column to match the search bar card, refined thumbnail letterbox zoom (1.35x) to eliminate black bars, and eliminated nested border conflicts on track inspection.

---

## 2. Commit Log

| Commit | Scope | Description |
|---|---|---|
| `00586f3` | Phase 1 | `Add design tokens, aubergine header, theme toggle and SVG icons` |
| `c317de4` | Phase 2 | `Unify form styling across profile, settings, search and auth` |
| `a8edcff` | Phase 3 | `Fix search layout and polish results, favorites and history` |
| `9a7d29a` | Phase 3 Amend | `Show bio and favorite genre, add taste summary to profile` |
| `6f83349` | Phase 4 | `Add two-column track details with search results rail` |
| `3fc7cce` | Polish | `Recenter search results and refine track detail cover art styling` |

---

## 3. Detailed Scope & Architecture by Phase

### Phase 1: Design Tokens, Layout, and Header
- **`static/css/common/tokens.css`**: CSS variables for light and dark modes (`--bg`, `--surface`, `--surface-raised`, `--ink`, `--ink-muted`, `--border`, `--accent`, `--accent-ink`, `--deep`, `--deep-surface`, `--deep-ink`, `--deep-border`, `--danger`, `--focus-ring`, spacing, radius, and shadows).
- **`static/css/common/layout.css`**: Shared `.app-container` (1200px max-width, 24px/16px gutters), `.grid-two-col` (65/35 split collapsing at 991px), and accessible `.skip-link`.
- **`static/css/common/components.css`**: Standardized `.btn`, `.icon-btn`, `.pill`, `.card`, `.cover`, `.track-row`, `.empty-state`, and `.toolbar`.
- **`static/css/common/base.css`**: Deep aubergine light-mode header, dark-mode 1px border separation, accessible mobile hamburger navigation, flash messages styling, and `@keyframes rise-in`.
- **`static/js/common/theme.js`**: Instant theme application, `localStorage` fallback for anonymous users, AJAX sync with `user_settings` endpoint for authenticated users, and mobile menu toggle.
- **`templates/common/_icons.html`**: 19 inline SVG symbols (heart, heart-fill, search, external-link, sun, moon, pencil, refresh, history, user, settings, music-note, trash, chevron, check, x, menu, arrow-left, youtube, deezer).

### Phase 2: Form Standardization
- **`static/css/common/forms.css`**: Standard 44px input/select/button heights, vertical-only textareas, inline error alerts with icons, custom SVG chevron for selects, `@supports (appearance: base-select)` native styling, and styled switch toggles.
- **`templates/common/_field.html`**: Reusable field include handling label, input widget, help text, and field errors.
- **Integrated Forms**: Profile form, User Settings forms (Appearance, Preferred Search Type, Change Password), Login, Register, and Catalogue Track Metadata Edit form.

### Phase 3: Search, Favorites, and History
- **Search (`templates/search/results.html`, `static/css/search/search.css`, `static/js/search/search.js`)**:
  - Unified 860px centered column ensuring title, search bar, toolbar, and results list share exact horizontal edges.
  - Consistent track card height, 2-line title clamping, optimistic AJAX heart toggle, and double-submit prevention with loading spinner.
- **Favorites (`templates/favorites/favorites.html`, `static/css/favorites/favorites.css`)**:
  - Responsive desktop grid (`repeat(auto-fill, minmax(340px, 1fr))`), clean mobile fallback, and SVG icon heart buttons.
- **History (`templates/history/history.html`, `static/css/history/history.css`, `apps/history/views.py`)**:
  - Python-level consecutive duplicate search grouping displaying `×N` badges and latest timestamp.
  - Native `<dialog>` confirmation modal for "Clear history".
- **Time Zone**: `config/settings.py` updated to `TIME_ZONE = 'Asia/Manila'` with `USE_TZ = True`.

### Phase 3 Amendment: Taste Summary & Personalization
- **Copy Polish**: Replaced misleading public-facing copy ("This is what other listeners will see") with personal-use copy ("Your taste notes. Only you can see these").
- **Profile Header & Home**: Displays user's declared favorite genre (pill with music note) and bio; home hero subtitle displays user bio with fallback.
- **`apps/favorites/taste.py`**:
  - `get_taste_summary(user, declared_genre='')`: Executes at most 3 targeted, read-only queries (BPM aggregates with `Exists` subquery avoiding duplicate genre joins, top 3 genres, and missing-detail nudges).
  - `format_bpm(value)`: Strips trailing zeroes (e.g., `205.00` $\to$ `"205"`, `128.50` $\to$ `"128.5"`).
- **`apps/favorites/test_taste.py`**: 7 unit test cases covering BPM averages, NULL handling, genre weighting immunity, case-insensitive declared genre matching, user isolation, and empty states.

### Phase 4: Track Details & Search Rail
- **Rail Context (`apps/catalogue/views.py`)**:
  - Reads `?q=<query>&type=<type>` GET parameters (capped to 300 chars, validated against `SearchType.values`).
  - Read-only lookup against `SearchCache` and `SearchCacheResult` (ignoring `expires_at`, no external API calls, zero database writes).
- **Template Filters (`apps/catalogue/templatetags/catalogue_tags.py`)**:
  - `format_bpm`: Clean BPM display without decimals.
  - `source_display_name`: Maps `'youtube'` $\to$ `'YouTube'`, `'deezer'` $\to$ `'Deezer'`, `'spotify'` $\to$ `'Spotify'`.
- **Track Detail Layout (`templates/catalogue/track_detail.html`, `static/css/catalogue/track_detail.css`)**:
  - Desktop 65/35 grid with sticky search results rail (independent scrolling, `.is-current` highlight).
  - Single-column fallback when accessed directly without search parameters.
  - Deep aubergine hero surface in light mode with prominent tempo (BPM) and genre badge strip.
  - Balanced 2-column metadata grid (`Duration` $\vert$ `Tempo`, `Release Year` $\vert$ `ISRC`, full-width `Album` with inline year, and full-width `Genres`).
  - Listen source buttons with official brand SVGs and unified heart toggle.
  - Responsive collapse below 992px with "Back to search results" mobile action button.
- **Cover Art Polish**:
  - Centered letterbox crop (`scale(1.35)`) for 16:9/4:3 YouTube thumbnails.
  - Removed clashing utility borders (`.cover--lg`, `.cover--sm`) so single container borders (`--deep-border` or `--border`) render cleanly.

---

## 4. File Inventory

```
synthdex/
├── apps/
│   ├── catalogue/
│   │   ├── templatetags/
│   │   │   └── catalogue_tags.py         # format_bpm, source_display_name, duration_display
│   │   └── views.py                      # Added rail context to track_detail_view
│   ├── favorites/
│   │   ├── taste.py                      # get_taste_summary(), format_bpm()
│   │   └── test_taste.py                 # 7 unit test cases for taste summaries
│   ├── history/
│   │   └── views.py                      # Consecutive search deduplication
│   ├── profile/
│   │   ├── context_processors.py         # Exposes profile_bio, profile_favorite_genre
│   │   └── views.py                      # Passes taste_summary to profile.html
│   └── user_settings/
│       ├── forms.py                      # Made pref_search_type optional in ThemeForm
│       └── views.py                      # AJAX JsonResponse for instant theme saving
├── config/
│   └── settings.py                       # TIME_ZONE = 'Asia/Manila'
├── static/
│   ├── css/
│   │   ├── catalogue/
│   │   │   └── track_detail.css          # Two-col layout, sticky rail, deep hero, info grid
│   │   ├── common/
│   │   │   ├── base.css                  # Aubergine header, flash messages, mobile nav
│   │   │   ├── components.css            # Buttons, pills, cards, covers, toolbars
│   │   │   ├── forms.css                 # 44px inputs, selects, textareas, switch toggles
│   │   │   ├── layout.css                # 1200px container, grid-two-col, skip link
│   │   │   └── tokens.css                # Full design token system (light & dark)
│   │   ├── favorites/
│   │   │   └── favorites.css             # Desktop 2-3 column card grid
│   │   ├── history/
│   │   │   └── history.css               # Search count badges, modal styles
│   │   ├── profile/
│   │   │   └── profile.css               # Taste card, BPM range bar, missing-details nudge
│   │   └── search/
│   │       └── search.css                # Centered 860px layout, track cards, loading state
│   └── js/
│       ├── common/
│       │   └── theme.js                  # Theme switching & mobile menu handler
│       ├── search/
│       │   └── search.js                 # Double-submit prevention & optimistic heart AJAX
│       └── user_settings/
│           └── user_settings.js          # Sync settings toggle with header toggle
└── templates/
    ├── catalogue/
    │   └── track_detail.html             # 2-col detail view with search rail
    ├── common/
    │   ├── _field.html                   # Reusable form field component
    │   ├── _icons.html                   # 19 inline SVG icons
    │   └── base.html                     # Foundation layout, SVG sprite, token styles
    ├── favorites/
    │   └── favorites.html                # Favorites card grid with unified components
    ├── history/
    │   └── history.html                  # Deduplicated history list with <dialog> modal
    ├── home/
    │   └── home.html                     # Hero subtitle bio display, updated copy
    ├── login/
    │   └── login.html                    # Unified form skinning
    ├── profile/
    │   └── profile.html                  # Header bio & genre, "Your Taste" card
    ├── register/
    │   └── register.html                 # Unified form skinning
    ├── search/
    │   └── results.html                  # Centered layout, rail param passing, SVG icons
    └── user_settings/
        └── settings.html                 # Unified form skinning, synced theme switch
```

---

## 5. Verification Commands

To verify system health at any point:

```powershell
# 1. Django System Checks
& ".\.venv\Scripts\python.exe" manage.py check

# 2. Compile all 15 template files
& ".\.venv\Scripts\python.exe" -c "import django, os, glob; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from django.template.loader import get_template; files = glob.glob('templates/**/*.html', recursive=True); [get_template(f.replace('templates\\', '').replace('\\', '/')) for f in files]; print(f'Successfully compiled {len(files)} templates!')"

# 3. Unit test template filters (format_bpm, source_display_name)
& ".\.venv\Scripts\python.exe" -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from apps.catalogue.templatetags.catalogue_tags import format_bpm, source_display_name; assert format_bpm(205.0) == '205'; assert format_bpm(128.5) == '128.5'; assert format_bpm(None) is None; assert source_display_name('youtube') == 'YouTube'; assert source_display_name('deezer') == 'Deezer'; print('Template filters verified!')"
```

---

## 6. Next Steps: Roadmap for Subsequent Phases

### Phase 5: Home Dashboard with Animated Orbit
*(To be started only upon explicit user command: "start phase 5")*
- **Layout:** Greeting and search card on top. Below, two columns: left is the deep aubergine "sky" panel with the interactive orbit; right is "Latest favorites" and "Recent searches". Remove redundant quick-link cards.
- **Orbit Component:**
  - Center "sun": Vinyl avatar or "Your catalogue" emblem.
  - Planet rings: 3 concentric rings (up to 12 favorite track circular covers, 4 per ring, newest on inner ring).
  - CSS animations: Smooth continuous rotation with counter-rotation transforms so artwork stays upright.
  - BPM-driven speed: Orbit period derived from average BPM of tracks on that ring (clamped between 30s and 120s).
  - Hover & Accessibility: Pauses animation on hover/focus-within; accessible tooltip with title and artist; static fallback for `prefers-reduced-motion`; empty-state dashed rings with CTA when 0 favorites.
- **Data:** Single optimized query via `select_related('album')` passing at most 12 favorites (zero N+1 queries).

### Phase 6: Accessibility, Responsive & Dark Mode Polish
*(To be started only upon explicit user command: "start phase 6")*
- Color contrast audit across all token pairs ($\ge 4.5:1$ text, $\ge 3:1$ UI icons).
- Keyboard-only navigation audit (tab order, focus-visible rings).
- Cross-breakpoint testing across 1440px, 1024px, 768px, and 390px in both themes.
- CSS dead code and redundancy cleanup.

---

## 7. Hard Constraints & Operating Rules

1. **No Schema Changes:** Never modify `models.py` or run `makemigrations`.
2. **Database is Read-Only:** Never insert, update, or delete live rows; never run `manage.py test` against the live Supabase database.
3. **Secrets:** Never open, print, or commit `.env`.
4. **Git Discipline:** Always stage files explicitly by name (never `git add .`); do not push or branch autonomously.
5. **Theme-Safe Styles:** No hard-coded hex colors in component CSS; use token variables from `tokens.css`.
6. **No External Libraries:** Vanilla JS only; no new npm/pip packages or CDN scripts.
