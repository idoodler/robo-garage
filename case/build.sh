#!/bin/bash
# Case: PCB data from parts.py -> STL (OpenSCAD) -> release zip
set -e
cd "$(dirname "$0")"
V=$(sed -n 's/^version = "\([^"]*\)".*/\1/p' robo-garage-case.scad)   # case version from the SCAD file
[ -n "$V" ] || { echo "version not found in robo-garage-case.scad"; exit 1; }
"${PY:-python3}" gen_pcb_data.py >/dev/null
openscad -q -D 'part="base"' -o base.stl robo-garage-case.scad
openscad -q -D 'part="lid_print"' -o lid_print.stl robo-garage-case.scad
rm -f robo-garage-case_v*.zip
zip -q -X "robo-garage-case_v$V.zip" README.md base.stl lid_print.stl robo-garage-case.scad pcb_data.scad \
    gen_pcb_data.py view_assembly.png view_lid_top.png
echo "case/robo-garage-case_v$V.zip"
