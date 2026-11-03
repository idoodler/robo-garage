# Robo-Garage controller PCB v1.3

100 × 100 mm, 2 layers, 1 oz copper, all parts on top. Made with KiCad 7 + Freerouting (FOSS). DRC: 0 errors, 0 warnings, 0 unconnected.
**Every BOM line has an LCSC number (all in stock, checked 3 Nov 2026) → JLCPCB assembles the whole board (SMD + clamps, sockets, fan header). You only plug in the DevKitC.**

**New in v1.3: power headroom**
| Area | v1.2 | v1.3 |
|---|---|---|
| 12 V input | 3 A, 2-pole clamp, PTC 2.6 A, AO3407A | **6 A**, 4-pole clamp (2 × 12V, 2 × GND), PTC 7 A (2920), P-FET AO4407C (11.5 mΩ), TVS SMAJ15A |
| Actuator | DRV8871, limit 1.9 A | **DRV8874** (6 A peak), current limit **4.9 A** (R5 = 1.5 kΩ), 3 A moves |
| Motor current | 0.1 Ω shunt, INA219 range 3.2 A | 20 mΩ / 2 W shunt with Kelvin taps, INA219 range 8 A |
| Valve | AO3400A, PTC 1.5 A → max 1.2 A | **IRLTS6342** (30 V, 8.3 A), PTC 4 A (1812) → **max 3 A** |
| 12 V aux | direct from the rail | own PTCs: F7 1.1 A (fan, beam, leak), F8 0.2 A (button LED) |
| LED 5 V | PTC 1.5 A | PTC 2 A |
| T/H sensor | SHT40 | SHT41 (same footprint, address 0x44) |
| Copper | 1.0–1.5 mm | every power path checked against IPC-2221 (table below) |

## Limits (also printed on the back)
| Output | Limit | Protection |
|---|---|---|
| 12 V IN | 6 A continuous (board ≤ 40 °C). PSU 12 V / 5 A recommended, a 3 A PSU still works | F1 PTC 7 A hold / 14 A trip, reverse-polarity P-FET, TVS 15 V |
| ACTUATOR | 3 A moving, **4.9 A hardware limit** | DRV8874 current regulation + over-current + thermal shutdown, INA219 stall stop (firmware) |
| VALVE | 12 V, **3 A** continuous, inductive OK | F4 PTC 4 A hold (≈ 3.2 A at 50 °C), SS34 flyback |
| LED 5 V | 1.5 A (16 WS2812 at full white ≈ 1 A) | F2 PTC 2 A |
| 5 V rail total | 3 A | LMR51430 current limit + hiccup |
| FAN + BEAM + LEAK 12 V | 1.1 A together | F7 1.1 A, F3 / F5 0.2 A per sensor feed |
| BUTTON LED 12 V | 0.2 A | F8 0.2 A |
| LEAK 3V3 | 50 mA | F6 0.2 A (shares the DevKit regulator) |
| Clamps | 5 A per pole, 0.2–0.75 mm² | – |

## Copper check (IPC-2221, outer layer, 1 oz)
DC network solve over every track and via of each power net, current = the limit above. Need = IPC-2221 width for ≤ 20 °C rise.
| Path | Current | Copper (narrowest) | Need | Drop |
|---|---|---|---|---|
| 12V IN → F1 → Q1 | 7 A | 3.0 / 4.2 mm | 2.9 mm | 21 mV |
| Q1 → shunt (west trunk) | 4.9 A | 2.0 mm | 1.8 mm | 81 mV |
| Q1 → valve PTC (east branch) | 4 A | 2.0 mm | 1.3 mm | 21 mV |
| Shunt → DRV8874 VM | 4.9 A | 2.0 mm | 1.8 mm | 67 mV |
| DRV8874 → ACTUATOR clamp | 4.9 A | 1.8 mm (spots ≤ 5 mm long: 1.5–1.7 mm) | 1.8 mm | 46 / 64 mV |
| VALVE 12V / VLV | 4 A | 1.5 mm | 1.3 mm | 21 / 20 mV |
| Buck input | 1.5 A | 0.8 mm | 0.4 mm | 29 mV |
| 5 V buck → LED clamp | 2 A | 0.8 mm | 0.5 mm | 92 mV |
| Aux 12 V (fan, beam, leak) | 1.1 A | 0.6 mm | 0.2 mm | 42 mV |
| Vias in power paths | ≤ 1.1 A | 0.4–0.6 mm drill | 1.3 A per via | – |

Pin necks: 0.4–0.6 mm for ≤ 1.4 mm at the 0.65 mm-pitch DRV8874 pins and the buck SW pin (set by the pin pitch; the wide copper starts right after the pad).
At 4.9 A the 1.5 mm spots run ≈ 26 °C above ambient when held for minutes; a door move takes ≤ 15 s.

## Part checks (datasheets)
| Part | Check | OK |
|---|---|---|
| DRV8874PWPR (U1) | VM 4.5–37 V, 6 A peak, 200 mΩ HS+LS. 3 A → 1.8 W for ≤ 15 s per move; a stall at 4.9 A ends in the firmware stall stop or the driver's thermal shutdown | ✓ |
| LMR51430XFDDCR (U4) | 500 kHz FPWM, 4.5–36 V in, 3 A. TI 12 → 5 V example: 6.8 µH + 44 µF → board: 6.8 µH (Isat 6 A) + 3 × 22 µF. EN tied to VIN through 100 k (allowed) | ✓ |
| INA219 (U2) | Bus ≤ 26 V; the TVS keeps surges ≤ 24.4 V | ✓ |
| IRLTS6342 (Q6) | 30 V, 8.3 A, Vgs ±12 V (driven at 3.3 V): 0.2 W at 3 A | ✓ |
| AO4407C (Q1) | 30 V, 14 A, Vgs ±25 V (BZT52C12 clamps it to 12 V): 0.4 W at 6 A | ✓ |
| R6 20 mΩ 2 W | 0.48 W at 4.9 A | ✓ |
| R44 10 Ω 1206 | ≈ 0.19 W while the buzzer sounds (0.25 W part) | ✓ |
| Electrolytics | C1 / C3 25 V on 12 V, C13 16 V on 5 V | ✓ |
| PTCs | voltage rating ≥ rail: F1 24 V, F4 16 V, F3/F5–F8 30 V on 12 V; F2 12 V on 5 V | ✓ |

## Files
| File | Use |
|---|---|
| `robo-garage_gerbers_JLCPCB.zip` | Upload at JLCPCB (PCB) |
| `robo-garage_BOM_JLCPCB.csv`, `robo-garage_CPL_JLCPCB.csv` | PCB Assembly: BOM + pick & place (48 lines, 114 parts) |
| `pin1-check.png` | Intended orientation of every polarised part: compare with JLC's placement preview |
| `robo-garage-pcb.yaml` | ESPHome config for this board |
| `kicad/` | KiCad project to edit later |
| `render_top.png`, `render_bottom.png` | Pictures |

## Order at JLCPCB
| Step | Setting |
|---|---|
| 1 PCB | Upload the gerbers zip → 2 layers, 1.6 mm, LeadFree HASL, **1 oz**, via covering *Tented*, "Mark on PCB": default. The C-shaped slot around the SHT41 (bottom right) is intended (heat isolation): confirm if JLC asks |
| 2 Assembly | **Economic**, top side, 2 boards, **Tooling holes: Added by Customer** (TH1–TH3 are on the board), *Confirm Parts Placement* = yes |
| 3 Files | Upload BOM + CPL. Parts list: all 48 lines must match by LCSC number (0 "no part selected") |
| 4 THT | The clamps, the 3 sockets and the fan header are THT: keep them ticked → JLC solders them (≈ $3.5 + $0.02 per joint, 96 joints per board) |
| 5 Preview | Compare the placement preview with **`pin1-check.png`**. New footprints in v1.3, check them first: **U1** (pin 1 top-left, next to IO25), **Q1** (pin 1 bottom-left), **Q6** (pin 1 top-left), D1, D2, D5, C1, C3, C13. Then U2–U5, Q2–Q7, D3–D7, LED1 and the clamps (wire entry towards the board edge, J3/J4/J15 pin 1 at the left = DevKit USB end). Rotate in the preview if one differs |
| 6 Price | ≈ 26 "extended" part types (≈ $3 loading fee each, once per order) – normal for a board like this |

Out of stock? U1 → DRV8874QPWPRQ1 (C22448174, same pinout). U5 → SHT40-AD1F-R2 (C7461846) or SHT41-AD1F-R2 (C7461862), same address, with PTFE cap. KF250 clamp → same footprint family DG250-3.5 / WJ250-3.5 (check the drawing: Ø1.2 holes, 3.5 mm pitch, single row), or leave that line out and hand-solder. PTCs → same size, hold current and at least the same voltage.

## Parts to buy separately
| Part | Qty | Where it goes |
|---|---|---|
| ESP32 DevKitC V4, **WROOM** (not WROVER: GPIO16/17 are used), board 1.1 in (28 mm) or 1.0 in (25.4 mm) wide – not the narrow 0.9 in clone | 1 | Plugs into J3 + J4 (25.4 mm rows) or J3 + J15 (22.86 mm), USB-C to the left board edge |
| Power supply 12 V DC, **5 A** (e.g. Mean Well GST60A12); the 3 A GST36E12 still works for the standard actuator | 1 | 12 V IN clamp (via a DC-jack adapter) |
| Light barrier pair, 12–24 V DC, through-beam, **NPN**, **Light-ON** (often sold as "NC"), e.g. Omron E3Z-T61 set to L-ON. Dark-ON ("NO", e.g. E3F-5DN1) works too → `beam_inverted: "false"` | 1 | BEAM clamp |
| Leak detection: 2 stainless screws / bare wire ends 5–10 mm apart on the cabinet floor (nothing else needed), **or** a leak sensor with a digital output: NPN / open-collector (12 V or 3.3 V supply, plus a 10 kΩ resistor between the 3V3 and SIG poles) or 3.3–5 V logic module (LM393 type, 3.3 V supply, ≤ 50 mA) | 1 | LEAK clamp |
| Water valve 12 V DC, **≤ 3 A**, that **closes when powered** (normally-open solenoid or motorised ball valve "NO") | 1 | VALVE clamp (optional) |
| VL53L1X module | 1 | I2C clamp (optional) |

## Wiring
| Clamp | Pins (top → bottom / left → right) | Connect |
|---|---|---|
| 12 V IN | +12V, +12V, GND, GND | 12 V adapter → DC-jack adapter. Up to 5 A one +12V + one GND is enough, above 5 A use both pairs |
| ACTUATOR | M+, M− | Actuator (≤ 4.9 A). Door moves the wrong way → swap the 2 wires |
| FAN | 4-pin header | ARCTIC P12 Slim PWM plug |
| LED | 5V, DAT, GND | WS2812B strip / ring (DIN) |
| BUTTON | BTN, GND, 12V, LED− | Alu button: NO, C, LED+, LED− |
| REEDS | CL/GND, OP/GND, DR/GND | Door closed, door open, drawer reed |
| BEAM (left) | RX+, RX−, SIG, TX+, TX−, GND | Receiver: brown, blue, black. Emitter: brown, blue. Beam across the cabinet front, ≈ 12 cm in front of the door, ≈ 2 cm above the floor |
| LEAK (left) | 3V3, SIG, GND, 12V | Electrodes: SIG + GND (no polarity). Digital sensor: VCC → 3V3 (≤ 50 mA) or 12V, OUT → SIG (0–5 V only, never 12 V), GND; NPN / open collector: 10 kΩ between 3V3 and SIG. Wet = SIG low (NPN / active-low); active-high sensor → `leak_inverted: "true"` |
| VALVE (right) | 12V, VLV | Valve + → 12V, valve − → VLV (low side, flyback diode on board), ≤ 3 A |
| I2C ToF | 3V3, SDA, SCL, GND | VL53L1X module (optional) |

**Clamps:** push the button with a 2.5 mm screwdriver, insert the stripped wire (6–7 mm, 0.2–0.75 mm², ferrules OK) at 45° from the board edge, release.

## Pins (ESP32)
| GPIO | Function |
|---|---|
| 25 / 26 | DRV8874 IN1 (open) / IN2 (close), PWM mode |
| 32 / 33 / 18 | Reed door closed / door open / drawer |
| 19 | Clean button |
| 23 | Button ring (AO3400A, 12 V) |
| 16 | WS2812 data (74AHCT1G125 → 330 Ω) |
| 17 / 27 | Fan PWM (2N7002, inverted) / fan tach |
| 21 / 22 | I²C SDA / SCL (INA219 0x40 + SHT41 0x44 on board, VL53L1X on the clamp) |
| 34 | Light barrier input (via 2N7002, 12 V safe) |
| 13 | Light barrier emitter on/off (AO3400A) |
| 4 / 35 | Leak drive (pulsed 3.3 V through 100 k) / leak ADC (BAT54S clamp) |
| 2 | Valve (IRLTS6342 low side, 10 k pull-down: off at boot) |
| 15 | Buzzer (AO3400A, 10 k pull-down: off at boot) |
| 36 (VP) | 12 V rail ADC (100k / 22k, BAT54S clamp) |
| 14, 5, 39 (VN) | Spare on the EXP header J11 (not assembled); 39 = input only |

## Sensors, safety, alarms
| Item | How it works |
|---|---|
| Leak | Every 10 s IO4 drives 3.3 V through 100 k for 70 ms, IO35 reads SIG (dry electrodes ≈ 3.1 V, a digital sensor 0 V / 3.3 V). 3 wet readings in a row (25 s) → "Water leak" on, valve powered, red strobe, beep. Water gone → LED off after 60 s; **the valve stays powered until you switch it off in HA**. Tap water between two screws 5–10 mm apart reads well below 1 V; only very clean water (< 200 kΩ needed) could stay above the 2.2 V threshold → raise `leak_threshold` to 2.8 then. |
| Valve | Use a valve that closes when powered: a cut wire or a dead PSU cannot shut the water, but a leak does. F4 (4 A / 16 V PTC) protects the output. |
| Buzzer | Alerts in ESPHome via `rtttl.play`. "Buzzer" switch off → everything except the leak alarm is silent. |
| 12 V rail | "12 V rail" sensor (±0.3 V) and "Supply voltage low" when it sags below `supply_low` (weak PSU, stalled actuator). |
| SHT41 | Own island + vented case chamber → cabinet air. Set `offset` in the YAML after a check. Humidity can read low for 1–2 days after soldering. |
| Auto vent | Fan on above 65 %RH / 30 °C (HA numbers), 30–100 % speed; off 5 %RH / 1 °C below, and while the drawer is out. |
| Light barrier | Door does not close while the beam is blocked; broken while closing → stop + reopen. Self-test before every close and every 10 min (emitter off, receiver must react) → "Door beam fault". |
| Stall stop | INA219 motor current > `stall_current` (default 0.8 A) → stop. Stronger actuator: set it ≈ 0.3 A above the running current shown in HA ("Door motor current"). |

## Power
12 V in (6 A) → PTC 7 A → reverse-polarity P-FET → TVS 15 V → three branches: actuator (shunt → DRV8874, 4.9 A limit), valve (PTC 4 A), aux 12 V (PTC 1.1 A: fan, beam, leak; PTC 0.2 A: button LED). LMR51430 buck makes 5.1 V (3 A max) for the ESP32 (via Schottky, USB can stay plugged in), the LEDs (PTC 2 A) and the buzzer.

| PSU sizing (12 V side) | Current |
|---|---|
| Actuator (running) | as measured, e.g. 1.5 A (board limit 4.9 A) |
| Valve | as rated, e.g. 0.5 A (board limit 3 A) |
| 5 V side (ESP32 + 16 LEDs full white + buzzer) | ≈ 0.6 A |
| Fan + beam + button LED | ≈ 0.3 A |
| **Sum** | standard parts ≈ 3 A → 12 V / 5 A PSU; the board itself takes up to 6 A |

Keep LED brightness low (full white on all LEDs heats the buck).
