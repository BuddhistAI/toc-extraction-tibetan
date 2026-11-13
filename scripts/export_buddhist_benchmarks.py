#!/usr/bin/env python3
"""Export the evaluation passages to the buddhist-benchmarks toc-extraction format.

python scripts/export_buddhist_benchmarks.py OUT_DIR      # writes OUT_DIR/inputs/*.txt, OUT_DIR/references/*.json

Exports the `unused` and `test` sets of benchmark/bench_skills.py (the passages GEPA never saw); the 48 passages
GEPA trained on stay in this repo only.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'benchmark'))
import bench_skills as b  # noqa: E402

out = Path(sys.argv[1])
(out / 'inputs').mkdir(parents=True, exist_ok=True)
(out / 'references').mkdir(parents=True, exist_ok=True)
sets = b.split_sets(str(ROOT / 'benchmark' / 'data' / 'dataset.jsonl'))
manifest = []
for sname in ('unused', 'test'):
    for ex in sets[sname]:
        (out / 'inputs' / f'{ex.id}.txt').write_text(ex.text, encoding='utf-8', newline='')
        entries = [dict(title=h['title'], level=h['depth'], start=h['start'], anchor=h['anchor']) for h in ex.gold]
        (out / 'references' / f'{ex.id}.json').write_text(
            json.dumps({'entries': entries}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
        manifest.append(dict(id=ex.id, subset='same-book' if sname == 'unused' else 'held-out-book',
                             chars=len(ex.text), headings=len(entries)))
(out / 'items.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(len(manifest), 'items')
