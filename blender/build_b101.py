"""
Bloque B · Departamento 101 — builds the apartment in Blender and exports site/b101/apartment.glb.

Run headless:   python3 blender/build_b101.py [--blend]      (needs `pip install bpy`)

One-bedroom, 100.20 m² in total, on a long north-south strip (brochure page 9, "imagen referencial"). North up:
a large terrace at the top with an outdoor dining table and a barbecue on the east side, a laundry cubicle in
its SW corner, then the bedroom (sliding door onto the terrace, headboard on the east wall) with the wardrobe
room and the bathroom stacked in a column along the WEST side, the living in the middle (sofa on the east wall),
and the kitchen run down the west wall + dining table at the south end, entrance in the SE corner.
The plan below is written with the column on the east and mirrored at the end (mirror_x), so read every x as W − x. The brochure gives only the total, so the strip is scaled from the drawing: 5.7 m wide,
6.8 m of terrace + 10.7 m enclosed.

Same interior concept as the other two: minimal bachelor pad — off-white plaster, oak floor, matte black
and walnut, charcoal linen and black leather.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ktlib import (H, T, M, X, box, soft, cyl, floor_plane, build_walls, downlights, mirror_x,  # noqa: E402
                   plant, grass, sofa, lounge_chair, stool, chair, office_chair, floor_lamp, wall_art, export)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "b101", "apartment.glb")
APT = dict(name="Bloque B · Dpto. 101", site="site/b101")

# ----------------------------------------------------------------------------- plan (metres; x east, z south, origin NW corner of the terrace)
W, TZ, D = 5.7, 6.8, 17.5           # width, terrace depth, total depth
BZ, CZ, BS = 9.65, 12.9, 9.2        # bedroom south wall, bathroom south wall, closet/bath partition
walls = [
    # terrace edge: glass railings north and west, the neighbour's wall on the east
    (0, 0, W, 0, "N", dict(y0=0.12, y1=1.1, glass=True)),
    (0, 0, 0, TZ, "W", dict(y0=0.12, y1=1.1, glass=True)),
    (W, 0, W, D, "E", dict(**X)),
    # terrace / bedroom wall with the sliding door x 0.8–2.6
    (0, TZ, 0.8, TZ, "N", dict(ext=(True, False))), (2.6, TZ, W, TZ, "N", dict(ext=(False, True))),
    (0.8, TZ, 2.6, TZ, "N", dict(y0=2.25, y1=H, noskirt=True)),
    # laundry cubicle on the terrace (x 4.4–5.7, z 5.5–6.8), door on its north side x 4.6–5.4
    (4.4, 5.5, 4.6, 5.5, "N", dict(ext=(True, False))), (5.4, 5.5, W, 5.5, "N", dict(ext=(False, True))),
    (4.6, 5.5, 5.4, 5.5, "N", dict(y0=2.1, y1=H, noskirt=True)),
    (4.4, 5.5, 4.4, TZ, "W", dict(**X)),
    # west wall with the living window z 10.2–12.2
    (0, TZ, 0, 10.2, "W", dict(ext=(True, False))), (0, 12.2, 0, D, "W", dict(ext=(False, True))),
    (0, 10.2, 0, 12.2, "W", dict(y0=0, y1=0.9)), (0, 10.2, 0, 12.2, "W", dict(y0=2.25, y1=H, noskirt=True)),
    (0, 10.2, 0, 12.2, "W", dict(y0=0.9, y1=2.25, glass=True)),
    # south wall with the entrance x 0.5–1.4
    (0, D, 0.5, D, "S", dict(ext=(True, False))), (1.4, D, W, D, "S", dict(ext=(False, True))),
    (0.5, D, 1.4, D, "S", dict(y0=2.1, y1=H, noskirt=True)),
    # interior: bedroom south wall (door x 2.55–3.4), the east column (closet door z 7.3–8.1, bath door z 10.0–10.8)
    (0, BZ, 2.55, BZ, "I", dict(ext=(True, False))), (3.4, BZ, 3.6, BZ, "I", dict(ext=(False, True))),
    (2.55, BZ, 3.4, BZ, "I", dict(y0=2.1, y1=H, noskirt=True)),
    (3.6, TZ, 3.6, 7.3, "I", dict(ext=(True, False))), (3.6, 8.1, 3.6, 10.0, "I", {}), (3.6, 10.8, 3.6, CZ, "I", dict(ext=(False, True))),
    (3.6, 7.3, 3.6, 8.1, "I", dict(y0=2.1, y1=H, noskirt=True)), (3.6, 10.0, 3.6, 10.8, "I", dict(y0=2.1, y1=H, noskirt=True)),
    (3.6, BS, W, BS, "I", dict(**X)),
    (3.6, CZ, W, CZ, "I", dict(**X)),
]
frames = [
    (0, 10.2, 0, 12.2, 0.9, 2.25, "W"),
    (0.8, TZ, 2.6, TZ, 0, 2.25, "N"),
]
DOWNLIGHTS = [(1.2, 7.6), (2.6, 8.8), (4.65, 8.0), (4.65, 10.2), (4.65, 12.0), (1.2, 10.6), (2.6, 12.2),
              (1.6, 14.2), (3.6, 14.2), (1.6, 16.4), (3.6, 16.4), (5.05, 6.15)]

# ----------------------------------------------------------------------------- structure
build_walls(walls, frames)
floor_plane("Floor_terrace_a", (0, 0, W, 5.5), M["stone"], room="terrace")
floor_plane("Floor_terrace_b", (0, 5.5, 4.4, TZ), M["stone"], room="terrace")
floor_plane("Floor_laundry", (4.4, 5.5, W, TZ), M["tile"], room="service")
floor_plane("Floor_bedroom", (0, TZ, 3.6, BZ), M["wood"], room="bedroom")
floor_plane("Floor_closet", (3.6, TZ, W, BS), M["wood"], room="bedroom")
floor_plane("Floor_bath", (3.6, BS, W, CZ), M["tile"], room="bath")
floor_plane("Floor_living", (0, BZ, 3.6, CZ), M["wood"], room="living")
floor_plane("Floor_kitchen", (0, CZ, W, D), M["wood"], room="kitchen")
box("Slab", (W / 2, -0.17, D / 2), (W + 0.8, 0.3, D + 0.8), M["concrete"], "Structure", bevel=0.02, part="slab")

box("Ceiling", (W / 2, H + 0.05, (TZ + D) / 2), (W + T, 0.1, D - TZ + T), M["ceiling"], "Ceiling", bevel=0, part="ceiling")
box("Ceiling_laundry", (5.05, H + 0.05, 6.08), (1.44, 0.1, 1.3), M["ceiling"], "Ceiling", bevel=0, part="ceiling")
downlights(DOWNLIGHTS)

# terrace curbs + railings (north and west edges)
box("Curb_N", (W / 2, 0.06, 0), (W, 0.12, T), M["concrete"], "Structure", part="slab", room="terrace")
box("RailCap_N", (W / 2, 1.12, 0), (W, 0.04, 0.05), M["railing"], "Structure", part="slab", room="terrace")
box("Curb_W", (0, 0.06, TZ / 2 + 0.07), (T, 0.12, TZ - 0.14), M["concrete"], "Structure", part="slab", room="terrace")
box("RailCap_W", (0, 1.12, TZ / 2 + 0.07), (0.05, 0.04, TZ - 0.14), M["railing"], "Structure", part="slab", room="terrace")
for i, x in enumerate([0.1, 1.5, 2.9, 4.3, 5.6]):
    box(f"RailPostN_{i}", (x, 0.6, 0), (0.03, 1.0, 0.03), M["railing"], "Structure", bevel=0, part="slab", room="terrace")
for i, z in enumerate([1.4, 2.8, 4.2, 5.6, 6.7]):
    box(f"RailPostW_{i}", (0, 0.6, z), (0.03, 1.0, 0.03), M["railing"], "Structure", bevel=0, part="slab", room="terrace")

# doors
box("SlideLeaf", (1.25, 1.12, TZ - 0.06), (0.9, 2.2, 0.03), M["glass"], "Glass", bevel=0, part="glass", side="I")
box("Door_entry", (0.95, 1.05, D - 0.08), (0.9, 2.1, 0.05), M["black"], "Furniture", part="furniture", room="kitchen")
box("Door_handle", (1.28, 1.02, D - 0.13), (0.02, 0.3, 0.02), M["frame"], "Furniture", bevel=0, part="furniture", room="kitchen")
box("Door_bedroom", (2.6, 1.05, BZ - 0.45), (0.04, 2.1, 0.85), M["walnut"], "Furniture", part="furniture", room="bedroom")   # open into the bedroom
box("Door_closet", (3.67, 1.05, 7.7), (0.04, 2.1, 0.8), M["walnut"], "Furniture", part="furniture", room="bedroom")           # open, flat against the closet wall
box("Door_bath", (3.53, 1.05, 10.4), (0.04, 2.1, 0.8), M["walnut"], "Furniture", part="furniture", room="bath")             # open flat on the living side
box("Door_laundry", (4.63, 1.05, 5.9), (0.04, 2.1, 0.8), M["walnut"], "Furniture", part="furniture", room="service")

F = dict(part="furniture")

# ---------- terrace: outdoor dining for four, a brick barbecue, planters and two olive trees
Tr = dict(room="terrace", **F)
box("TerraceTable", (2.85, 0.74, 2.9), (1.8, 0.04, 0.9), M["walnut"], bevel=0.006, **Tr)
for i, (dx, dz) in enumerate([(-0.6, -0.5), (0.6, -0.5), (-0.6, 0.5), (0.6, 0.5)]):
    box(f"TerraceTableLeg{i}", (2.85 + dx, 0.36, 2.9 + dz * 0.75), (0.04, 0.72, 0.04), M["frame"], bevel=0, **Tr)
for i, (dx, dz, r) in enumerate([(-0.45, -0.8, math.pi), (0.45, -0.8, math.pi), (-0.45, 0.8, 0.0), (0.45, 0.8, 0.0)]):
    chair(f"TerraceChair{i}", 2.85 + dx, 2.9 + dz, r, room="terrace", fabric=M["linen"])
box("BBQ", (0.75, 0.45, 0.85), (1.1, 0.9, 0.7), M["concrete"], bevel=0.008, **Tr)
box("BBQTop", (0.75, 0.905, 0.85), (1.14, 0.03, 0.74), M["black"], bevel=0.004, **Tr)
box("Grill", (0.55, 0.925, 0.85), (0.55, 0.012, 0.5), M["steel"], bevel=0, **Tr)
box("BBQHood", (0.55, 1.7, 0.85), (0.6, 0.35, 0.5), M["black"], bevel=0.01, **Tr)
box("Chimney", (0.55, 2.2, 0.85), (0.16, 0.7, 0.16), M["black"], bevel=0.004, **Tr)
sofa("OutdoorSofa", 1.6, 5.05, math.pi, w=1.9, fabric=M["linen"], room="terrace")
box("Rug_terrace", (1.6, 0.006, 4.4), (2.6, 0.012, 1.8), M["rug"], bevel=0.004, **Tr)
box("OutdoorTable", (1.6, 0.3, 4.05), (0.8, 0.04, 0.45), M["walnut"], bevel=0.006, **Tr)
box("OutdoorTableFrame", (1.6, 0.14, 4.05), (0.7, 0.26, 0.35), M["frame"], bevel=0.004, **Tr)
for i, x in enumerate([2.0, 3.0, 4.0]):
    box(f"Planter_{i}", (x, 0.2, 0.35), (0.8, 0.4, 0.38), M["pot_black"], bevel=0.01, **Tr)
    grass(f"Grass_{i}", x, 0.35, s=1.0)
plant("Olive_1", 5.2, 0.55, s=1.6, pot="black", room="terrace", leaves=48)
plant("Olive_2", 0.5, 6.25, s=1.3, pot="black", room="terrace", leaves=40)
plant("Olive_3", 3.9, 6.2, s=1.2, pot="black", room="terrace", leaves=36)
box("WallLight", (3.5, 2.0, TZ - 0.08), (0.1, 0.22, 0.1), M["frame"], bevel=0.008, part="light", room="terrace")
box("WallLightGlow", (3.5, 2.0, TZ - 0.14), (0.06, 0.16, 0.02), M["downlight"], bevel=0, part="light", room="terrace")

# ---------- laundry cubicle
Sv = dict(room="service", **F)
box("Washer", (5.3, 0.425, 6.4), (0.6, 0.85, 0.6), M["white"], bevel=0.015, **Sv)
cyl("WasherDoor", (5.3, 0.45, 6.09), 0.19, 0.02, M["screen"], rot=(math.radians(90), 0, 0), **Sv)
box("Dryer", (5.3, 1.3, 6.4), (0.6, 0.85, 0.6), M["white"], bevel=0.015, **Sv)
cyl("DryerDoor", (5.3, 1.32, 6.09), 0.19, 0.02, M["screen"], rot=(math.radians(90), 0, 0), **Sv)
box("LaundryShelf", (4.7, 1.5, 6.4), (0.5, 0.025, 0.35), M["oak"], bevel=0.004, **Sv)
box("Basket", (4.7, 0.16, 6.4), (0.4, 0.32, 0.4), M["black"], bevel=0.01, **Sv)

# ---------- bedroom: bed with the headboard on the south wall, facing the terrace; nightstands; art
B = dict(room="bedroom", **F)
box("Rug_bedroom", (1.7, 0.008, 7.6), (2.4, 0.012, 1.2), M["rug_dark"], bevel=0.004, **B)
box("BedPlatform", (1.7, 0.13, 8.4), (2.0, 0.24, 2.2), M["walnut"], bevel=0.01, **B)
soft("Mattress", (1.7, 0.36, 8.4), (1.6, 0.24, 2.0), M["linen"], r=0.05, **B)
soft("Duvet", (1.7, 0.5, 8.05), (1.64, 0.07, 1.25), M["charcoal"], r=0.03, **B)
box("Headboard", (1.7, 0.65, BZ - 0.1), (2.6, 1.1, 0.06), M["charcoal"], bevel=0.01, **B)
soft("PillowL", (1.3, 0.55, 9.05), (0.68, 0.16, 0.42), M["linen"], r=0.05, **B)
soft("PillowR", (2.1, 0.55, 9.05), (0.68, 0.16, 0.42), M["linen"], r=0.05, **B)
for i, x in enumerate([0.4, 3.0]):
    box(f"Nightstand_{i}", (x, 0.45, 9.15), (0.45, 0.12, 0.38), M["walnut"], bevel=0.006, **B)
    box(f"WallLampArm_{i}", (x, 1.15, BZ - 0.09), (0.02, 0.02, 0.14), M["frame"], bevel=0, **B)
    cyl(f"WallLamp_{i}", (x, 1.1, BZ - 0.19), 0.05, 0.12, M["lamp"], r2=0.06, part="light", room="bedroom")
wall_art("Art_bedroom", 1.7, 1.75, BZ - 0.08, 1.5, 0.6, 0, M["art2"], room="bedroom")
plant("Plant_bedroom", 3.2, 7.2, s=1.2, room="bedroom")
# closet room: wardrobe wall on the east, shelves on the north
box("Wardrobe", (5.4, 1.15, 8.0), (0.6, 2.3, 2.2), M["black"], bevel=0.006, **B)
for i, z in enumerate([7.2, 7.7, 8.2, 8.7]):
    box(f"WardrobeGap_{i}", (5.097, 1.15, z), (0.01, 2.26, 0.004), M["frame"], bevel=0, **B)
for i, y in enumerate([0.4, 0.9, 1.4, 1.9]):
    box(f"ClosetShelf_{i}", (4.35, y, TZ + 0.25), (1.3, 0.025, 0.4), M["oak"], bevel=0.004, **B)
box("ClosetBox1", (4.1, 1.53, TZ + 0.25), (0.35, 0.24, 0.35), M["black"], bevel=0.01, **B)
box("ClosetBox2", (4.6, 1.03, TZ + 0.25), (0.35, 0.24, 0.35), M["book"], bevel=0.01, **B)

# ---------- bathroom: shower across the south end, toilet and vanity on the east wall
Ba = dict(room="bath", **F)
box("ShowerGlass", (4.65, 1.1, 11.7), (1.9, 2.2, 0.01), M["glass"], "Glass", bevel=0, part="glass", side="I", room="bath")
box("ShowerPost", (3.72, 1.1, 11.7), (0.025, 2.2, 0.025), M["frame"], bevel=0, **Ba)
box("ShowerPipe", (5.62, 1.5, 12.3), (0.02, 1.2, 0.02), M["frame"], bevel=0, **Ba)
box("ShowerHead", (5.45, 2.15, 12.3), (0.25, 0.012, 0.25), M["frame"], bevel=0.003, **Ba)
box("ShowerArm", (5.55, 2.15, 12.3), (0.14, 0.012, 0.012), M["frame"], bevel=0, **Ba)
soft("Toilet", (5.3, 0.2, 10.9), (0.55, 0.4, 0.38), M["white"], r=0.06, **Ba)
soft("Cistern", (5.53, 0.6, 10.9), (0.18, 0.4, 0.38), M["white"], r=0.03, **Ba)
box("Vanity", (5.4, 0.5, 9.85), (0.45, 0.35, 0.9), M["walnut"], bevel=0.006, **Ba)
box("VanityTop", (5.4, 0.69, 9.85), (0.47, 0.03, 0.92), M["quartz"], bevel=0.004, **Ba)
soft("Basin", (5.38, 0.76, 9.85), (0.32, 0.11, 0.42), M["white"], r=0.04, **Ba)
box("BasinTap", (5.56, 0.9, 9.85), (0.02, 0.2, 0.02), M["frame"], bevel=0, **Ba)
box("Mirror", (5.62, 1.55, 9.85), (0.015, 0.8, 0.8), M["steel"], bevel=0, **Ba)
box("MirrorFrame", (5.615, 1.55, 9.85), (0.01, 0.84, 0.84), M["frame"], bevel=0, **Ba)
box("TowelRail", (3.68, 1.2, 11.2), (0.015, 0.015, 0.5), M["frame"], bevel=0, **Ba)
soft("Towel", (3.7, 1.0, 11.2), (0.03, 0.4, 0.3), M["towel"], r=0.01, **Ba)

# ---------- living: sofa under the window facing the media wall on the bathroom side, lounge chair, lamp
L = dict(room="living", **F)
box("Rug_living", (1.9, 0.008, 11.3), (2.6, 0.012, 2.4), M["rug"], bevel=0.004, **L)
sofa("Sofa", 0.75, 11.3, -math.pi / 2, w=2.2)                          # back to the west wall, facing east
box("CoffeeTable", (2.0, 0.34, 11.3), (0.55, 0.03, 1.1), M["walnut"], bevel=0.006, **L)
box("CoffeeFrame", (2.0, 0.16, 11.3), (0.4, 0.3, 0.9), M["frame"], bevel=0.004, **L)
box("Book1", (2.0, 0.37, 10.95), (0.2, 0.025, 0.28), M["book"], bevel=0.004, **L)
box("Tray", (2.0, 0.365, 11.6), (0.2, 0.015, 0.3), M["frame"], bevel=0.004, **L)
lounge_chair("Lounge", 2.7, 10.25, math.pi + 0.7)                      # by the bedroom wall, angled to the sofa
floor_lamp("FloorLamp", 0.6, 12.55)
box("Console", (3.32, 0.42, 11.8), (0.42, 0.28, 1.6), M["walnut"], bevel=0.008, **L)
box("ConsoleGap", (3.32, 0.42, 10.995), (0.4, 0.01, 0.005), M["frame"], bevel=0, **L)
box("TV", (3.5, 1.35, 11.8), (0.035, 0.72, 1.25), M["screen"], bevel=0.004, **L)
box("TVpanel", (3.48, 1.35, 11.8), (0.004, 0.66, 1.19), M["screen"], bevel=0, **L)
box("Speaker1", (3.32, 0.14, 11.15), (0.2, 0.28, 0.16), M["black"], bevel=0.008, **L)
box("Speaker2", (3.32, 0.14, 12.45), (0.2, 0.28, 0.16), M["black"], bevel=0.008, **L)
wall_art("Art_living", 1.9, 1.55, BZ + 0.08, 1.1, 0.8, 0, M["art2"])   # on the bedroom wall, above the lounge side
plant("Plant_living", 3.2, 12.55, s=1.3)

# ---------- kitchen + dining: matte black run down the east wall with the fridge at the south end, table for four, entry
K = dict(room="kitchen", **F)
box("KitchenBase", (5.4, 0.44, 14.6), (0.6, 0.88, 3.3), M["black"], bevel=0.005, **K)
for i, z in enumerate([13.5, 14.1, 14.7, 15.3, 15.9]):
    box(f"BaseGap_{i}", (5.095, 0.44, z), (0.01, 0.84, 0.004), M["frame"], bevel=0, **K)
box("KitchenTop", (5.385, 0.9, 14.6), (0.63, 0.03, 3.34), M["quartz"], bevel=0.006, **K)
box("Backsplash", (5.62, 1.28, 14.6), (0.02, 0.7, 3.3), M["quartz"], bevel=0, **K)
box("KitchenUpper", (5.525, 2.1, 14.6), (0.35, 0.7, 3.3), M["oak"], bevel=0.005, **K)
for i, z in enumerate([13.5, 14.1, 14.7, 15.3, 15.9]):
    box(f"UpperGap_{i}", (5.347, 2.1, z), (0.01, 0.66, 0.004), M["frame"], bevel=0, **K)
box("UpperLED", (5.5, 1.732, 14.6), (0.2, 0.01, 3.2), M["downlight"], bevel=0, part="light", room="kitchen")
box("Sink", (5.38, 0.905, 13.7), (0.4, 0.02, 0.55), M["steel"], bevel=0.005, **K)
box("Tap", (5.55, 1.06, 13.7), (0.018, 0.32, 0.018), M["frame"], bevel=0, **K)
box("TapSpout", (5.48, 1.21, 13.7), (0.16, 0.018, 0.018), M["frame"], bevel=0, **K)
box("Hob", (5.38, 0.912, 15.3), (0.5, 0.008, 0.6), M["screen"], bevel=0.003, **K)
box("Hood", (5.525, 1.66, 15.3), (0.35, 0.06, 0.7), M["steel"], bevel=0.006, **K)
box("Column", (5.37, 1.1, 16.8), (0.64, 2.2, 1.2), M["black"], bevel=0.006, **K)      # fridge + pantry
box("ColumnGap1", (5.047, 1.1, 16.8), (0.01, 2.16, 0.004), M["frame"], bevel=0, **K)
box("ColumnGap2", (5.047, 1.55, 16.8), (0.01, 0.004, 1.16), M["frame"], bevel=0, **K)
box("Board", (5.4, 0.93, 14.5), (0.22, 0.015, 0.32), M["walnut"], bevel=0.003, **K)
cyl("Bowl", (5.4, 0.96, 16.05), 0.13, 0.08, M["black"], r2=0.08, bevel=0.01, **K)
box("DiningTable", (2.6, 0.74, 15.0), (1.7, 0.04, 0.9), M["walnut"], bevel=0.006, **K)
for i, (dx, dz) in enumerate([(-0.55, -0.32), (0.55, -0.32), (-0.55, 0.32), (0.55, 0.32)]):
    box(f"DiningLeg{i}", (2.6 + dx, 0.36, 15.0 + dz), (0.04, 0.72, 0.04), M["frame"], bevel=0, **K)
for i, (dx, dz, r) in enumerate([(-0.42, -0.8, math.pi), (0.42, -0.8, math.pi), (-0.42, 0.8, 0.0), (0.42, 0.8, 0.0)]):
    chair(f"DiningChair{i}", 2.6 + dx, 15.0 + dz, r)
for i, z in enumerate([14.55, 15.45]):
    cyl(f"PendantCord_{i}", (2.6, 2.1, z), 0.003, 1.0, M["frame"], verts=6, **K)
    cyl(f"Pendant_{i}", (2.6, 1.55, z), 0.07, 0.24, M["pendant"], r2=0.09, part="light", room="kitchen")
box("Rug_entry", (0.95, 0.006, 16.7), (1.0, 0.012, 0.7), M["rug_dark"], bevel=0.004, **K)
box("Bench", (0.5, 0.22, 15.4), (0.4, 0.04, 1.0), M["walnut"], bevel=0.005, **K)
for i, z in enumerate([14.95, 15.85]):
    box(f"BenchLeg{i}", (0.5, 0.1, z), (0.34, 0.2, 0.03), M["frame"], bevel=0, **K)
box("CoatRail", (0.09, 1.7, 16.3), (0.03, 0.03, 0.5), M["frame"], bevel=0, **K)
for i in range(3):
    box(f"Hook{i}", (0.11, 1.65, 16.1 + i * 0.15), (0.05, 0.08, 0.012), M["frame"], bevel=0, **K)
wall_art("Art_kitchen", 0.09, 1.55, 13.6, 0.9, 1.2, math.pi / 2, M["art2"], room="kitchen")
plant("Plant_kitchen", 4.4, 17.05, s=1.2, room="kitchen")

# ----------------------------------------------------------------------------- lighting + renders (used by bake_lightmaps.py / render_views.py)
LIGHTS = [(f"Down_{i}", (x, 2.5, z), 18, (1.0, 0.92, 0.8)) for i, (x, z) in enumerate(DOWNLIGHTS)] + [
    ("Pendant_a", (2.6, 1.45, 14.55), 10), ("Pendant_b", (2.6, 1.45, 15.45), 10),
    ("FloorLamp", (1.2, 1.45, 12.55), 25),
    ("WallLamp_a", (0.4, 1.1, BZ - 0.2), 6), ("WallLamp_b", (3.0, 1.1, BZ - 0.2), 6),
    ("LED", (5.45, 1.7, 14.6), 14, (1.0, 0.95, 0.85), 1.6),
    ("Terrace", (3.5, 2.0, TZ - 0.3), 12),
]
mirror_x(W)   # the brochure has the column on the west: flip everything built above
_mx = lambda p: (W - p[0], p[1], p[2])
LIGHTS = [(n, _mx(p), *rest) for n, p, *rest in LIGHTS]
SUN_ROT = (50, 10, 35)            # afternoon sun from the east: through the living window and across the terrace
FILL_AT = (2.85, 9.0, 9.0)
_sw = {"E": "W", "W": "E"}
RENDER_VIEWS = [(k, _mx(p), _mx(t), f, "".join(_sw.get(c, c) for c in h)) for k, p, t, f, h in [
    ("whole",   (-16.0, 20.0, 30.0), (2.85, 0.4, 9.0), 30, "SW"),
    ("living",  (-8.0, 6.0, 11.3),   (2.0, 0.6, 11.3), 42, "W"),
    ("kitchen", (2.85, 7.0, 25.0),   (3.0, 0.7, 15.3), 40, "S"),
    ("bedroom", (1.8, 7.0, -1.5),    (1.8, 0.4, 8.4), 40, "N"),
    ("bath",    (-2.5, 8.5, 11.0),   (4.65, 0.6, 11.0), 40, "W"),
    ("terrace", (-7.0, 6.5, -6.0),   (2.85, 0.6, 3.2), 42, "NW"),
    ("service", (5.05, 4.5, -2.0),   (5.05, 0.7, 6.2), 40, "N"),
]]

export(OUT, blend=os.path.join(HERE, "b101.blend"))
