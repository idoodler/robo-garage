#!/bin/bash
# Printed door parts: STL per print (OpenSCAD) -> release zip. Extra args go to OpenSCAD, e.g. ./build.sh -D cj=0.35
set -e
cd "$(dirname "$0")"
V=$(sed -n 's/^version = "\([^"]*\)".*/\1/p' parallel-lift.scad)
[ -n "$V" ] || { echo "version not found in parallel-lift.scad"; exit 1; }
stl() { openscad -q --export-format binstl -D "part=\"$2\"" "${@:4}" -o "$3" "$1"; }
for p in left right mount template; do stl parallel-lift.scad "$p" "parallel_$p.stl" "$@" & done
for p in left right mount template; do stl up-over.scad "$p" "upover_$p.stl" "$@" & done
wait
stl up-over.scad track upover_track_right.stl "$@" &
stl up-over.scad track_l upover_track_left.stl "$@" &
stl parallel-lift.scad coupon coupon.stl "$@" &
for p in channel saddle foot clamp; do stl lift-door.scad "$p" "lift_$p.stl" "$@" & done
for p in lever mount; do stl flap.scad "$p" "flap_$p.stl" "$@" & done
wait
rm -f robo-garage-doors_v*.zip parallel_coupon.stl upover_coupon.stl upover_track.stl
zip -q -X "robo-garage-doors_v$V.zip" README.md ./*.scad ./*.py build.sh ./*.stl ./*.png
echo "doors/robo-garage-doors_v$V.zip"
