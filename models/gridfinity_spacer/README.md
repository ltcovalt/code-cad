# Parametric Gridfinity Drawer Gap Spacer

Parametric drawer gap spacer generator built with `build123d`. Designed to drop along the edges and corners of drawers on top of Gridfinity baseplate padding, keeping bins from shifting and preventing small parts, screws, or bits from falling into perimeter crevices.

---

## Features

- **Intuitive Dimension-Driven Generation**:
  - Setting both `leg_x_length > 0` and `leg_y_length > 0` generates an **L-shaped corner piece**.
  - Setting `leg_y_length = 0` automatically generates a **straight front/back spacer** (`leg_x_length` by `leg_x_width`).
  - Setting `leg_x_length = 0` automatically generates a **straight side spacer** (`leg_y_length` by `leg_y_width`).
  - No mode switches or dropdowns needed.
- **Independent Leg Widths & Lengths**:
  - Set each leg's length and width independently (e.g. front spacer width of **15.5 mm** vs side spacer width of **15.0 mm**, with different lengths).
  - Single shared height across both legs.
- **Corner & Edge Radius Control**:
  - `corner_radius`: Smooth vertical corners to fit against rounded drawer interiors.
  - `edge_radius`: Beveled or filleted top perimeter edges for smooth touch and effortless sliding of bins/hands.
  - `edge_treatment`: Selectable `'fillet'` (rounded) or `'chamfer'` (45° bevel).
  - `inner_corner_radius`: Pre-configured to `4.0 mm` by default to match standard Gridfinity bin outer corner profiles.
  - `end_corner_radius`: Set to `0.0 mm` by default for flush butt-joints against adjacent straight spacers.
- **Hollow / Shell Mode** (`hollow=True`):
  - Hollows out the underside with customizable `wall_thickness` and `top_thickness` to save filament and print time on thick spacers.
- **Finger-Lift Scoop** (`finger_notch=True`):
  - Optional top recess scoop for effortless removal and re-arrangement in tight drawers.

---

## Spacer Geometry

### Corner Piece (Both `leg_x_length > 0` and `leg_y_length > 0`)
```text
  Y (Side Drawer Wall)
   ^
Ly |   +------------+
   |   |            |  Leg Y (Side)
   |   |            |  Width: leg_y_width (in X)
   |   |            |  Length: leg_y_length (in Y)
   |   |            |
Wx |   |     (0,0)  +------------------------+
   |   |     Outer            Inner Corner   |  Leg X (Front)
   |   |    Corner            (R4 Gridfinity)|  Width: leg_x_width (in Y)
 0 +---+-------------------------------------+---> X (Front Drawer Wall)
       0     Wy                               Lx
```

### Straight Piece (`leg_y_length = 0` or `leg_x_length = 0`)
```text
         +---------------------------------------+
         |                                       |
  Width  |            Top Face                   |
         |   (filleted/chamfered perimeter)      |
         |                                       |
         +---------------------------------------+
                           Length
```

---

## Usage

Configure the parameters in `SpacerParams` at the top of [`spacer.py`](file:///models/gridfinity_spacer/spacer.py) and execute the script:

```bash
python spacer.py
```

Generated `.step` and `.stl` files are automatically saved to `models/gridfinity_spacer/exports/`.

### Export Configuration

At the top of [`spacer.py`](file:///models/gridfinity_spacer/spacer.py), exports can be toggled using standard configuration variables:

```python
EXPORT_STEP: bool = False              # Save .step file on execution (default: False)
EXPORT_STL: bool = False               # Save .stl file on execution (default: False)
OUTPUT_DIR: str = "exports"            # Output folder alongside this script
```

---

## Python / Scripting API

```python
from models.gridfinity_spacer.spacer import SpacerParams, create_spacer

# 1. Corner Piece (15.5mm Front gap, 15.0mm Side gap)
corner_params = SpacerParams(
    leg_x_length=100.0,   # Front wall leg length in mm
    leg_x_width=15.5,     # Front wall gap width in mm
    leg_y_length=80.0,    # Side wall leg length in mm
    leg_y_width=15.0,     # Side wall gap width in mm
    height=12.0,          # Shared spacer height in mm
    corner_radius=2.5,    # Drawer corner fillet
    inner_corner_radius=4.0, # Standard Gridfinity bin corner match (R4)
    edge_radius=1.0,      # Top edge fillet
)
corner_spacer = create_spacer(corner_params)

# 2. Straight Front Spacer (Setting leg_y_length = 0)
front_params = SpacerParams(
    leg_x_length=150.0,
    leg_x_width=15.5,
    leg_y_length=0.0,     # Omit Leg Y -> generates straight front spacer
    height=12.0,
)
front_spacer = create_spacer(front_params)

# 3. Straight Side Spacer (Setting leg_x_length = 0)
side_params = SpacerParams(
    leg_x_length=0.0,     # Omit Leg X -> generates straight side spacer
    leg_y_length=120.0,
    leg_y_width=15.0,
    height=12.0,
)
side_spacer = create_spacer(side_params)
```

---

## Parameter Reference

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `height` | `float` | `12.0` | Shared spacer height above baseplate padding (mm) |
| `leg_x_length` | `float` | `100.0` | Length of Leg X along drawer wall (mm). Set `0` to omit Leg X |
| `leg_x_width` | `float` | `15.5` | Width / gap thickness of Leg X (mm) — e.g. front drawer gap |
| `leg_y_length` | `float` | `80.0` | Length of Leg Y along drawer wall (mm). Set `0` to omit Leg Y |
| `leg_y_width` | `float` | `15.0` | Width / gap thickness of Leg Y (mm) — e.g. side drawer gap |
| `corner_radius` | `float` | `2.0` | General vertical corner radius (mm) |
| `outer_corner_radius` | `Optional[float]`| `None` | Radius of outer drawer corner (mm, None = `corner_radius`) |
| `inner_corner_radius` | `Optional[float]`| `4.0` | Radius of inside corner facing Gridfinity bin (mm) |
| `end_corner_radius` | `float` | `0.0` | Radius on mating arm ends (mm, `0.0` for flush butt joint) |
| `edge_radius` | `float` | `1.0` | Top perimeter edge radius/bevel (mm) |
| `edge_treatment` | `str` | `"fillet"` | Top edge treatment: `"fillet"` or `"chamfer"` |
| `hollow` | `bool` | `False` | Hollow underside mode to save filament and print time |
| `wall_thickness` | `float` | `2.0` | Side wall thickness when `hollow=True` (mm) |
| `top_thickness` | `float` | `2.0` | Top roof thickness when `hollow=True` (mm) |
| `finger_notch` | `bool` | `False` | Recessed spherical scoop on top for easy finger removal |
| `finger_notch_radius` | `float` | `12.0` | Radius of the finger notch scoop cutter (mm) |
| `finger_notch_depth` | `float` | `2.5` | Depth of the finger scoop from top face (mm) |
