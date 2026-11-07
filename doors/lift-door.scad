// Robo-Garage lift door - printed parts (OpenSCAD, FOSS)
// David Gölzhäuser (idoodler) - https://github.com/idoodler/robo-garage
//
// A 6 mm MDF panel (496 x 220 mm) rides in two U-channels behind the drawer front. The actuator stands in
// the left front corner and pushes the panel up 150 mm from below; going down the panel follows by its own
// weight, so it can never pinch.
//
// Frame (mm): X = depth behind the cheek front edge (= back of the front legs), Y = height above the floor
// (drawer tray top = 15), W = distance from the left cheek's inner face towards the robot bay.
//
// part = "channel"  4x: U-channel segment, 190 mm (2 per side) - alternative to the alu profile
//        "saddle"   1x: clip over the panel's top left corner; the actuator rod pushes into its cup
//        "foot"     1x: clevis for the actuator's bottom eye, screwed to the tray
//        "clamp"    1x: keeps the actuator body upright on the left cheek (zip tie)
//        "set"      all prints, laid out as on the bed
//        "scene"    side view of the left cheek from the bay; `pose` 0 = closed .. 1 = open
// All parts print without supports in the orientation exported here.

version = "1.0";

/* [Output] */
part = "scene";         // [channel, saddle, foot, clamp, set, scene]
pose = 0;               // [0:0.05:1]

/* [Actuator] */
act_len = 225;          // pin to pin, retracted (check yours)
stroke = 150;
eye_r = 9;              // rod eye: outer radius around its hole (the tip pushes into the saddle cup)
bolt = 6;               // clevis bolt M6
body_d = 28;            // actuator body diameter at the clamp

/* [Hidden] */
$fn = 48;
door_x = [4, 10];  door_y = [15, 235];                  // panel, resting on the tray when closed
ch_x = [2, 12];  ch_wall = 1.5;  ch_base = 1.5;  ch_h = 10;  // channel: same envelope as the 10 x 10 alu profile
ch_flange = [12, 22];  ch_ft = 3;  ch_len = 190;  ch_split = 205;
act_x = 32;  act_w = 36;                                // actuator axis (X, W)
foot_y = 30;                                            // bottom pivot, 15 mm above the tray
tip_y = foot_y + act_len + eye_r;                       // rod tip, retracted
seat_y = tip_y + 3;                                     // cup roof: 3 mm air when closed (the panel rests on the tray)
sd_w = [act_w - 15, act_w + 15];                        // saddle width
sd_top = seat_y + 9;

// helpers: world (X, Y, W) -> print orientation, both proper rotations
module to_bed_from_top(top) multmatrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, top]]) children();   // Y top -> bed
module to_bed_from_bottom(b) multmatrix([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, -b]]) children();   // Y bottom -> bed
module countersink(d, dh, len) { cylinder(d = d, h = len, $fn = 24); translate([0, 0, len - (dh - d) / 2]) cylinder(d1 = d, d2 = dh, h = (dh - d) / 2 + 0.01, $fn = 32); }

// ---------------------------------------------------------------- channel: local x = X, y = W, z = along Y
module channel_profile() union() {
  translate([ch_x[0], 0]) square([ch_x[1] - ch_x[0], ch_base]);
  translate([ch_x[0], 0]) square([ch_wall, ch_h]);
  translate([ch_x[1] - ch_wall, 0]) square([ch_wall, ch_h]);
  translate([ch_flange[0] - 0.01, 0]) square([ch_flange[1] - ch_flange[0] + 0.01, ch_ft]);
}
module channel() difference() {
  linear_extrude(ch_len) channel_profile();
  for (z = [0, ch_len]) for (s = [1, -1]) {                       // 45 deg lead-in on the inner faces at both ends
    x = s > 0 ? ch_x[0] + ch_wall : ch_x[1] - ch_wall;
    translate([x, ch_base, z]) rotate([90, 0, 0]) translate([0, 0, -ch_h - 1]) linear_extrude(ch_h + 2)
      polygon([[0, -1.2], [-s * 1.2, 0], [0, 1.2]]);
  }
  for (z = [22, ch_len / 2, ch_len - 22]) translate([(ch_flange[0] + ch_flange[1]) / 2, -0.01, z]) rotate([-90, 0, 0]) countersink(3.9, 7.6, ch_ft + 0.02);
  for (z = [0, ch_len]) translate([ch_flange[1] - 2.5, ch_ft / 2, z]) cylinder(d = 1.9, h = 16, center = true, $fn = 16);   // dowel: 1.75 filament
}

// ---------------------------------------------------------------- saddle (world frame)
module saddle_profile() union() {
  translate([door_x[1] + 0.2, 198]) square([4, sd_top - 198]);                                   // plate on the panel's back
  translate([door_x[0] - 2, door_y[1] + 0.3]) square([door_x[1] + 4.2 - door_x[0] + 2, 5]);     // bridge over the top edge
  translate([door_x[0] - 2, 226]) square([1.8, door_y[1] + 5.3 - 226]);                          // front lip, hidden by the drawer front
  translate([door_x[1] + 0.2, seat_y - 2]) square([act_x + 13 - door_x[1] - 0.2, sd_top - seat_y + 2]);   // seat arm
  translate([door_x[1] + 4.2, seat_y - 2]) polygon([[0, 0], [0, -14], [14, 0]]);                // gusset
}
module saddle_world() difference() {
  translate([0, 0, sd_w[0]]) linear_extrude(sd_w[1] - sd_w[0]) saddle_profile();
  translate([act_x, seat_y - 2.01, act_w]) rotate([-90, 0, 0]) cylinder(d = 2 * eye_r + 2, h = 2.01, $fn = 48);   // cup: printed upside down
  translate([act_x, seat_y - 0.01, act_w]) rotate([-90, 0, 0]) cylinder(d1 = 2 * eye_r + 2, d2 = 4, h = eye_r, $fn = 48);
  translate([door_x[0] - 3, 230, act_w]) rotate([0, 90, 0]) cylinder(d = 3.4, h = 20, $fn = 24);                 // M3 through lip + panel
  translate([door_x[1] + 4.2 - 2.5, 230, act_w]) rotate([0, 90, 0]) rotate(30) cylinder(d = 6.4 / cos(30), h = 3, $fn = 6);   // nut
}
module saddle() to_bed_from_top(sd_top) saddle_world();

// ---------------------------------------------------------------- foot (world frame, on the tray)
ft_x = [act_x - 16, act_x + 16];  ft_gap = 12;  ft_ear = 6;  ft_t = 4;
ft_w = [act_w - ft_gap / 2 - ft_ear, act_w + ft_gap / 2 + ft_ear];
module foot_world() difference() {
  union() {
    translate([ft_x[0], 15, ft_w[0]]) cube([ft_x[1] - ft_x[0], ft_t, ft_w[1] - ft_w[0]]);
    for (w = [ft_w[0], act_w + ft_gap / 2]) hull() {
      translate([act_x - 10, 15, w]) cube([20, ft_t, ft_ear]);
      translate([act_x, foot_y, w]) cylinder(r = 8, h = ft_ear);
    }
  }
  translate([act_x, foot_y, ft_w[0] - 1]) cylinder(d = bolt + 0.4, h = ft_w[1] - ft_w[0] + 2, $fn = 32);
  translate([act_x, foot_y, ft_w[1] - 3]) rotate(30) cylinder(d = (bolt >= 6 ? 10.4 : 8.4) / cos(30), h = 4, $fn = 6);   // nut
  for (x = [ft_x[0] + 5, ft_x[1] - 5]) translate([x, 15 + ft_t + 0.01, act_w]) rotate([90, 0, 0]) countersink(4.4, 8.6, ft_t + 0.02);
}
module foot() to_bed_from_bottom(15) foot_world();

// ---------------------------------------------------------------- clamp (world frame, left cheek)
cl_y = [160, 182];  cl_x = [act_x - 13, act_x + 13];
module clamp() difference() {                                   // printed as is: cheek face (W 0) on the bed
  union() {
    translate([ch_flange[1] + 1, cl_y[0], 0]) cube([cl_x[1] + 12 - ch_flange[1] - 1, cl_y[1] - cl_y[0], 4]);   // flange, behind the channel's
    translate([cl_x[0], cl_y[0], 0]) cube([cl_x[1] - cl_x[0], cl_y[1] - cl_y[0], act_w - 4]);                   // post
  }
  translate([cl_x[0] - 1, cl_y[0] - 1, -1]) cube([ch_flange[1] + 1.5 - cl_x[0], cl_y[1] - cl_y[0] + 2, ch_ft + 1.5]);   // notch: channel flange
  translate([act_x, cl_y[0] - 1, act_w]) rotate([-90, 0, 0]) cylinder(d = body_d + 1, h = cl_y[1] - cl_y[0] + 2, $fn = 64);   // cradle
  for (y = [cl_y[0] + 5.5, cl_y[1] - 5.5]) translate([cl_x[0] - 1, y - 2, 9]) cube([cl_x[1] - cl_x[0] + 2, 4, 3]);   // zip tie channels
  for (x = [ch_flange[1] + 5, cl_x[1] + 7]) translate([x, (cl_y[0] + cl_y[1]) / 2, -0.01]) countersink(4.4, 8.6, 4.02);
}

// ---------------------------------------------------------------- one bed
module channel_print() translate([0, ch_len, 0]) rotate([90, 0, 0]) channel();   // cheek face on the bed
module set() {
  for (i = [0 : 3]) translate([i * 24 - 2, 15, 0]) channel_print();
  translate([100, 25, 0]) translate([0, -sd_w[0], 0]) saddle();
  translate([160, 30, 0]) translate([-ft_x[0], ft_w[1], 0]) foot();
  translate([160, 110, 0]) translate([-cl_x[0], -cl_y[0], 0]) clamp();
}

// ---------------------------------------------------------------- scene: left cheek seen from the bay
module scene(f) {
  L = stroke * f;
  color("Tan", 0.6) translate([door_x[0], door_y[0] + L, -60]) cube([door_x[1] - door_x[0], door_y[1] - door_y[0], 60 + 3]);   // panel
  color("Silver") for (y = [15, ch_split]) translate([0, y, 0]) multmatrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]]) channel();
  color("SteelBlue") translate([0, L, 0]) saddle_world();
  color("SteelBlue") foot_world();
  color("SteelBlue") clamp();
  color("DimGray") { translate([act_x, foot_y, act_w]) rotate([-90, 0, 0]) cylinder(d = body_d, h = act_len - 30);
                     translate([act_x, foot_y, act_w]) rotate([-90, 0, 0]) cylinder(d = 14, h = act_len + L); }
  CH = [[0, 15], [250, 15], [250, 47], [100, 247], [100, 520], [0, 520]];
  color("SaddleBrown") translate([0, 0, -70]) linear_extrude(1) difference() { polygon(CH); offset(delta = -2) polygon(CH); }
  color("Tan") translate([-19, 225, -70]) cube([16, 295, 1]);
  color("BurlyWood") translate([-19, 17, -70]) cube([19, 208, 1]);
  color("Sienna") translate([-19, 3, -70]) cube([19 + 250, 12, 1]);
}

if (part == "channel") channel_print();
else if (part == "saddle") saddle();
else if (part == "foot") foot();
else if (part == "clamp") clamp();
else if (part == "set") set();
else if (part == "scene") scene(pose);
// world-frame bodies for check_simple.py
else if (part == "w_channel") for (y = [15, ch_split]) translate([0, y, 0]) multmatrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]]) channel();
else if (part == "w_saddle") saddle_world();
else if (part == "w_foot") foot_world();
else if (part == "w_clamp") clamp();
else if (part == "echo") echo(str("GEO tip_y=", tip_y, ";seat_y=", seat_y, ";stroke=", stroke, ";door_y=", door_y, ";door_x=", door_x, ";act_len=", act_len, ";version='", version, "'"));
