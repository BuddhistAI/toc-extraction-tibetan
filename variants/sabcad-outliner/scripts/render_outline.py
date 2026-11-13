#!/usr/bin/env python3
"""
render_outline.py — render an interlinear Tibetan sa-bcad outline to .docx.

INPUT: a plain-text (UTF-8) "reflowed" file in which the outline has ALREADY been
woven into the running Tibetan.  Each line becomes one paragraph, and blank lines
become empty paragraphs (this is how the original chunking / verse layout is
preserved).  Three kinds of line get special treatment:

  1. Marker line       CODE) heading
        e.g.  21A2) yan-lag-can gyi gdams-pa dngos.
     The leading CODE is peeled into ordinal (normal) + level-number (subscript)
     runs; the rest of the line is one plain run.

  2. Bracket line      [CODE) heading [FOLIO]]
        e.g.  [21A2) yan-lag-can gyi gdams-pa dngos. [001B]]
     Same code-peeling on the leading CODE; the trailing [FOLIO] and any inline
     [NNNx] inside the heading stay plain.

  3. Body line         anything else, including inline [NNNx] folio tags
     Emitted as a single plain run (folio tags are NOT peeled — only leading
     outline codes are).

STYLING:
  A named PARAGRAPH style "Tibetan" is created (based on Normal) set to the given
  font at the given size, with the font applied to the ascii/hAnsi/complex-script
  (cs)/eastAsia slots so Tibetan Unicode renders in it reliably.  EVERY paragraph
  is assigned this style, so all Tibetan text lives in one editable style the user
  can restyle globally.  Each run ALSO gets the font set explicitly (belt and
  suspenders) and the level-number digits get run.font.subscript = True — because
  subscript is a character property, it cannot live in a paragraph style, so it is
  always applied at the run level here.

CODE SCHEME (see references/code-scheme.md):
  A code is read left-to-right, one nesting level at a time.  At level L:
    * odd  L  -> ordinal is a single DIGIT  (1-9)
    * even L  -> ordinal is a single LETTER (A-Z)
  followed by the level number str(L) rendered as SUBSCRIPT (may be >1 digit at
  level >=10).  So `21A213` peels to 2 1(sub) A 2(sub) 1 3(sub)  = 2 A 1 at
  levels 1,2,3 -> displayed 2₁A₂1₃.  The peel is fully deterministic; we never
  recompute ordinals from tree position (deep codes legitimately diverge).

USAGE:
  python3 render_outline.py INPUT.txt OUTPUT.docx [--font "Microsoft Himalaya"] [--size 20]
"""
import argparse
import re

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.shared import Pt

STYLE_NAME = "Tibetan"
FONT_SLOTS = ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia")

# Outline codes may appear anywhere in a line, not just at its start:
#   * a standalone marker line          11) heading
#   * a bracket recall line             [11) heading [119]]
#   * codes woven INLINE into a          … ལ་གསུམ།  11) h1 །  21) h2 །  31) h3
#     retained enumeration
# A code is a run of digits/letters immediately followed by ")".  It is never
# preceded by another alphanumeric (so we grab the whole run), and Tibetan text
# never itself contains "…)" — so matching "[0-9A-Z]+)" anywhere is safe.
INLINE_CODE = re.compile(r"(?<![0-9A-Za-z])([0-9A-Z]+)\)")


def _apply_font_slots(rfonts, font):
    for slot in FONT_SLOTS:
        rfonts.set(qn(slot), font)


def ensure_tibetan_style(doc, font, size):
    """Create (or update) a paragraph style named 'Tibetan' set to font/size.

    The font is written to every rFonts slot (ascii/hAnsi/cs/eastAsia) so that
    Tibetan Unicode — which Word may route through the complex-script slot — is
    guaranteed to render in the chosen face.  Returns the style object.
    """
    styles = doc.styles
    existing = {s.name: s for s in styles}
    if STYLE_NAME in existing:
        style = existing[STYLE_NAME]
    else:
        style = styles.add_style(STYLE_NAME, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles["Normal"]
    style.font.name = font
    style.font.size = Pt(size)
    rpr = style.element.get_or_add_rPr()
    _apply_font_slots(rpr.get_or_add_rFonts(), font)
    # keep paragraph spacing tight so the outline reads as running text
    return style


def peel_code(code):
    """Yield (text, is_subscript) tuples for a raw code string.

    Deterministic left-to-right peel: at level L read 1 ordinal char, then
    len(str(L)) subscript digits.  If the string does not conform (bad char,
    runs out mid-level), the remainder is emitted as a single normal run so we
    never lose characters or crash on unexpected input.
    """
    out = []
    i = 0
    level = 1
    n = len(code)
    while i < n:
        ordc = code[i]
        expect_letter = (level % 2 == 0)
        ok = ordc.isalpha() if expect_letter else ordc.isdigit()
        if not ok:
            out.append((code[i:], False))
            return out
        out.append((ordc, False))
        i += 1
        lvl_str = str(level)
        d = len(lvl_str)
        if code[i:i + d] != lvl_str:
            out.append((code[i:], False))
            return out
        out.append((lvl_str, True))
        i += d
        level += 1
    return out


def add_runs(paragraph, segments, font, size):
    for text, sub in segments:
        if text == "":
            continue
        r = paragraph.add_run(text)
        r.font.name = font
        r.font.size = Pt(size)
        _apply_font_slots(r._element.get_or_add_rPr().get_or_add_rFonts(), font)
        if sub:
            r.font.subscript = True
    return paragraph


def build_segments(line):
    """Return a list of (text, is_subscript) segments for one input line.

    Every ``CODE)`` occurrence anywhere in the line is peeled into normal-ordinal
    + subscript-level-digit runs; everything else (including inline ``[NNNx]``
    folio tags and the retained enumeration text) stays plain.
    """
    segs = []
    pos = 0
    for m in INLINE_CODE.finditer(line):
        if m.start() > pos:
            segs.append((line[pos:m.start()], False))
        segs.extend(peel_code(m.group(1)))
        segs.append((")", False))
        pos = m.end()
    if pos < len(line):
        segs.append((line[pos:], False))
    return segs or [(line, False)]


def render(input_path, output_path, font="Microsoft Himalaya", size=20):
    with open(input_path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    doc = Document()
    ensure_tibetan_style(doc, font, size)
    n_sub = 0
    for line in lines:
        p = doc.add_paragraph()
        p.style = doc.styles[STYLE_NAME]  # all Tibetan text in the Tibetan style
        if line.strip() == "":
            continue
        segs = build_segments(line)
        n_sub += sum(1 for _, s in segs if s)
        add_runs(p, segs, font, size)
    doc.save(output_path)
    return len(lines), n_sub


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--font", default="Microsoft Himalaya")
    ap.add_argument("--size", type=float, default=20)
    args = ap.parse_args()
    n, n_sub = render(args.input, args.output, args.font, args.size)
    print(f"Rendered {n} paragraphs -> {args.output}")
    print(f"  style '{STYLE_NAME}' = {args.font} {args.size}pt applied to all paragraphs")
    print(f"  {n_sub} subscript level-digit runs emitted")


if __name__ == "__main__":
    main()
