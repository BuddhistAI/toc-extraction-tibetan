---
name: toc-extraction-tibetan
description: Extract the hierarchical table of contents (sa-bcad / ས་བཅད་ outline) of a Tibetan Buddhist commentary whose outline is embedded in the text (ordinals, ལ་གཉིས / ལ་གསུམ announcements, ནི introducers): each heading's nesting level, start position and a short label, plus a TOC tree and the text with inline XML section markup. Use when given Tibetan commentary, with or without formatting, and asked for its outline, TOC or section structure.
metadata:
  task: toc-extraction
  language: tibetan
  language-code: bo
  variant: sabcad-outliner-toc
  version: 1.0.0
  benchmark: toc-extraction-tibetan@1.0.0
  origin: sabcad-outliner 1.0.0 (by a colleague of NT's, MIT) with a task section on top that replaces its .docx deliverable
---

# Extract the sa-bcad outline of a Tibetan text

## The task (this overrides the .docx deliverable described further down)

The input is a passage or a whole Tibetan text whose sa-bcad is embedded in the text itself (regime B below).
Line breaks and folio tags may have been removed. Do NOT produce a .docx, outline codes, folios or review notes, and
do not ask questions. Use the method below only to find the structure. Return the outline as a JSON list of
headings in reading order: one entry per outline element whose transition (its own ordinal + heading / ལ་N / ནི
introducer) occurs in the text.

  depth  = the element's nesting level counted RELATIVE to the text you were given (1 = the shallowest level that
           appears in it, 2 = its sub-division, ...). In the code scheme below this is the code level minus a constant.
  anchor = the first 40 characters of the element's transition point, copied verbatim from the text, starting at
           its first character (including a leading ༈ if present)
  title  = a short label

```json
[{"depth": 1, "anchor": "<first 40 characters of the heading, verbatim>", "title": "<short label>"}]
```

Return an empty list if the text contains no outline elements. For long texts, work in passages of about 6,000
characters cut at heading boundaries, then shift each passage's depths to the depth of its first heading in the
whole text.

## Rendering the two deliverables

1. **TOC tree** - one line per heading, indented two spaces per depth level, prefixed with a dotted
   sibling number (1, 1.1, 1.1.1, ...) followed by the title.
2. **Inline XML** - wrap the whole passage in `<text>`; at each heading's start insert
   `<section depth="N" title="...">` and close it (`</section>`) just before the next heading of the same or a
   shallower depth, or at the end of the text. Escape `& < >`. Removing the tags must give back the input
   text exactly.

## The method (sabcad-outliner 1.0.0, unchanged)

The method below comes from a skill that weaves the outline into a .docx. Ignore its deliverable and its
`scripts/` (not included here); use its rules for recognising outline elements and their levels. Its
`references/methods.md` and `references/code-scheme.md` are next to this file.

# Tibetan sa-bcad outliner

Turn a running Tibetan text into an **interlinear outline**: the sa-bcad (topical
outline) is woven back into the text so that at each topic's first heading you see
a marker line, and where that topic is actually elaborated you see a bracketed
recall line carrying the folio. The deliverable is a `.docx` whose Tibetan text
all lives in a named **"Tibetan" paragraph style** (Microsoft Himalaya 20 pt), with
the outline codes' level-numbers set as subscripts.

The named style matters: because every paragraph is assigned the one "Tibetan"
style, the user can restyle the whole document's font/size in one place in Word.
The engine also sets the font on each run (including the complex-script slot, so
Tibetan Unicode renders reliably) and applies subscript at the run level — since
subscript is a character property it cannot live in a paragraph style, so the
engine always sets it on the level-number digits directly.

This skill is **hybrid by design**. A Python engine owns everything mechanical and
error-prone (code subscripting, folio tags, font, chunking, and a survey of the
text's structural markers). *You* own the judgment: deciding which structural
regime the text is in, assembling and validating the outline tree, and flagging
what you had to infer. Do the thinking; let the engine do the typing.

## The output format (non-negotiable — the engine enforces it)

For every outline element, using its **code** (see Code scheme below):

- **Marker line** at the heading, inside the parent's enumeration:
  `CODE) heading` — e.g. `21A2) རྩོམ་པ་ལ་འཇུག་པའི་ཡན་ལག།`
- **Bracket recall line** immediately before the element's elaboration:
  `[CODE) heading [FIRST-FOLIO]]` — e.g. `[21A2) རྩོམ་པ་ལ་འཇུག་པའི་ཡན་ལག། [003B]]`
  Folio is zero-padded to 3 digits + A/B, e.g. folio 2B → `002B`.
- **Inline folio tags** `[NNNx]` stay in the running text at each page turn.
- The six (or however many) top-level divisions each get their own marker line.
- Marker/bracket **text is the text's own heading form**, not a citation form.
- **Chunking is preserved**: keep the input's line/verse breaks — one input line =
  one paragraph, blank line = blank paragraph.

The marker/bracket *text* is what you produce; the *rendering* (subscripts, font,
run-splitting) is done for you by `scripts/render_outline.py`. You never hand-set
subscripts. See `references/format-spec.md` for the exact layout and more examples.

## Workflow

### 1. Detect the regime — this decides everything

Read enough of the text to classify it. See `references/methods.md` for full
recipes; the short version:

- **A. External published outline exists** (e.g. a Kilty/Jinpa sa-bcad, an ACIP
  dual-page outline the user gives you). → *Mechanical insertion.* Build the tree
  from the external outline, then find each element's transition in the running
  text and place markers/brackets.
- **B. Embedded sa-bcad** — the text announces its own structure with
  `…ལ་N །  h1 །  h2 …  hN །` plus `<ordinal>་ལ / <ordinal>་ནི` introducers.
  → *Mechanical extraction.* Run `scripts/extract_sabcad.py` to survey the
  announcements and ordinals, then assemble the tree with a stack + overrun check.
- **C. No formal sa-bcad** — a sādhana / practice manual that self-structures
  sequentially (`དེ་ནས་ X་ བྱ་བ་ནི།` ritual-stage markers, no nested `ལ་N།`).
  → *Synthesized outline.* You interpret the structure. **Ask the user how many
  levels** they want (the Phabongkha tshe-sgrub used 2 levels: parts, then ritual
  stages). Headings are your paraphrase of the text's own wording; remove nothing.

If unsure which of A/B/C applies, say what you see and ask. Guessing wrong wastes
the whole run.

### 2. Assemble and validate the outline tree

- **Parent** of a code = the longest existing code that is a proper prefix of it.
- **Explained-folio is monotonic** in depth-first order — use it as a position
  anchor and a sanity check (folios must not go backwards as you walk the DFS).
- For regime B, drive assembly from `extract_sabcad.py`'s report: each
  announcement gives a child **count** and **heading list**; match children by
  their heading cores; close a division when its slots are filled. Apply the
  **overrun check** — ordinals appearing beyond a division's declared count are
  inline prose enumeration (a citation saying "first… second…"), not structure.
- Derive each node's ordinal from **its own** `<ord>་ལ/ནི` prefix or from the
  code's own last ordinal char — **never** recompute from sibling position. Deep
  trees legitimately diverge (this is why the engine peels codes literally).

### 3. Place markers and brackets in the running text

Find each element's transition point. Three introducer styles all occur and all
are fine (details + examples in `references/methods.md`):

1. **Direct** `[ordinal]་ལ་[N]` (non-leaf) or `[ordinal]་ནི` (leaf).
2. **Deferred** `[ordinal]་ནི། … འདི་ལ / དེ་ལ [N]` — put the bracket at the `ནི`,
   leave the prose, mark children at the later enumeration.
3. **Topical recap** `[noun]་ལ་[N]` (e.g. `རིམ་བཤད་པ་ལ་གསུམ`).

An element's elaboration can be marked wherever its own heading phrase — or its
code-derived ordinal — recurs near its explained folio together with a `ལ་N`/`ནི`
introducer. This is what lets you resolve otherwise-ambiguous placements.

**Retain the original text — add only codes and formatting.** The single most
important rule: the outliner never paraphrases a heading, abbreviates it, or
deletes source words. The only additions are outline codes and formatting (line
breaks, subscripts, the Tibetan style). So when a division announces its children
by listing their headings inline — the direct-enumeration style
`…ལ་N །  h1 །  h2 …  hN །` — insert each code **inline, immediately before its
heading in the original list**, and add a line break after the `…ལ་N །` count
clause. Do NOT emit separate `CODE) heading` lines with reconstructed headings, and
do NOT delete the list. So

```
༈ འདི་ལ་གསུམ།  h1 །  h2 །  །h3ལོ །     →     ༈ འདི་ལ་གསུམ།
                                              11) h1 །  21) h2 །  །31) h3ལོ །
```

The headings stay byte-for-byte (e.g. `ཚུལ་ལོ།` stays `ཚུལ་ལོ།`, not `ཚུལ།`), the
`།` separators stay, and any inline `[NNN]`/`[NNNx]` folio tag inside a heading
stays put. NEVER do this when the text after the count runs straight into child 1's
prose (the deferred style `…ལ་N་ལས། དང་པོ་ … ནི། …`) or when the "list" is actually
a quoted root-text verse (`… ནི། [source] གྱིས། …verse…`) — a verse cannot be
annotated in place, so those children keep standalone `CODE) heading` marker lines.
The bundled `scripts/annotate_enumeration.py` applies exactly this, with those
guards.

### 4. Annotate enumerations inline, then render the .docx

Write your fully-woven text to a UTF-8 file. For direct-enumeration divisions you
can weave the inline codes yourself (step 3), or weave the older separate
`CODE) heading` marker lines and let the helper fold them into the retained list:

```
python3 scripts/annotate_enumeration.py WOVEN.txt WOVEN.annotated.txt
python3 scripts/render_outline.py WOVEN.annotated.txt OUTPUT.docx
```

`render_outline.py` subscripts every `CODE)` wherever it appears — line-start marker
lines, bracket-line codes, and codes woven inline into an enumeration all render the
same way. If you are instead **redlining an existing .docx** (the user wants the fix
shown as tracked changes rather than a fresh render), do it as INSERTIONS: leave the
original enumeration runs untouched, insert each `CODE) ` and the line break as
`<w:ins>`, and delete the old separate marker-line paragraphs as `<w:del>`. Nothing
in the source text is deleted. See the docx skill's Tracked Changes reference.

The engine peels each leading code into normal-ordinal + subscript-level-digit
runs, keeps inline `[NNNx]` folios plain, creates the named **"Tibetan" style**
(Microsoft Himalaya 20 pt) and assigns it to every paragraph. Override the face
with `--font` / `--size` only if the user asks; the style name stays "Tibetan".

### 5. Verify, then flag honestly

- Confirm folios are monotonic across the DFS and no heading text was altered.
- Reopen the .docx and check a few marker/bracket lines have the expected
  subscript pattern (the level-number digits, not the ordinal, are subscript).
- **Flag with `†`** every node you had to infer without an explicit marker
  (closing subsections, deep completion-stage nesting) and list them for the user
  in a short `_REVIEW-NOTES.txt`. Best-effort-plus-flag is the agreed approach —
  do not silently paper over gaps. Note any OCR fixes you made (e.g. a missing
  `ལ་` before a count) so the user can confirm them.

## Naming

Deliver as `YYYY-MM-DD_<short-title>_outline-inserted_kk.docx` in the project
folder, plus `_REVIEW-NOTES.txt` if anything was flagged.

## Files

- `scripts/render_outline.py` — the docx renderer. Owns subscripts, folios, font,
  chunking. Run it last. This is the reliable part; trust it.
- `scripts/extract_sabcad.py` — surveys embedded `ལ་N།` announcements and ordinal
  markers (regime B). A scaffolding aid whose output you verify, not an oracle.
- `scripts/annotate_enumeration.py` — folds outline codes INLINE into a division's
  retained heading list (run between weaving and rendering). Retains the original
  text verbatim; skips verse/deferred announcements. Conservative by design.
- `references/format-spec.md` — exact output layout and worked examples.
- `references/code-scheme.md` — the odd-digit / even-letter code scheme and the
  deterministic subscript peel.
- `references/methods.md` — the three regimes in detail, with the introducer
  styles, the stack/overrun assembly, and lessons from the delivered texts.
