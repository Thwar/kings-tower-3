"""
Bloque B · Departamento 101 — builds the apartment in Blender and exports site/b101/apartment.glb.

Run headless:   python3 blender/build_b101.py [--blend]      (needs `pip install bpy`)

One-bedroom, 100.20 m² in total, on a long north-south strip (brochure page 9, "imagen referencial"). North up:
a large terrace at the top (solid parapets, a brick barbecue with twin chimneys and a concrete counter with a sink
along the east parapet, bronze sliding door — matched to a photo of the real terrace), a laundry cubicle in
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
from ktlib import (H, T, M, X, STYLE, mat, tmat, box, soft, cyl, floor_plane, build_walls, downlights, mirror_x,  # noqa: E402
                   plant, grass, sofa, lounge_chair, stool, chair, office_chair, floor_lamp, wall_art, export,
                   led_cove, gaming_desk, display_cabinet, vanity, glass_wardrobe, sectional, tv_wall, loft_coffee_table)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "b101", "apartment.glb" if STYLE == "bachelor" else f"apartment-{STYLE}.glb")
APT = dict(name="Bloque B · Dpto. 101", site="site/b101")

# ----------------------------------------------------------------------------- plan (metres; x east, z south, origin NW corner of the terrace)
W, TZ, D = 5.7, 6.8, 17.5           # width, terrace depth, total depth
BZ, CZ, BS = 9.65, 12.9, 9.2        # bedroom south wall, bathroom south wall, closet/bath partition
# terrace finishes from Thomas's photo: grey parapets, large light-grey tiles, bronze sliding door, blue-grey facade, brick barbecue
M["parapet"] = tmat("parapet", "plaster_ext", tint="#a6adb1")
M["facade"] = tmat("facade", "plaster_ext", tint="#e4eaee")
M["terrace_tile"] = tmat("terrace_tile", "tile", tint="#d4d6d7")
M["brick"] = tmat("brick", "brick")
M["counter"] = tmat("counter_concrete", "concrete", tint="#ecebe8")
M["anodized"] = mat("anodized", "#6f665d", 0.35, 0.8)
M["accent"] = tmat("accent_grey", "plaster", tint="#737c82")
M["led_warm"] = mat("led_warm", "#fff2c0", 0.5, emit="#ffc868", emit_strength=4.0)
M["futon"] = tmat("futon", "charcoal", tint="#2c2c2e", sheen=0.3)
M["proj_screen"] = mat("proj_screen", "#f3f3f1", 0.95)
M["headboard"] = tmat("headboard_leather", "leather", tint="#3a3a3c", clearcoat=0.2)
if STYLE == "bachelor":
    M["skirting"] = mat("skirting_wood", "#6e3b24", 0.5)
FLOOR = tmat("floor_tile", "tile", tint="#dcdcda") if STYLE == "bachelor" else M["wood"]
walls = [
    # terrace edge: solid 1.1 m parapets on three sides (the side ones 4 mm lower so the corner tops never coincide)
    (0, 0, W, 0, "N", dict(y1=1.1, ext=(True, True), mat=M["parapet"], noclad=True)),
    (0, 0, 0, TZ, "W", dict(y1=1.096, mat=M["parapet"], noclad=True)),
    (W, 0, W, 5.5, "E", dict(y1=1.096, mat=M["parapet"], noclad=True)),
    (W, 5.5, W, D, "E", dict(ext=(False, True))),
    # terrace / bedroom wall with the sliding door x 0.6–3.0 (two leaves, 2.3 m high)
    (0, TZ, 0.6, TZ, "N", dict(ext=(True, False))), (3.0, TZ, W, TZ, "N", dict(ext=(False, True))),
    (0.6, TZ, 3.0, TZ, "N", dict(y0=2.3, y1=H, noskirt=True)),
    # laundry cubicle on the terrace (x 4.4–5.7, z 5.5–6.8), door on its north side x 4.6–5.4
    (4.4, 5.5, 4.6, 5.5, "N", dict(ext=(True, False))), (5.4, 5.5, W, 5.5, "N", dict(ext=(False, True))),
    (4.6, 5.5, 5.4, 5.5, "N", dict(y0=2.1, y1=H, noskirt=True)),
    (4.4, 5.5, 4.4, TZ, "W", dict(**X)),
    # long outer wall of the bedroom, living and kitchen (solid: the photo shows plain wall beside the bed and the couch)
    (0, TZ, 0, D, "W", dict(ext=(False, True))),
    # the short fin wall at the end of the bed, where the bedroom meets the living (from the photo: ~1.2 m deep, 25 cm thick)
    (0, BZ, 1.2, BZ, "I", dict(ext=(True, False), t=0.25)),
    # south wall with the entrance x 0.5–1.4
    (0, D, 0.5, D, "S", dict(ext=(True, False))), (1.4, D, W, D, "S", dict(ext=(False, True))),
    (0.5, D, 1.4, D, "S", dict(y0=2.1, y1=H, noskirt=True)),
    # interior: the bedroom opens straight onto the living (no wall); the east column (closet door z 7.3–8.1, bath door z 10.0–10.8)
    (3.6, TZ, 3.6, 7.0, "I", dict(ext=(True, False))), (3.6, 7.7, 3.6, 10.0, "I", {}), (3.6, 10.8, 3.6, CZ, "I", dict(ext=(False, True))),
    (3.6, 7.0, 3.6, 7.7, "I", dict(y0=2.1, y1=H, noskirt=True)), (3.6, 10.0, 3.6, 10.8, "I", dict(y0=2.1, y1=H, noskirt=True)),
    (3.6, BS, W, BS, "I", dict(**X)),
    (3.6, CZ, W, CZ, "I", dict(**X)),
]
frames = [
    (0.6, TZ, 3.0, TZ, 0, 2.3, "N"),
]
DOWNLIGHTS = [(1.2, 7.6), (2.6, 8.8), (4.65, 8.0), (4.65, 10.2), (4.65, 12.0), (1.2, 10.6), (2.6, 12.2),
              (1.6, 14.2), (3.6, 14.2), (1.6, 16.4), (3.6, 16.4), (5.05, 6.15)]

# ----------------------------------------------------------------------------- structure
build_walls(walls, frames, frame_mat=M["anodized"], cladding={"N": M["facade"], "W": M["facade"]})
floor_plane("Floor_terrace_a", (0, 0, W, 5.5), M["terrace_tile"], room="terrace")
floor_plane("Floor_terrace_b", (0, 5.5, 4.4, TZ), M["terrace_tile"], room="terrace")
floor_plane("Floor_laundry", (4.4, 5.5, W, TZ), M["tile"], room="service")
floor_plane("Floor_bedroom", (0, TZ, 3.6, BZ), FLOOR, room="bedroom")
floor_plane("Floor_closet", (3.6, TZ, W, BS), FLOOR, room="bedroom")
floor_plane("Floor_bath", (3.6, BS, W, CZ), M["tile"], room="bath")
floor_plane("Floor_living", (0, BZ, 3.6, CZ), FLOOR, room="living")
floor_plane("Floor_kitchen", (0, CZ, W, D), FLOOR, room="kitchen")
box("Slab", (W / 2, -0.17, D / 2), (W + 0.8, 0.3, D + 0.8), M["concrete"], "Structure", bevel=0.02, part="slab")

box("Ceiling", (W / 2, H + 0.05, (TZ + D) / 2), (W + T, 0.1, D - TZ + T), M["ceiling"], "Ceiling", bevel=0, part="ceiling")
box("Ceiling_laundry", (5.05, H + 0.05, 6.08), (1.44, 0.1, 1.3), M["ceiling"], "Ceiling", bevel=0, part="ceiling")
downlights(DOWNLIGHTS)

# doors
# sliding door: two glass leaves in bronze frames; the operable one is slid open behind the fixed one (x 0.6–1.8 clear)
for nm, x0, x1, dz in [("DoorFixed", 1.8, 3.0, 0.03), ("DoorSlide", 1.72, 2.92, -0.03)]:
    zc = TZ + dz
    box(f"{nm}_glass", ((x0 + x1) / 2, 1.14, zc), (x1 - x0 - 0.1, 2.18, 0.012), M["glass"], "Glass", bevel=0, part="glass", side="I")
    for k, xx in enumerate([x0 + 0.03, x1 - 0.03]):
        box(f"{nm}_stile{k}", (xx, 1.14, zc), (0.06, 2.26, 0.05), M["anodized"], "Walls", bevel=0.003, part="frame", side="N")
    for k, yy in enumerate([0.04, 2.24]):
        box(f"{nm}_rail{k}", ((x0 + x1) / 2, yy, zc), (x1 - x0 - 0.12, 0.06, 0.05), M["anodized"], "Walls", bevel=0.003, part="frame", side="N")
box("DoorPull", (1.77, 1.1, TZ - 0.1), (0.03, 0.9, 0.03), M["steel"], "Furniture", bevel=0.004, part="furniture", room="terrace")
for k, yy in enumerate([0.75, 1.45]):
    box(f"DoorPullPost{k}", (1.77, yy, TZ - 0.07), (0.02, 0.02, 0.05), M["steel"], "Furniture", bevel=0, part="furniture", room="terrace")
box("Door_entry", (0.95, 1.05, D - 0.08), (0.9, 2.1, 0.05), M["black"], "Furniture", part="furniture", room="kitchen")
box("Door_handle", (1.28, 1.02, D - 0.13), (0.02, 0.3, 0.02), M["frame"], "Furniture", bevel=0, part="furniture", room="kitchen")
box("Door_closet", (4.07, 1.05, 7.72), (0.8, 2.1, 0.04), M["walnut"], "Furniture", part="furniture", room="bedroom")          # open into the closet, hinged at its south jamb
box("Door_bath", (3.53, 1.05, 10.4), (0.04, 2.1, 0.8), M["walnut"], "Furniture", part="furniture", room="bath")             # open flat on the living side
box("Door_laundry", (4.63, 1.05, 5.9), (0.04, 2.1, 0.8), M["walnut"], "Furniture", part="furniture", room="service")

F = dict(part="furniture")

# ---------- terrace, as in the photo: along the east parapet (x≈0 here, before the mirror) a brick barbecue with twin chimneys
#            and a long concrete counter with a sink running toward the door; the rest is open tiled floor. Light staging only:
#            a dining table and one olive in the far corner.
Tr = dict(room="terrace", **F)
BX = T / 2                     # inner face of the parapet
box("BBQ_base", (BX + 0.375, 0.475, 1.7), (0.75, 0.95, 1.6), M["brick"], bevel=0.01, **Tr)
box("BBQ_hearth", (BX + 0.4, 0.97, 1.7), (0.8, 0.04, 1.64), M["counter"], bevel=0.006, **Tr)
box("BBQ_back", (BX + 0.1, 1.5, 1.7), (0.2, 1.0, 1.6), M["brick"], bevel=0.008, **Tr)
for k, z in enumerate([0.99, 2.41]):
    box(f"BBQ_cheek{k}", (BX + 0.375, 1.5, z), (0.75, 1.0, 0.18), M["brick"], bevel=0.008, **Tr)
box("BBQ_lintel", (BX + 0.375, 2.15, 1.7), (0.75, 0.3, 1.6), M["brick"], bevel=0.008, **Tr)
box("BBQ_grill", (BX + 0.45, 1.25, 1.7), (0.5, 0.015, 1.2), M["steel"], bevel=0, **Tr)
box("BBQ_soot", (BX + 0.205, 1.5, 1.7), (0.012, 0.9, 1.2), M["black"], bevel=0, **Tr)
for k, (z0, z1) in enumerate([(1.0, 1.6), (1.8, 2.4)]):
    zc = (z0 + z1) / 2
    box(f"Chimney{k}", (BX + 0.3, 2.95, zc), (0.6, 1.3, z1 - z0), M["brick"], bevel=0.008, **Tr)
    for j, (dx, dz) in enumerate([(-0.24, -0.24), (0.24, -0.24), (-0.24, 0.24), (0.24, 0.24)]):
        box(f"ChimneyPier{k}{j}", (BX + 0.3 + dx, 3.65, zc + dz), (0.1, 0.1, 0.1), M["brick"], bevel=0, **Tr)
    box(f"ChimneyCap{k}", (BX + 0.3, 3.73, zc), (0.72, 0.06, z1 - z0 + 0.12), M["counter"], bevel=0.006, **Tr)
# counter with open shelves below and a sink near the door end
box("Counter_top", (BX + 0.33, 0.89, 3.9), (0.66, 0.06, 2.6), M["counter"], bevel=0.006, **Tr)
box("Counter_shelf", (BX + 0.31, 0.12, 3.9), (0.6, 0.05, 2.52), M["counter"], bevel=0.004, **Tr)
for k, z in enumerate([2.64, 3.9, 5.16]):
    box(f"Counter_leg{k}", (BX + 0.31, 0.49, z), (0.6, 0.72, 0.07), M["counter"], bevel=0.004, **Tr)
box("Counter_sink", (BX + 0.34, 0.905, 4.6), (0.42, 0.04, 0.5), M["steel"], bevel=0.006, **Tr)
box("Counter_tap", (BX + 0.08, 1.06, 4.6), (0.02, 0.28, 0.02), M["frame"], bevel=0, **Tr)
box("Counter_spout", (BX + 0.15, 1.19, 4.6), (0.16, 0.02, 0.02), M["frame"], bevel=0, **Tr)
# light staging
box("TerraceTable", (2.95, 0.74, 2.9), (1.8, 0.04, 0.9), M["walnut"], bevel=0.006, **Tr)
for i, (dx, dz) in enumerate([(-0.6, -0.5), (0.6, -0.5), (-0.6, 0.5), (0.6, 0.5)]):
    box(f"TerraceTableLeg{i}", (2.95 + dx, 0.36, 2.9 + dz * 0.75), (0.04, 0.72, 0.04), M["frame"], bevel=0, **Tr)
for i, (dx, dz, r) in enumerate([(-0.45, -0.8, math.pi), (0.45, -0.8, math.pi), (-0.45, 0.8, 0.0), (0.45, 0.8, 0.0)]):
    chair(f"TerraceChair{i}", 2.95 + dx, 2.9 + dz, r, room="terrace", fabric=M["linen"])
plant("Olive_1", 5.2, 0.55, s=1.6, pot="black", room="terrace", leaves=48)
# small black wall light on the west parapet (x = W here), as in the photo
box("WallLight", (W - T / 2 - 0.05, 0.85, 3.2), (0.1, 0.12, 0.1), M["black"], bevel=0.006, part="light", room="terrace")
box("WallLightGlow", (W - T / 2 - 0.106, 0.83, 3.2), (0.012, 0.06, 0.07), M["downlight"], bevel=0, part="light", room="terrace")

# ---------- laundry cubicle
Sv = dict(room="service", **F)
box("Washer", (5.3, 0.425, 6.4), (0.6, 0.85, 0.6), M["white"], bevel=0.015, **Sv)
cyl("WasherDoor", (5.3, 0.45, 6.09), 0.19, 0.02, M["screen"], rot=(math.radians(90), 0, 0), **Sv)
box("Dryer", (5.3, 1.3, 6.4), (0.6, 0.85, 0.6), M["white"], bevel=0.015, **Sv)
cyl("DryerDoor", (5.3, 1.32, 6.09), 0.19, 0.02, M["screen"], rot=(math.radians(90), 0, 0), **Sv)
box("LaundryShelf", (4.7, 1.5, 6.4), (0.5, 0.025, 0.35), M["oak"], bevel=0.004, **Sv)
box("Basket", (4.7, 0.16, 6.4), (0.4, 0.32, 0.4), M["black"], bevel=0.01, **Sv)

if STYLE == "bachelor":
    # ---------- bedroom, as in the photo: grey accent wall between the door wall and the fin with a warm LED cove along the
    #            ceiling, a black box bed with a tufted black leather headboard, no nightstands
    B = dict(room="bedroom", **F)
    FIN0 = BZ - 0.125                                   # face of the fin
    box("AccentWall", (0.08, (H - 0.02) / 2, (TZ + T / 2 + FIN0) / 2), (0.02, H - 0.02, FIN0 - TZ - T / 2), M["accent"], "Walls", bevel=0, part="wall", side="I", room="bedroom")
    box("LEDCove", (0.14, H - 0.02, (TZ + T / 2 + FIN0) / 2), (0.1, 0.02, FIN0 - TZ - T / 2 - 0.04), M["led_warm"], bevel=0, part="light", room="bedroom")
    box("LEDCoveLip", (0.2, H - 0.06, (TZ + T / 2 + FIN0) / 2), (0.02, 0.1, FIN0 - TZ - T / 2 - 0.04), M["ceiling"], bevel=0, part="furniture", room="bedroom")
    BEDZ = 8.15
    box("BedBase", (1.14, 0.22, BEDZ), (1.95, 0.3, 1.45), M["black"], bevel=0.01, **B)
    for j, (dx, dz) in enumerate([(-0.85, -0.62), (0.85, -0.62), (-0.85, 0.62), (0.85, 0.62)]):
        cyl(f"BedLeg{j}", (1.14 + dx, 0.035, BEDZ + dz), 0.025, 0.07, M["frame"], verts=10, **B)
    soft("Mattress", (1.15, 0.5, BEDZ), (1.9, 0.26, 1.4), M["linen"], r=0.05, **B)
    box("Headboard", (0.12, 0.8, BEDZ), (0.06, 1.0, 1.5), M["headboard"], bevel=0.01, **B)
    for r, y in enumerate([0.95, 1.2]):
        for c in range(5):
            soft(f"HeadTuft{r}{c}", (0.165, y, BEDZ - 0.6 + c * 0.3), (0.04, 0.23, 0.28), M["headboard"], r=0.015, **B)
    soft("PillowN", (0.4, 0.69, BEDZ - 0.33), (0.36, 0.14, 0.6), M["linen"], r=0.05, **B)
    soft("PillowS", (0.4, 0.69, BEDZ + 0.33), (0.36, 0.14, 0.6), M["linen"], r=0.05, **B)
    # closet room: wardrobe wall on the east, shelves on the north
    box("Wardrobe", (5.4, 1.15, 8.0), (0.6, 2.3, 2.2), M["black"], bevel=0.006, **B)
    for i, z in enumerate([7.2, 7.7, 8.2, 8.7]):
        box(f"WardrobeGap_{i}", (5.097, 1.15, z), (0.01, 2.26, 0.004), M["frame"], bevel=0, **B)
    for i, y in enumerate([0.4, 0.9, 1.4, 1.9]):
        box(f"ClosetShelf_{i}", (4.35, y, TZ + 0.25), (1.3, 0.025, 0.4), M["oak"], bevel=0.004, **B)
    box("ClosetBox1", (4.1, 1.53, TZ + 0.25), (0.35, 0.24, 0.35), M["black"], bevel=0.01, **B)
    box("ClosetBox2", (4.6, 1.03, TZ + 0.25), (0.35, 0.24, 0.35), M["book"], bevel=0.01, **B)

# ---------- TV wall facing the bed (both schemes): floating white console 150 × 25 cm with open cubbies and a warm LED strip
#            underneath, a 55" TV above it, a PS5 with its controller and a laptop on top
Tv = dict(room="bedroom", **F)
CF = 3.6 - T / 2                                  # column face
CZ0, CZ1 = 7.8, 9.3                               # console extent along the wall
CX = CF - 0.125
box("TVConsoleTop", (CX, 0.615, (CZ0 + CZ1) / 2), (0.25, 0.03, CZ1 - CZ0), M["white"], bevel=0.004, **Tv)
box("TVConsoleBottom", (CX, 0.365, (CZ0 + CZ1) / 2), (0.25, 0.03, CZ1 - CZ0), M["white"], bevel=0.004, **Tv)
for k, z in enumerate([CZ0 + 0.015, 8.45, 8.9, CZ1 - 0.015]):
    box(f"TVConsoleDiv{k}", (CX, 0.49, z), (0.25, 0.22, 0.03), M["white"], bevel=0.003, **Tv)
box("TVConsoleDoor", (CF - 0.245, 0.49, (CZ0 + 8.45) / 2), (0.012, 0.22, 8.45 - CZ0 - 0.04), M["white"], bevel=0.003, **Tv)   # closed section on the left
box("TVConsoleLED", (CF - 0.12, 0.345, (CZ0 + CZ1) / 2), (0.18, 0.01, CZ1 - CZ0 - 0.06), M["led_warm"], bevel=0, part="light", room="bedroom")
box("BluRay", (CX + 0.02, 0.42, 8.68), (0.2, 0.06, 0.34), M["black"], bevel=0.004, **Tv)
box("BooksConsole", (CX + 0.02, 0.41, 9.1), (0.2, 0.05, 0.3), M["book"], bevel=0.004, **Tv)
TVZ = 8.4
box("BedTV", (CF - 0.015, 1.42, TVZ), (0.03, 0.70, 1.23), M["screen"], bevel=0.004, **Tv)
box("BedTVpanel", (CF - 0.032, 1.42, TVZ), (0.004, 0.66, 1.19), M["screen"], bevel=0, **Tv)
box("PS5", (CX + 0.01, 0.83, 9.08), (0.26, 0.39, 0.1), M["white"], bevel=0.02, segments=4, **Tv)
box("PS5core", (CX + 0.01, 0.82, 9.08), (0.27, 0.36, 0.04), M["black"], bevel=0.01, **Tv)
soft("Controller", (CX - 0.02, 0.655, 8.85), (0.1, 0.05, 0.16), M["white"], r=0.02, **Tv)
box("LaptopBase", (CX - 0.02, 0.638, 8.1), (0.22, 0.015, 0.31), M["steel"], bevel=0.004, **Tv)
box("LaptopScreen", (CF - 0.03, 0.75, 8.1), (0.012, 0.21, 0.31), M["steel"], bevel=0.003, **Tv)
box("LaptopDisplay", (CF - 0.037, 0.75, 8.1), (0.003, 0.19, 0.29), M["tv"], bevel=0, part="light", room="bedroom")

def projector_corner(prefix, zc, width=2.0, room="living"):
    """living-room cinema: matte projection screen (16:9) on the long outer wall, black case above it, a low media bench with a
    soundbar below, and a ceiling-mounted projector above the couch about 2.9 m back from the screen"""
    Pj = dict(part="furniture", room=room)
    h = width * 9 / 16
    yc = 0.95 + h / 2
    box(f"{prefix}Border", (0.082, yc, zc), (0.006, h + 0.08, width + 0.08), M["black"], bevel=0, **Pj)
    box(f"{prefix}Screen", (0.09, yc, zc), (0.01, h, width), M["proj_screen"], bevel=0, **Pj)
    box(f"{prefix}Case", (0.13, yc + h / 2 + 0.1, zc), (0.12, 0.1, width + 0.2), M["black"], bevel=0.01, **Pj)
    box(f"{prefix}Bench", (0.26, 0.2, zc), (0.38, 0.4, 1.8), M["walnut"], bevel=0.008, **Pj)
    box(f"{prefix}BenchGap", (0.452, 0.2, zc), (0.005, 0.36, 0.005), M["frame"], bevel=0, **Pj)
    box(f"{prefix}Soundbar", (0.3, 0.44, zc), (0.1, 0.07, 0.9), M["black"], bevel=0.01, **Pj)
    px = 3.0                                      # over the couch
    cyl(f"{prefix}Pole", (px, H - 0.14, zc), 0.015, 0.28, M["frame"], verts=8, **Pj)
    box(f"{prefix}Projector", (px, H - 0.33, zc), (0.3, 0.1, 0.28), M["white"], bevel=0.02, segments=4, **Pj)
    cyl(f"{prefix}Lens", (px - 0.16, H - 0.33, zc), 0.035, 0.03, M["screen"], rot=(0, math.radians(90), 0), **Pj)


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

if STYLE == "bachelor":
    # ---------- living: the couch backs onto the closet/bath column just past the bathroom door, facing a projection screen on
    #            the long outer wall with the projector on the ceiling above the couch (the TV is in the bedroom, facing the bed)
    L = dict(room="living", **F)
    LZ = 11.85
    box("Rug_living", (1.8, 0.008, LZ), (2.6, 0.012, 2.0), M["rug"], bevel=0.004, **L)
    sofa("Sofa", 3.04, LZ, math.pi / 2, w=1.9, fabric=M["futon"])          # back to the column, facing the TV
    box("CoffeeTable", (1.75, 0.34, LZ), (0.55, 0.03, 1.1), M["walnut"], bevel=0.006, **L)
    box("CoffeeFrame", (1.75, 0.16, LZ), (0.4, 0.3, 0.9), M["frame"], bevel=0.004, **L)
    box("Book1", (1.75, 0.37, LZ - 0.35), (0.2, 0.025, 0.28), M["book"], bevel=0.004, **L)
    box("Tray", (1.75, 0.365, LZ + 0.3), (0.2, 0.015, 0.3), M["frame"], bevel=0.004, **L)
    floor_lamp("FloorLamp", 0.35, 10.2)
    projector_corner("Cinema", LZ, width=2.0)

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

plant("Plant_kitchen", 4.4, 17.05, s=1.2, room="kitchen")

if STYLE == "loft":
    # ---------- loft bedroom (open to the living): bed in grey, lit vanity and glass wardrobe in the closet room
    B = dict(room="bedroom", **F)
    led_cove("Cove_bedliving", (0, TZ, 3.6, CZ), room="bedroom")
    led_cove("Cove_kitchen", (0, CZ, W, D), room="kitchen")
    box("Rug_bedroom", (2.7, 0.008, 8.2), (1.2, 0.012, 2.3), M["rug_dark"], bevel=0.004, **B)
    box("BedPlatform", (1.15, 0.13, 8.2), (2.2, 0.24, 2.0), M["black"], bevel=0.01, **B)
    soft("Mattress", (1.15, 0.36, 8.2), (2.0, 0.24, 1.6), M["linen"], r=0.05, **B)
    soft("Duvet", (1.5, 0.5, 8.2), (1.25, 0.07, 1.64), M["charcoal"], r=0.03, **B)
    box("Headboard", (0.09, 0.65, 8.2), (0.06, 1.1, 2.4), M["charcoal"], bevel=0.01, **B)
    soft("PillowN", (0.38, 0.55, 7.8), (0.42, 0.16, 0.68), M["linen"], r=0.05, **B)
    soft("PillowS", (0.38, 0.55, 8.6), (0.42, 0.16, 0.68), M["linen"], r=0.05, **B)
    for i, z in enumerate([7.04, 9.36]):   # slim nightstands: the fin wall stands just past the south one
        box(f"Nightstand_{i}", (0.3, 0.45, z), (0.38, 0.12, 0.3), M["walnut"], bevel=0.006, **B)
        box(f"WallLampArm_{i}", (0.12, 1.15, z), (0.14, 0.02, 0.02), M["frame"], bevel=0, **B)
        cyl(f"WallLamp_{i}", (0.22, 1.1, z), 0.05, 0.12, M["lamp"], r2=0.06, part="light", room="bedroom")
    wall_art("Art_bedroom", 0.09, 1.75, 8.2, 1.4, 0.55, math.pi / 2, M["art2"], room="bedroom")
    plant("Plant_bedroom", 2.95, 9.45, s=1.1, room="bedroom")
    glass_wardrobe("Wardrobe", 5.33, 8.0, -math.pi / 2, w=2.2)
    vanity("Vanity", 4.4, 8.85, math.pi)
    for i, y in enumerate([1.5, 1.95]):
        box(f"ClosetShelf_{i}", (4.35, y, TZ + 0.25), (1.3, 0.025, 0.4), M["oak"], bevel=0.004, **B)
    # ---------- loft living: sectional backed onto the column past the bath door, fur rug, media wall on the long outer wall
    L = dict(room="living", **F)
    box("Rug_living", (1.8, 0.008, 11.85), (2.4, 0.012, 2.0), M["rug"], bevel=0.004, **L)
    sectional("Sofa", 3.04, 11.85, math.pi / 2, w=2.0)
    loft_coffee_table("CoffeeTable", 1.7, 11.85)
    display_cabinet("Cabinet", 0.27, 10.45, -math.pi / 2)
    projector_corner("Cinema", 11.95, width=1.8)
    floor_lamp("FloorLamp", 0.35, 12.8)
    # gaming desk against the west wall of the dining zone (the kitchen art comes off that wall)
    gaming_desk("Desk", 0.45, 13.75, -math.pi / 2, room="kitchen")

# ----------------------------------------------------------------------------- lighting + renders (used by bake_lightmaps.py / render_views.py)
LIGHTS = [(f"Down_{i}", (x, 2.5, z), 18, (1.0, 0.92, 0.8)) for i, (x, z) in enumerate(DOWNLIGHTS)] + [
    ("Pendant_a", (2.6, 1.45, 14.55), 10), ("Pendant_b", (2.6, 1.45, 15.45), 10),
    ("FloorLamp", (0.95, 1.45, 10.2), 25),
    ("BedLED", (0.3, 2.45, 8.2), 10, (1.0, 0.85, 0.55), 1.2),
    ("LED", (5.45, 1.7, 14.6), 14, (1.0, 0.95, 0.85), 1.6),
    ("Terrace", (W - 0.4, 0.9, 3.2), 12),
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
