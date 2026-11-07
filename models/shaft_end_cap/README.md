# Parametric Shaft End Cap

Parametric build123d end cap designed for rod and shaft assemblies, such as 1/2" rod shelf brackets used for filament spool storage. The cap presses onto the rod to prevent filament spools from sliding off while providing smooth, bump-safe outer profiles.

---

## Features

- **Parametric Shaft Dimensions**: Configurable shaft diameter (defaults to 12.7 mm / 0.5 inches) and dialed-in 3D print fit clearance (default 0.2 mm).
- **Customizable Collar**: Configurable press-fit collar sleeve length and wall thickness for sturdy grip strength.
- **Filament Retention Flange**: Wide flange with customizable diameter and thickness, reinforced with a stress-relief fillet to the collar body.
- **Multiple End Cap Styles**:
  - `'dome'` (or `'semi-spherical'`): Smooth spherical dome / crown protecting hands and heads from painful bumps. Supports full hemisphere or custom low-profile `dome_height`.
  - `'flat'`: Clean low-profile flat face with rounded or chamfered front rim.
  - `'chamfer'`: Conical beveled face with adjustable chamfer length.
  - `'round'`: Generously rounded front rim transition.
- **Easy Press-Fit Lead-In**: 45° internal chamfer at the mouth of the collar bore for effortless alignment and insertion onto rods.
- **Invisible Internal Vent Channel**: Longitudinal groove along the internal collar bore vents trapped air backwards out the collar mouth, allowing a 100% solid, flawless front face.
- **Optional Air-Relief Vent Hole**: Optional coaxial through-hole if a through-bore or tap-out access is desired (defaults to `0.0` disabled).
- **Optional Finger Grip Flutes**: Scalloped perimeter flutes around the flange for quick grip and twisting during removal.

---

## Parameter Reference (`ShaftEndCapParams`)

| Parameter | Type | Default | Description |
|:---|:---:|:---:|:---|
| `shaft_diameter` | `float` | `12.7` | Nominal shaft/rod diameter in mm (12.7 mm = 1/2 inch) |
| `fit_clearance` | `float` | `0.2` | Diametral fit clearance in mm (bore = `shaft_diameter + fit_clearance`) |
| `collar_length` | `float` | `18.0` | Insertion depth of the collar sleeve pressing onto the rod (mm) |
| `collar_wall_thickness` | `float` | `2.4` | Wall thickness of the collar sleeve (mm) |
| `lead_in_chamfer` | `float` | `1.0` | Internal entry chamfer at collar mouth for easy push-on fit (mm) |
| `flange_diameter` | `float` | `32.0` | Outer diameter of retaining flange disk (mm) |
| `flange_thickness` | `float` | `3.5` | Thickness of the flange disk (mm) |
| `flange_fillet` | `float` | `1.5` | Stress-relief fillet between collar body and flange underside (mm) |
| `flange_front_radius` | `float` | `1.0` | Front rim edge radius (tip / bed side) (mm, `0.0` for crisp edge) |
| `flange_rear_radius` | `float` | `1.5` | Rear rim edge radius (collar / spool side) (mm, `0.0` for crisp edge) |
| `cap_style` | `str` | `"dome"` | End cap style: `'dome'`, `'flat'`, `'chamfer'`, or `'round'` |
| `dome_height` | `Optional[float]` | `None` | Dome height above flange in mm (`None` = full hemisphere) |
| `chamfer_length` | `float` | `2.5` | Axial length of 45° conical bevel when using `'chamfer'` style (mm) |
| `vent_hole_diameter` | `float` | `0.0` | Coaxial air relief hole diameter in mm (`0.0` for solid seamless front face) |
| `vent_channel_width` | `float` | `1.0` | Width of internal collar vent channel along bore (mm, `0.0` to disable) |
| `vent_channel_depth` | `float` | `0.6` | Radial depth of internal vent channel into collar wall (mm) |
| `grip_groove_count` | `int` | `0` | Number of scalloped finger grip grooves around perimeter (`0` = smooth) |
| `grip_groove_radius` | `float` | `1.2` | Radial cut radius of perimeter finger grip grooves (mm) |

---

## Usage

Configure parameters in `ShaftEndCapParams` at the top of `shaft_end_cap.py` and run:

```bash
python3 shaft_end_cap.py
```

### Export Configuration

Toggle export flags at the top of `shaft_end_cap.py` to generate STEP and STL files into `models/shaft_end_cap/exports/`:

```python
EXPORT_STL: bool = False                # Save .stl file on execution (default: False)
EXPORT_STEP: bool = False               # Save .step file on execution (default: False)
OUTPUT_DIR: str = "exports"            # Output folder alongside this script
```

### Python API Example

```python
from shaft_end_cap import ShaftEndCapParams, create_shaft_end_cap

# Create a 1/2" rod filament shelf cap with a bump-safe semi-spherical dome
params = ShaftEndCapParams(
    shaft_diameter=12.7,       # 1/2 inch rod
    flange_diameter=34.0,      # Wide filament spool stop
    cap_style="dome",          # Smooth semi-spherical bump protection
    grip_groove_count=12,      # 12 finger grip grooves for easy removal
)

cap = create_shaft_end_cap(params)
```
