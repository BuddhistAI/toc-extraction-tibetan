# Changelog: toc-extraction-tibetan benchmark

Semver: **patch** = wrong references fixed; **minor** = new items, each with a note on what it tests and where it came from; **major** = scorer or input/output format changed. Results are only compared within one version.

## Pinned to buddhist-benchmarks 2.0.0 (2026-11-13)

- buddhist-benchmarks `toc-extraction/bo` 2.0.0 is the same 85 items and answers in the standard one-file format (`test.jsonl`: id, input, target, metadata). `eval_data.py` reads it; the evaluation sets are unchanged.

## Moved to buddhist-benchmarks (2026-11-13)

- The evaluation passages (`unused` and `test`) now come only from buddhist-benchmarks `toc-extraction/bo`, pinned in `benchmark.json` (1.0.0, the same 85 passages and references). New versions are released there. This repo keeps the GEPA training passages (`data/train.jsonl`), the EPUBs and the build script.

## 1.0.0 (2026-11-13)

- Two books: *A Lamp Illuminating the Intent of Vasubandhu* (IBA-LWS-08, 129 passages) and *The Jewel Garland* (RCP-FM-07, 9 passages), cut into passages of about 6,000 characters at heading boundaries.
- Evaluation sets: `unused` (76 passages of the first book that GEPA never saw) and `test` (the 9 passages of the second book). `seen` (48 passages) is GEPA's training and validation data.
- Score per passage: 0.3 × position F1 + 0.7 × position-and-depth F1 (a heading matches if it starts within 3 characters). Also exported as buddhist-benchmarks `toc-extraction/bo` 1.0.0, whose headline `structure_f1` is the micro F1 over all headings.
- Known issue: the Jewel Garland references miss many real headings (see REPORT.md). To fix in 1.0.1 after review by a Tibetan reader.
