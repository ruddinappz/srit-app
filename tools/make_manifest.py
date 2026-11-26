#!/usr/bin/env python3
"""Tulis clasp_package/Manifest_Berkas.gs: ukuran + MD5 (setelah normalisasi: buang \\r, buang spasi akhir) tiap berkas .html, dan ukuran halaman Index.
Dipakai selfCheck_() (Code.gs) untuk menunjukkan berkas HTML di proyek Apps Script yang BERBEDA / TERPOTONG dari paket (salah tempel, kurang push, versi lama).
Jalankan SETIAP kali berkas .html berubah dan sebelum membuat zip:  python srit-app/tools/make_manifest.py clasp_package   (build.py memanggilnya otomatis)."""
import sys, re, hashlib, pathlib
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'clasp_package')
def norm(t): return re.sub(r'\s+$', '', t.replace('\r', ''))
rows, sizes = [], {}
for f in sorted(src.glob('*.html')):
    b = norm(f.read_text(encoding='utf-8')).encode('utf-8')
    sizes[f.stem] = len(b)
    rows.append("  '%s': [%d, '%s']" % (f.stem, len(b), hashlib.md5(b).hexdigest()))
idx = (src / 'Index.html').read_text(encoding='utf-8')
page = len(idx.encode('utf-8')) + sum(sizes.get(n, 0) for n in re.findall(r"include\('([^']+)'\)", idx))
out = ("/* Manifest_Berkas.gs — DIBANGUN OLEH srit-app/tools/make_manifest.py (jangan diedit tangan). Dipakai selfCheck_() untuk mendeteksi berkas HTML yang berbeda/terpotong.\n"
       " * Normalisasi: buang \\r dan spasi/baris kosong di akhir. [ukuran byte UTF-8, MD5]. */\n"
       "const BERKAS_MANIFEST_ = {\n" + ",\n".join(rows) + "\n};\n"
       "/** Ukuran halaman Index + seluruh include (KiB), saat paket dibangun. Batas keluaran HtmlService ~2048 KiB; jaga < 1900. */\n"
       "const BERKAS_HALAMAN_KIB_ = %d;\n" % (page // 1024))
(src / 'Manifest_Berkas.gs').write_text(out, encoding='utf-8')
print('OK Manifest_Berkas.gs:', len(rows), 'berkas; ukuran halaman', page // 1024, 'KiB')
