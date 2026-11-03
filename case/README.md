# Robo-Garage case v1.3.1 (for controller PCB v1.3.1)

Base + lid, OpenSCAD (FOSS). Checked against a PCB v1.3.1 stand-in (clamps, DevKit + USB-C plug, electrolytics, inductor, buzzer, fan plug): 0 mm³ overlap with parts.

v1.3.1: the clamp solder pins sit in two rows (KF250 zig-zag, PCB v1.3.1): the three edge rails under the clamp strips are 0.4 mm narrower (outer pin row 1 mm away). Bodies, windows, lid unchanged.

v1.3: follows PCB v1.3 – the 12 V IN clamp has 4 poles now (right window and rail cover it), the LED window and the vents above / below the buck and the motor driver moved with their parts. Same print, same screws.

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
| T/H chamber | Front-right corner = own chamber for the SHT41, vents in wall, floor and lid. Keep them free. |
| WiFi | Antenna sits back-left (vented wall): no metal within 15 mm there. |
| Rails | Under each clamp strip a rail carries the push-button force. |
| Clamps | KF250: wire in at 45° from the window side, push button on top (lid is 4.8 mm above it). |
| Buzzer | 9 holes Ø1.6 in the lid above BZ1. |
| USB-C | 14.5 mm wide opening in the left wall from 4.5 mm below the receptacle centre up to the lid, a 1 mm plug pocket outside and a slot in the lid edge above it: fits both DevKit widths and plug overmolds up to 12 × 9 mm (checked in OpenSCAD: no collision at full insertion). The receptacle face is ≈ 0.5 mm behind the pocket floor. USB-C DevKit clones differ: if yours has the connector set back more than 1.6 mm from the board end, set the USB face offset (2.68 mm from pin 19) in `gen_pcb_data.py` and rebuild. |
| Mounting | Base plate against the cabinet top (lid down, clamp buttons reachable from below), USB-C wall towards the cabinet front. |
| Wi-Fi | The DevKit antenna now sits over the board (copper keep-out underneath): a little less range than the v1.1 overhang, fine inside a flat. |
