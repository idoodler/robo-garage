# Route with Freerouting: board -> DSN -> freerouting -> SES -> board, then GND zones + fill + DRC report
import os
import re
import subprocess
import sys
import time

import pcbnew

MM = pcbnew.FromMM
FR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools', 'freerouting.jar'))


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def export_dsn(pcb_path, dsn):
    b = pcbnew.LoadBoard(pcb_path)
    ok = pcbnew.ExportSpecctraDSN(b, dsn)
    if not ok:
        raise SystemExit('DSN export failed')
    return b


def run_freerouting(dsn, ses, passes=40, timeout=1500):
    t0 = time.time()
    cmd = ['java', '-Djava.awt.headless=true', '-jar', FR, '-de', dsn, '-do', ses, '-mp', str(passes),
           '--gui.enabled=false', '-mt', '1']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    log = (r.stdout + r.stderr)
    lines = [l for l in log.splitlines() if 'JAVA_TOOL' not in l]
    print('\n'.join(lines[-12:]))
    print('freerouting %.0f s, exit %d' % (time.time() - t0, r.returncode))
    if not os.path.exists(ses):
        raise SystemExit('no SES written')


def add_zones(board, inset=0.3):
    gnd_code = board.GetNetcodeFromNetname('GND')
    import parts
    x0, y0, x1, y1 = 0.0, 0.0, parts.W, parts.H
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNetCode(gnd_code)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0 + inset, y0 + inset), (x1 - inset, y0 + inset), (x1 - inset, y1 - inset), (x0 + inset, y1 - inset)):
            ol.Append(MM(x), MM(y))
        z.SetLocalClearance(MM(0.3))
        z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.4))
        z.SetThermalReliefSpokeWidth(MM(0.6))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(0)
        board.Add(z)
    import build
    for rect in getattr(parts, 'NOPOUR', []):      # e.g. the SHT40 chamber: no copper pour there
        build.rule_area(board, rect, False)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def drc(pcb_path, report):
    b = pcbnew.LoadBoard(pcb_path)
    pcbnew.WriteDRCReport(b, report, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(report).read()
    errs = re.findall(r'^\[(\w+)\]: (.*)$', txt, flags=re.M)
    summ = {}
    for k, _ in errs:
        summ[k] = summ.get(k, 0) + 1
    m = re.search(r'\*\* Found (\d+) unconnected pads', txt)
    return summ, (int(m.group(1)) if m else None), txt


if __name__ == '__main__':
    pcb = sys.argv[1]
    base = pcb[:-10]
    dsn, ses = base + '.dsn', base + '.ses'
    passes = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    export_dsn(pcb, dsn)
    run_freerouting(dsn, ses, passes)
    b = pcbnew.LoadBoard(pcb)
    if not pcbnew.ImportSpecctraSES(b, ses):
        raise SystemExit('SES import failed')
    add_zones(b)
    out = base + '_routed.kicad_pcb'
    pcbnew.SaveBoard(out, b)
    import shutil
    shutil.copy(base + '.kicad_pro', out.replace('.kicad_pcb', '.kicad_pro'))
    summ, unc, _ = drc(out, base + '_drc.rpt')
    print('DRC', summ, 'unconnected', unc)
