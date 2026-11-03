# Post-processing steps that keep the board DRC-clean in KiCad 7 and 9 (v1.1.1):
#  trim_silk       - clip footprint silk lines that run over / onto the board edge or the sensor slots
#  set_solid       - solid zone connection for selected GND pads (power pins with starved thermals)
#  remove_dangling - drop redundant router stubs that KiCad reports as "track has unconnected end"
#  stitch_islands  - GND vias into copper-pour islands that are only tied to a single pad
import math

import pcbnew
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

import checks

MM = pcbnew.FromMM
TM = pcbnew.ToMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


# ---------------------------------------------------------------- silk
def trim_silk(board, margin=0.2, log=print):
    """Clip footprint silk segments so they stay >= margin away from Edge.Cuts (outline + slots)."""
    region = checks.board_region(board)
    n_clip = n_del = n_new = 0
    for fp in board.GetFootprints():
        for g in list(fp.GraphicalItems()):
            if g.GetClass() != 'MGRAPHIC' or g.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                continue
            w = TM(g.GetWidth())
            inner = region.buffer(-(margin + w / 2))
            shape = checks.item_poly(g)
            if inner.buffer(w / 2 + 1e-4).contains(shape):
                continue
            if g.GetShape() != pcbnew.SHAPE_T_SEGMENT:
                fp.Remove(g)
                n_del += 1
                continue
            line = LineString([checks._pt(g.GetStart()), checks._pt(g.GetEnd())])
            parts = line.intersection(inner)
            pieces = [p for p in (parts.geoms if hasattr(parts, 'geoms') else [parts])
                      if p.geom_type == 'LineString' and p.length > 0.1]
            if not pieces:
                fp.Remove(g)
                n_del += 1
                continue
            (ax, ay), (bx, by) = pieces[0].coords[0], pieces[0].coords[-1]
            g.SetStart(V(ax, ay))
            g.SetEnd(V(bx, by))
            g.SetLocalCoord()
            n_clip += 1
            for p in pieces[1:]:
                s = pcbnew.FP_SHAPE(fp)
                s.SetShape(pcbnew.SHAPE_T_SEGMENT)
                s.SetLayer(g.GetLayer())
                s.SetWidth(g.GetWidth())
                (ax, ay), (bx, by) = p.coords[0], p.coords[-1]
                s.SetStart(V(ax, ay))
                s.SetEnd(V(bx, by))
                s.SetLocalCoord()
                fp.Add(s)
                n_new += 1
    log('silk: %d clipped, %d removed, %d split' % (n_clip, n_del, n_new))
    return n_clip, n_del, n_new


# ---------------------------------------------------------------- pads
def find_pad(board, label):
    ref, num = label.split('.')
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise SystemExit('no footprint ' + ref)
    pads = [p for p in fp.Pads() if p.GetNumber() == num]
    if not pads:
        raise SystemExit('no pad ' + label)
    return pads


def set_solid(board, labels):
    for lbl in labels:
        for pad in find_pad(board, lbl):
            pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)


# ---------------------------------------------------------------- dangling stubs
def remove_dangling(board, log=print):
    """Remove unlocked tracks with an unconnected end (same test the KiCad DRC uses).
    Aborts (restores) if a removal would create an unconnected item. Locked hand stubs: see trim_locked_stubs."""
    removed = []
    for _ in range(20):
        board.BuildConnectivity()
        conn = board.GetConnectivity()
        before = conn.GetUnconnectedCount(False)
        bad = [t for t in board.GetTracks()
               if t.Type() == pcbnew.PCB_TRACE_T and not t.IsLocked()
               and conn.TestTrackEndpointDangling(t, True)]
        if not bad:
            break
        for t in bad:
            removed.append((t.GetNetname(), checks._pt(t.GetStart()), checks._pt(t.GetEnd()),
                            TM(t.GetWidth()), t.GetLayer()))
            board.Remove(t)
        board.BuildConnectivity()
        if board.GetConnectivity().GetUnconnectedCount(False) > before:
            raise SystemExit('dangling removal broke connectivity: %s' % removed)
    for r in removed:
        log('removed dangling %s (%.3f,%.3f)-(%.3f,%.3f)' % (r[0], r[1][0], r[1][1], r[2][0], r[2][1]))
    return removed


def remove_duplicate_tracks(board, log=print):
    """Drop tracks / vias with identical geometry (the SES brings the locked pre-routes back a second time).
    Keeps the locked copy."""
    seen, dup = {}, []
    for t in list(board.GetTracks()):
        if t.Type() == pcbnew.PCB_TRACE_T:
            key = ('t', t.GetNetCode(), t.GetLayer(), t.GetWidth(), (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y))
            key2 = ('t', t.GetNetCode(), t.GetLayer(), t.GetWidth(), key[5], key[4])
        elif t.Type() == pcbnew.PCB_VIA_T:
            key = key2 = ('v', t.GetNetCode(), (t.GetPosition().x, t.GetPosition().y), t.GetWidth())
        else:
            continue
        other = seen.get(key) or seen.get(key2)
        if other is None:
            seen[key] = t
            continue
        victim = t if other.IsLocked() or not t.IsLocked() else other
        if victim is other:
            seen[key] = t
        dup.append(victim)
    for t in dup:
        board.Remove(t)
    if dup:
        log('removed %d duplicate tracks / vias' % len(dup))
    return len(dup)


def trim_locked_stubs(board, log=print):
    """v1.2: a locked hand-placed stub whose far end the router did not use (it joined somewhere along the stub)
    ends up with a dangling end. Shorten it to the last junction (track end, via or pad on the stub); remove it
    when nothing touches it at all. Aborts if that would create an unconnected item."""
    changed = []
    for _ in range(10):
        board.BuildConnectivity()
        conn = board.GetConnectivity()
        before = conn.GetUnconnectedCount(False)
        bad = [t for t in board.GetTracks()
               if t.Type() == pcbnew.PCB_TRACE_T and t.IsLocked() and conn.TestTrackEndpointDangling(t, True)]
        if not bad:
            break
        for t in bad:
            s, e = t.GetStart(), t.GetEnd()
            lay, net, half = t.GetLayer(), t.GetNetCode(), t.GetWidth() / 2.0
            seg = LineString([(s.x, s.y), (e.x, e.y)])
            s_dang = conn.TestTrackEndpointDangling(t, False) if hasattr(conn, 'TestTrackEndpointDangling') else False
            # junction candidates on the same net and layer: ends of other tracks, vias, pads
            pts = []
            for o in board.GetTracks():
                if o.m_Uuid == t.m_Uuid or o.GetNetCode() != net:   # SWIG wrappers differ, compare the UUID
                    continue
                if o.Type() == pcbnew.PCB_TRACE_T and o.GetLayer() == lay:
                    pts += [o.GetStart(), o.GetEnd()]
                elif o.Type() == pcbnew.PCB_VIA_T:
                    pts.append(o.GetPosition())
            for f in board.GetFootprints():
                for pd in f.Pads():
                    if pd.GetNetCode() == net and pd.IsOnLayer(lay):
                        pts.append(pd.GetPosition())
            on = [p for p in pts if seg.distance(Point(p.x, p.y)) <= half + 10]
            # which end is dangling? the one no junction point sits on
            def near(p, q):
                return math.hypot(p.x - q.x, p.y - q.y) <= half + 10
            s_ok = any(near(p, s) for p in on)
            e_ok = any(near(p, e) for p in on)
            if not on or (not s_ok and not e_ok):
                changed.append(('removed', net, _geo(t)))
                board.Remove(t)
                continue
            anchor, free = (s, e) if s_ok else (e, s)
            # last junction measured from the anchored end
            far = max(on, key=lambda p: math.hypot(p.x - anchor.x, p.y - anchor.y))
            if near(far, free):
                continue                       # both ends used: KiCad calls it dangling for another reason
            if anchor is s:
                t.SetEnd(far)
            else:
                t.SetStart(far)
            changed.append(('trimmed', net, _geo(t)))
        board.BuildConnectivity()
        if board.GetConnectivity().GetUnconnectedCount(False) > before:
            raise SystemExit('stub trim broke connectivity: %s' % changed)
    for c in changed:
        log('%s locked stub %s' % (c[0], c[1]))
    return changed


def _geo(t):
    s, e = t.GetStart(), t.GetEnd()
    return (t.GetNetname(), t.GetLayer(), t.GetWidth(), (s.x, s.y), (e.x, e.y))


def _live(board, geo):
    """Live track objects matching stored geometries (never reuse wrappers of removed items)."""
    want = set(geo)
    return [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and _geo(t) in want]


def _state(board):
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    dang = sum(1 for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and conn.TestTrackEndpointDangling(t, True))
    return conn.GetUnconnectedCount(False), dang


def remove_redundant(board, region=None, log=print, nets=None):
    """Remove autorouter (unlocked) track segments that only duplicate an existing connection: after removal
    the board is still fully connected and no track end is loose. Single segments, repeated until nothing
    changes (a 2-piece jog goes in 2 steps). region = (x0, y0, x1, y1) mm or None = whole board; nets = list of
    net names or None = all. Before the pour exists, use a region without pour (every GND track would look
    redundant inside a filled pour); after the pour is filled, nets=['GND'] drops the router's GND tracks that
    the pour makes unnecessary (v1.2), which frees the room for the thermal spokes."""
    removed = []
    while True:
        cands = [_geo(t) for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and not t.IsLocked()
                 and (nets is None or t.GetNetname() in nets)
                 and (region is None or all(region[0] <= x <= region[2] and region[1] <= y <= region[3]
                                            for x, y in (checks._pt(t.GetStart()), checks._pt(t.GetEnd()))))]
        changed = False
        for g in cands:
            before = _state(board)
            live = _live(board, [g])
            if not live:
                continue
            board.Remove(live[0])
            after = _state(board)
            if after[0] <= before[0] and after[1] <= before[1]:
                removed.append(g)
                changed = True
                log('removed duplicate %s track (%.3f,%.3f)-(%.3f,%.3f)' % (g[0], TM(g[3][0]), TM(g[3][1]),
                                                                          TM(g[4][0]), TM(g[4][1])))
                continue
            t = pcbnew.PCB_TRACK(board)                     # needed: put it back
            t.SetStart(pcbnew.VECTOR2I(*g[3]))
            t.SetEnd(pcbnew.VECTOR2I(*g[4]))
            t.SetWidth(g[2])
            t.SetLayer(g[1])
            t.SetNet(board.FindNet(g[0]))
            board.Add(t)
        if not changed:
            break
    board.BuildConnectivity()
    return removed


# ---------------------------------------------------------------- stitching vias
def _holes(board):
    out = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.HasHole():
                d = max(TM(pad.GetDrillSizeX()), TM(pad.GetDrillSizeY()))
                out.append(Point(checks._pt(pad.GetPosition())).buffer(d / 2))
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            out.append(Point(checks._pt(t.GetPosition())).buffer(TM(t.GetDrillValue()) / 2))
    return unary_union(out)


def robust_fill(polys, neck=0.25, min_area=20.0):
    """Pour without necks narrower than 2*neck and without small pieces: what any zone filler keeps."""
    u = unary_union(polys)
    op = u.buffer(-neck).buffer(neck)
    comps = list(op.geoms) if op.geom_type == 'MultiPolygon' else ([op] if not op.is_empty else [])
    return unary_union([c for c in comps if c.area >= min_area])


def _obstacles(board, r, drill, silk=True):
    pads = unary_union([checks.item_poly(p) for fp in board.GetFootprints() for p in fp.Pads()])
    tracks = unary_union([checks.item_poly(t) for t in board.GetTracks() if t.Type() != pcbnew.PCB_VIA_T])
    vias = unary_union([checks.item_poly(t) for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T])
    crt = []
    for fp in board.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE:
            continue
        for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            cy = fp.GetCourtyard(layer)
            if cy.OutlineCount():
                crt.append(checks.polyset_to_shapely(cy))
    parts = [pads.buffer(r + 0.3), tracks.buffer(r + 0.2), vias.buffer(r + 1.0),
             _holes(board).buffer(drill / 2 + 0.3), unary_union(crt).buffer(r) if crt else Point(-99, -99),
             checks.via_keepouts(board).buffer(r + 0.05)]            # v1.2: no vias under protected silk
    if silk:
        parts.append(unary_union([p for _, _, p in checks.silk_shapes(board)]).buffer(r + 0.1))
    return unary_union(parts)


def _label(c):
    k, o = c[0], c[1]
    return '%s.%s' % (o.GetParent().GetReference(), o.GetNumber()) if k == 'pad' else k


def island_targets(board, min_area=1.5, neck=0.25):
    """Pour regions tied to a single item: real islands of this fill, plus regions that hang on a neck
    narrower than 2*neck (another zone filler, e.g. KiCad 9/10 on refill, may cut those necks)."""
    isl = checks.islands(board)
    targets = []
    for (z, layer), (sp, conns) in isl.items():
        items = checks.gnd_items(board, layer)
        for poly, c in zip(sp, conns):
            if len(c) == 1 and poly.area >= min_area:
                targets.append((layer, poly, _label(c[0]), 'island'))
            op = poly.buffer(-neck).buffer(neck)
            comps = list(op.geoms) if op.geom_type == 'MultiPolygon' else []
            for comp in comps:
                cc = [it for it in items if comp.intersects(it[2]) or comp.covers(it[3])]
                if len(cc) == 1 and cc[0][0] == 'pad' and comp.area >= min_area:
                    targets.append((layer, comp, _label(cc[0]), 'neck'))
    return isl, targets


def stitch_islands(board, via_d=0.6, drill=0.3, min_area=1.5, per_area=40.0, max_per=6, log=print):
    """GND vias into every pour region that only connects to one item (KiCad 8+ ignore thermal spokes
    into such islands), so the region is tied to the other layer's pour."""
    r = via_d / 2
    isl, targets = island_targets(board, min_area)
    if not targets:
        return []
    # the via's cluster always contains the region's pad, so any (locally wide) pour piece on the
    # other layer is fine here - no robust_fill() needed (unlike stitch_grid)
    fills = {}
    for (z, layer), (sp, conns) in isl.items():
        fills.setdefault(layer, []).extend(sp)
    fills = {l: unary_union(v) for l, v in fills.items()}
    edge_ok = checks.board_region(board).buffer(-(r + 1.0))
    blocked = {True: _obstacles(board, r, drill, True), False: None}
    gnd = board.FindNet('GND')
    added = []
    for layer, poly, lbl, kind in targets:
        other = fills.get(pcbnew.B_Cu if layer == pcbnew.F_Cu else pcbnew.F_Cu)
        if other is None or other.is_empty:
            continue
        base = poly.buffer(-(r + 0.1)).intersection(other.buffer(-(r + 0.15))).intersection(edge_ok)
        ok = base.difference(blocked[True])
        if ok.is_empty:                                   # last resort: allow a (tented) via under silk
            if blocked[False] is None:
                blocked[False] = _obstacles(board, r, drill, False)
            ok = base.difference(blocked[False])
        if ok.is_empty:
            log('%s %s (%s, %.1f mm2): no via position' % (kind, board.GetLayerName(layer), lbl, poly.area))
            continue
        want = max(1, min(max_per, int(math.ceil(poly.area / per_area))))
        x0, y0, x1, y1 = ok.bounds
        cand = [Point(round(x0 + 0.05 * a, 2), round(y0 + 0.05 * b, 2))
                for a in range(int((x1 - x0) / 0.05) + 1) for b in range(int((y1 - y0) / 0.05) + 1)]
        cand = [p for p in cand if ok.contains(p)]
        if not cand:
            continue
        # first via: the spot deepest inside the allowed area (most margin), then spread out
        picks = [max(cand, key=lambda p: ok.exterior.distance(p) if ok.geom_type == 'Polygon'
                     else ok.boundary.distance(p))]
        while len(picks) < want:
            best = max(cand, key=lambda p: min(p.distance(q) for q in picks))
            if min(best.distance(q) for q in picks) < 3.0:
                break
            picks.append(best)
        for p in picks:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(V(p.x, p.y))
            v.SetDrill(MM(drill))
            v.SetWidth(MM(via_d))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(gnd)
            v.SetLocked(True)
            board.Add(v)
            added.append((board.GetLayerName(layer), lbl, p.x, p.y))
            blocked[True] = blocked[True].union(p.buffer(r + 1.0 + r))
            if blocked[False] is not None:
                blocked[False] = blocked[False].union(p.buffer(r + 1.0 + r))
        log('%s %s (%s, %.1f mm2): %d via(s) %s' % (kind, board.GetLayerName(layer), lbl, poly.area, len(picks),
                                                  [(p.x, p.y) for p in picks]))
    return added


def stitch_grid(board, pitch=6.0, search=1.5, via_d=0.6, drill=0.3, log=print):
    """General GND stitching: a via near every node of a staggered grid where it fits inside the GND pour
    of BOTH layers (keeps the two pours tied together, independent of small zone-filler differences)."""
    from shapely.ops import nearest_points
    r = via_d / 2
    isl = checks.islands(board)
    fills = {}
    for (z, layer), (sp, conns) in isl.items():
        fills.setdefault(layer, []).extend(sp)
    if pcbnew.F_Cu not in fills or pcbnew.B_Cu not in fills:
        return []
    both = robust_fill(fills[pcbnew.F_Cu]).intersection(robust_fill(fills[pcbnew.B_Cu]))
    pads = unary_union([checks.item_poly(p) for fp in board.GetFootprints() for p in fp.Pads()])
    tracks = unary_union([checks.item_poly(t) for t in board.GetTracks() if t.Type() != pcbnew.PCB_VIA_T])
    vias = [checks.item_poly(t) for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    silk = unary_union([p for _, _, p in checks.silk_shapes(board)])
    crt = []
    for fp in board.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE:
            continue
        for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            cy = fp.GetCourtyard(layer)
            if cy.OutlineCount():
                crt.append(checks.polyset_to_shapely(cy))
    blocked = unary_union([pads.buffer(r + 0.3), tracks.buffer(r + 0.2), unary_union(vias).buffer(r + 1.0),
                           _holes(board).buffer(drill / 2 + 0.3), silk.buffer(r + 0.1),
                           checks.via_keepouts(board).buffer(r + 0.05),
                           unary_union(crt).buffer(r) if crt else Point(-99, -99)])
    ok = both.buffer(-(r + 0.15)).intersection(checks.board_region(board).buffer(-(r + 1.0))).difference(blocked)
    gnd = board.FindNet('GND')
    added = []
    rows = int(100 / (pitch * 0.866)) + 2
    for j in range(rows):
        y = 2.0 + j * pitch * 0.866
        x0 = 2.0 + (pitch / 2 if j % 2 else 0.0)
        x = x0
        while x < 100:
            g = Point(x, y)
            x += pitch
            near = ok.intersection(g.buffer(search))
            if near.is_empty:
                continue
            p = g if near.contains(g) else nearest_points(near, g)[0]
            p = Point(round(p.x, 2), round(p.y, 2))
            if not ok.buffer(0.004).contains(p):
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(V(p.x, p.y))
            v.SetDrill(MM(drill))
            v.SetWidth(MM(via_d))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(gnd)
            v.SetLocked(True)
            board.Add(v)
            added.append((p.x, p.y))
            ok = ok.difference(p.buffer(via_d + 1.0))
    log('grid stitching: %d vias (pitch %.1f mm)' % (len(added), pitch))
    return added


def via_margins(board):
    """Smallest distance (mm) between a GND via's copper edge and the pour edge, per via, worst first."""
    fills = {}
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != 'GND':
            continue
        for l in z.GetLayerSet().CuStack():
            fills[l] = unary_union(checks.subpolys(z.GetFilledPolysList(l)))
    out = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND':
            p = Point(checks._pt(t.GetPosition()))
            r = TM(t.GetWidth()) / 2
            m = min((f.boundary.distance(p) if f.contains(p) else -f.distance(p)) for f in fills.values()) - r
            out.append((round(m, 3), round(p.x, 2), round(p.y, 2), t.IsLocked()))
    return sorted(out)


def refill(board):
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


# ---------------------------------------------------------------- v1.2: thermal spokes by hand
def fix_starved(board, starved, isl=None, width=0.4, log=print):
    """For every GND pad the KiCad check reports with < 2 spokes: add a short locked GND track from the pad
    into the pour (a track counts as a spoke for the DRC). 8 directions are tried; the stub must stay clear
    (0.25 mm) of other copper on that layer and end inside the current fill. SMD pads with no free direction
    fall back to a solid zone connection. Returns the number of pads fixed."""
    import math
    isl = isl or checks.islands(board)
    region = checks.board_region(board).buffer(-0.4)
    fixed = 0
    done = set()
    for entry in starved:
        label, lname = entry[0], entry[1]
        if (label, lname) in done:
            continue
        done.add((label, lname))
        layer = board.GetLayerID(lname)
        pads = find_pad(board, label)
        if not pads:
            continue
        pad = pads[0]
        fills = [unary_union(sp) for (z, ly), (sp, _) in isl.items() if ly == layer]
        fill = unary_union(fills) if fills else None
        pp = checks.item_poly(pad)
        cx, cy = checks._pt(pad.GetPosition())
        others = unary_union([checks.item_poly(p) for fp in board.GetFootprints() for p in fp.Pads()
                              if p.GetNetname() != 'GND' and p.IsOnLayer(layer)] +
                             [checks.item_poly(t) for t in board.GetTracks()
                              if t.GetNetname() != 'GND' and t.IsOnLayer(layer)])
        half = max(TM(pad.GetSize().x), TM(pad.GetSize().y)) / 2
        best = None
        for k in range(8):
            a = math.radians(45 * k)
            L = half + 1.4
            ex, ey = cx + L * math.cos(a), cy + L * math.sin(a)
            stub = LineString([(cx, cy), (ex, ey)]).buffer(width / 2)
            if not region.covers(stub):
                continue
            if stub.buffer(0.25).intersects(others):
                continue
            if fill is not None and not fill.covers(Point(ex, ey)):
                continue
            best = (ex, ey)
            break
        if best is None:
            if not pad.HasHole():
                pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
                log('spoke %s %s: no free direction -> solid pad' % (label, lname))
                fixed += 1
            else:
                log('spoke %s %s: no free direction, left as is' % (label, lname))
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(best[0]), pcbnew.FromMM(best[1])))
        t.SetWidth(pcbnew.FromMM(width))
        t.SetLayer(layer)
        t.SetNet(board.FindNet('GND'))
        t.SetLocked(True)
        board.Add(t)
        log('spoke %s %s: stub to (%.2f, %.2f)' % (label, lname, best[0], best[1]))
        fixed += 1
    if fixed:
        board.BuildConnectivity()
    return fixed
