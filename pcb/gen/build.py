# Build the Robo-Garage controller board (placement + nets + outline + labels) with the KiCad 7 Python API.
import json
import math
import os
import sys

import pcbnew

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


def rule_area(board, rect, tracks):
    """Rule area on F.Cu + B.Cu: never copper pour; tracks / vias forbidden too when tracks=True."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(tracks)
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
        # silkscreen reference: keep for connectors / ICs, hide for small passives
        fp.Reference().SetVisible(ref[0] in 'UQLFD' and not p.get('noref'))
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
        fp.Reference().SetTextThickness(MM(0.12))
        for pad in fp.Pads():
            n = pad.GetNumber()
            if n and p['nets'].get(n):
                pad.SetNet(net(p['nets'][n]))

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

    for t in parts.TEXTS if hasattr(parts, 'TEXTS') else []:
        txt = pcbnew.PCB_TEXT(board)
        txt.SetText(t['text'])
        txt.SetPosition(V(t['x'], t['y']))
        txt.SetLayer(pcbnew.B_SilkS if t.get('back') else pcbnew.F_SilkS)
        sz = t.get('size', 1.0)
        txt.SetTextSize(pcbnew.VECTOR2I(MM(sz), MM(sz)))
        txt.SetTextThickness(MM(t.get('th', 0.15)))
        txt.SetTextAngleDegrees(t.get('rot', 0))
        if t.get('back'):
            txt.SetMirrored(True)
        just = t.get('just', 'c')
        txt.SetHorizJustify({'l': pcbnew.GR_TEXT_H_ALIGN_LEFT, 'r': pcbnew.GR_TEXT_H_ALIGN_RIGHT,
                             'c': pcbnew.GR_TEXT_H_ALIGN_CENTER}[just])
        board.Add(txt)

    pin1_dots(board)

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
    for netname, x, y in (getattr(parts, 'VIAS', []) if tracks else []):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y)); v.SetDrill(MM(0.3)); v.SetWidth(MM(0.6))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net(netname)); v.SetLocked(True)
        board.Add(v)

    ds = board.GetDesignSettings()
    ds.m_MinClearance = MM(0.15)
    ds.m_TrackMinWidth = MM(0.2)
    ds.m_ViasMinSize = MM(0.5)
    ds.m_CopperEdgeClearance = MM(0.4)
    ds.m_HoleClearance = MM(0.25)
    pcbnew.SaveBoard(path, board)
    write_project(path.replace('.kicad_pcb', '.kicad_pro'))
    return path


POWER = ['+12V_IN', '+12V_F', '+12V', '+12V_MOT', 'MOT_A', 'MOT_B']
FIVE = ['+5V', '+5V_LED', '+5V_DEV', 'SW']


def write_project(path):
    cls = [
        {"name": "Default", "clearance": 0.15, "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Power12", "clearance": 0.3, "track_width": 1.0, "via_diameter": 0.9, "via_drill": 0.45,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Power5", "clearance": 0.25, "track_width": 0.8, "via_diameter": 0.8, "via_drill": 0.4,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Gnd", "clearance": 0.15, "track_width": 0.3, "via_diameter": 0.6, "via_drill": 0.3,
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
         "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
         "pcb_color": "rgba(0, 0, 0, 0.000)"},
    ]
    pats = [{"netclass": "Power12", "pattern": n} for n in POWER] + \
           [{"netclass": "Power5", "pattern": n} for n in FIVE] + [{"netclass": "Gnd", "pattern": "GND"}]
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
            "track_widths": [0.0, 0.25, 0.5, 0.8, 1.0, 1.5],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3},
                               {"diameter": 0.9, "drill": 0.45}],
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
