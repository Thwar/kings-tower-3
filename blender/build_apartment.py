"""
King's Tower · Dept. D — builds the apartment in Blender and exports apartment.glb.

Run headless:   python3 blender/build_apartment.py            (needs `pip install bpy`)
Or in Blender:  blender --background --python blender/build_apartment.py

Units are metres. Blender axes: X east, Y north, Z up.
The plan (src/scene/plan.js) uses x east, z south, y up — so plan z becomes -Y here,
and the glTF exporter's Y-up conversion turns it back into the same layout three.js expects.

Every object carries custom properties that the web viewer reads from glTF extras:
  side  = N | S | E | W | I   (exterior wall facing, I = interior)   → cutaway hides walls facing the camera
  part  = wall | ceiling | floor | slab | glass | furniture | light
  room  = living | kitchen | bedroom | bath | service | terrace
"""
import math
import os
import sys

import bpy
from mathutils import Vector

H = 2.6      # ceiling height
T = 0.14     # wall thickness
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "apartment.glb")

# ----------------------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"

COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


# ----------------------------------------------------------------------------- materials
MATS = {}


def mat(name, color, rough=0.6, metal=0.0, alpha=1.0, emit=None, emit_strength=0.0, sheen=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    r, g, b = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    # sRGB → linear so the glTF base colour matches the hex we typed
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    bsdf.inputs["Base Color"].default_value = (lin(r), lin(g), lin(b), 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Alpha"].default_value = alpha
    if sheen:
        bsdf.inputs["Sheen Weight"].default_value = sheen
    if emit:
        er, eg, eb = [int(emit[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        bsdf.inputs["Emission Color"].default_value = (lin(er), lin(eg), lin(eb), 1)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1:
        m.surface_render_method = "BLENDED"
        m.use_transparency_overlap = True
    MATS[name] = m
    return m


M = dict(
    plaster=mat("plaster", "#ece8e1", 0.9),
    plaster_ext=mat("plaster_ext", "#c9c5be", 0.95),
    concrete=mat("concrete", "#b4b1ab", 0.95),
    ceiling=mat("ceiling", "#f4f2ee", 0.9),
    wood=mat("wood_floor", "#c8a274", 0.55),
    tile=mat("tile", "#d9d6d0", 0.3),
    stone=mat("stone", "#b7b1a7", 0.85),
    skirting=mat("skirting", "#f2efe9", 0.6),
    frame=mat("frame", "#2b2d30", 0.45, 0.5),
    glass=mat("glass", "#cfe3ec", 0.05, 0.0, 0.22),
    oak=mat("oak", "#c9a87d", 0.6),
    walnut=mat("walnut", "#5b4232", 0.5),
    graphite=mat("graphite", "#33363a", 0.4),
    quartz=mat("quartz", "#eae7e1", 0.2),
    white=mat("white", "#f6f6f4", 0.25),
    steel=mat("steel", "#c6c9cd", 0.3, 0.9),
    brass=mat("brass", "#b8955a", 0.35, 0.85),
    sofa=mat("sofa", "#8d8477", 0.95, sheen=0.4),
    sofa2=mat("sofa_dark", "#6e6559", 0.95, sheen=0.4),
    linen=mat("linen", "#efece6", 0.95, sheen=0.5),
    throw=mat("throw", "#a49f94", 0.95, sheen=0.4),
    pillow=mat("pillow", "#b7a178", 0.95, sheen=0.4),
    rug=mat("rug", "#b3a690", 1.0),
    rug2=mat("rug_terrace", "#a9a493", 1.0),
    screen=mat("screen", "#111214", 0.15, 0.3),
    tv=mat("tv_glow", "#1d3550", 0.3, emit="#2a5a85", emit_strength=0.8),
    leaf=mat("leaf", "#4d7a3a", 0.85),
    leaf2=mat("leaf_light", "#6a9c50", 0.85),
    pot=mat("pot", "#a08066", 0.9),
    lamp=mat("lamp_shade", "#f5ead3", 0.8, emit="#ffd9a0", emit_strength=0.6),
    pendant=mat("pendant", "#1b1b1b", 0.5, emit="#7a5525", emit_strength=0.5),
    downlight=mat("downlight", "#fff4e2", 0.5, emit="#ffe6c2", emit_strength=3.0),
    art=mat("art", "#8ea393", 0.8),
    railing=mat("railing", "#3a3d41", 0.4, 0.6),
)

# ----------------------------------------------------------------------------- primitives


def _finish(obj, name, collection, material, props, bevel):
    obj.name = name
    obj.data.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll(collection).objects.link(obj)
    obj.data.materials.append(material)
    for k, v in props.items():
        obj[k] = v
    if bevel:
        b = obj.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return obj


def box(name, center, size, material, collection="Furniture", bevel=0.012, rot_z=0.0, rot_x=0.0, **props):
    """center/size in plan space: (x, y_up, z_south). Converted to Blender here."""
    x, y, z = center
    sx, sy, sz = size
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -z, y))
    o = bpy.context.active_object
    o.scale = (sx, sz, sy)
    o.rotation_euler = (rot_x, 0, -rot_z)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, collection, material, props, min(bevel, min(sx, sy, sz) * 0.35) if bevel else 0)


def cyl(name, center, radius, height, material, collection="Furniture", r2=None, verts=24, bevel=0.0, **props):
    x, y, z = center
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r2 if r2 is not None else radius, radius2=radius,
                                    depth=height, location=(x, -z, y))
    o = bpy.context.active_object
    for poly in o.data.polygons:
        poly.use_smooth = True
    return _finish(o, name, collection, material, props, bevel)


def sphere(name, center, radius, material, collection="Furniture", scale=(1, 1, 1), **props):
    x, y, z = center
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=(x, -z, y))
    o = bpy.context.active_object
    o.scale = (scale[0], scale[2], scale[1])
    bpy.ops.object.transform_apply(scale=True)
    for poly in o.data.polygons:
        poly.use_smooth = True
    return _finish(o, name, collection, material, props, 0)


def floor_plane(name, rect, material, y=0.0, **props):
    x1, z1, x2, z2 = rect
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x1 + x2) / 2, -(z1 + z2) / 2, y))
    o = bpy.context.active_object
    o.scale = (x2 - x1, z2 - z1, 1)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, "Floors", material, dict(part="floor", **props), 0)


# ----------------------------------------------------------------------------- plan
# walls: (x1, z1, x2, z2, side, opts)
#   opts: y0, y1, glass, noskirt, ext=(start, end)
#   ext: extend that end by half a wall thickness so corners and T-junctions close up.
#   Never extend into an opening: overlapping boxes with coincident faces render black
#   in Cycles and z-fight in WebGL, so jambs stop exactly at the opening edge.
X = dict(ext=(True, True))
walls = [
    # exterior
    (-0.4, 0, 12.8, 0, "N", dict(**X)),
    (0, 0, 0, 1.3, "W", dict(ext=(True, False))), (0, 2.8, 0, 4.45, "W", dict(ext=(False, True))),
    (0, 1.3, 0, 2.8, "W", dict(y0=0, y1=0.9)),                    # window sill
    (0, 1.3, 0, 2.8, "W", dict(y0=2.25, y1=H, noskirt=True)),      # window head
    (0, 1.3, 0, 2.8, "W", dict(y0=0.9, y1=2.25, glass=True)),      # window
    (0, 4.45, -0.4, 4.45, "N", dict(**X)), (-0.4, 4.45, -0.4, 5.95, "W", dict(**X)),  # bath bump-out
    (-0.4, 5.95, 7.8, 5.95, "S", dict(**X)),
    (12.8, 0, 12.8, 5.95, "E", dict(**X)),                          # terrace east
    (7.8, 5.95, 12.8, 5.95, "S", dict(y0=0.12, y1=1.1, glass=True)),  # railing
    # interior
    (3.35, 2.75, 7.8, 2.75, "I", dict(**X)),
    (3.35, 2.75, 3.35, 2.95, "I", dict(ext=(True, False))), (3.35, 3.85, 3.35, 5.95, "I", dict(ext=(False, True))),
    (-0.4, 4.45, 0.25, 4.45, "I", dict(ext=(True, False))), (1.15, 4.45, 2.25, 4.45, "I", {}), (3.15, 4.45, 3.35, 4.45, "I", dict(ext=(False, True))),
    (2.05, 4.45, 2.05, 5.95, "I", dict(**X)),
    # east wall of the living room with two terrace openings
    (7.8, 0, 7.8, 0.35, "I", dict(ext=(True, False))), (7.8, 1.85, 7.8, 3.95, "I", {}), (7.8, 5.55, 7.8, 5.95, "I", dict(ext=(False, True))),
    (7.8, 0.35, 7.8, 1.85, "I", dict(y0=2.25, y1=H, noskirt=True)),
    (7.8, 3.95, 7.8, 5.55, "I", dict(y0=2.25, y1=H, noskirt=True)),
]
frames = [  # dark aluminium frames: x1,z1,x2,z2,y0,y1,side (same side as the wall they sit in)
    (0, 1.3, 0, 2.8, 0.9, 2.25, "W"),
    (7.8, 0.35, 7.8, 1.85, 0, 2.25, "I"),
    (7.8, 3.95, 7.8, 5.55, 0, 2.25, "I"),
]
downlights = [(1.2, 1.2), (2.6, 3.0), (5.6, 1.4), (4.3, 1.4), (5.4, 4.3), (1.0, 5.2), (2.7, 5.2)]

# ----------------------------------------------------------------------------- structure
EXT = T / 2 - 0.008   # 8 mm short of the neighbouring wall's far face (past its 6 mm bevel): hidden inside, never coincident
for i, (x1, z1, x2, z2, side, o) in enumerate(walls):
    y0, y1 = o.get("y0", 0), o.get("y1", H)
    dx, dz = x2 - x1, z2 - z1
    length, rot = math.hypot(dx, dz), math.atan2(dz, dx)
    ux, uz = dx / length, dz / length
    e0, e1 = o.get("ext", (False, False))
    a0, a1 = (EXT if e0 else 0), (EXT if e1 else 0)
    length_ext = length + a0 + a1
    cx, cz = (x1 + x2) / 2 + ux * (a1 - a0) / 2, (z1 + z2) / 2 + uz * (a1 - a0) / 2
    if o.get("glass"):
        box(f"Glass_{side}_{i:02d}", (cx, (y0 + y1) / 2, cz), (length_ext, y1 - y0, 0.02), M["glass"], "Glass",
            bevel=0, rot_z=rot, part="glass", side=side)
        continue
    box(f"Wall_{side}_{i:02d}", (cx, (y0 + y1) / 2, cz), (length_ext, y1 - y0, T),
        M["plaster_ext"] if side in "NSEW" else M["plaster"], "Walls", bevel=0.006, rot_z=rot, part="wall", side=side)
    if y0 == 0 and not o.get("noskirt"):
        s0, s1 = (0.01 if e0 else 0), (0.01 if e1 else 0)
        scx, scz = cx + ux * (s1 - s0) / 2, cz + uz * (s1 - s0) / 2
        box(f"Skirting_{side}_{i:02d}", (scx, 0.045, scz), (length_ext + s0 + s1, 0.09, T + 0.03), M["skirting"], "Walls",
            bevel=0.004, rot_z=rot, part="wall", side=side)

for i, (x1, z1, x2, z2, y0, y1, fside) in enumerate(frames):
    dx, dz = x2 - x1, z2 - z1
    length, rot = math.hypot(dx, dz), math.atan2(dz, dx)
    cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
    ux, uz = dx / length, dz / length
    for j, (off, y, sz) in enumerate([(0, y0 + 0.025, (length + 0.06, 0.05)), (0, y1 - 0.025, (length + 0.06, 0.05)),
                                      (-length / 2, (y0 + y1) / 2, (0.05, y1 - y0)), (length / 2, (y0 + y1) / 2, (0.05, y1 - y0))]):
        box(f"Frame_{i}_{j}", (cx + ux * off, y, cz + uz * off), (sz[0], sz[1], T + 0.04), M["frame"], "Walls",
            bevel=0.004, rot_z=rot, part="frame", side=fside)

# floors (never overlapping each other or the slab: avoids z-fighting on phones)
floor_plane("Floor_living_a", (0, 0, 7.8, 4.45), M["wood"], room="living")
floor_plane("Floor_living_b", (3.35, 4.45, 7.8, 5.95), M["wood"], room="bedroom")
floor_plane("Floor_wet", (-0.4, 4.45, 3.35, 5.95), M["tile"], room="bath")
floor_plane("Floor_terrace", (7.8, 0, 12.8, 5.95), M["stone"], room="terrace")
box("Slab", (6.2, -0.17, 2.975), (13.6, 0.3, 6.75), M["concrete"], "Structure", bevel=0.02, part="slab")

# ceiling + downlights
box("Ceiling", (3.7, H + 0.05, 2.975), (8.2, 0.1, 5.95), M["ceiling"], "Ceiling", bevel=0, part="ceiling")
for i, (x, z) in enumerate(downlights):
    cyl(f"Downlight_{i}", (x, H - 0.004, z), 0.07, 0.008, M["downlight"], "Ceiling", part="ceiling")

# terrace curb + rail cap + planters
box("Curb", (10.3, 0.06, 5.95), (5, 0.12, T), M["graphite"], "Structure", part="slab", room="terrace")
box("RailCap", (10.3, 1.12, 5.95), (5.0, 0.05, 0.06), M["railing"], "Structure", part="slab", room="terrace")
for i, x in enumerate([7.9, 9.15, 10.4, 11.65, 12.75]):
    box(f"RailPost_{i}", (x, 0.6, 5.95), (0.04, 1.0, 0.04), M["railing"], "Structure", bevel=0, part="slab", room="terrace")

# sliding glass leaves stacked open + doors
box("SlideLeaf_1", (7.86, 1.12, 1.5), (0.03, 2.2, 0.7), M["glass"], "Glass", bevel=0, part="glass", side="I")
box("SlideLeaf_2", (7.86, 1.12, 5.2), (0.03, 2.2, 0.7), M["glass"], "Glass", bevel=0, part="glass", side="I")
box("Door_bedroom", (3.42, 1.05, 4.28), (0.05, 2.1, 0.85), M["oak"], "Furniture", part="furniture", room="bedroom")
box("Door_bath", (0.7, 1.05, 4.52), (0.85, 2.1, 0.05), M["oak"], "Furniture", part="furniture", room="bath")
box("Door_service", (2.7, 1.05, 4.52), (0.85, 2.1, 0.05), M["oak"], "Furniture", part="furniture", room="service")
box("Door_entry", (1.25, 1.05, 0.08), (0.9, 2.1, 0.05), M["walnut"], "Furniture", part="furniture", room="living")
box("Door_handle", (1.6, 1.0, 0.12), (0.05, 0.05, 0.05), M["brass"], "Furniture", bevel=0.01, part="furniture", room="living")

# ----------------------------------------------------------------------------- furniture helpers
_seed = [11]


def rnd():
    _seed[0] = (_seed[0] * 9301 + 49297) % 233280
    return _seed[0] / 233280


def plant(name, x, z, s=1.0, pot=True, room="living"):
    if pot:
        cyl(f"{name}_pot", (x, 0.16 * s, z), 0.18 * s, 0.32 * s, M["pot"], r2=0.14 * s, part="furniture", room=room)
    cyl(f"{name}_stem", (x, 0.57 * s, z), 0.025, 0.5 * s, M["walnut"], r2=0.04, verts=10, part="furniture", room=room)
    for i in range(7):
        sphere(f"{name}_leaf{i}", (x + (rnd() - 0.5) * 0.36 * s, 0.78 * s + rnd() * 0.34 * s, z + (rnd() - 0.5) * 0.36 * s),
               0.2 * s, M["leaf"] if i % 2 else M["leaf2"], scale=(1, 0.7, 1), part="furniture", room=room)


def sofa(name, x, z, rot, room="living"):
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)

    def part(n, dx, y, dz, size, m, rx=0.0):
        px, pz = P(dx, dz)
        box(f"{name}_{n}", (px, y, pz), size, m, rot_z=rot, rot_x=rx, bevel=0.03, part="furniture", room=room)

    part("seat", 0, 0.21, 0, (1.9, 0.42, 0.9), M["sofa"])
    part("back", 0, 0.63, -0.33, (1.9, 0.45, 0.25), M["sofa2"])
    part("armL", -0.85, 0.3, 0, (0.2, 0.6, 0.9), M["sofa2"])
    part("armR", 0.85, 0.3, 0, (0.2, 0.6, 0.9), M["sofa2"])
    part("cushL", -0.4, 0.5, 0.1, (0.7, 0.16, 0.55), M["sofa"])
    part("cushR", 0.4, 0.5, 0.1, (0.7, 0.16, 0.55), M["sofa"])
    part("pillow1", 0.5, 0.72, -0.2, (0.4, 0.4, 0.14), M["pillow"])
    part("pillow2", -0.5, 0.72, -0.2, (0.4, 0.4, 0.14), M["throw"])


def chair(name, x, z, rot, room="terrace"):
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0)
    box(f"{name}_seat", (px, 0.45, pz), (0.42, 0.04, 0.42), M["oak"], rot_z=rot, part="furniture", room=room)
    px, pz = P(0, -0.2)
    box(f"{name}_back", (px, 0.68, pz), (0.42, 0.45, 0.04), M["oak"], rot_z=rot, part="furniture", room=room)
    for i, (dx, dz) in enumerate([(-0.18, -0.18), (0.18, -0.18), (-0.18, 0.18), (0.18, 0.18)]):
        px, pz = P(dx, dz)
        box(f"{name}_leg{i}", (px, 0.22, pz), (0.03, 0.45, 0.03), M["frame"], bevel=0, part="furniture", room=room)


def lounger(name, x, z, room="terrace"):
    box(f"{name}_bed", (x, 0.35, z), (0.7, 0.08, 1.3), M["linen"], bevel=0.03, part="furniture", room=room)
    box(f"{name}_back", (x, 0.6, z - 0.85), (0.7, 0.08, 0.7), M["linen"], bevel=0.03, rot_x=-0.9, part="furniture", room=room)
    box(f"{name}_frame", (x, 0.3, z), (0.75, 0.05, 1.35), M["oak"], part="furniture", room=room)
    for i, (dx, dz) in enumerate([(-0.3, -0.6), (0.3, -0.6), (-0.3, 0.6), (0.3, 0.6)]):
        box(f"{name}_leg{i}", (x + dx, 0.15, z + dz), (0.05, 0.3, 0.05), M["oak"], bevel=0, part="furniture", room=room)


F = dict(part="furniture")

# ---------- living
box("Curtain_1", (0.12, 1.15, 1.15), (0.05, 2.3, 0.6), M["linen"], bevel=0.02, room="living", **F)
box("Curtain_2", (0.12, 1.15, 2.95), (0.05, 2.3, 0.6), M["linen"], bevel=0.02, room="living", **F)
box("CurtainRail", (0.1, 2.35, 2.05), (0.03, 0.03, 2.0), M["frame"], bevel=0, room="living", **F)
box("Rug_living", (1.7, 0.009, 2.1), (2.4, 0.012, 2.8), M["rug"], bevel=0.005, room="living", **F)
sofa("Sofa_1", 1.7, 0.75, 0)
sofa("Sofa_2", 1.7, 3.45, math.pi)
box("CoffeeTable", (1.7, 0.4, 2.1), (1.0, 0.05, 0.5), M["walnut"], room="living", **F)
for i, (x, z) in enumerate([(1.25, 1.9), (2.15, 1.9), (1.25, 2.3), (2.15, 2.3)]):
    box(f"CoffeeLeg_{i}", (x, 0.2, z), (0.04, 0.4, 0.04), M["frame"], bevel=0, room="living", **F)
box("Bowl", (1.5, 0.5, 2.1), (0.22, 0.14, 0.22), M["brass"], bevel=0.04, room="living", **F)
plant("Plant_table", 1.95, 2.1, 0.4)
box("TVunit", (3.0, 0.225, 0.3), (1.4, 0.45, 0.4), M["walnut"], bevel=0.02, room="living", **F)
box("TV", (3.0, 1.15, 0.11), (1.2, 0.7, 0.04), M["screen"], bevel=0.005, room="living", **F)
box("TVglow", (3.0, 1.15, 0.1), (0.95, 0.02, 0.05), M["tv"], bevel=0, room="living", **F)
box("SideTable", (0.55, 0.34, 0.5), (0.4, 0.03, 0.4), M["oak"], room="living", **F)
box("SideTableLeg", (0.55, 0.17, 0.5), (0.05, 0.34, 0.05), M["frame"], bevel=0, room="living", **F)
plant("Plant_living", 0.55, 0.5, 0.7)

# ---------- kitchen / dining
K = dict(room="kitchen", **F)
box("KitchenBase", (6.1, 0.45, 2.38), (3.4, 0.9, 0.6), M["graphite"], bevel=0.008, **K)
box("KitchenTop", (6.1, 0.92, 2.38), (3.4, 0.04, 0.62), M["quartz"], bevel=0.008, **K)
box("KitchenUpper", (6.1, 2.05, 2.5), (3.4, 0.7, 0.35), M["graphite"], bevel=0.008, **K)
box("KitchenShelf", (6.1, 1.72, 2.5), (3.4, 0.04, 0.35), M["graphite"], bevel=0.005, **K)
box("Backsplash", (6.1, 1.35, 2.71), (3.4, 0.6, 0.02), M["quartz"], bevel=0, **K)
for i, x in enumerate([4.9, 5.5, 6.1, 6.7, 7.3]):
    box(f"UpperGap_{i}", (x, 2.05, 2.5), (0.02, 0.66, 0.34), M["frame"], bevel=0, **K)
box("Sink", (5.3, 0.945, 2.38), (0.5, 0.02, 0.4), M["steel"], bevel=0.005, **K)
box("Tap", (5.3, 1.1, 2.55), (0.02, 0.3, 0.02), M["steel"], bevel=0, **K)
box("TapSpout", (5.24, 1.25, 2.55), (0.14, 0.02, 0.02), M["steel"], bevel=0, **K)
box("Hob", (6.9, 0.947, 2.38), (0.6, 0.012, 0.5), M["screen"], bevel=0.004, **K)
for i, (dx, dz) in enumerate([(-0.15, -0.12), (0.15, -0.12), (-0.15, 0.12), (0.15, 0.12)]):
    cyl(f"Burner_{i}", (6.9 + dx, 0.96, 2.38 + dz), 0.06, 0.012, M["steel"], **K)
box("Hood", (6.9, 1.72, 2.55), (0.7, 0.4, 0.3), M["steel"], bevel=0.01, **K)
box("Fridge", (7.35, 0.95, 0.42), (0.7, 1.9, 0.7), M["steel"], bevel=0.015, **K)
box("FridgeHandle", (7.02, 1.05, 0.42), (0.02, 0.9, 0.03), M["frame"], bevel=0, **K)
box("Pantry", (6.65, 1.1, 0.37), (0.6, 2.2, 0.6), M["graphite"], bevel=0.01, **K)
box("IslandBase", (3.9, 0.525, 1.5), (0.5, 1.05, 2.0), M["graphite"], bevel=0.01, **K)
box("IslandTop", (3.85, 1.07, 1.5), (0.7, 0.04, 2.1), M["oak"], bevel=0.01, **K)
for i, z in enumerate([0.85, 1.5, 2.15]):
    box(f"StoolPost_{i}", (3.38, 0.35, z), (0.04, 0.7, 0.04), M["frame"], bevel=0, **K)
    cyl(f"StoolSeat_{i}", (3.38, 0.72, z), 0.18, 0.06, M["walnut"], bevel=0.01, **K)
    cyl(f"StoolBase_{i}", (3.38, 0.02, z), 0.2, 0.02, M["frame"], **K)
box("Vase", (3.85, 1.2, 0.9), (0.2, 0.25, 0.2), M["white"], bevel=0.03, **K)
plant("Plant_island", 3.85, 0.9, 0.4, pot=False, room="kitchen")
for i, z in enumerate([1.1, 1.9]):
    box(f"PendantCord_{i}", (3.85, 2.1, z), (0.01, 1.0, 0.01), M["frame"], bevel=0, **K)
    cyl(f"Pendant_{i}", (3.85, 1.58, z), 0.1, 0.18, M["pendant"], r2=0.16, part="light", room="kitchen")

# ---------- bedroom
Bd = dict(room="bedroom", **F)
box("BedFrame", (5.4, 0.14, 4.85), (1.7, 0.28, 2.1), M["walnut"], bevel=0.02, **Bd)
box("Mattress", (5.4, 0.39, 4.85), (1.6, 0.22, 2.0), M["linen"], bevel=0.05, **Bd)
box("Duvet", (5.4, 0.52, 4.5), (1.62, 0.05, 1.3), M["throw"], bevel=0.02, **Bd)
box("Headboard", (5.4, 0.75, 5.87), (1.7, 0.9, 0.1), M["sofa"], bevel=0.02, **Bd)
box("PillowL", (5.0, 0.6, 5.6), (0.65, 0.18, 0.4), M["linen"], bevel=0.05, **Bd)
box("PillowR", (5.8, 0.6, 5.6), (0.65, 0.18, 0.4), M["linen"], bevel=0.05, **Bd)
box("PillowAccent", (5.0, 0.58, 5.33), (0.45, 0.16, 0.14), M["pillow"], bevel=0.04, **Bd)
for i, x in enumerate([4.35, 6.45]):
    box(f"Nightstand_{i}", (x, 0.25, 5.65), (0.45, 0.5, 0.45), M["oak"], bevel=0.015, **Bd)
    box(f"LampStem_{i}", (x, 0.68, 5.65), (0.03, 0.35, 0.03), M["brass"], bevel=0, **Bd)
    cyl(f"LampShade_{i}", (x, 0.88, 5.65), 0.12, 0.2, M["lamp"], r2=0.15, part="light", room="bedroom")
box("Wardrobe", (3.72, 1.15, 4.9), (0.6, 2.3, 1.9), M["oak"], bevel=0.012, **Bd)
for i, z in enumerate([4.2, 4.7, 5.2, 5.7]):
    box(f"WardrobeGap_{i}", (4.03, 1.15, z), (0.02, 2.2, 0.02), M["walnut"], bevel=0, **Bd)
for i, z in enumerate([4.45, 5.45]):
    box(f"WardrobeHandle_{i}", (4.04, 1.1, z), (0.03, 0.25, 0.02), M["brass"], bevel=0, **Bd)
box("Desk", (7.0, 0.74, 3.1), (1.2, 0.04, 0.55), M["oak"], **Bd)
box("DeskLegL", (6.45, 0.36, 3.1), (0.04, 0.72, 0.5), M["frame"], bevel=0, **Bd)
box("DeskLegR", (7.55, 0.36, 3.1), (0.04, 0.72, 0.5), M["frame"], bevel=0, **Bd)
box("Laptop", (7.0, 0.77, 3.1), (0.4, 0.02, 0.28), M["steel"], bevel=0.004, **Bd)
box("LaptopScreen", (7.0, 0.9, 2.97), (0.4, 0.26, 0.01), M["screen"], bevel=0, **Bd)
box("DeskChairSeat", (7.0, 0.45, 3.6), (0.45, 0.05, 0.45), M["frame"], bevel=0.02, **Bd)
box("DeskChairBack", (7.0, 0.72, 3.8), (0.45, 0.5, 0.05), M["frame"], bevel=0.02, **Bd)
box("DeskChairPost", (7.0, 0.22, 3.6), (0.04, 0.43, 0.04), M["steel"], bevel=0, **Bd)
box("Rug_bedroom", (5.4, 0.009, 3.85), (2.2, 0.012, 1.5), M["rug"], bevel=0.005, **Bd)
plant("Plant_bedroom", 7.4, 5.5, 0.9, room="bedroom")
box("ArtFrame", (5.4, 1.7, 5.88), (0.7, 0.5, 0.03), M["frame"], bevel=0.004, **Bd)
box("Art", (5.4, 1.7, 5.865), (0.62, 0.42, 0.01), M["art"], bevel=0, **Bd)

# ---------- bathroom
Ba = dict(room="bath", **F)
box("ShowerGlass", (0.55, 1.1, 5.2), (0.02, 2.2, 1.4), M["glass"], "Glass", bevel=0, part="glass", side="I", room="bath")
box("ShowerPost", (0.55, 1.1, 4.5), (0.03, 2.2, 0.03), M["frame"], bevel=0, **Ba)
box("ShowerPipe", (0.1, 1.5, 4.6), (0.03, 1.2, 0.03), M["steel"], bevel=0, **Ba)
box("ShowerHead", (0.2, 2.1, 4.75), (0.2, 0.02, 0.2), M["steel"], bevel=0.005, **Ba)
box("Toilet", (0.95, 0.2, 5.62), (0.38, 0.4, 0.55), M["white"], bevel=0.05, **Ba)
box("Cistern", (0.95, 0.6, 5.82), (0.38, 0.4, 0.18), M["white"], bevel=0.03, **Ba)
box("Vanity", (1.65, 0.4, 5.7), (0.6, 0.8, 0.45), M["oak"], bevel=0.01, **Ba)
box("VanityTop", (1.65, 0.82, 5.7), (0.62, 0.04, 0.47), M["quartz"], bevel=0.006, **Ba)
box("Basin", (1.65, 0.9, 5.7), (0.4, 0.12, 0.3), M["white"], bevel=0.04, **Ba)
box("BasinTap", (1.65, 1.0, 5.85), (0.03, 0.2, 0.03), M["steel"], bevel=0, **Ba)
box("Mirror", (1.65, 1.6, 5.92), (0.55, 0.7, 0.02), M["steel"], bevel=0, **Ba)
box("TowelRail", (1.7, 1.3, 4.54), (0.3, 0.5, 0.03), M["white"], bevel=0.01, **Ba)

# ---------- service
Sv = dict(room="service", **F)
box("Washer", (2.4, 0.425, 5.62), (0.6, 0.85, 0.6), M["white"], bevel=0.02, **Sv)
cyl("WasherDoor", (2.4, 0.45, 5.31), 0.19, 0.03, M["frame"], **Sv)
box("ShelfA", (2.7, 1.6, 5.75), (0.5, 0.02, 0.4), M["oak"], **Sv)
box("ShelfB", (2.7, 2.0, 5.75), (0.5, 0.02, 0.4), M["oak"], **Sv)
box("Detergent", (2.6, 1.77, 5.75), (0.2, 0.3, 0.15), M["white"], bevel=0.02, **Sv)
box("Boiler", (3.05, 0.425, 5.65), (0.5, 0.85, 0.45), M["white"], bevel=0.02, **Sv)
box("BoilerTop", (3.05, 0.9, 5.65), (0.4, 0.1, 0.35), M["steel"], bevel=0.01, **Sv)

# ---------- terrace
Tr = dict(room="terrace", **F)
for i, x in enumerate([8.3, 9.15, 10.0, 10.85, 11.7, 12.55]):
    box(f"Planter_{i}", (x, 0.2, 5.6), (0.6, 0.4, 0.4), M["pot"], bevel=0.02, **Tr)
    plant(f"PlanterPlant_{i}", x, 5.6, 0.7, pot=False, room="terrace")
lounger("Lounger_1", 11.6, 3.2)
lounger("Lounger_2", 10.6, 3.2)
cyl("BistroTop", (9.0, 0.74, 1.3), 0.4, 0.04, M["oak"], bevel=0.01, **Tr)
box("BistroPost", (9.0, 0.36, 1.3), (0.06, 0.72, 0.06), M["frame"], bevel=0, **Tr)
cyl("BistroBase", (9.0, 0.015, 1.3), 0.25, 0.03, M["frame"], **Tr)
chair("Chair_1", 8.3, 1.3, math.pi / 2)
chair("Chair_2", 9.7, 1.3, -math.pi / 2)
plant("Plant_terrace_1", 12.3, 0.5, 1.5, room="terrace")
plant("Plant_terrace_2", 8.2, 0.5, 1.2, room="terrace")
plant("Plant_terrace_3", 12.3, 5.0, 1.0, room="terrace")
box("WallLight", (10.3, 2.0, 0.08), (0.12, 0.25, 0.12), M["frame"], bevel=0.01, part="light", room="terrace")
box("Rug_terrace", (11.0, 0.009, 3.2), (3.0, 0.012, 2.2), M["rug2"], bevel=0.005, **Tr)

# ----------------------------------------------------------------------------- export
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=OUT, export_format="GLB", export_apply=True, export_extras=True,
    export_yup=True, export_lights=False, export_cameras=False, export_animations=False,
    export_materials="EXPORT", export_normals=True, use_selection=False,
)
print("exported", OUT, os.path.getsize(OUT) // 1024, "KB", "objects:", len(bpy.data.objects))

# Optional: save a .blend next to the script for opening in Blender
if "--blend" in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT), "..", "blender", "apartment.blend"))
