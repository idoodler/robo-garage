# Robo-Garage controller PCB v1.2

100 × 100 mm, 2 layers, all parts on top. Made with KiCad 7 + Freerouting (FOSS). DRC: 0 errors, 0 warnings, 0 unconnected.
**Every BOM line has an LCSC number → JLCPCB assembles the whole board (SMD + the clamps, sockets and fan header). You only plug in the DevKitC.**

**New in v1.2**
| Change | Detail |
|---|---|
| Clamps assembled | WAGO 804 (not at LCSC) → Cixi Kefa **KF250-3.5** spring clamps (push button, 45° wire entry, 0.2–0.75 mm², 5 A), 2P/3P/4P/6P all in stock at LCSC |
| LEAK clamp (J13) | 4 poles: 3V3, SIG, GND, 12V (3V3 and 12V PTC-fused; 12V only next to GND, 0.3 mm clearance). Bare electrodes (pulsed 3.3 V, no corrosion) **or** any leak sensor with a digital output. ADC on IO35, clamp diode. HA: "Water leak", "Leak probe" |
| VALVE clamp (J14) | Right edge, between BUTTON and REEDS. 12 V low-side switch (AO3400A, SS34 flyback, PTC 1.5 A / 16 V) for a water valve. A leak powers it automatically. HA: "Water valve" |
| Buzzer (BZ1) | MLT-8530 on 5 V, driven by IO15 (rtttl). Leak alarm beeps even with the "Buzzer" switch off |
| 12 V monitor | 100k/22k divider on VP (IO36). HA: "12 V rail", "Supply voltage low" (< 10.5 V) |
| DevKit sockets | Three 1×19 sockets: J3 + J4 (25.4 mm row spacing) or J3 + J15 (22.86 mm). Both pitches fit, no measuring. **DevKit USB-C at the left board edge** (through the case wall), antenna inboard over a copper keep-out |
| JLC requests | 3 tooling holes Ø1.152 mm (TH1–TH3, corners), pin-1 dots on all ICs / transistors / diodes, rotation rule for SOT-23 fixed |
| Silkscreen | JLC standard size (≥ 1.0 mm text, 0.17 mm stroke), every pole and circuit block named. Back: title, author (David Gölzhäuser · idoodler), repo link + QR code, fuse table, clamp limits. Every text is checked against pads, parts, other silk and the board edge (JLC: 0.15 mm to pads); no vias under title, author, repo and QR code |

## Files
| File | Use |
|---|---|
| `robo-garage_gerbers_JLCPCB.zip` | Upload at JLCPCB (PCB) |
| `robo-garage_BOM_JLCPCB.csv`, `robo-garage_CPL_JLCPCB.csv` | PCB Assembly: BOM + pick & place (45 lines, 110 parts) |
| `pin1-check.png` | Intended orientation of every polarised part: compare with JLC's placement preview |
| `robo-garage-pcb.yaml` | ESPHome config for this board |
| `kicad/` | KiCad project to edit later |
| `render_top.png`, `render_bottom.png` | Pictures |

## Order at JLCPCB
| Step | Setting |
|---|---|
| 1 PCB | Upload the gerbers zip → 2 layers, 1.6 mm, LeadFree HASL, 1 oz, via covering *Tented*, "Mark on PCB": default (no order number since May 2026). The C-shaped slot around the SHT40 (bottom right) is intended (heat isolation): confirm if JLC asks |
| 2 Assembly | **Economic**, top side, 2 boards, **Tooling holes: Added by Customer** (TH1–TH3 are on the board), *Confirm Parts Placement* = yes |
| 3 Files | Upload BOM + CPL. Parts list: all 45 lines must match by LCSC number (0 "no part selected") |
| 4 THT | The clamps, the 3 sockets and the fan header are THT: keep them ticked → JLC solders them (wave / hand soldering fee ≈ $3.5 + $0.02 per joint, 94 joints per board) |
| 5 Preview | Compare the placement preview with **`pin1-check.png`**: U1–U5, Q1–Q7, D1–D7, LED1, C1, C3, C13 and the clamps (wire entry towards the board edge, J3/J4/J15 pin 1 at the left = DevKit USB end). Rotate in the preview if one differs |
| 6 Price | ≈ 30 "extended" part types (≈ $3 loading fee each, once per order) — normal for a board like this |

Out of stock? SHT40 → SHT40-AD1B-R3 (C2848306) / SHT41-AD1B-R2 (C7461861). F3 → any 1206 PTC 200 mA ≥ 24 V (e.g. C2892415). F4 → any 1206 PTC 1–1.5 A ≥ 16 V (e.g. C883131); **not** the 6 V ASMD1206-150 of F2. KF250 clamp → same footprint family DG250-3.5 / WJ250-3.5 (check the drawing: Ø1.2 holes, 3.5 mm pitch, single row), or leave that line out and hand-solder.

## Parts to buy separately
| Part | Qty | Where it goes |
|---|---|---|
| ESP32 DevKitC V4, **WROOM** (not WROVER: GPIO16/17 are used), board 1.1 in (28 mm) or 1.0 in (25.4 mm) wide – not the narrow 0.9 in clone | 1 | Plugs into J3 + J4 (25.4 mm rows) or J3 + J15 (22.86 mm), USB-C to the left board edge |
| Light barrier pair, 12–24 V DC, through-beam, **NPN**, **Light-ON** (often sold as "NC"), e.g. Omron E3Z-T61 set to L-ON. Dark-ON ("NO", e.g. E3F-5DN1) works too → `beam_inverted: "false"` | 1 | BEAM clamp |
| Leak detection: 2 stainless screws / bare wire ends 5–10 mm apart on the cabinet floor (nothing else needed), **or** a leak sensor with a digital output: NPN / open-collector (12 V or 3.3 V supply, plus a 10 kΩ resistor between the 3V3 and SIG poles) or 3.3–5 V logic module (LM393 type, 3.3 V supply, ≤ 50 mA) | 1 | LEAK clamp |
| Water valve 12 V DC, ≤ 1.2 A, that **closes when powered** (normally-open solenoid or motorised ball valve "NO") | 1 | VALVE clamp (optional) |
| VL53L1X module | 1 | I2C clamp (optional) |

## Wiring
| Clamp | Pins (from the board edge) | Connect |
|---|---|---|
| 12 V IN | +12V, GND | GST36E12 plug → DC-jack adapter → 2 wires |
| ACTUATOR | M+, M− | Actuator. Door moves the wrong way → swap the 2 wires |
| FAN | 4-pin header | ARCTIC P12 Slim PWM plug |
| LED | 5V, DAT, GND | WS2812B strip / ring (DIN) |
| BUTTON | BTN, GND, 12V, LED− | Alu button: NO, C, LED+, LED− |
| REEDS | CL/GND, OP/GND, DR/GND | Door closed, door open, drawer reed |
| BEAM (left) | RX+, RX−, SIG, TX+, TX−, GND | Receiver: brown, blue, black. Emitter: brown, blue. Beam across the cabinet front, ≈ 12 cm in front of the door, ≈ 2 cm above the floor |
| LEAK (left) | 3V3, SIG, GND, 12V | Electrodes: SIG + GND (no polarity). Digital sensor: VCC → 3V3 (≤ 50 mA) or 12V, OUT → SIG (0–5 V only, never 12 V), GND; NPN / open collector: 10 kΩ between 3V3 and SIG. Wet = SIG low (NPN / active-low); active-high sensor → `leak_inverted: "true"` |
| VALVE (right) | 12V, VLV | Valve + → 12V, valve − → VLV (low side, flyback diode on board), ≤ 1.2 A |
| I2C ToF | 3V3, SDA, SCL, GND | VL53L1X module (optional) |

**Clamps:** push the button with a 2.5 mm screwdriver, insert the stripped wire (6–7 mm, 0.2–0.75 mm², ferrules OK) at 45° from the board edge, release.

## Pins (ESP32)
| GPIO | Function |
|---|---|
| 25 / 26 | DRV8871 IN1 (open) / IN2 (close) |
| 32 / 33 / 18 | Reed door closed / door open / drawer |
| 19 | Clean button |
| 23 | Button ring (AO3400A, 12 V) |
| 16 | WS2812 data (74AHCT1G125 → 330 Ω) |
| 17 / 27 | Fan PWM (2N7002, inverted) / fan tach |
| 21 / 22 | I²C SDA / SCL (INA219 0x40 + SHT40 0x44 on board, VL53L1X on the clamp) |
| 34 | Light barrier input (via 2N7002, 12 V safe) |
| 13 | Light barrier emitter on/off (AO3400A) |
| 4 / 35 | Leak drive (pulsed 3.3 V through 100 k) / leak ADC (BAT54S clamp) |
| 2 | Valve (AO3400A low side, 10 k pull-down: off at boot) |
| 15 | Buzzer (AO3400A, 10 k pull-down: off at boot) |
| 36 (VP) | 12 V rail ADC (100k / 22k, BAT54S clamp) |
| 14, 5, 39 (VN) | Spare on the EXP header J11 (not assembled); 39 = input only |

## Sensors, safety, alarms
| Item | How it works |
|---|---|
| Leak | Every 10 s IO4 drives 3.3 V through 100 k for 70 ms, IO35 reads SIG (dry electrodes ≈ 3.1 V, a digital sensor 0 V / 3.3 V). 3 wet readings in a row (25 s) → "Water leak" on, valve powered, red strobe, beep. Water gone → LED off after 60 s; **the valve stays powered until you switch it off in HA**. Tap water between two screws 5–10 mm apart reads well below 1 V; only very clean water (< 200 kΩ needed) could stay above the 2.2 V threshold → raise `leak_threshold` to 2.8 then. |
| Valve | Use a valve that closes when powered: a cut wire or a dead PSU cannot shut the water, but a leak does. F4 (1.5 A / 16 V PTC) protects the output. |
| Buzzer | Alerts in ESPHome via `rtttl.play`. "Buzzer" switch off → everything except the leak alarm is silent. |
| 12 V rail | "12 V rail" sensor (±0.3 V) and "Supply voltage low" when it sags below `supply_low` (weak PSU, stalled actuator). |
| SHT40 | Own island + vented case chamber → cabinet air. Set `offset` in the YAML after a check. Humidity can read low for 1–2 days after soldering. |
| Auto vent | Fan on above 65 %RH / 30 °C (HA numbers), 30–100 % speed; off 5 %RH / 1 °C below, and while the drawer is out. |
| Light barrier | Door does not close while the beam is blocked; broken while closing → stop + reopen. Self-test before every close and every 10 min (emitter off, receiver must react) → "Door beam fault". |
| Stall stop | INA219 motor current > `stall_current` (default 0.8 A) → stop. |

## Power
12 V 3 A in → PTC 2.6 A → reverse-polarity P-FET → TVS 15 V. LMR51430 buck makes 5.1 V (3 A max) for the ESP32 (via Schottky, USB can stay plugged in), the LEDs (PTC 1.5 A) and the buzzer. Light barrier: 12 V via PTC 200 mA (F3). Valve: 12 V via PTC 1.5 A (F4).
Worst case ≈ 2.5 A from the adapter with the valve on. Keep LED brightness low (full white on all LEDs heats the buck).

| Limit | Value |
|---|---|
| LED clamp | 1.2 A continuous (PTC 1.5 A hold at 23 °C, less when warm) ≈ 20 LEDs at full white; 16 LEDs are fine |
| BEAM clamp | 200 mA (PTC) for receiver + emitter (typ. 30–50 mA) |
| VALVE clamp | 1.2 A continuous (PTC 1.5 A hold at 23 °C), 12 V, inductive loads OK (SS34) |
| Actuator | DRV8871 limits at ≈ 1.9 A (R5 = 33 kΩ) |
| Clamps | 5 A, 0.2–0.75 mm² |
| LEAK poles | 12V: 200 mA (PTC). 3V3: ≤ 50 mA (it shares the DevKit regulator with the ESP32; PTC 200 mA only against shorts) |
