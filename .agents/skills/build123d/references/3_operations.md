# build123d Reference: Operations & Modifications

Operations manipulate, transform, or combine 1D, 2D, and 3D shapes.

---

## 1. Extrude, Revolve, Sweep & Loft

### `extrude(to_extrude=None, amount=0.0, dir=None, mode=Mode.ADD, both=False)`
Extrudes a 2D sketch or face into a 3D solid.
- `amount`: Extrusion depth.
- `dir`: Custom extrusion vector direction.
- `both`: Extrude equally in positive and negative directions.

### `revolve(profiles=None, axis=Axis.Z, revolution_angle=360.0, mode=Mode.ADD)`
Revolves 2D sketch around a specified `Axis`.

### `sweep(sections=None, path=None, multisection=False, mode=Mode.ADD)`
Sweeps 2D profile(s) along a 1D path line.

### `loft(sections=None, ruled=False, mode=Mode.ADD)`
Lofts across multiple 2D profile sections.

---

## 2. Fillets, Chamfers & Shelling

### `fillet(objects=None, radius=0.0)`
Rounds specified edges.
```python
fillet(part.edges(), radius=2.0)
```

### `chamfer(objects=None, length=0.0, length2=None)`
Bevels specified edges.
```python
chamfer(part.edges().filter_by(Axis.Z), length=1.5)
```

### `offset(objects=None, amount=0.0, openings=None, kind=Kind.ARC, mode=Mode.ADD)`
Offsets 2D or 3D geometry inwards or outwards.

### `thick_solid(objects=None, openings=None, amount=0.0)`
Hollows out a solid while removing specified faces (`openings`).

---

## 3. Transformations & Boolean Operations

- **`mirror(objects=None, about=Plane.XZ, mode=Mode.ADD)`**: Mirrors shape across a plane.
- **`scale(objects=None, by=1.0, mode=Mode.ADD)`**: Uniformly scales geometry.
- **`split(objects=None, bisect_by=Plane.XZ, keep=Keep.BOTH)`**: Cuts solid using a plane.
- **`project(target=..., line=...)`**: Projects 1D/2D curve onto 3D face.
