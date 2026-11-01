---
name: build123d
description: Expert build123d 3D CAD modeling skill. Automatically triggered for any build123d modeling, 3D CAD, 2D sketch, assembly, or export tasks. Provides full API reference and best practices.
---

# build123d CAD Modeling Skill

This skill provides full API reference documentation, code patterns, and instructions for creating 3D CAD models using `build123d`.

## How Skill Invocation Works

This skill is **automatically invoked** whenever you request a build123d modeling task in this workspace. The assistant reads the instructions below and queries the API reference files in `references/` for exact parameters and signatures.

## Key Modeling Rules & Standards

1. **Prefer Builder API**: Use `with BuildPart()`, `with BuildSketch()`, and `with BuildLine()` context managers unless algebra syntax (`+`, `-`, `&`) is explicitly requested.
2. **Parametric Design**: Define all geometric parameters at the top of the script or inside a `@dataclass`.
3. **Topology Selectors**: Use `part.faces().sort_by(Axis.Z)[-1]` or `part.edges().filter_by(Axis.Z)` to select edges/faces robustly without hardcoded indices.
4. **Operations Chain**: Perform fillets and chamfers as the final step in part generation.
5. **Manufacturing Clearances**: Apply a default tolerance of `0.2mm` for mating 3D printed components.

## Complete API Reference Files

- [api_builders_and_common.md](file:///home/luke/repos/cad/.agents/skills/build123d/references/api_builders_and_common.md) - Full Builder API reference, Selectors (`vertices`, `faces`, `edges`), Enums (`Mode`, `Kind`, `Keep`, `Align`, `Select`, `SortBy`, `Until`), Locations (`Locations`, `GridLocations`, `PolarLocations`, `HexLocations`).
- [api_objects_1d_2d_3d.md](file:///home/luke/repos/cad/.agents/skills/build123d/references/api_objects_1d_2d_3d.md) - Full reference for 1D Curves (`Line`, `Polyline`, `Spline`, `Bezier`, `Arc`s), 2D Sketches (`Rectangle`, `Circle`, `Ellipse`, `Polygon`, `Slot`s, `Text`), 3D Solids (`Box`, `Cylinder`, `Sphere`, `Cone`, `Torus`, `Wedge`).
- [api_topological_objects.md](file:///home/luke/repos/cad/.agents/skills/build123d/references/api_topological_objects.md) - Topological shapes (`Vertex`, `Edge`, `Wire`, `Face`, `Shell`, `Solid`, `Compound`), Vector, Plane, Axis, and all operations (`extrude`, `revolve`, `sweep`, `loft`, `fillet`, `chamfer`, `offset`, `split`, `mirror`, `scale`, `thick_solid`).
- [api_import_export_joints.md](file:///home/luke/repos/cad/.agents/skills/build123d/references/api_import_export_joints.md) - Import/Export API (`export_step`, `export_stl`, `export_svg`, `export_dxf`, `import_step`, `import_stl`) and Joints (`RigidJoint`, `RevoluteJoint`, `LinearJoint`).
- [cheatsheet_and_faq.md](file:///home/luke/repos/cad/.agents/skills/build123d/references/cheatsheet_and_faq.md) - Best practices, FAQ, design tips, and quick cheat sheet.
