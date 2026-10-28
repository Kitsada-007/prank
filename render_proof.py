#!/usr/bin/env python3
"""Render the installed fonts through Windows GDI (ctypes) and compare glyphs.

Produces proof_windows_gdi.png and prints a pixel-level diff:
the prank font's ก/ข/ง/ส should be byte-identical to the original font's ค.

Usage: python render_proof.py
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

import numpy as np
from PIL import Image

gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

BI_RGB = 0
DIB_RGB_COLORS = 0
TRANSPARENT = 1
DEFAULT_CHARSET = 1
ANTIALIASED_QUALITY = 4
FW_NORMAL = 400
DEFAULT_PITCH = 0
FF_DONTCARE = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateDIBSection.argtypes = [
    wintypes.HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD,
]
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.CreateFontW.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
    wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.LPCWSTR,
]
gdi32.CreateFontW.restype = wintypes.HFONT
gdi32.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
gdi32.TextOutW.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.LPCWSTR, ctypes.c_int]
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]


def make_font(face: str, height: int) -> int:
    return gdi32.CreateFontW(
        -height, 0, 0, 0, FW_NORMAL, 0, 0, 0,
        DEFAULT_CHARSET, 0, 0, ANTIALIASED_QUALITY,
        DEFAULT_PITCH | FF_DONTCARE, face,
    )


def render(canvas, x: int, y: int, text: str, face: str, height: int, color=0x000000) -> None:
    hdc, bits, width, _height = canvas
    font = make_font(face, height)
    old = gdi32.SelectObject(hdc, font)
    gdi32.SetTextColor(hdc, color)
    gdi32.SetBkMode(hdc, TRANSPARENT)
    gdi32.TextOutW(hdc, x, y, text, len(text))
    gdi32.SelectObject(hdc, old)
    gdi32.DeleteObject(font)


def new_canvas(width: int, height: int):
    hdc = gdi32.CreateCompatibleDC(None)
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height  # top-down rows
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB

    bits = ctypes.c_void_p()
    hbmp = gdi32.CreateDIBSection(hdc, ctypes.byref(bmi), DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
    if not hbmp:
        raise ctypes.WinError(ctypes.get_last_error())

    gdi32.SelectObject(hdc, hbmp)
    buffer = (ctypes.c_ubyte * (width * height * 4)).from_address(bits.value)
    ctypes.memset(bits, 0xFF, width * height * 4)  # white BGRA
    return (hdc, bits, width, height), buffer, hbmp


def to_image(buffer, width: int, height: int) -> Image.Image:
    arr = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)
    return Image.fromarray(arr[:, :, 2::-1].copy())  # BGRA -> RGB


def main() -> None:
    import install_font

    families = install_font.installed_families()
    missing = [f for f in ("TH Sarabun Prank", "TH Sarabun New") if f not in families]
    if missing:
        raise SystemExit(f"not installed: {', '.join(missing)} — run `python install_font.py` first")

    width, height = 1000, 420
    canvas, buffer, hbmp = new_canvas(width, height)
    hdc = canvas[0]

    grey = 0x5A5A5A
    red = 0x2000B0  # COLORREF is 0x00BBGGRR
    black = 0x141414

    render(canvas, 30, 24, "1) Original  TH Sarabun New", "Arial", 24, grey)
    render(canvas, 30, 56, "ก ข ค ง ส", "TH Sarabun New", 72, black)
    render(canvas, 30, 190, "2) Prank  TH Sarabun Prank  (ก ข ง ส ถูกสวมด้วย ค)", "Arial", 24, red)
    render(canvas, 30, 222, "ก ข ค ง ส", "TH Sarabun Prank", 72, red)
    render(canvas, 30, 360, "Both lines were typed with the same characters.", "Arial", 24, grey)

    to_image(buffer, width, height).save("proof_windows_gdi.png")
    print("wrote proof_windows_gdi.png")

    # ---- pixel-exact comparison through GDI ----
    def glyph(face: str, char: str) -> np.ndarray:
        c, buf, bmp = new_canvas(260, 220)
        render(c, 20, 20, char, face, 130)
        img = np.array(to_image(buf, 260, 220).convert("L"), dtype=int)
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(c[0])
        return img

    pairs = [
        ("prank ก", glyph("TH Sarabun Prank", "ก"), "original ค", glyph("TH Sarabun New", "ค")),
        ("prank ข", glyph("TH Sarabun Prank", "ข"), "original ค", glyph("TH Sarabun New", "ค")),
        ("prank ง", glyph("TH Sarabun Prank", "ง"), "original ค", glyph("TH Sarabun New", "ค")),
        ("prank ส", glyph("TH Sarabun Prank", "ส"), "original ค", glyph("TH Sarabun New", "ค")),
        ("original ก", glyph("TH Sarabun New", "ก"), "original ค", glyph("TH Sarabun New", "ค")),
    ]
    for label_a, a, label_b, b in pairs:
        print(f"{label_a:>12} vs {label_b:<12}: differing pixels = {int((a != b).sum())}")

    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc)


if __name__ == "__main__":
    main()
