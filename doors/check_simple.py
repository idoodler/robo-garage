#!/usr/bin/env python3
"""Check the simple door types: lift door (lift-door.scad) and flap out (flap.scad).
Lift door: printed parts do not touch each other or the panel over the whole lift, saddle clear of the drawer front.
Flap: actuator stroke, lever arm and holding force over the swing, lever + flap clear of the drawer front.
Usage: python3 check_simple.py"""
import math, os, sys
import numpy as np
from shapely.geometry import box, Polygon, LineString, Point
from shapely import affinity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checklib import HERE, scad_echo, render, slices

ok, report = True, []
def fail(m):
    global ok; ok = False; report.append(m)

# ---------------- lift door
SC = os.path.join(HERE, 'lift-door.scad'); G = scad_echo(SC)
ws = np.round(np.arange(0.25, 60, 0.5), 2)
body = {k: slices(render(SC, 'w_' + k), ws) for k in ('channel', 'saddle', 'foot', 'clamp')}
lift = G['stroke'] - (G['seat_y'] - G['tip_y'])                  # panel travel: stroke minus the 3 mm air at the cup
panel = box(G['door_x'][0], G['door_y'][0], G['door_x'][1], G['door_y'][1])
vedd = box(-19, 225, -3, 700)
worst = {'saddle-channel': 1e9, 'saddle-clamp': 1e9, 'saddle-foot': 1e9, 'clamp-channel': 1e9, 'foot-channel': 1e9, 'saddle-drawer front': 1e9, 'panel-clamp': 1e9, 'panel-foot': 1e9}
for L in np.linspace(0, lift, 31):
    for w in ws:
        sd = affinity.translate(body['saddle'][w], 0, L)
        pn = affinity.translate(panel, 0, L) if w >= 3 else None              # panel edge 3 mm from the cheek
        for k in ('channel', 'clamp', 'foot'):
            g = body[k][w]
            if not sd.is_empty and not g.is_empty: worst['saddle-' + k] = min(worst['saddle-' + k], sd.distance(g))
            if pn is not None and k != 'channel' and not g.is_empty: worst['panel-' + k] = min(worst['panel-' + k], pn.distance(g))
        if not sd.is_empty: worst['saddle-drawer front'] = min(worst['saddle-drawer front'], sd.distance(vedd))
        for k in ('clamp', 'foot'):
            a, b = body[k][w], body['channel'][w]
            if not a.is_empty and not b.is_empty: worst[k + '-channel'] = min(worst[k + '-channel'], a.distance(b))
print(f'--- lift door: panel rises {lift:.0f} mm (opening {G["door_y"][0] + lift - 15:.0f} mm above the tray)')
print('  gaps (mm): ' + ', '.join(f'{k} {v:.1f}' if v < 1e8 else f'{k} apart' for k, v in worst.items()))
for k, v in worst.items():
    if v < (0.3 if k in ('clamp-channel', 'foot-channel') else 1.0): fail(f'lift door: {k} {v:.1f} mm')
if G['door_y'][0] + lift - 15 < 125: fail('lift door: opening too low for the robot')

# ---------------- flap
SC = os.path.join(HERE, 'flap.scad'); G = scad_echo(SC)
H, PIN, F = (np.array(G[k], float) for k in ('H', 'PIN', 'F'))
def rot(p, a):                                       # clockwise about the hinge (flap opening)
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); q = np.array(p) - H
    return H + np.array([c * q[0] + s * q[1], -s * q[0] + c * q[1]])
l0, l1 = np.linalg.norm(F - rot(PIN, 0)), np.linalg.norm(F - rot(PIN, 90))
W, cg = 17.2, np.array([-9.5, 224 - 103.5])          # flap 596 x 207 x 19 MDF
arms, forces = [], []
for a in np.linspace(0, 90, 91):
    p = rot(PIN, a); u = (F - p) / np.linalg.norm(F - p); r = p - H
    arm = abs(r[0] * u[1] - r[1] * u[0]); arms.append(arm)
    g = rot(cg, a) - H; forces.append(W * abs(g[0]) / arm)
lv = slices(render(SC, 'w_lever'), [G['lv_w'][0] + 6])[G['lv_w'][0] + 6]
flap = box(-19, 17, 0, 224)
dl = min(affinity.rotate(lv, -a, origin=tuple(H)).distance(vedd) for a in np.linspace(0, 90, 46))
df = min(affinity.rotate(flap, -a, origin=tuple(H)).distance(vedd) for a in np.linspace(0.5, 90, 46))
mt = render(SC, 'w_mount'); lo, hi = mt.bounds
print(f'--- flap: actuator {l0:.1f} -> {l1:.1f} mm (stroke {l1 - l0:.1f}), lever arm {min(arms):.0f}..{max(arms):.0f} mm, '
      f'holding force max {max(forces):.0f} N; lever {dl:.1f} mm and flap {df:.1f} mm from the drawer front; mount X {lo[0]:.0f}..{hi[0]:.0f} Y {lo[1]:.0f}..{hi[1]:.0f}')
if abs(l1 - l0 - G['stroke']) > 1: fail('flap: stroke mismatch')
if min(arms) < 50: fail('flap: lever arm below 50 mm')
if max(forces) > 35: fail('flap: holding force above 35 N')
if dl < 2 or df < 0.5: fail('flap: touches the drawer front')
if lo[0] < 2 or hi[1] > 578: fail('flap: mount off the cheek or into the top rail')
print('RESULT:', 'OK' if ok else 'PROBLEMS\n  ' + '\n  '.join(report))
sys.exit(0 if ok else 1)
