# Parametric CAD Models (build123d)

A collection of parametric, code-driven 3D CAD models and generators built with [build123d](https://github.com/gumyr/build123d) and Python. Designed primarily for 3D printing, functional workshop organization, and rack hardware.

---

## Prerequisites

1. **Python 3.10+** (with virtual environment recommended)
2. **CAD Libraries**:
   ```bash
   pip install build123d ocp-vscode
   ```
3. **VS Code Viewer Extension**:
   Install the **OCP CAD Viewer** extension (`bierpatese.ocp-cad-viewer` or `OCP CAD Viewer`) in VS Code to see live 3D interactive previews when running any script.

---

## Repository Structure

Each generator is structured in its own self-contained directory with its source script, dedicated documentation, and 3D export files (`.stl` / `.step`):

```
cad/
├── .gitignore
├── README.md                   # Repository overview (this file)
├── docs/                       # Manuals and general reference PDFs
├── models/                     # Parametric generator projects
│   ├── magnetic_label/         # Parametric magnetic label generator
│   │   ├── magnetic_label.py   # Generator script (single or batch)
│   │   ├── README.md           # Instructions, parameter options, slicer tips
│   │   └── exports/            # Generated STL / STEP files
│   └── rack_bracket/           # 19" EIA-310 rackmount brackets (1U, 2U+)
│       ├── rack_bracket.py     # Parametric rack bracket generator
│       ├── rack_bracket_2u.py  # 2U specialized bracket
│       └── README.md
└── .agents/                    # Agent skills, references, and validation scripts
```

---

## Available Models

| Model | Description | Output Formats |
| :--- | :--- | :--- |
| **[Magnetic Label](models/magnetic_label/)** | Parametric magnetic label generator with auto-sizing to text, embossed/debossed/flush inlay styles, and press-fit round magnet pockets. | STL, STEP (Single & Multi-body) |
| **[Rackmount Brackets](models/rack_bracket/)** | Parametric 19-inch rackmount L-brackets (1U, 2U, custom lengths) with EIA-310 mounting slots, M4 thread-in holes, and honeycomb cutouts. | STL, STEP |

---

## Workflow & Tips

- **Interactive Viewer**: Scripts use `ocp_vscode.show()` to render models. Ensure the OCP CAD Viewer panel is open in VS Code before executing scripts.
- **Batch Generation**: Generators like `magnetic_label.py` support batch processing via a simple list of text strings or calling `batch_generate(...)` directly.
- **Multi-Material Slicing**: For multi-color flush inlays, multi-body `.step` files can be imported directly into Bambu Studio, OrcaSlicer, or PrusaSlicer as a unified multi-part object with 1-click filament slot assignment.
