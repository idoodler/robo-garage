# Build the download manifests + pictures of the simulator page from pcb/out and case/.
# files/pcb-v<V>.json, files/case-v<V>.json: text files inline, PNGs by URL, the gerber zip as a nested zip
# (the page packs them with JSZip and saves through the claude.ai downloads capability).
import glob
import json
import os
import re
import zipfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
FILES = os.path.join(HERE, 'files')
IMG = os.path.join(HERE, 'img')
PCB_OUT = os.path.join(ROOT, 'pcb', 'out')
CASE = os.path.join(ROOT, 'case')

PCB_V = re.search(r"^VERSION = '([^']*)'", open(os.path.join(ROOT, 'pcb', 'gen', 'parts.py')).read(), re.M).group(1)
CASE_V = re.search(r'^version = "([^"]*)"', open(os.path.join(CASE, 'robo-garage-case.scad')).read(), re.M).group(1)


def text(path):
    return {'text': open(path, encoding='utf-8').read()}


def png(src, name):
    Image.open(src).convert('RGB').save(os.path.join(FILES, name), optimize=True)
    return {'url': 'files/' + name}


def manifest(name, zipname, entries):
    with open(os.path.join(FILES, name), 'w', encoding='utf-8') as f:
        json.dump({'zip': zipname, 'files': entries}, f, ensure_ascii=False, separators=(',', ':'))
    print(name, os.path.getsize(os.path.join(FILES, name)) // 1024, 'kB')


os.makedirs(FILES, exist_ok=True)
os.makedirs(IMG, exist_ok=True)
for old in glob.glob(os.path.join(FILES, '*')) + glob.glob(os.path.join(IMG, '*')):
    os.remove(old)

# ---------------- PCB
gz = zipfile.ZipFile(os.path.join(PCB_OUT, 'robo-garage_gerbers_JLCPCB.zip'))
gerbers = [{'path': n, 'text': gz.read(n).decode('utf-8')} for n in gz.namelist()]
pcb = [
    dict(path='README.md', **text(os.path.join(PCB_OUT, 'README.md'))),
    {'path': 'robo-garage_gerbers_JLCPCB.zip', 'zip': gerbers},
    dict(path='robo-garage_BOM_JLCPCB.csv', **text(os.path.join(PCB_OUT, 'robo-garage_BOM_JLCPCB.csv'))),
    dict(path='robo-garage_CPL_JLCPCB.csv', **text(os.path.join(PCB_OUT, 'robo-garage_CPL_JLCPCB.csv'))),
    dict(path='robo-garage-pcb.yaml', **text(os.path.join(PCB_OUT, 'robo-garage-pcb.yaml'))),
    dict(path='render_top.png', **png(os.path.join(PCB_OUT, 'render_top.png'), 'pcb-render_top.png')),
    dict(path='render_bottom.png', **png(os.path.join(PCB_OUT, 'render_bottom.png'), 'pcb-render_bottom.png')),
    dict(path='pin1-check.png', **png(os.path.join(PCB_OUT, 'pin1-check.png'), 'pcb-pin1-check.png')),
    dict(path='kicad/robo-garage.kicad_pro', **text(os.path.join(PCB_OUT, 'kicad', 'robo-garage.kicad_pro'))),
    dict(path='kicad/parts.py', **text(os.path.join(PCB_OUT, 'kicad', 'parts.py'))),
    dict(path='kicad/robo-garage.kicad_pcb', **text(os.path.join(PCB_OUT, 'kicad', 'robo-garage.kicad_pcb'))),
]
manifest('pcb-v%s.json' % PCB_V, 'robo-garage-pcb_v%s.zip' % PCB_V, pcb)

# ---------------- case
case = [
    dict(path='README.md', **text(os.path.join(CASE, 'README.md'))),
    dict(path='base.stl', **text(os.path.join(CASE, 'base.stl'))),
    dict(path='lid_print.stl', **text(os.path.join(CASE, 'lid_print.stl'))),
    dict(path='robo-garage-case.scad', **text(os.path.join(CASE, 'robo-garage-case.scad'))),
    dict(path='pcb_data.scad', **text(os.path.join(CASE, 'pcb_data.scad'))),
    dict(path='gen_pcb_data.py', **text(os.path.join(CASE, 'gen_pcb_data.py'))),
    dict(path='view_assembly.png', **png(os.path.join(CASE, 'view_assembly.png'), 'case-view_assembly.png')),
    dict(path='view_lid_top.png', **png(os.path.join(CASE, 'view_lid_top.png'), 'case-view_lid_top.png')),
]
manifest('case-v%s.json' % CASE_V, 'robo-garage-case_v%s.zip' % CASE_V, case)

# ---------------- pictures for the page (webp)
im = Image.open(os.path.join(PCB_OUT, 'render_top.png')).convert('RGB')
im.resize((1200, round(1200 * im.height / im.width)), Image.LANCZOS).save(os.path.join(IMG, 'pcb-v%s-top.webp' % PCB_V), quality=82)
im = Image.open(os.path.join(CASE, 'view_assembly.png')).convert('RGB')
bg = im.getpixel((0, 0))
px = im.load()
xs = [x for x in range(im.width) for y in range(0, im.height, 4) if px[x, y] != bg]
ys = [y for y in range(im.height) for x in range(0, im.width, 4) if px[x, y] != bg]
im = im.crop((max(min(xs) - 20, 0), max(min(ys) - 20, 0), min(max(xs) + 21, im.width), min(max(ys) + 21, im.height)))
im.resize((1000, round(1000 * im.height / im.width)), Image.LANCZOS).save(os.path.join(IMG, 'case-v%s.webp' % CASE_V), quality=82)
for f in sorted(glob.glob(os.path.join(IMG, '*.webp'))):
    print(os.path.basename(f), Image.open(f).size, os.path.getsize(f) // 1024, 'kB')
