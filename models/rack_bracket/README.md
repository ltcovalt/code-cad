# Parametric 19-Inch Rackmount L-Brackets

Parametric 19-inch EIA-310 rackmount L-bracket model built with `build123d`.

---

## Features

- **Arbitrary Rack Units**: Fully parametric height supporting 1U, 2U, 3U, 4U, and arbitrary U heights with standard 1.2mm total stacking clearance (defaults to **2U Hex Bracket**).
- **Standard EIA-310 Compliance**: Automatically places dual EIA-310 mounting slots at top and bottom edges (including 1U, spaced 31.75mm / 1.25in center-to-center) plus intermediate rack unit centers on 3U+.
- **Customizable Length & Reinforcements**: Side plate length, wall thickness, and bend/corner fillets can be customized.
- **Side Pilot Holes**: Repeating horizontal arrays of M4 thread-in pilot holes (3.3mm diameter for direct tapping into 3D prints) — centered vertically on 1U brackets and positioned within solid top/bottom margins on 2U+, with a master toggle (`side_holes.enabled`).
- **Ventilation Styles**: Selectable center cutout styles:
  - `'hex'`: Honeycomb mesh grill for airflow (default on 2U+).
  - `'window'`: Clean rectangular opening.
  - `'none'`: Solid plate for maximum rigidity (used by the **1U Solid Bracket** preset).

---

## Presets

- **2U Hex Bracket** *(default)*: 2U 19-inch rackmount L-bracket with honeycomb ventilation, dual side M4 hole rows, and dual EIA-310 front slots.
- **1U Solid Bracket** (`presets.json` → `1u_solid`): 1U 19-inch rackmount L-bracket with solid side plate, centered M4 side holes, and dual EIA-310 front slots.

---

## Parameter Reference (`RackBracketParams`)

| Group / Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `core.u_count` | `int` | `2` | Number of Rack Units (`1` for 1U, `2` for 2U, `3` for 3U, etc.) |
| `core.u_height_unit` | `float` | `44.45` | Nominal 1U rack height in mm ($1.75\text{ in}$) |
| `core.height_margin` | `float` | `1.2` | Subtracted height margin in mm for stacking clearance |
| `core.bracket_length` | `float` | `150.0` | Side plate depth/length in mm |
| `core.front_flange_width` | `float` | `20.0` | Front mounting ear width in mm |
| `core.thickness` | `float` | `3.0` | Bracket wall thickness in mm |
| `core.inner_bend_radius` | `float` | `1.5` | Inside L-corner fillet radius in mm |
| `core.outer_corner_radius` | `float` | `1.5` | Outer vertical corner fillet radius in mm |
| `side_holes.enabled` | `bool` | `True` | Master toggle to enable/disable side M4 pilot hole arrays |
| `side_holes.diameter` | `float` | `3.3` | M4 thread-in pilot hole diameter in mm |
| `side_holes.spacing_x` | `float` | `25.0` | Horizontal spacing between side hole columns in mm |
| `cutout.style` | `str` | `"hex"` | Center cutout style: `"hex"`, `"window"`, or `"none"` |
| `cutout.hex_radius` | `float` | `4.5` | Circumradius of honeycomb hex cutouts in mm |
| `cutout.hex_wall_thickness` | `float` | `1.5` | Wall thickness between adjacent hex cells in mm |
| `rack_slots.single_slot_1u` | `bool` | `False` | For 1U brackets: `False` for 2 EIA-310 end slots, `True` for 1 centered slot |

---

## Usage

Configure the parameters in `RackBracketParams` and run the script:

```bash
python3 rack_bracket.py
```

Generated `.step` and `.stl` files are saved to the gitignored repo-root `exports/` folder.

### Export Settings

At the top of `rack_bracket.py`, you can toggle exports using standard repo settings:

```python
EXPORT_STL: bool = False                # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False               # Save .step to repo-root exports/ (default: False)
```

### Python / Scripting API

```python
from rack_bracket import CoreParams, CutoutParams, RackBracketParams, create_rack_bracket

params = RackBracketParams(
    core=CoreParams(u_count=3, bracket_length=150.0),
    cutout=CutoutParams(style="hex"),
)

bracket = create_rack_bracket(params)
```
