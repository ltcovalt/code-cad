# Parametric Gridfinity Bin with Pred-Compatible Printable Label Holder

A modular, component-based 3D CAD generator written in Python using `build123d`. Designed for universal compatibility with Zack Freedman's open-source **Gridfinity** modular storage system and community creator **Pred**'s printable snap-in label standard ([Printables #592545](https://www.printables.com/model/592545-gridfinity-bin-with-printable-label-by-pred-parame)).

---

## Modular Component Architecture

Each geometric feature is implemented as an independent, standalone component function in [gridfinity_bin.py](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py) and composed cleanly in [`create_gridfinity_bin()`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L622-L649):

1. **[`create_base_feet(params)`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L223-L280)**:
   - Builds the $N \times M$ array of 3-stage Gridfinity stacking feet ($0.8\,\text{mm}$ $45^\circ$ bottom chamfer, $1.8\,\text{mm}$ vertical step, $2.15\,\text{mm}$ $45^\circ$ upper chamfer).
   - Cuts optional corner magnet pockets ($\varnothing 6.5 \times 2.4\,\text{mm}$ at $26\,\text{mm}$ spacing) and M3 mounting holes.
2. **[`create_bin_body(params)`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L286-L354)**:
   - Generates the outer bin shell from $z = 4.75\,\text{mm}$ up to $z = \text{grid\_z} \times \text{unit\_z}$.
   - Incorporates optional asymmetric drawer-spacer overhangs (`overhang_front`, `overhang_back`, `overhang_left`, `overhang_right`) with print-safe $45^\circ$ underside chamfers.
   - Cuts the $C_x \times C_y$ interior compartments and dividing walls.
3. **[`create_stacking_lip(params)`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L360-L433)**:
   - Generates a complete, unbroken concentric top stacking rim around all 4 straight walls and all 4 rounded corners.
   - Includes the internal $45^\circ$ support step below $z = \text{body\_h}$ (transitioning from `wall_thickness` to the $2.6\,\text{mm}$ lip depth) and the standard $0.7\,\text{mm} / 1.8\,\text{mm} / 1.9\,\text{mm}$ stacking profile above $z = \text{body\_h}$.
4. **[`create_compartment_scoops(params)`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L542-L674)**:
   - Generates true circular tangent finger-scoop ramps (`scoop_front_radius`, `scoop_back_radius`) along the bottom front and/or back interior edges of every compartment (set either radius to `0.0` to disable that side), adapting automatically to both vertical walls and angled overhang walls.
5. **[`create_label_holders(params)`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L680-L833)**:
   - Generates a thin horizontal Pred-style label shelf deck at $z = \text{body\_h}$ supported by evenly spaced diagonal support fins (`label_fin_count`, `label_fin_thickness`, `label_overhang_angle`) that bridge cleanly while preserving interior bin space underneath.
   - Cuts a recessed snap-in label socket into the top of the shelf matching standard 3D-printable Pred labels ($11.5\,\text{mm}$ deep $\times 0.8\,\text{mm}$ recessed), complete with side snap-tab retention notches.

---

## Parameters Reference (`GridfinityBinParams`)

All geometric parameters are defined in [`GridfinityBinParams`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L41-L117):

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `grid_x` | `int` | `1` | Number of grid units along X (width) |
| `grid_y` | `int` | `1` | Number of grid units along Y (length/depth) |
| `grid_z` | `int` | `4` | Number of height units along Z |
| `unit_size` | `float` | `42.0` | Base XY grid pitch in mm (standard Gridfinity = $42.0\,\text{mm}$) |
| `unit_z` | `float` | `7.0` | Height Z unit pitch in mm (standard Gridfinity = $7.0\,\text{mm}$) |
| `grid_clearance` | `float` | `0.5` | Total XY clearance gap between bins in mm ($0.25\,\text{mm}$/side) |
| `wall_thickness` | `float` | `1.2` | Exterior wall thickness in mm (3 perimeters w/ $0.4\,\text{mm}$ nozzle) |
| `floor_thickness` | `float` | `2.0` | Solid floor thickness above base feet sockets in mm |
| `corner_radius` | `float` | `3.75` | Outer vertical corner radius in mm ($4.0\,\text{mm} - 0.25\,\text{mm}$ inset) |
| `magnet_holes` | `bool` | `False` | Adds 4 corner pockets per foot cell for $6\times 2\,\text{mm}$ magnets |
| `screw_holes` | `bool` | `False` | Adds through-holes for M3 mounting bolts |
| `stackable` | `bool` | `True` | Adds continuous upper stacking lip for bin nesting |
| `lip_height` | `float` | `3.8` | Printable stacking lip height above `body_h` in mm |
| `lip_top_flat` | `float` | `0.6` | Flat top rim width in mm (avoids fragile knife-edge) |
| `label_enabled` | `bool` | `True` | Adds Pred-compatible printable label shelf & recessed socket |
| `label_wall` | `str` | `"back"` | Compartment wall (`"back"` or `"front"`) where label shelf mounts |
| `label_style` | `str` | `"per_column"` | `"per_column"` (slot per unit) or `"full_width"` (one wide slot) |
| `label_height` | `float` | `11.5` | Label plate depth (Y) in mm (fits $\sim 11.3\,\text{mm}$ Pred label) |
| `label_thickness` | `float` | `1.0` | Recessed pocket & tab slot height (Z) in mm (fits $\sim 0.87\,\text{mm}$ tab) |
| `label_shelf_depth` | `float` | `13.5` | Total inward depth (Y) of the supporting shelf overhang in mm |
| `label_shelf_thickness`| `float`| `1.8` | Vertical thickness of the horizontal shelf deck in mm |
| `label_fin_count` | `int \| None` | `None` | Manual fin count override per compartment (`None` = auto-calculate) |
| `label_fin_max_span` | `float` | `12.0` | Max unsupported bridge span in mm when `label_fin_count` is `None` |
| `label_fin_thickness`| `float` | `1.2` | Thickness (X) of each diagonal support fin in mm |
| `label_overhang_angle`| `float`| `35.0` | Support fin angle underneath the label shelf in degrees |
| `label_tab_width` | `float` | `6.5` | Width (Y) of side snap-in retention tab slots in mm (fits $\sim 5.9\,\text{mm}$ tab) |
| `label_tab_extension`| `float` | `0.8` | Extension (X) of side retention tab notches per side in mm |
| `scoop_front_radius`| `float` | `12.0` | Front ($-Y$) concave finger scoop radius in mm (`0.0` to disable) |
| `scoop_back_radius` | `float` | `6.0` | Back ($+Y$) concave finger scoop radius in mm (`0.0` to disable) |
| `compartments_x`| `int` | `1` | Number of interior compartments along X |
| `compartments_y`| `int` | `1` | Number of interior compartments along Y |
| `divider_thickness` | `float`| `1.2` | Wall thickness of internal dividing walls in mm |
| `overhang_front`| `float` | `0.0` | Body extension past front ($-Y$) grid boundary in mm |
| `overhang_back` | `float` | `0.0` | Body extension past back ($+Y$) grid boundary in mm |
| `overhang_left` | `float` | `0.0` | Body extension past left ($-X$) grid boundary in mm |
| `overhang_right`| `float` | `0.0` | Body extension past right ($+X$) grid boundary in mm |

---

## Export Configuration

Exports are controlled by the standardized top-level variables in [gridfinity_bin.py](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L36-L38):

```python
EXPORT_STL: bool = False      # Enable/disable STL export
EXPORT_STEP: bool = False     # Enable/disable STEP export
OUTPUT_DIR: str = "exports"   # Relative subfolder alongside the script
```
