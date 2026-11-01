# Build Robo-Garage simulator v5.1 (PCB v1.1.1) from v4.9: light barrier + auto vent + PCB/case section with downloads.
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'robo-garage.html')
OUT = os.path.join(HERE, 'index.html')
YAML = os.path.join(HERE, '..', 'esphome', 'robo-garage-pcb.yaml')

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
    '''      <!-- fixed: toy test + light barrier (sender + receiver at the front corners, beam 12 cm in front, 2 cm high) -->
      <g class="part" data-part="obstacle" id="obstS" style="display:none" transform="translate(-11,1.2)"><rect x="-4" y="-9" width="8" height="7.5" rx=".6" fill="#ff8a00"/><text x="0" y="-4.6" font-size="1.5" text-anchor="middle" style="fill:#fff">toy</text></g>
      <g class="part" data-part="beam" tabindex="0" role="button" aria-label="Light barrier">
        <rect x="-13.3" y="-3.7" width="2.6" height="3.1" rx=".35" fill="#2b2f36"/>
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
rep('''      <tr class="grp"><td colspan="4">Hardware store (cut to size)</td></tr>''', '''      <tr class="grp"><td colspan="4">Controller PCB v1.1.1 – <a href="#pcb">files below</a></td></tr>
      <tr><td>JLCPCB: 5 PCBs, 2 assembled (Economic PCBA) – Gerber zip, BOM, CPL from the download <span class="tag">15 extended parts × $3</span></td><td>1 order</td><td class="num">80–110</td><td><a href="https://jlcpcb.com/">JLCPCB</a></td></tr>
      <tr><td>WAGO 804 push-in clamps: 3× 804-102, 804-103, 2× 804-104, 804-105, 804-106</td><td>8</td><td class="num">15–22</td><td><a href="https://octopart.com/search?q=WAGO%20804">compare</a></td></tr>
      <tr><td>2× female header 1×19, 8.5 mm (DevKitC socket) + Molex 47053-1000 fan header</td><td>3</td><td class="num">2–4</td><td>–</td></tr>
      <tr><td>Light barrier pair 12–24 V, through-beam, NPN, Light-ON ("NC") – door safety</td><td>1 pair</td><td class="num">9–15</td><td><a href="https://www.aliexpress.com/w/wholesale-through-beam-photoelectric-sensor.html">AliExpress</a></td></tr>
      <tr><td>Case: PETG ≈ 70 g + 4× M3×25 screws (STL in the download)</td><td>–</td><td class="num">2–4</td><td>–</td></tr>
      <tr class="grp"><td colspan="4">Hardware store (cut to size)</td></tr>''')
rep('''      <tr><td>Wire, Wago, 3 A fuse, screws, wood glue, 4 steel angles 30 mm, 330 Ω, 1000 µF/10 V, BC547 + 1 kΩ (button ring)</td><td>–</td><td class="num">12–22</td><td>–</td></tr>''',
    '''      <tr><td>Wire 0.5 mm², screws, wood glue, 4 steel angles 30 mm, zip ties</td><td>–</td><td class="num">8–15</td><td>–</td></tr>''')
for d, w in (('flap', 'flap'), ('upover', 'flap'), ('parallel', 'door')):
    rep('''      <tr data-door="%s"><td>INA219 current sensor – stops the %s when it hits something</td><td>1</td><td class="num">1–3</td><td><a href="https://www.aliexpress.com/w/wholesale-ina219.html">AliExpress</a></td></tr>
''' % (d, w), '')
rep('<p class="note">IKEA/Amazon prices from current listings; AliExpress changes daily. Core = all rows without a tag, plus the LED and door parts you picked above the 3D model.</p>',
    '<p class="note">IKEA/Amazon prices from current listings; AliExpress changes daily; the PCB price is an estimate (get the exact quote at JLCPCB). Core = all rows without a tag, plus the LED and door parts you picked above the 3D model.</p>')

# ---------------------------------------------------------------- PCB + case section
yaml_txt = open(YAML, encoding='utf-8').read()
assert yaml_txt.count('num_leds: 16') == 1
yaml_html = html.escape(yaml_txt, quote=False).replace('num_leds: 16', 'num_leds: <span id="numLeds">16</span>')
pcb_section = '''<section class="card" style="margin-top:14px" id="pcb">
  <div class="vhead"><h2>Controller PCB v1.1.1 + 3D-printed case</h2><span class="lbl">KiCad + OpenSCAD · all files open</span></div>
  <div class="cols2">
    <figure class="shot"><img src="img/pcb-v1.1.1-top.webp" width="1200" height="1240" loading="lazy" alt="PCB v1.1.1 top view: ESP32 DevKitC socket at the top, push-in clamps on the left, right and bottom edge, SHT40 on a slotted island in the bottom-right corner"><figcaption>PCB 100 × 100 mm, 2 layers · JLCPCB places all SMD parts · DRC: 0 errors, 0 warnings</figcaption></figure>
    <figure class="shot light"><img src="img/case-v1.1.webp" width="1002" height="691" loading="lazy" alt="3D-printed case: base with wire shelves, lid with clamp cut-outs, vented sensor corner at the front right"><figcaption>Case: base + lid, PETG, no supports · vented SHT40 corner</figcaption></figure>
  </div>
  <div class="dl">
    <button class="btn primary" data-dl="pcb" disabled>⬇ PCB v1.1.1 · JLCPCB files, KiCad, YAML (zip, 1.3 MB)</button>
    <button class="btn primary" data-dl="case" disabled>⬇ Case v1.1 · STL + OpenSCAD (zip, 0.4 MB)</button>
    <span class="note" id="dlNote" role="status">Checking downloads…</span>
  </div>
  <div class="cols2" style="margin-top:14px">
    <div>
      <h3>On the board</h3>
      <table class="kv"><tbody>
        <tr><td>ESP32</td><td>DevKitC V4 plugs into a socket · USB for the first flash, then OTA</td></tr>
        <tr><td>Power</td><td>12 V in → PTC, reverse protection, TVS → 5.1 V buck on board (no 5 V adapter)</td></tr>
        <tr><td>Door</td><td>DRV8871 driver (1.9 A limit) + INA219 current sense → stall stop</td></tr>
        <tr><td>Sensors</td><td>SHT40 temperature + humidity on a slotted island · light-barrier input (12 V safe, self-test)</td></tr>
        <tr><td>Outputs</td><td>Fan PWM + tach · WS2812 level shifter · 12 V button ring</td></tr>
        <tr><td>Clamps</td><td>8 WAGO push-in blocks on 3 edges</td></tr>
      </tbody></table>
    </div>
    <div>
      <h3>ESP32 pins</h3>
      <table><tbody>
        <tr><td class="m">25 / 26</td><td>DRV8871 IN1 (open) / IN2 (close)</td></tr>
        <tr><td class="m">32 / 33 / 18</td><td>Reed door closed / door open / drawer</td></tr>
        <tr><td class="m">19 / 23</td><td>Clean button / button ring</td></tr>
        <tr><td class="m">16</td><td>WS2812 data (level shifter)</td></tr>
        <tr><td class="m">17 / 27</td><td>Fan PWM / fan tach</td></tr>
        <tr><td class="m">21 / 22</td><td>I²C: INA219 0x40, SHT40 0x44, VL53L1X (clamp)</td></tr>
        <tr><td class="m">34 / 13</td><td>Light barrier input / sender on-off</td></tr>
        <tr><td class="m">4, 14, 35</td><td>Spare (EXP header)</td></tr>
      </tbody></table>
    </div>
  </div>
  <div class="cols2" style="margin-top:14px">
    <div>
      <h3>Order at JLCPCB</h3>
      <ol class="steps">
        <li>PCB: upload <code>robo-garage_gerbers_JLCPCB.zip</code> → 2 layers, 1.6 mm, HASL.</li>
        <li>Assembly: Economic, top side, 2 boards → upload BOM + CPL.</li>
        <li>Check the preview: pin 1 of U1–U5 (SHT40 pin 1 top left).</li>
        <li>Solder yourself: WAGO clamps, DevKit sockets, fan header.</li>
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
    <summary>ESPHome config v1.1</summary>
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
    'Wire it to the BUTTON clamp (BTN, GND, 12V, LED−): GPIO19 reads the switch, a MOSFET on the PCB switches the ring (GPIO23). The fascia is fixed, so no wires through the drag chain.</li>\n      <li><b>Light barrier:</b> sender + receiver on 2 small L-brackets at the front corners of the cabinet sides. Beam ≈12 cm in front of the door, ≈2 cm above the floor – past the ramp wedge and under the door\'s swing, so the door never breaks it itself. Both cables go to the BEAM clamp.</li>\n      <li><b>Controller:</b> PCB in its printed case under the top, the vented SHT40 corner open to the cabinet air. Keep those vents free.</li>')
old_wiring = s[s.index('  <details>\n    <summary>ESP32 wiring + ESPHome snippets</summary>'):s.index('  </details>\n</section>\n</div>\n\n<script>') + len('  </details>\n')]
assert old_wiring.count('<details>') == 1
rep(old_wiring, '''  <details>
    <summary>Wiring · PCB v1.1.1 clamps</summary>
    <div class="tablewrap" style="margin-top:8px"><table>
      <thead><tr><th>Clamp</th><th>Pins</th><th>Connect</th></tr></thead>
      <tbody>
        <tr><td>12 V IN</td><td class="m">+12V, GND</td><td>Mean Well GST36E12 → DC jack adapter</td></tr>
        <tr><td>ACTUATOR</td><td class="m">M+, M−</td><td>Linear actuator (wrong direction → swap the 2 wires)</td></tr>
        <tr><td>FAN</td><td class="m">4-pin</td><td>ARCTIC P12 Slim PWM plug</td></tr>
        <tr><td>LED</td><td class="m">5V, DAT, GND</td><td>WS2812B strip or ring (DIN)</td></tr>
        <tr><td>BUTTON</td><td class="m">BTN, GND, 12V, LED−</td><td>Alu button: NO, C, LED+, LED−</td></tr>
        <tr><td>REEDS</td><td class="m">CL/GND, OP/GND, DR/GND</td><td>Door closed, door open, drawer</td></tr>
        <tr><td>BEAM</td><td class="m">RX+, RX−, SIG, TX+, TX−</td><td>Receiver brown, blue, black · sender brown, blue</td></tr>
        <tr><td>I2C</td><td class="m">3V3, SDA, SCL, GND</td><td>VL53L1X (optional)</td></tr>
      </tbody>
    </table></div>
    <p class="note">Full ESPHome config, pin table and files: <a href="#pcb">Controller PCB</a>.</p>
  </details>
''')

print('html replacements ok:', n_ok)
exec(open(os.path.join(HERE, 'build_js.py'), encoding='utf-8').read())
open(OUT, 'w', encoding='utf-8').write(s)
print('written', OUT, len(s), 'bytes, replacements', n_ok)
