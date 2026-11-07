"""Shared helpers for the door checks: render OpenSCAD bodies, slice them, measure gaps and overhangs.
Needs: openscad, python3 with trimesh + rtree + shapely + numpy."""
import math, os, re, subprocess, sys, tempfile
import numpy as np, trimesh
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix='doorcheck_')


def defs_from_argv():
    """-D style overrides from the command line: name=value (e.g. cj=0.35)."""
    return [a for a in sys.argv[1:] if re.match(r'^[A-Za-z_]\w*=', a)]


def scad_echo(scad, defs=()):
    """Values printed by the SCAD file's part="echo" (one ECHO line 'GEO k=v;k=v...')."""
    fn = os.path.join(TMP, os.path.basename(scad) + '.echo')
    subprocess.run(['openscad', '-D', 'part="echo"', *sum((['-D', d] for d in defs), []), '-o', fn, scad], check=True,
                   stderr=subprocess.DEVNULL)   # -q would also drop the ECHO lines
    txt = open(fn).read()
    body = txt.split('GEO ', 1)[1].rsplit('"', 1)[0]
    out = {}
    for kv in body.split(';'):
        k, v = kv.split('=', 1)
        out[k] = eval(v.replace('true', 'True').replace('false', 'False').replace('undef', 'None'))
    return out


def render(scad, part, defs=()):
    fn = os.path.join(TMP, f'{os.path.basename(scad)}.{part}.stl')
    subprocess.run(['openscad', '-q', '--export-format', 'binstl', '-D', f'part="{part}"',
                    *sum((['-D', d] for d in defs), []), '-o', fn, scad], check=True)
    return trimesh.load(fn)


def slices(mesh, zs):
    out = {}
    secs = mesh.section_multiplane(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1], heights=list(zs))
    for z, s in zip(zs, secs):
        if s is None:
            out[z] = Polygon(); continue
        polys = [p for p in s.polygons_full if p.area > 1e-4]
        out[z] = unary_union(polys).buffer(0) if polys else Polygon()
    return out


def layer_zs(z_top, extra=()):
    layers = sorted(set(np.round(np.arange(0.1, z_top, 0.2), 3).tolist()))
    return layers, sorted(set(layers + list(extra)))


def overhangs(sl, layers, min_area=1.0):
    """Area of each layer not resting on the layer below (45 deg = 0.2 mm per 0.2 mm layer)."""
    items = []
    for z0, z1 in zip(layers, layers[1:]):
        lo, up = sl[z0], sl[z1]
        un = up.difference(lo.buffer(0.2 + 0.05))
        if un.area > min_area:
            w = max((g.area / max(g.length, 1e-6)) * 2 for g in (un.geoms if hasattr(un, 'geoms') else [un]))
            items.append((z1, un.area, w))
    return items


def screw_walls(sl, screws, r_cb, zmax, wall=1.5):
    """Missing plastic area in a ring of `wall` mm around each counterbore (worst layer below zmax)."""
    res = []
    for sx, sy in screws:
        ring = Point(sx, sy).buffer(r_cb + wall).difference(Point(sx, sy).buffer(r_cb + 0.15))
        worst = min(ring.difference(sl[z]).area for z in sl if z < zmax)
        res.append(((sx, sy), worst))
    return res


def footprint(polys):
    g = unary_union(polys)
    x0, y0, x1, y1 = g.bounds
    return x1 - x0, y1 - y0


def strip(a, b, z, zc, r):
    """Cross-section at height z of a cylinder (axis a-b in the plane z = zc, radius r): a capsule or None."""
    dz = abs(z - zc)
    if dz >= r: return None
    return LineString([tuple(a), tuple(b)]).buffer(math.sqrt(r * r - dz * dz), 16)


def fmt_gap(v):
    return '   -  ' if v > 1e8 else f'{v:6.2f}'
