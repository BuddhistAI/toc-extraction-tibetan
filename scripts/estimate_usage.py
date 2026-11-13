#!/usr/bin/env python3
"""Estimate the tokens (and so the cost) of the 2026-11-13 benchmark runs, which did not log usage.

python scripts/estimate_usage.py --benchmarks ../buddhist-benchmarks [--write]

Input: the exact prompt DSPy sends for every passage (ChatAdapter.format on the same programs as
bench_skills.py), so instruction and passage sizes are real. Output: the stored predictions of each run
(outputs/*.json in buddhist-benchmarks) plus an allowance for the chain-of-thought `reasoning` field,
which was not stored. Tokens are counted from characters, because no Claude tokenizer is available
offline:
  Tibetan characters (U+0F00-U+0FFF): 1 token each  (byte-level BPE covers this script poorly)
  everything else:                    1 token per 4 characters
  reasoning (not stored):             300 + 100 per predicted heading
Every estimate is written as `usage.estimated: true`. Runs made with the current bench_skills.py log
real usage instead (Prediction.get_lm_usage).
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'benchmark'))

TIB = re.compile(r'[ༀ-࿿]')
METHOD = ('estimated from characters: exact DSPy prompts, stored outputs, Tibetan 1 token/char, other text '
          '4 chars/token, reasoning 300 + 100 tokens per heading (scripts/estimate_usage.py in toc-extraction-tibetan)')


def tokens(s):
    t = len(TIB.findall(s))
    return t + (len(s) - t) / 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--benchmarks', required=True)
    ap.add_argument('--write', action='store_true', help='write usage into the result.json files')
    a = ap.parse_args()
    import dspy
    import bench_skills as b
    import eval_data

    recs = [r for r in eval_data.load_eval_records() if r[0] in ('unused', 'test')]
    adapter = dspy.ChatAdapter()
    conds = {'gepa-v1': 'ours', 'sabcad-outliner': 'colleague', 'sabcad-outliner+script': 'colleague+tool',
             'seed': 'seed', 'sabcad-outliner-toc': 'skill:variants/sabcad-outliner-toc'}
    instr = b.skill_text()

    def program(c):
        if c == 'ours':
            p = b.g.TOCExtractor(); p.load(str(ROOT / 'variants' / 'gepa-v1' / 'program.json')); return p
        if c == 'seed':
            return b.g.TOCExtractor()
        if c == 'colleague':
            return b.ColleagueInstr(instr)
        if c == 'colleague+tool':
            return b.ColleagueTool(instr)
        return b.ColleagueInstr(b.skill_dir_text(c[len('skill:'):]))

    runs = Path(a.benchmarks) / 'tasks' / 'toc-extraction' / 'results' / 'bo' / 'runs'
    for d in sorted(runs.glob('*/result.json')):
        res = json.loads(d.read_text(encoding='utf8'))
        c = conds[res['variant']]
        pred = program(c).extract.predict
        inp = out = 0
        for _, rid, text, _ in recs:
            kw = {'text': text}
            if c == 'colleague+tool':
                import subprocess, tempfile, os
                with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf8') as f:
                    f.write(text)
                kw['survey'] = subprocess.run([sys.executable, '-I', str(b.SKILL_DIR / 'scripts' / 'extract_sabcad.py'),
                                               f.name, '--json'], capture_output=True, text=True).stdout
                os.unlink(f.name)
            msgs = adapter.format(pred.signature, pred.demos, kw)
            inp += sum(tokens(m['content']) for m in msgs)
            o = d.parent / 'outputs' / f'{rid}.json'
            entries = json.loads(o.read_text(encoding='utf8')).get('entries', []) if o.exists() else []
            out += tokens(json.dumps(entries, ensure_ascii=False)) + 300 + 100 * len(entries) + 30
        usage = {'input_tokens': round(inp), 'output_tokens': round(out), 'items': len(recs),
                 'estimated': True, 'method': METHOD}
        print(f"{d.parent.name:80s} in {usage['input_tokens']:>9,} out {usage['output_tokens']:>8,}")
        if a.write:
            res['usage'] = usage
            res.pop('cost_usd', None)
            d.write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
