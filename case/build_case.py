"""10-inch rack, 1U case for the homelab notebook board. 3D-printable.

Run headless (needs board/out/board.glb from board/build_board.py first):
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python case/build_case.py -- case/out

Coordinates are the board's (mm): X = west edge of the board's wide section,
Y = south edge of the board, Z = bottom of the case. North (ports) faces the
front of the rack.

Layout:
  * Board on 7 standoffs (its 7 mounting holes), pushed against the west wall.
    No screws: each standoff ends in a pin that the hole presses over (size it
    with pin_gauge.stl).
  * 2.5" drive flat on the floor, under the board's wide section just north of
    the SW notch (the tab's own mounting holes rule out putting it under the
    tab), long side east-west, connector at the east end toward the SATA
    ribbon header in the board's SE corner.
  * Stock blower fan (fan/, traced from photos) lives in the SW notch, top
    flush with the board, on two posts at its M2.5 holes, outlet against the
    west wall. Forced air path, as in the
    laptop: intake grill in the lid above the CPU block -> CPU block -> fan ->
    exhaust grill in the west wall beside the notch. No other vents, so the
    fan pulls everything through the CPU block.
  * Ethernet: the board has half of a laptop "drop-jaw" jack. The plug rests,
    contacts down, on springs in a housing under the board, its body passing
    up through a board cutout, latch up. A printed hood on top, hanging off the
    front panel, supplies the rest: side walls, a ceiling that holds the plug
    down on the springs, a nose stop, and a lip the plug's own spring latch
    snaps behind. Press the latch (on top) to release, like any RJ45 jack.

Parts to print: tray (floor + walls + front panel with rack ears) and lid.
Test first: pin_gauge.stl, a row of pins around the hole size to pick a snug
PIN_D; rj45_test.stl, a small cut of the panel + hood to check plug fit;
fit_test.stl (panel strip + the H1/H2 board mounts on a light frame, lowered) to
check the port openings against the real board (snug PIN_D pins: two pins must hold it square);
fit_childboard.stl for the child board's holes.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "board"))
import build_board as brd  # noqa: E402

# ---------------------------------------------------------------- rack
U = 44.45
PANEL_H = 43.66            # 1U panel, EIA gap
PANEL_W = 254.0            # 10" rack panel
PANEL_T = 3.0
EAR_HOLE_SPACING = 236.525  # 10" rack horizontal hole pitch
EAR_HOLE_Z = (6.35, 38.1)   # outer holes of the U, from U boundary
EAR_SLOT_D, EAR_SLOT_L = 6.5, 10.0

# ---------------------------------------------------------------- case
BODY_W = 220.0             # max between 10" rails is ~222
WALL = 2.5
FLOOR = 2.5
LID_T = 2.0
GAP_SOUTH = 15.0           # room south of the board for cable loops

# ---------------------------------------------------------------- drive (SFF-8201)
# Long side east-west, to match the SATA ribbon; connector at the east end
# (ribbon header is in the board's SE corner).
DRIVE_SX, DRIVE_SY, DRIVE_T = 100.0, 69.85, 9.5  # footprint X, Y; 9.5 covers 7 mm drives too
DRIVE_X0, DRIVE_Y0 = 9.0, 66.0                   # SW corner; boxed in by standoffs H4/H5/H7
DRIVE_BOSS_H, DRIVE_BOSS_D = 3.0, 7.0
# bottom holes: 14.0 / 90.6 from the connector end, 4.07 / 65.79 from a long side
DRIVE_HOLES = [(DRIVE_SX - a, b) for a in (14.0, 90.6) for b in (4.07, 65.79)]  # from SW corner
SCREW_CLEAR = 3.4          # M3 clearance
SCREW_CBORE_D, SCREW_CBORE_H = 6.5, 1.5

# ---------------------------------------------------------------- board mount
BOARD_TOP_CLEAR = 15.6     # board top surface -> lid underside (halfway between 8.5 and the original 22.7): CPU block near the
                           # lid intake, roomy intake plenum for the fan
BOARD_Z = PANEL_H - LID_T - BOARD_TOP_CLEAR - brd.PCB_T   # board bottom
STANDOFF_D = 7.5          # tall standoffs now (~30 mm), so thicker
PILOT = 2.5                # M3 self-tapping into the print (lid screws)
PIN_D = 3.40               # standoff pin through the board's 3.56 mm holes; pick from pin_gauge.stl
PIN_ABOVE = 2.0            # pin length above the board top
PIN_CHAMFER = 0.4          # lead-in at the pin tip
GAUGE_PINS = [3.20 + 0.05 * i for i in range(9)]   # 3.20 .. 3.60

# ---------------------------------------------------------------- lid
POST = 7.0                 # corner posts for lid screws
VENT_W, VENT_PITCH = 3.0, 6.0
PORT_MARGIN = 1.0
# Fit test 1: board 3.5 mm north, ports into the panel. Port fronts end this far
# behind its outer face; the board edge and RJ45 jack get pockets in its inner face.
PORT_RECESS = 1.0
EDGE_CLEAR = 0.5           # board edge / RJ45 jack -> pocket walls

# ---------------------------------------------------------------- RJ45 hood (estimates; tune with rj45_test.stl)
# First print (11.9 / 6.8 / 6.6) was too tight for the plug to go in at all.
RJ45_OPEN_W = 12.7         # plug width 11.68 (8P8C standard) + 0.5 per side
RJ45_BODY_H = 7.4          # plug insertion-area height 6.60 + 0.8
RJ45_LATCH_W = 7.4         # slot for the plug's latch
RJ45_LATCH_FACE_H = 8.4    # plug overall height 8.00; top of latch slot = the catch lip
RJ45_POCKET_H = 11.0       # behind the lip the latch springs back up into this pocket
RJ45_WALL = 2.0

# ---------------------------------------------------------------- derived
_xs = [x for x, _ in brd.outline_mm()]
_ys = [y for _, y in brd.outline_mm()]
BOARD_NORTH = max(_ys)
NOTCH_X = brd.px2mm(780, 1150)[0]   # tab west edge
NOTCH_Y = brd.px2mm(780, 1126)[1]   # wide section south edge

# ---------------------------------------------------------------- fan (from fan/out/fan.json)
# Where the fan sat in the laptop: its two screw holes triangulated against H4 and
# H7 (caliper, near edge to near edge; fan holes 2.7 mm): F1-H7 55.8, F1-H4 13.0,
# F2-H4 90.74, F2-H7 76.5, F1-F2 77.2. Least-squares centres, residuals <= 0.02 mm.
# The fan body goes on their midpoint; it sits ~0.8 deg turned there, ignored
# (<= 0.5 mm at its corners). The west wall goes against the fan's outlet.
# Solved in the photo frame; levelled with the board (brd.level).
FAN = json.load(open(os.path.join(HERE, "..", "fan", "out", "fan.json")))
FAN_HOLES = [brd.level(*p) for p in [(60.26, 52.12), (11.36, -11.08)]]   # F1 (screw ear), F2
FAN_GAP = 0.5                                        # outlet face -> inner west wall
FAN_X0, FAN_Y0 = (sum(m[i] - f[i] for m, f in zip(FAN_HOLES, FAN["holes"])) / 2 for i in (0, 1))

X_IN0 = FAN_X0 - FAN_GAP
X_OUT0 = X_IN0 - WALL
X_OUT1 = X_OUT0 + BODY_W
X_IN1 = X_OUT1 - WALL
Y_IN0 = -GAP_SOUTH
Y_OUT0 = Y_IN0 - WALL
Y_FRONT = brd.PORT_FRONT_Y + PORT_RECESS - PANEL_T   # panel inner face
Z_TOP = PANEL_H - LID_T                            # top of walls / bottom of lid
CX = (X_OUT0 + X_OUT1) / 2

RJ45_CX = brd.rj45_center_x()
RJ45_FLOOR = BOARD_Z - brd.RJ45_PLUG_FLOOR              # plug's contact face, on the springs
RJ45_FRAME_TOP = BOARD_Z + brd.PCB_T + brd.RJ45_TOP_H   # top-side frame around the cutout
RJ45_STOP_Y = brd.rj45_frame_rect()[1]                 # nose stop = back wall of the frame
_cpu = next(r for n, r, _, _ in brd.PARTS if n == "cpu_heatplate")
CPU_RECT = brd.rect_mm(*_cpu)
TALLEST = max([p[3] for p in brd.PORTS] + [p[2] for p in brd.PARTS])

FAN_Z0 = BOARD_Z + brd.PCB_T - FAN["thickness"]      # fan top flush with the board top
FAN_POST_D, FAN_PILOT = 7.0, 2.1                     # M2.5 self-tapping
assert FAN_X0 + FAN["width_x"] <= NOTCH_X - 0.5, "fan does not fit the notch"
assert FAN_Y0 >= Y_IN0 + 0.3, "fan hits the rear wall"
assert FAN_Y0 + FAN["depth_y"] <= NOTCH_Y - 0.3, "fan hits the board's south edge"
assert min(_xs) >= X_IN0 + 1.0, "board hits the west wall"
assert RJ45_FLOOR + RJ45_POCKET_H <= Z_TOP - 0.5, "RJ45 latch pocket hits the lid"

# ---------------------------------------------------------------- I/O child board (childboard/out/childboard.json)
# Rear wall, under the motherboard's tab, east of the fan: its ribbon (MB_CONN) can
# reach the motherboard's south-edge connector. Jacks (USB-A, audio) face the rear.
CB = json.load(open(os.path.join(HERE, "..", "childboard", "out", "childboard.json")))
CB_X0 = NOTCH_X + 1.0                                 # clear of the fan
CB_Y0 = Y_IN0 - CB["depth_y"][0] + 0.3                # PCB's southmost tab just off the rear wall
CB_Z0 = FLOOR + 3.6                                   # PCB bottom: jacks hang 3.2 below it
CB_POST_D, CB_PILOT = 5.0, 1.7                        # M2 self-tapping (board says M2xL2.5)
MB_RIBBON_PX = (870, 1440, 1005, 1465)                # motherboard header the ribbon plugs into (assumed)
assert CB_Z0 + CB["z_range"][1] < BOARD_Z - 3, "child board hits the motherboard"


# ---------------------------------------------------------------- helpers
def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def mesh_obj(name, bm, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    return obj


def box(name, x0, y0, z0, x1, y1, z1, coll):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return mesh_obj(name, bm, coll)


def cyl(name, x, y, z, d, h, coll, axis="Z", seg=48):
    """Cylinder centered on (x, y, z) along axis, length h."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=d / 2, radius2=d / 2, depth=h)
    if axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(1.5708, 3, "X"))
    bmesh.ops.translate(bm, vec=(x, y, z), verts=bm.verts)
    return mesh_obj(name, bm, coll)


def pin(name, x, y, z0, d, h, coll):
    """Pin standing on z0, chamfered tip (one closed solid)."""
    bm = bmesh.new()
    body = h - PIN_CHAMFER
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=d / 2, radius2=d / 2, depth=body)
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    ext = bmesh.ops.extrude_face_region(bm, geom=[top])
    tip = [v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)]
    s = 1 - 2 * PIN_CHAMFER / d
    bmesh.ops.scale(bm, vec=(s, s, 1), verts=tip)
    bmesh.ops.translate(bm, vec=(0, 0, PIN_CHAMFER), verts=tip)
    bmesh.ops.delete(bm, geom=[top], context="FACES_ONLY")
    bmesh.ops.translate(bm, vec=(x, y, z0 + body / 2), verts=bm.verts)
    return mesh_obj(name, bm, coll)


def boolean(target, operation, coll):
    mod = target.modifiers.new(f"{operation}_{coll.name}", "BOOLEAN")
    mod.operation = operation
    mod.solver = "EXACT"
    mod.operand_type = "COLLECTION"
    mod.collection = coll
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def material(name, rgba, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgba[:3], alpha)
    return m


def vent_slots(prefix, coll, along, lo, hi, fixed, span, z0=None, z1=None):
    """Parallel slots. along='X': slots step in X, run in Y over span (y0, y1).
    along='Y' (west wall): slots step in Y, run in Z over (z0, z1); fixed=(x0, x1)."""
    n = 0
    p = lo
    while p + VENT_W <= hi:
        if along == "X":
            box(f"{prefix}{n}", p, span[0], fixed[0], p + VENT_W, span[1], fixed[1], coll)
        else:
            box(f"{prefix}{n}", fixed[0], p, z0, fixed[1], p + VENT_W, z1, coll)
        p += VENT_PITCH
        n += 1


def post_xy():
    return [
        (X_IN0, Y_IN0), (X_IN1 - POST, Y_IN0),
        (X_IN0, Y_FRONT - POST), (X_IN1 - POST, Y_FRONT - POST),
    ]


def _clip(p, q, x0, y0, x1, y1):
    """Segment p-q clipped to a rectangle (Liang-Barsky): its end points, or []."""
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for d, e in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if d == 0:
            if e < 0:
                return []
        elif d < 0:
            t0 = max(t0, e / d)
        else:
            t1 = min(t1, e / d)
    return [] if t0 > t1 else [(p[0] + t * dx, p[1] + t * dy) for t in (t0, t1)]


def post_notch(px, py):
    """(x0, y0, x1, y1): the part of a corner post the board outline (+ EDGE_CLEAR)
    reaches, out to the post's inner sides; None if clear."""
    c, ol = EDGE_CLEAR, brd.outline_mm()
    pts = [v for a, b in zip(ol, ol[1:] + ol[:1])
           for v in _clip(a, b, px - c, py - c, px + POST + c, py + POST + c)]
    if not pts:
        return None
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    x0, x1 = (min(xs) - c, px + POST + 0.01) if px < CX else (px - 0.01, max(xs) + c)
    y0, y1 = (py - 0.01, max(ys) + c) if py > 0 else (min(ys) - c, py + POST + 0.01)
    return x0, y0, x1, y1


# ---------------------------------------------------------------- RJ45 hood
def rj45_hood_adds(coll):
    w = RJ45_OPEN_W / 2 + RJ45_WALL
    top = min(RJ45_FLOOR + RJ45_POCKET_H + RJ45_WALL, Z_TOP)   # the lid caps the latch pocket
    # hood: sits 0.3 above the top-side frame, hangs off the panel
    box("rj45_hood", RJ45_CX - w, RJ45_STOP_Y - RJ45_WALL, RJ45_FRAME_TOP + 0.3,
        RJ45_CX + w, Y_FRONT + 0.01, top, coll)


def rj45_hood_cuts(coll):
    hw, lw = RJ45_OPEN_W / 2, RJ45_LATCH_W / 2
    # plug body channel, through the panel back to the nose stop
    box("rj45_body", RJ45_CX - hw, RJ45_STOP_Y, RJ45_FLOOR,
        RJ45_CX + hw, Y_FRONT + PANEL_T + 1, RJ45_FLOOR + RJ45_BODY_H, coll)
    # latch slot in the panel face (its top edge is the catch lip)
    box("rj45_latch_slot", RJ45_CX - lw, Y_FRONT - 0.01, RJ45_FLOOR,
        RJ45_CX + lw, Y_FRONT + PANEL_T + 1, RJ45_FLOOR + RJ45_LATCH_FACE_H, coll)
    # latch pocket behind the lip
    box("rj45_latch_pocket", RJ45_CX - lw - 0.2, RJ45_STOP_Y, RJ45_FLOOR,
        RJ45_CX + lw + 0.2, Y_FRONT, RJ45_FLOOR + RJ45_POCKET_H, coll)


def build_rj45_coupon(tray, root):
    """Small test print: panel + hood around the jack, with stand-ins for the
    board's springs (floor) and top-side frame. Print panel-face down."""
    me = tray.data.copy()
    coupon = bpy.data.objects.new("RJ45_test", me)
    root.objects.link(coupon)
    work = new_coll("_work", root)
    keep = new_coll("_keep", work)
    w = 10.0
    y0 = RJ45_STOP_Y - RJ45_WALL - 1
    top = min(RJ45_FLOOR + RJ45_POCKET_H + RJ45_WALL, Z_TOP)   # the lid caps the latch pocket
    box("keep", RJ45_CX - w, y0, RJ45_FLOOR - 3, RJ45_CX + w, Y_FRONT + PANEL_T + 1, top + 1, keep)
    boolean(coupon, "INTERSECT", keep)
    add = new_coll("_add", work)
    hw, sw = RJ45_OPEN_W / 2, w - 0.5
    box("standin_floor", RJ45_CX - sw, y0 + 0.5, RJ45_FLOOR - 3, RJ45_CX + sw, Y_FRONT + 0.2, RJ45_FLOOR, add)
    for sx in (-1, 1):
        box(f"standin_frame{sx}", RJ45_CX + sx * hw, y0 + 0.5, RJ45_FLOOR - 0.01,
            RJ45_CX + sx * sw, Y_FRONT + 0.2, RJ45_FRAME_TOP + 0.5, add)   # 0.2 into the hood
    boolean(coupon, "UNION", add)
    bpy.data.collections.remove(work)
    return coupon


# ---------------------------------------------------------------- parts
def build_tray(root, pin_d=PIN_D):
    work = new_coll("_work", root)
    tray = box("Tray", X_OUT0, Y_OUT0, 0, X_OUT1, Y_FRONT, Z_TOP, root)

    cavity = new_coll("_cavity", work)
    box("cavity", X_IN0, Y_IN0, FLOOR, X_IN1, Y_FRONT + 1, Z_TOP + 1, cavity)
    boolean(tray, "DIFFERENCE", cavity)

    adds = new_coll("_adds", work)
    box("front_panel", CX - PANEL_W / 2, Y_FRONT, 0, CX + PANEL_W / 2, Y_FRONT + PANEL_T, PANEL_H, adds)
    for i, (x, y, _) in enumerate(brd.HOLES_MM):
        cyl(f"standoff_{i}", x, y, (FLOOR + BOARD_Z) / 2, STANDOFF_D, BOARD_Z - FLOOR + 0.01, adds)
        pin(f"pin_{i}", x, y, BOARD_Z - 0.01, pin_d, brd.PCB_T + PIN_ABOVE + 0.01, adds)
    for i, (dx, dy) in enumerate(DRIVE_HOLES):
        cyl(f"drive_boss_{i}", DRIVE_X0 + dx, DRIVE_Y0 + dy, FLOOR + DRIVE_BOSS_H / 2 - 0.01,
            DRIVE_BOSS_D, DRIVE_BOSS_H + 0.02, adds)
    for i, (px, py) in enumerate(post_xy()):
        box(f"post_{i}", px, py, FLOOR - 0.01, px + POST, py + POST, Z_TOP, adds)
    for i, (hx, hy) in enumerate(FAN_HOLES):
        cyl(f"fan_post_{i}", hx, hy, (FLOOR + FAN_Z0) / 2, FAN_POST_D, FAN_Z0 - FLOOR + 0.01, adds)
    for i, h in enumerate(CB["holes"]):
        cyl(f"cb_post_{i}", CB_X0 + h["x"], CB_Y0 + h["y"], (FLOOR + CB_Z0) / 2, CB_POST_D, CB_Z0 - FLOOR + 0.01, adds)
    rj45_hood_adds(adds)
    boolean(tray, "UNION", adds)

    cuts = new_coll("_cuts", work)
    # ports through the front panel
    top = BOARD_Z + brd.PCB_T
    for name, _, below, above, _ in brd.PORTS:
        ax, _, bx, _ = brd.port_rect(name)
        box(f"cut_{name}", ax - PORT_MARGIN, Y_FRONT - 1, BOARD_Z - below - PORT_MARGIN,
            bx + PORT_MARGIN, Y_FRONT + PANEL_T + 1, top + above + PORT_MARGIN, cuts)
    rj45_hood_cuts(cuts)
    # pockets in the panel's inner face: board north edge where it reaches in, and
    # the RJ45 jack (under the board, and its top-side frame)
    north = brd.outline_mm()[:6]
    for i, ((ax, ay), (bx, by)) in enumerate(zip(north, north[1:])):
        if ay == by and ay + EDGE_CLEAR > Y_FRONT:
            box(f"edge_pocket_{i}", ax - EDGE_CLEAR, Y_FRONT - 1, BOARD_Z - EDGE_CLEAR,
                bx + EDGE_CLEAR, ay + EDGE_CLEAR, top + EDGE_CLEAR, cuts)
    jx0, jx1 = brd.PORT_X["rj45"]
    box("rj45_jack_pocket", jx0 - EDGE_CLEAR, Y_FRONT - 1, BOARD_Z - brd.RJ45_JACK_BELOW - EDGE_CLEAR,
        jx1 + EDGE_CLEAR, brd.rj45_front_y() + EDGE_CLEAR, RJ45_FRAME_TOP + 0.3, cuts)
    # rack ear slots
    z_off = (U - PANEL_H) / 2
    for sx in (-1, 1):
        ex = CX + sx * EAR_HOLE_SPACING / 2
        for hz in EAR_HOLE_Z:
            z = hz - z_off
            yc, ly = Y_FRONT + PANEL_T / 2, PANEL_T + 2
            for dx in (-1, 1):
                cyl(f"ear_{sx}_{hz}_{dx}", ex + dx * (EAR_SLOT_L - EAR_SLOT_D) / 2, yc, z, EAR_SLOT_D, ly, cuts, axis="Y")
            box(f"ear_{sx}_{hz}_mid", ex - (EAR_SLOT_L - EAR_SLOT_D) / 2, Y_FRONT - 1, z - EAR_SLOT_D / 2,
                ex + (EAR_SLOT_L - EAR_SLOT_D) / 2, Y_FRONT + PANEL_T + 1, z + EAR_SLOT_D / 2, cuts)
    # drive screws from below, counterbored
    for i, (dx, dy) in enumerate(DRIVE_HOLES):
        x, y = DRIVE_X0 + dx, DRIVE_Y0 + dy
        cyl(f"drive_hole_{i}", x, y, FLOOR, SCREW_CLEAR, 2 * (FLOOR + DRIVE_BOSS_H) + 2, cuts)
        cyl(f"drive_cbore_{i}", x, y, 0, SCREW_CBORE_D, 2 * SCREW_CBORE_H, cuts)
    # lid screw pilots in corner posts
    for i, (px, py) in enumerate(post_xy()):
        cyl(f"post_pilot_{i}", px + POST / 2, py + POST / 2, Z_TOP, PILOT, 24, cuts)
        # notch where the board outline reaches the post, open upward so the board drops in
        n = post_notch(px, py)
        if n:
            box(f"post_notch_{i}", *n[:2], BOARD_Z - EDGE_CLEAR, *n[2:], Z_TOP + 1, cuts)
    # child board: post pilots, rear-wall openings for its jacks
    for i, h in enumerate(CB["holes"]):
        cyl(f"cb_pilot_{i}", CB_X0 + h["x"], CB_Y0 + h["y"], CB_Z0, CB_PILOT, 10, cuts)
    u = CB["parts"]["usb_a"]
    box("cb_usb_cut", CB_X0 + u["x"][0] - 0.5, Y_OUT0 - 1, max(FLOOR, CB_Z0 + u["z"][0] - 0.5),
        CB_X0 + u["x"][1] + 0.5, Y_IN0 + 1, CB_Z0 + u["z"][1] + 0.5, cuts)
    a = CB["parts"]["audio"]
    cyl("cb_audio_cut", CB_X0 + sum(a["x"]) / 2, (Y_OUT0 + Y_IN0) / 2, CB_Z0 + sum(a["z"]) / 2, 6.5, WALL + 2, cuts, axis="Y")
    # fan posts: pilot holes
    for i, (hx, hy) in enumerate(FAN_HOLES):
        cyl(f"fan_pilot_{i}", hx, hy, FAN_Z0, FAN_PILOT, 16, cuts)
    # fan exhaust: west wall, sized to the fan's outlet only so all air takes the CPU path
    oy0, oy1 = FAN["outlet"]["y"]
    vent_slots("west_vent_", cuts, "Y", FAN_Y0 + oy0 + 1, FAN_Y0 + oy1 - 1,
               (X_OUT0 - 1, X_IN0 + 1), None, z0=FAN_Z0 + 0.8, z1=FAN_Z0 + FAN["thickness"] - 0.8)
    boolean(tray, "DIFFERENCE", cuts)

    bpy.data.collections.remove(work)
    return tray


def build_lid(root):
    work = new_coll("_work", root)
    lid = box("Lid", X_OUT0, Y_OUT0, Z_TOP, X_OUT1, Y_FRONT, PANEL_H, root)
    cuts = new_coll("_cuts", work)
    for i, (px, py) in enumerate(post_xy()):
        cyl(f"lid_hole_{i}", px + POST / 2, py + POST / 2, Z_TOP + LID_T / 2, SCREW_CLEAR, LID_T + 2, cuts)
    # intake: lid above the CPU block (air path CPU block -> fan -> west grill)
    x0, y0, x1, y1 = CPU_RECT
    vent_slots("top_vent_", cuts, "X", x0 + 3, x1 - 3,
               (Z_TOP - 1, PANEL_H + 1), (y0 + 3, y1 - 3))
    boolean(lid, "DIFFERENCE", cuts)
    bpy.data.collections.remove(work)
    return lid


def import_glb(path, root, offset):
    units = bpy.context.scene.unit_settings
    scale, units.scale_length = units.scale_length, 1.0   # glTF importer rescales by this
    bpy.ops.import_scene.gltf(filepath=path)
    units.scale_length = scale
    objs = list(bpy.context.selected_objects)
    for o in objs:
        for c in o.users_collection:
            c.objects.unlink(o)
        root.objects.link(o)
        if o.parent is None:
            o.location += Vector(offset)
    return objs


def build_context(root, board_glb, fan_glb):
    """Board, drive and fan: assembly/preview only, not printed."""
    board_objs = import_glb(board_glb, root, (0, 0, BOARD_Z))
    fan_objs = import_glb(fan_glb, root, (FAN_X0, FAN_Y0, FAN_Z0))
    cb_objs = import_glb(os.path.join(HERE, "..", "childboard", "out", "childboard.glb"), root, (CB_X0, CB_Y0, CB_Z0))
    drive = box("drive_2_5in", DRIVE_X0, DRIVE_Y0, FLOOR + DRIVE_BOSS_H,
                DRIVE_X0 + DRIVE_SX, DRIVE_Y0 + DRIVE_SY, FLOOR + DRIVE_BOSS_H + DRIVE_T, root)
    drive.data.materials.append(material("drive", (0.25, 0.27, 0.3)))
    xe = DRIVE_X0 + DRIVE_SX   # SATA data+power connector, east end (visual only)
    sata = box("drive_sata_connector", xe - 4, DRIVE_Y0 + 8, FLOOR + DRIVE_BOSS_H + 1,
               xe + 0.5, DRIVE_Y0 + 8 + 40, FLOOR + DRIVE_BOSS_H + DRIVE_T - 1.5, root)
    sata.data.materials.append(material("sata", (0.95, 0.85, 0.2)))
    return board_objs + fan_objs + cb_objs + [drive, sata]


# ---------------------------------------------------------------- fit tests
FIT_STANDOFF = 8.0        # standoff height in the fit test (board keeps its height vs the panel)
FIT_BASE_T, FIT_BAR_W = 2.0, 6.0


def bar(name, p, q, z0, z1, coll, w=FIT_BAR_W):
    """Flat bar from p to q (XY), rounded off by overlapping the posts at each end."""
    (x0, y0), (x1, y1) = p, q
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(math.dist(p, q) + w, w, z1 - z0), verts=bm.verts)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.atan2(y1 - y0, x1 - x0), 3, "Z"))
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return mesh_obj(name, bm, coll)


def build_fit_test(tray, root):
    """Tray cut down to the front panel strip (ports + RJ45 hood) and the two north
    board mounts (H1, H2; the rest checked out in fit test 1), re-based on a light
    bar frame. Everything drops by the same amount, so board-to-panel alignment is
    exact; only the standoffs get shorter."""
    zb = BOARD_Z - FIT_STANDOFF - FIT_BASE_T          # bottom of the frame
    holes = {f"H{i + 1}": (x, y) for i, (x, y, _) in enumerate(brd.HOLES_MM[:2])}
    cut_x = [x for x0x1 in brd.PORT_X.values() for x in x0x1]
    px0, px1 = min(cut_x) - 8, max(cut_x) + 8

    me = tray.data.copy()
    fit = bpy.data.objects.new("Fit_test", me)
    root.objects.link(fit)
    work = new_coll("_work", root)
    keep_parts = new_coll("_keep_parts", work)
    keep = box("keep_panel", px0, Y_FRONT - 18, zb, px1, Y_FRONT + PANEL_T + 1, BOARD_Z + 14, work)
    for n, (x, y) in holes.items():
        # from inside the frame (no face coplanar with its bottom) to above the pin tips
        cyl(f"keep_{n}", x, y, (zb + 1 + BOARD_Z + 4) / 2, STANDOFF_D + 0.5, BOARD_Z + 3 - zb, keep_parts)
    boolean(keep, "UNION", keep_parts)          # one keep volume: a collection INTERSECT would AND them all
    only = new_coll("_keep", work)
    work.objects.unlink(keep)
    only.objects.link(keep)
    boolean(fit, "INTERSECT", only)

    frame = new_coll("_frame", work)
    P = {**holes,
         "P1": (holes["H1"][0], Y_FRONT + 1), "P2": (holes["H2"][0], Y_FRONT + 1), "P3": (RJ45_CX, Y_FRONT + 1)}
    for a, b in [("H1", "H2"), ("P1", "H1"), ("P2", "H2"), ("P3", "H1"), ("P1", "P2")]:
        bar(f"bar_{a}_{b}", P[a], P[b], zb, zb + FIT_BASE_T, frame)
    for n, (x, y) in holes.items():                       # pads so posts sit on solid base
        cyl(f"pad_{n}", x, y, zb + FIT_BASE_T / 2, STANDOFF_D + 3, FIT_BASE_T, frame)
    boolean(fit, "UNION", frame)
    bpy.data.collections.remove(work)
    bm = bmesh.new()                                      # drop zero-area slivers from coincident faces
    bm.from_mesh(fit.data)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-6], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(fit.data)
    bm.free()
    fit.location.z = -zb                                  # sit it on the print bed
    return fit


def build_childboard_fit(root):
    """Three posts at the child board's holes on a bar, with pilot holes."""
    work = new_coll("_work", root)
    pts = [(h["x"], h["y"]) for h in CB["holes"]]
    piece = bar("Fit_childboard", pts[0], pts[1], 0, FIT_BASE_T, root)
    add = new_coll("_add", work)
    bar("b2", pts[1], pts[2], 0, FIT_BASE_T, add)
    for i, (x, y) in enumerate(pts):
        cyl(f"p{i}", x, y, FIT_BASE_T + 2.5, CB_POST_D, 5.0, add)
    boolean(piece, "UNION", add)
    cuts = new_coll("_cuts", work)
    for i, (x, y) in enumerate(pts):
        cyl(f"c{i}", x, y, FIT_BASE_T + 3, CB_PILOT, 8, cuts)
    boolean(piece, "DIFFERENCE", cuts)
    bpy.data.collections.remove(work)
    return piece


def build_pin_gauge(root):
    """Row of board-mount pins, GAUGE_PINS diameters, each on a collar the board
    rests on, with its size raised on the base. Press a board hole over each:
    the snug one is PIN_D."""
    pitch, collar_d, collar_h, base_w = 12.0, 7.0, 4.0, 16.0
    n = len(GAUGE_PINS)
    work = new_coll("_work", root)
    gauge = box("Pin_gauge", -pitch / 2, -base_w / 2, 0, (n - 0.5) * pitch, base_w / 2, FIT_BASE_T, root)
    add = new_coll("_add", work)
    for i, d in enumerate(GAUGE_PINS):
        x = i * pitch
        cyl(f"collar_{i}", x, 2, FIT_BASE_T + collar_h / 2 - 0.01, collar_d, collar_h + 0.02, add)
        pin(f"pin_{i}", x, 2, FIT_BASE_T + collar_h - 0.01, d, brd.PCB_T + PIN_ABOVE + 0.01, add)
        cu = bpy.data.curves.new(f"label_{i}", "FONT")
        cu.body = f"{d:.2f}"
        cu.size, cu.extrude, cu.align_x = 2.8, 0.3, "CENTER"
        t = bpy.data.objects.new(f"label_{i}", cu)
        add.objects.link(t)
        t.location = (x, -base_w / 2 + 1.2, FIT_BASE_T + 0.29)
        bpy.context.view_layer.objects.active = t
        bpy.ops.object.select_all(action="DESELECT")
        t.select_set(True)
        bpy.ops.object.convert(target="MESH")
    boolean(gauge, "UNION", add)
    bpy.data.collections.remove(work)
    return gauge


def export_stl(obj, path):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bad = sum(not e.is_manifold for e in bm.edges)
    bm.free()
    if bad:
        print(f"NON-MANIFOLD {os.path.basename(path)}: {bad} edges")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)


def render(scene, path, loc, target, res=(1400, 1000), lens=45):
    cam = scene.camera
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main(outdir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"
    os.makedirs(outdir, exist_ok=True)

    case = new_coll("Case")
    ctx = new_coll("Context (not printed)")
    tray = build_tray(case)
    lid = build_lid(case)
    tray.data.materials.append(material("tray", (0.15, 0.15, 0.16)))
    lid.data.materials.append(material("lid", (0.55, 0.57, 0.6)))

    export_stl(tray, os.path.join(outdir, "tray.stl"))
    export_stl(lid, os.path.join(outdir, "lid.stl"))
    fit = build_fit_test(tray, case)
    export_stl(fit, os.path.join(outdir, "fit_test.stl"))
    fit.hide_render = True
    cbfit = build_childboard_fit(case)
    export_stl(cbfit, os.path.join(outdir, "fit_childboard.stl"))
    cbfit.hide_render = True
    gauge = build_pin_gauge(case)
    export_stl(gauge, os.path.join(outdir, "pin_gauge.stl"))
    gauge.hide_render = True
    coupon = build_rj45_coupon(tray, case)
    export_stl(coupon, os.path.join(outdir, "rj45_test.stl"))
    coupon.hide_render = True

    build_context(ctx, os.path.join(HERE, "..", "board", "out", "board.glb"),
                  os.path.join(HERE, "..", "fan", "out", "fan.glb"))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, "assembly.glb"),
                              export_format="GLB", use_selection=True)

    with open(os.path.join(outdir, "dimensions.txt"), "w") as f:
        f.write(f"front panel: {PANEL_W} x {PANEL_H} mm (1U, 10\")\n")
        f.write(f"body: {BODY_W:.1f} W x {Y_FRONT - Y_OUT0 + PANEL_T:.1f} D x {PANEL_H} H mm (depth incl. panel)\n")
        f.write(f"board bottom at Z {BOARD_Z:.1f}, tallest part top at Z {BOARD_Z + brd.PCB_T + TALLEST:.1f}, "
                f"lid underside at Z {Z_TOP:.1f}\n")
        f.write(f"drive: X {DRIVE_X0}-{DRIVE_X0 + DRIVE_SX:.1f}, Y {DRIVE_Y0}-{DRIVE_Y0 + DRIVE_SY:.1f}, "
                f"Z {FLOOR + DRIVE_BOSS_H}-{FLOOR + DRIVE_BOSS_H + DRIVE_T}\n")
        f.write(f"RJ45: plug Z {RJ45_FLOOR:.1f}-{RJ45_FLOOR + RJ45_BODY_H:.1f} (through the board, latch up), center X {RJ45_CX:.1f}, nose stop Y {RJ45_STOP_Y:.1f}, "
                f"panel face Y {Y_FRONT + PANEL_T:.1f}\n")
        f.write(f"fan: X {FAN_X0:.1f}-{FAN_X0 + FAN['width_x']:.1f}, Y {FAN_Y0:.1f}-{FAN_Y0 + FAN['depth_y']:.1f}, "
                f"Z {FAN_Z0:.1f}-{FAN_Z0 + FAN['thickness']:.1f}; gap to tab {NOTCH_X - FAN_X0 - FAN['width_x']:.1f}\n")
        mx0, _, mx1, my1 = brd.rect_mm(*MB_RIBBON_PX)
        m = CB["parts"]["mb_conn"]
        f.write(f"child board: X {CB_X0:.1f}-{CB_X0 + CB['length_x']:.1f}, Y {CB_Y0 + CB['depth_y'][0]:.1f}-"
                f"{CB_Y0 + CB['depth_y'][1]:.1f}, PCB Z {CB_Z0:.1f}; MB_CONN X {CB_X0 + m['x'][0]:.1f}-"
                f"{CB_X0 + m['x'][1]:.1f} Y {CB_Y0 + m['y'][0]:.1f}-{CB_Y0 + m['y'][1]:.1f} Z {CB_Z0 + m['z'][1]:.1f}; "
                f"motherboard header X {mx0:.1f}-{mx1:.1f} Y ~{my1:.1f} Z {BOARD_Z + brd.PCB_T:.1f}\n")
        f.write("tray footprint for printing: "
                f"{PANEL_W:.0f} x {Y_FRONT + PANEL_T - Y_OUT0:.0f} mm\n")

    # renders
    scene.world = bpy.data.worlds.new("World")
    scene.world.color = (0.82, 0.82, 0.8)
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.display.shading.show_shadows = True
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.clip_end = 5000
    mid = (CX, (Y_OUT0 + Y_FRONT) / 2, 15)

    render(scene, os.path.join(outdir, "closed_front.png"), (CX - 330, Y_FRONT + 330, 260), mid)
    render(scene, os.path.join(outdir, "closed_rear_west.png"), (CX - 360, Y_OUT0 - 250, 220), mid)
    lid.hide_render = True
    render(scene, os.path.join(outdir, "open.png"), (CX + 120, Y_OUT0 - 300, 380), mid)
    for o in ctx.objects:
        o.hide_render = True
    render(scene, os.path.join(outdir, "tray_only.png"), (CX + 120, Y_OUT0 - 300, 380), mid)
    for o in ctx.objects:
        o.hide_render = False
    lid.hide_render = False

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, "case.blend"))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(os.path.abspath(argv[0] if argv else os.path.join(HERE, "out")))
