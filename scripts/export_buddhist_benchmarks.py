#!/usr/bin/env python3
"""Export the evaluation passages to the buddhist-benchmarks toc-extraction format.

python scripts/export_buddhist_benchmarks.py OUT/test.jsonl   # buddhist-benchmarks format: id, input, target, metadata

Used to make a new buddhist-benchmarks version from the EPUBs. First rebuild the full local data with
`python benchmark/build_dataset.py` (writes benchmark/data/dataset.jsonl, git-ignored). Exports every passage of at
most 6,500 characters that GEPA never saw; the 48 passages GEPA trained on (benchmark/data/train.jsonl) stay in this
repo only. After the new version is tagged in buddhist-benchmarks, point benchmark/benchmark.json at it.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'benchmark'))
import bench_skills as b  # noqa: E402

BOOKS = {'IBA-LWS-08': ('A Lamp Illuminating the Intent of Vasubandhu', 'Jamyang Loter Wangpo'),
         'RCP-FM-07': ('The Jewel Garland', 'Chenga Chökyi Gyalpo')}
out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
full = b.g.load_dataset(str(ROOT / 'benchmark' / 'data' / 'dataset.jsonl'), 6500)
seen = {json.loads(l)['id'] for l in open(ROOT / 'benchmark' / 'data' / 'train.jsonl', encoding='utf8')}
sets = dict(unused=[e for e in full['train'] + full['val'] if e.id not in seen], test=full['test'])
rows = []
for sname in ('unused', 'test'):
    for ex in sets[sname]:
        book = ex.id.rsplit('-', 1)[0]
        entries = [dict(title=h['title'], level=h['depth'], start=h['start'], anchor=h['anchor']) for h in ex.gold]
        rows.append(dict(id=ex.id, input=ex.text, target=dict(entries=entries),
                         metadata=dict(subset='same-book' if sname == 'unused' else 'held-out-book', book=book,
                                       book_title=BOOKS[book][0], author=BOOKS[book][1],
                                       chars=len(ex.text), headings=len(entries))))
rows.sort(key=lambda r: r['id'])
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(len(rows), 'items ->', out)
