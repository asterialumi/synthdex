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
    }

    toggle.addEventListener('change', function () {
        // Instant visual feedback, no reload needed to see the switch.
        applyTheme(toggle.checked ? 'dark' : 'light');

        // Persist the choice to the database (survives across devices)
        // by submitting the form it lives in.
        var form = toggle.closest('form');
        if (form) {
            form.requestSubmit ? form.requestSubmit() : form.submit();
        }
    });
})();
