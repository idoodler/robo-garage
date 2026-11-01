# Robo-Garage

Kitchen cabinet garage for a **Dreame L10s Pro Ultra Heat** robot vacuum.
ESP32 + ESPHome + Home Assistant: motorised door, light barrier, reed contacts, fan, LED ring, temperature/humidity.

**Live simulator:** https://claude.ai/artifact/KapGY8dMDmhuJijCuEXQXC

## Versions

| Part | Version | Status |
|---|---|---|
| Controller PCB | v1.1.1 | DRC 0 errors / 0 warnings (KiCad 7 + KiCad 10) |
| Case | v1.1 | fits PCB v1.1 / v1.1.1 |
| ESPHome config | – | checked with ESPHome 2026.10.1 |
| Simulator | v5.1 | |

## Folders

| Folder | What is inside |
|---|---|
| `esphome/` | ESPHome config for the board (needs `secrets.yaml` with `wifi_ssid`, `wifi_password`) |
| `pcb/gen/` | PCB generator (Python + KiCad `pcbnew`). `parts.py` = single source of truth |
| `pcb/robo-garage/` | Work folder. Only `robo-garage.ses` (Freerouting result) is in git |
| `pcb/out/` | Order files: gerbers zip, BOM + CPL for JLCPCB, KiCad project, renders. **Order guide: `pcb/out/README.md`** |
| `case/` | 3D-printed case: OpenSCAD source, STL files, pictures, print guide |
| `simulator/` | Simulator web page: `robo-garage.html` (source) → `build_page.py` → `index.html` |

## Build

Run from the repo root. Tested with KiCad 7.0.11 (Python `pcbnew`), Python 3, OpenSCAD.

| Step | Command |
|---|---|
| PCB: bare board | `python3 pcb/gen/build.py` |
| PCB: tracks + GND pour + DRC | `python3 pcb/gen/finish.py` |
| PCB: gerbers, BOM, CPL, renders | `python3 pcb/gen/fab.py pcb/robo-garage/robo-garage_routed.kicad_pcb pcb/out` |
| PCB: copy to `pcb/out` + zip | `pcb/gen/package.sh` |
| PCB: re-route (optional) | `pcb/gen/pipeline.sh` |
| Case: PCB data | `python3 case/gen_pcb_data.py` |
| Case: STL | `openscad -D 'part="base"' -o case/base.stl case/robo-garage-case.scad` |
| | `openscad -D 'part="lid_print"' -o case/lid_print.stl case/robo-garage-case.scad` |
| Simulator page | `python3 simulator/build_page.py` |
| Flash ESP32 | `esphome run esphome/robo-garage-pcb.yaml` |

| Tool | Needed for |
|---|---|
| `kicad-cli`, `rsvg-convert` | `fab.py` |
| `zip` | `package.sh` |
| Java, `xvfb-run`, `pcb/tools/freerouting-1.9.0.jar` ([Freerouting releases](https://github.com/freerouting/freerouting/releases)) | `pipeline.sh` only |
