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
4. **[`create_compartment_scoops(params)`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L584-L828)**:
   - Supports two scoop modes via `scoop_style`:
     - `"directional"` *(default)*: Generates true circular tangent finger-scoop ramps along any combination of `scoop_front_radius`, `scoop_back_radius`, `scoop_left_radius`, and `scoop_right_radius` (set any radius to `0.0` to disable that wall), adapting automatically to both vertical walls and angled overhang walls.
     - `"bowl"`: Generates a 360° all-around floor fillet of radius `scoop_bowl_radius` with cylindrical wall ramps and smooth spherical/toroidal corners around all 4 sides of every compartment so small parts slide out from any direction.
5. **[`create_label_holders(params)`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L815-L932)**:
   - Generates a continuous horizontal Pred-style label shelf deck at $z = \text{body\_h}$ supported by evenly spaced diagonal support fins (`label_fin_count`, `label_fin_max_span`, `label_fin_thickness`, `label_overhang_angle`) that bridge cleanly while preserving interior bin space underneath.
   - Cuts a two-tier recessed snap-in label socket into the top of the shelf matching standard 3D-printable Pred labels ($11.5\,\text{mm}$ deep) with self-contained undercut side-tab slots ($1.0\,\text{mm}$ tall beneath a $0.6\,\text{mm}$ top retention roof flush with $z = \text{body\_h}$), locking down both outer and inner label tabs without interfering with upper bin stacking.
   - Supports 4 `label_style` layouts:
     - `"auto"` *(default)*: Ties labels to X-dividers when compartments are $\ge 1\text{U}$ wide (e.g., a $2\times2$ bin gets 1 full-width label when undivided, or 2 standard 1U labels when divided in two), falling back to `"per_column"` if compartments are narrower than 1U.
     - `"center_1u"`: Always places a single centered 1U label ($36.4\,\text{mm}$ pocket width) regardless of bin width or X-dividers.
     - `"full_width"`: Always places a single full-width label across the bin width regardless of X-dividers.
     - `"per_column"`: Always places one standard 1U label per $42\,\text{mm}$ grid column along X regardless of X-dividers.

---

## Parameters Reference (`GridfinityBinParams`)

All geometric parameters are defined in [`GridfinityBinParams`](file:///home/luke/repos/code-cad/models/gridfinity_bin/gridfinity_bin.py#L41-L121):

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
| `magnet_holes` | `bool` | `False` | Master toggle: adds 4 corner pockets per foot cell for $6\times 2\,\text{mm}$ magnets |
| `screw_holes` | `bool` | `False` | Master toggle: adds through-holes for M3 mounting bolts |
| `stackable` | `bool` | `True` | Master toggle: adds continuous upper stacking lip for bin nesting |
| `lip_height` | `float` | `3.8` | Printable stacking lip height above `body_h` in mm |
| `lip_top_flat` | `float` | `0.6` | Flat top rim width in mm (avoids fragile knife-edge) |
| `label_enabled` | `bool` | `True` | Master toggle: adds Pred-compatible printable label shelf & recessed socket |
| `label_wall` | `str` | `"back"` | Compartment wall (`"back"` or `"front"`) where label shelf mounts |
| `label_style` | `str` | `"auto"` | `"auto"`, `"center_1u"`, `"full_width"`, or `"per_column"` |
| `label_height` | `float` | `11.5` | Label plate depth (Y) in mm (fits $\sim 11.3\,\text{mm}$ Pred label) |
| `label_thickness` | `float` | `1.0` | Recessed pocket & tab slot height (Z) in mm (fits $\sim 0.87\,\text{mm}$ tab) |
| `label_shelf_depth` | `float` | `13.5` | Total inward depth (Y) of the supporting shelf overhang in mm |
| `label_shelf_thickness`| `float`| `2.4` | Vertical thickness of shelf deck in mm ($0.6$ roof + $1.0$ slot + $0.8$ floor) |
| `label_fin_count` | `int \| None` | `None` | Manual fin count override per compartment (`None` = auto-calculate) |
| `label_fin_max_span` | `float` | `12.0` | Max unsupported bridge span in mm when `label_fin_count` is `None` |
| `label_fin_thickness`| `float` | `0.8` | Thickness (X) of each diagonal support fin in mm |
| `label_overhang_angle`| `float`| `35.0` | Support fin angle underneath the label shelf in degrees |
| `label_tab_width` | `float` | `6.5` | Width (Y) of side snap-in retention tab slots in mm (fits $\sim 5.9\,\text{mm}$ tab) |
| `label_tab_extension`| `float` | `0.8` | Extension (X) of side retention tab notches per side in mm |
| `scoop_enabled` | `bool` | `True` | Master toggle: enables/disables all ergonomic finger scoops |
| `scoop_style` | `str` | `"directional"` | `"directional"` (per-wall radii) or `"bowl"` (360° all-around floor fillet) |
| `scoop_bowl_radius` | `float` | `8.0` | 360° all-around floor fillet radius in mm when `scoop_style="bowl"` |
| `scoop_front_radius`| `float` | `12.0` | Front ($-Y$) concave finger scoop radius in mm (`0.0` to disable) |
| `scoop_back_radius` | `float` | `6.0` | Back ($+Y$) concave finger scoop radius in mm (`0.0` to disable) |
| `scoop_left_radius` | `float` | `0.0` | Left ($-X$) concave finger scoop radius in mm (`0.0` to disable) |
| `scoop_right_radius`| `float` | `0.0` | Right ($+X$) concave finger scoop radius in mm (`0.0` to disable) |
| `dividers_enabled` | `bool` | `False` | Master toggle: enables/disables interior dividing walls |
| `dividers_x` | `int` | `1` | Number of interior divider walls along X (`0` = undivided) |
| `dividers_y` | `int` | `0` | Number of interior divider walls along Y (`0` = undivided) |
| `divider_thickness` | `float`| `1.2` | Wall thickness of internal dividing walls in mm |
| `overhang_enabled` | `bool` | `False` | Master toggle: enables/disables drawer spacer gap overhangs |
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
