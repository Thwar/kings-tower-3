"""
Bakes Cycles lighting into lightmaps and exports the baked model.

    python3 blender/bake_lightmaps.py [--apt=duna] [--fast] [--only=Floor_living,Walls_N]

    --apt selects the apartment: build_<apt>.py and site/<apt>/ (default: build_apartment.py → site/).

What it does
1. Runs build_<apt>.py to build the scene.
2. Joins objects into groups: one per (cutaway group, material). Cutaway groups keep walls per side and the
   ceiling separate so the viewer can still hide them; everything else is "static".
3. Gives every group its own material copy and a second UV map ("Lightmap", exported as TEXCOORD_1),
   unwrapped with a lightmap pack so texels never overlap.
4. Sets up the lighting: sun through the openings, sky, and the apartment's own lamps as emitters.
5. Bakes COMBINED lighting (direct + indirect, diffuse only, no albedo) per group into
   site/lightmaps/<group>.jpg and records the file name in the object's `lightmap` custom property.
6. Exports site/apartment.glb with the lightmap UVs.

The viewer multiplies albedo × lightmap and adds a weak environment for reflections: no real-time lights,
no shadow map, which is what makes it look photographic *and* run fast.
"""
import math
import os
import runpy
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
APT = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--apt=")), "apartment")
SITE = os.path.join(HERE, "..", "site") if APT == "apartment" else os.path.join(HERE, "..", "site", APT)
LM_DIR = os.path.join(SITE, "lightmaps")
FAST = "--fast" in sys.argv
only = [a for a in sys.argv if a.startswith("--only=")]
only = only[0].split("=")[1].split(",") if only else None

t_start = time.time()
os.environ["KT_SKIP_EXPORT"] = "1"   # the build must not overwrite the baked GLB
G = runpy.run_path(os.path.join(HERE, f"build_{APT}.py"))   # the build module's globals: LIGHTS, SUN_ROT
scene = bpy.context.scene
P = lambda x, y, z: Vector((x, -z, y))

# ----------------------------------------------------------------------------- group objects
def group_key(o):
    part, side = o.get("part"), o.get("side")
    mat = o.data.materials[0].name if o.data.materials else "none"
    if part == "ceiling":
        return "Ceiling", mat
    if part in ("wall", "frame", "glass") and side and side != "I":
        return f"Walls_{side}", mat
    if part in ("wall", "frame", "glass"):
        return "Walls_I", mat
    return "Static", mat


groups = {}
footprints = []
for o in list(bpy.data.objects):
    if o.type != "MESH":
        continue
    if o.get("part") in ("furniture", "light"):
        xs = [(o.matrix_world @ Vector(c)) for c in o.bound_box]
        x0, x1 = min(v.x for v in xs), max(v.x for v in xs)
        y0, y1 = min(v.y for v in xs), max(v.y for v in xs)
        z0 = min(v.z for v in xs)
        if (x1 - x0) * (y1 - y0) > 0.05 and z0 < 1.2:
            footprints.append([round(x0, 3), round(-y1, 3), round(x1 - x0, 3), round(y1 - y0, 3)])   # plan space: x, z, w, d
    groups.setdefault(group_key(o), []).append(o)
import json
os.makedirs(SITE, exist_ok=True)
with open(os.path.join(SITE, "footprints.json"), "w") as f:
    json.dump(footprints, f)

merged = []
for (grp, matname), objs in groups.items():
    # apply modifiers (bevels) before joining so the bake sees the final shape
    for o in objs:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    name = f"{grp}__{matname}"
    ob.name = name
    ob.data.name = name
    # keep the viewer's tags on the group
    for k in list(ob.keys()):
        if k not in ("part", "side", "room"):
            del ob[k]
    ob["part"] = "ceiling" if grp == "Ceiling" else "wall" if grp.startswith("Walls") else "static"
    ob["side"] = grp.split("_")[1] if grp.startswith("Walls_") else "I"
    ob["room"] = ""
    # own material copy so each group can carry its own lightmap in the viewer
    m = ob.data.materials[0].copy()
    m.name = f"{matname}__{grp}"
    ob.data.materials.clear()
    ob.data.materials.append(m)
    merged.append(ob)
print(f"grouped {len(merged)} objects in {time.time() - t_start:.0f}s")

# ----------------------------------------------------------------------------- lightmap UVs
def surface_area(ob):
    return sum(p.area for p in ob.data.polygons)


def lightmap_size(ob):
    a = surface_area(ob)
    # ~ texel density target: 64 texels per metre → size from area, clamped, power of two
    px = math.sqrt(a) * (96 if FAST else 200)
    size = 2 ** round(math.log2(max(128, min(2048, px))))
    return int(size)


for ob in merged:
    uv = ob.data.uv_layers.new(name="Lightmap")
    ob.data.uv_layers.active = uv
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02, correct_aspect=True, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.data.uv_layers.active = ob.data.uv_layers[0]      # rendering/export still uses the texture UVs first

# ----------------------------------------------------------------------------- lighting
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.93, 0.92, 0.89, 1)   # bright neutral sky: walls read white, not blue-grey
bg.inputs[1].default_value = 2.6

sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 2.0
sun_data.angle = math.radians(3)
sun_data.color = (1.0, 0.95, 0.88)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = tuple(math.radians(a) for a in G["SUN_ROT"])   # per apartment: low afternoon sun through the main openings

# interior lights: warm point lights at the lamps and downlights
def point(name, pos, energy, color=(1.0, 0.85, 0.65), radius=0.08):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = energy; d.color = color; d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = P(*pos)


for name, pos, energy, *rest in G["LIGHTS"]:   # the apartment's own lamps, listed by its build script
    point(name, pos, energy, *rest)

# emissive materials glow a little in the bake too (they're already emissive in the model)

# ----------------------------------------------------------------------------- bake
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24 if FAST else 96
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.bake.use_pass_direct = True
scene.render.bake.use_pass_indirect = True
scene.render.bake.use_pass_color = False          # lighting only; albedo comes from the textures in the viewer
scene.render.bake.margin = 8
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 92
scene.view_settings.view_transform = "Standard"   # write the bake values straight (sRGB-encoded 8-bit)
scene.view_settings.look = "None"
scene.view_settings.exposure = -1.0               # halve on save so sunlit patches survive 8-bit; the viewer doubles it back
os.makedirs(LM_DIR, exist_ok=True)

ceilings = [o for o in merged if o.name.startswith("Ceiling")]
for ob in sorted(merged, key=lambda o: o.name.startswith("Ceiling")):   # ceiling groups last
    if only and not any(ob.name.startswith(k) for k in only):
        continue
    # everything but the ceiling itself is baked with the ceiling removed: the sky floods the cutaway,
    # which is how the viewer presents the apartment (soft, even, bright)
    for c in ceilings:
        c.hide_render = not ob.name.startswith("Ceiling")
    size = lightmap_size(ob)
    img = bpy.data.images.new(f"LM_{ob.name}", size, size, alpha=False, float_buffer=True)
    m = ob.data.materials[0]
    nt = m.node_tree
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = img
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "Lightmap"
    nt.links.new(uvn.outputs[0], node.inputs[0])
    nt.nodes.active = node
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    t0 = time.time()
    # DIFFUSE without COLOR = lighting only (albedo stays in the material textures)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, uv_layer="Lightmap", margin=8)
    # compress the lighting range a little (floor vs wall) so the apartment reads evenly lit, like a photo with fill
    px = np.empty(size * size * 4, np.float32)
    img.pixels.foreach_get(px)
    rgb = px.reshape(-1, 4)[:, :3]
    rgb[:] = np.power(np.clip(rgb, 0, None), 0.65) * 1.05
    img.pixels.foreach_set(px)
    fname = f"{ob.name}.jpg".replace("__", "-")
    img.filepath_raw = os.path.join(LM_DIR, fname)
    img.file_format = "JPEG"
    img.save()
    nt.nodes.remove(node); nt.nodes.remove(uvn)
    bpy.data.images.remove(img)
    ob["lightmap"] = fname
    print(f"baked {ob.name} {size}px in {time.time() - t0:.0f}s")

# ----------------------------------------------------------------------------- export
bpy.ops.object.select_all(action="SELECT")
out = os.path.join(SITE, "apartment.glb")
bpy.ops.export_scene.gltf(
    filepath=out, export_format="GLB", export_apply=True, export_extras=True, export_yup=True,
    export_lights=False, export_cameras=False, export_animations=False, export_materials="EXPORT",
    export_normals=True, export_image_format="AUTO", export_jpeg_quality=82, use_selection=False,
)
print("exported", out, os.path.getsize(out) // 1024, "KB", "groups:", len(merged), "total %.0fs" % (time.time() - t_start))
