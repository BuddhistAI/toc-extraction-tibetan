"""toc_lib.py - shared helpers for the Tibetan sa-bcad (outline) TOC task.

* reconstruct_toc(): rebuild the hierarchical outline of a Tibetan commentary from
  the EPUB's `Tibetan-Sabche` paragraphs (ordinal + "ལ་གསུམ" declaration logic).
* render_tree() / render_inline_xml(): turn a flat list of headings
  (depth, start, title) into the two requested output formats.
* round-trip helpers used by the dataset builder, the metric and the tests.
"""
import re
from xml.sax.saxutils import escape, quoteattr, unescape

# ---------------------------------------------------------------- numbers
CARD = {'གཅིག': 1, 'གཉིས': 2, 'གསུམ': 3, 'བཞི': 4, 'ལྔ': 5, 'དྲུག': 6, 'བདུན': 7,
        'བརྒྱད': 8, 'དགུ': 9, 'བཅུ': 10, 'བཅུ་གཅིག': 11, 'བཅུ་གཉིས': 12,
        'བཅུ་གསུམ': 13, 'བཅུ་བཞི': 14, 'བཅོ་ལྔ': 15, 'བཅུ་དྲུག': 16,
        'བཅུ་བདུན': 17, 'བཅོ་བརྒྱད': 18, 'བཅུ་དགུ': 19, 'ཉི་ཤུ': 20}
ORD = {'དང་པོ': 1}
for _w, _v in CARD.items():
    if _v >= 2:
        ORD[_w + '་པ'] = _v
_alt = lambda d: '|'.join(sorted(map(re.escape, d), key=len, reverse=True))
CARD_ALT, ORD_ALT = _alt(CARD), _alt(ORD)
ORD_RE = re.compile(r'^(?:༈\s*)?(' + ORD_ALT + r')(?=[་\s(（]|$)')
D1 = re.compile(r'(?:ལ|ལས)་?(?:དོན་)?(' + CARD_ALT + r')(?:་?(?:ཏེ|སྟེ|ལས))?$')   # "..ལ་གསུམ(་ཏེ)" + list follows
D2 = re.compile(r'(' + CARD_ALT + r')་?(?:ཏེ|སྟེ)$')                          # "..གསུམ་ཏེ"
D3 = re.compile(r'(' + CARD_ALT + r')་?ཡོད་པ་ལས$')                             # "..བརྒྱད་ཡོད་པ་ལས" (no list)


def clean(s):
    return s.replace('༷', '').replace('༌', '་').strip().lstrip('༈').strip()


def cut_label(label):
    """cut a heading label at its first 'ནི'/'ལ' syllable (syllable-level, not substring)."""
    label = label.strip('་ ')
    if label.startswith(('(', '（')):
        m = re.match(r'[(（](.+?)[)）]', label)
        if m:
            return m.group(1).strip('་ ')
    syl = label.split('་')
    for i, s in enumerate(syl):
        if s in ('ནི', 'ལ'):
            return '་'.join(syl[:i]).strip('་ ')
    return label


def classify(c):
    """c = cleaned clause. -> (k or None, decl or None, label)
    decl = ('list', n) | ('nolist', n)"""
    m = ORD_RE.match(c)
    k, rem = None, c
    if m:
        k = ORD[m.group(1)]
        rem = c[m.end():].lstrip('་ ')
    for rx, kind in ((D1, 'list'), (D3, 'nolist'), (D2, 'list')):
        mm = rx.search(rem)
        if mm:
            return k, (kind, CARD[mm.group(1)]), cut_label(rem[:mm.start()])
    return k, None, cut_label(rem) if k is not None else ''


def strip_final(s):
    syl = s.split('་')
    last = syl[-1]
    if last.endswith('འོ') and len(last) > 2:
        syl[-1] = last[:-2]
    elif len(last) == 2 and last[1] == 'ོ' and len(syl) > 1:
        syl = syl[:-1]
    return '་'.join(syl).strip('་ ')


def finalize_items(frame, clauses, mode):
    items = []
    frame['list_text'] = '་' + '་'.join(re.sub(r'\s+', '་', c).strip('་') for c in clauses) + '་'
    for c in clauses:
        c = re.sub(r'^(?:' + ORD_ALT + r')་?', '', c) if mode == 'shad' else c
        c = re.sub(r'་?དང་?$', '', c).strip('་ ')
        if c:
            items.append(c)
    if mode == 'ord' and items:
        if 'དབྱེ་ན་' in items[0]:
            items[0] = items[0].split('དབྱེ་ན་', 1)[1]
        syl = items[-1].split('་')
        if syl[-1] in CARD:
            items[-1] = '་'.join(syl[:-1])
    if items:
        items[-1] = strip_final(items[-1])
    n = frame['n']
    if n and len(items) != n:
        joined = '་'.join(items)
        parts = [p.strip('་ ') for p in re.split(r'(?<=་)དང་(?!པོ)', joined) if p.strip('་ ')]
        if len(parts) == n:
            items = parts
    frame['items'] = items


# ---------------------------------------------------------------- engine
class Engine:
    def __init__(self):
        self.frames, self.nodes, self.warn = [], [], []
        self.last = None
        self.n_declared = self.n_complete = 0
        self.in_list = False
        self.list_frame, self.list_clauses, self.list_mode = None, [], 'shad'

    def _pop_to(self, idx, seg):
        for f in self.frames[idx + 1:]:
            if f['n'] is not None:
                self.n_declared += 1
                self.n_complete += (f['cur'] == f['n'])
                if f['cur'] != f['n']:
                    self.warn.append(('incomplete_frame', seg, f['n'], f['cur']))
        del self.frames[idx + 1:]

    @staticmethod
    def _sim(label, item):
        if not label or not item:
            return 0.0
        if item in label or label in item:
            return 1.0
        a, b = label.split('་'), item.split('་')
        p = 0
        while p < min(len(a), len(b)) and a[p] == b[p]:
            p += 1
        return p / min(len(a), len(b))

    def open(self, k, label, start, seg):
        ok = lambda f: f['n'] is None or k <= f['n']
        strict = [i for i, f in enumerate(self.frames) if f['cur'] == k - 1 and ok(f)]
        loose = [i for i, f in enumerate(self.frames) if f['cur'] < k - 1 and ok(f)]
        def sc(i):
            f = self.frames[i]
            v = self._sim(label, f['items'][k - 1]) if k - 1 < len(f['items']) else 0.0
            if label and ('་' + label + '་') in f.get('list_text', ''):
                v = max(v, 1.0)
            return v
        idx = None
        if strict:
            best = max(sc(i) for i in strict)
            idx = max(i for i in strict if sc(i) == best) if best >= 0.5 else strict[-1]
        if (idx is None or sc(idx) < 0.5) and label:
            good = [i for i in loose if sc(i) >= 0.5]
            if good:
                idx = good[-1]
                self.frames[idx]['cur'] = k - 1
                self.warn.append(('ordinal_jump', seg, k))
        if idx is None:
            if k == 1:
                self.frames.append(dict(n=None, cur=0, items=[]))
                idx = len(self.frames) - 1
                self.warn.append(('implicit_frame', seg))
            else:
                cands = [i for i, f in enumerate(self.frames) if f['cur'] < k]
                if not cands:
                    self.frames.append(dict(n=None, cur=k - 1, items=[]))
                    idx = len(self.frames) - 1
                else:
                    idx = cands[-1]
                    self.frames[idx]['cur'] = k - 1
                self.warn.append(('ordinal_jump', seg, k))
        self._pop_to(idx, seg)
        f = self.frames[idx]
        f['cur'] = k
        title = label or (f['items'][k - 1] if k - 1 < len(f['items']) else '')
        node = dict(i=len(self.nodes), depth=idx + 1, k=k, title=title, start=start, seg=seg)
        self.nodes.append(node)
        self.last = 'open'
        return node

    def declare(self, decl, seg):
        kind, n = decl if decl else (None, None)
        frame = dict(n=n, cur=0, items=[])
        self.frames.append(frame)
        self.last = 'decl'
        if kind == 'nolist':
            return
        self.in_list, self.list_frame, self.list_clauses = True, frame, []
        self.list_mode = 'shad' if kind == 'list' else 'ord'

    def end_list(self):
        if self.in_list:
            finalize_items(self.list_frame, self.list_clauses, self.list_mode)
        self.in_list = False


def _split(t):
    out, pos = [], 0
    for part in t.split('།'):
        out.append((part, pos))
        pos += len(part) + 1
    return out


def process_para(E, seg, text, base):
    cl = _split(text)
    n = len(cl)
    has_later_ord = any(ORD_RE.match(clean(c)) for c, _ in cl)
    first_done = False
    i = 0
    while i < n:
        raw_c, off = cl[i]
        c = clean(raw_c)
        blank = (c == '')
        if E.in_list:
            first_done = True
            if blank:
                i += 1
                continue
            is_ord = bool(ORD_RE.match(c))
            if (E.list_mode == 'ord' and is_ord) or (E.list_mode == 'shad' and is_ord and c.endswith('ནི')):
                E.end_list()
                continue
            E.list_clauses.append(c)
            term = (i + 1 < n - 1 and cl[i + 1][0].strip() == '')
            fn = E.list_frame['n'] or 6
            if E.list_mode == 'shad' and (term or len(E.list_clauses) > 2 * fn + 4):
                if not term:
                    E.warn.append(('runaway_list', seg))
                E.end_list()
                i += 1
            i += 1
            continue
        if blank:
            i += 1
            continue
        k, decl, label = classify(c)
        start = base + off + (len(raw_c) - len(raw_c.lstrip()))
        if k is not None:
            E.open(k, label, start, seg)
            if decl:
                E.declare(decl, seg)
        elif decl:
            if E.last == 'decl' and E.frames and E.frames[-1]['cur'] == 0:
                E.open(1, label, start, seg)
            E.declare(decl, seg)
        elif not first_done and has_later_ord:
            E.declare(None, seg)          # un-numbered introductory list (n unknown)
        first_done = True
        i += 1


def reconstruct_toc(segments):
    """segments: list of (text, is_sabche). Returns (raw_text, nodes, warnings)."""
    raw_parts, starts, pos = [], [], 0
    for text, _ in segments:
        starts.append(pos)
        raw_parts.append(text)
        pos += len(text) + 1
    raw = ' '.join(raw_parts)
    E = Engine()
    for si, (text, is_s) in enumerate(segments):
        if is_s:
            process_para(E, si, text, starts[si])
    E.end_list()
    for f in E.frames:
        if f['n'] is not None:
            E.n_declared += 1
            E.n_complete += (f['cur'] == f['n'])
            if f['cur'] != f['n']:
                E.warn.append(('incomplete_frame_eof', f['n'], f['cur']))
    reconstruct_toc.last_stats = dict(declared=E.n_declared, complete=E.n_complete)
    nodes = E.nodes
    # parent + end offsets
    stack = []
    for nd in nodes:
        while stack and stack[-1]['depth'] >= nd['depth']:
            stack.pop()
        nd['parent'] = stack[-1]['i'] if stack else None
        stack.append(nd)
    for j, nd in enumerate(nodes):
        nd['end'] = len(raw)
        for m in nodes[j + 1:]:
            if m['depth'] <= nd['depth']:
                nd['end'] = m['start']
                break
    return raw, nodes, E.warn


# ---------------------------------------------------------------- renderers
def numbered(headings):
    """headings: [{'depth','title',...}] -> list of dotted paths from sibling counters."""
    cnt, paths = [], []
    for h in headings:
        d = h['depth']
        cnt = cnt[:d]
        while len(cnt) < d:
            cnt.append(0)
        cnt[d - 1] += 1
        paths.append('.'.join(map(str, cnt)))
    return paths


def render_tree(headings):
    lines = []
    for h, p in zip(headings, numbered(headings)):
        lines.append('%s%s %s' % ('  ' * (h['depth'] - 1), p, h.get('title') or '(untitled)'))
    return '\n'.join(lines)


def render_inline_xml(raw, headings):
    """headings: [{'depth','start','title'}] sorted by start. Nested <section> inline XML,
    everything wrapped in <text>. Stripping the tags (+unescape) gives `raw` back exactly."""
    out, stack, pos = ['<text>'], [], 0
    for h in headings:
        while stack and stack[-1] >= h['depth']:
            out.append(escape(raw[pos:h['start']]))
            pos = h['start']
            out.append('</section>')
            stack.pop()
        out.append(escape(raw[pos:h['start']]))
        pos = h['start']
        out.append('<section depth="%d" title=%s>' % (h['depth'], quoteattr(h.get('title') or '')))
        stack.append(h['depth'])
    out.append(escape(raw[pos:]))
    out.append('</section>' * len(stack))
    out.append('</text>')
    return ''.join(out)


def strip_xml(xml):
    return unescape(re.sub(r'<[^>]*>', '', xml))


def locate_anchors(raw, anchors):
    """sequentially locate verbatim anchors in raw -> list of start offsets (None if not found)."""
    out, cur = [], 0
    for a in anchors:
        a = (a or '').strip()
        p = raw.find(a, cur) if a else -1
        if p < 0:
            out.append(None)
        else:
            out.append(p)
            cur = p + 1
    return out
