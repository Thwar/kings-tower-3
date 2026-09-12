import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// The first-person walkthrough is published under /walk/; the Blender-model viewer (site/) owns the root.
export default defineConfig({ base: './', plugins: [react()], server: { host: true }, build: { outDir: 'dist/walk', emptyOutDir: true } })
