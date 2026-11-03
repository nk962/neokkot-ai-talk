#!/usr/bin/env python3
"""애니메이션 안정성 검사 (11-03). 실제 크롬으로 모든 쪽을 처음부터 끝까지 넘기며
화면이 보인 뒤 요소가 자리를 옮긴 순간(layout shift)을 쪽마다 적는다.
python3 motion.py <주소>
"""
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    pg.add_init_script("""
      window.__shifts = [];
      new PerformanceObserver(l => { for (const e of l.getEntries()) {
        const s = document.querySelector('#stage > section.on');
        window.__shifts.push({page: location.hash, id: s && s.id, v: +e.value.toFixed(4), t: Math.round(e.startTime),
          src: (e.sources || []).map(x => x.node ? (x.node.className || x.node.nodeName) : '?').slice(0, 3).join(' / ')});
      }}).observe({type: 'layout-shift', buffered: true});
    """)
    pg.goto(url + '#1')
    pg.wait_for_selector('#stage.ready', state='attached', timeout=30000)
    pg.wait_for_timeout(1500)
    n = pg.evaluate('document.querySelectorAll("#stage > section").length')
    steps = 0
    while True:
        cur = pg.evaluate('location.hash')
        pg.keyboard.press('ArrowRight')
        pg.wait_for_timeout(320)
        steps += 1
        if pg.evaluate('location.hash') == cur and pg.evaluate('document.querySelector("#stage > section.on").querySelectorAll("[data-build-in].pending").length') == 0 and cur == f'#{n}':
            break
        if steps > 1200:
            break
    shifts = pg.evaluate('window.__shifts')
    b.close()
print(f'{n}쪽, 넘김 {steps}번, 자리 이동 {len(shifts)}번, 합계 {sum(s["v"] for s in shifts):.3f}')
for s in shifts[:40]:
    print(s)
