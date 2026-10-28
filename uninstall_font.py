#!/usr/bin/env python3
"""Remove a per-user font installed by install_font.py — pure Python.

Usage:
    python uninstall_font.py                    # removes TH Sarabun Prank
    python uninstall_font.py --remove-original  # also removes TH Sarabun New
    python uninstall_font.py --font other.ttf
"""

from __future__ import annotations

import argparse
import time
import winreg
from pathlib import Path

import install_font as core


def registry_entries_for(dest: Path) -> list[str]:
    """Registry value names whose data points at this font file."""
    matches: list[str] = []
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, core.REG_PATH, 0, winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return matches

    with key:
        index = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, index)
            except OSError:
                break
            index += 1
            if Path(str(value)).name.lower() == dest.name.lower():
                matches.append(name)

        for name in matches:
            try:
                winreg.DeleteValue(key, name)
            except OSError:
                pass
    return matches


def remove(font_file: Path, family_hint: str | None = None) -> int:
    family, postscript = core.font_names(font_file) if font_file.is_file() else (family_hint or font_file.stem, font_file.stem)
    dest = core.font_dir() / f"{postscript}.ttf"

    removed_values = registry_entries_for(dest)

    if dest.exists():
        core.gdi32.RemoveFontResourceW(str(dest))
        time.sleep(0.3)
        for _ in range(6):
            try:
                dest.unlink()
                break
            except PermissionError:
                time.sleep(0.7)
        else:
            print(f"could not delete {dest} — close any app using the font and retry")
            return 1

    core.broadcast_font_change()

    still_there = family in core.installed_families()
    print(f"removed   : {family}")
    print(f"file      : {dest} (exists: {dest.exists()})")
    print(f"registry  : {removed_values or 'no matching values'}")
    print(f"GDI still lists '{family}': {still_there}")
    return 0 if not still_there else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--font", default="THSarabunPrank.ttf", help=".ttf that was installed")
    ap.add_argument("--remove-original", action="store_true",
                    help="also remove the untouched TH Sarabun New copy")
    args = ap.parse_args()

    status = remove(Path(args.font))
    if args.remove_original:
        status |= remove(Path("src/THSarabunNew-original.ttf"), family_hint="TH Sarabun New")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
