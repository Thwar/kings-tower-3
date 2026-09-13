// 2D plan data for the Bloque B · 101 minimap — same metres / axes as the model (x east, z south).
export const T = 0.14
// [x1, z1, x2, z2, kind]  kind: wall | glass | head (above an opening: drawn dashed)
export const walls = [
  [0, 0, 5.7, 0, 'glass'], [0, 0, 0, 6.8, 'glass'],
  [5.7, 0, 5.7, 17.5, 'wall'],
  [0, 6.8, 0.8, 6.8, 'wall'], [2.6, 6.8, 5.7, 6.8, 'wall'], [0.8, 6.8, 2.6, 6.8, 'head'],
  [4.4, 5.5, 4.6, 5.5, 'wall'], [5.4, 5.5, 5.7, 5.5, 'wall'], [4.6, 5.5, 5.4, 5.5, 'head'], [4.4, 5.5, 4.4, 6.8, 'wall'],
  [0, 6.8, 0, 10.2, 'wall'], [0, 12.2, 0, 17.5, 'wall'], [0, 10.2, 0, 12.2, 'glass'],
  [0, 17.5, 0.5, 17.5, 'wall'], [1.4, 17.5, 5.7, 17.5, 'wall'], [0.5, 17.5, 1.4, 17.5, 'head'],
  [0, 9.65, 2.55, 9.65, 'wall'], [3.4, 9.65, 3.6, 9.65, 'wall'], [2.55, 9.65, 3.4, 9.65, 'head'],
  [3.6, 6.8, 3.6, 7.3, 'wall'], [3.6, 8.1, 3.6, 10.0, 'wall'], [3.6, 10.8, 3.6, 12.9, 'wall'],
  [3.6, 7.3, 3.6, 8.1, 'head'], [3.6, 10.0, 3.6, 10.8, 'head'],
  [3.6, 9.2, 5.7, 9.2, 'wall'], [3.6, 12.9, 5.7, 12.9, 'wall'],
]
export const rooms = [
  { key: 'terrace', rect: [0, 0, 5.7, 5.5],      fill: '#b9b4ab', label: 'Terrace' },
  { key: 'terrace2', rect: [0, 5.5, 4.4, 6.8],   fill: '#b9b4ab', label: '' },
  { key: 'service', rect: [4.4, 5.5, 5.7, 6.8],  fill: '#d3d6d9', label: '' },
  { key: 'bedroom', rect: [0, 6.8, 3.6, 9.65],   fill: '#dfc39b', label: 'Bedroom' },
  { key: 'closet',  rect: [3.6, 6.8, 5.7, 9.2],  fill: '#d9c8a6', label: 'Closet' },
  { key: 'bath',    rect: [3.6, 9.2, 5.7, 12.9], fill: '#c9cdd1', label: 'Bath' },
  { key: 'living',  rect: [0, 9.65, 3.6, 12.9],  fill: '#d9b98c', label: 'Living' },
  { key: 'kitchen', rect: [0, 12.9, 5.7, 17.5],  fill: '#d2b58c', label: 'Kitchen' },
]
export const BOUNDS = { x0: -0.25, x1: 5.95, z0: -0.25, z1: 17.75 }
export function roomAt(x, z) {
  for (const r of rooms) { const [a, b, c, d] = r.rect; if (x >= a && x <= c && z >= b && z <= d) return r }
  return null
}
