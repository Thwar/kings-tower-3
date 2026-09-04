import React, { useMemo } from 'react'
import { flat, usePBR } from './materials.js'

const B = ({ size, pos, mat, rot, shadow = true }) => (
  <mesh position={pos} rotation={rot} material={mat} castShadow={shadow} receiveShadow>
    <boxGeometry args={size} />
  </mesh>
)
const Cyl = ({ args, pos, mat, rot }) => (
  <mesh position={pos} rotation={rot} material={mat} castShadow receiveShadow>
    <cylinderGeometry args={args} />
  </mesh>
)

let seed = 11
const rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280 }

export function Plant({ x, z, s = 1, pot = true }) {
  const leaves = useMemo(() => Array.from({ length: 7 }, (_, i) => ({
    p: [x + (rnd() - 0.5) * 0.36 * s, 0.78 * s + rnd() * 0.34 * s, z + (rnd() - 0.5) * 0.36 * s], m: i % 2 ? flat.leaf : flat.leaf2,
  })), [x, z, s])
  return (
    <group>
      {pot && <Cyl args={[0.18 * s, 0.14 * s, 0.32 * s, 18]} pos={[x, 0.16 * s, z]} mat={flat.pot} />}
      <Cyl args={[0.025, 0.04, 0.5 * s, 8]} pos={[x, 0.57 * s, z]} mat={flat.walnut} />
      {leaves.map((l, i) => (
        <mesh key={i} position={l.p} scale={[1, 0.7, 1]} material={l.m} castShadow>
          <sphereGeometry args={[0.2 * s, 12, 9]} />
        </mesh>
      ))}
    </group>
  )
}

function Sofa({ x, z, rot, fabric }) {
  return (
    <group position={[x, 0, z]} rotation={[0, rot, 0]}>
      <B size={[1.9, 0.42, 0.9]} pos={[0, 0.21, 0]} mat={fabric} />
      <B size={[1.9, 0.45, 0.25]} pos={[0, 0.63, -0.33]} mat={flat.sofa2} />
      <B size={[0.2, 0.6, 0.9]} pos={[-0.85, 0.3, 0]} mat={flat.sofa2} />
      <B size={[0.2, 0.6, 0.9]} pos={[0.85, 0.3, 0]} mat={flat.sofa2} />
      <B size={[0.7, 0.16, 0.55]} pos={[-0.4, 0.5, 0.1]} mat={fabric} />
      <B size={[0.7, 0.16, 0.55]} pos={[0.4, 0.5, 0.1]} mat={fabric} />
      <B size={[0.4, 0.4, 0.14]} pos={[0.5, 0.72, -0.2]} rot={[0, 0, 0.2]} mat={flat.pillow} />
      <B size={[0.4, 0.4, 0.14]} pos={[-0.5, 0.72, -0.2]} mat={flat.throw} />
    </group>
  )
}

function Lounger({ x, z }) {
  return (
    <group position={[x, 0, z]}>
      <B size={[0.7, 0.08, 1.3]} pos={[0, 0.35, 0]} mat={flat.linen} />
      <B size={[0.7, 0.08, 0.7]} pos={[0, 0.6, -0.85]} rot={[-0.9, 0, 0]} mat={flat.linen} />
      <B size={[0.75, 0.05, 1.35]} pos={[0, 0.3, 0]} mat={flat.oak} />
      {[[-0.3, -0.6], [0.3, -0.6], [-0.3, 0.6], [0.3, 0.6]].map(([dx, dz], i) => (
        <B key={i} size={[0.05, 0.3, 0.05]} pos={[dx, 0.15, dz]} mat={flat.oak} />
      ))}
    </group>
  )
}

function Chair({ x, z, rot }) {
  return (
    <group position={[x, 0, z]} rotation={[0, rot, 0]}>
      <B size={[0.42, 0.04, 0.42]} pos={[0, 0.45, 0]} mat={flat.oak} />
      <B size={[0.42, 0.45, 0.04]} pos={[0, 0.68, -0.2]} mat={flat.oak} />
      {[[-0.18, -0.18], [0.18, -0.18], [-0.18, 0.18], [0.18, 0.18]].map(([dx, dz], i) => (
        <B key={i} size={[0.03, 0.45, 0.03]} pos={[dx, 0.22, dz]} mat={flat.frame} />
      ))}
    </group>
  )
}

export function Furniture() {
  const fabric = usePBR('fabric', { repeat: [2, 2], color: '#8b8275', roughness: 1 })
  const marble = usePBR('marble', { repeat: [2, 1], color: '#e8e5df', roughness: 0.18, clearcoat: 0.6 })
  const metal = usePBR('metal', { repeat: [1, 1], color: '#c9ccd0', roughness: 0.28, metalness: 0.9 })

  return (
    <group>
      {/* ---------- living ---------- */}
      <B size={[0.05, 2.3, 0.6]} pos={[0.12, 1.15, 1.15]} mat={flat.linen} />
      <B size={[0.05, 2.3, 0.6]} pos={[0.12, 1.15, 2.95]} mat={flat.linen} />
      <B size={[0.03, 0.03, 2.0]} pos={[0.1, 2.35, 2.05]} mat={flat.frame} />
      <B size={[2.4, 0.012, 2.8]} pos={[1.7, 0.006, 2.1]} mat={flat.rug} shadow={false} />
      <Sofa x={1.7} z={0.75} rot={0} fabric={fabric} />
      <Sofa x={1.7} z={3.45} rot={Math.PI} fabric={fabric} />
      <B size={[1.0, 0.05, 0.5]} pos={[1.7, 0.4, 2.1]} mat={flat.walnut} />
      {[[1.25, 1.9], [2.15, 1.9], [1.25, 2.3], [2.15, 2.3]].map(([x, z], i) => (
        <B key={i} size={[0.04, 0.4, 0.04]} pos={[x, 0.2, z]} mat={flat.frame} />
      ))}
      <B size={[0.22, 0.14, 0.22]} pos={[1.5, 0.5, 2.1]} mat={flat.brass} />
      <Plant x={1.95} z={2.1} s={0.4} />
      <B size={[1.4, 0.45, 0.4]} pos={[3.0, 0.225, 0.3]} mat={flat.walnut} />
      <B size={[1.2, 0.7, 0.04]} pos={[3.0, 1.15, 0.11]} mat={flat.screen} />
      <B size={[0.95, 0.02, 0.05]} pos={[3.0, 1.15, 0.1]} mat={flat.tv} />
      <B size={[0.4, 0.03, 0.4]} pos={[0.55, 0.34, 0.5]} mat={flat.oak} />
      <B size={[0.05, 0.34, 0.05]} pos={[0.55, 0.17, 0.5]} mat={flat.frame} />
      <Plant x={0.55} z={0.5} s={0.7} />

      {/* ---------- comedor-cocina ---------- */}
      <B size={[3.4, 0.9, 0.6]} pos={[6.1, 0.45, 2.38]} mat={flat.graphite} />
      <B size={[3.4, 0.04, 0.62]} pos={[6.1, 0.92, 2.38]} mat={marble} />
      <B size={[3.4, 0.7, 0.35]} pos={[6.1, 2.05, 2.5]} mat={flat.graphite} />
      <B size={[3.4, 0.04, 0.35]} pos={[6.1, 1.72, 2.5]} mat={flat.graphite} />
      <B size={[3.4, 0.6, 0.02]} pos={[6.1, 1.35, 2.71]} mat={marble} />
      {[4.9, 5.5, 6.1, 6.7, 7.3].map(x => <B key={x} size={[0.02, 0.66, 0.34]} pos={[x, 2.05, 2.5]} mat={flat.frame} />)}
      <B size={[0.5, 0.02, 0.4]} pos={[5.3, 0.945, 2.38]} mat={metal} />
      <B size={[0.02, 0.3, 0.02]} pos={[5.3, 1.1, 2.55]} mat={flat.steel} />
      <B size={[0.14, 0.02, 0.02]} pos={[5.24, 1.25, 2.55]} mat={flat.steel} />
      <B size={[0.6, 0.012, 0.5]} pos={[6.9, 0.947, 2.38]} mat={flat.screen} />
      {[[-0.15, -0.12], [0.15, -0.12], [-0.15, 0.12], [0.15, 0.12]].map(([dx, dz], i) => (
        <mesh key={i} rotation={[Math.PI / 2, 0, 0]} position={[6.9 + dx, 0.96, 2.38 + dz]} material={flat.steel}>
          <torusGeometry args={[0.06, 0.012, 8, 20]} />
        </mesh>
      ))}
      <B size={[0.7, 0.4, 0.3]} pos={[6.9, 1.72, 2.55]} mat={metal} />
      <B size={[0.7, 1.9, 0.7]} pos={[7.35, 0.95, 0.42]} mat={metal} />
      <B size={[0.02, 0.9, 0.03]} pos={[7.02, 1.05, 0.42]} mat={flat.frame} />
      <B size={[0.6, 2.2, 0.6]} pos={[6.65, 1.1, 0.37]} mat={flat.graphite} />
      <B size={[0.5, 1.05, 2.0]} pos={[3.9, 0.525, 1.5]} mat={flat.graphite} />
      <B size={[0.7, 0.04, 2.1]} pos={[3.85, 1.07, 1.5]} mat={flat.oak} />
      {[0.85, 1.5, 2.15].map(z => (
        <group key={z}>
          <B size={[0.04, 0.7, 0.04]} pos={[3.38, 0.35, z]} mat={flat.frame} />
          <Cyl args={[0.18, 0.18, 0.06, 24]} pos={[3.38, 0.72, z]} mat={flat.walnut} />
          <Cyl args={[0.2, 0.2, 0.02, 24]} pos={[3.38, 0.02, z]} mat={flat.frame} />
        </group>
      ))}
      <B size={[0.2, 0.25, 0.2]} pos={[3.85, 1.2, 0.9]} mat={flat.white} />
      <Plant x={3.85} z={0.9} s={0.4} pot={false} />
      {[1.1, 1.9].map(z => (
        <group key={z}>
          <B size={[0.01, 1.0, 0.01]} pos={[3.85, 2.1, z]} mat={flat.frame} />
          <mesh position={[3.85, 1.58, z]} material={flat.pendant}>
            <cylinderGeometry args={[0.1, 0.16, 0.18, 20, 1, true]} />
          </mesh>
          <pointLight position={[3.85, 1.5, z]} color="#ffd9a8" intensity={2.5} distance={3} decay={2} />
        </group>
      ))}

      {/* ---------- dormitorio ---------- */}
      <B size={[1.7, 0.28, 2.1]} pos={[5.4, 0.14, 4.85]} mat={flat.walnut} />
      <B size={[1.6, 0.22, 2.0]} pos={[5.4, 0.39, 4.85]} mat={flat.linen} />
      <B size={[1.62, 0.04, 1.3]} pos={[5.4, 0.52, 4.5]} mat={flat.throw} />
      <B size={[1.7, 0.9, 0.1]} pos={[5.4, 0.75, 5.87]} mat={fabric} />
      <B size={[0.65, 0.18, 0.4]} pos={[5.0, 0.6, 5.6]} mat={flat.linen} />
      <B size={[0.65, 0.18, 0.4]} pos={[5.8, 0.6, 5.6]} mat={flat.linen} />
      <B size={[0.45, 0.16, 0.14]} pos={[5.0, 0.58, 5.33]} mat={flat.pillow} />
      {[4.35, 6.45].map(x => (
        <group key={x}>
          <B size={[0.45, 0.5, 0.45]} pos={[x, 0.25, 5.65]} mat={flat.oak} />
          <B size={[0.03, 0.35, 0.03]} pos={[x, 0.68, 5.65]} mat={flat.brass} />
          <mesh position={[x, 0.88, 5.65]} material={flat.lampShade}>
            <cylinderGeometry args={[0.12, 0.15, 0.2, 20, 1, true]} />
          </mesh>
          <pointLight position={[x, 0.9, 5.65]} color="#ffd9a8" intensity={1.5} distance={2.5} decay={2} />
        </group>
      ))}
      <B size={[0.6, 2.3, 1.9]} pos={[3.72, 1.15, 4.9]} mat={flat.oak} />
      {[4.2, 4.7, 5.2, 5.7].map(z => <B key={z} size={[0.02, 2.2, 0.02]} pos={[4.03, 1.15, z]} mat={flat.walnut} />)}
      {[4.45, 5.45].map(z => <B key={z} size={[0.03, 0.25, 0.02]} pos={[4.04, 1.1, z]} mat={flat.brass} />)}
      <B size={[1.2, 0.04, 0.55]} pos={[7.0, 0.74, 3.1]} mat={flat.oak} />
      <B size={[0.04, 0.72, 0.5]} pos={[6.45, 0.36, 3.1]} mat={flat.frame} />
      <B size={[0.04, 0.72, 0.5]} pos={[7.55, 0.36, 3.1]} mat={flat.frame} />
      <B size={[0.4, 0.02, 0.28]} pos={[7.0, 0.77, 3.1]} mat={flat.steel} />
      <B size={[0.4, 0.26, 0.01]} pos={[7.0, 0.9, 2.97]} mat={flat.screen} />
      <B size={[0.45, 0.05, 0.45]} pos={[7.0, 0.45, 3.6]} mat={flat.frame} />
      <B size={[0.45, 0.5, 0.05]} pos={[7.0, 0.72, 3.8]} mat={flat.frame} />
      <B size={[0.04, 0.43, 0.04]} pos={[7.0, 0.22, 3.6]} mat={flat.steel} />
      <B size={[2.2, 0.012, 1.5]} pos={[5.4, 0.006, 3.85]} mat={flat.rug} shadow={false} />
      <Plant x={7.4} z={5.5} s={0.9} />
      <B size={[0.7, 0.5, 0.03]} pos={[5.4, 1.7, 5.88]} mat={flat.frame} />
      <B size={[0.62, 0.42, 0.01]} pos={[5.4, 1.7, 5.865]} mat={flat.art} />

      {/* ---------- baño ---------- */}
      <B size={[0.02, 2.2, 1.4]} pos={[0.55, 1.1, 5.2]} mat={flat.glass} />
      <B size={[0.03, 2.2, 0.03]} pos={[0.55, 1.1, 4.5]} mat={flat.frame} />
      <B size={[0.03, 1.2, 0.03]} pos={[0.1, 1.5, 4.6]} mat={flat.steel} />
      <B size={[0.2, 0.02, 0.2]} pos={[0.2, 2.1, 4.75]} mat={flat.steel} />
      <B size={[0.38, 0.4, 0.55]} pos={[0.95, 0.2, 5.62]} mat={flat.white} />
      <B size={[0.38, 0.4, 0.18]} pos={[0.95, 0.6, 5.82]} mat={flat.white} />
      <B size={[0.6, 0.8, 0.45]} pos={[1.65, 0.4, 5.7]} mat={flat.oak} />
      <B size={[0.62, 0.04, 0.47]} pos={[1.65, 0.82, 5.7]} mat={marble} />
      <B size={[0.4, 0.12, 0.3]} pos={[1.65, 0.9, 5.7]} mat={flat.white} />
      <B size={[0.03, 0.2, 0.03]} pos={[1.65, 1.0, 5.85]} mat={flat.steel} />
      <B size={[0.55, 0.7, 0.02]} pos={[1.65, 1.6, 5.92]} mat={flat.steel} />
      <B size={[0.3, 0.5, 0.03]} pos={[1.7, 1.3, 4.54]} mat={flat.white} />

      {/* ---------- servicio ---------- */}
      <B size={[0.6, 0.85, 0.6]} pos={[2.4, 0.425, 5.62]} mat={flat.white} />
      <mesh position={[2.4, 0.45, 5.31]} material={flat.frame}>
        <torusGeometry args={[0.19, 0.03, 8, 24]} />
      </mesh>
      <B size={[0.5, 0.02, 0.4]} pos={[2.7, 1.6, 5.75]} mat={flat.oak} />
      <B size={[0.5, 0.02, 0.4]} pos={[2.7, 2.0, 5.75]} mat={flat.oak} />
      <B size={[0.2, 0.3, 0.15]} pos={[2.6, 1.77, 5.75]} mat={flat.white} />
      <B size={[0.5, 0.85, 0.45]} pos={[3.05, 0.425, 5.65]} mat={flat.white} />
      <B size={[0.4, 0.1, 0.35]} pos={[3.05, 0.9, 5.65]} mat={flat.steel} />

      {/* ---------- terraza ---------- */}
      {[8.3, 9.15, 10.0, 10.85, 11.7, 12.55].map(x => (
        <group key={x}>
          <B size={[0.6, 0.4, 0.4]} pos={[x, 0.2, 5.6]} mat={flat.pot} />
          <Plant x={x} z={5.6} s={0.7} pot={false} />
        </group>
      ))}
      <Lounger x={11.6} z={3.2} />
      <Lounger x={10.6} z={3.2} />
      <Cyl args={[0.4, 0.4, 0.04, 32]} pos={[9.0, 0.74, 1.3]} mat={flat.oak} />
      <B size={[0.06, 0.72, 0.06]} pos={[9.0, 0.36, 1.3]} mat={flat.frame} />
      <Cyl args={[0.25, 0.25, 0.03, 32]} pos={[9.0, 0.015, 1.3]} mat={flat.frame} />
      <Chair x={8.3} z={1.3} rot={Math.PI / 2} />
      <Chair x={9.7} z={1.3} rot={-Math.PI / 2} />
      <Plant x={12.3} z={0.5} s={1.5} />
      <Plant x={8.2} z={0.5} s={1.2} />
      <Plant x={12.3} z={5.0} s={1.0} />
      <B size={[0.12, 0.25, 0.12]} pos={[10.3, 2.0, 0.08]} mat={flat.frame} />
      <B size={[3.0, 0.012, 2.2]} pos={[11.0, 0.006, 3.2]} mat={flat.rug} shadow={false} />
    </group>
  )
}
