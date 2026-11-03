#!/usr/bin/env python3
"""2안 여백 검수 (11-03). python3 margin.py <site 폴더> <a|b>

장마다 1920x1080 원판에서 잰다.
- 좌우 여백: 글 · 그림이 왼쪽 120 / 오른쪽 1800 밖으로 나감
- 머리 · 꼬리 줄 침범: 내용이 머리 줄(동그라미 · 이름표, 아래 끝) 또는 꼬리 줄(위 끝)과 겹침
- 화면 밖: 0~1920 · 0~1080 밖
- 잘린 글: 글 상자보다 글이 넓거나 높음
- 줄인 장: 넘쳐서 글자 배율을 0.8 아래로 줄인 장(읽기 어려울 수 있음)
"""
import functools, http.server, json, sys, threading
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
  const L = 120, R = 1800, out = [];
  for (const [i, s] of Array.from(document.querySelectorAll('#stage > section')).entries()) {
    const S = s.getBoundingClientRect(), k = S.width / 1920;
    const box = el => { const r = el.getBoundingClientRect(); return [(r.left - S.left) / k, (r.top - S.top) / k, (r.right - S.left) / k, (r.bottom - S.top) / k]; };
    const hd = s.querySelector('.hd'), ft = s.querySelector('.ft');
    const hdB = Math.max(...Array.from(hd.children).map(c => box(c)[3]));
    const ftT = Math.min(...Array.from(ft.children).map(c => box(c)[1]));
    const body = s.querySelector('.bd') || s.querySelector('.keep');
    const leaves = Array.from(body.querySelectorAll('p, h1, h2, h3, li, figure, img, svg, iframe, .chip, .tag, .box, span, text'))
      .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; });
    const hit = (kind, e, b) => out.push([i + 1, s.id, kind, (e.innerText || e.getAttribute('alt') || e.tagName).trim().slice(0, 24), b.map(Math.round)]);
    for (const e of leaves) {
      if (e.closest('svg') && e.tagName.toLowerCase() !== 'svg') continue;
      const b = box(e);
      if (b[0] < -1 || b[1] < -1 || b[2] > 1921 || b[3] > 1081) { hit('화면 밖', e, b); continue; }
      if (b[0] < L - 1 || b[2] > R + 1) hit('좌우 여백', e, b);
      if (b[1] < hdB + 8) hit('머리 줄 겹침', e, b);
      if (b[3] > ftT - 8) hit('꼬리 줄 겹침', e, b);
      if (/^(P|H1|H2|H3|LI)$/.test(e.tagName) && (e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 2) && getComputedStyle(e).overflow !== 'visible') hit('잘린 글', e, b);
    }
    const kk = +(s.dataset.k || 1);
    if (kk < 0.8) out.push([i + 1, s.id, '줄인 장', '배율 ' + kk, []]);
  }
  return out;
}
"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    pg.goto(f'http://127.0.0.1:{srv.server_port}/{theme}/index.html#1')
    pg.evaluate('document.fonts.ready')
    pg.wait_for_timeout(1200)
    # 숨은 장도 재려면 잠깐 모두 보이게
    pg.add_style_tag(content='#stage > section { visibility: visible !important; opacity: 0 !important; } #stage > section.on { opacity: 1 !important; } [data-build-in].pending { opacity: 1 !important; transform: none !important; }')
    pg.wait_for_timeout(300)
    rows = pg.evaluate(JS)
    b.close()

seen = set()
for i, sid, kind, txt, bx in rows:
    key = (i, kind, txt)
    if key in seen:
        continue
    seen.add(key)
    print(f'{i:3d} {sid:16s} {kind:8s} {txt!r:28s} {bx}')
print(f'걸린 장 {len({r[0] for r in rows})}, 걸린 곳 {len(seen)}')
