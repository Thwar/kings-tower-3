import React, { useMemo } from 'react'
import * as THREE from 'three'
import { walls, frames, rooms, downlights, H, T, SLAB_TOP } from './plan.js'
import { usePBR, flat } from './materials.js'
import { Furniture } from './Furniture.jsx'

export function B({ size, pos, mat, rot, shadow = true }) {
  return (
    <mesh position={pos} rotation={rot} material={mat} castShadow={shadow} receiveShadow>
      <boxGeometry args={size} />
    </mesh>
  )
}

function Wall({ seg, mat }) {
  const [x1, z1, x2, z2, o = {}] = seg
  const y0 = o.y0 ?? 0, y1 = o.y1 ?? H
  const dx = x2 - x1, dz = z2 - z1, len = Math.hypot(dx, dz), rot = -Math.atan2(dz, dx)
  const cx = (x1 + x2) / 2, cz = (z1 + z2) / 2
  const m = o.glass ? flat.glass : mat
  return (
    <group>
      <B size={[len + T, y1 - y0, T]} pos={[cx, (y0 + y1) / 2, cz]} rot={[0, rot, 0]} mat={m} />
      {!o.glass && !o.noskirt && y0 === 0 && (
        <B size={[len + T + 0.02, 0.09, T + 0.03]} pos={[cx, 0.045, cz]} rot={[0, rot, 0]} mat={flat.linen} shadow={false} />
      )}
    </group>
  )
}

function Frame({ f }) {
  const [x1, z1, x2, z2, y0, y1] = f
  const dx = x2 - x1, dz = z2 - z1, len = Math.hypot(dx, dz), rot = -Math.atan2(dz, dx)
  const cx = (x1 + x2) / 2, cz = (z1 + z2) / 2
  const at = (ox, oy) => [cx + Math.cos(rot) * ox, oy, cz - Math.sin(rot) * ox]
  return (
    <group>
      <B size={[len + 0.06, 0.05, T + 0.04]} pos={at(0, y0 + 0.025)} rot={[0, rot, 0]} mat={flat.frame} />
      <B size={[len + 0.06, 0.05, T + 0.04]} pos={at(0, y1 - 0.025)} rot={[0, rot, 0]} mat={flat.frame} />
      <B size={[0.05, y1 - y0, T + 0.04]} pos={at(-len / 2, (y0 + y1) / 2)} rot={[0, rot, 0]} mat={flat.frame} />
      <B size={[0.05, y1 - y0, T + 0.04]} pos={at(len / 2, (y0 + y1) / 2)} rot={[0, rot, 0]} mat={flat.frame} />
    </group>
  )
}

function Floor({ rect, mat, y = 0 }) {
  const [x1, z1, x2, z2] = rect
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[(x1 + x2) / 2, y, (z1 + z2) / 2]} material={mat} receiveShadow>
      <planeGeometry args={[x2 - x1, z2 - z1]} />
    </mesh>
  )
}

export function Apartment({ showCeiling }) {
  const wallMat = usePBR('wall', { repeat: [2, 1], color: '#e9e5de', roughness: 0.92 })
  const wood = usePBR('woodFloor', { repeat: [3.2, 2.4], color: '#b8926a', roughness: 0.7, clearcoat: 0.35, clearcoatRoughness: 0.35 })
  const tile = usePBR('tile', { repeat: [3, 1.5], color: '#d6d3cd', roughness: 0.25, clearcoat: 0.5 })
  const stone = usePBR('terrace', { repeat: [4, 5], color: '#b9b3aa', roughness: 0.85 })
  const conc = usePBR('concrete', { repeat: [4, 2], color: '#b8b6b0', roughness: 0.95 })

  const ceilPlane = useMemo(() => new THREE.PlaneGeometry(8.2, 5.95), [])

  return (
    <group>
      {/* floors */}
      {rooms.living.rects.map((r, i) => <Floor key={i} rect={r} mat={wood} />)}
      <Floor rect={rooms.wet.rect} mat={tile} />
      <Floor rect={rooms.terrace.rect} mat={stone} />
      {/* slab + exterior faces (slab top stays below y=0 so it never fights the floors) */}
      <B size={[15, 0.4, 8]} pos={[6.4, SLAB_TOP - 0.2, 3]} mat={conc} shadow={false} />
      <B size={[0.2, H + 0.4, 6.2]} pos={[12.9, H / 2 - 0.2, 3]} mat={conc} shadow={false} />

      {walls.map((w, i) => <Wall key={i} seg={w} mat={wallMat} />)}
      {frames.map((f, i) => <Frame key={i} f={f} />)}
      {/* terrace curb + rail cap */}
      <B size={[5, 0.12, T]} pos={[10.3, 0.06, 5.95]} mat={flat.graphite} />
      <B size={[5.0, 0.05, 0.06]} pos={[10.3, 1.12, 5.95]} mat={flat.frame} />
      {/* sliding glass leaves, stacked open */}
      <B size={[0.04, 2.2, 0.7]} pos={[7.86, 1.12, 1.5]} mat={flat.glass} />
      <B size={[0.04, 2.2, 0.7]} pos={[7.86, 1.12, 5.2]} mat={flat.glass} />
      {/* doors (open, flat to walls) + entrance */}
      <B size={[0.05, 2.1, 0.85]} pos={[3.42, 1.05, 4.28]} mat={flat.oak} />
      <B size={[0.85, 2.1, 0.05]} pos={[0.7, 1.05, 4.52]} mat={flat.oak} />
      <B size={[0.85, 2.1, 0.05]} pos={[2.7, 1.05, 4.52]} mat={flat.oak} />
      <B size={[0.9, 2.1, 0.05]} pos={[1.25, 1.05, 0.08]} mat={flat.walnut} />
      <B size={[0.05, 0.05, 0.05]} pos={[1.6, 1.0, 0.12]} mat={flat.brass} />

      {/* ceiling + downlights */}
      <group visible={showCeiling}>
        <mesh geometry={ceilPlane} material={flat.ceil} rotation={[Math.PI / 2, 0, 0]} position={[3.7, H, 2.975]} />
        {downlights.map(([x, z], i) => (
          <mesh key={i} rotation={[Math.PI / 2, 0, 0]} position={[x, H - 0.005, z]} material={flat.downlight}>
            <circleGeometry args={[0.07, 16]} />
          </mesh>
        ))}
      </group>
      {downlights.map(([x, z], i) => (
        <pointLight key={i} position={[x, 2.5, z]} color="#ffe9cf" intensity={9} distance={7} decay={2} />
      ))}

      <Furniture />
    </group>
  )
}
