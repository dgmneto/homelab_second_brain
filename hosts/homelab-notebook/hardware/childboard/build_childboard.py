"""3D model of the I/O child board (Acer "NB8513 UB V3"): USB-A, 3.5 mm audio,
MB_CONN ribbon (to the motherboard), SPK_CONN (speakers).

Run headless:
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python childboard/build_childboard.py -- childboard/out

Source of truth:
  * IMG_2198.HEIC (top view, caliper 17.96 px/mm) and IMG_2199.HEIC
    (17.00 px/mm): both give ~101.8-102.1 x 18.7 mm. No height correction: the
    caliper face and the board top (resting on its jacks) are both ~4 mm up.
  * IMG_2197.HEIC (side view): PCB ~0.8 mm; USB-A and audio jack are mid-mount,
    hanging ~3.2 / ~3.0 mm below the PCB. Side-view scale taken from the USB-A
    shell (13.15 mm standard width), so heights are estimates.

Coordinates (mm): X along the board (photo left -> right), Y = 0 at the I/O
edge (photo bottom, jacks stick out to -Y), Z = 0 at the PCB bottom.
Outline below is in deskewed IMG_2198 crop pixels (y down).
Writes childboard/out/childboard.json for case/build_case.py.
"""

import json
import os
import sys

import bmesh
import bpy
from mathutils import Vector

PX_PER_MM = 18.35          # caliper: length 99.60, hole-to-hole 55.58 (both fit within 0.1 mm)
X0_PX, Y0_PX = 40, 360          # left end, I/O edge
PCB_T = 0.8

OUTLINE_PX = [
    (40, 68), (700, 66), (715, 60), (1010, 60), (1025, 75), (1615, 76), (1628, 57),
    (1860, 55), (1867, 90), (1867, 404),                               # right end (taller)
    (1625, 400), (1612, 360), (1185, 360), (1182, 395), (1055, 395), (1050, 360),  # tab at middle hole
    (985, 360), (985, 140), (850, 140), (850, 355),                    # audio jack cutout
    (700, 352), (700, 128), (430, 128), (430, 358),                    # USB-A cutout
    (342, 360), (342, 262), (318, 262), (318, 360),                    # slot
    (192, 360), (192, 262), (170, 262), (170, 360),                    # slot
    (40, 362),
]
# holes: (x, y, d, open_to) - open_to "east" = C-slot through the right end
HOLES_PX = [(110, 150, 3.0, None), (1120, 280, 2.9, None), (1830, 345, 2.8, "east")]

# parts: name, (x0, y0, x1, y1) px, z0, z1 (mm, relative to PCB bottom), colour
PARTS = [
    ("usb_a",    (430, 120, 700, 418), -3.2, PCB_T + 2.3, "metal"),
    ("audio",    (850, 130, 985, 430), -3.0, PCB_T + 2.0, "metal"),
    ("mb_conn",  (1150, 140, 1590, 270), PCB_T, PCB_T + 2.0, "dark"),
    ("spk_conn", (1640, 60, 1760, 270), PCB_T, PCB_T + 3.5, "white"),
]


def mm(p):
    return ((p[0] - X0_PX) / PX_PER_MM, (Y0_PX - p[1]) / PX_PER_MM)


def rect_mm(r):
    (ax, ay), (bx, by) = mm((r[0], r[3])), mm((r[2], r[1]))
    return ax, ay, bx, by


def prism(name, pts, z0, z1, coll, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z0)) for x, y in pts]
    f = bm.faces.new(vs)
    if f.normal.z < 0:
        f.normal_flip()
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in ret["geom"]:
        if isinstance(v, bmesh.types.BMVert):
            v.co.z = z1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def cut(target, cutter):
    m = target.modifiers.new("cut", "BOOLEAN")
    m.operation, m.solver, m.object = "DIFFERENCE", "EXACT", cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def circle(x, y, d, n=40):
    import math
    return [(x + d / 2 * math.cos(2 * math.pi * i / n), y + d / 2 * math.sin(2 * math.pi * i / n)) for i in range(n)]


def main(outdir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"
    os.makedirs(outdir, exist_ok=True)
    coll = bpy.data.collections.new("ChildBoard")
    sc.collection.children.link(coll)
    mats = {}
    for n, c in [("pcb", (0.1, 0.35, 0.55, 1)), ("metal", (0.75, 0.75, 0.77, 1)),
                 ("dark", (0.08, 0.08, 0.09, 1)), ("white", (0.9, 0.9, 0.86, 1))]:
        mats[n] = bpy.data.materials.new("cb_" + n)
        mats[n].diffuse_color = c
        mats[n].use_nodes = True    # glTF export reads the node colour
        mats[n].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = c

    poly = [mm(p) for p in OUTLINE_PX]
    pcb = prism("cb_pcb", poly, 0, PCB_T, coll, mats["pcb"])
    xmax = max(x for x, _ in poly)
    holes = []
    for hx, hy, d, open_to in HOLES_PX:
        x, y = mm((hx, hy))
        holes.append({"x": round(x, 2), "y": round(y, 2), "d": d, "open_to": open_to})
        cut(pcb, prism("h", circle(x, y, d), -1, PCB_T + 1, coll, None))
        if open_to == "east":
            cut(pcb, prism("s", [(x, y - d / 2), (xmax + 1, y - d / 2), (xmax + 1, y + d / 2), (x, y + d / 2)],
                           -1, PCB_T + 1, coll, None))
    parts = {}
    for name, r, z0, z1, col in PARTS:
        ax, ay, bx, by = rect_mm(r)
        prism("cb_" + name, [(ax, ay), (bx, ay), (bx, by), (ax, by)], z0, z1, coll, mats[col])
        parts[name] = {"x": [round(ax, 2), round(bx, 2)], "y": [round(ay, 2), round(by, 2)],
                       "z": [round(z0, 2), round(z1, 2)]}

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, "childboard.glb"), export_format="GLB", use_selection=True)
    bpy.ops.wm.stl_export(filepath=os.path.join(outdir, "childboard.stl"), export_selected_objects=True)
    ys = [y for _, y in poly]
    info = {"pcb_t": PCB_T, "length_x": round(xmax, 2), "depth_y": [round(min(ys), 2), round(max(ys), 2)],
            "z_range": [min(p["z"][0] for p in parts.values()), max(p["z"][1] for p in parts.values())],
            "outline": [[round(x, 2), round(y, 2)] for x, y in poly], "holes": holes, "parts": parts}
    with open(os.path.join(outdir, "childboard.json"), "w") as f:
        json.dump(info, f, indent=1)

    sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.82, 0.82, 0.8)
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
    tgt = Vector((xmax / 2, 8, 0))
    cam.location = Vector((xmax / 2 + 40, -150, 120))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    sc.render.resolution_x, sc.render.resolution_y = 1200, 700
    sc.render.filepath = os.path.join(outdir, "preview.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, "childboard.blend"))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(os.path.abspath(argv[0] if argv else "childboard/out"))
