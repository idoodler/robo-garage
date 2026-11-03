# Project footprint library (pcb/lib/robo.pretty), generated from the numbers in the datasheets.
# build.py calls make_lib() before loading footprints, so the library is always in sync with this file.
import os
import uuid

LIB = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib', 'robo.pretty'))


def _id():
    return str(uuid.uuid4())


def _line(a, b, layer, w=0.12):
    return '  (fp_line (start %.3f %.3f) (end %.3f %.3f) (stroke (width %.2f) (type solid)) (layer "%s") (tstamp %s))\n' % (
        a[0], a[1], b[0], b[1], w, layer, _id())


def _rect(x0, y0, x1, y1, layer, w=0.12):
    return (_line((x0, y0), (x1, y0), layer, w) + _line((x1, y0), (x1, y1), layer, w) +
            _line((x1, y1), (x0, y1), layer, w) + _line((x0, y1), (x0, y0), layer, w))


def _circle(cx, cy, r, layer, w=0.12, fill=False):
    return '  (fp_circle (center %.3f %.3f) (end %.3f %.3f) (stroke (width %.2f) (type solid)) (fill %s) (layer "%s") (tstamp %s))\n' % (
        cx, cy, cx + r, cy, w, 'solid' if fill else 'none', layer, _id())


def _text(kind, text, x, y, layer, size=1.0, hide=False):
    return ('  (fp_text %s "%s" (at %.3f %.3f) (layer "%s")%s\n'
            '    (effects (font (size %.1f %.1f) (thickness 0.15)))\n    (tstamp %s)\n  )\n' % (
                kind, text, x, y, layer, ' hide' if hide else '', size, size, _id()))


def _header(name, descr, tags, attr):
    return ('(footprint "%s" (version 20221018) (generator robo_fplib)\n  (layer "F.Cu")\n  (descr "%s")\n'
            '  (tags "%s")\n  (attr %s)\n' % (name, descr, tags, attr))


def kf250(n):
    """Cixi Kefa KF250-3.5-nP-1 (45 deg wire entry, push buttons). Same body as Degson DG250-3.5.
    Datasheet (LCSC C475154) and JLC's footprint (C475154..8): the poles alternate between TWO pin rows 5.0 mm apart
    (zig-zag) -- odd poles 2.2 mm, even poles 7.2 mm from the rear face; pole pitch 3.5 (7.0 within a row), hole 1.2,
    pins 0.4 x 0.85, solder pin 3.6; body 2.70 mm left of pole 1 and 2.40 mm right of pole n (L = n*3.5 + 1.6),
    depth 12.0, height 11.7. (v1.2-v1.3 had all pins in one row -- the part would not have fitted.)
    Local frame as before, so the body has not moved: pole 1 at x = 0, poles along +x, wires enter from +y
    (front face y = +7.0, rear face y = -5.0): odd pins y = -2.8, even pins y = +2.2."""
    name = 'KF250-3.5-%dP_1x%02d_P3.50mm_45Degree' % (n, n)
    x0, x1 = -2.70, (n - 1) * 3.5 + 2.40
    L = x1 - x0
    yr, yf = -5.0, 7.0
    s = _header(name, 'Cixi Kefa KF250-3.5-%dP-1 spring clamp terminal block, 3.5 mm pitch, 45 deg, push button, '
                      'L %.1f x D 12 x H 11.7 mm, LCSC C47515x; same body as Degson DG250-3.5' % (n, L),
                'terminal block 3.5mm spring push-in 45deg KF250 DG250', 'through_hole')
    s += _text('reference', 'REF**', (x0 + x1) / 2, yr - 1.2, 'F.SilkS', 0.8)
    s += _text('value', name, (x0 + x1) / 2, yf + 1.2, 'F.Fab', 0.8)
    s += _text('user', '${REFERENCE}', (x0 + x1) / 2, 2.5, 'F.Fab', 0.6)
    s += _rect(x0, yr, x1, yf, 'F.Fab', 0.1)                                  # body
    s += _line((x0, yf - 4.0), (x1, yf - 4.0), 'F.Fab', 0.1)                  # push-button row / wire entry edge
    s += _rect(x0 - 0.11, yr - 0.11, x1 + 0.11, yf + 0.11, 'F.SilkS')         # silk outline
    for k in range(n):                                                        # wire entry marks on the front edge
        cx = k * 3.5
        s += _line((cx - 0.6, yf + 0.11), (cx, yf + 0.8), 'F.SilkS') + _line((cx, yf + 0.8), (cx + 0.6, yf + 0.11), 'F.SilkS')
    s += _rect(x0 - 0.25, yr - 0.25, x1 + 0.25, yf + 0.25, 'F.CrtYd', 0.05)
    for k in range(n):
        shape = 'rect' if k == 0 else 'oval'
        s += ('  (pad "%d" thru_hole %s (at %.3f %.3f) (size 2.1 2.1) (drill 1.3) (layers "*.Cu" "*.Mask") '
              '(tstamp %s))\n' % (k + 1, shape, k * 3.5, yr + (2.2 if k % 2 == 0 else 7.2), _id()))
    return name, s + ')\n'


def tooling_hole():
    """JLCPCB PCBA tooling hole: 1.152 mm NPTH, 0.148 mm solder mask expansion (jlcpcb.com help article 47)."""
    name = 'ToolingHole_JLCPCB_1.152mm'
    s = _header(name, 'JLCPCB PCBA tooling hole, 1.152 mm non-plated, solder mask expansion 0.148 mm',
                'tooling hole npth jlcpcb', 'through_hole exclude_from_pos_files exclude_from_bom')
    s += _text('reference', 'REF**', 0, -1.8, 'F.SilkS', 0.6, hide=True)
    s += _text('value', name, 0, 1.8, 'F.Fab', 0.6, hide=True)
    s += _circle(0, 0, 0.9, 'F.CrtYd', 0.05)
    s += ('  (pad "" np_thru_hole circle (at 0 0) (size 1.152 1.152) (drill 1.152) (layers "*.Cu" "*.Mask") '
          '(solder_mask_margin 0.148) (tstamp %s))\n' % _id())
    return name, s + ')\n'


def mlt8530():
    """Jiangsu Huaneng MLT-8530 SMD magnetic buzzer 8.5 x 8.5 x 3.3 mm (LCSC C94599). Pad layout after the
    community footprint nanbuwks/KiCadLibrary (terminals + and - on the x = -3.6 side, dummy pads opposite)."""
    name = 'Buzzer_SMD_MLT-8530_8.5x8.5mm'
    s = _header(name, 'Jiangsu Huaneng MLT-8530 passive SMD magnetic buzzer, 8.5 x 8.5 x 3.3 mm, 3.6 V, 2.7 kHz, '
                      'LCSC C94599', 'buzzer smd mlt-8530 huaneng', 'smd')
    s += _text('reference', 'REF**', 0, -5.6, 'F.SilkS', 0.8)
    s += _text('value', name, 0, 5.6, 'F.Fab', 0.8)
    s += _text('user', '${REFERENCE}', 0, 0, 'F.Fab', 0.6)
    s += _rect(-4.25, -4.25, 4.25, 4.25, 'F.Fab', 0.1)
    s += _line((3.0, -4.25), (4.25, -3.0), 'F.Fab', 0.1)                        # chamfered corner (datasheet mark)
    s += _circle(-3.6, -3.6, 0.3, 'F.Fab', 0.1, fill=True)                      # pin 1 (+)
    # silk: corners only (the pads sit at the corners, keep 0.2 mm off them)
    s += _line((-4.9, -1.8), (-4.9, 1.8), 'F.SilkS') + _line((4.9, -1.8), (4.9, 1.8), 'F.SilkS')
    s += _line((-1.8, -4.9), (1.8, -4.9), 'F.SilkS') + _line((-1.8, 4.9), (1.8, 4.9), 'F.SilkS')
    s += _circle(-5.6, -3.6, 0.25, 'F.SilkS', 0.12, fill=True)                  # pin 1 dot
    s += _rect(-5.0, -5.0, 5.0, 5.0, 'F.CrtYd', 0.05)
    for num, x, y in (('1', -3.6, -3.6), ('2', -3.6, 3.6), ('', 3.6, 3.6), ('', 3.6, -3.6)):
        s += ('  (pad "%s" smd rect (at %.3f %.3f) (size 1.8 1.8) (layers "F.Cu" "F.Paste" "F.Mask") (tstamp %s))\n' % (
            num, x, y, _id()))
    return name, s + ')\n'


def pinsocket_tight(n=19):
    """KiCad PinSocket_1xN with the courtyard narrowed to the body (+/-1.22 instead of +/-1.8): two sockets in
    adjacent rows (DevKit inner / outer row) then pass the courtyard check. Silk: only the pin-1 corner is kept
    on the long sides (the two bodies touch)."""
    import re
    src = '/usr/share/kicad/footprints/Connector_PinSocket_2.54mm.pretty/PinSocket_1x%d_P2.54mm_Vertical.kicad_mod' % n
    name = 'PinSocket_1x%02d_P2.54mm_Vertical_Tight' % n
    s = open(src).read()
    s = s.replace('(footprint "PinSocket_1x%d_P2.54mm_Vertical"' % n, '(footprint "%s"' % name)
    s = s.replace('(fp_text value "PinSocket_1x%d_P2.54mm_Vertical"' % n, '(fp_text value "%s"' % name)
    s = re.sub(r'(\(fp_line \(start )(-?1\.[78]5?)( -?[0-9.]+\) \(end )(-?1\.[78]5?)( -?[0-9.]+\)[^\n]*F\.CrtYd)',
               lambda m: m.group(1) + ('-1.22' if m.group(2).startswith('-') else '1.22') + m.group(3) +
               ('-1.22' if m.group(4).startswith('-') else '1.22') + m.group(5), s)
    s = re.sub(r'\(fp_line \(start (-?)1\.[78]5? (-?[0-9.]+)\) \(end (-?)1\.[78]5? (-?[0-9.]+)\)',
               lambda m: '(fp_line (start %s1.22 %s) (end %s1.22 %s)' % (m.group(1), m.group(2), m.group(3), m.group(4)), s)
    s = s.replace('(descr "', '(descr "courtyard narrowed to the body for adjacent rows; ')
    return name, s


def pwp16():
    """v1.3: TI PWP0016J (HTSSOP-16 PowerPAD, 5.0 x 4.4 mm) for the DRV8874PWPR, after the land pattern in TI SLVSF66A:
    16 pads 0.65 mm pitch, rows 5.72 mm apart (1.55 x 0.4 mm: 0.25 mm gap = the Motor net-class clearance),
    exposed pad 2.46 x 3.55 mm. Copper under the pad 3.4 x 5.0 mm (heat spreading on F.Cu), solder-mask opening
    2.56 x 3.65 mm, paste 4 windows (~70 %), 6 tented thermal vias 0.3 / 0.6 mm at both ends of the pad (no via in
    the paste area -> no solder wicking), B.Cu pad 3.0 x 5.0 mm that merges into the GND pour."""
    name = 'TI_PWP0016J_HTSSOP-16_ThermalVias'
    s = _header(name, 'TI PWP0016J PowerPAD HTSSOP-16 5.0 x 4.4 mm, P0.65, EP 2.46 x 3.55 mm, 6 tented thermal vias; '
                      'DRV8874PWPR (LCSC C1855818)', 'HTSSOP-16 PowerPAD PWP DRV8874 thermal vias', 'smd')
    s += _text('reference', 'REF**', 0, -3.6, 'F.SilkS', 0.8)
    s += _text('value', name, 0, 3.6, 'F.Fab', 0.6)
    s += _text('user', '${REFERENCE}', 0, 0, 'F.Fab', 0.6)
    s += _rect(-2.2, -2.5, 2.2, 2.5, 'F.Fab', 0.1)
    s += _line((-2.2, -1.7), (-1.4, -2.5), 'F.Fab', 0.1)                      # pin-1 bevel
    s += _line((-1.6, -2.61), (1.6, -2.61), 'F.SilkS') + _line((-1.6, 2.61), (1.6, 2.61), 'F.SilkS')
    s += _circle(-3.1, -3.1, 0.2, 'F.SilkS', 0.12, fill=True)                  # pin-1 dot
    s += _rect(-3.9, -2.85, 3.9, 2.85, 'F.CrtYd', 0.05)
    for k in range(8):
        y = -2.275 + 0.65 * k
        for num, x in ((k + 1, -2.86), (16 - k, 2.86)):
            s += ('  (pad "%d" smd roundrect (at %.3f %.3f) (size 1.55 0.4) (layers "F.Cu" "F.Paste" "F.Mask") '
                  '(roundrect_rratio 0.25) (tstamp %s))\n' % (num, x, y, _id()))
    s += ('  (pad "17" smd rect (at 0 0) (size 3.4 5.0) (layers "F.Cu") (zone_connect 2) (tstamp %s))\n' % _id())
    s += ('  (pad "" smd rect (at 0 0) (size 2.56 3.65) (layers "F.Mask") (tstamp %s))\n' % _id())
    for x in (-0.6, 0.6):
        for y in (-0.88, 0.88):
            s += ('  (pad "" smd rect (at %.2f %.2f) (size 1.0 1.5) (layers "F.Paste") (tstamp %s))\n' % (x, y, _id()))
    for y in (-2.2, 2.2):
        for x in (-1.0, 0.0, 1.0):
            s += ('  (pad "17" thru_hole circle (at %.2f %.2f) (size 0.6 0.6) (drill 0.3) (layers "*.Cu") '
                  '(zone_connect 2) (tstamp %s))\n' % (x, y, _id()))
    s += ('  (pad "17" smd rect (at 0 0) (size 3.0 5.0) (layers "B.Cu") (zone_connect 2) (tstamp %s))\n' % _id())
    return name, s + ')\n'


def make_lib():
    os.makedirs(LIB, exist_ok=True)
    made = []
    for name, text in [kf250(n) for n in (2, 3, 4, 6)] + [tooling_hole(), mlt8530(), pinsocket_tight(19), pwp16()]:
        path = os.path.join(LIB, name + '.kicad_mod')
        old = open(path).read() if os.path.exists(path) else None
        if old is None or _strip_ids(old) != _strip_ids(text):
            open(path, 'w').write(text)
        made.append(name)
    return made


def _strip_ids(s):
    import re
    return re.sub(r'\(tstamp [0-9a-f-]+\)', '', s)


if __name__ == '__main__':
    print('\n'.join(make_lib()))
