# Robo-Garage controller PCB - parts, footprints, nets, placement, LCSC numbers (single source of truth)
# Coordinates in mm, KiCad board coords (x right, y down); board 100 x 100 mm, top-left at (0, 0).
# rot = KiCad footprint rotation in degrees (CCW).

VERSION = '1.2'   # PCB version: silkscreen title + release zip name (pcb/gen/package.sh)

W, H = 100.0, 100.0

# ---- ESP32 DevKitC V4: top row = DevKit J3 side, bottom row = J2 side (dual column 22.86 / 25.4 mm) ----
J3_PINS = ['GND', 'IO23', 'IO22', 'TXD', 'RXD', 'IO21', 'GND', 'IO19', 'IO18', 'IO5', 'IO17', 'IO16', 'IO4',
           'IO0', 'IO2', 'IO15', 'SD1', 'SD0', 'CLK']
J2_PINS = ['+3V3', 'EN', 'VP', 'VN', 'IO34', 'IO35', 'IO32', 'IO33', 'IO25', 'IO26', 'IO27', 'IO14', 'IO12',
           'GND', 'IO13', 'SD2', 'SD3', 'CMD', '+5V_DEV']
# VP = GPIO36, VN = GPIO39 (input only, ADC1). v1.2 adds IO2 (valve), IO15 (buzzer), VP (12 V monitor),
# IO35 (leak probe, ADC1), VN + IO5 (EXP header spares).
USED = {'GND', 'IO23', 'IO22', 'IO21', 'IO19', 'IO18', 'IO17', 'IO16', 'IO4', '+3V3', 'IO32', 'IO33', 'IO25',
        'IO26', 'IO27', 'IO14', 'IO13', '+5V_DEV', 'IO34', 'IO35', 'IO2', 'IO15', 'VP', 'VN', 'IO5'}
DK_X0, DK_Y0 = 3.0, 5.0
ROW_NARROW, ROW_WIDE = 22.86, 25.4


def j3_nets():
    return {str(k + 1): (n if n in USED else None) for k, n in enumerate(J3_PINS)}


def j4_nets():
    return {str(k + 1): (n if n in USED else None) for k, n in enumerate(J2_PINS)}


R0603 = ('Resistor_SMD', 'R_0603_1608Metric')
C0603 = ('Capacitor_SMD', 'C_0603_1608Metric')
C0805 = ('Capacitor_SMD', 'C_0805_2012Metric')
C1206 = ('Capacitor_SMD', 'C_1206_3216Metric')
SOT23 = ('Package_TO_SOT_SMD', 'SOT-23')

# passives: value -> LCSC (all JLC basic, checked against the basic list of 2026-10-31)
RES = {'10k': 'C25804', '1k': 'C21190', '100k': 'C25803', '4.7k': 'C23162', '330': 'C23138', '100': 'C22775',
       '2.2k': 'C4190', '33k': 'C4216', '75k': 'C23242', '22k': 'C31850', '10': 'C22859'}
CAP = {'100nF': 'C14663', '1nF': 'C1588', '10uF 50V': 'C13585', '22uF 25V': 'C45783'}

# v1.2: spring clamps Cixi Kefa KF250-3.5-nP-1 (3.5 mm pitch, 45 deg, push buttons, 0.2-0.75 mm2, 5 A),
# JLC extended parts, wave soldered by JLC (Economic PCBA). Footprint: pcb/lib/robo.pretty (fplib.py).
KF_LCSC = {2: 'C475154', 3: 'C475155', 4: 'C475156', 6: 'C475158'}


def kf(n):
    return ('robo', 'KF250-3.5-%dP_1x%02d_P3.50mm_45Degree' % (n, n))


P = {}


def add(ref, fp, val, x, y, rot, nets, lcsc=None, mpn=None, **kw):
    if lcsc is None:
        lcsc = RES.get(val) if fp == R0603 else CAP.get(val)
    P[ref] = dict(lib=fp[0], fp=fp[1], val=val, x=x, y=y, rot=rot, nets=nets, lcsc=lcsc, mpn=mpn, **kw)


def R(ref, val, x, y, rot, a, b):
    add(ref, R0603, val, x, y, rot, {'1': a, '2': b})


def C(ref, val, x, y, rot, a, b, fp=C0603):
    add(ref, fp, val, x, y, rot, {'1': a, '2': b})


def clamp(ref, n, val, x, y, rot, nets):
    add(ref, kf(n), val, x, y, rot, nets, lcsc=KF_LCSC[n], mpn='KF250-3.5-%dP-1' % n, tht=True)


# ================= ESP32 DevKitC V4 socket =================
# Three 1x19 sockets: J3 (top row) + J4 (outer bottom row, 25.4 mm) + J15 (inner bottom row, 22.86 mm).
# Both bottom rows are fitted and wired in parallel, so either DevKit width plugs in.
SOCKET = ('robo', 'PinSocket_1x19_P2.54mm_Vertical_Tight')   # courtyard = body, so J4 + J15 may touch
add('J3', SOCKET, 'DevKitC socket (GND..CLK)', DK_X0, DK_Y0, 90, j3_nets(),
    lcsc='C2932678', mpn='KH-2.54FH-1X19P-H8.5', tht=True)
add('J4', SOCKET, 'DevKitC socket (3V3..5V) outer 25.4', DK_X0, DK_Y0 + ROW_WIDE, 90, j4_nets(),
    lcsc='C2932678', mpn='KH-2.54FH-1X19P-H8.5', tht=True)
add('J15', SOCKET, 'DevKitC socket (3V3..5V) inner 22.86', DK_X0, DK_Y0 + ROW_NARROW, 90, j4_nets(),
    lcsc='C2932678', mpn='KH-2.54FH-1X19P-H8.5', tht=True)

# ================= 12 V input + protection (top right) =================
clamp('J2', 2, '12V IN', 92.8, 15.0, 90, {'1': '+12V_IN', '2': 'GND'})
add('F1', ('Fuse', 'Fuse_1812_4532Metric'), 'PTC 2.6A 16V', 78.0, 10.5, 180, {'1': '+12V_IN', '2': '+12V_F'},
    lcsc='C438899', mpn='SMD1812P260TF/16')
add('Q1', SOT23, 'AO3407A', 72.8, 10.5, 0, {'1': 'Q1_G', '2': '+12V', '3': '+12V_F'}, lcsc='C15155', mpn='AO3407A')
add('D1', ('Diode_SMD', 'D_SOD-123'), 'BZT52C12', 67.5, 7.0, 0, {'1': '+12V', '2': 'Q1_G'},
    lcsc='C43491', mpn='BZT52C12')
R('R1', '100k', 72.8, 6.6, 0, 'GND', 'Q1_G')
add('D2', ('Diode_SMD', 'D_SMA'), 'SMAJ15A', 66.5, 13.0, 0, {'1': '+12V', '2': 'GND'},
    lcsc='C148216', mpn='SMAJ15A')
add('C1', ('Capacitor_SMD', 'CP_Elec_6.3x7.7'), '100uF 25V', 75.5, 17.5, 0, {'1': '+12V', '2': 'GND'},
    lcsc='C3338', mpn='RVT1E101M0607')
C('C2', '10uF 50V', 75.5, 22.8, 0, '+12V', 'GND', fp=C1206)

# ================= 12 V -> 5.1 V buck (LMR51430, TI SLUSEF4 sec. 9.2) =================
UX, UY = 69.0, 31.0
add('U4', ('Package_TO_SOT_SMD', 'TSOT-23-6'), 'LMR51430XFDDCR', UX, UY, 0,
    {'1': 'GND', '2': 'SW', '3': '+12V', '4': 'FB', '5': 'EN', '6': 'CB'}, lcsc='C5219260', mpn='LMR51430XFDDCR')
add('L1', ('Inductor_SMD', 'L_Chilisin_BMRx00060630'), '6.8uH 6A', UX - 6.8, UY, 0, {'1': '+5V', '2': 'SW'},
    lcsc='C167221', mpn='FXL0630-6R8-M')
C('C20', '100nF', UX, UY - 4.0, 0, 'SW', 'CB')                      # bootstrap CB -> SW
C('C21', '100nF', UX, UY + 2.6, 0, '+12V', 'GND')                   # HF input cap
C('C22', '10uF 50V', UX, UY + 5.2, 0, '+12V', 'GND', fp=C1206)      # CIN
C('C23', '10uF 50V', UX, UY + 8.0, 0, '+12V', 'GND', fp=C1206)      # CIN
C('C24', '22uF 25V', UX - 13.4, UY - 1.2, 0, 'GND', '+5V', fp=C0805)  # COUT
C('C25', '22uF 25V', UX - 13.4, UY + 1.4, 0, 'GND', '+5V', fp=C0805)  # COUT
R('R26', '10k', UX + 3.6, UY + 0.95, 0, 'FB', 'GND')                # RFBB
R('R25', '75k', UX + 3.6, UY + 2.75, 0, 'FB', '+5V')                # RFBT -> 0.6 V * (1 + 75/10) = 5.1 V
R('R27', '100k', UX + 3.6, UY - 0.85, 0, 'EN', '+12V')              # EN tied to VIN
C('C26', '22uF 25V', UX - 13.4, UY + 4.0, 0, 'GND', '+5V', fp=C0805)  # COUT (3rd, DC-bias derating)
R('R4', '2.2k', UX - 13.4, UY + 6.8, 0, '+5V', 'LED_PWR')
add('LED1', ('LED_SMD', 'LED_0805_2012Metric'), 'green', UX - 13.4, UY + 9.0, 180, {'1': 'GND', '2': 'LED_PWR'},
    lcsc='C2297', mpn='KT-0805G')
add('D3', ('Diode_SMD', 'D_SOD-123'), 'B5819W', 49.2, 35.5, 180, {'1': '+5V_DEV', '2': '+5V'},
    lcsc='C8598', mpn='B5819W')

# ================= v1.2: 12 V supply monitor -> GPIO36 (VP, ADC1_CH0) =================
# 100k / 22k divider: 12 V -> 2.16 V, 24 V -> 4.3 V, clamped by D7 (BAT54S) to 3V3 through the 10k.
R('R47', '100k', 10.5, 36.5, 0, '+12V', 'VMON')
R('R48', '22k', 13.5, 36.5, 0, 'VMON', 'GND')
R('R49', '10k', 16.5, 36.5, 0, 'VMON', 'VP')
C('C32', '100nF', 10.5, 38.5, 0, 'VP', 'GND')
add('D7', SOT23, 'BAT54S', 14.0, 39.0, 0, {'1': 'GND', '2': '+3V3', '3': 'VP'}, lcsc='C408389', mpn='BAT54S', noref=True)

# ================= motor driver + current sense (left) =================
add('R6', ('Resistor_SMD', 'R_2512_6332Metric'), '0R1 1W', 21.0, 40.0, 0, {'1': '+12V', '2': '+12V_MOT'},
    lcsc='C844904', mpn='WSL2512R1000FEA')
add('U2', ('Package_TO_SOT_SMD', 'SOT-23-8'), 'INA219AIDCNR', 21.0, 46.0, 0,
    {'1': 'ISNS_P', '2': 'ISNS_N', '3': 'GND', '4': '+3V3', '5': 'IO22', '6': 'IO21', '7': 'GND', '8': 'GND'},
    lcsc='C87469', mpn='INA219AIDCNR')
add('R28', R0603, '0R', 16.5, 44.2, 90, {'1': '+12V', '2': 'ISNS_P'}, lcsc='C21189')     # Kelvin tap IN+
add('R29', R0603, '0R', 25.5, 44.2, 90, {'1': '+12V_MOT', '2': 'ISNS_N'}, lcsc='C21189') # Kelvin tap IN-
C('C11', '100nF', 25.5, 47.5, 90, '+3V3', 'GND')
U1X, U1Y = 30.0, 72.0      # v1.1: moved right, the left edge now carries the BEAM clamp
add('U1', ('Package_SO', 'TI_SO-PowerPAD-8_ThermalVias'), 'DRV8871DDAR', U1X, U1Y, 0,
    {'1': 'GND', '2': 'IO26', '3': 'IO25', '4': 'ILIM', '5': '+12V_MOT', '6': 'MOT_A', '7': 'GND', '8': 'MOT_B',
     '9': 'GND'}, lcsc='C75864', mpn='DRV8871DDAR')
R('R5', '33k', U1X - 5.0, U1Y + 4.0, 90, 'ILIM', 'GND')            # I_trip = 64 kV / 33 k = 1.9 A
C('C9', '100nF', U1X + 6.5, U1Y + 3.0, 90, '+12V_MOT', 'GND')
C('C10', '10uF 50V', U1X + 7.0, U1Y - 5.5, 90, '+12V_MOT', 'GND', fp=C1206)
add('C3', ('Capacitor_SMD', 'CP_Elec_6.3x7.7'), '100uF 25V', 35.5, 57.0, 0, {'1': '+12V_MOT', '2': 'GND'},
    lcsc='C3338', mpn='RVT1E101M0607')
clamp('J5', 2, 'ACTUATOR', 11.0, 92.8, 0, {'1': 'MOT_A', '2': 'MOT_B'})

# ================= signal conditioning under the DevKit =================
R('R19', '10k', 15.5, 22.5, 90, 'REED_CL', '+3V3')
R('R22', '1k', 17.5, 22.5, 90, 'IO32', 'REED_CL')
C('C17', '100nF', 19.5, 22.5, 90, 'GND', 'IO32')
R('R20', '10k', 21.5, 22.5, 90, 'REED_OP', '+3V3')
R('R23', '1k', 23.5, 22.5, 90, 'IO33', 'REED_OP')
C('C18', '100nF', 25.5, 22.5, 90, 'GND', 'IO33')
R('R13', '10k', 27.5, 22.5, 90, 'FAN_TACH', '+3V3')
R('R14', '1k', 29.5, 22.5, 90, 'IO27', 'FAN_TACH')
C('C15', '1nF', 31.5, 22.5, 90, 'GND', 'IO27')
R('R21', '10k', 21.5, 10.0, 90, '+3V3', 'REED_DR')
R('R24', '1k', 23.5, 10.0, 90, 'REED_DR', 'IO18')
C('C19', '100nF', 25.5, 10.0, 90, 'IO18', 'GND')
R('R17', '10k', 15.5, 10.0, 90, '+3V3', 'BTN')
R('R18', '1k', 17.5, 10.0, 90, 'BTN', 'IO19')
C('C16', '100nF', 19.5, 10.0, 90, 'IO19', 'GND')
R('R7', '4.7k', 9.5, 10.0, 90, '+3V3', 'IO21')
R('R8', '4.7k', 11.5, 10.0, 90, '+3V3', 'IO22')
add('U3', ('Package_TO_SOT_SMD', 'SOT-23-5'), 'SN74AHCT1G125DBVR', 33.0, 11.0, 0,
    {'1': 'GND', '2': 'LED_IN', '3': 'GND', '4': 'LED_BUF', '5': '+5V'}, lcsc='C7484', mpn='SN74AHCT1G125DBVR')
R('R30', '1k', 29.5, 14.0, 90, 'IO16', 'LED_IN')                   # limits back-feed when only USB powers the ESP32
C('C12', '100nF', 36.5, 10.0, 90, '+5V', 'GND')
R('R10', '10k', 29.5, 10.5, 90, 'LED_IN', 'GND')
R('R9', '330', 36.5, 14.0, 90, 'LED_BUF', 'LED_DATA')

# ================= outputs =================
add('Q2', SOT23, '2N7002', 30.5, 85.0, 0, {'1': 'Q2_G', '2': 'GND', '3': 'FAN_PWM'}, lcsc='C8545', mpn='2N7002')
R('R11', '100', 26.5, 85.0, 90, 'Q2_G', 'IO17')
R('R12', '10k', 26.5, 81.0, 90, 'Q2_G', '+3V3')                    # fan off while the ESP32 boots
add('J6', ('Connector', 'FanPinHeader_1x04_P2.54mm_Vertical'), 'Fan 4-pin', 22.5, 95.0, 0,
    {'1': 'GND', '2': '+12V', '3': 'FAN_TACH', '4': 'FAN_PWM'}, lcsc='C240840', mpn='Molex 47053-1000', tht=True)
add('F2', ('Fuse', 'Fuse_1206_3216Metric'), 'PTC 1.5A', 38.5, 78.0, 0, {'1': '+5V', '2': '+5V_LED'},
    lcsc='C135341', mpn='ASMD1206-150')
add('C13', ('Capacitor_SMD', 'CP_Elec_8x10'), '470uF 16V', 47.5, 77.0, 90, {'1': '+5V_LED', '2': 'GND'},
    lcsc='C970706', mpn='RVT1C471M0810')
clamp('J7', 3, 'LED', 37.0, 92.8, 0, {'1': '+5V_LED', '2': 'LED_DATA', '3': 'GND'})
clamp('J10', 4, 'I2C', 55.0, 92.8, 0, {'1': '+3V3', '2': 'IO21', '3': 'IO22', '4': 'GND'})
add('J11', ('Connector_PinHeader_2.54mm', 'PinHeader_1x06_P2.54mm_Vertical'), 'EXP (optional)', 31.0, 35.0, 90,
    {'1': '+3V3', '2': 'GND', '3': '+5V', '4': 'IO14', '5': 'VN', '6': 'IO5'}, tht=True, dnp=True)
add('Q3', SOT23, 'AO3400A', 78.2, 27.5, 0, {'1': 'Q3_G', '2': 'GND', '3': 'RING_K'}, lcsc='C20917', mpn='AO3400A')
R('R16', '100k', 75.2, 27.5, 90, 'Q3_G', 'GND')
R('R15', '100', 77.5, 32.5, 90, 'IO23', 'Q3_G')
clamp('J8', 4, 'BUTTON', 92.8, 42.0, 90, {'1': 'BTN', '2': 'GND', '3': '+12V', '4': 'RING_K'})
clamp('J9', 6, 'REEDS', 92.8, 78.0, 90,
      {'1': 'REED_CL', '2': 'GND', '3': 'REED_OP', '4': 'GND', '5': 'REED_DR', '6': 'GND'})

# ================= v1.1: door light barrier (left edge) =================
# 6-pole clamp (pole 6 = spare GND), wires enter from the left: RX+ RX- SIG (receiver), TX+ TX- (emitter).
# Receiver: NPN output. SIG is pulled up to +12V (before F3), so a cut wire or a tripped F3 reads "blocked".
# Q5 turns the 12 V level into a clean 3.3 V signal (IO34 low = SIG high = no light / blocked).
# Q4 switches the emitter (low side): the ESP32 turns it off before every close and checks the receiver reacts.
BX, BY = 7.2, 47.0
clamp('J12', 6, 'BEAM', BX, BY, 270,
      {'1': 'BEAM_12V', '2': 'GND', '3': 'BEAM_SIG', '4': 'BEAM_12V', '5': 'BEAM_TX', '6': 'GND'})
add('F3', ('Fuse', 'Fuse_1206_3216Metric'), 'PTC 200mA 30V', 21.0, 53.5, 90, {'1': '+12V', '2': 'BEAM_12V'},
    lcsc='C883118', mpn='BSMD1206-020-30V')
R('R31', '4.7k', 23.6, 53.5, 90, 'BEAM_SIG', '+12V')                # pull-up to +12V: cut wire = blocked
R('R32', '10k', 25.2, 53.5, 90, 'BEAM_SIG', 'Q5_G')
R('R35', '10k', 24.6, 59.6, 90, 'Q5_G', 'GND')                      # 10k/10k: NPN residual <1.5 V stays off
C('C27', '1nF', 26.2, 59.6, 90, 'Q5_G', 'GND')
add('Q5', SOT23, '2N7002', 21.6, 59.6, 0, {'1': 'Q5_G', '2': 'GND', '3': 'IO34'}, lcsc='C8545', mpn='2N7002')
R('R36', '10k', 24.6, 64.5, 90, 'IO34', '+3V3')
add('Q4', SOT23, 'AO3400A', 21.6, 69.0, 0, {'1': 'Q4_G', '2': 'GND', '3': 'BEAM_TX'}, lcsc='C20917', mpn='AO3400A')
R('R33', '100', 26.2, 64.5, 90, 'IO13', 'Q4_G')
R('R34', '100k', 24.6, 69.0, 90, 'Q4_G', 'GND')                     # emitter off while the ESP32 boots

# ================= v1.2: water leak probe (left edge, below BEAM) =================
# Two bare electrodes on the cabinet floor between SENSE and GND. IO4 drives the probe through R40 only while
# measuring (50 ms every 10 s, no DC across the electrodes -> no corrosion); IO35 (ADC1) reads the divider
# R40 / water. Dry: 3.3 V. Tap water (< 200 kOhm): below 2.2 V. R41 + C31 filter, D4 clamps to 3V3 / GND.
LX, LY = 7.2, 70.5
clamp('J13', 2, 'LEAK', LX, LY, 270, {'1': 'LEAK_S', '2': 'GND'})
R('R40', '100k', 19.5, 71.8, 0, 'IO4', 'LEAK_S')
C('C30', '1nF', 19.5, 74.3, 0, 'LEAK_S', 'GND')
R('R41', '10k', 22.5, 71.8, 0, 'LEAK_S', 'IO35')
C('C31', '100nF', 22.5, 74.3, 0, 'IO35', 'GND')
add('D4', SOT23, 'BAT54S', 19.5, 77.0, 0, {'1': 'GND', '2': '+3V3', '3': 'IO35'}, lcsc='C408389', mpn='BAT54S', noref=True)

# ================= v1.2: 12 V valve output (left edge, below LEAK) =================
# Low-side switch for a 12 V solenoid or motorised valve (<= 1.5 A): IO2 -> R42 -> Q6 (AO3400A), SS34 flyback,
# PTC F4. Pole 1 = +12V (fused), pole 2 = switched return. IO2 is a strapping pin: R43 keeps it low at boot.
VX, VY = 7.2, 80.0
clamp('J14', 2, 'VALVE', VX, VY, 270, {'1': '+12V_VLV', '2': 'VALVE_K'})
add('F4', ('Fuse', 'Fuse_1206_3216Metric'), 'PTC 1.5A', 19.0, 80.0, 0, {'1': '+12V', '2': '+12V_VLV'},
    lcsc='C135341', mpn='ASMD1206-150', noref=True)
add('D5', ('Diode_SMD', 'D_SMA'), 'SS34', 19.5, 84.0, 0, {'1': '+12V_VLV', '2': 'VALVE_K'},
    lcsc='C8678', mpn='SS34')
add('Q6', SOT23, 'AO3400A', 23.6, 80.5, 0, {'1': 'Q6_G', '2': 'GND', '3': 'VALVE_K'}, lcsc='C20917', mpn='AO3400A', noref=True)
R('R42', '100', 22.8, 77.2, 90, 'IO2', 'Q6_G')
R('R43', '10k', 24.5, 84.0, 90, 'Q6_G', 'GND')

# ================= v1.2: buzzer (centre) =================
# MLT-8530 passive magnetic buzzer (3.6 V, 16 Ohm, 2.7 kHz): +5V -> R44 (10 Ohm) -> BZ1 -> Q7 (AO3400A) -> GND.
# ESPHome drives IO15 with a 2.7 kHz square wave (rtttl). IO15 is a strapping pin: R46 keeps it low at boot
# (only silences the boot ROM log). D6 is the flyback diode.
BZX, BZY = 56.0, 62.0
add('BZ1', ('robo', 'Buzzer_SMD_MLT-8530_8.5x8.5mm'), 'MLT-8530', BZX, BZY, 0, {'1': 'BZ_P', '2': 'BZ_K'},
    lcsc='C94599', mpn='MLT-8530')
R('R44', '10', 49.0, 59.5, 0, '+5V', 'BZ_P')
add('D6', ('Diode_SMD', 'D_SOD-123'), 'B5819W', 56.0, 69.5, 0, {'1': 'BZ_P', '2': 'BZ_K'},
    lcsc='C8598', mpn='B5819W')
add('Q7', SOT23, 'AO3400A', 49.0, 65.0, 0, {'1': 'Q7_G', '2': 'GND', '3': 'BZ_K'}, lcsc='C20917', mpn='AO3400A', noref=True)
R('R45', '100', 45.3, 65.0, 0, 'IO15', 'Q7_G')
R('R46', '10k', 49.0, 62.0, 0, 'Q7_G', 'GND')

# ================= v1.1: SHT40 temperature / humidity (bottom-right, thermally isolated) =================
# Sits on an 8 x 8 mm island inside a C-shaped 1.5 mm milled slot; only 4 thin traces cross the neck.
# The case gives this corner its own vented chamber. No copper pour in the chamber.
SX, SY = 84.0, 92.0
add('U5', ('Sensor_Humidity', 'Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad'), 'SHT40-AD1B', SX, SY, 0,
    {'1': 'IO21', '2': 'IO22', '3': '+3V3', '4': 'GND'}, lcsc='C2909890', mpn='SHT40-AD1B-R2')
C('C28', '100nF', SX + 2.3, SY, 90, '+3V3', 'GND')               # pad 1 (+3V3) below, pad 2 (GND) above
ISL = (80.0, 88.0, 88.0, 96.0)            # island x0, y0, x1, y1
SLOT_W, NECK = 1.5, (90.25, 93.75)        # slot width, neck y range (left side)
x0, y0, x1, y1 = ISL
o0, p0, o1, p1 = x0 - SLOT_W, y0 - SLOT_W, x1 + SLOT_W, y1 + SLOT_W
SLOTS = [[(o0, NECK[0]), (o0, p0), (o1, p0), (o1, p1), (o0, p1), (o0, NECK[1]), (x0, NECK[1]), (x0, y1),
          (x1, y1), (x1, y0), (x0, y0), (x0, NECK[0])]]
k = 0.4                                   # copper-to-edge clearance
KEEPOUTS = [(o0 - k, p0 - k, o1 + k, y0 + k), (o0 - k, y1 - k, o1 + k, p1 + k), (x1 - k, p0 - k, o1 + k, p1 + k),
            (o0 - k, p0 - k, x0 + k, NECK[0] + k), (o0 - k, NECK[1] - k, x0 + k, p1 + k)]
CHAMBER = (76.0, 84.0, 100.0, 100.0)     # case chamber around the sensor (partitions at x = 76 and y = 84)
NOPOUR = [(CHAMBER[0] + 0.6, CHAMBER[1] + 0.6, W - 0.3, H - 0.3)]

# v1.1.1: GND pins that only get 1 thermal spoke (tracks around them) -> solid pour connection instead.
# Q3 = 2 A ring-LED low-side switch (solid is better for current anyway), C16 = button debounce cap.
SOLID_PADS = ['Q3.2', 'C16.2', 'C11.2']   # v1.2: C11 (INA219 decoupling) too

# ================= mounting holes + JLCPCB tooling holes =================
for i, (x, y) in enumerate([(96.5, 3.5), (3.5, 96.5), (96.5, 96.5), (3.5, 40.0)]):
    add('H%d' % (i + 1), ('MountingHole', 'MountingHole_3.2mm_M3'), 'M3', x, y, 0, {}, tht=True, nobom=True)
# v1.2: three 1.152 mm tooling holes for the assembly line (JLC: "tooling holes by customer"), far apart,
# outside the case posts (7 mm) and the copper-free sensor chamber for TH3.
for i, (x, y) in enumerate([(90.0, 3.5), (3.5, 90.0), (94.0, 90.0)]):
    add('TH%d' % (i + 1), ('robo', 'ToolingHole_JLCPCB_1.152mm'), 'tooling', x, y, 0, {}, tht=True, nobom=True)

# ================= pre-routed tracks (locked) =================
c, r = 0.775, 0.825          # 0603 cap / resistor pad offsets
TR = []          # (net, width, layer, [points])
TR += [('SW', 0.6, 'F', [(UX - 1.14, UY), (UX - 3.8, UY)])]                                  # SW -> L1
TR += [('SW', 0.4, 'F', [(UX - c, UY - 4.0), (UX - 3.4, UY - 4.0), (UX - 3.4, UY - 1.6)])]    # CBOOT -> SW
TR += [('CB', 0.3, 'F', [(UX + c, UY - 4.0), (UX + 1.14, UY - 0.95)])]                       # CBOOT -> CB
TR += [('GND', 0.3, 'F', [(UX - 1.14, UY - 0.95), (UX, UY - 0.5), (UX, UY + 1.7), (UX + c, UY + 2.6)])]
TR += [('+12V', 0.6, 'F', [(UX - 1.14, UY + 0.95), (UX - c, UY + 1.6), (UX - c, UY + 2.6)])]
TR += [('+12V', 0.8, 'F', [(UX - c, UY + 2.6), (UX - 1.48, UY + 5.2), (UX - 1.48, UY + 8.0)])]
TR += [('GND', 0.8, 'F', [(UX + c, UY + 2.6), (UX + 1.48, UY + 5.2), (UX + 1.48, UY + 8.0)])]
TR += [('+5V', 0.8, 'F', [(UX - 9.82, UY), (UX - 12.45, UY - 1.2)]),
       ('+5V', 0.8, 'F', [(UX - 9.82, UY), (UX - 12.45, UY + 1.4)])]
TR += [('FB', 0.25, 'F', [(UX + 1.14, UY + 0.95), (UX + 3.6 - r, UY + 0.95), (UX + 3.6 - r, UY + 2.75)])]
TR += [('EN', 0.25, 'F', [(UX + 1.14, UY), (UX + 2.0, UY), (UX + 3.6 - r, UY - 0.85)])]
VIAS = [('GND', UX + 2.9, UY + 5.2), ('GND', UX + 2.9, UY + 8.0), ('GND', UX + 5.4, UY + 0.95),
        ('GND', UX - 15.4, UY - 1.2), ('GND', UX - 15.4, UY + 1.4)]
TR += [('GND', 0.5, 'F', [(UX + 1.48, UY + 5.2), (UX + 2.9, UY + 5.2)]),
       ('GND', 0.5, 'F', [(UX + 1.48, UY + 8.0), (UX + 2.9, UY + 8.0)]),
       ('GND', 0.4, 'F', [(UX + 3.6 + r, UY + 0.95), (UX + 5.4, UY + 0.95)]),
       ('GND', 0.5, 'F', [(UX - 14.35, UY - 1.2), (UX - 15.4, UY - 1.2)]),
       ('GND', 0.5, 'F', [(UX - 14.35, UY + 1.4), (UX - 15.4, UY + 1.4)])]
TR += [('+5V', 0.8, 'F', [(UX - 12.45, UY + 1.4), (UX - 12.45, UY + 4.0)]),
       ('GND', 0.5, 'F', [(UX - 14.35, UY + 4.0), (UX - 15.4, UY + 4.0)])]
VIAS += [('GND', UX - 15.4, UY + 4.0)]
# IO23 (button ring gate) from the far-left DevKit pin along the top edge, dips under the 12 V input
TR += [('IO23', 0.25, 'F', [(5.54, 5.0), (5.54, 1.6), (84.0, 1.6), (84.0, 7.0)]),
       ('IO23', 0.25, 'B', [(84.0, 7.0), (84.0, 33.5)]),
       ('IO23', 0.25, 'F', [(84.0, 33.5), (78.3, 33.5), (77.5, 33.325)])]
VIAS += [('IO23', 84.0, 7.0), ('IO23', 84.0, 33.5)]
# v1.2: GND spokes by hand for the socket pins the router boxes in (J3.1 top-left, J4.14 under the EXP header):
# a short locked track on each layer to a GND via counts as a thermal spoke for the KiCad DRC.
for (px, py), (vx, vy) in (((DK_X0, DK_Y0), (DK_X0, DK_Y0 + 2.6)),
                           ((DK_X0 + 13 * 2.54, DK_Y0 + ROW_WIDE), (DK_X0 + 13 * 2.54, DK_Y0 + ROW_WIDE + 2.1))):
    TR += [('GND', 0.4, 'F', [(px, py), (vx, vy)]), ('GND', 0.4, 'B', [(px, py), (vx, vy)])]
    VIAS += [('GND', vx, vy)]
# DRV8871 VM -> 100 nF
TR += [('+12V_MOT', 0.6, 'F', [(U1X + 2.7, U1Y + 1.905), (U1X + 4.4, U1Y + 1.905), (U1X + 4.4, U1Y + 3.775),
                                (U1X + 6.5, U1Y + 3.775)])]
# SHT40 island: hand fan-out of the 0.8 mm-pitch DFN through the neck, ending left of the chamber wall (x = 76)
XE = 75.0
TR += [('GND', 0.3, 'F', [(XE, 90.9), (SX + 2.3, 90.9), (SX + 2.3, SY - 0.775)]),
       ('GND', 0.25, 'F', [(SX + 0.7, SY - 0.4), (SX + 2.3, SY - 0.4), (SX + 2.3, SY - 0.775)]),  # VSS -> C28 (leave the pad outwards:
       ('IO21', 0.25, 'F', [(XE, SY - 0.4), (SX - 0.7, SY - 0.4)]),
       ('IO22', 0.25, 'F', [(XE, SY + 0.4), (SX - 0.7, SY + 0.4)]),
       ('+3V3', 0.25, 'F', [(XE, 93.1), (SX + 2.3, 93.1), (SX + 2.3, SY + 0.775)]),
       ('+3V3', 0.25, 'F', [(SX + 0.7, SY + 0.4), (SX + 2.3, SY + 0.4), (SX + 2.3, SY + 0.775)])]  #  the footprint has a keepout body;
# v1.1.1: both end exactly in the C28 pad centres, so the autorouter sees them as connected)

# ================= silkscreen =================
TEXTS = []


def T(text, x, y, size=1.0, rot=0, just='c', back=False):
    TEXTS.append(dict(text=text, x=x, y=y, size=size, rot=rot, just=just, back=back))


PITCH = 3.5


def pin_labels_bottom(x0, labels, y=86.2):
    for k, s in enumerate(labels):
        T(s, x0 + PITCH * k, y, 0.8)


def pin_labels_right(y0, labels, x=83.6):
    for k, s in enumerate(labels):
        T(s, x, y0 - PITCH * k, 0.8, just='r')


def pin_labels_left(y0, labels, x=13.0):
    for k, s in enumerate(labels):
        T(s, x, y0 + PITCH * k, 0.8, just='l')


pin_labels_bottom(11.0, ['M+', 'M-'])
pin_labels_bottom(37.0, ['5V', 'DAT', 'GND'])
pin_labels_bottom(55.0, ['3V3', 'SDA', 'SCL', 'GND'])
pin_labels_right(15.0, ['+12V', 'GND'])
pin_labels_right(42.0, ['BTN', 'GND', '12V', 'LED-'])
pin_labels_right(78.0, ['CL', 'GND', 'OP', 'GND', 'DR', 'GND'])
pin_labels_left(BY, ['RX+', 'RX-', 'SIG', 'TX+', 'TX-', 'GND'])
pin_labels_left(LY, ['SENSE', 'GND'])
pin_labels_left(VY, ['12V', 'VLV'])
T('BEAM', 12.6, BY - 3.5, 0.8, just='l')
T('LEAK', 13.0, LY - 2.4, 0.8, just='l')
T('VALVE', 13.0, VY - 2.4, 0.8, just='l')
T('ACTUATOR', 18.0, 88.6, 0.8, just='l')
T('FAN', 26.3, 91.0, 0.9)
T('LED', 40.5, 84.6, 0.8)
T('I2C  ToF', 60.25, 84.6, 0.8)
T('12 V IN', 83.6, 8.0, 0.8, just='r')
T('BUTTON', 83.6, 26.4, 0.8, just='r')
T('REEDS', 83.6, 56.8, 0.8, just='r')
T('EXP: 3V3 GND 5V IO14 IO39 IO5', 37.35, 37.6, 0.8)
T('BUZZER', BZX, BZY - 6.6, 0.8)
T('ROBO-GARAGE CTRL v' + VERSION, 42.0, 46.0, 1.4)
T('ESP32 DevKitC V4  (antenna <-)  USB-C ->', 26.0, 2.4, 0.8)
T('DevKit: either row fits (25.4 / 22.86)', 3.0, 33.6, 0.8, just='l')
