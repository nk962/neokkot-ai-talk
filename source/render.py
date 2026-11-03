#!/usr/bin/env python3
"""뽑은 내용(content.json)을 새 디자인으로 굽는다 (11-03). 아티팩트 코드는 쓰지 않는다.

python3 render.py <content.json> <그림 폴더> <출력 폴더> <a|b>
- a(1안): Pretendard, 흰 바탕, 짧은 장은 첫 줄 높이 고정
- b(2안): 학원 사이트 글꼴(Paperlogy 제목 · KoPub 돋움 Light 본문), 바탕 #F6F4F1,
  핀 장표 요소(알약 이름표 · 동그라미 화살표 · 장 나누기 큰 번호 · 둥근 카드 · 두 색 문장), 짧은 장은 아래에 앉힌다
색은 두 안 모두 강연 장표 색 그대로: 오렌지 #FF6A00 · 글자 #1F1B18 · 회색 #6B6560 · 바탕 #F6F4F1 · 선 #E4E0DB
"""
import html, json, re, shutil, sys
from pathlib import Path

content, asset_dir, out, theme = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
here = Path(__file__).parent
deck = json.loads(content.read_text())
out.mkdir(parents=True, exist_ok=True)
(out / 'assets').mkdir(exist_ok=True)
assets = {p.stem: p for p in asset_dir.iterdir() if re.fullmatch(r'[0-9a-f]{32}', p.stem)}
used = set()

META = 'AI 강연 <em>|</em> 우리 학원과 강의를 위해, AI 어디까지 활용해 볼 수 있을까?'
FOOT = '너희가 꽃이다 <em>|</em> 권나윤'
ORDINAL = {'첫': '01', '두': '02', '세': '03', '네': '04', '다섯': '05', '여섯': '06', '일곱': '07'}

# 아이콘 모양(lucide)만 가져온다. 선 굵기 · 색은 테마 CSS 가 정한다
ICONS = {
    'Book': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
    'Chart': '<path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="6"/><rect x="12" y="8" width="3" height="10"/><rect x="17" y="5" width="3" height="13"/>',
    'Chat': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    'Clock': '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    'ListChecks': '<path d="m3 7 2 2 4-4"/><path d="m3 17 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
    'PaperPlane': '<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>',
    'Play': '<circle cx="12" cy="12" r="10"/><path d="m10 8 6 4-6 4z"/>',
    'Search': '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    'UserPlus': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6"/><path d="M22 11h-6"/>',
    'Users': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'Wallet': '<path d="M20 7H5a2 2 0 0 1 0-4h13v4"/><path d="M3 5v14a2 2 0 0 0 2 2h15V7"/><circle cx="16" cy="14" r="1.5"/>',
}
ARROW = {'arrow-right': 'M5 12h14M13 6l6 6-6 6', 'arrow-left': 'M19 12H5M11 6l-6 6 6 6',
         'arrow-up': 'M12 19V5M6 11l6-6 6 6', 'arrow-down': 'M12 5v14M6 13l6 6 6-6',
         'corner': 'M7 7l10 10M17 9v8H9'}


def svg(d, cls):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>')


def plain(h):
    return re.sub(r'<[^>]+>', '', h).strip()


def asset(src):
    i = src.rsplit('/', 1)[-1]
    p = assets.get(i)
    if not p:
        sys.exit(f'그림 없음: {i}')
    used.add(p)
    return f'assets/{p.name}'


def attrs(n, cls):
    if n.get('space'):
        cls += ' sp'
    a = f' class="{cls}"'
    if n.get('build'):
        a += f' data-build-in="{n["build"]}"'
    return a


def is_tag(n):
    """상자 안 짧은 오렌지 글(1 · 02 · STEP 1)은 이름표로 그린다"""
    return n['t'] == 'text' and n['tone'] == 'accent' and len(plain(n['html'])) <= 8 and '<br>' not in n['html']


CTX = {'title': False}  # 쪽마다 첫 제목을 지났는지


def role(n, in_box):
    """원본 크기 단계 대신 역할로 크기를 정한다. 크기는 theme 의 r-* 다섯 단계 + 카드 두 단계"""
    big, bold, short = n['step'] in ('m', 'l', 'xl'), n.get('bold') or n.get('head'), len(plain(n['html'])) <= 30
    if in_box:
        return 'r-ctitle' if (bold or big) else 'r-cbody'
    if n['tone'] == 'accent' and short and n['step'] in ('xs', 's') or n.get('sub'):
        return 'r-label'
    if n.get('head') or (bold and big):
        return 'r-title'  # 같은 수준의 제목은 덱 전체에서 한 크기
    return 'r-strong' if bold else 'r-body'  # 문장은 원본 크기와 상관없이 한 크기


def text(n, in_box=False):
    if plain(n['html']) == '|':
        return ''  # 커서 모양 회색 막대(38 core-2). 글이 아닌 장식이라 뺀다(슬기님 11-03)
    if in_box and is_tag(n):
        return f'<p{attrs(n, "tag")}>{n["html"]}</p>'
    if n.get('chip'):
        long = ' chip-long' if len(plain(n['html'])) > 14 else ''
        return f'<p{attrs(n, "t chip chip-" + n["chip"] + long + " " + n["tone"])}>{n["html"]}</p>'
    cls = ['t', role(n, in_box), n['tone']]
    if n.get('bold'):
        cls.append('b')
    if n.get('head'):
        cls.append('h')
    style = f' style="--w:{int(n["w"])}px"' if n.get('w') else ''
    if style:
        cls.append('fw')
    return f'<p{attrs(n, " ".join(cls))}{style}>{n["html"]}</p>'


def render(n, in_box=False):
    t = n['t']
    if t == 'text':
        return text(n, in_box)
    if t == 'rule':
        return '<hr class="rule%s">' % (' short' if n.get('short') else '')
    if t == 'bar':
        return '<span class="bar%s"></span>' % (' on' if n['on'] else '')
    if t == 'img':
        fit = ' contain' if n.get('fit') == 'contain' else ''
        return f'<figure{attrs(n, "im" + fit)}><img src="{asset(n["src"])}" alt="{html.escape(n["alt"])}"></figure>'
    if t == 'video':  # 누르면 재생. 장 넘김 클릭과 겹치지 않게 template 이 영상 클릭은 넘기지 않는다
        return (f'<figure{attrs(n, "vid")}><video controls playsinline preload="auto" poster="{asset(n["poster"])}" '
                f'aria-label="{html.escape(n["alt"])}"><source src="{asset(n["src"])}" type="video/mp4"></video></figure>')
    if t == 'icon':
        return svg(ICONS[n['name']], 'ic ' + n.get('tone', 'accent'))
    if t == 'list':
        tag = 'ol' if n['ordered'] else 'ul'
        return f'<{tag}{attrs(n, "ls")}>' + ''.join(f'<li>{i}</li>' for i in n['items']) + f'</{tag}>'
    if t == 'embed':
        doc = '<!doctype html><meta charset="utf-8"><style>*{letter-spacing:-0.02em}</style>' + n['html']
        w, h = int(n.get('w') or 760), int(n.get('h') or 700)
        return (f'<iframe{attrs(n, "em")} style="width:{w}px;height:{h}px" srcdoc="{html.escape(doc, quote=True)}" '
                f'sandbox="" scrolling="no"></iframe>')
    if t == 'shape':
        if n['kind'] in ARROW and not n['kids']:
            path = '<path d="%s"/>' % ARROW[n['kind']]
            return f'<span{attrs(n, "ar " + n["kind"] + " " + n.get("tone", "accent"))}>{svg(path, "")}</span>'
        inner = ''.join(render(k, True) for k in n['kids'])
        return f'<div{attrs(n, "g g-col box" + (" accent" if n.get("tone") == "accent" else ""))}>{inner}</div>'
    if t == 'group':
        cls = ['g', 'g-' + n['dir']]
        box = n.get('box')
        for k in ('box', 'dark', 'accent', 'rule', 'wrap', 'line', 'step', 'kakao', 'kakaobar', 'right'):
            if n.get(k):
                cls.append(k)
        if n['dir'] == 'row' and any(k['t'] == 'img' for k in n['kids']):
            cls.append('media')
        if n['dir'] == 'row' and any(k['t'] == 'shape' and not k['kids'] for k in n['kids']):
            cls.append('flow')  # 화살표로 잇는 흐름: 칸마다 둥근 카드
        if n['dir'] == 'row' and any(k['t'] == 'embed' for k in n['kids']):
            cls.append('withphone')
        style = f' style="--cols:{n["cols"]}"' if n['dir'] == 'grid' else ''
        inner = ''.join(render(k, in_box or box) for k in n['kids'])
        return f'<div{attrs(n, " ".join(cls))}{style}>{inner}</div>'
    sys.exit(f'모르는 요소: {t}')


# 원래 배치를 살리는 장: 좌표 · 짜임은 그대로, 색은 2안 색으로, 글꼴은 CSS(.keep)가 정한다
KEEP_COLOR = {
    '#111111': '#1f1b18', '#22324f': '#1f1b18',
    '#ff6b1a': '#ff6a00', '#e8590c': '#ff6a00', '#d2470a': '#ff6a00', '#ff7a1a': '#ff6a00',
    '#6b6b6b': '#6b6560', '#555555': '#6b6560', '#8a8a8a': '#6b6560', '#4a4a4a': '#6b6560', '#9a9a9a': '#9c958e',
    '#f7f7f7': '#ffffff', '#f1f1f1': '#ffffff', '#efefef': '#e4e0db',
    '#e3e3e3': '#e4e0db', '#e0e0e0': '#e4e0db', '#bdbdbd': '#c9c3bc', '#c8c8c8': '#c9c3bc', '#cfcfcf': '#c9c3bc',
}
CLIP = {
    'arrow-right': 'polygon(0 30%,60% 30%,60% 0,100% 50%,60% 100%,60% 70%,0 70%)',
    'arrow-left': 'polygon(100% 30%,40% 30%,40% 0,0 50%,40% 100%,40% 70%,100% 70%)',
    'arrow-up': 'polygon(30% 100%,30% 40%,0 40%,50% 0,100% 40%,70% 40%,70% 100%)',
    'arrow-down': 'polygon(30% 0,30% 60%,0 60%,50% 100%,100% 60%,70% 60%,70% 0)',
}


def keep_html(k, extra='', pill=None):
    h = re.sub(r'<aside>.*?</aside>', '', k['html'], flags=re.S)
    if pill:  # 알약과 글이 똑같은 머리말만 숨긴다(카드 안 이름표는 그대로)
        h = re.sub(r'<p (style="[^"]*letter-spacing:\s*2px[^"]*")>' + re.escape(pill) + r'</p>',
                   r'<p class="kick" \1>' + pill + '</p>', h)
    h = re.sub(r'<td>.*?</td>', '', h, flags=re.S)
    h = re.sub(r'#[0-9a-fA-F]{6}\b', lambda m: KEEP_COLOR.get(m.group(0).lower(), m.group(0).lower()), h)
    h = re.sub(r"font-family:\s*(?:'[^']*'|[^;\"'])*?(?=;|\")\s*;?\s*", '', h)
    h = re.sub(r'\sfont-family="[^"]*"', '', h)
    h = re.sub(r'src="/_blob/([0-9a-f]{32})"', lambda m: f'src="{asset(m.group(1))}"', h)

    def shape(m):
        st = (re.search(r'style="([^"]*)"', m.group(1)) or [None, ''])[1]
        kind = re.search(r'kind="([^"]+)"', m.group(1)).group(1)
        extra = f'clip-path:{CLIP[kind]};' if kind in CLIP else ('border-radius:16px;' if kind == 'rounded' else '')
        return f'<div style="{extra}{st}">{m.group(2)}</div>'
    h = re.sub(r'<x-shape([^>]*)>(.*?)</x-shape>', shape, h, flags=re.S)

    def icon(m):
        st = (re.search(r'style="([^"]*)"', m.group(1)) or [None, ''])[1]
        name = re.search(r'name="([^"]+)"', m.group(1)).group(1)
        return svg(ICONS[name], 'kic').replace('<svg ', f'<svg style="{st}" ', 1)
    h = re.sub(r'<x-icon([^>]*)>\s*</x-icon>', icon, h)

    def embed(m):
        st = (re.search(r'style="([^"]*)"', m.group(1)) or [None, ''])[1]
        doc = '<!doctype html><meta charset="utf-8"><style>*{letter-spacing:-0.02em}</style>' + m.group(2)
        return f'<iframe class="em" style="{st}" srcdoc="{html.escape(doc, quote=True)}" sandbox="" scrolling="no"></iframe>'
    h = re.sub(r'<x-embed([^>]*)>(.*?)</x-embed>', embed, h, flags=re.S)
    if re.search(r'<x-|/_blob/', h):
        sys.exit('원래 배치 장에 처리 못 한 요소')
    st = ';'.join(d for d in k['style'].split(';') if d.split(':')[0].strip() not in ('background', 'color', 'font-family'))
    return f'<div class="keep {extra}" style="{st}">{h}</div>'


def scatter_html(k):
    """73 dump: 원본의 흩어진 이름표 좌표를 제목 아래 영역(가로 1680 · 세로 460)으로 줄여 옮긴다. 흩어진 모양은 그대로"""
    pts = []
    for attrs_, txt in re.findall(r'<p ([^>]*position:\s*absolute[^>]*)>(.*?)</p>', k['html']):
        x, y = re.search(r'left:\s*(\d+)px', attrs_), re.search(r'top:\s*(\d+)px', attrs_)
        b = re.search(r'data-build-in="([^"]+)"', attrs_)
        if x and y:
            pts.append((int(x.group(1)), int(y.group(1)), re.sub(r'<[^>]+>', '', txt), b.group(1) if b else ''))
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    out = []
    for x, y, txt, b in pts:  # 원본처럼 하나씩 나타난다(data-build-in)
        nx = (x - x0) / max(1, x1 - x0) * 1380
        ny = (y - y0) / max(1, y1 - y0) * 380
        bi = f' data-build-in="{b}"' if b else ''
        out.append(f'<p class="t chip chip-outline"{bi} style="position:absolute;left:{nx:.0f}px;top:{ny:.0f}px">{txt}</p>')
    return '<div class="scatter">' + ''.join(out) + '</div>'


def kicker_of(body):
    """맨 앞 작은 오렌지 글은 머리말. 제목 묶음 안에 있으면 꺼낸다"""
    first = body[0] if body else None
    if first and first['t'] == 'group' and first['dir'] == 'col' and not first.get('box') and first['kids']:
        k = first['kids'][0]
        if k['t'] == 'text' and k['step'] == 'xs' and k['tone'] == 'accent' and not k.get('build'):
            rest = first['kids'][1:]
            return k['html'], ([dict(first, kids=rest)] if len(rest) > 1 else rest) + body[1:]
    if first and first['t'] == 'text' and first['step'] == 'xs' and first['tone'] == 'accent' and not first.get('build'):
        return first['html'], body[1:]
    return None, body


def kind_of(body):
    if len(body) == 1 and body[0]['t'] == 'text' and body[0]['tone'] == 'accent':
        word = plain(body[0]['html'])
        m = re.fullmatch(r'(첫|두|세|네|다섯|여섯|일곱)\s?번째', word)
        if m:
            return 'divider', ORDINAL[m.group(1)]
    if any(n['t'] == 'video' for n in body):
        return 'compose', None
    if all(n['t'] in ('text', 'list') for n in body):
        return 'statement', None
    if all(n['t'] in ('text', 'list') or (n['t'] == 'group' and n['dir'] == 'col' and not n.get('box')
                                          and all(k['t'] == 'text' for k in n['kids'])) for n in body):
        return 'statement', None
    return 'compose', None


def foot_of(i):
    return f'<footer class="ft"><span>{FOOT}</span><span class="pg">{i:03d}</span>{ARROW_CIRCLE}</footer>'


ARROW_CIRCLE = '<span class="circ">' + svg(f'<path d="{ARROW["corner"]}"/>', '') + '</span>'
# 강연 7부를 여는 장(원본 장 이름 p1~p6 · 44c5cdaa). 덱 순서대로 01~07
PART_IDS = [s['id'] for s in deck['slides'] if re.fullmatch(r'p\d+|44c5cdaa', s['id'])]
sections = []
slides = deck['slides']
last_kicker = None
for i, s in enumerate(slides, 1):
    kicker, body = kicker_of(s['body'])
    if s.get('keeps'):  # 겹친 장의 알약: 처음 나오는 머리말
        kicker = next((kicker_of(b)[0] for b in s['keep_body'] if kicker_of(b)[0]), None)
    kind, num = ('keep', None) if (s.get('keep') or s.get('keeps')) else kind_of(body)
    if kind == 'statement' and not body and kicker:
        kind, body, kicker = 'opener', [{'t': 'text', 'step': 'l', 'tone': 'accent', 'bold': True, 'html': kicker}], None
    solo = kind == 'statement' and len(body) == 1 and body[0]['t'] == 'text' and body[0]['tone'] == 'accent' and len(plain(body[0]['html'])) <= 12
    if s['id'] in PART_IDS:
        kind, num = 'part', f'{PART_IDS.index(s["id"]) + 1:02d}'
        last_kicker = None
        if kicker:  # 부 나눔 장의 머리말(첫번째 이야기)은 알약이 PART 번호라 본문에 남긴다
            body = [{'t': 'text', 'step': 's', 'tone': 'accent', 'bold': True, 'html': kicker}] + body
            kicker = None
    cls = ['s', 's-' + kind]
    if s.get('dark') or kind in ('part', 'opener'):
        cls.append('dark')
    tones = {n.get('tone') for n in body if n['t'] == 'text'} | {k.get('tone') for n in body if n['t'] == 'group' for k in n['kids']}
    def flat(ns):
        for n in ns:
            yield n
            yield from flat(n.get('kids', []))
    if kind == 'compose' and not any(n['t'] in ('img', 'embed', 'shape', 'icon') or n.get('box') or n.get('chip') for n in flat(body)):
        cls.append('textonly')  # 카드 · 그림 없이 글로만 짠 목록은 글을 한 단계 키운다
    if solo:
        cls.append('solo')  # 주황 낱말 하나로 말을 여는 장(왜 쓰는가 · 가설 · CLOSING)
    if kind == 'statement' and 'dim' in tones and tones & {'ink', 'accent'}:
        cls.append('two')
    if s['id'].startswith('cover') or s['id'] == 'welcome':
        cls.append('s-cover')
    # 머리말이 없는 장은 앞 장의 머리말을 이어 받아, 같은 흐름에서 알약이 바뀌지 않게
    if kind == 'part':
        pill = f'PART {num}'
    else:
        if kicker and ' | ' in plain(kicker) and kind == 'keep':
            kicker = kicker.partition(' | ')[0]  # 원래 배치 장은 본문 머리말이 그대로 보이므로 알약만 줄인다
        if kicker and ' | ' in plain(kicker) and kind != 'keep':
            head_k, _, tail_k = kicker.partition(' | ')
            kicker = head_k
            body = [{'t': 'text', 'step': 'xs', 'tone': 'accent', 'bold': True, 'html': tail_k, 'sub': True}] + body
        run = re.sub(r'-\d+[a-z]?$', '', s['id'])  # 같은 흐름: busy · busy-2 · busy-3
        pill = kicker or (last_kicker[1] if last_kicker and last_kicker[0] == run else 'AI 강연')
        if kicker:
            last_kicker = (run, kicker)
    head = (f'<header class="hd">{ARROW_CIRCLE}<span class="pill">{pill}</span>'
            f'<span class="meta">{META}</span></header>')
    if any(n['t'] == 'embed' for n in body):
        texts_ = [n for n in body if n['t'] != 'embed']
        phone = [n for n in body if n['t'] == 'embed']
        body = [{'t': 'group', 'dir': 'row', 'kids': [{'t': 'group', 'dir': 'col', 'kids': texts_}] + phone}]
    if False and kind == 'keep' and s['id'] == 'dump':  # 슬기님: 37쪽은 원래 배치대로(11-03). 흩어 옮기기는 쓰지 않는다
        heads = [n for n in body if n['t'] == 'text' and not n.get('chip')]
        k0 = kicker_of(s['body'])[0] or ''
        if ' | ' in k0:  # 알약에는 앞부분만, 뒷부분(첫째, 쏟아 놓기)은 제목 위 머리말로
            heads = [{'t': 'text', 'step': 'xs', 'tone': 'accent', 'bold': True, 'html': k0.partition(' | ')[2], 'sub': True}] + heads
        CTX['title'] = False
        inner = ''.join(render(n) for n in heads) + scatter_html(s['keep'])
        sections.append(f'<section id="dump" class="s s-compose">{head}<div class="bd">{inner}</div>{foot_of(i)}</section>')
        continue
    if kind == 'keep':
        if s.get('keeps'):  # 같은 위치에서 바뀌는 연속 장: 겹쳐 두고 클릭마다 다음 장으로
            layers = ''.join(keep_html(k, f'layer" data-build-in="swap {j}' if j else 'layer', pill)
                             for j, k in enumerate(s['keeps']))
            sections.append(f'<section id="{s["id"]}" class="{" ".join(cls)} layered">{layers}{head}{foot_of(i)}</section>')
        else:
            sections.append(f'<section id="{s["id"]}" class="{" ".join(cls)}">{keep_html(s["keep"], "", pill)}{head}{foot_of(i)}</section>')
        continue
    if len(s.get('members', [])) > 1:
        cls.append('multi')
    CTX['title'] = False
    inner = ''
    if kicker:
        inner += f'<p class="k">{kicker}</p>'
    if kind in ('divider', 'part'):
        inner += f'<p class="num">{num}</p>'
    inner += ''.join(render(n) for n in body)
    foot = foot_of(i)
    sections.append(f'<section id="{s["id"]}" class="{" ".join(cls)}">{head}<div class="bd">{inner}</div>{foot}</section>')

for p in used:
    shutil.copy2(p, out / 'assets' / p.name)
fonts_src = here / 'fonts' if (here / 'fonts').exists() else here.parent / 'fonts'  # 저장소에서는 source/ 옆 fonts/
if fonts_src.resolve() != (out / 'fonts').resolve():
    shutil.copytree(fonts_src, out / 'fonts', dirs_exist_ok=True)
tpl = (here / 'template.html').read_text()
css = (here / f'theme-{theme}.css').read_text()
page = (tpl.replace('{{TITLE}}', '원장과 강사를 위한 AI 강연 | 너희가 꽃이다')
           .replace('{{THEME}}', css)
           .replace('{{SLIDES}}', '\n'.join(sections)))
(out / 'index.html').write_text(page)
print(f'{theme}: {len(sections)}장, 그림 {len(used)}개 → {out}')
