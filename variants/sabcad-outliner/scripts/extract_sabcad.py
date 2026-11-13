#!/usr/bin/env python3
"""
extract_sabcad.py — survey a Tibetan text's embedded sa-bcad skeleton.

This is a SCAFFOLDING aid, not an oracle.  It scans the running Tibetan and
reports the structural signals that the sa-bcad is built from, so Claude can
assemble (and VERIFY) the outline tree by hand.  It never writes the final
document — that is render_outline.py's job — and its output should always be
spot-checked, because Tibetan enumerations contain inline prose that mimics
structural markers (see the overrun note below).

It reports, with character offsets and nearby folio:

  * ANNOUNCEMENTS:  "... ལ་N །  h1 །  h2 །  ... hN (ནོ)། །"
      A division declaring N sub-topics followed by their heading list.  These
      are the most reliable structural anchors: they give both a child count
      and the heading strings.  N is parsed from a Tibetan number word or digit.

  * ORDINAL MARKERS:  "དང་པོ", "གཉིས་པ", "གསུམ་པ" ... and digit forms.
      "<ord>་ལ..."  tends to introduce a NON-LEAF (it will itself announce a
      count).  "<ord>་ནི..." tends to introduce a LEAF (elaboration follows).
      A topical recap "<noun>་ལ་N" restates a division before enumerating it.

  * FOLIOS:  inline [NNNx] tags, used as monotonic position anchors.

Assembling the tree (do this yourself, using the report):
  Walk announcements in order; push a division and expect its N children.  Match
  children by their heading cores.  Close (pop) a division when its N slots are
  filled by leaf "<ord>་ནི" markers.  OVERRUN CHECK: ordinals appearing beyond
  the declared count N are inline prose enumeration (e.g. a citation listing
  "first... second... third"), NOT structure — do not open nodes for them.
  Derive each node's ordinal from its own "<ord>་ལ/ནི" prefix, never from
  sibling position.  Flag with † any node you had to infer without an explicit
  marker, and list it for the user.

USAGE:
  python3 extract_sabcad.py INPUT.txt            # human-readable report
  python3 extract_sabcad.py INPUT.txt --json     # machine-readable
"""
import argparse
import json
import re
import sys

# Tibetan cardinal number words -> int (enough for sa-bcad child counts).
NUM_WORDS = {
    "གཅིག": 1, "གཉིས": 2, "གསུམ": 3, "བཞི": 4, "ལྔ": 5,
    "དྲུག": 6, "བདུན": 7, "བརྒྱད": 8, "དགུ": 9, "བཅུ": 10,
    "བཅུ་གཅིག": 11, "བཅུ་གཉིས": 12, "བཅུ་གསུམ": 13, "བཅུ་བཞི": 14,
}
# Tibetan digits 0-9
TIB_DIGITS = "༠༡༢༣༤༥༦༧༨༩"
DIG_MAP = {c: str(i) for i, c in enumerate(TIB_DIGITS)}

# Ordinal words དང་པོ (1st) .. and the regular "<stem>་པ/པོ" pattern (2nd+).
ORDINALS = {
    "དང་པོ": 1, "གཉིས་པ": 2, "གསུམ་པ": 3, "བཞི་པ": 4, "ལྔ་པ": 5,
    "དྲུག་པ": 6, "བདུན་པ": 7, "བརྒྱད་པ": 8, "དགུ་པ": 9, "བཅུ་པ": 10,
}

FOLIO_RE = re.compile(r"\[(\d{1,3}[AB])\]")
# "...ལ་<number>།" — a division announcing its child count.
COUNT_RE = re.compile(r"ལ་(" + "|".join(sorted(NUM_WORDS, key=len, reverse=True))
                      + r"|[" + TIB_DIGITS + r"]+)[།\s]")
ORD_RE = re.compile(r"(" + "|".join(sorted(ORDINALS, key=len, reverse=True)) + r")་(ལ|ནི)")


def tib_number(tok):
    if tok in NUM_WORDS:
        return NUM_WORDS[tok]
    if all(c in DIG_MAP for c in tok):
        return int("".join(DIG_MAP[c] for c in tok))
    return None


def nearest_folio(text, pos, folios):
    """Return the folio tag at or before position `pos`."""
    last = None
    for m in folios:
        if m.start() <= pos:
            last = m.group(1)
        else:
            break
    return last


def survey(text):
    folios = list(FOLIO_RE.finditer(text))
    announcements = []
    for m in COUNT_RE.finditer(text):
        n = tib_number(m.group(1))
        if n is None:
            continue
        announcements.append({
            "pos": m.start(),
            "count": n,
            "folio": nearest_folio(text, m.start(), folios),
            "context": text[max(0, m.start() - 30):m.start() + 60].replace("\n", " "),
        })
    ordinals = []
    for m in ORD_RE.finditer(text):
        ordinals.append({
            "pos": m.start(),
            "ordinal": ORDINALS[m.group(1)],
            "kind": "non-leaf(ལ)" if m.group(2) == "ལ" else "leaf(ནི)",
            "folio": nearest_folio(text, m.start(), folios),
            "context": text[m.start():m.start() + 50].replace("\n", " "),
        })
    return {
        "n_folios": len(folios),
        "folio_first": folios[0].group(1) if folios else None,
        "folio_last": folios[-1].group(1) if folios else None,
        "announcements": announcements,
        "ordinals": ordinals,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        text = f.read()
    rep = survey(text)
    if args.json:
        json.dump(rep, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return
    print(f"Folios: {rep['n_folios']}  ({rep['folio_first']} -> {rep['folio_last']})")
    print(f"\nANNOUNCEMENTS (ལ་N །) — {len(rep['announcements'])}:")
    for a in rep["announcements"]:
        print(f"  @{a['pos']:>7}  [{a['folio']}]  ལ་{a['count']}   …{a['context']}…")
    print(f"\nORDINAL MARKERS — {len(rep['ordinals'])}:")
    for o in rep["ordinals"]:
        print(f"  @{o['pos']:>7}  [{o['folio']}]  #{o['ordinal']} {o['kind']:12} {o['context']}")
    print("\nReminder: verify against the running text; overrun ordinals beyond a "
          "division's declared count are inline prose, not structure.")


if __name__ == "__main__":
    main()
