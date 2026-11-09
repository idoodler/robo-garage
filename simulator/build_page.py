# Build Robo-Garage simulator v5.6 (PCB + case version from parts.py / the SCAD file) from v4.9: light barrier + auto vent +
# PCB/case section with downloads, leak probe + valve + buzzer (v1.2), power headroom (v1.3).
# Run simulator/build_files.py first (download manifests + pictures).
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'robo-garage.html')
OUT = os.path.join(HERE, 'index.html')
YAML = os.path.join(HERE, '..', 'esphome', 'robo-garage-pcb.yaml')
PCB_V = re.search(r"^VERSION = '([^']*)'", open(os.path.join(HERE, '..', 'pcb', 'gen', 'parts.py')).read(), re.M).group(1)
CASE_V = re.search(r'^version = "([^"]*)"', open(os.path.join(HERE, '..', 'case', 'robo-garage-case.scad')).read(), re.M).group(1)
from PIL import Image                                       # picture sizes for the <img> tags
PCB_WH = Image.open(os.path.join(HERE, 'img', 'pcb-v%s-top.webp' % PCB_V)).size
CASE_WH = Image.open(os.path.join(HERE, 'img', 'case-v%s.webp' % CASE_V)).size

s = open(SRC, encoding='utf-8').read()
n_ok = 0


def rep(old, new, count=1):
    global s, n_ok
    c = s.count(old)
    if c != count:
        raise SystemExit('expected %d match(es), found %d for:\n%s' % (count, c, old[:300]))
    s = s.replace(old, new)
    n_ok += 1


# ---------------------------------------------------------------- head / css
rep('<p class="sub">METOD 60×60×80 · pull-out robot drawer on soft wheels · 4 door options · ramp · rear fan · Dreame L10s Pro Ultra Heat · ESPHome + Home Assistant</p>',
    '<p class="sub">METOD 60×60×80 · pull-out robot drawer on soft wheels · 4 door options · ramp · light barrier · rear fan with auto vent · own controller PCB · Dreame L10s Pro Ultra Heat · ESPHome + Home Assistant</p>')
rep('</style>', '''h3{font-size:.86rem;margin:0 0 6px}
.status.s4{grid-template-columns:repeat(4,1fr)}
@media (max-width:700px){.status.s4{grid-template-columns:1fr 1fr}}
.shot{margin:0;border-radius:10px;overflow:hidden;background:#0b3d1e;border:1px solid var(--line);align-self:start}
.shot.light{background:#f8f8f8}
.shot img{display:block;width:100%;height:auto}
.shot figcaption{font-size:.78rem;color:var(--muted);padding:6px 10px;background:var(--surface)}
.dl{display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center;margin-top:12px}
.kv td:first-child{color:var(--muted);white-space:nowrap}
</style>''')

# ---------------------------------------------------------------- side view
rep('''      <g class="part" data-part="esp" tabindex="0" role="button" aria-label="ESP32 and motor driver">
        <rect x="8" y="-77" width="7.5" height="2.8" rx=".3" fill="var(--pcb)"/><text x="11.75" y="-75.1" font-size="1.4" text-anchor="middle" style="fill:#d7f5e5">ESP32</text>
        <rect x="8" y="-73" width="5" height="5" rx=".3" fill="#b23a3a"/><text x="10.5" y="-70.1" font-size="1.05" text-anchor="middle" style="fill:#fff">BTS7960</text>
        <rect x="14" y="-72.4" width="2.4" height="1.6" rx=".2" fill="#2b5fa8"/>
      </g>''', '''      <g class="part" data-part="esp" tabindex="0" role="button" aria-label="Controller PCB in its case">
        <rect x="6.5" y="-79.7" width="12.5" height="2.9" rx=".5" fill="#dfe3e8" stroke="var(--dockline)" stroke-width=".2"/>
        <rect x="7.3" y="-78.6" width="10.9" height=".4" fill="var(--pcb)"/>
        <text x="12.2" y="-74.9" font-size="1.4" text-anchor="middle">controller</text>
      </g>
      <g class="part" data-part="th" tabindex="0" role="button" aria-label="Temperature and humidity sensor">
        <rect x="16.9" y="-79.5" width="1.9" height="2.5" rx=".2" fill="none" stroke="var(--accent)" stroke-width=".22" stroke-dasharray=".45 .3"/>
        <text id="thTxt" x="12.2" y="-72.8" font-size="1.4" text-anchor="middle">22.0 °C · 50 %</text>
      </g>''')
rep('<text x="49.5" y="-77.6" font-size="1.6" text-anchor="middle">rear fan</text>',
    '<text id="fanTxt" x="49.5" y="-77.6" font-size="1.6" text-anchor="middle">rear fan</text>')
rep('''        <g class="part" data-part="obstacle" id="obstS" style="display:none"><rect x="-4" y="-9" width="8" height="7.5" rx=".6" fill="#ff8a00"/><text x="0" y="-4.6" font-size="1.5" text-anchor="middle" style="fill:#fff">toy</text></g>
''', '')
rep('''      <g id="robotS" class="part" data-part="robot" tabindex="0" role="button" aria-label="Robot">''',
    '''      <!-- fixed: toy test + light barrier (retroreflective sensor at the left front corner, reflector at the right one, beam 12 cm in front, 2 cm high) -->
      <g class="part" data-part="obstacle" id="obstS" style="display:none" transform="translate(-11,1.2)"><rect x="-4" y="-9" width="8" height="7.5" rx=".6" fill="#ff8a00"/><text x="0" y="-4.6" font-size="1.5" text-anchor="middle" style="fill:#fff">toy</text></g>
      <g class="part" data-part="beam" tabindex="0" role="button" aria-label="Light barrier">
        <rect x="-12.54" y="-3.65" width="1.08" height="3.1" rx=".2" fill="#2b2f36"/>
        <rect id="lbLedO" x="-12.42" y="-3.85" width=".34" height=".2" fill="#ff9f0a"/><rect id="lbLedG" x="-11.92" y="-3.85" width=".34" height=".2" fill="#3ddc84"/>
        <circle id="beamGlow" cx="-12" cy="-2.1" r="2.2" fill="#3ddc84" filter="url(#gS)" opacity=".6"/>
        <circle id="beamDot" cx="-12" cy="-2.1" r=".75" fill="#3ddc84"/>
        <text x="-12" y="3.4" font-size="1.5" text-anchor="middle">beam</text>
      </g>
      <g id="robotS" class="part" data-part="robot" tabindex="0" role="button" aria-label="Robot">''')

# ---------------------------------------------------------------- controls + HUD
rep('        <button class="btn" id="bBlock" aria-pressed="false">Block door</button>',
    '        <button class="btn" id="bBlock" aria-pressed="false">Toy in front</button>\n        <button class="btn" id="bFault" aria-pressed="false">Beam fault</button>')
rep('''    <div class="status">
      <div class="stat"><small>Phase</small><b id="sPhase">Docked</b></div>
      <div class="stat"><small>Real duration</small><b id="sReal">—</b></div>
      <div class="stat"><small>Battery · progress</small><b id="sBat">100 % · 0 %</b></div>
    </div>''', '''    <div class="status s4">
      <div class="stat"><small>Phase</small><b id="sPhase">Docked</b></div>
      <div class="stat"><small>Real duration</small><b id="sReal">—</b></div>
      <div class="stat"><small>Battery · progress</small><b id="sBat">100 % · 0 %</b></div>
      <div class="stat"><small>Cabinet air · fan</small><b id="sAir">22.0 °C · 50 %</b></div>
    </div>''')

# ---------------------------------------------------------------- shopping list
rep('''      <tr><td>BTS7960 "IBT-2" H-bridge</td><td>1</td><td class="num">1–4</td><td><a href="https://www.aliexpress.com/item/4000002701244.html">item</a></td></tr>
      <tr><td>MP1584EN buck → set to 5.0 V first</td><td>1</td><td class="num">1–2</td><td><a href="https://www.aliexpress.com/item/32261885063.html">item</a></td></tr>
''', '')
rep('''      <tr class="grp"><td colspan="4">Hardware store (cut to size)</td></tr>''', '''      <tr class="grp"><td colspan="4">Controller PCB v''' + PCB_V + ''' – <a href="#pcb">files below</a></td></tr>
      <tr><td>JLCPCB: 5 PCBs, 2 fully assembled (Economic PCBA: SMD + push-button clamps + DevKit sockets) – Gerber zip, BOM, CPL from the download <span class="tag">≈ 26 extended parts × $3</span></td><td>1 order</td><td class="num">140–180</td><td><a href="https://jlcpcb.com/">JLCPCB</a></td></tr>
      <tr><td>Light barrier 12–24 V, retroreflective + reflector, NPN, mode switch on L (Light-ON), E3Z-R61 type – door safety</td><td>1</td><td class="num">9–15</td><td><a href="https://www.aliexpress.com/w/wholesale-E3Z-R61.html">AliExpress</a></td></tr>
      <tr class="opt"><td>Leak detection: 2 stainless screws on the cabinet floor, or any water-leak sensor with a digital output (NPN / 3.3–5 V logic, powered from the clamp) <span class="tag">optional</span> – LEAK clamp</td><td>1</td><td class="num">0–8</td><td><a href="https://www.aliexpress.com/w/wholesale-water-leak-sensor-module.html">AliExpress</a></td></tr>
      <tr class="opt"><td>Water valve 12 V DC ≤ 3 A that closes when powered (NO solenoid / motorised ball valve) <span class="tag">optional</span> – VALVE clamp, for the water kit</td><td>1</td><td class="num">10–30</td><td><a href="https://www.aliexpress.com/w/wholesale-12v-normally-open-solenoid-valve.html">AliExpress</a></td></tr>
      <tr><td>Case: PETG ≈ 70 g + 4× M3×25 screws (STL in the download)</td><td>–</td><td class="num">2–4</td><td>–</td></tr>
      <tr class="grp"><td colspan="4">Hardware store (cut to size)</td></tr>''')
old_led = [l for l in s.split('\n') if l.startswith('      <tr data-led="line under">')]
assert len(old_led) == 1
rep(old_led[0], old_led[0].replace('data-led="line under"', 'data-led="under"').replace('status LED (Line / Underglow)', 'status LED (Underglow)') + '\n'
    '      <tr data-led="line"><td>SK6812 RGBW strip 144 LED/m, 5 V, RGBNW (natural white 4000 K), black PCB, IP30, 1 m – status LED (Line): one 50 cm segment = 72 LEDs</td><td>1</td><td class="num">12.89–14.27</td><td><a href="https://de.aliexpress.com/item/32857962825.html">AliExpress</a></td></tr>')
rep('''      <tr><td>Wire, Wago, 3 A fuse, screws, wood glue, 4 steel angles 30 mm, 330 Ω, 1000 µF/10 V, BC547 + 1 kΩ (button ring)</td><td>–</td><td class="num">12–22</td><td>–</td></tr>''',
    '''      <tr><td>Wire 0.5 mm², screws, wood glue, 4 steel angles 30 mm, zip ties</td><td>–</td><td class="num">8–15</td><td>–</td></tr>''')
for d, w in (('flap', 'flap'), ('upover', 'flap'), ('parallel', 'door')):
    rep('''      <tr data-door="%s"><td>INA219 current sensor – stops the %s when it hits something</td><td>1</td><td class="num">1–3</td><td><a href="https://www.aliexpress.com/w/wholesale-ina219.html">AliExpress</a></td></tr>
''' % (d, w), '')
rep('<p class="note">IKEA/Amazon prices from current listings; AliExpress changes daily. Core = all rows without a tag, plus the LED and door parts you picked above the 3D model.</p>',
    '<p class="note">IKEA/Amazon prices from current listings; AliExpress changes daily; the PCB price is an estimate (get the exact quote at JLCPCB). Core = all rows without a tag, plus the LED and door parts you picked above the 3D model.</p>')

# ---------------------------------------------------------------- PCB + case section
yaml_txt = open(YAML, encoding='utf-8').read()
CC_LINE = '    color_correct: [25%, 25%, 25%, 25%]                        # <= 1.44 A at full RGBW: the LED clamp gives 1.5 A (F2)\n'
for k in ('num_leds: 72', 'chipset: SK6812', 'channel_colors: GRBW', CC_LINE):
    assert yaml_txt.count(k) == 1, k
yaml_html = (html.escape(yaml_txt, quote=False)
             .replace('num_leds: 72', 'num_leds: <span id="numLeds">72</span>')
             .replace('chipset: SK6812', 'chipset: <span id="ledChip">SK6812</span>')
             .replace('channel_colors: GRBW', 'channel_colors: <span id="ledOrder">GRBW</span>')
             .replace(html.escape(CC_LINE, quote=False), '<span id="ledCC">' + html.escape(CC_LINE, quote=False) + '</span>'))
pcb_section = '''<section class="card" style="margin-top:14px" id="pcb">
  <div class="vhead"><h2>Controller PCB v''' + PCB_V + ''' + 3D-printed case</h2><span class="lbl">KiCad + OpenSCAD · all files open</span></div>
  <div class="cols2">
    <figure class="shot"><img src="img/pcb-v''' + PCB_V + '''-top.webp" width="''' + str(PCB_WH[0]) + '''" height="''' + str(PCB_WH[1]) + '''" loading="lazy" alt="PCB v''' + PCB_V + ''' top view: ESP32 DevKitC sockets at the top, push-button clamps on the left, right and bottom edge, buzzer in the middle, SHT41 on a slotted island in the bottom-right corner"><figcaption>PCB 100 × 100 mm, 2 layers · JLCPCB assembles every part, clamps included · DRC: 0 errors, 0 warnings</figcaption></figure>
    <figure class="shot light"><img src="img/case-v''' + CASE_V + '''.webp" width="''' + str(CASE_WH[0]) + '''" height="''' + str(CASE_WH[1]) + '''" loading="lazy" alt="3D-printed case: base with wire shelves, lid with clamp cut-outs and buzzer holes, vented sensor corner at the front right"><figcaption>Case: base + lid, PETG, no supports · vented sensor corner</figcaption></figure>
  </div>
  <div class="dl">
    <button class="btn primary" data-dl="pcb" disabled>⬇ PCB v''' + PCB_V + ''' · JLCPCB files, KiCad, YAML (zip, 1.2 MB)</button>
    <button class="btn primary" data-dl="case" disabled>⬇ Case v''' + CASE_V + ''' · STL + OpenSCAD (zip, 0.4 MB)</button>
    <span class="note" id="dlNote" role="status">Checking downloads…</span>
  </div>
  <div class="cols2" style="margin-top:14px">
    <div>
      <h3>On the board</h3>
      <table class="kv"><tbody>
        <tr><td>ESP32</td><td>DevKitC V4 plugs into a socket, its USB-C sits in the case wall: flash with the lid on, then OTA</td></tr>
        <tr><td>Power</td><td>12 V in, 6 A (4-pole clamp) → 7 A PTC, reverse protection, TVS → 5.1 V buck on board (no 5 V adapter)</td></tr>
        <tr><td>Door</td><td>DRV8874 driver (3 A moves, 4.9 A hardware limit) + INA219 current sense (20 mΩ shunt) → stall stop</td></tr>
        <tr><td>Sensors</td><td>SHT41 temperature + humidity on a slotted island · light-barrier input (12 V safe, self-test) · water-leak input: bare electrodes (pulsed, no corrosion) or a digital sensor (12 V / 3.3 V on the clamp) · 12 V rail monitor</td></tr>
        <tr><td>Outputs</td><td>Fan PWM + tach · LED strip level shifter · 12 V button ring · 12 V valve output (3 A, a leak closes the water) · buzzer</td></tr>
        <tr><td>Clamps</td><td>9 push-button spring clamps (KF250, 0.2–0.75 mm²) on 3 edges, soldered by JLCPCB</td></tr>
      </tbody></table>
    </div>
    <div>
      <h3>ESP32 pins</h3>
      <table><tbody>
        <tr><td class="m">25 / 26</td><td>DRV8874 IN1 (open) / IN2 (close)</td></tr>
        <tr><td class="m">32 / 33 / 18</td><td>Reed door closed / door open / drawer</td></tr>
        <tr><td class="m">19 / 23</td><td>Clean button / button ring</td></tr>
        <tr><td class="m">16</td><td>LED strip data (level shifter)</td></tr>
        <tr><td class="m">17 / 27</td><td>Fan PWM / fan tach</td></tr>
        <tr><td class="m">21 / 22</td><td>I²C: INA219 0x40, SHT41 0x44, VL53L1X (clamp)</td></tr>
        <tr><td class="m">34 / 13</td><td>Light barrier input / sensor on-off (self-test)</td></tr>
        <tr><td class="m">4 / 35</td><td>Leak probe drive / leak ADC</td></tr>
        <tr><td class="m">2 / 15 / 36</td><td>Valve / buzzer / 12 V rail ADC</td></tr>
        <tr><td class="m">14, 5, 39</td><td>Spare (EXP header)</td></tr>
      </tbody></table>
    </div>
  </div>
  <div class="cols2" style="margin-top:14px">
    <div>
      <h3>Order at JLCPCB</h3>
      <ol class="steps">
        <li>PCB: upload <code>robo-garage_gerbers_JLCPCB.zip</code> → 2 layers, 1.6 mm, HASL.</li>
        <li>Assembly: Economic, top side, 2 boards, tooling holes "added by customer" → upload BOM + CPL (all 48 lines match by LCSC number).</li>
        <li>Compare the placement preview with <code>pin1-check.png</code> from the download (ICs, transistors, diodes, clamps).</li>
        <li>Plug in the ESP32 DevKitC (both row pitches fit). Nothing to solder.</li>
      </ol>
    </div>
    <div>
      <h3>Print the case</h3>
      <table class="kv"><tbody>
        <tr><td>Material</td><td>PETG</td></tr>
        <tr><td>Layer · walls · infill</td><td>0.2 mm · 3 · 20 %</td></tr>
        <tr><td>Supports</td><td>none (the lid prints top face down)</td></tr>
        <tr><td>Hardware</td><td>4× M3×25, 4 wood screws, zip ties</td></tr>
      </tbody></table>
    </div>
  </div>
  <details>
    <summary>ESPHome config v''' + PCB_V + '''</summary>
    <div class="dl" style="margin-top:8px"><button class="btn" id="cpYaml">Copy YAML</button><span class="note" id="cpNote" role="status"></span></div>
    <pre id="yaml" style="margin-top:8px;max-height:420px">''' + yaml_html + '''</pre>
  </details>
</section>

'''
rep('''<section class="card" style="margin-top:14px">
  <details open>
    <summary>Build notes</summary>''', pcb_section + '''<section class="card" style="margin-top:14px">
  <details open>
    <summary>Build notes</summary>''')

# ---------------------------------------------------------------- build notes
rep('<li>Lift door: PTFE tape in the channels; if it ever tilts, add a second actuator on the right, wired in parallel. All other doors push when closing → add the INA219 stall stop.</li>',
    '<li>Lift door: PTFE tape in the channels; if it ever tilts, add a second actuator on the right, wired in parallel. Every door: the light barrier keeps it from closing on anything in front; the INA219 stall stop on the PCB is the backup.</li>')
rep('Switch between GPIO19 and GND; ring: 12 V → ring → BC547 → GND, base via 1 kΩ from GPIO23. The fascia is fixed, so no wires through the drag chain.</li>',
    'Wire it to the BUTTON clamp (BTN, GND, 12V, LED−): GPIO19 reads the switch, a MOSFET on the PCB switches the ring (GPIO23). The fascia is fixed, so no wires through the drag chain.</li>\n      <li><b>Light barrier:</b> retroreflective sensor on a small L-bracket at the left front corner, its reflector on the right one. Beam ≈12 cm in front of the door, ≈2 cm above the floor – past the ramp wedge and under the door\'s swing, so the door never breaks it itself. Mode switch on L (Light-ON); turn the sensor until the green LED is steady. Cable to the BEAM clamp: brown → RX+, black → SIG, blue → TX− (the self-test switches the sensor off there).</li>\n      <li><b>Controller:</b> PCB in its printed case under the top, the vented sensor corner open to the cabinet air. Keep those vents free.</li>')
old_wiring = s[s.index('  <details>\n    <summary>ESP32 wiring + ESPHome snippets</summary>'):s.index('  </details>\n</section>\n</div>\n\n<script>') + len('  </details>\n')]
assert old_wiring.count('<details>') == 1
rep(old_wiring, '''  <details>
    <summary>Wiring · PCB v''' + PCB_V + ''' clamps</summary>
    <div class="tablewrap" style="margin-top:8px"><table>
      <thead><tr><th>Clamp</th><th>Pins</th><th>Connect</th></tr></thead>
      <tbody>
        <tr><td>12 V IN</td><td class="m">+12V, +12V, GND, GND</td><td>12 V / 5 A adapter (e.g. Mean Well GST60A12) → DC jack adapter; above 5 A use both pairs</td></tr>
        <tr><td>ACTUATOR</td><td class="m">M+, M−</td><td>Linear actuator (wrong direction → swap the 2 wires)</td></tr>
        <tr><td>FAN</td><td class="m">4-pin</td><td>ARCTIC P12 Slim PWM plug</td></tr>
        <tr><td>LED</td><td class="m">5V, DAT, GND</td><td>Strip or ring DIN: SK6812 RGBW line or WS2812B</td></tr>
        <tr><td>BUTTON</td><td class="m">BTN, GND, 12V, LED−</td><td>Alu button: NO, C, LED+, LED−</td></tr>
        <tr><td>REEDS</td><td class="m">CL/GND, OP/GND, DR/GND</td><td>Door closed, door open, drawer</td></tr>
        <tr><td>BEAM</td><td class="m">RX+, RX−, SIG, TX+, TX−, GND</td><td>Sensor brown → RX+, black → SIG, blue → TX− · RX−, TX+, GND stay free</td></tr>
        <tr><td>LEAK</td><td class="m">3V3, SIG, GND, 12V</td><td>2 electrodes on SIG + GND, or a digital leak sensor (power from 3V3 ≤ 50 mA or 12V; NPN: 10 kΩ 3V3–SIG)</td></tr>
        <tr><td>VALVE</td><td class="m">+12V, VLV</td><td>12 V valve ≤ 3 A that closes when powered (optional)</td></tr>
        <tr><td>I2C</td><td class="m">3V3, SDA, SCL, GND</td><td>VL53L1X (optional)</td></tr>
      </tbody>
    </table></div>
    <p class="note">Full ESPHome config, pin table and files: <a href="#pcb">Controller PCB</a>.</p>
  </details>
''')

print('html replacements ok:', n_ok)
exec(open(os.path.join(HERE, 'build_js.py'), encoding='utf-8').read())
s = s.replace('@@PCB_V@@', PCB_V).replace('@@CASE_V@@', CASE_V)   # file names inside the JS (v1.3)
exec(open(os.path.join(HERE, 'build_doors.py'), encoding='utf-8').read())   # door mechanisms v2 + open slider + door parts card
assert '@@' not in s
open(OUT, 'w', encoding='utf-8').write(s)
print('written', OUT, len(s), 'bytes, replacements', n_ok)
