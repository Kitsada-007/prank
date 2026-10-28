# TH Sarabun Prank — Homoglyph Attack on a TrueType Font

สาธิตการโจมตีแบบ **Homoglyph / Homograph Attack** กับฟอนต์ TrueType:
พิมพ์ `ก` `ข` `ง` `ส` แต่หน้าจอแสดงเป็น `ค` ทั้งหมด

ฟอนต์ต้นฉบับ **ไม่ถูกแก้ไขหรือเขียนทับ** — สคริปต์อ่านไฟล์ต้นฉบับแล้วสร้างไฟล์ใหม่ชื่อ
`THSarabunPrank.ttf` โดยเปลี่ยนทั้ง *ชื่อ famille* และ *รูปทรง glyph* ข้างใน

---

## 1. ไฟล์ในโฟลเดอร์นี้

| ไฟล์ | หน้าที่ |
|---|---|
| `src/THSarabunNew-original.ttf` | ฟอนต์ต้นฉบับ TH Sarabun New (Regular) — ใช้อ่านเท่านั้น |
| `build_prank.py` | สคริปต์สร้างฟอนต์ prank (Python + fontTools) |
| `THSarabunPrank.ttf` | ผลลัพธ์: ฟอนต์ "TH Sarabun Prank" |
| `verify.py` | ตรวจสอบภายใน + สร้างภาพ proof (FreeType) |
| `render_proof.py` | เรนเดอร์ฟอนต์ที่ติดตั้งแล้วผ่าน Windows GDI (ctypes) + เทียบพิกเซล |
| `make_docx.py` | สร้าง `prank_demo.docx` สำหรับเปิดใน Word |
| `prank_demo.docx` | ไฟล์ Word สาธิต (มีทั้งฟอนต์จริงและฟอนต์ปลอม) |
| `proof_before_after.png` | ภาพเทียบก่อน/หลัง (FreeType) |
| `proof_windows_gdi.png` | ภาพเรนเดอร์ผ่าน Windows GDI+ ด้วยฟอนต์ที่ติดตั้งแล้ว |
| `install_font.py` / `uninstall_font.py` | ติดตั้ง/ถอนฟอนต์แบบ per-user (Python ล้วน, ไม่ต้อง admin) |
| `requirements.txt` | รายการ package ที่ต้องติดตั้ง |

---

## 2. เครื่องมือที่ใช้

ติดตั้ง dependencies ครั้งเดียว:

```bash
pip install -r requirements.txt
```

- **Python 3** + **fontTools** (`pip install fonttools`) — ใช้แก้ตาราง `glyf`, `hmtx`, `name`, `head`
- **Pillow** (`pip install pillow`) — ใช้เรนเดอร์ภาพตรวจผล
- **python-docx** (`pip install python-docx`) — ใช้สร้างไฟล์ Word สาธิต
- `ctypes` + `winreg` (built-in) — ใช้ติดตั้ง/ถอนฟอนต์และเรนเดอร์ผ่าน GDI โดยไม่ต้องพึ่ง PowerShell

ทางเลือกแบบ GUI (ถ้าอยากทำในวิดีโอให้เห็นภาพ):
- **FontForge** (ฟรี, Open Source) — เปิด TTF → Element > Font Info เปลี่ยนชื่อ → ดับเบิลคลิก glyph `ก` แล้ว paste รูป `ค` ทับ → Generate Fonts
- **High-Logic FontCreator** (มี trial) — เหมือนกัน แต่ลาก glyph ได้ง่ายกว่า
- **Birdfont** (ฟรี) — ใช้แก้ outline ได้

---

## 3. หลักการที่ทำ (สรุปสั้น ๆ สำหรับคอมเมนต์ในกระทู้)

1. **Rename ก่อนแก้** — เขียนทับทุก record ในตาราง `name`:
   - nameID 1 (Family) = `TH Sarabun Prank`
   - nameID 4 (Full name) = `TH Sarabun Prank`
   - nameID 6 (PostScript) = `THSarabunPrank`
   - เพิ่ม nameID 16/17 (Typographic family/subfamily) ให้ Windows 10 มองเห็นถูกต้อง
   - bump `head.fontRevision` เป็น 2.0 กัน Windows cache หน้าเก่า
2. **สวมรอย glyph** — คัดลอก outline ของ glyph `uni0E04` (ค) ไปทับ `uni0E01` (ก),
   `uni0E02` (ข), `uni0E07` (ง), `uni0E2A` (ส) พร้อมคัดลอก advance width จาก `hmtx`
   (cmap เดิมไม่แตะ — ตัวอักษรยัง map ไป glyph เดิม แต่รูปข้างในกลายเป็น ค)
3. **ลบ `hdmx`** — ตารางความกว้างพิกเซลต่อขนาด (legacy) จะค้างค่าเดิมหลังแก้
   ตัวเรนเดอร์สมัยใหม่ (DirectWrite) ไม่ใช้ตารางนี้อยู่แล้ว

> หมายเหตุ: อีกวิธีที่ได้ผลเหมือนกันคือ **cmap remap** — ให้ U+0E01/0E02/0E07/0E2A
> ชี้ไปที่ glyph ของ ค โดยตรง (แก้แค่ตาราง map ไม่แตะ outline) วิธีนี้สั้นกว่า
> แต่ถ้าอาจารย์ถามว่า "แก้ glyph จริงไหม" การแทน outline จะตรงคำถามกว่า

---

## 4. ทำซ้ำเอง (สำหรับถ่ายวิดีโอ)

```bash
# 1) คัดลอกฟอนต์ต้นฉบับ แล้วเปลี่ยนชื่อไฟล์ก่อนแก้ (ห้าม save ทับต้นฉบับ)
cp src/THSarabunNew-original.ttf THSarabunPrank.ttf

# 2) แก้ชื่อ + สวม glyph
python build_prank.py

# 3) ตรวจผล + สร้างภาพ proof
python verify.py

# 4) ติดตั้งแบบ per-user (ไม่ต้อง admin)
python install_font.py

# 4.1) ตรวจซ้ำผ่าน Windows GDI (เทียบพิกเซลกับ ค ต้นฉบับ)
python render_proof.py

# 5) เปิด Word -> เลือกฟอนต์ "TH Sarabun Prank" -> พิมพ์ ก ข ค ง ส
#    หรือเปิด prank_demo.docx ที่เตรียมไว้
```

ผลการตรวจของสคริปต์ `verify.py`:

```
uni0E01: identical to uni0E04? True  advance=(393, 33)
uni0E02: identical to uni0E04? True  advance=(393, 33)
uni0E07: identical to uni0E04? True  advance=(393, 33)
uni0E2A: identical to uni0E04? True  advance=(393, 33)
```

และการเทียบภาพระดับพิกเซล (FreeType):

```
== rendered ink difference (FreeType) ==
   prank ก vs original ก : differing pixels = 227
   prank ก vs original ค : differing pixels = 0
   prank ข vs original ค : differing pixels = 0
   prank ง vs original ค : differing pixels = 0
   prank ส vs original ค : differing pixels = 0
```

(บรรทัด `prank ก vs original ก` ต้องต่างกันจริง เพื่อพิสูจน์ว่าไม่ได้คืนฟอนต์เดิม
ส่วน `vs original ค` ต้องเป็น 0 ทุกตัว)

และเทียบซ้ำผ่าน **Windows GDI** (ฟอนต์ที่ติดตั้งแล้ว, `render_proof.py`):

```
prank ก vs original ค : differing pixels = 0
prank ข vs original ค : differing pixels = 0
prank ง vs original ค : differing pixels = 0
prank ส vs original ค : differing pixels = 0
original ก vs original ค : differing pixels = 579
```

---

## 5. โครงสคริปต์วิดีโอ (ตรงตามโจทย์ 2.1–2.3)

| เวลา | สิ่งที่ถ่าย |
|---|---|
| 0:00–0:20 | เปิดหน้า Desktop / โฟลเดอร์ฟอนต์ ให้เห็นไฟล์ `THSarabunNew.ttf` ต้นฉบับ และ **สำเนา** ที่เปลี่ยนชื่อเป็น `THSarabunPrank.ttf` แล้ว (ข้อ 2.1) |
| 0:20–0:50 | เปิด `build_prank.py` ให้เห็นบรรทัดที่เปลี่ยนชื่อ family และบรรทัดที่ copy outline `uni0E04` ไปทับ `uni0E01/0E02/0E07/0E2A` |
| 0:50–1:20 | รัน `python build_prank.py` แล้วรัน `python verify.py` ให้เห็นผล `identical ... True` |
| 1:20–1:50 | ติดตั้งฟอนต์ (ดับเบิลคลิก TTF → Install for me only หรือ `python install_font.py`) |
| 1:50–2:30 | เปิด Microsoft Word → พิมพ์ `ก` `ข` `ง` `ส` → เปลี่ยนฟอนต์เป็น **TH Sarabun Prank** → ตัวอักษรกลายเป็น `ค` ทั้งหมด (ข้อ 2.2) |
| 2:30–3:00 | เปิด `prank_demo.docx` เทียบบรรทัดบน (TH Sarabun New) กับบรรทัดล่าง (TH Sarabun Prank) |
| 3:00–3:20 | พูดสรุปว่าแก้ด้วย fontTools อย่างไร + ประโยชน์จริง + เปิดหน้า reg.msu.ac.th หรือโผล่หน้าเพื่อยืนยันตัวตน (ข้อ 3.3) |

> ถ้าถ่ายในห้อง lab: ให้ใช้ `python install_font.py` (per-user, ไม่แตะ `C:\Windows\Fonts`)
> และก่อนจบให้รัน `python uninstall_font.py` — ไม่มีไฟล์ระบบถูกเขียนทับ

---

## 6. ประโยชน์จริง (ไม่ใช่แค่แกล้ง)

1. **ตรวจจับฟิชชิง/โดเมนปลอม** — Homoglyph ถูกใช้ทำ `paypa1.com`, `аpple.com` (а ซีริลลิก)
   การเข้าใจกลไกทำให้เขียนตัว normalize ด้วย **Unicode TR39 confusables** ได้
2. **กรองข้อความแอบแฝง** — แชท/อีเมล/ฟอร์มลงทะเบียนที่มีตัวอักษรคล้ายกันปนกัน
   (mixed-script detection) เพื่อกันการหลบคำหยุด/ระบบ mod
3. **Brand protection** — ตรวจว่ามีฟอนต์หรือชื่อแบรนด์ที่ถูกสวม glyph ไปใช้หลอกลูกค้า
4. **QA ฟอนต์** — ตรวจว่าตาราง `cmap` กับ `glyf` สอดคล้องกันจริง ไม่มี glyph ถูกสลับ
   (เคสจริง: ฟอนต์ TH Sarabun IT๙ ที่เอาเลขไทยไปทับด้วยเลขอารบิก)
5. **ความตระหนักด้านความปลอดภัย** — ใช้เป็นสื่อสอนพนักงานว่า "เห็นอย่างเดียวไม่พอ"

---

## 7. ข้อควรระวัง / จริยธรรม

- **ห้าม save ทับฟอนต์ต้นฉบับ** — สคริปต์นี้อ่านไฟล์ต้นฉบับอย่างเดียว และเขียนไฟล์ใหม่
- **ห้ามแจกจ่ายในชื่อ "TH Sarabun New"** — ตั้งชื่อให้ชัดว่าเป็นของเล่น (`TH Sarabun Prank`)
  การปลอมชื่อฟอนต์ราชการแล้วแจกจ่ายอาจเข้าข่ายหลอกลวง
- ใช้กับเครื่องตัวเอง/ในวงจำกัด และถอนออกเมื่อสาธิตเสร็จ

---

## 8. ข้อความพร้อมโพสต์ตอบกระทู้ (แก้รหัส/ชื่อก่อนส่ง)

```
รหัสนิสิต: 6XXXXXXXX-X   ชื่อ: ........................

ทำ Homoglyph Attack กับ TH Sarabun New ครับ
วิธี: ใช้ Python + fontTools (ไม่ใช้ GUI) แก้ที่ระดับ binary
- copy ฟอนต์เป็น THSarabunPrank.ttf ก่อน (ไม่แตะต้นฉบับ)
- เขียนทับ name table ทุก record: Family/Full = "TH Sarabun Prank", PostScript = THSarabunPrank
- copy outline ของ glyph ค (uni0E04) ไปทับ glyph ก (uni0E01), ข (uni0E02), ง (uni0E07), ส (uni0E2A)
  พร้อม copy advance width จาก hmtx
- cmap เดิมไม่แก้ ตัวอักษรยัง map ที่ glyph เดิม แต่รูปข้างในกลายเป็น ค
ผล: พิมพ์ ก ข ค ง ส แล้วขึ้น ค ค ค ค ค (ตรวจด้วยการเทียบ bitmap ระดับ pixel = ตรงกัน 100%)
VDO: <แปะลิงก์>
```

> ถ้าเพื่อนส่งก่อนด้วยวิธีเดียวกัน (เช่นใช้ FontForge ลาก glyph) ให้ reply กระทู้ตัวเองว่า
> "วิธีเดียวกับของ <ชื่อเพื่อน> ครับ" ตามกติกาข้อ 3

---

## 9. ถอนการติดตั้ง

```bash
# ถอนเฉพาะฟอนต์ prank
python uninstall_font.py

# ถอนฟอนต์ TH Sarabun New ที่ติดตั้งไว้เทียบผลด้วย (ถ้าไม่อยากเก็บไว้)
python uninstall_font.py --remove-original
```

ลบเฉพาะค่าที่ติดตั้งแบบ per-user (`HKCU` + `%LOCALAPPDATA%\Microsoft\Windows\Fonts`)
ไม่แตะฟอนต์ระบบของ Windows
