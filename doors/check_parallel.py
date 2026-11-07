#!/usr/bin/env python3
"""Check the print-in-place parallel lift (parallel-lift.scad).

Renders every body with OpenSCAD, slices it every 0.2 mm and moves the slices through the whole door travel
(f = 0 closed .. 1 open, 1 % steps). Reports per pair of parts the smallest gap in the joints and elsewhere,
the door path against the drawer front, the cabinet obstacles, the actuator, screw access, print overhangs and
the bed footprint at the print pose.
Usage: python3 check_parallel.py [--quick] [cj=0.45] [cs=1.0] [gz=0.6]
"""
import math, os, sys
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checklib import HERE, defs_from_argv, scad_echo, render, slices, layer_zs, overhangs, screw_walls, footprint, fmt_gap

SCAD = os.path.join(HERE, 'parallel-lift.scad')
QUICK = '--quick' in sys.argv
DEFS = defs_from_argv()
G = scad_echo(SCAD, DEFS)
P1, P2, A1, A2, F = (np.array(G[k], float) for k in ('P1', 'P2', 'A1', 'A2', 'F'))
R, TH0, SW, LEV, LEV_A = (float(G[k]) for k in ('R', 'TH0', 'SWING', 'LEV', 'LEV_A'))
CJ, CS, GZ, Z_TOP, Z_MOV = (float(G[k]) for k in ('cj', 'cs', 'gz', 'z_top', 'z_mov'))
d = lambda a: np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
T = lambda f: R * (d(TH0 - SW * f) - d(TH0))
C = lambda f: P1 + LEV * d(LEV_A - SW * f)

DOOR = affinity.translate(Polygon([(-19, 17), (0, 17), (0, 203), (-18, 221), (-19, 221)]), 0, G['door_up'])   # door section, 45 deg back chamfer, 1 mm flat
VEDD = box(-19, 225, -3, 700)                                                # drawer front (VEDDINGE)
WHEEL = box(55, 0, 85, 30)                                                   # drawer wheel, Z 9..19 in the module frame
Z_ACT = -(G['act_gap'] + 4)                                                  # actuator plane: spacer + half an 8 mm eye


def door_loaded(f, g):
    """Door pose with the joint play of radial gap g taken up by its weight: (polygon, lean in deg, + = top outwards). Both sides averaged:
    the door is stiff. Each pin sits g off its ring centre, against the force. The rear arm only pushes; the front arm also carries shear."""
    u, t = d(TH0 - SW * f), T(f)
    a1, a2, cg = A1 + t, A2 + t, np.array([-9.5, 119.0]) + t
    w = np.array([0, -0.5 * 1.48 * 9.81])
    cr = lambda a, b: a[0] * b[1] - a[1] * b[0]
    un = lambda v: v / np.linalg.norm(v)
    sa = -cr(cg - a1, w) / cr(a2 - a1, u)                    # force on the bracket from the rear arm = sa * u
    f1 = -w - sa * u                                         # ... and from the front arm
    pose = []
    for lev in (True, False):
        gg = f1
        if lev:                                              # left front arm: the actuator holds both sides via the rod
            c = C(f); ua = un(F - c)
            gg = f1 - (-2 * cr(a1 - P1, -f1) / cr(c - P1, ua)) * ua
        p1 = P1 - g * un(gg) + R * u - g * un(f1)            # bracket pin A1
        r2 = R - 2 * g * np.sign(sa)                         # rear arm: effective length
        dv = P2 - p1; dd = np.linalg.norm(dv)                # bracket pin A2: BASE from A1, r2 from P2
        aa = (G['BASE'] ** 2 - r2 ** 2 + dd ** 2) / (2 * dd); hh = math.sqrt(max(G['BASE'] ** 2 - aa ** 2, 0))
        e = dv / dd; n = np.array([-e[1], e[0]])
        p2 = min((p1 + aa * e + hh * n, p1 + aa * e - hh * n), key=lambda q: np.linalg.norm(q - a2))
        pose.append((math.degrees(math.atan2((p1 - p2)[1], (p1 - p2)[0])) - G['BDIR'], (p1 + p2) / 2))
    a = (pose[0][0] + pose[1][0]) / 2 - float(G['lean'])
    mid, nom = (pose[0][1] + pose[1][1]) / 2, (A1 + A2) / 2
    # the door lies on the wedged flange: its bottom back corner on the flange's bottom corner, then door + bracket turn together
    y0 = 17 + G['door_up']; lean = float(G['lean'])
    door = affinity.rotate(affinity.translate(DOOR, 0, 0), -lean, origin=(0, y0))
    door = affinity.translate(door, math.tan(math.radians(lean)) * (y0 - G['y_mid']), 0)
    return affinity.translate(affinity.rotate(door, a + lean, origin=tuple(nom)), *(mid - nom)), a


def place(g, kind, f, pivot=None):
    if kind == 'fix': return g
    if kind == 'rot': return affinity.rotate(g, -SW * f, origin=tuple(pivot))
    t = T(f); return affinity.translate(g, t[0], t[1])


def main():
    layers, zs = layer_zs(Z_TOP, [5.95, 6.05, 6.3, 6.55, 6.65])
    fs = np.linspace(0, 1, 21 if QUICK else 101)
    report, ok = [], True
    def fail(msg):
        nonlocal ok; report.append(msg); ok = False

    # ---- door path (2D) ----
    dv = min(affinity.translate(DOOR, *T(f)).distance(VEDD) for f in np.linspace(0, 1, 401))
    outs = [-T(f)[0] for f in np.linspace(0, 1, 401)]
    t1 = T(1)
    print(f'--- door, all joints centred: out max {max(outs):.1f} mm, parked {-t1[0]:.1f} mm out / {t1[1]:.1f} mm up '
          f'(bottom edge {17 + t1[1]:.0f} mm above the floor), gap to the drawer front: min {dv:.1f}, parked {-t1[0] - 19:.1f} mm')
    # no limit here: with its weight on the joints the door never sits like this; the loaded case below is the real test
    if min(T(f)[1] for f in fs) < -0.5: fail('door goes down when opening')
    if max(T(f)[0] for f in fs) > 0.01: fail('door moves into the cabinet')

    # ---- door under gravity: its weight takes up all joint play, which tilts the bracket. Solved from the joint forces, as the
    # front arm's load turns from axial to mostly shear over the travel. Real gaps vary, so test the set gap and 0.1 mm either side.
    print(f'--- door with joint play taken up by its weight (flange wedge {G["lean"]:.2f} deg):')
    for g in (CJ - 0.1, CJ, CJ + 0.1):
        res = [door_loaded(f, g) for f in np.linspace(0, 1, 201)]
        worst = min(dr.distance(VEDD) for dr, _ in res)
        tray = min(dr.bounds[1] for dr, _ in res) - 15
        a0, a1 = res[0][1], res[-1][1]
        print(f'    gap {g:.2f}: lean closed {a0:+.2f}, parked {a1:+.2f} deg; door top {math.radians(a0) * (221 - G["y_mid"]):.1f} mm out when closed; '
              f'gap to the drawer front {worst:.1f} mm (parked {res[-1][0].distance(VEDD):.1f}), to the tray {tray:.1f} mm')
        if worst < 1.0: fail(f'door within {worst:.1f} mm of the drawer front at joint gap {g:.2f}')
        if tray < 1.0: fail(f'door within {tray:.1f} mm of the tray at joint gap {g:.2f}')

    n = len(render(SCAD, 'coupon', DEFS).split(only_watertight=False))
    print(f'--- coupon: {n} separate bodies, 2 per joint')
    if n != 8: fail(f'coupon has {n} bodies, not 8: a joint is fused')

    for side in ('left', 'right'):
        lev = side == 'left'
        bodies = {'plate': ('plate_l' if lev else 'plate_r', 'fix', None),
                  'arm1': ('arm1_l' if lev else 'arm1_r', 'rot', P1),
                  'arm2': ('arm2', 'rot', P2),
                  'bracket': ('bracket', 'move', None)}
        meshes, sl = {}, {}
        for k, (p, kind, piv) in bodies.items():
            m = render(SCAD, p, DEFS); meshes[k] = m
            if not m.is_watertight: fail(f'{side} {k}: mesh not watertight')
            if len(m.split(only_watertight=False)) != 1: fail(f'{side} {k}: not one connected body')
            sl[k] = slices(m, zs)
        print(f'--- {side} module ---')
        for k, m in meshes.items():
            lo, hi = m.bounds
            print(f'  {k:8s} volume {m.volume / 1000:6.1f} cm3  X {lo[0]:6.1f}..{hi[0]:6.1f}  Y {lo[1]:6.1f}..{hi[1]:6.1f}  Z {lo[2]:4.1f}..{hi[2]:4.1f}')
        for k in ('arm1', 'arm2', 'bracket'):
            if meshes[k].bounds[1][2] > Z_MOV + 1e-3: fail(f'{side} {k}: above Z {Z_MOV} (door edge)')
        if meshes['plate'].bounds[1][2] > Z_TOP + 1e-3: fail(f'{side} plate thicker than {Z_TOP}')

        pairs = [('plate', 'arm1'), ('plate', 'arm2'), ('plate', 'bracket'), ('arm1', 'arm2'), ('arm1', 'bracket'), ('arm2', 'bracket')]
        best = {pr: [(1e9, None), (1e9, None)] for pr in pairs}     # [joint zone, elsewhere]
        env = {'tray': 1e9, 'wheel': 1e9, 'drawer front': 1e9, 'door (arms)': 1e9}
        for f in fs:
            placed = {k: {z: place(sl[k][z], bodies[k][1], f, bodies[k][2]) for z in zs} for k in bodies}
            t = T(f)
            jc = {('plate', 'arm1'): (P1, G['rRP1']), ('plate', 'arm2'): (P2, G['rRP2']),
                  ('arm1', 'bracket'): (A1 + t, G['rRA']), ('arm2', 'bracket'): (A2 + t, G['rRA'])}
            door = affinity.translate(DOOR, t[0], t[1])
            for z in zs:
                for a, b in pairs:
                    ga, gb = placed[a][z], placed[b][z]
                    if ga.is_empty or gb.is_empty: continue
                    if (a, b) in jc:
                        c, rz = jc[(a, b)]
                        zone = Point(*c).buffer(rz + 0.6)
                        ia, ib = ga.intersection(zone), gb.intersection(zone)
                        if not ia.is_empty and not ib.is_empty:
                            dd = ia.distance(ib)
                            if dd < best[(a, b)][0][0]: best[(a, b)][0] = (dd, (round(float(f), 2), z))
                        oa, ob = ga.difference(zone), gb.difference(zone)
                        if not oa.is_empty and not ob.is_empty:
                            dd = oa.distance(ob)
                            if dd < best[(a, b)][1][0]: best[(a, b)][1] = (dd, (round(float(f), 2), z))
                    else:
                        dd = ga.distance(gb)
                        if dd < best[(a, b)][1][0]: best[(a, b)][1] = (dd, (round(float(f), 2), z))
                for k in ('arm1', 'arm2', 'bracket'):
                    g = placed[k][z]
                    if g.is_empty: continue
                    env['tray'] = min(env['tray'], g.bounds[1] - 15)
                    if 9 <= z <= 19: env['wheel'] = min(env['wheel'], g.distance(WHEEL))
                    env['drawer front'] = min(env['drawer front'], g.distance(VEDD))
                    if k != 'bracket': env['door (arms)'] = min(env['door (arms)'], g.distance(door))
        pg = unary_union([sl['plate'][z] for z in zs])
        env['plate behind door'] = pg.bounds[0]
        env['plate above tray'] = pg.bounds[1] - 15
        print('  gaps (mm)           joint  where (f, Z)        elsewhere  where (f, Z)')
        for pr in pairs:
            (dj, wj), (de, we) = best[pr]
            js = f'{fmt_gap(dj)}  {str(wj):18s}' if dj < 1e8 else '     -' + ' ' * 20
            print(f'  {pr[0]:8s}-{pr[1]:8s} {js} {fmt_gap(de)}   {we}')
            if dj < 1e8 and dj < CJ - 0.06: fail(f'{side} {pr}: joint gap {dj:.2f} < {CJ}')
            if de < CS - 0.06: fail(f'{side} {pr}: gap {de:.2f} < {CS} at {we}')
        print('  obstacles (mm):', ', '.join(f'{k} {v:.1f}' for k, v in env.items()))
        lim = {'tray': 1.5, 'wheel': 2, 'drawer front': 2, 'door (arms)': 1, 'plate behind door': 1.9, 'plate above tray': 0.4}
        for k, v in env.items():
            if v < lim[k]: fail(f'{side}: {k} margin {v:.1f}')

        # wall plate screws: >= 1.5 mm plastic around the counterbore over its full depth
        rcb = (2 * G['wall_screw'] + 0.6) / 2
        for s, worst in screw_walls(sl['plate'], G['SCREWS'], rcb, Z_TOP - 7.5):
            if worst > 0.5: fail(f'{side} wall screw {s} too close to an edge ({worst:.1f} mm2 missing)')
        print(f'  wall screws {G["SCREWS"]}: walls ok' if all(w <= 0.5 for _, w in screw_walls(sl['plate'], G['SCREWS'], rcb, Z_TOP - 7.5)) else '  wall screws: see problems')

        # door screws: driver from the robot bay at 45 deg must reach the head at every door position
        a = math.radians(G['dsb']); u_out = np.array([math.cos(a), -math.sin(a)])      # (X, Z) from the door towards the head
        sh = G['dze'] / math.sin(a) - 1
        worst = 1e9
        for ys in G['YSC']:
            for f in fs[::5]:
                t = T(f)
                for k in ('plate', 'arm1', 'arm2'):
                    for z in zs:
                        if z > 8: continue
                        g = place(sl[k][z], bodies[k][1], f, bodies[k][2])
                        if g.is_empty: continue
                        reg = []
                        for tt in np.linspace(0, 14, 15):
                            cx, cz = np.array([math.tan(math.radians(G['lean'])) * (ys - G['y_mid']), G['dze']]) + (sh + tt) * u_out
                            dz = z - cz
                            if abs(dz) < 4.2: reg.append(Point(cx + t[0], ys + t[1]).buffer(math.sqrt(4.2 ** 2 - dz ** 2)))
                        if reg: worst = min(worst, g.distance(unary_union(reg)))
        print(f'  door screws at Y {G["YSC"]}: driver path free by {worst:.1f} mm at every door position')
        if worst < 0.5: fail(f'{side}: door screw driver path blocked ({worst:.1f} mm)')

        # actuator (left): tube and body next to the module, in the plane Z_ACT
        if lev:
            worst_a = 1e9
            for f in fs:
                c = C(f); u = (c - F) / np.linalg.norm(c - F)
                parts = [(c - G['act_tube_from'] * u, F + G['act_body_len'] * u, G['act_r_tube']),
                         (F + 15 * u, F + G['act_body_len'] * u, G['act_r_body'])]
                for k in bodies:
                    for z in zs:
                        g = place(sl[k][z], bodies[k][1], f, bodies[k][2])
                        if g.is_empty: continue
                        for p0, p1, r in parts:
                            dz = abs(z - Z_ACT)
                            if dz >= r: continue
                            w = math.sqrt(r * r - dz * dz)
                            worst_a = min(worst_a, g.distance(LineString([tuple(p0), tuple(p1)]).buffer(w, cap_style=2)))
            print(f'  actuator (eye plane Z {Z_ACT:.0f}): clear of the module by {"> 5" if worst_a > 5 else f"{worst_a:.1f}"} mm')
            if worst_a < 1: fail(f'actuator touches the module ({worst_a:.1f} mm)')

        # print pose footprint + overhangs
        fp = print_pose_footprint(sl, bodies, zs)
        print(f'  print footprint (printed open) {fp[0]:.0f} x {fp[1]:.0f} mm, height {Z_TOP:.0f} mm')
        if max(fp) > 218: fail(f'{side}: does not fit a 220 x 220 bed ({fp[0]:.0f} x {fp[1]:.0f})')
        print('  unsupported area per body (outside 45 deg, > 1 mm2):')
        for k in bodies:
            items = overhangs(sl[k], layers)
            print(f'    {k:8s} ' + ('; '.join(f'Z{z:.1f}: {a:.0f} mm2 (widest ~{w:.1f} mm)' for z, a, w in items) if items else 'none'))

    # actuator stroke and holding force (door 1.43 kg + brackets, both sides via the rod)
    l0, l1 = np.linalg.norm(F - C(0)), np.linalg.norm(F - C(1))
    print(f'--- actuator: pin to pin {l0:.1f} mm closed, {l1:.1f} mm open, stroke {l1 - l0:.1f} mm, top pivot X {F[0]:.0f} Y {F[1]:.0f}')
    W, fmax, fcl = 1.48 * 9.81, 0, None
    for f in np.linspace(0, 1, 201):
        a_out = math.radians(180 - (TH0 - SW * f))
        torque = W * R / 1000 * math.cos(a_out)          # N m about the pivots (lift rate dY/dphi = R cos)
        c = C(f); u = (F - c) / np.linalg.norm(F - c); r = (c - P1) / 1000
        arm = abs(r[0] * u[1] - r[1] * u[0]); fa = torque / arm if arm > 1e-6 else 0
        fmax = max(fmax, fa); fcl = fa if fcl is None else fcl
    print(f'--- actuator force to hold the door (no friction): max {fmax:.0f} N, closed {fcl:.0f} N')
    if abs(l1 - l0 - 150) > 1: fail(f'stroke {l1 - l0:.1f} mm, not 150')
    print('RESULT:', 'OK' if ok else 'PROBLEMS\n  ' + '\n  '.join(report))
    return 0 if ok else 1


def print_pose_footprint(sl, bodies, zs):
    f = float(G['print_pose'])
    return footprint([place(sl[k][z], bodies[k][1], f, bodies[k][2]) for k in bodies for z in zs])


if __name__ == '__main__':
    sys.exit(main())
