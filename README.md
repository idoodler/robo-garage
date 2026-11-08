# Robo-Garage

Kitchen cabinet garage for a **Dreame L10s Pro Ultra Heat** robot vacuum.
ESP32 + ESPHome + Home Assistant: motorised door, light barrier, reed contacts, fan, LED ring, temperature/humidity, water leak probe + valve, buzzer.

**Live simulator:** https://claude.ai/artifact/KapGY8dMDmhuJijCuEXQXC

## Versions

| Part | Version | Status |
|---|---|---|
| Controller PCB | v1.3.1 | DRC 0 errors / 0 warnings (KiCad 7). JLCPCB assembles all parts (SMD + clamps), only the DevKitC is plugged in (USB-C reachable from outside). Power headroom: 12 V in 6 A, actuator 4.9 A limit, valve 3 A, every power path checked against IPC-2221. v1.3.1: clamp pins in 2 rows like the real part, pick & place rotations computed from JLC's own footprints |
| Case | v1.3.1 | fits PCB v1.3.1 (0 mm³ overlap with the part stand-in), DevKit USB-C through the left wall |
| ESPHome config | – | checked with ESPHome 2026.10.1 |
| Simulator | v5.4 | door open slider for all 4 door types, printed door parts in 3D + side view, door downloads |
| Doors | v2.2 | Printed parts for all 4 door types (lift door, flap out, up & over, parallel lift), no supports. Up & over + parallel lift: print-in-place modules with hourglass joints and hollow pins, skeleton plates and arms checked by 3D FE as printed (`check_strength.py`): 12 % less filament than v2.1 (both module pairs together), the most loaded spot down from 1.35 to 0.87 of its allowable at a 100 N stall (calculated), checked over the whole travel (joint gap 0.45 mm, up & over peg in its track 0.4 mm, other gaps ≥ 1 mm). Parallel lift parks 23 mm out (40 mm max) |

## Folders

| Folder | What is inside |
|---|---|
| `esphome/` | ESPHome config for the board (needs `secrets.yaml` with `wifi_ssid`, `wifi_password`) |
| `pcb/gen/` | PCB generator (Python + KiCad `pcbnew`). `parts.py` = single source of truth, `fplib.py` makes the own footprints (`pcb/lib/robo.pretty`) |
| `pcb/robo-garage/` | Work folder. Only `robo-garage.ses` (Freerouting result) is in git |
| `pcb/out/` | Order files: gerbers zip, BOM + CPL for JLCPCB, KiCad project, renders, `pin1-check.png`. **Order guide: `pcb/out/README.md`** |
| `case/` | 3D-printed case: OpenSCAD source, STL files, pictures, print guide |
| `doors/` | Printed door parts for all 4 door types: OpenSCAD source, STL files, check scripts, print + assembly guide (`doors/README.md`) |
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
| PCB: re-route (optional) | `pcb/gen/pipeline.sh` (Freerouting is not deterministic: run it again if `finish.py` reports unconnected items) |
| Case: PCB data, STL, zip | `case/build.sh` |
| Doors: STL, zip | `doors/build.sh` (other joint gap: `doors/build.sh -D cj=0.35`) |
| Doors: motion, gap and overhang checks | `python3 doors/check_parallel.py`, `python3 doors/check_upover.py`, `python3 doors/check_simple.py` |
| Doors: strength (joint loads + 3D FE as printed, about 6 min on 32 cores, up to 48 GB; `--jobs=1` for less) | `python3 doors/check_strength.py` (misuse case: `--yank`) |
| Simulator page | `python3 simulator/build_files.py` (downloads, pictures, case + door GLB) then `python3 simulator/build_page.py` |
| Flash ESP32 | `esphome run esphome/robo-garage-pcb.yaml` |

| Tool | Needed for |
|---|---|
| Python packages `shapely` 2.2, `segno` 1.6 (QR code on the silkscreen) | `build.py`, `finish.py` |
| `kicad-cli`, `rsvg-convert`, Python package `Pillow` | `fab.py` |
| `zip` | `package.sh`, `case/build.sh`, `doors/build.sh` |
| `openscad`, font DejaVu Sans | `case/build.sh`, `doors/build.sh`, `simulator/build_files.py` |
| Python packages `trimesh`, `rtree`, `shapely`, `numpy`; `xvfb-run` for `render.py`; `scipy`, `pyamg` for `check_strength.py` | `doors/check_*.py`, `doors/render.py` |
| Python packages `Pillow`, `trimesh`, `numpy`, `shapely`, `fast-simplification` | `simulator/build_files.py` |
| Java, `xvfb-run`, `pcb/tools/freerouting-1.9.0.jar` ([Freerouting releases](https://github.com/freerouting/freerouting/releases)) | `pipeline.sh` only |

Moved a part in `parts.py`? Then the old tracks no longer fit: run `pcb/gen/pipeline.sh` and commit the new `pcb/robo-garage/robo-garage.ses`.

## Release

| Step | What to do |
|---|---|
| 1 | Set the versions: `VERSION` in `pcb/gen/parts.py` (also printed on the board), `version` in `case/robo-garage-case.scad` |
| 2 | Push to `main` → GitHub Actions builds everything and checks the DRC |
| 3 | Push a tag: `git tag v1.3.1 && git push origin v1.3.1` → GitHub Actions publishes the release with both zips |
| or | On github.com: *Releases* → *Draft a new release* → new tag `v1.3.1` → *Publish*. The zips get attached about 2 min later |

Every build also keeps both zips for 30 days: *Actions* → run → *Artifacts*.
