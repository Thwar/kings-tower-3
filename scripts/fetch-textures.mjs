// Downloads CC0 photo-scanned PBR sets (ambientCG) into site/textures/<key>/ and writes a manifest.
// Runs on the GitHub Actions runner at deploy time (the dev sandbox has no internet); the viewer swaps these
// in over the procedural textures when the manifest is present. Physical size per set is recorded so the
// viewer can keep the world-space tiling that the model's UVs assume.
import { mkdirSync, writeFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { execSync } from 'node:child_process'

// key (material name prefix in the model) → ambientCG id, physical size of one tile in metres
const SETS = {
  oak_floor: ['WoodFloor051', 2],
  oak:       ['Wood049', 1],
  walnut:    ['Wood051', 1],
  plaster:   ['Plaster001', 2],
  concrete:  ['Concrete034', 2],
  charcoal:  ['Fabric030', 1],
  linen:     ['Fabric025', 1],
  wool_rug:  ['Fabric042', 1],
  leather:   ['Leather026', 1],
  quartz:    ['Marble012', 2],
  tile:      ['Tiles074', 2],
  paving:    ['PavingStones131', 2],
  brushed:   ['Metal032', 1],
}
const out = 'site/textures'
mkdirSync(out, { recursive: true })
const manifest = {}
for (const [key, [id, size]] of Object.entries(SETS)) {
  const dir = join(out, key)
  if (existsSync(join(dir, 'color.jpg'))) { manifest[key] = { size }; continue }
  try {
    const r = await fetch(`https://ambientcg.com/get?file=${id}_1K-JPG.zip`, { headers: { 'User-Agent': 'kings-tower-3d' } })
    if (!r.ok) throw new Error(`${r.status}`)
    const zip = join(out, `${key}.zip`)
    writeFileSync(zip, Buffer.from(await r.arrayBuffer()))
    mkdirSync(dir, { recursive: true })
    execSync(`unzip -o -q "${zip}" -d "${dir}"`)
    execSync(`cd "${dir}" && (mv *_Color.jpg color.jpg; mv *_NormalGL.jpg normal.jpg; mv *_Roughness.jpg roughness.jpg; ls | grep -vE '^(color|normal|roughness)\\.jpg$' | xargs -r rm -rf)`)
    execSync(`rm -f "${zip}"`)   // absolute to the repo root, not the set folder
    manifest[key] = { size }
    console.log('ok', key, id)
  } catch (e) { console.log('failed', key, id, e.message) }
}
writeFileSync(join(out, 'manifest.json'), JSON.stringify(manifest))
console.log('textures:', Object.keys(manifest).length, '/', Object.keys(SETS).length)
