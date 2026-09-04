import { useEffect, useState, createContext, useContext } from 'react'
import { useTexture } from '@react-three/drei'
import * as THREE from 'three'

// Which texture sets exist on disk (written by `npm run assets`).
export const ManifestCtx = createContext({})

export function useManifest() {
  const [m, setM] = useState(null)
  useEffect(() => {
    fetch(import.meta.env.BASE_URL + 'textures/manifest.json').then(r => (r.ok ? r.json() : {})).then(setM).catch(() => setM({}))
  }, [])
  return m
}

// Loads color/normal/roughness/ao for a set and returns a ready material.
// Falls back to a flat MeshPhysicalMaterial if the set isn't downloaded yet.
export function usePBR(key, { repeat = [1, 1], color = '#cccccc', roughness = 0.8, ...rest } = {}) {
  const manifest = useContext(ManifestCtx)
  const has = !!manifest[key]
  const maps = useTexture(
    has
      ? { map: `${import.meta.env.BASE_URL}textures/${key}/color.jpg`, normalMap: `${import.meta.env.BASE_URL}textures/${key}/normal.jpg`, roughnessMap: `${import.meta.env.BASE_URL}textures/${key}/roughness.jpg`, aoMap: `${import.meta.env.BASE_URL}textures/${key}/ao.jpg` }
      : {}
  )
  const [mat] = useState(() => new THREE.MeshPhysicalMaterial({ color, roughness, ...rest }))
  useEffect(() => {
    if (!has) return
    for (const [k, t] of Object.entries(maps)) {
      t.wrapS = t.wrapT = THREE.RepeatWrapping
      t.repeat.set(repeat[0], repeat[1])
      t.anisotropy = 8
      if (k === 'map') t.colorSpace = THREE.SRGBColorSpace
      mat[k] = t
    }
    mat.color.set('#ffffff')
    mat.needsUpdate = true
  }, [has, maps, mat, repeat])
  return mat
}

// flat materials shared across the scene
export const flat = {
  ceil:     new THREE.MeshStandardMaterial({ color: '#f3f1ec', roughness: 0.9 }),
  graphite: new THREE.MeshPhysicalMaterial({ color: '#34373a', roughness: 0.45, clearcoat: 0.3 }),
  quartz:   new THREE.MeshPhysicalMaterial({ color: '#e8e5df', roughness: 0.18, clearcoat: 0.6, clearcoatRoughness: 0.15 }),
  oak:      new THREE.MeshStandardMaterial({ color: '#c2a078', roughness: 0.65 }),
  walnut:   new THREE.MeshStandardMaterial({ color: '#5a4030', roughness: 0.55 }),
  frame:    new THREE.MeshStandardMaterial({ color: '#2a2c2f', roughness: 0.5, metalness: 0.4 }),
  sofa:     new THREE.MeshStandardMaterial({ color: '#8b8275', roughness: 1 }),
  sofa2:    new THREE.MeshStandardMaterial({ color: '#6f665a', roughness: 1 }),
  linen:    new THREE.MeshStandardMaterial({ color: '#efece6', roughness: 1 }),
  throw:    new THREE.MeshStandardMaterial({ color: '#a39e93', roughness: 1 }),
  pillow:   new THREE.MeshStandardMaterial({ color: '#b59f77', roughness: 1 }),
  rug:      new THREE.MeshStandardMaterial({ color: '#b1a48f', roughness: 1, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }),
  white:    new THREE.MeshPhysicalMaterial({ color: '#f7f7f5', roughness: 0.2, clearcoat: 0.5 }),
  steel:    new THREE.MeshStandardMaterial({ color: '#c9ccd0', roughness: 0.28, metalness: 0.9 }),
  glass:    new THREE.MeshPhysicalMaterial({ color: '#dbe9f0', transparent: true, opacity: 0.22, roughness: 0.02, envMapIntensity: 1.2, depthWrite: false }),
  screen:   new THREE.MeshPhysicalMaterial({ color: '#0e0e10', roughness: 0.15, metalness: 0.3, clearcoat: 0.8 }),
  leaf:     new THREE.MeshStandardMaterial({ color: '#4b7539', roughness: 0.85 }),
  leaf2:    new THREE.MeshStandardMaterial({ color: '#679a4f', roughness: 0.85 }),
  pot:      new THREE.MeshStandardMaterial({ color: '#9d7d64', roughness: 0.9 }),
  brass:    new THREE.MeshStandardMaterial({ color: '#b8955a', roughness: 0.35, metalness: 0.85 }),
  tv:       new THREE.MeshStandardMaterial({ color: '#1d3550', emissive: '#2a5a85', emissiveIntensity: 0.8 }),
  lampShade: new THREE.MeshStandardMaterial({ color: '#f3e8d0', side: THREE.DoubleSide, emissive: '#ffd9a0', emissiveIntensity: 0.5 }),
  pendant:  new THREE.MeshStandardMaterial({ color: '#1a1a1a', side: THREE.DoubleSide, emissive: '#7a5525', emissiveIntensity: 0.7 }),
  downlight: new THREE.MeshStandardMaterial({ color: '#fff4e2', emissive: '#ffe6c2', emissiveIntensity: 3 }),
  art:      new THREE.MeshStandardMaterial({ color: '#8ea393' }),
  ground:   new THREE.MeshStandardMaterial({ color: '#88927b', roughness: 1 }),
}
