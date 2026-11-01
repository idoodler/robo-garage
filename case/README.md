# Robo-Garage case v1.1 (for controller PCB v1.1)

Base + lid, OpenSCAD (FOSS). Checked against a PCB stand-in: 0 mm³ overlap with parts.

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
| Zip ties ≤ 4 mm | ≈ 10 | Strain relief on the 3 shelves |

## Assembly
1. PCB on the 4 posts: BEAM clamp left, ACT/FAN/LED/I2C front, 12V/BTN/REEDS right.
2. Lid on, 4 × M3 × 25. Snug only (plastic thread).
3. Wire into the clamps, lay the wires on the shelf, zip-tie.
4. Flash: lid off → USB on the DevKit. After the first flash: OTA.

## Notes
| Topic | Note |
|---|---|
| T/H chamber | Front-right corner = own chamber for the SHT40, vents in wall, floor and lid. Keep them free. |
| WiFi | Antenna sits back-left (vented wall): no metal within 15 mm there. |
| Rails | Under each clamp strip a rail carries the push-button force. |
