# Workspace Instructions: build123d CAD Modeling

When building CAD models in this repository:

1. **Follow `build123d` Skill Standards**: Always follow the syntax and patterns defined in the `build123d` skill ([SKILL.md](file:///home/luke/repos/code-cad/.agents/skills/build123d/SKILL.md)).
2. **API Reference Documents**: Rely on the extracted API reference documents in [.agents/skills/build123d/references/](file:///home/luke/repos/code-cad/.agents/skills/build123d/references/) for accurate parameters and method signatures.
3. **Model Script Architecture (No CLI, Generator-Ready)**:
   - **No CLI Interfaces**: Do NOT add CLI argument parsers (`argparse`, `click`, `sys.argv`). The user interacts with scripts directly by tweaking parameters/variables in the code.
   - **Parametric `@dataclass` as Single Source of Truth**:
     - Define all geometric and feature parameters at the top of the file in a dedicated dataclass named `<Model>Params` (e.g. `RackBracketParams`, `LidParams`).
     - Provide clear type annotations, default values, and comments for all fields.
     - Avoid redundant alias properties or duplicate getters.
   - **Decoupled Generator Function**:
     - Implement CAD logic as a standalone generator function `create_<model>(params: <Model>Params) -> Part | Compound | Solid`.
     - It must accept the dataclass instance and return the generated geometry without side effects (no exports or viewer calls inside the generator). This ensures it can be imported and plugged into a future web generator/preview service directly.
   - **Standardized Export Variables**:
     Every model script must standardize on these exact top-level variable names to control exports:
     ```python
     EXPORT_STEP: bool = True      # Enable/disable STEP file export
     EXPORT_STL: bool = True       # Enable/disable STL file export
     OUTPUT_DIR: str = "exports"   # Relative subfolder alongside the script
     ```
   - **Exports Location Standard**:
     Always default to saving exports inside an `exports/` directory located alongside the source `.py` script (e.g. `Path(__file__).resolve().parent / OUTPUT_DIR`), creating the directory if it does not exist. Never export directly into the repository root or current working directory.
   - **Clean `__main__` Block Without Parameter Overrides**:
     In the `if __name__ == "__main__":` block:
     - Instantiate `params = <Model>Params()` with **no hardcoded arguments** so that editing the dataclass defaults at the top of the file immediately takes effect.
     - Call the generator function: `part = create_<model>(params)`.
     - Export STEP/STL according to `EXPORT_STEP` and `EXPORT_STL` into `OUTPUT_DIR`.
     - Display the part via `ocp_vscode`'s `show(part)`.
4. **Model Validation**: Validate models by running python scripts with `ocp_vscode` `show()` or checking export operations.
5. **Clean Workspace Rule**: Do NOT create temporary test or validation scripts in the root project directory. Store reusable test/utility scripts inside `.agents/scripts/` or delete temporary scratch scripts immediately after validation completes.
