# JLCPCB outputs: gerbers + drill zip, BOM (LCSC), CPL (with rotation fixes), renders
import csv
import os
import re
import shutil
import subprocess
import sys
import zipfile

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import parts

PCB = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
G = os.path.join(OUT, 'gerbers')
shutil.rmtree(G, ignore_errors=True)
os.makedirs(G)

LAYERS = 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'
subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '--layers', LAYERS, '--subtract-soldermask',
                '--no-x2', '-o', G + '/', PCB], check=True, capture_output=True)
subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-units', 'mm',
                '--excellon-separate-th', '--excellon-oval-format', 'alternate', '-o', G + '/', PCB],
               check=True, capture_output=True)
zp = os.path.join(OUT, 'robo-garage_gerbers_JLCPCB.zip')
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(G)):
        z.write(os.path.join(G, f), f)
print('gerber files:', sorted(os.listdir(G)))

# ---------- BOM + CPL ----------
b = pcbnew.LoadBoard(PCB)
# KiCad -> JLCPCB rotation offsets, checked against JLC's DFM preview of order SMT026110160950 (Nov 2026):
# 3-pin SOT-23 needs +180, SOT-23-5/6/8 and TSOT-23-6 need 0 (v1.1.1 had them at +180: U2/U4 came out
# rotated), SOIC / PowerPAD +270, electrolytics +180. Everything else 0; check pin1-check.png in the preview.
ROT = [(r'^SOT-23$', 180), (r'^(SOIC-|TI_SO-PowerPAD|TI_PWP)', 270), (r'^CP_Elec_', 180)]
# v1.3: the DRV8874 HTSSOP-16 (TI_PWP0016J) follows the SOIC rule (JLC/EasyEDA: pin 1 bottom-left, rows horizontal);
# SOT-23-6 (Q6 TSOP-6) like SOT-23-5 = 0. New footprints: verify in JLC's DFM preview / pin1-check.png.


def jlc_rot(fpname, rot):
    for pat, off in ROT:
        if re.match(pat, fpname):
            return (rot + off) % 360
    return rot % 360


bom, cpl = {}, []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    p = parts.P[ref]
    if p.get('nobom') or p.get('dnp'):
        continue
    # one BOM line per LCSC part (JLC warns when several lines match the same part), else per value/footprint
    key = (p['lcsc'], p['fp']) if p.get('lcsc') else (p['val'], p['fp'], p.get('mpn') or '')
    bom.setdefault(key, []).append(ref)
    if p.get('tht'):
        pins = [pad for pad in fp.Pads() if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]   # not the J6 latch hole
        xs = [pcbnew.ToMM(pad.GetPosition().x) for pad in pins]
        ys = [pcbnew.ToMM(pad.GetPosition().y) for pad in pins]
        x, y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    else:
        x, y = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
    cpl.append([ref, '%.3fmm' % x, '%.3fmm' % (-y), 'Top', '%.1f' % jlc_rot(p['fp'], fp.GetOrientationDegrees())])


def natkey(r):
    m = re.match(r'([A-Z]+)(\d+)', r)
    return (m.group(1), int(m.group(2)))


with open(os.path.join(OUT, 'robo-garage_BOM_JLCPCB.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'MPN', 'Mount'])
    for key, refs in sorted(bom.items(), key=lambda kv: natkey(sorted(kv[1], key=natkey)[0])):
        refs = sorted(refs, key=natkey)
        p0 = parts.P[refs[0]]
        vals = sorted({parts.P[r]['val'] for r in refs})
        mount = 'THT' if p0.get('tht') else 'SMD'
        # Comment: the value; the MPN when the values differ or for THT parts (clamp values are their roles)
        val = vals[0] if len(vals) == 1 and not (mount == 'THT' and p0.get('mpn')) else (p0.get('mpn') or vals[0])
        w.writerow([val, ','.join(refs), p0['fp'], p0.get('lcsc') or '', p0.get('mpn') or '', mount])
with open(os.path.join(OUT, 'robo-garage_CPL_JLCPCB.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for row in sorted(cpl, key=lambda r: natkey(r[0])):
        w.writerow(row)
print('BOM lines', len(bom), 'CPL parts', len(cpl))


# ---------- renders ----------
def render(layers, name, flip=False, bg='#0b3d1e'):
    svg = os.path.join(OUT, name + '.svg')
    png = os.path.join(OUT, name + '.png')
    args = ['kicad-cli', 'pcb', 'export', 'svg', '--layers', layers, '--page-size-mode', '2',
            '--exclude-drawing-sheet', '-o', svg, PCB]
    if flip:
        args.insert(-1, '--mirror')
    subprocess.run(args, check=True, capture_output=True)
    subprocess.run(['rsvg-convert', '-w', '1800'] + (['-b', bg] if bg else []) + ['-o', png, svg], check=True)
    os.remove(svg)
    return png


def render_side(side, name):
    """Copper + Edge.Cuts, then the silk (+ Edge.Cuts, same page box) composited on top: kicad-cli 7 plots
    B.Cu over B.SilkS, which would hide the bottom silkscreen in the picture."""
    from PIL import Image
    flip = side == 'B'
    cu = render('%s.Cu,Edge.Cuts' % side, name, flip)
    sk = render('%s.SilkS,Edge.Cuts' % side, name + '_silk', flip, bg=None)
    a, b = Image.open(cu).convert('RGBA'), Image.open(sk).convert('RGBA')
    if a.size != b.size:
        b = b.resize(a.size)
    Image.alpha_composite(a, b).convert('RGB').save(cu)
    os.remove(sk)
    return cu


top = render_side('F', 'render_top')
print(top)
print(render_side('B', 'render_bottom'))


# ---------- pin-1 check picture (compare with JLCPCB's DFM preview before confirming the order) ----------
def pin1_check(png_in, png_out, refs=r'^(U|Q|D|LED|BZ|J|C1$|C3$|C13$)'):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(png_in).convert('RGB')
    d = ImageDraw.Draw(im)
    bb = b.GetBoundingBox()                                  # = the SVG page with --page-size-mode 2
    x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
    sx = im.width / pcbnew.ToMM(bb.GetWidth())
    sy = im.height / pcbnew.ToMM(bb.GetHeight())
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    except OSError:
        font = ImageFont.load_default()
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if not re.match(refs, ref) or parts.P[ref].get('nobom') or parts.P[ref].get('dnp'):
            continue
        p1 = [pd for pd in fp.Pads() if pd.GetNumber() == '1']
        if not p1:
            continue
        px = (pcbnew.ToMM(p1[0].GetPosition().x) - x0) * sx
        py = (pcbnew.ToMM(p1[0].GetPosition().y) - y0) * sy
        r = max(10, 0.9 * sx * max(pcbnew.ToMM(p1[0].GetSize().x), pcbnew.ToMM(p1[0].GetSize().y)) / 2)
        d.ellipse([px - r, py - r, px + r, py + r], outline=(0, 230, 255), width=3)
        d.text((px + r + 2, py - r - 4), ref, fill=(0, 230, 255), font=font)
    d.text((10, 8), 'cyan ring = pin 1 / + / cathode (compare with the JLCPCB preview)', fill=(255, 255, 255), font=font)
    im.save(png_out)
    return png_out


print(pin1_check(top, os.path.join(OUT, 'pin1-check.png')))
