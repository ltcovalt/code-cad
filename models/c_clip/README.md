# Parametric C-Clip

Parametric `build123d` snap-on C-clip for cylindrical rods and shafts—usable as a retaining clip (e.g., filament spool keeper, shaft collar) or axial spacer without requiring disassembly. Includes a smooth inside-edge cutout bordering the shaft for easy gripping and removal, with optional outer wall reinforcement for large finger-pull loops.

---

## Features

- **Parametric Clip Thickness**: Configure exact axial thickness (`core.thickness`, Z height) along the rod.
- **Parametric Shaft & Outer Diameters**: Independently specify `core.inside_diameter` (nominal rod/shaft size), `core.fit_clearance` (default `0.2 mm` diametral clearance for 3D printing), and `core.outside_diameter`.
- **Snap-On C-Opening**: Configurable `jaw.opening_angle` (`< 180°` so the clip wraps around and retains itself on the shaft), `jaw.jaw_flare_angle` (controls how straight/closed the outer jaw edges are relative to the inner rim), `jaw.jaw_curve_depth` (gently bows each jaw face inward into a smooth C-curve between the outer and inner points), and independent `jaw.inner_tip_fillet` / `jaw.outer_tip_fillet` jaw radii.
- **Inside-Edge Removal Cutout**: Smooth elliptical cutout bordering the shaft (defaulting to the spine opposite the C-opening at `180°`) with filleted entry corners to reduce bending stress risers while creating a pocket for a fingernail, finger, or small tool to grab and remove the clip. Optionally enable `removal_notch.reinforce_outer` to smoothly expand the outer profile into a G1-tangent reinforced lobe behind large cutouts—preserving spine strength even when `depth` exceeds the ring wall thickness.
- **Subtle Edge Chamfer**: Optional small bevel on the top and bottom perimeter edges to prevent print-bed elephant's foot and sharp edges.

---

## Parameter Reference (`CClipParams`)

| Parameter | Type | Default | Description |
|:---|:---:|:---:|:---|
| `core.thickness` | `float` | `12.0` | Axial thickness along the shaft in mm (Z height) |
| `core.inside_diameter` | `float` | `44.0` | Nominal diameter of the rod/shaft to fit in mm |
| `core.outside_diameter` | `float` | `76.0` | Outer diameter of the clip ring in mm |
| `core.fit_clearance` | `float` | `0.2` | Diametral bore clearance in mm (bore = `inside_diameter + fit_clearance`) |
| `jaw.opening_angle` | `float` | `95.0` | Angular width of inner C-opening in degrees (`< 180` for shaft retention) |
| `jaw.jaw_flare_angle` | `float` | `8.0` | Jaw cut angle from `+X` in degrees (`0` = straight parallel slot, smaller = more closed outer rim) |
| `jaw.jaw_curve_depth` | `float` | `1.2` | Concave C-curve bow depth along each jaw face in mm (`0.0` for straight jaw) |
| `jaw.inner_tip_fillet` | `float` | `4.0` | Rounding radius transitioning jaw edge into inner bore in mm (`0.0` for crisp corner) |
| `jaw.outer_tip_fillet` | `float` | `2.4` | Rounding radius curving outer jaw point toward inner point in mm (`0.0` for crisp tip) |
| `removal_notch.enabled` | `bool` | `True` | Master toggle: inside-edge grab/remove cutout bordering the shaft |
| `removal_notch.width` | `float` | `32.0` | Tangential width of the inside-edge cutout in mm |
| `removal_notch.depth` | `float` | `8.0` | Radial depth of cutout extending outward from inner bore in mm |
| `removal_notch.angle` | `float` | `180.0` | Angular position of cutout in degrees (`180` = spine opposite C-opening) |
| `removal_notch.fillet` | `float` | `0.6` | Transition fillet where cutout meets inner bore in mm (`0.0` for crisp edge) |
| `removal_notch.reinforce_outer` | `bool` | `False` | Smoothly expand outer profile behind cutout into a G1-tangent reinforced lobe |
| `removal_notch.spine_wall` | `Optional[float]` | `None` | Minimum outer wall thickness behind cutout in mm (`None` = match ring wall thickness) |
| `edge_chamfer.enabled` | `bool` | `True` | Master toggle: subtle top and bottom perimeter edge bevel |
| `edge_chamfer.size` | `float` | `0.3` | Chamfer size on top and bottom edges in mm |

---

## Usage

Configure parameters in `CClipParams` at the top of `c_clip.py` and run:

```bash
python3 c_clip.py
```

### Export Configuration

Toggle export flags at the top of `c_clip.py` to generate STEP and STL files into the gitignored repo-root `exports/` folder:

```python
EXPORT_STL: bool = False      # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False     # Save .step to repo-root exports/ (default: False)
```

### Python API Example

```python
from c_clip import CClipParams, CoreParams, RemovalNotchParams, create_c_clip

# Compact spool-holder retaining clip with reinforced finger-pull loop
params = CClipParams(
    core=CoreParams(thickness=10.0, inside_diameter=25.0, outside_diameter=37.0),
    removal_notch=RemovalNotchParams(
        width=19.0,
        depth=14.0,
        reinforce_outer=True,
    ),
)

clip = create_c_clip(params)
```
