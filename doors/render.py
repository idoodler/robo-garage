#!/usr/bin/env python3
"""PNG previews for the README (OpenSCAD + xvfb-run + Pillow). Usage: python3 render.py <type>  (parallel | lift | flap | upover | all)"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp(prefix='doorpng_')
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)

def png(scad, part, defs=(), camera='0,0,0,55,0,25,500', size=(900, 900), name=None, ortho=True, render=False):
    fn = os.path.join(TMP, (name or part) + '.png')
    cmd = ['xvfb-run', '-a', 'openscad', '-q', '--render' if render else '', '--colorscheme=Tomorrow', f'--imgsize={size[0]},{size[1]}',
           f'--camera={camera}', '--viewall' if camera is None else '', '-D', f'part="{part}"']
    cmd = [c for c in cmd if c]
    if ortho: cmd.append('--projection=o')
    for d in defs: cmd += ['-D', d]
    cmd += ['-o', fn, os.path.join(HERE, scad)]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    return Image.open(fn).convert('RGB')

def row(imgs, labels, out, pad=10, bg=(248, 248, 248)):
    h = max(i.height for i in imgs) + 36; w = sum(i.width for i in imgs) + pad * (len(imgs) - 1)
    canvas = Image.new('RGB', (w, h), (255, 255, 255)); x = 0; dr = ImageDraw.Draw(canvas)
    for im, lab in zip(imgs, labels):
        canvas.paste(im, (x, 36)); dr.text((x + 12, 6), lab, fill=(20, 20, 20), font=FONT); x += im.width + pad
    canvas.save(os.path.join(HERE, out), optimize=True); print(out, canvas.size)

def top_view(cx, cy, dist=800):      # looking from the cheek side (+Z) at the X-Y plane
    return f'{cx},{cy},{dist},{cx},{cy},0'

def parallel():
    poses = [(0, 'closed'), (0.5, 'half way: 40 mm out (max)'), (1, 'open: 23 mm out, 116 mm up')]
    imgs = [png('parallel-lift.scad', 'scene', [f'pose={p}'], top_view(95, 262, 1500), (520, 800), name=f'pl_{i}') for i, (p, _) in enumerate(poses)]
    row(imgs, [l for _, l in poses], 'parallel_motion.png')
    lay = png('parallel-lift.scad', 'layout', [], '225,110,0,0,0,0,800', (1100, 560), name='pl_layout', ortho=True)
    lay.save(os.path.join(HERE, 'parallel_print.png'), optimize=True); print('parallel_print.png', lay.size)

def upover():
    poses = [(0, 'closed'), (0.35, 'tilting: 35 mm out (max)'), (0.7, 'nearly open'), (1, 'open: inside, 13 mm out')]
    imgs = [png('up-over.scad', 'scene', [f'pose={p}'], top_view(95, 262, 1500), (440, 800), name=f'uo_{i}') for i, (p, _) in enumerate(poses)]
    row(imgs, [l for _, l in poses], 'upover_motion.png')
    lay = png('up-over.scad', 'layout', [], '225,110,0,0,0,0,800', (1100, 560), name='uo_layout', ortho=True)
    lay.save(os.path.join(HERE, 'upover_print.png'), optimize=True); print('upover_print.png', lay.size)

def lift():
    imgs = [png('lift-door.scad', 'scene', [f'pose={p}'], top_view(60, 230, 1300), (440, 760), name=f'ld_{i}') for i, p in enumerate((0, 1))]
    s = png('lift-door.scad', 'set', [], '100,110,30,55,0,25,520', (700, 760), name='ld_set', ortho=False)
    row(imgs + [s], ['closed', 'open: 150 mm up', 'prints (one bed)'], 'lift_motion.png')

def flap():
    imgs = [png('flap.scad', 'scene', [f'pose={p}'], top_view(-20, 320, 1500), (520, 760), name=f'fl_{i}') for i, p in enumerate((0, 0.5, 1))]
    s = png('flap.scad', 'set', [], '70,100,10,55,0,25,420', (600, 760), name='fl_set', ortho=False)
    row(imgs + [s], ['closed', 'half', 'open 90°', 'prints'], 'flap_motion.png')

if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    for k, fn in [('parallel', parallel), ('upover', upover), ('lift', lift), ('flap', flap)]:
        if what in (k, 'all'): fn()
