# Workspace Instructions: build123d CAD Modeling

When building CAD models in this repository:

1. **Follow `build123d` Skill Standards**: Always follow the syntax and patterns defined in the `build123d` skill ([SKILL.md](file:///home/luke/repos/code-cad/.agents/skills/build123d/SKILL.md)).
2. **API Reference Documents**: Rely on the extracted API reference documents in [.agents/skills/build123d/references/](file:///home/luke/repos/code-cad/.agents/skills/build123d/references/) for accurate parameters and method signatures.
3. **Model Script Architecture (No CLI, Generator-Ready)**:
   - **No CLI Interfaces**: Do NOT add CLI argument parsers (`argparse`, `click`, `sys.argv`). The user interacts with scripts directly by tweaking parameters/variables in the code.
   - **Parametric `@dataclass` as Single Source of Truth**:
     - Define all geometric and feature parameters at the top of the file in a dedicated dataclass named `<Model>Params` (e.g. `RackBracketParams`, `ContainerLidParams`).
     - Provide clear type annotations, default values, and comments for all fields.
     - **Explicit Nested `@dataclass` Grouping & Feature Toggles**:
       - Group related parameters into explicit nested `@dataclass`es composed on the root `<Model>Params` dataclass using `field(default_factory=...)` (e.g., `core: CoreParams`, `scoop: ScoopParams`, `label: LabelHolderParams`, `dividers: DividersParams`, `overhang: OverhangParams`).
       - For any optional/toggleable feature section, include an `enabled: bool` field inside that section's dataclass (e.g. `ScoopParams.enabled`, `DividersParams.enabled`). The GUI (`code-cad-studio`) automatically renders each nested dataclass as a collapsible section card and promotes `enabled: bool` into the section header toggle.
       - Use `Literal[...]` for constrained string choices so the GUI renders dropdowns.
       - **UI Metadata Conventions (`code-cad-studio`)**:
         - Use `field(default=..., metadata={"min": ..., "max": ..., "step": ...})` for slider bounds on key tunable dimensions.
         - Use `field(default=..., metadata={"when": {"<field_or_path>": <value_or_list>}})` for mode-dependent/conditional parameters (bare keys resolve from the current group; dotted paths like `"core.shape"` resolve from root params; also supported on nested group fields).
         - Use `Optional[T] = None` for auto-computed parameters (rendered as `Auto` in Studio).
       - Avoid string-prefix `*_enabled` grouping heuristics and redundant alias properties.
     - **Presets Standard (`presets.json`)**:
       - Do **not** embed preset dictionaries inside Python model scripts (only canonical dataclass defaults belong in Python).
       - Store model presets in `models/<model_name>/presets.json` using the Studio sparse-diff JSON schema (`{ "<key>": { "label": "...", "description": "...", "params": { ... } } }`).
   - **Decoupled Generator Function & Side-Effect-Free Imports**:
     - Implement CAD logic as a standalone generator function `create_<model>(params: <Model>Params) -> Part | Compound | Solid`.
     - It must accept the dataclass instance and return the generated geometry without side effects (no exports, file writes, or viewer calls inside the generator). This ensures it can be imported and plugged directly into an external GUI/web viewer worker.
     - **Never import `ocp_viewer` / `ocp_vscode` or call `set_defaults()` at module top-level** (nor construct geometry at import time). Keep viewer imports strictly inside `if __name__ == "__main__":` (or a lazy helper invoked only from `__main__`) so external preview/generator workers can import `<Model>Params` and `create_<model>` cleanly without viewer side effects.
   - **Standardized Export Variables**:
     Every model script must standardize on these exact top-level variable names to control exports, and they **must always be set to `False` by default**:
     ```python
     EXPORT_STL: bool = False      # Enable/disable STL file export (default: False)
     EXPORT_STEP: bool = False     # Enable/disable STEP file export (default: False)
     OUTPUT_DIR: str = "exports"   # Relative subfolder alongside the script
     ```
   - **Exports Location Standard**:
     Always default to saving exports inside an `exports/` directory located alongside the source `.py` script (e.g. `Path(__file__).resolve().parent / OUTPUT_DIR`), creating the directory if it does not exist. Never export directly into the repository root or current working directory.
   - **Standardized Export Filename Convention & Hook**:
     Export filenames must follow the pattern:
     `<model_name>_<primary_dimensions>_<variant_or_style>.<ext>`
     in lowercase `snake_case` (e.g. `rack_bracket_2u_hex.stl`, `shaft_end_cap_12.7mm_round.stl`, `magnetic_label_100x16mm_fasteners_embossed_base.stl`, `container_lid_150mm_round_tpu.stl`, `spacer_100x100x3mm_corner.stl`).
     Models may define `def export_filename(params: <Model>Params) -> str:` returning this lowercase `snake_case` stem (without extension), reused by both `__main__` exports and Studio Save-As dialogs.
     This ensures immediate identification across slicers, file managers, and future web generator download endpoints.
   - **Strict Standalone Architecture (No Compatibility Shims or Legacy Wrappers)**:
     - Every model script must be completely self-contained in its canonical file: `models/<model_name>/<model_name>.py`.
     - **Never create backwards-compatibility shims, wrapper scripts, redirect files, or deprecated alias modules** (e.g. do not create `old_name.py` alongside `new_name.py`). When refactoring, renaming, or migrating, rename cleanly and delete obsolete files.
     - **Never retain legacy parameter aliases, duplicate getters, or forwarding shims in `@dataclass` definitions** (e.g. do not keep deprecated `x`, `y`, `z` fields or `__post_init__` alias mappings). Remove dead fields directly.
     - Scripts must remain concise and zero-dependency beyond `build123d` and `ocp_viewer`/`ocp_vscode`.
   - **Clean `__main__` Block Without Parameter Overrides**:
     In the `if __name__ == "__main__":` block:
     - Instantiate `params = <Model>Params()` with **no hardcoded arguments** so that editing the dataclass defaults at the top of the file immediately takes effect.
     - Call the generator function: `part = create_<model>(params)`.
     - Export STL/STEP according to `EXPORT_STL` and `EXPORT_STEP` into `OUTPUT_DIR`.
     - Display the part via `show(part)` using a dual-compatible import (`ocp_viewer` preferred, falling back to `ocp_vscode`):
       ```python
       try:
           from ocp_viewer import set_defaults, show
           set_defaults(orbit_control=True)
       except ImportError:
           try:
               from ocp_vscode import set_defaults, show
               set_defaults(orbit_control=True)
           except ImportError:
               def show(*args, **kwargs):
                   pass
       ```
4. **Model Validation**: Validate models by running python scripts with `ocp_viewer` / `ocp_vscode` `show()` or checking export operations.
5. **Clean Workspace Rule**: Do NOT create temporary test or validation scripts in the root project directory. Store reusable test/utility scripts inside `.agents/scripts/` or delete temporary scratch scripts immediately after validation completes.
6. **Git & Commit Protocol**:
   - Never commit or push changes without first presenting a full recap/summary explaining the solution, and waiting for explicit user approval to proceed.
   - **Per-Model Commit Isolation**: Always keep commits for each model separate (scoping model changes to their respective `models/<model_name>/` directory and related index entry, and keeping repo-level config/rule changes in separate commits) so the git history for any specific model directory remains clean and easy to inspect.
