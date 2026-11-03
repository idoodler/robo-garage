# Robo-Garage case v1.2 (for controller PCB v1.2)

Base + lid, OpenSCAD (FOSS). Checked against a PCB stand-in: 0 mm³ overlap with parts.

v1.2: left window + lid cut-out now span VALVE / LEAK / BEAM (KF250 clamps, 11.7 mm high), sound holes above the buzzer, lid vents moved right of the LEAK label, 3 mm bridge keeps the front-left lid corner (screw post) attached, **the DevKit's own USB-C pokes through the left wall** (opening + plug pocket, closed by the lid) so the ESP32 is flashed with the lid on; VALVE clamp now on the right edge (between BUTTON and REEDS).

## Files
| File | Use |
|---|---|
| `base.stl` | Print as is (floor down) |
| `lid_print.stl` | Print as is (already flipped: top face on the bed) |
| `robo-garage-case.scad` + `pcb_data.scad` | Source. `part = "base"`, `"lid_print"`, `"assembly"` |
| `gen_pcb_data.py` | Rebuilds `pcb_data.scad` from the PCB `parts.py` |
| `view_assembly.png`, `view_lid_top.png` | Pictures |

## Print
| Setting | Value |
|---|---|
| Material | PETG (warm, humid cabinet) |
| Layer / walls / infill | 0.2 mm / 3 perimeters / 20 % |
| Supports | none |
| Size | base 135 × 132 × 26 mm, lid 105 × 105 × 20 mm |

## Hardware
| Part | Qty | Use |
|---|---|---|
| M3 × 25 pan-head screw | 4 | Lid → PCB → base posts (cuts its own thread in the Ø2.8 hole) |
| 4 mm countersunk wood screw | 4 | Base to the cabinet |
| Zip ties ≤ 4 mm | ≈ 10 | Strain relief on the 3 shelves |

## Assembly
1. PCB on the 4 posts: LEAK/BEAM clamps + USB-C left, ACT/FAN/LED/I2C front, 12V/BTN/VALVE/REEDS right.
2. Lid on, 4 × M3 × 25. Snug only (plastic thread).
3. Wire into the clamps, lay the wires on the shelf, zip-tie.
4. DevKit into the sockets (USB-C towards the left wall, antenna inboard). Lid on: its edge closes the USB-C opening.
5. Flash through the USB-C opening (lid stays on). After the first flash: OTA.

## Notes
| Topic | Note |
|---|---|
| T/H chamber | Front-right corner = own chamber for the SHT40, vents in wall, floor and lid. Keep them free. |
| WiFi | Antenna sits back-left (vented wall): no metal within 15 mm there. |
| Rails | Under each clamp strip a rail carries the push-button force. |
| Clamps | KF250: wire in at 45° from the window side, push button on top (lid is 4.8 mm above it). |
| Buzzer | 9 holes Ø1.6 in the lid above BZ1. |
| USB-C | 13 mm wide opening in the left wall from 4 mm below the receptacle centre up to the lid, with a 1 mm plug pocket outside; fits the 25.4 mm and the 22.86 mm DevKit widths. The receptacle face is ≈ 0.5 mm behind the pocket floor, so any USB-C cable reaches. |
| Mounting | Base plate against the cabinet top (lid down, clamp buttons reachable from below), USB-C wall towards the cabinet front. |
| Wi-Fi | The DevKit antenna now sits over the board (copper keep-out underneath): a little less range than the v1.1 overhang, fine inside a flat. |
