# Parametric 19-Inch Rackmount L-Brackets

Parametric 19-inch EIA-310 rackmount L-bracket model built with `build123d`.

---

## Features

- **Arbitrary Rack Units**: Fully parametric height supporting 1U, 2U, 3U, 4U, and arbitrary U heights with standard 1.2mm total stacking clearance.
- **Standard EIA-310 Compliance**: Automatically places standard EIA-310 mounting slots at top/bottom edges and intermediate rack unit centers.
- **Customizable Length & Reinforcements**: Side plate length, wall thickness, and bend/corner fillets can be customized.
- **Side Pilot Holes**: Repeating horizontal arrays of M4 thread-in pilot holes (3.3mm diameter for direct tapping into 3D prints) positioned securely within the solid edge margins, with a master toggle (`side_holes_enabled = True / False`).
- **Ventilation Styles**: Selectable center cutout styles:
  - `'hex'`: Honeycomb mesh grill for airflow.
  - `'window'`: Clean rectangular opening.
  - `'none'`: Solid plate for maximum rigidity.

---

## Parameter Reference (`RackBracketParams`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `u_count` | `int` | `1` | Number of Rack Units (`1` for 1U, `2` for 2U, `3` for 3U, etc.) |
| `u_height_unit` | `float` | `44.45` | Nominal 1U rack height in mm ($1.75\text{ in}$) |
| `height_margin` | `float` | `1.2` | Subtracted height margin in mm for stacking clearance |
| `bracket_length` | `float` | `150.0` | Side plate depth/length in mm |
| `front_flange_width`| `float`| `20.0` | Front mounting ear width in mm |
| `thickness` | `float` | `3.0` | Bracket wall thickness in mm |
| `inner_bend_radius` | `float` | `1.5` | Inside L-corner fillet radius in mm |
| `outer_corner_radius`| `float`| `1.5` | Outer vertical corner fillet radius in mm |
| `side_holes_enabled`| `bool` | `True` | Master toggle to enable/disable side M4 pilot hole arrays |
| `side_hole_dia` | `float` | `3.3` | M4 thread-in pilot hole diameter in mm |
| `side_hole_spacing_x`| `float`| `25.0` | Horizontal spacing between side hole columns in mm |
| `cutout_style` | `str` | `"hex"` | Center cutout style: `"hex"`, `"window"`, or `"none"` |
| `hex_radius` | `float` | `4.5` | Circumradius of honeycomb hex cutouts in mm |
| `hex_wall_thickness`| `float` | `1.5` | Wall thickness between adjacent hex cells in mm |
| `single_slot_1u` | `bool` | `True` | For 1U brackets: `True` for 1 centered slot, `False` for 2 end slots |

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
