// Dept. D — dimensions from the King's Tower plan (metres).
// Axes: x → east (right on the plan), z → south (down on the plan), y → up.
export const H = 2.6       // ceiling height
export const T = 0.14      // wall thickness

// [x1, z1, x2, z2, opts]  opts: { y0, y1, glass, nomap, noskirt }
export const walls = [
  // exterior
  [-0.4, 0, 12.8, 0],
  [0, 0, 0, 1.3], [0, 2.8, 0, 4.45],                        // west (window between)
  [0, 1.3, 0, 2.8, { y0: 0, y1: 0.9, nomap: true }],         // window sill
  [0, 1.3, 0, 2.8, { y0: 2.25, y1: H, nomap: true, noskirt: true }],
  [0, 1.3, 0, 2.8, { y0: 0.9, y1: 2.25, glass: true }],
  [0, 4.45, -0.4, 4.45], [-0.4, 4.45, -0.4, 5.95],           // bath bump-out
  [-0.4, 5.95, 7.8, 5.95],                                   // south
  [12.8, 0, 12.8, 5.95],                                     // terrace east
  [7.8, 5.95, 12.8, 5.95, { y0: 0.12, y1: 1.1, glass: true }], // railing
  // interior
  [3.35, 2.75, 7.8, 2.75],
  [3.35, 2.75, 3.35, 2.95], [3.35, 3.85, 3.35, 5.95],        // bedroom door
  [-0.4, 4.45, 0.25, 4.45], [1.15, 4.45, 2.25, 4.45], [3.15, 4.45, 3.35, 4.45],
  [2.05, 4.45, 2.05, 5.95],
  // east wall with two terrace openings
  [7.8, 0, 7.8, 0.35], [7.8, 1.85, 7.8, 3.95], [7.8, 5.55, 7.8, 5.95],
  [7.8, 0.35, 7.8, 1.85, { y0: 2.25, y1: H, nomap: true, noskirt: true }],
  [7.8, 3.95, 7.8, 5.55, { y0: 2.25, y1: H, nomap: true, noskirt: true }],
]

// dark aluminium frames around openings [x1,z1,x2,z2,y0,y1]
export const frames = [
  [0, 1.3, 0, 2.8, 0.9, 2.25],
  [7.8, 0.35, 7.8, 1.85, 0, 2.25],
  [7.8, 3.95, 7.8, 5.55, 0, 2.25],
]

// Floor planes must never overlap each other or the slab top (z-fighting on mobile),
// so the wood floor is split around the wet room instead of running underneath it.
export const rooms = {
  living:  { floor: 'wood',  rect: [0, 0, 7.8, 5.95], rects: [[0, 0, 7.8, 4.45], [3.35, 4.45, 7.8, 5.95]] },
  wet:     { floor: 'tile',  rect: [-0.4, 4.45, 3.35, 5.95] },
  terrace: { floor: 'stone', rect: [7.8, 0, 12.8, 5.95] },
}
export const SLAB_TOP = -0.02   // slab sits just below the floor planes

export const downlights = [[1.2, 1.2], [2.6, 3.0], [5.6, 1.4], [4.3, 1.4], [5.4, 4.3], [1.0, 5.2], [2.7, 5.2]]

// camera presets: x, y, z, yaw, pitch
export const spots = {
  living:  [1.7, 1.55, 2.15, 0.1, -0.1],
  cocina:  [4.6, 1.55, 1.1, Math.PI * 0.5, -0.05],
  dorm:    [5.4, 1.5, 3.4, Math.PI, -0.1],
  bano:    [1.2, 1.55, 4.85, Math.PI, -0.15],
  terraza: [9.6, 1.6, 2.6, Math.PI * 0.35, -0.05],
  aerea:   [6.2, 7.5, 3.0, 0, -1.35],
}

export function roomName(x, z, y) {
  if (y > 3) return 'Vista aérea'
  if (x > 7.85) return 'Terraza libre'
  if (z > 4.5 && x < 2.05) return 'Baño'
  if (z > 4.5 && x < 3.35) return 'Área de servicio'
  if (x > 3.35 && z > 2.75) return 'Dormitorio'
  if (x > 3.4) return 'Comedor-cocina'
  return 'Living'
}

// AABB colliders derived from walls (camera collision + minimap)
export function wallBoxes() {
  return walls.map(([x1, z1, x2, z2, o = {}]) => {
    const hx = Math.abs(x2 - x1) / 2 + T / 2, hz = Math.abs(z2 - z1) / 2 + T / 2
    const cx = (x1 + x2) / 2, cz = (z1 + z2) / 2
    return { minX: cx - hx, maxX: cx + hx, minZ: cz - hz, maxZ: cz + hz, minY: o.y0 ?? 0, maxY: o.y1 ?? H }
  })
}
