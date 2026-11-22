"""Standalone script runner and export helpers for build123d models.

Provides a shared ``__main__`` entrypoint helper so model scripts stay concise
and side-effect-free on import while still allowing quick standalone execution
and STL/STEP/3MF exports into the gitignored repository-root ``exports/`` folder.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
EXPORTS_DIR: Path = REPO_ROOT / "exports"


def get_exports_dir(output_dir: str | Path | None = None) -> Path:
    """Resolve the output directory for standalone exports.

    Defaults to ``<repo_root>/exports``. Relative paths are resolved relative
    to ``<repo_root>`` so files never scatter across subdirectories.
    """
    if output_dir is None:
        return EXPORTS_DIR
    path = Path(output_dir)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def show_in_viewer(*args: Any, **kwargs: Any) -> None:
    """Display generated geometry in ocp_viewer (or ocp_vscode fallback)."""
    try:
        from ocp_viewer import set_defaults, show

        set_defaults(orbit_control=True)
    except ImportError:
        try:
            from ocp_vscode import set_defaults, show

            set_defaults(orbit_control=True)
        except ImportError:
            return
    show(*args, **kwargs)


def run_model(
    part: Any,
    stem: str,
    *,
    stl: bool = False,
    step: bool = False,
    threemf: bool = False,
    output_dir: str | Path | None = None,
    show_part: bool = True,
) -> list[Path]:
    """Export requested formats to ``<repo_root>/exports/`` and preview in viewer."""
    exported: list[Path] = []

    if stl or step or threemf:
        exports_path = get_exports_dir(output_dir)
        exports_path.mkdir(parents=True, exist_ok=True)

        if stl:
            from build123d import export_stl

            stl_file = exports_path / f"{stem}.stl"
            export_stl(part, str(stl_file))
            exported.append(stl_file)
            print(f"Exported STL:  {stl_file}")

        if step:
            from build123d import export_step

            step_file = exports_path / f"{stem}.step"
            export_step(part, str(step_file))
            exported.append(step_file)
            print(f"Exported STEP: {step_file}")

        if threemf:
            from build123d import Mesher

            threemf_file = exports_path / f"{stem}.3mf"
            mesher = Mesher()
            mesher.add_shape(part)
            mesher.write(str(threemf_file))
            exported.append(threemf_file)
            print(f"Exported 3MF:  {threemf_file}")

    if show_part:
        show_in_viewer(part)

    return exported
