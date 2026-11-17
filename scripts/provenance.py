#!/usr/bin/env python3
"""Write and check the provenance record ("bill of materials") of every leaderboard run of this skill.

python scripts/provenance.py --benchmarks ../buddhist-benchmarks      # write provenance/<run-id>.json + README.md
python scripts/provenance.py --check                                   # check the records against the files here

One record per leaderboard row, named after the row's run id in buddhist-benchmarks. It says exactly what
made the score: the skill files, the model and its settings, the prompt, the benchmark data, the harness and
libraries, the command, the raw run files and logs (with SHA-256 hashes), tokens, cost, scores and date.
Format: buddhistai/provenance@1, defined in the BuddhistAI handbook:
https://buddhistai.github.io/knowledge-base/handbook/provenance.html

buddhist-benchmarks keeps only the clean result.json. The full record lives here, next to the variants.
"""
import argparse, glob, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'provenance'
REPO = 'BuddhistAI/toc-extraction-tibetan'
SCHEMA = 'buddhistai/provenance@1'
REQUIRED = ['schema', 'run_id', 'date', 'by', 'task', 'language', 'skill', 'model', 'prompt', 'benchmark',
            'harness', 'runs', 'usage', 'cost', 'scores', 'links']
CONDS = {  # variant -> (lab condition, how the prompt is built)
    'gepa-v1': ('ours', 'DSPy ChainOfThought on the TOCExtractor signature, with the GEPA-optimised instructions '
                        'and demos loaded from variants/gepa-v1/program.json'),
    'sabcad-outliner': ('colleague', 'SKILL.md (without front matter) and references/*.md, joined, as the '
                                     'instructions of a DSPy ChainOfThought signature (text -> headings)'),
    'sabcad-outliner+script': ('colleague+tool', 'as sabcad-outliner, plus the output of the variant\'s own '
                                                 'scripts/extract_sabcad.py on the passage'),
    'sabcad-outliner-toc': ('skill:variants/sabcad-outliner-toc',
                            'SKILL.md (without front matter) and references/*.md, joined, as the instructions '
                            'of a DSPy ChainOfThought signature (text -> headings)'),
    'seed': ('seed', 'DSPy ChainOfThought on the TOCExtractor signature with its un-optimised seed instructions'),
}


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_files(commit, folder):
    """Every file of a folder at a commit, with its git blob id (content hash)."""
    files = []
    for line in git('ls-tree', '-r', commit, folder).splitlines():
        meta, path = line.split('\t', 1)
        files.append({'path': path, 'git_blob': meta.split()[2]})
    return files


def prompt_files(commit, folder, variant):
    """The files whose text is sent to the model (the rest of the folder is notes)."""
    names = [x['path'] for x in tree_files(commit, folder)]
    if variant == 'gepa-v1':
        return [n for n in names if n.endswith('program.json')]
    if variant == 'seed':
        return ['benchmark/gepa_toc.py (TOCExtractor signature)']
    keep = [n for n in names if n.endswith('/SKILL.md') or '/references/' in n]
    if variant.endswith('+script'):
        keep += [n for n in names if n.endswith('scripts/extract_sabcad.py')]
    return keep


def bench_git(bench, *args):
    return subprocess.run(['git', *args], cwd=bench, capture_output=True, check=True).stdout


def build(bench):
    bench = Path(bench)
    pin = json.loads((ROOT / 'benchmark' / 'benchmark.json').read_text(encoding='utf-8'))
    models = json.loads((bench / 'models.json').read_text(encoding='utf-8'))['models']
    data = bench_git(bench, 'show', f"{pin['tag']}:{pin['path']}/{pin['file']}")
    data_sha = hashlib.sha256(data).hexdigest()
    n_items = sum(1 for line in data.decode('utf-8').splitlines() if line.strip())
    OUT.mkdir(exist_ok=True)
    written = []
    for f in sorted(glob.glob(str(bench / 'tasks/toc-extraction/results/bo/runs/*/result.json'))):
        res = json.loads(Path(f).read_text(encoding='utf-8'))
        if not res.get('skill_ref', '').startswith(REPO + '@'):
            continue
        run_id = Path(f).parent.name
        commit, folder = res['skill_ref'].split('@', 1)[1].split(':', 1)
        run_json = json.loads((Path(f).parent / 'run.json').read_text(encoding='utf-8'))
        cond, prompt_how = CONDS[res['variant']]
        meta = None
        slug = res['model'].removeprefix('claude-')
        promoted = '-promoted' if cond.startswith('skill:') else ''
        run_files = sorted(glob.glob(str(ROOT / 'results' / f"{res['date']}-{slug}{promoted}-run*.json")))
        run_files = [f for f in run_files if not f.endswith('.meta.json')]
        runs, conds_in_file = [], []
        for rf in run_files:
            rows = json.loads(Path(rf).read_text(encoding='utf-8'))
            if not any(k.split('|')[0] == cond for k in rows):
                continue
            conds_in_file = list(dict.fromkeys(k.split('|')[0] for k in rows))
            mf = Path(rf).with_suffix('.meta.json')  # written by bench_skills.py since 2026-11-17
            if mf.exists():
                meta = json.loads(mf.read_text(encoding='utf-8'))
            log = Path(rf).with_suffix('.log')
            runs.append({'output': str(Path(rf).relative_to(ROOT)), 'output_sha256': sha256(rf),
                         'log': str(log.relative_to(ROOT)), 'log_sha256': sha256(log)})
        price = models[res['model']]['price']
        u = res['usage']
        per_pass = (u['input_tokens'] * price['input_per_mtok'] + u['output_tokens'] * price['output_per_mtok']) / 1e6
        reqs = git('show', f'{commit}:benchmark/requirements.txt').split()
        rec = {
            'schema': SCHEMA,
            'run_id': run_id,
            'date': res['date'],
            'by': res['by'],
            'task': res['task'],
            'language': res['language'],
            'skill': {'name': res['skill'], 'variant': res['variant'], 'version': res['skill_version'],
                      'ref': res['skill_ref'], 'files': tree_files(commit, folder)},
            'model': {'id': res['model'], 'provider': models[res['model']]['provider'],
                      'api': 'Anthropic Messages API through LiteLLM (dspy[litellm])',
                      'settings': {'temperature': res['temperature'], 'max_tokens': 8000, 'cache': False}},
            'prompt': {'how': prompt_how, 'files': prompt_files(commit, folder, res['variant']),
                       'note': 'The prompt is the skill files above, sent through the harness below. '
                               'scripts/estimate_usage.py rebuilds the exact prompt for each passage.'},
            'benchmark': {'repo': pin['repo'], 'tag': pin['tag'], 'path': f"{pin['path']}/{pin['file']}",
                          'data_version': res['data_version'], 'scorer_version': res['scorer_version'],
                          'data_sha256': data_sha, 'items': n_items,
                          'measured_on': run_json.get('data_measured_on', res['data_version']),
                          'note': 'Measured on 1.0.0 (the copy inside this repo at the skill commit). 2.0.0 has the '
                                  'same 85 items and answers in the standard format; re-scoring gives identical '
                                  'numbers (buddhist-benchmarks tasks/toc-extraction/CHANGELOG.md).'},
            'harness': {'repo': REPO, 'commit': commit, 'script': 'benchmark/bench_skills.py',
                        'libraries': meta['libraries'] if meta else reqs,
                        'python': meta['python'] if meta else 'not recorded',
                        'command': meta['command'] if meta else
                                   f"python benchmark/bench_skills.py --model anthropic/{res['model']} "
                                   f"--temperature {res['temperature']} --conds {','.join(conds_in_file)} "
                                   f"--sets unused,test --out results/{res['date']}-{slug}{promoted}-run<N>.json",
                        'command_recorded': bool(meta),
                        **({} if meta else {'command_note': 'Rebuilt from the README and the run files (which hold '
                            'these conditions); the exact command line was not saved before 2026-11-17. '
                            'bench_skills.py now saves it in <out>.meta.json.'})},
            'runs': runs,
            'repeats': res['repeats'],
            'usage': u,
            'cost': {'usd_per_pass': round(per_pass, 4), 'estimated': bool(u.get('estimated')),
                     'price': {k: price[k] for k in ('input_per_mtok', 'output_per_mtok', 'date', 'source')},
                     'note': 'tokens x list price, one pass over the test set; '
                             + ('tokens are estimated (see usage.method)' if u.get('estimated') else 'tokens from the API')},
            'scores': {'headline': res['headline'],
                       **{split: {m: v['mean'] for m, v in ms.items()} for split, ms in res['scores'].items()},
                       'std': {split: ms[res['headline']]['std'] for split, ms in res['scores'].items()}},
            'links': {'result': f"https://github.com/{pin['repo']}/blob/main/tasks/toc-extraction/results/bo/runs/{run_id}/result.json",
                      'outputs': f"https://github.com/{pin['repo']}/tree/main/tasks/toc-extraction/results/bo/runs/{run_id}/outputs",
                      'report': res.get('report'),
                      'leaderboard': 'https://buddhistai.github.io/buddhist-benchmarks/tasks/toc-extraction/bo/'},
            'notes': run_json.get('note', ''),
        }
        path = OUT / f'{run_id}.json'
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        written.append(rec)
        print('wrote', path.relative_to(ROOT))
    index(written)


def index(recs):
    lines = ['# Provenance', '',
             'One record per leaderboard row of this skill: the exact skill files, model, settings, prompt, benchmark data, '
             'harness, command, run files, logs, tokens, cost and date. Format: '
             '[buddhistai/provenance@1](https://buddhistai.github.io/knowledge-base/handbook/provenance.html).', '',
             'Made by `python scripts/provenance.py --benchmarks ../buddhist-benchmarks`. Do not edit by hand.', '',
             '| Run | Variant | Model | Data | structure_f1 (all) | Cost per pass | Record |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for r in sorted(recs, key=lambda r: (r['model']['id'], -r['scores']['all']['structure_f1'])):
        est = ' (estimated)' if r['cost']['estimated'] else ''
        lines.append(f"| {r['date']} | {r['skill']['variant']} {r['skill']['version']} | {r['model']['id']} | "
                     f"{r['benchmark']['tag']} | {r['scores']['all']['structure_f1']:.3f} ± {r['scores']['std']['all']:.3f} | "
                     f"${r['cost']['usd_per_pass']:.3f}{est} | [{r['run_id']}.json]({r['run_id']}.json) |")
    (OUT / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


def check():
    errors = []
    files = sorted(OUT.glob('*.json'))
    if not files:
        errors.append('provenance/: no records')
    for p in files:
        rec = json.loads(p.read_text(encoding='utf-8'))
        name = p.relative_to(ROOT)
        errors += [f'{name}: missing {k!r}' for k in REQUIRED if k not in rec]
        if rec.get('schema') != SCHEMA:
            errors.append(f'{name}: schema must be {SCHEMA}')
        if rec.get('run_id') != p.stem:
            errors.append(f'{name}: run_id must match the file name')
        if not re.fullmatch(r'[\w.-]+/[\w.-]+@[0-9a-f]{7,40}:\S+', rec.get('skill', {}).get('ref', '')):
            errors.append(f'{name}: skill.ref must be owner/repo@commit:path')
        if not rec.get('runs'):
            errors.append(f'{name}: no run files')
        for r in rec.get('runs', []):
            for key in ('output', 'log'):
                f = ROOT / r[key]
                if not f.exists():
                    errors.append(f'{name}: {r[key]} is missing')
                elif sha256(f) != r[f'{key}_sha256']:
                    errors.append(f'{name}: {r[key]} changed since the record was made (hash differs)')
        commit = rec.get('harness', {}).get('commit')
        for x in rec.get('skill', {}).get('files', []):
            try:
                blob = git('rev-parse', f"{commit}:{x['path']}").strip()
            except subprocess.CalledProcessError:
                blob = None
            if blob != x['git_blob']:
                errors.append(f"{name}: {x['path']} at {commit} does not match its recorded hash")
    for e in errors:
        print('ERROR', e)
    print(f'{len(files)} records, {len(errors)} errors')
    return 1 if errors else 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--benchmarks', help='path to a buddhist-benchmarks checkout (to write records)')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    if a.check:
        sys.exit(check())
    if not a.benchmarks:
        ap.error('give --benchmarks to write records, or --check')
    build(a.benchmarks)
    sys.exit(check())
