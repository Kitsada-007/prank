#!/usr/bin/env python3
"""Install a font for the current Windows user — pure Python, no admin.

Copies the .ttf into %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts, registers it in
HKCU, tells running apps to re-enumerate fonts, then verifies that GDI can see
the family.

Usage:
    python install_font.py                      # installs THSarabunPrank.ttf
    python install_font.py --font some.ttf
"""

from __future__ import annotations

import argparse
import ctypes
import os
import shutil
import time
import winreg
from ctypes import wintypes
from pathlib import Path

REG_PATH = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
WM_FONTCHANGE = 0x001D
HWND_BROADCAST = 0xFFFF
DEFAULT_CHARSET = 1

gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)

gdi32.AddFontResourceW.argtypes = [wintypes.LPCWSTR]
gdi32.AddFontResourceW.restype = ctypes.c_int
gdi32.RemoveFontResourceW.argtypes = [wintypes.LPCWSTR]
gdi32.RemoveFontResourceW.restype = wintypes.BOOL
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.restype = wintypes.LPARAM


class LOGFONTW(ctypes.Structure):
    _fields_ = [
        ("lfHeight", wintypes.LONG),
        ("lfWidth", wintypes.LONG),
        ("lfEscapement", wintypes.LONG),
        ("lfOrientation", wintypes.LONG),
        ("lfWeight", wintypes.LONG),
        ("lfItalic", wintypes.BYTE),
        ("lfUnderline", wintypes.BYTE),
        ("lfStrikeOut", wintypes.BYTE),
        ("lfCharSet", wintypes.BYTE),
        ("lfOutPrecision", wintypes.BYTE),
        ("lfClipPrecision", wintypes.BYTE),
        ("lfQuality", wintypes.BYTE),
        ("lfPitchAndFamily", wintypes.BYTE),
        ("lfFaceName", wintypes.WCHAR * 32),
    ]


ENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_int, ctypes.POINTER(LOGFONTW), ctypes.c_void_p, wintypes.DWORD, wintypes.LPARAM
)
gdi32.EnumFontFamiliesExW.argtypes = [
    wintypes.HDC, ctypes.POINTER(LOGFONTW), ENUMPROC, wintypes.LPARAM, wintypes.DWORD
]
gdi32.EnumFontFamiliesExW.restype = ctypes.c_int


def font_dir() -> Path:
    path = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def font_names(path: Path) -> tuple[str, str]:
    """(family, postscript name) read straight from the font's name table."""
    try:
        from fontTools.ttLib import TTFont

        with TTFont(str(path), lazy=True) as font:
            name = font["name"]
            family = name.getDebugName(16) or name.getDebugName(1) or path.stem
            postscript = name.getDebugName(6) or path.stem
        return family, postscript
    except Exception:
        return path.stem, path.stem


def installed_families() -> set[str]:
    families: set[str] = set()

    @ENUMPROC
    def collect(logfont, _text_metric, _font_type, _param):
        families.add(logfont.contents.lfFaceName)
        return 1  # keep enumerating

    hdc = gdi32.CreateCompatibleDC(None)
    try:
        lf = LOGFONTW()
        lf.lfCharSet = DEFAULT_CHARSET
        gdi32.EnumFontFamiliesExW(hdc, ctypes.byref(lf), collect, 0, 0)
    finally:
        gdi32.DeleteDC(hdc)
    return families


def broadcast_font_change() -> None:
    user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)


def install(source: Path) -> int:
    source = source.resolve()
    if not source.is_file():
        print(f"font not found: {source}")
        return 1

    family, postscript = font_names(source)
    dest = font_dir() / f"{postscript}.ttf"

    # A registered font file stays mapped by the font service. Release it
    # before overwriting, otherwise the copy fails with "file in use".
    if dest.exists():
        gdi32.RemoveFontResourceW(str(dest))
        time.sleep(0.4)

    for _ in range(6):
        try:
            shutil.copy2(source, dest)
            break
        except PermissionError:
            gdi32.RemoveFontResourceW(str(dest))
            time.sleep(0.8)
    else:
        print(f"could not replace {dest} — close Word/any app using the font and retry")
        return 1

    value_name = f"{family} (TrueType)"
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, str(dest))

    added = gdi32.AddFontResourceW(str(dest))
    broadcast_font_change()

    visible = family in installed_families()
    print(f"installed : {family}")
    print(f"file      : {dest}")
    print(f"registry  : HKCU\\{REG_PATH}\\{value_name}")
    print(f"AddFontResourceW returned {added}; GDI sees '{family}': {visible}")
    return 0 if visible else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--font", default="THSarabunPrank.ttf", help=".ttf to install")
    return install(Path(ap.parse_args().font))


if __name__ == "__main__":
    raise SystemExit(main())
