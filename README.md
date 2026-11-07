# Parametric CAD Models (build123d)

A collection of parametric, code-driven 3D CAD models and generators built with [build123d](https://github.com/gumyr/build123d) and Python. Designed primarily for 3D printing, functional workshop organization, and rack hardware.

---

## Prerequisites

1. **Python 3.10+** (with virtual environment recommended)
2. **CAD Libraries & Viewer**:
   - **Standalone / Neovim / Browser (Recommended)**:
     ```bash
     pip install build123d ocp_viewer
     ```
   - **VS Code Extension**:
     ```bash
     pip install build123d ocp-vscode
     ```
     Install the **OCP CAD Viewer** extension (`bierpatese.ocp-cad-viewer` or `OCP CAD Viewer`) in VS Code.

---

## 3D Interactive Viewer Setup

All model scripts include universal viewer bindings that automatically support both standalone `ocp_viewer` and VS Code `ocp-vscode`:

- **Standalone Mode (Neovim / Terminal / Browser)**:
  1. Start the standalone viewer server in a terminal or tmux split:
     ```bash
     python -m ocp_viewer
     # (or python -m ocp_vscode if using ocp-vscode)
     ```
  2. Open **`http://127.0.0.1:3939`** in your browser.
  3. Execute any script (e.g. from Neovim via `:!python %` or terminal `python model.py`). The 3D model immediately streams to your browser tab.

- **VS Code Mode**:
  Open the **OCP CAD Viewer** panel in VS Code before executing scripts.

---

## Repository Structure

Each generator is structured in its own self-contained directory with its source script, dedicated documentation, and 3D export files (`.stl` / `.step`):

```
cad/
├── .gitignore
├── README.md                   # Repository overview (this file)
├── docs/                       # Manuals and general reference PDFs
├── models/                     # Parametric generator projects
│   ├── container_lid/          # Container lid generator (Pyrex, etc.)
│   ├── gridfinity_spacer/      # Custom Gridfinity drawer fitment spacers
│   ├── magnetic_label/         # Magnetic label generator
│   ├── rack_bracket/           # 19" EIA-310 rackmount brackets (1U, 2U+)
│   └── shaft_end_cap/          # Retention end caps for cylindrical shelving rods
└── .agents/                    # Agent skills, references, and validation scripts
```

---

## Available Models

| Model | Description | Output Formats |
| :--- | :--- | :--- |
| **[Container Lid](models/container_lid/)** | Airtight container lid generator with sealing bead, stacking rim, and pull tab. Built-in presets for Pyrex rectangular and round glass dishes. | STL, STEP |
| **[Gridfinity Spacer](models/gridfinity_spacer/)** | Precision drawer spacer to eliminate play around Gridfinity baseplates. Supports front/back/side positions, finger scoops, and hollow underside. | STL, STEP |
| **[Magnetic Label](models/magnetic_label/)** | Magnetic label generator with auto-sizing to text, embossed/debossed/flush inlay styles, and press-fit round magnet pockets. | STL, STEP (Single & Multi-body) |
| **[Rackmount Brackets](models/rack_bracket/)** | 19-inch rackmount L-brackets (1U, 2U, custom lengths) with EIA-310 mounting slots, M4 thread-in holes, and honeycomb cutouts. | STL, STEP |
| **[Shaft End Cap](models/shaft_end_cap/)** | Press-fit retention end caps for spool storage rods with dome/flat/chamfer styles, internal lead-in chamfer, and optional grip flutes. | STL, STEP |

---

## Workflow & Tips

- **Interactive Viewer**: Scripts call `show()` using `ocp_viewer` (with fallback to `ocp_vscode`). Run `python -m ocp_viewer` (or open the VS Code panel) before executing scripts.
- **Batch Generation**: Generators like `magnetic_label.py` support batch processing via a simple list of text strings or calling `batch_generate(...)` directly.
- **Multi-Material Slicing**: For multi-color flush inlays, multi-body `.step` files can be imported directly into Bambu Studio, OrcaSlicer, or PrusaSlicer as a unified multi-part object with 1-click filament slot assignment.
