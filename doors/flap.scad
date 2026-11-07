// Robo-Garage flap out - printed parts (OpenSCAD, FOSS)
// David Gölzhäuser (idoodler) - https://github.com/idoodler/robo-garage
//
// A flush 18 mm flap (596 x 207 mm) hangs on a piano hinge at its top front edge and swings up and out to 90 deg.
// A lever on its back reaches 90 mm above the hinge; the actuator stands right behind the drawer front on the
// left cheek and pushes the lever tip down and back. Replaces the bent steel L-bracket.
//
// Frame (mm): X = depth behind the cheek front edge, Y = height above the floor (tray top = 15),
// W = distance from the left cheek's inner face towards the robot bay. Hinge axis: X -19, Y 224.
//
// part = "lever"   1x: screwed to the flap's back (3 screws 3.5 x 25), M6 bolt for the rod eye
//        "mount"   1x: actuator top mount on the left cheek (3 screws 4 x 25, +-8 mm slots), spacer printed with it
//        "set"     both on one bed
//        "scene"   side view of the left cheek from the bay; `pose` 0 = closed .. 1 = open (90 deg)

version = "1.0";

/* [Output] */
part = "scene";         // [lever, mount, set, scene]
pose = 0;               // [0:0.05:1]

/* [Hardware] */
eye_bolt = 6;           // M6 bolts for both actuator eyes
act_len = 225;          // actuator pin to pin, retracted
wall_screw = 4;         // mount: 4 mm countersunk wood screws
flap_screw = 3.5;       // lever: 3.5 x 25 countersunk into the flap's back

/* [Hidden] */
$fn = 48;
H = [-19, 224];                         // hinge axis
PIN = [37, 315.5];                      // lever pin, closed: 56 mm behind and 91.5 mm above the hinge (chord 152 mm)
lv_w = [8, 20];                         // lever plane (W), rod eye on its bay side with a washer
eye_w = lv_w[1] + 1 + 4;                // actuator centre plane (8 mm eyes)
lv_t = 14;                              // lever depth on the flap's back (X 0..14)
lv_y0 = 144;                            // lower end on the flap
SCREWS = [154, 180, 206];               // flap screws (Y), all below the hinge line
stroke = 150;
// actuator top pivot: act_len from the closed pin and act_len + stroke from the open pin, on the cheek side
function rotH(p, a) = H + [[cos(a), sin(a)], [-sin(a), cos(a)]] * (p - H);   // clockwise by a (flap opening)
PIN1 = rotH(PIN, 90);
CH_ = norm(PIN - PIN1);
TH_ = acos((act_len * act_len + CH_ * CH_ - (act_len + stroke) * (act_len + stroke)) / (2 * act_len * CH_));
A_ = atan2(PIN[1] - PIN1[1], PIN[0] - PIN1[0]);
F = PIN + act_len * [cos(A_ - (180 - TH_)), sin(A_ - (180 - TH_))];

module disk(c, r) translate(c) circle(r = r);
function nut_af(d) = d >= 6 ? 10 : d >= 5 ? 8 : 7;

// ---------------------------------------------------------------- lever (world frame, closed)
module lever_profile() union() {
  translate([0, lv_y0]) square([lv_t, PIN[1] + 10 - lv_y0]);                     // along the flap's back
  hull() { translate([0, PIN[1] - 10]) square([lv_t, 20]); disk(PIN, 10); }      // arm to the pin
  translate([lv_t, PIN[1] - 10]) polygon([[0, 0], [0, -22], [22, 0]]);            // gusset under the arm
}
module lever_world() difference() {
  translate([0, 0, lv_w[0]]) linear_extrude(lv_w[1] - lv_w[0]) lever_profile();
  translate([PIN[0], PIN[1], lv_w[0] - 1]) cylinder(d = eye_bolt + 0.4, h = 20, $fn = 32);
  translate([PIN[0], PIN[1], lv_w[0] - 1]) cylinder(d = (nut_af(eye_bolt) + 0.4) / cos(30), h = 6, $fn = 6);   // nut, cheek side
  for (y = SCREWS) translate([lv_t + 0.01, y, (lv_w[0] + lv_w[1]) / 2]) rotate([0, -90, 0]) {   // countersunk from the back
    cylinder(d = flap_screw + 0.4, h = lv_t + 1, $fn = 24);
    cylinder(d1 = 2 * flap_screw + 0.6, d2 = flap_screw + 0.4, h = flap_screw / 2 + 0.2, $fn = 32);
  }
}
module lever() translate([0, 0, -lv_w[0]]) lever_world();          // printed on its side: all features in the X-Y profile

// ---------------------------------------------------------------- top mount (left cheek, printed cheek face down)
mt = 14;  mslot = 8;
MS = [F + [-14, 18], F + [24, 18], F + [-14, -8]];
module mount_block() difference() {
  union() {
    linear_extrude(mt) hull() { disk(F, 11); disk(F + [-14, -18], 9.5); disk(F + [-14, 27], 9.5); disk(F + [24, 27], 9.5); }
    translate([F[0], F[1], mt - 0.01]) cylinder(d = 22, h = eye_w - 4 - 1 - mt + 0.01, $fn = 48);   // boss: top = eye face (with washer)
  }
  translate([F[0], F[1], -1]) cylinder(d = eye_bolt + 0.4, h = eye_w + 2, $fn = 32);
  translate([F[0], F[1], -1]) cylinder(d = (nut_af(eye_bolt) + 0.4) / cos(30), h = 7, $fn = 6);
  for (s = MS) {
    d = wall_screw + 0.5;  dc = 2 * wall_screw + 0.6;
    hull() for (dy = [-mslot, mslot]) translate([s[0], s[1] + dy, -1]) cylinder(d = d, h = mt + 2, $fn = 24);
    hull() for (dy = [-mslot, mslot]) translate([s[0], s[1] + dy, mt - (dc - d) / 2]) cylinder(d1 = d, d2 = dc, h = (dc - d) / 2 + 0.01, $fn = 32);
  }
  translate([F[0] + 5, F[1] + 18, mt - 0.6]) linear_extrude(1) text("UP", size = 6, halign = "center", valign = "center");
}
module mount() mount_block();

module set() {
  translate([10, -lv_y0 + 10, 0]) lever();
  translate([110 - F[0], 60 - F[1], 0]) mount();
}

// ---------------------------------------------------------------- scene
module scene(f) {
  a = 90 * f;
  module rot() translate([H[0], H[1], 0]) rotate(-a) translate([-H[0], -H[1], 0]) children();
  color("Tan", 0.6) rot() translate([-19, 17, -60]) cube([19, H[1] - 17, 60 + 18]);        // flap
  color("SteelBlue") rot() lever_world();
  p = rotH(PIN, a);
  color("SlateGray") mount_placed();
  color("DimGray") hull() { translate([F[0], F[1], eye_w - 6]) cylinder(d = 26, h = 2); translate([F[0], F[1], eye_w - 6] + concat((p - F) / norm(p - F) * 190, [0])) cylinder(d = 26, h = 2); }
  color("Silver") hull() { translate([F[0], F[1], eye_w - 6] + concat((p - F) / norm(p - F) * 150, [0])) cylinder(d = 14, h = 2); translate([p[0], p[1], eye_w - 6]) cylinder(d = 14, h = 2); }
  CH = [[0, 15], [250, 15], [250, 47], [100, 247], [100, 620], [0, 620]];
  color("SaddleBrown") translate([0, 0, -80]) linear_extrude(1) difference() { polygon(CH); offset(delta = -2) polygon(CH); }
  color("Tan") translate([-19, 225, -80]) cube([16, 395, 1]);
  color("Sienna") translate([-19, 3, -80]) cube([19 + 250, 12, 1]);
}
module mount_placed() mount_block();     // printed cheek face down = W 0 on the cheek

if (part == "echo") echo(str("GEO F=", F, ";PIN=", PIN, ";PIN1=", PIN1, ";H=", H, ";act_len=", act_len, ";stroke=", stroke, ";eye_w=", eye_w, ";lv_w=", lv_w, ";lv_t=", lv_t, ";lv_y0=", lv_y0, ";version='", version, "'"));
else if (part == "lever") lever();
else if (part == "w_lever") lever_world();
else if (part == "w_mount") mount_placed();
else if (part == "mount") mount();
else if (part == "set") set();
else if (part == "scene") scene(pose);
