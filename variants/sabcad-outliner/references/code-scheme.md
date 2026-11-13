# Outline code scheme and the subscript peel

Every outline element has a **code** that encodes its full path from the root of
the sa-bcad. The code is read one nesting **level** at a time, left to right.

At level **L**:

- if **L is odd**, the ordinal is a single **digit** `1–8` (1st, 2nd, … sibling);
- if **L is even**, the ordinal is a single **letter** `A–H`;
- the ordinal is immediately followed by the **level number** `str(L)`, and that
  level number is rendered as a **subscript**.

So a code alternates *(ordinal, normal) (level-number, subscript)* pairs.

## Examples

| Raw code | Peeled (⌄ = subscript) | Displayed |
|---|---|---|
| `11` | `1` `1⌄` | 1₁ |
| `21A2` | `2` `1⌄` `A` `2⌄` | 2₁A₂ |
| `21A213` | `2` `1⌄` `A` `2⌄` `1` `3⌄` | 2₁A₂1₃ |
| `11B213` | `1` `1⌄` `B` `2⌄` `1` `3⌄` | 1₁B₂1₃ |
| `61B233B425C637D819B10311F12` | 6 1⌄ B 2⌄ 3 3⌄ B 4⌄ 2 5⌄ C 6⌄ 3 7⌄ D 8⌄ 1 9⌄ B 10⌄ 3 11⌄ F 12⌄ | 6₁B₂3₃B₄2₅C₆3₇D₈1₉B₁₀3₁₁F₁₂ |

Note the last row: at level 10 the subscript is the **two-digit** string `10`, and
`B10` means "letter B at level 10", not "B, 1, 0". The peel handles this because
it always consumes exactly `len(str(L))` digits for the level number.

## Why we peel literally (and never recompute)

It is tempting to recompute a node's ordinal from its position among siblings.
**Don't.** In deep sub-trees — especially where the source outline has gaps
(`†` nodes with missing intermediate headings) — the ordinal letters/digits in the
authoritative codes legitimately diverge from naive sibling position. The codes
carried in the user's outline files are ground truth. `render_outline.py` peels
the code string exactly as written; you should build codes by string-prefixing
(child = parent code + this level's ordinal + level number), not by counting.

## The peel algorithm (implemented in `scripts/render_outline.py`)

```
level = 1; i = 0
while i < len(code):
    ordinal = code[i]                 # 1 char, normal run
    emit(ordinal, subscript=False)
    i += 1
    lvl = str(level)                  # e.g. "1", "10"
    digits = code[i : i+len(lvl)]     # must equal lvl
    emit(digits, subscript=True)
    i += len(lvl)
    level += 1
```

If the string ever fails to match (unexpected character, or the level-number
digits aren't where they should be), the engine emits the remainder as one normal
run rather than crashing — so malformed codes degrade gracefully and are visible
in the output for correction.

## Even/odd and the level count

Because odd levels use digits and even levels use letters, you can read a code's
depth directly, and you can tell a well-formed code from noise. A `†`-flagged node
is still given a proper code (its path is known); the `†` is a review marker you
keep out of the rendered document and record in `_REVIEW-NOTES.txt`.
