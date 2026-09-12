# Project notes for Claude Code

One static site (`site/`) + one Blender pipeline (`blender/`). No npm, no bundler. Push to `main` → Pages deploys `site/`.

- `site/app.js` — the viewer. `?mode=walk` boots it as the first-person walkthrough (same model, same lighting).
  Viewpoints/copy in `VIEWS`; coordinates are metres, x east, y up, z south, origin at the NW corner of the living room.
  Render-on-demand (`dirty` flag): anything that changes the picture must set `dirty = true`. Lightmaps are sampled on UV
  channel 1 (`texture.channel = 1`). Static geometry arrives pre-merged from the bake; walls stay per side for the cutaway.
- `site/plan.js` — 2D plan for the minimap and walk-mode wall collision. Keep it in sync with the walls in `build_apartment.py`.
- `blender/build_apartment.py` — the model. Rules: never let two boxes overlap with coincident faces (black in Cycles,
  z-fighting in WebGL); wall segments take `ext=(start, end)` and only extend into corners, never into openings.
  Set `KT_SKIP_EXPORT=1` (the helper scripts do) so a rebuild never overwrites the baked `site/apartment.glb`.
- `blender/textures.py` — procedural seamless PBR sets, cached in `blender/tex/` (gitignored).
- `blender/bake_lightmaps.py` — the lighting bake (full ≈ 25 min CPU, `--fast` ≈ 5 min). After ANY model change run it and
  commit `site/apartment.glb`, `site/lightmaps/` and `site/footprints.json` together.
- `blender/render_views.py` — Cycles renders for the "Blender renders" tab (`--fast` for previews). Commit the JPGs.
