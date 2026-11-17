#!/usr/bin/env python3
"""Bangun clasp_package/Assets_RaporSRMA.gs dari DUA berkas contoh (tools/contoh/):
  - tools/contoh/*.xlsx (template nilai SRMA)     -> katalog 62 indikator, pustaka deskripsi per predikat, bagian statis xlsx
  - tools/contoh/*.docx (raport keasramaan contoh) -> cetakan docx (document.xml/header1.xml bertanda {{...}}), katalog 79 indikator, watermark
Pakai:  python make_assets_rapor.py <folder_clasp_package>
Metadata pribadi pada berkas contoh (email pembuat, path komputer, nama pengubah, customXml WPS) SENGAJA TIDAK disalin."""
import sys, os, re, io, json, base64, zipfile, copy, collections
from lxml import etree
from openpyxl import load_workbook
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'contoh')
import glob
_x, _d = sorted(glob.glob(os.path.join(C, '*.xlsx'))), sorted(glob.glob(os.path.join(C, '*.docx')))
assert _x and _d, 'Letakkan satu berkas .xlsx (template nilai SRMA) dan satu .docx (raport keasramaan contoh) di tools/contoh/'
XLSX, DOCX = _x[0], _d[0]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'; ns = {'w': W}; q = lambda t: '{%s}%s' % (W, t)
XML = '{http://www.w3.org/XML/1998/namespace}space'
CUT_B, CUT_A = 75, 85           # A >= 85, B 75-84, C < 75  (98,6% konsisten dengan deskripsi pada data contoh)
band = lambda n: 'A' if n >= CUT_A else ('B' if n >= CUT_B else 'C')

# ------------------------------------------------------------------ XLSX
wb = load_workbook(XLSX); ws, rf = wb['Penilaian'], wb['Referensi']
cat62 = []; grp = None
for r in rf.iter_rows(min_row=2, values_only=True):
    if r[1]: grp = r[1].strip()
    cat62.append({'n': int(r[0]), 'g': grp, 'i': r[2].strip()})
assert len(cat62) == 62
cnt = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for r in ws.iter_rows(min_row=2, values_only=True):
    for k in range(62):
        if r[3 + 2 * k] and r[3 + 2 * k + 1]: cnt[k + 1][band(int(r[3 + 2 * k]))][r[3 + 2 * k + 1].strip()] += 1
lib62 = {}
for n in range(1, 63):
    d = {b: cnt[n][b].most_common(1)[0][0] for b in 'ABC' if cnt[n][b]}
    for b, near in (('A', 'BC'), ('B', 'AC'), ('C', 'BA')):          # pita kosong -> pakai pita terdekat
        if b not in d:
            for nb in near:
                if nb in d: d[b] = d[nb]; break
    lib62[str(n)] = d
zx = zipfile.ZipFile(XLSX); rd = lambda z, p: z.read(p).decode('utf-8')
wbx = rd(zx, 'xl/workbook.xml')
wbx = re.sub(r'<mc:AlternateContent.*?</mc:AlternateContent>', '', wbx, flags=re.S)      # buang path komputer pembuat
wbx = re.sub(r'<xr:revisionPtr[^>]*/>', '', wbx)
wbx = re.sub(r'<definedNames>.*?</definedNames>', '{{DEFNAMES}}', wbx, flags=re.S)
xlsx_parts = {'xl/styles.xml': rd(zx, 'xl/styles.xml'), 'xl/theme/theme1.xml': rd(zx, 'xl/theme/theme1.xml'), 'xl/workbook.xml': wbx,
              'xl/_rels/workbook.xml.rels': rd(zx, 'xl/_rels/workbook.xml.rels'), '_rels/.rels': rd(zx, '_rels/.rels'),
              '[Content_Types].xml': rd(zx, '[Content_Types].xml')}
sheet1_cols = re.search(r'<cols>.*?</cols>', rd(zx, 'xl/worksheets/sheet1.xml'), re.S).group(0)
sheet2_cols = re.search(r'<cols>.*?</cols>', rd(zx, 'xl/worksheets/sheet2.xml'), re.S).group(0)
srma = {'hdr1': [c.value for c in ws[1]], 'hdr2': [c.value for c in rf[1]], 'cat': cat62, 'lib': lib62, 'cutA': CUT_A, 'cutB': CUT_B, 'xlsx': xlsx_parts, 'cols1': sheet1_cols, 'cols2': sheet2_cols}

# ------------------------------------------------------------------ DOCX
zd = zipfile.ZipFile(DOCX)
doc = etree.fromstring(zd.read('word/document.xml')); hdr = etree.fromstring(zd.read('word/header1.xml'))
body = doc.find('w:body', ns); big = body[0]; kh = body[2]; ttd = body[4]

def own_runs(p): return [r for r in p.findall('w:r', ns) if r.find('w:t', ns) is not None]
def set_cell_text(tc, text):
    """semua teks sel -> satu run bertanda; format (rPr) run pertama dipertahankan"""
    ps = tc.findall('w:p', ns)
    p = next((x for x in ps if own_runs(x)), ps[0])      # paragraf bertulisan; paragraf kosong lain (ruang tanda tangan) DIPERTAHANKAN
    runs = own_runs(p); rpr = None
    if runs: rpr = runs[0].find('w:rPr', ns)
    elif p.find('w:pPr/w:rPr', ns) is not None: rpr = p.find('w:pPr/w:rPr', ns)
    for r in runs: p.remove(r)
    r = etree.SubElement(p, q('r'))
    if rpr is not None: r.append(copy.deepcopy(rpr))
    t = etree.SubElement(r, q('t')); t.text = text; t.set(XML, 'preserve')

cat79 = []; cur = None; idx = 0
for tr in big.findall('w:tr', ns):
    tcs = tr.findall('w:tc', ns); txt = [''.join(tc.itertext()).strip() for tc in tcs]
    if len(tcs) == 1: cur = txt[0]; continue
    if txt[0] == 'No': continue
    if len(tcs) == 4 and txt[0].isdigit():
        idx += 1
        cat79.append({'k': idx, 'g': cur, 'no': int(txt[0]), 'i': txt[1], 'p': txt[2], 'd': txt[3]})
        set_cell_text(tcs[2], '{{P%d}}' % idx); set_cell_text(tcs[3], '{{D%d}}' % idx)
assert len(cat79) == 79, len(cat79)
# ketidakhadiran: kolom Jumlah pada 3 baris terakhir
for key, tr in zip(('KH1', 'KH2', 'KH3'), kh.findall('w:tr', ns)[2:5]): set_cell_text(tr.findall('w:tc', ns)[2], '{{%s}}' % key)
# tanda tangan
rows = ttd.findall('w:tr', ns); cell = lambda r, c: rows[r].findall('w:tc', ns)[c]
def set_run_texts(tc, mapping):          # mapping: {indeks_run_bertulis: teks_baru, ...} pada paragraf pertama
    rs = own_runs(next(x for x in tc.findall('w:p', ns) if own_runs(x)))
    for i, tx in mapping.items(): rs[i].find('w:t', ns).text = tx; rs[i].find('w:t', ns).set(XML, 'preserve')
    return rs
def merge_from(tc, start, text):         # gabungkan run mulai 'start' menjadi satu bertanda
    p = next(x for x in tc.findall('w:p', ns) if own_runs(x)); rs = own_runs(p)
    rs[start].find('w:t', ns).text = text; rs[start].find('w:t', ns).set(XML, 'preserve')
    for r in rs[start + 1:]: p.remove(r)
set_run_texts(cell(0, 1), {1: '{{TGL_HB}}', 2: '{{TGL_TH}}'})      # 'Jombang,' | '12 Desember' | '2025' (tiga run asli, format asli dipertahankan)
set_cell_text(cell(1, 0), '{{WALI_ASRAMA}}'); set_cell_text(cell(1, 1), '{{WALI_ASUH}}')
merge_from(cell(2, 0), 2, ' {{NIP_WALI_ASRAMA}}'); merge_from(cell(2, 1), 1, '{{NIP_WALI_ASUH}}')
set_cell_text(cell(4, 1), '{{KEPSEK}}'); merge_from(cell(5, 1), 0, 'NIP. {{NIP_KEPSEK}}')
# header: tujuh isian identitas. Run nilai dicari dari POSISI (setelah label dan tanda ':'), bukan dari isinya -> tidak ada data siswa di skrip ini.
LABELS = {'Nama Sekolah': 'NAMA_SEKOLAH', 'Alamat': 'ALAMAT', 'Nama Peserta Didik': 'NAMA', 'NIS/NISN': 'NIS_NISN', 'Kelas': 'KELAS', 'Semester': 'SEMESTER', 'Tahun Ajaran': 'TAHUN_AJARAN'}
def tx(r): t = r.find('w:t', ns); return t.text if t is not None else None
done = set()
for p in hdr.iter(q('p')):
    rs = [r for r in p.findall('w:r', ns) if r.find('w:t', ns) is not None]; texts = [tx(r) or '' for r in rs]
    lab = [(i, texts[i].strip()) for i in range(len(rs)) if texts[i].strip() in LABELS]
    for j, (i, name) in enumerate(lab):
        c = next(k for k in range(i + 1, len(rs)) if texts[k].strip() == ':')
        end = lab[j + 1][0] if j + 1 < len(lab) else len(rs)
        val = list(range(c + 1, end))
        while val and texts[val[-1]].strip() == '': val.pop()          # run spasi di ujung dibiarkan
        while val and texts[val[0]].strip() == '': val.pop(0)          # run spasi di awal dibiarkan (formatnya berbeda dari run nilai)
        first = val[0]; lead = re.match(r'\s*', texts[first]).group(0)
        rs[first].find('w:t', ns).text = lead + '{{%s}}' % LABELS[name]; rs[first].find('w:t', ns).set(XML, 'preserve')
        for k in val[1:]: p.remove(rs[k])
        done.add(name)
assert done == set(LABELS), done

STRIP = re.compile(r'\s+(?:w:rsid\w*|w14:paraId|w14:textId)="[^"]*"')
def ser(e):
    s = etree.tostring(e, xml_declaration=True, encoding='UTF-8', standalone=True).decode('utf-8')
    return STRIP.sub('', s)
tpl_doc, tpl_hdr = ser(doc), ser(hdr)
for k in range(1, 80): assert '{{P%d}}' % k in tpl_doc and '{{D%d}}' % k in tpl_doc
for key in ('TGL_HB', 'TGL_TH', 'WALI_ASRAMA', 'WALI_ASUH', 'NIP_WALI_ASRAMA', 'NIP_WALI_ASUH', 'KEPSEK', 'NIP_KEPSEK', 'KH1', 'KH2', 'KH3'): assert '{{%s}}' % key in tpl_doc, key
for key in ('NAMA_SEKOLAH', 'KELAS', 'ALAMAT', 'SEMESTER', 'NAMA', 'TAHUN_AJARAN', 'NIS_NISN'): assert '{{%s}}' % key in tpl_hdr, key
rels = rd(zd, 'word/_rels/document.xml.rels')
rels = re.sub(r'<Relationship [^>]*customXml[^>]*/>', '', rels)
ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
      '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
      '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
      '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
      '<Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>'
      '<Override PartName="/word/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
      '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
      '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
      '<Override PartName="/word/endnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml"/>'
      '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
      '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>')
root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
             '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
docx_parts = {'[Content_Types].xml': ct, '_rels/.rels': root_rels, 'word/_rels/document.xml.rels': rels,
              'word/_rels/header1.xml.rels': rd(zd, 'word/_rels/header1.xml.rels'), 'word/document.xml': tpl_doc, 'word/header1.xml': tpl_hdr,
              'word/styles.xml': rd(zd, 'word/styles.xml'), 'word/settings.xml': rd(zd, 'word/settings.xml'), 'word/fontTable.xml': rd(zd, 'word/fontTable.xml'),
              'word/theme/theme1.xml': rd(zd, 'word/theme/theme1.xml'), 'word/footnotes.xml': rd(zd, 'word/footnotes.xml'), 'word/endnotes.xml': rd(zd, 'word/endnotes.xml')}
# padanan 79 -> 62 hanya bila deskripsi docx persis ada di Excel dan tunjuk TEPAT SATU indikator (bukti data, bukan tebakan)
norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', str(s).lower())).strip()
pool = collections.defaultdict(set)
for r in ws.iter_rows(min_row=2, values_only=True):
    for k in range(62):
        if r[3 + 2 * k + 1]: pool[norm(r[3 + 2 * k + 1])].add(k + 1)
for e in cat79:
    s = pool.get(norm(e['d'])); e['x'] = list(s)[0] if s and len(s) == 1 else 0
rk = {'cat': cat79, 'parts': docx_parts}
wm = base64.b64encode(zd.read('word/media/image1.png')).decode('ascii')

HEAD = '/** DIBANGUN OTOMATIS oleh srit-app/tools/make_assets_rapor.py dari berkas contoh. JANGAN diedit tangan. */\n'
o1 = os.path.join(sys.argv[1], 'Assets_RaporSRMA.gs'); o2 = os.path.join(sys.argv[1], 'Assets_RaporWM.gs')
open(o1, 'w', encoding='utf-8').write(HEAD + '/* Cetakan Excel Template Nilai SRMA (62 indikator) + cetakan Word Raport Keasramaan (79 indikator). */\nconst RAPOR_ASSETS_ = ' + json.dumps({'srma': srma, 'rk': rk}, ensure_ascii=False, separators=(',', ':')) + ';\n')
open(o2, 'w', encoding='utf-8').write(HEAD + '/* Watermark logo Sekolah Rakyat (PNG, base64) untuk header Word. */\nconst RAPOR_WM_ = ' + json.dumps(wm) + ';\n')
print('OK', round(os.path.getsize(o1) / 1024), 'KB +', round(os.path.getsize(o2) / 1024), 'KB | 62 indikator, 79 indikator, padanan unik 79->62:', sum(1 for e in cat79 if e['x']))
