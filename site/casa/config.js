// Casa · 2 plantas + desván — everything in app.js that is specific to this house.
// pos / target in metres, x east, y up, z south (origin = NW corner of the comedor). Levels: 0 planta baja, 1 planta alta, 2 desván.
// walk: [x, z, yaw] standing spot + heading (yaw 0 = north, π/2 = west, −π/2 = east); the view's `level` picks the floor.
import { levels as plans } from './plan.js'

const Y1 = 2.95, Y2 = 5.8
export default {
  key: 'casa',
  name: 'Casa · 2 plantas',
  plan: plans[0],
  levels: [
    { key: 'ground', name: 'Planta baja', y: 0,  plan: plans[0], walkBounds: { minX: 0.15, maxX: 9.65, minZ: 0.15, maxZ: 9.9 } },
    { key: 'upper',  name: 'Planta alta', y: Y1, plan: plans[1], walkBounds: { minX: 0.15, maxX: 9.65, minZ: 2.15, maxZ: 8.9 } },
    { key: 'attic',  name: 'Desván',      y: Y2, plan: plans[2], walkBounds: { minX: 0.3, maxX: 9.5, minZ: 2.3, maxZ: 8.8 } },
  ],
  textures: '../textures/',
  glbBytes: 11.5e6,
  center: [4.9, 3.0, 5.0],
  walkBounds: { minX: 0.15, maxX: 9.65, minZ: 0.15, maxZ: 9.9 },
  views: [
    { key: 'whole',   name: 'Whole house',      room: 'Whole house',      area: '2 plantas + desván', title: 'A house on three levels.',
      pos: [-14.0, 16.0, 22.0], target: [4.9, 2.5, 4.5], walk: [3.7, 8.4, 0.0], level: undefined },
    { key: 'ground',  name: 'Planta baja',      room: 'Planta baja',      area: 'living · comedor · cocina · estudio', title: 'Ground floor.',
      pos: [-12.0, 12.0, 18.0], target: [4.9, 0.5, 4.5], walk: [4.6, 4.2, Math.PI / 2], level: 0 },
    { key: 'living',  name: 'Living & comedor', room: 'Living & comedor', area: '≈ 24 m²', title: 'Long room, two ends.',
      pos: [-8.0, 5.0, 12.0], target: [1.6, 0.6, 5.5], walk: [1.5, 4.1, Math.PI], level: 0 },
    { key: 'kitchen', name: 'Cocina',           room: 'Cocina',           area: '3.2 × 2.6 m', title: 'Kitchen under the lean-to.',
      pos: [4.8, 5.0, -6.0], target: [4.8, 0.7, 1.3], walk: [5.0, 2.2, 0.0], level: 0 },
    { key: 'estudio', name: 'Estudio',          room: 'Estudio',          area: '2.67 × 4 m', title: 'Two desks, one wall of books.',
      pos: [14.0, 6.0, 10.0], target: [8.2, 0.6, 4.8], walk: [7.6, 6.5, 0.2], level: 0 },
    { key: 'upper',   name: 'Planta alta',      room: 'Planta alta',      area: '3 dormitorios · baño · balcón', title: 'Upstairs.',
      pos: [-12.0, 15.0, 18.0], target: [4.9, Y1 + 0.5, 5.5], walk: [4.5, 6.4, 0.0], level: 1 },
    { key: 'bedroom', name: 'Dormitorio NW',    room: 'Dormitorio',       area: '4.09 × 3.44 m', title: 'Bed to the north wall.',
      pos: [-6.0, 9.0, 0.0], target: [2.0, Y1 + 0.5, 3.7], walk: [2.0, 4.9, 0.0], level: 1 },
    { key: 'padres',  name: 'Dormitorio padres', room: 'Dormitorio padres', area: '6.2 m deep', title: 'The long bedroom.',
      pos: [15.0, 9.0, 12.0], target: [8.2, Y1 + 0.5, 6.0], walk: [7.3, 5.2, -Math.PI / 2 - 0.5], level: 1 },
    { key: 'balcon',  name: 'Balcón',           room: 'Balcón',           area: 'over the porch', title: 'Over the front door.',
      pos: [4.8, 8.0, 16.0], target: [4.8, Y1 + 0.5, 8.3], walk: [4.8, 7.6, Math.PI], level: 1 },
    { key: 'attic',   name: 'Desván',           room: 'Desván',           area: 'storage under the roof', title: 'Under the tiles.',
      pos: [-8.0, 12.0, 14.0], target: [4.9, Y2 + 0.5, 5.5], walk: [4.9, 6.5, Math.PI / 2], level: 2 },
  ],
}
