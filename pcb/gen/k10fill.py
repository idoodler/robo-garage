# Apply the zone fill of a KiCad 9/10-saved board (text-parsed) to our KiCad 7 board, then run the
# KiCad 9/10 thermal / island emulation. Usage: k10fill.py <kicad7 board> <kicad10 board>
import sys
import pcbnew
import checks
from ses import parse_sexpr, find

MM = pcbnew.FromMM


def k10_fills(path):
    tree = parse_sexpr(open(path, encoding='utf-8').read())
    out = {}          # (net, layer) -> [ [ (x,y), ... ], ... ]
    for z in find(tree, 'zone'):
        net = next((n[1] for n in find(z, 'net_name')), None)
        if net is None:
            net = next((n[1] for n in find(z, 'net') if len(n) > 1 and not str(n[1]).lstrip('-').isdigit()), None)
        for fp in find(z, 'filled_polygon'):
            layer = next(find(fp, 'layer'))[1]
            pts = next(find(fp, 'pts'))
            poly = [(float(p[1]), float(p[2])) for p in pts if isinstance(p, list) and p[0] == 'xy']
            out.setdefault((net, layer), []).append(poly)
    return out


def apply(board, fills):
    names = {pcbnew.F_Cu: 'F.Cu', pcbnew.B_Cu: 'B.Cu'}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for layer in z.GetLayerSet().CuStack():
            polys = fills.get((z.GetNetname(), names[layer]), [])
            ps = pcbnew.SHAPE_POLY_SET()
            for poly in polys:
                ch = pcbnew.SHAPE_LINE_CHAIN()
                for x, y in poly:
                    ch.Append(MM(x), MM(y))
                ch.SetClosed(True)
                ps.AddOutline(ch)
            z.SetFilledPolysList(layer, ps)
            print(z.GetNetname(), names[layer], 'subpolys', ps.OutlineCount())


if __name__ == '__main__':
    b = pcbnew.LoadBoard(sys.argv[1])
    fills = k10_fills(sys.argv[2])
    print({k: len(v) for k, v in fills.items()})
    apply(b, fills)
    isl = checks.islands(b)
    for s in checks.single_islands(isl):
        print('single island', s[:4])
    for v in (7, 9):
        print('KiCad', v, [t[:4] for t in checks.thermals_exact(b, v, isl=isl)])
