# sabcad-outliner-toc (version 1.0.0)

- **Made by:** WeBuddhist (NT), 2026-11-13, from [sabcad-outliner 1.0.0](../sabcad-outliner/).
- **What is different:** the benchmark adapter is now part of the skill, as a "task" section on top, plus the output format and rendering rules from gepa-v1. The colleague's `SKILL.md`, `references/methods.md` and `references/code-scheme.md` follow unchanged. `scripts/` and `references/format-spec.md` (the .docx format) are left out.
- **Why:** sabcad-outliner had the best headline score (structure_f1) on Haiku 5.5, but its own deliverable is a .docx. This variant is the form that could ship as `toc-extraction-tibetan`. It tied with gepa-v1 and was not promoted (see REPORT.md); it is the main challenger.
- **Benchmarked:** directly, as condition `skill:variants/sabcad-outliner-toc` (see REPORT.md).
