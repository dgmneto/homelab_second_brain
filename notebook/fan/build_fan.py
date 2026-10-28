"""3D model of the stock laptop blower fan (cooler), traced from photos.

Run headless:
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python fan/build_fan.py -- fan/out

Source of truth:
  * IMG_2196.HEIC: fan top view next to a caliper (scale: 12.04 px/mm from
    ~100 mm ticks). Cross-checked against IMG_2195.HEIC: width 70.3 mm in both.
  * Thickness 6.5 mm (given).
  * Checked with calipers: holes 79.50 apart (model 79.33), ear hole to photo bottom
    edge 62.58 (62.57), width near the bottom 70.10.
  * Outline traced from the housing's edge highlight (radial scan from the
    impeller center), deskewed (fan sat ~0.8 deg rotated).

Orientation: installed inlet up, as photographed, turned 90 deg clockwise so
the outlet faces the west wall's exhaust grill. The outlet is the long flat
side at the photo's bottom (the scroll runs clockwise and ends there):
photo bottom = west, photo left = north, photo top = east (screw ear NE).
Origin: SW corner of the housing, Z = 0 at the fan's bottom.

Writes fan/out/fan.json (outline, holes, outlet) for case/build_case.py.
"""

import json
import math
import os
import sys

import bmesh
import bpy

PX_PER_MM = 12.04
THICKNESS = 6.5

# Outline points in photo pixels (full-res crop of IMG_2196 at x=1335, y=1638),
# clockwise in the image starting at the top of the scroll.
SCROLL_RIGHT_BOTTOM = [
    (439, 106), (462, 105), (485, 105), (507, 106), (529, 109), (551, 112), (573, 117),
    (594, 123), (615, 129), (635, 136), (655, 144), (674, 153), (693, 163), (711, 173),
    (729, 185), (746, 196), (766, 204), (782, 217), (792, 238), (807, 252), (820, 268),
    (833, 284), (844, 301), (854, 319), (864, 336), (873, 354), (881, 373), (888, 392),
    (894, 411), (899, 430), (903, 450), (905, 470), (908, 490), (908, 510), (909, 530),
    (910, 549), (911, 570), (911, 590), (912, 611), (914, 633), (914, 654), (915, 678),
    (916, 702), (917, 727), (914, 752), (915, 780), (914, 811), (913, 848), (913, 887),
    (913, 927),                                   # SE corner (caliper: width 70.1 near the bottom)
    (896, 936), (826, 937), (766, 938), (712, 939), (663, 939), (617, 940), (573, 941),
    (530, 941), (486, 942), (442, 943), (395, 944), (345, 944), (290, 945), (227, 946),
    (153, 948), (72, 948),                        # SW corner
    (71, 901), (70, 863), (68, 796), (66, 708), (66, 628), (64, 578), (63, 505),
    (67, 456), (80, 370), (98, 300), (100, 252),  # west edge bends in toward the ear
]
EAR_C, EAR_R = (125, 195), 55                     # screw ear, top-left (M2.5)
EAR_ARC_DEG = (120, 330)                          # image angles (y down): lower-left, west, top, NE
EAR_TO_SCROLL = [(185, 190), (217, 182), (237, 169), (281, 146), (302, 135), (370, 118)]
HOLES_PX = [(125, 195), (880, 780)]               # M2.5 mounting holes
HOLE_D = 2.7
INLET_C, INLET_R, HUB_R = (530, 530), 260, 160
OUTLET_X_PX = (90, 896)                           # flat bottom edge = outlet mouth


def outline_px():
    ear = []
    a0, a1 = EAR_ARC_DEG
    for i in range(13):
        a = math.radians(a0 + (a1 - a0) * i / 12)
        ear.append((EAR_C[0] + EAR_R * math.cos(a), EAR_C[1] + EAR_R * math.sin(a)))
    return SCROLL_RIGHT_BOTTOM + ear + EAR_TO_SCROLL


def make_transform(pts):
    """Deskew (bottom edge horizontal, west edge vertical) and convert to mm."""
    bottom = [p for p in SCROLL_RIGHT_BOTTOM if p[1] > 930 and 100 < p[0] < 900]
    west = [p for p in SCROLL_RIGHT_BOTTOM if p[0] < 75 and 450 < p[1] < 940]
    sb = (bottom[-1][1] - bottom[0][1]) / (bottom[-1][0] - bottom[0][0])
    sw = -(west[-1][0] - west[0][0]) / (west[-1][1] - west[0][1])
    phi = math.atan((sb + sw) / 2)                  # small rotation to undo
    c, s = math.cos(-phi), math.sin(-phi)
    rot = lambda p: (p[0] * c - p[1] * s, p[0] * s + p[1] * c)
    r = [rot(p) for p in pts]
    ymax = max(p[1] for p in r)
    xmax = max(p[0] for p in r)
    # turned 90 deg clockwise: X = up from the photo's bottom, Y = left from its right
    return lambda p: ((ymax - rot(p)[1]) / PX_PER_MM, (xmax - rot(p)[0]) / PX_PER_MM), math.degrees(phi)


def extrude(name, pts, z0, z1, coll, mat):
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
    o.data.materials.append(mat)
    return o


def cyl(name, x, y, d, z0, z1, coll, mat=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=d / 2, radius2=d / 2, depth=z1 - z0)
    bmesh.ops.translate(bm, vec=(x, y, (z0 + z1) / 2), verts=bm.verts)
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


def main(outdir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"
    os.makedirs(outdir, exist_ok=True)

    raw = outline_px()
    tf, rot_deg = make_transform(raw)
    poly = [tf(p) for p in raw]
    holes = [tf(p) for p in HOLES_PX]
    inlet = tf(INLET_C)
    r_in, r_hub = INLET_R / PX_PER_MM, HUB_R / PX_PER_MM
    w = max(x for x, _ in poly)
    d = max(y for _, y in poly)
    outlet_y = sorted(tf((x, 940))[1] for x in OUTLET_X_PX)

    coll = bpy.data.collections.new("Fan")
    sc.collection.children.link(coll)
    metal = bpy.data.materials.new("fan_metal"); metal.diffuse_color = (0.75, 0.76, 0.78, 1)
    dark = bpy.data.materials.new("fan_dark"); dark.diffuse_color = (0.12, 0.12, 0.13, 1)
    for m in (metal, dark):    # glTF export reads the node colour
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = m.diffuse_color

    housing = extrude("fan_housing", poly, 0, THICKNESS, coll, metal)
    cut(housing, cyl("inlet", *inlet, 2 * r_in, 1.0, THICKNESS + 1, coll))   # top inlet, 1 mm floor left
    for i, (hx, hy) in enumerate(holes):
        cut(housing, cyl(f"hole{i}", hx, hy, HOLE_D, -1, THICKNESS + 1, coll))
    cyl("impeller", *inlet, 2 * r_in - 1.5, 1.0, THICKNESS - 0.6, coll, metal)
    cyl("hub", *inlet, 2 * r_hub, 1.0, THICKNESS - 0.4, coll, dark)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, "fan.glb"), export_format="GLB", use_selection=True)
    bpy.ops.wm.stl_export(filepath=os.path.join(outdir, "fan.stl"), export_selected_objects=True)

    info = {
        "thickness": THICKNESS, "width_x": round(w, 2), "depth_y": round(d, 2),
        "outline": [[round(x, 2), round(y, 2)] for x, y in poly],
        "holes": [[round(x, 2), round(y, 2)] for x, y in holes], "hole_d": HOLE_D,
        "inlet_center": [round(inlet[0], 2), round(inlet[1], 2)], "inlet_d": round(2 * r_in, 2),
        "outlet": {"side": "west", "y": [round(outlet_y[0], 2), round(outlet_y[1], 2)]},
        "photo_rotation_deg": round(rot_deg, 2),
    }
    with open(os.path.join(outdir, "fan.json"), "w") as f:
        json.dump(info, f, indent=1)

    # preview
    sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.82, 0.82, 0.8)
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True
    from mathutils import Vector
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
    tgt = Vector((w / 2, d / 2, 3))
    cam.location = Vector((w / 2 - 70, d / 2 - 110, 120))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.render.filepath = os.path.join(outdir, "preview.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, "fan.blend"))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(os.path.abspath(argv[0] if argv else "fan/out"))
