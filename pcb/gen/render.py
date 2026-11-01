# Render board layers to PNG for visual review: kicad-cli svg -> rsvg-convert png
import subprocess
import sys

pcb = sys.argv[1]
out = sys.argv[2]
layers = sys.argv[3] if len(sys.argv) > 3 else 'F.Cu,B.Cu,F.SilkS,Edge.Cuts,F.Fab,F.CrtYd'
svg = out.replace('.png', '.svg')
subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '--layers', layers, '--page-size-mode', '2',
                '--exclude-drawing-sheet', '-o', svg, pcb], check=True, capture_output=True)
subprocess.run(['rsvg-convert', '-w', sys.argv[4] if len(sys.argv) > 4 else '1600', '-b', 'white', '-o', out, svg],
               check=True)
print(out)
