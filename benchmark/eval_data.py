#!/usr/bin/env python3
"""The evaluation passages, from buddhist-benchmarks at the release pinned in benchmark.json.

python benchmark/eval_data.py        # download (once) and print the set sizes

load_eval_sets() returns {'unused': [...], 'test': [...]} as dspy Examples (text, gold, id), with the
benchmark's references converted to this lab's heading format (depth, start, title, anchor).
`unused` is the benchmark's same-book subset, `test` its held-out-book subset.
"""
import io, json, tarfile, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
PIN = json.loads((HERE / 'benchmark.json').read_text(encoding='utf8'))
CACHE = HERE / 'eval' / PIN['tag'].replace('/', '-')


def fetch():
    """Download the pinned data set into benchmark/eval/<tag>/ unless it is already there."""
    if (CACHE / 'items.json').exists():
        return CACHE
    url = f"https://codeload.github.com/{PIN['repo']}/tar.gz/refs/tags/{urllib.parse.quote(PIN['tag'], safe='')}"
    with urllib.request.urlopen(url, timeout=120) as r:
        data = r.read()
    prefix = PIN['path'].strip('/') + '/'
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
        for m in tar.getmembers():
            rel = m.name.split('/', 1)[1] if '/' in m.name else ''
            if not m.isfile() or not rel.startswith(prefix):
                continue
            dest = CACHE / rel[len(prefix):]
            if '..' in dest.relative_to(CACHE).parts:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(tar.extractfile(m).read())
    if not (CACHE / 'items.json').exists():
        raise SystemExit(f'{url}: no {PIN["path"]}/items.json in the archive')
    return CACHE


def load_eval_records():
    """[(set_name, id, text, gold)] in items.json order."""
    d = fetch()
    by_subset = {v: k for k, v in PIN['sets'].items()}
    out = []
    for item in json.loads((d / 'items.json').read_text(encoding='utf8')):
        text = (d / 'inputs' / f"{item['id']}.txt").read_text(encoding='utf8')
        ref = json.loads((d / 'references' / f"{item['id']}.json").read_text(encoding='utf8'))
        gold = [dict(depth=e['level'], start=e['start'], title=e['title'], anchor=e['anchor']) for e in ref['entries']]
        out.append((by_subset[item['subset']], item['id'], text, gold))
    return out


def load_eval_sets(max_chars=10 ** 9):
    import dspy
    sets = {k: [] for k in PIN['sets']}
    for sname, iid, text, gold in load_eval_records():
        if len(text) <= max_chars:
            sets[sname].append(dspy.Example(text=text, gold=gold, id=iid).with_inputs('text'))
    return sets


if __name__ == '__main__':
    recs = load_eval_records()
    print(PIN['tag'], {s: sum(1 for r in recs if r[0] == s) for s in PIN['sets']}, 'from', CACHE)
