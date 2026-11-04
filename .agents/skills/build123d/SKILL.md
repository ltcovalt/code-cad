---
name: build123d
description: Expert build123d 3D CAD modeling skill. Automatically triggered for any build123d modeling, 3D CAD, 2D sketch, assembly, or export tasks. Provides full API reference and best practices.
---

# build123d CAD Modeling Skill

This skill provides full API reference documentation, code patterns, and instructions for creating 3D CAD models using `build123d`.

## How Skill Invocation Works

This skill is **automatically invoked** whenever you request a build123d modeling task in this workspace. The assistant reads the instructions below and queries the API reference files in `references/` for exact parameters and signatures.

## Key Modeling Rules & Standards

1. **Script Architecture (No CLI, Generator-Ready)**:
   - **No CLI / Argument Parsing**: Do not add CLI interfaces (`argparse`, `click`, etc.). Models are configured directly by editing variables/dataclass parameters in the file.
   - **Parametric `@dataclass` as Single Source of Truth**:
     - Define all geometric and feature parameters in a `@dataclass` named `<Model>Params` at the top of the file with clear default values and comments.
     - Avoid redundant alias properties or duplicate getters.
   - **Decoupled Generator Function**:
     - Implement the CAD logic in a standalone generator function `create_<model>(params: <Model>Params) -> Part | Compound | Solid` that receives the dataclass and returns the geometry object without side effects.
     - Do not run exports or viewer calls inside the generator function so it can easily be plugged into future online generators or preview services.
   - **Standardized Export Variables**:
     Every script must standardize on these exact top-level variable names:
     ```python
     EXPORT_STEP: bool = True      # Enable/disable STEP export
     EXPORT_STL: bool = True       # Enable/disable STL export
     OUTPUT_DIR: str = "exports"   # Relative subfolder alongside the script
     ```
   - **Exports Location Standard**:
     Always default to saving exports inside an `exports/` directory located alongside the source `.py` script (`Path(__file__).resolve().parent / OUTPUT_DIR`). Never dump export files in the repository root or current working directory.
   - **Clean Execution Block**: In `if __name__ == "__main__":`:
     - Instantiate `params = <Model>Params()` with no hardcoded parameter overrides so the defaults at the top of the file directly govern execution.
     - Call the generator function.
     - Export STEP/STL according to `EXPORT_STEP` and `EXPORT_STL` into `OUTPUT_DIR`.
     - View with `show(part)` from `ocp_vscode`.
2. **Prefer Builder API**: Use `with BuildPart()`, `with BuildSketch()`, and `with BuildLine()` context managers unless algebra syntax (`+`, `-`, `&`) is explicitly requested.
3. **Topology Selectors**: Use `part.faces().sort_by(Axis.Z)[-1]` or `part.edges().filter_by(Axis.Z)` to select edges/faces robustly without hardcoded indices.
4. **Operations Chain**: Perform fillets and chamfers as the final step in part generation.
5. **Manufacturing Clearances**: Apply a default tolerance of `0.2mm` for mating 3D printed components.

## Complete API Reference Files

- [api_builders_and_common.md](file:///home/luke/repos/code-cad/.agents/skills/build123d/references/api_builders_and_common.md) - Full Builder API reference, Selectors (`vertices`, `faces`, `edges`), Enums (`Mode`, `Kind`, `Keep`, `Align`, `Select`, `SortBy`, `Until`), Locations (`Locations`, `GridLocations`, `PolarLocations`, `HexLocations`).
- [api_objects_1d_2d_3d.md](file:///home/luke/repos/code-cad/.agents/skills/build123d/references/api_objects_1d_2d_3d.md) - Full reference for 1D Curves (`Line`, `Polyline`, `Spline`, `Bezier`, `Arc`s), 2D Sketches (`Rectangle`, `Circle`, `Ellipse`, `Polygon`, `Slot`s, `Text`), 3D Solids (`Box`, `Cylinder`, `Sphere`, `Cone`, `Torus`, `Wedge`).
- [api_topological_objects.md](file:///home/luke/repos/code-cad/.agents/skills/build123d/references/api_topological_objects.md) - Topological shapes (`Vertex`, `Edge`, `Wire`, `Face`, `Shell`, `Solid`, `Compound`), Vector, Plane, Axis, and all operations (`extrude`, `revolve`, `sweep`, `loft`, `fillet`, `chamfer`, `offset`, `split`, `mirror`, `scale`, `thick_solid`).
- [api_import_export_joints.md](file:///home/luke/repos/code-cad/.agents/skills/build123d/references/api_import_export_joints.md) - Import/Export API (`export_step`, `export_stl`, `export_svg`, `export_dxf`, `import_step`, `import_stl`) and Joints (`RigidJoint`, `RevoluteJoint`, `LinearJoint`).
- [cheatsheet_and_faq.md](file:///home/luke/repos/code-cad/.agents/skills/build123d/references/cheatsheet_and_faq.md) - Best practices, FAQ, design tips, and quick cheat sheet.
