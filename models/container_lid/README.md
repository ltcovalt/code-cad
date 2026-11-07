# Container Lid Generator (`build123d`) [DRAFT / WIP]

> [!NOTE]
> **Status: Work In Progress (Draft / WIP)**
> This generator is an active prototype undergoing development, tuning, and testing.

A fully parameterized 3D CAD model generator for replacing lost or damaged container lids (such as round and rectangular **Pyrex** glass containers, food storage bowls, and bakeware dishes).

Designed to support:
1. **Flexible Materials (TPU / TPE)**: Uses a continuous under-lip retention bead for a 100% leak-resistant, airtight stretch-fit seal.
2. **Rigid Food-Safe Plastics (PCTG / PETG / PP)**: Automatically adapts geometry with compliant cantilever flexure slots and a shallower retention bead so the skirt snaps over the glass bead without cracking or fatiguing.

---

## Key Features

- **Multi-Shape Support**: Parametric models for `round`, `rectangular`, and `square` container shapes.
- **Under-Lip Snap Retention Bead**: Protruding inner ridge that snaps underneath the container's glass rim lip. Bottom $45^\circ$ lead-in chamfer ensures effortless push-on mounting.
- **Inner Seal Plug Ring**: Downward tongue that fits just inside the container opening, creating a snug channel for the glass rim that prevents liquid from sloshing out.
- **Stacking Nesting Rim**: Raised rim on the top deck allowing another container or lid to stack securely without slipping.
- **Ergonomic Pull Tab**: Peeling flexible lids off glass containers is effortless thanks to a corner pull tab (rectangular) or edge pull tab (round), featuring textured non-slip traction ribs and a hanging/drying peg hole.
- **PCTG / PETG Flexure Relief Slots**: For rigid plastics, cuts vertical relief slots through the skirt with radiused stress-relief roots, converting the stiff skirt into springy snap-fingers.
- **Verified Pyrex Presets**: Built-in dimensions for popular Pyrex 1-cup, 2-cup, 4-cup, 7-cup round bowls and 3-cup, 6-cup, 11-cup rectangular baking dishes.

---

## Material Comparison & Print Recommendations

| Material | Fit Clearance | Bead Depth | Skirt Design | 3D Printing Tips |
| :--- | :--- | :--- | :--- | :--- |
| **TPU 95A** *(Recommended)* | `-0.2 mm` (Stretch) | `0.8 mm` | Solid continuous skirt | Print slow (30–45 mm/s), 4–5 top/bottom layers for watertightness, retraction minimized or off. Virtually zero warp. |
| **PCTG / PETG** | `+0.2 mm` (Slide) | `0.35 mm` | Compliant flexure slots | 4 perimeter walls, no brim needed, PETG/PCTG has high chemical/heat resistance. Washable up to ~75°C. |
| **PP (Polypropylene)** | `-0.1 mm` | `0.6 mm` | Solid or flex slots | Ideal food-safe OEM lid material. Requires PP print sheet or PP tape on build plate. |

---

## Configurable Parameters (`LidParams`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `material` | `str` | `"tpu"` | `"tpu"` (continuous stretch) or `"pctg"` / `"petg"` (compliant flex slots) |
| `shape` | `str` | `"round"` | `"round"` or `"rectangular"` |
| `rim_style` | `str` | `"beaded"` | `"beaded"` (standard container with lip bead) or `"smooth"` (straight glass wall) |
| `friction_ribs` | `bool` | `False` | Auto-enabled for `"smooth"`: adds dual wiper gasket ribs for vacuum friction grip |
| `diameter` | `float` | `150.0` | Container rim lip outer diameter (mm, round containers) |
| `diameter_in` | `float` | `None` | Container rim lip outer diameter in **inches** (e.g. `6.0`) |
| `length` | `float` | `182.0` | Container rim lip outer length (mm, rectangular containers) |
| `length_in` | `float` | `None` | Container rim lip outer length in **inches** (e.g. `7.25`) |
| `width` | `float` | `132.0` | Container rim lip outer width (mm, rectangular containers) |
| `width_in` | `float` | `None` | Container rim lip outer width in **inches** (e.g. `5.25`) |
| `corner_radius`| `float` | `20.0` | Glass dish corner radius (mm, rectangular containers) |
| `rim_lip_height` | `float` | `5.0` | Vertical thickness of the container's glass rim lip (mm) |
| `glass_wall_thickness` | `float` | `4.0` | Glass wall thickness at the container rim (mm) |
| `top_thickness` | `float` | `1.8` | Top plate thickness (mm) |
| `skirt_height` | `float` | `10.0` | Total downward skirt height (mm) |
| `skirt_wall_thickness` | `float` | `1.8` | Skirt wall thickness (mm) |
| `test_ring` | `bool` | `False` | Fast **fit-check gauge ring**: hollows out center deck (~8 min print, ~5g filament) |
| `snap_ridge` | `bool` | `True` | Enable/disable the under-lip retention bead |
| `inner_seal_ring` | `bool` | `True` | Enable/disable inner plug ring for spill prevention |
| `stacking_rim` | `bool` | `True` | Enable/disable top stacking nesting rim |
| `pull_tab` | `bool` | `True` | Enable/disable pull tab with grip ridges |
| `tab_length` | `float` | `8.5` | Compact protrusion length beyond skirt in mm |
| `tab_width` | `float` | `22.0` | Width of pull tab in mm |
| `tab_root_overlap` | `float` | `6.0` | Deep root overlap into top plate/skirt to prevent tear-off |
| `tab_gusset_depth` | `float` | `2.5` | Depth of under-tab structural gusset down the skirt wall in mm |
| `flex_slots` | `bool` | `None` | Auto: `True` for PCTG/rigid, `False` for TPU |

---

## Quick Usage

```python
from build123d import *
from container_lid import ContainerLidParams, PYREX_PRESETS, create_container_lid

# 1. Using a Pyrex preset (4-Cup Round in TPU)
params = PYREX_PRESETS["pyrex_round_4_cup"]
params.material = "tpu"
lid = create_container_lid(params)

# 2. Custom Rectangular Dish in PCTG
custom_rect = ContainerLidParams(
    shape="rectangular",
    material="pctg",
    length=195.0,
    width=145.0,
    corner_radius=22.0,
    rim_lip_height=5.2,
)
pctg_lid = create_container_lid(custom_rect)
```
