#!/usr/bin/env python3
"""Check the print-in-place up & over door (up-over.scad).

Renders every body, slices it every 0.2 mm and moves the slices through the whole travel (f = 0 closed .. 1 open,
1 % steps): door turns by 90 f deg about its track peg, the peg slides back, the arm keeps the rest.
Reports gaps per pair (joints / elsewhere), the door path against drawer front, tray and the docked robot,
the wall plate against the door's sweep, the track, the actuator, screw access, overhangs and the bed footprint.
Usage: python3 check_upover.py [--quick] [cj=0.45] [cs=1.0] [gz=0.6]
"""
import math, os, sys
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checklib import HERE, defs_from_argv, scad_echo, render, slices, layer_zs, overhangs, screw_walls, footprint, fmt_gap

SCAD = os.path.join(HERE, 'up-over.scad')
QUICK = '--quick' in sys.argv
DEFS = defs_from_argv()
G = scad_echo(SCAD, DEFS)
Q, D, F, FA = (np.array(G[k], float) for k in ('Q', 'D', 'F', 'FA'))
L, PSI, LEV, LEV_A = (float(G[k]) for k in ('L', 'PSI', 'LEV', 'LEV_A'))
CJ, CS, Z_TOP, Z_MOV = (float(G[k]) for k in ('cj', 'cs', 'z_top', 'z_mov'))
d = lambda a: np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])


def Rcw(p):
    c, s = math.cos(math.radians(p)), math.sin(math.radians(p)); return np.array([[c, s], [-s, c]])


def s_of(p):
    u = Rcw(p) @ (D - Q); h = Q[1] + u[1] - F[1]
    return F[0] - Q[0] - u[0] - math.sqrt(L * L - h * h)


def Qw(f): return np.array([Q[0] + s_of(PSI * f), Q[1]])
def Dw(f): return Qw(f) + Rcw(PSI * f) @ (D - Q)
def ang(a, b): return math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], a @ b))
def arm_rot(f): return ang(D - F, Dw(f) - F)
def C(f): return F + LEV * d(LEV_A + arm_rot(f))


def door_place(g, f):          # rigid motion of door + bracket: turn clockwise by psi about Q, then slide
    g = affinity.rotate(g, -PSI * f, origin=tuple(Q))
    t = Qw(f) - Q
    return affinity.translate(g, t[0], t[1])


def place(g, kind, f):
    if kind == 'fix': return g
    if kind == 'rot': return affinity.rotate(g, arm_rot(f), origin=tuple(F))
    return door_place(g, f)


DOOR = Polygon([(-19, 17), (0, 17), (0, G['DOOR_TOP']), (-19, G['DOOR_TOP'])])
VEDD = box(-19, 225, -3, 700)
WHEEL = box(55, 0, 85, 30)
ROBOT = box(20, 15, 380, 118)                                   # docked robot (bay centre, full width of the door)
STATION = [box(240, 137, 600, 700), box(380, 27, 600, 700)]
Z_ACT = -(G['act_gap'] + 4)


def main():
    layers, zs = layer_zs(Z_TOP, [5.95, 6.05, 6.3, 6.55, 6.65, 17.3, 17.7, 18.5, 20.5])
    fs = np.linspace(0, 1, 21 if QUICK else 101)
    report, ok = [], True
    def fail(msg):
        nonlocal ok; report.append(msg); ok = False

    # ---- door path ----
    ff = np.linspace(0, 1, 401)
    doors = [door_place(DOOR, f) for f in ff]
    dv = min(g.distance(VEDD) for g in doors); dr = min(g.distance(ROBOT) for g in doors)
    out = max(-19 - g.bounds[0] for g in doors); g1 = doors[-1]
    tray = min(g.bounds[1] for g in doors) - 15
    print(f'--- door: max {out:.1f} mm out while moving; open: horizontal, Y {g1.bounds[1]:.0f}..{g1.bounds[3]:.0f}, '
          f'{-19 - g1.bounds[0]:.1f} mm out, inner end {g1.bounds[2]:.0f} mm deep; peg travel {s_of(PSI):.1f} mm')
    print(f'    gaps: drawer front {dv:.1f}, docked robot {dr:.1f}, tray {tray:.1f}, robot passage under the open door {g1.bounds[1] - 15:.0f} mm')
    if dv < 1.9: fail(f'door passes the drawer front with only {dv:.1f} mm')
    if dr < 2.4: fail(f'door comes within {dr:.1f} mm of the docked robot')
    if tray < 0.9: fail(f'door within {tray:.1f} mm of the tray')
    if g1.bounds[1] < 128: fail('open door too low for the robot')

    for side in ('left', 'right'):
        lev = side == 'left'
        bodies = {'plate': ('plate_l' if lev else 'plate_r', 'fix'), 'arm': ('arm_l' if lev else 'arm_r', 'rot'), 'bracket': ('bracket', 'move')}
        meshes, sl = {}, {}
        for k, (p, kind) in bodies.items():
            m = render(SCAD, p, DEFS); meshes[k] = m
            if not m.is_watertight: fail(f'{side} {k}: mesh not watertight')
            sl[k] = slices(m, zs)
        trk = render(SCAD, 'track', DEFS)
        trk.apply_scale([1, 1, -1]); trk.apply_translation([0, 0, Z_TOP])        # printed cheek face down -> module frame
        trk.invert()
        trk_sl = slices(trk, zs)
        print(f'--- {side} module ---')
        for k, m in meshes.items():
            lo, hi = m.bounds
            print(f'  {k:8s} volume {m.volume / 1000:6.1f} cm3  X {lo[0]:6.1f}..{hi[0]:6.1f}  Y {lo[1]:6.1f}..{hi[1]:6.1f}  Z {lo[2]:4.1f}..{hi[2]:4.1f}')
        if meshes['arm'].bounds[1][2] > Z_MOV + 1e-3: fail(f'{side} arm above Z {Z_MOV}')
        pairs = [('plate', 'arm'), ('plate', 'bracket'), ('arm', 'bracket'), ('track', 'arm'), ('track', 'bracket'), ('track', 'plate')]
        best = {pr: [(1e9, None), (1e9, None)] for pr in pairs}
        env = {'tray': 1e9, 'wheel': 1e9, 'drawer front': 1e9, 'door (arm)': 1e9, 'door (plate)': 1e9, 'station': 1e9}
        for f in fs:
            placed = {k: {z: place(sl[k][z], bodies[k][1], f) for z in zs} for k in bodies}
            placed['track'] = trk_sl
            jc = {('plate', 'arm'): (F, G['rRP']), ('arm', 'bracket'): (Dw(f), G['rRA'])}
            door = door_place(DOOR, f)
            for z in zs:
                for a, b in pairs:
                    ga, gb = placed[a][z], placed[b][z]
                    if ga.is_empty or gb.is_empty: continue
                    if (a, b) in jc:
                        c, rz = jc[(a, b)]; zone = Point(*c).buffer(rz + 0.6)
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
                for k in ('arm', 'bracket'):
                    g = placed[k][z]
                    if g.is_empty: continue
                    env['tray'] = min(env['tray'], g.bounds[1] - 15)
                    if 9 <= z <= 19: env['wheel'] = min(env['wheel'], g.distance(WHEEL))
                    env['drawer front'] = min(env['drawer front'], g.distance(VEDD))
                    env['station'] = min(env['station'], min(g.distance(s) for s in STATION))
                    if k == 'arm' and z <= Z_MOV: env['door (arm)'] = min(env['door (arm)'], g.distance(door))
                pg = placed['plate'][z]
                if z <= Z_MOV and not pg.is_empty: env['door (plate)'] = min(env['door (plate)'], pg.distance(door))
        print('  gaps (mm)           joint  where (f, Z)        elsewhere  where (f, Z)')
        for pr in pairs:
            (dj, wj), (de, we) = best[pr]
            js = f'{fmt_gap(dj)}  {str(wj):18s}' if dj < 1e8 else '     -' + ' ' * 20
            print(f'  {pr[0]:8s}-{pr[1]:8s} {js} {fmt_gap(de)}   {we}')
            lim = 0.3 if pr == ('track', 'bracket') else CS - 0.06
            if dj < 1e8 and dj < CJ - 0.06: fail(f'{side} {pr}: joint gap {dj:.2f} < {CJ}')
            if de < lim: fail(f'{side} {pr}: gap {de:.2f} at {we}')
        pa = unary_union([sl['plate'][z] for z in zs])
        env['plate above tray'] = pa.bounds[1] - 15
        print('  obstacles (mm):', ', '.join(f'{k} {v:.1f}' for k, v in env.items()))
        lim = {'tray': 1.5, 'wheel': 2, 'drawer front': 2, 'door (arm)': 1, 'door (plate)': 1, 'station': 3, 'plate above tray': 0.4}
        for k, v in env.items():
            if v < lim[k]: fail(f'{side}: {k} margin {v:.1f}')
        rcb = (2 * G['wall_screw'] + 0.6) / 2
        sw = screw_walls(sl['plate'], G['SCREWS'], rcb, Z_TOP - 7.5)
        for s, worst in sw:
            if worst > 0.5: fail(f'{side} wall screw {s} too close to an edge ({worst:.1f} mm2 missing)')
        print('  wall screws: walls ok' if all(w <= 0.5 for _, w in sw) else '  wall screws: see problems')
        # door screws from the bay at 45 deg
        a = math.radians(G['dsb']); u_out = np.array([math.cos(a), -math.sin(a)]); sh = G['dze'] / math.sin(a) - 1
        worst = 1e9
        for ys in G['YSC']:
            for f in fs[::5]:
                for k in ('plate', 'arm'):
                    for z in zs:
                        if z > 8: continue
                        g = place(sl[k][z], bodies[k][1], f)
                        if g.is_empty: continue
                        reg = []
                        for tt in np.linspace(0, 14, 15):
                            cx, cz = np.array([0.0, G['dze']]) + (sh + tt) * u_out
                            dz = z - cz
                            if abs(dz) < 4.2: reg.append(door_place(Point(cx, ys).buffer(math.sqrt(4.2 ** 2 - dz ** 2)), f))
                        if reg: worst = min(worst, g.distance(unary_union(reg)))
        print(f'  door screws at Y {G["YSC"]}: driver path free by {worst:.1f} mm at every door position')
        if worst < 0.5: fail(f'{side}: door screw driver path blocked ({worst:.1f} mm)')
        if lev:
            worst_a, worst_d, worst_s = 1e9, 1e9, 1e9
            for f in fs:
                c = C(f); u = (c - FA) / np.linalg.norm(c - FA)
                parts = [(c - G['act_tube_from'] * u, FA + G['act_body_len'] * u, G['act_r_tube']),
                         (FA + 15 * u, FA + G['act_body_len'] * u, G['act_r_body'])]
                door = door_place(DOOR, f)
                for p0, p1, r in parts:
                    seg = LineString([tuple(p0), tuple(p1)])
                    worst_d = min(worst_d, door.distance(seg) - r)
                    worst_s = min(worst_s, min(s.distance(seg) for s in STATION) - r)
                for k in bodies:
                    for z in zs:
                        g = place(sl[k][z], bodies[k][1], f)
                        if g.is_empty: continue
                        for p0, p1, r in parts:
                            dz = abs(z - Z_ACT)
                            if dz >= r: continue
                            w = math.sqrt(r * r - dz * dz)
                            worst_a = min(worst_a, g.distance(LineString([tuple(p0), tuple(p1)]).buffer(w, cap_style=2)))
            print(f'  actuator: clear of the module by {"> 5" if worst_a > 5 else f"{worst_a:.1f}"} mm, of the door by {worst_d:.1f} mm, of the station by {worst_s:.1f} mm')
            if worst_a < 1: fail(f'actuator touches the module ({worst_a:.1f} mm)')
            if worst_d < 2: fail(f'actuator touches the door ({worst_d:.1f} mm)')
            if worst_s < 2: fail(f'actuator touches the station ({worst_s:.1f} mm)')
        fp = footprint([place(sl[k][z], bodies[k][1], float(G['print_pose'])) for k in bodies for z in zs])
        print(f'  print footprint (pose {G["print_pose"]}) {fp[0]:.0f} x {fp[1]:.0f} mm, height {Z_TOP:.0f} mm')
        if '--poses' in sys.argv:
            for pp in np.linspace(0, 1, 21):
                q = footprint([place(sl[k][z], bodies[k][1], pp) for k in bodies for z in zs[::10]])
                print(f'    pose {pp:.2f}: {q[0]:.0f} x {q[1]:.0f}')
        if max(fp) > 218: fail(f'{side}: does not fit a 220 x 220 bed ({fp[0]:.0f} x {fp[1]:.0f})')
        print('  unsupported area per body (outside 45 deg, > 1 mm2):')
        for k in bodies:
            items = overhangs(sl[k], layers)
            print(f'    {k:8s} ' + ('; '.join(f'Z{z:.1f}: {a:.0f} mm2 (widest ~{w:.1f} mm)' for z, a, w in items) if items else 'none'))
    # actuator stroke + holding force (door 1.43 kg + brackets ~ 14.5 N, both sides; virtual work on the door's centre)
    l0, l1 = np.linalg.norm(FA - C(0)), np.linalg.norm(FA - C(1))
    print(f'--- actuator: pin to pin {l0:.1f} mm closed, {l1:.1f} mm open, stroke {l1 - l0:.1f} mm, top pivot X {FA[0]:.0f} Y {FA[1]:.0f}')
    W, fmax, h = 14.5, 0, 1e-3
    cg = np.array([-9.5, 119.0])
    for f in np.linspace(h, 1 - h, 199):
        y = lambda ff: (Qw(ff) + Rcw(PSI * ff) @ (cg - Q))[1]
        la = lambda ff: np.linalg.norm(FA - C(ff))
        fmax = max(fmax, abs(W * (y(f + h) - y(f - h)) / (la(f + h) - la(f - h))))
    print(f'--- actuator force to hold the door (no friction): max {fmax:.0f} N')
    if abs(l1 - l0 - 150) > 1: fail(f'stroke {l1 - l0:.1f} mm, not 150')
    print('RESULT:', 'OK' if ok else 'PROBLEMS\n  ' + '\n  '.join(report))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
