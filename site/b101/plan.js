// 2D plan data for the Bloque B · 101 minimap — same metres / axes as the model (x east, z south).
export const T = 0.14
// [x1, z1, x2, z2, kind]  kind: wall | glass | head (above an opening: drawn dashed)
export const walls = [
  [5.7, 0, 0, 0, 'glass'], [5.7, 0, 5.7, 6.8, 'glass'],
  [0, 0, 0, 17.5, 'wall'],
  [5.7, 6.8, 4.9, 6.8, 'wall'], [3.1, 6.8, 0, 6.8, 'wall'], [4.9, 6.8, 3.1, 6.8, 'head'],
  [1.3, 5.5, 1.1, 5.5, 'wall'], [0.3, 5.5, 0, 5.5, 'wall'], [1.1, 5.5, 0.3, 5.5, 'head'], [1.3, 5.5, 1.3, 6.8, 'wall'],
  [5.7, 6.8, 5.7, 10.2, 'wall'], [5.7, 12.2, 5.7, 17.5, 'wall'], [5.7, 10.2, 5.7, 12.2, 'glass'],
  [5.7, 17.5, 5.2, 17.5, 'wall'], [4.3, 17.5, 0, 17.5, 'wall'], [5.2, 17.5, 4.3, 17.5, 'head'],
  [2.1, 6.8, 2.1, 7.3, 'wall'], [2.1, 8.1, 2.1, 10, 'wall'], [2.1, 10.8, 2.1, 12.9, 'wall'],
  [2.1, 7.3, 2.1, 8.1, 'head'], [2.1, 10, 2.1, 10.8, 'head'],
  [2.1, 9.2, 0, 9.2, 'wall'], [2.1, 12.9, 0, 12.9, 'wall'],
]
export const rooms = [
  { key: 'terrace', rect: [0, 0, 5.7, 5.5],      fill: '#b9b4ab', label: 'Terrace' },
  { key: 'terrace2', rect: [1.3, 5.5, 5.7, 6.8],   fill: '#b9b4ab', label: '' },
  { key: 'service', rect: [0, 5.5, 1.3, 6.8],  fill: '#d3d6d9', label: '' },
  { key: 'bedroom', rect: [2.1, 6.8, 5.7, 9.65],   fill: '#dfc39b', label: 'Bedroom' },
  { key: 'closet',  rect: [0, 6.8, 2.1, 9.2],  fill: '#d9c8a6', label: 'Closet' },
  { key: 'bath',    rect: [0, 9.2, 2.1, 12.9], fill: '#c9cdd1', label: 'Bath' },
  { key: 'living',  rect: [2.1, 9.65, 5.7, 12.9],  fill: '#d9b98c', label: 'Living' },
  { key: 'kitchen', rect: [0, 12.9, 5.7, 17.5],  fill: '#d2b58c', label: 'Kitchen' },
]
export const BOUNDS = { x0: -0.25, x1: 5.95, z0: -0.25, z1: 17.75 }
export function roomAt(x, z) {
  for (const r of rooms) { const [a, b, c, d] = r.rect; if (x >= a && x <= c && z >= b && z <= d) return r }
  return null
}
