import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js'
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js'
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js'
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js'
import { walls as PLAN_WALLS, rooms as PLAN_ROOMS, BOUNDS as PLAN, roomAt, T as WALL_T } from './plan.js'
const q = new URLSearchParams(location.search)   // ?mode=walk · ?env= ?exp= ?lm= tune lighting · ?ao=1

// ------------------------------------------------------------------ viewpoints
// pos / target in metres, apartment space: x east, y up, z south (origin = NW corner of the living room)
const VIEWS = [
  { key: 'whole',   name: 'Whole apartment', room: 'Whole apartment', area: '50.21 m² + 29.75 m² terrace', title: 'Room to live.',
    pos: [-7.5, 11.5, 16.5], target: [6.2, 0.5, 3.0], walk: [1.4, 0.9, -Math.PI / 2 - 0.3] },
  { key: 'living',  name: 'Living',          room: 'Living',            area: '≈ 14 m²',  title: 'Where the day lands.',
    pos: [-6.0, 5.0, 5.0], target: [2.8, 0.6, 2.2], walk: [3.0, 1.1, Math.PI / 2 + 0.35] },
  { key: 'kitchen', name: 'Kitchen & dining', room: 'Kitchen & dining', area: '≈ 12 m²',  title: 'Cook, eat, repeat.',
    pos: [9.0, 6.0, -5.5], target: [5.3, 0.7, 1.7], walk: [5.9, 0.75, Math.PI] },
  { key: 'bedroom', name: 'Bedroom',         room: 'Bedroom',           area: '≈ 12 m²',  title: 'Quiet corner.',
    pos: [6.2, 9.5, 11.0], target: [5.5, 0.3, 4.4], walk: [5.3, 3.25, Math.PI] },
  { key: 'bath',    name: 'Bathroom',        room: 'Bathroom',          area: '≈ 3.5 m²', title: 'Walk-in shower.',
    pos: [-3.5, 4.0, 9.0], target: [1.0, 0.8, 5.0], walk: [1.55, 4.75, Math.PI * 0.75] },
  { key: 'service', name: 'Service area',    room: 'Service area',      area: '≈ 2 m²',   title: 'Laundry, tucked away.',
    pos: [2.6, 5.0, 12.0], target: [2.55, 0.6, 5.3], walk: [2.7, 4.7, Math.PI] },
  { key: 'terrace', name: 'Terrace',         room: 'Terrace',           area: '29.75 m²', title: 'The outdoor room.',
    pos: [17.0, 5.0, -2.5], target: [10.3, 0.8, 3.0], walk: [8.6, 2.6, -Math.PI / 2] },
]
const CENTER = new THREE.Vector3(6.2, 1.3, 3.0)
// walk-mode collision: every plan wall (except the heads above doorways) as an XZ box, thickness T
const WALK_R = 0.22
const WALL_BOXES = PLAN_WALLS.filter(w => w[4] !== 'head').map(([x1, z1, x2, z2]) => ({
  minX: Math.min(x1, x2) - WALL_T / 2, maxX: Math.max(x1, x2) + WALL_T / 2, minZ: Math.min(z1, z2) - WALL_T / 2, maxZ: Math.max(z1, z2) + WALL_T / 2,
}))
const blocked = (x, z) => WALL_BOXES.some(b => x + WALK_R > b.minX && x - WALK_R < b.maxX && z + WALK_R > b.minZ && z - WALK_R < b.maxZ)
const WALK_ONLY = q.get('mode') === 'walk'
const BOUNDS = { minX: -0.3, maxX: 12.7, minZ: 0.1, maxZ: 5.85 }   // walk mode stays inside the apartment
const $ = s => document.querySelector(s)

// ------------------------------------------------------------------ renderer / scene
const canvas = $('#c')
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' })
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5))   // retina at 2× is the single biggest GPU cost; 1.5 is visually close
renderer.outputColorSpace = THREE.SRGBColorSpace
renderer.toneMapping = THREE.ACESFilmicToneMapping
renderer.shadowMap.enabled = true
renderer.toneMappingExposure = +(q.get('exp') ?? 1.0)
renderer.shadowMap.type = q.get('shadow') === 'basic' ? THREE.BasicShadowMap : THREE.PCFSoftShadowMap
renderer.shadowMap.autoUpdate = false   // static scene: the shadow map is re-rendered only when visibility changes (see requestShadows)
const requestShadows = () => { renderer.shadowMap.needsUpdate = true; dirty = true }
let dirty = true                        // render-on-demand flag; anything that changes the picture sets it

const scene = new THREE.Scene()
scene.background = new THREE.Color('#616a75')
const pmrem = new THREE.PMREMGenerator(renderer)
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
scene.environmentIntensity = +(q.get('env') ?? 0.4)

const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 200)
camera.position.set(...VIEWS[0].pos)

const sun = new THREE.DirectionalLight('#fff4e4', +(q.get('sun') ?? 4.5))
sun.position.set(5, 20, 1)   // near-overhead, a touch north: short shadows fall toward the default viewpoint
sun.castShadow = true
sun.shadow.mapSize.set(2048, 2048)
sun.shadow.bias = -0.0004
sun.shadow.normalBias = 0.03
sun.shadow.radius = 4
Object.assign(sun.shadow.camera, { left: -11, right: 11, top: 9, bottom: -9, near: 1, far: 50 })
sun.shadow.camera.updateProjectionMatrix()
sun.target.position.copy(CENTER)
scene.add(sun, sun.target)
const hemi = new THREE.HemisphereLight('#dfe7f0', '#6f6a63', 0.4)
scene.add(hemi)

// ground shadow catcher so the slab floats on a soft shadow like a model on a table
const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.ShadowMaterial({ opacity: 0.25 }))
ground.rotation.x = -Math.PI / 2
ground.position.y = -0.33
ground.receiveShadow = true
scene.add(ground)

// ------------------------------------------------------------------ post-processing (ambient occlusion, opt-in)
// GTAO gives contact shadows in corners but costs a second full scene pass plus several screen passes,
// which is the difference between 60 and 15 fps on integrated GPUs. Off by default; the "High quality" toggle
// (or ?ao=1) enables it, and the composer is built lazily the first time it is needed.
let composer = null, gtao = null, aoOn = false
function setAO(on) {
  aoOn = on
  if (on && !composer) {
    composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(1, 1, { samples: 4, type: THREE.HalfFloatType }))
    composer.addPass(new RenderPass(scene, camera))
    gtao = new GTAOPass(scene, camera, 1, 1)
    gtao.output = GTAOPass.OUTPUT.Default
    gtao.blendIntensity = 0.9
    gtao.updateGtaoMaterial({ radius: 0.35, distanceExponent: 1, thickness: 1, scale: 1.2, samples: 8, distanceFallOff: 1, screenSpaceRadius: false })
    gtao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 4, radiusExponent: 1, rings: 2, samples: 8 })
    composer.addPass(gtao)
    composer.addPass(new OutputPass())
    const w = canvas.clientWidth, h = canvas.clientHeight
    composer.setSize(w, h); gtao.setSize(w, h)
  }
  dirty = true
}

// adaptive resolution: if rendered frames stay slow, step the pixel ratio down (never back up, to avoid flicker)
const DPR_STEPS = [Math.min(devicePixelRatio, 1.5), 1.25, 1]
let dprIndex = 0, slowFrames = 0, lastFrameStart = 0
function noteFrameTime(ms) {
  if (ms > 24) slowFrames++; else slowFrames = Math.max(0, slowFrames - 1)
  if (slowFrames > 40 && dprIndex < DPR_STEPS.length - 1) {
    dprIndex++; slowFrames = 0
    renderer.setPixelRatio(DPR_STEPS[dprIndex])
    renderer.setSize(canvas.clientWidth, canvas.clientHeight, false)
    if (composer) { composer.setSize(canvas.clientWidth, canvas.clientHeight); gtao.setSize(canvas.clientWidth, canvas.clientHeight) }
    dirty = true
  }
}

// ------------------------------------------------------------------ controls
const controls = new OrbitControls(camera, canvas)
controls.addEventListener('change', () => { dirty = true })
controls.enableDamping = true
controls.dampingFactor = 0.08
controls.maxPolarAngle = Math.PI * 0.49
controls.minDistance = 2
controls.maxDistance = 60
controls.target.set(...VIEWS[0].target)
controls.autoRotateSpeed = 0.6
const ORBIT_BTNS = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN }
const PAN_BTNS = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE }

// ------------------------------------------------------------------ model
const parts = { walls: [], ceiling: [], glass: [] }   // walls: { mesh, side }
const footprints = []   // [x, z, w, d] of furniture, for the minimap
let model = null
const loader = new GLTFLoader()
const texLoader = new THREE.TextureLoader()
const LM_INTENSITY = +(q.get('lm') ?? 3.2)   // π (three's lightmap convention) × 2 (bake saved at −1 stop)
let baked = false
loader.load('apartment.glb', gltf => {
  model = gltf.scene
  model.traverse(o => {
    if (o.isMesh && o.userData.lightmap && o.geometry.attributes.uv1 && !o.material.transparent) {   // glass keeps its plain look
      baked = true
      const t = texLoader.load('lightmaps/' + o.userData.lightmap, () => { dirty = true })
      t.colorSpace = THREE.SRGBColorSpace
      t.flipY = false
      t.channel = 1          // sample with the lightmap UVs (TEXCOORD_1), not the texture UVs
      o.material.lightMap = t
      o.material.lightMapIntensity = LM_INTENSITY
      o.material.needsUpdate = true
    }
    if (o.isMesh && o.material.transparent) { o.material.depthWrite = false; o.renderOrder = 10 }
    if (!o.isMesh) return
    const x = o.userData || {}
    o.castShadow = x.part !== 'floor' && x.part !== 'glass' && x.part !== 'ceiling'
    o.receiveShadow = true
    if (x.part === 'glass') {
      o.material.transparent = true
      o.material.opacity = 0.28
      o.material.depthWrite = false
      o.material.roughness = 0.05
      o.material.envMapIntensity = 1.4
      o.renderOrder = 10
      parts.glass.push(o)
    }
    if (x.part === 'ceiling') parts.ceiling.push(o)
    if ((x.part === 'wall' || x.part === 'frame' || x.part === 'glass') && x.side && x.side !== 'I') parts.walls.push({ mesh: o, side: x.side })
    if (x.part === 'floor') o.material.envMapIntensity = 0.7
    if (x.part === 'furniture' || x.part === 'light') {
      // footprint for the minimap: XZ bounding box, skipping small bits (legs, handles, plant leaves)
      const b = new THREE.Box3().setFromObject(o)
      const w = b.max.x - b.min.x, d = b.max.z - b.min.z
      if (w * d > 0.05 && b.min.y < 1.2) footprints.push([b.min.x, b.min.z, w, d])
    }
    if (o.material.emissive && o.material.emissiveIntensity > 0) o.material.toneMapped = false
  })
  if (baked) {
    // lighting lives in the lightmaps: no real-time lights, no shadow map, just a faint environment for reflections
    sun.intensity = 0; hemi.intensity = 0; ground.visible = false
    renderer.shadowMap.enabled = false
    scene.environmentIntensity = +(q.get('env') ?? 0.18)
  } else mergeStatic(model)
  scene.add(model)
  $('#loading').classList.add('done')
  applyCutaway(true)
  requestShadows()
}, ev => {
  const p = ev.total ? Math.round(ev.loaded / ev.total * 100) : Math.min(99, Math.round(ev.loaded / 3.1e6 * 100))
  $('#loadingText').textContent = `Opening the apartment · ${p}%`
}, err => { $('#loadingText').textContent = 'Could not load the model'; console.error(err) })

// Merge everything that never changes visibility (furniture, lights, slab, floors) into one mesh per material.
// ~500 draw calls become ~40, which is what makes orbiting smooth on integrated GPUs and phones.
function mergeStatic(root) {
  const groups = new Map()
  const drop = []
  root.traverse(o => {
    if (!o.isMesh) return
    const p = o.userData.part
    if (p === 'wall' || p === 'frame' || p === 'glass' || p === 'ceiling') return   // toggled by the cutaway: keep separate
    o.updateWorldMatrix(true, false)
    const g = o.geometry.clone().applyMatrix4(o.matrixWorld)
    for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'uv') g.deleteAttribute(k)
    if (!g.attributes.uv) g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2))
    const key = o.material.uuid
    if (!groups.has(key)) groups.set(key, { material: o.material, geos: [], cast: false })
    const grp = groups.get(key)
    grp.geos.push(g); grp.cast = grp.cast || o.castShadow
    drop.push(o)
  })
  for (const o of drop) o.parent.remove(o)
  for (const { material, geos, cast } of groups.values()) {
    const merged = mergeGeometries(geos, false)
    if (!merged) continue
    const m = new THREE.Mesh(merged, material)
    m.castShadow = cast; m.receiveShadow = true
    m.userData.part = 'merged'
    root.add(m)
    for (const g of geos) g.dispose()
  }
}

// ------------------------------------------------------------------ cutaway
const state = { cutaway: true, ceiling: false, mode: 'orbit', view: 0 }
const lastHidden = new Set()
const OUTWARD = { N: new THREE.Vector3(0, 0, -1), S: new THREE.Vector3(0, 0, 1), E: new THREE.Vector3(1, 0, 0), W: new THREE.Vector3(-1, 0, 0) }
const toCam = new THREE.Vector3()
function applyCutaway(force = false) {
  if (!model) return
  const hidden = new Set()
  if (state.cutaway && state.mode !== 'walk') {
    toCam.copy(camera.position).sub(CENTER).setY(0).normalize()
    for (const [side, n] of Object.entries(OUTWARD)) {
      // hysteresis so a wall doesn't flicker while the camera hovers on its plane
      const d = toCam.dot(n)
      if (d > 0.12 || (d > -0.12 && lastHidden.has(side))) hidden.add(side)
    }
  }
  let changed = force || hidden.size !== lastHidden.size
  for (const s of hidden) if (!lastHidden.has(s)) changed = true
  if (changed) {
    for (const w of parts.walls) w.mesh.visible = !hidden.has(w.side)
    lastHidden.clear(); for (const s of hidden) lastHidden.add(s)
    requestShadows()
  }
  const showCeil = state.mode === 'walk' || state.ceiling || !state.cutaway
  if (parts.ceiling.length && parts.ceiling[0].visible !== showCeil) requestShadows()
  for (const c of parts.ceiling) c.visible = showCeil
}

// ------------------------------------------------------------------ camera tweens
let tween = null
function framed(pos, target) {
  // viewpoints are tuned for a ~1.5 aspect; on a phone in portrait, back off so the same subject fits
  const k = Math.max(1, 1.5 / Math.max(0.4, camera.aspect))
  const t = new THREE.Vector3(...target)
  return t.clone().add(new THREE.Vector3(...pos).sub(t).multiplyScalar(k))
}
function flyTo(pos, target, ms = 1400) {
  tween = { p0: camera.position.clone(), t0: controls.target.clone(), p1: framed(pos, target), t1: new THREE.Vector3(...target), start: performance.now(), ms }
}
const ease = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2

function setView(i) {
  state.view = i
  dirty = true
  const v = VIEWS[i]
  document.querySelectorAll('#views button').forEach((b, j) => b.classList.toggle('on', j === i))
  document.querySelectorAll('#rooms button').forEach((b, j) => b.classList.toggle('on', j + 1 === i))
  $('#introTitle').textContent = v.title
  $('#introRoom').textContent = v.room
  $('#introArea').textContent = v.area
  if (state.mode === 'walk') { setMode('walk'); return }   // in the walkthrough, the room list teleports to each room's standing spot
  flyTo(v.pos, v.target)
}

// ------------------------------------------------------------------ walk mode (first person)
const walk = { keys: {}, yaw: 0, pitch: -0.05, dragging: false, last: null, stick: { x: 0, y: 0 } }
const FOV_ORBIT = 30, FOV_WALK = 75   // the isometric views want a long lens; a person sees ~75° across
let fovTarget = FOV_ORBIT
function setMode(m) {
  dirty = true
  const wasWalk = state.mode === 'walk'
  state.mode = m
  document.querySelectorAll('.modes button').forEach(b => b.classList.toggle('on', b.dataset.mode === m))
  if (m === 'walk') {
    controls.enabled = false
    const v = VIEWS[state.view]
    // each viewpoint has a standing spot on open floor and a heading into the room
    const [wx, wz, yaw] = v.walk
    camera.position.set(wx, 1.6, wz)
    walk.yaw = yaw
    fovTarget = FOV_WALK
    walk.pitch = -0.08
    tween = null
    $('#hint').textContent = matchMedia('(pointer:coarse)').matches ? 'Left: joystick · right: drag to look' : 'Drag to look · WASD / arrows to walk · Q/E for height'
  } else {
    controls.enabled = true
    fovTarget = FOV_ORBIT
    controls.mouseButtons = m === 'pan' ? PAN_BTNS : ORBIT_BTNS
    controls.touches = m === 'pan' ? { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE } : { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN }
    if (wasWalk) {
      // re-seat orbit target ahead of the walker so the camera doesn't jump
      const f = new THREE.Vector3(0, 0, -1).applyEuler(new THREE.Euler(walk.pitch, walk.yaw, 0, 'YXZ'))
      controls.target.copy(camera.position).addScaledVector(f, 4)
    }
    $('#hint').textContent = m === 'pan' ? 'Drag to pan · Right-drag to orbit · WASD to move' : 'Drag to orbit · Right-drag to pan · WASD to move'
  }
  applyCutaway(true)
}
addEventListener('keydown', e => { walk.keys[e.code] = true; dirty = true })
addEventListener('keyup', e => { walk.keys[e.code] = false })
canvas.addEventListener('pointerdown', e => { if (state.mode === 'walk') { walk.dragging = true; walk.last = [e.clientX, e.clientY]; canvas.setPointerCapture(e.pointerId) } })
canvas.addEventListener('pointermove', e => {
  if (state.mode !== 'walk' || !walk.dragging) return
  walk.yaw -= (e.clientX - walk.last[0]) * 0.0045
  walk.pitch = THREE.MathUtils.clamp(walk.pitch - (e.clientY - walk.last[1]) * 0.0045, -1.3, 1.3)
  walk.last = [e.clientX, e.clientY]
  dirty = true
})
canvas.addEventListener('pointerup', () => { walk.dragging = false })
canvas.addEventListener('pointercancel', () => { walk.dragging = false })
// phones in walk mode: left half of the screen is a joystick, right half drags to look
const stickEl = $('#stick'), knobEl = $('#knob')
let moveT = null, lookT = null, lookLast = null
canvas.addEventListener('touchstart', e => {
  if (state.mode !== 'walk') return
  for (const t of e.changedTouches) {
    if (t.clientX < innerWidth / 2 && moveT === null) {
      moveT = { id: t.identifier, x: t.clientX, y: t.clientY }
      const r = $('#stage').getBoundingClientRect()
      stickEl.style.left = (t.clientX - r.left - 55) + 'px'; stickEl.style.top = (t.clientY - r.top - 55) + 'px'
      knobEl.style.left = '32px'; knobEl.style.top = '32px'; stickEl.hidden = false
    } else if (lookT === null) { lookT = t.identifier; lookLast = { x: t.clientX, y: t.clientY } }
  }
  e.preventDefault()
}, { passive: false })
canvas.addEventListener('touchmove', e => {
  if (state.mode !== 'walk') return
  for (const t of e.changedTouches) {
    if (moveT && t.identifier === moveT.id) {
      let dx = t.clientX - moveT.x, dy = t.clientY - moveT.y; const d = Math.hypot(dx, dy), max = 45
      if (d > max) { dx *= max / d; dy *= max / d }
      walk.stick = { x: dx / max, y: dy / max }
      knobEl.style.left = (32 + dx) + 'px'; knobEl.style.top = (32 + dy) + 'px'
    } else if (t.identifier === lookT) {
      walk.yaw -= (t.clientX - lookLast.x) * 0.005
      walk.pitch = THREE.MathUtils.clamp(walk.pitch - (t.clientY - lookLast.y) * 0.005, -1.3, 1.3)
      lookLast = { x: t.clientX, y: t.clientY }
    }
  }
  dirty = true
  e.preventDefault()
}, { passive: false })
const touchEnd = e => {
  for (const t of e.changedTouches) {
    if (moveT && t.identifier === moveT.id) { moveT = null; walk.stick = { x: 0, y: 0 }; stickEl.hidden = true }
    if (t.identifier === lookT) lookT = null
  }
}
canvas.addEventListener('touchend', touchEnd); canvas.addEventListener('touchcancel', touchEnd)

function stepWalk(dt) {
  const k = walk.keys
  let f = (k.KeyW || k.ArrowUp ? 1 : 0) - (k.KeyS || k.ArrowDown ? 1 : 0)
  let s = (k.KeyD || k.ArrowRight ? 1 : 0) - (k.KeyA || k.ArrowLeft ? 1 : 0)
  const u = (k.KeyE ? 1 : 0) - (k.KeyQ ? 1 : 0)
  f -= walk.stick.y; s += walk.stick.x                       // phone joystick
  const len = Math.hypot(f, s); if (len > 1) { f /= len; s /= len }
  const sp = 2.0 * dt, sin = Math.sin(walk.yaw), cos = Math.cos(walk.yaw)
  const dx = (-sin * f + cos * s) * sp, dz = (-cos * f - sin * s) * sp
  const p = camera.position
  if (!blocked(p.x + dx, p.z)) p.x += dx      // slide along walls: test each axis separately
  if (!blocked(p.x, p.z + dz)) p.z += dz
  p.y = THREE.MathUtils.clamp(p.y + u * sp, 0.6, 2.35)
  p.x = THREE.MathUtils.clamp(p.x, BOUNDS.minX, BOUNDS.maxX)
  p.z = THREE.MathUtils.clamp(p.z, BOUNDS.minZ, BOUNDS.maxZ)
  camera.rotation.order = 'YXZ'
  camera.rotation.set(walk.pitch, walk.yaw, 0)
}

// keyboard in Orbit / Pan mode: W/S dolly along the view, A/D strafe, Q/E up/down. Camera and target move together.
const _fwd = new THREE.Vector3(), _right = new THREE.Vector3(), _step = new THREE.Vector3()
function stepOrbitKeys(dt) {
  const k = walk.keys
  const f = (k.KeyW || k.ArrowUp ? 1 : 0) - (k.KeyS || k.ArrowDown ? 1 : 0)
  const r = (k.KeyD || k.ArrowRight ? 1 : 0) - (k.KeyA || k.ArrowLeft ? 1 : 0)
  const u = (k.KeyE ? 1 : 0) - (k.KeyQ ? 1 : 0)
  if (!f && !r && !u) return
  tween = null
  _fwd.copy(controls.target).sub(camera.position).setY(0).normalize()
  _right.crossVectors(_fwd, camera.up).normalize()
  const dist = camera.position.distanceTo(controls.target)
  const speed = THREE.MathUtils.clamp(dist * 0.35, 1.2, 6) * dt      // faster when zoomed out
  _step.set(0, 0, 0).addScaledVector(_fwd, f * speed).addScaledVector(_right, r * speed).addScaledVector(camera.up, u * speed)
  camera.position.add(_step)
  controls.target.add(_step)
  controls.target.y = Math.max(0.1, controls.target.y)
}

// ------------------------------------------------------------------ UI wiring
const viewsEl = $('#views')
VIEWS.forEach((v, i) => {
  const li = document.createElement('li')
  li.innerHTML = `<button><small>${String(i + 1).padStart(2, '0')}</small><span>${v.name}</span><em>↗</em></button>`
  li.querySelector('button').addEventListener('click', () => setView(i))
  viewsEl.appendChild(li)
})
setView(0)
if (WALK_ONLY) {
  document.title = "King's Tower · Dept. D — walkthrough"
  $('#navWalk').classList.add('on'); $('#nav3d').classList.remove('on')
  $('#linkWalk').href = './'; $('#linkWalk').textContent = '→ Back to the cutaway model'
  $('#footWalk').href = './'; $('#footWalk').textContent = 'Back to the model ↗'
  document.querySelector('.chip').innerHTML = '<span class="dot"></span>WALKTHROUGH<i>FIRST PERSON</i>'
  $('#tgCut').closest('label').hidden = true; $('#tgCeil').closest('label').hidden = true; $('#tgSpin').closest('label').hidden = true
  // full-bleed: no side panel, room chips float over the view
  document.body.classList.add('walkmode')
  const rooms = $('#rooms'); rooms.hidden = false
  VIEWS.forEach((v, i) => { if (i === 0) return; const b = document.createElement('button'); b.textContent = v.name; b.addEventListener('click', () => setView(i)); rooms.appendChild(b) })
  setMode('walk')
}
resize()
if (!WALK_ONLY) { camera.position.copy(framed(VIEWS[0].pos, VIEWS[0].target)); controls.target.set(...VIEWS[0].target); tween = null }

$('#tgCut').addEventListener('change', e => { state.cutaway = e.target.checked; applyCutaway(true) })
$('#tgCeil').addEventListener('change', e => { state.ceiling = e.target.checked; applyCutaway(true) })
$('#tgSpin').addEventListener('change', e => { controls.autoRotate = e.target.checked; dirty = true })
$('#tgAO').addEventListener('change', e => setAO(e.target.checked))
if (q.get('ao') === '1') { $('#tgAO').checked = true; setAO(true) }
document.querySelectorAll('.modes button').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)))
document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === b))
  $('#tab3d').hidden = b.dataset.tab !== '3d'
  $('#tabRenders').hidden = b.dataset.tab !== 'renders'
}))

const spherical = new THREE.Spherical()
function nudge(dTheta = 0, dPhi = 0, zoom = 1) {
  dirty = true
  if (state.mode === 'walk') { walk.yaw += dTheta; walk.pitch = THREE.MathUtils.clamp(walk.pitch + dPhi, -1.3, 1.3); return }
  tween = null
  const off = camera.position.clone().sub(controls.target)
  spherical.setFromVector3(off)
  spherical.theta += dTheta
  spherical.phi = THREE.MathUtils.clamp(spherical.phi + dPhi, 0.05, controls.maxPolarAngle)
  spherical.radius = THREE.MathUtils.clamp(spherical.radius * zoom, controls.minDistance, controls.maxDistance)
  camera.position.copy(controls.target).add(off.setFromSpherical(spherical))
}
const ACTS = {
  rotL: () => nudge(-Math.PI / 8), rotR: () => nudge(Math.PI / 8),
  up: () => nudge(0, -0.12), down: () => nudge(0, 0.12),
  zoomIn: () => nudge(0, 0, 0.8), zoomOut: () => nudge(0, 0, 1.25),
  reset: () => setView(state.view),
  full: () => document.fullscreenElement ? document.exitFullscreen() : $('#stage').requestFullscreen?.(),
}
document.querySelectorAll('.toolbar button').forEach(b => b.addEventListener('click', () => ACTS[b.dataset.act]()))

// renders gallery
const gallery = $('#gallery')
VIEWS.forEach((v, i) => {
  const f = document.createElement('figure')
  f.innerHTML = `<img loading="lazy" src="renders/${v.key}.jpg" alt="${v.name} render" /><figcaption><small>${String(i + 1).padStart(2, '0')}</small>${v.name}</figcaption>`
  f.addEventListener('click', () => { $('#lightboxImg').src = `renders/${v.key}.jpg`; $('#lightboxCap').textContent = `${v.name} · Blender Cycles render`; $('#lightbox').hidden = false })
  gallery.appendChild(f)
})
$('#lightboxClose').addEventListener('click', () => { $('#lightbox').hidden = true })
$('#lightbox').addEventListener('click', e => { if (e.target === e.currentTarget) e.currentTarget.hidden = true })

// phone: drag the sheet up/down
const panel = $('#panel')
$('#grip').addEventListener('click', () => panel.classList.toggle('tall'))

// ------------------------------------------------------------------ minimap (2D plan)
const map = $('#map'), mg = map.getContext('2d')
const MS = map.width / (PLAN.x1 - PLAN.x0)
const mx = x => (x - PLAN.x0) * MS, mz = z => (z - PLAN.z0) * MS
const planLayer = document.createElement('canvas'); planLayer.width = map.width; planLayer.height = map.height
let planDrawn = false
fetch('footprints.json').then(r => r.ok ? r.json() : []).then(list => { if (list.length) { footprints.length = 0; footprints.push(...list); planDrawn = false; dirty = true } }).catch(() => {})
function drawPlanLayer() {
  const g = planLayer.getContext('2d')
  g.clearRect(0, 0, map.width, map.height)
  for (const r of PLAN_ROOMS) { const [a, b, c, d] = r.rect; g.fillStyle = r.fill; g.fillRect(mx(a), mz(b), (c - a) * MS, (d - b) * MS) }
  g.fillStyle = 'rgba(255,255,255,.45)'
  for (const [x, z, w, d] of footprints) g.fillRect(mx(x), mz(z), w * MS, d * MS)
  g.lineCap = 'butt'
  for (const [x1, z1, x2, z2, kind] of PLAN_WALLS) {
    g.setLineDash(kind === 'head' ? [3, 3] : [])
    g.strokeStyle = kind === 'glass' ? '#6fb6dc' : kind === 'head' ? '#9aa0a8' : '#262a2f'
    g.lineWidth = kind === 'wall' ? WALL_T * MS : 2
    g.beginPath(); g.moveTo(mx(x1), mz(z1)); g.lineTo(mx(x2), mz(z2)); g.stroke()
  }
  g.setLineDash([])
  g.font = '600 9px ' + getComputedStyle(document.body).fontFamily; g.fillStyle = 'rgba(30,32,36,.55)'; g.textAlign = 'center'
  for (const r of PLAN_ROOMS) { const [a, b, c, d] = r.rect; if ((c - a) > 1.3) g.fillText(r.label.toUpperCase(), mx((a + c) / 2), mz((b + d) / 2) + 3) }
  planDrawn = true
}
const mapRoomEl = $('#mapRoom')
let lastRoomLabel = ''
function drawMinimap() {
  if (!planDrawn && model) drawPlanLayer()
  mg.clearRect(0, 0, map.width, map.height)
  mg.drawImage(planLayer, 0, 0)
  const walkMode = state.mode === 'walk'
  const px = camera.position.x, pz = camera.position.z
  const tx = walkMode ? px - Math.sin(walk.yaw) * 3 : controls.target.x
  const tz = walkMode ? pz - Math.cos(walk.yaw) * 3 : controls.target.z
  const cx = Math.min(Math.max(px, PLAN.x0 + 0.2), PLAN.x1 - 0.2), cz = Math.min(Math.max(pz, PLAN.z0 + 0.2), PLAN.z1 - 0.2)
  const a = Math.atan2(tz - pz, tx - px), spread = walkMode ? 0.5 : 0.35
  // view cone from the (clamped) camera toward what it looks at
  mg.fillStyle = 'rgba(37,99,235,.18)'
  mg.beginPath(); mg.moveTo(mx(cx), mz(cz)); mg.arc(mx(cx), mz(cz), walkMode ? 26 : 40, a - spread, a + spread); mg.closePath(); mg.fill()
  if (!walkMode) {   // orbit target
    mg.strokeStyle = '#2563eb'; mg.lineWidth = 1.5
    mg.beginPath(); mg.arc(mx(tx), mz(tz), 5, 0, Math.PI * 2); mg.stroke()
    mg.beginPath(); mg.moveTo(mx(tx) - 8, mz(tz)); mg.lineTo(mx(tx) + 8, mz(tz)); mg.moveTo(mx(tx), mz(tz) - 8); mg.lineTo(mx(tx), mz(tz) + 8); mg.stroke()
  }
  mg.fillStyle = '#2563eb'; mg.beginPath(); mg.arc(mx(cx), mz(cz), 4.5, 0, Math.PI * 2); mg.fill()
  mg.strokeStyle = '#fff'; mg.lineWidth = 1.5; mg.stroke()
  const r = roomAt(walkMode ? px : tx, walkMode ? pz : tz)
  const label = state.mode !== 'walk' && state.view === 0 && !tween ? 'Whole apartment' : (r ? r.label : 'Outside')
  if (label !== lastRoomLabel) { mapRoomEl.textContent = label; lastRoomLabel = label }
}
map.addEventListener('click', e => {
  const rect = map.getBoundingClientRect()
  const x = PLAN.x0 + (e.clientX - rect.left) / rect.width * (PLAN.x1 - PLAN.x0)
  const z = PLAN.z0 + (e.clientY - rect.top) / rect.height * (PLAN.z1 - PLAN.z0)
  if (state.mode === 'walk') { camera.position.x = x; camera.position.z = z; return }
  // keep the current orbit offset, move the target to the clicked point
  const off = camera.position.clone().sub(controls.target)
  const t = new THREE.Vector3(x, 0.6, z)
  flyTo(t.clone().add(off).toArray(), t.toArray(), 900)
})

window.__app = { renderer, scene, camera, controls, sun, parts, state, walk, blocked }   // debugging hook

// ------------------------------------------------------------------ resize + loop
function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight
  if (canvas.width !== Math.floor(w * renderer.getPixelRatio()) || canvas.height !== Math.floor(h * renderer.getPixelRatio())) {
    renderer.setSize(w, h, false)
    dirty = true
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    if (composer) { composer.setSize(w, h); gtao.setSize(w, h) }
  }
}
new ResizeObserver(resize).observe(canvas)
document.addEventListener('fullscreenchange', resize)

let prev = performance.now()
renderer.setAnimationLoop(now => {
  const dt = Math.min(0.05, (now - prev) / 1000); prev = now
  resize()
  if (tween) {
    const k = ease(Math.min(1, (now - tween.start) / tween.ms))
    camera.position.lerpVectors(tween.p0, tween.p1, k)
    controls.target.lerpVectors(tween.t0, tween.t1, k)
    if (k >= 1) tween = null
  }
  if (Math.abs(camera.fov - fovTarget) > 0.05) {   // ease the lens change so entering Walk doesn't snap
    camera.fov += (fovTarget - camera.fov) * Math.min(1, dt * 8)
    camera.updateProjectionMatrix()
    dirty = true
  }
  const keysHeld = Object.values(walk.keys).some(Boolean) || walk.stick.x || walk.stick.y
  if (state.mode === 'walk') { if (keysHeld || walk.dragging) dirty = true; stepWalk(dt) }
  else { stepOrbitKeys(dt); if (controls.update()) dirty = true }   // update() returns true while damping still moves the camera
  if (tween || controls.autoRotate) dirty = true
  applyCutaway()
  if (!dirty) return   // nothing changed: skip the frame entirely (idle costs nothing)
  dirty = false
  drawMinimap()
  if (aoOn && composer) composer.render(); else renderer.render(scene, camera)
  // frame pacing is only meaningful across consecutive rendered frames (GPU work is async, so CPU timing of render() is not)
  if (now - lastFrameStart < 100) noteFrameTime(now - lastFrameStart)
  lastFrameStart = now
})
