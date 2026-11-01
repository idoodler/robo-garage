import pcbnew, sys
FP='/usr/share/kicad/footprints/'
def info(lib, name):
    f = pcbnew.FootprintLoad(FP + lib + '.pretty', name)
    if f is None:
        print('MISSING', lib, name); return
    mm = pcbnew.ToMM
    bb = f.GetCourtyard(pcbnew.F_CrtYd).BBox() if not f.GetCourtyard(pcbnew.F_CrtYd).IsEmpty() else f.GetBoundingBox()
    print(f'== {lib}:{name}  courtyard x[{mm(bb.GetLeft()):.2f},{mm(bb.GetRight()):.2f}] y[{mm(bb.GetTop()):.2f},{mm(bb.GetBottom()):.2f}]')
    for p in f.Pads():
        pos = p.GetPosition(); sz = p.GetSize()
        print(f'   pad {p.GetNumber():>3} @({mm(pos.x):6.2f},{mm(pos.y):6.2f}) size {mm(sz.x):.2f}x{mm(sz.y):.2f} drill {mm(p.GetDrillSize().x):.2f} {"THT" if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else "SMD"}')
for a in sys.argv[1:]:
    lib, name = a.split(':'); info(lib, name)
