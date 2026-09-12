import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'

// ------------------------------------------------------------------ viewpoints
// pos / target in metres, apartment space: x east, y up, z south (origin = NW corner of the living room)
const VIEWS = [
  { key: 'whole',   name: 'Whole apartment', room: 'Whole apartment', area: '50.21 m² + 29.75 m² terrace', title: 'Room to live.',
    pos: [-7.5, 11.5, 16.5], target: [6.2, 0.5, 3.0] },
  { key: 'living',  name: 'Living',          room: 'Living',            area: '≈ 14 m²',  title: 'Where the day lands.',
    pos: [-6.0, 5.0, 5.0], target: [2.8, 0.6, 2.2] },
  { key: 'kitchen', name: 'Kitchen & dining', room: 'Kitchen & dining', area: '≈ 12 m²',  title: 'Cook, eat, repeat.',
    pos: [9.0, 6.0, -5.5], target: [5.3, 0.7, 1.7] },
  { key: 'bedroom', name: 'Bedroom',         room: 'Bedroom',           area: '≈ 12 m²',  title: 'Quiet corner.',
    pos: [7.8, 6.8, 12.5], target: [5.4, 0.5, 4.5] },
  { key: 'bath',    name: 'Bathroom',        room: 'Bathroom',          area: '≈ 3.5 m²', title: 'Walk-in shower.',
    pos: [-3.5, 4.0, 9.0], target: [1.0, 0.8, 5.0] },
  { key: 'service', name: 'Service area',    room: 'Service area',      area: '≈ 2 m²',   title: 'Laundry, tucked away.',
    pos: [2.6, 5.0, 12.0], target: [2.55, 0.6, 5.3] },
  { key: 'terrace', name: 'Terrace',         room: 'Terrace',           area: '29.75 m²', title: 'The outdoor room.',
    pos: [17.0, 5.0, -2.5], target: [10.3, 0.8, 3.0] },
]
const CENTER = new THREE.Vector3(6.2, 1.3, 3.0)
const BOUNDS = { minX: -0.3, maxX: 12.7, minZ: 0.1, maxZ: 5.85 }   // walk mode stays inside the apartment
const $ = s => document.querySelector(s)

// ------------------------------------------------------------------ renderer / scene
const canvas = $('#c')
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' })
renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
renderer.outputColorSpace = THREE.SRGBColorSpace
renderer.toneMapping = THREE.ACESFilmicToneMapping
renderer.shadowMap.enabled = true
const q = new URLSearchParams(location.search)   // ?env=0.3&sun=4.5&exp=1 tweak the light balance while tuning
renderer.toneMappingExposure = +(q.get('exp') ?? 1.0)
renderer.shadowMap.type = q.get('shadow') === 'basic' ? THREE.BasicShadowMap : THREE.PCFSoftShadowMap

const scene = new THREE.Scene()
scene.background = new THREE.Color('#616a75')
const pmrem = new THREE.PMREMGenerator(renderer)
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
scene.environmentIntensity = +(q.get('env') ?? 0.3)

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
scene.add(new THREE.HemisphereLight('#dfe7f0', '#6f6a63', 0.4))

// ground shadow catcher so the slab floats on a soft shadow like a model on a table
const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.ShadowMaterial({ opacity: 0.25 }))
ground.rotation.x = -Math.PI / 2
ground.position.y = -0.33
ground.receiveShadow = true
scene.add(ground)

// ------------------------------------------------------------------ controls
const controls = new OrbitControls(camera, canvas)
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
let model = null
const loader = new GLTFLoader()
loader.load('apartment.glb', gltf => {
  model = gltf.scene
  model.traverse(o => {
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
    if (o.material.emissive && o.material.emissiveIntensity > 0) o.material.toneMapped = false
  })
  scene.add(model)
  $('#loading').classList.add('done')
  applyCutaway(true)
}, ev => {
  const p = ev.total ? Math.round(ev.loaded / ev.total * 100) : Math.min(99, Math.round(ev.loaded / 3.1e6 * 100))
  $('#loadingText').textContent = `Opening the apartment · ${p}%`
}, err => { $('#loadingText').textContent = 'Could not load the model'; console.error(err) })

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
  }
  const showCeil = state.mode === 'walk' || state.ceiling || !state.cutaway
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
  const v = VIEWS[i]
  document.querySelectorAll('#views button').forEach((b, j) => b.classList.toggle('on', j === i))
  $('#introTitle').textContent = v.title
  $('#introRoom').textContent = v.room
  $('#introArea').textContent = v.area
  if (state.mode === 'walk') setMode('orbit')
  flyTo(v.pos, v.target)
}

// ------------------------------------------------------------------ walk mode (first person)
const walk = { keys: {}, yaw: 0, pitch: -0.05, dragging: false, last: null }
function setMode(m) {
  const wasWalk = state.mode === 'walk'
  state.mode = m
  document.querySelectorAll('.modes button').forEach(b => b.classList.toggle('on', b.dataset.mode === m))
  if (m === 'walk') {
    controls.enabled = false
    const v = VIEWS[state.view]
    // stand inside the current room, look toward its target
    const eye = new THREE.Vector3(v.target[0], 1.55, v.target[2])
    const dir = new THREE.Vector3(v.pos[0], 0, v.pos[2]).sub(eye).setY(0)
    eye.addScaledVector(dir.normalize(), Math.min(1.6, dir.length() * 0.3))
    eye.x = THREE.MathUtils.clamp(eye.x, BOUNDS.minX + 0.3, BOUNDS.maxX - 0.3)
    eye.z = THREE.MathUtils.clamp(eye.z, BOUNDS.minZ + 0.3, BOUNDS.maxZ - 0.3)
    camera.position.copy(eye)
    const look = new THREE.Vector3(v.target[0], 1.3, v.target[2]).sub(eye)
    walk.yaw = Math.atan2(-look.x, -look.z)
    walk.pitch = -0.08
    tween = null
    $('#hint').textContent = 'Drag to look · WASD / arrows to walk · Q/E for height'
  } else {
    controls.enabled = true
    controls.mouseButtons = m === 'pan' ? PAN_BTNS : ORBIT_BTNS
    controls.touches = m === 'pan' ? { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE } : { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN }
    if (wasWalk) {
      // re-seat orbit target ahead of the walker so the camera doesn't jump
      const f = new THREE.Vector3(0, 0, -1).applyEuler(new THREE.Euler(walk.pitch, walk.yaw, 0, 'YXZ'))
      controls.target.copy(camera.position).addScaledVector(f, 4)
    }
    $('#hint').textContent = m === 'pan' ? 'Drag to pan · Right-drag to orbit · Scroll to zoom' : 'Drag to orbit · Right-drag to pan · Scroll to zoom'
  }
  applyCutaway(true)
}
addEventListener('keydown', e => { walk.keys[e.code] = true })
addEventListener('keyup', e => { walk.keys[e.code] = false })
canvas.addEventListener('pointerdown', e => { if (state.mode === 'walk') { walk.dragging = true; walk.last = [e.clientX, e.clientY]; canvas.setPointerCapture(e.pointerId) } })
canvas.addEventListener('pointermove', e => {
  if (state.mode !== 'walk' || !walk.dragging) return
  walk.yaw -= (e.clientX - walk.last[0]) * 0.0045
  walk.pitch = THREE.MathUtils.clamp(walk.pitch - (e.clientY - walk.last[1]) * 0.0045, -1.3, 1.3)
  walk.last = [e.clientX, e.clientY]
})
canvas.addEventListener('pointerup', () => { walk.dragging = false })
canvas.addEventListener('pointercancel', () => { walk.dragging = false })

function stepWalk(dt) {
  const k = walk.keys
  let f = (k.KeyW || k.ArrowUp ? 1 : 0) - (k.KeyS || k.ArrowDown ? 1 : 0)
  let s = (k.KeyD || k.ArrowRight ? 1 : 0) - (k.KeyA || k.ArrowLeft ? 1 : 0)
  const u = (k.KeyE ? 1 : 0) - (k.KeyQ ? 1 : 0)
  const sp = 2.0 * dt, sin = Math.sin(walk.yaw), cos = Math.cos(walk.yaw)
  camera.position.x += (-sin * f + cos * s) * sp
  camera.position.z += (-cos * f - sin * s) * sp
  camera.position.y = THREE.MathUtils.clamp(camera.position.y + u * sp, 0.6, 2.3)
  camera.position.x = THREE.MathUtils.clamp(camera.position.x, BOUNDS.minX, BOUNDS.maxX)
  camera.position.z = THREE.MathUtils.clamp(camera.position.z, BOUNDS.minZ, BOUNDS.maxZ)
  camera.rotation.order = 'YXZ'
  camera.rotation.set(walk.pitch, walk.yaw, 0)
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
resize(); camera.position.copy(framed(VIEWS[0].pos, VIEWS[0].target)); controls.target.set(...VIEWS[0].target); tween = null

$('#tgCut').addEventListener('change', e => { state.cutaway = e.target.checked; applyCutaway(true) })
$('#tgCeil').addEventListener('change', e => { state.ceiling = e.target.checked; applyCutaway(true) })
$('#tgSpin').addEventListener('change', e => { controls.autoRotate = e.target.checked })
document.querySelectorAll('.modes button').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)))
document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === b))
  $('#tab3d').hidden = b.dataset.tab !== '3d'
  $('#tabRenders').hidden = b.dataset.tab !== 'renders'
}))

const spherical = new THREE.Spherical()
function nudge(dTheta = 0, dPhi = 0, zoom = 1) {
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

window.__app = { renderer, scene, camera, controls, sun, parts, state }   // debugging hook

// ------------------------------------------------------------------ resize + loop
function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight
  if (canvas.width !== Math.floor(w * renderer.getPixelRatio()) || canvas.height !== Math.floor(h * renderer.getPixelRatio())) {
    renderer.setSize(w, h, false)
    camera.aspect = w / h
    camera.updateProjectionMatrix()
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
  if (state.mode === 'walk') stepWalk(dt); else controls.update()
  applyCutaway()
  renderer.render(scene, camera)
})
