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
# Interior design scheme. "bachelor" (default): off-white plaster, oak floor, walnut and black.
# "loft": grey walls, polished concrete floor, LED coves, gaming desk, glass cabinet, lit vanity, sectional + fur rug.
STYLE = os.environ.get("KT_STYLE", "bachelor")
# Multi-storey builds: set_level(n, y) makes every primitive built afterwards carry level=n and sit y metres up.
LEVEL = [0]
Y_BASE = [0.0]


def set_level(n, y=0.0):
    LEVEL[0] = n
    Y_BASE[0] = y
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

if STYLE == "loft":
    M.update(
        plaster=tmat("plaster_grey", "plaster", tint="#868b94"),
        skirting=mat("skirting_dark", "#33363b", 0.5),
        ceiling=mat("ceiling_loft", "#e3e5e8", 0.9),
        wood=tmat("concrete_floor", "concrete", tint="#a3a5a9", rough_mul=0.55, clearcoat=0.45),
        rug=tmat("fur", "wool_rug", tint="#f6f4f0", sheen=0.8),
        rug_dark=tmat("fur", "wool_rug", tint="#f6f4f0", sheen=0.8),
        charcoal=tmat("charcoal_loft", "charcoal", tint="#43464c", sheen=0.4),
        linen=tmat("linen_loft", "linen", tint="#d9dbdf", sheen=0.5),
        art2=tmat("art_print_loft", "concrete", tint="#8e949c"),
    )
    M.update(
        led=mat("led", "#bff3ff", 0.5, emit="#35d6ff", emit_strength=5.0),
        led_soft=mat("led_soft", "#bff3ff", 0.5, emit="#35d6ff", emit_strength=1.6),
        neon=mat("neon", "#ffb0ff", 0.5, emit="#ff4fd8", emit_strength=3.0),
        white_gloss=mat("white_gloss", "#f4f5f7", 0.15, clearcoat=0.7),
        chair_red=mat("chair_red", "#b3202a", 0.5),
        plush_blue=mat("plush_blue", "#3fa7e6", 0.9, sheen=0.9),
        plush_orange=mat("plush_orange", "#f08a3c", 0.9, sheen=0.9),
        plush_yellow=mat("plush_yellow", "#f2c43d", 0.9, sheen=0.9),
        plush_white=mat("plush_white", "#f3f1ee", 0.9, sheen=0.9),
        bottle=mat("bottle", "#4a2a12", 0.1, clearcoat=0.8),
        bottle2=mat("bottle2", "#1f4d2b", 0.1, clearcoat=0.8),
        cloth_a=mat("cloth_a", "#d94f6a", 0.9), cloth_b=mat("cloth_b", "#3b5fa8", 0.9), cloth_c=mat("cloth_c", "#efe9df", 0.9),
        monitor_glow=mat("monitor_glow", "#26496b", 0.3, emit="#4c8fd8", emit_strength=1.2),
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
    props.setdefault("level", LEVEL[0])
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
    y += Y_BASE[0]
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
    y += Y_BASE[0]
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r2 if r2 is not None else radius, radius2=radius,
                                    depth=height, location=(x, -z, y), rotation=rot)
    o = bpy.context.active_object
    return _finish(o, name, collection, material, props, bevel, 3, smooth=True)


def sphere(name, center, radius, material, collection="Furniture", scale=(1, 1, 1), rot=(0, 0, 0), sub=2, **props):
    x, y, z = center
    y += Y_BASE[0]
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=radius, location=(x, -z, y), rotation=rot)
    o = bpy.context.active_object
    o.scale = (scale[0], scale[2], scale[1])
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, name, collection, material, props, 0, smooth=True)


def floor_plane(name, rect, material, y=0.0, **props):
    x1, z1, x2, z2 = rect
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x1 + x2) / 2, -(z1 + z2) / 2, y + Y_BASE[0]))
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


def build_walls(walls, frames, height=H, y_base=0.0, level=None, frame_mat=None, cladding=None):
    """cladding: {side: material} paints the OUTER face of exterior walls (a 2 cm panel 1 mm off the wall, so the
    interior face keeps the plaster); frame_mat overrides the window-frame material (default dark aluminium)"""
    level = LEVEL[0] if level is None else level
    frame_mat = frame_mat or M["frame"]
    OUTWARD = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
    """walls and dark aluminium frames (x1,z1,x2,z2,y0,y1,side) as boxes with the viewer's tags"""
    for i, (x1, z1, x2, z2, side, o) in enumerate(walls):
        y0, y1 = o.get("y0", 0), o.get("y1", height)
        base_floor = y0 == 0
        # Walls that meet overlap inside the junction (see ext). Their top faces would be coplanar there and
        # z-fight (black squares in Cycles), so every wall top gets its own sub-centimetre offset below the ceiling.
        jit = 0.0004 * (i % 23)
        if y1 >= height:
            y1 = height - jit
        y0, y1 = y0 + y_base, y1 + y_base
        dx, dz = x2 - x1, z2 - z1
        length, rot = math.hypot(dx, dz), math.atan2(dz, dx)
        ux, uz = dx / length, dz / length
        e0, e1 = o.get("ext", (False, False))
        a0, a1 = (EXT if e0 else 0), (EXT if e1 else 0)
        length_ext = length + a0 + a1
        cx, cz = (x1 + x2) / 2 + ux * (a1 - a0) / 2, (z1 + z2) / 2 + uz * (a1 - a0) / 2
        if o.get("glass"):
            # a pane sits between a sill and a head: sink 1 cm into both so no face of it is coplanar with theirs
            g0, g1 = (y0 - 0.01 if not base_floor else y0), (y1 + 0.01 if y1 < y_base + height - 0.05 else y1)
            box(f"Glass_{side}_L{level}_{i:02d}", (cx, (g0 + g1) / 2, cz), (length_ext, g1 - g0, 0.02), M["glass"], "Glass",
                bevel=0, rot_z=rot, part="glass", side=side, level=level)
            continue
        box(f"Wall_{side}_L{level}_{i:02d}", (cx, (y0 + y1) / 2, cz), (length_ext, y1 - y0, T),
            o.get("mat") or M["plaster"], "Walls", bevel=0.006, rot_z=rot, part="wall", side=side, level=level)
        if cladding and side in cladding and not o.get("noclad"):
            nx, nz = -uz, ux                                   # one of the wall's two normals
            ox, oz = OUTWARD[side]
            if nx * ox + nz * oz < 0:
                nx, nz = -nx, -nz                              # pick the one facing out
            d = T / 2 + 0.011
            box(f"Clad_{side}_L{level}_{i:02d}", (cx + nx * d, (y0 + y1) / 2, cz + nz * d), (length_ext + 0.02, y1 - y0, 0.02),
                cladding[side], "Walls", bevel=0, rot_z=rot, part="wall", side=side, level=level)
        if base_floor and not o.get("noskirt"):
            s0, s1 = (0.01 if e0 else 0), (0.01 if e1 else 0)
            scx, scz = cx + ux * (s1 - s0) / 2, cz + uz * (s1 - s0) / 2
            box(f"Skirting_{side}_L{level}_{i:02d}", (scx, y_base + (0.08 - jit) / 2, scz), (length_ext + s0 + s1, 0.08 - jit, T + 0.024), M["skirting"], "Walls",
                bevel=0.003, rot_z=rot, part="wall", side=side, level=level)

    for i, (x1, z1, x2, z2, y0, y1, fside) in enumerate(frames):
        dx, dz = x2 - x1, z2 - z1
        length, rot = math.hypot(dx, dz), math.atan2(dz, dx)
        cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
        ux, uz = dx / length, dz / length
        for j, (off, y, sz) in enumerate([(0, y0 + 0.025, (length + 0.06, 0.05)), (0, y1 - 0.025, (length + 0.06, 0.05)),
                                          (-length / 2, (y0 + y1) / 2, (0.05, y1 - y0)), (length / 2, (y0 + y1) / 2, (0.05, y1 - y0))]):
            box(f"Frame_L{level}_{i}_{j}", (cx + ux * off, y + y_base, cz + uz * off), (sz[0], sz[1], T + 0.06), frame_mat, "Walls",
                bevel=0.004, rot_z=rot, part="frame", side=fside, level=level)


def downlights(points, height=H, level=None):
    level = LEVEL[0] if level is None else level
    for i, (x, z) in enumerate(points):
        cyl(f"Downlight_L{level}_{i}", (x, height - 0.004, z), 0.05, 0.008, M["downlight"], "Ceiling", part="ceiling", level=level)


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


# ----------------------------------------------------------------------------- house pieces (multi-storey)
def prism(name, pts, y0, y1, material, collection="Walls", **props):
    """vertical extrusion of a 2D polygon in plan space (list of (x, z)), from height y0 to y1 — gable ends, landings"""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    y0, y1 = y0 + Y_BASE[0], y1 + Y_BASE[0]
    bottom = [bm.verts.new((x, -z, y0)) for x, z in pts]
    top = [bm.verts.new((x, -z, y1)) for x, z in pts]
    bm.faces.new(bottom[::-1]); bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        bm.faces.new((bottom[i], bottom[(i + 1) % n], top[(i + 1) % n], top[i]))
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    return _finish(o, name, collection, material, props, 0)


def side_wall(name, x, pts, material, thickness=T, collection="Walls", **props):
    """a vertical wall standing at constant x, its outline given as (z, y) points — stair spandrels, gable ends"""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    y0 = Y_BASE[0]
    a = [bm.verts.new((x - thickness / 2, -z, y0 + y)) for z, y in pts]
    b = [bm.verts.new((x + thickness / 2, -z, y0 + y)) for z, y in pts]
    bm.faces.new(a)
    bm.faces.new(b)
    n = len(pts)
    for i in range(n):
        bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    return _finish(o, name, collection, material, props, 0)


def roof_slab(name, x1, x2, z_eave, z_ridge, y_eave, y_ridge, material, thickness=0.12, collection="Ceiling", **props):
    """one pitched roof plane between an eave line and a ridge line (both along x), as a tilted box"""
    dz, dy = z_ridge - z_eave, y_ridge - y_eave
    length = math.hypot(dz, dy)
    ang = math.atan2(dy, -dz)          # tilt about x: positive raises the ridge end when the ridge is north of the eave
    box(name, ((x1 + x2) / 2, (y_eave + y_ridge) / 2 + thickness / 2 * math.cos(ang), (z_eave + z_ridge) / 2),
        (x2 - x1, thickness, length), material, collection, bevel=0, rot_x=ang, **props)


def stair_flight(name, x1, x2, z_start, z_end, y0, y1, steps, material, room="hall", open_risers=False, stringer=None):
    """straight flight from z_start (bottom, height y0) to z_end (top, height y1): treads and risers as boxes.
    open_risers=True leaves the risers out; stringer=<material> adds one central sloped beam under the treads"""
    run = (z_end - z_start) / steps
    rise = (y1 - y0) / steps
    for i in range(steps):
        y = y0 + rise * (i + 1)
        zc = z_start + run * (i + 0.5)
        box(f"{name}_t{i}", ((x1 + x2) / 2, y - 0.02, zc), (x2 - x1, 0.04, abs(run) + 0.02), material, bevel=0.004,
            part="furniture", room=room)
        if not open_risers:
            box(f"{name}_r{i}", ((x1 + x2) / 2, y - rise / 2 - 0.02, z_start + run * i), (x2 - x1, rise - 0.02, 0.03), material, bevel=0,
                part="furniture", room=room)
    if stringer:
        ang = math.atan2(y1 - y0, z_end - z_start)
        box(f"{name}_stringer", ((x1 + x2) / 2, (y0 + y1) / 2 - 0.16, (z_start + z_end) / 2), (0.16, 0.28, math.hypot(y1 - y0, z_end - z_start) - 0.2),
            stringer, bevel=0.01, rot_x=-ang, part="furniture", room=room)


def wood_railing(name, x1, z1, x2, z2, y0, h=0.95, material=None, room="hall", newels=(True, True)):
    """balustrade with turned balusters every 13 cm, a moulded handrail and ball-topped newels at the ends"""
    material = material or M["walnut"]
    dx, dz = x2 - x1, z2 - z1
    length, rot = math.hypot(dx, dz), math.atan2(dz, dx)
    n = max(2, int(length / 0.13))
    for i in range(1, n):
        t = i / n
        x, z = x1 + dx * t, z1 + dz * t
        cyl(f"{name}_b{i}", (x, y0 + h / 2 - 0.02, z), 0.014, h - 0.06, material, verts=8, part="furniture", room=room)
        sphere(f"{name}_k{i}", (x, y0 + h * 0.36, z), 0.028, material, sub=1, part="furniture", room=room)
        sphere(f"{name}_k2{i}", (x, y0 + h * 0.66, z), 0.022, material, sub=1, part="furniture", room=room)
    box(f"{name}_rail", ((x1 + x2) / 2, y0 + h, (z1 + z2) / 2), (length + 0.1, 0.06, 0.08), material, bevel=0.012, segments=4, rot_z=rot,
        part="furniture", room=room)
    for k, (x, z) in enumerate([(x1, z1), (x2, z2)]):
        if newels[k]:
            box(f"{name}_n{k}", (x, y0 + h / 2 + 0.03, z), (0.09, h + 0.06, 0.09), material, bevel=0.008, part="furniture", room=room)
            sphere(f"{name}_nb{k}", (x, y0 + h + 0.13, z), 0.065, material, sub=2, part="furniture", room=room)





def railing(name, x1, z1, x2, z2, y0, h=1.0, material=None, glass=False, room="hall", posts=3):
    """handrail on posts (or a glass balustrade) between two points at floor height y0"""
    material = material or M["railing"]
    dx, dz = x2 - x1, z2 - z1
    length, rot = math.hypot(dx, dz), math.atan2(dz, dx)
    cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
    box(f"{name}_cap", (cx, y0 + h, cz), (length, 0.04, 0.05), material, bevel=0.004, rot_z=rot, part="furniture", room=room)
    if glass:
        box(f"{name}_glass", (cx, y0 + h / 2 + 0.05, cz), (length - 0.02, h - 0.1, 0.012), M["glass"], "Glass", bevel=0, rot_z=rot,
            part="glass", side="I", room=room)
    for i in range(posts):
        t = (i + 0.5) / posts if posts > 1 else 0.5
        box(f"{name}_p{i}", (x1 + dx * t, y0 + h / 2, z1 + dz * t), (0.03, h, 0.03), material, bevel=0, rot_z=rot, part="furniture", room=room)


def column(name, x, z, y0, h, r=0.16, material=None, room="porch"):
    material = material or M["plaster"]
    cyl(f"{name}_shaft", (x, y0 + h / 2, z), r, h, material, "Structure", verts=24, part="slab", room=room)
    box(f"{name}_cap", (x, y0 + h - 0.06, z), (r * 2.6, 0.12, r * 2.6), material, "Structure", bevel=0.01, part="slab", room=room)
    box(f"{name}_base", (x, y0 + 0.06, z), (r * 2.6, 0.12, r * 2.6), material, "Structure", bevel=0.01, part="slab", room=room)


# ----------------------------------------------------------------------------- loft pieces
def led_strip(name, x1, z1, x2, z2, y, room="living", m=None):
    """thin emissive strip between two points at height y"""
    dx, dz = x2 - x1, z2 - z1
    length, rot = math.hypot(dx, dz), math.atan2(dz, dx)
    box(name, ((x1 + x2) / 2, y, (z1 + z2) / 2), (length, 0.018, 0.03), m or M["led"], "Furniture", bevel=0, rot_z=rot, part="light", room=room)


def led_cove(name, rect, room="living", y=None, inset=0.09):
    """LED strip around a room's ceiling perimeter, like the coves in the reference photo"""
    x1, z1, x2, z2 = rect
    y = y or H - 0.06
    a, b, c, d = x1 + inset, z1 + inset, x2 - inset, z2 - inset
    led_strip(f"{name}_n", a, b, c, b, y, room); led_strip(f"{name}_s", a, d, c, d, y, room)
    led_strip(f"{name}_w", a, b, a, d, y, room); led_strip(f"{name}_e", c, b, c, d, y, room)


def gaming_chair(name, x, z, rot, room="living"):
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0)
    soft(f"{name}_seat", (px, 0.48, pz), (0.52, 0.1, 0.52), M["black"], r=0.04, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, -0.26)
    soft(f"{name}_back", (px, 0.95, pz), (0.5, 0.86, 0.12), M["black"], r=0.05, rot_z=rot, rot_x=-0.15, part="furniture", room=room)
    px, pz = P(0, -0.3)
    soft(f"{name}_head", (px, 1.3, pz), (0.3, 0.16, 0.09), M["chair_red"], r=0.03, rot_z=rot, rot_x=-0.15, part="furniture", room=room)
    for i, dx in enumerate([-0.24, 0.24]):
        px, pz = P(dx, -0.2)
        soft(f"{name}_wing{i}", (px, 0.72, pz), (0.06, 0.35, 0.16), M["chair_red"], r=0.02, rot_z=rot, part="furniture", room=room)
        px, pz = P(dx * 1.2, -0.05)
        box(f"{name}_arm{i}", (px, 0.68, pz), (0.05, 0.03, 0.3), M["black"], bevel=0.005, rot_z=rot, part="furniture", room=room)
    cx0, cz0 = P(0, 0)
    cyl(f"{name}_post", (cx0, 0.28, cz0), 0.025, 0.36, M["steel"], verts=10, part="furniture", room=room)
    for i in range(5):
        a = i * math.pi * 2 / 5 + rot
        box(f"{name}_spoke{i}", (x + math.cos(a) * 0.16, 0.04, z + math.sin(a) * 0.16), (0.32, 0.03, 0.035), M["black"], bevel=0.005,
            rot_z=-a, part="furniture", room=room)
        sphere(f"{name}_caster{i}", (x + math.cos(a) * 0.3, 0.03, z + math.sin(a) * 0.3), 0.03, M["frame"], sub=1, part="furniture", room=room)


def gaming_desk(name, x, z, rot, room="living", w=1.6):
    """black desk facing -dz: curved monitor on a stand, keyboard, mouse, PC tower with a lit side panel, gaming chair"""
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0)
    box(f"{name}_top", (px, 0.74, pz), (w, 0.03, 0.7), M["black"], bevel=0.006, rot_z=rot, part="furniture", room=room)
    for i, dx in enumerate([-w / 2 + 0.06, w / 2 - 0.06]):
        px, pz = P(dx, 0)
        box(f"{name}_leg{i}", (px, 0.36, pz), (0.04, 0.72, 0.6), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, -0.24)
    box(f"{name}_led", (px, 0.73, pz), (w - 0.1, 0.012, 0.02), M["led"], bevel=0, rot_z=rot, part="light", room=room)   # edge glow at the back
    px, pz = P(-0.05, -0.22)
    box(f"{name}_monitor", (px, 1.1, pz), (0.85, 0.38, 0.03), M["screen"], bevel=0.004, rot_z=rot, part="furniture", room=room)
    box(f"{name}_panel", (px - s * 0.018, 1.1, pz + c * 0.018), (0.8, 0.34, 0.004), M["monitor_glow"], bevel=0, rot_z=rot, part="light", room=room)
    box(f"{name}_stand", (px, 0.84, pz), (0.04, 0.18, 0.04), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)
    box(f"{name}_foot", (px, 0.76, pz), (0.3, 0.012, 0.16), M["frame"], bevel=0.003, rot_z=rot, part="furniture", room=room)
    px, pz = P(-0.05, 0.08)
    box(f"{name}_keyboard", (px, 0.765, pz), (0.42, 0.012, 0.14), M["black"], bevel=0.003, rot_z=rot, part="furniture", room=room)
    box(f"{name}_keys", (px, 0.772, pz), (0.38, 0.004, 0.1), M["neon"], bevel=0, rot_z=rot, part="light", room=room)
    px, pz = P(0.28, 0.08)
    soft(f"{name}_mouse", (px, 0.775, pz), (0.06, 0.03, 0.1), M["black"], r=0.012, rot_z=rot, part="furniture", room=room)
    px, pz = P(w / 2 + 0.16, 0.05)
    box(f"{name}_pc", (px, 0.24, pz), (0.22, 0.46, 0.45), M["black"], bevel=0.006, rot_z=rot, part="furniture", room=room)
    box(f"{name}_pcglow", (px - c * 0.115, 0.24, pz - s * 0.115), (0.004, 0.36, 0.36), M["led_soft"], bevel=0, rot_z=rot, part="light", room=room)
    px, pz = P(0, 0.62)
    gaming_chair(f"{name}_chair", px, pz, rot + math.pi, room=room)


def display_cabinet(name, x, z, rot, room="living", w=0.8, h=1.9):
    """black-framed glass cabinet with lit shelves of bottles"""
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0)
    box(f"{name}_base", (px, 0.04, pz), (w, 0.08, 0.4), M["black"], bevel=0.004, rot_z=rot, part="furniture", room=room)
    box(f"{name}_top", (px, h - 0.02, pz), (w, 0.04, 0.4), M["black"], bevel=0.004, rot_z=rot, part="furniture", room=room)
    box(f"{name}_topled", (px, h - 0.045, pz), (w - 0.06, 0.01, 0.34), M["led_soft"], bevel=0, rot_z=rot, part="light", room=room)
    for i, (dx, dz) in enumerate([(-w / 2 + 0.015, -0.185), (w / 2 - 0.015, -0.185), (-w / 2 + 0.015, 0.185), (w / 2 - 0.015, 0.185)]):
        px, pz = P(dx, dz)
        box(f"{name}_post{i}", (px, h / 2, pz), (0.03, h, 0.03), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, 0)
    box(f"{name}_glass", (px, h / 2, pz), (w - 0.03, h - 0.12, 0.37), M["glass"], "Glass", bevel=0, rot_z=rot, part="glass", side="I", room=room)
    n = 4
    for k in range(n):
        y = 0.08 + (h - 0.14) * (k + 1) / (n + 1)
        px, pz = P(0, 0)
        box(f"{name}_shelf{k}", (px, y, pz), (w - 0.05, 0.015, 0.36), M["glass"], "Glass", bevel=0, rot_z=rot, part="glass", side="I", room=room)
        for j in range(5):
            dx = -w / 2 + 0.1 + j * (w - 0.2) / 4
            bx, bz = P(dx, (rnd() - 0.5) * 0.16)
            cyl(f"{name}_b{k}{j}", (bx, y + 0.13, bz), 0.03, 0.24, M["bottle"] if (j + k) % 2 else M["bottle2"], verts=10, part="furniture", room=room)


def vanity(name, x, z, rot, room="bedroom"):
    """white dressing table with drawers, a round mirror ringed with bulbs, a stool and a row of bottles"""
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0)
    box(f"{name}_top", (px, 0.75, pz), (1.1, 0.03, 0.45), M["white_gloss"], bevel=0.004, rot_z=rot, part="furniture", room=room)
    px, pz = P(0.35, 0)
    box(f"{name}_drawers", (px, 0.37, pz), (0.38, 0.72, 0.42), M["white_gloss"], bevel=0.004, rot_z=rot, part="furniture", room=room)
    for i, y in enumerate([0.2, 0.44, 0.66]):
        px, pz = P(0.35, 0.212)
        box(f"{name}_pull{i}", (px, y, pz), (0.12, 0.01, 0.01), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)
    for dx in (-0.53,):
        px, pz = P(dx, 0)
        box(f"{name}_leg", (px, 0.37, pz), (0.03, 0.72, 0.4), M["white_gloss"], bevel=0, rot_z=rot, part="furniture", room=room)
    px, pz = P(-0.1, -0.21)
    cyl(f"{name}_mirror", (px, 1.35, pz), 0.3, 0.012, M["steel"], rot=(math.radians(90), 0, -rot), part="furniture", room=room)
    for i in range(12):
        a = i * math.pi * 2 / 12
        bx, bz = P(-0.1 + math.cos(a) * 0.31, -0.2)
        sphere(f"{name}_bulb{i}", (bx, 1.35 + math.sin(a) * 0.31, bz), 0.018, M["downlight"], sub=1, part="light", room=room)
    for j in range(8):
        bx, bz = P(-0.45 + j * 0.09, -0.12 + (rnd() - 0.5) * 0.1)
        cyl(f"{name}_pot{j}", (bx, 0.815, bz), 0.015, 0.1, M["neon"] if j % 3 == 0 else M["white_gloss"], verts=8, part="furniture", room=room)
    px, pz = P(-0.1, 0.45)
    cyl(f"{name}_stool", (px, 0.42, pz), 0.17, 0.06, M["charcoal"], bevel=0.015, part="furniture", room=room)
    cyl(f"{name}_stoolpost", (px, 0.2, pz), 0.02, 0.38, M["frame"], verts=10, part="furniture", room=room)
    cyl(f"{name}_stoolbase", (px, 0.012, pz), 0.14, 0.024, M["frame"], part="furniture", room=room)


def glass_wardrobe(name, x, z, rot, w=1.9, room="bedroom"):
    """wardrobe with a black frame, glass doors, an LED strip and a rail of hanging clothes"""
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0.3)
    box(f"{name}_body", (px, 1.15, pz), (w, 2.3, 0.02), M["black"], bevel=0.004, rot_z=rot, part="furniture", room=room)   # back panel
    for i, dz in enumerate([-0.29, 0.29]):
        pass
    for i, dx in enumerate([-w / 2 + 0.01, w / 2 - 0.01]):
        px, pz = P(dx, 0)
        box(f"{name}_side{i}", (px, 1.15, pz), (0.02, 2.3, 0.6), M["black"], bevel=0.004, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, 0)
    box(f"{name}_top", (px, 2.29, pz), (w, 0.02, 0.6), M["black"], bevel=0, rot_z=rot, part="furniture", room=room)
    box(f"{name}_bottom", (px, 0.01, pz), (w, 0.02, 0.6), M["black"], bevel=0, rot_z=rot, part="furniture", room=room)
    box(f"{name}_led", (px, 2.26, pz), (w - 0.06, 0.012, 0.03), M["led_soft"], bevel=0, rot_z=rot, part="light", room=room)
    px, pz = P(0, -0.29)
    box(f"{name}_doors", (px, 1.15, pz), (w - 0.04, 2.24, 0.012), M["glass"], "Glass", bevel=0, rot_z=rot, part="glass", side="I", room=room)
    px, pz = P(0, 0)
    cyl(f"{name}_rail", (px, 1.85, pz), 0.012, w - 0.08, M["steel"], verts=8, rot=(0, math.radians(90), -rot), part="furniture", room=room)
    n = int((w - 0.2) / 0.13)
    for j in range(n):
        dx = -w / 2 + 0.14 + j * 0.13
        px, pz = P(dx, (rnd() - 0.5) * 0.05)
        mtr = (M["cloth_a"], M["cloth_b"], M["cloth_c"], M["charcoal"])[j % 4]
        box(f"{name}_cloth{j}", (px, 1.35, pz), (0.09, 0.9 + rnd() * 0.3, 0.3), mtr, bevel=0.01, rot_z=rot, part="furniture", room=room)


def sectional(name, x, z, rot, w=2.6, room="living"):
    """dark grey sectional with a chaise on the right, plush cushions like the reference"""
    fabric = M["charcoal"]
    sofa(name, x, z, rot, w=w, fabric=fabric, room=room)
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(w / 2 - 0.45, 0.85)
    soft(f"{name}_chaise", (px, 0.2, pz), (0.9, 0.22, 0.75), fabric, r=0.03, rot_z=rot, part="furniture", room=room)
    soft(f"{name}_chaiseseat", (px, 0.38, pz), (0.85, 0.14, 0.7), fabric, r=0.06, rot_z=rot, part="furniture", room=room)
    for i, (dx, m) in enumerate([(-w / 2 + 0.35, M["plush_blue"]), (-w / 2 + 0.75, M["plush_orange"]), (w / 2 - 0.4, M["plush_white"]), (0.05, M["plush_yellow"])]):
        px, pz = P(dx, -0.15)
        soft(f"{name}_plush{i}", (px, 0.62, pz), (0.36, 0.34, 0.14), m, r=0.06, rot_z=rot, rot_x=-0.3, part="furniture", room=room)
    px, pz = P(-w / 2 + 0.55, 0.15)
    soft(f"{name}_throw", (px, 0.47, pz), (0.8, 0.05, 0.7), M["leather_tan"], r=0.02, rot_z=rot, part="furniture", room=room)


def tv_wall(name, x, z, rot, room="living", w=1.8, shelf_dx=-1.2, shoes=True):
    """walnut media console, big TV, shelves of bottles and a row of framed photos above"""
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0.22)
    box(f"{name}_console", (px, 0.25, pz), (w, 0.5, 0.42), M["walnut"], bevel=0.008, rot_z=rot, part="furniture", room=room)
    box(f"{name}_gap", (px - s * 0.211, 0.25, pz + c * 0.211), (w - 0.06, 0.006, 0.004), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, 0.03)
    box(f"{name}_tv", (px, 1.25, pz), (1.5, 0.85, 0.035), M["screen"], bevel=0.004, rot_z=rot, part="furniture", room=room)
    box(f"{name}_panel", (px - s * 0.02, 1.25, pz + c * 0.02), (1.44, 0.79, 0.004), M["tv"], bevel=0, rot_z=rot, part="light", room=room)
    for i, dx in enumerate([shelf_dx] * 3):
        px, pz = P(dx, 0.1)
        box(f"{name}_shelf{i}", (px, 1.15 + i * 0.35, pz), (0.5, 0.02, 0.18), M["walnut"], bevel=0.003, rot_z=rot, part="furniture", room=room)
        for j in range(4):
            bx, bz = P(dx - 0.18 + j * 0.12, 0.1)
            cyl(f"{name}_bt{i}{j}", (bx, 1.24 + i * 0.35, bz), 0.02, 0.16, M["bottle"] if j % 2 else M["white_gloss"], verts=8, part="furniture", room=room)
    for i in range(4):
        px, pz = P(-0.55 + i * 0.4, 0.02)
        wall_art(f"{name}_photo{i}", px, 2.05, pz, 0.28, 0.24, rot, M["art2"], room=room, depth=0.02)
    if not shoes:
        return
    px, pz = P(w / 2 + 0.35, 0.22)
    box(f"{name}_shoerack", (px, 0.4, pz), (0.45, 0.8, 0.32), M["white_gloss"], bevel=0.005, rot_z=rot, part="furniture", room=room)
    for i in range(3):
        box(f"{name}_shoe{i}", (px - s * 0.14, 0.15 + i * 0.25, pz + c * 0.14), (0.38, 0.015, 0.05), M["frame"], bevel=0, rot_z=rot, part="furniture", room=room)


def loft_coffee_table(name, x, z, room="living"):
    box(f"{name}_top", (x, 0.42, z), (1.0, 0.03, 0.6), M["white_gloss"], bevel=0.005, part="furniture", room=room)
    soft(f"{name}_cloth", (x, 0.44, z), (0.96, 0.012, 0.56), M["plush_white"], r=0.005, part="furniture", room=room)
    for i, (dx, dz) in enumerate([(-0.45, -0.25), (0.45, -0.25), (-0.45, 0.25), (0.45, 0.25)]):
        box(f"{name}_leg{i}", (x + dx, 0.2, z + dz), (0.03, 0.4, 0.03), M["walnut"], bevel=0, part="furniture", room=room)
    cyl(f"{name}_vase", (x, 0.52, z - 0.1), 0.04, 0.16, M["glass"], "Glass", bevel=0, part="glass", side="I", room=room)
    for i in range(5):
        sphere(f"{name}_flower{i}", (x + (rnd() - 0.5) * 0.14, 0.66 + rnd() * 0.05, z - 0.1 + (rnd() - 0.5) * 0.14), 0.03,
               (M["plush_orange"], M["chair_red"], M["plush_yellow"])[i % 3], sub=1, part="furniture", room=room)
    for i, (dx, dz) in enumerate([(-0.25, 0.1), (0.05, 0.15), (0.3, 0.05)]):
        cyl(f"{name}_plate{i}", (x + dx, 0.455, z + dz), 0.09, 0.012, M["white_gloss"], part="furniture", room=room)


# ----------------------------------------------------------------------------- 2D plan export (minimap + walk collision)
def write_plan(path, levels):
    """writes site/<apt>/plan.js from the same wall lists the model is built from, one entry per level:
    dict(walls=<build_walls input>, rooms=[(key, (x1,z1,x2,z2), fill, label)], bounds=(x0,z0,x1,z1), extra=[(x1,z1,x2,z2,kind)])"""
    import json
    out = ["// Generated by the build script from its wall lists — do not edit by hand (x east, z south, metres).",
           f"export const T = {T}", "export const levels = ["]
    for lv in levels:
        segs = {}
        for x1, z1, x2, z2, side, o in lv["walls"]:
            key = (round(x1, 3), round(z1, 3), round(x2, 3), round(z2, 3))
            segs.setdefault(key, []).append(o)
        lines = []
        for (x1, z1, x2, z2), opts in segs.items():
            if any(o.get("glass") for o in opts):
                kind = "glass"
            elif all(o.get("y0", 0) > 0 for o in opts):
                kind = "head"
            else:
                kind = "wall"
            lines.append(f"[{x1:g}, {z1:g}, {x2:g}, {z2:g}, '{kind}']")
        for x1, z1, x2, z2, kind in lv.get("extra", []):
            lines.append(f"[{x1:g}, {z1:g}, {x2:g}, {z2:g}, '{kind}']")
        rooms = ", ".join(f"{{ key: '{k}', rect: [{r[0]:g}, {r[1]:g}, {r[2]:g}, {r[3]:g}], fill: '{f}', label: {json.dumps(l)} }}" for k, r, f, l in lv["rooms"])
        x0, z0, x1, z1 = lv["bounds"]
        out.append("  { walls: [" + ", ".join(lines) + "],")
        out.append("    rooms: [" + rooms + "],")
        out.append(f"    BOUNDS: {{ x0: {x0:g}, x1: {x1:g}, z0: {z0:g}, z1: {z1:g} }} }},")
    out.append("]")
    out.append("for (const l of levels) { l.T = T; l.roomAt = (x, z) => { for (const r of l.rooms) { const [a, b, c, d] = r.rect; if (x >= a && x <= c && z >= b && z <= d) return r } return null } }")
    out.append("export const walls = levels[0].walls, rooms = levels[0].rooms, BOUNDS = levels[0].BOUNDS, roomAt = levels[0].roomAt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    print("wrote", path)


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
