# toc-extraction-tibetan

The lab for the BuddhistAI skill `toc-extraction-tibetan`: find the sa-bcad (ས་བཅད) outline of a Tibetan commentary, with each heading's nesting level and position. This repo holds the benchmark, every skill variant we tried, the runs, and the ranking report. The winner ships in [BuddhistAI/buddhist-skills](https://github.com/BuddhistAI/buddhist-skills/tree/main/skills/toc-extraction-tibetan); the evaluation data is also published as [buddhist-benchmarks `toc-extraction/bo` v1](https://github.com/BuddhistAI/buddhist-benchmarks/tree/main/tasks/toc-extraction/data/bo/v1).

**Read first: [REPORT.md](./REPORT.md)** (ranking on Claude Haiku 5.5 and Sonnet 5.5).

## Layout

```
benchmark/            version 1.0.0 (see benchmark/CHANGELOG.md)
  sources/*.epub      the two public-domain books
  build_dataset.py    EPUB -> data/ (outline tree from the Tibetan-Sabche paragraphs)
  data/               per book: raw.txt, toc.json, toc_tree.txt, inline_toc.xml; dataset.jsonl (138 passages)
  toc_lib.py          outline tree, rendering, anchor location
  gepa_toc.py         DSPy task, metric with feedback, GEPA optimisation
  bench_skills.py     runs variants on the benchmark
variants/<name>/      SKILL.md (with metadata.version) + VARIANT.md
results/              one JSON + log per model and run; summary tables
scripts/              summarize.py, export_buddhist_benchmarks.py, to_benchmark_run.py
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

Every variant has `metadata.version` (semver). The benchmark has its own version in `benchmark/CHANGELOG.md`: patch = fixed references, minor = new items (with a note on what each tests and where it came from), major = scorer or format change. A new benchmark version means re-running the promoted skill and the challengers.

## License

MIT. The two Tibetan texts are public domain. `variants/sabcad-outliner/` is published under MIT with its author's agreement.
