# Output format specification

The deliverable is a `.docx`. Every paragraph is assigned a named paragraph style
**"Tibetan"** (based on Normal) set to **Microsoft Himalaya, 20 pt** — the font is
written to the ascii/hAnsi/complex-script/eastAsia slots so Tibetan Unicode always
renders in it. Each run also carries the font explicitly, and the code level-digit
runs carry `subscript = True` (a character property, so it lives on the run, not
the style). Because all text shares one style, the user can change the whole
document's font or size from a single place in Word. The document is the full
running Tibetan with the outline woven in. **The only additions are outline codes
and formatting** (line breaks, subscripts, the Tibetan style) — no heading is ever
paraphrased, abbreviated, or deleted. When a division lists its children's headings
inline (`…ལ་N །  h1 །  h2 …`), the code is inserted **inline before each heading in
that retained list**, with a line break after the `…ལ་N །` count clause; the
headings and their `།` separators stay byte-for-byte (`ཚུལ་ལོ།` stays `ཚུལ་ལོ།`).
Standalone `CODE) heading` marker lines are used only where the enumeration is a
quoted verse or a deferred introducer that cannot be annotated in place. See
`annotate_enumeration.py`.

## Line types

The renderer decides a paragraph's type from how the line begins:

1. **Marker line** — begins with a code then `) `:
   ```
   21A2) རྩོམ་པ་ལ་འཇུག་པའི་ཡན་ལག། 
   ```
   Appears inside the parent division's enumeration, one per child, in order.
   The code is peeled to subscripts; the heading is the text's own heading form.

2. **Bracket recall line** — begins with `[` then a code then `) `, and ends with
   the first-appearance folio in brackets:
   ```
   [21A2) རྩོམ་པ་ལ་འཇུག་པའི་ཡན་ལག། [003B]]
   ```
   Placed immediately before the element's elaboration. The trailing `[003B]` and
   any inline `[NNNx]` inside the heading are plain text (not peeled).

3. **Body line** — the running Tibetan, including inline folio tags at page turns:
   ```
   [003A]དེ་འདྲ་བའི་ཟུང་འཇུག་གི་ཐབས་ཤེས་སྦྱོར་བ་...
   ```

## Folios

- Inline tag form: `[NNNx]` where `NNN` is the folio number zero-padded to 3
  digits and `x` is `A` or `B` (recto/verso). Folio 2B → `[002B]`.
- The bracket recall line's folio is the **first appearance** folio of that
  element (where its heading is first announced), not where it is elaborated.
- Folios must be **monotonic** along the depth-first walk of the outline — a good
  automatic sanity check.

## Chunking / layout

One input line → one paragraph. A blank input line → a blank paragraph. This is
how verse structure and the source's reflowed chunking are preserved. Do not
collapse or rewrap the text; feed the engine text that already has the line breaks
you want in the document.

## Worked micro-example

Input (woven text file):

```
...རྡོ་རྗེ་བཟླས་པའི་རིམ་པའི་མན་ངག་ལ་གསུམ།
11) མཚན་གྱི་དོན། 
21) གཞུང་གི་དོན། 
31) མཇུག་གི་དོན་ནོ། 

[11) མཚན་གྱི་དོན། [001B]]
དང་པོ་ནི། བྫྲ་ཛ་པ་ཀྲ་མ་...
```

Rendered result: three marker lines with `1₁ 2₁ 3₁` (level-1 subscripts), a blank
paragraph, then the bracket recall line `[1₁) མཚན་གྱི་དོན། [001B]]`, then the
elaboration. All runs Microsoft Himalaya 20 pt.
