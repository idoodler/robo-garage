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

GitHub Actions runs all of this on every push (`.github/workflows/build.yml`).
Locally: run from the repo root. Tested with KiCad 7.0.11 (Python `pcbnew`), Python 3 + shapely 2.2, OpenSCAD 2021.01.

| Step | Command |
|---|---|
| PCB: bare board | `python3 pcb/gen/build.py` |
| PCB: tracks + GND pour + DRC | `python3 pcb/gen/finish.py` (stops with an error on any DRC issue) |
| PCB: gerbers, BOM, CPL, renders | `python3 pcb/gen/fab.py pcb/robo-garage/robo-garage_routed.kicad_pcb pcb/out` |
| PCB: copy to `pcb/out` + zip | `pcb/gen/package.sh` |
| PCB: re-route (optional) | `pcb/gen/pipeline.sh` |
| Case: PCB data, STL, zip | `case/build.sh` |
| Simulator page | `python3 simulator/build_page.py` |
| Flash ESP32 | `esphome run esphome/robo-garage-pcb.yaml` |

| Tool | Needed for |
|---|---|
| Python package `shapely` 2.2 | `finish.py` |
| `kicad-cli`, `rsvg-convert` | `fab.py` |
| `zip` | `package.sh`, `case/build.sh` |
| `openscad`, font DejaVu Sans | `case/build.sh` |
| Java, `xvfb-run`, `pcb/tools/freerouting-1.9.0.jar` ([Freerouting releases](https://github.com/freerouting/freerouting/releases)) | `pipeline.sh` only |

Moved a part in `parts.py`? Then the old tracks no longer fit: run `pcb/gen/pipeline.sh` and commit the new `pcb/robo-garage/robo-garage.ses`.

## Release

| Step | What to do |
|---|---|
| 1 | Set the versions: `VERSION` in `pcb/gen/parts.py` (also printed on the board), `version` in `case/robo-garage-case.scad` |
| 2 | Push to `main` → GitHub Actions builds everything and checks the DRC |
| 3 | Push a tag: `git tag v1.2.0 && git push origin v1.2.0` → GitHub Actions publishes the release with both zips |
| or | On github.com: *Releases* → *Draft a new release* → new tag `v1.2.0` → *Publish*. The zips get attached about 2 min later |

Every build also keeps both zips for 30 days: *Actions* → run → *Artifacts*.
