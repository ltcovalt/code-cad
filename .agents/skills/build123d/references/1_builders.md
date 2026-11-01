# build123d Reference: Builder API & Context Managers

The **Builder API** uses Python context managers (`with`) to implicitly manage geometry state, working planes, pending faces/edges, and boolean operations.

---

## 1. Core Builders

### A. `BuildPart`
Context manager for creating 3D solid parts.

```python
with BuildPart(workplanes=Plane.XY, mode=Mode.ADD) as part_builder:
    # 3D primitives and extrusions automatically operate on part_builder
    Box(10, 20, 30)
```
- **`part_builder.part`**: Access the generated `Solid` or `Compound` object.
- **Parameters**:
  - `workplanes`: Single `Plane` or list of `Plane`s (default `Plane.XY`).
  - `mode`: Boolean mode for combining new solids (`Mode.ADD`, `Mode.SUBTRACT`, `Mode.INTERSECT`, `Mode.PRIVATE`).

### B. `BuildSketch`
Context manager for creating 2D sketches (used for extrusions, revolves, lofts, sweeps).

```python
with BuildSketch(plane=Plane.XY, mode=Mode.ADD) as sketch_builder:
    Circle(radius=10)
    Rectangle(5, 5, mode=Mode.SUBTRACT)
```
- **`sketch_builder.sketch`**: Access the generated 2D `Sketch` / `Face`.
- **`make_face()`**: Converts open or closed wires inside the sketch context into a filled face.

### C. `BuildLine`
Context manager for creating 1D curves and paths.

```python
with BuildLine(plane=Plane.XY) as line_builder:
    l1 = Line((0, 0), (10, 0))
    l2 = RadiusArc(l1.end, (20, 10), radius=10)
```
- **`line_builder.line`**: Access the generated `Wire` or `Edge`.

---

## 2. Boolean Modes (`Mode` Enum)

When adding geometry inside a builder context manager, the `mode` parameter controls how the new shape interacts with the active model:

| Mode | Description |
| :--- | :--- |
| `Mode.ADD` | Union / add geometry to the active builder (default for most operations). |
| `Mode.SUBTRACT` | Difference / cut geometry out of the active builder. |
| `Mode.INTERSECT` | Keep only the intersection between existing geometry and new shape. |
| `Mode.PRIVATE` | Create shape without adding/submitting it to the active builder context. |

---

## 3. Nesting Builders

Builders nest intuitively:
1. `BuildSketch` inside `BuildPart`: Extrude or revolve operations automatically consume the pending sketch.
2. `BuildLine` inside `BuildSketch`: Sketches can use `BuildLine` paths to define boundary wires.

```python
with BuildPart() as base:
    Box(50, 50, 10)
    with BuildSketch(base.faces().sort_by(Axis.Z)[-1]) as top_sketch:
        Circle(15)
    extrude(amount=-5, mode=Mode.SUBTRACT) # Cuts a pocket in top face
```
