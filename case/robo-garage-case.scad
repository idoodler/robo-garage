// Robo-Garage controller PCB v1.2 - 3D printed base + lid (OpenSCAD, FOSS)
// Coordinates: x right, y up, z up. PCB occupies [0,100] x [0,100]; y = 0 is the edge with the
// ACTUATOR / FAN / LED / I2C clamps, x = 100 the edge with 12V IN / BUTTON / REEDS, x = 0 the BEAM / LEAK / VALVE clamps.
// The front-right corner is a separate vented chamber for the SHT40 (measures cabinet air, not box air).
// part = "base" | "lid" | "lid_print" (lid flipped for printing) | "assembly" | "check_base" | "check_lid"
part = "assembly";
labels = true;     // false: no engraved text (small 3D model for the simulator page)
version = "1.2";   // case version: release zip name (case/build.sh)

include <pcb_data.scad>

$fn = 48;
pcb = 100;  pcb_t = 1.6;
wall = 2.0; floor_t = 2.0;
clr = 0.5;          // PCB edge -> wall
ant = 7.0;          // room left of the PCB for the DevKit antenna overhang
stand_h = 5.0;      // floor -> PCB bottom (THT leads stick out ~2 mm)
inner_h = 16.5;     // PCB top -> lid (DevKit stack 14.4; the 11.7 mm clamps sit under cut-outs: push buttons)
lid_t = 2.0;
shelf = 15.0;       // wire shelf with zip-tie slots on the clamp sides
gap = 0.3;          // walls stop 0.3 below the lid: the lid is clamped by its pillars
part_t = 1.2;       // sensor chamber partitions

z_pcb_bot = floor_t + stand_h;      // 7.0
z_pcb_top = z_pcb_bot + pcb_t;      // 8.6
z_lid = z_pcb_top + inner_h;        // 25.1

ix0 = -ant; ix1 = pcb + clr; iy0 = -clr; iy1 = pcb + clr;   // cavity
ox0 = ix0 - wall; ox1 = ix1 + wall; oy0 = iy0 - wall; oy1 = iy1 + wall;

// clamp windows (open sides) and lid cut-outs, from the clamp bodies in pcb_data.scad
J2 = wago[0]; J5 = wago[1]; J10 = wago[3]; J9 = wago[5]; J12 = wago[6]; J13 = wago[7]; J14 = wago[8];
right_y0 = J9[1] - 1.0;  right_y1 = J2[3] + 0.6;   // REEDS .. 12V IN (stays clear of the corner pillar)
bot_x0 = J5[0] - 1.0;    bot_x1 = J10[2] + 1.0;    // ACTUATOR .. I2C
left_y0 = J14[1] - 1.0;  left_y1 = J12[3] + 1.0;   // VALVE .. LEAK .. BEAM (v1.2)
// v1.2: the VALVE clamp sits 1.75 mm from the front clamp row, so the lid corner (screw post at 3.5/3.5) keeps
// a 3 mm bridge: the front cut-out stops at the J5 rear face for x < bridge_x1, the left cut-out starts 3 mm above it
bridge_w = 3.0; bridge_x1 = 19.0;
lid_left_y0 = max(left_y0, J5[3] + bridge_w);     // 15.2: pole-2 button of VALVE (y 15.25..17.75) stays free
win_z0 = floor_t + 2.0;                            // 2 mm curb, wires drop to the shelf

cx0 = chamber[0]; cy1 = chamber[3];                // sensor chamber: x > cx0 and y < cy1

screw_d = 3.4; pilot_d = 2.8; post_d = 7.0;

// v1.2: USB-C panel socket in the back wall (flange type with 2 M3 holes, e.g. SparkFun CAB-15455 or a generic
// "USB-C panel mount extension"; its 15-30 cm pigtail plugs into the DevKit). Measure your socket, then adjust:
usb_x = 80.5;  usb_z = 17.0;      // centre on the back wall (right of the DevKit, left of the 12V IN clamp)
usb_cut = [11.0, 7.0];            // cut-out for the socket nose (w x h), corners r 1
usb_pitch = 18.0;                 // flange hole spacing; holes are M3 pilots (2.6) into 4 mm bosses behind the wall
usb_body = [13.0, 18.0, 8.0];     // socket body behind the panel (w x depth x h): only for the fit check

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
                // vents in the left (antenna) wall
                for (y = [64 : 8 : 88]) rbox([ox0 - 1, y, 12], [ix0 + 1, y + 4, 20]);
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
            // v1.2: bosses for the USB-C socket screws (inside the back wall)
            for (dx = [-usb_pitch / 2, usb_pitch / 2]) translate([usb_x + dx, iy1 - 4, usb_z]) rotate([-90, 0, 0]) cylinder(d = 5, h = 4.01);
            // sensor chamber: partitions floor -> PCB bottom, and closing the PCB-edge gap up to the PCB top
            partitions(0, z_pcb_bot);
            rbox([cx0 - part_t / 2, iy0, z_pcb_bot - 0.01], [cx0 + part_t / 2, 0, z_pcb_top]);
            rbox([pcb, cy1 - part_t / 2, z_pcb_bot - 0.01], [ix1, cy1 + part_t / 2, z_pcb_top]);
        }
        // pilot holes for M3 x 25 (self-tapping into the post, 1 mm floor left)
        for (h = holes) translate([h[0], h[1], 1.0]) cylinder(d = pilot_d, h = 20);
        // v1.2: USB-C socket: nose cut-out through the back wall + 2 pilot holes through wall and bosses
        hull() for (dx = [-1, 1], dz = [-1, 1])
            translate([usb_x + dx * (usb_cut[0] / 2 - 1), iy1 - 1, usb_z + dz * (usb_cut[1] / 2 - 1)]) rotate([-90, 0, 0]) cylinder(r = 1, h = wall + 2);
        for (dx = [-usb_pitch / 2, usb_pitch / 2]) translate([usb_x + dx, iy1 - 4.5, usb_z]) rotate([-90, 0, 0]) cylinder(d = 2.6, h = wall + 6);
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
        for (x = [56 : 5 : 76]) rbox([x, 62, -1], [x + 2.5, 76, 5]);
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
        for (x = [52 : 5 : 67]) rbox([x, 63, z_lid - 1], [x + 2.5, 78, 99]);      // ends left of the BTN label
        for (x = [30 : 5 : 45]) rbox([x, 22, z_lid - 1], [x + 2.5, 32.5, 99]);   // right of the LEAK / VALVE labels
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
        label("VALVE", 17.5, 22.8, s = 2.6, ha = "left");   // above the FAN label, left of the vents
        label("T/H", (cx0 + 92) / 2, cy1, s = 2.6);
        label("ROBO-GARAGE", 50, 52, s = 5);
        label("USB-C on the back wall", 58, 45, s = 2.2);   // starts right of the BEAM label
        label("USB-C", usb_x, 97.3, s = 2.6);
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
    // DevKitC on 8.5 mm female headers (board 1.6 + parts 4.3), antenna end at x = -4.5
    color("black") rbox([-4.5, 68.35, z_pcb_top + 8.5], [51.4, 96.25, z_pcb_top + 14.4]);
    color("dimgray") {
        rbox([1.7, 93.7, z_pcb_top], [50.0, 96.3, z_pcb_top + 8.5]);
        rbox([1.7, 68.3, z_pcb_top], [50.0, 73.5, z_pcb_top + 8.5]);
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
    // v1.2: USB-C plug in the DevKit port (straight plug + overmold, 22 mm) and the panel socket body behind the back wall
    color("red") rbox([51.4, 77.8, z_pcb_top + 8.5], [73.0, 86.8, z_pcb_top + 15.0]);
    color("red") rbox([usb_x - usb_body[0] / 2, iy1 - usb_body[1], usb_z - usb_body[2] / 2], [usb_x + usb_body[0] / 2, iy1, usb_z + usb_body[2] / 2]);
    // solder pins under the board (2.2 mm): WAGO rows, DevKit header rows, fan header
    color("orange") {
        rbox([91.6, J9[1], z_pcb_bot - 2.2], [94.0, J2[3], z_pcb_bot]);   // right clamp pins (x = 92.8)
        rbox([J5[0], 6.0, z_pcb_bot - 2.2], [J10[2], 8.4, z_pcb_bot]);      // bottom clamp pins (y = 7.2)
        rbox([6.0, J14[1], z_pcb_bot - 2.2], [8.4, J12[3], z_pcb_bot]);     // left clamp pins (x = 7.2)
        rbox([21.5, 4.0, z_pcb_bot - 2.2], [31.2, 6.0, z_pcb_bot]);   // fan header pins
        rbox([2.0, 94.0, z_pcb_bot - 2.2], [49.8, 96.0, z_pcb_bot]);  // DevKit J3 row
        rbox([2.0, 68.6, z_pcb_bot - 2.2], [49.8, 73.2, z_pcb_bot]);  // DevKit J4 rows
    }
}

if (part == "base") base();
else if (part == "lid") lid();
else if (part == "lid_print") translate([0, 0, z_lid + lid_t]) mirror([0, 0, 1]) lid();
else if (part == "check_base") intersection() { base(); pcb_model(); }
else if (part == "check_lid") intersection() { lid(); pcb_model(); }
else if (part == "pcb_model") pcb_model();
else { color("lightgray") base(); pcb_model(); color("lightblue", 0.55) lid(); }
