#!/usr/bin/env python3
"""gepa_toc.py - optimise a "TOC extraction" skill for raw Tibetan commentary with DSPy GEPA.

Task (one chunk = one example):
    input : raw passage, all formatting/line-returns stripped
    output: list of headings  {depth, anchor, title}
            depth  1 = shallowest level present in the passage
            anchor first <=40 chars of the heading, verbatim (used to locate it in the text)
            title  short label (shown in the tree, NOT scored)
From that list the code renders the two deliverables: the formatted TOC tree and the text with
inline nested <section depth=".."> XML (toc_lib.render_tree / render_inline_xml).

Usage
  python gepa_toc.py selftest                       # no LLM needed: metric + renderer sanity checks
  python gepa_toc.py baseline  --task-model M        # score the un-optimised seed prompt on val/test
  python gepa_toc.py optimize  --task-model M --reflection-model R [--auto light]
  python gepa_toc.py eval      --program out/program.json --task-model M
  python gepa_toc.py predict   --program out/program.json --task-model M --file data/RCP-FM-07/raw.txt
API keys are read from the environment (e.g. ANTHROPIC_API_KEY) by litellm.
"""
import argparse, json, random, sys
from pathlib import Path
import dspy
from pydantic import BaseModel, Field

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from toc_lib import locate_anchors, render_tree, render_inline_xml, strip_xml

ANCHOR_LEN = 40
TOL = 3


def load_env(path=HERE / '.env'):
    """minimal .env loader (KEY=VALUE lines); real environment variables win."""
    import os
    if path.exists():
        for line in path.read_text(encoding='utf8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"\''))


load_env()          # chars of slack when matching a located anchor to a gold heading start (e.g. missing "༈ ")


# ------------------------------------------------------------------ task definition
class Heading(BaseModel):
    depth: int = Field(description="1 = shallowest heading level present in this passage")
    anchor: str = Field(description="first 40 characters of the heading, copied verbatim from the passage")
    title: str = Field(description="short Tibetan label for the section")


SEED_INSTRUCTIONS = (
    "You are given a passage of a Tibetan Buddhist commentary in which all formatting and line breaks have been "
    "removed. Find every outline heading (ས་བཅད, sa-bcad) in the passage, in reading order. For each heading "
    "return: depth (1 = the shallowest heading level present in this passage, 2 = a sub-section of a depth-1 "
    "heading, and so on), anchor (the first 40 characters of the heading copied verbatim from the passage, "
    "starting at its first character, including a leading ༈ if there is one) and title (a short label of the "
    "section). Return an empty list if the passage contains no headings."
)


class ExtractTOC(dspy.Signature):
    text: str = dspy.InputField(desc="raw Tibetan passage without formatting")
    headings: list[Heading] = dspy.OutputField(desc="all outline headings in reading order")


ExtractTOC = ExtractTOC.with_instructions(SEED_INSTRUCTIONS)


class TOCExtractor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractTOC)

    def forward(self, text):
        return self.extract(text=text)


# ------------------------------------------------------------------ data
def load_dataset(path, max_chars=6500):
    sets = {'train': [], 'val': [], 'test': []}
    for line in open(path, encoding='utf8'):
        r = json.loads(line)
        if r['split'] not in sets or len(r['raw_text']) > max_chars:
            continue
        ex = dspy.Example(text=r['raw_text'], gold=r['headings'], id=r['id']).with_inputs('text')
        sets[r['split']].append(ex)
    return sets


def subsample(exs, n, seed=0):
    """keep every example that has headings first; at most one heading-less example."""
    exs = list(exs)
    random.Random(seed).shuffle(exs)
    with_h = [e for e in exs if e.gold]
    without = [e for e in exs if not e.gold][:1]
    return (with_h + without)[:n] if n else with_h + without


# ------------------------------------------------------------------ metric
def _f1(tp, n_pred, n_gold):
    if n_pred == 0 and n_gold == 0:
        return 1.0
    if tp == 0:
        return 0.0
    p, r = tp / n_pred, tp / n_gold
    return 2 * p * r / (p + r)


def _ancestors(gold):
    stack, out = [], []
    for h in gold:
        while stack and stack[-1]['depth'] >= h['depth']:
            stack.pop()
        out.append(' > '.join(s['title'] for s in stack if s['title']) or '(top level of passage)')
        stack.append(h)
    return out


def _as_dict(h):
    return h if isinstance(h, dict) else h.model_dump() if hasattr(h, 'model_dump') else dict(h)


def evaluate_headings(raw, gold, pred_headings):
    """-> (score, feedback, details)"""
    pred = [_as_dict(h) for h in (pred_headings or [])]
    pos = locate_anchors(raw, [p.get('anchor', '') for p in pred])
    located = [(pos[i], int(p.get('depth', 0) or 0), p) for i, p in enumerate(pred) if pos[i] is not None]
    unlocated = [p for i, p in enumerate(pred) if pos[i] is None]
    # one-to-one greedy match on start offset (+-TOL)
    gstarts = [g['start'] for g in gold]
    used, match = set(), {}
    for pi, (ps, pd, _) in enumerate(located):
        best = None
        for gi, gs in enumerate(gstarts):
            if gi in used or abs(gs - ps) > TOL:
                continue
            if best is None or abs(gs - ps) < abs(gstarts[best] - ps):
                best = gi
        if best is not None:
            used.add(best)
            match[pi] = best
    tp_pos = len(match)
    tp_depth = sum(1 for pi, gi in match.items() if located[pi][1] == gold[gi]['depth'])
    ng, np_ = len(gold), len(pred)
    f_pos, f_depth = _f1(tp_pos, np_, ng), _f1(tp_depth, np_, ng)
    score = 0.3 * f_pos + 0.7 * f_depth

    anc = _ancestors(gold)
    fb = [f"Gold has {ng} heading(s); you returned {np_} ({len(unlocated)} anchor(s) not found verbatim in the text). "
          f"Position F1={f_pos:.2f}, position+depth F1={f_depth:.2f}."]
    missed = [gi for gi in range(ng) if gi not in used]
    for gi in missed[:6]:
        g = gold[gi]
        fb.append(f"MISSED heading (gold depth {g['depth']}, parent: {anc[gi]}) starting: \"{g['anchor']}\"")
    if len(missed) > 6:
        fb.append(f"... and {len(missed) - 6} more missed headings.")
    wrong_depth = [(pi, gi) for pi, gi in match.items() if located[pi][1] != gold[gi]['depth']]
    for pi, gi in wrong_depth[:6]:
        fb.append(f"WRONG DEPTH for \"{gold[gi]['anchor']}\": you said {located[pi][1]}, gold is "
                  f"{gold[gi]['depth']} (parent chain: {anc[gi]}).")
    spurious = [located[pi] for pi in range(len(located)) if pi not in match]
    for ps, pd, p in spurious[:5]:
        fb.append(f"SPURIOUS heading (not an outline heading in gold): \"{p.get('anchor', '')[:40]}\"")
    for p in unlocated[:3]:
        fb.append(f"ANCHOR NOT FOUND verbatim in the passage (copy characters exactly): \"{p.get('anchor', '')[:40]}\"")
    if ng == 0 and np_ == 0:
        score, fb = 1.0, ["Correct: the passage has no headings and you returned none."]
    elif ng == 0:
        score = max(0.0, 1.0 - 0.25 * np_)
    if score >= 0.999:
        fb = ["Perfect: every heading found with the right depth."]
    return score, '\n'.join(fb), dict(tp_pos=tp_pos, tp_depth=tp_depth, n_gold=ng, n_pred=np_)


def toc_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
    score, fb, _ = evaluate_headings(gold.text, gold.gold, getattr(pred, 'headings', None))
    return dspy.Prediction(score=score, feedback=fb)


def toc_score(gold, pred, trace=None):
    return evaluate_headings(gold.text, gold.gold, getattr(pred, 'headings', None))[0]


# ------------------------------------------------------------------ outputs
def render_outputs(raw, headings):
    hs = [_as_dict(h) for h in headings]
    pos = locate_anchors(raw, [h.get('anchor', '') for h in hs])
    rows = sorted([dict(depth=max(1, int(h['depth'])), start=p, title=h.get('title', ''))
                   for h, p in zip(hs, pos) if p is not None], key=lambda r: r['start'])
    return render_tree(rows), render_inline_xml(raw, rows)


def export_skill(program, out_dir, extra=''):
    instr = next(iter(program.named_predictors()))[1].signature.instructions
    d = Path(out_dir) / 'skills' / 'extract-tibetan-toc'
    d.mkdir(parents=True, exist_ok=True)
    (d / 'SKILL.md').write_text(f"""---
name: extract-tibetan-toc
description: Extract a hierarchical table of contents (sa-bcad outline) from raw Tibetan Buddhist commentary text whose formatting and line breaks have been stripped, and return a TOC tree plus the text with inline XML section markup. Use when given unformatted Tibetan commentary and asked for its outline, TOC or section structure.
---

# Extract a TOC from raw Tibetan commentary

{instr.strip()}

## Output format

Return a JSON list, in reading order, of objects:

```json
[{{"depth": 1, "anchor": "<first <=40 characters of the heading, verbatim>", "title": "<short label>"}}]
```

* `depth` is relative: 1 is the shallowest level present in the passage you were given.
* `anchor` must be an exact substring of the passage and must start at the first character of the heading
  (including a leading ༈).

## Rendering the two deliverables

1. **TOC tree** - one line per heading, indented two spaces per depth level, prefixed with a dotted
   sibling number (1, 1.1, 1.1.1, ...) followed by the title.
2. **Inline XML** - wrap the whole passage in `<text>`; at each heading's start insert
   `<section depth="N" title="...">` and close it (`</section>`) just before the next heading of the same or a
   shallower depth, or at the end of the text. Escape `& < >`. Removing the tags must give back the input
   text exactly.
{extra}""", encoding='utf8')
    return d / 'SKILL.md'


# ------------------------------------------------------------------ CLI
def load_key():
    """ANTHROPIC_API_KEY from the environment, else .env, else keys/api.txt (all git-ignored). Never printed."""
    import os, re
    for f in (HERE / '.env', HERE / 'keys' / 'api.txt', HERE / 'keys' / 'workspace.txt'):
        if not f.exists():
            continue
        t = f.read_text(encoding='utf8')
        m = re.search(r'(sk-ant-[A-Za-z0-9_\-]+)', t)
        if m and not os.environ.get('ANTHROPIC_API_KEY'):
            os.environ['ANTHROPIC_API_KEY'] = m.group(1)
        m = re.search(r'(wrkspc_[A-Za-z0-9]+)', t)          # user-scoped keys need a workspace id
        if m and not os.environ.get('ANTHROPIC_WORKSPACE_ID'):
            os.environ['ANTHROPIC_WORKSPACE_ID'] = m.group(1)


def make_lm(name, temperature=0.0, max_tokens=8000):
    import os
    kw = {}
    if os.environ.get('ANTHROPIC_WORKSPACE_ID'):
        kw['extra_headers'] = {'anthropic-workspace-id': os.environ['ANTHROPIC_WORKSPACE_ID']}
    return dspy.LM(name, temperature=temperature, max_tokens=max_tokens, cache=False, **kw)


def run_eval(program, devset, threads, label):
    ev = dspy.Evaluate(devset=devset, metric=toc_score, num_threads=threads, display_progress=True, display_table=0)
    res = ev(program)
    print(f"[{label}] mean score over {len(devset)} chunks: {float(res.score):.2f}/100")
    return float(res.score)


def selftest():
    sets = load_dataset(HERE / 'data' / 'train.jsonl', max_chars=10 ** 9)
    ok = True
    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(('PASS ' if cond else 'FAIL ') + name)
    allx = sets['train'] + sets['val'] + sets['test']
    check('dataset loaded (%d chunks)' % len(allx), len(allx) > 50)
    perfect = bad_xml = 0
    for ex in allx:
        pred = [dict(depth=h['depth'], anchor=h['anchor'], title=h['title']) for h in ex.gold]
        s, fb, _ = evaluate_headings(ex.text, ex.gold, pred)
        perfect += (s > 0.999)
        tree, xml = render_outputs(ex.text, pred)
        bad_xml += (strip_xml(xml) != ex.text)
    check('gold-as-prediction scores 1.0 on every chunk', perfect == len(allx))
    check('rendered XML round-trips to the raw text on every chunk', bad_xml == 0)
    ex = next(e for e in sets['train'] if len(e.gold) >= 4)
    g = ex.gold
    shallow = [dict(depth=1, anchor=h['anchor'], title='') for h in g]
    s, fb, _ = evaluate_headings(ex.text, g, shallow)
    check('flat (all depth 1) prediction scores well below 1 (%.2f)' % s, s < 0.7)
    drop = [dict(depth=h['depth'], anchor=h['anchor'], title='') for h in g[1:]]
    s2, fb2, _ = evaluate_headings(ex.text, g, drop)
    check('dropping a heading is reported as MISSED (%.2f)' % s2, 'MISSED' in fb2 and s2 < 1)
    junk = [dict(depth=1, anchor='not in the text at all', title='')]
    s3, fb3, _ = evaluate_headings(ex.text, g, junk)
    check('unlocatable anchor gets 0 and ANCHOR NOT FOUND feedback', s3 == 0 and 'NOT FOUND' in fb3)
    nm = dict(depth=1, anchor=g[0]['anchor'][2:], title='')   # slightly shifted anchor, within TOL
    check('anchor shifted by 2 chars still matches', evaluate_headings(ex.text, g[:1], [nm])[0] > 0.999)
    # module wiring with a dummy LM
    try:
        from dspy.utils import DummyLM
        h0 = g[0]
        dummy = DummyLM([{'reasoning': 'r', 'headings': json.dumps([dict(depth=h0['depth'], anchor=h0['anchor'], title='t')],
                                                                  ensure_ascii=False)}])
        with dspy.context(lm=dummy):
            out = TOCExtractor()(text=ex.text)
        check('TOCExtractor parses a structured output via DummyLM', len(out.headings) == 1 and out.headings[0].depth == h0['depth'])
        m = toc_metric(ex, out)
        check('toc_metric returns Prediction(score, feedback)', hasattr(m, 'score') and hasattr(m, 'feedback'))
    except Exception as e:  # pragma: no cover
        check('DummyLM wiring (%r)' % e, False)
    print('SELFTEST', 'OK' if ok else 'FAILED')
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['selftest', 'baseline', 'optimize', 'eval', 'predict'])
    ap.add_argument('--data', default=str(HERE / 'data' / 'train.jsonl'))
    ap.add_argument('--out', default=str(HERE / 'out'))
    ap.add_argument('--task-model', default='anthropic/claude-haiku-4-5')
    ap.add_argument('--reflection-model', default='anthropic/claude-sonnet-4-5')
    ap.add_argument('--auto', default='light', choices=['light', 'medium', 'heavy'])
    ap.add_argument('--n-train', type=int, default=24)
    ap.add_argument('--n-val', type=int, default=24)
    ap.add_argument('--max-chars', type=int, default=6500, help='skip chunks longer than this')
    ap.add_argument('--threads', type=int, default=8)
    ap.add_argument('--program')
    ap.add_argument('--file')
    a = ap.parse_args()
    if a.mode == 'selftest':
        sys.exit(0 if selftest() else 1)

    load_key()
    dspy.configure(lm=make_lm(a.task_model))
    sets = load_dataset(a.data, a.max_chars)
    train, val = subsample(sets['train'], a.n_train), subsample(sets['val'], a.n_val, seed=1)
    import eval_data  # held-out book from buddhist-benchmarks, pinned in benchmark.json
    test = sets['test'] or eval_data.load_eval_sets(a.max_chars)['test']
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    prog = TOCExtractor()
    if a.program:
        prog.load(a.program)

    if a.mode == 'baseline':
        run_eval(prog, val, a.threads, 'seed prompt / val')
        run_eval(prog, test, a.threads, 'seed prompt / test (held-out book)')
    elif a.mode == 'eval':
        run_eval(prog, val, a.threads, 'val')
        run_eval(prog, test, a.threads, 'test (held-out book)')
    elif a.mode == 'optimize':
        gepa = dspy.GEPA(metric=toc_metric, auto=a.auto, reflection_lm=make_lm(a.reflection_model, 1.0, 32000),
                         num_threads=a.threads, track_stats=True, reflection_minibatch_size=3,
                         log_dir=str(out / 'gepa_logs'), seed=0)
        best = gepa.compile(prog, trainset=train, valset=val)
        best.save(str(out / 'program.json'))
        sk = export_skill(best, out)
        print('saved', out / 'program.json', 'and', sk)
        run_eval(TOCExtractor(), val, a.threads, 'seed prompt / val')
        run_eval(best, val, a.threads, 'GEPA-optimised / val')
        run_eval(best, test, a.threads, 'GEPA-optimised / test (held-out book)')
    elif a.mode == 'predict':
        raw = Path(a.file).read_text(encoding='utf8').strip()
        if len(raw) > a.max_chars:
            print(f'warning: {len(raw)} chars > --max-chars; run on passages of about that size '
                  f'(depth is relative to each passage).', file=sys.stderr)
        res = prog(text=raw)
        tree, xml = render_outputs(raw, res.headings)
        (out / 'pred_toc_tree.txt').write_text(tree + '\n', encoding='utf8')
        (out / 'pred_inline_toc.xml').write_text(xml, encoding='utf8')
        print(tree)


if __name__ == '__main__':
    main()
