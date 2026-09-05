import React, { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { Environment, Sky, BakeShadows } from '@react-three/drei'
import { EffectComposer, N8AO, Bloom, SMAA, ToneMapping } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'
import * as THREE from 'three'
import { Apartment } from './scene/Apartment.jsx'
import { ManifestCtx, useManifest, flat } from './scene/materials.js'
import { FlyControls } from './controls/FlyControls.jsx'
import { Hud } from './ui/Hud.jsx'
import { spots } from './scene/plan.js'

const isTouch = matchMedia('(pointer:coarse)').matches

// Anything that throws inside Suspense (a failed fetch, a bad asset) would otherwise unmount the
// whole canvas and leave a blank page. Fall back to `fallback` instead and keep rendering.
class Boundary extends React.Component {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(e) { console.warn('[scene] fallback:', e?.message || e) }
  render() { return this.state.failed ? this.props.fallback ?? null : this.props.children }
}

// Procedural sky + lighting when no HDRI is available. No network needed.
const ProceduralSky = () => <Sky sunPosition={[9, 16, -6]} turbidity={6} rayleigh={1.5} />

function Skyline() {
  const items = useMemo(() => {
    let seed = 7; const rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280 }
    const out = []
    for (let i = 0; i < 70; i++) {
      const w = 4 + rnd() * 8, h = 6 + rnd() * 28, d = 4 + rnd() * 8, a = rnd() * Math.PI * 2, r = 26 + rnd() * 80
      const x = 6 + Math.cos(a) * r, z = 3 + Math.sin(a) * r
      if (z < 12 && z > -8 && x > -8 && x < 20) continue
      out.push({ s: [w, h, d], p: [x, -18 + h / 2, z], c: new THREE.Color().setHSL(0.07, 0.07, 0.5 + rnd() * 0.22) })
    }
    return out
  }, [])
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -18, 0]} material={flat.ground}><planeGeometry args={[400, 400]} /></mesh>
      {items.map((b, i) => (
        <mesh key={i} position={b.p}><boxGeometry args={b.s} /><meshStandardMaterial color={b.c} roughness={1} /></mesh>
      ))}
    </group>
  )
}

function Scene({ cam, input, hasHdri }) {
  const [above, setAbove] = useState(false)
  return (
    <>
      <Boundary fallback={<ProceduralSky />}>
        <Suspense fallback={<ProceduralSky />}>
          {hasHdri
            ? <Environment files={import.meta.env.BASE_URL + 'hdri/sky.hdr'} background blur={0} />
            : <><ProceduralSky /><Environment preset="city" /></>}
        </Suspense>
      </Boundary>
      <hemisphereLight args={['#dfe8f2', '#7d6f60', 1.1]} />
      <directionalLight
        position={[9, 16, -6]} intensity={3} color="#fff3df" castShadow
        shadow-mapSize={[2048, 2048]} shadow-bias={-0.0002} shadow-normalBias={0.06}
        shadow-camera-left={-9} shadow-camera-right={9} shadow-camera-top={8} shadow-camera-bottom={-8} shadow-camera-near={2} shadow-camera-far={45}
      />
      <Apartment showCeiling={!above} />
      <Skyline />
      <FlyControls cam={cam} input={input} onUpdate={a => setAbove(v => (v === a ? v : a))} />
      <BakeShadows />
      {!isTouch && (
        <EffectComposer disableNormalPass multisampling={0}>
          <N8AO aoRadius={0.6} intensity={2.5} distanceFalloff={0.8} quality="medium" />
          <Bloom luminanceThreshold={1.2} intensity={0.25} mipmapBlur />
          <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
          <SMAA />
        </EffectComposer>
      )}
    </>
  )
}

export default function App() {
  const manifest = useManifest()
  const [hasHdri, setHasHdri] = useState(null)
  useEffect(() => { fetch(import.meta.env.BASE_URL + 'hdri/sky.hdr', { method: 'HEAD' }).then(r => setHasHdri(r.ok && (r.headers.get('content-type') || '').indexOf('html') < 0)).catch(() => setHasHdri(false)) }, [])
  const s = spots.living
  const cam = useRef({ x: s[0], y: s[1], z: s[2], yaw: s[3], pitch: s[4] })
  const input = useRef({ move: { x: 0, y: 0 }, vert: 0, stick: null })

  if (manifest === null || hasHdri === null) return <div className="loading">Cargando…</div>
  return (
    <ManifestCtx.Provider value={manifest}>
      <Canvas
        shadows dpr={[1, isTouch ? 1.5 : 2]}
        camera={{ fov: 68, near: 0.08, far: 300, position: [s[0], s[1], s[2]] }}
        gl={{ antialias: isTouch, powerPreference: 'high-performance', toneMapping: isTouch ? THREE.ACESFilmicToneMapping : THREE.NoToneMapping, toneMappingExposure: 0.95 }}
        onCreated={({ gl }) => { gl.shadowMap.type = THREE.PCFSoftShadowMap }}
      >
        <Boundary fallback={<><ProceduralSky /><hemisphereLight args={['#dfe8f2', '#7d6f60', 1.1]} /><Apartment showCeiling /><FlyControls cam={cam} input={input} /></>}>
          <Suspense fallback={null}>
            <Scene cam={cam} input={input} hasHdri={hasHdri} />
          </Suspense>
        </Boundary>
      </Canvas>
      <Hud cam={cam} input={input} hintDesktop={!isTouch} />
    </ManifestCtx.Provider>
  )
}
