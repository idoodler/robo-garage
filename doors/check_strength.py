#!/usr/bin/env python3
"""Strength check of the print-in-place modules (parallel-lift.scad, up-over.scad), no test print needed.

1. Joint loads from statics (side view, all load on one module): the actuator stalls at --actuator N (default 100) while the door is
   blocked at a corner; the block pushes against the door's motion, up to 20 deg off it (friction). Worst pose over the whole travel.
   This reproduces the guide's "about 400 N on the worst pin" of the parallel lift.
   --yank: misuse instead: a hand pulls or pushes a door corner with 150 N in any direction, at any pose, the actuator holds.
2. 3D finite elements of every loaded body as rendered: 0.5 mm cubes (8-node hexahedra, about one extrusion width), isotropic PETG
   (E 2000 MPa, nu 0.38), loads as bearing pressure on bores and pins, supports where the body really bears (screw bosses on the cheek,
   door flange, the far ring of an arm). Material as printed with the guide's settings: the outer 1.8 mm (4 perimeters) and the top and
   bottom 0.8 mm (4 layers) solid, the core 20 % gyroid at 10 % of the stiffness (--solid: all solid).
3. Hot spots against PETG allowables: 45 MPa along the layers, 25 MPa tension across them, 15 MPa shear between them. Each value is
   the largest average over a 1 mm ball of walls: single cells on the stair-stepped surface of a round pin keep growing with finer
   cells (+25 to +40 % from 0.5 to 0.35-0.4 mm), the 1 mm average far less (+4 to +19 %). Spots within 2 mm of a load or support are left out, except the pin roots, which are
   checked on their own. FE is linear, so the actuator force for a safety factor of 2 follows from the worst use.

Usage: python3 check_strength.py [--quick] [--yank] [--solid] [--jobs=3] [--only par_bracket,uo_arm_l,...] [--actuator=100] [name=value ...]
       --quick: 0.7 mm cells, about 3x faster, but corner peaks come out lower: only to compare variants with each other.
       A full run took about 6 min (326 s) on 32 cores; one body needs up to 16 GB, and --jobs bodies run at a time (default 3: up to 48 GB;
       --jobs=1 for a 16 GB machine, about 3x slower).
Needs: openscad, python3 with numpy, scipy, pyamg, trimesh, shapely.
"""
import math, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np, scipy.sparse as sp, pyamg, trimesh
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt
from shapely import contains_xy
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checklib import HERE, TMP, defs_from_argv, scad_echo, render

PAR, UO = os.path.join(HERE, 'parallel-lift.scad'), os.path.join(HERE, 'up-over.scad')
ARGS = sys.argv[1:]
H = 0.7 if '--quick' in ARGS else 0.5
FACT = float(next((a.split('=', 1)[1] for a in ARGS if a.startswith('--actuator=')), 100))
ONLY = next((ARGS[i + 1].split(',') for i, a in enumerate(ARGS) if a == '--only'), None)
JOBS = int(next((a.split('=', 1)[1] for a in ARGS if a.startswith('--jobs=')), 3))
DEFS = defs_from_argv()
JAM = 20                                        # deg: the block's push may lean this far off the door's motion
YANK = 150.0 if '--yank' in ARGS else None      # N: hand force on a door corner (misuse case)
PRINTED = '--solid' not in ARGS                 # 4 perimeters + 4 top / bottom layers solid, 20 % gyroid core
WALL, SKIN, CORE_E, AVG_R = 1.8, 0.8, 0.1, 1.0  # mm, mm, core stiffness share, hot-spot averaging radius (mm)
ALLOW = dict(s1=45.0, sz=25.0, tz=15.0)         # MPa: along the layers, tension across them, shear between them
E, NU, W = 2000.0, 0.38, 1.48 * 9.81            # PETG; door + brackets in N
d = lambda a: np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
cr = lambda a, b: a[0] * b[1] - a[1] * b[0]
rot = lambda v, a: v[0] * d(a) + v[1] * d(a + 90)                    # turn v by a deg
ang = lambda v: math.degrees(math.atan2(v[1], v[0]))


# ---------------------------------------------------------------- joint loads
def parallel_cases(G):
    """Forces on the bracket: F1 from arm 1 at A1, S2 * u from arm 2 at A2; fa = actuator force on the lever; rot = arm turn (deg)."""
    P1, P2, A1, A2, F = (np.array(G[k], float) for k in ('P1', 'P2', 'A1', 'A2', 'F'))
    R, TH0, SW, LEV, LEV_A = (float(G[k]) for k in ('R', 'TH0', 'SWING', 'LEV', 'LEV_A'))
    T = lambda f: R * (d(TH0 - SW * f) - d(TH0))
    door = [np.array(p) + [0, G['door_up']] for p in [(-19, 17), (0, 17), (0, 203), (-18, 221), (-19, 221)]]
    out = []
    for f in np.linspace(0, 1, 51):
        u, t = d(TH0 - SW * f), T(f); a1, a2 = A1 + t, A2 + t
        c = P1 + LEV * d(LEV_A - SW * f); ua = (c - F) / np.linalg.norm(c - F)      # extending, the actuator pushes the lever away from its top pivot
        vel = T(min(f + .01, 1)) - T(max(f - .01, 0)); vel /= np.linalg.norm(vel)
        cg, wv = np.array([-9.5, 119.0]) + t, np.array([0, -W / 2])
        if YANK:                                                         # unknowns F1x, F1y, S2, actuator force (it holds)
            for p in door:
                for an in range(0, 360, 15):
                    fy = YANK * d(an)
                    M = np.array([[1, 0, u[0], 0], [0, 1, u[1], 0], [0, 0, cr(a2 - a1, u), 0], [(a1 - P1)[1], -(a1 - P1)[0], 0, cr(c - P1, ua)]])
                    x = np.linalg.solve(M, [-fy[0] - wv[0], -fy[1] - wv[1], -cr(p + t - a1, fy) - cr(cg - a1, wv), 0])
                    out.append(dict(f=f, F1=x[:2], S2=x[2], S2u=x[2] * u, fa=x[3] * ua, rot=-SW * f,
                                    case=f'f={f:.2f}, {YANK:.0f} N at door ({p[0]:.0f},{p[1]:.0f}) towards {an} deg'))
            continue
        for sgn in (1, -1):
            fa = sgn * FACT * ua
            for p in door:
                for da in np.linspace(-JAM, JAM, 5):
                    dj = -rot(sgn * vel, da)
                    # unknowns F1x, F1y, S2, J: bracket force and moment (about A1) balance, arm 1 moment balance about P1
                    M = np.array([[1, 0, u[0], dj[0]], [0, 1, u[1], dj[1]], [0, 0, cr(a2 - a1, u), cr(p + t - a1, dj)], [(a1 - P1)[1], -(a1 - P1)[0], 0, 0]])
                    x = np.linalg.solve(M, [-wv[0], -wv[1], -cr(cg - a1, wv), -cr(c - P1, fa)])
                    if x[3] >= 0:
                        out.append(dict(f=f, F1=x[:2], S2=x[2], S2u=x[2] * u, fa=fa, rot=-SW * f,
                                        case=f'f={f:.2f}, actuator {"pushing" if sgn > 0 else "pulling"}, block at door ({p[0]:.0f},{p[1]:.0f}) {da:+.0f} deg'))
    return out


def upover_kin(G):
    Q, D, F = (np.array(G[k], float) for k in ('Q', 'D', 'F'))
    L, PSI, LEV, LEV_A = (float(G[k]) for k in ('L', 'PSI', 'LEV', 'LEV_A'))
    Rcw = lambda p: np.array([[math.cos(math.radians(p)), math.sin(math.radians(p))], [-math.sin(math.radians(p)), math.cos(math.radians(p))]])
    u_of = lambda p: Rcw(p) @ (D - Q)
    def s_of(p):
        u = u_of(p); h = Q[1] + u[1] - F[1]; return F[0] - Q[0] - u[0] - math.sqrt(L * L - h * h)
    Qw = lambda f: np.array([Q[0] + s_of(PSI * f), Q[1]])
    Dw = lambda f: Qw(f) + u_of(PSI * f)
    arm_rot = lambda f: (ang(Dw(f) - F) - ang(D - F) + 180) % 360 - 180
    Cf = lambda f: F + LEV * d(LEV_A + arm_rot(f))
    return dict(Q=Q, D=D, F=F, PSI=PSI, Rcw=Rcw, Qw=Qw, Dw=Dw, arm_rot=arm_rot, Cf=Cf)


def upover_cases(G):
    """Forces on the bracket: FD from the arm at D, Qy from the track on the peg (normal to the slot); psi = door turn (deg)."""
    K = upover_kin(G); Q, D, F, PSI, Rcw, Qw, Dw, Cf = (K[k] for k in ('Q', 'D', 'F', 'PSI', 'Rcw', 'Qw', 'Dw', 'Cf'))
    FA = np.array(G['FA'], float); top = float(G['DOOR_TOP'])
    door0 = [np.array(p, float) for p in [(-19, 17), (0, 17), (0, top), (-19, top)]]
    pt = lambda p0, f: Qw(f) + Rcw(PSI * f) @ (p0 - Q)
    out = []
    for f in np.linspace(0, 1, 51):
        q, dw, c = Qw(f), Dw(f), Cf(f); ua = (c - FA) / np.linalg.norm(c - FA)
        cg, wv = pt(np.array([-9.5, (17 + top) / 2]), f), np.array([0, -W / 2])
        if YANK:
            for p0 in door0:
                p = pt(p0, f)
                for an in range(0, 360, 15):
                    fy = YANK * d(an)
                    M = np.array([[1, 0, 0, 0], [0, 1, 1, 0], [0, 0, (q - dw)[0], 0], [(dw - F)[1], -(dw - F)[0], 0, cr(c - F, ua)]])
                    try: x = np.linalg.solve(M, [-fy[0] - wv[0], -fy[1] - wv[1], -cr(p - dw, fy) - cr(cg - dw, wv), 0])
                    except np.linalg.LinAlgError: continue
                    out.append(dict(f=f, FD=x[:2], Qy=x[2], fa=x[3] * ua, psi=PSI * f, rot=K['arm_rot'](f),
                                    case=f'f={f:.2f}, {YANK:.0f} N at door ({p0[0]:.0f},{p0[1]:.0f}) towards {an} deg'))
            continue
        for sgn in (1, -1):
            fa = sgn * FACT * ua
            for p0 in door0:
                p = pt(p0, f); mot = pt(p0, min(f + .01, 1)) - pt(p0, max(f - .01, 0)); mot = sgn * mot / np.linalg.norm(mot)
                for da in np.linspace(-JAM, JAM, 5):
                    dj = -rot(mot, da)
                    M = np.array([[1, 0, 0, dj[0]], [0, 1, 1, dj[1]], [0, 0, (q - dw)[0], cr(p - dw, dj)], [(dw - F)[1], -(dw - F)[0], 0, 0]])
                    try: x = np.linalg.solve(M, [-wv[0], -wv[1], -cr(cg - dw, wv), -cr(c - F, fa)])
                    except np.linalg.LinAlgError: continue
                    if x[3] >= 0:
                        out.append(dict(f=f, FD=x[:2], Qy=x[2], fa=fa, psi=PSI * f, rot=K['arm_rot'](f),
                                        case=f'f={f:.2f}, actuator {"pushing" if sgn > 0 else "pulling"}, block at door ({p0[0]:.0f},{p0[1]:.0f}) {da:+.0f} deg'))
    return out


# ---------------------------------------------------------------- voxel finite elements
def ke_hex(h):
    lam = E * NU / ((1 + NU) * (1 - 2 * NU)); mu = E / (2 * (1 + NU))
    Dm = np.zeros((6, 6)); Dm[:3, :3] = lam; Dm[np.arange(3), np.arange(3)] += 2 * mu; Dm[3:, 3:] = np.eye(3) * mu
    xi = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
    def Bmat(p):
        dN = np.array([xi[:, 0] * (1 + xi[:, 1] * p[1]) * (1 + xi[:, 2] * p[2]), xi[:, 1] * (1 + xi[:, 0] * p[0]) * (1 + xi[:, 2] * p[2]),
                       xi[:, 2] * (1 + xi[:, 0] * p[0]) * (1 + xi[:, 1] * p[1])]) / 8 * (2 / h)
        B = np.zeros((6, 24))
        for a in range(8):
            B[0, 3 * a], B[1, 3 * a + 1], B[2, 3 * a + 2] = dN[0, a], dN[1, a], dN[2, a]
            B[3, 3 * a], B[3, 3 * a + 1] = dN[1, a], dN[0, a]            # gamma xy
            B[4, 3 * a + 1], B[4, 3 * a + 2] = dN[2, a], dN[1, a]        # gamma yz
            B[5, 3 * a], B[5, 3 * a + 2] = dN[2, a], dN[0, a]            # gamma xz
        return B
    K = sum(Bmat(p).T @ Dm @ Bmat(p) * (h / 2) ** 3 for p in xi / math.sqrt(3))
    return K, Dm @ Bmat(np.zeros(3))


class Body:
    """One printed body sampled in cubes of h mm (cell inside = its centre inside the layer outline)."""
    def __init__(self, mesh, h):
        lo, hi = mesh.bounds; n = np.ceil((hi - lo) / h).astype(int) + 1
        ctr = [lo[i] + h * (np.arange(n[i]) + 0.5) for i in range(3)]
        X, Y = np.meshgrid(ctr[0], ctr[1], indexing='ij'); occ = np.zeros(n, bool)
        for k, s in enumerate(mesh.section_multiplane(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1], heights=list(ctr[2]))):
            polys = [p for p in s.polygons_full if p.area > 1e-6] if s is not None else []
            if polys: occ[:, :, k] = contains_xy(unary_union(polys), X, Y)
        core = np.zeros(n, bool)
        if PRINTED:                             # core = farther than WALL from the outline in its layer and SKIN from a top / bottom face
            dxy = np.stack([distance_transform_edt(occ[:, :, k]) for k in range(n[2])], axis=2)
            dz = distance_transform_edt(occ, sampling=(1e3, 1e3, 1.0))
            core = occ & ((dxy - 0.5) * h > WALL) & ((dz - 0.5) * h > SKIN)
        ei = np.argwhere(occ)
        corner = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
        allc = (ei[:, None, :] + corner[None]).reshape(-1, 3); uniq, inv = np.unique(allc, axis=0, return_inverse=True)
        self.h, self.nodes, self.conn, self.cent = h, lo + h * uniq, inv.reshape(-1, 8), lo + h * (ei + 0.5)
        self.vol_err = len(ei) * h ** 3 / mesh.volume - 1
        self.core = core[ei[:, 0], ei[:, 1], ei[:, 2]]; self.k = np.where(self.core, CORE_E, 1.0)
        Ke, self.DB = ke_hex(h)
        self.edof = (3 * self.conn[:, :, None] + np.arange(3)).reshape(-1, 24); nd = 3 * len(uniq)
        self.K = sp.csr_matrix(((self.k[:, None] * Ke.ravel()[None]).ravel(), (np.repeat(self.edof, 24, axis=1).ravel(), np.tile(self.edof, (1, 24)).ravel())), shape=(nd, nd))
        self.F, self.fixed, self.patch = np.zeros(nd), np.zeros(nd, bool), np.zeros(len(uniq), bool)
        self.surf = np.bincount(self.conn.ravel(), minlength=len(uniq)) < 8

    def ring(self, c, r, z0, z1, pin):
        """Surface nodes on a pin (radius r, outer surface) or a bore (radius r, inner surface) about c between z0 and z1."""
        p = self.nodes; rr = np.hypot(p[:, 0] - c[0], p[:, 1] - c[1]); b = 1.2 * self.h
        band = (rr <= r + 0.3 * self.h) & (rr >= r - b) if pin else (rr >= r - 0.3 * self.h) & (rr <= r + b)
        return band & (p[:, 2] >= z0 - 1e-6) & (p[:, 2] <= z1 + 1e-6) & self.surf

    def bearing(self, c, r, z0, z1, force, pin):
        """Force (in plane) through contact on a pin or bore: cos-distributed over the half the force pushes on."""
        p = self.nodes; rad = (p[:, :2] - c) / np.maximum(np.hypot(p[:, 0] - c[0], p[:, 1] - c[1])[:, None], 1e-9)
        fv = np.asarray(force, float); w = np.maximum(0, -((rad if pin else -rad) @ (fv / np.linalg.norm(fv)))) * self.ring(c, r, z0, z1, pin)
        if w.sum() == 0: raise ValueError(f'no contact at {c}')
        w /= w.sum(); self.F[0::3] += w * fv[0]; self.F[1::3] += w * fv[1]; self.patch |= w > 0

    def fix(self, mask):
        for k in range(3): self.fixed[3 * np.where(mask)[0] + k] = True
        self.patch |= mask

    def solve(self):
        free = ~self.fixed; Kf = self.K[free][:, free].tocsr()
        fn = np.where(free[0::3])[0]; pc = self.nodes[fn] - self.nodes[fn].mean(0)
        B = np.zeros((3 * len(fn), 6)); B[0::3, 0] = B[1::3, 1] = B[2::3, 2] = 1          # rigid body modes for the AMG
        B[0::3, 3], B[1::3, 3], B[1::3, 4], B[2::3, 4], B[0::3, 5], B[2::3, 5] = -pc[:, 1], pc[:, 0], -pc[:, 2], pc[:, 1], pc[:, 2], -pc[:, 0]
        ml = pyamg.smoothed_aggregation_solver(Kf, B=B, symmetry='symmetric', strength=('symmetric', {'theta': 0.0}), max_coarse=2000)
        res = []; self.u = np.zeros(len(free)); self.u[free] = ml.solve(self.F[free], tol=1e-8, accel='cg', maxiter=400, residuals=res)
        if res[-1] / res[0] > 1e-6: raise RuntimeError('FE did not converge')
        s = (self.u[self.edof] @ self.DB.T) * self.k[:, None]                              # sxx syy szz txy tyz txz per cell
        T3 = np.stack([s[:, [0, 3, 5]], s[:, [3, 1, 4]], s[:, [5, 4, 2]]], 1)
        self.s1, self.sz, self.tz = np.linalg.eigvalsh(T3)[:, -1], s[:, 2], np.hypot(s[:, 4], s[:, 5])
        self.ok = cKDTree(self.nodes[self.patch]).query(self.cent)[0] > 2.0                 # 2 mm away from load / support patches
        return self

    def peaks(self, sel=None, use_ok=True):
        """Per stress: (largest 1 mm-ball average of the walls, where, largest single cell) over the selected wall cells."""
        sel = (self.ok if use_ok else True) & (True if sel is None else sel) & ~self.core
        if not hasattr(self, 'tree'): self.tree = cKDTree(self.cent)
        out = {}
        for k in ('s1', 'sz', 'tz'):
            v = getattr(self, k); idx = np.where(sel)[0]; top = idx[np.argsort(-v[idx])[:400]]
            best, at = -1e9, None
            for i in top:
                nb = [j for j in self.tree.query_ball_point(self.cent[i], AVG_R) if not self.core[j]]
                a = float(v[nb].mean())
                if a > best: best, at = a, i
            out[k] = (best, tuple(round(float(x), 1) for x in self.cent[at]), float(v[top[0]]))
        out['umax'] = float(np.linalg.norm(self.u.reshape(-1, 3), axis=1).max())
        return out

    def cyl(self, c, r, z0, z1):
        e = self.cent; return (np.hypot(e[:, 0] - c[0], e[:, 1] - c[1]) <= r) & (e[:, 2] >= z0) & (e[:, 2] <= z1)


def job(args):
    """One body: render, load, solve. Returns {spot label: peaks}."""
    name, G, U = args
    t0 = time.time(); res = {}
    pick = lambda cs, key: max(cs, key=key)
    turn = lambda v, a: rot(v, -a)                                    # world force -> body frame of a part turned by a
    if name.startswith('par'):
        cs = parallel_cases(G); P1, P2, A1, A2 = (np.array(G[k], float) for k in ('P1', 'P2', 'A1', 'A2'))
        h1, z2, zm, cj = G['h1'], G['h1'] + G['gz'], G['z_mov'], G['cj']
    else:
        cs = upover_cases(G); K = upover_kin(G); D, F, Q = K['D'], K['F'], K['Q']
        h1, z2, zm, cj = G['h1'], G['h1'] + G['gz'], G['z_mov'], G['cj']
    scad = PAR if name.startswith('par') else UO
    part = {'par_bracket': 'bracket', 'par_plate_l': 'plate_l', 'par_plate_r': 'plate_r', 'par_arm1_l': 'arm1_l', 'par_arm1_r': 'arm1_r',
            'par_arm2': 'arm2', 'uo_bracket': 'bracket', 'uo_plate_l': 'plate_l', 'uo_plate_r': 'plate_r', 'uo_arm_l': 'arm_l', 'uo_arm_r': 'arm_r'}[name]
    b = Body(render(scad, part, DEFS), H); p = b.nodes
    screws = lambda S: [(p[:, 2] >= G['z_top'] - 0.6 * H) & (np.hypot(p[:, 0] - s[0], p[:, 1] - s[1]) <= 6.8) for s in S]
    if name == 'par_bracket':
        c = pick(cs, lambda c: np.linalg.norm(c['F1']) + abs(c['S2']))
        b.bearing(A1, G['rA'], 3.2, h1, c['F1'], True); b.bearing(A2, G['rA'], 3.2, h1, c['S2u'], True)
        b.fix((np.abs(p[:, 0] - math.tan(math.radians(G['lean'])) * (p[:, 1] - G['y_mid'])) < 0.6 * H) & b.surf)   # glued to the door
        b.solve(); res['body'] = b.peaks()
        for a, n in ((A1, 'A1'), (A2, 'A2')): res[f'pin root {n}'] = b.peaks(b.cyl(a, G['rA'] + 0.1, h1, z2 + 1), use_ok=False)
    elif name in ('par_plate_l', 'par_plate_r'):
        if name.endswith('l'): c = pick(cs, lambda c: np.linalg.norm(c['fa'] - c['F1'])); f1 = c['fa'] - c['F1']
        else: c = pick(cs, lambda c: np.linalg.norm(c['F1'])); f1 = -c['F1']      # right: the rod brings the torque as a couple
        # the pins bear on the ring layer only: above it the arms' own sweeps cut most of the bore, and the 0.45 mm gap keeps the rest out
        # of contact except right in the force direction (conservative for the ring, where the plates peak)
        b.bearing(P1, G['rP1'] + cj, 3.2, h1, f1, False); b.bearing(P2, G['rP2'] + cj, 3.2, h1, -c['S2u'], False)
        b.fix(np.any(screws(G['SCREWS']), axis=0)); b.solve(); res['body'] = b.peaks()
    elif name in ('par_arm1_l', 'par_arm1_r', 'par_arm2'):
        # the plate ring pushes on the pivot pin (z 3.2..h1: above it the arm's own sweep cut the bore), the bracket pin holds the far ring
        if name == 'par_arm2':
            c = pick(cs, lambda c: abs(c['S2'])); b.bearing(P2, G['rP2'], 3.2, h1, turn(c['S2u'], c['rot']), True)
            b.fix(b.ring(A2, G['rA'] + cj, 3.2, h1, False)); piv, rp = P2, G['rP2']
        else:
            c = pick(cs, lambda c: np.linalg.norm(c['F1']))
            if name.endswith('l'):
                b.bearing(P1, G['rP1'], 3.2, h1, turn(c['F1'] - c['fa'], c['rot']), True)
                b.bearing(P1 + G['LEV'] * d(G['LEV_A']), (G['eye_bolt'] + 0.4) / 2, 0, zm - 9, turn(c['fa'], c['rot']), False)
                b.fix(b.ring(A1, G['rA'] + cj, 3.2, h1, False)); piv, rp = P1, G['rP1']
            else:                                                       # right: the rod brings the torque; it and the pin sit in the socket
                b.bearing(A1, G['rA'] + cj, 3.2, h1, turn(-c['F1'], c['rot']), False); sq = (G['shaft'] + 0.25) / 2
                b.fix((np.maximum(np.abs(p[:, 0] - P1[0]), np.abs(p[:, 1] - P1[1])) <= sq + 0.6 * H) & (p[:, 2] <= G['sock_top']) & b.surf); piv = None
        b.solve(); res['body'] = b.peaks()
        if piv is not None: res[f'pin root {"P2" if name == "par_arm2" else "P1"}'] = b.peaks(b.cyl(piv, rp + 0.1, h1, z2 + 1), use_ok=False)
    elif name == 'uo_bracket':
        c = pick(cs, lambda c: np.linalg.norm(c['FD']) + abs(c['Qy']))
        b.bearing(D, G['rA'], 3.2, h1, turn(c['FD'], -c['psi']), True)
        b.bearing(Q, G['peg_d'] / 2, G['trk'][0], G['z_top'], turn(np.array([0, c['Qy']]), -c['psi']), True)
        b.fix((p[:, 0] < 0.6 * H) & b.surf); b.solve(); res['body'] = b.peaks()
        res['pin root D'] = b.peaks(b.cyl(D, G['rA'] + 0.1, h1, z2 + 1), use_ok=False)
        res['peg root'] = b.peaks(b.cyl(Q, G['peg_d'] / 2 + 0.1, zm - 1, zm + 1.5), use_ok=False)
    elif name in ('uo_plate_l', 'uo_plate_r'):
        if name.endswith('l'): c = pick(cs, lambda c: np.linalg.norm(c['fa'] - c['FD'])); fF = c['fa'] - c['FD']; r = G['rFl']
        else:                                                               # right arm: a link, its pull along F-D as big as the left D force
            c = pick(cs, lambda c: np.linalg.norm(c['FD'])); ax = K['Dw'](c['f']) - F; fF = np.linalg.norm(c['FD']) * ax / np.linalg.norm(ax); r = G['rFr']
        b.bearing(F, r + cj, 3.2, h1, fF, False); b.fix(np.any(screws(G['SCREWS']), axis=0)); b.solve(); res['body'] = b.peaks()
    elif name in ('uo_arm_l', 'uo_arm_r'):
        if name.endswith('l'):                                         # plate ring on the pivot pin, actuator on the eye, bracket pin holds the far ring
            c = pick(cs, lambda c: np.linalg.norm(c['FD']) + np.linalg.norm(c['fa'])); r = G['rFl']
            b.bearing(F, r, 3.2, h1, turn(c['FD'] - c['fa'], c['rot']), True)
            b.bearing(K['Cf'](0), (G['eye_bolt'] + 0.4) / 2, 0, zm - 9, turn(c['fa'], c['rot']), False)
        else:                                                           # right arm: a link, pulled along F-D as hard as the left D force
            c = pick(cs, lambda c: np.linalg.norm(c['FD'])); ax = (F - D) / np.linalg.norm(F - D); r = G['rFr']
            b.bearing(F, r, 3.2, h1, np.linalg.norm(c['FD']) * ax, True)
        b.fix(b.ring(D, G['rA'] + cj, 3.2, h1, False)); b.solve(); res['body'] = b.peaks()
        res['pin root F'] = b.peaks(b.cyl(F, r + 0.1, h1, z2 + 1), use_ok=False)
    return name, c['case'], res, b.vol_err, time.time() - t0


def main():
    G = {'par': scad_echo(PAR, DEFS), 'uo': scad_echo(UO, DEFS)}
    names = ['par_bracket', 'par_plate_l', 'par_plate_r', 'par_arm1_l', 'par_arm1_r', 'par_arm2',
             'uo_bracket', 'uo_plate_l', 'uo_plate_r', 'uo_arm_l', 'uo_arm_r']
    names = [n for n in names if not ONLY or n in ONLY]
    for k, cs in (('par', parallel_cases(G['par'])), ('uo', upover_cases(G['uo']))):
        key = (lambda c: np.linalg.norm(c['F1'])) if k == 'par' else (lambda c: np.linalg.norm(c['FD']))
        c = max(cs, key=key)
        what = f'{YANK:.0f} N on a door corner, actuator holding' if YANK else f'actuator {FACT:.0f} N stalled'
        print(f'--- {"parallel lift" if k == "par" else "up & over"}: {what}, worst arm-to-bracket joint force {key(c):.0f} N ({c["case"]})')
    print(f'--- FE, cells {H} mm, {"as printed (4 walls, 4 skins, 20 % core)" if PRINTED else "solid"}; hot spots in MPa, 1 mm average (single cell in brackets):'
          f' along the layers / across them / shear between them; allowables {ALLOW["s1"]:.0f} / {ALLOW["sz"]:.0f} / {ALLOW["tz"]:.0f}')
    rows = []
    with ProcessPoolExecutor(JOBS) as ex:
        for name, case, res, verr, dt in ex.map(job, [(n, G[n.split('_')[0]], None) for n in names]):
            for spot, pk in res.items():
                use = max(pk['s1'][0] / ALLOW['s1'], pk['sz'][0] / ALLOW['sz'], pk['tz'][0] / ALLOW['tz'])
                rows.append((name, spot, pk, use))
                print(f'  {name:12s} {spot:12s} ' + '  '.join(f'{pk[k][0]:5.1f} ({pk[k][2]:5.1f}) at {str(pk[k][1]):19s}' for k in ('s1', 'sz', 'tz')) +
                      f' use {use:4.2f}' + (f'  moves {pk["umax"]:.2f} mm' if spot == 'body' and 'arm' not in name else ''))
            if abs(verr) > 0.03: print(f'  {name}: cell volume off by {verr * 100:.1f} %')
    worst = max(rows, key=lambda r: r[3])
    if YANK: print(f'--- worst: {worst[0]} {worst[1]}, use {worst[3]:.2f}: safety factor {1 / worst[3]:.1f} against a {YANK:.0f} N yank')
    else: print(f'--- worst: {worst[0]} {worst[1]}, use {worst[3]:.2f} at {FACT:.0f} N. Safety factor 2 everywhere up to about {FACT / worst[3] / 2:.0f} N actuator stall force.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
