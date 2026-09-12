"""
Procedural, seamless PBR texture sets generated with numpy and saved through Blender's image API.
No downloads needed, so the model builds identically offline and in CI.

Each set is written to blender/tex/<name>_color.jpg, _rough.jpg, _normal.png and cached; delete the folder to regenerate.
Every set tiles over `tile` metres (returned with the paths) so the build script can scale UVs per object.
"""
import math
import os

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(HERE, "tex")
os.makedirs(TEX_DIR, exist_ok=True)

_rng = np.random.default_rng(7)


# ----------------------------------------------------------------------------- periodic noise
def _lattice(n, seed):
    return np.random.default_rng(seed).random((n, n)).astype(np.float32)


def value_noise(size, period, seed=0, octaves=4, gain=0.5):
    """fBm value noise that tiles seamlessly: each octave's lattice is periodic over the image."""
    out = np.zeros((size, size), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = period * (2 ** o)
        lat = _lattice(n, seed * 31 + o)
        ys = np.linspace(0, n, size, endpoint=False)
        xs = np.linspace(0, n, size, endpoint=False)
        y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
        fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        y1 = (y0 + 1) % n; x1 = (x0 + 1) % n
        a = lat[np.ix_(y0, x0)]; b = lat[np.ix_(y0, x1)]; c = lat[np.ix_(y1, x0)]; d = lat[np.ix_(y1, x1)]
        v = a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy
        out += v * amp
        total += amp
        amp *= gain
    return out / total


def stretched_noise(size, px, py, seed=0, octaves=4):
    """anisotropic tiling noise (wood grain): different lattice periods per axis."""
    out = np.zeros((size, size), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        nx, ny = px * (2 ** o), py * (2 ** o)
        lat = np.random.default_rng(seed * 17 + o).random((ny, nx)).astype(np.float32)
        ys = np.linspace(0, ny, size, endpoint=False); xs = np.linspace(0, nx, size, endpoint=False)
        y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
        fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        y1 = (y0 + 1) % ny; x1 = (x0 + 1) % nx
        a = lat[np.ix_(y0, x0)]; b = lat[np.ix_(y0, x1)]; c = lat[np.ix_(y1, x0)]; d = lat[np.ix_(y1, x1)]
        out += (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy) * amp
        total += amp; amp *= 0.5
    return out / total


def warp(size, field_fn, amount=0.08, seed=100):
    """domain-warp a periodic field: sample it at coordinates displaced by two noise fields (stays periodic)."""
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    dx = (value_noise(size, 4, seed, 3) - 0.5) * amount * size
    dy = (value_noise(size, 4, seed + 1, 3) - 0.5) * amount * size
    xi = np.mod(np.rint(xs + dx), size).astype(int); yi = np.mod(np.rint(ys + dy), size).astype(int)
    return field_fn()[yi, xi]


def normal_from_height(h, strength=2.0):
    """tangent-space normal map from a periodic height field (0..1)."""
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * strength
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * strength
    nx, ny, nz = -dx, dy, np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / l, ny / l, nz / l], -1) * 0.5 + 0.5


def _hex(c):
    return np.array([int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def _save(name, rgb, fmt):
    """rgb: HxWx3 float 0..1 → file. JPEG for colour/roughness, PNG for normals."""
    path = os.path.join(TEX_DIR, name + ("." + ("png" if fmt == "PNG" else "jpg")))
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    px = np.concatenate([np.clip(rgb, 0, 1), np.ones((h, w, 1), np.float32)], -1)
    img.pixels.foreach_set(np.ascontiguousarray(np.flipud(px), dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = fmt
    if fmt == "JPEG":
        bpy.context.scene.render.image_settings.quality = 90 if "normal" in name else 82
    img.save()
    bpy.data.images.remove(img)
    return path


# ----------------------------------------------------------------------------- generators
def _wood_grain(size, seed, rings=26, wander=0.05, streak=0.4):
    """periodic wood: ring stripes along x, warped so they wander like real cathedral grain"""
    ys = np.linspace(0, 1, size, endpoint=False)[:, None]
    base = value_noise(size, 2, seed, 2)
    field = lambda: (np.sin((ys + base * 0.35) * 2 * np.pi * rings) * 0.5 + 0.5).astype(np.float32) * np.ones((size, size), np.float32)
    r = warp(size, field, amount=wander, seed=seed + 40)
    r = r ** 2.2                                            # thin dark late-wood lines
    fine = stretched_noise(size, 3, 64, seed + 3, 3)         # fibre streaks along the plank
    fine2 = stretched_noise(size, 2, 200, seed + 9, 2)       # very fine fibres
    return np.clip(0.35 + r * 0.45 + (fine - 0.5) * streak + (fine2 - 0.5) * 0.15, 0, 1)


def wood_planks(size, base, dark, plank_w=0.16, plank_len=1.0, tile=2.0, seed=1, grain=0.35):
    """staggered planks with wandering ring grain; tile is the physical size covered by the image."""
    rows = int(round(tile / plank_w)); cols = int(round(tile / plank_len))
    ys = np.linspace(0, rows, size, endpoint=False); xs = np.linspace(0, cols, size, endpoint=False)
    row = np.floor(ys).astype(int)[:, None]
    offset = (row * 0.5) % 1.0                       # stagger every other row by half a plank
    col = np.floor(xs[None, :] + offset).astype(int) % cols
    plank_id = (row * 7919 + col * 104729) % 977
    rng = np.random.default_rng(seed)
    per = rng.random(977).astype(np.float32)[plank_id]                              # per-plank tone
    hue = rng.random(977).astype(np.float32)[plank_id]                              # per-plank warmth
    g = _wood_grain(size, seed)
    # each plank samples the grain at its own vertical offset so neighbours never repeat
    shift = (rng.random(977) * size).astype(int)[plank_id]
    g = np.take_along_axis(np.broadcast_to(g, (size, size)), (np.arange(size)[:, None] + shift) % size, axis=0)
    t = np.clip(0.5 + (per - 0.5) * 0.4 + (g - 0.5) * grain * 1.6, 0, 1)
    fy = ys[:, None] - np.floor(ys[:, None]); fx = (xs[None, :] + offset) - np.floor(xs[None, :] + offset)
    seam = np.minimum(np.minimum(fy, 1 - fy) * rows * tile / 0.005, np.minimum(fx, 1 - fx) * cols * tile / 0.005)
    seam = np.clip(seam, 0, 1)                                                      # 0 at joints
    warm = np.array([1.06, 1.0, 0.92], np.float32)
    color = base[None, None, :] * t[..., None] + dark[None, None, :] * (1 - t[..., None])
    color = color * (1 + (hue[..., None] - 0.5) * 0.12 * (warm[None, None, :] - 1) * 8)
    color = color * (0.5 + 0.5 * seam[..., None])
    rough = np.clip(0.38 + (1 - t) * 0.3 + (1 - seam) * 0.4, 0, 1)
    height = np.clip(t * 0.2 + seam * 0.8, 0, 1)
    return color, rough, normal_from_height(height, 1.8), tile


def plaster(size, base, tile=2.0, seed=5, amount=0.05):
    n = value_noise(size, 6, seed, 5); n2 = value_noise(size, 96, seed + 1, 2)
    trowel = warp(size, lambda: stretched_noise(size, 3, 10, seed + 5, 3), 0.06, seed + 9)   # faint diagonal sweeps
    t = 1 + (n - 0.5) * amount * 2 + (n2 - 0.5) * amount + (trowel - 0.5) * amount * 0.8
    color = base[None, None, :] * t[..., None]
    rough = np.clip(0.8 + (n2 - 0.5) * 0.2 + (trowel - 0.5) * 0.1, 0, 1)
    return color, rough, normal_from_height(n2 * 0.35 + trowel * 0.4 + n * 0.25, 0.5), tile


def concrete(size, base, tile=2.0, seed=9):
    n = value_noise(size, 6, seed, 6, 0.55); sp = value_noise(size, 128, seed + 2, 1)
    stains = warp(size, lambda: value_noise(size, 3, seed + 7, 4), 0.1, seed + 8)
    holes = np.clip((sp - 0.9) * 12, 0, 1)
    t = 1 + (n - 0.5) * 0.3 + (stains - 0.5) * 0.22 - holes * 0.3
    color = base[None, None, :] * t[..., None]
    rough = np.clip(0.82 + (n - 0.5) * 0.2 + holes * 0.15 + (stains - 0.5) * 0.1, 0, 1)
    return color, rough, normal_from_height(np.clip(n * 0.6 + stains * 0.4 - holes * 0.6, 0, 1), 1.2), tile


def fabric(size, base, tile=0.5, seed=3, weave=180, contrast=0.12):
    xs = np.linspace(0, 2 * math.pi * weave, size, endpoint=False)
    w = (np.sin(xs)[None, :] * np.sin(xs)[:, None]) * 0.5 + 0.5           # fine weave
    w2 = (np.sin(xs / 3)[None, :] * np.sin(xs / 3)[:, None]) * 0.5 + 0.5  # coarser basket structure
    n = value_noise(size, 16, seed, 4); fuzz = value_noise(size, 128, seed + 2, 1)
    t = 1 + (w - 0.5) * contrast + (w2 - 0.5) * contrast * 0.6 + (n - 0.5) * 0.14 + (fuzz - 0.5) * 0.06
    color = base[None, None, :] * t[..., None]
    rough = np.clip(0.88 + (w - 0.5) * 0.1 + (fuzz - 0.5) * 0.05, 0, 1)
    return color, rough, normal_from_height(w * 0.5 + w2 * 0.3 + n * 0.2, 1.0), tile


def leather(size, base, tile=0.6, seed=4):
    n = value_noise(size, 64, seed, 2, 0.5); n3 = value_noise(size, 24, seed + 4, 2, 0.5); n2 = value_noise(size, 5, seed + 1, 3)
    cells = np.clip((np.abs(n - 0.5) * 2) * 0.6 + (np.abs(n3 - 0.5) * 2) * 0.4, 0, 1)   # pebble grain at two scales
    creases = np.clip(1 - np.abs(warp(size, lambda: stretched_noise(size, 2, 8, seed + 6, 3), 0.08, seed + 7) - 0.5) * 10, 0, 1)
    t = 1 + (cells - 0.5) * 0.12 + (n2 - 0.5) * 0.14 + creases * 0.05
    color = base[None, None, :] * t[..., None]
    rough = np.clip(0.4 + cells * 0.28 + creases * 0.1, 0, 1)
    return color, rough, normal_from_height(1 - cells * 0.8 - creases * 0.2, 1.1), tile


def quartz(size, base, tile=1.5, seed=11):
    v = warp(size, lambda: stretched_noise(size, 3, 12, seed, 5), 0.12, seed + 3)
    veins = np.clip(1 - np.abs(v - 0.5) * 9, 0, 1) ** 2
    n = value_noise(size, 32, seed + 2, 2)
    t = 1 - veins * 0.18 - (n - 0.5) * 0.05
    color = base[None, None, :] * t[..., None]
    rough = np.clip(0.18 + veins * 0.05 + (n - 0.5) * 0.05, 0, 1)
    return color, rough, normal_from_height(n, 0.15), tile


def tiles(size, base, grout, tile_w=0.6, tile=1.2, seed=13, gap=0.004):
    n = int(round(tile / tile_w))
    xs = np.linspace(0, n, size, endpoint=False)
    fx = xs - np.floor(xs)
    sx = np.clip(np.minimum(fx, 1 - fx) * n * tile / gap, 0, 1)
    mask = np.minimum(sx[None, :], sx[:, None])
    ids = (np.floor(xs)[:, None] * 17 + np.floor(xs)[None, :] * 31).astype(int) % 101
    per = np.random.default_rng(seed).random(101).astype(np.float32)[ids]
    nz = value_noise(size, 12, seed, 3)
    t = 1 + (per - 0.5) * 0.08 + (nz - 0.5) * 0.06
    color = base[None, None, :] * t[..., None] * mask[..., None] + grout[None, None, :] * (1 - mask[..., None])
    rough = np.clip(0.22 + (1 - mask) * 0.6 + (nz - 0.5) * 0.05, 0, 1)
    return color, rough, normal_from_height(mask, 1.2), tile


def paving(size, base, slab=0.6, tile=2.4, seed=17):
    n = int(round(tile / slab))
    xs = np.linspace(0, n, size, endpoint=False)
    fx = xs - np.floor(xs)
    sx = np.clip(np.minimum(fx, 1 - fx) * n * tile / 0.012, 0, 1)
    mask = np.minimum(sx[None, :], sx[:, None])
    ids = (np.floor(xs)[:, None] * 13 + np.floor(xs)[None, :] * 29).astype(int) % 89
    per = np.random.default_rng(seed).random(89).astype(np.float32)[ids]
    nz = value_noise(size, 10, seed, 5, 0.55)
    t = 1 + (per - 0.5) * 0.22 + (nz - 0.5) * 0.25
    color = base[None, None, :] * t[..., None] * (0.6 + 0.4 * mask[..., None])
    rough = np.clip(0.8 + (nz - 0.5) * 0.2, 0, 1)
    return color, rough, normal_from_height(mask * 0.7 + nz * 0.3, 1.2), tile


def brushed(size, base, tile=0.5, seed=19):
    n = stretched_noise(size, 96, 2, seed, 3)
    color = base[None, None, :] * (1 + (n - 0.5) * 0.08)[..., None]
    rough = np.clip(0.28 + (n - 0.5) * 0.25, 0, 1)
    return color, rough, normal_from_height(n, 0.2), tile


def wood_solid(size, base, dark, tile=1.2, seed=23):
    g = _wood_grain(size, seed, rings=40, wander=0.02, streak=0.55)
    g2 = stretched_noise(size, 6, 40, seed + 1, 3)
    t = np.clip(0.5 + (g - 0.5) * 0.55 + (g2 - 0.5) * 0.15, 0, 1)
    color = base[None, None, :] * t[..., None] + dark[None, None, :] * (1 - t[..., None])
    rough = np.clip(0.4 + (1 - t) * 0.2, 0, 1)
    return color, rough, normal_from_height(t, 0.5), tile


# ----------------------------------------------------------------------------- catalogue
SETS = {
    "oak_floor": lambda s: wood_planks(s, _hex("#c9a778"), _hex("#8a6a45"), seed=1),
    "walnut":    lambda s: wood_solid(s, _hex("#6a4a35"), _hex("#3a2718"), seed=23),
    "oak":       lambda s: wood_solid(s, _hex("#cdae82"), _hex("#9a7a55"), seed=29),
    "plaster":   lambda s: plaster(s, _hex("#f0ece5")),
    "plaster_ext": lambda s: plaster(s, _hex("#d3cfc8"), seed=6, amount=0.08),
    "concrete":  lambda s: concrete(s, _hex("#b3b0aa")),
    "charcoal":  lambda s: fabric(s, _hex("#454749"), weave=200, contrast=0.16),
    "linen":     lambda s: fabric(s, _hex("#e9e4da"), weave=260, contrast=0.08),
    "wool_rug":  lambda s: fabric(s, _hex("#9c9891"), tile=0.8, weave=90, contrast=0.22),
    "leather":   lambda s: leather(s, _hex("#2a2725")),
    "leather_tan": lambda s: leather(s, _hex("#8a5a3a"), seed=8),
    "quartz":    lambda s: quartz(s, _hex("#ebe9e4")),
    "tile":      lambda s: tiles(s, _hex("#cfd0cf"), _hex("#a7a8a8")),
    "paving":    lambda s: paving(s, _hex("#a9a49c")),
    "brushed":   lambda s: brushed(s, _hex("#c8cacc")),
    "matte_black": lambda s: fabric(s, _hex("#232426"), tile=0.4, weave=1, contrast=0.0),
}


def ensure(name, size=1024):
    """returns dict(color=path, rough=path, normal=path, tile=metres), generating on first use."""
    color_p = os.path.join(TEX_DIR, f"{name}_color.jpg")
    rough_p = os.path.join(TEX_DIR, f"{name}_rough.jpg")
    norm_p = os.path.join(TEX_DIR, f"{name}_normal.jpg")
    meta_p = os.path.join(TEX_DIR, f"{name}.tile")
    if not all(os.path.exists(p) for p in (color_p, rough_p, norm_p, meta_p)):
        color, rough, normal, tile = SETS[name](size)
        _save(f"{name}_color", color, "JPEG")
        half = rough[::2, ::2]
        _save(f"{name}_rough", np.repeat(half[..., None], 3, -1), "JPEG")
        _save(f"{name}_normal", normal[::2, ::2], "JPEG")
        with open(meta_p, "w") as f:
            f.write(str(tile))
        print(f"  generated texture set {name} (tile {tile} m)")
    with open(meta_p) as f:
        tile = float(f.read())
    return dict(color=color_p, rough=rough_p, normal=norm_p, tile=tile)


if __name__ == "__main__":
    import time
    t0 = time.time()
    for k in SETS:
        ensure(k)
    print("done in %.1fs" % (time.time() - t0))
