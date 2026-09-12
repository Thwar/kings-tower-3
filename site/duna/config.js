// Torre Duna · Dept. Tipo E — everything in app.js that is specific to this apartment.
// pos / target in metres, apartment space: x east, y up, z south (origin = NW corner, the bathroom).
// walk: [x, z, yaw] standing spot + heading for the first-person mode (yaw 0 = north, π/2 = west, −π/2 = east).
import * as plan from './plan.js'

export default {
  key: 'duna-e',
  name: 'Torre Duna · Tipo E',
  plan,
  textures: '../textures/',
  glbBytes: 8e6,
  center: [3.65, 1.3, 3.2],
  walkBounds: { minX: 0.1, maxX: 7.2, minZ: 0.1, maxZ: 6.85 },
  views: [
    { key: 'whole',   name: 'Whole apartment', room: 'Whole apartment', area: '49.61 m² incl. terrace', title: 'Compact, complete.',
      pos: [-7.5, 12.0, 15.5], target: [3.65, 0.4, 3.2], walk: [3.75, 0.7, Math.PI] },
    { key: 'living',  name: 'Living',          room: 'Living',            area: '≈ 10 m²',  title: 'Sofa, screen, sunset.',
      pos: [5.5, 6.0, 12.5], target: [5.4, 0.6, 3.9], walk: [4.4, 3.7, -Math.PI / 2 - 0.45] },
    { key: 'kitchen', name: 'Kitchen & island', room: 'Kitchen & island', area: '≈ 8 m²',   title: 'Three stools at the island.',
      pos: [5.8, 6.0, -6.0], target: [5.8, 0.7, 1.3], walk: [5.4, 1.75, 0.0] },
    { key: 'bedroom', name: 'Bedroom',         room: 'Bedroom',           area: '≈ 11.5 m²', title: 'Bed to the wall, desk to the light.',
      pos: [1.4, 6.5, 12.0], target: [1.6, 0.3, 3.9], walk: [2.9, 4.0, Math.PI / 2 + 0.2] },
    { key: 'bath',    name: 'Bathroom',        room: 'Bathroom',          area: '≈ 4.2 m²', title: 'Shower in the corner.',
      pos: [-6.5, 4.5, 1.2], target: [0.9, 0.8, 1.1], walk: [1.45, 1.75, 0.45] },
    { key: 'service', name: 'Service (P.S.)',  room: 'Service room',      area: '≈ 1.5 m²', title: 'Laundry, behind a door.',
      pos: [2.4, 5.0, -5.5], target: [2.4, 0.6, 0.8], walk: [2.45, 1.2, 0.0] },
    { key: 'terrace', name: 'Terrace',         room: 'Terrace',           area: '≈ 5.5 m²', title: 'The outdoor strip.',
      pos: [-4.5, 4.0, 11.5], target: [1.8, 0.7, 6.2], walk: [1.8, 6.0, Math.PI] },
  ],
}
