#!/usr/bin/env python3
"""bench_skills.py - run several skills through the SAME harness/metric as gepa_toc.py.

Conditions
  ours            variants/gepa-v1 (GEPA-optimised instructions, program.json), signature text -> headings
  colleague       variants/sabcad-outliner: SKILL.md + methods.md + code-scheme.md as instructions (+ adapter)
  colleague+tool  same, plus the output of its own scripts/extract_sabcad.py run on the passage
  seed            variants/seed: the un-optimised seed prompt
  skill:<dir>     any skill folder (e.g. skill:variants/sabcad-outliner-toc): SKILL.md + references/*.md

Run from the repo root:  python benchmark/bench_skills.py --model anthropic/claude-haiku-5-5 --temperature 1.0                            --conds ours,colleague,colleague+tool,seed --out results/<run>.json

Evaluation sets (all passages <= 6500 chars)
  unused  Vasubandhu-book passages GEPA never saw: buddhist-benchmarks same-book subset            <- fair for both
  test    Jewel Garland passages (held out for both): buddhist-benchmarks held-out-book subset     <- fair for both
  seen    the 24 train + 24 val passages GEPA optimised on (data/train.jsonl)                      <- biased towards ours
unused and test are downloaded from buddhist-benchmarks at the release pinned in benchmark.json (eval_data.py).
"""
import argparse, json, os, subprocess, sys, tempfile, random
from pathlib import Path
import dspy

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import gepa_toc as g
import eval_data

SKILL_DIR = Path(os.environ.get('COLLEAGUE_SKILL_DIR', str(HERE.parent / 'variants' / 'sabcad-outliner')))
ADAPTER = """BENCHMARK ADAPTATION (this overrides the deliverable described in the skill below)
You are being evaluated on the structure-detection part of the skill only. The input is ONE passage of a Tibetan
text whose sa-bcad is embedded in the text itself (regime B). All line breaks and folio tags have been removed.
Do NOT produce a .docx, outline codes, folios, review notes, or ask questions. Instead return the outline as the
`headings` list, in reading order: one entry per outline element whose transition (its own ordinal + heading /
ལ་N / ནི introducer) occurs in this passage.
  depth  = the element's nesting level counted RELATIVE to this passage (1 = the shallowest level that appears
           in the passage, 2 = its sub-division, ...). In the skill's code scheme this is the code level minus a constant.
  anchor = the first 40 characters of the element's transition point, copied verbatim from the passage, starting at
           its first character (including a leading ༈ if present)
  title  = a short label
Return an empty list if the passage contains no outline elements.

===== THE SKILL (colleague's, unmodified) =====
"""


def skill_dir_text(d):
    """A skill folder as instructions: SKILL.md without frontmatter, then every references/*.md."""
    d = HERE.parent / d
    parts = [(d / 'SKILL.md').read_text(encoding='utf8').split('\n---\n', 1)[1]]
    for f in sorted((d / 'references').glob('*.md')):
        parts.append(f'\n\n===== references/{f.name} =====\n' + f.read_text(encoding='utf8'))
    return '\n'.join(parts)


def skill_text():
    parts = [(SKILL_DIR / 'SKILL.md').read_text(encoding='utf8')]
    for f in ('methods.md', 'code-scheme.md'):
        parts.append(f'\n\n===== references/{f} =====\n' + (SKILL_DIR / 'references' / f).read_text(encoding='utf8'))
    return ADAPTER + '\n'.join(parts)


class Survey(dspy.Signature):   # placeholder docstring is replaced via with_instructions
    text: str = dspy.InputField(desc="raw Tibetan passage without formatting")
    survey: str = dspy.InputField(desc="JSON output of the skill's scripts/extract_sabcad.py run on the passage "
                                       "(a scaffolding aid, not an oracle)")
    headings: list[g.Heading] = dspy.OutputField(desc="all outline headings in reading order")


class ColleagueTool(dspy.Module):
    def __init__(self, instructions):
        super().__init__()
        self.extract = dspy.ChainOfThought(Survey.with_instructions(instructions))

    def forward(self, text):
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf8') as f:
            f.write(text)
            p = f.name
        try:
            out = subprocess.run([sys.executable, '-I', str(SKILL_DIR / 'scripts' / 'extract_sabcad.py'), p, '--json'],
                                 capture_output=True, text=True, timeout=60).stdout
        finally:
            os.unlink(p)
        return self.extract(text=text, survey=out)


class ColleagueInstr(dspy.Module):
    def __init__(self, instructions):
        super().__init__()
        self.extract = dspy.ChainOfThought(g.ExtractTOC.with_instructions(instructions))

    def forward(self, text):
        return self.extract(text=text)


def split_sets(data, max_chars=6500):
    """unused and test come from buddhist-benchmarks (pinned in benchmark.json); seen is GEPA's data in data/train.jsonl."""
    sets = g.load_dataset(data, max_chars)
    ev = eval_data.load_eval_sets(max_chars)
    return dict(unused=ev['unused'], test=ev['test'], seen=sets['train'] + sets['val'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=str(HERE / 'data' / 'train.jsonl'), help='GEPA training data (the seen set)')
    ap.add_argument('--model', default='anthropic/claude-haiku-4-5')
    ap.add_argument('--temperature', type=float, default=0.0, help='Sonnet 5.5 only accepts 1.0')
    ap.add_argument('--conds', default='ours,colleague,colleague+tool')
    ap.add_argument('--sets', default='unused,test')
    ap.add_argument('--limit', type=int, default=0, help='debug: only first N per set')
    ap.add_argument('--threads', type=int, default=6)
    ap.add_argument('--out', default=str(HERE.parent / 'results' / 'bench_results.json'))
    a = ap.parse_args()
    g.load_key()
    dspy.configure(lm=g.make_lm(a.model, temperature=a.temperature))
    sets = split_sets(a.data)
    instr = skill_text()
    print('instruction chars (colleague):', len(instr), '| sets:', {k: len(v) for k, v in sets.items()}, flush=True)

    def build(c):
        if c == 'ours':
            p = g.TOCExtractor(); p.load(str(HERE.parent / 'variants' / 'gepa-v1' / 'program.json')); return p
        if c == 'seed':
            return g.TOCExtractor()
        if c == 'colleague':
            return ColleagueInstr(instr)
        if c == 'colleague+tool':
            return ColleagueTool(instr)
        if c.startswith('skill:'):
            return ColleagueInstr(skill_dir_text(c[len('skill:'):]))
        raise SystemExit('unknown condition ' + c)

    results = {}
    for c in a.conds.split(','):
        prog = build(c)
        for sname in a.sets.split(','):
            exs = sets[sname][:a.limit] if a.limit else sets[sname]
            ev = dspy.Evaluate(devset=exs, metric=g.toc_score, num_threads=a.threads, display_progress=False,
                               display_table=0, provide_traceback=False, max_errors=len(exs))
            res = ev(prog)
            rows = []
            for ex, pred, score in res.results:
                hs = getattr(pred, 'headings', None)
                s, fb, det = g.evaluate_headings(ex.text, ex.gold, hs)
                rows.append(dict(id=ex.id, score=float(score), **det,
                                 headings=[g._as_dict(h) for h in (hs or [])]))
            results[f'{c}|{sname}'] = rows
            print(f'[{c:15s} | {sname:6s}] mean {float(res.score):6.2f}  (n={len(exs)})', flush=True)
            Path(a.out).write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf8')


if __name__ == '__main__':
    main()
