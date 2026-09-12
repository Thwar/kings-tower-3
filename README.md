# King's Tower · Dept. D — 3D

A Blender-modelled apartment published as an interactive cutaway viewer and a first-person walkthrough on GitHub Pages.

| URL | What |
|---|---|
| `/` | **Apartment 3D** — isometric cutaway: orbit / pan, room viewpoints, 2D minimap, Blender renders tab |
| `/?mode=walk` | **Walkthrough** — the same baked model in first person: WASD or touch joystick, wall collision, 75° lens |

Both are one page (`site/`), one model and one lighting bake, so they always look the same.

## Pipeline (all headless, all offline)

```bash
pip install bpy                                   # Blender as a Python module (~370 MB, Python 3.11)
python3 blender/build_apartment.py                # model → site/apartment.glb (unbaked, for quick checks)
python3 blender/bake_lightmaps.py [--fast]        # bakes Cycles lighting → site/lightmaps/*.jpg, site/apartment.glb (baked), site/footprints.json
python3 blender/render_views.py [--fast]          # Cycles renders → site/renders/*.jpg (the "Blender renders" tab)
python3 blender/build_apartment.py --blend        # also writes blender/apartment.blend to open in Blender
```

- `build_apartment.py` builds everything procedurally from the floor plan: walls with openings, floors, furniture, materials.
  Every object carries `part` / `side` / `room` custom properties that survive glTF export; the viewer uses `side` for the cutaway.
- `textures.py` generates seamless PBR sets (oak planks, plaster, concrete, linen, leather, quartz, tiles, paving…) with numpy,
  box-projected in world space so grain and tiles line up across pieces. Delete `blender/tex/` to regenerate.
- `bake_lightmaps.py` is what gives the viewer its photographic look: it merges the model into one mesh per material
  (walls per side, so the cutaway still works), unwraps a second UV set, bakes diffuse global illumination with Cycles
  (neutral sky + sun + the apartment's own lamps, ceiling removed so the cutaway reads evenly lit) and stores it as lightmaps.
  The viewer multiplies albedo by lightmap and adds a faint environment for reflections — no real-time lights or shadow maps,
  which is why it looks like a render and runs at 60 fps. **Run it after any model change** and commit its outputs together.

Dimensions come from the plan: 50.21 m² interior + 29.75 m² terrace, 2.6 m ceilings. Furniture is approximate.
Interior concept: minimal bachelor pad — warm off-white plaster, mid-oak floor, matte black and walnut, charcoal linen, black leather.

## The viewer (`site/`)

Plain HTML + three.js (vendored in `site/vendor`, no build step). Viewpoints, copy and stats live in the `VIEWS` array at the top
of `site/app.js`; the 2D plan for the minimap is `site/plan.js`. Useful query params: `?mode=walk`, `?ao=1` (screen-space AO),
`?lm=` / `?env=` / `?exp=` for light balance while tuning.

## Deploy

`.github/workflows/deploy.yml` publishes `site/` to GitHub Pages on every push to `main`. Pages source must be **GitHub Actions**.
