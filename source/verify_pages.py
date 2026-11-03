#!/usr/bin/env python3
"""쪽을 모은 판에서 사라진 글이 없는지 확인한다 (11-03, 2차).

python3 verify_pages.py <content_rev.json> <site/b/index.html> [<content.json>]
- 기준: content_rev.json(원본 443장 + 나윤님 수정)의 글 줄 하나하나
- 대상: 구운 index.html 의 보이는 글(쪽에 모인 장 · 겹친 장 · 클릭으로 나타나는 글 포함)
- 셋째 인자를 주면 나윤님 수정으로 바뀐 원본 글 줄도 따로 적는다
"""
import html as H, json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup

def norm(t):
    return re.sub(r'\s+', '', H.unescape(t))


def text_only(h):
    soup = BeautifulSoup(h, 'html.parser')
    for x in soup.find_all(['style', 'script']):
        x.extract()
    return soup.get_text(' ')


def lines(nodes):
    for n in nodes:
        if n['t'] == 'text':
            for part in re.split(r'<br\s*/?>', n['html']):
                yield re.sub(r'<[^>]+>', '', part)
        elif n['t'] == 'list':
            yield from (re.sub(r'<[^>]+>', '', i) for i in n['items'])
        elif n['t'] == 'embed':
            yield text_only(n['html'])
        yield from lines(n.get('kids', []))


def slide_lines(s):
    # 머리말 '대표 자동화 1 | 카톡'은 알약(앞)과 본문 머리(뒤)로 나뉘므로 조각마다 찾는다
    for ln in _slide_lines(s):
        if ' | ' in ln and len(ln) < 40:
            yield from ln.split(' | ')
        else:
            yield ln


def _slide_lines(s):
    if s.get('keep'):
        soup = BeautifulSoup(re.sub(r'<td>.*?</td>', '', s['keep']['html'], flags=re.S), 'html.parser')
        for e in soup.find_all(['x-embed']):
            yield text_only(e.decode_contents())
            e.extract()
        for el in soup.find_all(string=True):
            if el.strip():
                yield str(el)
    else:
        yield from lines(s['body'])


if __name__ == '__main__':
    rev = json.loads(Path(sys.argv[1]).read_text())
    page = BeautifulSoup(Path(sys.argv[2]).read_text(), 'html.parser')
    stage = page.find(id='stage')
    for f in stage.find_all('iframe'):
        f.replace_with(BeautifulSoup(text_only(f.get('srcdoc', '')), 'html.parser'))
    for x in stage.find_all(['style', 'script']):
        x.extract()
    for x in stage.select('.hd .meta, .ft'):
        x.extract()
    got = norm(stage.get_text(''))

    missing = []
    for s in rev['slides']:
        for ln in slide_lines(s):
            t = norm(ln)
            if t and t not in got:
                missing.append((s['id'], ln.strip()))
    print(f"기준 {len(rev['slides'])}장의 글 줄 가운데 빠진 줄: {len(missing)}")
    for sid, ln in missing[:40]:
        print(f'  {sid}: {ln[:60]}')

    if len(sys.argv) > 3:
        orig = {s['id']: s for s in json.loads(Path(sys.argv[3]).read_text())['slides']}
        revd = {s['id']: s for s in rev['slides']}
        print('\n나윤님 수정으로 바뀐 원본 글 줄:')
        for sid, s in revd.items():
            if s.get('rev') == '바꿈':
                old = {norm(l): l.strip() for l in slide_lines(orig[sid]) if norm(l)}
                new = {norm(l) for l in slide_lines(s)}
                gone = [v for k, v in old.items() if k not in new]
                if gone:
                    print(f'  {sid}: ' + ' / '.join(gone))
