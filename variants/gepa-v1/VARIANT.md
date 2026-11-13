# gepa-v1 (version 1.0.0)

- **Made by:** WeBuddhist (NT), with DSPy GEPA, 2026-11-02.
- **How:** started from the [seed](../seed/) prompt and let GEPA rewrite the instructions using the benchmark's feedback metric. Task model `claude-haiku-4-5`, reflection model `claude-sonnet-4-5`, `auto=light`, 24 train + 24 val passages from the Vasubandhu book. The log is in `gepa_run.log`.
- **Files:** `SKILL.md` (the instructions as a skill), `program.json` (the same instructions as a DSPy program; this is what the harness loads).
- **Caveat:** the optimiser wrote some rules that quote training passages ("in the first example ..."). They still read as rules, but they are fitted to one book.
