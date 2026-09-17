"""
Casa de dos plantas (+ desván) — builds the house in Blender and exports site/casa/apartment.glb.

Run headless:   python3 blender/build_casa.py [--blend]      (needs `pip install bpy`)

From the architect's set (esc. 1:100): PLANTA BAJA — comedor + living down the west side (3.09 × 7.85, the living with a
chamfered bay at the SW), cocina 3.2 × 2.6 at the north, hall 3.21 × 2.9 with a U-shaped stair, estudio 2.67 × 4 on the
east, patio de servicio 3 × 3 in the NE corner, a w.c. under the stair, front porch on columns to the south.
PLANTA ALTA — dormitorio NW 4.09 × 3.44, dormitorio SW, baño over the hall's north end, dormitorio padres 6.2 deep
down the east side, hall with the stair well, balcón over the porch. The north lean-to (comedor/cocina) is single
storey with a 2.7 → 3.1 m sloping ceiling (corte C-C'). The attic under the tiled gable roof is storage, with the
dormer seen on the south elevation.

Levels: 0 = planta baja (y 0 → 2.7), 1 = planta alta (y 2.95 → 5.55), 2 = desván (y 5.8 →). Every object carries `level`.
x east, z south, origin = NW corner of the comedor.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ktlib import (T, M, X, STYLE, mat, tmat, box, soft, cyl, sphere, floor_plane, build_walls, downlights,  # noqa: E402
                   plant, grass, sofa, lounge_chair, stool, chair, office_chair, floor_lamp, wall_art, export,
                   prism, roof_slab, stair_flight, railing, column, rnd, set_level, write_plan, wood_railing)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "casa", "apartment.glb" if STYLE == "bachelor" else f"apartment-{STYLE}.glb")
APT = dict(name="Casa · 2 plantas", site="site/casa")

M["roof"] = mat("roof_tile", "#9b4f30", 0.85)
M["stone"] = tmat("stone_band", "paving", tint="#b8a58c")
M["stair"] = M["walnut"]
# the real house: terracotta ground floor, salmon upper floor, white bands and columns, stone base, wooden windows, iron railing
M["terracotta"] = tmat("terracotta", "plaster_ext", tint="#c9633f")
M["salmon"] = tmat("salmon", "plaster_ext", tint="#f0a888")
M["band"] = mat("band", "#f2efe8", 0.7)
M["wood_frame"] = tmat("wood_frame", "walnut", tint="#7a4a2a", clearcoat=0.3)
M["iron"] = mat("iron", "#dcdcdc", 0.45, 0.6)
M["bar_tile"] = tmat("bar_tile", "tile", tint="#e8e2d6")
M["mahogany"] = tmat("mahogany", "walnut", tint="#5a2a1a", clearcoat=0.4)
M["stair"] = tmat("stair_tile", "tile", tint="#d8c8a6")            # the lower flight is tiled, beige
M["plaster"] = tmat("plaster_cream", "plaster", tint="#ecdfc4")     # cream interior walls
CLAD0 = {s_: M["terracotta"] for s_ in "NSEW"}
CLAD1 = {s_: M["salmon"] for s_ in "NSEW"}

# ----------------------------------------------------------------------------- dimensions (metres)
W = 9.8                       # overall width
H0, Y1, H1, Y2 = 2.7, 2.95, 2.6, 5.8   # ground ceiling, upper floor level, upper ceiling, attic floor level
ZN1 = 2.0                     # the upper floor starts here (the 2 m strip north of it is single-storey lean-to)
ZS = 9.06                     # south face of the upper floor / porch edge
XL = 3.16                     # comedor-living east wall centreline
XK = 6.51                     # cocina / hall east wall centreline
ZC = 2.74                     # cocina south wall (hall north wall)
WC_X0, WC_X1, WC_Z0, WC_Z1, WC_DROP = 4.16, XK, 5.71, 7.0, 0.45
ST_X0, ST_X1, ST_Z0, ST_Z1, ST_N = 4.9, 6.44, 4.2, 6.95, 14        # the main flight: x band, bottom z (clear of the estudio door), top z, risers


def floorp(name, rect, material, y, level, room):
    x1, z1, x2, z2 = rect
    floor_plane(name, rect, material, y=y, room=room, level=level)


# ============================================================================= PLANTA BAJA (level 0)
walls0 = [
    # north: comedor + cocina (lean-to), patio low wall
    (0, 0, 0.8, 0, "N", dict(ext=(True, False))), (2.4, 0, 4.0, 0, "N", {}), (5.8, 0, XK, 0, "N", dict(ext=(False, True))),
    (0.8, 0, 2.4, 0, "N", dict(y0=0, y1=1.0)), (0.8, 0, 2.4, 0, "N", dict(y0=2.2, y1=H0, noskirt=True)), (0.8, 0, 2.4, 0, "N", dict(y0=1.0, y1=2.2, glass=True)),
    (4.0, 0, 5.8, 0, "N", dict(y0=0, y1=1.0)), (4.0, 0, 5.8, 0, "N", dict(y0=2.2, y1=H0, noskirt=True)), (4.0, 0, 5.8, 0, "N", dict(y0=1.0, y1=2.2, glass=True)),
    (XK, 0, W, 0, "N", dict(y0=0, y1=2.0, ext=(True, True), noclad=True)),         # patio wall
    (W, 0, W, ZC, "E", dict(y0=0, y1=2.0, ext=(True, True), noclad=True)),
    # east: estudio
    (W, ZC, W, 4.0, "E", dict(ext=(True, False))), (W, 6.0, W, 7.14, "E", dict(ext=(False, True))),
    (W, 4.0, W, 6.0, "E", dict(y0=0, y1=1.0)), (W, 4.0, W, 6.0, "E", dict(y0=2.2, y1=H0, noskirt=True)), (W, 4.0, W, 6.0, "E", dict(y0=1.0, y1=2.2, glass=True)),
    # south: estudio, w.c., front door, living (with chamfered bay)
    (XK, 7.14, 7.5, 7.14, "S", dict(ext=(True, False))), (9.0, 7.14, W, 7.14, "S", dict(ext=(False, True))),
    (7.5, 7.14, 9.0, 7.14, "S", dict(y0=0, y1=1.0)), (7.5, 7.14, 9.0, 7.14, "S", dict(y0=2.2, y1=H0, noskirt=True)), (7.5, 7.14, 9.0, 7.14, "S", dict(y0=1.0, y1=2.2, glass=True)),
    (4.16, 7.0, XK, 7.0, "S", dict(ext=(True, True))),                              # w.c. south wall
    (XL, 7.0, 4.16, 7.0, "S", dict(y0=2.1, y1=H0, noskirt=True)),                   # front door head (door x 3.23–4.16 → the passage)
    (0, 7.85, 0.45, 7.85, "S", dict(ext=(True, False))), (2.75, 7.85, XL, 7.85, "S", dict(ext=(False, True))),
    # bay window: three lights (angled left, centre, angled right) projecting 0.45 m beyond the south wall
    *[(x1, z1, x2, z2, "S", dict(**o)) for (x1, z1, x2, z2) in [(0.45, 7.85, 0.9, 8.3), (0.9, 8.3, 2.3, 8.3), (2.3, 8.3, 2.75, 7.85)]
      for o in (dict(y0=0, y1=0.9), dict(y0=2.2, y1=H0, noskirt=True), dict(y0=0.9, y1=2.2, glass=True))],
    # west: comedor + living
    (0, 0, 0, 4.5, "W", dict(ext=(True, False))), (0, 6.5, 0, 7.85, "W", dict(ext=(False, True))),
    (0, 4.5, 0, 6.5, "W", dict(y0=0, y1=0.9)), (0, 4.5, 0, 6.5, "W", dict(y0=2.2, y1=H0, noskirt=True)), (0, 4.5, 0, 6.5, "W", dict(y0=0.9, y1=2.2, glass=True)),
    # patio / house boundary
    (XK, 0, XK, 1.2, "E", dict(ext=(True, False))), (XK, 2.0, XK, ZC, "E", dict(ext=(False, True))),      # cocina east wall, door to the patio z 1.2–2.0
    (XK, 1.2, XK, 2.0, "E", dict(y0=2.1, y1=H0, noskirt=True)),
    (XK, ZC, 6.6, ZC, "N", dict(ext=(True, False))), (7.4, ZC, W, ZC, "N", dict(ext=(False, True))),      # estudio north wall, door to the patio x 6.6–7.4
    (6.6, ZC, 7.4, ZC, "N", dict(y0=2.1, y1=H0, noskirt=True)),
    # interior
    (XL, 0, XL, ZC, "I", dict(ext=(True, True))), (XL, 6.9, XL, 7.85, "I", dict(ext=(False, True))),   # comedor | cocina; the living is open to the hall, short return by the front door
    # cocina | hall: a tiled bar (low wall x 3.6–5.6, open above it) and the walkway into the kitchen x 5.6–6.4
    (XL, ZC, 3.6, ZC, "I", dict(ext=(True, False))), (6.4, ZC, XK, ZC, "I", dict(ext=(False, True))),
    (3.6, ZC, 5.6, ZC, "I", dict(y0=0, y1=1.05, mat=M["bar_tile"])), (3.6, ZC, 6.4, ZC, "I", dict(y0=2.3, y1=H0, noskirt=True)),
    (XK, ZC, XK, 2.88, "I", dict(ext=(True, False))), (XK, 3.68, XK, 7.14, "I", dict(ext=(False, True))),  # hall | estudio, door z 2.88–3.68
    (XK, 2.88, XK, 3.68, "I", dict(y0=2.1, y1=H0, noskirt=True)),
    (4.16, 5.71, XK, 5.71, "I", dict(**X)),                                                              # w.c. north wall (under the stair)
    (4.16, 5.71, 4.16, 5.9, "I", dict(ext=(True, False))), (4.16, 6.6, 4.16, 7.0, "I", dict(ext=(False, True))),   # w.c. west wall, door z 5.9–6.6
    (4.16, 5.9, 4.16, 6.6, "I", dict(y0=2.1, y1=H0, noskirt=True)),
]
frames0 = [
    (0.8, 0, 2.4, 0, 1.0, 2.2, "N"), (4.0, 0, 5.8, 0, 1.0, 2.2, "N"),
    (W, 4.0, W, 6.0, 1.0, 2.2, "E"), (7.5, 7.14, 9.0, 7.14, 1.0, 2.2, "S"),
    (0.45, 7.85, 0.9, 8.3, 0.9, 2.2, "S"), (0.9, 8.3, 2.3, 8.3, 0.9, 2.2, "S"), (2.3, 8.3, 2.75, 7.85, 0.9, 2.2, "S"), (0, 4.5, 0, 6.5, 0.9, 2.2, "W"),
]
set_level(0, 0.0)
build_walls(walls0, frames0, height=H0, frame_mat=M["wood_frame"], cladding=CLAD0)

floorp("Floor_comedor", (0, 0, XL, 7.85), M["wood"], 0, 0, "living")
prism("Floor_bay", [(0.45, 7.85), (2.75, 7.85), (2.3, 8.3), (0.9, 8.3)], 0.0, 0.002, M["wood"], "Floors", part="floor", room="living")
for k, (x, z) in enumerate([(0.45, 7.85), (0.9, 8.3), (2.3, 8.3), (2.75, 7.85)]):
    box(f"BayPost{k}", (x, H0 / 2, z), (T + 0.03, H0, T + 0.03), M["plaster"], "Walls", bevel=0.004, part="wall", side="S")
floorp("Floor_cocina", (XL, 0, XK, ZC), M["tile"], 0, 0, "kitchen")
floorp("Floor_hall_a", (XL, ZC, XK, WC_Z0), M["tile"], 0, 0, "hall")
floorp("Floor_hall_b", (XL, WC_Z0, WC_X0, 7.0), M["tile"], 0, 0, "hall")
floorp("Floor_wc", (WC_X0, WC_Z0, WC_X1, WC_Z1), M["tile"], -WC_DROP, 0, "wc")
floorp("Floor_estudio", (XK, ZC, W, 7.14), M["wood"], 0, 0, "estudio")
floorp("Floor_patio", (XK, 0, W, ZC), M["stone"], 0, 0, "patio")
floorp("Floor_porch", (XL, 7.85, W, ZS), M["stone"], 0, 0, "porch")
floorp("Floor_porch_b", (XL, 7.0, XK, 7.85), M["stone"], 0, 0, "porch")
floorp("Floor_porch_c", (0, 7.85, XL, ZS), M["stone"], 0, 0, "porch")
# ground slab in pieces around the w.c., whose floor is sunk 0.45 m (two steps down) to clear the stair above it
for i, (x1, z1, x2, z2) in enumerate([(-0.4, -0.4, WC_X0, ZS + 0.4), (WC_X1, -0.4, W + 0.4, ZS + 0.4), (WC_X0, -0.4, WC_X1, WC_Z0), (WC_X0, WC_Z1, WC_X1, ZS + 0.4)]):
    box(f"Slab_{i}", ((x1 + x2) / 2, -0.17, (z1 + z2) / 2), (x2 - x1, 0.3, z2 - z1), M["concrete"], "Structure", bevel=0, part="slab", level=0)
box("Slab_wc", ((WC_X0 + WC_X1) / 2, -WC_DROP - 0.17, (WC_Z0 + WC_Z1) / 2), (WC_X1 - WC_X0, 0.3, WC_Z1 - WC_Z0), M["concrete"], "Structure", bevel=0, part="slab", level=0)
for i, (cx, cz, sx, sz) in enumerate([((WC_X0 + WC_X1) / 2, WC_Z0, WC_X1 - WC_X0 + T, T), ((WC_X0 + WC_X1) / 2, WC_Z1, WC_X1 - WC_X0 + T, T),
                                      (WC_X0, (WC_Z0 + WC_Z1) / 2, T, WC_Z1 - WC_Z0), (WC_X1, (WC_Z0 + WC_Z1) / 2, T, WC_Z1 - WC_Z0)]):
    box(f"WcWallLow_{i}", (cx, -WC_DROP / 2 - 0.02, cz), (sx, WC_DROP - 0.04, sz), M["plaster"], "Walls", bevel=0, part="wall", side="I", level=0)
wood_railing("Rail_wc", 4.16, 5.72, 4.16, 6.78, -WC_DROP, h=0.9, material=M["mahogany"], room="wc", newels=(False, True))   # along the steps' open side
box("WcStep1", (4.48, -0.11, 6.25), (0.5, 0.22, 1.1), M["stone"], "Structure", bevel=0.004, part="slab", level=0)
box("WcStep2", (4.25, -0.34, 6.25), (0.16, 0.22, 1.1), M["stone"], "Structure", bevel=0.004, part="slab", level=0)
box("BarTop", (4.6, 1.08, ZC), (2.1, 0.05, 0.55), M["quartz"], "Furniture", bevel=0.004, part="furniture", room="kitchen", level=0)
box("BarPillar", (5.6, H0 / 2, ZC), (0.3, H0, 0.3), M["plaster"], "Walls", bevel=0.004, part="wall", side="I", level=0)
box("BarFront", (4.6, 0.52, ZC + T / 2 + 0.011), (2.0, 1.02, 0.02), M["bar_tile"], "Furniture", bevel=0, part="furniture", room="kitchen", level=0)
box("BarBeam", (5.0, 2.3 - 0.075, ZC), (2.9, 0.15, T + 0.06), M["band"], "Walls", bevel=0.004, part="wall", side="I", level=0)
# ground ceilings: flat over hall/estudio/w.c., the lean-to slope over comedor + cocina (2.7 at the north wall → 3.1 at z=2)
box("Ceiling0_main", ((XL + W) / 2, H0 + 0.05, (ZC + 7.14) / 2), (W - XL + T, 0.1, 7.14 - ZC + T), M["ceiling"], "Ceiling", bevel=0, part="ceiling", level=0)
box("Ceiling0_living", (XL / 2, H0 + 0.05, (ZN1 + 8.3) / 2), (XL + T, 0.1, 8.3 - ZN1 + T), M["ceiling"], "Ceiling", bevel=0, part="ceiling", level=0)
roof_slab("Ceiling0_leanto", -0.3, XK + 0.1, -0.3, ZN1, H0 - 0.1, 3.1, M["ceiling"], thickness=0.08, part="ceiling", level=0)
roof_slab("Roof_leanto", -0.35, XK + 0.15, -0.4, ZN1 + 0.05, H0 + 0.05, 3.35, M["roof"], thickness=0.1, part="ceiling", level=0)
downlights([(1.5, 1.6), (1.5, 5.5), (4.8, 1.3), (4.8, 4.2), (8.2, 4.5), (5.3, 6.4)], height=H0)
for nm, (cx, cz, sx, sz) in {"CorniceN": ((XL + XK) / 2, ZC + 0.08, XK - XL, 0.1), "CorniceS": ((XL + XK) / 2, 7.0 - 0.08, XK - XL, 0.1),
                             "CorniceE": (XK - 0.08, (ZC + 7.0) / 2, 0.1, 7.0 - ZC), "CorniceLivN": (XL / 2, 0.08, XL, 0.1),
                             "CorniceLivW": (0.08, 3.9, 0.1, 7.85), "CorniceLivS": (XL / 2, 7.85 - 0.08, XL, 0.1)}.items():
    box(nm, (cx, H0 - 0.06, cz), (sx, 0.12, sz), M["band"], "Ceiling", bevel=0.01, segments=4, part="ceiling", level=0)
box("BeamHall", ((XL + XK) / 2, H0 - 0.15, 4.4), (XK - XL, 0.3, 0.25), M["band"], "Ceiling", bevel=0.01, part="ceiling", level=0)
box("BeamStair", (ST_X0 - 0.12, H0 - 0.15, (ZC + 7.0) / 2), (0.25, 0.3, 7.0 - ZC), M["band"], "Ceiling", bevel=0.01, part="ceiling", level=0)

# porch: four columns carrying the upper floor, two steps up to the door
for i, x in enumerate([0.25, 3.35, 6.35, 9.55]):
    column(f"Column_{i}", x, ZS - 0.25, 0, Y1 - 0.25, material=M["band"])
    for k in range(10):   # fluting: thin dark grooves around the shaft
        a = k * math.pi / 5
        box(f"Flute_{i}_{k}", (x + math.cos(a) * 0.158, (Y1 - 0.25) / 2, ZS - 0.25 + math.sin(a) * 0.158), (0.02, Y1 - 0.75, 0.02), M["terracotta"], "Structure", bevel=0, rot_z=-a, part="slab", room="porch")
box("StoneBase", (W / 2, -0.17, ZS + 0.21), (W + 0.8, 0.3, 0.02), M["stone"], "Structure", bevel=0, part="slab", level=0)
box("StoneBase_W", (-0.41, -0.17, ZS / 2), (0.02, 0.3, ZS + 0.8), M["stone"], "Structure", bevel=0, part="slab", level=0)
box("StoneBase_E", (W + 0.41, -0.17, ZS / 2), (0.02, 0.3, ZS + 0.8), M["stone"], "Structure", bevel=0, part="slab", level=0)
box("Step1", (3.7, 0.08, ZS + 0.35), (1.4, 0.16, 0.7), M["stone"], "Structure", bevel=0.01, part="slab", level=0, room="porch")
box("Step2", (3.7, -0.02, ZS + 0.75), (1.6, 0.16, 0.5), M["stone"], "Structure", bevel=0.01, part="slab", level=0, room="porch")
def panel_door(name, x, z, rot, w=0.85, room="hall", glass=False):
    """dark panelled door leaf: two raised panels with an arched top rail, optional glazed upper panel"""
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0)
    box(f"{name}", (px, 1.05, pz), (w, 2.1, 0.045), M["mahogany"], "Furniture", bevel=0.004, rot_z=rot, part="furniture", room=room)
    for k, (y, h) in enumerate([(0.55, 0.7), (1.5, 0.9)]):
        for j, dx in enumerate([-w / 4, w / 4]):
            px, pz = P(dx, -0.03)
            m = M["glass"] if (glass and k == 1) else M["mahogany"]
            box(f"{name}_p{k}{j}", (px, y, pz), (w / 2 - 0.1, h, 0.012), m, "Glass" if m is M["glass"] else "Furniture", bevel=0.003, rot_z=rot,
                part="glass" if m is M["glass"] else "furniture", side="I", room=room)
    px, pz = P(0, -0.035)
    box(f"{name}_arch", (px, 2.0, pz), (w - 0.1, 0.05, 0.01), M["mahogany"], "Furniture", bevel=0.003, rot_z=rot, rot_x=0, part="furniture", room=room)
    px, pz = P(w / 2 - 0.08, -0.04)
    box(f"{name}_handle", (px, 1.02, pz), (0.02, 0.12, 0.02), M["brass"], "Furniture", bevel=0, rot_z=rot, part="furniture", room=room)


panel_door("Door_entry", 3.7, 7.08, 0, w=0.9)
sphere("Door_entry_oval", (3.7, 1.35, 7.08), 1.0, M["glass"], "Glass", scale=(0.17, 0.42, 0.07), sub=3, part="glass", side="I", room="hall")
sphere("Door_entry_ovalrim", (3.7, 1.35, 7.08), 1.0, M["mahogany"], "Furniture", scale=(0.19, 0.44, 0.05), sub=3, part="furniture", room="hall")
panel_door("Door_patio", XK + 0.05, 1.6, math.pi / 2, w=0.8, room="kitchen", glass=True)
panel_door("Door_wc", 4.1, 6.95, math.pi / 2, w=0.7, room="wc", glass=True)
panel_door("Door_estudio", XK + 0.05, 3.28, math.pi / 2, w=0.8, room="estudio")

# straight stair along the east side of the hall: starts on the floor in front of the estudio door (z 3.3) and rises
# southward to the upper hall (z 6.6); the w.c. sits under its high end. Handrail on the open (west) side.
stair_flight("Stair", ST_X0, ST_X1, ST_Z0, ST_Z1, 0.0, Y1, ST_N, M["stair"])
_run, _rise = (ST_Z1 - ST_Z0) / ST_N, Y1 / ST_N
for i in range(ST_N):   # turned balusters, one per tread
    z = ST_Z0 + _run * (i + 0.5); y = _rise * (i + 1)
    cyl(f"Baluster{i}", (ST_X0 + 0.05, y + 0.42, z), 0.018, 0.84, M["mahogany"], verts=10, part="furniture", room="hall")
    sphere(f"BalusterKnob{i}", (ST_X0 + 0.05, y + 0.3, z), 0.032, M["mahogany"], sub=1, part="furniture", room="hall")
    sphere(f"BalusterKnob2{i}", (ST_X0 + 0.05, y + 0.58, z), 0.026, M["mahogany"], sub=1, part="furniture", room="hall")
_ang = math.atan2(Y1, ST_Z1 - ST_Z0)
box("StairRail", (ST_X0 + 0.05, Y1 / 2 + 0.9, (ST_Z0 + ST_Z1) / 2), (0.07, 0.06, math.hypot(Y1, ST_Z1 - ST_Z0) + 0.2), M["mahogany"], bevel=0.01, segments=4,
    rot_x=-_ang, part="furniture", room="hall")
cyl("Newel", (ST_X0 + 0.05, 0.5, ST_Z0 - 0.12), 0.05, 1.0, M["mahogany"], verts=12, part="furniture", room="hall")
sphere("NewelBall", (ST_X0 + 0.05, 1.07, ST_Z0 - 0.12), 0.075, M["mahogany"], sub=2, part="furniture", room="hall")
box("StairWall", (ST_X1 + 0.02, Y1 / 4, (ST_Z0 + ST_Z1) / 2), (0.04, Y1 / 2, ST_Z1 - ST_Z0), M["plaster"], bevel=0, part="furniture", room="hall")   # closes the triangle under the flight against the estudio wall

F = dict(part="furniture")
# ---------- comedor: six-seat table under two pendants, sideboard on the west wall, head chair toward the window
D = dict(room="living", level=0, **F)
box("DiningTable", (1.55, 0.74, 1.5), (0.9, 0.04, 1.6), M["walnut"], bevel=0.006, **D)
for i, (dx, dz) in enumerate([(-0.35, -0.65), (0.35, -0.65), (-0.35, 0.65), (0.35, 0.65)]):
    box(f"DiningLeg{i}", (1.55 + dx, 0.36, 1.5 + dz), (0.05, 0.72, 0.05), M["frame"], bevel=0, **D)
for i, z in enumerate([1.1, 1.9]):
    chair(f"DChairW{i}", 0.95, z, -math.pi / 2, room="living")
    chair(f"DChairE{i}", 2.15, z, math.pi / 2, room="living")
chair("DChairN", 1.55, 0.45, math.pi, room="living")
box("Sideboard", (0.3, 0.42, 1.5), (0.42, 0.84, 1.6), M["walnut"], bevel=0.008, **D)
box("SideboardGap", (0.512, 0.42, 1.5), (0.005, 0.8, 0.005), M["frame"], bevel=0, **D)
wall_art("Art_comedor", 0.09, 1.7, 1.5, 1.2, 0.7, math.pi / 2, M["art2"], room="living")
for i, z in enumerate([1.1, 1.9]):
    cyl(f"PendantCord_{i}", (1.55, 2.4, z), 0.003, 0.5, M["frame"], verts=6, **D)
    cyl(f"Pendant_{i}", (1.55, 2.05, z), 0.09, 0.22, M["pendant"], r2=0.11, part="light", room="living", level=0)
# ---------- living: media wall on the solid stretch of west wall, sofa on the diagonal facing it, an armchair in the
#            bay window and one under the west window, round table on a big rug; the route hall → comedor stays clear
L = dict(room="living", level=0, **F)
box("Rug_living", (1.45, 0.008, 5.3), (2.6, 0.012, 3.0), M["rug"], bevel=0.004, **L)
sofa("Sofa3", 1.95, 5.55, math.pi * 0.75, w=2.2)                                 # facing north-west, toward the TV
lounge_chair("Armchair1", 1.6, 7.55, math.pi)                                    # in the bay, facing the room
lounge_chair("Armchair2", 0.7, 6.2, -math.pi / 2 + 0.3)                          # under the west window
cyl("RoundTable", (1.15, 0.42, 5.0), 0.45, 0.04, M["walnut"], bevel=0.005, **L)
cyl("RoundTableLeg", (1.15, 0.2, 5.0), 0.05, 0.4, M["frame"], verts=12, **L)
box("Tray", (1.15, 0.455, 5.0), (0.3, 0.015, 0.2), M["frame"], bevel=0.004, **L)
box("Book1", (1.0, 0.46, 4.85), (0.22, 0.025, 0.28), M["book"], bevel=0.004, **L)
box("MediaUnit", (0.3, 0.24, 3.62), (0.42, 0.48, 1.5), M["walnut"], bevel=0.008, **L)
box("MediaGap", (0.512, 0.24, 3.62), (0.004, 0.006, 1.46), M["frame"], bevel=0, **L)
box("TV", (0.11, 1.3, 3.62), (0.035, 0.68, 1.2), M["screen"], bevel=0.004, **L)
box("TVpanel", (0.13, 1.3, 3.62), (0.004, 0.62, 1.14), M["screen"], bevel=0, **L)
box("Speaker", (0.3, 0.14, 2.95), (0.2, 0.28, 0.16), M["black"], bevel=0.008, **L)
floor_lamp("FloorLamp", 2.8, 7.3)
plant("Plant_living", 0.5, 2.95, s=1.2)   # beside the media unit, out of the bay
box("Curtain", (0.11, 1.35, 6.75), (0.04, 2.35, 0.4), M["linen"], bevel=0.015, **L)
box("CurtainRail", (0.1, 2.5, 5.5), (0.02, 0.02, 2.3), M["frame"], bevel=0, **L)
# ---------- cocina: L run along the north and west walls, window over the sink
K = dict(room="kitchen", level=0, **F)
box("KBaseN", (4.85, 0.44, 0.37), (3.2, 0.88, 0.6), M["black"], bevel=0.005, **K)
box("KTopN", (4.85, 0.9, 0.37), (3.24, 0.03, 0.63), M["quartz"], bevel=0.006, **K)
box("KBaseW", (3.53, 0.44, 1.65), (0.6, 0.88, 1.9), M["black"], bevel=0.005, **K)
box("KTopW", (3.53, 0.9, 1.65), (0.63, 0.03, 1.94), M["quartz"], bevel=0.006, **K)
box("KUpperN", (4.85, 2.05, 0.25), (3.2, 0.7, 0.35), M["oak"], bevel=0.005, **K)
box("Hob", (4.9, 0.912, 0.37), (0.6, 0.008, 0.5), M["screen"], bevel=0.003, **K)
box("Hood", (4.9, 1.62, 0.25), (0.7, 0.06, 0.35), M["steel"], bevel=0.006, **K)
box("Sink", (5.9, 0.905, 0.37), (0.55, 0.02, 0.4), M["steel"], bevel=0.005, **K)
box("Fridge", (3.53, 0.9, 0.5), (0.65, 1.8, 0.7), M["steel"], bevel=0.008, **K)
box("KTable", (5.2, 0.74, 1.9), (1.2, 0.04, 0.7), M["walnut"], bevel=0.006, **K)
for i, (dx, dz) in enumerate([(-0.5, -0.25), (0.5, -0.25), (-0.5, 0.25), (0.5, 0.25)]):
    box(f"KTableLeg{i}", (5.2 + dx, 0.36, 1.9 + dz), (0.04, 0.72, 0.04), M["frame"], bevel=0, **K)
# ---------- estudio: two desks on the east wall, shelving on the west wall
E = dict(room="estudio", level=0, **F)
for i, z in enumerate([3.9, 5.6]):
    box(f"Desk{i}", (9.05, 0.74, z), (1.2, 0.03, 0.65), M["walnut"], bevel=0.005, **E)
    for j, dz in enumerate([-0.28, 0.28]):
        box(f"DeskLeg{i}{j}", (9.05, 0.36, z + dz), (1.1, 0.72, 0.03), M["frame"], bevel=0, **E)
    box(f"Monitor{i}", (9.55, 1.05, z), (0.02, 0.36, 0.6), M["screen"], bevel=0.003, **E)
    box(f"MonitorStand{i}", (9.55, 0.83, z), (0.03, 0.14, 0.03), M["frame"], bevel=0, **E)
    office_chair(f"DeskChair{i}", 8.3, z, -math.pi / 2, room="estudio")
box("Bookcase", (6.8, 1.1, 5.0), (0.35, 2.2, 3.6), M["walnut"], bevel=0.006, **E)
for i in range(4):
    box(f"Shelf{i}", (6.8, 0.45 + i * 0.5, 5.0), (0.3, 0.02, 3.5), M["oak"], bevel=0, **E)
    for j in range(9):
        box(f"Book{i}{j}", (6.8, 0.6 + i * 0.5, 3.4 + j * 0.38 + rnd() * 0.1), (0.22, 0.26, 0.2), (M["book"], M["art"], M["vinyl"])[(i + j) % 3], bevel=0.003, **E)
plant("Plant_estudio", 9.3, 6.8, s=1.1, room="estudio")
# ---------- w.c. under the stair
Wc = dict(room="wc", level=0, **F)
soft("Toilet", (5.0, 0.2 - WC_DROP, 6.75), (0.38, 0.4, 0.55), M["white"], r=0.06, **Wc)
soft("Cistern", (5.0, 0.6 - WC_DROP, 6.92), (0.38, 0.4, 0.18), M["white"], r=0.03, **Wc)
box("WcVanity", (5.9, 0.5 - WC_DROP, 6.7), (0.6, 0.35, 0.45), M["walnut"], bevel=0.006, **Wc)
soft("WcBasin", (5.9, 0.76 - WC_DROP, 6.7), (0.42, 0.11, 0.32), M["white"], r=0.04, **Wc)
box("WcMirror", (5.9, 1.4 - WC_DROP, 6.92), (0.5, 0.6, 0.015), M["steel"], bevel=0, **Wc)
# ---------- patio de servicio + porch
Pa = dict(room="patio", level=0, **F)
box("Washer", (9.3, 0.425, 0.45), (0.6, 0.85, 0.6), M["white"], bevel=0.015, **Pa)
box("Dryer", (8.6, 0.425, 0.45), (0.6, 0.85, 0.6), M["white"], bevel=0.015, **Pa)
box("Sink_patio", (7.2, 0.45, 0.4), (0.7, 0.9, 0.5), M["concrete"], bevel=0.01, **Pa)
for i, x in enumerate([7.0, 8.0, 9.0]):
    box(f"PatioPlanter_{i}", (x, 0.2, 2.3), (0.6, 0.4, 0.4), M["pot_black"], bevel=0.01, **Pa)
    grass(f"PatioGrass_{i}", x, 2.3, s=0.9, room="patio")
Po = dict(room="porch", level=0, **F)
lounge_chair("PorchChair0", 7.0, 8.4, math.pi + 0.3, room="porch")
lounge_chair("PorchChair1", 8.6, 8.4, math.pi - 0.3, room="porch")
plant("Plant_porch", 1.5, 8.5, s=1.4, room="porch")

# ============================================================================= PLANTA ALTA (level 1)
walls1 = [
    (0, ZN1, XK, ZN1, "N", dict(ext=(True, True))),                                                    # north wall (over the lean-to)
    (XK, ZN1, XK, 3.14, "E", dict(ext=(False, True))),                                                  # side of the void over the patio
    (XK, 3.14, W, 3.14, "N", dict(ext=(True, True))),                                                   # padres north wall
    (W, 3.14, W, 5.4, "E", dict(ext=(True, False))), (W, 7.4, W, ZS, "E", dict(ext=(False, True))),
    (W, 5.4, W, 7.4, "E", dict(y0=0, y1=0.9)), (W, 5.4, W, 7.4, "E", dict(y0=2.2, y1=H1, noskirt=True)), (W, 5.4, W, 7.4, "E", dict(y0=0.9, y1=2.2, glass=True)),
    (XK, ZS, 7.4, ZS, "S", dict(ext=(True, False))), (9.0, ZS, W, ZS, "S", dict(ext=(False, True))),     # padres south wall, window x 7.4–9.0
    (7.4, ZS, 9.0, ZS, "S", dict(y0=0, y1=0.9)), (7.4, ZS, 9.0, ZS, "S", dict(y0=2.2, y1=H1, noskirt=True)), (7.4, ZS, 9.0, ZS, "S", dict(y0=0.9, y1=2.2, glass=True)),
    (0, ZS, 0.6, ZS, "S", dict(ext=(True, False))), (2.5, ZS, XL, ZS, "S", dict(ext=(False, True))),     # SW dormitorio south wall, window x 0.6–2.5
    (0.6, ZS, 2.5, ZS, "S", dict(y0=0, y1=0.9)), (0.6, ZS, 2.5, ZS, "S", dict(y0=2.2, y1=H1, noskirt=True)), (0.6, ZS, 2.5, ZS, "S", dict(y0=0.9, y1=2.2, glass=True)),
    (XL, 7.14, 3.5, 7.14, "S", dict(ext=(True, False))), (4.5, 7.14, 5.5, 7.14, "S", {}), (6.3, 7.14, XK, 7.14, "S", dict(ext=(False, True))),
    (3.5, 7.14, 4.5, 7.14, "S", dict(y0=2.2, y1=H1, noskirt=True)),                                              # balcony door x 3.5–4.5
    (5.5, 7.14, 6.3, 7.14, "S", dict(y0=0, y1=0.8)), (5.5, 7.14, 6.3, 7.14, "S", dict(y0=2.4, y1=H1, noskirt=True)),
    (5.5, 7.14, 6.3, 7.14, "S", dict(y0=0.8, y1=2.4, glass=True)),                                                # tall frosted window beside the stair
    (0, ZN1, 0, 2.8, "W", dict(ext=(True, False))), (0, 4.4, 0, 6.2, "W", {}), (0, 8.0, 0, ZS, "W", dict(ext=(False, True))),
    (0, 2.8, 0, 4.4, "W", dict(y0=0, y1=0.9)), (0, 2.8, 0, 4.4, "W", dict(y0=2.2, y1=H1, noskirt=True)), (0, 2.8, 0, 4.4, "W", dict(y0=0.9, y1=2.2, glass=True)),
    (0, 6.2, 0, 8.0, "W", dict(y0=0, y1=0.9)), (0, 6.2, 0, 8.0, "W", dict(y0=2.2, y1=H1, noskirt=True)), (0, 6.2, 0, 8.0, "W", dict(y0=0.9, y1=2.2, glass=True)),
    # interior
    (0, 5.51, XL, 5.51, "I", dict(**X)),                                                                 # between the two west bedrooms
    (XL, 5.51, XL, 6.0, "I", dict(ext=(True, False))), (XL, 6.8, XL, ZS, "I", dict(ext=(False, True))),   # SW dorm east wall, door z 6.0–6.8; continues as the balcony's west wall
    (XL, 6.0, XL, 6.8, "I", dict(y0=2.1, y1=H1, noskirt=True)),
    (4.16, ZN1, 4.16, 4.5, "I", dict(ext=(True, False))), (4.16, 5.3, 4.16, 5.51, "I", dict(ext=(False, True))),   # NW dorm east wall, door z 4.5–5.3
    (4.16, 4.5, 4.16, 5.3, "I", dict(y0=2.1, y1=H1, noskirt=True)),
    (XL, 5.51, 4.16, 5.51, "I", dict(ext=(False, True))) if False else (4.16, 5.51, 4.16, 5.51, "I", {}),
    (4.16, 3.67, 5.5, 3.67, "I", dict(ext=(True, False))), (6.2, 3.67, XK, 3.67, "I", dict(ext=(False, True))),   # baño south wall, door x 5.5–6.2
    (5.5, 3.67, 6.2, 3.67, "I", dict(y0=2.1, y1=H1, noskirt=True)),
    (XK, 3.14, XK, 6.4, "I", dict(ext=(True, False))), (XK, 7.2, XK, ZS, "I", dict(ext=(False, True))),   # padres west wall, door z 6.4–7.2
    (XK, 6.4, XK, 7.2, "I", dict(y0=2.1, y1=H1, noskirt=True)),
]
walls1 = [w for w in walls1 if not (w[0] == w[2] and w[1] == w[3])]   # drop the zero-length placeholder
frames1 = [
    (W, 5.4, W, 7.4, 0.9, 2.2, "E"), (7.4, ZS, 9.0, ZS, 0.9, 2.2, "S"), (0.6, ZS, 2.5, ZS, 0.9, 2.2, "S"),
    (3.5, 7.14, 4.5, 7.14, 0, 2.2, "S"), (5.5, 7.14, 6.3, 7.14, 0.8, 2.4, "S"), (0, 2.8, 0, 4.4, 0.9, 2.2, "W"), (0, 6.2, 0, 8.0, 0.9, 2.2, "W"),
]

# upper floor slab (in pieces around the stair well x 4.9–6.44, z 3.74–5.64), then everything else relative to Y1
SW_X0, SW_X1, SW_Z0, SW_Z1 = 4.9, 6.44, 5.1, 7.0
for i, (x1, z1, x2, z2) in enumerate([(-0.07, ZN1 - 0.07, SW_X0, ZS + 0.07), (SW_X1, ZN1 - 0.07, W + 0.07, ZS + 0.07),
                                       (SW_X0, ZN1 - 0.07, SW_X1, SW_Z0), (SW_X0, SW_Z1, SW_X1, ZS + 0.07)]):
    box(f"Slab1_{i}", ((x1 + x2) / 2, (H0 + Y1) / 2, (z1 + z2) / 2), (x2 - x1, Y1 - H0, z2 - z1), M["concrete"], "Structure", bevel=0, part="slab", level=1)
set_level(1, Y1)
build_walls(walls1, frames1, height=H1, frame_mat=M["wood_frame"], cladding=CLAD1)
for nm, (cx, cz, sx, sz) in {"BandS": (W / 2, ZS + 0.09, W + 0.36, 0.06), "BandW": (-0.09, (ZN1 + ZS) / 2, 0.06, ZS - ZN1 + 0.36),
                             "BandE": (W + 0.09, (ZN1 + ZS) / 2, 0.06, ZS - ZN1 + 0.36), "BandN": (W / 2, ZN1 - 0.09, W + 0.36, 0.06)}.items():
    box(nm, (cx, (H0 + Y1) / 2, cz), (sx, Y1 - H0 + 0.1, sz), M["band"], "Structure", bevel=0.004, part="slab", level=1)
floorp("Floor1_dormNW", (0, ZN1, 4.16, 5.51), M["wood"], 0, 1, "dorm1")
floorp("Floor1_dormSW", (0, 5.51, XL, ZS), M["wood"], 0, 1, "dorm2")
floorp("Floor1_bano", (4.16, ZN1, XK, 3.67), M["tile"], 0, 1, "bano")
floorp("Floor1_hall_a", (4.16, 3.67, SW_X0, 7.14), M["wood"], 0, 1, "hall1")
floorp("Floor1_hall_b", (SW_X1, 3.67, XK, 7.14), M["wood"], 0, 1, "hall1")
floorp("Floor1_hall_c", (SW_X0, SW_Z1, SW_X1, 7.14), M["wood"], 0, 1, "hall1")
floorp("Floor1_hall_d", (XL, 5.51, 4.16, 7.14), M["wood"], 0, 1, "hall1")
floorp("Floor1_padres", (XK, 3.14, W, ZS), M["wood"], 0, 1, "padres")
floorp("Floor1_balcon", (XL, 7.14, XK, ZS), M["stone"], 0, 1, "balcon")
box("Ceiling1", (W / 2, H1 + 0.05, (ZN1 + ZS) / 2), (W + T, 0.1, ZS - ZN1 + T), M["ceiling"], "Ceiling", bevel=0, part="ceiling", level=1)
downlights([(2.0, 3.7), (1.5, 7.3), (5.3, 2.8), (5.3, 6.0), (8.2, 4.5), (8.2, 7.5)], height=H1)
# stair well railing on the upper floor
wood_railing("Rail_well_w", SW_X0, SW_Z1, SW_X0, SW_Z0, 0, h=0.95, material=M["mahogany"], newels=(True, True))
wood_railing("Rail_well_n", SW_X0 + 0.09, SW_Z0, SW_X1 - 0.05, SW_Z0, 0, h=0.95, material=M["mahogany"], newels=(False, False))
panel_door("Door_dormNW", 4.16 - 0.05, 4.9, math.pi / 2, w=0.8, room="dorm1")
panel_door("Door_dormSW", XL - 0.05, 6.4, math.pi / 2, w=0.8, room="dorm2")
panel_door("Door_bano", 5.85, 3.67 - 0.05, 0, w=0.7, room="bano")
panel_door("Door_padres", XK + 0.05, 6.8, math.pi / 2, w=0.8, room="padres")
# flight to the attic: starts on the landing by the south wall and climbs north over the well, open treads on a steel stringer
ST2_Z0, ST2_Z1, ST2_N = 6.9, 4.0, 13
stair_flight("Stair2", ST_X0, ST_X1, ST2_Z0, ST2_Z1, 0.0, Y2 - Y1, ST2_N, M["mahogany"], open_risers=True, stringer=M["black"])
_run2, _rise2 = (ST2_Z1 - ST2_Z0) / ST2_N, (Y2 - Y1) / ST2_N
for i in range(ST2_N):
    z = ST2_Z0 + _run2 * (i + 0.5); y = _rise2 * (i + 1)
    cyl(f"Baluster2_{i}", (ST_X0 + 0.05, y + 0.42, z), 0.018, 0.84, M["mahogany"], verts=10, part="furniture", room="hall1")
    sphere(f"Baluster2Knob{i}", (ST_X0 + 0.05, y + 0.3, z), 0.032, M["mahogany"], sub=1, part="furniture", room="hall1")
    sphere(f"Baluster2Knob2{i}", (ST_X0 + 0.05, y + 0.58, z), 0.026, M["mahogany"], sub=1, part="furniture", room="hall1")
_ang2 = math.atan2(Y2 - Y1, ST2_Z1 - ST2_Z0)
box("Stair2Rail", (ST_X0 + 0.05, (Y2 - Y1) / 2 + 0.9, (ST2_Z0 + ST2_Z1) / 2), (0.07, 0.06, math.hypot(Y2 - Y1, ST2_Z1 - ST2_Z0) + 0.2), M["mahogany"], bevel=0.01, segments=4,
    rot_x=-_ang2, part="furniture", room="hall1")
box("Newel2", (ST_X0 + 0.05, 0.5, ST2_Z0 + 0.12), (0.09, 1.0, 0.09), M["mahogany"], bevel=0.008, part="furniture", room="hall1")
sphere("Newel2Ball", (ST_X0 + 0.05, 1.07, ST2_Z0 + 0.12), 0.075, M["mahogany"], sub=2, part="furniture", room="hall1")
for k, x in enumerate([5.9]):
    box(f"WinMullion{k}", (x, 1.6, 7.14), (0.04, 1.56, T + 0.07), M["wood_frame"], "Walls", bevel=0, part="frame", side="S")
for k, y in enumerate([1.2, 1.6, 2.0]):
    box(f"WinBar{k}", (5.9, y, 7.14), (0.76, 0.04, T + 0.07), M["wood_frame"], "Walls", bevel=0, part="frame", side="S")
railing("Rail_balcon", XL + 0.1, ZS - 0.03, XK - 0.1, ZS - 0.03, 0.12, h=0.95, material=M["iron"], posts=22)   # wrought iron, white
box("Curb_balcon", ((XL + XK) / 2, 0.06, ZS), (XK - XL, 0.12, T), M["concrete"], "Structure", part="slab")


def bed(name, x, z, rot, w=1.6, l=2.0, room="bedroom"):
    """double bed: headboard at -dz (rot 0 → headboard on the north side); heights relative to the current level"""
    y = 0
    c, s = math.cos(rot), math.sin(rot)
    P = lambda dx, dz: (x + dx * c - dz * s, z + dx * s + dz * c)
    px, pz = P(0, 0.05)
    box(f"{name}_platform", (px, y + 0.13, pz), (w + 0.4, 0.24, l + 0.2), M["walnut"], bevel=0.01, rot_z=rot, part="furniture", room=room)
    soft(f"{name}_mattress", (px, y + 0.36, pz), (w, 0.24, l), M["linen"], r=0.05, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, 0.3)
    soft(f"{name}_duvet", (px, y + 0.5, pz), (w + 0.04, 0.07, l * 0.6), M["charcoal"], r=0.03, rot_z=rot, part="furniture", room=room)
    px, pz = P(0, -l / 2 - 0.02)
    box(f"{name}_head", (px, y + 0.65, pz), (w + 0.6, 1.1, 0.06), M["charcoal"], bevel=0.01, rot_z=rot, part="furniture", room=room)
    for i, dx in enumerate([-w / 4, w / 4]):
        px, pz = P(dx, -l / 2 + 0.3)
        soft(f"{name}_pillow{i}", (px, y + 0.55, pz), (w / 2 - 0.1, 0.16, 0.42), M["linen"], r=0.05, rot_z=rot, part="furniture", room=room)
    for i, dx in enumerate([-w / 2 - 0.5, w / 2 + 0.5]):
        px, pz = P(dx, -l / 2 + 0.2)
        box(f"{name}_nightstand{i}", (px, y + 0.45, pz), (0.45, 0.12, 0.38), M["walnut"], bevel=0.006, rot_z=rot, part="furniture", room=room)


F1 = dict(**F)
# ---------- dormitorio NW: bed against the north wall, wardrobe on the east
bed("BedNW", 1.9, ZN1 + 1.35, 0, room="dorm1")
box("WardrobeNW", (3.75, 1.1, 2.9), (0.6, 2.2, 1.6), M["black"], bevel=0.006, room="dorm1", **F1)
box("Rug_NW", (1.9, 0.008, 4.6), (2.4, 0.012, 1.2), M["rug"], bevel=0.004, room="dorm1", **F1)
plant("Plant_NW", 0.4, 5.1, s=1.1, room="dorm1")
# ---------- dormitorio SW: bed against the south... headboard on the north partition, desk under the window
bed("BedSW", 1.55, 5.51 + 1.35, 0, w=1.4, room="dorm2")
box("DeskSW", (0.45, 0.74, 8.3), (0.55, 0.03, 1.2), M["walnut"], bevel=0.005, room="dorm2", **F1)
office_chair("ChairSW", 1.1, 8.3, math.pi / 2, room="dorm2")
box("WardrobeSW", (2.75, 1.1, 8.2), (0.6, 2.2, 1.4), M["black"], bevel=0.006, room="dorm2", **F1)
# ---------- baño (over the hall's north end): shower, toilet, vanity
Bn = dict(room="bano", **F1)
box("ShowerGlass1", (5.1, 1.1, 2.9), (0.01, 2.2, 1.3), M["glass"], "Glass", bevel=0, part="glass", side="I", room="bano")
box("ShowerHead1", (4.6, 2.15, 2.9), (0.25, 0.012, 0.25), M["frame"], bevel=0.003, **Bn)
soft("Toilet1", (5.6, 0.2, 2.4), (0.38, 0.4, 0.55), M["white"], r=0.06, **Bn)
soft("Cistern1", (5.6, 0.6, 2.18), (0.38, 0.4, 0.18), M["white"], r=0.03, **Bn)
box("Vanity1", (6.15, 0.5, 2.9), (0.45, 0.35, 0.8), M["walnut"], bevel=0.006, **Bn)
soft("Basin1", (6.15, 0.76, 2.9), (0.32, 0.11, 0.42), M["white"], r=0.04, **Bn)
box("Mirror1", (6.42, 1.55, 2.9), (0.015, 0.7, 0.7), M["steel"], bevel=0, **Bn)
# ---------- dormitorio padres: bed with the headboard on the east wall, long wardrobe along the north, armchair by the window
bed("BedP", 8.3, 6.0, -math.pi / 2, w=1.8, l=2.0, room="padres")
box("WardrobeP", (8.15, 1.15, 3.5), (2.7, 2.3, 0.6), M["black"], bevel=0.006, room="padres", **F1)
box("Rug_P", (7.6, 0.008, 6.0), (1.4, 0.012, 2.6), M["rug_dark"], bevel=0.004, room="padres", **F1)
lounge_chair("ChairP", 8.3, 8.4, math.pi + 0.4, room="padres")
plant("Plant_P", 7.0, 8.6, s=1.2, room="padres")
wall_art("Art_P", 9.71, 1.75, 6.0, 1.3, 0.6, -math.pi / 2, M["art2"], room="padres")
# ---------- balcón
for i, x in enumerate([3.9, 5.7]):
    lounge_chair(f"BalconChair{i}", x, 8.3, math.pi, room="balcon")
box("BalconTable", (4.8, 0.4, 8.35), (0.5, 0.03, 0.5), M["walnut"], bevel=0.006, room="balcon", **F1)
cyl("BalconTableLeg", (4.8, 0.2, 8.35), 0.02, 0.4, M["frame"], verts=10, room="balcon", **F1)
plant("Plant_balcon", 3.5, 7.5, s=1.0, room="balcon")

# ============================================================================= DESVÁN (level 2): attic under the gable roof, dormer to the south
RIDGE_Z, RIDGE_H, EAVE_H = (ZN1 + ZS) / 2, 2.4, 0.35          # heights relative to the attic floor
AT_Z0, AT_Z1 = 3.6, 6.3     # opening in the attic floor over the second flight
for i, (x1, z1, x2, z2) in enumerate([(-0.07, ZN1 - 0.07, SW_X0, ZS + 0.07), (SW_X1, ZN1 - 0.07, W + 0.07, ZS + 0.07),
                                       (SW_X0, ZN1 - 0.07, SW_X1, AT_Z0), (SW_X0, AT_Z1, SW_X1, ZS + 0.07)]):
    box(f"Slab2_{i}", ((x1 + x2) / 2, (Y1 + H1 + Y2) / 2, (z1 + z2) / 2), (x2 - x1, Y2 - Y1 - H1, z2 - z1), M["concrete"], "Structure", bevel=0, part="slab", level=2)
box("Cornice", (W / 2, (Y1 + H1 + Y2) / 2, (ZN1 + ZS) / 2), (W + 0.44, Y2 - Y1 - H1 + 0.12, ZS - ZN1 + 0.44), M["band"], "Structure", bevel=0.01, part="slab", level=2)
set_level(2, Y2)
floorp("Floor2_a", (0, ZN1, SW_X0, ZS), M["concrete"], 0, 2, "attic")
floorp("Floor2_b", (SW_X1, ZN1, W, ZS), M["concrete"], 0, 2, "attic")
floorp("Floor2_c", (SW_X0, ZN1, SW_X1, AT_Z0), M["concrete"], 0, 2, "attic")
floorp("Floor2_d", (SW_X0, AT_Z1, SW_X1, ZS), M["concrete"], 0, 2, "attic")
wood_railing("Rail_attic_w", SW_X0, AT_Z1, SW_X0, AT_Z0, 0, h=0.95, material=M["mahogany"], room="attic")
wood_railing("Rail_attic_s", SW_X0 + 0.09, AT_Z1, SW_X1 - 0.05, AT_Z1, 0, h=0.95, material=M["mahogany"], room="attic", newels=(False, False))
import bmesh, bpy  # noqa: E402
from ktlib import coll, uv_box  # noqa: E402


def gable_wall(name, x, side):
    """triangular gable end in the (z, y) plane, T thick"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    pts = [(ZN1 - 0.07, 0), (ZS + 0.07, 0), (ZS + 0.07, EAVE_H), (RIDGE_Z, RIDGE_H), (ZN1 - 0.07, EAVE_H)]
    a = [bm.verts.new((x - T / 2, -z, Y2 + y)) for z, y in pts]
    c = [bm.verts.new((x + T / 2, -z, Y2 + y)) for z, y in pts]
    bm.faces.new(a[::-1]); bm.faces.new(c)
    for i in range(len(pts)):
        bm.faces.new((a[i], a[(i + 1) % len(pts)], c[(i + 1) % len(pts)], c[i]))
    bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll("Walls").objects.link(o)
    o.data.materials.append(M["plaster"]); o["part"] = "wall"; o["side"] = side; o["level"] = 2
    bpy.context.view_layer.update(); uv_box(o, M["plaster"]["tile"])


gable_wall("Gable_W", 0.0, "W"); gable_wall("Gable_E", W, "E")
box("Knee_N", (W / 2, EAVE_H / 2, ZN1), (W + T, EAVE_H, T), M["plaster"], "Walls", bevel=0, part="wall", side="N")
box("Knee_S", (W / 2, EAVE_H / 2, ZS), (W + T, EAVE_H, T), M["plaster"], "Walls", bevel=0, part="wall", side="S")
roof_slab("Roof_N", -0.4, W + 0.4, ZN1 - 0.4, RIDGE_Z, EAVE_H - 0.12, RIDGE_H + 0.05, M["roof"], thickness=0.14, part="ceiling")
roof_slab("Roof_S", -0.4, W + 0.4, ZS + 0.4, RIDGE_Z, EAVE_H - 0.12, RIDGE_H + 0.05, M["roof"], thickness=0.14, part="ceiling")
box("Ridge", (W / 2, RIDGE_H + 0.1, RIDGE_Z), (W + 0.8, 0.12, 0.3), M["roof"], "Ceiling", bevel=0.02, part="ceiling")
# dormer on the south slope with its window
DX0, DX1, DZ = 3.7, 6.1, ZS - 1.6
box("Dormer_front", ((DX0 + DX1) / 2, 1.0, DZ), (DX1 - DX0, 2.0, T), M["plaster"], "Walls", bevel=0.006, part="wall", side="S")
box("Dormer_clad", ((DX0 + DX1) / 2, 1.0, DZ + T / 2 + 0.011), (DX1 - DX0 + 0.02, 2.0, 0.02), M["salmon"], "Walls", bevel=0, part="wall", side="S")
box("Dormer_glass", ((DX0 + DX1) / 2, 1.0, DZ), (1.6, 1.0, 0.02), M["glass"], "Glass", bevel=0, part="glass", side="S")
for k, x in enumerate([-0.8, -0.27, 0.27, 0.8]):
    box(f"Dormer_mullion{k}", ((DX0 + DX1) / 2 + x, 1.0, DZ + 0.02), (0.06, 1.06, 0.06), M["wood_frame"], "Walls", bevel=0, part="frame", side="S")
box("Dormer_sill", ((DX0 + DX1) / 2, 0.47, DZ + 0.03), (1.7, 0.06, 0.1), M["wood_frame"], "Walls", bevel=0, part="frame", side="S")
box("Dormer_head", ((DX0 + DX1) / 2, 1.53, DZ + 0.03), (1.7, 0.06, 0.1), M["wood_frame"], "Walls", bevel=0, part="frame", side="S")
cyl("Dormer_fan", ((DX0 + DX1) / 2, 1.8, DZ + 0.045), 0.28, 0.03, M["glass"], "Glass", verts=24, rot=(math.radians(90), 0, 0), part="glass", side="S")
cyl("Dormer_fanring", ((DX0 + DX1) / 2, 1.8, DZ + 0.04), 0.31, 0.02, M["wood_frame"], "Walls", verts=24, rot=(math.radians(90), 0, 0), part="frame", side="S")
for i, x in enumerate([DX0, DX1]):
    prism(f"Dormer_side{i}", [(x - T / 2, DZ), (x + T / 2, DZ), (x + T / 2, RIDGE_Z - 0.6), (x - T / 2, RIDGE_Z - 0.6)], 0, 2.0, M["plaster"], part="wall", side="I")
roof_slab("Dormer_roof", DX0 - 0.2, DX1 + 0.2, DZ - 0.3, RIDGE_Z - 0.6, 2.0, 2.3, M["roof"], thickness=0.1, part="ceiling")
# storage: crates, an old chair, a trunk, the hatch over the stair well
A = dict(room="attic", **F)
for i in range(8):
    x = 0.8 + (i % 4) * 0.9; z = ZN1 + 1.4 + (i // 4) * 0.9
    box(f"Crate{i}", (x, 0.25, z), (0.6, 0.5, 0.6), (M["book"], M["oak"])[i % 2], bevel=0.01, **A)
for i in range(3):
    box(f"CrateTop{i}", (0.8 + i * 0.9, 0.72, ZN1 + 1.4), (0.5, 0.42, 0.5), M["book"], bevel=0.01, **A)
chair("OldChair", 8.5, 5.0, 0.7, room="attic")
box("Trunk", (8.4, 0.3, 7.5), (1.0, 0.6, 0.6), M["leather_tan"], bevel=0.02, **A)
set_level(0, 0.0)

# ----------------------------------------------------------------------------- lighting + renders (used by bake_lightmaps.py / render_views.py)
LIGHTS = [("Pendant_a", (1.55, 2.0, 1.7), 12), ("Living", (1.55, 2.5, 5.5), 18), ("Hall", (5.0, 2.5, 4.2), 18), ("Estudio", (8.2, 2.5, 4.5), 18),
          ("DormNW", (2.0, Y1 + 2.4, 3.7), 18), ("DormSW", (1.5, Y1 + 2.4, 7.3), 18), ("Padres", (8.2, Y1 + 2.4, 6.0), 18), ("Hall1", (5.3, Y1 + 2.4, 6.0), 14)]
SUN_ROT = (50, 10, 35)
FILL_AT = (4.9, 12.0, 12.0)
RENDER_VIEWS = [   # key, camera, target, fov, hidden sides, highest floor shown
    ("whole",   (-14.0, 16.0, 22.0), (4.9, 2.5, 4.5), 30, "SW", 2),
    ("ground",  (-12.0, 12.0, 18.0), (4.9, 0.5, 4.5), 32, "SW", 0),
    ("upper",   (-12.0, 15.0, 18.0), (4.9, Y1 + 0.5, 5.5), 32, "SW", 1),
    ("living",  (-8.0, 5.0, 12.0),   (1.6, 0.6, 5.5), 42, "SW", 0),
    ("kitchen", (4.8, 5.0, -6.0),    (4.8, 0.7, 1.3), 40, "N", 0),
    ("bedroom", (-6.0, 9.0, 0.0),    (2.0, Y1 + 0.5, 3.7), 42, "NW", 1),
    ("terrace", (4.8, 8.0, 16.0),    (4.8, Y1 + 0.5, 8.3), 40, "S", 1),
]

# the minimap / walk-collision plans come straight from the wall lists above
write_plan(os.path.join(HERE, "..", "site", "casa", "plan.js"), [
    dict(walls=walls0, bounds=(-0.3, -0.3, W + 0.3, ZS + 1.2),
         extra=[(ST_X0, ST_Z0 + 0.9, ST_X0, ST_Z1, "wall"), (ST_X0, ST_Z1, ST_X1, ST_Z1, "wall")],
         rooms=[("living", (0, 0, XL, 3.3), "#d9b98c", "Comedor"), ("living2", (0, 3.3, XL, 7.85), "#d9b98c", "Living"),
                ("kitchen", (XL, 0, XK, ZC), "#d2b58c", "Cocina"), ("hall", (XL, ZC, XK, 7.0), "#cfc6b8", "Hall"),
                ("estudio", (XK, ZC, W, 7.14), "#dfc39b", "Estudio"), ("patio", (XK, 0, W, ZC), "#b9b4ab", "Patio"),
                ("wc", (4.16, 5.71, XK, 7.0), "#c9cdd1", ""), ("porch", (XL, 7.14, W, ZS), "#bdb8b0", "Porch")]),
    dict(walls=walls1, bounds=(-0.3, ZN1 - 0.3, W + 0.3, ZS + 0.3),
         extra=[(SW_X0, SW_Z0, SW_X0, SW_Z1, "wall"), (SW_X0, SW_Z0, SW_X1, SW_Z0, "wall"), (ST_X0, ST2_Z1, ST_X0, ST2_Z0 - 0.9, "wall")],
         rooms=[("dorm1", (0, ZN1, 4.16, 5.51), "#dfc39b", "Dormitorio"), ("dorm2", (0, 5.51, XL, ZS), "#dfc39b", "Dormitorio"),
                ("bano", (4.16, ZN1, XK, 3.67), "#c9cdd1", "Baño"), ("hall1", (XL, 3.67, XK, 7.14), "#cfc6b8", "Hall"),
                ("padres", (XK, 3.14, W, ZS), "#d9b98c", "Padres"), ("balcon", (XL, 7.14, XK, ZS), "#bdb8b0", "Balcón")]),
    dict(walls=[], bounds=(-0.3, ZN1 - 0.3, W + 0.3, ZS + 0.3),
         extra=[(0, ZN1, W, ZN1, "wall"), (0, ZS, W, ZS, "wall"), (0, ZN1, 0, ZS, "wall"), (W, ZN1, W, ZS, "wall"),
                (SW_X0, AT_Z0, SW_X0, AT_Z1, "wall"), (SW_X0, AT_Z1, SW_X1, AT_Z1, "wall"), (SW_X1, AT_Z0, SW_X1, AT_Z1, "wall"),
                (DX0, DZ, DX1, DZ, "glass"), (DX0, DZ, DX0, RIDGE_Z - 0.6, "wall"), (DX1, DZ, DX1, RIDGE_Z - 0.6, "wall")],
         rooms=[("attic", (0, ZN1, W, ZS), "#d6d2c8", "Desván")]),
])

export(OUT, blend=os.path.join(HERE, "casa.blend"))
