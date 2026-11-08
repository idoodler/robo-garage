# Doors: 3D-printed parts

Four door types, all for the same robot drawer. Pick one in the simulator; each has its own printed parts here.

| Door | How it opens | Out while moving | Out when open | Printed parts |
|---|---|---|---|---|
| **Lift door** | 6 mm panel slides up 147 mm behind the drawer front | 0 | 0 | 4 channels, saddle, foot, clamp |
| **Flap out** | Flap swings up and out to 90° | 207 mm | 207 mm | Lever, top mount |
| **Up & over** | Tilts up and slides into the cabinet, above the robot | 35 mm | 13 mm | 2 print-in-place modules, 2 tracks, top mount |
| **Parallel lift** | Moves out, then up, stays vertical | 40 mm | 23 mm | 2 print-in-place modules, top mount |

"Out" = how far the door comes in front of the drawer front. All doors use the same 12 V actuator (150 mm stroke, ≈225 mm pin to pin retracted).

## Print settings (all parts)

| Setting | Value |
|---|---|
| Material | PETG: the cabinet is warm and humid |
| Layers | 0.2 mm, first layer also 0.2 mm. The joint gaps are multiples of 0.2 mm |
| Walls / infill | 4 perimeters, 20 %. The pins and the lever need the walls: do not go below 4 |
| Supports / brim | None. Bridges only under the arms where they pass over the rings, 13.5 mm at most (left front arm; coupon joint `P` copies it) |
| Elephant-foot compensation | 0.1–0.2 mm |
| Orientation | As exported |
| Bed | 220 × 220 mm |

**Print-in-place joints (up & over, parallel lift):** print `coupon.stl` first. Twist each test joint firmly once and use
the smallest gap that then turns freely. Joint `P` is the big bore at 0.45 mm: if 45 turns but `P` stays stiff, use 0.55.
If your gap is not 0.45, rebuild with `doors/build.sh -D cj=0.35`: the door wedge (below) follows the gap.
After printing, move each module through its full travel a few times until all joints run smoothly. The left front arm has the longest bridge over its ring, so expect its joint to be the stiffest at first. A joint that sticks:
run a 0.4 mm nozzle-cleaning needle around the gap from the bed side, do not force it.

Slicer tips, these matter most for a joint that comes free: random seam (never "rear": pin and ring seams would face each other),
minimum travel for retraction 0.5 mm so it retracts across the gap, PETG at the low end (about 235 °C), outer wall at most 30 mm/s, fan about 50 %.

## How the hinges work

| Part | Design | Why |
|---|---|---|
| Joint | Hourglass pin in a ring with an inner lip, 0.45 mm radial gap, lip flanks 45° | Thickest at the root, where bending peaks. The lip holds the joint together |
| Pin | 4 mm hole through every 11 mm pin (parallel lift A1, A2, P2; up & over D). The P1 pins hold the rod socket; the up & over pivot pins (Ø 20 / Ø 14) stay solid | The walls then fill the whole pin and run on through its root. Without the hole the pin's 7 mm core prints as 20 % infill in OrcaSlicer and Bambu Studio (solid only below 15 mm²) and in PrusaSlicer with Prusa's own printer profiles (solid below 0 mm²); only PrusaSlicer's bare default (70 mm²) fills it |
| Arm rings | Parallel lift 5 mm wall; both doors: the ring runs into the arm as a 14 mm tapered lug | A ring on a narrower arm bends at the corner where they meet. On the up & over a thicker ring would bring the arm within 1.1 mm of the door, so it stays 3.5 mm |
| Arm roots | Parallel front arms 24 mm wide at their pivot; up & over left arm and lever 28 mm (right arm 12 mm) | Next to its pivot each arm steps from the upper layer down into the 6 mm ring layer; that step shears between the layers |
| Lever | Full height near the pivot and at the eye boss (M6 bolt and nut), 12 mm tall in between | Bending is highest at the pivot and falls to zero at the eye |
| Bracket underside | Grows out at 45° from the pins | No flat bridge over the rings, the print's worst spot in v2.0 |
| Wall plate | Rings + screw bosses + ribs, all full height, 3 mm fillets where ribs meet rings and bosses. 4 screws | The ribs follow the load paths. Ties and a 5th screw that carried little load are gone (FE at the design case: 33–35 N on the parallel lift's, under 5 N on the up & over's, against about 200 N on the busiest screw) |
| Plate rings | Thicker where the FE peaked: parallel P2 5 mm wall (v2.1: 3.5), left P1 12 mm (9), up & over right F 7 mm (4) | Where a ring drops to its 6 mm bottom layer (the arm's sweep cuts it above) and meets a full-height rib, the stress peaks: the joint loads sit on the bay side, the screws on the cheek side |
| Door flange (parallel lift) | Wedged about 2.2° | The door's weight takes up all joint play, which would lean its top 8 mm out when closed. The wedge cuts this to about 2 mm and still leaves 2 mm to the drawer front when parked |

Printed filament and time, as estimated by PrusaSlicer 2.8.1 at the settings above (0.2 mm layers, 4 perimeters, 20 % gyroid, 4 top and 4 bottom layers):

| Print | v2.1 | v2.2 |
|---|---|---|
| Parallel lift, left + right | 230 g, 20 h 13 min | 205 g, 18 h 24 min |
| Up & over, left + right | 173 g, 15 h 52 min | 151 g, 13 h 57 min |
| Coupon | 21 g | 26 g (joint `P` now also copies the arms' longest bridge) |

**Strength, calculated** (`check_strength.py`; nothing has been printed or bench-tested yet, see the tests below). Design case: the actuator stalls at 100 N
while the door is blocked at a corner, the block pushing against the door's motion up to 20° off it (side view). Worst pose, all on one module: 404 N on the
parallel lift's front bracket pin, 228 N on the up & over bracket pin. A 3D finite-element model of every module body (0.5 mm cells) as printed with the
settings above: walls and top / bottom layers solid, the 20 % core at a tenth of the stiffness. Each hot spot is averaged over a 1 mm ball: a single cell on a
stepped round surface keeps growing with finer cells (+25 to +40 % at 0.35–0.4 mm), the average far less (+4 to +19 %). "Use" = hot spot ÷ allowable, the worst of 45 MPa along the layers, 25 MPa
tension across them and 15 MPa shear between them: typical PETG values, assumed, not measured on a print.

| Worst spots, use at the design case | v2.1 | v2.2 |
|---|---|---|
| Up & over arm, its step into the ring layer next to the pivot | 1.35 | 0.87 |
| Up & over arm, pivot pin root | 1.06 | 0.54 |
| Up & over left plate, F ring | 0.47 | 0.70 |
| Parallel rear arm, pivot pin root (P2) | 0.93 | 0.84 |
| Parallel front arms, step at the pivot (shear between the layers) | 0.92–0.93 | 0.76–0.78 |
| Parallel bracket, front pin root | 0.82 | 0.66 |
| Parallel bracket, body | 0.78 | 0.81 |
| Parallel plates, left / right | 0.65 / 0.80 | 0.50 / 0.76 |
| **Worst of all** | **1.35** | **0.87** |

FE is linear and the joint loads come almost all from the actuator, so the use scales with the stall force.
**Actuator: 50 N, with the stall stop set so it cuts out at about 50 N** (`stall_current` in the ESPHome config, about 0.3 A above the running current;
`max_duration` backs it up). An actuator can stall well above its rating: the stall stop is what sets the force. At 50 N, by this calculation, the parallel lift
keeps a safety factor of 2.4 everywhere and the up & over 2.3 (about 2.0 and 2.2 with finer cells: the parallel lift's worst spot, the P2 pin root,
grew 19 % there, the up & over's 4 %); v2.1 had 1.5 there. The up & over needs 39 N to hold the door
without friction, so 50 N is about the least that works; more force only raises the joint loads. (All solid instead, `--solid`: worst use 0.81 in v2.1, 0.69 in v2.2.)

Misuse, also calculated (`check_strength.py --yank`: 150 N on a door corner, any direction in the side view, any pose, actuator holding, all on one module):

- Parallel lift: up to 742 N on a pin, worst use 1.78 (bracket body; v2.1: 1.93 at the front arm). A hard yank on one corner can break a module. Two spots got worse
  than in v2.1: the right plate at its P1 ring (1.05 → 1.51, it lost material to the wider front arm's sweep) and the bracket body (1.55 → 1.78).
  The door screws on their own could pull out too (earlier estimate, not part of the check), so **glue the flanges to the door**, see the door steps.
- **Up & over: never push or pull the closed door by hand.** Closed, the peg sits only 6.5 mm behind the door's pin (and 68 mm above it), so the track has almost
  no lever about the pin and the door is near a dead point: 20 N pushed on its top edge puts 440–500 N on that side's pin and peg and about 300 N on the actuator
  (statics); 150 N there would put 3.7 kN on them. Open, 150 N gives 273 N on a pin (statics).

## Test before you fit the door

No part of this design has been printed yet. These tests decide whether it is sound; stop at the first failure and report it.

| # | Test | Pass |
|---|---|---|
| 1 | `coupon.stl`: one firm twist on each joint | The joint at the gap you will use and joint `P` turn freely, no cracks. `P`'s flat bar spans 13.5 mm over its ring, 0.6 mm above it: the riskiest bridge of the modules (the left front arm over the P1 ring). If the bar sticks to the ring, the arm will too |
| 2 | Spare coupon, 0.45 joint: clamp the base tab in a vice, pull the post sideways with a luggage scale until it breaks | The same pin in the bracket reaches its allowable at about 600 N (FE). Note where it broke. Under 200 N, the worst pin load at a 50 N stall: do not use the design |
| 3 | Module: free all joints. Screw the plate to a board, hold the plate and rock the bracket by hand | Moves through the full travel, no binding, no cracks |
| 4 | Same module on the board: pull the bracket away from the plate with the scale, in line with the front arm, to 200 N for 10 s. That is about the worst pin load with a 50 N stall at one side (404 N at 100 N, halved) | No cracks or whitening, still turns freely |

## Lift door

![Lift door: closed, open, prints](lift_motion.png)

| File | Qty | What |
|---|---|---|
| `lift_channel.stl` | 4 | U-channel, 190 mm. 2 per side, one above the other. Replaces the alu profile |
| `lift_saddle.stl` | 1 | Clip over the panel's top left corner. The actuator rod pushes into its cup |
| `lift_foot.stl` | 1 | Clevis for the actuator's bottom eye, on the tray |
| `lift_clamp.stl` | 1 | Holds the actuator upright on the left cheek (zip tie) |
| `lift-door.scad` | | Source. Customizer: actuator length, rod eye, body diameter |

| Step | What to do |
|---|---|
| 1 | Channels: front edge 2 mm behind the cheek front edge, lower one on the tray, upper one on top of it. A piece of 1.75 mm filament in the end holes lines them up. 3 screws 3.5 × 16 each |
| 2 | Foot: centre 32 mm behind the cheek front edge, 36 mm from the left cheek. 2 screws 4 × 16 |
| 3 | Actuator bottom eye into the foot (M6 bolt + nut). Clamp at 145 mm above the tray, notch over the channel. 2 screws 4 × 16, zip tie round the actuator |
| 4 | Saddle on the panel's top left corner, centre 33 mm from the panel's left edge. M3 × 16 bolt + nut through lip, panel and plate (hidden behind the drawer front) |
| 5 | Panel into the channels. Closed it rests on the tray, the rod tip 3 mm under the cup |

Check (`check_simple.py`): panel rises 147 mm. Saddle 5 mm from the drawer front, 17 mm from the clamp. Parts do not touch.

## Flap out

![Flap: closed, half, open, prints](flap_motion.png)

| File | Qty | What |
|---|---|---|
| `flap_lever.stl` | 1 | Lever on the flap's back, reaches 92 mm above the hinge. Replaces the bent steel L-bracket |
| `flap_mount.stl` | 1 | Actuator top mount on the left cheek, ±8 mm slots |
| `flap.scad` | | Source |

| Step | What to do |
|---|---|
| 1 | Lever on the flap's back: outer face 55 mm from the flap's left edge, lower end 80 mm below the hinge axis. 3 screws 3.5 × 25 |
| 2 | Top mount: bolt 28 mm behind the cheek front edge, 525 mm above the tray. 3 screws 4 × 25 |
| 3 | Actuator: top eye on the mount boss, rod eye on the bay side of the lever pin (M6, washer between) |
| 4 | Retract the actuator fully, slide the mount until the flap just closes, tighten |

Check (`check_simple.py`): stroke 225 → 375 mm, lever arm 60–107 mm, holding force max 21 N.

## Up & over

![Up & over: closed, tilting, nearly open, open](upover_motion.png)

Like a small garage door. A peg on each door bracket runs in a short track; one arm per side tilts the door up.
Open, the door lies flat inside the cabinet, 137 mm above the tray, above the robot.

| File | Qty | What |
|---|---|---|
| `coupon.stl` | 1 | **Print first.** 3 test joints, 0.35 / 0.45 / 0.55 mm gap, plus big joint `P` |
| `upover_left.stl` | 1 | Left module, with the actuator lever. Printed half open, 206 × 206 mm |
| `upover_right.stl` | 1 | Right module, 197 × 134 mm |
| `upover_track_left.stl`, `upover_track_right.stl` | 1 + 1 | Tracks for the pegs |
| `upover_mount.stl` | 1 | Actuator top mount + rod-eye spacer |
| `upover_template.stl` | 1 | Drill template for plate and track screws |
| `up-over.scad` | | Source |

**Door:** 492 × 202 mm (2 mm lower than the other doors: 6 mm gap under the drawer front). No chamfer needed.

![Up & over: print layout](upover_print.png)

| Step | What to do |
|---|---|
| 1 | Template on the cheek: front edge against the back of the front leg, bottom edge on the tray. Pre-drill the 4 plate holes and 3 track holes (3 mm). Left cheek: turn it over like a page |
| 2 | Modules on the cheeks: 4 screws 4 × 20 each, from the robot side |
| 3 | Tracks over the pegs (slot towards the bay), 3 screws 3 × 16 each. A little grease in the slot |
| 4 | Door: hold it in place, closed. Brackets: bottom edge 23 mm above the door's bottom edge. Polyurethane or epoxy glue on the flange face (sand the PETG first), 3 screws 3.5 × 16 per bracket at 45° from the bay side (pre-drill 2.5 mm through the bracket holes) |
| 5 | Top mount: bolt 13 mm behind the cheek front edge, 428 mm above the tray. 3 screws 4 × 25 |
| 6 | Actuator: rod eye with the printed spacer on the lever (nyloc nut in the hex pocket), top eye on the mount boss |
| 7 | Retract fully, slide the mount until the door is just shut, tighten |

No sync rod: the arms sit at 98 mm height, right over the robot. The door itself keeps both sides in step.
Do not push or pull the closed door by hand (see "How the hinges work"): open and close it with the actuator only.

Check (`check_upover.py`): joint gap 0.45 mm, peg in its track 0.4 mm, other moving gaps ≥ 1.0 mm, each body one piece. Door ≥ 2.5 mm from the drawer front and from
the docked robot, 2 mm above the tray. Actuator 225 → 375 mm, no dead point, holding force max 39 N.
The peg is now Ø10 mm and its slot runs 3 mm past the open position, so the peg never ends up against the slot's end.

## Parallel lift

![Parallel lift: closed, half way, open](parallel_motion.png)

The door stays vertical. It moves out, then up on a circle and parks 116 mm higher, only 3.5 mm in front of the drawer front.

| File | Qty | What |
|---|---|---|
| `coupon.stl` | 1 | **Print first.** 3 test joints plus big joint `P` |
| `parallel_left.stl` | 1 | Left module, with the actuator lever. Printed open, 167 × 194 mm |
| `parallel_right.stl` | 1 | Right module, 143 × 194 mm |
| `parallel_mount.stl` | 1 | Actuator top mount + rod-eye spacer |
| `parallel_template.pdf` | 1 | Drill template on paper: print on A4 at 100 %, page 1 right cheek, page 2 left cheek |
| `parallel-lift.scad` | | Source |

**Door:** 492 × 204 mm. **45° chamfer on the top back edge, leave a 1 mm flat at the front.** It lets the door slide past
the drawer front's bottom edge; from the front you do not see it.

![Parallel lift: print layout](parallel_print.png)

| Step | What to do |
|---|---|
| 1 | Template: print `parallel_template.pdf` on A4 at 100 % ("actual size") and check that both bars measure 100 mm. Cut along the two cut lines, tape it on the cheek's inner face: front edge against the back of the front leg, bottom edge on the tray. Pre-drill the 4 crosses with 3 mm. Page 1 is the right cheek, page 2 the left |
| 2 | Left module on, 4 screws 4 × 20 from the robot side |
| 3 | Solid steel square rod 8 × 8 mm into the square hole of the left front arm, 14 mm deep (tight on purpose: file the hole if the rod does not go in). Length = distance between the cheeks − 16 mm (502 → 486 mm) |
| 4 | Right module onto the other end of the rod, then screw it on |
| 5 | Door: hold it closed. Bracket bottom = door bottom edge, outer face = door side edge. Pull the door flat against the flange: the flange is wedged on purpose (see "How the hinges work"), so do not shim it. Polyurethane or epoxy glue on the whole flange face (sand the PETG first), 3 screws 3.5 × 16 per bracket at 45° from the bay side (pre-drill 2.5 mm) |
| 6 | Top mount: bolt 59 mm behind the cheek front edge, 455 mm above the tray. Actuator with the spacer on the lever, as above |
| 7 | Retract fully, slide the mount until the door is flush, tighten |

Check (`check_parallel.py`): joint gap 0.45 mm, other gaps ≥ 1.0 mm, each body one piece. With the door's weight on the joints: top about 2 mm out when closed, 2 mm from the drawer front parked (1.3 mm if your real gap
comes out 0.1 mm tighter than set), 2 mm above the tray. Actuator 225 → 375 mm, holding force max 14 N.

## Reeds (all doors)

| Reed | Where |
|---|---|
| Door closed | Lift: on the tray under the panel. Others: magnet on the back of a bracket's (or the lever's) lower end, reed right behind it |
| Door open | Magnet on the lever tip (lift: on the saddle), reed where it stops. Set it so the door stops before the actuator's own end stop |

ESPHome: no change. Same endstop cover with both reeds.

## Hardware for every door

| Part | Qty |
|---|---|
| Linear actuator 12 V, 150 mm stroke, 50 N with the stall stop set up (sized for the up & over and the parallel lift, see "How the hinges work"; the flap needs 21 N), ≈225 mm pin to pin retracted | 1 |
| M6 bolts (eye thickness + 25 mm), nyloc nuts, washers | 2 |
| Countersunk wood screws, see the steps | – |

## Rebuild + check

| Command | What |
|---|---|
| `doors/build.sh` | All STL, the paper template `parallel_template.pdf` (`paper_template.py`) + `robo-garage-doors_v<version>.zip`. Extra args go to OpenSCAD, e.g. `-D cj=0.35` |
| `python3 doors/check_parallel.py` | Parallel lift: whole travel in 1 % steps (`--quick`: 5 %) |
| `python3 doors/check_upover.py` | Up & over |
| `python3 doors/check_simple.py` | Lift door + flap |
| `python3 doors/check_strength.py` | Up & over + parallel lift: joint loads over the whole travel, 3D FE of every module body as printed (`--yank`: misuse case, `--solid`: all solid). About 6 min on 32 cores; one body needs up to 16 GB and 3 run at a time (`--jobs=1` for a 16 GB machine) |
| `python3 doors/render.py` | The pictures in this file |

Needs `openscad`, `zip`, `xvfb-run`; Python `trimesh`, `rtree`, `shapely`, `numpy`, `Pillow`, `matplotlib` (paper template); for `check_strength.py` also `scipy`, `pyamg`.
