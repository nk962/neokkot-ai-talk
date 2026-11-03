#!/usr/bin/env python3
"""구운 판을 장마다 찍어 12장씩 한 판(contact sheet)으로 모으고, 넘친 장을 적는다 (11-03).

python3 sheets.py <site 폴더> <a|b> <출력 폴더> [첫 장 번호] [마지막 장 번호]
"""
import functools, http.server, sys, threading, io
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

root, theme, out = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3])
lo = int(sys.argv[4]) if len(sys.argv) > 4 else 1
out.mkdir(parents=True, exist_ok=True)


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(root)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
W, H = 480, 270
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    pg.goto(f'http://127.0.0.1:{srv.server_port}/{theme}/index.html#1')
    pg.wait_for_selector('#stage.ready', state='attached', timeout=20000)
    pg.evaluate('document.fonts.ready')
    pg.wait_for_timeout(800)
    n = pg.evaluate('document.querySelectorAll("#stage > section").length')
    hi = int(sys.argv[5]) if len(sys.argv) > 5 else n
    report = pg.evaluate('''() => Array.from(document.querySelectorAll('#stage > section')).map((s, i) => {
        const bd = s.querySelector('.bd');
        if (!bd) return [i + 1, s.id, 1, false];
        let top = 1e9, bottom = 0, right = 0;
        for (const el of bd.children) { if (getComputedStyle(el).position === 'absolute') continue; top = Math.min(top, el.offsetTop); bottom = Math.max(bottom, el.offsetTop + el.offsetHeight); right = Math.max(right, el.offsetLeft + el.offsetWidth); }
        return [i + 1, s.id, +s.dataset.k, top < -1 || bottom > bd.clientHeight + 1 || right > bd.clientWidth + 1];
    })''')
    for i, sid, k, over in report:
        if over or k < 0.8:
            print(f'{i:3d} {sid:18s} 배율 {k:.2f}' + ('  넘침' if over else ''))
    shots = []
    for i in range(lo, hi + 1):
        pg.evaluate(f'location.hash = "#{i}"')
        pg.wait_for_timeout(350)
        pg.evaluate('document.querySelectorAll("#stage > section.on .pending").forEach(e => e.classList.remove("pending"))')
        pg.wait_for_timeout(320)
        im = Image.open(io.BytesIO(pg.screenshot())).convert('RGB').resize((W, H), Image.LANCZOS)
        shots.append((i, report[i - 1][1], im))
    b.close()

for c in range(0, len(shots), 12):
    part = shots[c:c + 12]
    sheet = Image.new('RGB', (3 * W + 4 * 8, 4 * (H + 22) + 8), (128, 128, 128))
    d = ImageDraw.Draw(sheet)
    for j, (i, sid, im) in enumerate(part):
        x, y = 8 + (j % 3) * (W + 8), 8 + (j // 3) * (H + 22)
        d.text((x, y), f'{i} {sid}', fill=(255, 255, 255))
        sheet.paste(im, (x, y + 14))
    sheet.save(out / f'{theme}_{part[0][0]:03d}.png')
print(f'{len(shots)}장 → {out}')
