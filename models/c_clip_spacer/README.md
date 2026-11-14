# Parametric C-Clip Spacer

Parametric `build123d` snap-on C-clip spacer designed to add precise axial spacing along cylindrical rods and shafts without requiring shaft disassembly. Includes a smooth inside-edge cutout bordering the shaft for easy gripping and removal.

---

## Features

- **Parametric Spacer Thickness**: Configure exact axial spacing (`thickness`, Z height) added along the rod.
- **Parametric Shaft & Outer Diameters**: Independently specify `inside_diameter` (nominal rod/shaft size), `fit_clearance` (default `0.2 mm` diametral clearance for 3D printing), and `outside_diameter`.
- **Snap-On C-Opening**: Configurable `opening_angle` (`< 180°` so the clip wraps around and retains itself on the shaft) with rounded `tip_fillet` jaw corners for smooth snap-on gliding and comfortable handling.
- **Inside-Edge Removal Cutout**: Smooth elliptical cutout bordering the shaft (defaulting to the spine opposite the C-opening at `180°`) with filleted entry corners to reduce bending stress risers while creating a pocket for a fingernail, pick, or small tool to grab and remove the clip.
- **Subtle Edge Chamfer**: Optional small bevel on the top and bottom perimeter edges to prevent print-bed elephant's foot and sharp edges.

---

## Parameter Reference (`CClipSpacerParams`)

| Parameter | Type | Default | Description |
|:---|:---:|:---:|:---|
| `thickness` | `float` | `5.0` | Axial thickness / space added by the spacer in mm (Z height) |
| `inside_diameter` | `float` | `44.0` | Nominal diameter of the rod/shaft to fit in mm |
| `outside_diameter` | `float` | `72.0` | Outer diameter of the spacer ring in mm |
| `fit_clearance` | `float` | `0.2` | Diametral bore clearance in mm (bore = `inside_diameter + fit_clearance`) |
| `opening_angle` | `float` | `90.0` | Angular width of the C-opening in degrees (`< 180` for shaft retention) |
| `tip_fillet` | `float` | `4.0` | Rounding radius on the C-opening jaw tips in mm (`0.0` for crisp tips) |
| `removal_notch_enabled` | `bool` | `True` | Master toggle: inside-edge grab/remove cutout bordering the shaft |
| `removal_notch_width` | `float` | `24.0` | Tangential width of the inside-edge cutout in mm |
| `removal_notch_depth` | `float` | `6.0` | Radial depth of cutout extending outward from inner bore in mm |
| `removal_notch_angle` | `float` | `180.0` | Angular position of cutout in degrees (`180` = spine opposite C-opening) |
| `removal_notch_fillet` | `float` | `0.6` | Transition fillet where cutout meets inner bore in mm (`0.0` for crisp edge) |
| `edge_chamfer_enabled` | `bool` | `True` | Master toggle: subtle top and bottom perimeter edge bevel |
| `edge_chamfer` | `float` | `0.3` | Chamfer size on top and bottom edges in mm |

---

## Usage

Configure parameters in `CClipSpacerParams` at the top of `c_clip_spacer.py` and run:

```bash
python3 c_clip_spacer.py
```

### Export Configuration

Toggle export flags at the top of `c_clip_spacer.py` to generate STEP and STL files into `models/c_clip_spacer/exports/`:

```python
EXPORT_STL: bool = False      # Enable/disable STL file export (default: False)
EXPORT_STEP: bool = False     # Enable/disable STEP file export (default: False)
OUTPUT_DIR: str = "exports"   # Relative subfolder alongside the script
```

### Python API Example

```python
from c_clip_spacer import CClipSpacerParams, create_c_clip_spacer

# Create a 4mm thick C-clip spacer for a 1/2" (12.7mm) rod
params = CClipSpacerParams(
    thickness=4.0,
    inside_diameter=12.7,
    outside_diameter=24.0,
    removal_notch_width=4.5,
    removal_notch_depth=1.8,
)

spacer = create_c_clip_spacer(params)
```
