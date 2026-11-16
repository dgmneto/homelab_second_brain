"""10-inch rack, 3U case for casaos (ZimaBoard 832 + SAS HBA + 4 x 3.5" drives). 3D-printable.

Plain Python + manifold3d (no Blender):
    pip install manifold3d trimesh numpy scipy
    python3 build_case.py            # writes STLs, assembly.glb and dimensions.txt to out/
    node render.mjs                  # renders out/*.png from assembly.glb (Playwright + three.js from jsDelivr)

Coordinates (mm): X = outer west (left, seen from the front) side of the body, Y = back face of the
front panel (Y grows toward the rear), Z = bottom of the case. The front panel is Y -3..0.

Layout, seen from the front:
  +---------------- 220 body / 254 panel -----------------+
  | column (west, 88 wide)  | divider | drive cage (124)  |
  |  80 mm intake fan       |         | 120 mm intake fan |
  |  HBA on a top shelf     |         | 4 x 3.5" drives   |
  |  ZimaBoard on a shelf   |         | standing on edge, |
  |  Flex-ATX PSU on floor  |         | connectors rear   |
  +--------------------------------------------------------+
  * Drive cage: 4 identical slots (2 SATA + 2 SAS, all 3.5"), drives stand on their long edge
    between floor ribs and drop in from the top. Two comb bars on the lid's underside hold them
    down; a floor bar stops them at the front. A 120 mm fan in the front panel blows along all four,
    out through the rear-wall grille. Cables go on behind the drives (~48 mm).
  * Column: a Flex-ATX ("1U") PSU on the floor at the rear, its IEC inlet + fan through the rear
    wall. Over it, the ZimaBoard on a removable shelf, its I/O end through a rear-wall window.
    Over that, the HBA on a second removable shelf, connected through a PCIe x4 riser
    cable (the ZimaBoard's slot is in line with the board, so a card plugged in directly would
    stick out ~170 mm). An 80 mm front fan blows across both shelves.
  * Shelves rest on short ledge segments on the west wall and on the divider. The board shelf has
    notches where the upper (HBA) ledges are, so it drops past them to the lower ledges.
    Assembly order: PSU, board shelf, HBA shelf, drives, lid.
  * Cables: PSU cables leave its front face, run back over the PSU (a 10 mm channel under the board
    shelf) and cross into the drive area through the divider's rear window.
  * Rack: same Lab Rax 10" rack and same depth as the homelab-notebook case, so the notebook case's
    rear_bracket_left/right.stl fit unchanged (bolt them to the rear posts at this case's bottom U).

Parts to print (PETG/ASA, not PLA: ~5 kg loaded): tray (floor + walls + divider + front panel with
rack ears), lid, board_shelf, hba_shelf; rear_bracket_left/right from
hosts/homelab-notebook/hardware/case/out/.
"""

import math
import os

import numpy as np
from manifold3d import CrossSection, Manifold, OpType

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# ---------------------------------------------------------------- rack (same as the notebook case)
U = 44.45
N_U = 3
PANEL_H = N_U * U - 0.79       # EIA gap: 132.56
PANEL_W = 254.0
PANEL_T = 3.0
Z_OFF = (U - (U - 0.79)) / 2   # panel bottom above the U boundary (0.395), as in the notebook case
EAR_HOLE_SPACING = 236.525
EAR_HOLE_Z = tuple(z - Z_OFF for z in (6.35, U + 22.225, 2 * U + 38.1))  # bottom, middle, top
EAR_SLOT_D, EAR_SLOT_L = 6.5, 10.0

# ---------------------------------------------------------------- case
BODY_W = 220.0                 # max between the Lab Rax posts is ~222
DEPTH = 235.2                  # behind the panel; same as the notebook case (ends at the rear posts)
WALL = 2.5
FLOOR = 3.0
LID_T = 2.5
Z_TOP = PANEL_H - LID_T        # top of the walls / underside of the lid
X_IN0, X_IN1 = WALL, BODY_W - WALL
Y_IN1 = DEPTH - WALL           # rear wall inner face
CX = BODY_W / 2

# ---------------------------------------------------------------- column / divider
COL_X1 = 90.5                  # column is X_IN0..COL_X1 (88 wide)
DIV_T = 3.0
DIV_X0, DIV_X1 = COL_X1, COL_X1 + DIV_T
FAN_DEPTH = 25.0
DIV_Y0 = FAN_DEPTH + 3.0       # divider starts behind the fans so the 120 mm fan has room

# ---------------------------------------------------------------- drives (SFF-8301, 3.5")
DRIVE_L, DRIVE_H, DRIVE_T = 147.0, 101.6, 26.1   # standing on edge: L along Y, H up, T along X
SLOT_W = DRIVE_T + 0.6
N_DRIVES = 4
RIB_W = (X_IN1 - DIV_X1 - N_DRIVES * SLOT_W) / (N_DRIVES - 1)
RIB_H = 12.0
SLOT_X0 = [DIV_X1 + i * (SLOT_W + RIB_W) for i in range(N_DRIVES)]
DRIVE_Y0 = 36.0
DRIVE_Y1 = DRIVE_Y0 + DRIVE_L
STOP_Y0 = DRIVE_Y0 - 2.0
STOP_H = 8.0
DRIVE_TOP = FLOOR + DRIVE_H
COMB_GAP = 0.8                 # drive top -> comb bar
COMB_Y = (70.0, 150.0)         # comb bars' front faces
COMB_T = 5.0
COMB_FINGER = 10.0             # fingers between drives reach this far below the bar

# ---------------------------------------------------------------- fans
FAN120 = dict(size=120.0, hole=105.0, grille=114.0, cx=(DIV_X1 + X_IN1) / 2 + 0.5, cz=PANEL_H / 2)
FAN80 = dict(size=80.0, hole=71.5, grille=76.0, cx=52.0, cz=88.0)
FAN_SCREW_D = 4.4

# ---------------------------------------------------------------- PSU (Flex ATX / "1U")
PSU_W, PSU_H, PSU_L = 81.5, 40.5, 150.0
PSU_X0 = (X_IN0 + COL_X1) / 2 - PSU_W / 2
PSU_Y0 = Y_IN1 - PSU_L
PSU_WIN = (76.0, 36.0)          # rear-wall opening; the wall rim stops the PSU sliding out
PSU_RAIL_H = 6.0
PSU_STOP_H = 5.0                # low, so the PSU tilts over it while sliding back
PSU_DROP_Y = 43.5               # PSU drops in this far forward (clear of the rear-west boss), then slides back
CABLE_CHANNEL = 10.0            # over the PSU, under the board shelf

# ---------------------------------------------------------------- ZimaBoard 832 (in its heatsink shell)
ZB_L, ZB_W, ZB_H = 138.7, 81.4, 31.0
SHELF_T = 3.0
LEDGE_P, LEDGE_T = 2.5, 2.0     # ledge protrusion and thickness (plus a 45 deg chamfer below)
LOW_LEDGE_TOP = FLOOR + PSU_H + CABLE_CHANNEL
ZB_Z0 = LOW_LEDGE_TOP + SHELF_T
ZB_X0 = (X_IN0 + COL_X1) / 2 - ZB_W / 2
ZB_Y0 = Y_IN1 - ZB_L            # I/O end against the rear wall
BOARD_SHELF_Y0 = ZB_Y0 - 6.0

# ---------------------------------------------------------------- HBA (generic low-profile PCIe card)
HBA_L, HBA_W, HBA_H = 168.0, 69.0, 20.0
HBA_PAD = 3.0                   # printed pads under the card
UP_LEDGE_TOP = ZB_Z0 + ZB_H + 11.0  # 11 mm of air over the ZimaBoard's fins
HBA_SHELF_Y0, HBA_SHELF_Y1 = 30.0, 222.0
HBA_X0 = (X_IN0 + COL_X1) / 2 - HBA_W / 2
HBA_Y0 = 42.0
HBA_Z0 = UP_LEDGE_TOP + SHELF_T + HBA_PAD

# ledge segments (Y ranges). Board shelf rests on LOW, passes UP through notches.
LOW_LEDGES = {"west": [(95, 115), (140, 160), (200, 220)], "div": [(95, 115), (140, 160)]}
UP_LEDGES = {"west": [(40, 60), (118, 137), (170, 195)], "div": [(40, 60), (118, 137)]}
DIV_WIN = (165.0, Y_IN1 - 4.0, FLOOR + PSU_H + 1.0, Z_TOP - 4.0)  # y0, y1, z0, z1 (cable window)

# ---------------------------------------------------------------- lid screws (M3 heat-set inserts)
BOSS = 8.0
BOSS_H = 9.5                    # solid block under the lid; a 45 deg chamfer below it
INSERT_D, INSERT_DEPTH = 4.0, 6.5
LID_HOLE_D = 3.4
BOSSES = {  # name: (x0, y0, wedge side) — wedge side = the wall it grows from
    "front_west": (X_IN0, 0.0, "post"),
    "front_east": (X_IN1 - BOSS, 26.0, "east"),
    "rear_west": (X_IN0, Y_IN1 - BOSS, "west"),
    "rear_east": (X_IN1 - BOSS, Y_IN1 - BOSS, "east"),
    "mid_div": (DIV_X0 - BOSS, DIV_Y0 + 2.0, "div"),
}
CLEAR = 0.5

# ---------------------------------------------------------------- rear wall / front panel features
ZB_WIN_MARGIN = 2.0
DC_HOLE_D, DC_HOLE_X, DC_HOLE_Z = 9.0, 80.0, (FLOOR + PSU_H + LOW_LEDGE_TOP) / 2 + 1
BUTTON_HOLE_D, BUTTON_X, BUTTON_Z = 16.2, 30.0, 26.0   # latching button wired to PS_ON
SLOT_VENT_W, SLOT_VENT_PITCH = 4.0, 8.0


# ================================================================= geometry helpers
def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(cx, cy, cz, d, h, axis="z", seg=40):
    m = Manifold.cylinder(h, d / 2, d / 2, seg, True)
    if axis == "y":
        m = m.rotate([90, 0, 0])
    elif axis == "x":
        m = m.rotate([0, 90, 0])
    return m.translate([cx, cy, cz])


def union(parts):
    parts = [p for p in parts if p is not None]
    return Manifold.batch_boolean(parts, OpType.Add) if len(parts) > 1 else parts[0]


def _ccw(pts):
    a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return pts if a > 0 else pts[::-1]


def prism_y(pts_xz, y0, y1):
    """Extrude an XZ polygon along Y from y0 to y1."""
    cs = CrossSection([_ccw(list(pts_xz))])
    return cs.extrude(y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def ledge(side, y0, y1, ztop, p=LEDGE_P):
    """Ledge with a 45 deg chamfer below, on the west wall (+X) or the divider's column face (-X)."""
    t = LEDGE_T
    if side == "west":
        x = X_IN0
        pts = [(x - 0.01, ztop), (x + p, ztop), (x + p, ztop - t), (x - 0.01, ztop - t - p)]
    else:
        x = DIV_X0
        pts = [(x + 0.01, ztop), (x - p, ztop), (x - p, ztop - t), (x + 0.01, ztop - t - p)]
    return prism_y(pts, y0, y1)


def boss(x0, y0, side):
    zt = Z_TOP
    zb = zt - BOSS_H
    if side == "post":
        body = box(x0, y0, FLOOR - 0.01, x0 + BOSS, y0 + BOSS, zt)
    else:
        body = box(x0, y0, zb, x0 + BOSS, y0 + BOSS, zt)
        if side == "west":
            w = [(x0 - 0.01, zb + 0.01), (x0 + BOSS, zb + 0.01), (x0 - 0.01, zb - BOSS)]
        else:  # grows from a wall on its east side (east wall, or divider for mid_div)
            x1 = x0 + BOSS
            w = [(x1 + 0.01, zb + 0.01), (x0, zb + 0.01), (x1 + 0.01, zb - BOSS)]
        body = body + prism_y(w, y0, y0 + BOSS)
    hole = cyl(x0 + BOSS / 2, y0 + BOSS / 2, zt - INSERT_DEPTH / 2 + 0.01, INSERT_D, INSERT_DEPTH + 0.02)
    return body, hole


def fan_cuts(f, y0, y1):
    """Round-hole grille + 4 screw holes through a wall spanning y0..y1 (fan axis = Y)."""
    cuts = []
    pitch, d = 6.5, 5.2
    r = f["grille"] / 2
    n = int(r / pitch) + 2
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            x = i * pitch + (pitch / 2 if j % 2 else 0)
            z = j * pitch * math.sqrt(3) / 2
            if math.hypot(x, z) + d / 2 <= r:
                cuts.append(cyl(f["cx"] + x, (y0 + y1) / 2, f["cz"] + z, d, y1 - y0 + 2, "y", 16))
    h = f["hole"] / 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            cuts.append(cyl(f["cx"] + sx * h, (y0 + y1) / 2, f["cz"] + sz * h, FAN_SCREW_D, y1 - y0 + 2, "y", 20))
    return cuts


def slot_vents_y(x0, x1, z0, z1, y0, y1):
    """Vertical slot vents through a wall spanning y0..y1."""
    cuts = []
    x = x0
    while x + SLOT_VENT_W <= x1:
        cuts.append(box(x, y0 - 1, z0, x + SLOT_VENT_W, y1 + 1, z1))
        x += SLOT_VENT_PITCH
    return cuts


def fan_box(f, y0):
    s = f["size"]
    return box(f["cx"] - s / 2, y0 + 0.05, f["cz"] - s / 2, f["cx"] + s / 2, y0 + FAN_DEPTH, f["cz"] + s / 2)


# ================================================================= components (for clearance + renders)
def components():
    c = {}
    for i, x0 in enumerate(SLOT_X0):
        x = x0 + (SLOT_W - DRIVE_T) / 2
        c[f"drive{i}"] = box(x, DRIVE_Y0, FLOOR, x + DRIVE_T, DRIVE_Y1, DRIVE_TOP)
    c["psu"] = box(PSU_X0, PSU_Y0, FLOOR, PSU_X0 + PSU_W, Y_IN1, FLOOR + PSU_H)
    c["zimaboard"] = box(ZB_X0, ZB_Y0, ZB_Z0, ZB_X0 + ZB_W, Y_IN1, ZB_Z0 + ZB_H)
    c["hba"] = box(HBA_X0, HBA_Y0, HBA_Z0, HBA_X0 + HBA_W, HBA_Y0 + HBA_L, HBA_Z0 + HBA_H)
    c["fan120"] = fan_box(FAN120, 0.0)
    c["fan80"] = fan_box(FAN80, 0.0)
    return c


# ================================================================= tray
def build_tray():
    adds, cuts = [], []
    # shell
    adds.append(box(0, -0.01, 0, BODY_W, DEPTH, FLOOR))
    adds.append(box(0, -0.01, 0, WALL, DEPTH, Z_TOP))
    adds.append(box(X_IN1, -0.01, 0, BODY_W, DEPTH, Z_TOP))
    adds.append(box(0, Y_IN1, 0, BODY_W, DEPTH, Z_TOP))
    adds.append(box(CX - PANEL_W / 2, -PANEL_T, 0, CX + PANEL_W / 2, 0.0, PANEL_H))
    # divider
    adds.append(box(DIV_X0, DIV_Y0, FLOOR - 0.01, DIV_X1, Y_IN1 + 0.01, Z_TOP))
    y0, y1, z0, z1 = DIV_WIN
    cuts.append(box(DIV_X0 - 1, y0, z0, DIV_X1 + 1, y1, z1))
    # drive cage: ribs between slots, front stop bar
    for i in range(N_DRIVES - 1):
        x = SLOT_X0[i] + SLOT_W
        adds.append(box(x, DRIVE_Y0, FLOOR - 0.01, x + RIB_W, DRIVE_Y1, FLOOR + RIB_H))
    adds.append(box(DIV_X1 - 0.01, STOP_Y0, FLOOR - 0.01, X_IN1 + 0.01, DRIVE_Y0, FLOOR + STOP_H))
    # PSU side rails and front stop
    for x in (PSU_X0 - 2.5, PSU_X0 + PSU_W + 0.5):
        adds.append(box(x, PSU_Y0 + 10, FLOOR - 0.01, x + 2.0, Y_IN1, FLOOR + PSU_RAIL_H))
    adds.append(box(PSU_X0 + 10, PSU_Y0 - 3.5, FLOOR - 0.01, PSU_X0 + PSU_W - 10, PSU_Y0 - 0.5, FLOOR + PSU_STOP_H))
    # shelf ledges
    for side, segs in LOW_LEDGES.items():
        for a, b in segs:
            adds.append(ledge("west" if side == "west" else "div", a, b, LOW_LEDGE_TOP))
    for side, segs in UP_LEDGES.items():
        for a, b in segs:
            adds.append(ledge("west" if side == "west" else "div", a, b, UP_LEDGE_TOP))
    # lid bosses
    for name, (x0, y0, side) in BOSSES.items():
        b, h = boss(x0, y0, side)
        adds.append(b)
        cuts.append(h)
    # front panel: fans, power button, rack-ear slots
    cuts += fan_cuts(FAN120, -PANEL_T, 0)
    cuts += fan_cuts(FAN80, -PANEL_T, 0)
    cuts.append(cyl(BUTTON_X, -PANEL_T / 2, BUTTON_Z, BUTTON_HOLE_D, PANEL_T + 2, "y"))
    for sx in (-1, 1):
        ex = CX + sx * EAR_HOLE_SPACING / 2
        for z in EAR_HOLE_Z:
            dx = (EAR_SLOT_L - EAR_SLOT_D) / 2
            for s in (-1, 1):
                cuts.append(cyl(ex + s * dx, -PANEL_T / 2, z, EAR_SLOT_D, PANEL_T + 2, "y"))
            cuts.append(box(ex - dx, -PANEL_T - 1, z - EAR_SLOT_D / 2, ex + dx, 1, z + EAR_SLOT_D / 2))
    # rear wall: PSU window, ZimaBoard I/O window, DC cable hole, vents
    pw, ph = PSU_WIN
    pcx, pcz = PSU_X0 + PSU_W / 2, FLOOR + PSU_H / 2
    cuts.append(box(pcx - pw / 2, Y_IN1 - 1, pcz - ph / 2, pcx + pw / 2, DEPTH + 1, pcz + ph / 2))
    m = ZB_WIN_MARGIN
    cuts.append(box(ZB_X0 + m, Y_IN1 - 1, ZB_Z0 + m, ZB_X0 + ZB_W - m, DEPTH + 1, ZB_Z0 + ZB_H - m))
    cuts.append(cyl(DC_HOLE_X, DEPTH - WALL / 2, DC_HOLE_Z, DC_HOLE_D, WALL + 2, "y"))
    cuts += slot_vents_y(DIV_X1 + 6, X_IN1 - BOSS - 4, FLOOR + 12, Z_TOP - 12, Y_IN1, DEPTH)
    cuts += slot_vents_y(X_IN0 + BOSS + 4, COL_X1 - 6, ZB_Z0 + ZB_H + 4, Z_TOP - 6, Y_IN1, DEPTH)
    tray = union(adds) - union(cuts)
    return tray


# ================================================================= shelves
def _shelf_plate(y0, y1, z):
    x0, x1 = X_IN0 + CLEAR, COL_X1 - CLEAR
    return box(x0, y0, z, x1, y1, z + SHELF_T), x0, x1


def _strap_slots(x0, x1, ys, z):
    """Pairs of 3 x 22 mm slots for a hook-and-loop strap, just outside x0..x1."""
    cuts = []
    for y in ys:
        for x in (x0 - 4.5, x1 + 1.5):
            cuts.append(box(x, y - 11, z - 1, x + 3, y + 11, z + SHELF_T + 1))
    return cuts


def build_board_shelf():
    z = LOW_LEDGE_TOP
    plate, x0, x1 = _shelf_plate(BOARD_SHELF_Y0, Y_IN1 - CLEAR, z)
    cuts = []
    n = LEDGE_P + CLEAR
    for side, segs in UP_LEDGES.items():
        for a, b in segs:
            if b < BOARD_SHELF_Y0:
                continue
            xs = (x0 - 1, x0 + n) if side == "west" else (x1 - n, x1 + 1)
            cuts.append(box(xs[0], a - CLEAR, z - 1, xs[1], b + CLEAR, z + SHELF_T + 1))
    bx, by, _ = BOSSES["rear_west"]
    cuts.append(box(x0 - 1, by - CLEAR, z - 1, bx + BOSS + CLEAR, Y_IN1 + 1, z + SHELF_T + 1))
    # air holes under the board
    for yy in np.arange(ZB_Y0 + 15, Y_IN1 - 15, 14):
        cuts.append(box(ZB_X0 + 12, yy, z - 1, ZB_X0 + ZB_W - 12, yy + 7, z + SHELF_T + 1))
    cuts += _strap_slots(ZB_X0 + 3, ZB_X0 + ZB_W - 3, (ZB_Y0 + 30, Y_IN1 - 30), z)
    adds = [plate]
    # front stop for the board, two low side guides
    adds.append(box(ZB_X0 + 15, ZB_Y0 - 3, z + SHELF_T - 0.01, ZB_X0 + ZB_W - 15, ZB_Y0 - 0.5, z + SHELF_T + 6))
    return union(adds) - union(cuts)


def build_hba_shelf():
    z = UP_LEDGE_TOP
    plate, x0, x1 = _shelf_plate(HBA_SHELF_Y0, HBA_SHELF_Y1, z)
    cuts = []
    bx, by, _ = BOSSES["mid_div"]
    cuts.append(box(bx - CLEAR, by - CLEAR, z - 1, x1 + 1, by + BOSS + CLEAR, z + SHELF_T + 1))
    # riser cable slot in front of the ZimaBoard, and air holes under the card
    cuts.append(box(HBA_X0 + 4, ZB_Y0 - 22, z - 1, HBA_X0 + HBA_W - 4, ZB_Y0 - 8, z + SHELF_T + 1))
    for yy in np.arange(ZB_Y0 + 8, HBA_Y0 + HBA_L - 12, 14):
        cuts.append(box(HBA_X0 + 10, yy, z - 1, HBA_X0 + HBA_W - 10, yy + 7, z + SHELF_T + 1))
    cuts += _strap_slots(HBA_X0 + 2, HBA_X0 + HBA_W - 2, (HBA_Y0 + 35, HBA_Y0 + HBA_L - 35), z)
    adds = [plate]
    for yy in (HBA_Y0 + 6, HBA_Y0 + HBA_L / 2, HBA_Y0 + HBA_L - 10):  # pads under the card
        for xx in (HBA_X0 + 4, HBA_X0 + HBA_W - 10):
            adds.append(box(xx, yy - 3, z + SHELF_T - 0.01, xx + 6, yy + 3, z + SHELF_T + HBA_PAD))
    return union(adds) - union(cuts)


# ================================================================= lid
def build_lid():
    adds = [box(0, 0, Z_TOP, BODY_W, DEPTH, PANEL_H)]
    cuts = []
    comb_bot = DRIVE_TOP + COMB_GAP
    for y in COMB_Y:
        adds.append(box(DIV_X1 + 0.3, y, comb_bot, X_IN1 - 0.3, y + COMB_T, Z_TOP + 0.01))
        for i in range(N_DRIVES - 1):
            xr = SLOT_X0[i] + SLOT_W
            adds.append(box(xr + 0.5, y, comb_bot - COMB_FINGER, xr + RIB_W - 0.5, y + COMB_T, comb_bot + 0.01))
    for name, (x0, y0, _) in BOSSES.items():
        cuts.append(cyl(x0 + BOSS / 2, y0 + BOSS / 2, Z_TOP + LID_T / 2, LID_HOLE_D, LID_T + 2))
    cuts += [box(x, 40, Z_TOP - 1, x + SLOT_VENT_W, Y_IN1 - 20, PANEL_H + 1)
             for x in np.arange(X_IN0 + 16, COL_X1 - 10, SLOT_VENT_PITCH)]
    return union(adds) - union(cuts)


# ================================================================= checks
def overlap(a, b):
    return (a ^ b).volume()


def check(parts, comps):
    errs = []
    solid = union(list(parts.values()))
    for n, c in comps.items():
        v = overlap(c, solid)
        if v > 0.5:
            errs.append(f"{n} hits the printed parts ({v:.0f} mm3)")
    names = list(comps)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if overlap(comps[a], comps[b]) > 0.5:
                errs.append(f"{a} hits {b}")
    pn = list(parts)
    for i, a in enumerate(pn):
        for b in pn[i + 1:]:
            v = overlap(parts[a], parts[b])
            if v > 0.5:
                errs.append(f"part {a} hits part {b} ({v:.0f} mm3)")
    # shelves can be lowered into place: sweep each straight up to the lid and check against the tray
    for n in ("board_shelf", "hba_shelf"):
        bb = parts[n].bounding_box()
        sweep = union([parts[n].translate([0, 0, dz]) for dz in np.arange(0, Z_TOP - bb[5] + 0.01, 1.0)])
        v = overlap(sweep, parts["tray"])
        if v > 0.5:
            errs.append(f"{n} can't be lowered in ({v:.0f} mm3 in the way)")
    # PSU drops in past the ledges and bosses
    psu = comps["psu"]
    lift = PSU_STOP_H + 0.5
    path = [psu.translate([0, -PSU_DROP_Y, dz]) for dz in np.arange(lift, Z_TOP, 2.0)]
    path += [psu.translate([0, -dy, lift]) for dy in np.arange(0, PSU_DROP_Y + 0.01, 2.0)]
    v = overlap(union(path), parts["tray"])
    if v > 0.5:
        errs.append(f"psu can't be put in ({v:.0f} mm3)")
    for i in range(N_DRIVES):
        d = comps[f"drive{i}"]
        v = overlap(union([d.translate([0, 0, dz]) for dz in np.arange(0, 40, 2.0)]), parts["tray"])
        if v > 0.5:
            errs.append(f"drive{i} can't be lowered in ({v:.0f} mm3)")
    assert DRIVE_Y1 + 35 <= Y_IN1, "no room for drive connectors"
    assert FAN120["cx"] - 60 >= COL_X1 and FAN120["cx"] + 60 <= X_IN1, "120 fan doesn't fit"
    assert FAN80["cx"] - 40 >= X_IN0 + BOSS and FAN80["cx"] + 40 <= FAN120["cx"] - 60, "80 fan doesn't fit"
    assert HBA_Z0 + HBA_H <= Z_TOP - 3, "HBA hits the lid"
    assert PSU_W + 2 * 0.5 <= COL_X1 - X_IN0 - 2 * LEDGE_P, "PSU can't pass the ledges"
    return errs


# ================================================================= output
def to_trimesh(m, color=None):
    import trimesh
    mesh = m.to_mesh()
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    if color is not None:
        t.visual.face_colors = color
    return t


def main():
    os.makedirs(OUT, exist_ok=True)
    parts = {
        "tray": build_tray(),
        "lid": build_lid(),
        "board_shelf": build_board_shelf(),
        "hba_shelf": build_hba_shelf(),
    }
    comps = components()
    errs = check(parts, comps)
    for e in errs:
        print("CLEARANCE:", e)

    # print orientation: tray on its floor; lid upside down (combs up); shelves as they sit
    lid_print = parts["lid"].mirror([0, 0, 1])
    printable = {
        "tray": parts["tray"],
        "lid": lid_print,
        "board_shelf": parts["board_shelf"],
        "hba_shelf": parts["hba_shelf"],
    }
    for n, m in printable.items():
        bb = m.bounding_box()
        m = m.translate([-bb[0], -bb[1], -bb[2]])
        to_trimesh(m).export(os.path.join(OUT, f"{n}.stl"))
        print(f"{n}.stl  {bb[3]-bb[0]:.1f} x {bb[4]-bb[1]:.1f} x {bb[5]-bb[2]:.1f} mm  "
              f"{m.volume()/1000:.0f} cm3  genus {m.genus()}  status {m.status()}")

    colors = {"tray": (200, 205, 215, 255), "lid": (200, 205, 215, 255), "board_shelf": (240, 160, 60, 255),
              "hba_shelf": (240, 160, 60, 255)}
    ccol = {"drive": (90, 110, 140, 255), "psu": (60, 60, 60, 255), "zimaboard": (150, 150, 160, 255),
            "hba": (40, 140, 70, 255), "fan120": (30, 30, 30, 255), "fan80": (30, 30, 30, 255)}

    def cm(n):
        return ccol["drive"] if n.startswith("drive") else ccol[n]

    comp_meshes = [(to_trimesh(m), cm(n)) for n, m in comps.items()]
    tm = {n: to_trimesh(m) for n, m in parts.items()}

    import trimesh
    scene = trimesh.Scene()
    for n, t in tm.items():
        t2 = t.copy()
        t2.visual.face_colors = colors[n]
        scene.add_geometry(t2, node_name=n)
    for (t, c), n in zip(comp_meshes, comps):
        t2 = t.copy()
        t2.visual.face_colors = c
        scene.add_geometry(t2, node_name=n)
    # lid in print orientation, for the lid render
    t = to_trimesh(lid_print.translate([0, 0, 2 * PANEL_H]))
    t.visual.face_colors = colors["lid"][:3] + (255,)
    scene.add_geometry(t, node_name="lid_print")
    scene.export(os.path.join(OUT, "assembly.glb"))

    with open(os.path.join(OUT, "dimensions.txt"), "w") as f:
        f.write(f"front panel: {PANEL_W} x {PANEL_H:.2f} mm (3U, 10\")\n")
        f.write(f"body: {BODY_W} W x {DEPTH + PANEL_T:.1f} D x {PANEL_H:.2f} H mm (depth incl. panel)\n")
        f.write(f"rack ear slots Z (from panel bottom): {', '.join(f'{z:.2f}' for z in EAR_HOLE_Z)}\n")
        f.write(f"column X {X_IN0}-{COL_X1}, divider X {DIV_X0}-{DIV_X1}, cage X {DIV_X1}-{X_IN1}\n")
        f.write(f"drive slots {SLOT_W:.1f} wide, ribs {RIB_W:.2f}; drives Y {DRIVE_Y0}-{DRIVE_Y1}, "
                f"top Z {DRIVE_TOP:.1f}; {Y_IN1 - DRIVE_Y1:.1f} mm behind them for connectors\n")
        f.write(f"slot X: {', '.join(f'{x:.1f}' for x in SLOT_X0)}\n")
        f.write(f"PSU (Flex ATX {PSU_W}x{PSU_H}x{PSU_L}): X {PSU_X0:.1f}, Y {PSU_Y0:.1f}-{Y_IN1}, Z {FLOOR}-{FLOOR+PSU_H}\n")
        f.write(f"board shelf top Z {LOW_LEDGE_TOP + SHELF_T:.1f}; ZimaBoard Z {ZB_Z0:.1f}-{ZB_Z0+ZB_H:.1f}, "
                f"Y {ZB_Y0:.1f}-{Y_IN1}\n")
        f.write(f"HBA shelf top Z {UP_LEDGE_TOP + SHELF_T:.1f}; card envelope {HBA_L}x{HBA_W}x{HBA_H} at "
                f"Z {HBA_Z0:.1f}-{HBA_Z0+HBA_H:.1f}; lid underside Z {Z_TOP:.2f}\n")
        f.write(f"fans: 120 mm at X {FAN120['cx']:.1f} Z {FAN120['cz']:.1f}; 80 mm at X {FAN80['cx']} Z {FAN80['cz']}\n")
        f.write(f"power button hole {BUTTON_HOLE_D} mm at X {BUTTON_X} Z {BUTTON_Z}; "
                f"DC cable hole {DC_HOLE_D} mm rear at X {DC_HOLE_X} Z {DC_HOLE_Z:.1f}\n")
        f.write(f"tray footprint for printing: {PANEL_W:.0f} x {DEPTH + PANEL_T:.0f} x {PANEL_H:.0f} mm\n")
        f.write("clearance check: " + ("OK" if not errs else "; ".join(errs)) + "\n")
    print(open(os.path.join(OUT, "dimensions.txt")).read())


if __name__ == "__main__":
    main()
