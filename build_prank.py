#!/usr/bin/env python3
"""
TH Sarabun Prank — Homoglyph attack on a TrueType font.

Copies the outlines of the Thai letter "ค" (U+0E04) into the glyph slots of
"ก" (U+0E01), "ข" (U+0E02), "ง" (U+0E07) and "ส" (U+0E2A), then renames the
whole family to "TH Sarabun Prank".

The original font is never modified: we read src/THSarabunNew-original.ttf and
write a brand-new THSarabunPrank.ttf.

Usage:  python build_prank.py
"""

from copy import deepcopy

from fontTools.ttLib import TTFont

import argparse

SRC = "src/THSarabunNew-original.ttf"
DST = "THSarabunPrank.ttf"

FAMILY = "TH Sarabun Prank"
PS_NAME = "THSarabunPrank"

# character -> glyph name, and the donor glyph whose shape we copy
VICTIMS = {
    "ก": "uni0E01",
    "ข": "uni0E02",
    "ง": "uni0E07",
    "ส": "uni0E2A",
}
DONOR = "uni0E04"  # ค


def main() -> None:
    global SRC, DST
    ap = argparse.ArgumentParser(description="Build the TH Sarabun Prank font.")
    ap.add_argument("--src", default=SRC, help="original TH Sarabun New .ttf")
    ap.add_argument("--dst", default=DST, help="output .ttf")
    args = ap.parse_args()
    SRC, DST = args.src, args.dst

    font = TTFont(SRC)
    glyf = font["glyf"]
    hmtx = font["hmtx"]

    donor_glyph = deepcopy(glyf[DONOR])
    donor_metrics = hmtx[DONOR]

    for char, glyph_name in VICTIMS.items():
        if glyph_name not in glyf:
            raise SystemExit(f"glyph {glyph_name} ({char}) not found in {SRC}")
        # Replace the outline itself ...
        glyf[glyph_name] = deepcopy(donor_glyph)
        # ... and its advance width / left side bearing, so spacing matches ค.
        hmtx[glyph_name] = donor_metrics

    # ---- rename every name-table record so Windows sees a new family ----
    name = font["name"]
    seen = {(r.nameID, r.platformID, r.platEncID, r.langID) for r in name.names}
    for name_id, value in {
        1: FAMILY,          # family
        2: "Regular",       # subfamily
        3: f"{PS_NAME}: Prank Edition 2026",  # unique id
        4: FAMILY,          # full name
        6: PS_NAME,         # PostScript name
        16: FAMILY,         # typographic family
        17: "Regular",      # typographic subfamily
    }.items():
        for _, platform_id, plat_enc_id, lang_id in sorted(seen):
            if platform_id == 1 and lang_id != 0:
                continue
            try:
                name.setName(value, name_id, platform_id, plat_enc_id, lang_id)
            except Exception:
                pass

    # A fresh revision number keeps Windows from reusing a cached face.
    font["head"].fontRevision = 2.0

    # hdmx stores per-size pixel widths keyed by glyph id; they are stale after
    # the edit and modern renderers ignore the table anyway.
    if "hdmx" in font:
        del font["hdmx"]

    try:
        font["maxp"].recalc(font)
    except Exception:
        pass

    font.save(DST)
    print(f"wrote {DST}")
    print(f"  family   : {FAMILY}")
    print(f"  replaced : {', '.join(f'{c} ({g})' for c, g in VICTIMS.items())} -> {DONOR} outline")


if __name__ == "__main__":
    main()
