# Door mechanisms v2 (doors/*.scad) in the simulator page: printed parts in the side view and in 3D, an open-state
# slider for every door type, the "Door parts" card with downloads. exec'd by build_page.py after build_js.py
# (uses rep() and s from there). Needs simulator/door2d.json, img/doors-*.webp and files/doors-*.json
# (build_files.py -> build_door_files.py).
import io
import json
import math
import zipfile
import base64
import trimesh
from PIL import Image

D2 = json.load(open(os.path.join(HERE, 'door2d.json'), encoding='utf-8'))
DV = D2['pl']['version']
PLd, UOd, FLd, LDd = D2['pl'], D2['uo'], D2['flap'], D2['lift']
TYPES = ('lift', 'flap', 'upover', 'parallel')
DOORS_DIR = os.path.join(HERE, '..', 'doors')


def cm(v): return round(v / 10, 5)
def P(p): return '[%s,%s]' % (json.dumps(cm(p[0])), json.dumps(cm(p[1])))
def between(a, b, first=False):
    assert first or s.count(a) == 1, 'marker not unique: ' + a
    i = s.index(a)
    return s[i:s.index(b, i)]
def path(key, cls, extra=''): return '<path class="%s"%s d="%s"/>' % (cls, extra, D2[key])
def pin(p, r=.35, rel=(0, 0)):
    return '<circle cx="%.2f" cy="%.2f" r="%s" fill="#e5a50a"/>' % ((p[0] - rel[0]) / 10, -(p[1] - rel[1]) / 10, r)
def T(src, **kw):
    for k, v in kw.items(): src = src.replace('@@' + k + '@@', v)
    assert '@@' not in src, src[src.index('@@') - 80:src.index('@@') + 80]
    return src


# ---------------------------------------------------------------- numbers from the SCAD files
def dirv(a): return (math.cos(math.radians(a)), math.sin(math.radians(a)))
PL_C0 = [PLd['P1'][0] + PLd['LEV'] * dirv(PLd['LEV_A'])[0], PLd['P1'][1] + PLd['LEV'] * dirv(PLd['LEV_A'])[1]]
UO_C0 = UOd['C0']


def grams(names):          # rough filament mass: 3 perimeters (≈1.35 mm shell) + 20 % infill, PETG 1.27 g/cm³
    g = 0
    for n in names:
        m = trimesh.load(os.path.join(DOORS_DIR, n), force='mesh')
        v, a = m.volume / 1000, m.area / 100
        sv = min(v, a * 0.135)
        g += (sv + 0.2 * max(0, v - sv)) * 1.27
    return int(round(g / 10) * 10) if g < 200 else int(round(g / 50) * 50)


PRINTS = {
    'lift': ['lift_channel.stl'] * 4 + ['lift_saddle.stl', 'lift_foot.stl', 'lift_clamp.stl'],
    'flap': ['flap_lever.stl', 'flap_mount.stl'],
    'upover': ['upover_left.stl', 'upover_right.stl', 'upover_track_left.stl', 'upover_track_right.stl', 'upover_mount.stl',
               'upover_template.stl', 'coupon.stl'],
    'parallel': ['parallel_left.stl', 'parallel_right.stl', 'parallel_mount.stl', 'parallel_template.stl', 'coupon.stl'],
}
G = {k: grams(v) for k, v in PRINTS.items()}


def zip_kb(k):             # size of the zip the page packs from files/doors-<k>-v<V>.json
    man = json.load(open(os.path.join(HERE, 'files', 'doors-%s-v%s.json' % (k, DV)), encoding='utf-8'))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in man['files']:
            if 'b64' in f: z.writestr(f['path'], base64.b64decode(f['b64']))
            elif 'url' in f: z.write(os.path.join(HERE, f['url']), f['path'])
            else: z.writestr(f['path'], f['text'])
    return len(buf.getvalue()) / 1024


def mb(kb): return '%.1f MB' % (kb / 1024) if kb >= 1000 else '%d kB' % (round(kb / 10) * 10)


PICS = {}
for k, alt, cap in (
        ('lift', 'Lift door: side view closed and open, and the printed channels, saddle, foot and clamp',
         'Lift door · closed, open · all prints on one bed'),
        ('flap', 'Flap out: side view closed, half and open, with the printed lever and top mount',
         'Flap out · closed, half, open · lever + top mount'),
        ('upover', 'Up & over: side view closed, tilting, nearly open and open, with the printed modules and tracks',
         'Up & over · closed, tilting, nearly open, open'),
        ('parallel', 'Parallel lift: side view closed, half way and open, with the printed modules',
         'Parallel lift · closed, half way, open')):
    src = 'img/doors-%s-v%s.webp' % (k, DV)
    w, h = Image.open(os.path.join(HERE, src)).size
    PICS[k] = [src, w, h, alt, cap]

# ---------------------------------------------------------------- CSS
rep('</style>', '''.dpos{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;margin-bottom:8px}
.dpos input[type=range]{flex:1 1 150px;min-width:120px;margin:0;accent-color:var(--accent)}
.dpos output{font-family:var(--mono);font-size:.78rem;min-width:3.2em;text-align:right}
.dpos .dposI{font-family:var(--mono);font-size:.74rem}
.btn.sm{padding:4px 10px;font-size:.8rem}
#dpTab td:last-child{white-space:nowrap}
.pp,.pm{fill-rule:evenodd;stroke-linejoin:round}
.pp{fill:#a7c8ee;fill-opacity:.65;stroke:#4f7fb8;stroke-width:.1}
.pm{fill:#3f86d8;fill-opacity:.92;stroke:#1f4f8c;stroke-width:.1}
</style>''')

# ---------------------------------------------------------------- open slider (3D card + side view card, kept in sync)
DPOS = ('<div class="dpos"><span class="lbl">Door open</span><input type="range" class="dposR" min="0" max="100" step="1" value="0" '
        'aria-label="Door open state in percent"><output class="dposV">0 %</output><button class="btn sm dposA" aria-pressed="true" '
        'title="On: the cleaning simulation moves the door. Drag the slider to hold the door yourself.">Auto</button>'
        '<span class="lbl dposI"></span></div>\n')
rep('    <div class="three" id="three">', '    ' + DPOS + '    <div class="three" id="three">')
rep('<div class="vhead"><h2>How it works · side cut-away</h2></div>\n',
    '<div class="vhead"><h2>How it works · side cut-away</h2></div>\n    ' + DPOS)

# ---------------------------------------------------------------- side view: the 4 door types with their printed parts
ACT = ('<line id="@@ID@@Body" x1="0" y1="0" x2="0" y2="0" stroke="#5b6370" stroke-width="2.4" stroke-linecap="round"/>'
       '<line id="@@ID@@Rod" x1="0" y1="0" x2="0" y2="0" stroke="#9aa3ae" stroke-width="1" stroke-linecap="round"/>')
uoQ = UOd['Q']
uo_door = '%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f' % (
    (-19 - uoQ[0]) / 10, -(17 - uoQ[1]) / 10, (0 - uoQ[0]) / 10, -(17 - uoQ[1]) / 10,
    (0 - uoQ[0]) / 10, -(UOd['DOOR_TOP'] - uoQ[1]) / 10, (-19 - uoQ[0]) / 10, -(UOd['DOOR_TOP'] - uoQ[1]) / 10)
SIDE = T('''        <!-- door type: lift – 6 mm panel in 4 printed channels, rod pushes a printed saddle -->
        <g id="dLift" style="display:none">
          <g class="part" data-part="channels" tabindex="0" role="button" aria-label="Printed door channels">
            <rect class="pp" x=".2" y="-20.5" width="2" height="19"/><rect class="pp" x=".2" y="-39.5" width="2" height="19"/>
          </g>
          <g class="part" data-part="door" tabindex="0" role="button" aria-label="Lift door">
            <g id="ldMove"><rect x=".4" y="-23.5" width=".6" height="22" fill="var(--front)" stroke="var(--dockline)" stroke-width=".12"/>@@SADDLE@@</g>
          </g>
          <g class="part" data-part="actuator" tabindex="0" role="button" aria-label="Linear actuator">
            @@FOOT@@@@CLAMP@@
            <line x1="3.2" y1="-3" x2="3.2" y2="-22.5" stroke="#5b6370" stroke-width="2.8"/>
            <line id="ldRod" x1="3.2" y1="-22.5" x2="3.2" y2="-25.5" stroke="#9aa3ae" stroke-width="1.4"/>
            <circle id="ldEye" cx="3.2" cy="-25.5" r=".9" fill="#9aa3ae" stroke="#5b6370" stroke-width=".15"/>@@FOOTPIN@@
          </g>
        </g>
        <!-- door type: flap out – printed lever on the flap, printed top mount -->
        <g id="dFlap">
          <g class="part" data-part="flap" tabindex="0" role="button" aria-label="Outward flap">
            <polygon id="flapP" points="" fill="var(--front)" stroke="var(--dockline)" stroke-width=".15"/>
            <g id="flapLev">@@LEVER@@@@PINPIN@@</g>
            <circle cx="-1.9" cy="-22.4" r=".6" fill="#e5a50a"/>
          </g>
          <g class="part" data-part="actuator" tabindex="0" role="button" aria-label="Flap actuator">
            @@FMOUNT@@@@FACT@@@@FPIN@@
          </g>
        </g>
        <!-- door type: up & over – 2 printed modules (plate, arm + lever, door bracket with peg) + printed tracks -->
        <g id="dUO" style="display:none">
          <g class="part" data-part="uo" tabindex="0" role="button" aria-label="Up and over mechanism">
            @@UPLATE@@@@UTRACK@@
            <g id="uoMove"><polygon points="@@UODOOR@@" fill="var(--front)" stroke="var(--dockline)" stroke-width=".15"/>@@UBRK@@@@UQPIN@@@@UDPIN@@</g>
            <g id="uoArm">@@UARM@@@@UCPIN@@</g>@@UFPIN@@
          </g>
          <g class="part" data-part="actuator" tabindex="0" role="button" aria-label="Up and over actuator">
            @@UMOUNT@@@@UACT@@@@UAPIN@@
          </g>
        </g>
        <!-- door type: parallel lift – 2 print-in-place modules (plate, 2 arms, lever, door bracket) -->
        <g id="dPar" style="display:none">
          <g class="part" data-part="par" tabindex="0" role="button" aria-label="Parallel lift mechanism">
            @@PPLATE@@
            <g id="parMove"><polygon points="-1.9,-1.7 0,-1.7 0,-20.3 -1.8,-22.1 -1.9,-22.1" fill="var(--front)" stroke="var(--dockline)" stroke-width=".15"/>@@PBRK@@@@PA1@@@@PA2@@</g>
            <g id="parArm2">@@PARM2@@</g>
            <g id="parArm1">@@PARM1@@<rect x="@@SQX@@" y="@@SQY@@" width=".8" height=".8" fill="#9ba2ac" stroke="#5b6370" stroke-width=".08"/>@@PCPIN@@</g>@@PP1@@@@PP2@@
          </g>
          <g class="part" data-part="actuator" tabindex="0" role="button" aria-label="Parallel lift actuator">
            @@PMOUNT@@@@PACT@@@@PFPIN@@
          </g>
        </g>
''',
    SADDLE=path('ld_saddle', 'pm'), FOOT=path('ld_foot', 'pp'), CLAMP=path('ld_clamp', 'pp'), FOOTPIN=pin((32, 30), .4),
    LEVER=path('fl_lever', 'pm'), PINPIN=pin(FLd['PIN'], .4), FMOUNT=path('fl_mount', 'pp'), FACT=T(ACT, ID='flap'), FPIN=pin(FLd['F'], .5),
    UPLATE=path('uo_plate', 'pp'), UTRACK=path('uo_track', 'pp'), UODOOR=uo_door, UBRK=path('uo_bracket', 'pm'),
    UQPIN=pin(uoQ, .3, uoQ), UDPIN=pin(UOd['D'], .35, uoQ), UARM=path('uo_arm', 'pm'), UCPIN=pin(UO_C0, .4), UFPIN=pin(UOd['F'], .45),
    UMOUNT=path('uo_mount', 'pp'), UACT=T(ACT, ID='uo'), UAPIN=pin(UOd['FA'], .5),
    PPLATE=path('pl_plate', 'pp'), PBRK=path('pl_bracket', 'pm'), PA1=pin(PLd['A1'], .35), PA2=pin(PLd['A2'], .35),
    PARM2=path('pl_arm2', 'pm'), PARM1=path('pl_arm1', 'pm'), SQX='%.2f' % (PLd['P1'][0] / 10 - .4), SQY='%.2f' % (-PLd['P1'][1] / 10 - .4),
    PCPIN=pin(PL_C0, .4), PP1=pin(PLd['P1'], .45), PP2=pin(PLd['P2'], .45), PMOUNT=path('pl_mount', 'pp'), PACT=T(ACT, ID='par'), PFPIN=pin(PLd['F'], .5))
rep(between('        <!-- door type: lift -->', '        <g class="part" data-part="reed"'), SIDE)

# ---------------------------------------------------------------- "Door parts" card (before the PCB card) + BOM rows
ROWS = {
    'lift': ('Lift door', '4 channels, saddle, foot, clamp'),
    'flap': ('Flap out', 'lever, actuator top mount'),
    'upover': ('Up &amp; over', '2 print-in-place modules, 2 tracks, top mount, drill template'),
    'parallel': ('Parallel lift', '2 print-in-place modules, top mount, drill template'),
}
KB = {k: zip_kb(k) for k in TYPES}
card = '''<section class="card" style="margin-top:14px" id="doorparts">
  <div class="vhead"><h2>Door parts v@@DV@@ · 3D print</h2><span class="lbl">OpenSCAD · PETG · no supports · all files open</span></div>
  <div class="cols2">
    <figure class="shot light"><img id="dpImg" src="@@SRC@@" width="@@W@@" height="@@H@@" loading="lazy" alt="@@ALT@@"><figcaption id="dpCap">@@CAP@@</figcaption></figure>
    <div>
      <div class="tablewrap"><table id="dpTab"><thead><tr><th>Door</th><th>Printed</th><th class="num">PETG</th><th>Out open / moving</th></tr></thead><tbody>
@@ROWS@@      </tbody></table></div>
      <p class="note">PETG, 0.2 mm layers, 3 perimeters, 20 % infill, no supports, 220 × 220 mm bed. Up &amp; over and parallel lift print in place:
      plate, arms, lever and door bracket come off the bed already joined. Print <code>coupon.stl</code> first and pick the joint gap that turns
      freely (0.45 mm default). Each zip has the STL, the OpenSCAD source, the check scripts and a README with the mounting steps.
      Drag the <b>Door open</b> slider above the 3D model to see every part move.</p>
    </div>
  </div>
  <div class="dl">
@@BTNS@@    <span class="note dlnote" role="status">Checking downloads…</span>
  </div>
</section>

'''
p0 = PICS['flap']
card = T(card, DV=DV, SRC=p0[0], W=str(p0[1]), H=str(p0[2]), ALT=p0[3], CAP=p0[4],
         ROWS=''.join('        <tr data-d="%s"><td>%s</td><td>%s</td><td class="num">≈ %d g</td><td data-o="%s"></td></tr>\n'
                      % (k, ROWS[k][0], ROWS[k][1], G[k], k) for k in TYPES),
         BTNS=''.join('    <button class="btn primary" data-dl="d%s" disabled>⬇ %s · STL + OpenSCAD (zip, %s)</button>\n'
                      % (k, ROWS[k][0], mb(KB[k])) for k in TYPES))
rep('<section class="card" style="margin-top:14px" id="pcb">', card + '<section class="card" style="margin-top:14px" id="pcb">')

old_rows = between('      <tr data-door="lift">', '\n    </tbody>', first=True)
hinge = [l for l in old_rows.split('\n') if 'Piano hinge' in l]
assert len(hinge) == 1
rep(old_rows, '\n'.join([
    '      <tr data-door="lift"><td>3D-printed PETG ≈ %d g: 4 door channels, saddle, foot, clamp (STL in "Door parts" below) – or alu U-profile 10×10×1 mm for the channels</td><td>–</td><td class="num">2–3</td><td>–</td></tr>' % G['lift'],
    '      <tr data-door="lift"><td>MDF 6 mm door 49.6×22, PTFE tape, M3×16 bolt + nut, 2 front legs 4.9×20.8 from the 18 mm MDF</td><td>–</td><td class="num">4–7</td><td>store</td></tr>',
    hinge[0],
    '      <tr data-door="flap"><td>3D-printed PETG ≈ %d g: lever + actuator top mount (STL in "Door parts" below)</td><td>–</td><td class="num">1–2</td><td>–</td></tr>' % G['flap'],
    '      <tr data-door="flap"><td>Flap 59.6×20.7 from the 18 mm MDF, 2 M6 bolts + nyloc nuts, screws</td><td>–</td><td class="num">2–4</td><td>store</td></tr>',
    '      <tr data-door="upover"><td>3D-printed PETG ≈ %d g: 2 print-in-place modules, 2 tracks, top mount, drill template (STL in "Door parts" below)</td><td>–</td><td class="num">8–10</td><td>–</td></tr>' % G['upover'],
    '      <tr data-door="upover"><td>Door 49.2×20.2 + 2 front legs 4.9×20.8 from the 18 mm MDF, 2 M6 bolts + nyloc nuts, screws</td><td>–</td><td class="num">4–6</td><td>store</td></tr>',
    '      <tr data-door="parallel"><td>3D-printed PETG ≈ %d g: 2 print-in-place modules, top mount, drill template (STL in "Door parts" below)</td><td>–</td><td class="num">9–12</td><td>–</td></tr>' % G['parallel'],
    '      <tr data-door="parallel"><td>Square rod 8×8 mm, 1 m (steel or alu), cut to 48.4 cm – couples the two sides</td><td>1</td><td class="num">4–7</td><td>store</td></tr>',
    '      <tr data-door="parallel"><td>Door 49.2×20.4 with a 45° chamfer on the top back edge + 2 front legs 4.9×20.8 from the 18 mm MDF, 2 M6 bolts + nyloc nuts, screws</td><td>–</td><td class="num">4–6</td><td>store</td></tr>']))
rep("DP={lift:[8.09,17.89],flap:[11.79,15.79],upover:[13.09,26.89],parallel:[9.15,23.05]}",
    "DP={lift:[6,10],flap:[9.79,12.79],upover:[12,16],parallel:[17,25]}")

# ---------------------------------------------------------------- door texts
rep("extra:'2 alu channels'", "extra:'4 printed channels, saddle, foot, clamp'")
rep("note:'Lift door: a 6 mm panel rides in two alu channels behind the drawer front. The actuator in the left corner pushes it up from below;",
    r"note:'Lift door: a 6 mm panel rides in four printed channels behind the drawer front. The actuator stands in the left corner in a printed foot and clamp and pushes a printed saddle on the panel\'s top corner;")
rep("drive:'actuator on the left cheek pushes down and back on an L-bracket – the flap swings up and out to 90°'",
    "drive:'actuator on the left cheek pushes a printed lever down and back – the flap swings up and out to 90°'")
rep("extra:'piano hinge, L-bracket'", "extra:'piano hinge, printed lever + top mount'")
rep("A steel L-bracket on its back reaches 9 cm above the hinge; the actuator stands right behind the drawer front on the left cheek, leans back 3–7° and pushes the bracket down and back",
    "A printed lever on its back reaches 9 cm above the hinge; the actuator hangs from a printed mount right behind the drawer front on the left cheek and pushes the lever down and back")
rep("Max ≈25 N of its 50 N, at least 6 cm lever (no dead point), and the bay floor stays free.",
    "Max ≈21 N of its 50 N, at least 6 cm lever (no dead point), and the bay floor stays free.")
rep("drive:'actuator pulls the top edge in along 2 short tracks; 2 arms tilt it up'",
    "drive:'2 printed arms tilt it up while pegs on its brackets slide back in 2 printed tracks'")
rep("extra:'2 tracks, 2 arms, rollers'", "extra:'2 print-in-place modules, 2 tracks, top mount'")
rep(r"note:'Up & over: like a small garage door. The flap\'s top edge runs inward in two short tracks while two arms tilt it up – open, it forms a ≈8 cm canopy (≈11 cm while moving).",
    r"note:'Up & over: like a small garage door. A peg on each door bracket slides 6.7 cm back in a printed track while a printed arm tilts the door up. Open, it lies flat inside the cabinet 13.7 cm above the tray – only 1.3 cm in front of the drawer front (3.5 cm while moving). Door 49.2 × 20.2 cm.")
rep("drive:'actuator + lever turn 4 parallel arms – door stays vertical, moves out, then up on a circle'",
    "drive:'actuator + lever turn 4 printed arms – the door stays vertical, comes out ≤ 4 cm, then lifts on a circle'")
rep("extra:'4 arms, 2 brackets, lever'", "extra:'2 print-in-place modules, top mount, 8 mm rod'")
rep("note:'Parallel lift: 4 arms (2 per side, 10 cm) form a parallelogram, so the door stays vertical. It first moves straight out, then up on a circle and parks 12.6 cm higher in front of the drawer front (≈10 cm out). The actuator turns the rear-left arm via a lever.",
    r"note:'Parallel lift: two print-in-place modules, each with 2 arms (7.7 cm) that turn 100° as a parallelogram, so the door stays vertical. It comes out at most 4 cm, then lifts on a circle and parks 11.6 cm higher, only 2.3 cm in front of the drawer front (3.5 mm gap). A 45° chamfer on the door\'s top back edge lets it pass the drawer front. The actuator turns the left front arm via a lever; an 8 mm square rod couples both sides.")

rep(" door:['Lift door','6 mm MDF 49.6×22 cm in two alu channels behind the drawer front. Lifts 15 cm → 15 cm opening. Drops by its own weight – cannot pinch.'],",
    " door:['Lift door','6 mm MDF 49.6×22 cm in 4 printed channels behind the drawer front. The actuator rod pushes a printed saddle on its top left corner (M3 bolt, hidden behind the drawer front): lifts 14.7 cm. Drops by its own weight – cannot pinch.'],")
rep(" channels:['Alu U-profile 10×10×1 mm','Two 38 cm pieces on the drawer cheeks; 8 mm inside, so the 6 mm door slides freely (add PTFE tape).'],",
    " channels:['Door channels · printed','4 PETG channels, 19 cm, 2 per side one above the other – a piece of 1.75 mm filament in the end holes lines them up. 8 mm inside, so the 6 mm panel slides freely. Same size as the alu U-profile 10×10×1 mm, which still works. Download: \"Door parts\" below.'],")
rep(between(" par:['Parallel lift (4 arms)'", " esp:['"), T(r""" par:['Parallel lift · printed modules','Two print-in-place modules on the cheeks: plate, 2 arms (7.7 cm), lever and door bracket come off the printer already joined (0.45 mm joint gap). The arms turn 100°: the door stays vertical, comes out at most 4 cm, then lifts and parks 11.6 cm higher, 2.3 cm in front of the drawer front. Needs a 45° chamfer on the door\'s top back edge. Actuator max ≈14 N via a 9.8 cm lever on the left front arm; an 8 mm square rod couples both sides. INA219 stall stop. Download: "Door parts" below.'],
 flap:['Flap out (90°)','Flush 18 mm flap on a piano hinge. A printed lever on its back reaches 9 cm above the hinge; the actuator hangs from a printed mount right behind the drawer front on the left cheek and pushes the lever down and back – the flap swings up and out to 90°, ≈21 cm. Max ≈21 N of its 50 N, at least 6 cm lever all the way (also to pull it shut). The self-locking actuator holds the flap shut while you pull the drawer. INA219 stall stop. Download: "Door parts" below.'],
 uo:['Up & over · printed modules','Garage style: a peg on each door bracket slides 6.7 cm back in a printed track while a printed arm tilts the door up. Open, it lies flat 13.7 cm above the tray over the robot, only 1.3 cm in front of the drawer front (3.5 cm while moving). 2 print-in-place modules (arm, lever, bracket), 2 tracks, top mount; door 49.2×20.2 cm. Actuator max ≈39 N via a 15 cm lever. INA219 stall stop. Download: "Door parts" below.'],
"""))

# ---------------------------------------------------------------- kinematics (generated from the SCAD echo values)
KIN = T(r'''/* ---------- door mechanisms (printed parts, doors/ v@@DV@@) – cm: x = depth behind the door's back face (front face of the drawer front = -1.9), y = up from the floor ---------- */
const RAD=Math.PI/180;
const rcw=(p,a)=>[p[0]*Math.cos(a)+p[1]*Math.sin(a),-p[0]*Math.sin(a)+p[1]*Math.cos(a)];   /* turn clockwise by a */
/* lift door: the rod pushes a printed saddle on the panel; @@AIR@@ cm air when closed */
const LD={tip:@@TIP@@,air:@@AIR@@,stroke:@@STROKE@@};
function ldState(f){return{lift:Math.max(0,LD.stroke*f-LD.air),tip:LD.tip+LD.stroke*f};}
/* flap out: hinge H, printed lever pin behind / above it, actuator top pivot F on the left cheek */
const FL={px:@@HX@@,py:@@HY@@,H:@@FH@@,pin:@@PIN@@,F:@@FF@@};
function rotP(rel,th){const u=-rel[0],y=rel[1];const ur=u*Math.cos(th)-y*Math.sin(th),yr=u*Math.sin(th)+y*Math.cos(th);return[FL.px-ur,FL.py+yr];}
/* up & over: the peg Q on each door bracket slides back in a printed track while the door turns 90° clockwise; arm F→D, lever on the left arm, actuator from FA */
const UO={Q:@@UQ@@,D:@@UD@@,F:@@UF@@,L:@@UL@@,lev:@@ULEV@@,levA:@@ULEVA@@,FA:@@UFA@@,bot:1.7,top:@@UTOP@@};
function uoState(f){const ps=f*Math.PI/2,u=rcw([UO.D[0]-UO.Q[0],UO.D[1]-UO.Q[1]],ps),h=UO.Q[1]+u[1]-UO.F[1],
 s=UO.F[0]-UO.Q[0]-u[0]-Math.sqrt(Math.max(0,UO.L*UO.L-h*h)),Q=[UO.Q[0]+s,UO.Q[1]],D=[Q[0]+u[0],Q[1]+u[1]],
 v0=[UO.D[0]-UO.F[0],UO.D[1]-UO.F[1]],v1=[D[0]-UO.F[0],D[1]-UO.F[1]],ar=Math.atan2(v0[0]*v1[1]-v0[1]*v1[0],v0[0]*v1[0]+v0[1]*v1[1]),la=UO.levA*RAD+ar;
 return{ps,s,Q,D,ar,C:[UO.F[0]+UO.lev*Math.cos(la),UO.F[1]+UO.lev*Math.sin(la)]};}
function uoPt(st,p){const r=rcw([p[0]-UO.Q[0],p[1]-UO.Q[1]],st.ps);return[st.Q[0]+r[0],st.Q[1]+r[1]];}
/* parallel lift: 4 printed arms R (2 per side) turn sw° clockwise from th0: the door stays vertical, comes out, then lifts; lever on the left front arm */
const PL={R:@@PR@@,th0:@@PTH0@@,sw:@@PSW@@,P1:@@PP1@@,P2:@@PP2@@,lev:@@PLEV@@,levA:@@PLEVA@@,F:@@PF@@,
 door:[[-1.9,1.7],[0,1.7],[0,20.3],[-1.8,22.1],[-1.9,22.1]]};
function plState(f){const a=(PL.th0-PL.sw*f)*RAD,a0=PL.th0*RAD,b=(PL.levA-PL.sw*f)*RAD;
 return{ar:-PL.sw*f*RAD,T:[PL.R*(Math.cos(a)-Math.cos(a0)),PL.R*(Math.sin(a)-Math.sin(a0))],C:[PL.P1[0]+PL.lev*Math.cos(b),PL.P1[1]+PL.lev*Math.sin(b)]};}
/* how far the door comes out in front of the drawer front, and the free height under it (cm) */
function doorGeo(t,f){let P;
 if(t==='lift')return{out:0,clear:1.5+ldState(f).lift};
 if(t==='flap'){const th=f*Math.PI/2;P=[[0,0],[0,-FL.H],[1.9,-FL.H],[1.9,0]].map(p=>rotP(p,th));}
 else if(t==='upover'){const st=uoState(f);P=[[-1.9,UO.bot],[0,UO.bot],[0,UO.top],[-1.9,UO.top]].map(p=>uoPt(st,p));}
 else{const T=plState(f).T;P=PL.door.map(p=>[p[0]+T[0],p[1]+T[1]]);}
 return{out:Math.max(0,-1.9-Math.min(...P.map(p=>p[0]))),clear:Math.min(...P.map(p=>p[1]))};}
(()=>{const fm=v=>v<.05?'0 cm':'≈ '+(v<9.95?v.toFixed(1):Math.round(v))+' cm';
 Object.keys(DOORS).forEach(k=>{let m=0;for(let i=0;i<=200;i++)m=Math.max(m,doorGeo(k,i/200).out);DOORS[k].out=fm(doorGeo(k,1).out);DOORS[k].move=fm(m);});})();
''', DV=DV, TIP=json.dumps(cm(LDd['tip_y'])), AIR=json.dumps(cm(LDd['seat_y'] - LDd['tip_y'])), STROKE=json.dumps(cm(LDd['stroke'])),
    HX=json.dumps(cm(FLd['H'][0])), HY=json.dumps(cm(FLd['H'][1])), FH=json.dumps(cm(FLd['H'][1] - 17)),
    PIN=P([FLd['PIN'][0] - FLd['H'][0], FLd['PIN'][1] - FLd['H'][1]]), FF=P(FLd['F']),
    UQ=P(UOd['Q']), UD=P(UOd['D']), UF=P(UOd['F']), UL=json.dumps(cm(UOd['L'])), ULEV=json.dumps(cm(UOd['LEV'])),
    ULEVA=json.dumps(UOd['LEV_A']), UFA=P(UOd['FA']), UTOP=json.dumps(cm(UOd['DOOR_TOP'])),
    PR=json.dumps(cm(PLd['R'])), PTH0=json.dumps(PLd['TH0']), PSW=json.dumps(PLd['SWING']), PP1=P(PLd['P1']), PP2=P(PLd['P2']),
    PLEV=json.dumps(cm(PLd['LEV'])), PLEVA=json.dumps(PLd['LEV_A']), PF=P(PLd['F']))
rep(between('/* flap out geometry (cm, xs = depth from front, y = up) */', '/* ---------- phases ---------- */'), KIN)
rep("const SIM=window.SIM={S,PH,MODES,FL,UO,PL,rotP,uoState,plState,led:null,",
    "const SIM=window.SIM={S,PH,MODES,FL,UO,PL,LD,rotP,uoState,uoPt,plState,ldState,doorGeo,led:null,")
rep("const S={btnT:-9,ph:0,pt:0,rod:0,door:0,", "const S={btnT:-9,ph:0,pt:0,rod:0,door:0,man:null,simDoor:0,simRod:0,")

# ---------------------------------------------------------------- slider: hold the door anywhere, Auto gives it back to the simulation
rep("function step(dt){\n S.t+=dt;", """/* the open slider holds the door; the simulation keeps its own door position underneath (S.simDoor / S.simRod) */
function step(dt){
 if(S.man==null){stepSim(dt);return;}
 S.door=S.simDoor;S.rod=S.simRod;stepSim(dt);S.simDoor=S.door;S.simRod=S.rod;S.door=S.rod=S.man;
}
function stepSim(dt){
 S.t+=dt;""")
rep("function start(){\n const id=pid();", "function start(){\n manOff();\n const id=pid();")
rep("E('doorGrpName').textContent=DOORS[v].name;updTotals();", "E('doorGrpName').textContent=DOORS[v].name;updTotals();doorCard(v);")
rep("E('bAuto').onclick=()=>{S.auto=!S.auto;setP(E('bAuto'),S.auto);log(S.auto?'Auto demo on':'Auto demo off');};",
    T("""E('bAuto').onclick=()=>{S.auto=!S.auto;setP(E('bAuto'),S.auto);log(S.auto?'Auto demo on':'Auto demo off');};
/* ---------- door open slider (3D card + side view) ---------- */
const dpR=[...document.querySelectorAll('.dposR')],dpV=[...document.querySelectorAll('.dposV')],dpA=[...document.querySelectorAll('.dposA')],dpI=[...document.querySelectorAll('.dposI')];
function manSet(v){if(S.man==null){S.simDoor=S.door;S.simRod=S.rod;if(S.auto)E('bAuto').click();log('Door held by the slider – Auto gives it back');}
 S.man=clamp(v,0,1);S.door=S.rod=S.man;dpA.forEach(b=>setP(b,false));}
function manOff(){if(S.man==null)return;S.man=null;S.door=S.simDoor;S.rod=S.simRod;dpA.forEach(b=>setP(b,true));}
dpR.forEach(r=>r.addEventListener('input',()=>manSet(r.value/100)));
dpA.forEach(b=>b.addEventListener('click',()=>{if(S.man==null)manSet(S.door);else{manOff();log('Door back to the simulation');}}));
E('bAuto').addEventListener('click',()=>{if(S.auto)manOff();});
function updDoorPos(){const g=doorGeo(S.doorType,S.door),p=Math.round(S.door*100),info=Math.round(g.out*10)+' mm out · '+Math.round(g.clear*10)+' mm clear';
 dpR.forEach(r=>{if(+r.value!==p)r.value=p;});dpV.forEach(o=>o.textContent=p+' %');dpI.forEach(o=>o.textContent=info);}
/* door parts card: picture + highlighted row follow the door switch */
const DPIC=@@PICS@@;
function doorCard(v){const p=DPIC[v],im=E('dpImg');if(!p||!im)return;im.src=p[0];im.width=p[1];im.height=p[2];im.alt=p[3];E('dpCap').textContent=p[4];
 document.querySelectorAll('#dpTab tr[data-d]').forEach(tr=>tr.classList.toggle('hl',tr.dataset.d===v));}
document.querySelectorAll('#dpTab [data-o]').forEach(c=>{const d=DOORS[c.dataset.o];c.textContent=d.out+' / '+d.move;});""",
      PICS=json.dumps(PICS, ensure_ascii=False, separators=(',', ':'))))
rep(" renderDoor2D();\n", " renderDoor2D();updDoorPos();\n")
rep("' · '+DOORS[S.doorType].name+' · LED: '", "' · '+DOORS[S.doorType].name+(S.man!=null?' held at '+Math.round(S.man*100)+' %':'')+' · LED: '")

# ---------------------------------------------------------------- side view per frame
rep("door:E('doorS'),br:E('brS'),rod:E('rodS'),", "ldMove:E('ldMove'),ldRod:E('ldRod'),ldEye:E('ldEye'),")
rep("flapP:E('flapP'),flapCrank:E('flapCrank'),flapBody:E('flapBody'),flapRod:E('flapRod'),uoDoor:E('uoDoor'),uoArm:E('uoArm'),uoRod:E('uoRod'),uoLink:E('uoLink'),",
    "flapP:E('flapP'),flapLev:E('flapLev'),flapBody:E('flapBody'),flapRod:E('flapRod'),uoMove:E('uoMove'),uoArm:E('uoArm'),uoBody:E('uoBody'),uoRod:E('uoRod'),")
rep(" parDoor:E('parDoorS'),parArm1:E('parArm1'),parArm2:E('parArm2'),parLever:E('parLever'),parA1:E('parA1'),parA2:E('parA2'),parBody:E('parBody'),parRod:E('parRod')};",
    " parMove:E('parMove'),parArm1:E('parArm1'),parArm2:E('parArm2'),parBody:E('parBody'),parRod:E('parRod')};")
rep(between('function renderDoor2D(){', 'let entT=0;'), r"""function renderDoor2D(){
 const t=S.doorType,f=S.door,deg=a=>(a*180/Math.PI).toFixed(2),
  ln=(e,p,q)=>{e.setAttribute('x1',p[0].toFixed(2));e.setAttribute('y1',(-p[1]).toFixed(2));e.setAttribute('x2',q[0].toFixed(2));e.setAttribute('y2',(-q[1]).toFixed(2));},
  act=(bd,rd,F,P)=>{const dx=P[0]-F[0],dy=P[1]-F[1],L=Math.hypot(dx,dy),be=[F[0]+dx/L*19,F[1]+dy/L*19];ln(bd,F,be);ln(rd,be,P);};
 if(t==='lift'){const st=ldState(S.rod),e=(-(st.tip-.9)).toFixed(2);
  el.ldMove.setAttribute('transform','translate(0,'+(-st.lift).toFixed(2)+')');el.ldRod.setAttribute('y2',e);el.ldEye.setAttribute('cy',e);}
 else if(t==='flap'){const th=f*Math.PI/2;
  el.flapP.setAttribute('points',pts([rotP([0,0],th),rotP([0,-FL.H],th),rotP([1.9,-FL.H],th),rotP([1.9,0],th)]));
  el.flapLev.setAttribute('transform','rotate('+(90*f).toFixed(2)+' '+FL.px+' '+(-FL.py)+')');
  act(el.flapBody,el.flapRod,FL.F,rotP(FL.pin,th));}
 else if(t==='upover'){const st=uoState(f);
  el.uoMove.setAttribute('transform','translate('+st.Q[0].toFixed(3)+' '+(-st.Q[1]).toFixed(3)+') rotate('+(90*f).toFixed(2)+')');
  el.uoArm.setAttribute('transform','rotate('+deg(-st.ar)+' '+UO.F[0]+' '+(-UO.F[1])+')');
  act(el.uoBody,el.uoRod,UO.FA,st.C);}
 else if(t==='parallel'){const st=plState(f),r=deg(-st.ar);
  el.parMove.setAttribute('transform','translate('+st.T[0].toFixed(3)+' '+(-st.T[1]).toFixed(3)+')');
  el.parArm1.setAttribute('transform','rotate('+r+' '+PL.P1[0]+' '+(-PL.P1[1])+')');
  el.parArm2.setAttribute('transform','rotate('+r+' '+PL.P2[0]+' '+(-PL.P2[1])+')');
  act(el.parBody,el.parRod,PL.F,st.C);}
 el.obst.style.display=S.block?'':'none';
}
""")

# ---------------------------------------------------------------- 3D: door panels + actuators in JS, printed parts from files/doors-model-v<V>.json
rep(between('/* door: lift */', 'window.door3D=v=>'), T(r"""/* door: lift – 6 mm panel in printed channels; the rod pushes a printed saddle */
const liftG=new THREE.Group();drawer.add(liftG);
const door=add(B(49.6,22,.6),M.front,0,12.5,-.7,liftG,'door');
const ldSad=new THREE.Group();liftG.add(ldSad);
add(CY(1.4,1.4,19.5,20),M.alu,-21.5,12.75,-3.2,liftG,'actuator');
const ldRod=add(CY(.7,.7,1,14),M.steel,0,0,0,liftG,'actuator');
const ldEye=add(CY(.9,.9,.8,16),M.steel,-21.5,25.5,-3.2,liftG,'actuator');ldEye.rotation.z=Math.PI/2;
add(B(1.2,.7,.8),M.reed,-23.4,2.1,-1.7,liftG,'reed');add(B(1.2,.7,.8),M.reed,-23.4,42.6,-1.7,liftG,'reed');
function act(bd,rd,A,P,bl=19){const dx=P[0]-A[0],dy=P[1]-A[1],dz=P[2]-A[2],L=Math.hypot(dx,dy,dz),e=[A[0]+dx/L*bl,A[1]+dy/L*bl,A[2]+dz/L*bl];orient(bd,A,e);orient(rd,e,P);}

/* door: flap out – printed lever on the flap, actuator from a printed mount on the left cheek */
const FL=SIM.FL;
const flapG=new THREE.Group();drawer.add(flapG);
const flapPivot=new THREE.Group();flapPivot.position.set(0,FL.py,-FL.px);flapG.add(flapPivot);
add(B(59.6,FL.H,1.9),M.front,0,-FL.H/2,-.95,flapPivot,'flap');
add(CY(.3,.3,59.6,10),M.steel,0,FL.py,-FL.px,flapG,'flap').rotation.z=Math.PI/2;
const flapBody=add(CY(1.3,1.3,1,16),M.alu,0,0,0,flapG,'actuator');
const flapRod=add(CY(.5,.5,1,12),M.steel,0,0,0,flapG,'actuator');

/* door: up & over – the door turns up while its pegs slide back in printed tracks; printed arms, left one with the lever */
const UO=SIM.UO;
const uoG=new THREE.Group();drawer.add(uoG);
const uoDoor=new THREE.Group();uoDoor.position.set(0,UO.Q[1],-UO.Q[0]);uoG.add(uoDoor);
add(B(49.2,UO.top-UO.bot,1.9),M.front,0,(UO.top+UO.bot)/2-UO.Q[1],UO.Q[0]+.95,uoDoor,'uo');
const uoBody=add(CY(1.3,1.3,1,16),M.alu,0,0,0,uoG,'actuator');
const uoRod=add(CY(.6,.6,1,12),M.steel,0,0,0,uoG,'actuator');

/* door: parallel lift – 2 print-in-place modules; 4 arms keep the door vertical, an 8 mm square rod couples the front arms */
const PL=SIM.PL;
const parG=new THREE.Group();drawer.add(parG);
const parDoor=new THREE.Group();parG.add(parDoor);
add(wedge(PL.door.map(p=>[-p[0],p[1]]),49.2),M.front,0,0,0,parDoor,'par');
const parSq=add(B(48.4,.8,.8),M.steel,0,PL.P1[1],-PL.P1[0],parG,'par');
const parBody=add(CY(1.3,1.3,1,16),M.alu,0,0,0,parG,'actuator');
const parRod=add(CY(.6,.6,1,12),M.steel,0,0,0,parG,'actuator');

/* printed door parts: files/doors-model-v@@DV@@.json = base64 GLB from doors/*.scad (cm, y up, each node's origin = its pivot) */
M.petg=std(0x3f86d8,.5,0,{flatShading:true});M.petgFix=std(0xa7c8ee,.6,0,{flatShading:true});
const cutR=[],DN={};
fetch('files/doors-model-v@@DV@@.json').then(r=>r.ok?r.json():Promise.reject(r.status)).then(j=>{const s=atob(j.glb),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);
 new GLTFLoader().parse(a.buffer,'',g=>{const ms=[],P=new THREE.Vector3();g.scene.updateMatrixWorld(true);g.scene.traverse(o=>{if(o.isMesh)ms.push(o);});
  const home={pl:parG,uo:uoG,ld:liftG,fl:flapG},part={pl:'par',uo:'uo',ld:'channels',fl:'flap'};
  ms.forEach(o=>{const k=(o.userData.name||o.name).replace(/_\d+$/,''),ty=k.slice(0,2);o.getWorldPosition(P);o.removeFromParent();
   o.position.copy(P);o.rotation.set(0,0,0);o.scale.set(1,1,1);
   o.material=/plate|track|channel|mount|foot|clamp/.test(k)?M.petgFix:M.petg;o.castShadow=o.receiveShadow=true;
   o.userData.part=/mount|foot|clamp/.test(k)?'actuator':k==='ld_saddle'?'door':part[ty]||'door';pick.push(o);
   const par=/_bracket_/.test(k)?(ty==='pl'?parDoor:uoDoor):k==='ld_saddle'?ldSad:k==='fl_lever'?flapPivot:home[ty];
   if(!par)return;if(par!==home[ty])o.position.set(0,0,0);par.add(o);if(/_r$/.test(k))cutR.push(o);DN[k]=o;});
  window.mode3D(mode);},e=>console.error(e));}).catch(e=>console.error('door model',e));

""", DV=DV))
rep("[sideR,cheekR,railR,chanR,slideR,slideRi,legR,trackR,armR,parArms[1][0],parArms[1][1],wheels[1]].forEach(o=>o.visible=!cut);",
    "[sideR,cheekR,railR,slideR,slideRi,legR,wheels[1]].concat(cutR).forEach(o=>o.visible=!cut);")
rep(between(" if(t==='lift'){const L=15*S.door;", " wheels.forEach(g=>{g.rotation.x=d/1.5;})"), r""" if(t==='lift'){const st=SIM.ldState(S.rod);door.position.y=12.5+st.lift;ldSad.position.y=st.lift;
  orient(ldRod,[-21.5,22.5,-3.2],[-21.5,st.tip-.9,-3.2]);ldEye.position.y=st.tip-.9;}
 else if(t==='flap'){const th=S.door*Math.PI/2;flapPivot.rotation.x=-th;
  const P=SIM.rotP(FL.pin,th);act(flapBody,flapRod,[-22.6,FL.F[1],-FL.F[0]],[-22.6,P[1],-P[0]]);}
 else if(t==='upover'){const st=SIM.uoState(S.door);uoDoor.position.set(0,st.Q[1],-st.Q[0]);uoDoor.rotation.x=-st.ps;
  ['uo_arm_l','uo_arm_r'].forEach(k=>{if(DN[k])DN[k].rotation.x=st.ar;});
  act(uoBody,uoRod,[-21.8,UO.FA[1],-UO.FA[0]],[-21.8,st.C[1],-st.C[0]]);}
 else if(t==='parallel'){const st=SIM.plState(S.door);parDoor.position.set(0,st.T[1],-st.T[0]);
  ['pl_arm1_l','pl_arm1_r','pl_arm2_l','pl_arm2_r'].forEach(k=>{if(DN[k])DN[k].rotation.x=st.ar;});parSq.rotation.x=st.ar;
  act(parBody,parRod,[-21.8,PL.F[1],-PL.F[0]],[-21.8,st.C[1],-st.C[0]]);}
""")

# ---------------------------------------------------------------- close-up camera + see-through robot while the slider holds the door
rep('<button data-v="top">Top</button>', '<button data-v="top">Top</button><button data-v="door" title="Close-up of the door mechanism on the left cheek">Door</button>')
rep("led_under:[[38,30,92],[0,4,10]]};", "led_under:[[38,30,92],[0,4,10]],door:[[67,28,-5],[-23,23,-10]]};")
rep(" dpR.forEach(r=>{if(+r.value!==p)r.value=p;});", " dpR.forEach(r=>{if(+r.value!==p)r.value=p;});el.robot.style.opacity=S.man!=null?'.3':'';")
rep("window.render3D=dt=>{\n", """let seeR=false;   /* robot turns see-through while the slider holds the door, so the mechanism behind it shows */
window.render3D=dt=>{
 if((S.man!=null)!==seeR){seeR=S.man!=null;[M.robot,M.robotDark,M.bump,M.mop].forEach(m=>{m.transparent=seeR;m.opacity=seeR?.22:1;m.depthWrite=!seeR;m.needsUpdate=true;});}
""")

# ---------------------------------------------------------------- build notes
rep("<li>Lift door: PTFE tape in the channels;", "<li>Lift door: PTFE tape in the printed channels;")
rep("      <li>Parallel lift: 4 arms, 10 cm hole to hole (12 cm pieces), all pivots on M6 shoulder bolts.</li>",
    "      <li><b>Printed door parts:</b> every door type has its own STL set (\"Door parts\" above). Up &amp; over and parallel lift print in place – print <code>coupon.stl</code> first, then move each module through its full travel a few times before mounting. The parallel lift needs a 45° chamfer on the door's top back edge; the up &amp; over door is 20.2 cm tall (2 mm less than the others).</li>")

# ---------------------------------------------------------------- downloads: one zip per door type, status note per card
rep("const PKG={pcb:'files/pcb-v" + PCB_V + ".json',case:'files/case-v" + CASE_V + ".json'};",
    "const PKG={pcb:'files/pcb-v" + PCB_V + ".json',case:'files/case-v" + CASE_V + ".json'," +
    ','.join("d%s:'files/doors-%s-v%s.json'" % (k, k, DV) for k in TYPES) + "};")
rep("const E=id=>document.getElementById(id),note=E('dlNote'),btns=[...document.querySelectorAll('[data-dl]')];",
    "const E=id=>document.getElementById(id),notes=[...document.querySelectorAll('.dlnote')],btns=[...document.querySelectorAll('[data-dl]')];")
rep('<span class="note" id="dlNote" role="status">', '<span class="note dlnote" id="dlNote" role="status">')
rep("if(!dl){note.textContent='Downloads work when the page is opened on claude.ai.';",
    "if(!dl){notes.forEach(n=>n.textContent='Downloads work when the page is opened on claude.ai.');")
rep("  note.textContent='';\n  btns.forEach(b=>{b.disabled=false;b.onclick=async()=>{",
    "  notes.forEach(n=>n.textContent='');\n  btns.forEach(b=>{const note=b.parentNode.querySelector('.dlnote');b.disabled=false;b.onclick=async()=>{")
print('door replacements ok, PETG g:', G, 'zip kB:', {k: round(v) for k, v in KB.items()})
