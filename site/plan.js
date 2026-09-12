// 2D plan data for the minimap — same metres / axes as the model (x east, z south).
export const T = 0.14
// [x1, z1, x2, z2, kind]  kind: wall | glass | low (sill) | head (above an opening: drawn dashed)
export const walls = [
  [-0.4, 0, 12.8, 0, 'wall'],
  [0, 0, 0, 1.3, 'wall'], [0, 2.8, 0, 4.45, 'wall'], [0, 1.3, 0, 2.8, 'glass'],
  [0, 4.45, -0.4, 4.45, 'wall'], [-0.4, 4.45, -0.4, 5.95, 'wall'],
  [-0.4, 5.95, 7.8, 5.95, 'wall'],
  [12.8, 0, 12.8, 5.95, 'wall'],
  [7.8, 5.95, 12.8, 5.95, 'glass'],
  [3.35, 2.75, 7.8, 2.75, 'wall'],
  [3.35, 2.75, 3.35, 2.95, 'wall'], [3.35, 3.85, 3.35, 5.95, 'wall'],
  [-0.4, 4.45, 2.2, 4.45, 'wall'], [3.05, 4.45, 3.35, 4.45, 'wall'],
  [2.05, 4.45, 2.05, 4.6, 'wall'], [2.05, 5.4, 2.05, 5.95, 'wall'],
  [7.8, 0, 7.8, 0.35, 'wall'], [7.8, 1.85, 7.8, 3.95, 'wall'], [7.8, 5.55, 7.8, 5.95, 'wall'],
  [7.8, 0.35, 7.8, 1.85, 'head'], [7.8, 3.95, 7.8, 5.55, 'head'],
]
export const rooms = [
  { key: 'living',  rect: [0, 0, 3.4, 4.45],       fill: '#d9b98c', label: 'Living' },
  { key: 'kitchen', rect: [3.4, 0, 7.8, 2.75],     fill: '#d2b58c', label: 'Kitchen' },
  { key: 'bedroom', rect: [3.35, 2.75, 7.8, 5.95], fill: '#dfc39b', label: 'Bedroom' },
  { key: 'bath',    rect: [-0.4, 4.45, 2.05, 5.95], fill: '#c9cdd1', label: 'Bath' },
  { key: 'service', rect: [2.05, 4.45, 3.35, 5.95], fill: '#d3d6d9', label: 'Service' },
  { key: 'terrace', rect: [7.8, 0, 12.8, 5.95],    fill: '#b9b4ab', label: 'Terrace' },
]
export const BOUNDS = { x0: -0.6, x1: 13.0, z0: -0.2, z1: 6.15 }
export function roomAt(x, z) {
  for (const r of rooms) { const [a, b, c, d] = r.rect; if (x >= a && x <= c && z >= b && z <= d) return r }
  return null
}
