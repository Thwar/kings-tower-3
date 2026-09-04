# Project notes for Claude Code

Vite + React 18 + three r169 + @react-three/fiber 8 + drei 9 + @react-three/postprocessing.

- Units are metres. x → east, z → south, y → up. Origin is the NW corner of the living room. See `src/scene/plan.js`.
- Ceiling height `H = 2.6`, wall thickness `T = 0.14`.
- Materials: use `usePBR('<key>')` for anything textured; keys must exist in `scripts/fetch-assets.mjs` `TEX`. Never hard-fail when a texture is missing — the hook already falls back to flat colour.
- Camera state lives in a mutable ref (`cam.current`), not React state, to avoid re-renders each frame. The HUD reads it in its own rAF loop.
- Post-processing is disabled on touch devices for performance; keep that guard.
- `npm run build` must stay green. `npm run assets` needs internet (ambientcg.com, dl.polyhaven.org).
- Terrace railing, sliding doors and window are `glass` walls in `plan.js` — collision ignores nothing; the camera is meant to stay inside the apartment volume.
