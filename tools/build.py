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
# V1.9.92: menu "lazy" (LAZY_VIEWS_ di Config.gs) di Apps Script dimuat saat dibuka; GitHub Pages tidak memakai server-lib, jadi disisipkan langsung di sini.
_lz = re.search(r"const LAZY_VIEWS_ = \{([^}]*)\}", (src / 'Config.gs').read_text(encoding='utf-8'))
_lazy = re.findall(r"'[^']+':\s*'([A-Za-z0-9_]+)'", _lz.group(1)) if _lz else []
_blob = ''.join('<script>__srit.n(\'%s\')</script>\n%s\n' % (n, expand((src / (n + '.html')).read_text(encoding='utf-8'))) for n in _lazy)
if _lazy and '<!--LAZY_VIEWS-->' not in html: raise SystemExit('Penanda <!--LAZY_VIEWS--> tidak ada di Index.html')
html = html.replace('<!--LAZY_VIEWS-->', _blob, 1)
if '<?' in html: print('PERINGATAN: masih ada tag <? ?> yang tidak diganti')
bridge = ('<link rel="manifest" href="manifest.webmanifest"><meta name="theme-color" content="#1c6ef2">'
          '<link rel="icon" type="image/png" href="favicon.png"><link rel="apple-touch-icon" href="apple-touch-icon.png">'
          '<meta name="mobile-web-app-capable" content="yes">'
          '<script src="config.js"></script><script src="gas-bridge.js"></script>'
          '<script>if("serviceWorker" in navigator&&location.protocol==="https:")addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){});});</script>')
html = html.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">' + bridge, 1)
if 'gas-bridge.js' not in html: raise SystemExit('Gagal menyisipkan jembatan (tag <meta charset> tidak ditemukan)')
(out / 'index.html').write_text(html, encoding='utf-8')
print('OK index.html', len(html) // 1024, 'KB')
try:    # peringatan bila ada ikon yang tidak akan tampil (tidak menggagalkan build)
    sys.path.insert(0, str(pathlib.Path(__file__).parent)); import cek_ikon
    _e, _w, _a, _b = cek_ikon.audit(str(src), str(out))
    for _x in _e: print('PERINGATAN IKON:', _x)
except Exception as _ex: print('(pemeriksaan ikon dilewati:', _ex, ')')
