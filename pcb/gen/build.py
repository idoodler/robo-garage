# Build the Robo-Garage controller board (placement + nets + outline + labels) with the KiCad 7 Python API.
import json
import math
import os
import sys

import pcbnew

import checks

sys.path.insert(0, os.path.dirname(__file__))
import importlib
import parts
importlib.reload(parts)

FPDIR = '/usr/share/kicad/footprints/'
import fplib                       # project footprints (clamps, tooling hole, buzzer) -> pcb/lib/robo.pretty
fplib.make_lib()
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'robo-garage'))
MM = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def rule_area(board, rect, tracks, vias_only=False):
    """Rule area on F.Cu + B.Cu: never copper pour; tracks / vias forbidden too when tracks=True.
    vias_only: only vias forbidden (pour + tracks allowed) - exported to Freerouting as a via_keepout."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    z.SetDoNotAllowCopperPour(not vias_only)
    z.SetDoNotAllowTracks(tracks and not vias_only)
    z.SetDoNotAllowVias(tracks or vias_only)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ol = z.Outline()
    ol.NewOutline()
    xa, ya, xb, yb = rect
    for x, y in ((xa, ya), (xb, ya), (xb, yb), (xa, yb)):
        ol.Append(MM(x), MM(y))
    board.Add(z)
    return z


def pin1_dots(board, refs=r'^(U|Q|D|LED)\d', r=0.2, gap=0.5):
    """v1.2: a filled silk dot next to pad 1 of every IC / transistor / diode (what JLC checks in the preview).
    The dot sits 'gap' outside pad 1, away from the footprint centre; skipped if it would touch any pad."""
    import re
    pads = [(pcbnew.ToMM(pd.GetPosition().x), pcbnew.ToMM(pd.GetPosition().y),
             max(pcbnew.ToMM(pd.GetSize().x), pcbnew.ToMM(pd.GetSize().y)) / 2)
            for f in board.GetFootprints() for pd in f.Pads()]
    n = 0
    for f in board.GetFootprints():
        if not re.match(refs, f.GetReference()):
            continue
        p1 = [pd for pd in f.Pads() if pd.GetNumber() == '1']
        if not p1:
            continue
        p1 = p1[0]
        cx, cy = pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y)
        px, py = pcbnew.ToMM(p1.GetPosition().x), pcbnew.ToMM(p1.GetPosition().y)
        dx, dy = px - cx, py - cy
        d = math.hypot(dx, dy) or 1.0
        half = max(pcbnew.ToMM(p1.GetSize().x), pcbnew.ToMM(p1.GetSize().y)) / 2
        # preferred spot: 'gap' beyond pad 1, away from the centre; else the nearest free spot on the pad-1 side
        a0 = math.atan2(dy, dx)
        cands = [(gap, a0)] + [(g, a0 + k * math.pi / 8) for g in (0.35, 0.25) for k in (0, 1, -1, 2, -2, 3, -3)]
        for g, a in cands:
            x, y = px + math.cos(a) * (half + g + r), py + math.sin(a) * (half + g + r)
            clr = 0.25 if g == gap else 0.15
            if all(math.hypot(x - qx, y - qy) >= qr + r + clr for qx, qy, qr in pads):
                break
        else:
            print('pin1_dots: no room for a dot at', f.GetReference())
            continue
        dot = pcbnew.PCB_SHAPE(board)
        dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
        dot.SetCenter(V(x, y))
        dot.SetEnd(V(x + r, y))
        dot.SetFilled(True)
        dot.SetWidth(MM(0.1))
        dot.SetLayer(pcbnew.F_SilkS)
        board.Add(dot)
        n += 1
    return n


def draw_qr(board, q):
    """v1.2: QR code as filled silk rectangles (one per run of dark modules in a row). On the back it is mirrored,
    so it reads correctly from below."""
    import segno
    code = segno.make(q['data'], error=q.get('error', 'm'), micro=False)
    neg = q.get('negative')                 # print the light modules + quiet zone (dark modules = bare mask)
    rows = [[(not v) if neg else v for v in r] for r in code.matrix_iter(scale=1, border=4 if neg else 0)]
    n, m = len(rows), q['module']
    x0, y0 = q['x'] - n * m / 2, q['y'] - n * m / 2
    layer = pcbnew.B_SilkS if q.get('back') else pcbnew.F_SilkS
    k = 0
    for r, row in enumerate(rows):
        c = 0
        while c < n:
            if not row[c]:
                c += 1
                continue
            c1 = c
            while c1 < n and row[c1]:
                c1 += 1
            xa, xb = (n - c1, n - c) if q.get('back') else (c, c1)
            sh = pcbnew.PCB_SHAPE(board)
            sh.SetShape(pcbnew.SHAPE_T_RECT)
            sh.SetStart(V(x0 + xa * m, y0 + r * m))
            sh.SetEnd(V(x0 + xb * m, y0 + (r + 1) * m))
            sh.SetFilled(True)
            sh.SetWidth(0)
            sh.SetLayer(layer)
            board.Add(sh)
            k += 1
            c = c1
    print('QR %s: version %s, %d x %d modules of %.2f mm, %d rectangles' % (q['data'], code.version, n, n, m, k))


def nudge_texts(board, items, step=0.2):
    """v1.2: move each listed text to the nearest spot (within its radius) that is clear of pads, silk,
    courtyards and the board edge. Logs the moves; leaves the text where it is if nothing fits."""
    import checks
    for txt, radius in items:
        side = 'B' if txt.GetLayer() == pcbnew.B_SilkS else 'F'
        pads, yards, region = checks.silk_env(board, side)
        silk = [s for s in checks.silk_geoms(board) if s[1].GetLayer() == txt.GetLayer()]
        p0 = txt.GetPosition()
        n = int(radius / step)
        offs = sorted(((i * step, j * step) for i in range(-n, n + 1) for j in range(-n, n + 1)
                       if math.hypot(i, j) * step <= radius + 1e-9), key=lambda d: (math.hypot(*d), abs(d[1])))
        for dx, dy in offs:
            txt.SetPosition(pcbnew.VECTOR2I(p0.x + MM(dx), p0.y + MM(dy)))
            if not checks.text_conflicts(checks.text_ink(txt), pads, yards, region, silk, self_item=txt):
                if dx or dy:
                    print('nudged %r by (%.1f, %.1f) mm' % (txt.GetText(), dx, dy))
                break
        else:
            txt.SetPosition(p0)
            print('nudge: no free spot for %r within %.1f mm' % (txt.GetText(), radius))


def silk_via_keepouts(board, texts, margin=0.35):
    """v1.2: no vias under the board texts and the QR code (JLCPCB clips silk at via holes): one via-only
    rule area per text line / QR, exported to Freerouting as via_keepout; the GND stitching avoids silk anyway."""
    import checks
    from shapely.ops import unary_union
    boxes = [checks.text_ink(d) for d in texts]
    qr = [checks.item_poly(d) for d in board.GetDrawings() if checks.is_qr(d)]
    if qr:
        boxes.append(unary_union(qr).envelope)
    for bx in boxes:
        x0, y0, x1, y1 = bx.buffer(margin, join_style=2).bounds
        rule_area(board, (x0, y0, x1, y1), True, vias_only=True)
    print('via keep-outs under silk:', len(boxes))


def apart(p, q):
    """A reference never reads as part of a label: 3 mm from it on the same text line, else 0.8 mm."""
    (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = p.bounds, q.bounds
    same_line = min(ay1, by1) - max(ay0, by0) > 0.2
    return p.distance(q) >= (3.0 if same_line else 0.8)


def place_refs(board):
    """v1.2: put every visible reference (U, Q, D, F, L) where it is clear of pads, silk and courtyards:
    library position first, then around the courtyard. No room -> hidden (logged)."""
    import checks
    hidden = []
    for side in ('F',):
        pads, yards, region = checks.silk_env(board, side)
        for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
            t = fp.Reference()
            if not t.IsVisible():
                continue
            t.SetTextAngle(pcbnew.EDA_ANGLE(-fp.GetOrientationDegrees(), pcbnew.DEGREES_T))   # horizontal
            cy = fp.GetCourtyard(pcbnew.F_CrtYd)
            bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False)
            x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()))
            cx, cyy = (x0 + x1) / 2, (y0 + y1) / 2
            tb = t.GetEffectiveTextShape().BBox()
            w, h = pcbnew.ToMM(tb.GetWidth()), pcbnew.ToMM(tb.GetHeight())
            g = 0.15
            cands = [None]
            for d in (0.0, 0.8):
                cands += [(cx, y0 - h / 2 - g - d), (cx, y1 + h / 2 + g + d), (x0 - w / 2 - g - d, cyy),
                          (x1 + w / 2 + g + d, cyy), (x0 - w / 2 - g - d, y0 - h / 2 - g - d),
                          (x1 + w / 2 + g + d, y0 - h / 2 - g - d), (x0 - w / 2 - g - d, y1 + h / 2 + g + d),
                          (x1 + w / 2 + g + d, y1 + h / 2 + g + d), (x0 + w / 2, y0 - h / 2 - g - d),
                          (x1 - w / 2, y0 - h / 2 - g - d), (x0 + w / 2, y1 + h / 2 + g + d),
                          (x1 - w / 2, y1 + h / 2 + g + d)]
            silk = [s for s in checks.silk_geoms(board) if s[1].GetLayer() == pcbnew.F_SilkS]
            labels = [q for _, it, q in silk if isinstance(it, pcbnew.PCB_TEXT)]
            ok = False
            for c in cands:
                if c is not None:
                    t.SetPosition(V(*c))
                    if hasattr(t, 'SetLocalCoord'):
                        t.SetLocalCoord()
                p = checks.text_ink(t)
                if not checks.text_conflicts(p, pads, yards, region, silk, self_item=t) and \
                        all(apart(p, q) for q in labels):     # never reads as part of a label
                    ok = True
                    break
            if not ok:
                t.SetVisible(False)
                hidden.append(fp.GetReference())
    if hidden:
        print('place_refs: no room, hidden:', ' '.join(hidden))
    return hidden


def build(path=OUT + '/robo-garage.kicad_pcb', tracks=True):
    os.makedirs(OUT, exist_ok=True)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    nets = {}

    def net(name):
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
            nets[name] = ni
        return nets[name]

    for ref, p in parts.P.items():
        libdir = fplib.LIB if p['lib'] == 'robo' else FPDIR + p['lib'] + '.pretty'
        fp = pcbnew.FootprintLoad(libdir, p['fp'])
        if fp is None:
            raise SystemExit('missing footprint %s:%s' % (p['lib'], p['fp']))
        fp.SetReference(ref)
        fp.SetValue(p['val'])
        board.Add(fp)
        fp.SetPosition(V(p['x'], p['y']))
        fp.SetOrientationDegrees(p['rot'])
        attr = pcbnew.FP_THROUGH_HOLE if p.get('tht') else pcbnew.FP_SMD
        if p.get('nobom') or p.get('dnp'):
            attr |= pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        fp.SetAttributes(attr)
        if ref == 'U1':
            fp.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)   # PowerPAD + thermal vias solid to GND
        if p.get('lcsc'):
            fp.SetProperty('LCSC', p['lcsc'])
        # silkscreen reference: ICs, transistors, diodes, fuses, inductor (placed later by place_refs: where it fits),
        # hidden for passives. v1.2: 1.0 mm / 0.17 mm = JLCPCB standard silkscreen
        fp.Reference().SetVisible(ref[0] in 'UQLFD')
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0)))
        fp.Reference().SetTextThickness(MM(0.17))
        for pad in fp.Pads():
            n = pad.GetNumber()
            if n and p['nets'].get(n):
                pad.SetNet(net(p['nets'][n]))
            if p.get('npth') and pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:      # v1.3.1: peg hole per datasheet
                pad.SetDrillSize(pcbnew.VECTOR2I(MM(p['npth']), MM(p['npth'])))
                pad.SetSize(pcbnew.VECTOR2I(MM(p['npth']), MM(p['npth'])))

    # outline with 2 mm rounded corners
    W, H, r = parts.W, parts.H, 2.0

    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a))
        s.SetEnd(V(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        board.Add(s)

    def arc(c, a0):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        pts = [(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))) for a in (a0, a0 + 45, a0 + 90)]
        s.SetArcGeometry(V(*pts[0]), V(*pts[1]), V(*pts[2]))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        board.Add(s)

    seg((r, 0), (W - r, 0)); seg((W, r), (W, H - r)); seg((W - r, H), (r, H)); seg((0, H - r), (0, r))
    arc((W - r, r), 270); arc((W - r, H - r), 0); arc((r, H - r), 90); arc((r, r), 180)
    # milled slots (closed polygons, e.g. thermal isolation around the SHT40)
    for poly in getattr(parts, 'SLOTS', []):
        for a, b in zip(poly, poly[1:] + poly[:1]):
            seg(a, b)

    # v1.1.1: clip footprint silk (WAGO bodies overhang the edge) to stay 0.2 mm inside the outline / slots
    import post
    post.trim_silk(board, 0.2, log=lambda *a: None)

    # rule areas: KEEPOUTS = no tracks / vias / pour (exported to Freerouting).
    # NOPOUR areas are added after routing (route.add_zones), because the DSN export turns every rule area into a keepout.
    for rect in getattr(parts, 'KEEPOUTS', []):
        rule_area(board, rect, True)

    nudge, novia = [], []
    for t in parts.TEXTS if hasattr(parts, 'TEXTS') else []:
        txt = pcbnew.PCB_TEXT(board)
        txt.SetText(t['text'])
        txt.SetPosition(V(t['x'], t['y']))
        txt.SetLayer(pcbnew.B_SilkS if t.get('back') else pcbnew.F_SilkS)
        sz = t.get('size', 1.0)
        txt.SetTextSize(pcbnew.VECTOR2I(MM(sz), MM(sz)))
        txt.SetTextThickness(MM(t.get('th', max(0.17, sz / 6.0))))     # JLCPCB: >= 0.153 mm, ~1:6
        txt.SetTextAngleDegrees(t.get('rot', 0))
        if t.get('back'):
            txt.SetMirrored(True)
        just = t.get('just', 'c')
        txt.SetHorizJustify({'l': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'r': pcbnew.GR_TEXT_H_ALIGN_RIGHT,
                             'c': pcbnew.GR_TEXT_H_ALIGN_CENTER}[just])
        board.Add(txt)
        if t.get('nudge'):
            nudge.append((txt, t['nudge']))
        if t.get('novia'):
            novia.append(txt)

    pin1_dots(board)
    if getattr(parts, 'QR', None):
        draw_qr(board, parts.QR)
    nudge_texts(board, nudge)

    for poly in getattr(parts, 'SILK_LINES', []):
        for a, b in zip(poly[:-1], poly[1:]):
            s = pcbnew.PCB_SHAPE(board)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(V(*a)); s.SetEnd(V(*b))
            s.SetLayer(pcbnew.F_SilkS); s.SetWidth(MM(0.15))
            board.Add(s)

    for netname, w, layer, pts in (getattr(parts, 'TR', []) if tracks else []):
        for a, b in zip(pts[:-1], pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(V(*a)); t.SetEnd(V(*b)); t.SetWidth(MM(w))
            t.SetLayer(pcbnew.F_Cu if layer == 'F' else pcbnew.B_Cu)
            t.SetNet(net(netname)); t.SetLocked(True)
            board.Add(t)
    for vdef in (getattr(parts, 'VIAS', []) if tracks else []):    # (net, x, y[, diameter, drill])
        netname, x, y = vdef[:3]
        dia, drill = vdef[3:5] if len(vdef) >= 5 else (0.6, 0.3)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y)); v.SetDrill(MM(drill)); v.SetWidth(MM(dia))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net(netname)); v.SetLocked(True)
        board.Add(v)

    place_refs(board)
    silk_via_keepouts(board, novia)
    for side, ref, text, c in checks.silk_text_conflicts(board):
        print('silk conflict %s %s %r: %s' % (side, ref, text, ', '.join(c[:4])))

    ds = board.GetDesignSettings()
    ds.m_MinClearance = MM(0.15)
    ds.m_TrackMinWidth = MM(0.2)
    ds.m_ViasMinSize = MM(0.5)
    ds.m_CopperEdgeClearance = MM(0.4)
    ds.m_HoleClearance = MM(0.25)
    pcbnew.SaveBoard(path, board)
    write_project(path.replace('.kicad_pcb', '.kicad_pro'))
    return path


# v1.3 net classes, widths after IPC-2221 (external layer, 1 oz, <= 20 C rise at the rated current):
# Power12 1.5 mm: valve 4 A (F4 hold) and short 12 V links; the trunks are pre-routed (parts.py): input 3.0 / 4.2 mm
# (7 A), west trunk + motor supply 2.0 mm (4.9 A), east branch 2.0 mm (valve + buck);
# Motor 1.5 mm, 0.2 mm clearance (the DRV8874 pins sit 0.25 mm apart): routed at 1.5 mm, finish.py widens every
# segment to 1.8 mm where the clearances allow (4.9 A current limit at ~20 C rise);
# Aux12 0.6 mm: fan / button LED / beam / leak behind F7 (1.1 A); Power5 0.8 mm: 5 V up to 2 A.
POWER = ['+12V_IN', '+12V_F', '+12V', '+12V_VLV', 'VALVE_K']
MOTOR = ['+12V_MOT', 'MOT_A', 'MOT_B']
AUX12 = ['+12V_A', '+12V_BTN']
FIVE = ['+5V', '+5V_LED', '+5V_DEV', 'SW']
SIG12 = ['+12V_LK']                 # v1.2: 12 V sensor feed on the LEAK clamp: 0.3 mm clearance to the 3V3 / SIG nets


def write_project(path):
    cls = [
        {"name": "Default", "clearance": 0.15, "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Power12", "clearance": 0.3, "track_width": 1.5, "via_diameter": 1.1, "via_drill": 0.6,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Motor", "clearance": 0.2, "track_width": 1.5, "via_diameter": 1.1, "via_drill": 0.6,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Aux12", "clearance": 0.3, "track_width": 0.6, "via_diameter": 0.8, "via_drill": 0.4,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Power5", "clearance": 0.25, "track_width": 0.8, "via_diameter": 0.8, "via_drill": 0.4,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Sig12", "clearance": 0.3, "track_width": 0.3, "via_diameter": 0.6, "via_drill": 0.3,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Gnd", "clearance": 0.15, "track_width": 0.3, "via_diameter": 0.6, "via_drill": 0.3,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
    ]
    pats = [{"netclass": "Power12", "pattern": n} for n in POWER] + [{"netclass": "Motor", "pattern": n} for n in MOTOR] + \
           [{"netclass": "Aux12", "pattern": n} for n in AUX12] + \
           [{"netclass": "Power5", "pattern": n} for n in FIVE] + [{"netclass": "Sig12", "pattern": n} for n in SIG12] + \
           [{"netclass": "Gnd", "pattern": "GND"}]
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                         "copper_text_size_v": 1.5, "copper_text_thickness": 0.3, "silk_line_width": 0.15,
                         "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
            "rules": {"min_clearance": 0.15, "min_track_width": 0.2, "min_via_diameter": 0.5,
                      "min_via_annular_width": 0.1, "min_through_hole_diameter": 0.3, "min_hole_to_hole": 0.25,
                      "min_hole_clearance": 0.25, "min_copper_edge_clearance": 0.4, "min_silk_clearance": 0.0,
                      "min_text_height": 0.8, "min_text_thickness": 0.12, "solder_mask_clearance": 0.05,
                      "allow_blind_buried_vias": False, "allow_microvias": False},
            "track_widths": [0.0, 0.25, 0.5, 0.8, 1.0, 1.5, 1.8, 2.0, 2.4, 3.0],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3},
                               {"diameter": 0.8, "drill": 0.4}, {"diameter": 1.1, "drill": 0.6}],
            "rule_severities": {"silk_overlap": "ignore", "starved_thermal": "warning", "silk_over_copper": "warning",
                                "silk_edge_clearance": "warning", "lib_footprint_mismatch": "ignore",
                                "lib_footprint_issues": "ignore", "text_height": "warning",
                                "text_thickness": "warning"}}},
        "meta": {"filename": os.path.basename(path), "version": 1},
        "net_settings": {"classes": cls, "meta": {"version": 3}, "net_colors": None,
                         "netclass_assignments": None, "netclass_patterns": pats},
    }
    json.dump(pro, open(path, 'w'), indent=2)


if __name__ == '__main__':
    print(build())
