# Parametric 19-Inch Rackmount L-Brackets

Parametric 19-inch EIA-310 rackmount L-bracket model built with `build123d`.

---

## Features

- **Arbitrary Rack Units**: Fully parametric height supporting 1U, 2U, 3U, 4U, and arbitrary U heights with standard 1.2mm total stacking clearance.
- **Standard EIA-310 Compliance**: Automatically places standard EIA-310 mounting slots at top/bottom edges and intermediate rack unit centers.
- **Customizable Length & Reinforcements**: Side plate length, wall thickness, and bend/corner fillets can be customized.
- **Side Pilot Holes**: Repeating horizontal arrays of M4 thread-in pilot holes (3.3mm diameter for direct tapping into 3D prints) positioned securely within the solid edge margins.
- **Ventilation Styles**: Selectable center cutout styles:
  - `'hex'`: Honeycomb mesh grill for airflow.
  - `'window'`: Clean rectangular opening.
  - `'none'`: Solid plate for maximum rigidity.

---

## Usage

Simply configure the parameters in `RackBracketParams` (e.g. `u_count=2` for 2U, `u_count=3` for 3U) and run the script:

```bash
python3 rack_bracket.py
```

Generated `.step` and `.stl` files are saved to `models/rack_bracket/exports/`.

### Export Settings

At the top of `rack_bracket.py`, you can toggle exports using standard repo settings:

```python
EXPORT_STL: bool = False                # Save .stl file on execution (default: False)
EXPORT_STEP: bool = False               # Save .step file on execution (default: False)
OUTPUT_DIR: str = "exports"            # Output folder alongside this script
```

### Python / Scripting API

```python
from rack_bracket import RackBracketParams, create_rack_bracket
from build123d import export_step, export_stl

params = RackBracketParams(
    u_count=3,              # 3U height (132.15 mm including 1.2mm stack margin)
    bracket_length=150.0,   # Side plate length in mm
    cutout_style="hex",     # 'hex', 'window', or 'none'
)

bracket = create_rack_bracket(params)
```
