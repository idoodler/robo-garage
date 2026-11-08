// Robo-Garage up & over door - print-in-place modules (OpenSCAD, FOSS)
// David Gölzhäuser (idoodler) - https://github.com/idoodler/robo-garage
//
// Like a small garage door: a peg on the door's back (Q) runs in a short track on each cheek while one arm per
// side (F -> D) tilts the door up. Open, the door lies horizontal inside the cabinet, above the robot, only
// 13 mm in front of the drawer front; while moving it never comes out more than 35 mm. The door is 202 mm tall
// (6 mm gap under the drawer front, 2 mm more than the other doors) and needs no chamfer.
// Each side prints as ONE piece: skeleton wall plate + arm + door bracket (with the peg). The track is a separate
// print. The left arm carries the actuator lever. The door itself keeps both sides in step.
//
// Frame (mm): X = depth behind the door's back face (= cheek front edge), Y = height above the floor
// (drawer tray top = 15), Z = print height: 0 = print bed = side facing the robot bay, z_top = cheek face.
//
// part = "left" | "right" | "track" | "mount" | "template"              the prints (build.sh -> STL)
//        "assembly" | "scene" | "layout"                                previews; `pose` 0 = closed .. 1 = open
//        "plate_l" | "plate_r" | "arm_l" | "arm_r" | "bracket"          single bodies (closed pose)

version = "1.2";

/* [Output] */
part = "assembly";      // [left, right, track, mount, template, assembly, scene, layout]
pose = 0;               // [0:0.05:1]
print_pose = 0.55;      // printed half open: fits a 220 x 220 bed

/* [Print-in-place gaps - print coupon.stl first (parallel-lift.scad, part = "coupon")] */
cj = 0.45;  gz = 0.6;  cs = 1.0;

/* [Hardware] */
eye_bolt = 6;           // actuator eye bolts M6
act_gap = 7;            // printed spacer between the lever and the rod eye
wall_screw = 4;         // wall plate: 4 x 20 countersunk wood screws
door_screw = 3.5;       // bracket: 3.5 x 16 countersunk, driven at 45 deg from the bay
track_screw = 3;        // track: 3 x 16 countersunk

/* [Hidden] */
$fn = 48;  FNJ = 96;  N = 34;
function dirv(a) = [cos(a), sin(a)];
function cross2(a, b) = a[0] * b[1] - a[1] * b[0];
function angle_between(a, b) = atan2(cross2(a, b), a * b);

// ---- kinematics: door turns clockwise by psi about the peg Q, which slides back by s(psi); arm F-D fixes s ----
Q = [18, 134.05];       // peg on the door bracket, in the closed pose
D = [11.5, 66.5];       // arm joint on the door bracket
F = [76.7, 98.2];       // arm pivot in the wall plate
DOOR_TOP = 219;         // door 17 .. 219 (202 mm)
PSI = 90;               // door: vertical -> horizontal
L = norm(D - F);
function Rcw(p) = [[cos(p), sin(p)], [-sin(p), cos(p)]];
function u_of(p) = Rcw(p) * (D - Q);
function s_of(p) = let(u = u_of(p), h = Q[1] + u[1] - F[1]) F[0] - Q[0] - u[0] - sqrt(L * L - h * h);
function psi(f) = PSI * f;
function Qw(f) = [Q[0] + s_of(psi(f)), Q[1]];
function Dw(f) = Qw(f) + u_of(psi(f));
function arm_rot(f) = angle_between(D - F, Dw(f) - F);               // arm turn (negative = clockwise)
function rel_rot(f) = arm_rot(f) + psi(f);                           // arm turn seen from the door bracket
function door_pt(p, f) = Qw(f) + Rcw(psi(f)) * (p - Q);
module door_tf(f) translate(Qw(f)) rotate(-psi(f)) translate(-Q) children();
TRAVEL = s_of(PSI);
// lever on the arm, actuator from above on the left cheek (pushes to open: 225 -> 375 mm pin to pin)
LEV = 150;  LEV_OFF = -131.2;
LEV_A = atan2(D[1] - F[1], D[0] - F[0]) + LEV_OFF;
function Cf(f) = F + LEV * dirv(LEV_A + arm_rot(f));
C0 = Cf(0);  C1 = Cf(1);
ACT0 = 225;  ACT1 = 375;
FA = let(d = norm(C1 - C0), a = (ACT0 * ACT0 - ACT1 * ACT1 + d * d) / (2 * d), h = sqrt(ACT0 * ACT0 - a * a), u = (C1 - C0) / d)
     C0 + a * u + h * [-u[1], u[0]];

// ---- layer stack + joints (hourglass pin, as the parallel lift) ----
z_top = 22;  h1 = 6;  z2 = h1 + gz;  z_mov = z_top - 5;
ridge = 1;  land = 0.8;  ef = 0.4;  fz = 0.2;
rFl = 10;  rFr = 7;  rA = 5.5;  wall = 3.5;  wallF_l = 9;  wallF_r = 7;  // left arm carries the lever; the right arm is a link, its ring takes the full pull
// wall: ring at D. The lug below makes a thicker one unnecessary (FE: same stress at 3.5 and 4.5) and 4.5 left the arm 1.1 mm from the door
lug_l = 14;  pin_hole = 4;              // tapered lug from the arm's ring into the arm; hole through the solid pin (see parallel-lift.scad)
w_lev = 14;                             // lever half width at the pivot: the lever root over the F ring is only z 6.6..17 tall
z_lev = 12;  lev_full_r = 30;           // lever web top: full height only near the pivot and at the eye boss
function rF(lev) = lev ? rFl : rFr;
function rRF(lev) = rF(lev) + cj + (lev ? wallF_l : wallF_r);
rRA = rA + cj + wall;
function w0(lev) = lev ? 14 : 6;        // arm half width at F. Left: as wide as the lever root (FE: the arm's step into the ring layer 1.05 -> 0.87 of the allowable from 12 to 14);
                                        // its sweep trims the bearing wall above the ring, which the lever's sweep has cut there anyway
function wA(lev) = lev ? 6 : 5;         // arm half width at D
rboss = 12;  tf = 5;
yf = [40, 146];                         // bracket flange on the door's back
YSC = [48, 95, 125];  dsb = 45;  dze = 5;
peg_d = 10;  trk = [17.5, z_top];  trk_y = [Q[1] - 10, Q[1] + 18];   // track: Z band and Y extent
ENV_L = [[38, 15.5], [178, 15.5], [178, 95], [140, 95], [100, 108], [38, 108]];   // nothing above the pivot: lever + arm
ENV_R = [[38, 15.5], [178, 15.5], [178, 120], [38, 120]];                         // below the track
S0 = [62, 40];  S1 = [115, 28];  S2 = [115, 70];  S4 = [167, 75];
SCREWS = [S0, S1, S2, S4];             // v2.1 had a 5th screw at [167, 28]: FE gives it under 5 N, so it and its ties are gone
// ribs [from, to, width]: routes and widths from FE (check_strength.py, 3D as printed: v2.2 at a 100 N stall, plates at 0.70 / 0.32 of the allowable)
function ribs_of(lev) = let(w = lev ? 7 : 5) [[F, S0, w], [F, S2, w], [S1, S2, 3], [S2, S4, 3]];   // ties without load left out (FE)
WHEEL = [[52, 0], [88, 33]];
rbs = 6.8;                              // screw boss radius (counterbore r 4.3 + 2.5 mm wall)
function Qof(lev) = D - (rA + cs + wA(lev)) * (D - F) / norm(D - F);   // upper-layer arm end, clear of the bracket hub

// ---------------------------------------------------------------- 2D helpers
module disk(c, r, fn = 0) translate(c) circle(r = r, $fn = fn > 0 ? fn : $fn);
module capsule(a, b, ra, rb = -1) hull() { disk(a, ra); disk(b, rb < 0 ? ra : rb); }
module rot_about(c, a) translate(c) rotate(a) translate(-c) children();
module sweep_rot(c) for (i = [0 : N - 1]) hull() { rot_about(c, arm_rot(i / N)) children(); rot_about(c, arm_rot((i + 1) / N)) children(); }
module sweep_rel(c) for (i = [0 : N - 1]) hull() { rot_about(c, rel_rot(i / N)) children(); rot_about(c, rel_rot((i + 1) / N)) children(); }
lh = 0.2;
module grow(n) {  // self-supporting underside: children(0) = seed, children(1) = target; grows 45 deg until the full outline is reached
  for (i = [0 : n - 1]) translate([0, 0, z2 + i * lh]) linear_extrude(lh + 0.001) intersection() { children(1); offset(r = i * lh) children(0); }
  translate([0, 0, z2 + n * lh]) linear_extrude(z_mov - z2 - n * lh) children(1);
}
module sweep_door() for (i = [0 : N - 1]) hull() { door_tf(i / N) children(); door_tf((i + 1) / N) children(); }

// ---------------------------------------------------------------- joints
module pin_prof(r, h) polygon([[0, 0], [r - ef, 0], [r, ef], [r - ridge, ef + ridge], [r - ridge, ef + ridge + land], [r, ef + 2 * ridge + land],
                               [r, z2], [r - 0.5, z2], [r - 0.5, z2 + 0.5], [0, z2 + 0.5]]);
module hole_prof(r, h, top, g = cj) polygon([[0, -1], [r + g + ef + 1, -1], [r + g + ef, 0], [r + g, ef + fz],
                               [r - ridge + g, ef + ridge + fz], [r - ridge + g, ef + ridge + land - fz], [r + g, ef + 2 * ridge + land - fz],
                               [r + g, top], [0, top]]);
module pin3d(c, r) translate(c) rotate_extrude($fn = FNJ) pin_prof(r, h1);
module hole3d(c, r, top = h1 + 1) translate(c) rotate_extrude($fn = FNJ) hole_prof(r, h1, top);

// ---------------------------------------------------------------- arm (+ lever on the left), closed pose
module arm_shape(lev, E) capsule(F, E, w0(lev), wA(lev));
module lug(lev) hull() { disk(D, rRA); disk(D + lug_l * (F - D) / L, wA(lev)); }
module arm_b1(lev) { difference() { arm_shape(lev, D); disk(F, rRF(lev) + cs); } disk(D, rRA); lug(lev); }
module arm_b2(lev) { disk(F, rF(lev), FNJ); arm_shape(lev, Qof(lev)); }
module lever_hull() hull() { disk(F, w_lev); disk(C0, rboss); }
module lever_b1() difference() { lever_hull(); disk(F, rRF(true) + cs); }
function nut_af(d) = d >= 6 ? 10 : d >= 5 ? 8 : 7;
module eye_hole(c, h) {
  translate([c[0], c[1], -1]) cylinder(d = eye_bolt + 0.4, h = h + 2, $fn = 32);
  translate([c[0], c[1], h - 9]) cylinder(d = (nut_af(eye_bolt) + 0.4) / cos(30), h = 10, $fn = 6);
}
module arm3d(lev = false) difference() {
  union() {
    linear_extrude(h1) { arm_b1(lev); if (lev) lever_b1(); }
    translate([0, 0, h1]) linear_extrude(gz) { intersection() { arm_b1(lev); arm_b2(lev); } if (lev) lever_b1(); }
    translate([0, 0, z2]) linear_extrude(z_mov - z2) { arm_b2(lev); if (lev) intersection() { lever_hull(); union() { disk(F, lev_full_r); disk(C0, rboss); } } }
    if (lev) translate([0, 0, z2]) linear_extrude(z_lev - z2) lever_hull();
    pin3d(F, rF(lev));
  }
  hole3d(D, rA);
  if (lev) eye_hole(C0, z_mov);
}

// ---------------------------------------------------------------- door bracket (closed pose) with the track peg
module brk_desired() hull() { translate([0, yf[0]]) square([tf, yf[1] - yf[0]]); disk(D, rA + 5); disk(Q, 8); }
// same bracket left and right: it clears the wider (left) arm
module arm_bf_b1() { sweep_rel(D) arm_shape(true, D); disk(D, rRA); sweep_rel(D) difference() { lug(true); disk(D, rRA + 0.3); } }   // ring not swept: see parallel-lift.scad
module arm_bf_b2() sweep_rel(D) arm_shape(true, Qof(true));
module brk_b1() difference() { brk_desired(); offset(delta = cs) arm_bf_b1(); }
module brk_b2() { difference() { brk_desired(); offset(delta = cs) arm_bf_b2(); } disk(D, rA, FNJ); }
module bracket3d() difference() {
  union() {
    linear_extrude(h1) brk_b1();
    translate([0, 0, h1]) linear_extrude(gz) intersection() { brk_b1(); brk_b2(); }
    grow(25) { union() { intersection() { brk_b1(); brk_b2(); } disk(D, rA, FNJ); disk(Q, 8); } brk_b2(); }   // no bridges over the ring
    pin3d(D, rA);
    translate([Q[0], Q[1], z_mov - 0.01]) cylinder(d = peg_d, h = trk[0] + 3.5 - z_mov, $fn = 32);       // peg into the track
    translate([Q[0], Q[1], z_mov - 0.01]) cylinder(d1 = peg_d + 3, d2 = peg_d, h = 0.51, $fn = 32);
  }
  for (y = YSC) door_screw_hole(y);
  translate([D[0], D[1], -1]) cylinder(d = pin_hole, h = z_mov + 2, $fn = 24);
}
module door_screw_hole(y) translate([0, y, dze]) rotate([0, 90 + dsb, 0]) {
  d = door_screw + 0.4;  dh = 2 * door_screw + 0.6;  sh = dze / sin(dsb) - 1;
  translate([0, 0, -6]) cylinder(d = d, h = sh + 6, $fn = 24);
  translate([0, 0, sh - (dh - d) / 2]) cylinder(d1 = d, d2 = dh, h = (dh - d) / 2 + 0.01, $fn = 32);
  translate([0, 0, sh]) cylinder(d = dh + 0.4, h = 25, $fn = 32);
}

// ---------------------------------------------------------------- what the wall plate must avoid
DOOR2D = [[-19, 17], [0, 17], [0, DOOR_TOP], [-19, DOOR_TOP]];
act_r_tube = 10;  act_r_body = 18;  act_tube_from = 12;  act_body_len = 190;
function Uf(f) = (Cf(f) - FA) / norm(Cf(f) - FA);
module act_tube(f) capsule(Cf(f) - act_tube_from * Uf(f), FA + act_body_len * Uf(f), act_r_tube);
module act_body(f) hull() { disk(FA + 15 * Uf(f), act_r_body); disk(FA + act_body_len * Uf(f), act_r_body); }
module act_sw() for (i = [0 : N - 1]) { hull() { act_tube(i / N); act_tube((i + 1) / N); } hull() { act_body(i / N); act_body((i + 1) / N); } }
function x_cheek(y) = y < 47 ? 250 : max(100, 250 - (y - 47) * 0.75);
module plate_desired(lev) difference() {
  intersection() { polygon(lev ? ENV_L : ENV_R); polygon([for (y = [0 : 10 : 520]) [x_cheek(y) - 3, y], [0, 520], [0, 0]]); }
  translate(WHEEL[0]) square(WHEEL[1] - WHEEL[0]);
}
module arm_sw_b1(lev) { difference() { sweep_rot(F) arm_shape(lev, D); disk(F, rRF(lev) + cs); } sweep_rot(F) disk(D, rRA); sweep_rot(F) lug(lev); }
module arm_sw_b2(lev) sweep_rot(F) arm_shape(lev, Qof(lev));
module lever_sw_b1() difference() { sweep_rot(F) lever_hull(); disk(F, rRF(true) + cs); }
module lever_sw_b2() sweep_rot(F) lever_hull();
module moving_sw(lev) { sweep_door() brk_desired(); sweep_door() polygon(DOOR2D); if (lev) act_sw(); }
module plate_b1_full(lev) {
  difference() { plate_desired(lev); offset(delta = cs) { arm_sw_b1(lev); if (lev) lever_sw_b1(); moving_sw(lev); } }
  disk(F, rRF(lev), FNJ);
}
module plate_b2_full(lev) intersection() {
  difference() { plate_desired(lev); offset(delta = cs) { arm_sw_b2(lev); if (lev) lever_sw_b2(); moving_sw(lev); } }
  offset(r = 0.8) plate_b1_full(lev);
}
// ---- skeleton plate: ring + screw bosses + ribs, all full height, so the ribs print as solid in-layer walls
module skel2d(lev) {
  for (r = ribs_of(lev)) capsule(r[0], r[1], r[2] / 2);
  for (s = SCREWS) disk(s, rbs);
  disk(F, rRF(lev), FNJ);
}
rf = 3;   // fillet in the concave corners where ribs meet rings and bosses, clipped back to the free space
module fil() intersection() { children(0); offset(r = -rf) offset(r = rf) intersection() { children(0); children(1); } }
module plate_b1(lev) fil() { plate_b1_full(lev); skel2d(lev); }
module plate_b2(lev) offset(r = 0.6) offset(r = -0.6) fil() { plate_b2_full(lev); skel2d(lev); }   // sliver tips rounded off
module wall_screw_hole(s, h) translate([s[0], s[1], 0]) {
  d = wall_screw + 0.5;  dc = 2 * wall_screw + 0.6;  zs = h - 5 - (dc - d) / 2;
  translate([0, 0, -1]) cylinder(d = d, h = h + 2, $fn = 24);
  translate([0, 0, -1]) cylinder(d = dc, h = zs + 1, $fn = 32);
  translate([0, 0, zs - 0.01]) cylinder(d1 = dc, d2 = d, h = (dc - d) / 2 + 0.01, $fn = 32);
}
module plate3d(lev) difference() {
  union() { linear_extrude(h1) plate_b1(lev); translate([0, 0, h1]) linear_extrude(z_top - h1) plate_b2(lev); }
  hole3d(F, rF(lev), z_top + 1);
  for (s = SCREWS) wall_screw_hole(s, z_top);
  translate([F[0], F[1] - rF(lev) - cj - 2, z_top - 0.6]) linear_extrude(1) text(lev ? "L" : "R", size = 3, halign = "center", valign = "center");
}

// ---------------------------------------------------------------- module (print-in-place)
module uo_module(lev, f = 0) {
  color("Gainsboro") plate3d(lev);
  color("DarkOrange") rot_about(F, arm_rot(f)) arm3d(lev);
  color("SteelBlue") door_tf(f) bracket3d();
}

// ---------------------------------------------------------------- track (separate print, cheek face down)
// Module frame: Z trk[0]..z_top, slot for the peg along the travel. Printed with the cheek face (Z 22) on the bed.
slot_over = 3;                          // the slot runs on past the open position: the peg never ends up against the slot's end
TRK_X = [3, Q[0] + TRAVEL + slot_over + peg_d / 2 + 4.5];
TRK_SCREWS = [for (x = [TRK_X[0] + 9 : 30 : TRK_X[1] - 6]) [x, Q[1] + 12]];
module track_world() difference() {
  translate([TRK_X[0], trk_y[0], trk[0]]) cube([TRK_X[1] - TRK_X[0], trk_y[1] - trk_y[0], trk[1] - trk[0]]);
  hull() for (x = [Q[0], Q[0] + TRAVEL + slot_over]) translate([x, Q[1], trk[0] - 1]) cylinder(d = peg_d + 0.8, h = 4 + 1, $fn = 32);
  for (s = TRK_SCREWS) translate([s[0], s[1], trk[0] - 0.01]) {
    cylinder(d = track_screw + 0.4, h = 10, $fn = 24);
    cylinder(d1 = 2 * track_screw + 0.6, d2 = track_screw + 0.4, h = (track_screw + 0.2) / 2, $fn = 32);
  }
}
module track() translate([0, 0, z_top]) mirror([0, 0, 1]) track_world();

// ---------------------------------------------------------------- actuator top mount + spacer (as the parallel lift)
mt = 14;  mslot = 8;
MS = [FA + [30, 6], FA + [30, 34], FA + [4, 34]];         // block reaches back: the pivot is 12 mm behind the cheek's front edge
module mount_block() difference() {
  union() {
    linear_extrude(mt) hull() { disk(FA, 9.5); disk(FA + [30, -3.5], 10); disk(FA + [30, 44], 10); disk(FA + [0, 44], 9.5); }
    translate([FA[0], FA[1], mt - 0.01]) cylinder(d = 18, h = z_top + act_gap - mt + 0.01, $fn = 48);
  }
  translate([FA[0], FA[1], -1]) cylinder(d = eye_bolt + 0.4, h = z_top + act_gap + 2, $fn = 32);
  translate([FA[0], FA[1], -1]) cylinder(d = (nut_af(eye_bolt) + 0.4) / cos(30), h = 7, $fn = 6);
  for (s = MS) {
    d = wall_screw + 0.5;  dc = 2 * wall_screw + 0.6;
    hull() for (dy = [-mslot, mslot]) translate([s[0], s[1] + dy, -1]) cylinder(d = d, h = mt + 2, $fn = 24);
    hull() for (dy = [-mslot, mslot]) translate([s[0], s[1] + dy, mt - (dc - d) / 2]) cylinder(d1 = d, d2 = dc, h = (dc - d) / 2 + 0.01, $fn = 32);
  }
  translate([FA[0] + 17, FA[1] + 20, mt - 0.6]) linear_extrude(1) text("UP", size = 6, halign = "center", valign = "center");
}
module spacer() difference() { cylinder(d = 16, h = act_gap, $fn = 48); translate([0, 0, -1]) cylinder(d = eye_bolt + 0.4, h = act_gap + 2, $fn = 32); }
module mount() { mount_block(); translate([FA[0] + 20, FA[1] - 22, 0]) spacer(); }
module mount_placed() translate([0, 0, z_top]) mirror([0, 0, 1]) mount_block();

// ---------------------------------------------------------------- drill template: plate + track screws
module template() difference() {
  linear_extrude(1.2) union() {
    translate([0, 15]) square([6, trk_y[1] + 4 - 15]);
    translate([0, 15]) square([205, 7.5]);
    for (s = concat(SCREWS, TRK_SCREWS, [F])) { translate(s - [7, 7]) square(14); translate([0, s[1] - 3]) square([s[0], 6]); translate([s[0] - 3, 15]) square([6, s[1] - 15]); }
  }
  for (s = concat(SCREWS, TRK_SCREWS)) translate([s[0], s[1], -1]) cylinder(d = 3.2, h = 4, $fn = 24);
  translate([F[0], F[1], -1]) cylinder(d = 2, h = 4, $fn = 16);
  translate([35, 18.75, 0.8]) linear_extrude(1) text("< FRONT", size = 4, halign = "center", valign = "center");
  translate([155, 18.75, 0.8]) linear_extrude(1) text("TRAY", size = 4, halign = "center", valign = "center");
}

// ---------------------------------------------------------------- output
if (part == "right") uo_module(false, print_pose);
else if (part == "left") mirror([1, 0, 0]) uo_module(true, print_pose);
else if (part == "track") track();
else if (part == "track_l") mirror([1, 0, 0]) track();
else if (part == "mount") mount();
else if (part == "template") template();
else if (part == "plate_l") plate3d(true);
else if (part == "plate_r") plate3d(false);
else if (part == "arm_l") arm3d(true);
else if (part == "arm_r") arm3d(false);
else if (part == "bracket") bracket3d();
else if (part == "mount_w") mount_placed();
else if (part == "track_w") track_world();
else if (part == "assembly") uo_module(true, pose);
else if (part == "echo") echo(str("GEO Q=", Q, ";D=", D, ";F=", F, ";L=", L, ";PSI=", PSI, ";TRAVEL=", TRAVEL, ";LEV=", LEV, ";LEV_A=", LEV_A,
                                  ";FA=", FA, ";C0=", C0, ";C1=", C1, ";act_gap=", act_gap, ";SCREWS=", SCREWS, ";TRK_SCREWS=", TRK_SCREWS,
                                  ";print_pose=", print_pose, ";DOOR_TOP=", DOOR_TOP, ";rRP=", rRF(true), ";rRA=", rRA, ";cj=", cj, ";cs=", cs, ";gz=", gz,
                                  ";z_top=", z_top, ";z_mov=", z_mov, ";h1=", h1, ";YSC=", YSC, ";dsb=", dsb, ";dze=", dze,
                                  ";wall_screw=", wall_screw, ";act_r_tube=", act_r_tube, ";act_r_body=", act_r_body,
                                  ";act_tube_from=", act_tube_from, ";act_body_len=", act_body_len, ";trk=", trk, ";trk_y=", trk_y,
                                  ";TRK_X=", TRK_X, ";peg_d=", peg_d, ";rA=", rA, ";rFl=", rFl, ";rFr=", rFr, ";eye_bolt=", eye_bolt,
                                  ";version='", version, "'"));
else if (part == "2d_plate_b1_l") plate_b1(true);
else if (part == "2d_plate_b2_l") plate_b2(true);
else if (part == "2d_plate_b1_r") plate_b1(false);
else if (part == "2d_plate_b2_r") plate_b2(false);
else if (part == "2d_brk_b1") brk_b1();
else if (part == "2d_brk_b2") brk_b2();
else if (part == "scene") {
  uo_module(true, pose);
  c = Cf(pose);
  color("Peru", 0.35) door_tf(pose) translate([0, 0, -60]) linear_extrude(60 + z_mov) polygon(DOOR2D);
  color("Silver") track_world();
  CH = [[0, 15], [250, 15], [250, 47], [100, 247], [100, 520], [0, 520]];
  color("SaddleBrown") translate([0, 0, z_top]) linear_extrude(1) difference() { polygon(CH); offset(delta = -2) polygon(CH); }
  color("Tan") translate([-19, 225, z_top]) cube([16, 295, 1]);
  color("Tan") translate([-19, 0, z_top]) cube([19, 15, 1]);
  color("Silver") hull() { translate([c[0], c[1], -act_gap - 8]) cylinder(d = 20, h = 8); translate([FA[0], FA[1], -act_gap - 8]) cylinder(d = 20, h = 8); }
  color("SlateGray") mount_placed();
}
else if (part == "layout") {
  translate([189.6, -11.35, 0]) mirror([1, 0, 0]) uo_module(true, print_pose);      // centred on the beds (bounds at print_pose)
  translate([262.7, 24.5, 0]) uo_module(false, print_pose);
  for (x = [0, 230]) color("LightGray") translate([x, 0, -1]) difference() { cube([220, 220, 0.5]); translate([1, 1, -1]) cube([218, 218, 3]); }
}
