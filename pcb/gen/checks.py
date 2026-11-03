# Extra board checks that emulate KiCad 9 DRC details KiCad 7 doesn't report:
#  - silk items touching / crossing Edge.Cuts (incl. slots)
#  - GND zone "single connection" islands (KiCad 8/9 isolated-island logic)
#  - thermal spokes per pad, ignoring spokes into single-connection islands
import pcbnew
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

TM = pcbnew.ToMM
ARC_ERR = pcbnew.FromMM(0.005)


def _ring(chain):
    return [(TM(chain.CPoint(i).x), TM(chain.CPoint(i).y)) for i in range(chain.PointCount())]


def polyset_to_shapely(ps):
    """SHAPE_POLY_SET -> shapely (Multi)Polygon, holes kept (unfractures first)."""
    ps = pcbnew.SHAPE_POLY_SET(ps)
    if not any(ps.HoleCount(i) for i in range(ps.OutlineCount())):
        ps.Unfracture(pcbnew.SHAPE_POLY_SET.PM_FAST)     # zone fills are stored fractured (slits, no holes)
    polys = []
    for i in range(ps.OutlineCount()):
        outer = _ring(ps.Outline(i))
        holes = [_ring(ps.Hole(i, h)) for h in range(ps.HoleCount(i))]
        if len(outer) >= 3:
            polys.append(Polygon(outer, holes).buffer(0))
    return unary_union(polys) if polys else Polygon()


def subpolys(ps):
    """Fill SHAPE_POLY_SET -> list of shapely Polygons, one per KiCad sub-polygon (outline index)."""
    out = []
    for i in range(ps.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(ps.Outline(i))
        for h in range(ps.HoleCount(i)):
            one.AddHole(ps.Hole(i, h))
        out.append(polyset_to_shapely(one))
    return out


def _pt(v):
    return (TM(v.x), TM(v.y))


def _arc_pts(a, m, e, n=24):
    """Points along the arc through a (start), m (mid), e (end)."""
    import math
    (x1, y1), (x2, y2), (x3, y3) = a, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return [a, e]
    ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    t1, t2, t3 = (math.atan2(y - uy, x - ux) for x, y in (a, m, e))
    def norm(t):
        return t % (2 * math.pi)
    s, mm, en = norm(t1), norm(t2 - t1), norm(t3 - t1)
    sweep = en if mm < en else en - 2 * math.pi       # go through the mid point
    return [(ux + r * math.cos(t1 + sweep * i / n), uy + r * math.sin(t1 + sweep * i / n)) for i in range(n + 1)]


def item_poly(item, layer=None, inflate=0.0):
    """Shapely polygon of a board item's copper / graphic shape (+ inflate mm)."""
    t = item.Type()
    if t == pcbnew.PCB_PAD_T:
        return polyset_to_shapely(item.GetEffectivePolygon()).buffer(inflate) if inflate else \
            polyset_to_shapely(item.GetEffectivePolygon())
    if t == pcbnew.PCB_VIA_T:
        return Point(_pt(item.GetPosition())).buffer(TM(item.GetWidth()) / 2 + inflate)
    if t == pcbnew.PCB_TRACE_T:
        return LineString([_pt(item.GetStart()), _pt(item.GetEnd())]).buffer(TM(item.GetWidth()) / 2 + inflate)
    if t == pcbnew.PCB_ARC_T:
        return LineString(_arc_pts(_pt(item.GetStart()), _pt(item.GetMid()), _pt(item.GetEnd()))).buffer(
            TM(item.GetWidth()) / 2 + inflate)
    if hasattr(item, 'GetShape'):
        w = TM(item.GetWidth()) / 2 + inflate
        sh = item.GetShape()
        if sh == pcbnew.SHAPE_T_SEGMENT:
            return LineString([_pt(item.GetStart()), _pt(item.GetEnd())]).buffer(max(w, 1e-4))
        if sh == pcbnew.SHAPE_T_ARC:
            return LineString(_arc_pts(_pt(item.GetStart()), _pt(item.GetArcMid()), _pt(item.GetEnd()))).buffer(max(w, 1e-4))
        if sh == pcbnew.SHAPE_T_CIRCLE:
            c, r = Point(_pt(item.GetCenter())), TM(item.GetRadius())
            if item.IsFilled():
                return c.buffer(r + w)
            return c.buffer(r + w).difference(c.buffer(max(r - w, 0)))
        if sh == pcbnew.SHAPE_T_RECT:
            pts = [_pt(v) for v in item.GetRectCorners()]
            p = Polygon(pts)
            return p.buffer(w) if item.IsFilled() else p.exterior.buffer(max(w, 1e-4))
        if sh == pcbnew.SHAPE_T_POLY:
            p = polyset_to_shapely(item.GetPolyShape())
            return p.buffer(w) if item.IsFilled() else p.boundary.buffer(max(w, 1e-4))
    bb = item.GetBoundingBox()           # texts etc.
    return Polygon([(TM(bb.GetX()), TM(bb.GetY())), (TM(bb.GetRight()), TM(bb.GetY())),
                    (TM(bb.GetRight()), TM(bb.GetBottom())), (TM(bb.GetX()), TM(bb.GetBottom()))]).buffer(inflate)


def board_edges(board):
    """Edge.Cuts centre lines (outline + slots), stroke width 0 like the KiCad DRC uses them."""
    lines = []
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        sh = d.GetShape()
        if sh == pcbnew.SHAPE_T_SEGMENT:
            lines.append(LineString([_pt(d.GetStart()), _pt(d.GetEnd())]))
        elif sh == pcbnew.SHAPE_T_ARC:
            lines.append(LineString(_arc_pts(_pt(d.GetStart()), _pt(d.GetArcMid()), _pt(d.GetEnd()))))
        elif sh == pcbnew.SHAPE_T_CIRCLE:
            lines.append(Point(_pt(d.GetCenter())).buffer(TM(d.GetRadius())).exterior)
        else:
            lines.append(item_poly(d).boundary)
    return unary_union(lines)


def board_region(board):
    """Board area (outline minus slots / cut-outs) as a shapely polygon."""
    ps = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(ps)
    return polyset_to_shapely(ps)


def silk_shapes(board):
    """[(ref, item, shapely shape)] for visible silk graphics / texts (board + footprints)."""
    items = [(d, '-') for d in board.GetDrawings()]
    for fp in board.GetFootprints():
        items += [(g, fp.GetReference()) for g in fp.GraphicalItems()]
        items += [(fp.Reference(), fp.GetReference()), (fp.Value(), fp.GetReference())]
    out = []
    for it, ref in items:
        lay = it.GetLayer()
        if lay not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        if hasattr(it, 'IsVisible') and not it.IsVisible():
            continue
        p = item_poly(it, lay)
        if not p.is_empty:
            out.append((ref, it, p))
    return out


def silk_edge(board, clr=0.0):
    """Silk items closer than clr to an Edge.Cuts centre line (KiCad: silk_edge_clearance)."""
    edges = board_edges(board)
    return [(ref, it) for ref, it, p in silk_shapes(board) if p.distance(edges) <= clr + 1e-6]


def gnd_items(board, layer):
    """GND pads / vias / tracks present on a copper layer: list of (kind, obj, shapely shape, anchor)."""
    out = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == 'GND' and pad.IsOnLayer(layer) and pad.FlashLayer(layer):
                pos = pad.GetPosition()
                out.append(('pad', pad, item_poly(pad, layer), Point(TM(pos.x), TM(pos.y))))
    for t in board.GetTracks():
        if t.GetNetname() != 'GND' or not t.IsOnLayer(layer):
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            pos = t.GetPosition()
            out.append(('via', t, item_poly(t, layer), Point(TM(pos.x), TM(pos.y))))
        else:
            s = t.GetStart()
            out.append(('track', t, item_poly(t, layer), Point(TM(s.x), TM(s.y))))
    return out


def islands(board):
    """{(zone, layer): (subpolys, [connected item lists])} for GND zones."""
    res = {}
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != 'GND':
            continue
        for layer in z.GetLayerSet().CuStack():
            fill = z.GetFilledPolysList(layer)
            sp = subpolys(fill)
            items = gnd_items(board, layer)
            conns = []
            for poly in sp:
                c = [it for it in items if poly.intersects(it[2]) or poly.covers(it[3])]
                conns.append(c)
            res[(z, layer)] = (sp, conns)
    return res


def thermals(board, isl=None, min_spokes=2):
    """KiCad 9-style starved-thermal check. Returns list of (pad label, layer, spokes, ignored)."""
    isl = isl or islands(board)
    bad = []
    for (z, layer), (sp, conns) in isl.items():
        gap = TM(z.GetThermalReliefGap())
        single = {i for i, c in enumerate(conns) if len(c) == 1}
        fill_all = unary_union(sp)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() != 'GND' or not pad.FlashLayer(layer):
                    continue
                conn = pad.GetZoneConnection()
                if conn == pcbnew.ZONE_CONNECTION_INHERITED:
                    conn = fp.GetZoneConnection()
                if conn == pcbnew.ZONE_CONNECTION_INHERITED:
                    conn = z.GetPadConnection()
                if conn != pcbnew.ZONE_CONNECTION_THERMAL:
                    continue
                ring = item_poly(pad, layer, gap / 2)
                if ring.is_empty:
                    continue
                ring = ring.exterior if ring.geom_type == 'Polygon' else ring.convex_hull.exterior
                spokes = ignored = 0
                for i, poly in enumerate(sp):
                    x = ring.intersection(poly.boundary)
                    n = 0 if x.is_empty else (len(x.geoms) if hasattr(x, 'geoms') else 1)
                    if n >= 2:
                        if i in single:
                            ignored += n // 2
                        else:
                            spokes += n // 2
                if spokes == 0 and ignored == 0:
                    continue
                if spokes < min_spokes:
                    ringpoly = Polygon(ring)
                    for t in board.GetTracks():
                        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'GND' or t.GetLayer() != layer:
                            continue
                        s, e = t.GetStart(), t.GetEnd()
                        ps, pe = Point(TM(s.x), TM(s.y)), Point(TM(e.x), TM(e.y))
                        on_pad = item_poly(pad, layer)
                        if not (on_pad.covers(ps) or on_pad.covers(pe)):
                            continue
                        if ringpoly.covers(ps) and fill_all.covers(pe):
                            spokes += 1
                        elif ringpoly.covers(pe) and fill_all.covers(ps):
                            spokes += 1
                if spokes == 0:
                    spokes, ignored = ignored, 0
                if spokes < min_spokes:
                    lbl = '%s.%s' % (fp.GetReference(), pad.GetNumber())
                    bad.append((lbl, board.GetLayerName(layer), spokes, ignored, pad))
    return bad


def single_islands(isl):
    out = []
    for (z, layer), (sp, conns) in isl.items():
        for i, c in enumerate(conns):
            if len(c) == 1:
                kind, obj = c[0][0], c[0][1]
                lbl = ('%s.%s' % (obj.GetParent().GetReference(), obj.GetNumber())) if kind == 'pad' else kind
                out.append((pcbnew.LayerName(layer) if hasattr(pcbnew, 'LayerName') else layer, i, lbl,
                            round(sp[i].area, 3), sp[i]))
    return out


if __name__ == '__main__':
    import sys
    b = pcbnew.LoadBoard(sys.argv[1])
    for ref, it in silk_edge(b):
        bb = it.GetBoundingBox()
        print('SILK', ref, it.GetClass(), '(%.2f,%.2f)-(%.2f,%.2f)' % (TM(bb.GetX()), TM(bb.GetY()), TM(bb.GetRight()), TM(bb.GetBottom())))
    isl = islands(b)
    for l in single_islands(isl):
        print('SINGLE-ISLAND', l[:4])
    for t in thermals(b, isl):
        print('THERMAL', t[:4])


# ---- exact emulation of the KiCad 7 / 9 starved-thermal test (fractured outlines, raw segment intersections) ----
def _chain_pts(chain):
    pts = [(chain.CPoint(i).x, chain.CPoint(i).y) for i in range(chain.PointCount())]
    if chain.IsClosed() and pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def _seg_x(a, b, c, d):
    """Intersection test of segments ab, cd (integer nm). Collinear -> False (aExcludeColinearAndTouching)."""
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1, d2 = cross(c, d, a), cross(c, d, b)
    d3, d4 = cross(a, b, c), cross(a, b, d)
    if d1 == 0 and d2 == 0:
        return False                                   # collinear
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0) or d1 == 0 or d2 == 0) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0) or d3 == 0 or d4 == 0):
        return True
    return False


def _count_x(chain_pts, ring_pts, bbox):
    x0, y0, x1, y1 = bbox
    n = 0
    for a, b in zip(chain_pts[:-1], chain_pts[1:]):
        if max(a[0], b[0]) < x0 or min(a[0], b[0]) > x1 or max(a[1], b[1]) < y0 or min(a[1], b[1]) > y1:
            continue
        for c, d in zip(ring_pts[:-1], ring_pts[1:]):
            if _seg_x(a, b, c, d):
                n += 1
    return n


def thermals_exact(board, version=9, min_spokes=2, isl=None):
    isl = isl or islands(board)
    res = []
    MMi = pcbnew.FromMM
    for (z, layer), (sp, conns) in isl.items():
        single = {i for i, c in enumerate(conns) if len(c) == 1}
        fill = z.GetFilledPolysList(layer)
        chains = [_chain_pts(fill.Outline(j)) for j in range(fill.OutlineCount())]
        mid_gap = TM(z.GetThermalReliefGap()) / 2
        fill_shp = unary_union(sp)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() != 'GND' or not pad.FlashLayer(layer):
                    continue
                conn = pad.GetZoneConnection()
                if conn == pcbnew.ZONE_CONNECTION_INHERITED:
                    conn = fp.GetZoneConnection()
                if conn == pcbnew.ZONE_CONNECTION_INHERITED:
                    conn = z.GetPadConnection()
                if conn != pcbnew.ZONE_CONNECTION_THERMAL:
                    continue
                pp = polyset_to_shapely(pad.GetEffectivePolygon()).buffer(mid_gap, quad_segs=8)
                ring = [(MMi(x), MMi(y)) for x, y in pp.exterior.coords]
                xs, ys = [p[0] for p in ring], [p[1] for p in ring]
                bbox = (min(xs), min(ys), max(xs), max(ys))
                spokes = ignored = 0
                per = []
                for j, ch in enumerate(chains):
                    n = _count_x(ch, ring, bbox)
                    if version == 7:
                        if j in single:
                            continue
                        spokes += n           # summed, halved below
                        continue
                    if n >= 2:
                        per.append((j, n, j in single))
                        if j in single:
                            ignored += n // 2
                        else:
                            spokes += n // 2
                if version == 7:
                    spokes //= 2
                    if spokes <= 0 or spokes >= min_spokes:
                        continue
                else:
                    if spokes == 0 and ignored == 0:
                        continue
                    if spokes >= min_spokes:
                        continue
                # manual spokes
                padshape = polyset_to_shapely(pad.GetEffectivePolygon())
                for t in board.GetTracks():
                    # KiCad quirk: tracks on ANY layer connected to the pad count as manual spokes
                    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'GND' or not pad.IsOnLayer(t.GetLayer()):
                        continue
                    s, e = Point(_pt(t.GetStart())), Point(_pt(t.GetEnd()))
                    if not (padshape.buffer(TM(t.GetWidth()) / 2).covers(s) or padshape.buffer(TM(t.GetWidth()) / 2).covers(e)):
                        continue                       # not connected to this pad
                    if pp.covers(s):
                        if fill_shp.covers(e):
                            spokes += 1
                    elif pp.covers(e):
                        if fill_shp.covers(s):
                            spokes += 1
                if version == 9 and spokes == 0:
                    spokes, ignored = ignored, 0
                if spokes < min_spokes:
                    lbl = '%s.%s' % (fp.GetReference(), pad.GetNumber())
                    res.append((lbl, board.GetLayerName(layer), spokes, ignored, per))
    return res


# ---------------- v1.2: silkscreen text rules (JLCPCB: 0.15 mm pad to silk, text >= 1.0 mm) ----------------
SIDES = {'F': (pcbnew.F_SilkS, pcbnew.F_Mask, pcbnew.F_CrtYd), 'B': (pcbnew.B_SilkS, pcbnew.B_Mask, pcbnew.B_CrtYd)}


def is_text(item):
    return hasattr(item, 'GetShownText')


def text_ink(item):
    """Rectangle around the printed strokes of a text (KiCad's own text bbox adds line spacing above / below)."""
    bb = item.GetEffectiveTextShape().BBox()
    return Polygon([(TM(bb.GetX()), TM(bb.GetY())), (TM(bb.GetRight()), TM(bb.GetY())),
                    (TM(bb.GetRight()), TM(bb.GetBottom())), (TM(bb.GetX()), TM(bb.GetBottom()))])


def silk_geoms(board):
    """silk_shapes() with texts as their ink rectangle."""
    return [(ref, it, text_ink(it) if is_text(it) else p) for ref, it, p in silk_shapes(board)]


def is_qr(item):
    """QR modules: filled rectangles on a silk layer (build.draw_qr)."""
    return item.Type() in (pcbnew.PCB_SHAPE_T,) and item.GetShape() == pcbnew.SHAPE_T_RECT and item.IsFilled()


def silk_env(board, side):
    """Obstacles for silk on one side: exposed pads (+ mask margin + 0.15 mm), part courtyards, board area."""
    silk, mask, crt = SIDES[side]
    pads, yards = [], []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.IsOnLayer(mask):
                m = max(0.05, TM(pad.GetLocalSolderMaskMargin()))
                pads.append(('%s.%s' % (fp.GetReference(), pad.GetNumber()), item_poly(pad).buffer(m + 0.15)))
        cy = fp.GetCourtyard(crt)
        if cy.OutlineCount():
            yards.append((fp.GetReference(), polyset_to_shapely(cy)))
    for v in board.GetTracks():                  # via holes: JLCPCB clips silk there (even when tented)
        if v.Type() == pcbnew.PCB_VIA_T:
            pads.append(('via %s' % v.GetNetname(), item_poly(v).buffer(0.1)))
    region = board_region(board).buffer(-0.3)
    return pads, yards, region


def text_conflicts(poly, pads, yards, region, silk_items, own_ref=None, self_item=None, gap=0.15):
    """What a silk text / QR polygon collides with: [str]."""
    out = []
    if not region.contains(poly):
        out.append('board edge')
    out += ['pad ' + n for n, p in pads if poly.intersects(p)]
    out += ['courtyard ' + r for r, p in yards if poly.intersection(p).area > 0.02]
    me = self_item.m_Uuid.AsString() if self_item is not None else None
    for ref, it, p in silk_items:
        if me is not None and it.m_Uuid.AsString() == me:          # SWIG wrappers differ: compare the UUID
            continue
        if self_item is not None and is_qr(self_item) and is_qr(it):
            continue
        if poly.distance(p) < gap:
            out.append('silk %s %s' % (ref, it.GetShownText() if is_text(it) else it.GetClass()))
    return out


def via_keepouts(board):
    """Union of all rule areas that forbid vias (SHT40 slot keep-outs, via keep-outs under silk)."""
    polys = [polyset_to_shapely(z.Outline()) for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    return unary_union(polys) if polys else Polygon()


def silk_text_conflicts(board):
    """Every visible silk text and the QR code: clear of pads, other silk, courtyards and the board edge.
    Returns [(side, ref, text, [conflicts])]."""
    shapes = silk_geoms(board)
    vk = via_keepouts(board)
    res = []
    for side, (silk, _, _) in SIDES.items():
        pads, yards, region = silk_env(board, side)
        items = [s for s in shapes if s[1].GetLayer() == silk]
        qr = unary_union([p for _, it, p in items if is_qr(it)])
        for ref, it, p in items:
            if not is_text(it):
                continue
            c = text_conflicts(p, pads, yards, region, [s for s in items if not is_qr(s[1])], self_item=it)
            if not p.difference(vk).area < 0.01 * p.area:     # text without a via keep-out: a via there is
                c = [x for x in c if not x.startswith('pad via')]   # only cosmetic (JLC clips the silk at the hole)
            if not qr.is_empty and p.distance(qr) < 1.2:      # keep a quiet zone of ~2 modules around the QR
                c.append('QR quiet zone')
            if c:
                res.append((side, ref, it.GetShownText(), c))
        if not qr.is_empty:
            c = text_conflicts(qr, pads, yards, region, [s for s in items if not is_qr(s[1]) and not is_text(s[1])],
                               self_item=None)
            if c:
                res.append((side, 'QR', 'QR code', c))
    return res
