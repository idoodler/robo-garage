// Robo-Garage parallel lift door v2 - print-in-place modules (OpenSCAD, FOSS)
// David Gölzhäuser (idoodler) - https://github.com/idoodler/robo-garage
//
// One module per cheek = skeleton wall plate (fixed) + front arm (P1-A1) + rear arm (P2-A2) + door bracket.
// The left front arm carries the actuator lever, a straight continuation of the arm behind its pivot.
// A square rod through both front arms couples the sides. Each module prints as ONE piece,
// joints already assembled, no supports.
//
// v2 keeps the door close to the cabinet: it moves 23 mm out and 116 mm up, never more than 40 mm out,
// and parks 3.5 mm in front of the drawer front. The door needs a 45 deg chamfer on its top BACK edge
// (1 mm flat left at the front), so it can slide past the drawer front's bottom edge.
//
// Frame (mm): X = depth behind the door's back face (= cheek front edge), Y = height above the
// floor (drawer tray top = 15), Z = print height: 0 = print bed = side facing the robot bay,
// z_top = face screwed to the cheek.
//
// part = "left" | "right" | "mount" | "coupon" | "template"   the prints (build.sh -> STL)
//        "assembly" | "scene" | "layout"                       previews; `pose` 0 = closed .. 1 = open
//        "plate_l" | "plate_r" | "arm1_l" | "arm1_r" | "arm2" | "bracket"   single bodies (closed pose)
// Other joint gap: openscad -D cj=0.35 -D 'part="left"' -o parallel_left.stl parallel-lift.scad

version = "2.2";

/* [Output] */
part = "assembly";      // [left, right, mount, coupon, template, assembly, scene, layout]
pose = 0;               // [0:0.05:1]
print_pose = 1;         // modules are printed open: the lever then fits a 220 x 220 bed

/* [Print-in-place gaps - print the coupon first] */
cj = 0.45;              // joint gap, radial (pin <-> ring)
gz = 0.6;               // vertical gap between stacked moving layers (3 layers at 0.2 mm)
cs = 1.0;               // gap between moving parts away from the joints
lean_comp = 0.7;        // door lean compensation (see below), share of the closed-pose lean to cancel. 0 = off

/* [Hardware] */
shaft = 8;              // square sync rod across the cabinet in mm: solid steel
sock_top = 15;          // rod socket depth from the bay side
eye_bolt = 6;           // actuator eye bolts: M6 (5 or 4 also work)
act_gap = 7;            // printed spacer between the lever and the rod eye: the actuator tube clears the lever
wall_screw = 4;         // wall plate: 4 mm countersunk wood screws, 4 x 20
door_screw = 3.5;       // door bracket: 3.5 mm countersunk wood screws, 3.5 x 16, driven at 45 deg

/* [Hidden] */
$fn = 48;
FNJ = 96;               // facets of the joint surfaces
N = 34;                 // sweep steps (~3 deg)
function dirv(a) = [cos(a), sin(a)];

// ---- kinematics: parallelogram, door translates on a circle of radius R ----
R = 77;  TH0 = 241;  SWING = 100;       // arm direction P -> A when closed; arms turn clockwise
A1 = [17, 96];                          // front bracket pin, closed
BASE = 50;  BDIR = 101;                 // A1 - A2 (= P1 - P2): 40 deg away from every arm direction
A2 = A1 - BASE * dirv(BDIR);
P1 = A1 - R * dirv(TH0);  P2 = A2 - R * dirv(TH0);
function arm_rot(f) = -SWING * f;
function T(f) = R * (dirv(TH0 - SWING * f) - dirv(TH0));     // door travel
// lever on the front arm, opposite the arm; length so the 150 mm stroke spans exactly the swing
LEV = 150 / (2 * sin(SWING / 2));  LEV_A = TH0 - 180;
C0 = P1 + LEV * dirv(LEV_A);
ACT0 = 225;                             // actuator pin to pin, retracted
F = C0 + ACT0 * dirv(LEV_A - SWING / 2 + 90);   // top pivot on the chord line: same lever arm at both ends

// ---- layer stack ----
z_top = 22;                             // bed -> cheek face
h1 = 6;                                 // ring height (bottom layer)
z2 = h1 + gz;                           // start of the upper moving layer
z_mov = z_top - 5;                      // arms + bracket end here: the door's side edge

// ---- joints: hourglass pin in a ring with an inner lip ----
// The pin is thickest at its root, where bending peaks, and bears on the 2.8 mm land right below the root. The waist near
// the bed side holds the lip, which is what keeps the joint together. All flanks are 45 deg, so no supports.
ridge = 1;  land = 0.8;                 // waist depth (= retention), waist length
ef = 0.4;  fz = 0.2;                    // first-layer relief; lip flanks moved apart axially: the layer-to-layer gap on a 45 deg flank stays = cj
rP1 = 10;  rP2 = 5.5;  rA = 5.5;        // pin radius at P1 (rod socket inside), P2 and A1/A2 (bracket pins)
wall = 5;                               // ring wall (radial) at A1/A2 in the arms (5.5 would bring the arms within 2 mm of the drawer front)
wallP2 = 5;  wall1_l = 12;  wall1_r = 7; // plate rings. P1 is wide: on the left the lever sweeps over it, so it is h1 tall and hangs on 2 narrow necks
lug_l = 14;                             // the arm's ring runs into the arm as a tapered lug over this length, not a sharp corner
pin_hole = 4;                           // hole through every solid pin: perimeters then fill the whole pin and run on through its root in any slicer
function rPof(P) = P == P1 ? rP1 : rP2;
rRA = rA + cj + wall;                   // ring radius at A1/A2 (in the arms)
function rRPof(P, lev = true) = rPof(P) + cj + (P == P1 ? (lev ? wall1_l : wall1_r) : wallP2);   // ring radius at P1/P2 (in the wall plate)

// ---- arms, lever, bracket, plate ----
// half widths at the pivot / at the door end. The front arms carry the actuator or rod torque, so they taper; the rear arms
// only see tension or compression. A pivot half width above rP + cj - cs lets the arm's sweep cut the bearing wall above the ring:
// only the front arm does that, on purpose (below).
function w0(P) = P == P1 ? 12 : 4.75;    // front arm wider than its pin at P1: its sweep trims the bearing wall above the ring, but FE shows
                                        // the arm's step into the ring layer gains more (shear between the layers -17 %) than the plate loses
function wA(P) = P == P1 ? 6 : 4.75;
rboss = 12;                             // lever boss at C (rod eye)
z_lev = 12;  lev_full_r = 30;           // lever web top: full height only near the pivot (bending peaks there) and at the eye boss
tf = 5;                                 // bracket flange on the door back
door_up = 2;                            // the wedge and the play lower the door's bottom: flange (and door) starts this much higher
yf = [17 + door_up, 106];               // flange: bottom flush with the door's bottom edge
YSC = [25, 50, 78];                     // door screws (45 deg, from the robot bay)
dsb = 45;  dze = 5;                     // door screw angle, entry depth on the door back (from the bed side)

// ---- door lean: the door's weight sits in front of the pins, so it takes up all joint play and tilts the bracket counter-clockwise:
// about 3.1 deg closed (8 mm at the door's top) but only 1.7 deg parked at cj = 0.45, because the front arm then carries mostly shear.
// No single wedge cancels both. 0.7 of the closed-pose value leaves the top 2.2 mm out when closed and 2.1 mm from the drawer front when parked.
// check_parallel.py solves this from the joint forces. The flange is wedged the other way about the middle of the two pins.
PLAY_R = 4 * cj / (BASE * abs(sin(TH0 - BDIR)));                   // radians, closed pose, all front-arm force axial
lean = lean_comp * atan(PLAY_R);
y_mid = (A1[1] + A2[1]) / 2;
function fx(y) = tan(lean) * (y - y_mid);                          // X of the flange's door face at height y

// ---- skeleton plate: pivot rings + screw bosses + ribs, all full height, so the ribs print as solid in-layer walls.
// Rib routes and widths from FE; check_strength.py runs the 3D FE of every body as printed (v2.2, 100 N stall: plates at 0.50 / 0.76 of the allowable).
rbs = 6.8;                              // screw boss radius (counterbore r 4.3 + 2.5 mm wall)
N1 = [48, 195];                         // rib node above P1 on the left: the lever's sweep leaves only this way out
N2 = [60, 146];                         // start of the diagonal rib to the screw at [112, 80]

// wall plate envelope (the sweeps cut it; nothing under the bracket: room for the closed reed on the tray) and screws [x, y] - same positions left and right (template)
ENV_L = [[40, 15.5], [40, 40], [2, 120], [2, 232], [92, 232], [125, 160], [125, 15.5]];
ENV_R = [[40, 15.5], [40, 40], [2, 120], [2, 232], [104, 232], [125, 205], [125, 15.5]];
S0 = [22, 222];  S1 = [66, 222];  S3 = [72, 42];  S4 = [112, 80];
SCREWS = [S0, S1, S3, S4];             // v2.1 had a 5th screw at [112, 24]: FE gives it under 35 N at the design load, so it and its two ribs are gone
WHEEL = [[52, 0], [88, 33]];            // drawer wheel (X 55-85, Y 0-30) + 3 mm: the plate's foot stays behind it

function Aof(P) = P + R * dirv(TH0);
function Qof(P) = Aof(P) - (rA + cs + wA(P)) * dirv(TH0);   // upper-layer arm end: clear of the bracket hub

// ---------------------------------------------------------------- 2D helpers
module disk(c, r, fn = 0) translate(c) circle(r = r, $fn = fn > 0 ? fn : $fn);
module capsule(a, b, ra, rb = -1) hull() { disk(a, ra); disk(b, rb < 0 ? ra : rb); }
module rot_about(c, a) translate(c) rotate(a) translate(-c) children();
module sweep_rot(c) for (i = [0 : N - 1]) hull() {          // convex child swept about c by the arm swing
  rot_about(c, arm_rot(i / N)) children();  rot_about(c, arm_rot((i + 1) / N)) children(); }
// self-supporting underside: from the seed outline grow 45 deg (lh per layer) until the full outline is reached
lh = 0.2;
module grow(n) {  // children(0) = seed, children(1) = target
  for (i = [0 : n - 1]) translate([0, 0, z2 + i * lh]) linear_extrude(lh + 0.001) intersection() { children(1); offset(r = i * lh) children(0); }
  translate([0, 0, z2 + n * lh]) linear_extrude(z_mov - z2 - n * lh) children(1);
}
module sweep_move() for (i = [0 : N - 1]) hull() {          // convex child moved along the door path
  translate(T(i / N)) children();  translate(T((i + 1) / N)) children(); }

// ---------------------------------------------------------------- joint profiles (r, z)
// pin: continues to z2 (hub starts there), a thinner stub overlaps into the hub
module pin_prof(r, h) polygon([[0, 0], [r - ef, 0], [r, ef], [r - ridge, ef + ridge], [r - ridge, ef + ridge + land], [r, ef + 2 * ridge + land],
                               [r, z2], [r - 0.5, z2], [r - 0.5, z2 + 0.5], [0, z2 + 0.5]]);
module hole_prof(r, h, top, g = cj) polygon([[0, -1], [r + g + ef + 1, -1], [r + g + ef, 0], [r + g, ef + fz],
                               [r - ridge + g, ef + ridge + fz], [r - ridge + g, ef + ridge + land - fz], [r + g, ef + 2 * ridge + land - fz],
                               [r + g, top], [0, top]]);
module pin3d(c, r) translate(c) rotate_extrude($fn = FNJ) pin_prof(r, h1);
module hole3d(c, r, top = h1 + 1) translate(c) rotate_extrude($fn = FNJ) hole_prof(r, h1, top);

// ---------------------------------------------------------------- arms (closed pose)
module arm_shape(P, E) capsule(P, E, w0(P), wA(P));
module lug(P) hull() { disk(Aof(P), rRA); disk(Aof(P) + lug_l * (P - Aof(P)) / R, wA(P)); }
module arm_b1(P, lev) { difference() { arm_shape(P, Aof(P)); disk(P, rRPof(P, lev) + cs); } disk(Aof(P), rRA); lug(P); }
module arm_b2(P) { disk(P, rPof(P), FNJ); arm_shape(P, Qof(P)); }
w_lev = 9;                              // lever half width at P1: wider would sweep over the left plate's P1 neck and the screw boss at S1
module lever_hull() hull() { disk(P1, w_lev); disk(C0, rboss); }
module lever_b1() difference() { lever_hull(); disk(P1, rRPof(P1, true) + cs); }

module arm3d(P, lev = false, sock = false) difference() {
  union() {
    linear_extrude(h1) { arm_b1(P, lev); if (lev && P == P1) lever_b1(); }
    translate([0, 0, h1]) linear_extrude(gz) { intersection() { arm_b1(P, lev); arm_b2(P); } if (lev && P == P1) lever_b1(); }
    translate([0, 0, z2]) linear_extrude(z_mov - z2) { arm_b2(P); if (lev && P == P1) intersection() { lever_hull(); union() { disk(P1, lev_full_r); disk(C0, rboss); } } }
    if (lev && P == P1) translate([0, 0, z2]) linear_extrude(z_lev - z2) lever_hull();
    pin3d(P, rPof(P));
  }
  hole3d(Aof(P), rA);
  if (!sock) translate([P[0], P[1], -1]) cylinder(d = pin_hole, h = z_mov + 2, $fn = 24);
  if (sock) translate([P[0], P[1], -1]) linear_extrude(sock_top + 1) square(shaft + 0.25, center = true);   // rod socket, open to the bay: tight, so little backlash between the sides
  if (lev && P == P1) eye_hole(C0, z_mov);
}

// eye bolt through the lever boss, nut sunk into the face towards the cheek
function nut_af(d) = d >= 6 ? 10 : d >= 5 ? 8 : 7;
module eye_hole(c, h) {
  translate([c[0], c[1], -1]) cylinder(d = eye_bolt + 0.4, h = h + 2, $fn = 32);
  translate([c[0], c[1], h - 9]) cylinder(d = (nut_af(eye_bolt) + 0.4) / cos(30), h = 10, $fn = 6);   // fits a nyloc nut
}

// ---------------------------------------------------------------- door bracket (closed pose)
module flange() polygon([[fx(yf[0]), yf[0]], [fx(yf[1]), yf[1]], [fx(yf[1]) + tf, yf[1]], [fx(yf[0]) + tf, yf[0]]]);
module brk_desired() hull() { flange(); disk(A1, rA + 4); disk(A2, rA + 4); }
// arms seen from the bracket: they turn about A1 / A2
// the lug's taper is swept, its ring is not: a polygon circle turned about its own centre only adds facets (the cs offset closes the seam)
module arms_bf_b1() for (P = [P1, P2]) { sweep_rot(Aof(P)) arm_shape(P, Aof(P)); disk(Aof(P), rRA);
  sweep_rot(Aof(P)) difference() { lug(P); disk(Aof(P), rRA + 0.3); } }
module arms_bf_b2() for (P = [P1, P2]) sweep_rot(Aof(P)) arm_shape(P, Qof(P));
module brk_b1() difference() { brk_desired(); offset(delta = cs) arms_bf_b1(); }
module brk_b2() { difference() { brk_desired(); offset(delta = cs) arms_bf_b2(); } disk(A1, rA, FNJ); disk(A2, rA, FNJ); }

module bracket3d() difference() {
  union() {
    linear_extrude(h1) brk_b1();
    translate([0, 0, h1]) linear_extrude(gz) intersection() { brk_b1(); brk_b2(); }
    grow(25) { union() { intersection() { brk_b1(); brk_b2(); } disk(A1, rA, FNJ); disk(A2, rA, FNJ); } brk_b2(); }   // no bridges over the rings
    pin3d(A1, rA);  pin3d(A2, rA);
  }
  for (y = YSC) door_screw_hole(y);
  for (a = [A1, A2]) translate([a[0], a[1], -1]) cylinder(d = pin_hole, h = z_mov + 2, $fn = 24);
}
// screw at 45 deg in the X-Z plane: head on the robot-bay face, driven from the bay at any door position.
// Axis through the door back (the flange face) at Z dze; 3.5 x 16 ends 7 mm deep in the door, 5 mm inside its side edge.
module door_screw_hole(y) translate([fx(y), y, dze]) rotate([0, 90 + dsb, 0]) {
  d = door_screw + 0.4;  dh = 2 * door_screw + 0.6;  sh = dze / sin(dsb) - 1;   // head top 1 mm below the bed face
  translate([0, 0, -6]) cylinder(d = d, h = sh + 6, $fn = 24);
  translate([0, 0, sh - (dh - d) / 2]) cylinder(d1 = d, d2 = dh, h = (dh - d) / 2 + 0.01, $fn = 32);
  translate([0, 0, sh]) cylinder(d = dh + 0.4, h = 25, $fn = 32);                // driver access
}

// ---------------------------------------------------------------- actuator (left): kept out of the wall plate
act_r_tube = 10;  act_r_body = 18;  act_tube_from = 12;  act_body_len = 190;
function Cf(f) = P1 + LEV * dirv(LEV_A + arm_rot(f));
function Uf(f) = (Cf(f) - F) / norm(Cf(f) - F);
module act_tube(f) capsule(Cf(f) - act_tube_from * Uf(f), F + act_body_len * Uf(f), act_r_tube);
module act_body(f) hull() { disk(F + 15 * Uf(f), act_r_body); disk(F + act_body_len * Uf(f), act_r_body); }
module act_sw() for (i = [0 : N - 1]) { hull() { act_tube(i / N); act_tube((i + 1) / N); } hull() { act_body(i / N); act_body((i + 1) / N); } }

// ---------------------------------------------------------------- wall plate (fixed)
function x_cheek(y) = y < 47 ? 250 : max(100, 250 - (y - 47) * 0.75);   // back edge of the cheek
module plate_desired(lev) difference() {
  intersection() { polygon(lev ? ENV_L : ENV_R); polygon([for (y = [0 : 10 : 520]) [x_cheek(y) - 3, y], [0, 520], [0, 0]]); }
  translate(WHEEL[0]) square(WHEEL[1] - WHEEL[0]);
}
module arm_sw_b1(P, lev) { difference() { sweep_rot(P) arm_shape(P, Aof(P)); disk(P, rRPof(P, lev) + cs); }
                           sweep_rot(P) disk(Aof(P), rRA);  sweep_rot(P) lug(P); }
module arm_sw_b2(P) sweep_rot(P) arm_shape(P, Qof(P));
module lever_sw_b1() difference() { sweep_rot(P1) lever_hull(); disk(P1, rRPof(P1, true) + cs); }
module lever_sw_b2() sweep_rot(P1) lever_hull();
module brk_sw() sweep_move() brk_desired();

// ribs [from, to, width]. The two necks at left P1 are as wide as the sweeps allow: this ring is only h1 tall
// Ties that FE showed carrying no load are left out: left S0-S1; right P1-S0 (arm 1's sweep cut it off the ring anyway).
function ribs_of(lev) = lev
  ? [[P1, N1, 14], [N1, S0, 5], [N1, S1, 6], [P1, P2, 14], [N2, S4, 8], [P2, S4, 6], [P2, S3, 6]]
  : [[P1, S1, 6], [S0, S1, 3], [P1, P2, 8], [P1, S4, 6], [P2, S4, 6], [P2, S3, 6]];
module skel2d(lev) {
  for (r = ribs_of(lev)) capsule(r[0], r[1], r[2] / 2);
  for (s = SCREWS) disk(s, rbs);
  disk(P1, rRPof(P1, lev), FNJ);  disk(P2, rRPof(P2, lev), FNJ);
}
module plate_b1_full(lev) {
  difference() { plate_desired(lev);
    offset(delta = cs) { arm_sw_b1(P1, lev); arm_sw_b1(P2, lev); if (lev) { lever_sw_b1(); act_sw(); } brk_sw(); } }
  disk(P1, rRPof(P1, lev), FNJ);  disk(P2, rRPof(P2, lev), FNJ);
}
module plate_b2_full(lev) intersection() {
  difference() { plate_desired(lev);
    offset(delta = cs) { arm_sw_b2(P1); arm_sw_b2(P2); if (lev) { lever_sw_b2(); act_sw(); } brk_sw(); } }
  offset(r = 0.8) plate_b1_full(lev);
}
rf = 3;   // fillet in the concave corners where ribs meet rings and bosses, clipped back to the free space
module fil() intersection() { children(0); offset(r = -rf) offset(r = rf) intersection() { children(0); children(1); } }
module plate_b1(lev) fil() { plate_b1_full(lev); skel2d(lev); }
module plate_b2(lev) offset(r = 0.6) offset(r = -0.6) fil() { plate_b2_full(lev); skel2d(lev); }   // sliver tips rounded off

module plate3d(lev) difference() {
  union() {
    linear_extrude(h1) plate_b1(lev);
    translate([0, 0, h1]) linear_extrude(z_top - h1) plate_b2(lev);
  }
  hole3d(P1, rP1, z_top + 1);  hole3d(P2, rP2, z_top + 1);    // ring + bearing wall above it
  for (s = SCREWS) wall_screw_hole(s, z_top);
  translate([P1[0], P1[1] + rP1 + cj + 2, z_top - 0.6]) linear_extrude(1) text(lev ? "L" : "R", size = 3, halign = "center", valign = "center");
}
// screw from the robot-bay side: deep counterbore, 90 deg seat, 5 mm under the head
module wall_screw_hole(s, h) translate([s[0], s[1], 0]) {
  d = wall_screw + 0.5;  dc = 2 * wall_screw + 0.6;  zs = h - 5 - (dc - d) / 2;
  translate([0, 0, -1]) cylinder(d = d, h = h + 2, $fn = 24);
  translate([0, 0, -1]) cylinder(d = dc, h = zs + 1, $fn = 32);
  translate([0, 0, zs - 0.01]) cylinder(d1 = dc, d2 = d, h = (dc - d) / 2 + 0.01, $fn = 32);
}

// ---------------------------------------------------------------- module = print-in-place set
// bracket with the door's weight on it: joint play taken up, flange face vertical
module bracket_loaded() rot_about([(A1[0] + A2[0]) / 2, y_mid], lean) bracket3d();
module lift_module(lev, f = 0, loaded = false) {
  color("Gainsboro") plate3d(lev);
  color("DarkOrange") rot_about(P1, arm_rot(f)) arm3d(P1, lev, true);
  color("Orange") rot_about(P2, arm_rot(f)) arm3d(P2, false, false);
  color("SteelBlue") translate(T(f)) if (loaded) bracket_loaded(); else bracket3d();
}

// ---------------------------------------------------------------- actuator top mount (left cheek)
// Printed with the cheek face down. Its boss reaches act_gap past the module face, so the actuator's top eye
// sits in the same plane as the rod eye on the lever spacer. Slots give +-8 mm to set the closed position.
// The spacer for the rod eye prints next to it.
mt = 14;  mslot = 8;
MS = [F + [-38, 6], F + [-38, 34], F + [-12, 34]];    // slot centres (+-8 mm)
module mount() { mount_block(); mount_spacer(); }
module mount_block() {
  difference() {
    union() {
      linear_extrude(mt) hull() { disk(F, 9.5); disk(F + [-38, -3.5], 10); disk(F + [-38, 44], 10); disk(F + [0, 44], 9.5); }
      translate([F[0], F[1], mt - 0.01]) cylinder(d = 18, h = z_top + act_gap - mt + 0.01, $fn = 48);   // boss: top = eye plane
    }
    translate([F[0], F[1], -1]) cylinder(d = eye_bolt + 0.4, h = z_top + act_gap + 2, $fn = 32);
    translate([F[0], F[1], -1]) cylinder(d = (nut_af(eye_bolt) + 0.4) / cos(30), h = 7, $fn = 6);   // nut on the cheek side
    for (s = MS) {
      d = wall_screw + 0.5;  dc = 2 * wall_screw + 0.6;
      hull() for (dy = [-mslot, mslot]) translate([s[0], s[1] + dy, -1]) cylinder(d = d, h = mt + 2, $fn = 24);
      hull() for (dy = [-mslot, mslot]) translate([s[0], s[1] + dy, mt - (dc - d) / 2]) cylinder(d1 = d, d2 = dc, h = (dc - d) / 2 + 0.01, $fn = 32);
    }
    translate([F[0] - 25, F[1] + 20, mt - 0.6]) linear_extrude(1) text("UP", size = 6, halign = "center", valign = "center");
  }
}
// rod-eye spacer, printed next to the mount
module spacer() difference() { cylinder(d = 16, h = act_gap, $fn = 48); translate([0, 0, -1]) cylinder(d = eye_bolt + 0.4, h = act_gap + 2, $fn = 32); }
module mount_spacer() translate([F[0] - 20, F[1] - 22, 0]) spacer();

// ---------------------------------------------------------------- clearance test coupon
// three joints like A1/A2 with 0.35 / 0.45 / 0.55 mm, each with the bracket's ceiling (no bridge). Keep the smallest one that
// turns freely. The fourth joint is the big P1 size at the chosen 0.45 mm: if that one is stiff, the large bore needs more gap.
// It also copies the riskiest bridge of the modules: the left front arm prints flat over the 12 mm wall of the P1 ring, 13.5 mm
// from the pin to its bottom layer, 0.6 mm above the ring. Joint P has the same ring and a flat bar as wide as the arm.
CJ_TEST = [0.35, 0.45, 0.55];
module coupon_joint(c, r, g, h, lab, rw = wall, flat_w = 0) difference() {   // the A-size test pins get the same hole as the real ones
  coupon_joint_solid(c, r, g, h, lab, rw, flat_w);
  if (r == rA) translate([c[0], c[1], -1]) cylinder(d = pin_hole, h = h + 2, $fn = 24);
}
module coupon_joint_solid(c, r, g, h, lab, rw, flat_w) {
  rr = r + g + rw;  arm_y = rr + cs + rA;
  difference() {
    linear_extrude(h1) { disk(c, rr); translate(c + [-5, -rr - 12]) square([10, 12 + rr]); }
    translate(c) rotate_extrude($fn = FNJ) hole_prof(r, h1, h1 + 1, g);
  }
  translate(c) rotate_extrude($fn = FNJ) pin_prof(r, h1);
  translate([0, 0, 0]) linear_extrude(h) disk(c + [0, arm_y], rA);
  if (flat_w > 0) translate([0, 0, z2]) linear_extrude(h - z2) capsule(c, c + [0, arm_y], flat_w, rA);   // flat over the ring, like an arm
  else translate([0, 0, z2]) for (i = [0 : (h - z2) / lh - 1]) translate([0, 0, i * lh]) linear_extrude(lh + 0.001)
    intersection() { capsule(c, c + [0, arm_y], r); offset(r = i * lh) { disk(c, r, FNJ); disk(c + [0, arm_y], rA); } }
  translate([c[0], c[1] + arm_y, h - 0.5]) linear_extrude(1) text(lab, size = 4, halign = "center", valign = "center");
}
module coupon() {
  for (i = [0 : 2]) coupon_joint([i * 42, 0], rA, CJ_TEST[i], z2 + 4, str(round(CJ_TEST[i] * 100)));
  coupon_joint([126 + rP1 - rA + 3 + wall1_l - wall, 0], rP1, 0.45, z2 + 4, "P", wall1_l, w0(P1));
}

// ---------------------------------------------------------------- drill template (both cheeks)
// 2 mm plate: front edge against the back of the front leg, bottom edge on the tray. Mark + pre-drill the
// 5 wall screws through it. For the left cheek turn it over like a page. Also marks the top mount bolt height.
module template() difference() {
  linear_extrude(1.2) union() {
    translate([0, 15]) square([6, 215]);                 // front edge (leg) 15 .. 230
    translate([0, 15]) square([128, 6]);                 // bottom edge (tray)
    for (s = concat(SCREWS, [P1])) { translate(s - [7, 7]) square(14); translate([0, s[1] - 3]) square([s[0], 6]); translate([s[0] - 3, 15]) square([6, s[1] - 15]); }
  }
  for (s = SCREWS) translate([s[0], s[1], -1]) cylinder(d = 3.2, h = 4, $fn = 24);
  translate([P1[0], P1[1], -1]) cylinder(d = 2, h = 4, $fn = 16);
  translate([10, 120, 0.8]) rotate(90) linear_extrude(1) text("FRONT  ^", size = 5, halign = "center", valign = "center");
  translate([64, 30, 0.8]) linear_extrude(1) text("TRAY", size = 5, halign = "center", valign = "center");
}

// mount in the module frame (cheek face at z_top), for previews
module mount_placed() translate([0, 0, z_top]) mirror([0, 0, 1]) mount_block();

// ---------------------------------------------------------------- output
if (part == "right") lift_module(false, print_pose);
else if (part == "left") mirror([1, 0, 0]) lift_module(true, print_pose);
else if (part == "mount") mount();
else if (part == "coupon") coupon();
else if (part == "template") template();
else if (part == "plate_l") plate3d(true);
else if (part == "plate_r") plate3d(false);
else if (part == "arm1_l") arm3d(P1, true, true);
else if (part == "arm1_r") arm3d(P1, false, true);
else if (part == "arm2") arm3d(P2, false, false);
else if (part == "bracket") bracket3d();
else if (part == "bracket_loaded") bracket_loaded();
else if (part == "mount_w") mount_placed();
else if (part == "assembly") lift_module(true, pose);
else if (part == "echo") echo(str("GEO ", "P1=", P1, ";P2=", P2, ";A1=", A1, ";A2=", A2, ";R=", R, ";TH0=", TH0, ";SWING=", SWING,
                                  ";LEV=", LEV, ";LEV_A=", LEV_A, ";F=", F, ";ACT0=", ACT0, ";act_gap=", act_gap, ";SCREWS=", SCREWS,
                                  ";print_pose=", print_pose, ";rRP1=", rRPof(P1), ";rRP2=", rRPof(P2), ";rRA=", rRA, ";lean=", lean, ";y_mid=", y_mid, ";door_up=", door_up, ";BASE=", BASE, ";BDIR=", BDIR,
                                  ";cj=", cj, ";cs=", cs, ";gz=", gz, ";z_top=", z_top, ";z_mov=", z_mov, ";h1=", h1,
                                  ";YSC=", YSC, ";dsb=", dsb, ";dze=", dze, ";door_screw=", door_screw, ";wall_screw=", wall_screw,
                                  ";act_r_tube=", act_r_tube, ";act_r_body=", act_r_body, ";act_tube_from=", act_tube_from,
                                  ";act_body_len=", act_body_len, ";mt=", mt, ";rA=", rA, ";rP1=", rP1, ";rP2=", rP2, ";shaft=", shaft,
                                  ";sock_top=", sock_top, ";eye_bolt=", eye_bolt, ";version=", str("'", version, "'")));
// 2D layer outlines (debug)
else if (part == "2d_plate_b1_l") plate_b1(true);
else if (part == "2d_plate_b2_l") plate_b2(true);
else if (part == "2d_plate_b1_r") plate_b1(false);
else if (part == "2d_plate_b2_r") plate_b2(false);
else if (part == "2d_brk_b1") brk_b1();
else if (part == "2d_brk_b2") brk_b2();
else if (part == "2d_arm1") { arm_b1(P1, true); arm_b2(P1); lever_hull(); }
else if (part == "2d_arm2") { arm_b1(P2, false); arm_b2(P2); }
// preview: left module seen through the left cheek, with door, drawer front, tray, rod, actuator axis and top mount
else if (part == "scene") {
  lift_module(true, pose, true);
  c = Cf(pose);
  color("Peru", 0.35) translate([T(pose)[0], T(pose)[1], -60]) linear_extrude(60 + z_mov)
    polygon([[-19, 17 + door_up], [0, 17 + door_up], [0, 203 + door_up], [-18, 221 + door_up], [-19, 221 + door_up]]);                         // door with the back chamfer
  CH = [[0, 15], [250, 15], [250, 47], [100, 247], [100, 520], [0, 520]];          // cheek outline
  color("SaddleBrown") translate([0, 0, z_top]) linear_extrude(1) difference() { polygon(CH); offset(delta = -2) polygon(CH); }
  color("Tan") translate([-19, 225, z_top]) cube([16, 295, 1]);                              // drawer front (VEDDINGE)
  color("Tan") translate([-19, 0, z_top]) cube([19, 15, 1]);                                 // tray
  color("DimGray") rot_about(P1, arm_rot(pose)) translate([P1[0], P1[1], -60]) linear_extrude(sock_top - 1 + 60) square(shaft, center = true);   // rod
  color("Silver") hull() { translate([c[0], c[1], -act_gap - 8]) cylinder(d = 20, h = 8); translate([F[0], F[1], -act_gap - 8]) cylinder(d = 20, h = 8); }  // actuator
  color("SlateGray") mount_placed();
}
// print layout preview: both modules as they sit on the bed, 220 x 220 mm bed outlines
else if (part == "layout") {
  xl = Cf(print_pose)[0] + rboss;  xr = 125;  x0 = T(print_pose)[0];        // module X range at the print pose
  translate([(220 - (xl - x0)) / 2 + xl, -13.5, 0]) mirror([1, 0, 0]) lift_module(true, print_pose);
  translate([230 + (220 - (xr - x0)) / 2 - x0, -13.5, 0]) lift_module(false, print_pose);
  for (x = [0, 230]) color("LightGray") translate([x, 0, -1]) difference() { cube([220, 220, 0.5]); translate([1, 1, -1]) cube([218, 218, 3]); }
}
