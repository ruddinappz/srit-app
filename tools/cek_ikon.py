#!/usr/bin/env python3
"""Periksa semua ikon SRITi — jalankan sebelum deploy (dipanggil otomatis oleh build.py sebagai peringatan).
Pakai:  python cek_ikon.py <folder_clasp_package> [<folder_srit-app>]
Butuh:  pip install fonttools brotli   (Pillow opsional, untuk memeriksa ikon aplikasi PWA)
Yang diperiksa:
  1) Setiap nama ikon bi-* yang dipakai di tampilan (termasuk yang dibentuk dinamis: bi bi-${a?'x':'y'}) ADA di subset Lib_Bootstrap.html.
  2) Setiap kode ikon di CSS punya glyph bergambar di font yang ditanam.
  3) Posisi glyph benar: selisih (xMin kotak glyph - lsb) harus 0. Bila tidak, ikon tampak menggeser/menempel ke kiri
     (penyebab: font di-subset dengan recalcBBoxes=True; lihat catatan di build_libs.py).
  4) (opsional) Ikon aplikasi di manifest: berkas ada, ukuran cocok, dan isi ikon maskable berada di zona aman (radius 40%).
Kode keluar 0 = bersih, 1 = ada masalah."""
import re, sys, glob, os, io, json, base64, math

def audit(clasp, app=None):
    err, warn = [], []
    lib = open(os.path.join(clasp, 'Lib_Bootstrap.html'), encoding='utf-8').read()
    defined = dict(re.findall(r'\.bi-([a-z0-9-]+)::before\{content:"\\([0-9a-f]+)"\}', lib))
    # ---- 1) ikon dipakai vs tersedia
    used = {}
    files = [f for f in glob.glob(os.path.join(clasp, '*')) if f.endswith(('.html', '.gs')) and not os.path.basename(f).startswith('Lib_')]
    for f in files:
        t = open(f, encoding='utf-8', errors='ignore').read(); b = os.path.basename(f)
        for m in re.finditer(r'(?<![\w-])bi-([a-z0-9]+(?:-[a-z0-9]+)*)(?![\w-]|\$\{)', t): used.setdefault(m.group(1), set()).add(b)
        for m in re.finditer(r'bi-\$\{', t):                       # bi-${a?'x':'y'} / bi bi-${...}: ambil NILAI hasil, bukan operand pembanding
            expr = t[m.end():m.end() + 220].split('}')[0]
            for q in re.finditer(r"'([a-z0-9][a-z0-9-]*)", expr):
                if expr[:q.start()].rstrip().endswith(('==', '!=')): continue     # type==='ok' -> 'ok' bukan ikon
                used.setdefault(q.group(1), set()).add(b + ' (dinamis)')
    for n, where in sorted(used.items()):
        if n not in defined and n != 'chevron': err.append('ikon bi-%s dipakai di %s tetapi TIDAK ADA di subset (jalankan build_libs.py --icons-only)' % (n, ', '.join(sorted(where))))
    # ---- 2 & 3) font tertanam
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.boundsPen import BoundsPen
        raw = base64.b64decode(re.search(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)', lib).group(1))
        f = TTFont(io.BytesIO(raw)); cmap = f.getBestCmap(); gs = f.getGlyphSet(); shifted = []
        for n, c in defined.items():
            cp = int(c, 16)
            if cp not in cmap: err.append('bi-%s: kode %s tidak ada di font tertanam' % (n, c)); continue
            g = cmap[cp]; bp = BoundsPen(gs); gs[g].draw(bp)
            if bp.bounds is None: err.append('bi-%s: glyph kosong (tanpa gambar)' % n); continue
            gl = f['glyf'][g]
            if abs(getattr(gl, 'xMin', 0) - f['hmtx'][g][1]) > 1: shifted.append(n)
        if shifted: err.append('%d ikon akan tampak bergeser ke kiri (xMin kotak glyph != lsb), mis. %s -> bangun ulang subset dengan build_libs.py --icons-only' % (len(shifted), ', '.join(shifted[:5])))
    except ImportError:
        warn.append('fontTools belum terpasang: pemeriksaan font dilewati (pip install fonttools brotli)')
    # ---- 4) ikon aplikasi
    if app:
        try:
            from PIL import Image
            man = json.load(open(os.path.join(app, 'manifest.webmanifest'), encoding='utf-8'))
            for ic in man.get('icons', []):
                p = os.path.join(app, ic['src'])
                if not os.path.exists(p): err.append('manifest: %s tidak ada' % ic['src']); continue
                im = Image.open(p); want = ic['sizes']
                if '%dx%d' % im.size != want: err.append('manifest: %s berukuran %dx%d, seharusnya %s' % (ic['src'], im.width, im.height, want))
                if ic.get('purpose') == 'maskable':
                    im = im.convert('RGB'); w = im.width; px = im.load(); far = 0
                    for y in range(0, w, 2):
                        for x in range(0, w, 2):
                            r, g, b = px[x, y]
                            if not (r > 245 and g > 245 and b > 245): far = max(far, math.hypot(x - w / 2, y - w / 2) / w)
                    if far > 0.40: err.append('%s: isi ikon menjangkau %.1f%% dari pusat (batas aman 40%%), bisa terpotong pada ikon bulat' % (ic['src'], far * 100))
            for fn in ('favicon.png', 'apple-touch-icon.png'):
                if not os.path.exists(os.path.join(app, fn)): err.append('%s tidak ada' % fn)
        except ImportError:
            warn.append('Pillow belum terpasang: pemeriksaan ikon aplikasi dilewati (pip install pillow)')
    return err, warn, len(defined), len(used)

if __name__ == '__main__':
    clasp = sys.argv[1]; app = sys.argv[2] if len(sys.argv) > 2 else None
    err, warn, nd, nu = audit(clasp, app)
    print('Ikon di subset: %d | ikon dipakai: %d' % (nd, nu))
    for w in warn: print('CATATAN :', w)
    for e in err: print('MASALAH :', e)
    print('HASIL   :', 'BERSIH' if not err else '%d MASALAH' % len(err)); sys.exit(1 if err else 0)
