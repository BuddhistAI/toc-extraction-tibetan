#!/usr/bin/env python3
"""Turn the lab's run files into buddhist-benchmarks result.json files (one per variant and model).

python scripts/to_result_json.py --date 2026-11-13 --commit 3253458 --benchmarks ../buddhist-benchmarks

Reads results/<date>-<model>-[promoted-]run<N>.json, averages the runs (mean and sample standard
deviation) per split, and writes tasks/toc-extraction/results/bo/runs/<run-id>/result.json in the
buddhist-benchmarks checkout. Format: buddhist-benchmarks docs/results.md.

Token usage is the mean per pass over the test set, from the API counts bench_skills.py logs per item.
Splits: `same-book` is the lab's `unused` set, `held-out-book` is its `test` set, `all` is both.
Metrics are micro-averaged over headings, exactly as the official scorer computes them:
  structure_f1   = 2 * (position and depth matches) / (predicted + reference)
  title_f1       = 2 * (position matches) / (predicted + reference)   (position mode)
  level_accuracy = (position and depth matches) / (position matches)
"""
import argparse, glob, json, re, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONDS = {  # lab condition -> (variant, variant folder, version)
    'ours': ('gepa-v1', 'gepa-v1', '1.0.0'),
    'colleague': ('sabcad-outliner', 'sabcad-outliner', '1.0.0'),
    'colleague+tool': ('sabcad-outliner+script', 'sabcad-outliner', '1.0.0'),
    'seed': ('seed', 'seed', '0.1.0'),
    'skill:variants/sabcad-outliner-toc': ('sabcad-outliner-toc', 'sabcad-outliner-toc', '1.0.0'),
}
SPLITS = {'same-book': ['unused'], 'held-out-book': ['test'], 'all': ['unused', 'test']}


def metrics(rows):
    tp_pos = sum(r['tp_pos'] for r in rows)
    tp_depth = sum(r['tp_depth'] for r in rows)
    n = sum(r['n_pred'] + r['n_gold'] for r in rows)
    return {'structure_f1': 2 * tp_depth / n if n else 1.0,
            'title_f1': 2 * tp_pos / n if n else 1.0,
            'level_accuracy': tp_depth / tp_pos if tp_pos else 0.0}


def mean_std(values):
    return {'mean': round(statistics.mean(values), 6),
            'std': round(statistics.stdev(values), 6) if len(values) > 1 else 0.0,
            'runs': [round(v, 6) for v in values]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True)
    ap.add_argument('--commit', required=True, help='short commit of this repo that holds the variants')
    ap.add_argument('--benchmarks', required=True, help='path to a buddhist-benchmarks checkout')
    ap.add_argument('--data-version', default='2.0.0')
    a = ap.parse_args()

    runs = {}  # (cond, model) -> list of {split: rows}
    for f in sorted(glob.glob(str(ROOT / 'results' / f'{a.date}-*-run*.json'))):
        m = re.search(r'\d{4}-\d\d-\d\d-(\w+-\d-\d)-(?:promoted-)?run\d+\.json$', f)
        model = 'claude-' + m.group(1)
        for key, rows in json.loads(Path(f).read_text(encoding='utf8')).items():
            cond, split = key.split('|')
            runs.setdefault((cond, model), {}).setdefault(f, {})[split] = rows

    out_root = Path(a.benchmarks) / 'tasks' / 'toc-extraction' / 'results' / 'bo' / 'runs'
    for (cond, model), by_file in sorted(runs.items()):
        variant, folder, version = CONDS[cond]
        per_run = [{s: metrics([r for p in parts for r in sp[p]]) for s, parts in SPLITS.items()}
                   for sp in by_file.values()]
        scores = {s: {k: mean_std([r[s][k] for r in per_run]) for k in per_run[0][s]} for s in SPLITS}
        rows_all = [r for sp in by_file.values() for p in SPLITS['all'] for r in sp[p]]
        if any(r.get('usage') is None for r in rows_all):
            raise SystemExit(f'{cond} {model}: some rows have no usage; run bench_skills.py again (it logs tokens), '
                             'or for old runs use scripts/estimate_usage.py')
        n = len(by_file)
        usage = {'input_tokens': round(sum(r['usage']['input_tokens'] for r in rows_all) / n),
                 'output_tokens': round(sum(r['usage']['output_tokens'] for r in rows_all) / n),
                 'items': len(rows_all) // n, 'estimated': False}
        run_id = f"{a.date}-toc-extraction-tibetan-{variant}-{version}-{a.commit}-{model.removeprefix('claude-')}"
        result = {
            'schema': 'buddhist-benchmarks/result@1',
            'task': 'toc-extraction', 'language': 'bo',
            'data_version': a.data_version, 'scorer_version': '2.0.0',
            'skill': 'toc-extraction-tibetan', 'variant': variant, 'skill_version': version,
            'skill_ref': f'BuddhistAI/toc-extraction-tibetan@{a.commit}:variants/{folder}',
            'model': model, 'temperature': 1.0, 'repeats': len(per_run),
            'harness': 'toc-extraction-tibetan benchmark/bench_skills.py (DSPy 3.5.0 ChainOfThought)',
            'headline': 'structure_f1',
            'scores': scores,
            'usage': usage,
            'date': a.date, 'by': 'WeBuddhist',
            'report': 'https://github.com/BuddhistAI/toc-extraction-tibetan/blob/main/REPORT.md',
        }
        d = out_root / run_id
        d.mkdir(parents=True, exist_ok=True)
        (d / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(run_id, scores['all']['structure_f1']['mean'])


if __name__ == '__main__':
    main()
