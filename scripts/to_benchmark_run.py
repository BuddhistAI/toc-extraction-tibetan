#!/usr/bin/env python3
"""Turn one condition of a results/<run>.json file into buddhist-benchmarks run outputs.

python scripts/to_benchmark_run.py results/2026-11-13-sonnet-5-5-run2.json ours OUT_DIR/outputs

Writes OUT_DIR/outputs/<item-id>.json in the toc-extraction task format ({"entries": [{title, level, anchor}]}).
Needs a results file written by the current bench_skills.py (it stores the predicted headings).
"""
import json, sys
from pathlib import Path

res, cond, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
data = json.loads(res.read_text(encoding='utf8'))
out.mkdir(parents=True, exist_ok=True)
n = 0
for sname in ('unused', 'test'):
    for r in data[f'{cond}|{sname}']:
        if 'headings' not in r:
            sys.exit(f'{res}: no predicted headings stored (made by an older bench_skills.py)')
        entries = [dict(title=h.get('title', ''), level=int(h.get('depth') or 0), anchor=h.get('anchor', ''))
                   for h in r['headings']]
        (out / f"{r['id']}.json").write_text(json.dumps({'entries': entries}, ensure_ascii=False, indent=1) + '\n',
                                             encoding='utf-8', newline='\n')
        n += 1
print(n, 'outputs')
