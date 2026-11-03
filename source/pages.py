#!/usr/bin/env python3
"""같은 흐름의 장을 한 쪽에 모아 쪽 수를 줄인다 (11-03, 2차 200쪽판).

python3 pages.py <content_rev.json> <heights.json> <출력 json> [한 쪽 높이 상한]

- 같은 흐름 = 장 이름의 뿌리가 같은 장(origin · origin-2 · origin-3). 차례대로 한 쪽에 담되 높이 합이 상한을 넘지 않게
- 한 쪽에 모인 둘째 장부터는 클릭할 때마다 차례로 나타난다(data-build-in). 발표 흐름은 그대로, 쪽 수만 준다
- 따로 두는 장: 배치가 곧 내용인 장(keep), 부 나눔 7장, 표지 4장, 폰 화면(embed)
- 소항목 장(첫 번째 · 두 번째)은 다음 장 머리에 붙인다
- 같은 쪽에 같은 글이 두 번 나오면 하나만 남긴다(글은 사라지지 않는다). 머리말이 첫 장과 같으면 뺀다
"""
import json, re, sys
from pathlib import Path

src, hpath, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
CAP = int(sys.argv[4]) if len(sys.argv) > 4 else 700
GAP = 40
deck = json.loads(src.read_text())
H = json.loads(hpath.read_text())
SOLO = {'welcome', 'cover', 'cover-2', 'cover-3'}
PART = re.compile(r'p\d+|44c5cdaa')
ORDINAL = re.compile(r'(첫|두|세|네|다섯|여섯|일곱)\s?번째')


def plain(h):
    return re.sub(r'<[^>]+>', '', h).replace('&amp;', '&').strip()


def run_of(sid):
    return re.sub(r'-\d+[a-z]?$', '', sid)


def solid(s):
    return bool(s.get('keep')) or PART.fullmatch(s['id']) or s['id'] in SOLO or H.get(s['id']) is None \
        or any(n['t'] in ('embed', 'video') for n in s['body'])


def ordinal(s):
    b = s['body']
    return len(b) == 1 and b[0]['t'] == 'text' and ORDINAL.fullmatch(plain(b[0]['html']))


def kicker(body):
    n = body[0] if body else None
    if n and n['t'] == 'group' and n['dir'] == 'col' and not n.get('box') and n['kids']:
        n = n['kids'][0]
    if n and n['t'] == 'text' and n['step'] == 'xs' and n['tone'] == 'accent':
        return plain(n['html'])
    return None


def drop_text(nodes, seen):
    """seen 에 이미 있는 글(4자 넘는 것)을 빼고 돌려준다"""
    outn = []
    for n in nodes:
        if n['t'] == 'text':
            p = plain(n['html'])
            if len(p) > 3 and p in seen:
                continue
            seen.add(p)
        if n.get('kids'):
            n = dict(n, kids=drop_text(n['kids'], seen))
            if not n['kids']:
                continue
        outn.append(n)
    return outn


def texts(nodes):
    for n in nodes:
        if n['t'] == 'text':
            yield plain(n['html'])
        yield from texts(n.get('kids', []))


def opens(x):
    """머리말을 빼고 첫 글이 제목(h2 · 큰 굵은 글)이면 새 주제를 여는 장"""
    b = x['body'][1:] if kicker(x['body']) and x['body'][0]['t'] == 'text' else x['body']
    n = b[0] if b else None
    while n and n['t'] == 'group' and n['dir'] == 'col' and not n.get('box') and n['kids']:
        n = n['kids'][0]
    return bool(n and n['t'] == 'text' and (n.get('head') or (n.get('bold') and n['step'] in ('m', 'l', 'xl'))))


def arrow_card(x):
    b = x['body'][1:] if kicker(x['body']) and x['body'][0]['t'] == 'text' else x['body']
    return b[0] if len(b) == 1 and b[0]['t'] == 'group' and b[0]['kids'] and b[0]['kids'][0]['t'] == 'shape' else None


# 0. 표지 정리(슬기님 11-03): 날짜 줄은 첫 표지에만 두고, 한 줄짜리 book-2(2025년과 2026년, 현재까지)는
#    셋째 표지의 숫자(외부 교육 100시간 | 현장 활용 5,000시간+) 아래로 옮긴다 [나윤님 확인]
def _strip_date(body, date):
    out = []
    for n in body:
        if n['t'] == 'text' and plain(n['html']) == date:
            continue
        if n.get('kids'):
            n = dict(n, kids=_strip_date(n['kids'], date))
        out.append(n)
    return out


slides0, book = [], None
date = next((plain(n['html']) for x in deck['slides'] if x['id'] == 'cover' for n in x['body']
             if n['t'] == 'text' and plain(n['html']).startswith('2026.')), None)
for x in deck['slides']:
    if x['id'] in ('cover-2', 'cover-3') and date:
        x = dict(x, body=_strip_date(x['body'], date))
    if x['id'] == 'book-2':
        book = x
        continue
    slides0.append(x)
if book:
    for i, x in enumerate(slides0):
        if x['id'] == 'cover-3':
            line = dict(book['body'][0], step='s', tone='dim', bold=False)
            slides0[i] = dict(x, body=x['body'] + [line], members=['book-2'])
deck['slides'] = slides0

# 1. 소항목 장을 다음 장 머리에 붙인다
units, carry = [], None
for s in deck['slides']:
    if ordinal(s):
        carry = s
        continue
    if carry and solid(s):  # 원래 배치를 살린 장 앞이면 붙이지 않고 따로 둔다(그 장은 본문 대신 원본 배치를 그린다)
        units.append(carry)
        carry = None
    if carry:
        lab = dict(carry['body'][0], step='s', tone='accent', bold=True)
        b = s['body']
        at = 1 if kicker(b) and b[0]['t'] == 'text' else 0  # 머리말 뒤에 붙여야 머리말이 알약으로 간다
        s = dict(s, body=b[:at] + [lab] + b[at:], members=[carry['id']] + s.get('members', []))
        H[s['id']] = (H.get(s['id']) or 0) + 90 if H.get(s['id']) is not None else None
        carry = None
    units.append(s)

# 2. 같은 흐름끼리 높이 상한 안에서 모은다. 머리말이 없거나 같은 머리말인 바로 다음 장도 같은 흐름으로 본다.
#    원래 배치를 살린 장은 같은 흐름끼리 한 쪽에 겹쳐 두고, 클릭할 때마다 같은 위치에서 다음 장으로 바뀐다
pages, cur, cur_h = [], [], 0
for s in units:
    h = H.get(s['id'])
    if cur and s.get('keep') and cur[-1].get('keep') and run_of(s['id']) == run_of(cur[-1]['id']) and len(cur) < 5:
        cur.append(s)
        continue
    same = run_of(s['id']) == run_of(cur[0]['id']) if cur else False
    # 이웃 장은 제목으로 시작하지 않을 때만 붙인다(새 주제의 제목이 앞 쪽 맨 아래에 붙지 않게)
    follows = cur and kicker(s['body']) in (None, kicker(cur[0]['body'])) and not opens(s)
    ok = cur and not solid(s) and not solid(cur[0]) and (same or follows) and len(cur) < 6 \
        and (cur_h + GAP + h <= (CAP * 1.15 if same else CAP) or (same and arrow_card(s) and len(cur) < 5))
    if ok:
        cur.append(s)
        cur_h += GAP + h
        continue
    if cur:
        pages.append(cur)
    cur, cur_h = [s], (h or 0)
pages.append(cur)

# 3. 쪽 만들기
outs = []
for grp in pages:
    first = grp[0]
    if first.get('keep') and len(grp) > 1:
        outs.append({'id': first['id'], 'body': [], 'note': '\n\n'.join(x.get('note', '') for x in grp if x.get('note')),
                     'keeps': [x['keep'] for x in grp], 'keep_ids': [x['id'] for x in grp],
                     'members': [x['id'] for x in grp], 'keep_body': [x['body'] for x in grp]})
        continue
    if len(grp) == 1:
        outs.append(dict(first, body=drop_text(first['body'], set()), members=first.get('members', []) + [first['id']]))
        continue
    k = kicker(first['body'])
    seen = set()
    body = drop_text(list(first['body']), seen)
    # 화살표 카드(화살표 + 낱말 + 설명)만 이어지는 흐름은 한 줄 카드로(중요도 ↑ · 난이도 ↓ · 귀찮음 ↑ · 반복 ↑)
    cards = [arrow_card(x) for x in grp[1:]]
    if len(cards) >= 2 and all(cards):
        body.append({'t': 'group', 'dir': 'grid', 'cols': len(cards),
                     'kids': [dict(c, box=True, build=f'fade {i}') for i, c in enumerate(cards, 1)]})
        outs.append({'id': first['id'], 'body': body, 'note': '\n\n'.join(x.get('note', '') for x in grp if x.get('note')),
                     'members': [m for x in grp for m in x.get('members', []) + [x['id']]]})
        continue
    for i, s in enumerate(grp[1:], 1):
        b = s['body']
        if k and kicker(b) == k:
            b = b[1:] if b[0]['t'] == 'text' else [dict(b[0], kids=b[0]['kids'][1:])] + b[1:]
        b = drop_text(b, seen)
        if b:
            body.append({'t': 'group', 'dir': 'col', 'kids': b, 'build': f'fade {i}', 'step': True})
    members = [m for s in grp for m in s.get('members', []) + [s['id']]]
    outs.append({'id': first['id'], 'body': body, 'note': '\n\n'.join(s.get('note', '') for s in grp if s.get('note')),
                 'members': members, **({'dark': True} if first.get('dark') else {})})

out.write_text(json.dumps(dict(deck, slides=outs), ensure_ascii=False, indent=1))
print(f'{len(deck["slides"])}장 → {len(outs)}쪽 (상한 {CAP}px) → {out}')
