# Door parts for the simulator page (run by build_files.py after it has emptied files/):
#  files/doors-model-v<V>.json  base64 GLB, one node per printed body, cm, y up, node origin = its pivot (the page turns/moves them)
#  files/doors-<type>-v<V>.json download manifests (STL as base64, SCAD + README as text, pictures by URL)
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile

import numpy as np
import trimesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DOORS = os.path.join(HERE, '..', 'doors')
FILES = os.path.join(HERE, 'files')
IMG = os.path.join(HERE, 'img')
DOORS_V = re.search(r'^version = "([^"]*)"', open(os.path.join(DOORS, 'parallel-lift.scad')).read(), re.M).group(1)
LOW = ['-D', '$fn=20', '-D', 'FNJ=28', '-D', 'N=16']


def echo(scad):
    with tempfile.TemporaryDirectory() as tmp:
        fn = os.path.join(tmp, 'e.echo')
        subprocess.run(['openscad', '-D', 'part="echo"', '-o', fn, os.path.join(DOORS, scad)], check=True, stderr=subprocess.DEVNULL)
        body = open(fn).read().split('GEO ', 1)[1].rsplit('"', 1)[0]
    return {k: eval(v) for k, v in (kv.split('=', 1) for kv in body.split(';'))}


def body(scad, part, tmp):
    fn = os.path.join(tmp, '%s-%s.stl' % (scad, part))
    subprocess.run(['openscad', '-q', '-D', 'part="%s"' % part, *LOW, '-o', fn, os.path.join(DOORS, scad)], check=True)
    m = trimesh.load(fn, force='mesh')
    if len(m.faces) > 3500:
        m = m.simplify_quadric_decimation(face_count=3500)
    return m


def frame_module(side):      # module frame (X back, Y up, Z 0 = bay side .. 22 = cheek) -> scene cm
    s = -1 if side == 'l' else 1
    return np.array([[0, 0, s * 0.1, s * 22.9], [0, 0.1, 0, 0], [-0.1, 0, 0, 0], [0, 0, 0, 1]])


def frame_cheek(side):       # (X back, Y up, W from the cheek face into the bay) -> scene cm
    s = -1 if side == 'l' else 1
    return np.array([[0, 0, -s * 0.1, s * 25.1], [0, 0.1, 0, 0], [-0.1, 0, 0, 0], [0, 0, 0, 1]])


def add(scene, name, m, M, pivot=(0.0, 0.0)):
    m = m.copy(); m.apply_transform(M)              # trimesh keeps the winding right for mirrored frames (left modules)
    piv = np.array([0, pivot[1] / 10, -pivot[0] / 10])
    m.apply_translation(-piv)
    T = np.eye(4); T[:3, 3] = piv
    scene.add_geometry(m, node_name=name, geom_name=name, transform=T)
    return len(m.faces)


def build():
    pl, uo = echo('parallel-lift.scad'), echo('up-over.scad')
    scene = trimesh.Scene(); tri = 0
    with tempfile.TemporaryDirectory() as tmp:
        B = lambda scad, part: body(scad, part, tmp)
        for side, lev in (('l', True), ('r', False)):
            M = frame_module(side)
            tri += add(scene, 'pl_plate_' + side, B('parallel-lift.scad', 'plate_' + side), M)
            tri += add(scene, 'pl_arm1_' + side, B('parallel-lift.scad', 'arm1_' + side), M, pl['P1'])
            tri += add(scene, 'pl_arm2_' + side, B('parallel-lift.scad', 'arm2'), M, pl['P2'])
            tri += add(scene, 'pl_bracket_' + side, B('parallel-lift.scad', 'bracket'), M)
            tri += add(scene, 'uo_plate_' + side, B('up-over.scad', 'plate_' + side), M)
            tri += add(scene, 'uo_arm_' + side, B('up-over.scad', 'arm_' + side), M, uo['F'])
            tri += add(scene, 'uo_bracket_' + side, B('up-over.scad', 'bracket'), M, uo['Q'])
            tri += add(scene, 'uo_track_' + side, B('up-over.scad', 'track_w'), M)
            Mc = frame_cheek(side)
            tri += add(scene, 'ld_channel_' + side, B('lift-door.scad', 'w_channel'), Mc)
        Ml = frame_module('l')
        tri += add(scene, 'pl_mount', B('parallel-lift.scad', 'mount_w'), Ml)
        tri += add(scene, 'uo_mount', B('up-over.scad', 'mount_w'), Ml)
        Mc = frame_cheek('l')
        for p in ('saddle', 'foot', 'clamp'):
            tri += add(scene, 'ld_' + p, B('lift-door.scad', 'w_' + p), Mc)
        tri += add(scene, 'fl_lever', B('flap.scad', 'w_lever'), Mc, (-19, 224))
        tri += add(scene, 'fl_mount', B('flap.scad', 'w_mount'), Mc)
    fn = os.path.join(FILES, 'doors-model-v%s.json' % DOORS_V)
    with open(fn, 'w') as f:
        json.dump({'glb': base64.b64encode(scene.export(file_type='glb')).decode('ascii')}, f)
    print(os.path.basename(fn), tri, 'triangles', os.path.getsize(fn) // 1024, 'kB')

    # download manifests, one per door type
    def stl(name): return {'path': name, 'b64': base64.b64encode(open(os.path.join(DOORS, name), 'rb').read()).decode('ascii')}
    def txt(name): return {'path': name, 'text': open(os.path.join(DOORS, name), encoding='utf-8').read()}
    def pic(name):
        dst = 'doors-' + name
        shutil.copy(os.path.join(DOORS, name), os.path.join(FILES, dst))
        return {'path': name, 'url': 'files/' + dst}
    common = [txt('README.md'), txt('checklib.py'), txt('render.py'), txt('build.sh')]
    sets = {
        'lift': [txt('lift-door.scad'), txt('check_simple.py'), stl('lift_channel.stl'), stl('lift_saddle.stl'), stl('lift_foot.stl'), stl('lift_clamp.stl'), pic('lift_motion.png')],
        'flap': [txt('flap.scad'), txt('check_simple.py'), stl('flap_lever.stl'), stl('flap_mount.stl'), pic('flap_motion.png')],
        'upover': [txt('up-over.scad'), txt('check_upover.py'), stl('coupon.stl'), stl('upover_left.stl'), stl('upover_right.stl'), stl('upover_track_left.stl'),
                   stl('upover_track_right.stl'), stl('upover_mount.stl'), stl('upover_template.stl'), pic('upover_motion.png'), pic('upover_print.png')],
        'parallel': [txt('parallel-lift.scad'), txt('check_parallel.py'), stl('coupon.stl'), stl('parallel_left.stl'), stl('parallel_right.stl'), stl('parallel_mount.stl'),
                     stl('parallel_template.stl'), pic('parallel_motion.png'), pic('parallel_print.png')],
    }
    for k, files in sets.items():
        name = 'doors-%s-v%s.json' % (k, DOORS_V)
        with open(os.path.join(FILES, name), 'w', encoding='utf-8') as f:
            json.dump({'zip': 'robo-garage-door-%s_v%s.zip' % (k, DOORS_V), 'files': common + files}, f, ensure_ascii=False, separators=(',', ':'))
        print(name, os.path.getsize(os.path.join(FILES, name)) // 1024, 'kB')
    for k in ('lift', 'flap', 'upover', 'parallel'):        # page pictures (the card under the parts list)
        im = Image.open(os.path.join(DOORS, k + '_motion.png')).convert('RGB')
        if im.width > 1200: im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
        im.save(os.path.join(IMG, 'doors-%s-v%s.webp' % (k, DOORS_V)), quality=88, method=6)
    outlines()
    return pl, uo



# ---------------- 2D outlines for the side view (simulator/door2d.json, read by build_page.py)
def _svg_polys(path):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    s = open(path).read()
    d = ' '.join(re.findall(r'd="([^"]*)"', s, re.S))
    rings, cur = [], []
    for tok in re.findall(r'[MLz]|-?\d+\.?\d*(?:e-?\d+)?', d):
        if tok == 'M':
            if cur: rings.append(cur)
            cur = []
        elif tok == 'L': pass
        elif tok == 'z':
            if cur: rings.append(cur); cur = []
        else: cur.append(float(tok))
    if cur: rings.append(cur)
    polys = [Polygon([(r[i], -r[i + 1]) for i in range(0, len(r) - 1, 2)]) for r in rings if len(r) >= 6]
    polys.sort(key=lambda p: -p.area); res = []
    for p in polys:
        for i, q in enumerate(res):
            if q.contains(p.representative_point()): res[i] = q.difference(p); break
        else: res.append(p)
    return unary_union(res)


def _path(g, origin=(0.0, 0.0)):
    """shapely geometry (mm, module frame) -> SVG path in side-view units (cm, y down), relative to origin (mm)."""
    out = []
    for p in getattr(g, 'geoms', [g]):
        for ring in [p.exterior] + list(p.interiors):
            pts = ['%.2f,%.2f' % ((x - origin[0]) / 10, -(y - origin[1]) / 10) for x, y in ring.coords[:-1]]
            out.append('M' + ' L'.join(pts) + 'Z')
    return ' '.join(out)


def outlines():
    """2D side outlines (cm, y down) of every printed part for the page's side view -> simulator/door2d.json.
    Fixed parts: absolute. Turning parts: absolute, the page turns them about their pivot. Up & over bracket: relative to its peg Q."""
    from shapely.ops import unary_union
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        def run(scad, args, name):
            fn = os.path.join(tmp, name + '.svg')
            subprocess.run(['openscad', '-q', *args, *LOW, '-o', fn, scad], check=True)
            return _svg_polys(fn)
        def two(scad, parts):                     # 2D parts of the SCAD file's own part list
            return unary_union([run(os.path.join(DOORS, scad), ['-D', 'part="%s"' % p], p) for p in parts]).buffer(0).simplify(0.25)
        def code(scad, src, name):                # any 2D geometry built from the file's modules (use <> renders nothing of its own)
            fn = os.path.join(tmp, name + '.scad')
            open(fn, 'w').write('use <%s>\n%s\n' % (os.path.join(DOORS, scad), src))
            return run(fn, [], name).buffer(0).simplify(0.25)
        pl, uo = echo('parallel-lift.scad'), echo('up-over.scad')
        P1, P2 = ('[%r, %r]' % tuple(pl[k]) for k in ('P1', 'P2'))
        res['pl_plate'] = _path(two('parallel-lift.scad', ['2d_plate_b1_l', '2d_plate_b2_l']))
        res['pl_bracket'] = _path(two('parallel-lift.scad', ['2d_brk_b1', '2d_brk_b2']))
        res['pl_arm1'] = _path(code('parallel-lift.scad', 'arm_b1(%s); arm_b2(%s); lever_hull();' % (P1, P1), 'pl_arm1'))
        res['pl_arm2'] = _path(code('parallel-lift.scad', 'arm_b1(%s); arm_b2(%s);' % (P2, P2), 'pl_arm2'))
        res['pl_mount'] = _path(code('parallel-lift.scad', 'projection() mount_placed();', 'pl_mount'))
        res['uo_plate'] = _path(two('up-over.scad', ['2d_plate_b1_l', '2d_plate_b2_l']))
        res['uo_bracket'] = _path(two('up-over.scad', ['2d_brk_b1', '2d_brk_b2']), uo['Q'])   # relative to the peg: the page turns it there
        res['uo_arm'] = _path(code('up-over.scad', 'arm_b1(); arm_b2(); lever_hull();', 'uo_arm'))
        res['uo_mount'] = _path(code('up-over.scad', 'projection() mount_placed();', 'uo_mount'))
        res['uo_track'] = _path(code('up-over.scad', 'projection() track_world();', 'uo_track'))
        res['fl_lever'] = _path(code('flap.scad', 'lever_profile();', 'fl_lever'))
        res['fl_mount'] = _path(code('flap.scad', 'projection() mount_placed();', 'fl_mount'))
        for k, m in (('saddle', 'saddle_world'), ('foot', 'foot_world'), ('clamp', 'clamp')):
            res['ld_' + k] = _path(code('lift-door.scad', 'projection() %s();' % m, 'ld_' + k))
    res['pl'] = pl; res['uo'] = uo; res['flap'] = echo('flap.scad'); res['lift'] = echo('lift-door.scad')
    fn = os.path.join(HERE, 'door2d.json')
    json.dump(res, open(fn, 'w'), separators=(',', ':'))
    print('door2d.json', os.path.getsize(fn) // 1024, 'kB')


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['outlines']: outlines()        # side-view shapes only (fast)
    else: os.makedirs(FILES, exist_ok=True); os.makedirs(IMG, exist_ok=True); build()
