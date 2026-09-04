import React, { useEffect, useRef, useState } from 'react'
import { walls, spots, roomName } from '../scene/plan.js'

const MX0 = -0.6, MX1 = 13.0, MZ0 = -0.2
const furn = [[0.7, 0.25, 2, 1], [0.7, 2.95, 2, 1], [1.2, 1.85, 1, 0.5], [2.3, 0.1, 1.4, 0.4], [4.4, 2.08, 3.4, 0.6], [7.0, 0.07, 0.7, 0.7],
  [3.65, 0.5, 0.5, 2.0], [4.55, 3.8, 1.7, 2.1], [3.42, 3.95, 0.6, 1.9], [6.4, 2.83, 1.2, 0.55], [0.76, 5.35, 0.38, 0.55], [1.35, 5.48, 0.6, 0.45],
  [2.1, 5.32, 0.6, 0.6], [11.22, 2.5, 0.76, 1.4], [10.22, 2.5, 0.76, 1.4], [8.6, 0.9, 0.8, 0.8]]

export function Hud({ cam, input, hintDesktop }) {
  const mapRef = useRef()
  const [room, setRoom] = useState('Living')
  const [stick, setStick] = useState(null)

  useEffect(() => {
    let raf
    const draw = () => {
      const cv = mapRef.current; if (!cv) return
      const g = cv.getContext('2d'), MS = cv.width / (MX1 - MX0), mx = x => (x - MX0) * MS, mz = z => (z - MZ0) * MS
      g.clearRect(0, 0, cv.width, cv.height)
      const fill = (x1, z1, x2, z2, c) => { g.fillStyle = c; g.fillRect(mx(x1), mz(z1), (x2 - x1) * MS, (z2 - z1) * MS) }
      fill(0, 0, 7.8, 5.95, '#c9a77a'); fill(-0.4, 4.45, 3.35, 5.95, '#b9bcbf'); fill(7.8, 0, 12.8, 5.95, '#a9a49b')
      g.fillStyle = 'rgba(255,255,255,.35)'; for (const [x, z, w, d] of furn) g.fillRect(mx(x), mz(z), w * MS, d * MS)
      g.lineCap = 'square'
      for (const [x1, z1, x2, z2, o = {}] of walls) {
        if (o.nomap) continue
        g.strokeStyle = o.glass ? '#7fc3e6' : '#26292d'; g.lineWidth = o.glass ? 2 : 3.5
        g.beginPath(); g.moveTo(mx(x1), mz(z1)); g.lineTo(mx(x2), mz(z2)); g.stroke()
      }
      const c = cam.current, px = mx(c.x), pz = mz(c.z), a = -c.yaw - Math.PI / 2
      g.fillStyle = 'rgba(216,181,106,.35)'; g.beginPath(); g.moveTo(px, pz); g.arc(px, pz, 26, a - 0.55, a + 0.55); g.closePath(); g.fill()
      g.fillStyle = '#d8b56a'; g.beginPath(); g.arc(px, pz, 5, 0, Math.PI * 2); g.fill(); g.strokeStyle = '#1a1408'; g.lineWidth = 1.5; g.stroke()
      const rn = roomName(c.x, c.z, c.y); setRoom(r => (r === rn ? r : rn))
      setStick(s => (input.current.stick ? { ...input.current.stick } : s ? null : s))
      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [cam, input])

  const goto = k => { const s = spots[k]; Object.assign(cam.current, { x: s[0], y: s[1], z: s[2], yaw: s[3], pitch: s[4] }) }
  const hold = v => ({
    onPointerDown: e => { input.current.vert = v; e.preventDefault() },
    onPointerUp: () => (input.current.vert = 0), onPointerLeave: () => (input.current.vert = 0), onPointerCancel: () => (input.current.vert = 0),
  })

  return (
    <div className="hud">
      <div className="title"><b>King's Tower · Dept. D</b><span>50.21 m² + terraza 29.75 m²</span></div>
      <div className="mapbox"><canvas ref={mapRef} width={340} height={168} /><div className="room">{room}</div></div>
      <div className="hint">{hintDesktop ? 'Clic para mirar · WASD vuela · Q/E sube y baja' : 'Izquierda: volar · derecha: mirar'}</div>
      <div className="alt"><button {...hold(1)}>▲</button><button {...hold(-1)}>▼</button></div>
      <div className="nav">
        {[['living', 'Living'], ['cocina', 'Cocina'], ['dorm', 'Dormitorio'], ['bano', 'Baño'], ['terraza', 'Terraza'], ['aerea', 'Vista aérea']].map(([k, l]) => (
          <button key={k} onClick={() => goto(k)}>{l}</button>
        ))}
      </div>
      {stick && (
        <div className="stick" style={{ left: stick.x - 55, top: stick.y - 55 }}>
          <div className="knob" style={{ left: 32 + stick.dx, top: 32 + stick.dy }} />
        </div>
      )}
    </div>
  )
}
