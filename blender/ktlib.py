"""
Shared Blender toolkit for the apartment models (build_apartment.py = King's Tower Dept. D, build_duna.py = Torre Duna Tipo E).

Units are metres. Blender axes: X east, Y north, Z up.
The plan (site/*/plan.js) uses x east, z south, y up — so plan z becomes -Y here,
and the glTF exporter's Y-up conversion turns it back into the same layout three.js expects.

Materials are PBR image textures generated procedurally by textures.py (seamless, offline) and
projected onto every object with a world-space box projection, so grain and tiles line up across pieces.

Every object carries custom properties that the web viewer reads from glTF extras:
  side  = N | S | E | W | I   (exterior wall facing, I = interior)   → cutaway hides walls facing the camera
  part  = wall | frame | ceiling | floor | slab | glass | furniture | light
  room  = living | kitchen | bedroom | bath | service | terrace

Importing this module resets Blender to an empty scene and creates the material palette `M`.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textures  # noqa: E402

H = 2.6      # ceiling height (default)
T = 0.14     # wall thickness
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


# ----------------------------------------------------------------------------- walls + frames
# walls: (x1, z1, x2, z2, side, opts)
#   opts: y0, y1, glass, noskirt, ext=(start, end)
#   ext: extend that end by half a wall thickness so corners and T-junctions close up.
#   Never extend into an opening: overlapping boxes with coincident faces render black
#   in Cycles and z-fight in WebGL, so jambs stop exactly at the opening edge.
X = dict(ext=(True, True))
EXT = T / 2 - 0.008   # 8 mm short of the neighbouring wall's far face (past its 6 mm bevel): hidden inside, never coincident


def build_walls(walls, frames, height=H):
    """walls and dark aluminium frames (x1,z1,x2,z2,y0,y1,side) as boxes with the viewer's tags"""
    for i, (x1, z1, x2, z2, side, o) in enumerate(walls):
        y0, y1 = o.get("y0", 0), o.get("y1", height)
        # Walls that meet overlap inside the junction (see ext). Their top faces would be coplanar there and
        # z-fight (black squares in Cycles), so every wall top gets its own sub-centimetre offset below the ceiling.
        jit = 0.0004 * (i % 23)
        if y1 >= height:
            y1 = height - jit
        dx, dz = x2 - x1, z2 - z1
        length, rot = math.hypot(dx, dz), math.atan2(dz, dx)
        ux, uz = dx / length, dz / length
        e0, e1 = o.get("ext", (False, False))
        a0, a1 = (EXT if e0 else 0), (EXT if e1 else 0)
        length_ext = length + a0 + a1
        cx, cz = (x1 + x2) / 2 + ux * (a1 - a0) / 2, (z1 + z2) / 2 + uz * (a1 - a0) / 2
        if o.get("glass"):
            # a pane sits between a sill and a head: sink 1 cm into both so no face of it is coplanar with theirs
            g0, g1 = (y0 - 0.01 if y0 > 0 else y0), (y1 + 0.01 if y1 < height - 0.05 else y1)
            box(f"Glass_{side}_{i:02d}", (cx, (g0 + g1) / 2, cz), (length_ext, g1 - g0, 0.02), M["glass"], "Glass",
                bevel=0, rot_z=rot, part="glass", side=side)
            continue
        box(f"Wall_{side}_{i:02d}", (cx, (y0 + y1) / 2, cz), (length_ext, y1 - y0, T),
            M["plaster"], "Walls", bevel=0.006, rot_z=rot, part="wall", side=side)
        if y0 == 0 and not o.get("noskirt"):
            s0, s1 = (0.01 if e0 else 0), (0.01 if e1 else 0)
            scx, scz = cx + ux * (s1 - s0) / 2, cz + uz * (s1 - s0) / 2
            box(f"Skirting_{side}_{i:02d}", (scx, (0.08 - jit) / 2, scz), (length_ext + s0 + s1, 0.08 - jit, T + 0.024), M["skirting"], "Walls",
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


def downlights(points, height=H):
    for i, (x, z) in enumerate(points):
        cyl(f"Downlight_{i}", (x, height - 0.004, z), 0.05, 0.008, M["downlight"], "Ceiling", part="ceiling")


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


def chair(name, x, z, rot, room="kitchen", fabric=None):
    """dining chair: thin black frame, leather seat and back. rot 0 faces south (back on the north side)"""
    fabric = fabric or M["leather"]
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0)
    soft(f"{name}_seat", (px, 0.46, pz), (0.44, 0.05, 0.44), fabric, r=0.02, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, -0.2)
    soft(f"{name}_back", (px, 0.72, pz), (0.42, 0.42, 0.035), fabric, r=0.015, rot_z=rot, rot_x=-0.1, part="furniture", room=room)
    for i, (dx, dz) in enumerate([(-0.19, -0.19), (0.19, -0.19), (-0.19, 0.19), (0.19, 0.19)]):
        px, pz = P(dx, dz)
        box(f"{name}_leg{i}", (px, 0.22, pz), (0.02, 0.44, 0.02), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)


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


# ----------------------------------------------------------------------------- mirror
def mirror_x(width):
    """flip the whole model east-west about x = width/2 (plan built mirrored to the brochure): bakes the flip into
    every mesh, restores outward normals, and swaps the E/W cutaway tags"""
    import bmesh
    flip = Matrix.Translation((width, 0, 0)) @ Matrix.Diagonal((-1, 1, 1, 1))
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        o.matrix_world = flip @ o.matrix_world
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        bm.to_mesh(o.data); bm.free()
        if o.get("side") in ("E", "W"):
            o["side"] = "W" if o["side"] == "E" else "E"


# ----------------------------------------------------------------------------- export
def export(out, blend=None):
    """render_views.py and bake_lightmaps.py build the scene but must not overwrite the baked GLB (KT_SKIP_EXPORT)"""
    if os.environ.get("KT_SKIP_EXPORT"):
        print("build done (export skipped)")
    else:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.export_scene.gltf(
            filepath=out, export_format="GLB", export_apply=True, export_extras=True,
            export_yup=True, export_lights=False, export_cameras=False, export_animations=False,
            export_materials="EXPORT", export_normals=True, export_image_format="AUTO", export_jpeg_quality=82,
            use_selection=False,
        )
        print("exported", out, os.path.getsize(out) // 1024, "KB", "objects:", len(bpy.data.objects))
    if blend and "--blend" in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=blend)
