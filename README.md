# toc-extraction-tibetan

The workshop for the BuddhistAI skill `toc-extraction-tibetan`: find the sa-bcad (ས་བཅད) outline of a Tibetan commentary, with each heading's nesting level and position. This repo holds every skill variant we tried, the runs, and the ranking report. It does not hold the test data.

## Where this repo fits

| Repo | Role |
| --- | --- |
| **toc-extraction-tibetan** (this one) | The workshop: variants, old versions, experiment runs and reports for one skill. Messy by design. |
| [buddhist-benchmarks](https://github.com/BuddhistAI/buddhist-benchmarks) | The exam for skills: the official test sets, scorers and results for every task. The leaderboards live there: [Tibetan TOC leaderboard](https://buddhistai.github.io/buddhist-benchmarks/tasks/toc-extraction/bo/). |
| [buddhist-skills](https://github.com/BuddhistAI/buddhist-skills) | The shelf: only the current winner of each leaderboard, which is what people install ([`toc-extraction-tibetan`](https://github.com/BuddhistAI/buddhist-skills/tree/main/skills/toc-extraction-tibetan)). |
| [buddhist-bench](https://github.com/BuddhistAI/buddhist-bench) | A different exam: BuddhistBench tests models on Buddhist knowledge, not skills. |

The flow: build a variant here, run it on the official benchmark, add its `result.json` to buddhist-benchmarks (`scripts/to_result_json.py`), and whatever tops the leaderboard is promoted to buddhist-skills.

The evaluation passages are the buddhist-benchmarks data set [`toc-extraction/bo` 2.0.0](https://github.com/BuddhistAI/buddhist-benchmarks/tree/toc-extraction/bo%402.0.0/tasks/toc-extraction/data/bo/v2), pinned in `benchmark/benchmark.json` and downloaded on first use. Only the 48 passages GEPA trained on, which are not part of the benchmark, are kept here (`benchmark/data/train.jsonl`).

**Read first: [REPORT.md](./REPORT.md)** (ranking on Claude Haiku 5.5 and Sonnet 5.5).

## Layout

```
benchmark/
  benchmark.json      the buddhist-benchmarks release used for evaluation (toc-extraction/bo@2.0.0)
  eval_data.py        downloads that release into benchmark/eval/ (git-ignored) and loads it
  data/train.jsonl    the 48 passages GEPA trained on, plus 5 too long or heading-less; not in the benchmark
  sources/*.epub      the two public-domain books the benchmark was built from
  build_dataset.py    EPUB -> data/ (full local rebuild, git-ignored; only needed to make a new benchmark version)
  toc_lib.py          outline tree, rendering, anchor location
  gepa_toc.py         DSPy task, metric with feedback, GEPA optimisation
  bench_skills.py     runs variants on the benchmark
variants/<name>/      SKILL.md (with metadata.version) + VARIANT.md
results/              one JSON + log per model and run; summary tables
scripts/              summarize.py, to_result_json.py (leaderboard rows), to_benchmark_run.py (outputs),
                      export_buddhist_benchmarks.py (new benchmark versions)
```

## Variants

| Variant | Version | What |
| --- | --- | --- |
| [sabcad-outliner-toc](./variants/sabcad-outliner-toc/) | 1.0.0 | sabcad-outliner with the TOC task on top, so it can ship as a TOC skill. **Promoted.** |
| [gepa-v1](./variants/gepa-v1/) | 1.0.0 | GEPA-optimised prompt. Near-tie challenger |
| [sabcad-outliner](./variants/sabcad-outliner/) | 1.0.0 | A colleague's .docx outliner skill, benchmarked through an adapter, with and without its script |
| [seed](./variants/seed/) | 0.1.0 | One-paragraph baseline prompt |

## Run it

```bash
python -m venv .venv && .venv/bin/pip install -r benchmark/requirements.txt
export ANTHROPIC_API_KEY=...        # or put it in benchmark/keys/api.txt (git-ignored)
python benchmark/bench_skills.py --model anthropic/claude-haiku-5-5 --temperature 1.0 \
  --conds ours,colleague,colleague+tool,seed,skill:variants/sabcad-outliner-toc --out results/<date>-haiku-5-5-run1.json
python scripts/summarize.py results/<date>-*-run*.json
```

Claude 5.5 models only accept temperature 1.0, so scores move a little between runs: run each variant at least 3 times.

## Versions

Every variant has `metadata.version` (semver). The benchmark version is the buddhist-benchmarks release pinned in `benchmark/benchmark.json` (history before the move: `benchmark/CHANGELOG.md`): patch = fixed references, minor = new items (with a note on what each tests and where it came from), major = scorer or format change. A new benchmark version means re-running the promoted skill and the challengers.

## License

MIT. The two Tibetan texts are public domain. `variants/sabcad-outliner/` is published under MIT with its author's agreement.
