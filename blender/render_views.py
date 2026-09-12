"""
Renders the apartment with Cycles (CPU) into site/renders/*.jpg — the "Blender renders" tab.

    python3 blender/render_views.py [--fast]      (--fast: 16 samples, 720px, for previews)

Builds the scene by running build_apartment.py first, then hides the ceiling and the two walls
facing the camera (the same cutaway the web viewer does) and renders each viewpoint.
"""
import math
import os
import runpy
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "renders")
FAST = "--fast" in sys.argv

os.environ["KT_SKIP_EXPORT"] = "1"   # the build must not overwrite the baked GLB
runpy.run_path(os.path.join(HERE, "build_apartment.py"))
scene = bpy.context.scene

# plan (x, y_up, z_south) → Blender (x, -z, y)
P = lambda x, y, z: Vector((x, -z, y))

VIEWS = [
    # key, camera position (plan), look-at (plan), fov, hide sides
    ("whole",   (-7.5, 11.5, 16.5), (6.2, 0.5, 3.0), 30, "SW"),
    ("living",  (-6.0, 5.0, 5.0),  (2.8, 0.6, 2.2), 40, "SW"),
    ("kitchen", (9.0, 6.0, -5.5),  (5.3, 0.7, 1.7), 40, "N"),
    ("bedroom", (6.2, 9.5, 11.0),  (5.5, 0.3, 4.4), 40, "S"),
    ("bath",    (-3.5, 4.0, 9.0),  (1.0, 0.8, 5.0), 42, "SW"),
    ("terrace", (17.0, 5.0, -2.5), (10.3, 0.8, 3.0), 42, "NE"),
    ("service", (2.6, 5.0, 12.0),  (2.55, 0.6, 5.3), 40, "S"),
]

# ---------------------------------------------------------------- world + light
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.36, 0.40, 0.45, 1)   # slate, like the viewer background
bg.inputs[1].default_value = 1.0

sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.5
sun_data.angle = math.radians(6)
sun_data.color = (1.0, 0.96, 0.9)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(35))

fill_data = bpy.data.lights.new("Fill", "AREA")
fill_data.energy = 900
fill_data.size = 12
fill = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill)
fill.location = P(2.0, 9.0, 8.0)
fill.rotation_euler = (math.radians(35), 0, math.radians(-20))

# ---------------------------------------------------------------- render settings
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16 if FAST else 64
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.resolution_x = 1280 if FAST else 1600
scene.render.resolution_y = 800 if FAST else 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 88
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
scene.view_settings.exposure = 0.35

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

os.makedirs(OUT, exist_ok=True)
objs = [o for o in bpy.data.objects if o.type == "MESH"]
only = [a for a in sys.argv if a.startswith("--only=")]
only = only[0].split("=")[1].split(",") if only else None

for key, pos, target, fov, hide in VIEWS:
    if only and key not in only:
        continue
    cam.location = P(*pos)
    direction = P(*target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam_data.angle = math.radians(fov)
    for o in objs:
        side = o.get("side")
        part = o.get("part")
        o.hide_render = part == "ceiling" or (side in hide if side else False)
    scene.render.filepath = os.path.join(OUT, f"{key}.jpg")
    bpy.ops.render.render(write_still=True)
    print("rendered", key)
