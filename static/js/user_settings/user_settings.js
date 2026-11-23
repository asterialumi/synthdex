(function () {
    var toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        try {
            window.localStorage.setItem('synthdex-theme', theme);
        } catch (e) {
            /* localStorage unavailable — the toggle still works for this page load. */
        }
        var headerToggle = document.getElementById('header-theme-toggle');
        if (headerToggle) {
            headerToggle.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
        }
    }

    toggle.addEventListener('change', function () {
        applyTheme(toggle.checked ? 'dark' : 'light');

        var form = toggle.closest('form');
        if (form) {
            form.requestSubmit ? form.requestSubmit() : form.submit();
        }
    });
})();
