// Robo-Garage parallel lift door v2 - print-in-place modules (OpenSCAD, FOSS)
// David Gölzhäuser (idoodler) - https://github.com/idoodler/robo-garage
//
// One module per cheek = wall plate (fixed) + front arm (P1-A1) + rear arm (P2-A2) + door bracket.
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

version = "2.0";

/* [Output] */
part = "assembly";      // [left, right, mount, coupon, template, assembly, scene, layout]
pose = 0;               // [0:0.05:1]
print_pose = 1;         // modules are printed open: the lever then fits a 220 x 220 bed

/* [Print-in-place gaps - print the coupon first] */
cj = 0.45;              // joint gap, radial (pin <-> ring)
gz = 0.6;               // vertical gap between stacked moving layers (3 layers at 0.2 mm)
cs = 1.0;               // gap between moving parts away from the joints

/* [Hardware] */
shaft = 8;              // square sync rod across the cabinet in mm
eye_bolt = 6;           // actuator eye bolts: M6 (5 or 4 also work)
act_gap = 7;            // printed spacer between the lever and the rod eye: the actuator tube clears the lever
wall_screw = 4;         // wall plate: 4 mm countersunk wood screws, 4 x 20
door_screw = 3.5;       // door bracket: 3.5 mm countersunk wood screws, 3.5 x 20, driven at 45 deg

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

// ---- joints: diamond pin in a grooved ring ----
bulge = 1;  ef = 0.4;                   // bulge (45 deg flanks), first-layer relief
rP = 9;  rA = 4.5;                      // pin core radius at P (arm pins) / at A (bracket pins)
wall = 4;  wall1 = 7;                   // ring wall (radial); P1 thicker: lever + arm leave only 2 narrow necks
rRA = rA + bulge + cj + wall;           // ring radius at A1/A2 (in the arms)
function rRPof(P) = rP + bulge + cj + (P == P1 ? wall1 : wall);   // ring radius at P1/P2 (in the wall plate)

// ---- arms, lever, bracket, plate ----
wb = 14;                                // arm and lever width
rboss = 12;                             // lever boss at C (rod eye)
tf = 5;                                 // bracket flange on the door back
yf = [17, 106];                         // flange: bottom flush with the door's bottom edge
YSC = [24, 70];                         // door screws (45 deg, from the robot bay)
dsb = 45;  dze = 5;                     // door screw angle, entry depth on the door back (from the bed side)

// wall plate envelope (the sweeps cut it; nothing under the bracket: room for the closed reed on the tray) and screws [x, y] - same positions left and right (template)
ENV_L = [[40, 15.5], [40, 40], [2, 120], [2, 232], [92, 232], [125, 160], [125, 15.5]];
ENV_R = [[40, 15.5], [40, 40], [2, 120], [2, 232], [104, 232], [125, 205], [125, 15.5]];
SCREWS = [[22, 222], [66, 222], [112, 24], [72, 42], [112, 80]];
WHEEL = [[52, 0], [88, 33]];            // drawer wheel (X 55-85, Y 0-30) + 3 mm: the plate's foot stays behind it

function Aof(P) = P + R * dirv(TH0);
function Qof(P) = Aof(P) - (rA + cs + wb / 2) * dirv(TH0);   // upper-layer arm end: clear of the bracket hub

// ---------------------------------------------------------------- 2D helpers
module disk(c, r, fn = 0) translate(c) circle(r = r, $fn = fn > 0 ? fn : $fn);
module capsule(a, b, ra, rb = -1) hull() { disk(a, ra); disk(b, rb < 0 ? ra : rb); }
module rot_about(c, a) translate(c) rotate(a) translate(-c) children();
module sweep_rot(c) for (i = [0 : N - 1]) hull() {          // convex child swept about c by the arm swing
  rot_about(c, arm_rot(i / N)) children();  rot_about(c, arm_rot((i + 1) / N)) children(); }
module sweep_move() for (i = [0 : N - 1]) hull() {          // convex child moved along the door path
  translate(T(i / N)) children();  translate(T((i + 1) / N)) children(); }

// ---------------------------------------------------------------- joint profiles (r, z)
// pin: ends at z2 (hub starts there), a thinner stub overlaps into the hub
module pin_prof(r, h) polygon([[0, 0], [r - ef, 0], [r + bulge, bulge + ef], [r + bulge, h - bulge],
                               [r, h], [r, z2], [r - 0.5, z2], [r - 0.5, z2 + 0.5], [0, z2 + 0.5]]);
module hole_prof(r, h, top, g = cj) polygon([[0, -1], [r + g + ef + 1, -1], [r + g + ef, 0], [r + g, ef],
                               [r + bulge + g, bulge + ef], [r + bulge + g, h - bulge], [r + g, h],
                               [r + g, top], [0, top]]);
module pin3d(c, r) translate(c) rotate_extrude($fn = FNJ) pin_prof(r, h1);
module hole3d(c, r, top = h1 + 1) translate(c) rotate_extrude($fn = FNJ) hole_prof(r, h1, top);

// ---------------------------------------------------------------- arms (closed pose)
module arm_b1(P) { difference() { capsule(P, Aof(P), wb / 2); disk(P, rRPof(P) + cs); } disk(Aof(P), rRA); }
module arm_b2(P) { disk(P, rP, FNJ); capsule(P, Qof(P), wb / 2); }
module lever_hull() hull() { disk(P1, wb / 2); disk(C0, rboss); }
module lever_b1() difference() { lever_hull(); disk(P1, rRPof(P1) + cs); }

module arm3d(P, lev = false, sock = false) difference() {
  union() {
    linear_extrude(h1) { arm_b1(P); if (lev) lever_b1(); }
    translate([0, 0, h1]) linear_extrude(gz) { intersection() { arm_b1(P); arm_b2(P); } if (lev) lever_b1(); }
    translate([0, 0, z2]) linear_extrude(z_mov - z2) { arm_b2(P); if (lev) lever_hull(); }
    pin3d(P, rP);
  }
  hole3d(Aof(P), rA);
  if (sock) translate([P[0], P[1], -1]) linear_extrude(z2 + 8) square(shaft + 0.4, center = true);   // rod socket, open to the bay
  if (lev) eye_hole(C0, z_mov);
}

// eye bolt through the lever boss, nut sunk into the face towards the cheek
function nut_af(d) = d >= 6 ? 10 : d >= 5 ? 8 : 7;
module eye_hole(c, h) {
  translate([c[0], c[1], -1]) cylinder(d = eye_bolt + 0.4, h = h + 2, $fn = 32);
  translate([c[0], c[1], h - 9]) cylinder(d = (nut_af(eye_bolt) + 0.4) / cos(30), h = 10, $fn = 6);   // fits a nyloc nut
}

// ---------------------------------------------------------------- door bracket (closed pose)
module brk_desired() hull() { translate([0, yf[0]]) square([tf, yf[1] - yf[0]]); disk(A1, rA + 5); disk(A2, rA + 5); }
// arms seen from the bracket: they turn about A1 / A2
module arms_bf_b1() for (P = [P1, P2]) { sweep_rot(Aof(P)) capsule(P, Aof(P), wb / 2); disk(Aof(P), rRA); }
module arms_bf_b2() for (P = [P1, P2]) sweep_rot(Aof(P)) capsule(P, Qof(P), wb / 2);
module brk_b1() difference() { brk_desired(); offset(delta = cs) arms_bf_b1(); }
module brk_b2() { difference() { brk_desired(); offset(delta = cs) arms_bf_b2(); } disk(A1, rA, FNJ); disk(A2, rA, FNJ); }

module bracket3d() difference() {
  union() {
    linear_extrude(h1) brk_b1();
    translate([0, 0, h1]) linear_extrude(gz) intersection() { brk_b1(); brk_b2(); }
    translate([0, 0, z2]) linear_extrude(z_mov - z2) brk_b2();
    pin3d(A1, rA);  pin3d(A2, rA);
  }
  for (y = YSC) door_screw_hole(y);
}
// screw at 45 deg in the X-Z plane: head on the robot-bay face, driven from the bay at any door position.
// Axis through the door back (X 0) at Z dze; 3.5 x 20 ends 9.9 mm deep in the door, 2 mm inside its side edge.
module door_screw_hole(y) translate([0, y, dze]) rotate([0, 90 + dsb, 0]) {
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
module arm_sw_b1(P) { difference() { sweep_rot(P) capsule(P, Aof(P), wb / 2); disk(P, rRPof(P) + cs); }
                      sweep_rot(P) disk(Aof(P), rRA); }
module arm_sw_b2(P) sweep_rot(P) capsule(P, Qof(P), wb / 2);
module lever_sw_b1() difference() { sweep_rot(P1) lever_hull(); disk(P1, rRPof(P1) + cs); }
module lever_sw_b2() sweep_rot(P1) lever_hull();
module brk_sw() sweep_move() brk_desired();

module plate_b1(lev) {
  difference() { plate_desired(lev);
    offset(delta = cs) { arm_sw_b1(P1); arm_sw_b1(P2); if (lev) { lever_sw_b1(); act_sw(); } brk_sw(); } }
  disk(P1, rRPof(P1), FNJ);  disk(P2, rRPof(P2), FNJ);
}
module plate_b2(lev) intersection() {
  difference() { plate_desired(lev);
    offset(delta = cs) { arm_sw_b2(P1); arm_sw_b2(P2); if (lev) { lever_sw_b2(); act_sw(); } brk_sw(); } }
  offset(r = 0.8) plate_b1(lev);
}

module plate3d(lev) difference() {
  union() {
    linear_extrude(h1) plate_b1(lev);
    translate([0, 0, h1]) linear_extrude(z_top - h1) plate_b2(lev);
  }
  hole3d(P1, rP, z_top + 1);  hole3d(P2, rP, z_top + 1);    // ring + bearing wall above it
  for (s = SCREWS) wall_screw_hole(s, z_top);
  translate([P1[0], P1[1] + rRPof(P1) + 6, z_top - 0.6]) linear_extrude(1) text(lev ? "L" : "R", size = 6, halign = "center", valign = "center");
}
// screw from the robot-bay side: deep counterbore, 90 deg seat, 5 mm under the head
module wall_screw_hole(s, h) translate([s[0], s[1], 0]) {
  d = wall_screw + 0.5;  dc = 2 * wall_screw + 0.6;  zs = h - 5 - (dc - d) / 2;
  translate([0, 0, -1]) cylinder(d = d, h = h + 2, $fn = 24);
  translate([0, 0, -1]) cylinder(d = dc, h = zs + 1, $fn = 32);
  translate([0, 0, zs - 0.01]) cylinder(d1 = dc, d2 = d, h = (dc - d) / 2 + 0.01, $fn = 32);
}

// ---------------------------------------------------------------- module = print-in-place set
module lift_module(lev, f = 0) {
  color("Gainsboro") plate3d(lev);
  color("DarkOrange") rot_about(P1, arm_rot(f)) arm3d(P1, lev, true);
  color("Orange") rot_about(P2, arm_rot(f)) arm3d(P2, false, false);
  color("SteelBlue") translate(T(f)) bracket3d();
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
// three joints like A1/A2 with 0.35 / 0.45 / 0.55 mm. Keep the smallest one that turns freely.
CJ_TEST = [0.35, 0.45, 0.55];
module coupon() for (i = [0 : 2]) {
  c = [i * 42, 0];  g = CJ_TEST[i];
  difference() {
    linear_extrude(h1) { disk(c, rRA); translate(c + [-5, -rRA - 12]) square([10, 12 + rRA]); }
    translate(c) rotate_extrude($fn = FNJ) hole_prof(rA, h1, h1 + 1, g);
  }
  pin3d(c, rA);
  translate([0, 0, z2]) linear_extrude(3) capsule(c, c + [0, rRA + cs + 4], rA);
  linear_extrude(z2 + 3) disk(c + [0, rRA + cs + 4], rA);
  translate([c[0], c[1] + rRA + cs + 4, z2 + 3 - 0.5]) linear_extrude(1)
    text(str(round(g * 100)), size = 4, halign = "center", valign = "center");
}

// ---------------------------------------------------------------- drill template (both cheeks)
// 2 mm plate: front edge against the back of the front leg, bottom edge on the tray. Mark + pre-drill the
// 5 wall screws through it. For the left cheek turn it over like a page. Also marks the top mount bolt height.
module template() difference() {
  linear_extrude(2) union() {
    translate([0, 15]) square([6, 215]);                 // front edge (leg) 15 .. 230
    translate([0, 15]) square([128, 6]);                 // bottom edge (tray)
    for (s = concat(SCREWS, [P1])) { translate(s - [7, 7]) square(14); translate([0, s[1] - 3]) square([s[0], 6]); translate([s[0] - 3, 15]) square([6, s[1] - 15]); }
  }
  for (s = SCREWS) translate([s[0], s[1], -1]) cylinder(d = 3.2, h = 4, $fn = 24);
  translate([P1[0], P1[1], -1]) cylinder(d = 2, h = 4, $fn = 16);
  translate([10, 120, 1.4]) rotate(90) linear_extrude(1) text("FRONT  ^", size = 5, halign = "center", valign = "center");
  translate([64, 30, 1.4]) linear_extrude(1) text("TRAY", size = 5, halign = "center", valign = "center");
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
else if (part == "mount_w") mount_placed();
else if (part == "assembly") lift_module(true, pose);
else if (part == "echo") echo(str("GEO ", "P1=", P1, ";P2=", P2, ";A1=", A1, ";A2=", A2, ";R=", R, ";TH0=", TH0, ";SWING=", SWING,
                                  ";LEV=", LEV, ";LEV_A=", LEV_A, ";F=", F, ";ACT0=", ACT0, ";act_gap=", act_gap, ";SCREWS=", SCREWS,
                                  ";print_pose=", print_pose, ";rRP1=", rRPof(P1), ";rRP2=", rRPof(P2), ";rRA=", rRA,
                                  ";cj=", cj, ";cs=", cs, ";gz=", gz, ";z_top=", z_top, ";z_mov=", z_mov, ";h1=", h1,
                                  ";YSC=", YSC, ";dsb=", dsb, ";dze=", dze, ";door_screw=", door_screw, ";wall_screw=", wall_screw,
                                  ";act_r_tube=", act_r_tube, ";act_r_body=", act_r_body, ";act_tube_from=", act_tube_from,
                                  ";act_body_len=", act_body_len, ";mt=", mt, ";version=", str("'", version, "'")));
// 2D layer outlines (debug)
else if (part == "2d_plate_b1_l") plate_b1(true);
else if (part == "2d_plate_b2_l") plate_b2(true);
else if (part == "2d_plate_b1_r") plate_b1(false);
else if (part == "2d_plate_b2_r") plate_b2(false);
else if (part == "2d_brk_b1") brk_b1();
else if (part == "2d_brk_b2") brk_b2();
// preview: left module seen through the left cheek, with door, drawer front, tray, rod, actuator axis and top mount
else if (part == "scene") {
  lift_module(true, pose);
  c = Cf(pose);
  color("Peru", 0.35) translate([T(pose)[0], T(pose)[1], -60]) linear_extrude(60 + z_mov)
    polygon([[-19, 17], [0, 17], [0, 203], [-18, 221], [-19, 221]]);                         // door with the back chamfer
  CH = [[0, 15], [250, 15], [250, 47], [100, 247], [100, 520], [0, 520]];          // cheek outline
  color("SaddleBrown") translate([0, 0, z_top]) linear_extrude(1) difference() { polygon(CH); offset(delta = -2) polygon(CH); }
  color("Tan") translate([-19, 225, z_top]) cube([16, 295, 1]);                              // drawer front (VEDDINGE)
  color("Tan") translate([-19, 0, z_top]) cube([19, 15, 1]);                                 // tray
  color("DimGray") rot_about(P1, arm_rot(pose)) translate([P1[0], P1[1], -60]) linear_extrude(z2 + 7 + 60) square(shaft, center = true);   // rod
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
