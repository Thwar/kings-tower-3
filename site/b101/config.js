// Bloque B · Departamento 101 — everything in app.js that is specific to this apartment.
// pos / target in metres, apartment space: x east, y up, z south (origin = NW corner of the terrace).
// walk: [x, z, yaw] standing spot + heading for the first-person mode (yaw 0 = north, π/2 = west, −π/2 = east).
import * as plan from './plan.js'

export default {
  key: 'b101',
  name: 'Bloque B · Dpto. 101',
  plan,
  mapRotate: true,              // the plan is three times taller than wide: draw the minimap with north to the left
  textures: '../textures/',
  glbBytes: 10e6,
  center: [2.85, 1.3, 9.0],
  walkBounds: { minX: 0.15, maxX: 5.55, minZ: 0.15, maxZ: 17.35 },
  views: [
    { key: 'whole',   name: 'Whole apartment', room: 'Whole apartment', area: '100.20 m² incl. terrace', title: 'One bedroom, one long terrace.',
      pos: [-15.0, 19.0, 28.0], target: [2.85, 0.4, 9.0], walk: [1.0, 16.8, 0.0] },
    { key: 'living',  name: 'Living',          room: 'Living',            area: '≈ 11 m²',  title: 'Sofa under the window.',
      pos: [-8.0, 6.0, 11.3], target: [2.0, 0.6, 11.3], walk: [2.6, 12.5, 0.35] },
    { key: 'kitchen', name: 'Kitchen & dining', room: 'Kitchen & dining', area: '≈ 26 m²',  title: 'Table for four.',
      pos: [2.85, 7.0, 25.0], target: [3.0, 0.7, 15.3], walk: [1.4, 13.6, Math.PI - 0.5] },
    { key: 'bedroom', name: 'Bedroom',         room: 'Bedroom',           area: '≈ 10 m²',  title: 'Wake up to the terrace.',
      pos: [1.8, 7.0, -1.5], target: [1.8, 0.4, 8.4], walk: [3.05, 8.9, Math.PI / 2 + 0.6] },
    { key: 'bath',    name: 'Bathroom',        room: 'Bathroom',          area: '≈ 7.5 m²', title: 'Walk-in shower at the end.',
      pos: [-2.5, 8.5, 11.0], target: [4.65, 0.6, 11.0], walk: [4.4, 10.3, Math.PI - 0.3] },
    { key: 'service', name: 'Laundry',         room: 'Laundry',           area: '≈ 1.7 m²', title: 'Washer and dryer, off the terrace.',
      pos: [5.05, 4.5, -2.0], target: [5.05, 0.7, 6.2], walk: [5.0, 5.0, Math.PI] },
    { key: 'terrace', name: 'Terrace',         room: 'Terrace',           area: '≈ 39 m²',  title: 'Dinner outside.',
      pos: [-7.0, 6.5, -6.0], target: [2.85, 0.6, 3.2], walk: [2.85, 5.0, 0.0] },
  ],
}
