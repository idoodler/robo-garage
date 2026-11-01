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
ROT = [(r'^(SOT-23|TSOT-23)', 180), (r'^(SOIC-|TI_SO-PowerPAD)', 270), (r'^CP_Elec_', 180)]


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
    key = (p['val'], p['fp'], p.get('lcsc') or '', p.get('mpn') or '')
    bom.setdefault(key, []).append(ref)
    if p.get('tht'):
        xs = [pcbnew.ToMM(pad.GetPosition().x) for pad in fp.Pads()]
        ys = [pcbnew.ToMM(pad.GetPosition().y) for pad in fp.Pads()]
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
    for (val, fpn, lcsc, mpn), refs in sorted(bom.items(), key=lambda kv: natkey(sorted(kv[1], key=natkey)[0])):
        refs = sorted(refs, key=natkey)
        mount = 'THT (hand solder)' if parts.P[refs[0]].get('tht') else 'SMD'
        w.writerow([val, ','.join(refs), fpn, lcsc, mpn, mount])
with open(os.path.join(OUT, 'robo-garage_CPL_JLCPCB.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for row in sorted(cpl, key=lambda r: natkey(r[0])):
        w.writerow(row)
print('BOM lines', len(bom), 'CPL parts', len(cpl))


# ---------- renders ----------
def render(layers, name, flip=False):
    svg = os.path.join(OUT, name + '.svg')
    png = os.path.join(OUT, name + '.png')
    args = ['kicad-cli', 'pcb', 'export', 'svg', '--layers', layers, '--page-size-mode', '2',
            '--exclude-drawing-sheet', '-o', svg, PCB]
    if flip:
        args.insert(-1, '--mirror')
    subprocess.run(args, check=True, capture_output=True)
    subprocess.run(['rsvg-convert', '-w', '1800', '-b', '#0b3d1e' if 'Cu' in layers else 'white', '-o', png, svg],
                   check=True)
    os.remove(svg)
    return png


print(render('F.Cu,F.SilkS,Edge.Cuts', 'render_top'))
print(render('B.Cu,B.SilkS,Edge.Cuts', 'render_bottom', flip=True))
