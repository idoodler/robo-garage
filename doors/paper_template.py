#!/usr/bin/env python3
"""Paper drill template for the parallel lift: parallel_template.pdf, A4, 1:1, page 1 right cheek, page 2 left cheek.

Both pages show the cheek's inner face as seen from the robot bay. Cut along the two cut lines, put the front cut edge against the
back of the front leg and the bottom cut edge on the tray, tape it on and pre-drill through the crosses. Hole positions come from
parallel-lift.scad (SCREWS, P1), so the paper always matches the modules.
Usage: python3 paper_template.py        Needs: openscad, python3 with matplotlib, trimesh, shapely, numpy.
"""
import os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checklib import HERE, scad_echo, render, slices

SCAD = os.path.join(HERE, 'parallel-lift.scad')
OUT = os.path.join(HERE, 'parallel_template.pdf')
A4 = (210.0, 297.0)                       # mm
TRAY = 15.0                               # tray top above the floor (frame Y)
X_MAX, Y_MAX = 132.0, 236.0               # template area: front edge .. 132 mm back, tray .. 236 mm above the floor
OY = 40.0                                 # paper Y of the tray line
INK, FAINT, CUT = '#000000', '#9a9a9a', '#000000'


def page(pdf, G, side, outline):
    right = side == 'right'
    ox = 172.0 if right else 38.0         # paper X of the front edge: seen from the bay the right cheek's front is on the right
    sx = -1.0 if right else 1.0
    P = lambda x, y: (ox + sx * x, OY + (y - TRAY))
    fig = plt.figure(figsize=(A4[0] / 25.4, A4[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, A4[0]); ax.set_ylim(0, A4[1]); ax.set_aspect('equal'); ax.axis('off')
    T = lambda x, y, s, **k: ax.text(x, y, s, fontsize=k.pop('fs', 8), color=k.pop('c', INK), **k)

    # module outline (faint): where the plate will sit, seen from the bay
    for poly in outline:
        for ring in [poly.exterior, *poly.interiors]:
            xs, ys = zip(*[P(x, y) for x, y in ring.coords]); ax.plot(xs, ys, color=FAINT, lw=0.4)
    # cut lines: front edge (against the back of the front leg) and bottom edge (on the tray)
    (fx0, fy0), (fx1, fy1) = P(0, TRAY), P(0, Y_MAX)
    ax.plot([fx0, fx1], [fy0, fy1], color=CUT, lw=0.6, ls=(0, (6, 3)))
    (bx0, by0), (bx1, by1) = P(0, TRAY), P(X_MAX, TRAY)
    ax.plot([bx0, bx1], [by0, by1], color=CUT, lw=0.6, ls=(0, (6, 3)))
    T(fx0 + (4 if right else -4), (fy0 + fy1) / 2, 'CUT  ✂   front edge: against the back of the front leg', fs=8,
      rotation=90, ha='left' if right else 'right', va='center')
    T((bx0 + bx1) / 2, by0 - 4, 'CUT  ✂   bottom edge: on the tray', ha='center', va='top')
    # screw holes: cross, 3 mm pilot circle, distances for a check with a ruler
    for i, (x, y) in enumerate(G['SCREWS']):
        cx, cy = P(x, y)
        ax.plot([cx - 8, cx + 8], [cy, cy], color=INK, lw=0.5); ax.plot([cx, cx], [cy - 8, cy + 8], color=INK, lw=0.5)
        ax.add_patch(plt.Circle((cx, cy), 1.5, fill=False, color=INK, lw=0.6))
        T(cx + 3, cy + 2.5, f'{x:.0f} back · {y - TRAY:.0f} up', fs=7)
    # front pivot P1: a check only, nothing to drill
    cx, cy = P(*G['P1'])
    ax.plot([cx - 5, cx + 5], [cy, cy], color=INK, lw=0.4, ls=':'); ax.plot([cx, cx], [cy - 5, cy + 5], color=INK, lw=0.4, ls=':')
    T(cx + 3, cy - 5, 'front pivot P1 (check only, do not drill)', fs=6.5)
    # scale check: 100 mm in both directions, in the part that gets cut off
    sx0, sy0 = 55.0, 18.0
    ax.plot([sx0, sx0 + 100], [sy0, sy0], color=INK, lw=0.8)
    for k in range(11): ax.plot([sx0 + 10 * k] * 2, [sy0, sy0 + (3 if k % 5 else 5)], color=INK, lw=0.5)
    T(sx0 + 50, sy0 - 2.5, '100 mm', ha='center', va='top', fs=7)
    vx = 196.0 if right else 14.0
    ax.plot([vx, vx], [80, 180], color=INK, lw=0.8)
    for k in range(11): ax.plot([vx, vx + (-1 if right else 1) * (3 if k % 5 else 5)], [80 + 10 * k] * 2, color=INK, lw=0.5)
    T(vx + (-7 if right else 7), 130, '100 mm', rotation=90, ha='center', va='center', fs=7)
    # title and how to use it
    T(105, 286, f'Robo-Garage parallel lift v{G["version"]}: drill template, {side.upper()} cheek', ha='center', fs=12, weight='bold')
    T(105, 279, 'Seen from the robot bay. Print on A4 at 100 % ("actual size", not "fit to page"): both bars must measure 100 mm.',
      ha='center', fs=7.5)
    T(105, 274, f'Cut along both cut lines, tape it on, pre-drill the {len(G["SCREWS"])} crosses with 3 mm for 4 × 20 countersunk screws.'
      + ('' if right else ' Page 1 is the right cheek.') + (' Page 2 is the left cheek.' if right else ''), ha='center', fs=7.5)
    T(105, 8, 'Hole positions from parallel-lift.scad (SCREWS); "back" = mm behind the front edge, "up" = mm above the tray.',
      ha='center', fs=6, c=FAINT)
    pdf.savefig(fig); plt.close(fig)


def main():
    G = scad_echo(SCAD)
    with PdfPages(OUT, metadata={'Title': f'Robo-Garage parallel lift v{G["version"]} drill template', 'Creator': 'paper_template.py'}) as pdf:
        for side, part in (('right', 'plate_r'), ('left', 'plate_l')):
            z = G['z_top'] - 0.5                                    # the plate's outline next to the cheek face
            g = slices(render(SCAD, part), [z])[z]
            page(pdf, G, side, list(g.geoms) if hasattr(g, 'geoms') else [g])
    print(os.path.basename(OUT), '2 pages, A4')


if __name__ == '__main__':
    main()
