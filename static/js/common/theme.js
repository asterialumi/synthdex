/**
 * SynthDex Theme & Header Navigation Controller
 * Handles instant theme switching (localStorage + database persistence)
 * and mobile navigation menu toggling.
 */
(function () {
  'use strict';

  var headerToggle = document.getElementById('header-theme-toggle');
  var mobileToggle = document.getElementById('mobile-menu-toggle');
  var primaryNav = document.getElementById('primary-nav');

  function getActiveTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
  }

  function updateToggleState(theme) {
    var isDark = theme === 'dark';
    if (headerToggle) {
      headerToggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
    }
    var settingsToggle = document.getElementById('theme-toggle');
    if (settingsToggle) {
      settingsToggle.checked = isDark;
    }
  }

  function saveThemeToServer(isDark) {
    var metaAuth = document.querySelector('meta[name="user-authenticated"]');
    if (!metaAuth || metaAuth.content !== 'true') {
      return;
    }

    var settingsUrlMeta = document.querySelector('meta[name="settings-url"]');
    if (!settingsUrlMeta) {
      return;
    }

    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    var csrfToken = csrfMeta ? csrfMeta.content : '';
    if (!csrfToken) {
      var match = document.cookie.match(/csrftoken=([^;]+)/);
      if (match) {
        csrfToken = match[1];
      }
    }

    var formData = new FormData();
    formData.append('form_id', 'theme');
    formData.append('csrfmiddlewaretoken', csrfToken);
    if (isDark) {
      formData.append('dark_mode', 'on');
    }

    fetch(settingsUrlMeta.content, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    }).catch(function () {
      // Non-blocking background sync
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      window.localStorage.setItem('synthdex-theme', theme);
    } catch (e) {
      // localStorage disabled / private mode
    }
    updateToggleState(theme);
    saveThemeToServer(theme === 'dark');
  }

  // Initialize toggle button state based on current page theme
  updateToggleState(getActiveTheme());

  // Listen for header theme toggle clicks
  if (headerToggle) {
    headerToggle.addEventListener('click', function () {
      var nextTheme = getActiveTheme() === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
    });
  }

  // Mobile navigation drawer toggle (< 992px)
  if (mobileToggle && primaryNav) {
    mobileToggle.addEventListener('click', function () {
      var isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
      mobileToggle.setAttribute('aria-expanded', isExpanded ? 'false' : 'true');
      primaryNav.classList.toggle('is-open', !isExpanded);
    });

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && primaryNav.classList.contains('is-open')) {
        primaryNav.classList.remove('is-open');
        mobileToggle.setAttribute('aria-expanded', 'false');
        mobileToggle.focus();
      }
    });

    // Close when clicking outside header
    document.addEventListener('click', function (e) {
      if (primaryNav.classList.contains('is-open') &&
          !primaryNav.contains(e.target) &&
          !mobileToggle.contains(e.target)) {
        primaryNav.classList.remove('is-open');
        mobileToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }
})();
