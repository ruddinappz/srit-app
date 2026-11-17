#!/usr/bin/env python3
"""Bangun clasp_package/Assets_RHK.gs (templat Word Laporan RHK) dari dua berkas contoh:
   python make_assets_rhk.py <Laporan_Harian_contoh.docx> <Laporan_per_RHK_contoh.docx> <keluaran Assets_RHK.gs>
Teks isian diganti penanda {{...}}; baris tabel yang berulang ditandai oleh penanda di dalam barisnya.
Foto contoh dan gambar tanda tangan dibuang (tanda tangan basah/stempel ditaruh pegawai saat mencetak)."""
import sys, re, zipfile, json, base64

def tx(s):  # teks w:t -> XML aman
    return s

def sub_exact(xml, old, new, count=None, must=True):
    pat = re.compile(r'(<w:t(?: [^>]*)?>)' + re.escape(old) + r'(</w:t>)')
    n = len(pat.findall(xml))
    if must and n == 0: raise SystemExit('Teks tidak ditemukan: ' + old[:60])
    if count is not None and n != count: raise SystemExit('Jumlah %s != %s untuk: %s' % (n, count, old[:60]))
    return pat.sub(lambda m: m.group(1) + new + m.group(2), xml)

def sub_prefix(xml, prefix, new, count=None):
    pat = re.compile(r'(<w:t(?: [^>]*)?>)' + re.escape(prefix) + r'[^<]*(</w:t>)')
    n = len(pat.findall(xml))
    if n == 0 or (count is not None and n != count): raise SystemExit('Awalan %s kali (%s): %s' % (n, count, prefix[:60]))
    return pat.sub(lambda m: m.group(1) + new + m.group(2), xml)

def rows_of(tbl):
    return re.findall(r'<w:tr[ >].*?</w:tr>', tbl, re.S)

def tables(xml):
    # tabel tingkat atas (tidak ada tabel bersarang pada contoh ini)
    return [(m.start(), m.end()) for m in re.finditer(r'<w:tbl>.*?</w:tbl>', xml, re.S)]

def table_with(xml, text):
    for a, b in tables(xml):
        if text in xml[a:b]: return a, b
    raise SystemExit('Tabel tidak ditemukan: ' + text)

def keep_first_row(xml, marker_text, header_rows):
    """Pada tabel yang memuat marker_text: pertahankan header_rows baris pertama + SATU baris data, hapus baris data lainnya."""
    a, b = table_with(xml, marker_text)
    t = xml[a:b]; rs = rows_of(t)
    for r in rs[header_rows + 1:]: t = t.replace(r, '', 1)
    return xml[:a] + t + xml[b:]


def kop_baru(h):
    """Kop surat TERBARU (sama dengan SRIT.Kop di JS_Brand.html): baris 2-3 diganti; logo & alamat sama dengan kop lama."""
    if 'KEMENTERIAN SOSIAL REPUBLIK INDONESIA' not in h: return h
    h = h.replace('PUSAT PENDIDIKAN, PELATIHAN, DAN PENGEMBANGAN PROFESI', 'SEKRETARIAT JENDERAL').replace('KESEJAHTERAAN SOSIAL', 'PUSDIKLATBANGPROFKESOS')
    def p14(m):  # baris 1 kop: 14 pt (sama dengan kop baru)
        return m.group(0).replace('w:val="32"', 'w:val="28"') if 'KEMENTERIAN SOSIAL REPUBLIK INDONESIA' in m.group(0) else m.group(0)
    return re.sub(r'<w:p(?: [^>]*)?>.*?</w:p>', p14, h, flags=re.S)

def build(path, kind):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    D = z.read('word/document.xml').decode('utf8')
    R = z.read('word/_rels/document.xml.rels').decode('utf8')
    drop_media = [n for n in names if re.match(r'word/media/image\d+\.(jpg|png)$', n)]
    # gambar header (logo) dipertahankan: ditentukan dari rels header
    keep = set()
    for n in names:
        if n.startswith('word/_rels/header') and n.endswith('.rels'):
            for t in re.findall(r'Target="([^"]+)"', z.read(n).decode('utf8')): keep.add('word/' + t)
    drop_media = [n for n in drop_media if n not in keep]
    # --- identitas & data umum ---
    for old, new in [('AKHMAD SYAHRUDDIN', '{{NAMA}}'), ('19890330 202622 1 001', '{{NIP}}'), ('Penata Muda / IX', '{{PANGKAT}}'),
                     ('Penata Layanan Operasional (Wali Asrama)', '{{JABATAN}}'), ('Sekolah Rakyat Terintegrasi 1 Kabupaten Jombang', '{{UNIT}}'),
                     ('1 April s.d. 31 Desember 2026', '{{PERIODE_SKP}}'), ('Oktober 2026', '{{PERIODE_LAP}}')]:
        D = sub_exact(D, old, new)
    D = sub_prefix(D, 'Penata Layanan Operasional (Wali Asrama) berperan', '{{UMUM}}', 1)
    D = sub_prefix(D, 'Melaksanakan tugas pokok', '{{MAKSUD}}', 1)
    D = sub_prefix(D, 'Pelaksanaan tugas Penata', '{{LINGKUP}}', 1)
    D = sub_prefix(D, 'Keputusan Kepala Pusat', '{{DASAR}}', 1)
    D = re.sub(r'Jombang, \d{2} \w+ \d{4}', 'Jombang, {{TGL_LAPOR}}', D)
    D = re.sub(r'(<w:t(?: [^>]*)?>)NIP\. 19890330 202622 1 001', r'\1NIP. {{NIP}}', D)
    D = sub_exact(D, 'Demikian laporan kegiatan harian ini disusun sebagai bentuk pertanggungjawaban pelaksanaan tugas Wali Asrama.',
                  'Demikian laporan kegiatan harian ini disusun sebagai bentuk pertanggungjawaban pelaksanaan tugas {{JABATAN_PENDEK}}.')
    if kind == 'harian':
        D = sub_exact(D, 'Wali Asrama Shift Malam (23.00-07.00)', '{{JAB_SHORT}} Shift {{SHIFT_NAMA}} ({{SHIFT_JAM}})')
        D = sub_exact(D, 'Jumat, 02 Oktober 2026', '{{TGL_PANJANG}}', 2)
        D = sub_exact(D, 'RHK-4, RHK-3', '{{KODE_RHK}}')
        # rincian RHK: satu baris prototipe
        a, b = table_with(D, 'Rincian RHK yang Dilaksanakan'); t = D[a:b]; rs = rows_of(t)
        proto = rs[1]
        proto = sub_exact(proto, 'RHK-4', '{{R_KODE}}')
        proto = sub_prefix(proto, 'Tersedianya laporan penerapan', '{{R_RHK}}', 1)
        proto = sub_prefix(proto, 'Jumlah laporan penerapan', '{{R_IND}}', 1)
        t = t.replace(rs[1], proto, 1).replace(rs[2], '', 1)
        D = D[:a] + t + D[b:]
        D = sub_prefix(D, 'Pada hari Jumat, 02 Oktober 2026, seluruh kegiatan', '{{INTRO_KEG}}', 1)
        # kegiatan
        a, b = table_with(D, 'Uraian Kegiatan'); t = D[a:b]; rs = rows_of(t)
        p = rs[1]
        p = sub_exact(p, '1', '{{K_NO}}'); p = sub_exact(p, '23.00–02.00', '{{K_PUKUL}}')
        p = sub_prefix(p, 'Ronda keamanan', '{{K_URAIAN}}', 1); p = sub_exact(p, 'RHK-4', '{{K_RHK}}')
        for r in rs[2:]: t = t.replace(r, '', 1)
        t = t.replace(rs[1], p, 1); D = D[:a] + t + D[b:]
        D = sub_prefix(D, 'Pada hari Jumat, 02 Oktober 2026, seluruh rangkaian', '{{HASIL}}', 1)
        D = sub_prefix(D, 'Pelaksanaan tugas Wali Asrama pada shift', '{{KESIMPULAN}}', 1)
        # dokumentasi + tanda tangan
        a, b = table_with(D, 'image1.jpg')
        D = D[:a] + '<w:p><w:r><w:t>{{FOTO_TABLE}}</w:t></w:r></w:p>' + D[b:]
        D = re.sub(r'<w:r(?: [^>]*)?>(?:(?!</w:r>).)*?<w:drawing>.*?</w:drawing>(?:(?!</w:r>).)*?</w:r>', '', D, flags=re.S)
        D = D.replace('<mc:AlternateContent>', '<mc:AlternateContent>') if False else D
    else:
        D = sub_exact(D, 'RHK 4 ', 'RHK {{R_NO}} ', 2)
        D = sub_exact(D, '– RHK UTAMA | ', '– RHK {{R_JENIS}} | ', 2)
        D = sub_exact(D, 'Kode: RHK-4', 'Kode: {{R_KODE}}', 2)
        D = sub_prefix(D, 'Tersedianya laporan penerapan', '{{R_RHK}}', 2)
        D = sub_prefix(D, 'Wali Asrama Shift Malam', '{{JAB_SHORT}} Shift {{SHIFT_NAMA}} ({{SHIFT_JAM}}) — {{TGL_PANJANG}}', 1)
        D = sub_exact(D, 'Kamis, 01 Oktober 2026', '{{TGL_PANJANG}}', 1)
        D = sub_prefix(D, 'Jumlah laporan penerapan', '{{R_IND}}', 1)
        D = sub_exact(D, '9 laporan/dokumen', '{{R_TARGET}}', 1)
        D = sub_exact(D, 'B. Kegiatan yang Dilaksanakan Terkait RHK-4', 'B. Kegiatan yang Dilaksanakan Terkait {{R_KODE}}', 1)
        D = sub_prefix(D, 'Pada hari Kamis, 01 Oktober 2026, kegiatan Wali Asrama', '{{INTRO_KEG}}', 1)
        a, b = table_with(D, 'Uraian Kegiatan'); t = D[a:b]; rs = rows_of(t)
        p = rs[1]
        p = sub_exact(p, '1', '{{K_NO}}'); p = sub_exact(p, '23.00–01.30', '{{K_PUKUL}}'); p = sub_prefix(p, 'Pengawasan keamanan', '{{K_URAIAN}}', 1)
        for r in rs[2:]: t = t.replace(r, '', 1)
        t = t.replace(rs[1], p, 1); D = D[:a] + t + D[b:]
        D = sub_prefix(D, 'Pada hari Kamis, 01 Oktober 2026, kegiatan yang termasuk', '{{HASIL}}', 1)
        D = sub_prefix(D, 'Pelaksanaan tugas Wali Asrama terkait', '{{KESIMPULAN}}', 1)
        ts = tables(D)
        a, b = ts[-1]   # tabel terakhir = kotak dokumentasi kosong
        D = D[:a] + '<w:p><w:r><w:t>{{FOTO_TABLE}}</w:t></w:r></w:p>' + D[b:]
    # rels: buang gambar contoh
    def keep_rel(m):
        return '' if any(n.split('/')[-1] in m.group(0) for n in drop_media) else m.group(0)
    R = re.sub(r'<Relationship [^>]*/>', keep_rel, R)
    parts = []
    for n in names:
        if n.endswith('/') or n in drop_media: continue
        if n == 'word/document.xml': parts.append((n, 't', D)); continue
        if n == 'word/_rels/document.xml.rels': parts.append((n, 't', R)); continue
        raw = z.read(n)
        if re.match(r'word/header\d+\.xml$', n): parts.append((n, 't', kop_baru(raw.decode('utf8')))); continue
        if n.endswith(('.xml', '.rels')): parts.append((n, 't', raw.decode('utf8')))
        else: parts.append((n, 'b', base64.b64encode(raw).decode()))
    # [Content_Types] dahulu
    parts.sort(key=lambda x: 0 if x[0] == '[Content_Types].xml' else 1)
    ct = [p for p in parts if p[0] == '[Content_Types].xml'][0][2]
    for ext, mime in (('jpg', 'image/jpeg'), ('jpeg', 'image/jpeg'), ('png', 'image/png')):
        if 'Extension="%s"' % ext not in ct:
            ct = ct.replace('<Types ', '<Types ', 1)
            ct = re.sub(r'(<Types[^>]*>)', r'\1<Default Extension="%s" ContentType="%s"/>' % (ext, mime), ct, 1)
    parts = [(n, k, ct if n == '[Content_Types].xml' else v) for n, k, v in parts]
    # parameter tata letak foto/ukuran halaman bagi pembangun
    return {'parts': [{'n': n, 'k': k, 'v': v} for n, k, v in parts]}

if __name__ == '__main__':
    h, r, out = sys.argv[1:4]
    A = {'harian': build(h, 'harian'), 'rhk': build(r, 'rhk')}
    js = '/* SRITi — Assets_RHK.gs (DIBANGUN OLEH srit-app/tools/make_assets_rhk.py — jangan diedit tangan)\n * Templat Word Laporan Harian RHK & Laporan per RHK (dari berkas contoh). Dipakai View_RHK.html lewat apiRhkAsset. */\n'
    js += 'const RHK_ASSETS_ = ' + json.dumps(A, ensure_ascii=False, separators=(',', ':')) + ';\n'
    open(out, 'w', encoding='utf8').write(js)
    print('OK', out, len(js) // 1024, 'KB')
