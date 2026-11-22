# Workspace Instructions: code-cad (build123d CAD Modeling)

> **Scope:** Applies to the `code-cad` repository.

> **Pre-Release Policy (Active Until Further Notice):**
> This project is pre-release. Always favor the cleanest, most ideal code and project structure—even when that introduces breaking changes or requires refactoring existing models, schemas, or conventions. Aggressively remove dead, redundant, or unnecessary code, and do **not** add backwards-compatibility shims, fallbacks, migration layers, or deprecated aliases.

When building CAD models in this repository:

1. **Follow `build123d` Skill Standards**: Always follow the syntax and patterns defined in the `build123d` skill ([SKILL.md](file:///home/luke/repos/code-cad/.agents/skills/build123d/SKILL.md)).
2. **API Reference Documents**: Rely on the extracted API reference documents in [.agents/skills/build123d/references/](file:///home/luke/repos/code-cad/.agents/skills/build123d/references/) for accurate parameters and method signatures.
3. **Model Script Architecture (No CLI, Generator-Ready)**:
   - **No CLI Interfaces**: Do NOT add CLI argument parsers (`argparse`, `click`, `sys.argv`). The user interacts with scripts directly by tweaking parameters/variables in the code.
   - **Parametric `@dataclass` as Single Source of Truth**:
     - Define all geometric and feature parameters at the top of the file in a dedicated dataclass named `<Model>Params` (e.g. `RackBracketParams`, `ContainerLidParams`).
     - Provide clear type annotations, default values, and structured UI metadata (`desc`, `unit`, and `label` when needed) via `utils/params.py`.
     - **Explicit Nested `@dataclass` Grouping & Feature Toggles**:
       - Group related parameters into explicit nested `@dataclass`es composed on the root `<Model>Params` dataclass using `group(<SubParams>, ...)` from `utils/params.py` (which wraps `field(default_factory=...)`; e.g., `core: CoreParams = group(CoreParams)`, `snap_bead: SnapBeadParams = group(SnapBeadParams, when={"core.rim_style": "beaded"})`).
       - For any optional/toggleable feature section, include an `enabled: bool` field inside that section's dataclass (e.g. `ScoopParams.enabled`, `DividersParams.enabled`). The GUI (`code-cad-studio`) automatically renders each nested dataclass as a collapsible section card and promotes `enabled: bool` into the section header toggle.
       - Use `Literal[...]` for constrained string choices so the GUI renders dropdowns.
       - **Structured UI Metadata (`utils/params.py` & `code-cad-studio`)**:
         - Use `param(default, *, label=None, desc=None, unit=None, min=None, max=None, step=None, when=None)` from `utils/params.py` (which outputs standard `dataclasses.Field.metadata`).
         - Always format `param(...)` calls across multiple lines with the bare default value on its own line, `label`/`desc` below, and `unit`/`min`/`max`/`step`/`when` grouped underneath for consistent visual scanning.
         - Do **not** rely on `#` comments for UI descriptions—Studio reads strictly from `Field.metadata` (plus runtime nested class `"""docstrings"""`), leaving `#` comments purely for developer notes.
         - Specify `unit` (`"mm"`, `"in"`, `"°"`, `"U"`, etc.) instead of repeating units inside `desc`, and specify `label` only when the humanized field name needs improvement (e.g. `diameter_in` → `label="Diameter Override", unit="in"`).
         - Use `when={"<field_or_path>": <value_or_list>}` for mode-dependent/conditional parameters (bare keys resolve from the current group; dotted paths like `"core.shape"` resolve from root params; also supported on `group(...)`).
         - Use `Optional[T] = param(None, ...)` for auto-computed parameters (rendered as `Auto` in Studio).
         - Import `group, param` with the upward-search `utils` fallback so standalone scripts run directly via `python models/<name>/<name>.py` or `:!python %` without requiring package installation.
       - Avoid string-prefix `*_enabled` grouping heuristics and redundant alias properties.
     - **Presets Standard (`presets.json` & `@default_preset`)**:
       - Do **not** embed preset dictionaries inside Python model scripts (only canonical dataclass defaults belong in Python).
       - When a model's canonical dataclass defaults represent a specific real-world target (rather than generic dimensions), decorate the root `<Model>Params` dataclass with `@default_preset("<Label>", desc="...")` from `utils/params.py` so both readers of the Python script and Studio display a friendly name instead of `"Default"`.
       - Store additional model presets in `models/<model_name>/presets.json` using the Studio sparse-diff JSON schema (`{ "<key>": { "label": "...", "description": "...", "verification": { "status": "unverified" | "unusable" | "usable" | "verified", "note": "..." }, "params": { ... } } }`). The `verification` block is optional (omitted when `unverified` with no note), and an optional metadata-only `"default": { "verification": { ... } }` entry may record verification status and print notes for the canonical model default preset without touching Python source files.
   - **Decoupled Generator Function & Side-Effect-Free Imports**:
     - Implement CAD logic as a standalone generator function `create_<model>(params: <Model>Params) -> Part | Compound | Solid`.
     - It must accept the dataclass instance and return the generated geometry without side effects (no exports, file writes, or viewer calls inside the generator). This ensures it can be imported and plugged directly into an external GUI/web viewer worker.
     - **Never import `ocp_viewer` / `ocp_vscode` or call `set_defaults()` at module top-level** (nor construct geometry at import time). Keep viewer imports strictly inside `if __name__ == "__main__":` (or a lazy helper invoked only from `__main__`) so external preview/generator workers can import `<Model>Params` and `create_<model>` cleanly without viewer side effects.
   - **Standardized Export Variables**:
     Every model script must standardize on these exact top-level variable names to control standalone exports, and they **must always be set to `False` by default**:
     ```python
     EXPORT_STL: bool = False      # Save .stl to repo-root exports/ (default: False)
     EXPORT_STEP: bool = False     # Save .step to repo-root exports/ (default: False)
     ```
   - **Exports Location Standard (Gitignored Root `exports/`)**:
     Standalone script exports write to the gitignored repository-root `exports/` directory via `utils/runner.py` (`run_model(...)` / `get_exports_dir()`). Never commit generated `.stl`, `.step`, `.stp`, or `.3mf` artifacts to source control—save reusable parameter configurations in `models/<model_name>/presets.json` instead.
   - **Standardized Export Filename Convention & Hook**:
     Export filenames must follow the pattern:
     `<model_name>_<primary_dimensions>_<variant_or_style>.<ext>`
     in lowercase `snake_case` (e.g. `rack_bracket_2u_hex.stl`, `shaft_end_cap_12.7mm_round.stl`, `magnetic_label_100x16mm_fasteners_embossed_base.stl`, `container_lid_150mm_round_tpu.stl`, `spacer_100x100x3mm_corner.stl`).
     Models may define `def export_filename(params: <Model>Params) -> str:` returning this lowercase `snake_case` stem (without extension), reused by both `__main__` exports and Studio Save-As dialogs.
     This ensures immediate identification across slicers, file managers, and future web generator download endpoints.
   - **Strict Standalone Architecture (No Compatibility Shims or Legacy Wrappers)**:
     - Every model script must live in its canonical file: `models/<model_name>/<model_name>.py`.
     - Shared non-geometry utility scripts live in `utils/` (e.g. `utils/params.py`, `utils/runner.py`), separate from `components/` (reusable 3D geometry).
     - **Never create backwards-compatibility shims, wrapper scripts, redirect files, or deprecated alias modules** (e.g. do not create `old_name.py` alongside `new_name.py`). When refactoring, renaming, or migrating, rename cleanly and delete obsolete files.
     - **Never retain legacy parameter aliases, duplicate getters, or forwarding shims in `@dataclass` definitions** (e.g. do not keep deprecated `x`, `y`, `z` fields or `__post_init__` alias mappings). Remove dead fields directly.
     - Scripts must remain concise and zero-dependency beyond `build123d`, `ocp_viewer`/`ocp_vscode`, and stdlib-only helpers in `utils/`.
   - **Clean `__main__` Block Without Parameter Overrides**:
     In the `if __name__ == "__main__":` block:
     - Import `run_model` from `utils.runner` (kept inside `__main__` so module imports stay side-effect-free).
     - Instantiate `params = <Model>Params()` with **no hardcoded arguments** so that editing the dataclass defaults at the top of the file immediately takes effect.
     - Call the generator function: `part = create_<model>(params)`.
     - Delegate export (to repo-root `exports/`) and `ocp_viewer` / `ocp_vscode` preview to `run_model(...)`:
       ```python
       if __name__ == "__main__":
           from utils.runner import run_model

           params = <Model>Params()
           part = create_<model>(params)
           run_model(part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
       ```
4. **Model Validation**: Validate models by running python scripts with `ocp_viewer` / `ocp_vscode` `show()` or checking export operations.
5. **Clean Workspace Rule**: Do NOT create temporary test or validation scripts in the root project directory. Store reusable test/utility scripts inside `.agents/scripts/` or delete temporary scratch scripts immediately after validation completes.
6. **Git & Commit Protocol**:
   - Local commits do not require prior approval once validation passes. Never push changes to a remote without presenting a summary and receiving explicit user approval (invoking `/ship` counts as approval).
   - **Per-Model Commit Isolation**: Always keep commits for each model separate (scoping model changes to their respective `models/<model_name>/` directory and related index entry, and keeping repo-level config/rule changes in separate commits) so the git history for any specific model directory remains clean and easy to inspect.
