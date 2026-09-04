# King's Tower · Dept. D — 3D walkthrough

Free-flying camera tour of the 1-bedroom (50.21 m² + 29.75 m² terrace), built with Vite + React Three Fiber.
Real PBR textures (ambientCG, CC0) + HDRI sky (Poly Haven, CC0), SSAO/bloom post-processing on desktop.

## Run
```bash
npm install
npm run assets   # downloads textures + HDRI into public/ (~40 MB, one-time)
npm run dev      # open the printed URL; add --host to test on your phone
```
Without `npm run assets` the scene still runs with flat colours and a procedural sky.

## Controls
- Desktop: click to lock mouse · WASD flies toward where you look · Q/E down/up
- Phone: left half of screen = stick (fly), right half = drag to look · ▲▼ = height
- Buttons jump to each room; "Vista aérea" lifts you above and hides the ceiling

## Layout
- `src/scene/plan.js` — walls, openings, rooms, camera presets (all in metres, from the plan)
- `src/scene/Apartment.jsx` — structure, floors, frames, ceiling, downlights
- `src/scene/Furniture.jsx` — furniture per room
- `src/scene/materials.js` — `usePBR(key)` loads a texture set, falls back to flat colour
- `src/controls/FlyControls.jsx` — camera, input, wall collision
- `src/ui/Hud.jsx` — minimap, room buttons, touch stick
- `scripts/fetch-assets.mjs` — asset downloader; change the ambientCG ids there to swap finishes

## Next steps (good Claude Code tasks)
1. Replace box furniture with glTF models (Poly Haven / Sketchfab CC0) via `useGLTF`
2. Bake lightmaps in Blender for the walls/floor and swap in `lightMap`
3. Add a day/night toggle (swap HDRI + downlight intensities)
4. Hotspots with `<Html>` labels for finishes and dimensions

## Deploy (works from a phone)
A GitHub Actions workflow is included (`.github/workflows/deploy.yml`). It installs, downloads the assets, builds and publishes to GitHub Pages on every push to `main`.
1. Create a repo on github.com and push this folder (or let Claude Code do it: "create a GitHub repo from this project and push it").
2. Repo → Settings → Pages → Source: **GitHub Actions**.
3. Wait ~2 min for the workflow; the URL appears under the Actions run / Settings → Pages.
