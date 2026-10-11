#!/usr/bin/env python3
"""Gabungkan Index.html + semua <?!= include('X') ?> dari folder GAS menjadi satu index.html.
Pakai:  python build.py  <folder_clasp_package>  <folder_keluaran>
Contoh: python build.py ../../clasp_package ..
"""
import re, sys, pathlib, shutil
src = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
inc = re.compile(r"<\?!=\s*include\(\s*['\"]([A-Za-z0-9_]+)['\"]\s*\)\s*;?\s*\?>")
def expand(text, depth=0):
    if depth > 5: raise SystemExit('include terlalu dalam')
    def rep(m):
        f = src / (m.group(1) + '.html')
        if not f.exists(): raise SystemExit('Berkas hilang: ' + f.name)
        return expand(f.read_text(encoding='utf-8'), depth + 1)
    return inc.sub(rep, text)
html = expand((src / 'Index.html').read_text(encoding='utf-8'))
if '<?' in html: print('PERINGATAN: masih ada tag <? ?> yang tidak diganti')
bridge = ('<link rel="manifest" href="manifest.webmanifest"><meta name="theme-color" content="#1c6ef2">'
          '<link rel="icon" href="icon-192.png"><link rel="apple-touch-icon" href="icon-192.png">'
          '<meta name="mobile-web-app-capable" content="yes">'
          '<script src="config.js"></script><script src="gas-bridge.js"></script>')
html = html.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">' + bridge, 1)
if 'gas-bridge.js' not in html: raise SystemExit('Gagal menyisipkan jembatan (tag <meta charset> tidak ditemukan)')
(out / 'index.html').write_text(html, encoding='utf-8')
print('OK index.html', len(html) // 1024, 'KB')
