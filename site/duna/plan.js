// 2D plan data for the Torre Duna Tipo E minimap — same metres / axes as the model (x east, z south).
export const T = 0.14
// [x1, z1, x2, z2, kind]  kind: wall | glass | head (above an opening: drawn dashed)
export const walls = [
  [0, 0, 3.3, 0, 'wall'], [4.2, 0, 7.3, 0, 'wall'], [3.3, 0, 4.2, 0, 'head'],
  [0, 0, 0, 0.4, 'wall'], [0, 1.2, 0, 6.95, 'wall'], [0, 0.4, 0, 1.2, 'glass'],
  [7.3, 0, 7.3, 5.4, 'wall'],
  [3.6, 5.4, 3.6, 6.95, 'wall'],
  [3.6, 5.4, 4.6, 5.4, 'wall'], [6.6, 5.4, 7.3, 5.4, 'wall'], [4.6, 5.4, 6.6, 5.4, 'glass'],
  [0, 5.4, 2.3, 5.4, 'wall'], [3.35, 5.4, 3.6, 5.4, 'wall'], [2.3, 5.4, 3.35, 5.4, 'head'],
  [0, 6.95, 3.6, 6.95, 'glass'],
  [1.9, 0, 1.9, 1.55, 'wall'], [1.9, 2.05, 1.9, 2.2, 'wall'],
  [0, 2.2, 1.9, 2.2, 'wall'],
  [2.9, 0, 2.9, 0.4, 'wall'], [2.9, 1.2, 2.9, 1.5, 'wall'],
  [1.9, 1.5, 2.9, 1.5, 'wall'],
  [1.9, 2.2, 2.6, 2.2, 'wall'], [3.45, 2.2, 3.6, 2.2, 'wall'],
  [3.6, 2.2, 3.6, 5.4, 'wall'],
]
export const rooms = [
  { key: 'bath',    rect: [0, 0, 1.9, 2.2],       fill: '#c9cdd1', label: 'Bath' },
  { key: 'service', rect: [1.9, 0, 2.9, 1.5],     fill: '#d3d6d9', label: 'P.S.' },
  { key: 'hall',    rect: [2.9, 0, 4.6, 1.5],     fill: '#d9b98c', label: 'Hall' },
  { key: 'hall2',   rect: [1.9, 1.5, 4.6, 2.2],   fill: '#d9b98c', label: '' },
  { key: 'kitchen', rect: [4.6, 0, 7.3, 3.1],     fill: '#d2b58c', label: 'Kitchen' },
  { key: 'living',  rect: [3.6, 2.2, 7.3, 5.4],   fill: '#d9b98c', label: 'Living' },
  { key: 'bedroom', rect: [0, 2.2, 3.6, 5.4],     fill: '#dfc39b', label: 'Bedroom' },
  { key: 'terrace', rect: [0, 5.4, 3.6, 6.95],    fill: '#b9b4ab', label: 'Terrace' },
]
export const BOUNDS = { x0: -0.25, x1: 7.55, z0: -0.25, z1: 7.2 }
export function roomAt(x, z) {
  for (const r of rooms) { const [a, b, c, d] = r.rect; if (x >= a && x <= c && z >= b && z <= d) return r }
  return null
}
