#!/usr/bin/env python3
"""브라우저에서 실제로 보이는 글로 사라진 줄을 다시 찾는다(숨긴 글은 세지 않음) (11-03, 2차).

python3 verify_visible.py <content_rev.json> <site 폴더> <a|b>
클릭으로 나타나는 글 · 겹친 장은 모두 펼친 뒤, 장마다 innerText(화면에 보이는 글)와 머리 줄 알약을 모은다.
"""
import functools, http.server, json, re, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
from verify_pages import slide_lines, norm  # noqa: E402  (같은 기준 줄을 쓴다)

rev = json.loads(Path(sys.argv[1]).read_text())
root, theme = Path(sys.argv[2]).resolve(), sys.argv[3]


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(root)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    pg.goto(f'http://127.0.0.1:{srv.server_port}/{theme}/index.html#1')
    pg.wait_for_selector('#stage.ready', state='attached', timeout=20000)
    pg.wait_for_timeout(1200)
    pg.add_style_tag(content='#stage > section { visibility: visible !important; opacity: 1 !important; } '
                             '[data-build-in].pending, .keep.layer { opacity: 1 !important; visibility: visible !important; } '
                             '#stage > section, [data-build-in], .keep.layer { transition: none !important; }')
    pg.wait_for_timeout(800)
    texts = pg.evaluate('''() => Array.from(document.querySelectorAll('#stage > section')).map(s => {
        const frames = Array.from(s.querySelectorAll('iframe')).map(f => f.contentDocument ? f.contentDocument.body.innerText : '');
        return s.innerText + frames.join(' ');
    })''')
    b.close()
got = norm(' '.join(texts))
miss = [(s['id'], ln.strip()) for s in rev['slides'] for ln in slide_lines(s) if norm(ln) and norm(ln) not in got]
print(f"화면에 보이는 글 기준, {len(rev['slides'])}장의 글 줄 가운데 빠진 줄: {len(miss)}")
for sid, ln in miss[:40]:
    print(f'  {sid}: {ln[:70]}')
