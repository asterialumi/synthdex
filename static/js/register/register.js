(function () {
    var pw1 = document.getElementById('id_password1');
    var pw2 = document.getElementById('id_password2');
    var checklist = document.getElementById('password-checklist');
    var matchHint = document.getElementById('password-match-hint');

    // A short list of very common passwords, mirroring Django's built-in
    // CommonPasswordValidator closely enough for live feedback purposes.
    var commonPasswords = [
        'password', 'password1', '123456', '12345678', 'qwerty',
        'letmein', 'welcome', 'admin', 'iloveyou', 'abc123'
    ];

    function setRule(name, met) {
        if (!checklist) return;
        var li = checklist.querySelector('[data-rule="' + name + '"]');
        if (!li) return;
        li.classList.toggle('is-met', met);
    }

    function evaluatePassword() {
        if (!pw1 || !checklist) return;
        var val = pw1.value;
        setRule('length', val.length >= 8);
        setRule('notnumeric', val.length > 0 && !/^\d+$/.test(val));
        setRule('notcommon', val.length > 0 && commonPasswords.indexOf(val.toLowerCase()) === -1);
    }

    function evaluateMatch() {
        if (!pw1 || !pw2 || !matchHint) return;
        if (pw2.value.length === 0) {
            matchHint.style.display = 'none';
            return;
        }
        matchHint.style.display = 'block';
        if (pw1.value === pw2.value) {
            matchHint.textContent = 'Passwords match.';
            matchHint.style.color = 'var(--color-success)';
        } else {
            matchHint.textContent = 'Passwords do not match yet.';
            matchHint.style.color = 'var(--color-ink-soft)';
        }
    }

    if (pw1) {
        pw1.addEventListener('input', function () {
            evaluatePassword();
            evaluateMatch();
        });
    }
    if (pw2) {
        pw2.addEventListener('input', evaluateMatch);
    }
})();
