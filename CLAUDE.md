# Project notes for Claude Code

Two apps, one Pages deploy (see README):

- `site/` — **Apartment 3D** viewer at the site root. Plain HTML/CSS/JS + three.js vendored in `site/vendor` (no bundler, no CDN).
  Viewpoints, copy and stats are in the `VIEWS` array at the top of `site/app.js`. Coordinates are metres, x east, y up, z south,
  origin at the NW corner of the living room (same as the walkthrough's `plan.js`).
- `blender/build_apartment.py` — the model. Change geometry/materials there, re-run it, commit the new `site/apartment.glb`.
  Rules baked in: never let two boxes overlap with coincident faces (renders black in Cycles, z-fights in WebGL); wall segments
  take `ext=(start, end)` flags and only extend into corners, never into openings.
- `blender/textures.py` — procedural seamless PBR sets (numpy → jpg via bpy), cached in `blender/tex/`. Add a set there, then
  `tmat(...)` it in the build script; UVs are box-projected automatically from the set's tile size.
- `blender/render_views.py` — Cycles renders for the "Blender renders" tab; `--fast` for previews. Commit the JPGs.
- `src/` — the older first-person walkthrough (Vite + React Three Fiber), built to `dist/walk`. Keep `npm run build` green.

Deploy: push to `main` → Actions builds the walkthrough, copies `site/` on top, publishes to Pages.
