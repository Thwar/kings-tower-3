"""
King's Tower · Dept. D — builds the apartment in Blender and exports apartment.glb.

Run headless:   python3 blender/build_apartment.py            (needs `pip install bpy`)
Or in Blender:  blender --background --python blender/build_apartment.py

Units are metres. Blender axes: X east, Y north, Z up.
The plan (src/scene/plan.js) uses x east, z south, y up — so plan z becomes -Y here,
and the glTF exporter's Y-up conversion turns it back into the same layout three.js expects.

Materials are PBR image textures generated procedurally by textures.py (seamless, offline) and
projected onto every object with a world-space box projection, so grain and tiles line up across pieces.

Every object carries custom properties that the web viewer reads from glTF extras:
  side  = N | S | E | W | I   (exterior wall facing, I = interior)   → cutaway hides walls facing the camera
  part  = wall | frame | ceiling | floor | slab | glass | furniture | light
  room  = living | kitchen | bedroom | bath | service | terrace

Interior concept: minimal bachelor pad — warm off-white plaster, mid-oak plank floor, matte black and walnut,
charcoal linen and black leather, one statement piece per room, nothing on the counters that doesn't earn its place.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textures  # noqa: E402

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
_lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(hexs):
    return tuple(_lin(int(hexs[i:i + 2], 16) / 255) for i in (1, 3, 5))


def mat(name, color, rough=0.6, metal=0.0, alpha=1.0, emit=None, emit_strength=0.0, sheen=0.0, clearcoat=0.0):
    """flat Principled material"""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*_rgb(color), 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Alpha"].default_value = alpha
    if sheen:
        bsdf.inputs["Sheen Weight"].default_value = sheen
    if clearcoat:
        bsdf.inputs["Coat Weight"].default_value = clearcoat
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*_rgb(emit), 1)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1:
        m.surface_render_method = "BLENDED"
        m.use_transparency_overlap = True
    MATS[name] = m
    return m


def tmat(name, tex_set, metal=0.0, rough_mul=1.0, tint=None, normal_strength=1.0, clearcoat=0.0, sheen=0.0):
    """textured Principled material from a procedural set; UVs are box-projected per object using m['tile']"""
    if name in MATS:
        return MATS[name]
    t = textures.ensure(tex_set)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = metal
    if clearcoat:
        bsdf.inputs["Coat Weight"].default_value = clearcoat
    if sheen:
        bsdf.inputs["Sheen Weight"].default_value = sheen

    def image(path, colorspace):
        img = bpy.data.images.load(path, check_existing=True)
        img.colorspace_settings.name = colorspace
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = img
        return n

    col = image(t["color"], "sRGB")
    if tint:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1.0
        nt.links.new(col.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (*_rgb(tint), 1)
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    else:
        nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    rough = image(t["rough"], "Non-Color")
    if rough_mul != 1.0:
        mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
        nt.links.new(rough.outputs["Color"], mm.inputs[0]); nt.links.new(mm.outputs[0], bsdf.inputs["Roughness"])
    else:
        nt.links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
    nrm = image(t["normal"], "Non-Color")
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = normal_strength
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    m["tile"] = t["tile"]
    MATS[name] = m
    return m


M = dict(
    # architecture
    plaster=tmat("plaster", "plaster"),
    plaster_ext=tmat("plaster_ext", "plaster_ext"),
    concrete=tmat("concrete", "concrete"),
    ceiling=mat("ceiling", "#f2f0ec", 0.9),
    wood=tmat("oak_floor", "oak_floor", clearcoat=0.25),
    tile=tmat("tile", "tile"),
    stone=tmat("paving", "paving"),
    skirting=mat("skirting", "#f1eee8", 0.55),
    frame=mat("frame", "#222427", 0.4, 0.6),
    glass=mat("glass", "#d6e6ee", 0.03, 0.0, 0.2),
    railing=mat("railing", "#2b2d30", 0.35, 0.7),
    # finishes
    oak=tmat("oak", "oak"),
    walnut=tmat("walnut", "walnut", clearcoat=0.15),
    black=tmat("matte_black", "matte_black", rough_mul=0.5),
    quartz=tmat("quartz", "quartz", clearcoat=0.4),
    steel=tmat("brushed", "brushed", metal=0.95),
    white=mat("white", "#f6f6f4", 0.22, clearcoat=0.5),
    # soft
    charcoal=tmat("charcoal", "charcoal", sheen=0.4),
    linen=tmat("linen", "linen", sheen=0.5),
    rug=tmat("wool_rug", "wool_rug"),
    rug_dark=tmat("wool_rug_dark", "wool_rug", tint="#5b5a58"),
    leather=tmat("leather", "leather"),
    leather_tan=tmat("leather_tan", "leather_tan"),
    # small stuff
    screen=mat("screen", "#0f1012", 0.12, 0.3, clearcoat=0.8),
    tv=mat("tv_glow", "#1a2e45", 0.3, emit="#2d5f8a", emit_strength=0.6),
    leaf=mat("leaf", "#3f6b33", 0.8),
    leaf2=mat("leaf_light", "#5c8f47", 0.8),
    bark=mat("bark", "#5a4632", 0.9),
    pot_black=mat("pot_black", "#26272a", 0.6),
    pot_clay=mat("pot_clay", "#9b7b63", 0.9),
    brass=mat("brass", "#b08d57", 0.3, 0.9),
    lamp=mat("lamp_shade", "#f3ead6", 0.7, emit="#ffd6a0", emit_strength=0.7),
    pendant=mat("pendant", "#161616", 0.45, 0.2, emit="#8a6030", emit_strength=0.4),
    downlight=mat("downlight", "#fff4e2", 0.5, emit="#ffe6c2", emit_strength=3.0),
    art=mat("art", "#2f3336", 0.7),
    art2=tmat("art_print", "concrete", tint="#d8d2c8"),
    vinyl=mat("vinyl", "#1b1b1b", 0.3, clearcoat=0.3),
    book=mat("book", "#7d7468", 0.85),
    towel=mat("towel", "#dcd7cd", 1.0, sheen=0.6),
)

# ----------------------------------------------------------------------------- primitives


def uv_box(obj, tile):
    """world-space box projection: each face is mapped along its dominant world normal, 1 UV unit = `tile` metres"""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    mw = obj.matrix_world
    nmat = mw.to_3x3().inverted().transposed()
    for poly in me.polygons:
        n = (nmat @ poly.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            u, v = (co.y, co.z) if ax == 0 else (co.x, co.z) if ax == 1 else (co.x, co.y)
            uv[li].uv = (u / tile, v / tile)


def _finish(obj, name, collection, material, props, bevel, segments=3, smooth=False):
    obj.name = name
    obj.data.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll(collection).objects.link(obj)
    obj.data.materials.append(material)
    for k, v in props.items():
        obj[k] = v
    bpy.context.view_layer.update()
    if material.get("tile"):
        uv_box(obj, material["tile"])
    if bevel:
        b = obj.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = segments
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
        b.harden_normals = True
    for poly in obj.data.polygons:
        poly.use_smooth = smooth
    if bevel and segments >= 4:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def box(name, center, size, material, collection="Furniture", bevel=0.012, rot_z=0.0, rot_x=0.0, segments=3, **props):
    """center/size in plan space: (x, y_up, z_south). Converted to Blender here."""
    x, y, z = center
    sx, sy, sz = size
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -z, y))
    o = bpy.context.active_object
    o.scale = (sx, sz, sy)
    o.rotation_euler = (rot_x, 0, -rot_z)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, collection, material, props, min(bevel, min(sx, sy, sz) * 0.42) if bevel else 0, segments)


def soft(name, center, size, material, r=0.05, **kw):
    """cushion-like box: big rounded bevel, smooth shading"""
    return box(name, center, size, material, bevel=r, segments=5, **kw)


def cyl(name, center, radius, height, material, collection="Furniture", r2=None, verts=32, bevel=0.0, rot=(0, 0, 0), **props):
    x, y, z = center
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r2 if r2 is not None else radius, radius2=radius,
                                    depth=height, location=(x, -z, y), rotation=rot)
    o = bpy.context.active_object
    return _finish(o, name, collection, material, props, bevel, 3, smooth=True)


def sphere(name, center, radius, material, collection="Furniture", scale=(1, 1, 1), rot=(0, 0, 0), sub=2, **props):
    x, y, z = center
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=radius, location=(x, -z, y), rotation=rot)
    o = bpy.context.active_object
    o.scale = (scale[0], scale[2], scale[1])
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, collection, material, props, 0, smooth=True)


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
    # bath + service wall: one door from the living into the service room (x 2.2–3.05); no door into the bath from the living
    (-0.4, 4.45, 2.2, 4.45, "I", dict(ext=(True, False))), (3.05, 4.45, 3.35, 4.45, "I", dict(ext=(False, True))),
    # bath/service partition with the bathroom door (z 4.6–5.4) reached from inside the service room
    (2.05, 4.45, 2.05, 4.6, "I", dict(ext=(True, False))), (2.05, 5.4, 2.05, 5.95, "I", dict(ext=(False, True))),
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
downlights = [(1.2, 1.0), (1.2, 3.4), (2.6, 2.2), (5.6, 1.4), (4.3, 1.4), (5.4, 4.3), (1.0, 5.2), (2.7, 5.2)]

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
        M["plaster"], "Walls", bevel=0.006, rot_z=rot, part="wall", side=side)
    if y0 == 0 and not o.get("noskirt"):
        s0, s1 = (0.01 if e0 else 0), (0.01 if e1 else 0)
        scx, scz = cx + ux * (s1 - s0) / 2, cz + uz * (s1 - s0) / 2
        box(f"Skirting_{side}_{i:02d}", (scx, 0.04, scz), (length_ext + s0 + s1, 0.08, T + 0.024), M["skirting"], "Walls",
            bevel=0.003, rot_z=rot, part="wall", side=side)

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
    cyl(f"Downlight_{i}", (x, H - 0.004, z), 0.05, 0.008, M["downlight"], "Ceiling", part="ceiling")

# terrace curb + railing
box("Curb", (10.3, 0.06, 5.95), (5, 0.12, T), M["concrete"], "Structure", part="slab", room="terrace")
box("RailCap", (10.3, 1.12, 5.95), (5.0, 0.04, 0.05), M["railing"], "Structure", part="slab", room="terrace")
for i, x in enumerate([7.9, 9.15, 10.4, 11.65, 12.75]):
    box(f"RailPost_{i}", (x, 0.6, 5.95), (0.03, 1.0, 0.03), M["railing"], "Structure", bevel=0, part="slab", room="terrace")

# sliding glass leaves stacked open + doors (flush, black hardware)
box("SlideLeaf_1", (7.86, 1.12, 1.5), (0.03, 2.2, 0.7), M["glass"], "Glass", bevel=0, part="glass", side="I")
box("SlideLeaf_2", (7.86, 1.12, 5.2), (0.03, 2.2, 0.7), M["glass"], "Glass", bevel=0, part="glass", side="I")
box("Door_bedroom", (3.42, 1.05, 4.28), (0.04, 2.1, 0.85), M["walnut"], "Furniture", part="furniture", room="bedroom")
box("Door_service", (2.63, 1.05, 4.52), (0.82, 2.1, 0.04), M["walnut"], "Furniture", part="furniture", room="service")   # open, flat inside the service room
box("Door_bath", (2.12, 1.05, 5.0), (0.04, 2.1, 0.78), M["walnut"], "Furniture", part="furniture", room="bath")        # open, flat against the partition
box("Door_entry", (1.25, 1.05, 0.08), (0.9, 2.1, 0.05), M["black"], "Furniture", part="furniture", room="living")
box("Door_handle", (1.58, 1.02, 0.13), (0.02, 0.3, 0.02), M["frame"], "Furniture", bevel=0.005, part="furniture", room="living")

# ----------------------------------------------------------------------------- furniture helpers
_seed = [11]


def rnd():
    _seed[0] = (_seed[0] * 9301 + 49297) % 233280
    return _seed[0] / 233280


def plant(name, x, z, s=1.0, pot="black", room="living", leaves=34, kind="ficus"):
    """fiddle-leaf-fig style: trunk, a few branches, and many small smooth leaves along them"""
    if pot == "black":
        cyl(f"{name}_pot", (x, 0.17 * s, z), 0.17 * s, 0.34 * s, M["pot_black"], r2=0.13 * s, bevel=0.01, part="furniture", room=room)
    elif pot == "clay":
        cyl(f"{name}_pot", (x, 0.17 * s, z), 0.18 * s, 0.34 * s, M["pot_clay"], r2=0.14 * s, bevel=0.01, part="furniture", room=room)
    top = 0.34 * s if pot else 0.0
    cyl(f"{name}_trunk", (x, top + 0.45 * s, z), 0.018 * s, 0.9 * s, M["bark"], r2=0.03 * s, verts=10, part="furniture", room=room)
    branches = []
    for b in range(5):
        a = b * 1.3 + rnd() * 0.6
        by = top + (0.55 + b * 0.12) * s
        bl = (0.28 + rnd() * 0.16) * s
        tilt = math.radians(28 + rnd() * 20)
        cyl(f"{name}_br{b}", (x + math.cos(a) * bl * 0.45, by + bl * 0.4, z + math.sin(a) * bl * 0.45), 0.008 * s, bl, M["bark"], verts=6,
            rot=(tilt, 0, -a), part="furniture", room=room)
        branches.append((a, by, bl))
    n = leaves * 3
    for i in range(n):
        a, by, bl = branches[i % len(branches)]
        t = 0.2 + rnd() * 0.9                               # position along the branch
        r = bl * t * 0.9
        spread = (rnd() - 0.5) * 0.22 * s                   # leaves fan out around the branch
        ang = a + (rnd() - 0.5) * 2.2
        lx, ly, lz = x + math.cos(a) * r + math.cos(ang) * abs(spread), by + bl * t * 0.8 + (rnd() - 0.5) * 0.1 * s, z + math.sin(a) * r + math.sin(ang) * abs(spread)
        sphere(f"{name}_leaf{i}", (lx, ly, lz), 0.065 * s,
               M["leaf"] if i % 3 else M["leaf2"], scale=(1.0, 0.2, 1.6), rot=(0.4 + (rnd() - 0.5) * 0.9, (rnd() - 0.5) * 0.7, -ang), sub=2,
               part="furniture", room=room)


def grass(name, x, z, room="terrace", blades=10, s=1.0):
    for i in range(blades):
        a = rnd() * math.pi * 2; r = rnd() * 0.12 * s
        cyl(f"{name}_b{i}", (x + math.cos(a) * r, 0.42 * s, z + math.sin(a) * r), 0.006, (0.5 + rnd() * 0.5) * s,
            M["leaf2"] if i % 2 else M["leaf"], verts=5, rot=(rnd() * 0.25, rnd() * 0.25, 0), part="furniture", room=room)


def sofa(name, x, z, rot, w=2.4, fabric=None, room="living"):
    """low modular sofa: platform, loose seat and back cushions, thin black feet"""
    fabric = fabric or M["charcoal"]
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)

    def part(n, dx, y, dz, size, m, r=0.02, rx=0.0):
        px, pz = P(dx, dz)
        box(f"{name}_{n}", (px, y, pz), size, m, rot_z=rot, rot_x=rx, bevel=r, segments=5, part="furniture", room=room)

    part("base", 0, 0.2, 0, (w, 0.22, 0.95), fabric, 0.03)
    part("back", 0, 0.5, -0.4, (w, 0.42, 0.16), fabric, 0.04)
    for i, dx in enumerate([-w / 4, w / 4]):
        part(f"seat{i}", dx, 0.38, 0.06, (w / 2 - 0.03, 0.14, 0.8), fabric, 0.06)
        part(f"backc{i}", dx, 0.6, -0.28, (w / 2 - 0.06, 0.4, 0.12), fabric, 0.05, rx=-0.15)
    part("cushion", w / 4 - 0.1, 0.55, -0.15, (0.45, 0.42, 0.12), M["leather_tan"], 0.04, rx=-0.25)
    for i, (dx, dz) in enumerate([(-w / 2 + 0.1, -0.35), (w / 2 - 0.1, -0.35), (-w / 2 + 0.1, 0.35), (w / 2 - 0.1, 0.35)]):
        px, pz = P(dx, dz)
        box(f"{name}_foot{i}", (px, 0.045, pz), (0.03, 0.09, 0.03), M["frame"], bevel=0, part="furniture", room=room)


def lounge_chair(name, x, z, rot, room="living"):
    """Barcelona-style: two tufted leather cushions on flat steel bars"""
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0.05)
    soft(f"{name}_seat", (px, 0.4, pz), (0.75, 0.09, 0.75), M["leather"], r=0.03, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, -0.32)
    soft(f"{name}_back", (px, 0.72, pz), (0.75, 0.62, 0.09), M["leather"], r=0.03, rot_z=rot, rot_x=-0.28, part="furniture", room=room)
    for i, dx in enumerate([-0.34, 0.34]):
        px, pz = P(dx, 0.05)
        box(f"{name}_bar{i}", (px, 0.33, pz), (0.02, 0.03, 0.72), M["steel"], bevel=0, rot_z=rot, part="furniture", room=room)
        px, pz = P(dx, -0.3)
        box(f"{name}_leg{i}", (px, 0.36, pz), (0.02, 0.72, 0.03), M["steel"], bevel=0, rot_z=rot, rot_x=-0.3, part="furniture", room=room)
        px, pz = P(dx, 0.1)
        box(f"{name}_leg2{i}", (px, 0.17, pz), (0.02, 0.36, 0.03), M["steel"], bevel=0, rot_z=rot, rot_x=0.45, part="furniture", room=room)


def stool(name, x, z, room="kitchen"):
    cyl(f"{name}_seat", (x, 0.71, z), 0.17, 0.05, M["leather"], bevel=0.015, part="furniture", room=room)
    cyl(f"{name}_ring", (x, 0.5, z), 0.16, 0.012, M["frame"], r2=0.16, verts=24, part="furniture", room=room)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        cyl(f"{name}_leg{i}", (x + math.cos(a) * 0.14, 0.34, z + math.sin(a) * 0.14), 0.008, 0.7, M["frame"], verts=8,
            rot=(math.sin(a) * 0.1, math.cos(a) * 0.1, 0), part="furniture", room=room)


def office_chair(name, x, z, rot, room="bedroom"):
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0)
    soft(f"{name}_seat", (px, 0.47, pz), (0.5, 0.07, 0.5), M["leather"], r=0.03, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, -0.24)
    soft(f"{name}_back", (px, 0.78, pz), (0.46, 0.58, 0.06), M["leather"], r=0.03, rot_z=rot, rot_x=-0.12, part="furniture", room=room)
    for i, dx in enumerate([-0.27, 0.27]):
        px, pz = P(dx, -0.05)
        box(f"{name}_arm{i}", (px, 0.66, pz), (0.03, 0.02, 0.3), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)
        box(f"{name}_armp{i}", (px, 0.56, pz), (0.02, 0.18, 0.02), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)
    cx0, cz0 = P(0, 0)
    cyl(f"{name}_post", (cx0, 0.28, cz0), 0.02, 0.36, M["steel"], verts=10, part="furniture", room=room)
    for i in range(5):
        a = i * math.pi * 2 / 5 + rot
        box(f"{name}_spoke{i}", (x + math.cos(a) * 0.15, 0.04, z + math.sin(a) * 0.15), (0.3, 0.025, 0.03), M["black"], bevel=0.005,
            rot_z=-a, part="furniture", room=room)
        sphere(f"{name}_caster{i}", (x + math.cos(a) * 0.29, 0.03, z + math.sin(a) * 0.29), 0.028, M["frame"], sub=1, part="furniture", room=room)


def floor_lamp(name, x, z, room="living"):
    cyl(f"{name}_base", (x, 0.012, z), 0.16, 0.024, M["frame"], bevel=0.004, part="furniture", room=room)
    cyl(f"{name}_pole", (x, 0.85, z), 0.012, 1.7, M["frame"], verts=10, part="furniture", room=room)
    cyl(f"{name}_arm", (x + 0.3, 1.66, z), 0.01, 0.62, M["frame"], verts=8, rot=(0, math.radians(90), 0), part="light", room=room)
    cyl(f"{name}_shade", (x + 0.6, 1.5, z), 0.16, 0.22, M["lamp"], r2=0.2, part="light", room=room)


def wall_art(name, x, y, z, w, h, rot, mat_in, frame=True, room="living", depth=0.03):
    c, s = math.cos(rot), math.sin(rot)
    if frame:
        box(f"{name}_frame", (x, y, z), (w, h, depth), M["frame"], bevel=0.004, rot_z=rot, part="furniture", room=room)
    box(f"{name}_print", (x - s * depth * 0.55, y, z + c * depth * 0.55), (w - 0.06, h - 0.06, 0.006), mat_in, bevel=0,
        rot_z=rot, part="furniture", room=room)


F = dict(part="furniture")

# ---------- living: one sofa facing the TV wall, a leather lounge chair by the window, one lamp, one large print
L = dict(room="living", **F)
box("Rug_living", (1.75, 0.008, 2.3), (2.6, 0.012, 3.0), M["rug"], bevel=0.004, **L)
sofa("Sofa", 1.75, 3.7, math.pi, w=2.4)                      # against the bath wall, facing north
lounge_chair("Lounge", 0.75, 1.75, -math.pi / 2 - 0.5)        # by the window, angled toward the TV
box("CoffeeTable", (1.75, 0.34, 2.2), (1.1, 0.03, 0.55), M["walnut"], bevel=0.006, **L)
box("CoffeeFrame", (1.75, 0.16, 2.2), (0.9, 0.3, 0.4), M["frame"], bevel=0.004, **L)
box("Book1", (1.55, 0.37, 2.15), (0.28, 0.025, 0.2), M["book"], bevel=0.004, **L)
box("Book2", (1.55, 0.395, 2.17), (0.24, 0.02, 0.18), M["art"], bevel=0.004, **L)
box("Tray", (2.1, 0.365, 2.28), (0.3, 0.015, 0.2), M["frame"], bevel=0.004, **L)
floor_lamp("FloorLamp", 3.05, 3.85)
# media wall on the north wall: floating walnut console, wall-mounted TV, turntable + a few records
box("Console", (2.55, 0.42, 0.3), (1.8, 0.28, 0.42), M["walnut"], bevel=0.008, **L)
box("ConsoleGap", (2.55, 0.42, 0.095), (1.74, 0.01, 0.005), M["frame"], bevel=0, **L)
box("TV", (2.55, 1.35, 0.11), (1.35, 0.78, 0.035), M["screen"], bevel=0.004, **L)
box("TVpanel", (2.55, 1.35, 0.128), (1.29, 0.72, 0.004), M["screen"], bevel=0, **L)
box("Turntable", (3.1, 0.585, 0.3), (0.42, 0.05, 0.34), M["black"], bevel=0.006, **L)
cyl("Platter", (3.1, 0.615, 0.3), 0.14, 0.01, M["vinyl"], **L)
for i in range(6):
    box(f"Record{i}", (1.8 + i * 0.012, 0.72, 0.31), (0.008, 0.31, 0.31), M["vinyl"] if i % 2 else M["book"], bevel=0, rot_z=0.06 * i, **L)
box("Speaker1", (1.72, 0.14, 0.3), (0.16, 0.28, 0.2), M["black"], bevel=0.008, **L)
box("Speaker2", (3.38, 0.14, 0.3), (0.16, 0.28, 0.2), M["black"], bevel=0.008, **L)
wall_art("Art_living", 0.09, 1.55, 3.7, 0.9, 1.2, math.pi / 2, M["art2"])         # west wall, south of the window
plant("Plant_living", 3.05, 0.55, s=1.35)
# window dressing: a single sheer, black rail
box("Curtain", (0.11, 1.35, 3.0), (0.04, 2.35, 0.5), M["linen"], bevel=0.015, **L)
box("CurtainRail", (0.1, 2.5, 2.05), (0.02, 0.02, 2.1), M["frame"], bevel=0, **L)
box("CoatRail", (1.95, 1.7, 0.09), (0.5, 0.03, 0.03), M["frame"], bevel=0, **L)
for i in range(3):
    box(f"Hook{i}", (1.8 + i * 0.15, 1.65, 0.11), (0.012, 0.08, 0.05), M["frame"], bevel=0, **L)

# ---------- kitchen / dining: matte black run, quartz top, oak uppers; island with two leather stools
K = dict(room="kitchen", **F)
box("KitchenBase", (6.1, 0.44, 2.38), (3.4, 0.88, 0.6), M["black"], bevel=0.005, **K)
for i, x in enumerate([4.9, 5.5, 6.1, 6.7, 7.3]):
    box(f"BaseGap_{i}", (x, 0.44, 2.075), (0.004, 0.84, 0.01), M["frame"], bevel=0, **K)
box("KitchenTop", (6.1, 0.9, 2.38), (3.44, 0.03, 0.63), M["quartz"], bevel=0.006, **K)
box("Backsplash", (6.1, 1.28, 2.71), (3.4, 0.7, 0.02), M["quartz"], bevel=0, **K)
box("KitchenUpper", (6.1, 2.1, 2.55), (3.4, 0.7, 0.35), M["oak"], bevel=0.005, **K)
for i, x in enumerate([4.9, 5.5, 6.1, 6.7, 7.3]):
    box(f"UpperGap_{i}", (x, 2.1, 2.373), (0.004, 0.66, 0.01), M["frame"], bevel=0, **K)
box("UpperLED", (6.1, 1.732, 2.5), (3.3, 0.01, 0.2), M["downlight"], bevel=0, part="light", room="kitchen")
box("Sink", (5.2, 0.905, 2.4), (0.55, 0.02, 0.4), M["steel"], bevel=0.005, **K)
box("Tap", (5.2, 1.06, 2.6), (0.018, 0.32, 0.018), M["frame"], bevel=0, **K)
box("TapSpout", (5.13, 1.21, 2.6), (0.16, 0.018, 0.018), M["frame"], bevel=0, **K)
box("Hob", (6.8, 0.912, 2.4), (0.6, 0.008, 0.5), M["screen"], bevel=0.003, **K)
box("Hood", (6.8, 1.66, 2.55), (0.7, 0.06, 0.35), M["steel"], bevel=0.006, **K)
box("Column", (7.15, 1.1, 0.42), (1.3, 2.2, 0.66), M["black"], bevel=0.006, **K)     # integrated fridge + pantry
box("ColumnGap1", (7.15, 1.1, 0.087), (0.004, 2.16, 0.01), M["frame"], bevel=0, **K)
box("ColumnGap2", (7.15, 1.55, 0.087), (1.26, 0.004, 0.01), M["frame"], bevel=0, **K)
# breakfast bar: the L return of the kitchen run, as on the plan (bar at x≈4.6, stools on the living side, ~1 m walkway to the living)
box("BarBase", (4.62, 0.44, 1.75), (0.5, 0.88, 1.95), M["black"], bevel=0.005, **K)
box("BarTop", (4.5, 0.905, 1.75), (0.85, 0.035, 2.05), M["oak"], bevel=0.006, **K)
stool("Stool1", 4.08, 1.05)
stool("Stool2", 4.08, 1.6)
stool("Stool3", 4.08, 2.15)
box("Board", (4.6, 0.93, 0.95), (0.32, 0.015, 0.22), M["walnut"], bevel=0.003, **K)
cyl("Bowl", (4.6, 0.96, 2.3), 0.13, 0.08, M["black"], r2=0.08, bevel=0.01, **K)
for i, z in enumerate([1.25, 2.15]):
    cyl(f"PendantCord_{i}", (4.4, 2.1, z), 0.003, 1.0, M["frame"], verts=6, **K)
    cyl(f"Pendant_{i}", (4.4, 1.55, z), 0.07, 0.24, M["pendant"], r2=0.09, part="light", room="kitchen")

# ---------- bedroom: low platform bed, wide charcoal headboard, floating nightstands, walnut desk, one big plant
B = dict(room="bedroom", **F)
box("Rug_bedroom", (5.45, 0.008, 4.0), (2.6, 0.012, 1.6), M["rug_dark"], bevel=0.004, **B)
box("BedPlatform", (5.45, 0.13, 4.95), (2.0, 0.24, 2.2), M["walnut"], bevel=0.01, **B)
soft("Mattress", (5.45, 0.36, 4.95), (1.6, 0.24, 2.0), M["linen"], r=0.05, **B)
soft("Duvet", (5.45, 0.5, 4.6), (1.64, 0.07, 1.25), M["charcoal"], r=0.03, **B)
box("Headboard", (5.45, 0.65, 5.86), (2.6, 1.1, 0.06), M["charcoal"], bevel=0.01, **B)
soft("PillowL", (5.05, 0.55, 5.62), (0.68, 0.16, 0.42), M["linen"], r=0.05, **B)
soft("PillowR", (5.85, 0.55, 5.62), (0.68, 0.16, 0.42), M["linen"], r=0.05, **B)
for i, x in enumerate([4.15, 6.75]):
    box(f"Nightstand_{i}", (x, 0.45, 5.7), (0.45, 0.12, 0.38), M["walnut"], bevel=0.006, **B)
    box(f"WallLampArm_{i}", (x, 1.15, 5.88), (0.02, 0.02, 0.14), M["frame"], bevel=0, **B)
    cyl(f"WallLamp_{i}", (x, 1.1, 5.78), 0.05, 0.12, M["lamp"], r2=0.06, part="light", room="bedroom")
box("Wardrobe", (3.7, 1.15, 4.9), (0.6, 2.3, 1.9), M["black"], bevel=0.006, **B)
for i, z in enumerate([4.2, 4.7, 5.2, 5.7]):
    box(f"WardrobeGap_{i}", (4.003, 1.15, z), (0.01, 2.26, 0.004), M["frame"], bevel=0, **B)
box("Desk", (7.05, 0.74, 3.15), (1.3, 0.03, 0.6), M["walnut"], bevel=0.005, **B)
for i, x in enumerate([6.45, 7.65]):
    box(f"DeskLeg_{i}", (x, 0.36, 3.15), (0.03, 0.72, 0.55), M["frame"], bevel=0, **B)
box("Monitor", (7.05, 1.05, 2.95), (0.62, 0.36, 0.02), M["screen"], bevel=0.003, **B)
box("MonitorStand", (7.05, 0.83, 2.95), (0.03, 0.14, 0.03), M["frame"], bevel=0, **B)
box("MonitorFoot", (7.05, 0.76, 2.95), (0.2, 0.01, 0.12), M["frame"], bevel=0.003, **B)
box("Keyboard", (7.05, 0.765, 3.25), (0.36, 0.012, 0.12), M["black"], bevel=0.003, **B)
box("DeskLamp", (7.55, 0.76, 2.98), (0.03, 0.03, 0.03), M["frame"], bevel=0, **B)
office_chair("DeskChair", 7.05, 3.75, math.pi)
plant("Plant_bedroom", 7.35, 5.5, s=1.5)
wall_art("Art_bedroom", 5.45, 1.75, 5.88, 1.5, 0.6, 0, M["art2"], room="bedroom")

# ---------- bathroom: black fixtures, walnut vanity, white basin
Ba = dict(room="bath", **F)
box("ShowerGlass", (0.55, 1.1, 5.2), (0.01, 2.2, 1.4), M["glass"], "Glass", bevel=0, part="glass", side="I", room="bath")
box("ShowerPost", (0.55, 1.1, 4.5), (0.025, 2.2, 0.025), M["frame"], bevel=0, **Ba)
box("ShowerPipe", (0.08, 1.5, 4.6), (0.02, 1.2, 0.02), M["frame"], bevel=0, **Ba)
box("ShowerHead", (0.2, 2.15, 4.75), (0.25, 0.012, 0.25), M["frame"], bevel=0.003, **Ba)
box("ShowerArm", (0.15, 2.15, 4.62), (0.14, 0.012, 0.012), M["frame"], bevel=0, **Ba)
soft("Toilet", (0.95, 0.2, 5.62), (0.38, 0.4, 0.55), M["white"], r=0.06, **Ba)
soft("Cistern", (0.95, 0.6, 5.82), (0.38, 0.4, 0.18), M["white"], r=0.03, **Ba)
box("Vanity", (1.6, 0.5, 5.7), (0.7, 0.35, 0.45), M["walnut"], bevel=0.006, **Ba)
box("VanityTop", (1.6, 0.69, 5.7), (0.72, 0.03, 0.47), M["quartz"], bevel=0.004, **Ba)
soft("Basin", (1.6, 0.76, 5.68), (0.42, 0.11, 0.32), M["white"], r=0.04, **Ba)
box("BasinTap", (1.6, 0.9, 5.86), (0.02, 0.2, 0.02), M["frame"], bevel=0, **Ba)
box("Mirror", (1.6, 1.55, 5.92), (0.6, 0.8, 0.015), M["steel"], bevel=0, **Ba)
box("MirrorFrame", (1.6, 1.55, 5.915), (0.64, 0.84, 0.01), M["frame"], bevel=0, **Ba)
box("TowelRail", (1.7, 1.2, 4.53), (0.5, 0.015, 0.015), M["frame"], bevel=0, **Ba)
soft("Towel", (1.7, 1.0, 4.55), (0.3, 0.4, 0.03), M["towel"], r=0.01, **Ba)

# ---------- service
Sv = dict(room="service", **F)
box("Washer", (2.4, 0.425, 5.62), (0.6, 0.85, 0.6), M["white"], bevel=0.015, **Sv)
cyl("WasherDoor", (2.4, 0.45, 5.31), 0.19, 0.02, M["screen"], rot=(math.radians(90), 0, 0), **Sv)
box("ShelfA", (2.75, 1.5, 5.75), (0.6, 0.025, 0.35), M["oak"], bevel=0.004, **Sv)
box("ShelfB", (2.75, 1.95, 5.75), (0.6, 0.025, 0.35), M["oak"], bevel=0.004, **Sv)
box("Basket", (2.55, 1.62, 5.75), (0.28, 0.22, 0.28), M["black"], bevel=0.01, **Sv)
box("Boiler", (3.05, 0.45, 5.65), (0.5, 0.9, 0.45), M["white"], bevel=0.015, **Sv)

# ---------- terrace: outdoor lounge set, one lounger, black planters with grasses, olive trees
Tr = dict(room="terrace", **F)
box("Rug_terrace", (10.3, 0.006, 3.0), (3.4, 0.012, 2.4), M["rug"], bevel=0.004, **Tr)
sofa("OutdoorSofa", 10.3, 4.05, math.pi, w=2.0, fabric=M["linen"], room="terrace")
box("OutdoorTable", (10.3, 0.3, 2.6), (0.9, 0.04, 0.5), M["walnut"], bevel=0.006, **Tr)
box("OutdoorTableFrame", (10.3, 0.14, 2.6), (0.8, 0.26, 0.4), M["frame"], bevel=0.004, **Tr)
for i, (x, z, r) in enumerate([(8.9, 2.3, -math.pi / 2), (11.7, 2.3, math.pi / 2)]):
    lounge_chair(f"OutdoorChair{i}", x, z, r, room="terrace")
box("LoungerBed", (11.9, 0.3, 0.9), (0.7, 0.08, 1.5), M["linen"], bevel=0.03, segments=5, **Tr)
box("LoungerBack", (11.9, 0.55, 0.2), (0.7, 0.08, 0.7), M["linen"], bevel=0.03, segments=5, rot_x=1.0, **Tr)
box("LoungerFrame", (11.9, 0.24, 0.85), (0.74, 0.04, 1.6), M["frame"], bevel=0.004, **Tr)
for i, (dx, dz) in enumerate([(-0.33, -0.7), (0.33, -0.7), (-0.33, 0.7), (0.33, 0.7)]):
    box(f"LoungerLeg{i}", (11.9 + dx, 0.11, 0.85 + dz), (0.03, 0.22, 0.03), M["frame"], bevel=0, **Tr)
for i, x in enumerate([8.35, 9.35, 10.35, 11.35, 12.35]):
    box(f"Planter_{i}", (x, 0.2, 5.62), (0.8, 0.4, 0.38), M["pot_black"], bevel=0.01, **Tr)
    grass(f"Grass_{i}", x, 5.62, s=1.0)
plant("Olive_1", 12.3, 0.5, s=1.6, pot="black", room="terrace", leaves=48)
plant("Olive_2", 8.3, 0.5, s=1.3, pot="black", room="terrace", leaves=40)
box("WallLight", (10.3, 2.0, 0.08), (0.1, 0.22, 0.1), M["frame"], bevel=0.008, part="light", room="terrace")
box("WallLightGlow", (10.3, 2.0, 0.14), (0.06, 0.16, 0.02), M["downlight"], bevel=0, part="light", room="terrace")

# ----------------------------------------------------------------------------- export
# render_views.py and bake_lightmaps.py build the scene but must not overwrite the baked site/apartment.glb
if os.environ.get("KT_SKIP_EXPORT"):
    print("build done (export skipped)")
else:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=OUT, export_format="GLB", export_apply=True, export_extras=True,
        export_yup=True, export_lights=False, export_cameras=False, export_animations=False,
        export_materials="EXPORT", export_normals=True, export_image_format="AUTO", export_jpeg_quality=82,
        use_selection=False,
    )
    print("exported", OUT, os.path.getsize(OUT) // 1024, "KB", "objects:", len(bpy.data.objects))

# Optional: save a .blend next to the script for opening in Blender
if "--blend" in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT), "..", "blender", "apartment.blend"))
