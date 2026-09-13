# Project notes for Claude Code

One static site (`site/`) + one Blender pipeline (`blender/`). No npm, no bundler. Push to `main` → Pages deploys `site/`.

| | King's Tower · Dept. D | Torre Duna · Tipo E | Bloque B · Dpto. 101 |
|---|---|---|---|
| page | `site/index.html` (`/`) | `site/duna/index.html` (`/duna/`) | `site/b101/index.html` (`/b101/`) |
| per-page data | `site/config.js`, `site/plan.js` | `site/duna/config.js`, `site/duna/plan.js` | `site/b101/config.js`, `site/b101/plan.js` |
| model + bake outputs | `site/apartment.glb`, `site/lightmaps/`, `site/footprints.json`, `site/renders/` | the same names under `site/duna/` | the same names under `site/b101/` |
| Blender build | `blender/build_apartment.py` | `blender/build_duna.py` | `blender/build_b101.py` |
| bake / renders | `bake_lightmaps.py`, `render_views.py` | the same scripts with `--apt=duna` | `--apt=b101` |

Two apartments share everything except their data: → three apartments. A page whose `apartment.glb` was exported by the build
script (not the bake) still works, lit in real time; the bake is what makes it look like the others. Tall plans set `mapRotate`
in their config so the minimap is drawn with north to the left.

Each apartment also has two **interior design schemes**, chosen with `KT_STYLE` (env) in Blender and `?style=` on the page:
`bachelor` (default: oak, walnut, black) and `loft` (grey walls, concrete floor, LED coves, gaming desk, glass cabinet, lit
vanity, sectional + fur rug). `ktlib.STYLE` swaps the palette; each build script has `if STYLE == "bachelor": … / if STYLE ==
"loft": …` blocks for the living and bedroom (kitchen, bath, service and terrace are shared). Loft assets carry a `-loft`
suffix: `apartment-loft.glb`, `lightmaps-loft/`, `footprints-loft.json`, `renders-loft/` — produced by
`bake_lightmaps.py --style=loft` and `render_views.py --style=loft` (with `--apt=` as usual). The "Minimal / Gamer loft"
switch in the panel just reloads the page with `?style=loft`, which every in-page link then preserves.

`site/app.js` and `site/style.css` are shared: the page's `config.js` (imported relative to the page URL) supplies viewpoints,
walk spots, the 2D plan, the cutaway centre and walk bounds. `blender/ktlib.py` holds the materials, primitives, wall builder and
furniture helpers used by both build scripts. To add a third apartment, copy `site/duna/` and `build_duna.py`.

- `site/app.js` — the viewer. `?mode=walk` boots it as the first-person walkthrough (same model, same lighting).
  Viewpoints/copy in each page's `config.js`; coordinates are metres, x east, y up, z south, origin at the NW corner of the plan.
  Render-on-demand (`dirty` flag): anything that changes the picture must set `dirty = true`. Lightmaps are sampled on UV
  channel 1 (`texture.channel = 1`). Static geometry arrives pre-merged from the bake; walls stay per side for the cutaway.
- `site/plan.js` / `site/duna/plan.js` — 2D plan for the minimap and walk-mode wall collision. Keep it in sync with the walls in the build script.
- `blender/build_apartment.py` / `build_duna.py` — the models (plan, furniture, and the `LIGHTS` / `SUN_ROT` / `RENDER_VIEWS`
  the bake and render scripts read). Rules: never let two boxes overlap with coincident faces (black in Cycles, z-fighting in
  WebGL); wall segments take `ext=(start, end)` and only extend into corners, never into openings; never split a straight wall
  into two collinear segments that both extend into the same junction (merge them instead). `build_walls` already offsets every
  wall top by a fraction of a millimetre so junction overlaps don't z-fight.
  Set `KT_SKIP_EXPORT=1` (the helper scripts do) so a rebuild never overwrites the baked `apartment.glb`.
- `blender/textures.py` — procedural seamless PBR sets, cached in `blender/tex/` (gitignored).
- `blender/bake_lightmaps.py [--apt=duna]` — the lighting bake (≈ 12 min on 4 CPU cores, a few minutes on a GPU, which it uses automatically; `--fast` ≈ 4 min). After ANY model change
  run it and commit that apartment's `apartment.glb`, `lightmaps/` and `footprints.json` together.
- `blender/render_views.py [--apt=duna]` — Cycles renders for the "Blender renders" tab (`--fast` for previews). Commit the JPGs.
