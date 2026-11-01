# build123d Reference: Planes, Axes, Locations & Selectors

---

## 1. Planes & Axes

### Standard Planes
- `Plane.XY`, `Plane.XZ`, `Plane.YZ`
- `Plane.front`, `Plane.back`, `Plane.top`, `Plane.bottom`, `Plane.left`, `Plane.right`

### Custom Planes
```python
custom_plane = Plane(origin=(0, 0, 10), z_dir=(0, 0, 1))
```

### Axes
- Standard axes: `Axis.X`, `Axis.Y`, `Axis.Z`
- Custom axis: `Axis(origin=(0, 0, 0), direction=(1, 1, 0))`

---

## 2. Locations & Positioning

### `Location` & `Locations`
Positions workplanes and child objects.

```python
with Locations((10, 0, 0), (20, 0, 0)):
    Circle(5) # Creates two circles at the specified locations
```

### Pattern Locations
- **`GridLocations(x_spacing, y_spacing, x_count, y_count)`**: Rectangular array of locations.
- **`PolarLocations(radius, count, start_angle=0, angular_range=360)`**: Circular array of locations.

---

## 3. Selectors & Filtering Topo Objects

Topology collections (`ShapeList`) provide powerful filtering methods:

### Filtering Edge/Face Collections
```python
# Filter faces by plane normal or geometry
top_face = part.faces().sort_by(Axis.Z)[-1]
vertical_edges = part.edges().filter_by(Axis.Z)
planar_faces = part.faces().filter_by(GeomType.PLANE)
parallel_edges = part.edges().filter_by(Parallel(Axis.X))
```

### Selection Modifiers
- **`.sort_by(Axis.Z)`**: Sort elements by position along an axis.
- **`.first()` / `.last()`**: Pick boundary element.
- **`.group_by(Axis.Z)`**: Group elements by coordinate.
