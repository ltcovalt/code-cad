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

Each generator is structured in its own directory with its source script, optional `presets.json`, and dedicated documentation. Standalone script exports write to the gitignored root `exports/` directory:

```
cad/
├── .gitignore
├── README.md                   # Repository overview (this file)
├── exports/                    # Gitignored output directory for local STL/STEP/3MF exports
├── components/                 # Reusable parametric 3D geometry components
│   ├── gridfinity_base/        # 42 mm Gridfinity base feet with optional magnet pockets
│   └── pull_tab/               # Flared lid pull tab with gusset, grip ribs, and hanging hole
├── utils/                      # Core zero-dependency helpers (params.py, runner.py)
├── models/                     # 3D printable model scripts
│   ├── c_clip/                 # Snap-on retaining clips and spacers for rods and shafts
│   ├── can_lid/                # Snap-on storage lids for beverage and food cans
│   ├── container_lid/          # Snap-fit lids for round and rectangular food containers (WIP)
│   ├── gridfinity_bin/         # Stackable Gridfinity bins with label holder, scoops, and dividers
│   ├── magnetic_label/         # Custom text labels with press-fit magnet pockets
│   ├── rack_bracket/           # 19" EIA-310 rackmount brackets (1U, 2U+)
│   ├── rc_battery_caddy/       # Storage rack and pit caddy for RC LiPo hardcase batteries
│   ├── shaft_end_cap/          # Press-fit end caps for cylindrical rods and shelving shafts
│   └── spacer/                 # Straight, L-corner, T-shape, and cross spacers
└── .agents/                    # Agent skills, references, and validation scripts
```

---

## Available Models

| Model | Description | Output Formats |
| :--- | :--- | :--- |
| **[C-Clip](models/c_clip/)** | Snap-on retaining clip and spacer for cylindrical rods and shafts with configurable thickness, inside/outside diameters, removal cutout, and optional outer finger-pull reinforcement. | STL, STEP |
| **[Can Lid](models/can_lid/)** | Snap-on storage lid for rolled-rim beverage and food/soup cans with under-rim retention bead, configurable pull tab, optional inner splash ring, and rigid-plastic flexure slots. | STL, STEP |
| **[Container Lid](models/container_lid/)** | Snap-fit lid for round and rectangular food containers with sealing bead, stacking rim, and pull tab, plus Pyrex and Anchor Hocking presets (WIP). | STL, STEP |
| **[Gridfinity Bin](models/gridfinity_bin/)** | Stackable Gridfinity storage bin with Pred-compatible printable label holder, finger scoops, dividers, and drawer spacer gap overhangs. | STL, STEP |
| **[Magnetic Label](models/magnetic_label/)** | Custom text label with auto-sizing to text, embossed/debossed/flush inlay styles, and press-fit round magnet pockets. | STL, STEP (Single & Multi-body) |
| **[Rackmount Brackets](models/rack_bracket/)** | 19-inch rackmount L-brackets (1U, 2U, custom lengths) with EIA-310 mounting slots, M4 thread-in holes, and honeycomb cutouts. | STL, STEP |
| **[RC LiPo Battery Caddy](models/rc_battery_caddy/)** | Storage rack and pit caddy for RC LiPo hardcase batteries (2S shorty, LCG, ULCG, stick, and custom packs) with flat or Gridfinity base, grid/pinwheel/auto-pack layouts, grip cutouts, and test-fit mode. | STL, STEP |
| **[Shaft End Cap](models/shaft_end_cap/)** | Press-fit end caps for cylindrical rods and shelving shafts with dome/flat/chamfer styles, internal lead-in chamfer, and optional grip flutes. | STL, STEP |
| **[Spacer](models/spacer/)** | Straight, L-corner, T-shape, and cross spacers for drawers and enclosures with configurable notches, pockets, pass-through cutouts, and rounded/chamfered edges. | STL, STEP |

---

## Workflow & Tips

- **Interactive Viewer**: Scripts call `show()` using `ocp_viewer` (with fallback to `ocp_vscode`). Run `python -m ocp_viewer` (or open the VS Code panel) before executing scripts.
- **Batch Generation**: Generators like `magnetic_label.py` support batch processing via a simple list of text strings or calling `batch_generate(...)` directly.
- **Multi-Material Slicing**: For multi-color flush inlays, multi-body `.step` files can be imported directly into Bambu Studio, OrcaSlicer, or PrusaSlicer as a unified multi-part object with 1-click filament slot assignment.
