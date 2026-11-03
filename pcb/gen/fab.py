# JLCPCB outputs: gerbers + drill zip, BOM (LCSC), CPL (with rotation fixes), renders
import csv
import json
import math
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
# v1.3.1: the CPL rotation of every part is computed from JLC's own library footprint (jlc_footprints.json: pads of
# the EasyEDA footprint JLC places with, see the file header). No package rules any more: the old rules were tuned
# on the pictures of JLC's order mail of Nov 2026, but those show the placement after JLC's engineers had already
# corrected it by hand -- they had U2/U3 and C13 the wrong way round. A part that does not fit at any rotation
# stops the build (that is how the single-row KF250 footprint of v1.3 would have been caught).
JLC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jlc_footprints.json')))
TOL = 0.5          # mm pad centre to pad centre (JLC's land patterns differ a little: the 2920 fuse by 0.39)


def rot(x, y, deg):
    """Rotate CCW as seen on the board (y down) -- the sense of KiCad and JLC rotations."""
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def board_pads(fp):
    """The pads JLC sees (front copper with mask opening, plus NPTH peg holes), relative to the centre of the
    numbered pads' bounding box (= JLC's placement origin; for SMD parts also the KiCad origin)."""
    out = []
    for pd in fp.Pads():
        npth = pd.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
        if not npth and not pd.GetLayerSet().Contains(pcbnew.F_Mask):
            continue                                     # B.Cu pads, thermal vias, paste-only windows
        out.append(('NPTH' if npth else pd.GetNumber(), pcbnew.ToMM(pd.GetPosition().x), pcbnew.ToMM(pd.GetPosition().y)))
    real = [q for q in out if q[0] != 'NPTH']
    cx = (min(q[1] for q in real) + max(q[1] for q in real)) / 2
    cy = (min(q[2] for q in real) + max(q[2] for q in real)) / 2
    return [(n, x - cx, y - cy) for n, x, y in out], (cx, cy)


def jlc_rotation(ref, lcsc, fp):
    """JLC rotation (CCW) that puts JLC's footprint onto our pads with the same pin functions; exits if none or if
    a polarised part fits more than one way."""
    j = JLC.get(lcsc)
    if j is None:
        sys.exit('fab: %s (%s) is not in jlc_footprints.json -- add JLC\'s footprint before ordering' % (ref, lcsc))
    ours, centre = board_pads(fp)
    remap = j.get('map', {})
    fits = []
    for phi in (0, 90, 180, 270):
        theirs = [(n,) + rot(x, y, phi) for n, x, y in j['pads']]
        geo = max([min(math.hypot(a[1] - c[1], a[2] - c[2]) for c in ours) for a in theirs] +
                  [min(math.hypot(a[1] - c[1], a[2] - c[2]) for c in theirs) for a in ours])
        fun = 0.0
        if not j.get('np'):
            where = {n: (x, y) for n, x, y in theirs}
            errs = [math.hypot(x - where[remap.get(n, n)][0], y - where[remap.get(n, n)][1])
                    for n, x, y in ours if n and remap.get(n, n) in where]
            fun = max(errs) if errs else 99.0
        fits.append((round(max(geo, fun), 2), phi))
    ok = [phi for e, phi in fits if e < TOL]
    if not ok:
        sys.exit('fab: %s (%s, JLC %s) fits our footprint at no rotation (error mm, rotation): %s' % (ref, lcsc, j['fp'], fits))
    if len(ok) > 1 and not j.get('np'):
        sys.exit('fab: %s (%s) is polarised but fits at %s -- pin functions ambiguous' % (ref, lcsc, ok))
    board_rot = round(fp.GetOrientationDegrees()) % 360
    phi = board_rot if board_rot in ok else ok[0]
    return phi, centre, j


bom, cpl, orient = {}, [], []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    p = parts.P[ref]
    if p.get('nobom') or p.get('dnp'):
        continue
    # one BOM line per LCSC part (JLC warns when several lines match the same part), else per value/footprint
    key = (p['lcsc'], p['fp']) if p.get('lcsc') else (p['val'], p['fp'], p.get('mpn') or '')
    bom.setdefault(key, []).append(ref)
    if not p.get('lcsc'):
        sys.exit('fab: %s is assembled but has no LCSC part' % ref)
    # position: centre of the pads (JLC's origin; = KiCad origin for the SMD parts, not for the zig-zag clamps)
    phi, (x, y), j = jlc_rotation(ref, p['lcsc'], fp)
    cpl.append([ref, '%.3fmm' % x, '%.3fmm' % (-y), 'Top', '%.1f' % phi])
    orient.append((ref, p['lcsc'], j['fp'], round(fp.GetOrientationDegrees()) % 360, phi, (x, y), j))


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
# orientation table (what JLC's preview has to show): polarised / multi-pin parts only
with open(os.path.join(OUT, 'orientation.txt'), 'w') as f:
    f.write('# CPL rotation per part, computed by fab.py from JLC\'s library footprints (jlc_footprints.json)\n')
    f.write('%-5s %-10s %-48s %5s %5s\n' % ('ref', 'LCSC', 'JLC footprint', 'board', 'CPL'))
    for ref, lcsc, name, brot, phi, _, j in sorted(orient, key=lambda o: natkey(o[0])):
        if not j.get('np'):
            f.write('%-5s %-10s %-48s %5d %5d\n' % (ref, lcsc, name, brot, phi))


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
    where = {o[0]: o for o in orient}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if not re.match(refs, ref) or ref not in where:
            continue
        p1 = [pd for pd in fp.Pads() if pd.GetNumber() == '1']
        if not p1:
            continue
        px = (pcbnew.ToMM(p1[0].GetPosition().x) - x0) * sx
        py = (pcbnew.ToMM(p1[0].GetPosition().y) - y0) * sy
        r = max(10, 0.9 * sx * max(pcbnew.ToMM(p1[0].GetSize().x), pcbnew.ToMM(p1[0].GetSize().y)) / 2)
        d.ellipse([px - r, py - r, px + r, py + r], outline=(0, 230, 255), width=3)
        d.text((px + r + 2, py - r - 4), ref, fill=(0, 230, 255), font=font)
        # where JLC puts its pin 1 / + / cathode: its footprint pad (mapped from our pad 1), turned by the CPL rotation
        _, _, _, _, phi, (cx, cy), j = where[ref]
        n1 = j.get('map', {}).get('1', '1')
        jp = [q for q in j['pads'] if q[0] == n1]
        if jp:
            jx, jy = rot(jp[0][1], jp[0][2], phi)
            mx, my = (cx + jx - x0) * sx, (cy + jy - y0) * sy
            d.ellipse([mx - 5, my - 5, mx + 5, my + 5], fill=(255, 0, 220))
    d.text((10, 8), 'cyan ring = our pin 1 / + / cathode, magenta dot = JLC\'s (from its footprint + CPL rotation): '
           'must sit inside the ring, here and in JLC\'s preview', fill=(255, 255, 255), font=font)
    im.save(png_out)
    return png_out


print(pin1_check(top, os.path.join(OUT, 'pin1-check.png')))
