// King's Tower · Dept. D — everything in app.js that is specific to this apartment.
// pos / target in metres, apartment space: x east, y up, z south (origin = NW corner of the living room).
// walk: [x, z, yaw] standing spot + heading for the first-person mode (yaw 0 = north, π/2 = west, −π/2 = east).
import * as plan from './plan.js'

export default {
  key: 'kings-tower-d',
  name: "King's Tower · Dept. D",
  plan,
  textures: 'textures/',        // shared photo-scanned texture sets (fetched at deploy time)
  glbBytes: 8.7e6,              // progress estimate when the server sends no content-length
  center: [6.2, 1.3, 3.0],      // cutaway pivot
  walkBounds: { minX: -0.3, maxX: 12.7, minZ: 0.1, maxZ: 5.85 },
  views: [
    { key: 'whole',   name: 'Whole apartment', room: 'Whole apartment', area: '50.21 m² + 29.75 m² terrace', title: 'Room to live.',
      pos: [-7.5, 11.5, 16.5], target: [6.2, 0.5, 3.0], walk: [1.4, 0.9, -Math.PI / 2 - 0.3] },
    { key: 'living',  name: 'Living',          room: 'Living',            area: '≈ 14 m²',  title: 'Where the day lands.',
      pos: [-6.0, 5.0, 5.0], target: [2.8, 0.6, 2.2], walk: [3.0, 1.1, Math.PI / 2 + 0.35] },
    { key: 'kitchen', name: 'Kitchen & dining', room: 'Kitchen & dining', area: '≈ 12 m²',  title: 'Cook, eat, repeat.',
      pos: [9.0, 6.0, -5.5], target: [5.3, 0.7, 1.7], walk: [5.9, 0.75, Math.PI] },
    { key: 'bedroom', name: 'Bedroom',         room: 'Bedroom',           area: '≈ 12 m²',  title: 'Quiet corner.',
      pos: [6.2, 9.5, 11.0], target: [5.5, 0.3, 4.4], walk: [5.3, 3.25, Math.PI] },
    { key: 'bath',    name: 'Bathroom',        room: 'Bathroom',          area: '≈ 3.5 m²', title: 'Walk-in shower.',
      pos: [-3.5, 4.0, 9.0], target: [1.0, 0.8, 5.0], walk: [1.5, 5.0, Math.PI * 0.5] },
    { key: 'service', name: 'Service area',    room: 'Service area',      area: '≈ 2 m²',   title: 'Laundry, tucked away.',
      pos: [2.6, 5.0, 12.0], target: [2.55, 0.6, 5.3], walk: [2.7, 4.7, Math.PI] },
    { key: 'terrace', name: 'Terrace',         room: 'Terrace',           area: '29.75 m²', title: 'The outdoor room.',
      pos: [17.0, 5.0, -2.5], target: [10.3, 0.8, 3.0], walk: [8.6, 2.6, -Math.PI / 2] },
  ],
}
