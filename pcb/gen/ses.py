# Minimal Specctra SES importer for KiCad 7 (pcbnew.ImportSpecctraSES needs the GUI frame)
import re

import pcbnew


def parse_sexpr(text):
    tokens = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == '(':
            stack.append(cur)
            cur = []
        elif t == ')':
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t.strip('"'))
    return cur[0]


def find(node, key):
    for n in node:
        if isinstance(n, list) and n and n[0] == key:
            yield n


def import_ses(board, ses_path):
    tree = parse_sexpr(open(ses_path).read())
    routes = next(find(tree, 'routes'))
    res = next(find(routes, 'resolution'))
    scale = {'um': 1e-3, 'mm': 1.0, 'mil': 0.0254, 'inch': 25.4}[res[1]] / float(res[2])   # unit -> mm
    pads = {}
    lib = next(find(routes, 'library_out'), [])
    for ps in find(lib, 'padstack'):
        name = ps[1]
        dia = None
        for sh in find(ps, 'shape'):
            c = sh[1]
            if c[0] == 'circle':
                dia = float(c[2]) * scale
        m = re.search(r'_(\d+):(\d+)_um', name)
        drill = int(m.group(2)) / 1000.0 if m else 0.3
        if m and dia is None:
            dia = int(m.group(1)) / 1000.0
        pads[name] = (dia, drill)
    netinfo = board.GetNetInfo()
    nw = nv = 0
    layers = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu}
    for net in find(next(find(routes, 'network_out')), 'net'):
        ni = board.FindNet(net[1])
        if ni is None:
            raise SystemExit('unknown net ' + net[1])
        for w in find(net, 'wire'):
            path = next(find(w, 'path'))
            layer, width = layers[path[1]], float(path[2]) * scale
            pts = [(float(path[i]) * scale, -float(path[i + 1]) * scale) for i in range(3, len(path) - 1, 2)]
            locked = any(isinstance(x, list) and x[0] == 'type' and x[1] in ('fix', 'protect') for x in w)
            for a, b in zip(pts[:-1], pts[1:]):
                if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 0.02:
                    continue
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
                tr.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
                tr.SetWidth(pcbnew.FromMM(width))
                tr.SetLayer(layer)
                tr.SetNet(ni)
                tr.SetLocked(locked)
                board.Add(tr)
                nw += 1
        for v in find(net, 'via'):
            dia, drill = pads.get(v[1], (0.6, 0.3))
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(float(v[2]) * scale), pcbnew.FromMM(-float(v[3]) * scale)))
            via.SetWidth(pcbnew.FromMM(dia))
            via.SetDrill(pcbnew.FromMM(drill))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(ni)
            board.Add(via)
            nv += 1
    return nw, nv
