"""
Torre Duna · Dept. Tipo E — builds the apartment in Blender and exports site/duna/apartment.glb.

Run headless:   python3 blender/build_duna.py [--blend]      (needs `pip install bpy`)

Layout traced from the developer's plan (north up): bathroom NW, a small service room (P.S.) beside it,
the entrance top-centre into a vestibule, the kitchen NE with an island and three stools, the living SE,
the bedroom SW and the terrace below it. The brochure gives no room dimensions, only the total
(49.61 m² per Thomas; the printed plan says 48.21), so every room is scaled proportionally from the drawing.

Same interior concept as Dept. D: minimal bachelor pad — off-white plaster, oak floor, matte black and
walnut, charcoal linen and black leather, one statement piece per room.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ktlib import (H, T, M, X, box, soft, cyl, floor_plane, build_walls, downlights,  # noqa: E402
                   plant, grass, sofa, lounge_chair, stool, office_chair, floor_lamp, wall_art, export)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "duna", "apartment.glb")
APT = dict(name="Torre Duna · Tipo E", site="site/duna")

# ----------------------------------------------------------------------------- plan (metres; x east, z south, origin NW corner)
W, D, TD = 7.3, 5.4, 6.95           # apartment width, depth of the enclosed part, depth including the terrace
walls = [
    # exterior
    (0, 0, 3.3, 0, "N", dict(ext=(True, False))), (4.2, 0, W, 0, "N", dict(ext=(False, True))),     # entry door x 3.3–4.2
    (3.3, 0, 4.2, 0, "N", dict(y0=2.1, y1=H, noskirt=True)),
    (0, 0, 0, 0.4, "W", dict(ext=(True, False))), (0, 1.2, 0, TD, "W", dict(ext=(False, True))),   # bath window x=0, z 0.4–1.2
    (0, 0.4, 0, 1.2, "W", dict(y0=0, y1=1.6)), (0, 0.4, 0, 1.2, "W", dict(y0=2.25, y1=H, noskirt=True)),
    (0, 0.4, 0, 1.2, "W", dict(y0=1.6, y1=2.25, glass=True)),
    (W, 0, W, D, "E", dict(**X)),
    (3.6, D, 3.6, TD, "E", dict(**X)),                                                              # terrace east wall
    (3.35, D, 4.6, D, "S", {}), (6.6, D, W, D, "S", dict(ext=(False, True))),                    # living window x 4.6–6.6
    (4.6, D, 6.6, D, "S", dict(y0=0, y1=0.9)), (4.6, D, 6.6, D, "S", dict(y0=2.25, y1=H, noskirt=True)),
    (4.6, D, 6.6, D, "S", dict(y0=0.9, y1=2.25, glass=True)),
    (0, D, 2.3, D, "S", dict(ext=(True, False))),                                                  # bedroom slider x 2.3–3.35
    (2.3, D, 3.35, D, "S", dict(y0=2.25, y1=H, noskirt=True)),
    (0, TD, 3.6, TD, "S", dict(y0=0.12, y1=1.1, glass=True)),                                      # terrace railing
    # interior
    (1.9, 0, 1.9, 1.55, "I", dict(ext=(True, False))), (1.9, 2.05, 1.9, 2.2, "I", dict(ext=(False, True))),  # bath east wall, door z 1.55–2.05

    (2.9, 0, 2.9, 0.4, "I", dict(ext=(True, False))), (2.9, 1.2, 2.9, 1.5, "I", dict(ext=(False, True))),  # P.S. east wall, door z 0.4–1.2
    (1.9, 1.5, 2.9, 1.5, "I", dict(**X)),                                                                     # P.S. south wall
    (0, 2.2, 2.6, 2.2, "I", dict(**X)), (3.45, 2.2, 3.6, 2.2, "I", dict(ext=(False, True))),                  # bath south + bedroom north wall, door x 2.6–3.45
    (3.6, 2.2, 3.6, D, "I", dict(**X)),                                                                       # bedroom / living partition
]
frames = [
    (0, 0.4, 0, 1.2, 1.6, 2.25, "W"),
    (4.6, D, 6.6, D, 0.9, 2.25, "S"),
    (2.3, D, 3.35, D, 0, 2.25, "S"),
]
DOWNLIGHTS = [(0.95, 1.1), (2.4, 0.75), (3.75, 0.8), (3.75, 2.0), (5.3, 1.3), (6.6, 1.3), (4.6, 4.3), (6.3, 4.3), (1.2, 4.0), (2.9, 3.6)]

# ----------------------------------------------------------------------------- structure
build_walls(walls, frames)
floor_plane("Floor_main", (3.6, 0, W, D), M["wood"], room="living")
floor_plane("Floor_hall", (2.9, 0, 3.6, 1.5), M["wood"], room="living")
floor_plane("Floor_vest", (1.9, 1.5, 3.6, 2.2), M["wood"], room="living")
floor_plane("Floor_bedroom", (0, 2.2, 3.6, D), M["wood"], room="bedroom")
floor_plane("Floor_bath", (0, 0, 1.9, 2.2), M["tile"], room="bath")
floor_plane("Floor_ps", (1.9, 0, 2.9, 1.5), M["tile"], room="service")
floor_plane("Floor_terrace", (0, D, 3.6, TD), M["stone"], room="terrace")
box("Slab", (W / 2, -0.17, TD / 2), (W + 0.8, 0.3, TD + 0.8), M["concrete"], "Structure", bevel=0.02, part="slab")

box("Ceiling", (W / 2, H + 0.05, D / 2), (W + T, 0.1, D + T), M["ceiling"], "Ceiling", bevel=0, part="ceiling")
downlights(DOWNLIGHTS)

# terrace curb + railing
box("Curb", (1.8, 0.06, TD), (3.6, 0.12, T), M["concrete"], "Structure", part="slab", room="terrace")
box("RailCap", (1.8, 1.12, TD), (3.6, 0.04, 0.05), M["railing"], "Structure", part="slab", room="terrace")
for i, x in enumerate([0.1, 1.0, 1.9, 2.8, 3.5]):
    box(f"RailPost_{i}", (x, 0.6, TD), (0.03, 1.0, 0.03), M["railing"], "Structure", bevel=0, part="slab", room="terrace")

# doors: sliding leaf stacked open, hinged doors open flat against the wall
box("SlideLeaf", (2.5, 1.12, D + 0.06), (0.55, 2.2, 0.03), M["glass"], "Glass", bevel=0, part="glass", side="I")
box("Door_entry", (3.75, 1.05, 0.08), (0.9, 2.1, 0.05), M["black"], "Furniture", part="furniture", room="living")
box("Door_handle", (4.08, 1.02, 0.13), (0.02, 0.3, 0.02), M["frame"], "Furniture", bevel=0.005, part="furniture", room="living")
box("Door_bath", (1.83, 1.05, 1.15), (0.04, 2.1, 0.5), M["walnut"], "Furniture", part="furniture", room="bath")        # open into the bath
box("Door_ps", (2.97, 1.05, 0.8), (0.04, 2.1, 0.8), M["walnut"], "Furniture", part="furniture", room="service")      # open flat in the hall
box("Door_bedroom", (2.67, 1.05, 2.6), (0.04, 2.1, 0.8), M["walnut"], "Furniture", part="furniture", room="bedroom")  # open into the bedroom

F = dict(part="furniture")

# ---------- entry / vestibule: coat hooks, one plant by the door
L = dict(room="living", **F)
box("CoatRail", (3.1, 1.7, 1.09), (0.4, 0.03, 0.03), M["frame"], bevel=0, rot_z=math.pi / 2, **L)
for i in range(3):
    box(f"Hook{i}", (3.03, 1.65, 0.95 + i * 0.14), (0.05, 0.08, 0.012), M["frame"], bevel=0, **L)
wall_art("Art_hall", 3.02, 1.5, 1.9, 0.5, 0.7, math.pi / 2, M["art2"])
plant("Plant_hall", 4.35, 0.42, s=1.1)

# ---------- kitchen: matte black run along the north wall with the fridge column in the NE corner,
#            a short return down the east wall with the sink, oak uppers, quartz island with three stools
K = dict(room="kitchen", **F)
box("KitchenBase", (5.65, 0.44, 0.37), (2.1, 0.88, 0.6), M["black"], bevel=0.005, **K)
for i, x in enumerate([5.0, 5.6, 6.2]):
    box(f"BaseGap_{i}", (x, 0.44, 0.675), (0.004, 0.84, 0.01), M["frame"], bevel=0, **K)
box("KitchenTop", (5.65, 0.9, 0.37), (2.14, 0.03, 0.63), M["quartz"], bevel=0.006, **K)
box("Backsplash", (5.65, 1.28, 0.09), (2.1, 0.7, 0.02), M["quartz"], bevel=0, **K)
box("KitchenUpper", (5.65, 2.1, 0.25), (2.1, 0.7, 0.35), M["oak"], bevel=0.005, **K)
for i, x in enumerate([5.0, 5.6, 6.2]):
    box(f"UpperGap_{i}", (x, 2.1, 0.427), (0.004, 0.66, 0.01), M["frame"], bevel=0, **K)
box("UpperLED", (5.65, 1.732, 0.3), (2.0, 0.01, 0.2), M["downlight"], bevel=0, part="light", room="kitchen")
box("Hob", (5.3, 0.912, 0.37), (0.6, 0.008, 0.5), M["screen"], bevel=0.003, **K)
box("Hood", (5.3, 1.66, 0.25), (0.7, 0.06, 0.35), M["steel"], bevel=0.006, **K)
box("Column", (6.95, 1.1, 0.37), (0.7, 2.2, 0.64), M["black"], bevel=0.006, **K)     # integrated fridge
box("ColumnGap", (6.95, 1.55, 0.047), (0.66, 0.004, 0.01), M["frame"], bevel=0, **K)
box("EastBase", (7.0, 0.44, 1.55), (0.6, 0.88, 1.7), M["black"], bevel=0.005, **K)  # return along the east wall
box("EastTop", (6.985, 0.9, 1.55), (0.63, 0.03, 1.74), M["quartz"], bevel=0.006, **K)
box("EastSplash", (7.21, 1.28, 1.55), (0.02, 0.7, 1.7), M["quartz"], bevel=0, **K)
box("Sink", (6.98, 0.905, 1.4), (0.4, 0.02, 0.55), M["steel"], bevel=0.005, **K)
box("Tap", (7.15, 1.06, 1.4), (0.018, 0.32, 0.018), M["frame"], bevel=0, **K)
box("TapSpout", (7.08, 1.21, 1.4), (0.16, 0.018, 0.018), M["frame"], bevel=0, **K)
# island: quartz slab on a black base, stools on the living side
box("IslandBase", (5.45, 0.44, 2.65), (1.7, 0.88, 0.6), M["black"], bevel=0.005, **K)
box("IslandTop", (5.45, 0.905, 2.65), (1.9, 0.035, 0.8), M["quartz"], bevel=0.006, **K)
for i, x in enumerate([4.85, 5.45, 6.05]):
    stool(f"Stool{i + 1}", x, 3.25)
box("Board", (4.8, 0.93, 2.6), (0.32, 0.015, 0.22), M["walnut"], bevel=0.003, **K)
cyl("Bowl", (6.0, 0.96, 2.6), 0.13, 0.08, M["black"], r2=0.08, bevel=0.01, **K)
for i, x in enumerate([5.0, 5.9]):
    cyl(f"PendantCord_{i}", (x, 2.1, 2.65), 0.003, 1.0, M["frame"], verts=6, **K)
    cyl(f"Pendant_{i}", (x, 1.55, 2.65), 0.07, 0.24, M["pendant"], r2=0.09, part="light", room="kitchen")

# ---------- living: sofa along the east wall facing the media wall on the bedroom partition
box("Rug_living", (5.35, 0.008, 4.35), (2.6, 0.012, 1.9), M["rug"], bevel=0.004, **L)
sofa("Sofa", 6.72, 4.35, math.pi / 2, w=2.1)                          # back to the east wall, facing west
box("CoffeeTable", (5.55, 0.34, 4.35), (0.55, 0.03, 1.0), M["walnut"], bevel=0.006, **L)
box("CoffeeFrame", (5.55, 0.16, 4.35), (0.4, 0.3, 0.8), M["frame"], bevel=0.004, **L)
box("Book1", (5.55, 0.37, 4.05), (0.2, 0.025, 0.28), M["book"], bevel=0.004, **L)
box("Tray", (5.55, 0.365, 4.6), (0.2, 0.015, 0.3), M["frame"], bevel=0.004, **L)
lounge_chair("Lounge", 4.55, 4.95, -math.pi / 2 - 0.9)               # by the window, angled toward the sofa
floor_lamp("FloorLamp", 6.85, 5.15)
box("Console", (3.88, 0.42, 4.35), (0.42, 0.28, 1.6), M["walnut"], bevel=0.008, **L)
box("ConsoleGap", (3.88, 0.42, 3.545), (0.4, 0.01, 0.005), M["frame"], bevel=0, **L)
box("TV", (3.7, 1.35, 4.35), (0.035, 0.72, 1.25), M["screen"], bevel=0.004, **L)
box("TVpanel", (3.72, 1.35, 4.35), (0.004, 0.66, 1.19), M["screen"], bevel=0, **L)
box("Speaker1", (3.88, 0.14, 3.7), (0.2, 0.28, 0.16), M["black"], bevel=0.008, **L)
box("Speaker2", (3.88, 0.14, 5.0), (0.2, 0.28, 0.16), M["black"], bevel=0.008, **L)
wall_art("Art_living", 7.21, 1.6, 3.3, 0.7, 0.95, -math.pi / 2, M["art2"])
plant("Plant_living", 3.95, 5.1, s=1.3)

# ---------- bedroom: bed with the headboard on the west wall, wardrobe wall along the north, desk by the partition
B = dict(room="bedroom", **F)
box("Wardrobe", (1.25, 1.15, 2.59), (2.3, 2.3, 0.6), M["black"], bevel=0.006, **B)
for i, x in enumerate([0.55, 1.05, 1.55, 2.05]):
    box(f"WardrobeGap_{i}", (x, 1.15, 2.893), (0.004, 2.26, 0.01), M["frame"], bevel=0, **B)
box("Rug_bedroom", (2.55, 0.008, 4.0), (1.4, 0.012, 2.4), M["rug_dark"], bevel=0.004, **B)
box("BedPlatform", (1.15, 0.13, 3.95), (2.2, 0.24, 2.0), M["walnut"], bevel=0.01, **B)
soft("Mattress", (1.15, 0.36, 3.95), (2.0, 0.24, 1.6), M["linen"], r=0.05, **B)
soft("Duvet", (1.5, 0.5, 3.95), (1.25, 0.07, 1.64), M["charcoal"], r=0.03, **B)
box("Headboard", (0.09, 0.65, 3.95), (0.06, 1.1, 2.4), M["charcoal"], bevel=0.01, **B)
soft("PillowN", (0.38, 0.55, 3.55), (0.42, 0.16, 0.68), M["linen"], r=0.05, **B)
soft("PillowS", (0.38, 0.55, 4.35), (0.42, 0.16, 0.68), M["linen"], r=0.05, **B)
box("Nightstand", (0.3, 0.45, 5.15), (0.38, 0.12, 0.42), M["walnut"], bevel=0.006, **B)
box("WallLampArm", (0.12, 1.15, 5.15), (0.14, 0.02, 0.02), M["frame"], bevel=0, **B)
cyl("WallLamp", (0.22, 1.1, 5.15), 0.05, 0.12, M["lamp"], r2=0.06, part="light", room="bedroom")
box("Desk", (3.25, 0.74, 3.9), (0.55, 0.03, 1.2), M["walnut"], bevel=0.005, **B)
for i, z in enumerate([3.35, 4.45]):
    box(f"DeskLeg_{i}", (3.25, 0.36, z), (0.5, 0.72, 0.03), M["frame"], bevel=0, **B)
box("Monitor", (3.45, 1.05, 3.9), (0.02, 0.36, 0.62), M["screen"], bevel=0.003, **B)
box("MonitorStand", (3.45, 0.83, 3.9), (0.03, 0.14, 0.03), M["frame"], bevel=0, **B)
box("MonitorFoot", (3.45, 0.76, 3.9), (0.12, 0.01, 0.2), M["frame"], bevel=0.003, **B)
box("Keyboard", (3.15, 0.765, 3.9), (0.12, 0.012, 0.36), M["black"], bevel=0.003, **B)
office_chair("DeskChair", 2.7, 3.9, -math.pi / 2)
wall_art("Art_bedroom", 0.09, 1.75, 3.95, 1.4, 0.55, math.pi / 2, M["art2"], room="bedroom")
plant("Plant_bedroom", 3.2, 5.05, s=1.1, room="bedroom")

# ---------- bathroom: shower in the NW corner, toilet on the north wall, walnut vanity on the south wall
Ba = dict(room="bath", **F)
box("ShowerGlass", (0.95, 1.1, 0.5), (0.01, 2.2, 1.0), M["glass"], "Glass", bevel=0, part="glass", side="I", room="bath")
box("ShowerGlass2", (0.5, 1.1, 1.0), (0.9, 2.2, 0.01), M["glass"], "Glass", bevel=0, part="glass", side="I", room="bath")
box("ShowerPost", (0.95, 1.1, 1.0), (0.025, 2.2, 0.025), M["frame"], bevel=0, **Ba)
box("ShowerPipe", (0.08, 1.5, 0.5), (0.02, 1.2, 0.02), M["frame"], bevel=0, **Ba)
box("ShowerHead", (0.2, 2.15, 0.5), (0.25, 0.012, 0.25), M["frame"], bevel=0.003, **Ba)
box("ShowerArm", (0.15, 2.15, 0.5), (0.14, 0.012, 0.012), M["frame"], bevel=0, **Ba)
soft("Toilet", (1.45, 0.2, 0.42), (0.38, 0.4, 0.55), M["white"], r=0.06, **Ba)
soft("Cistern", (1.45, 0.6, 0.18), (0.38, 0.4, 0.18), M["white"], r=0.03, **Ba)
box("Vanity", (0.6, 0.5, 1.9), (0.8, 0.35, 0.45), M["walnut"], bevel=0.006, **Ba)
box("VanityTop", (0.6, 0.69, 1.9), (0.82, 0.03, 0.47), M["quartz"], bevel=0.004, **Ba)
soft("Basin", (0.6, 0.76, 1.88), (0.42, 0.11, 0.32), M["white"], r=0.04, **Ba)
box("BasinTap", (0.6, 0.9, 2.06), (0.02, 0.2, 0.02), M["frame"], bevel=0, **Ba)
box("Mirror", (0.6, 1.55, 2.12), (0.6, 0.8, 0.015), M["steel"], bevel=0, **Ba)
box("MirrorFrame", (0.6, 1.55, 2.115), (0.64, 0.84, 0.01), M["frame"], bevel=0, **Ba)
box("TowelRail", (1.5, 1.2, 2.12), (0.5, 0.015, 0.015), M["frame"], bevel=0, **Ba)
soft("Towel", (1.5, 1.0, 2.1), (0.3, 0.4, 0.03), M["towel"], r=0.01, **Ba)

# ---------- service room (P.S.): washer, boiler, shelves
Sv = dict(room="service", **F)
box("Washer", (2.25, 0.425, 0.4), (0.6, 0.85, 0.6), M["white"], bevel=0.015, **Sv)
cyl("WasherDoor", (2.25, 0.45, 0.71), 0.19, 0.02, M["screen"], rot=(math.radians(90), 0, 0), **Sv)
box("Boiler", (2.45, 1.9, 0.3), (0.45, 0.7, 0.4), M["white"], bevel=0.015, **Sv)
box("ShelfA", (2.05, 1.3, 1.15), (0.28, 0.025, 0.6), M["oak"], bevel=0.004, **Sv)
box("ShelfB", (2.05, 1.75, 1.15), (0.28, 0.025, 0.6), M["oak"], bevel=0.004, **Sv)
box("Basket", (2.05, 1.42, 1.15), (0.22, 0.22, 0.28), M["black"], bevel=0.01, **Sv)

# ---------- terrace: two lounge chairs facing the view, a side table, planters against the east wall, one olive
Tr = dict(room="terrace", **F)
box("Rug_terrace", (1.8, 0.006, 6.2), (2.6, 0.012, 1.2), M["rug"], bevel=0.004, **Tr)
lounge_chair("OutdoorChair0", 1.15, 6.2, 0.0, room="terrace")
lounge_chair("OutdoorChair1", 2.45, 6.2, 0.0, room="terrace")
box("OutdoorTable", (1.8, 0.4, 6.35), (0.4, 0.03, 0.4), M["walnut"], bevel=0.006, **Tr)
cyl("OutdoorTableLeg", (1.8, 0.2, 6.35), 0.02, 0.4, M["frame"], verts=10, **Tr)
for i, z in enumerate([5.75, 6.55]):
    box(f"Planter_{i}", (3.32, 0.2, z), (0.38, 0.4, 0.6), M["pot_black"], bevel=0.01, **Tr)
    grass(f"Grass_{i}", 3.32, z, s=0.9)
plant("Olive_1", 0.38, 5.8, s=1.25, pot="black", room="terrace", leaves=40)
box("WallLight", (1.8, 2.0, 5.48), (0.1, 0.22, 0.1), M["frame"], bevel=0.008, part="light", room="terrace")
box("WallLightGlow", (1.8, 2.0, 5.54), (0.06, 0.16, 0.02), M["downlight"], bevel=0, part="light", room="terrace")

# ----------------------------------------------------------------------------- lighting + renders (used by bake_lightmaps.py / render_views.py)
LIGHTS = [(f"Down_{i}", (x, 2.5, z), 18, (1.0, 0.92, 0.8)) for i, (x, z) in enumerate(DOWNLIGHTS)] + [
    ("Pendant_a", (5.0, 1.45, 2.65), 10), ("Pendant_b", (5.9, 1.45, 2.65), 10),
    ("FloorLamp", (7.0, 1.45, 5.15), 25),
    ("WallLamp", (0.25, 1.1, 5.15), 6),
    ("LED", (5.65, 1.7, 0.3), 14, (1.0, 0.95, 0.85), 1.6),
    ("Terrace", (1.8, 2.0, 5.7), 12),
]
SUN_ROT = (48, 12, 30)            # afternoon sun from the south-west, through the terrace and the living window
FILL_AT = (3.6, 9.0, 9.0)
RENDER_VIEWS = [
    ("whole",   (-8.5, 13.5, 17.5), (3.65, 0.4, 3.2), 30, "SW"),
    ("living",  (5.5, 6.0, 12.5),   (5.4, 0.6, 3.9), 40, "S"),
    ("kitchen", (5.8, 6.0, -6.0),   (5.8, 0.7, 1.3), 40, "N"),
    ("bedroom", (1.4, 6.5, 12.0),   (1.6, 0.3, 3.9), 40, "S"),
    ("bath",    (-6.5, 4.5, 1.2),   (0.9, 0.8, 1.1), 42, "W"),
    ("terrace", (-4.5, 4.0, 11.5),  (1.8, 0.7, 6.2), 42, "SW"),
    ("service", (2.4, 5.0, -5.5),   (2.4, 0.6, 0.8), 40, "N"),
]

export(OUT, blend=os.path.join(HERE, "duna.blend"))
