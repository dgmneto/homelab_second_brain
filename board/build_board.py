"""Build a 3D model of the homelab notebook motherboard (Acer, label NBHE2...).

Run headless:
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python board/build_board.py -- board/out

Source of truth:
  * Photo IMG_2117.HEIC (top view, ~0.6 deg rotated, slight keystone).
  * Mounting holes: caliper triangulation, photo IMG_2289 (see HOLES_MM).
  * Hand measurements (cm) used to calibrate the photo scale:
      A  south edge width (bottom tab)                      4.924
      B  widest line, over the SO-DIMM slot                11.476
      C  NW notch SE corner -> bottom of wide left section  12.928
  * Component heights are NOT measured: standard part heights.
  * Ethernet is NOT a full RJ45 jack: it is the board half of a laptop
    "drop-jaw" jack. The plug goes into a housing on the board's UNDERSIDE
    (contacts up, latch down); the laptop's spring flap was the jack floor.
    The rack case recreates that half (see case/).
  * Ports, north edge: caliper, drawing IMG_2290 (see PORT_CHAIN). Ports are
    mid-mount, mostly below the PCB.

Everything below in PX is image coordinates (1200x1600 upright JPEG, y down).
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

# ---------------------------------------------------------------- calibration
# Perspective fit (image px -> mm, up to rotation/translation) to 6 caliper
# measurements: tab width 49.24, widest 114.76, notch step -> wide-section
# bottom 129.28, H1-H2 42.02, H3-H4 106.24, H1-H3 77.40. Residuals <= 0.16 mm.
# (Fit: scratch least-squares over a, b, d, g, h; image centred at (700, 900).)
HOMOGRAPHY = (0.18336646, -0.00642957, 0.17446114, 0.00014896, -0.00004758)
H_CENTER = (700, 900)
# The photo has a ~10-12 px shadow north of every north-facing edge (light from
# the south). Edges below are the real board edges, not the shadow line.
Y_BOTTOM = 1476           # south edge of the tab -> Y = 0 mm
X_LEFT = 409              # west edge of the wide section -> X = 0 mm

PCB_T = 1.0               # board thickness (mm), typical for laptop boards
HOLE_D = 3.56             # mounting hole diameter (mm), caliper (IMG_2289)
PAD_D = 7.0               # gold ring diameter (mm), from photo


def _project(x, y):
    a, b, d, g, h = HOMOGRAPHY
    u, v = x - H_CENTER[0], y - H_CENTER[1]
    w = g * u + h * v + 1.0
    return (a * u + b * v) / w, (d * v) / w


def _frame():
    """Rotation that makes the west edge vertical, and the origin."""
    (x1, y1), (x2, y2) = _project(409, 407), _project(416, 1128)
    ang = math.atan2(x2 - x1, y2 - y1)
    c, s = math.cos(ang), math.sin(ang)
    rot = lambda p: (p[0] * c - p[1] * s, p[0] * s + p[1] * c)
    x0 = rot(_project(X_LEFT, 500))[0]
    y0 = rot(_project(900, Y_BOTTOM))[1]
    return rot, x0, y0


def px2mm(x, y):
    rot, x0, y0 = _FRAME
    u, v = rot(_project(x, y))
    return u - x0, y0 - v      # image y grows south; model Y grows north


_FRAME = _frame()


# ---------------------------------------------------------------- geometry (px)
# Outline, clockwise in the image, from the NE corner round to the NW ear. The
# north (port) edge is not traced: the photo skews it (see north_edge_y).
OUTLINE_PX = [
    (1055, 908),                     # east edge
    (1040, 912), (1044, 1254),       # east recess
    (1061, 1258), (1062, 1476),      # SE corner
    (785, 1478),                     # SW corner of tab   (A = 4.924 cm)
    (782, 1400), (795, 1398),        # small step on tab's west edge
    (793, 1188), (780, 1184),
    (780, 1126),                     # inner corner, tab meets wide section
    (416, 1128),                     # SW corner of wide section
    (409, 407),                      # west edge (B line at y=500)
    (430, 406.5),                    # NW notch SE corner (C starts here)
    (430, 299), (405, 295), (404, 274), (409, 270), (429, 268),  # small ear
]
NW_X = px2mm(431, 236.5)[0]          # NW corner (narrow top section), from the photo

# 7 mounting holes. Caliper triangulation (IMG_2289): 12 hole-to-hole distances,
# each taken between the holes' NEAR edges, so centre distance = d + HOLE_D.
# Sketch labels: TL TR ML BL BM BR RM (sketch is the board turned 90 deg).
HOLE_EDGE_DIST = [            # (H_a, H_b, near-edge distance mm)
    (7, 3, 67.76), (7, 6, 118.04), (7, 4, 69.22), (4, 3, 103.90),
    (4, 6, 49.00), (4, 5, 77.58), (6, 5, 99.00), (3, 5, 105.30),
    (3, 2, 109.30), (3, 1, 75.10), (1, 2, 40.50), (5, 2, 69.60),
]
# Centres solved by least squares from HOLE_EDGE_DIST (residuals <= 0.03 mm; one
# redundant loop through H3-H7), then placed on the board by a best rigid fit
# to the old photo-derived centres (moves of 0.5-7.8 mm; the photo had H6 too
# far north). "slot" = half-hole open to the nearest edge.
HOLES_MM = [
    (56.90, 199.47, "round"),     # H1  RM
    (100.95, 200.55, "round"),    # H2  BR
    (6.07, 139.44, "round"),      # H3  TR
    (75.50, 57.44, "round"),      # H4  ML
    (114.39, 128.64, "slot_e"),   # H5  BM
    (117.67, 26.12, "slot_e"),    # H6  BL
    (3.54, 68.16, "slot_w"),      # H7  TL
]
# ---------------------------------------------------------------- north edge + ports (caliper)
# IMG_2290, front view (east -> west along the north edge, mm): edge gaps and
# port widths. The ports' front faces are in one line; the board edge behind
# them steps forward twice going west, so they stick out by different amounts.
PORT_CHAIN = [                       # (port, or None for a gap; width)
    (None, 19.40), ("usb_a_2", 13.20), (None, 6.23), ("usb_a_1", 13.20),
    (None, 6.76), ("hdmi", 15.10), (None, 5.30), ("rj45", 16.20),
    (None, 4.60), ("power_dc", 6.48),
]
# Port fronts -> board edge: east of usb_a_1, between it and hdmi, west of hdmi.
STICK_OUT = (4.30, 3.56, 1.70)
PWR_STICK_OUT = 1.38                 # the power jack alone stops short of the line
# Hole near edge -> board edge (top view): H2 (east level), H1 (middle level).
H2_TO_EDGE, H1_TO_EDGE = 13.28, 14.52
# Hole near edge -> east board edge, square to it: H2 (caliper). The east edge is
# taken as straight up to the NE corner, where the port chain starts.
H2_TO_EAST_EDGE = 12.30
NE_X = HOLES_MM[1][0] + HOLE_D / 2 + H2_TO_EAST_EDGE


def _port_x():
    x, out = NE_X, {}
    for name, w in PORT_CHAIN:
        if name:
            out[name] = (x - w, x)
        x -= w
    return out


PORT_X = _port_x()
STEP_X = (sum(PORT_X["usb_a_1"]) / 2,      # edge steps, hidden under these two ports
          sum(PORT_X["hdmi"]) / 2)
# Edge at the east level, from both holes (they agree +-0.3 mm).
_E = ((HOLES_MM[1][1] + HOLE_D / 2 + H2_TO_EDGE)
      + (HOLES_MM[0][1] + HOLE_D / 2 + H1_TO_EDGE - (STICK_OUT[0] - STICK_OUT[1]))) / 2
PORT_FRONT_Y = _E + STICK_OUT[0]
EDGE_Y = tuple(PORT_FRONT_Y - s for s in STICK_OUT)     # east, middle, west


def north_edge_y(x):
    """Board north edge (mm) at board X."""
    return EDGE_Y[0] if x > STEP_X[0] else EDGE_Y[1] if x > STEP_X[1] else EDGE_Y[2]


def outline_mm():
    north = [(NW_X, EDGE_Y[2]), (STEP_X[1], EDGE_Y[2]), (STEP_X[1], EDGE_Y[1]),
             (STEP_X[0], EDGE_Y[1]), (STEP_X[0], EDGE_Y[0]), (NE_X, EDGE_Y[0])]
    pts = [px2mm(x, y) for x, y in OUTLINE_PX]
    # The photo skews the wide section's south edge too (5.5 mm drop to the west),
    # which would overlap the fan where it sits in the laptop (case/build_case.py).
    # Taken straight at the tab end's height until measured.
    sw = OUTLINE_PX.index((416, 1128))
    pts[sw] = (pts[sw][0], px2mm(780, 1126)[1])
    return north + pts


def _photo_edge_px(x):
    """North edge as traced in the photo (image y at image column x)."""
    return 236.5 if x < 680 else 244 + 0.01 * (x - 732)


def near_edge_mm(x, y):
    """Photo px point near the north edge -> mm, keeping its distance behind the edge."""
    mx, my = px2mm(x, y)
    return mx, north_edge_y(mx) - (px2mm(x, _photo_edge_px(x))[1] - my)


# Ports are mid-mount (sit in board cutouts): name, depth behind the board edge
# (photo IMG_2117), mm below the PCB bottom / above the PCB top (caliper), material.
PORTS = [
    ("power_dc", 11.3, 2.5, 1.40, "metal"),
    ("hdmi",     10.3, 3.2, 1.89, "metal"),
    ("usb_a_1",  12.2, 3.4, 2.00, "metal"),
    ("usb_a_2",   8.2, 3.4, 2.00, "metal"),
]


def port_rect(name):
    """(x0, y0, x1, y1) mm footprint of a port, front face at PORT_FRONT_Y."""
    x0, x1 = PORT_X[name]
    depth = next(p[1] for p in PORTS if p[0] == name)
    edge = north_edge_y((x0 + x1) / 2)
    front = edge + PWR_STICK_OUT if name == "power_dc" else PORT_FRONT_Y
    return x0, edge - depth, x1, front


# Drop-jaw RJ45. Underside: housing with the 8 springs (IMG_2200/2201). The
# board has a cutout over it; the springs show through it from the top
# (IMG_2117), framed by a low top-side block. The plug rests on the springs,
# contacts down, its body passing up through the cutout, latch up. The laptop's
# top-side flap held it down; the case supplies that (case/build_case.py).
# X from the caliper chain; frame and springs keep their photo shape, re-centred.
RJ45_PX = (512, 227.5, 592, 283)     # top-side frame footprint (back wall at y=283)
RJ45_TOP_H = 2.6                     # top-side frame height
RJ45_SPRINGS_PX = (533, 252, 578, 278)
RJ45_JACK_BELOW = 3.9                # underside housing hangs below the PCB bottom
RJ45_PLUG_FLOOR = 2.5                # plug's contact face rests this far below the PCB bottom


def rj45_center_x():
    return sum(PORT_X["rj45"]) / 2


def _rj45_rect(r, to_front=False):
    x0, y0 = near_edge_mm(r[0], r[3])
    x1, y1 = near_edge_mm(r[2], r[1])
    sx0, sx1 = (px2mm(x, RJ45_SPRINGS_PX[3])[0] for x in RJ45_SPRINGS_PX[::2])
    dx = rj45_center_x() - (sx0 + sx1) / 2      # plug centre = centre of the springs
    return x0 + dx, y0, x1 + dx, PORT_FRONT_Y if to_front else y1


def rj45_frame_rect():
    """Top-side frame (mm); its back wall is the plug's nose stop."""
    return _rj45_rect(RJ45_PX, to_front=True)


def rj45_springs_rect():
    return _rj45_rect(RJ45_SPRINGS_PX)

PARTS = [
    ("sodimm_slot",   (520, 462, 930, 530), 4.0, "dark"),
    ("cpu_heatplate", (412, 673, 922, 972), 2.5, "metal"),
    ("m2_socket",     (800, 1220, 925, 1272), 3.2, "dark"),
    ("fan_header",    (850, 1140, 895, 1195), 3.5, "light"),
    ("ec_chip",       (820, 990, 910, 1080), 1.2, "dark"),
    ("inductor_1",    (793, 385, 835, 428), 3.0, "dark"),
    ("inductor_2",    (680, 990, 715, 1028), 3.0, "dark"),
    ("inductor_3",    (750, 990, 790, 1028), 3.0, "dark"),
    ("inductor_4",    (465, 1060, 510, 1100), 3.0, "dark"),
    ("capacitor",     (725, 993, 752, 1025), 4.0, "metal"),
    ("lan_magnetics", (520, 340, 610, 405), 2.0, "dark"),
    ("fpc_1",  (440, 435, 472, 575), 2.0, "light"),
    ("fpc_2",  (988, 355, 1035, 475), 2.0, "dark"),
    ("fpc_3",  (990, 605, 1027, 680), 2.0, "light"),
    ("fpc_4",  (980, 800, 1012, 915), 2.0, "light"),
    ("fpc_5",  (990, 925, 1022, 1110), 2.0, "light"),
    ("fpc_6",  (955, 1045, 985, 1225), 2.0, "light"),
    ("fpc_7",  (1000, 1150, 1030, 1205), 2.0, "light"),
    ("fpc_8",  (870, 1440, 1005, 1465), 2.0, "light"),
    ("fpc_9",  (1030, 1405, 1055, 1460), 2.0, "dark"),
]

# ---------------------------------------------------------------- blender helpers
MATS = {}


def material(name, rgba):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = rgba
    MATS[name] = m
    return m


def link(obj, coll):
    coll.objects.link(obj)
    return obj


def make_pcb(coll):
    pts = outline_mm()
    # Image is clockwise with y down -> counter-clockwise once Y is flipped.
    me = bpy.data.meshes.new("pcb")
    bm = bmesh.new()
    verts = [bm.verts.new((x, y, 0.0)) for x, y in pts]
    face = bm.faces.new(verts)
    if face.normal.z < 0:
        face.normal_flip()
    ret = bmesh.ops.extrude_face_region(bm, geom=[face])
    for v in ret["geom"]:
        if isinstance(v, bmesh.types.BMVert):
            v.co.z = PCB_T
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new("PCB", me), coll)
    obj.data.materials.append(MATS["pcb"])
    return obj


def box(name, x0, y0, x1, y1, z0, z1, mat, coll):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me), coll)
    obj.data.materials.append(MATS[mat])
    return obj


def cylinder(name, x, y, d, z0, z1, coll, segments=48):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments,
                          radius1=d / 2, radius2=d / 2, depth=z1 - z0)
    bmesh.ops.translate(bm, vec=(x, y, (z0 + z1) / 2), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me), coll)


def boolean_cut(target, cutter):
    mod = target.modifiers.new(cutter.name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def rect_mm(x0, y0, x1, y1):
    ax, ay = px2mm(x0, y1)   # SW corner (y down in image)
    bx, by = px2mm(x1, y0)   # NE corner
    return ax, ay, bx, by


# ---------------------------------------------------------------- build
def build(outdir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"

    material("pcb", (0.04, 0.12, 0.35, 1))
    material("metal", (0.72, 0.72, 0.74, 1))
    material("dark", (0.06, 0.06, 0.07, 1))
    material("light", (0.85, 0.85, 0.82, 1))
    material("gold", (0.85, 0.55, 0.3, 1))

    coll = bpy.data.collections.new("Board")
    scene.collection.children.link(coll)

    pcb = make_pcb(coll)
    xs = [x for x, _ in outline_mm()]
    xmin, xmax = min(xs), max(xs)

    holes = []
    for i, (x, y, kind) in enumerate(HOLES_MM):
        holes.append((x, y, kind))
        boolean_cut(pcb, cylinder(f"hole_{i}", x, y, HOLE_D, -1, PCB_T + 1, coll))
        if kind.startswith("slot"):
            edge = xmax + 2 if kind == "slot_e" else xmin - 2
            boolean_cut(pcb, box(f"slot_{i}", min(x, edge), y - HOLE_D / 2,
                                 max(x, edge), y + HOLE_D / 2, -1, PCB_T + 1, "pcb", coll))
        # gold annular ring, top side only (visual)
        ring = cylinder(f"pad_{i}", x, y, PAD_D, PCB_T, PCB_T + 0.05, coll)
        boolean_cut(ring, cylinder(f"padhole_{i}", x, y, HOLE_D, PCB_T - 1, PCB_T + 1, coll))
        if kind.startswith("slot"):
            edge = xmax + 2 if kind == "slot_e" else xmin - 2
            boolean_cut(ring, box(f"padslot_{i}", min(x, edge), y - HOLE_D / 2,
                                  max(x, edge), y + HOLE_D / 2, PCB_T - 1, PCB_T + 1, "pcb", coll))
        ring.name = f"MountHole_{i + 1}"
        ring.data.materials.append(MATS["gold"])

    for name, _, below, above, mat in PORTS:
        box(name, *port_rect(name), -below, PCB_T + above, mat, coll)
    for name, (x0, y0, x1, y1), h, mat in PARTS:
        ax, ay, bx, by = rect_mm(x0, y0, x1, y1)
        box(name, ax, ay, bx, by, PCB_T, PCB_T + h, mat, coll)
    fx0, fy0, fx1, fy1 = rj45_frame_rect()
    box("ethernet_top_block", fx0, fy0, fx1, fy1, PCB_T, PCB_T + RJ45_TOP_H, "dark", coll)
    jx0, jx1 = PORT_X["rj45"]
    box("ethernet_jack", jx0, fy0, jx1, PORT_FRONT_Y, -RJ45_JACK_BELOW, 0, "dark", coll)
    sx0, sy0, sx1, sy1 = rj45_springs_rect()
    box("ethernet_springs", sx0, sy0, sx1, sy1, -RJ45_PLUG_FLOOR, -RJ45_PLUG_FLOOR + 0.6, "gold", coll)

    os.makedirs(outdir, exist_ok=True)

    # exports
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.wm.stl_export(filepath=os.path.join(outdir, "board.stl"),
                          export_selected_objects=True, global_scale=1.0)
    bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, "board.glb"),
                              export_format="GLB", use_selection=True)

    # report
    ys = [y for _, y in outline_mm()]
    zmax = max(o.bound_box[1][2] for o in coll.objects)
    with open(os.path.join(outdir, "dimensions.txt"), "w") as f:
        f.write(f"bounding box (mm): X {xmax - xmin:.1f}  Y {max(ys) - min(ys):.1f}  "
                f"Z {zmax:.1f} (PCB {PCB_T} + tallest part)\n")
        f.write("check vs hand measurements (mm):\n")
        a = px2mm(1062, 1476)[0] - px2mm(785, 1478)[0]
        b = px2mm(1050, 500)[0] - px2mm(409, 500)[0]
        c = px2mm(430, 406.5)[1] - px2mm(430, 1125.5)[1]
        f.write(f"  A {a:.2f} (49.24)  B {b:.2f} (114.76)  C {c:.2f} (129.28)\n")
        f.write("  hole near-edge distances, model (caliper):\n")
        for a, b, d in HOLE_EDGE_DIST:
            m = math.dist(HOLES_MM[a - 1][:2], HOLES_MM[b - 1][:2]) - HOLE_D
            f.write(f"    H{a}-H{b} {m:6.2f} ({d:.2f})\n")
        f.write(f"north edge Y (east, middle, west): {EDGE_Y[0]:.2f} {EDGE_Y[1]:.2f} {EDGE_Y[2]:.2f}, "
                f"steps at X {STEP_X[0]:.2f} {STEP_X[1]:.2f}; port fronts Y {PORT_FRONT_Y:.2f}\n")
        f.write(f"  H2 edge->edge {EDGE_Y[0] - HOLES_MM[1][1] - HOLE_D / 2:.2f} ({H2_TO_EDGE})  "
                f"H1 {EDGE_Y[1] - HOLES_MM[0][1] - HOLE_D / 2:.2f} ({H1_TO_EDGE})\n")
        f.write("ports (X west-east, below PCB bottom, above PCB top, mm):\n")
        for name, _, below, above, _ in PORTS + [("rj45", 0, RJ45_JACK_BELOW, 0, 0)]:
            x0, x1 = PORT_X[name]
            f.write(f"  {name:9s} X {x0:6.2f}-{x1:6.2f} (w {x1 - x0:5.2f})  -{below}  +{above}\n")
        f.write("holes (center X, Y mm, origin X = west edge, Y = south edge):\n")
        for i, (x, y, k) in enumerate(holes):
            f.write(f"  H{i + 1}  {x:7.2f} {y:7.2f}  {k}\n")

    # preview renders: perspective + top-down ortho (compare with the photo)
    scene.world = bpy.data.worlds.new("World")
    scene.world.color = (0.8, 0.8, 0.78)
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.display.shading.background_type = "WORLD"
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.clip_end = 5000
    cx, cy = (xmin + xmax) / 2, (max(ys) + min(ys)) / 2

    cam.location = Vector((cx - 140, cy - 300, 260))
    cam.rotation_euler = (Vector((cx, cy + 10, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 55
    scene.render.resolution_x, scene.render.resolution_y = 1400, 1100
    scene.render.filepath = os.path.join(outdir, "preview.png")
    bpy.ops.render.render(write_still=True)

    cam.location = Vector((cx, cy, 300))
    cam.rotation_euler = (0, 0, 0)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 240
    scene.render.resolution_x, scene.render.resolution_y = 900, 1200
    scene.render.filepath = os.path.join(outdir, "top.png")
    bpy.ops.render.render(write_still=True)

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, "board.blend"))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(os.path.abspath(argv[0] if argv else "board/out"))
