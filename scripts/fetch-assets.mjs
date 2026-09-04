// Downloads CC0 PBR textures (ambientCG) and an HDRI (Poly Haven) into /public.
// Run: npm run assets
import { mkdirSync, writeFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import AdmZip from 'adm-zip'

const TEX = {
  // key: ambientCG asset id (1K JPG). Swap ids to taste — browse https://ambientcg.com
  woodFloor: 'WoodFloor051',
  tile: 'Tiles074',
  terrace: 'PavingStones131',
  wall: 'Plaster001',
  concrete: 'Concrete034',
  fabric: 'Fabric030',
  marble: 'Marble012',
  metal: 'Metal032',
}
const HDRI = { name: 'kloofendal_48d_partly_cloudy_puresky', res: '2k' }

const texDir = 'public/textures', hdrDir = 'public/hdri'
mkdirSync(texDir, { recursive: true }); mkdirSync(hdrDir, { recursive: true })

async function download(url) {
  const r = await fetch(url, { headers: { 'User-Agent': 'kings-tower-3d' } })
  if (!r.ok) throw new Error(`${r.status} ${url}`)
  return Buffer.from(await r.arrayBuffer())
}

const manifest = {}
for (const [key, id] of Object.entries(TEX)) {
  const out = join(texDir, key)
  if (existsSync(join(out, 'color.jpg'))) { manifest[key] = true; console.log('skip', key); continue }
  process.stdout.write(`↓ ${id} … `)
  try {
    const zip = new AdmZip(await download(`https://ambientcg.com/get?file=${id}_1K-JPG.zip`))
    mkdirSync(out, { recursive: true })
    for (const e of zip.getEntries()) {
      const n = e.entryName
      const map = /Color\.jpg$/i.test(n) ? 'color' : /NormalGL\.jpg$/i.test(n) ? 'normal' : /Roughness\.jpg$/i.test(n) ? 'roughness'
        : /AmbientOcclusion\.jpg$/i.test(n) ? 'ao' : null
      if (map) writeFileSync(join(out, `${map}.jpg`), e.getData())
    }
    manifest[key] = true; console.log('ok')
  } catch (e) { console.log('failed:', e.message); manifest[key] = false }
}
writeFileSync(join(texDir, 'manifest.json'), JSON.stringify(manifest, null, 2))

const hdrOut = join(hdrDir, 'sky.hdr')
if (!existsSync(hdrOut)) {
  process.stdout.write(`↓ HDRI ${HDRI.name} … `)
  try {
    writeFileSync(hdrOut, await download(`https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/${HDRI.res}/${HDRI.name}_${HDRI.res}.hdr`))
    console.log('ok')
  } catch (e) { console.log('failed:', e.message) }
}
console.log('\nTextures:', Object.values(manifest).filter(Boolean).length, '/', Object.keys(TEX).length, '· HDRI:', existsSync(hdrOut))
