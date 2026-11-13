# Methods: the three regimes

Detect the regime first — it determines whether the outline is *extracted*
mechanically or *synthesized* by you. When in doubt, describe what you see in the
text and ask the user before committing.

---

## Regime A — external published outline (mechanical insertion)

The user supplies (or names) a sa-bcad from a published source: e.g. the
Kilty/Jinpa outline for *rim-lnga gsal-sgron*, an ACIP dual-page outline, a
Thurman outline. The structure is authoritative; your job is to place it into the
running text.

Steps:
1. Build the tree from the external outline. Parent = longest existing code that
   is a proper prefix. The external outline usually already carries codes and
   folios; preserve them (including subscripts).
2. Walk the tree depth-first. The explained-folio is monotonic in DFS order — use
   it as a position anchor.
3. For each element, find its transition in the clean running text:
   - non-leaf: `[ordinal]་ལ་[N]` (the division announces N children);
   - leaf: `[ordinal]་ནི` (elaboration follows).
   Split a division's children by matching the outline heading cores against the
   text, handling both `།`-separated and `དང་`-separated enumerations.
4. Emit a marker line at each child's heading and a bracket recall line before its
   elaboration. Marker/bracket text is the **text's own** heading wording, not the
   outline's citation form when they differ.
5. **Annotate the enumeration inline — retain the original text.** In the
   direct-enumeration style the division already lists its children's headings
   inline (`…ལ་N །  h1 །  h2 …`). Insert each code *inline, before its heading in
   that list*, and add a line break after the `…ལ་N །` count clause. Keep the
   headings and separators verbatim (`ཚུལ་ལོ།` stays `ཚུལ་ལོ།`) and keep any inline
   folio tag. Do not emit separate reconstructed-heading marker lines here, and do
   not delete anything. The deferred style (`…ལ་N་ལས། དང་པོ་…ནི།`) and quoted
   root-text verses cannot be annotated in place — those children keep standalone
   `CODE) heading` marker lines. `scripts/annotate_enumeration.py` does this.

Delivered example: `rim-lnga gsal-sgron`, 215/218 elements placed, folios
2B→~309, 0 heading mismatches. The 3 unplaced sat in `†`-gapped subtrees (missing
intermediate headings → the text abbreviates later child headings). Those were
left for manual placement and flagged — the right call.

---

## Regime B — embedded sa-bcad (mechanical extraction)

No external outline; the text announces its own structure. The reliable signal is
an **announcement**:

```
… ལ་ N །   h1 །   h2 །   …   hN (ནོ)། །
```

a clause declaring N sub-topics followed by the list of their headings. Run
`scripts/extract_sabcad.py INPUT.txt` to get every announcement (with count,
folio, and context) plus every ordinal marker.

Assembly (stack machine — you drive it, verifying against the text):
- Each announcement pushes a division expecting **N** children; record its heading
  list.
- Children are introduced by `<ordinal>་ལ` (a non-leaf, which will itself announce
  a count) or `<ordinal>་ནི` (a leaf). Match each to the parent's heading list.
- **Close (pop)** a division when its N slots are filled by leaf `ནི` markers.
  Propagate the cursor on pop so the next sibling attaches to the right parent.
- **Overrun check:** ordinals that appear *beyond* a division's declared count N
  are inline prose enumeration (a quoted verse or citation saying "first… second…
  third…"), **not** structure. Do not open nodes for them. This is the single most
  important guard against a runaway tree.
- Derive each node's ordinal from its own `<ord>` prefix. Topical recaps
  `<noun>་ལ་N` (e.g. `རིམ་བཤད་པ་ལ་གསུམ`) restate a division before enumerating —
  take the ordinal from the preceding context.
- **Tail leaves** near the end (conclusions, `2C/2D`) may use `<ord>་<heading>`
  restatement rather than `<ord>་ནི`; watch for these so you don't miss them.

Delivered example: `rdo-rje bzlas-pa'i rim-pa'i zin-bris`, 32 divisions / 82
elements, monotonic 001B→084A. One OCR fix: `གཉིས་པ་ཉིས།` → `གཉིས་པ་ལ་གཉིས།`
(a dropped `ལ་` before the count) — note such fixes in `_REVIEW-NOTES.txt`. Six
nodes were `†`-flagged (closing subsections with no explicit marker; deep
completion-stage nesting auto-derived and needing a reference spot-check).

---

## Regime C — no formal sa-bcad (synthesized outline)

A practice manual / sādhana with no nested `ལ་N །` and no `དང་པོ་ནི` ordinals. It
self-structures **sequentially**, typically via ritual-stage markers like
`དེ་ནས་ X་ བྱ་བ་ནི།` ("then, as for doing X…"). There is nothing to extract
mechanically — the outline is **interpretive**.

- **Ask the user how many levels** they want. The Phabongkha vajra-recitation
  *tshe-sgrub* used **2 levels**: 3 top parts (purpose/method; the actual
  practice; concluding verses + colophon), and under the practice the ten ritual
  stages (sbyor-ba/lus-gnad, skyabs-'gro sems-bskyed, bdag-bskyed, mchod-pa,
  bstod-pa, rdo-rje bzlas-pa lus-rtsa'i gnad, rdor-bzlas dngos, nyer-bsdu,
  smon-shis, bkra-shis).
- Headings are **your paraphrase of the text's own wording** — keep them faithful.
- **Remove nothing.** Since there are no heading-lists to relocate, the prose
  stays verbatim; you only add marker/bracket lines.
- Codes still follow the odd-digit/even-letter scheme, so a 2-level outline reads
  `1₁ 2₁ 3₁` at the top and `2₁A₂ … 2₁J₂` for the stages.

Delivered example: Phabongkha *tshe-sgrub*, 13 nodes, folios 001B→006A, no nodes
flagged (the sequential structure was unambiguous).

---

## Cross-cutting reminders

- Explained-folio monotonicity is your friend: a backwards jump means a
  misplacement.
- Best-effort + explicit `†` flags beats false confidence. List every inferred
  node and every OCR fix in `_REVIEW-NOTES.txt`.
- The introducer can be **deferred**: `[ordinal]་ནི། … འདི་ལ / དེ་ལ་ [N]` — put the
  bracket at the `ནི`, leave the intervening prose, and mark the children at the
  later `འདི་ལ/དེ་ལ` enumeration. This user-approved layout keeps the reading flow
  intact.
