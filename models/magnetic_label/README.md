# Parametric Magnetic Label Generator

A fully parametric 3D printable magnetic label generator built with `build123d`. Designed for toolbox drawers, storage bins, rack panels, and workshop organization.

---

## Features

- **Adaptive Sizing**: Choose between **Auto-Sized** (plate dynamically bounds to text + padding) or fixed **Static Dimensions** (`width` and `height`).
- **Typography Controls**:
  - Font size, font family (e.g. Arial, FreeSans, Helvetica), and styles (`bold`, `regular`, `italic`, `bold_italic`).
  - True geometric vertical centering (`Align.CENTER`) and horizontal alignment (`center`, `left`, `right`).
- **3 Text Rendering Modes**:
  - `embossed`: Raised letters protruding from the front face (ideal for layer-height filament swaps).
  - `debossed`: Recessed letters engraved into the front face.
  - `flush`: Inlay text modeled as mating solid bodies for multi-color AMS 3D printing.
- **Round Press-Fit Magnets**:
  - Parametric diameter and thickness (e.g. 6x2mm, 6x3mm, 8x2mm, 10x2mm).
  - Configurable press-fit tolerance and sub-flush pocket depth allowance.
  - Symmetrical auto-spacing across the plate or manual magnet count/positions.
  - Automatic base thickness check to guarantee minimum solid floor thickness behind magnets.
- **Perimeter Styling**: Rounded corners (`CORNER_RADIUS`), top chamfer bevel (`TOP_EDGE_CHAMFER`), and optional raised border rim (`BORDER_RIM`).
- **Batch Processing**: Supply a Python list of strings to batch-generate and export a whole set of labels in one run.

---

## Quick Start

Open `magnetic_label.py`, adjust the parameters at the top of the file, and run:

```bash
python3 magnetic_label.py
```

If you have the standalone viewer running (`python -m ocp_viewer` at `http://127.0.0.1:3939`) or the **OCP CAD Viewer** extension open in VS Code, an interactive 3D preview with contrasting colors and metallic magnet placement will display automatically.

---

## Batch Generation

In `magnetic_label.py`, add your labels to `BATCH_LABELS`:

```python
BATCH_LABELS = [
    "M3 BOLTS",
    "M4 BOLTS",
    "M5 BOLTS",
    "LOCK NUTS",
    "WASHERS",
    # Per-label overrides are also supported:
    # ("SPECIAL ITEM", {"font_size": 14.0, "text_mode": "flush"}),
]

EXPORT_STL = True
OUTPUT_DIR = "./exports"
```

Running `python3 magnetic_label.py` will generate all labels, export `.stl` files to `./exports/`, and arrange them stacked in the 3D viewer.

Alternatively, import `batch_generate` into your own scripts:

```python
from magnetic_label import MagneticLabelParams, batch_generate

params = MagneticLabelParams(font_size=10.0, magnet_diameter=6.0)
batch_generate(["RESISTORS", "CAPACITORS", "DIODES"], defaults=params, do_export_stl=True)
```

---

## 3D Printing & Slicing Tips

### Method 1: Layer-Height Color Swap (Single Extruder / Zero Waste)
* Set `TEXT_MODE = "embossed"`.
* Optionally enable `BORDER_RIM = True` for a raised framed badge look.
* In your slicer (PrusaSlicer, Bambu Studio, OrcaSlicer), add a **pause** or **color change** at layer height $Z = 3.6\text{ mm}$ (or your configured `base_thickness`).
* The printer switches filament and prints the raised letters and outer rim in the accent color with zero purged waste.

### Method 2: Multi-Color Flush Printing (Bambu AMS / Prusa MMU)
* Set `TEXT_MODE = "flush"` and `EXPORT_STEP = True`.
* The generator exports a single unified `..._multibody_assembly.step` file.
* Drag the `.step` file into Bambu Studio / OrcaSlicer and select **"Load as single object with multiple parts"**.
* Assign Filament 1 to the Base and Filament 2 to the Text Inlay.
* **Pro-tip**: Flip the label 180° so the front face prints **face-down on a textured PEI plate** for a smooth, flush finish with no visible letter layer lines.
