# sabcad-outliner (version 1.0.0)

- **Made by:** a colleague of NT's, for the Tsong Khapa Outliner project. Published here under MIT with their agreement (2026-11-13).
- **What it is:** a full skill (`SKILL.md`, `references/`, `scripts/`) that inserts an interlinear sa-bcad outline into a Tibetan text and produces a `.docx`. It was not written for this benchmark.
- **Changes here:** only `metadata.variant` and `metadata.version` were added to the frontmatter. Everything else is unmodified.
- **How it is benchmarked:** the harness prepends a short adapter (`ADAPTER` in `benchmark/bench_skills.py`) telling the model to return the benchmark's heading list instead of a `.docx`, then gives it `SKILL.md`, `references/methods.md` and `references/code-scheme.md` as instructions. Two conditions:
  - `colleague`: instructions only.
  - `colleague+tool`: the same, plus the JSON output of `scripts/extract_sabcad.py` run on the passage.
