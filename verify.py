#!/usr/bin/env python3
"""Verify THSarabunPrank.ttf and render a before/after proof image."""

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
import numpy as np

SRC = "src/THSarabunNew-original.ttf"
DST = "THSarabunPrank.ttf"
VICTIMS = ["uni0E01", "uni0E02", "uni0E07", "uni0E2A"]
DONOR = "uni0E04"


def outline(ft, g):
    glyph = ft["glyf"][g]
    glyph.expand(ft["glyf"])
    return (
        glyph.numberOfContours,
        tuple(glyph.coordinates) if glyph.numberOfContours else (),
        tuple(glyph.endPtsOfContours) if glyph.numberOfContours else (),
        tuple(glyph.flags) if glyph.numberOfContours else (),
    )


def main():
    src = TTFont(SRC)
    dst = TTFont(DST)

    print("== names ==")
    for nid in (1, 2, 4, 6):
        print(f"  id {nid}: {dst['name'].getDebugName(nid)!r}")

    print("== cmap unchanged? ==")
    s_cmap, d_cmap = src.getBestCmap(), dst.getBestCmap()
    for ch in "กขคงส":
        print(f"  {ch} U+{ord(ch):04X}: src->{s_cmap[ord(ch)]}  prank->{d_cmap[ord(ch)]}")

    print("== outline replacement ==")
    donor = outline(dst, DONOR)
    ok = True
    for g in VICTIMS:
        same = outline(dst, g) == donor
        ok &= same
        print(f"  {g}: identical to {DONOR}? {same}  advance={dst['hmtx'][g]}")
    print("  ALL OK" if ok else "  MISMATCH")

    # ---- pixel comparison: prank glyphs must look exactly like ค ----
    def ink(path, text):
        font = ImageFont.truetype(path, 96)
        img = Image.new("L", (300, 220), 255)
        ImageDraw.Draw(img).text((20, 20), text, font=font, fill=0)
        return np.array(img) < 128

    print("== rendered ink difference (FreeType) ==")
    checks = [
        ("prank ก", ink(DST, "ก"), "original ก", ink(SRC, "ก")),
        ("prank ก", ink(DST, "ก"), "original ค", ink(SRC, "ค")),
        ("prank ข", ink(DST, "ข"), "original ค", ink(SRC, "ค")),
        ("prank ง", ink(DST, "ง"), "original ค", ink(SRC, "ค")),
        ("prank ส", ink(DST, "ส"), "original ค", ink(SRC, "ค")),
    ]
    for label_a, a, label_b, b in checks:
        print(f"  {label_a:>8} vs {label_b:<11}: differing pixels = {int((a != b).sum())}")

    # ---- proof image ----
    sample = "ก ข ค ง ส"
    sentence = "ทดสอบ กขงส กับฟอนต์แปลก"
    W, H = 1100, 420
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype("arial.ttf", 26)
    f_big = ImageFont.truetype(DST, 84)
    f_orig = ImageFont.truetype(SRC, 84)
    f_small = ImageFont.truetype(DST, 44)

    d.text((40, 20), "Original  TH Sarabun New", font=f_title, fill="black")
    d.text((40, 55), sample, font=f_orig, fill="#1a1a1a")
    d.text((40, 175), "Prank  TH Sarabun Prank  (ก ข ง ส  ->  ค)", font=f_title, fill="#b00020")
    d.text((40, 210), sample, font=f_big, fill="#b00020")
    d.text((40, 330), sentence, font=f_small, fill="#333333")
    img.save("proof_before_after.png")
    print("wrote proof_before_after.png")


if __name__ == "__main__":
    main()
