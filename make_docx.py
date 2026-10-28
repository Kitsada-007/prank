#!/usr/bin/env python3
"""Build a small .docx that shows the prank next to the untouched font."""

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


def set_font(run, name, size, color=None, bold=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    # Thai text in Word is driven by the complex-script slot, so set them all.
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), name)
    # Complex-script text also takes its size from w:szCs.
    szcs = rpr.find(qn("w:szCs"))
    if szcs is None:
        szcs = rpr.makeelement(qn("w:szCs"), {})
        rpr.insert_element_before(
            szcs,
            "w:highlight", "w:u", "w:effect", "w:bdr", "w:shd", "w:fitText",
            "w:vertAlign", "w:rtl", "w:cs", "w:em", "w:lang",
            "w:eastAsianLayout", "w:specVanish", "w:oMath",
        )
    szcs.set(qn("w:val"), str(int(size * 2)))


def add(doc, text, font, size, color=None, bold=False, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_font(p.add_run(text), font, size, color, bold)


def main():
    doc = Document()
    add(doc, "Homoglyph Attack Demo — TH Sarabun Prank", "TH Sarabun New", 18, (0x1F, 0x2A, 0x44), True, 18)

    add(doc, "1) ฟอนต์ต้นฉบับ TH Sarabun New", "TH Sarabun New", 14, (0x55, 0x55, 0x55), False, 2)
    add(doc, "ก ข ค ง ส", "TH Sarabun New", 40, (0x11, 0x11, 0x11), False, 14)

    add(doc, "2) ฟอนต์ที่ถูกแก้ TH Sarabun Prank (ก ข ง ส ถูกสวมรอยด้วย ค)", "TH Sarabun New", 14, (0xB0, 0x00, 0x20), False, 2)
    add(doc, "ก ข ค ง ส", "TH Sarabun Prank", 40, (0xB0, 0x00, 0x20), False, 14)

    add(doc, "พิมพ์ข้อความนี้ด้วย TH Sarabun Prank:", "TH Sarabun New", 14, (0x55, 0x55, 0x55), False, 2)
    add(doc, "ทดสอบ กขงส กับฟอนต์แปลก", "TH Sarabun Prank", 28, (0x11, 0x11, 0x11), False, 18)

    add(doc, "ทั้งสองบรรทัดข้างบนพิมพ์ตัวอักษรชุดเดียวกัน แต่บรรทัดล่างถูกฟอนต์สวมรอย",
        "TH Sarabun New", 12, (0x66, 0x66, 0x66), False, 0)

    doc.save("prank_demo.docx")
    print("wrote prank_demo.docx")


if __name__ == "__main__":
    main()
