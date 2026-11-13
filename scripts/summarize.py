#!/usr/bin/env python3
"""Summarize results/<date>-<model>-run<N>.json files into Markdown tables for REPORT.md.

python scripts/summarize.py results/2026-11-13-*-run*.json > results/2026-11-13-summary.md

Per model x variant: the lab score (per-passage mean of 0.3*position-F1 + 0.7*position+depth-F1, x100) on each set,
averaged over runs (+- the standard deviation between runs), and the buddhist-benchmarks headline structure_f1
(micro F1 over all headings of both sets, needing position and level to match).
"""
import json, re, statistics, sys
from collections import defaultdict
from pathlib import Path

VARIANT = {'ours': 'gepa-v1 1.0.0', 'colleague': 'sabcad-outliner 1.0.0', 'colleague+tool': 'sabcad-outliner 1.0.0 + script',
           'seed': 'seed 0.1.0', 'skill:variants/sabcad-outliner-toc': 'sabcad-outliner-toc 1.0.0'}
cells = defaultdict(lambda: defaultdict(list))   # (model, cond) -> metric -> [per-run value]
for f in sys.argv[1:]:
    m = re.search(r'\d{4}-\d\d-\d\d-(.+?)(-promoted)?-run(\d+)\.json$', f)
    model = m.group(1)
    data = json.loads(Path(f).read_text(encoding='utf8'))
    by = defaultdict(dict)
    for key, rows in data.items():
        cond, sname = key.split('|')
        by[cond][sname] = rows
    for cond, sets in by.items():
        if not {'unused', 'test'} <= set(sets):
            continue  # incomplete run
        c = cells[(model, cond)]
        for sname, rows in sets.items():
            c[sname].append(100 * statistics.mean(r['score'] for r in rows))
        allrows = sets['unused'] + sets['test']
        c['all'].append(100 * statistics.mean(r['score'] for r in allrows))
        tp, npred, ng = (sum(r[k] for r in allrows) for k in ('tp_depth', 'n_pred', 'n_gold'))
        p, rc = tp / npred if npred else 0, tp / ng
        c['structure_f1'].append(2 * p * rc / (p + rc) if p + rc else 0)


def fmt(v, d=1, scale=1):
    v = [x * scale for x in v]
    if not v:
        return '-'
    s = f'{statistics.mean(v):.{d}f}'
    return s + (f' ± {statistics.stdev(v):.{d}f}' if len(v) > 1 else '')


models = sorted({m for m, _ in cells}, key=lambda m: ('sonnet' in m, m))
for model in models:
    rows = sorted([(c, v) for (m, c), v in cells.items() if m == model], key=lambda x: -statistics.mean(x[1]['all']))
    print(f'\n### {model}\n')
    print('| Rank | Variant | Runs | All 85 | Same book (76) | Held-out book (9) | structure_f1 |')
    print('| --- | --- | --- | --- | --- | --- | --- |')
    for i, (c, v) in enumerate(rows, 1):
        print(f"| {i} | {VARIANT.get(c, c)} | {len(v['all'])} | {fmt(v['all'])} | {fmt(v['unused'])} | {fmt(v['test'])} | {fmt(v['structure_f1'], 3)} |")
print('\n### Both models (mean of the two model means)\n')
print('| Rank | Variant | All 85 | Held-out book (9) | structure_f1 |')
print('| --- | --- | --- | --- | --- |')
conds = {c for _, c in cells}
avg = {c: [statistics.mean(statistics.mean(cells[(m, c)][k]) for m in models if (m, c) in cells) for k in ('all', 'test', 'structure_f1')]
       for c in conds if all((m, c) in cells for m in models)}
for i, (c, (a, t, s)) in enumerate(sorted(avg.items(), key=lambda x: -x[1][0]), 1):
    print(f'| {i} | {VARIANT.get(c, c)} | {a:.1f} | {t:.1f} | {s:.3f} |')
