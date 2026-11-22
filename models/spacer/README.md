# Parametric Spacer Generator

Parametric spacer generator built with `build123d`. Generates straight bars, L-corners, mirrored L-corners, T-shapes, and cross (`+`) spacers for filling gaps in drawers, enclosures, trays, and shelving—complete with configurable notches, pockets, and pass-through cutouts.

---

## Features

- **Intuitive Dimension-Driven Generation**:
  - Setting both `leg_x_length > 0` and `leg_y_length > 0` generates an **L-corner**, **T-shape**, or **Cross (`+`)** piece depending on `leg_x_align` / `leg_y_align` and offsets.
  - Setting `leg_y_length = 0` automatically generates a **straight Leg X spacer** (`leg_x_length` × `leg_x_width`).
  - Setting `leg_x_length = 0` automatically generates a **straight Leg Y spacer** (`leg_y_length` × `leg_y_width`).
- **Independent Leg Widths, Lengths & Mirroring**:
  - Set each leg's length, width, and junction alignment/offset independently.
  - Flip `mirror_x` or `mirror_y` to mirror asymmetric L-shapes (and their cutouts) for opposite corners.
  - Single shared height across both legs.
- **Corner & Edge Radius Control**:
  - `corner_radius`: Smooth vertical corners in the XY plane.
  - `outer_corner_radius` / `inner_corner_radius` / `end_corner_radius`: Independent control over outer junction corners, inside junction corners, and arm end faces.
  - `edge_radius` & `edge_treatment`: Selectable `'fillet'` (rounded) or `'chamfer'` (45° bevel) along the top perimeter.
- **Notches, Pockets & Pass-Through Cutouts (`cutouts_enabled=True`)**:
  - Add any number of `SpacerCutout` entries along either leg using `align`/`offset` and `v_align`/`v_offset`.
  - Supports `"rectangle"`, `"circle"`, and `"chamfer"` profiles, optional `entry_radius` (`"fillet"` or `"chamfer"`) where edge cutouts meet the top/bottom border, full through-cuts or partial-depth pockets, and closed interior windows/bolt holes.
- **Hollow / Shell Mode** (`hollow=True`):
  - Hollows out the underside with customizable `wall_thickness` and `top_thickness`.
- **Finger-Lift Scoop** (`finger_notch=True`):
  - Optional top recess scoop for easy removal from tight spaces.

---

## Spacer Geometry

### Junction Piece (Both `leg_x_length > 0` and `leg_y_length > 0`)
```text
  Y (Side Wall)
   ^
Ly |   +------------+
   |   |            |  Leg Y
   |   |            |  Width: leg_y_width (in X)
   |   |            |  Length: leg_y_length (in Y)
   |   |            |
Wx |   |     (0,0)  +------------------------+
   |   |     Outer            Inner Corner   |  Leg X
   |   |    Corner            (inner_radius) |  Width: leg_x_width (in Y)
 0 +---+-------------------------------------+---> X (Front Wall)
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

Configure the parameters in `SpacerParams` at the top of [`spacer.py`](file:///c:/Users/luke/Repos/code-cad/models/spacer/spacer.py) and execute the script:

```bash
python spacer.py
```

When enabled, `.stl` and `.step` files are saved to the gitignored repo-root `exports/` folder.

### Export Configuration

At the top of `spacer.py`, exports can be toggled using standard configuration variables:

```python
EXPORT_STL: bool = False     # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False    # Save .step to repo-root exports/ (default: False)
```

---

## Python / Scripting API

```python
from models.spacer.spacer import SpacerCutout, SpacerParams, create_spacer

# 1. Corner Piece with Lock Clearance Notch
corner_params = SpacerParams(
    leg_x_length=180.0,
    leg_x_width=15.0,
    leg_y_length=280.0,
    leg_y_width=15.0,
    height=56.0,
    mirror_x=True,
    cutouts_enabled=True,
    cutouts=[
        SpacerCutout(
            leg="x",
            align="end",
            offset=15.0,
            length=50.0,
            height=16.0,
            shape="rectangle",
            radius=3.0,
            entry_radius=3.0,
        ),
    ],
)
corner_spacer = create_spacer(corner_params)

# 2. Centered T-Shape Spacer
t_params = SpacerParams(
    leg_x_length=180.0,
    leg_x_width=15.0,
    leg_y_length=120.0,
    leg_y_width=15.0,
    leg_y_align="center",
    height=40.0,
)
t_spacer = create_spacer(t_params)

# 3. Straight Spacer (Setting leg_y_length = 0)
straight_params = SpacerParams(
    leg_x_length=150.0,
    leg_x_width=15.5,
    leg_y_length=0.0,
    height=12.0,
)
straight_spacer = create_spacer(straight_params)
```

---

## Parameter Reference (`SpacerParams`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `height` | `float` | `56.0` | Shared spacer height (mm) |
| `leg_x_length` | `float` | `180.0` | Length of Leg X (mm). Set `0` to omit Leg X |
| `leg_x_width` | `float` | `15.0` | Width / thickness of Leg X (mm) |
| `leg_y_length` | `float` | `280.0` | Length of Leg Y (mm). Set `0` to omit Leg Y |
| `leg_y_width` | `float` | `15.0` | Width / thickness of Leg Y (mm) |
| `mirror_x` | `bool` | `True` | Mirror left $\leftrightarrow$ right (inverts L-shape for opposite corner) |
| `mirror_y` | `bool` | `False` | Mirror front $\leftrightarrow$ back |
| `leg_y_align` | `str` | `"start"` | Anchor for Leg Y along X: `"start"` (L-corner), `"center"` (T-shape), or `"end"` |
| `leg_y_offset` | `float` | `0.0` | Fine-tune shift of Leg Y from `leg_y_align` (mm, `+` or `-`) |
| `leg_x_align` | `str` | `"start"` | Anchor for Leg X along Y: `"start"` (L-corner), `"center"` (sideways T), or `"end"` |
| `leg_x_offset` | `float` | `0.0` | Fine-tune shift of Leg X from `leg_x_align` (mm, `+` or `-`) |
| `corner_radius` | `float` | `2.0` | General vertical corner radius (mm) |
| `outer_corner_radius` | `Optional[float]` | `None` | Radius of outer junction corner (mm, `None` = `corner_radius`) |
| `inner_corner_radius` | `Optional[float]` | `4.0` | Radius of inside junction corners (mm, `None` = `corner_radius`) |
| `end_corner_radius` | `float` | `0.0` | Radius on mating arm ends (mm, `0.0` for flush butt joint) |
| `edge_radius` | `float` | `1.0` | Top perimeter edge radius/bevel (mm) |
| `edge_treatment` | `str` | `"fillet"` | Top edge treatment: `"fillet"` or `"chamfer"` |
| `hollow` | `bool` | `False` | Hollow underside mode to save filament and print time |
| `wall_thickness` | `float` | `2.0` | Side wall thickness when `hollow=True` (mm) |
| `top_thickness` | `float` | `2.0` | Top roof thickness when `hollow=True` (mm) |
| `finger_notch` | `bool` | `False` | Recessed spherical scoop on top for easy finger removal |
| `finger_notch_radius` | `float` | `12.0` | Radius of the finger notch scoop cutter (mm) |
| `finger_notch_depth` | `float` | `2.5` | Depth of the finger scoop from top face (mm) |
| `cutouts_enabled` | `bool` | `True` | Master toggle to enable/disable all `SpacerCutout` entries |
| `cutouts` | `List[SpacerCutout]` | `[SpacerCutout(...)]` | List of notch, pocket, or pass-through cutouts along either leg |

### Cutout Parameters (`SpacerCutout`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `leg` | `str` | `"x"` | Which leg to cut: `"x"` or `"y"` |
| `align` | `str` | `"start"` | Horizontal anchor along leg: `"start"` (corner), `"center"`, or `"end"` (far end) |
| `offset` | `float` | `0.0` | Distance inward from `"start"`/`"end"`, or `+/-` shift from `"center"` (mm) |
| `v_align` | `str` | `"top"` | Vertical anchor: `"top"`, `"center"`, or `"bottom"` |
| `v_offset` | `float` | `0.0` | Distance inward from `"top"`/`"bottom"` (`0` = edge notch; `> 0` = closed hole/window), or `+/-` shift from `"center"` (mm) |
| `length` | `float` | `50.0` | Length of the cutout along the leg (mm) |
| `height` | `float` | `20.0` | Vertical height of the cutout (mm) |
| `shape` | `str` | `"rectangle"` | `"rectangle"` (`"square"`), `"circle"` (`"arc"`), or `"chamfer"` (`"trapezoid"`) |
| `radius` | `float` | `0.0` | Inside corner fillet for `"rectangle"`, circle radius for `"circle"` (`0` = auto), or ramp width for `"chamfer"` (`0` = 45° ramp) |
| `entry_radius` | `float` | `0.0` | Rounds/bevels the 90° outer corners where an edge cutout meets the top or bottom border (mm) |
| `entry_treatment` | `str` | `"fillet"` | Treatment for `entry_radius`: `"fillet"` (smooth curve) or `"chamfer"` (45° bevel) |
| `depth` | `Optional[float]` | `None` | Cut depth through spacer thickness (mm). `None` = full through-cut |
| `side` | `str` | `"outer"` | Face to cut from when `depth` is set: `"outer"` (wall side) or `"inner"` (bin side) |
