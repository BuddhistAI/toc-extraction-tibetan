#!/usr/bin/env python3
"""build_dataset.py - EPUB(s) -> before/after TOC test data.

For every book writes data/<book>/:
  raw.txt          BEFORE: all formatting + line returns stripped (one line of text)
  toc.json         AFTER : flat node list (depth, ordinal, title, start/end offsets, anchor)
  toc_tree.txt     AFTER : formatted TOC tree
  inline_toc.xml   AFTER : the raw text with nested <section depth=".."> markup
and data/dataset.jsonl (chunked examples with train/val/test split) for GEPA.

The EPUB's own nav is flat (it lists the `Tibetan-Sabche` outline paragraphs without
depth), so depth is reconstructed from the sa-bcad grammar - see toc_lib.py.
"""
import argparse, collections, json, random, re, sys, warnings, zipfile
from pathlib import Path
from bs4 import BeautifulSoup
sys.path.insert(0, str(Path(__file__).parent))
from toc_lib import *

warnings.filterwarnings('ignore')
ANCHOR_LEN = 40


def read_epub(path):
    z = zipfile.ZipFile(path)
    cands = [n for n in z.namelist() if n.endswith('.xhtml') and not n.endswith(('toc.xhtml', 'cover.xhtml'))]
    name = max(cands, key=lambda n: len(z.read(n)))
    soup = BeautifulSoup(z.read(name).decode('utf8'), 'lxml')
    opf = next(n for n in z.namelist() if n.endswith('.opf'))
    meta = BeautifulSoup(z.read(opf).decode('utf8'), 'xml')
    title = meta.find('title').get_text() if meta.find('title') else ''
    segs = []
    for p in soup.body.find_all('p'):
        t = re.sub(r'\s+', ' ', p.get_text()).strip()
        if t:
            segs.append((t, 'Tibetan-Sabche' in (p.get('class') or [])))
    body_chars = len(re.sub(r'\s', '', soup.body.get_text()))
    seg_chars = sum(len(re.sub(r'\s', '', t)) for t, _ in segs)
    return segs, title, name, body_chars, seg_chars


def mk_headings(raw, nodes, lo=0, hi=None, rel=True):
    hi = len(raw) if hi is None else hi
    sel = [n for n in nodes if lo <= n['start'] < hi]
    if not sel:
        return []
    d0 = min(n['depth'] for n in sel) if rel else 1
    return [dict(depth=n['depth'] - d0 + 1, start=n['start'] - lo, title=n['title'], ordinal=n['k'],
                 anchor=raw[n['start']:min(n['start'] + ANCHOR_LEN, hi)]) for n in sel]


def atoms(nodes, i, cap):
    n = nodes[i]
    kids = [m for m in nodes[i + 1:] if m['parent'] == n['i']]
    if n['end'] - n['start'] <= cap or not kids:
        return [(n['start'], n['end'], n['depth'])]
    res = [(n['start'], kids[0]['start'], n['depth'])]
    for k in kids:
        res += atoms(nodes, k['i'], cap)
    return res


def make_chunks(raw, nodes, cap):
    chunks = []
    if nodes and nodes[0]['start'] > 0:                      # preface (title + salutation verses)
        chunks.append((0, nodes[0]['start'], None))
    atl = []
    for n in nodes:
        if n['parent'] is None:
            atl += atoms(nodes, n['i'], cap)
    cur = None
    for a, b, d in atl:
        if cur and d >= cur[2] and a == cur[1] and (b - cur[0]) <= cap:
            cur = (cur[0], b, cur[2])
        else:
            if cur:
                chunks.append(cur)
            cur = (a, b, d)
    if cur:
        chunks.append(cur)
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('epubs', nargs='*')
    ap.add_argument('--out', default=str(Path(__file__).parent / 'data'))
    ap.add_argument('--cap', type=int, default=6000, help='soft max characters per chunk')
    ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    here = Path(__file__).parent
    epubs = a.epubs or sorted(map(str, (here / 'sources').glob('*.epub')))
    out = Path(a.out)
    rows = []
    for ep in epubs:
        book = re.match(r'([A-Za-z]+-[A-Za-z]+-\d+)', Path(ep).name).group(1)
        segs, title, fname, bc, sc = read_epub(ep)
        raw, nodes, warn = reconstruct_toc(segs)
        d = out / book
        d.mkdir(parents=True, exist_ok=True)
        (d / 'raw.txt').write_text(raw, encoding='utf8')
        heads = mk_headings(raw, nodes, rel=False)
        for h, n in zip(heads, nodes):
            h.update(id=n['i'], parent=n['parent'], end=n['end'])
        (d / 'toc.json').write_text(json.dumps(dict(book=book, title=title, source=fname, n_chars=len(raw),
                                                    headings=heads), ensure_ascii=False, indent=1), encoding='utf8')
        (d / 'toc_tree.txt').write_text(render_tree(heads) + '\n', encoding='utf8')
        xml = render_inline_xml(raw, heads)
        (d / 'inline_toc.xml').write_text(xml, encoding='utf8')
        assert strip_xml(xml) == raw, 'round-trip failed'
        # ---- stats
        wc = collections.Counter(w[0] for w in warn)
        dc = collections.Counter(n['depth'] for n in nodes)
        n_sab = sum(1 for _, s in segs if s)
        print(f'== {book}: {len(raw)} chars, {len(segs)} paragraphs ({n_sab} sabche), {len(nodes)} outline nodes, '
              f'text coverage {sc}/{bc}')
        print('   depth histogram:', dict(sorted(dc.items())))
        st = reconstruct_toc.last_stats
        print('   parser warnings:', dict(wc) or 'none')
        print(f"   declared child-counts satisfied: {st['complete']}/{st['declared']}; untitled nodes: {sum(1 for n in nodes if not n['title'])}")
        # ---- chunks
        for ci, (lo, hi, _) in enumerate(make_chunks(raw, nodes, a.cap)):
            text = raw[lo:hi].rstrip()
            hs = mk_headings(raw, nodes, lo, lo + len(text))
            rows.append(dict(id=f'{book}-{ci:03d}', book=book, raw_text=text, headings=hs,
                             toc_tree=render_tree(hs), inline_xml=render_inline_xml(text, hs)))
            assert strip_xml(rows[-1]['inline_xml']) == text
    # ---- splits: first book -> train/val (interleaved), every other book -> test
    books = list(dict.fromkeys(r['book'] for r in rows))
    rnd = random.Random(a.seed)
    first = [r for r in rows if r['book'] == books[0]]
    pool = [r for r in first if r['headings']]
    rnd.shuffle(pool)
    half = len(pool) // 2
    for i, r in enumerate(pool):
        r['split'] = 'train' if i < half else 'val'
    for r in rows:
        r.setdefault('split', 'test' if r['book'] != books[0] else 'extra')
    with open(out / 'dataset.jsonl', 'w', encoding='utf8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    c = collections.Counter(r['split'] for r in rows)
    L = [len(r['raw_text']) for r in rows]
    print('chunks:', len(rows), dict(c), 'chars min/median/max:', min(L), sorted(L)[len(L) // 2], max(L))
    print('headings per chunk (mean): %.1f' % (sum(len(r['headings']) for r in rows) / len(rows)))


if __name__ == '__main__':
    main()
