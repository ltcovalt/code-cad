# build123d Reference: Algebra API & Geometry Primitives

build123d supports an **Algebraic Syntax** for direct mathematical operations on shape objects without context managers.

---

## 1. Algebra Operators

- **Union (`+`)**: Combine two shapes (`shape1 + shape2`).
- **Difference (`-`)**: Cut shape2 from shape1 (`shape1 - shape2`).
- **Intersection (`&`)**: Keep overlapping volume (`shape1 & shape2`).

```python
# Algebraic modeling example
body = Box(30, 30, 10) - Cylinder(radius=5, height=10)
```

---

## 2. 3D Primitives

All 3D primitives accept `align` tuples, e.g. `align=(Align.CENTER, Align.CENTER, Align.MIN)`.

- **`Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.CENTER))`**
- **`Cylinder(radius, height, arc_size=360, align=...)`**
- **`Sphere(radius, arc_size1=-90, arc_size2=90, arc_size3=360, align=...)`**
- **`Cone(bottom_radius, top_radius, height, align=...)`**
- **`Torus(major_radius, minor_radius, major_angle=360, minor_angle=360, align=...)`**
- **`Wedge(dx, dy, dz, xmin, xmax, ymin, ymax, align=...)`**

---

## 3. 2D Primitives (Sketches & Profiles)

- **`Rectangle(width, height, align=...)`**
- **`RectangleRounded(width, height, radius, align=...)`**
- **`Circle(radius, align=...)`**
- **`Ellipse(x_radius, y_radius, align=...)`**
- **`Polygon(*pts, align=...)`**
- **`RegularPolygon(radius, side_count, align=...)`**
- **`SlotCenterToCenter(center_separation, height, rotation=0)`**
- **`SlotCenterToCorner(height, width, rotation=0)`**
- **`SlotOverall(width, height, rotation=0)`**
- **`Text(text, font_size, font="Arial", align=...)`**

---

## 4. 1D Curves & Lines (`BuildLine` elements)

- **`Line(pts1, pts2)`**: Straight line between two points.
- **`Polyline(*pts)`**: Series of connected line segments.
- **`Spline(*pts, tangents=..., mode=Mode.ADD)`**: Smooth cubic spline curve.
- **`CenterArc(center, radius, start_angle, arc_size)`**: Arc defined by center point.
- **`RadiusArc(start_pt, end_pt, radius)`**: Arc defined by start, end, and radius.
- **`ThreePointArc(pt1, pt2, pt3)`**: Arc passing through 3 points.
- **`Bezier(*control_points)`**: Bezier curve.
