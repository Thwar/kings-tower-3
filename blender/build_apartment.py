"""
King's Tower · Dept. D — builds the apartment in Blender and exports site/apartment.glb.

Run headless:   python3 blender/build_apartment.py [--blend]      (needs `pip install bpy`)
Or in Blender:  blender --background --python blender/build_apartment.py

Geometry, materials and furniture helpers live in ktlib.py (shared with build_duna.py).
Interior concept: minimal bachelor pad — warm off-white plaster, mid-oak plank floor, matte black and walnut,
charcoal linen and black leather, one statement piece per room, nothing on the counters that doesn't earn its place.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ktlib import (H, T, M, X, STYLE, box, soft, cyl, sphere, floor_plane, build_walls, downlights,  # noqa: E402
                   plant, grass, sofa, lounge_chair, stool, office_chair, floor_lamp, wall_art, export,
                   led_cove, gaming_desk, display_cabinet, vanity, glass_wardrobe, sectional, tv_wall, loft_coffee_table)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "apartment.glb" if STYLE == "bachelor" else f"apartment-{STYLE}.glb")
APT = dict(name="King's Tower · Dept. D", site="site")

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
DOWNLIGHTS = [(1.2, 1.0), (1.2, 3.4), (2.6, 2.2), (5.6, 1.4), (4.3, 1.4), (5.4, 4.3), (1.0, 5.2), (2.7, 5.2)]

# ----------------------------------------------------------------------------- structure
build_walls(walls, frames)
# floors (never overlapping each other or the slab: avoids z-fighting on phones)
floor_plane("Floor_living_a", (0, 0, 7.8, 4.45), M["wood"], room="living")
floor_plane("Floor_living_b", (3.35, 4.45, 7.8, 5.95), M["wood"], room="bedroom")
floor_plane("Floor_wet", (-0.4, 4.45, 3.35, 5.95), M["tile"], room="bath")
floor_plane("Floor_terrace", (7.8, 0, 12.8, 5.95), M["stone"], room="terrace")
box("Slab", (6.2, -0.17, 2.975), (13.6, 0.3, 6.75), M["concrete"], "Structure", bevel=0.02, part="slab")


# ceiling + downlights
box("Ceiling", (3.7, H + 0.05, 2.975), (8.2, 0.1, 5.95), M["ceiling"], "Ceiling", bevel=0, part="ceiling")
downlights(DOWNLIGHTS)

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

F = dict(part="furniture")

if STYLE == "bachelor":
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

if STYLE == "bachelor":
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


if STYLE == "loft":
    # ---------- loft living: sectional + fur rug, media wall with shelves and photos, gaming desk under the window, glass cabinet
    L = dict(room="living", **F)
    led_cove("Cove_living", (0, 0, 3.4, 4.45))
    led_cove("Cove_kitchen", (3.4, 0, 7.8, 2.75), room="kitchen")
    box("Rug_living", (1.7, 0.008, 2.4), (2.4, 0.012, 2.2), M["rug"], bevel=0.004, **L)
    sectional("Sofa", 1.6, 3.45, math.pi, w=2.4)
    loft_coffee_table("CoffeeTable", 1.7, 2.3)
    tv_wall("TVwall", 2.55, 0.08, 0, w=1.7, shelf_dx=1.2, shoes=False)
    gaming_desk("Desk", 0.45, 2.05, -math.pi / 2)
    display_cabinet("Cabinet", 0.55, 4.22, math.pi)
    floor_lamp("FloorLamp", 3.05, 3.85)
    plant("Plant_living", 3.05, 0.55, s=1.35)
    box("CoatRail", (1.95, 1.7, 0.09), (0.5, 0.03, 0.03), M["frame"], bevel=0, **L)
    for i in range(3):
        box(f"Hook{i}", (1.8 + i * 0.15, 1.65, 0.11), (0.012, 0.08, 0.05), M["frame"], bevel=0, **L)
    # ---------- loft bedroom: same bed in grey, glass wardrobe with LED, lit vanity instead of the desk
    B = dict(room="bedroom", **F)
    led_cove("Cove_bedroom", (3.35, 2.75, 7.8, 5.95), room="bedroom")
    box("Rug_bedroom", (5.45, 0.008, 4.0), (2.6, 0.012, 1.6), M["rug_dark"], bevel=0.004, **B)
    box("BedPlatform", (5.45, 0.13, 4.95), (2.0, 0.24, 2.2), M["black"], bevel=0.01, **B)
    soft("Mattress", (5.45, 0.36, 4.95), (1.6, 0.24, 2.0), M["linen"], r=0.05, **B)
    soft("Duvet", (5.45, 0.5, 4.6), (1.64, 0.07, 1.25), M["charcoal"], r=0.03, **B)
    box("Headboard", (5.45, 0.65, 5.86), (2.6, 1.1, 0.06), M["charcoal"], bevel=0.01, **B)
    soft("PillowL", (5.05, 0.55, 5.62), (0.68, 0.16, 0.42), M["linen"], r=0.05, **B)
    soft("PillowR", (5.85, 0.55, 5.62), (0.68, 0.16, 0.42), M["linen"], r=0.05, **B)
    for i, x in enumerate([4.15, 6.75]):
        box(f"Nightstand_{i}", (x, 0.45, 5.7), (0.45, 0.12, 0.38), M["walnut"], bevel=0.006, **B)
        box(f"WallLampArm_{i}", (x, 1.15, 5.88), (0.02, 0.02, 0.14), M["frame"], bevel=0, **B)
        cyl(f"WallLamp_{i}", (x, 1.1, 5.78), 0.05, 0.12, M["lamp"], r2=0.06, part="light", room="bedroom")
    glass_wardrobe("Wardrobe", 3.72, 4.9, math.pi / 2, w=1.9)
    vanity("Vanity", 7.0, 3.2, 0)
    plant("Plant_bedroom", 7.35, 5.5, s=1.5)
    wall_art("Art_bedroom", 5.45, 1.75, 5.88, 1.5, 0.6, 0, M["art2"], room="bedroom")

# ----------------------------------------------------------------------------- lighting + renders (used by bake_lightmaps.py / render_views.py)
# bake: (name, (x, y, z), energy[, color[, radius]])
LIGHTS = [(f"Down_{i}", (x, 2.5, z), 18, (1.0, 0.92, 0.8)) for i, (x, z) in enumerate(DOWNLIGHTS)] + [
    ("Pendant_a", (4.4, 1.45, 1.25), 10), ("Pendant_b", (4.4, 1.45, 2.15), 10),
    ("FloorLamp", (3.65, 1.45, 3.85), 25),
    ("WallLamp_a", (4.15, 1.1, 5.75), 6), ("WallLamp_b", (6.75, 1.1, 5.75), 6),
    ("LED", (6.1, 1.7, 2.4), 14, (1.0, 0.95, 0.85), 1.6),
    ("Terrace", (10.3, 2.0, 0.3), 12),
]
SUN_ROT = (48, -12, -40)          # low afternoon sun from the west window / terrace side (degrees, Blender XYZ euler)
FILL_AT = (2.0, 9.0, 8.0)         # area fill light for the Cycles renders
# renders: key, camera position (plan), look-at (plan), fov, hidden wall sides
RENDER_VIEWS = [
    ("whole",   (-7.5, 11.5, 16.5), (6.2, 0.5, 3.0), 30, "SW"),
    ("living",  (-6.0, 5.0, 5.0),  (2.8, 0.6, 2.2), 40, "SW"),
    ("kitchen", (9.0, 6.0, -5.5),  (5.3, 0.7, 1.7), 40, "N"),
    ("bedroom", (6.2, 9.5, 11.0),  (5.5, 0.3, 4.4), 40, "S"),
    ("bath",    (-3.5, 4.0, 9.0),  (1.0, 0.8, 5.0), 42, "SW"),
    ("terrace", (17.0, 5.0, -2.5), (10.3, 0.8, 3.0), 42, "NE"),
    ("service", (2.6, 5.0, 12.0),  (2.55, 0.6, 5.3), 40, "S"),
]

export(OUT, blend=os.path.join(HERE, "apartment.blend"))
