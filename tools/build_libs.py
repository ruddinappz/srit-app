#!/usr/bin/env python3
"""Buat ulang pustaka yang ditanam SRITi (jalankan HANYA bila ada ikon baru atau versi pustaka diganti).
Langkah:
  1) mkdir libsrc && cd libsrc
     npm pack bootstrap@5.3.3 bootstrap-icons@1.11.3 chart.js@4.4.6 xlsx@0.18.5 jsqr@1.4.0
     (ekstrak tiap .tgz ke folder bernama sama tanpa .tgz, mis. bootstrap-5.3.3/package/...)
  2) pip install fonttools brotli
  3) python build_libs.py <folder_libsrc> <folder_clasp_package> <folder_srit-app>
Hasil: Lib_Bootstrap.html (Bootstrap + ikon SUBSET), Lib_Chart/Lib_JsQR/Lib_Xlsx.html (sumber cadangan apiLibSource), srit-app/libs/*.
Ikon yang ikut = semua nama ikon bootstrap-icons yang muncul sebagai kata di berkas .html/.gs paket (aman untuk nama ikon dinamis)."""
import re, glob, base64, io, sys, os
from fontTools import subset
from fontTools.ttLib import TTFont
SRC, CLASP, APP = [os.path.abspath(a) for a in sys.argv[1:4]]
rd = lambda p: open(p, encoding='utf-8').read()
strip_map = lambda t: re.sub(r'/\*#\s*sourceMappingURL=[^*]*\*/|//# sourceMappingURL=\S+', '', t).strip()
P = lambda *a: os.path.join(SRC, *a)
css_icons = rd(P('bootstrap-icons-1.11.3', 'package', 'font', 'bootstrap-icons.css'))
m = dict(re.findall(r'\.bi-([a-z0-9-]+)::before\s*\{\s*content:\s*"\\([0-9a-f]+)"', css_icons))
toks = set()
for f in glob.glob(os.path.join(CLASP, '*.html')) + glob.glob(os.path.join(CLASP, '*.gs')):
    if os.path.basename(f).startswith('Lib_'): continue
    txt = open(f, encoding='utf-8', errors='ignore').read()
    toks.update(re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*', txt))                   # kata polos (nama ikon dalam ternary/string dinamis)
    toks.update(re.findall(r'\bbi-([a-z0-9]+(?:-[a-z0-9]+)*)', txt))             # kelas langsung: bi-nama-ikon
used = sorted(n for n in m if n in toks)
opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']; opts.notdef_outline = False
font = TTFont(P('bootstrap-icons-1.11.3', 'package', 'font', 'fonts', 'bootstrap-icons.woff2'))
s = subset.Subsetter(opts); s.populate(unicodes=[int(m[n], 16) for n in used]); s.subset(font)
font.flavor = 'woff2'; bio = io.BytesIO(); font.save(bio)
ico = ('@font-face{font-display:block;font-family:"bootstrap-icons";src:url(data:font/woff2;base64,' + base64.b64encode(bio.getvalue()).decode() + ') format("woff2")}\n'
       '.bi::before,[class^=bi-]::before,[class*=" bi-"]::before{display:inline-block;font-family:"bootstrap-icons"!important;font-style:normal;font-weight:400!important;font-variant:normal;text-transform:none;line-height:1;vertical-align:-.125em;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}\n'
       + ''.join('.bi-%s::before{content:"\\%s"}' % (n, m[n]) for n in used) + '\n')
css = strip_map(rd(P('bootstrap-5.3.3', 'package', 'dist', 'css', 'bootstrap.min.css')))
js = strip_map(rd(P('bootstrap-5.3.3', 'package', 'dist', 'js', 'bootstrap.bundle.min.js')))
open(os.path.join(CLASP, 'Lib_Bootstrap.html'), 'w', encoding='utf-8').write(
    '<!-- SRITi — pustaka inti DITANAM (tanpa CDN): Bootstrap 5.3.3 + Bootstrap Icons 1.11.3 (subset). Dibuat oleh tools/build_libs.py -->\n<style id="srit-lib-css">\n' + css + '\n' + ico + '</style>\n<script>\n' + js + '\n</script>\n')
os.makedirs(os.path.join(APP, 'libs'), exist_ok=True)
for src, name, fn in [('chart.js-4.4.6/package/dist/chart.umd.js', 'Lib_Chart', 'chart.umd.js'), ('jsqr-1.4.0/package/dist/jsQR.js', 'Lib_JsQR', 'jsQR.js'), ('xlsx-0.18.5/package/dist/xlsx.full.min.js', 'Lib_Xlsx', 'xlsx.full.min.js')]:
    t = strip_map(rd(P(*src.split('/'))))
    open(os.path.join(CLASP, name + '.html'), 'w', encoding='utf-8').write(t)
    open(os.path.join(APP, 'libs', fn), 'w', encoding='utf-8').write(t)
print('OK —', len(used), 'ikon disertakan')
