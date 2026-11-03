#!/bin/bash
# Collect deliverables into pcb/out and one zip
set -e
D="$(cd "$(dirname "$0")/.." && pwd)"   # pcb/
R="$D/robo-garage"
O="$D/out"
V=$(sed -n "s/^VERSION = '\([^']*\)'.*/\1/p" "$D/gen/parts.py")   # PCB version from parts.py
[ -n "$V" ] || { echo "VERSION not found in parts.py"; exit 1; }
mkdir -p "$O/kicad"
cp "$R/robo-garage_routed.kicad_pcb" "$O/kicad/robo-garage.kicad_pcb"
cp "$R/robo-garage_routed.kicad_pro" "$O/kicad/robo-garage.kicad_pro"
cp "$D/gen/parts.py" "$O/kicad/parts.py"
cp "$D/../esphome/robo-garage-pcb.yaml" "$O/"
cd "$O"
rm -f robo-garage-pcb_v*.zip
zip -q -r "robo-garage-pcb_v$V.zip" README.md robo-garage_gerbers_JLCPCB.zip robo-garage_BOM_JLCPCB.csv \
    robo-garage_CPL_JLCPCB.csv robo-garage-pcb.yaml render_top.png render_bottom.png pin1-check.png kicad
ls -la "$O"
