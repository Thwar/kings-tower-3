# Apartment 3D — King's Tower Dept. D · Torre Duna Tipo E · Bloque B 101

Blender-modelled apartments published as interactive cutaway viewers and first-person walkthroughs on GitHub Pages.
The header switches between the two apartments; each has its own model, lighting bake, renders and 2D plan.

| URL | What |
|---|---|
| `/` | **King's Tower · Dept. D** — isometric cutaway: orbit / pan, room viewpoints, 2D minimap, Blender renders tab |
| `/?mode=walk` | its **Walkthrough** — the same baked model in first person: WASD or touch joystick, wall collision, 75° lens |
| `/duna/` | **Torre Duna · Tipo E** (49.61 m²) — the same viewer on the second apartment |
| `/duna/?mode=walk` | its walkthrough |
| `/b101/` | **Bloque B · Departamento 101** (100.20 m², one bedroom, long terrace) |
| `/b101/?mode=walk` | its walkthrough |
| `/casa/` | **Casa · 2 plantas** — a two-storey house with an attic from the architect's 1:100 set; floor selector, per-floor minimap and walkthrough |

Cutaway and walkthrough are one page per apartment, one model and one lighting bake, so they always look the same.
Every page also has a **Minimal / Gamer loft** design switch (`?style=loft`): the same apartment furnished as a grey-and-LED
loft with a gaming desk, glass display cabinet, lit vanity mirror, sectional and fur rug.

## Pipeline (all headless, all offline)

```bash
pip install bpy                                   # Blender as a Python module (~370 MB, Python 3.11)
python3 blender/build_apartment.py                # model → site/apartment.glb (unbaked, for quick checks)
python3 blender/bake_lightmaps.py [--fast]        # bakes Cycles lighting → site/lightmaps/*.jpg, site/apartment.glb (baked), site/footprints.json
python3 blender/render_views.py [--fast]          # Cycles renders → site/renders/*.jpg (the "Blender renders" tab)
python3 blender/build_apartment.py --blend        # also writes blender/apartment.blend to open in Blender
python3 blender/build_duna.py                     # the second apartment; add --apt=duna to the bake / render scripts → site/duna/
python3 blender/build_b101.py                     # the third; --apt=b101 → site/b101/
python3 blender/build_casa.py                     # the house (three levels); also regenerates site/casa/plan.js
KT_STYLE=loft python3 blender/build_duna.py       # the loft design scheme; bake/render it with --style=loft → *-loft assets
```

- `build_apartment.py` / `build_duna.py` build everything procedurally from each floor plan: walls with openings, floors,
  furniture, materials — using the shared toolkit in `ktlib.py`. Every object carries `part` / `side` / `room` custom
  properties that survive glTF export; the viewer uses `side` for the cutaway.
- `textures.py` generates seamless PBR sets (oak planks, plaster, concrete, linen, leather, quartz, tiles, paving…) with numpy,
  box-projected in world space so grain and tiles line up across pieces. Delete `blender/tex/` to regenerate.
- `bake_lightmaps.py` is what gives the viewer its photographic look: it merges the model into one mesh per material
  (walls per side, so the cutaway still works), unwraps a second UV set, bakes diffuse global illumination with Cycles
  (neutral sky + sun + the apartment's own lamps, ceiling removed so the cutaway reads evenly lit) and stores it as lightmaps.
  It uses the GPU when Blender can see one (Metal / CUDA / OptiX / HIP) and prints which; on CPU it takes about 12 minutes.
  The viewer multiplies albedo by lightmap and adds a faint environment for reflections — no real-time lights or shadow maps,
  which is why it looks like a render and runs at 60 fps. **Run it after any model change** and commit its outputs together.

Dimensions come from the plans: Dept. D is 50.21 m² interior + 29.75 m² terrace; Tipo E is 49.61 m² in total, with its room
sizes scaled from the drawing because the brochure gives no individual dimensions. 2.6 m ceilings. Furniture is approximate.
Interior concept: minimal bachelor pad — warm off-white plaster, mid-oak floor, matte black and walnut, charcoal linen, black leather.

## The viewer (`site/`)

Plain HTML + three.js (vendored in `site/vendor`, no build step). One `app.js` serves both apartments: each page's `config.js`
(next to its `index.html`) supplies the viewpoints, walk spots, cutaway centre and 2D plan (`plan.js`). Useful query params: `?mode=walk`, `?ao=1` (screen-space AO),
`?lm=` / `?env=` / `?exp=` for light balance while tuning.

## Deploy

`.github/workflows/deploy.yml` publishes `site/` to GitHub Pages on every push to `main`. Pages source must be **GitHub Actions**.
