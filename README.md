# King's Tower · Dept. D — 3D

One apartment, two perspectives, one GitHub Pages site:

| URL | What | Built from |
|---|---|---|
| `/` | **Apartment 3D** — isometric cutaway viewer (orbit / pan / walk, room viewpoints, Blender renders tab) | `site/` + `blender/` |
| `/walk/` | **Walkthrough** — first-person fly-through with PBR textures and HDRI sky | `src/` (Vite + React Three Fiber) |

## The Blender model

`blender/build_apartment.py` builds the whole apartment procedurally from the floor plan (walls, openings, floors, furniture,
materials) and exports `site/apartment.glb`. It runs headless with the `bpy` pip module or inside Blender:

```bash
pip install bpy                                   # Blender as a Python module (~370 MB, Python 3.11)
python3 blender/build_apartment.py                # → site/apartment.glb
python3 blender/build_apartment.py --blend        # also writes blender/apartment.blend to open in Blender
python3 blender/render_views.py [--fast]          # Cycles renders → site/renders/*.jpg (the "Blender renders" tab)
```

Every object carries custom properties (`part`, `side`, `room`) that survive glTF export as extras; the viewer uses `side`
to hide whichever exterior walls face the camera (the cutaway) and `part` to toggle the ceiling.

Dimensions come from the plan: 50.21 m² interior + 29.75 m² terrace, 2.6 m ceilings. Furniture is approximate.

## The viewer (`site/`)

Plain HTML + three.js (vendored in `site/vendor`, no build step). Viewpoints, stats and labels live at the top of `site/app.js`.
Query params help while tuning lights: `?env=0.3&sun=4.5&exp=1`.

## The walkthrough (`src/`)

```bash
npm install
npm run assets   # textures + HDRI into public/ (~40 MB, one-time)
npm run dev      # Vite dev server
```

## Deploy

`.github/workflows/deploy.yml` builds the walkthrough into `dist/walk`, copies `site/` over `dist/`, and publishes to GitHub Pages
on every push to `main`. Pages source must be set to **GitHub Actions**.
