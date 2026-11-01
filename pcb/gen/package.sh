#!/bin/bash
# Collect deliverables into pcb/out and one zip
set -e
D="$(cd "$(dirname "$0")/.." && pwd)"   # pcb/
R=$D/robo-garage
O=$D/out
mkdir -p $O/kicad
cp $R/robo-garage_routed.kicad_pcb $O/kicad/robo-garage.kicad_pcb
cp $R/robo-garage_routed.kicad_pro $O/kicad/robo-garage.kicad_pro
cp $D/gen/parts.py $O/kicad/parts.py
cp $D/../esphome/robo-garage-pcb.yaml $O/
cd $O
rm -f robo-garage-pcb_v1.1.1.zip
zip -q -r robo-garage-pcb_v1.1.1.zip README.md robo-garage_gerbers_JLCPCB.zip robo-garage_BOM_JLCPCB.csv \
    robo-garage_CPL_JLCPCB.csv robo-garage-pcb.yaml render_top.png render_bottom.png kicad
ls -la $O
