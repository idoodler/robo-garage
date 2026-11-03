# Import SES, clean up, GND zones + fill, stitch single-pad pour islands, self-check, save, DRC summary
import os
import shutil
import sys

import pcbnew

import checks
import parts
import post
import route
import ses

base = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'robo-garage', 'robo-garage'))
b = pcbnew.LoadBoard(base + '.kicad_pcb')   # has the locked pre-routes; SES adds the rest
print('imported wires/vias', ses.import_ses(b, base + '.ses'))
post.remove_dangling(b)                      # redundant router stubs (KiCad: track_dangling)
post.remove_redundant(b, parts.CHAMBER)      # duplicate router jogs at the SHT40 (no pour there)
post.set_solid(b, getattr(parts, 'SOLID_PADS', []))
route.add_zones(b)                           # GND both layers + NOPOUR areas, filled
post.stitch_grid(b, pitch=8.0)              # tie both GND pours together every ~8 mm
post.refill(b)
for _ in range(3):                           # KiCad 8+ ignore spokes into single-connection islands
    if not post.stitch_islands(b):
        break
    post.refill(b)
post.remove_dangling(b)
isl = checks.islands(b)
t7, t9 = checks.thermals_exact(b, 7, isl=isl), checks.thermals_exact(b, 9, isl=isl)
for _ in range(2):                           # v1.2: hand spokes for pads the router boxed in
    if not (t7 or t9):
        break
    if not post.fix_starved(b, t7 + t9, isl=isl):
        break
    post.refill(b)
    post.remove_dangling(b)
    isl = checks.islands(b)
    t7, t9 = checks.thermals_exact(b, 7, isl=isl), checks.thermals_exact(b, 9, isl=isl)
silk = checks.silk_edge(b)
print('self-check: thermals KiCad7 %s | KiCad9 %s | silk-edge %d' % ([t[:4] for t in t7], [t[:4] for t in t9], len(silk)))
out = base + '_routed.kicad_pcb'
pcbnew.SaveBoard(out, b)
shutil.copy(base + '.kicad_pro', out.replace('.kicad_pcb', '.kicad_pro'))
summ, unc, txt = route.drc(out, base + '_drc.rpt')
print('DRC', summ, 'unconnected', unc)
if t7 or t9 or silk or summ or unc:
    sys.exit(1)
