# Robo-Garage case v1.2 (for controller PCB v1.2)

Base + lid, OpenSCAD (FOSS). Checked against a PCB stand-in: 0 mm³ overlap with parts.

v1.2: left window + lid cut-out now span VALVE / LEAK / BEAM (KF250 clamps, 11.7 mm high), sound holes above the buzzer, lid vents moved right of the LEAK/VALVE labels, 3 mm bridge keeps the front-left lid corner (screw post) attached, **USB-C panel socket** opening in the back wall (right of the DevKit) so the ESP32 can be flashed with the lid on.

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
| Size | base 142 × 132 × 25 mm, lid 112 × 105 × 19 mm |

## Hardware
| Part | Qty | Use |
|---|---|---|
| M3 × 25 pan-head screw | 4 | Lid → PCB → base posts (cuts its own thread in the Ø2.8 hole) |
| 4 mm countersunk wood screw | 4 | Base to the cabinet |
| USB-C panel-mount extension, flange with 2 M3 holes 18 mm apart, 15–30 cm pigtail (SparkFun CAB-15455 or generic) + 2× M3×8 | 1 | Back wall, screws from outside into the bosses |
| Zip ties ≤ 4 mm | ≈ 10 | Strain relief on the 3 shelves |

## Assembly
1. PCB on the 4 posts: VALVE/LEAK/BEAM clamps left, ACT/FAN/LED/I2C front, 12V/BTN/REEDS right.
2. Lid on, 4 × M3 × 25. Snug only (plastic thread).
3. Wire into the clamps, lay the wires on the shelf, zip-tie.
4. USB-C socket into the back wall (2× M3×8), its plug into the DevKit (straight in, 22 mm free in front of the port), coil the rest of the pigtail above the buck.
5. Flash through the USB-C socket (lid stays on). After the first flash: OTA.

## Notes
| Topic | Note |
|---|---|
| T/H chamber | Front-right corner = own chamber for the SHT40, vents in wall, floor and lid. Keep them free. |
| WiFi | Antenna sits back-left (vented wall): no metal within 15 mm there. |
| Rails | Under each clamp strip a rail carries the push-button force. |
| Clamps | KF250: wire in at 45° from the window side, push button on top (lid is 4.8 mm above it). |
| Buzzer | 9 holes Ø1.6 in the lid above BZ1. |
| USB-C | Cut-out 11 × 7 mm + 2 pilot holes Ø2.6 (18 mm apart) in 4 mm bosses. Other socket? Set `usb_cut`, `usb_pitch`, `usb_x`, `usb_z` in the SCAD and rebuild. |
| Mounting | Base plate against the cabinet top (lid down, clamp buttons reachable from below), USB-C wall towards the cabinet front. |
