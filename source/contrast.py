#!/usr/bin/env python3
"""글자색과 바탕색 대비 검사 (11-03). 대비가 3 아래면 적는다(글이 안 보이거나 흐린 곳).
python3 contrast.py <site 폴더> <a|b>
"""
import functools, http.server, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

root, theme = Path(sys.argv[1]).resolve(), sys.argv[2]


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(root)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = r"""
() => {
  const rgb = s => { const m = s.match(/[\d.]+/g) || []; return m.map(Number); };
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length === 3 || (c.length === 4 && c[3] > 0.5)) return c; } return [246, 244, 241]; };
  const out = [];
  document.querySelectorAll('#stage > section').forEach((s, i) => {
    s.querySelectorAll('.bd p, .bd li, .keep p, .pill').forEach(p => {
      if (!p.innerText.trim()) return;
      const a = lum(rgb(getComputedStyle(p).color)), b = lum(bgOf(p));
      const cr = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      if (cr < 3) out.push([i + 1, s.id, cr.toFixed(2), p.innerText.trim().slice(0, 30)]);
    });
  });
  return out;
}
"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    pg.goto(f'http://127.0.0.1:{srv.server_port}/{theme}/index.html#1')
    pg.wait_for_selector('#stage.ready', state='attached', timeout=20000)
    pg.wait_for_timeout(1200)
    rows = pg.evaluate(JS)
    b.close()
for r in rows:
    print(*r)
print(f'대비 3 아래: {len(rows)}곳')
