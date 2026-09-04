import { useEffect, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { H, wallBoxes } from '../scene/plan.js'

// `cam` is a mutable ref object { x, y, z, yaw, pitch } shared with the HUD.
export function FlyControls({ cam, input, onUpdate }) {
  const { camera, gl } = useThree()
  const keys = useRef({})
  const boxes = useRef(wallBoxes())
  const R = 0.16

  useEffect(() => {
    const down = e => (keys.current[e.code] = true), up = e => (keys.current[e.code] = false)
    addEventListener('keydown', down); addEventListener('keyup', up)
    const el = gl.domElement
    const isTouch = matchMedia('(pointer:coarse)').matches
    const look = (dx, dy) => { cam.current.yaw -= dx; cam.current.pitch = Math.max(-1.45, Math.min(1.45, cam.current.pitch - dy)) }
    const click = () => el.requestPointerLock?.()
    const move = e => { if (document.pointerLockElement === el) look(e.movementX * 0.0022, e.movementY * 0.0022) }
    if (!isTouch) { el.addEventListener('click', click); addEventListener('mousemove', move) }

    let moveT = null, lookT = null, lookLast = null
    const ts = e => {
      for (const t of e.changedTouches) {
        if (t.clientX < innerWidth / 2 && moveT === null) { moveT = { id: t.identifier, x: t.clientX, y: t.clientY }; input.current.stick = { x: t.clientX, y: t.clientY, dx: 0, dy: 0 } }
        else if (lookT === null) { lookT = t.identifier; lookLast = { x: t.clientX, y: t.clientY } }
      }
      e.preventDefault()
    }
    const tm = e => {
      for (const t of e.changedTouches) {
        if (moveT && t.identifier === moveT.id) {
          let dx = t.clientX - moveT.x, dy = t.clientY - moveT.y; const d = Math.hypot(dx, dy), max = 45
          if (d > max) { dx *= max / d; dy *= max / d }
          input.current.move = { x: dx / max, y: dy / max }; input.current.stick = { ...input.current.stick, dx, dy }
        } else if (t.identifier === lookT) { look((t.clientX - lookLast.x) * 0.005, (t.clientY - lookLast.y) * 0.005); lookLast = { x: t.clientX, y: t.clientY } }
      }
      e.preventDefault()
    }
    const te = e => {
      for (const t of e.changedTouches) {
        if (moveT && t.identifier === moveT.id) { moveT = null; input.current.move = { x: 0, y: 0 }; input.current.stick = null }
        if (t.identifier === lookT) lookT = null
      }
    }
    el.addEventListener('touchstart', ts, { passive: false }); el.addEventListener('touchmove', tm, { passive: false })
    el.addEventListener('touchend', te); el.addEventListener('touchcancel', te)
    return () => {
      removeEventListener('keydown', down); removeEventListener('keyup', up)
      el.removeEventListener('click', click); removeEventListener('mousemove', move)
      el.removeEventListener('touchstart', ts); el.removeEventListener('touchmove', tm); el.removeEventListener('touchend', te); el.removeEventListener('touchcancel', te)
    }
  }, [gl, cam, input])

  const blocked = (x, y, z) => boxes.current.some(c => !(y < c.minY - 0.05 || y > c.maxY + 0.05) && x + R > c.minX && x - R < c.maxX && z + R > c.minZ && z - R < c.maxZ)

  useFrame((_, dtRaw) => {
    const dt = Math.min(0.05, dtRaw), c = cam.current, k = keys.current, inp = input.current
    let f = 0, s = 0, u = inp.vert || 0
    if (k.KeyW || k.ArrowUp) f += 1; if (k.KeyS || k.ArrowDown) f -= 1
    if (k.KeyD || k.ArrowRight) s += 1; if (k.KeyA || k.ArrowLeft) s -= 1
    if (k.KeyE || k.Space) u += 1; if (k.KeyQ || k.ShiftLeft) u -= 1
    f -= inp.move.y; s += inp.move.x
    const len = Math.hypot(f, s); if (len > 1) { f /= len; s /= len }
    const speed = (c.y > 3 ? 4.5 : 2.2) * dt
    const sin = Math.sin(c.yaw), cos = Math.cos(c.yaw), cp = Math.cos(c.pitch), sp = Math.sin(c.pitch)
    const dx = (-sin * cp * f + cos * s) * speed, dz = (-cos * cp * f - sin * s) * speed, dy = (sp * f + u) * speed
    if (!blocked(c.x + dx, c.y, c.z)) c.x += dx
    if (!blocked(c.x, c.y, c.z + dz)) c.z += dz
    c.y = Math.max(0.35, Math.min(9, c.y + dy))
    c.x = Math.max(-3, Math.min(16, c.x)); c.z = Math.max(-3, Math.min(9, c.z))
    camera.position.set(c.x, c.y, c.z)
    camera.rotation.order = 'YXZ'; camera.rotation.set(c.pitch, c.yaw, 0)
    onUpdate?.(c.y > H - 0.05)
  })
  return null
}
