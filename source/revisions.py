#!/usr/bin/env python3
"""권나윤 님 수정본(카톡 11-03 19:47 수정한_장표_25장.pdf, 20:13 수업 영상 3장)을 content.json 에 반영한다 (11-03).

python3 revisions.py <content.json> <출력 json>
PDF 에 글자 층이 없어 쪽 그림을 보고 옮겨 적었다. 쪽 번호는 PDF 쪽.
- 바꿈: 원본 장 id 의 내용을 수정본으로 바꾼다(REPLACE)
- 끼움: 원본 장 뒤에 새 장을 넣는다(INSERT)
- 같음: PDF 1 · 2 · 7 · 9쪽은 원본(meetings-2 · meetings-3 · compare-4 · compare-6)과 글이 같아 그대로 둔다
"""
import json, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
deck = json.loads(src.read_text())


def T(html, step='s', tone='ink', bold=False, head=False):
    n = {'t': 'text', 'step': step, 'tone': tone, 'bold': bold, 'html': html}
    if head:
        n['head'] = True
    return n


def K(html):
    return T(html, 'xs', 'accent', True)


def H(html, step='l'):
    return T(html, step, 'ink', True, True)


def col(*kids, box=False):
    n = {'t': 'group', 'dir': 'col', 'kids': list(kids)}
    if box:
        n['box'] = True
    return n


def row(*kids, wrap=False):
    n = {'t': 'group', 'dir': 'row', 'kids': list(kids)}
    if wrap:
        n['wrap'] = True
    return n


def grid(cols, *kids):
    return {'t': 'group', 'dir': 'grid', 'cols': cols, 'kids': list(kids)}


def chip(html):
    n = T(html, 'xs', 'ink', True)
    n['chip'] = 'outline'
    return n


ARROW = {'t': 'shape', 'kind': 'arrow-right', 'kids': [], 'tone': 'accent'}


def proscons(good, careful, chips):
    return [row(col(T('좋은 점', 'xs', 'accent', True), *[T(g, 's', 'ink', True) for g in good], box=True),
                col(T('알아둘 점', 'xs', 'accent', True), *[T(c, 's', 'ink', True) for c in careful], box=True)),
            row(*[chip(c) for c in chips], wrap=True)]


def steps(items):
    kids = []
    for i, (num, name, sub) in enumerate(items):
        if i:
            kids.append(ARROW)
        card = [T(num, 'xs', 'accent', True), T(name, 's', 'ink', True)]
        if sub:
            card.append(T(sub, 'xs', 'dim'))
        kids.append(col(*card, box=True))
    return row(*kids)


TOOL = '쓰는 도구 | 세 AI 비교'
REPLACE = {
    # PDF 3쪽: 1부 여는 장
    '44c5cdaa': [T('첫번째 이야기', 'xs', 'accent', True), H('나는 어떤 도구를 선택했나?')],
    # PDF 4쪽
    'compare': [K(TOOL), H('보통 많이 쓰는 대표 3가지 AI', 'm'),
                grid(3, col(T('GPT', 'm', 'ink', True), T('ChatGPT', 'xs', 'dim'), box=True),
                     col(T('클로드', 'm', 'ink', True), T('Claude', 'xs', 'dim'), box=True),
                     col(T('제미나이', 'm', 'ink', True), T('Gemini', 'xs', 'dim'), box=True))],
    # PDF 6쪽
    'compare-3': [K(TOOL), H('GPT | ChatGPT', 'm')] + proscons(
        ['가장 쉬운 시작', '그림·사진 생성', '녹음 요약', 'Work 모드(7월 출시)'],
        ['결과는 화면 글', '무료는 낮은 모델', '자주 바뀌는 메뉴'], ['아이디어', '해석', '카드뉴스 그림']),
    # PDF 8쪽
    'compare-5': [K(TOOL), H('제미나이 | Gemini', 'm')] + proscons(
        ['구글과 한 몸', '긴 자료를 한 번에', '내 자료만 근거로', '그림 생성·편집'],
        ['흩어진 기능', '내 폴더와 거리', '결과는 화면 글'], ['구글 드라이브 작업', '긴 PDF·영상 정리']),
    # PDF 10쪽
    'compare-7': [K(TOOL), H('클로드 코드', 'm')] + proscons(
        ['파일로 끝난다', '원문이 안 바뀐다', 'AI끼리 검수', '규칙이 쌓인다'],
        ['세팅이 고비', '쓸수록 비용', '그림 생성은 없음', '배우는 시간'], ['시험지·교재 한 권', '매주 같은 틀 반복', '검수까지']),
    # PDF 11쪽
    'inbox-me-3': [K('내 일을 해체하기'), H('일을 끝내면, 어디에 보관하고 전달할까?', 'm'),
                   row(col(T('보관', 'xs', 'accent', True), T('내 로컬 · 노션', 'm', 'ink', True), box=True),
                       col(T('전달', 'xs', 'accent', True), T('카톡', 'm', 'ink', True), box=True))],
    # PDF 12쪽
    'auto-pick-8': [K('제가 자동화한 것 가운데'), T('세 가지 모두,', 'm', 'dim'), T('어떤 말로 시작했는지', 'm', 'dim'),
                    T('어디서 막혔는지', 'm', 'dim'), T('어떻게 돌아가는지를', 'm', 'dim'), T('화면으로 보여 드립니다.', 'm', 'ink', True)],
    # PDF 13쪽
    'a1-4': [K('대표 자동화 1 | 카톡'), H('등록 이후, 이 순서로 자동화합니다', 'm'),
             steps([('02', '번호 저장', '내 연락처에 저장'), ('03', '팀톡 생성', '반톡 초대 + 개별 팀톡'),
                    ('04', '환영 인사', '학부모 · 신규생'), ('05', '케어 일정 조율', ''), ('06', '노션 업로드', '올린 내용은 카톡으로 전송')])],
    # PDF 14쪽(원래 배치를 살리던 장. 수정본이 새 배치라 keep 에서 뺀다)
    'a2-4': [K('대표 자동화 1 | 카톡'), H('AI가 대신 합니다', 'm'),
             steps([('01', '번호 저장', ''), ('02', '카톡 친구 추가', ''), ('03', '관리톡 개설', '팀채팅'),
                    ('04', '인사 · 케어 안내', ''), ('05', '반톡 초대', '')])],
    # PDF 15쪽
    'pub-q': [K('믿을 수 있는가 | 검수'), H('누가 검수를 잘할까?')],
}
INSERT = {
    # PDF 5쪽
    'compare': [('rev-compare-uses', [K('쓰는 도구 | 세 AI의 특징'), H('각 AI, 이런 일에 씁니다', 'm'),
        grid(3, col(T('GPT', 'm', 'accent', True), T('만능 대화 상대', 's', 'ink', True), T('아이디어 · 해석', 'xs', 'dim'), T('그림 · 사진 생성', 'xs', 'dim'), box=True),
             col(T('클로드', 'm', 'accent', True), T('내 폴더에서 일하는 직원', 's', 'ink', True), T('클로드 코드 기준', 'xs', 'dim'), T('교재 · 시험지 제작과 검수', 'xs', 'dim'), box=True),
             col(T('제미나이', 'm', 'accent', True), T('구글 자료를 다루는 조수', 's', 'ink', True), T('구글 문서 · 드라이브', 'xs', 'dim'), T('긴 PDF · 영상 정리', 'xs', 'dim'), box=True))])],
    # PDF 16쪽
    'pub-q': [('rev-pub-publisher', [K('믿을 수 있는가 | 검수'), H('「출판사」는 어떻게 할까?')])],
    # 카톡 11-03 20:13: 수업 영상 → 리뷰 테스트 3장. 영상은 누르면 재생(1.5배속 47초, H.264로 바꿈)
    'b1-7': [
        ('rev-video-1', [K('수업 영상 | 내가 수업에서 한 말'), H('“Is there a law that says I can’t go?” — 캐서린의 당돌함', 'm'),
                         {'t': 'video', 'src': '/_blob/4eea2ef3b7d0449d1dd545defd419e25', 'poster': '/_blob/7ea9b47758367ba5b4e1eb4cec18af7e',
                          'alt': '수업 화면 녹화, 1.5배속 47초'}]),
        ('rev-video-2', [K('수업 영상 → 리뷰 테스트'), H('그 한마디가 문항이 됩니다', 'm'),
                         {'t': 'img', 'src': '/_blob/3e38187b6bdfe5fb88bec1277de1c5ef', 'alt': '대성고1 케어지 수업 Review Test 15번 학생용', 'fit': 'contain'}]),
        ('rev-video-3', [K('수업 영상 → 리뷰 테스트'), H('정답은 수업에서 한 말, bold', 'm'),
                         {'t': 'img', 'src': '/_blob/41dd3eb5d1783f897a93f015b5b9cec1', 'alt': '대성고1 케어지 수업 Review Test 15번 정답판: 정답 ② bold', 'fit': 'contain'}]),
    ],
    # PDF 17~25쪽: 원본에 없는 새 장 9장. 학생이 느끼는 퀄리티(ideal-4) 뒤에 넣는다 [나윤님 확인]
    'ideal-4': [
        ('rev-future-1', [T('앞으로 우리 학원은', 's', 'accent', True), H('자료는 누구나 갖게 됩니다'), T('교재와 문항의 원가는 0에 가까워집니다.', 's', 'dim')]),
        ('rev-future-2', [T('빅북 15회, 주간내신, 취약유형 교재.', 's', 'dim'), T('지금은 밤에 자동으로 뽑고 있지만', 's', 'dim'),
                          T('1~2년 안에 다른 학원도 비슷하게 합니다.', 's', 'dim'), T('「자료 좋은 학원」은', 'm', 'ink', True), T('차별점이 못 됩니다', 'm', 'accent', True)]),
        ('rev-future-3', [T('그래서 남는 것', 's', 'accent', True),
                          row(col(T('01', 'xs', 'accent', True), T('이 아이를 누가 얼마나 잘 아는가', 's', 'ink', True), T('학생의 상태와 기록을 놓치지 않고 아는 일', 'xs', 'dim'), box=True),
                              col(T('02', 'xs', 'accent', True), T('그걸 아이가 직접 느끼는가', 's', 'ink', True), T('알려졌다고 느끼는 순간 학원의 퀄리티가 됩니다', 'xs', 'dim'), box=True))]),
        ('rev-future-4', [T('바로잡고 싶은 세 가지', 's', 'accent', True),
                          grid(3, col(T('01', 'xs', 'accent', True), T('정성은 자동화하는 순간 값이 떨어진다', 's', 'ink', True), T('사람이 시간을 썼다는 사실에서 나옵니다', 'xs', 'dim'), box=True),
                               col(T('02', 'xs', 'accent', True), T('돈을 내는 이유는 성적과 습관', 's', 'ink', True), T('따뜻함에서 끝나지 않고 결과로 이어져야 합니다', 'xs', 'dim'), box=True),
                               col(T('03', 'xs', 'accent', True), T('미친 정성은 사람을 갈아 넣기 쉽다', 's', 'ink', True), T('덜어 준 시간이 아이 앞으로 가는지 재 봅니다', 'xs', 'dim'), box=True))]),
        ('rev-future-5', [T('01 정성의 기준', 's', 'accent', True), H('AI가 했다는 걸 알면<br>가치가 떨어지는 일인가?'),
                          T('그렇다면 사람이 직접 하고,', 's', 'dim'), T('AI는 준비만 합니다.', 's', 'accent', True)]),
        ('rev-future-6', [T('예를 들어', 's', 'accent', True),
                          row(col(T('AI가 하는 것', 'xs', 'dim', True), T('상담 메모와 오답 기록을 정리해 「오늘 꼭 할 말 한 줄」 뽑기', 's', 'ink', True), box=True),
                              col(T('선생님이 하는 것', 'xs', 'accent', True), T('그 말을 아이에게 직접 하기', 's', 'ink', True), box=True))]),
        ('rev-future-7', [T('02 학원의 진짜 자리', 's', 'accent', True), H('아이를 실제로<br>앉혀서 하게 만드는 일'),
                          T('동기를 주고, 약속을 받고,', 's', 'dim'), T('다음 주에 확인합니다.', 's', 'dim'), T('사람이 지켜보고 있다는 압력과 관계', 's', 'accent', True)]),
        ('rev-future-8', [T('03 숫자로 확인', 's', 'accent', True), H('선생님 한 분이 주에<br>학생 한 명당 몇 분을<br>얼굴 보고 쓰는가'),
                          T('이 숫자가 늘지 않으면', 's', 'dim'), T('전략이 작동하지 않는 겁니다.', 's', 'accent', True)]),
        ('rev-future-9', [T('한 줄 정리', 's', 'accent', True),
                          row(col(T('AI', 'xs', 'dim', True), T('이 아이를 아는 일', 'm', 'ink', True), box=True),
                              col(T('사람', 'xs', 'accent', True), T('알려졌다고 느끼게 하는 일, 실제로 하게 만드는 일', 'm', 'ink', True), box=True))]),
    ],
}

slides, seen = [], set()
for s in deck['slides']:
    if s['id'] in REPLACE:
        s = dict(s, body=REPLACE[s['id']], rev='바꿈')
        s.pop('keep', None)
        seen.add(s['id'])
    slides.append(s)
    for nid, body in INSERT.get(s['id'], []):
        slides.append({'id': nid, 'body': body, 'note': '', 'rev': '끼움'})
        seen.add(s['id'])
missing = (set(REPLACE) | set(INSERT)) - seen
if missing:
    sys.exit(f'원본에 없는 장: {missing}')
out.write_text(json.dumps(dict(deck, slides=slides), ensure_ascii=False, indent=1))
print(f'{len(slides)}장 (바꿈 {len(REPLACE)} · 끼움 {sum(len(v) for v in INSERT.values())}) → {out}')
