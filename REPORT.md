# Ranking report: toc-extraction-tibetan skills

_2026-11-13 · benchmark 1.0.0 · models Claude Haiku 5.5 (`claude-haiku-5-5`) and Claude Sonnet 5.5 (`claude-sonnet-5-5`) · 3 runs per variant and model_

## Result

**Promoted: sabcad-outliner-toc 1.0.0**, the colleague's sa-bcad method packaged as a TOC skill. It has the best headline score (structure_f1, the buddhist-benchmarks metric that promotion is based on) of the three variants that can ship as a TOC skill, averaged over both models. It ties gepa-v1 on Haiku 5.5 and beats it on Sonnet 5.5.

**It is a near-tie with gepa-v1.** The 0.007 gap is within run-to-run noise, and the two metrics disagree. The per-passage lab score, which counts short passages as much as long ones, prefers gepa-v1. So does the book no skill was tuned on. The held-out book's references are known to be incomplete (see "Known problems"), so after they are fixed (benchmark 1.0.1), re-run both before treating this as settled.

| Variant | Ships as a TOC skill | structure_f1, Haiku 5.5 | structure_f1, Sonnet 5.5 | structure_f1, mean | Lab score, mean | Held-out book, mean |
| --- | --- | --- | --- | --- | --- | --- |
| **sabcad-outliner-toc 1.0.0** | yes | 0.823 ± 0.022 | 0.962 ± 0.007 | **0.893** | 92.4 | 83.8 |
| gepa-v1 1.0.0 | yes | 0.824 ± 0.012 | 0.949 ± 0.020 | 0.886 | **93.9** | **87.8** |
| seed 0.1.0 | yes | 0.741 ± 0.022 | 0.951 ± 0.005 | 0.846 | 86.0 | 79.4 |
| sabcad-outliner 1.0.0 (adapter) | no, .docx skill | **0.859** ± 0.017 | 0.946 ± 0.014 | **0.903** | 93.4 | 79.7 |
| sabcad-outliner 1.0.0 + script | no, .docx skill | 0.831 ± 0.012 | **0.968** ± 0.001 | 0.899 | 90.9 | 78.9 |

The two sabcad-outliner rows are the colleague's original .docx skill, run through the benchmark adapter in `benchmark/bench_skills.py`. They can't ship as they are. sabcad-outliner-toc is the same skill with the adapter written into it.

## What was measured

- **Task.** Given a passage of Tibetan commentary with all formatting and line breaks removed, return every sa-bcad heading in reading order, with its depth (relative to the passage) and its first 40 characters verbatim.
- **Data.** Two public-domain books, cut into passages of about 6,000 characters at heading boundaries:
  - **Same book:** 76 passages of Jamyang Loter Wangpo's *A Lamp Illuminating the Intent of Vasubandhu*, 369 headings. GEPA never saw these 76, but it was tuned on 48 other passages of this book.
  - **Held-out book:** all 9 passages of Chenga Chökyi Gyalpo's *The Jewel Garland*, 25 headings. No variant was tuned on it.
- **Lab score.** Computed per passage as 0.3 × position F1 + 0.7 × (position and depth) F1, ×100, then averaged over passages. A heading counts as found if it starts within 3 characters of the reference.
- **structure_f1.** The buddhist-benchmarks headline: micro F1 over all 394 headings, where a match needs both position and depth. The official scorer (`toc-extraction` scorer 1.0.0) gives the same numbers as the lab harness.
- **Harness.** DSPy 3.5.0 `ChainOfThought` with a typed `headings` output (`benchmark/bench_skills.py`), temperature 1.0 (the only value Claude 5.5 models accept), 3 runs. ± is the standard deviation between runs.

## Variants

| Variant | Version | Instructions | Origin |
| --- | --- | --- | --- |
| gepa-v1 | 1.0.0 | 11k chars | Seed prompt optimised by DSPy GEPA (task model Haiku 4.5, reflection Sonnet 4.5), 2026-11-02 |
| sabcad-outliner-toc | 1.0.0 | 21k chars | sabcad-outliner with a TOC task section on top; scripts and the .docx spec removed |
| sabcad-outliner | 1.0.0 | 21k chars | A colleague's .docx outliner skill: SKILL.md, methods.md and code-scheme.md behind a benchmark adapter. "+ script" also passes the output of its `extract_sabcad.py` |
| seed | 0.1.0 | 0.6k chars | One-paragraph hand-written prompt |

## Full results

### Claude Haiku 5.5

| Rank | Variant | Runs | All 85 | Same book (76) | Held-out book (9) | structure_f1 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | gepa-v1 1.0.0 | 3 | 91.1 ± 1.0 | 91.7 ± 1.2 | 85.5 ± 2.5 | 0.824 ± 0.012 |
| 2 | sabcad-outliner 1.0.0 | 3 | 90.7 ± 0.5 | 92.1 ± 0.2 | 78.6 ± 3.3 | 0.859 ± 0.017 |
| 3 | sabcad-outliner-toc 1.0.0 | 3 | 87.9 ± 2.0 | 88.7 ± 1.9 | 81.0 ± 5.3 | 0.823 ± 0.022 |
| 4 | sabcad-outliner 1.0.0 + script | 3 | 84.8 ± 1.1 | 86.6 ± 1.0 | 69.6 ± 3.2 | 0.831 ± 0.012 |
| 5 | seed 0.1.0 | 3 | 75.8 ± 1.4 | 75.7 ± 1.8 | 76.5 ± 2.2 | 0.741 ± 0.022 |

### Claude Sonnet 5.5

| Rank | Variant | Runs | All 85 | Same book (76) | Held-out book (9) | structure_f1 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | sabcad-outliner 1.0.0 + script | 3 | 97.0 ± 0.2 | 98.0 ± 0.1 | 88.2 ± 1.6 | 0.968 ± 0.001 |
| 2 | sabcad-outliner-toc 1.0.0 | 3 | 97.0 ± 0.2 | 98.2 ± 0.3 | 86.6 ± 0.9 | 0.962 ± 0.007 |
| 3 | gepa-v1 1.0.0 | 3 | 96.7 ± 0.9 | 97.4 ± 1.1 | 90.1 ± 0.0 | 0.949 ± 0.020 |
| 4 | seed 0.1.0 | 3 | 96.2 ± 0.1 | 97.9 ± 0.1 | 82.3 ± 1.6 | 0.951 ± 0.005 |
| 5 | sabcad-outliner 1.0.0 | 3 | 96.2 ± 0.5 | 98.0 ± 0.6 | 80.7 ± 3.0 | 0.946 ± 0.014 |

### Both models (mean of the two model means)

| Rank | Variant | All 85 | Held-out book (9) | structure_f1 |
| --- | --- | --- | --- | --- |
| 1 | gepa-v1 1.0.0 | 93.9 | 87.8 | 0.886 |
| 2 | sabcad-outliner 1.0.0 | 93.4 | 79.7 | 0.903 |
| 3 | sabcad-outliner-toc 1.0.0 | 92.4 | 83.8 | 0.893 |
| 4 | sabcad-outliner 1.0.0 + script | 90.9 | 78.9 | 0.899 |
| 5 | seed 0.1.0 | 86.0 | 79.4 | 0.846 |

"All 85" and the set columns are lab scores. Raw per-passage results, including every predicted heading for runs 2 and 3, are in `results/`.

## What the numbers say

1. **The skills matter a lot on the cheap model, and little on the medium one.** On Haiku 5.5, gepa-v1 lifts the seed prompt from 75.8 to 91.1. On Sonnet 5.5, the one-paragraph seed already scores 97.9 on the same-book passages, and every variant lands between 96.2 and 97.0 overall.
2. **The book nobody was tuned on separates them.** gepa-v1 scores 85.5 on it with Haiku and 90.1 with Sonnet (identical in all 3 Sonnet runs). The colleague's skill scores 78.6 and 80.7.
3. **The colleague's skill is very strong on the same book, with no tuning.** It edges out gepa-v1 there (92.1 vs 91.7 on Haiku, 98.0 vs 97.4 on Sonnet), even though gepa-v1 was tuned on that book.
4. **The script helps Sonnet and hurts Haiku.** Feeding `extract_sabcad.py` output into sabcad-outliner gives the best Sonnet score (97.0, structure_f1 0.968) and the worst non-seed Haiku score (84.8). Haiku seems to over-trust the script's candidate list.
5. **Previous results don't carry over.** On 2026-11-05 with Haiku 4.5, gepa-v1 scored 89.2 and the colleague's skill 55.0 on the same-book set (`results/history/`). On Haiku 5.5 they are tied. Re-run the ranking whenever the default models change.

## Known problems

- **The held-out book's references miss headings.** Every variant predicts about 1.5 times as many headings as the references hold for *The Jewel Garland*, with recall near 1.0. About 12 positions are predicted in most runs of every variant and are missing from the references. Spot-checked, they are real sa-bcad headings, for example ``གཉིས་པ་བྱམས་པའི་བོ་ངོ་ནི།`` and ``བཞི་པ་བྱམས་པའི་བྱེད་ལས་ནི།``. The EPUB marked only some outline levels as `Tibetan-Sabche`. This lowers precision for every variant. It may also favour variants that find fewer headings. A Tibetan reader should review these 9 passages, which would give benchmark 1.0.1 (a patch: references fixed). Then re-run gepa-v1 and sabcad-outliner-toc.
- **The held-out set is small** (9 passages, 25 headings). Adding passages from other books would be a minor version (1.1.0).
- **References are silver.** Depths are rebuilt from the outline grammar, not checked by hand.
- **gepa-v1 includes rules that quote its training passages** ("in the first example ..."). They read as general rules, but a GEPA run on more books would likely give a cleaner prompt.

## Next steps

1. sabcad-outliner-toc scores lower on Haiku than the adapter version of the same skill (0.823 vs 0.859). The wording of its new task section, or the rendering section copied from gepa-v1, seems to cost Haiku something. A 1.0.1 that keeps the adapter's wording exactly is worth a run.
1. Fix the *Jewel Garland* references (benchmark 1.0.1) and re-run the top two variants.
2. Add passages from at least two more books with embedded sa-bcad (1.1.0), each with a note on what it tests.
3. Re-run GEPA with Haiku 5.5 as the task model, using sabcad-outliner's rules as the seed. Combining the two is the most likely way to beat both.
