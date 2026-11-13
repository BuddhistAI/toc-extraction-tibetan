#!/usr/bin/env python3
"""
annotate_enumeration.py — weave outline codes INLINE into retained enumerations.

Run this on the woven text file AFTER weaving and BEFORE render_outline.py.

THE PRINCIPLE
  The original text must be retained verbatim. The ONLY things the outliner adds
  are outline codes and formatting — it never paraphrases a heading or deletes
  source words. So when a division lists its children's headings inline
  (the direct-enumeration style  …ལ་N །  h1 །  h2 …  hN །), the outline code is
  inserted INLINE, immediately before each heading in the original list, and a
  line break is added after the "…ལ་N །" count clause:

      ༈ འདི་ལ་གསུམ།  གང་གིས་…རྟེན །  གང་ཞིག་…ཆོས །  །ཇི་ལྟར་…ཚུལ་ལོ །
  becomes
      ༈ འདི་ལ་གསུམ།
      11) གང་གིས་…རྟེན །  21) གང་ཞིག་…ཆོས །  །31) ཇི་ལྟར་…ཚུལ་ལོ །

  Note ཚུལ་ལོ། stays ཚུལ་ལོ། (verbatim) and the separator ། between headings is
  kept. This REPLACES the older approach of emitting separate `CODE) heading`
  marker lines with reconstructed headings — those duplicated and sometimes
  abbreviated the text.

INPUT SHAPE
  A woven file where each direct-enumeration announcement is followed (after blank
  lines) by its children's `CODE) heading` marker lines (that is what supplies the
  codes and their order). This tool folds those codes back into the announcement's
  own list and drops the separate marker lines.

WHAT IT LEAVES ALONE
  * Verse/citation enumerations (`… ནི། [source] གྱིས། …verse…`) — a root-text
    verse cannot be annotated in place, so its `CODE) heading` marker lines are
    KEPT as separate lines.
  * Deferred style (`…ལ་N་ལས། དང་པོ་…ནི།`) where the announcement runs straight
    into child 1's prose — no plain list to annotate; marker lines are kept.
  Both are detected and skipped automatically.

USAGE
  python3 annotate_enumeration.py WOVEN.txt WOVEN.annotated.txt
  (then run render_outline.py on the annotated file)

To apply this to an EXISTING .docx as tracked changes instead, insert the codes
and line break as <w:ins> and delete the separate marker-line paragraphs as
<w:del> (keep the original enumeration runs untouched). See the docx skill.
"""
import argparse
import re

MARK = re.compile(r"^([0-9A-Z]+)\)\s*(.*)$")
BRACK = re.compile(r"^\[[0-9A-Z]+\)")
NUM = r"(?:གཅིག|གཉིས|གསུམ|བཞི|ལྔ|དྲུག|བདུན|བརྒྱད|དགུ|བཅུ)"
COUNT = re.compile(r"ལ་" + NUM + r"།")            # bare "…ལ་N །" only
NI = re.compile(r"ནི[།་]")
ORD = re.compile(r"^\s*།?\s*(?:དང་པོ|གཉིས་པ|གསུམ་པ|བཞི་པ|ལྔ་པ|དྲུག་པ|བདུན་པ|བརྒྱད་པ|དགུ་པ|བཅུ)")
FOLIO = re.compile(r"\[\d{1,3}[AB]?\]")


def is_blank(t): return not t.strip()
def is_marker(t): return bool(MARK.match(t.strip()))
def is_bracket(t): return bool(BRACK.match(t.strip()))


def hprefix(h):
    h = re.sub(FOLIO, "", h)
    h = re.sub(r"[།་༎༏༐༑\s]+$", "", h)
    return h[:10]


def annotate(lines):
    out = list(lines)
    drop = set()      # indices of marker lines to remove
    n = len(lines)
    i = 0
    changed = 0
    while i < n:
        if is_marker(lines[i]):
            j = i
            codes, heads, mp = [], [], []
            while j < n:
                if is_marker(lines[j]):
                    m = MARK.match(lines[j].strip())
                    codes.append(m.group(1)); heads.append(m.group(2).strip()); mp.append(j); j += 1
                elif is_blank(lines[j]):
                    j += 1
                else:
                    break
            k = i - 1
            while k >= 0 and (is_blank(lines[k]) or is_marker(lines[k]) or is_bracket(lines[k])):
                k -= 1
            if k >= 0 and heads:
                t = lines[k]
                pref0 = hprefix(heads[0])
                cm = None
                for m in reversed(list(COUNT.finditer(t))):
                    span = t[m.end():]
                    if pref0 and pref0 in span and not NI.search(span) and not ORD.match(span):
                        cm = m; break
                if cm is not None:
                    positions, cur, ok = [], cm.end(), True
                    for h in heads:
                        idx = t.find(hprefix(h), cur)
                        if idx < 0:
                            ok = False; break
                        positions.append(idx); cur = idx + 1
                    if ok:
                        # build: count-clause line + inline-coded list line
                        pieces = []
                        prev = cm.end()
                        for pos, code in zip(positions, codes):
                            pieces.append(t[prev:pos])
                            pieces.append(code + ") ")
                            prev = pos
                        pieces.append(t[prev:])
                        list_line = "".join(pieces).lstrip()
                        out[k] = t[:cm.end()] + "\n" + list_line
                        drop.update(mp)
                        changed += 1
            i = j
        else:
            i += 1
    return [ln for idx, ln in enumerate(out) if idx not in drop], changed


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        lines = f.read().split("\n")
    out, changed = annotate(lines)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"annotated {changed} direct-enumeration divisions inline -> {args.output}")


if __name__ == "__main__":
    main()
