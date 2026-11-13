---
name: toc-extraction-tibetan
description: Extract a hierarchical table of contents (sa-bcad outline) from raw Tibetan Buddhist commentary text whose formatting and line breaks have been stripped, and return a TOC tree plus the text with inline XML section markup. Use when given unformatted Tibetan commentary and asked for its outline, TOC or section structure.
metadata:
  task: toc-extraction
  language: tibetan
  language-code: bo
  variant: seed
  version: 0.1.0
  benchmark: toc-extraction-tibetan@1.0.0
  origin: hand-written seed prompt that GEPA started from (gepa_toc.py SEED_INSTRUCTIONS)
---

# Extract a TOC from raw Tibetan commentary

You are given a passage of a Tibetan Buddhist commentary in which all formatting and line breaks have been removed. Find every outline heading (ས་བཅད, sa-bcad) in the passage, in reading order. For each heading return: depth (1 = the shallowest heading level present in this passage, 2 = a sub-section of a depth-1 heading, and so on), anchor (the first 40 characters of the heading copied verbatim from the passage, starting at its first character, including a leading ༈ if there is one) and title (a short label of the section). Return an empty list if the passage contains no headings.

## Output format

Return a JSON list, in reading order, of objects:

```json
[{"depth": 1, "anchor": "<first <=40 characters of the heading, verbatim>", "title": "<short label>"}]
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
