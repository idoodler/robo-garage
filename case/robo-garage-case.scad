// Robo-Garage controller PCB v1.2 - 3D printed base + lid (OpenSCAD, FOSS)
// Coordinates: x right, y up, z up. PCB occupies [0,100] x [0,100]; y = 0 is the edge with the
// ACTUATOR / FAN / LED / I2C clamps, x = 100 the edge with 12V IN / VALVE / BUTTON / REEDS, x = 0 the BEAM / LEAK clamps
// and the DevKit USB-C (through the wall).
// The front-right corner is a separate vented chamber for the SHT40 (measures cabinet air, not box air).
// part = "base" | "lid" | "lid_print" (lid flipped for printing) | "assembly" | "check_base" | "check_lid"
part = "assembly";
labels = true;     // false: no engraved text (small 3D model for the simulator page)
show_plug = true;  // USB-C plug stand-in in the assembly / fit views
version = "1.2";   // case version: release zip name (case/build.sh)

include <pcb_data.scad>

$fn = 48;
pcb = 100;  pcb_t = 1.6;
wall = 2.0; floor_t = 2.0;
clr = 0.5;          // PCB edge -> wall
ant = 0.0;          // v1.2: the DevKit antenna points inboard, its USB-C sits at the left board edge
stand_h = 5.0;      // floor -> PCB bottom (THT leads stick out ~2 mm)
inner_h = 17.5;     // PCB top -> lid (DevKit stack: 8.5 socket + 2.54 header spacer + 1.6 board + 3.2 USB-C = 15.8)
lid_t = 2.0;
shelf = 15.0;       // wire shelf with zip-tie slots on the clamp sides
gap = 0.3;          // walls stop 0.3 below the lid: the lid is clamped by its pillars
part_t = 1.2;       // sensor chamber partitions

z_pcb_bot = floor_t + stand_h;      // 7.0
z_pcb_top = z_pcb_bot + pcb_t;      // 8.6
z_lid = z_pcb_top + inner_h;        // 26.1

ix0 = -ant; ix1 = pcb + clr; iy0 = -clr; iy1 = pcb + clr;   // cavity
ox0 = ix0 - wall; ox1 = ix1 + wall; oy0 = iy0 - wall; oy1 = iy1 + wall;

// clamp windows (open sides) and lid cut-outs, from the clamp bodies in pcb_data.scad
J2 = wago[0]; J5 = wago[1]; J10 = wago[3]; J9 = wago[5]; J12 = wago[6]; J13 = wago[7]; J14 = wago[8];
right_y0 = J9[1] - 1.0;  right_y1 = J2[3] + 0.6;   // REEDS .. 12V IN (stays clear of the corner pillar)
bot_x0 = J5[0] - 1.0;    bot_x1 = J10[2] + 1.0;    // ACTUATOR .. I2C
left_y0 = J13[1] - 1.0;  left_y1 = J12[3] + 1.0;   // LEAK .. BEAM (v1.2)
// v1.2: the LEAK clamp sits close to the front clamp row, so the lid corner (screw post at 3.5/3.5) keeps
// a 3 mm bridge: the front cut-out stops at the J5 rear face for x < bridge_x1, the left cut-out starts 3 mm above it
bridge_w = 3.0; bridge_x1 = 19.0;
lid_left_y0 = max(left_y0, J5[3] + bridge_w);
win_z0 = floor_t + 2.0;                            // 2 mm curb, wires drop to the shelf

cx0 = chamber[0]; cy1 = chamber[3];                // sensor chamber: x > cx0 and y < cy1

screw_d = 3.4; pilot_d = 2.8; post_d = 7.0;
buck = [(l1_pos[0] + u4_pos[0]) / 2, l1_pos[1]];   // 12 V -> 5 V buck (vents in lid + floor)

// v1.2: the DevKit USB-C pokes through the left wall: the receptacle face sits 1 mm outside the PCB edge, i.e. just
// inside the wall (ix0 = -0.5); a 1 mm pocket in the outer face lets the plug overmold come close enough.
usb_yc = (devkit[2] + devkit[3]) / 2;                 // between the 25.4 mm and the 22.86 mm board centre lines
usb_zc = z_pcb_top + 8.5 + 2.54 + 1.6 + 1.6;          // USB-C receptacle centre (3.2 mm tall on the DevKit top)
usb_w = 13.0;                                         // opening width (receptacle 9 mm + both board widths)
usb_z0 = usb_zc - 3.8;                                // opening from here up to the wall top (the lid closes it)

module rbox(p0, p1) { translate(p0) cube([p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]]); }

// chamber partitions along x = cx0 and y = cy1, between z0 and z1
module partitions(z0, z1) {
    rbox([cx0 - part_t / 2, iy0, z0], [cx0 + part_t / 2, cy1 + part_t / 2, z1]);
    rbox([cx0 - part_t / 2, cy1 - part_t / 2, z0], [ix1, cy1 + part_t / 2, z1]);
}

// ---------------- base ----------------
module base() {
    difference() {
        union() {
            // floor incl. shelves (right + front full length, left front half) and a mounting tab (back)
            rbox([ox0, oy0 - shelf, 0], [ox1 + shelf, oy1, floor_t]);
            rbox([ox0 - shelf, oy0 - shelf, 0], [ox0, 66, floor_t]);
            rbox([40, oy1, 0], [60, oy1 + 12, floor_t]);
            // walls
            difference() {
                rbox([ox0, oy0, 0], [ox1, oy1, z_lid - gap]);
                rbox([ix0, iy0, -1], [ix1, iy1, 99]);
                // clamp windows
                rbox([ix1 - 1, right_y0, win_z0], [ox1 + 1, right_y1, 99]);
                rbox([bot_x0, oy0 - 1, win_z0], [bot_x1, iy0 + 1, 99]);
                rbox([ox0 - 1, left_y0, win_z0], [ix0 + 1, left_y1, 99]);
                // vents in the left wall, below the USB-C opening
                for (y = [58 : 6 : 72]) rbox([ox0 - 1, y, 12], [ix0 + 1, y + 3, 20]);
                // v1.2: USB-C opening (open to the top, the lid closes it) + 1 mm pocket for the plug overmold
                rbox([ox0 - 1, usb_yc - usb_w / 2, usb_z0], [ix0 + 1, usb_yc + usb_w / 2, 99]);
                rbox([ox0 - 1, usb_yc - usb_w / 2 - 2, usb_z0 - 1.5], [ox0 + 1.0, usb_yc + usb_w / 2 + 2, 99]);
                // sensor chamber vents (front + right wall), below and above the PCB
                for (x = [cx0 + 3 : 4 : 92]) {
                    rbox([x, oy0 - 1, 2.5], [x + 2, iy0 + 1, z_pcb_bot - 1]);
                    rbox([x, oy0 - 1, z_pcb_top + 2], [x + 2, iy0 + 1, z_lid - 3]);
                }
                for (y = [2 : 4 : cy1 - 4]) {
                    rbox([ix1 - 1, y, 2.5], [ox1 + 1, y + 2, z_pcb_bot - 1]);
                    rbox([ix1 - 1, y, z_pcb_top + 2], [ox1 + 1, y + 2, z_lid - 3]);
                }
            }
            // standoffs at the 4 PCB holes
            for (h = holes) translate([h[0], h[1], 0]) cylinder(d = post_d, h = z_pcb_bot);
            // edge rails under the clamp strips (between board edge and solder pins), not in the chamber
            rbox([96.6, right_y0 + 1, 0], [99.6, 92, z_pcb_bot]);
            rbox([8, 0.4, 0], [bot_x1 - 1, 3.4, z_pcb_bot]);
            rbox([0.4, left_y0 + 1, 0], [3.4, left_y1 - 1, z_pcb_bot]);
            // posts under the DevKit (pressing it in)
            for (x = [14, 38]) translate([x, 82, 0]) cylinder(d = 5, h = z_pcb_bot);
            // sensor chamber: partitions floor -> PCB bottom, and closing the PCB-edge gap up to the PCB top
            partitions(0, z_pcb_bot);
            rbox([cx0 - part_t / 2, iy0, z_pcb_bot - 0.01], [cx0 + part_t / 2, 0, z_pcb_top]);
            rbox([pcb, cy1 - part_t / 2, z_pcb_bot - 0.01], [ix1, cy1 + part_t / 2, z_pcb_top]);
        }
        // pilot holes for M3 x 25 (self-tapping into the post, 1 mm floor left)
        for (h = holes) translate([h[0], h[1], 1.0]) cylinder(d = pilot_d, h = 20);
        // zip-tie slots: right shelf, front shelf, left shelf
        for (y = [2 : 7 : 98]) if (abs(y - 50) > 6) translate([ox1 + 4.5, y, -1]) rbox([-2.25, -1.1, 0], [2.25, 1.1, 5]);
        for (x = [2 : 7 : 98]) if (abs(x - 50) > 6) translate([x, oy0 - 4.5, -1]) rbox([-1.1, -2.25, 0], [1.1, 2.25, 5]);
        for (y = [2 : 7 : 62]) if (abs(y - 40) > 6) translate([ox0 - 4.5, y, -1]) rbox([-2.25, -1.1, 0], [2.25, 1.1, 5]);
        // mounting holes for 4 mm wood screws, countersunk
        for (m = [[ox1 + 10.5, 50], [50, oy0 - 10.5], [ox0 - 10.5, 40], [50, oy1 + 6]])
            translate([m[0], m[1], 0]) {
                translate([0, 0, -1]) cylinder(d = 4.5, h = 5);
                translate([0, 0, floor_t - 1.8]) cylinder(d1 = 4.5, d2 = 8.4, h = 1.81);
            }
        // floor vents under the buck, the motor driver and the SHT40 island
        for (x = [buck[0] - 12 : 5 : buck[0] + 8]) rbox([x, buck[1] - 7, -1], [x + 2.5, buck[1] + 7, 5]);
        for (x = [22 : 5 : 37]) rbox([x, 21, -1], [x + 2.5, 33, 5]);
        for (x = [78.5 : 3.5 : 89]) rbox([x, 2, -1], [x + 2, 14, 5]);
    }
}

// ---------------- lid ----------------
module label(t, x, y, s = 3.6, ha = "center") {
    translate([x, y, z_lid + lid_t - 0.6])
        linear_extrude(1) text(t, size = s, halign = ha, valign = "center", font = "DejaVu Sans:style=Bold");
}

module lid() {
    difference() {
        union() {
            rbox([ox0, oy0, z_lid], [ox1, oy1, z_lid + lid_t]);
            for (h = holes) translate([h[0], h[1], z_pcb_top]) cylinder(d = post_d, h = inner_h + 0.01);
            partitions(z_pcb_top, z_lid + 0.01);            // sensor chamber, lid -> PCB top
            rbox([bot_x0, J5[3], z_lid - 3], [bridge_x1, lid_left_y0, z_lid + 0.01]);   // v1.2 corner bridge rib
        }
        // clamp cut-outs, open to the edges (push-buttons + wires reachable)
        rbox([84.0, right_y0, z_lid - 1], [ox1 + 1, right_y1, 99]);
        rbox([bot_x0, oy0 - 1, z_lid - 1], [bot_x1, J5[3], 99]);          // full length, up to the clamp rear faces
        rbox([bridge_x1, oy0 - 1, z_lid - 1], [bot_x1, 16.0, 99]);        // + 3.8 mm behind them, right of the bridge
        rbox([ox0 - 1, lid_left_y0, z_lid - 1], [16.0, left_y1, 99]);
        // screw holes
        for (h = holes) translate([h[0], h[1], z_pcb_top - 1]) cylinder(d = screw_d, h = 99);
        // status LED window
        translate([led1[0], led1[1], z_lid - 1]) cylinder(d = 3.2, h = 9);
        // vents above the buck, the motor driver and the sensor chamber
        for (x = [buck[0] - 8 : 4.5 : buck[0] + 3]) rbox([x, buck[1] - 6, z_lid - 1], [x + 2.5, buck[1] + 6, 99]);   // above L1 / U4
        for (x = [30 : 5 : 45]) rbox([x, 22, z_lid - 1], [x + 2.5, 32.5, 99]);   // right of the LEAK label
        // v1.2: 1 mm notch in the lid edge above the USB-C opening (plug overmold)
        rbox([ox0 - 1, usb_yc - usb_w / 2 - 2, z_lid - 1], [ox0 + 1.5, usb_yc + usb_w / 2 + 2, z_lid + 1.0]);
        // v1.2: sound holes above the buzzer
        for (dx = [-2.5, 0, 2.5], dy = [-2.5, 0, 2.5]) translate([bz_pos[0] + dx, bz_pos[1] + dy, z_lid - 1]) cylinder(d = 1.6, h = 9);
        for (x = [cx0 + 3 : 3.5 : 90]) rbox([x, 2, z_lid - 1], [x + 2, 13.5, 99]);
        // engraved labels
        if (labels) {
        label("12V", 82.5, (J2[1] + J2[3]) / 2, ha = "right");
        label("BTN", 82.5, (wago[4][1] + wago[4][3]) / 2, ha = "right");
        label("REEDS", 82.5, (J9[1] + J9[3]) / 2, ha = "right");
        label("ACT", (bot_x0 + bridge_x1) / 2, (J5[3] + lid_left_y0) / 2, s = 2.2);   // on the corner bridge
        label("FAN", j6_pos[0] + 3.8, 19.0);
        label("LED", (wago[2][0] + wago[2][2]) / 2, 19.0);
        label("I2C", (J10[0] + J10[2]) / 2, 19.0);
        label("BEAM", 17.5, (J12[1] + J12[3]) / 2, ha = "left");
        label("LEAK", 17.5, (J13[1] + J13[3]) / 2, s = 2.6, ha = "left");
        label("VALVE", 82.5, (J14[1] + J14[3]) / 2, s = 2.6, ha = "right");
        label("T/H", (cx0 + 92) / 2, cy1, s = 2.6);
        label("ROBO-GARAGE", 33, 60.5, s = 3.6);
        label("USB-C on the left side", 36.5, 55.0, s = 2.2);
        label("< USB-C", 3.0, usb_yc, s = 2.6, ha = "left");
        }
    }
}

// ---------------- PCB stand-in for fit checks ----------------
module pcb_model() {
    // board with the C-slot around the SHT40 island (neck on the left)
    color("green") difference() {
        rbox([0, 0, z_pcb_bot], [pcb, pcb, z_pcb_top]);
        difference() {
            rbox([slot_outer[0], slot_outer[1], z_pcb_bot - 1], [slot_outer[2], slot_outer[3], z_pcb_top + 1]);
            rbox([slot_outer[0] + 1.5, slot_outer[1] + 1.5, z_pcb_bot - 2], [slot_outer[2] - 1.5, slot_outer[3] - 1.5, z_pcb_top + 2]);
            rbox([slot_outer[0] - 1, u5_pos[1] - 1.75, z_pcb_bot - 2], [slot_outer[0] + 1.6, u5_pos[1] + 1.75, z_pcb_top + 2]);
        }
    }
    // clamp bodies (height from pcb_data.scad)
    for (w = wago) color("silver") rbox([w[0], w[1], z_pcb_top], [w[2], w[3], z_pcb_top + w[4]]);
    // DevKitC on 8.5 mm female sockets: header spacer 2.54, board 1.6, parts 3.2 (module / USB-C) -> top at +15.88
    // USB-C at the left board edge (devkit[0]), antenna end inboard (devkit[1])
    color("black") rbox([devkit[0] + 1.41, 68.35, z_pcb_top + 11.04], [devkit[1], 96.25, z_pcb_top + 15.88]);   // board edge 0.43
    color("silver") rbox([devkit[0], usb_yc - 4.5, usb_zc - 1.6], [devkit[0] + 7.5, usb_yc + 4.5, usb_zc + 1.6]);   // receptacle
    if (show_plug) color("red") rbox([devkit[0] - 20.5, usb_yc - 6, usb_zc - 3.25], [ox0 + 1.0, usb_yc + 6, usb_zc + 3.25]);   // plug overmold
    color("dimgray") {
        rbox([0.4, 93.7, z_pcb_top], [48.7, 96.3, z_pcb_top + 8.5]);
        rbox([0.4, 68.3, z_pcb_top], [48.7, 73.5, z_pcb_top + 8.5]);
    }
    // fan header with plug, electrolytics, inductor, SHT40
    color("white") rbox([20.0, 1.8, z_pcb_top], [32.6, 8.2, z_pcb_top + 16]);
    color("navy") {
        translate([c13_pos[0], c13_pos[1], z_pcb_top]) cylinder(d = 8.6, h = 10.6);
        translate([c1_pos[0], c1_pos[1], z_pcb_top]) cylinder(d = 6.9, h = 8.0);
        translate([c3_pos[0], c3_pos[1], z_pcb_top]) cylinder(d = 6.9, h = 8.0);
    }
    color("gray") translate([l1_pos[0] - 3.5, l1_pos[1] - 3.3, z_pcb_top]) cube([7, 6.6, 3.1]);
    color("gold") translate([u5_pos[0] - 0.75, u5_pos[1] - 0.75, z_pcb_top]) cube([1.5, 1.5, 0.6]);
    color("black") translate([bz_pos[0] - 4.25, bz_pos[1] - 4.25, z_pcb_top]) cube([8.5, 8.5, 3.3]);   // v1.2 buzzer
    // solder pins under the board (2.2 mm): WAGO rows, DevKit header rows, fan header
    color("orange") {
        rbox([91.6, J9[1], z_pcb_bot - 2.2], [94.0, J2[3], z_pcb_bot]);   // right clamp pins (x = 92.8)
        rbox([J5[0], 6.0, z_pcb_bot - 2.2], [J10[2], 8.4, z_pcb_bot]);      // bottom clamp pins (y = 7.2)
        rbox([6.0, J13[1], z_pcb_bot - 2.2], [8.4, J12[3], z_pcb_bot]);     // left clamp pins (x = 7.2)
        rbox([21.5, 4.0, z_pcb_bot - 2.2], [31.2, 6.0, z_pcb_bot]);   // fan header pins
        rbox([0.7, 94.0, z_pcb_bot - 2.2], [48.5, 96.0, z_pcb_bot]);  // DevKit J3 row
        rbox([0.7, 68.6, z_pcb_bot - 2.2], [48.5, 73.2, z_pcb_bot]);  // DevKit J4 / J15 rows
    }
}

if (part == "base") base();
else if (part == "lid") lid();
else if (part == "lid_print") translate([0, 0, z_lid + lid_t]) mirror([0, 0, 1]) lid();
else if (part == "check_base") intersection() { base(); pcb_model(); }
else if (part == "check_lid") intersection() { lid(); pcb_model(); }
else if (part == "pcb_model") pcb_model();
else { color("lightgray") base(); pcb_model(); color("lightblue", 0.55) lid(); }
