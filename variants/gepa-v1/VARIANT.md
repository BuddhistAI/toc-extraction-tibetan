# gepa-v1 (version 1.0.0)

- **Made by:** WeBuddhist (NT), with DSPy GEPA, 2026-11-02.
- **How:** started from the [seed](../seed/) prompt and let GEPA rewrite the instructions using the benchmark's feedback metric. Task model `claude-haiku-4-5`, reflection model `claude-sonnet-4-5`, `auto=light`, 24 train + 24 val passages from the Vasubandhu book. The log is in `gepa_run.log`.
- **Files:** `SKILL.md` (the instructions as a skill), `program.json` (the same instructions as a DSPy program; this is what the harness loads).
- **Caveat:** the optimiser wrote some rules that quote training passages ("in the first example ..."). They still read as rules, but they are fitted to one book.
- **Different from the promoted skill:** a self-contained prompt of numbered rules learned from benchmark feedback, instead of the sabcad-outliner method. Shorter, and it does not need the reference files.
- **Tested with:** Claude Haiku 5.5 and Sonnet 5.5 on `toc-extraction/bo@1.0.0`, 3 runs each: structure_f1 0.824 and 0.949 (mean 0.886). That is a near-tie with the promoted skill (0.823 and 0.962). It is better on the held-out book and on the per-passage score. Re-run it after the benchmark's held-out references are fixed (1.0.1).
- **History:** this variant was also kept as a challenger in buddhist-skills `drafts/toc-extraction-tibetan/webuddhist-gepa-v1/` until 2026-11-18. Challengers now live only in their task's workshop repo.
