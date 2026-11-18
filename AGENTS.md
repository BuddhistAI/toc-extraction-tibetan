# Notes for agents working in this repo

## Start here (every BuddhistAI repo)

- Read the maintainer handbook first: https://buddhistai.github.io/knowledge-base/handbook/ (source: BuddhistAI/knowledge-base `handbook/`). Follow its rules and conventions.
- Check the Development board for cards assigned to you: https://github.com/orgs/BuddhistAI/projects/3. Status and next steps: `handbook/status.md`.
- Rules: plain English for non-native readers, no idioms. "Buddhist tasks", not only texts. "Top performance" and "Best value". Neutral credits: WeBuddhist is one contributor among others. Never invent data, scores, votes or links. Never edit generated files by hand.
- buddhist-benchmarks stays clean (short `result.json`, outputs, scores). Provenance records (`buddhistai/provenance@1`) live in the skill's own repo.
- When you change something the handbook describes, update the handbook in the same pull request.
- Before you change anything users see (pages, forms, install steps, app screens), write a design in `docs/designs/` and run an EGM review with our personas: skills `buddhistai-elephant` and `buddhistai-ux-review` (handbook `ux.md`). Small text or bug fixes skip this.
- EGM artifact directory: docs/designs
- This repo: the workshop repo for the `toc-extraction-tibetan` skill: variants, runs, provenance records and `REPORT.md`. It holds no test data (the benchmark is pinned in `benchmark/benchmark.json`). Run each variant at least 3 times, never tune on the test set, and check records with `python scripts/provenance.py --check`.
