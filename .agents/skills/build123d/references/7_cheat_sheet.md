# build123d Quick Reference Cheat Sheet

| Category | Class / Function | Common Usage / Syntax |
| :--- | :--- | :--- |
| **3D Builder** | `BuildPart` | `with BuildPart(workplanes=Plane.XY) as p:` |
| **2D Builder** | `BuildSketch` | `with BuildSketch(Plane.XY) as s:` |
| **1D Builder** | `BuildLine` | `with BuildLine(Plane.XY) as l:` |
| **3D Prim** | `Box` | `Box(length, width, height, align=...)` |
| **3D Prim** | `Cylinder` | `Cylinder(radius, height, align=...)` |
| **3D Prim** | `Sphere` | `Sphere(radius)` |
| **2D Prim** | `Rectangle` | `Rectangle(width, height)` |
| **2D Prim** | `Circle` | `Circle(radius)` |
| **Operations** | `extrude` | `extrude(amount=10, mode=Mode.ADD)` |
| **Operations** | `revolve` | `revolve(axis=Axis.Z, revolution_angle=360)` |
| **Operations** | `fillet` | `fillet(part.edges(), radius=2.0)` |
| **Operations** | `chamfer` | `chamfer(part.edges(), length=1.0)` |
| **Selectors** | `filter_by` | `part.edges().filter_by(Axis.Z)` |
| **Selectors** | `sort_by` | `part.faces().sort_by(Axis.Z)[-1]` |
| **Locations** | `GridLocations` | `with GridLocations(x_spacing=10, y_spacing=10, x_count=2, y_count=2):` |
| **Locations** | `PolarLocations`| `with PolarLocations(radius=15, count=6):` |
| **Export** | `export_step` | `export_step(part, "out.step")` |
| **Export** | `export_stl` | `export_stl(part, "out.stl")` |

---

## Minimal Parametric Template

```python
from dataclasses import dataclass
from build123d import *
try:
    from ocp_viewer import show
except ImportError:
    from ocp_vscode import show

@dataclass
class PartConfig:
    width: float = 40.0
    length: float = 60.0
    height: float = 12.0
    hole_dia: float = 8.0
    fillet_r: float = 3.0

def make_part(cfg: PartConfig) -> Solid:
    with BuildPart() as b:
        Box(cfg.length, cfg.width, cfg.height)
        with BuildSketch(b.faces().sort_by(Axis.Z)[-1]):
            Circle(radius=cfg.hole_dia / 2)
        extrude(amount=-cfg.height, mode=Mode.SUBTRACT)
        fillet(b.edges().filter_by(Axis.Z), radius=cfg.fillet_r)
    return b.part

if __name__ == "__main__":
    cfg = PartConfig()
    model = make_part(cfg)
    show(model)
```
