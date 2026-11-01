# Robo-Garage controller PCB v1.1.1

100 × 100 mm, 2 layers, all SMD parts on top. Made with KiCad 7 + Freerouting (FOSS). DRC: 0 errors, 0 warnings, 0 unconnected.

**v1.1.1 (DRC clean-up, same parts / BOM / case / firmware):** silkscreen trimmed at the board edge · GND stitching vias about every 8 mm tie the top and bottom pours together (no copper island hangs on one pad any more) · Q3 + C16 GND pins solid to the pour · redundant autorouter tracks removed (CB stub, GND/3V3 jogs at C28). DRC checked in KiCad 7 and KiCad 10 (also after a zone refill).

**New in v1.1:** SHT40 temperature / humidity sensor (auto vent) on a thermally isolated island · light-barrier clamp (BEAM) with emitter self-test.

## Files
| File | Use |
|---|---|
| `robo-garage_gerbers_JLCPCB.zip` | Upload at JLCPCB (PCB) |
| `robo-garage_BOM_JLCPCB.csv` | PCB Assembly: BOM |
| `robo-garage_CPL_JLCPCB.csv` | PCB Assembly: pick & place |
| `robo-garage-pcb.yaml` | ESPHome config for this board |
| `kicad/` | KiCad project to edit later |
| `render_top.png`, `render_bottom.png` | Pictures |

## Order at JLCPCB
1. **PCB:** upload `robo-garage_gerbers_JLCPCB.zip` → 2 layers, 1.6 mm, LeadFree HASL, 1 oz, via covering *Tented*. "Mark on PCB": leave the default (no mark; JLCPCB stopped printing order numbers in May 2026, so the board has no JLCJLCJLCJLC text any more). The C-shaped slot around the SHT40 (bottom right) is intended (heat isolation): confirm if JLC asks.
2. **PCB Assembly:** Economic, top side, 2 boards → upload BOM + CPL.
3. **Check the placement preview:** pin 1 / polarity of U1–U5, Q1–Q5, D1–D3, LED1, C1, C3, C13. **U5 (SHT40): pin-1 mark top left** (towards the slot opening). Rotate in the preview if one looks wrong.
4. THT parts (J2–J12) are marked "THT (hand solder)": untick them in the assembly step and solder them yourself, or order JLC's THT assembly.
5. Out of stock? SHT40 → SHT40-AD1B-R3 (C2848306) or SHT41-AD1B-R2 (C7461861). F3 → any 1206 PTC 200 mA, ≥ 24 V (e.g. C2892415).

## Parts to buy separately (hand solder)
| Part | Qty | Where it goes |
|---|---|---|
| WAGO 804-102 | 3 | 12V IN, ACTUATOR, (spare) → J2, J5 |
| WAGO 804-103 | 1 | LED → J7 |
| WAGO 804-104 | 2 | BUTTON, I2C → J8, J10 |
| WAGO 804-105 | 1 | BEAM → J12 (new) |
| WAGO 804-106 | 1 | REEDS → J9 |
| 1×19 female header 2.54 mm, 8.5 mm | 2 | DevKitC socket J3 + J4 |
| Molex 47053-1000 (4-pin fan header) | 1 | FAN → J6 |
| Light barrier pair, 12–24 V DC, through-beam, **NPN**, **Light-ON** (often sold as "NC"), e.g. Omron E3Z-T61 set to L-ON. Dark-ON ("NO", e.g. E3F-5DN1) works too → set `beam_inverted: "false"` | 1 | BEAM clamp |

**DevKitC:** must be WROOM-based (not WROVER), because GPIO16/17 are used. Measure your board. 25.4 mm between rows → solder the bottom header into the **outer** row of J4; 22.86 mm → **inner** row.

## Wiring
| Clamp | Pins | Connect |
|---|---|---|
| 12 V IN | +12V, GND | GST36E12 plug → DC-jack adapter → 2 wires |
| ACTUATOR | M+, M− | Actuator. Door moves the wrong way → swap the 2 wires |
| FAN | 4-pin | ARCTIC P12 Slim PWM plug |
| LED | 5V, DAT, GND | WS2812B strip / ring (DIN) |
| BUTTON | BTN, GND, 12V, LED− | Alu button: NO, C, LED+, LED− |
| REEDS | CL/GND, OP/GND, DR/GND | Door closed, door open, drawer reed |
| BEAM (left edge) | RX+, RX−, SIG, TX+, TX− | Receiver: brown, blue, black. Emitter: brown, blue. Beam across the cabinet front, ≈ 12 cm in front of the door and ≈ 2 cm above the floor (past the ramp wedge, under the door's swing) |
| I2C ToF | 3V3, SDA, SCL, GND | VL53L1X module (optional) |

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
| 4, 14, 35 | Spare (EXP header; 35 = input only) |

## Sensors and door safety
| Item | How it works |
|---|---|
| SHT40 | Sits on an island with a milled slot, far from ESP32 / buck heat. The case gives it its own vented chamber → it measures cabinet air. Check once against a thermometer, set `offset` in the YAML if needed. Right after soldering, humidity can read a bit low for 1–2 days (normal). |
| Auto vent | Fan on above "Vent humidity limit" (65 %) or "Vent temperature limit" (30 °C), 30–100 % speed in 10 % steps; off again 5 %RH / 1 °C below, and while the drawer is out. "Vent auto" off → fan stops, then HA / manual control. |
| Light barrier | Door does not close while the beam is blocked. Beam broken while closing → stop + reopen. |
| Self-test | Before every close (and every 10 min) the emitter is switched off briefly (max 1.5 s): the receiver must react. If not → "Door beam fault" in HA and the door stays open. With a Light-ON sensor a cut wire or a tripped PTC reads "blocked" at once; with Dark-ON the next self-test catches it. |
| Beam always "Detected" | Nothing in the way? Check the 5 wires, the sensor alignment and F3. |
| Stall stop | Backup: INA219 motor current (unchanged) |

## Power
12 V 3 A in → PTC 2.6 A → reverse-polarity P-FET → TVS 15 V. LMR51430 buck makes 5.1 V (3 A max) for the ESP32 (via Schottky, so USB can stay plugged in) and the LEDs (PTC 1.5 A). The light barrier gets 12 V through its own PTC (200 mA): a short in its cable only trips F3 (the ESP32 may restart once; the door stays safe because the beam then reads "blocked").
Worst case ≈ 2 A from the 12 V adapter. Keep LED brightness low (full white on all LEDs heats the buck).

| Limit | Value |
|---|---|
| LED clamp | 1.5 A (PTC) ≈ 25 LEDs at full white; 16 LEDs are fine |
| BEAM clamp | 200 mA (PTC) for receiver + emitter (typ. 30–50 mA) |
| Actuator | DRV8871 limits at ≈ 1.9 A (R5 = 33 kΩ) |
| Stall stop | ESPHome `stall_current` (default 0.8 A): set it ≈ 0.3 A above the running current shown in HA |
