"""
Vertical stacking C-sleeve caddy for RC buggy and stadium truck tires.

Builds a rigid, sleek, 100% support-free 3D-printable vertical stacking tire
caddy pre-configured for 1/10 scale 2WD carpet buggies (Schumacher Cougar LD2,
XRAY XB2, Team Associated B6/B7) running 2.2" carpet tires such as JConcepts
3DP, Fuzz Bite, Pin Swag, and Schumacher Cactus/Mezzo, with built-in profiles
for 2WD wide fronts, 4WD carpet, 2WD dirt/clay, stadium truck, and custom sizes.

Features:
- Built-in 1/10 RC tire profiles (2WD Carpet Slim, 2WD Carpet Wide, 4WD Carpet,
  2WD Dirt/Clay, Stadium Truck) plus custom front/rear OD and width
- Four stacking arrangements:
  - `per_set`: 1 complete matched set (2 rears + 2 fronts) per tower (default:
    2 towers = 2 full sets / 8 tires, balanced height and unified lid)
  - `by_axle`: dedicated snug-fit front and rear towers
  - `rears_only` / `fronts_only`: uniform single-size tire stacks
- Reinforced C-sleeve support (`c_sleeve`, default):
  - Continuous ~265° curved shell with a configurable ~95° front opening and
    smooth rounded jaw tips (C-clip retention mechanic — captures even slim
    72-76 mm 2WD front tires inside an 86.5 mm rear-sized sleeve while keeping
    plenty of finger access)
  - Shared-wall twin/multi-tower fusion: adjacent towers overlap to partially
    share their inner wall into one compact, ultra-rigid monolithic body
  - 45° external base root gusset collar where the C-sleeve meets the base
  - Configurable vertical lightening slots (`cutout_count` up to 12 honored
    across each tower's clear arc, `cutout_width`, and `cutout_shape`:
    `crowned_arch`, smooth `teardrop`, `stadium`, or `hex_truss`)
- Dedicated Lid group (`LidParams`) supporting BOTH:
  - `outer_cap`: slip-over outer-skirt lid contoured to the tower exterior
    (unified figure-8 lid for equal-height shared-wall towers; zero interior
    height lost)
  - `inner_plug`: individual slotted press-fit plug lid per tower with
    automatic sleeve headroom so the plug never contacts the top tire
  - Single-part (`caddy` / `lid`) or combined build-plate export (`both`)
- Form-fitting contoured base or auto-sized Gridfinity 42 mm modular base
- Optional alternative center-spindle modes (`m4_rod`, `m5_rod`, `printed_post`)
  and optional 12 mm wheel-hex centering boss
- Single-tower Test Fit mode to quickly verify tire OD and lid fit in one print
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from build123d import *

try:
    from components.gridfinity_base import (
        GRIDFINITY_CORNER_RADIUS,
        GRIDFINITY_FOOT_HEIGHT,
        GridfinityBaseParams,
        compute_gridfinity_footprint,
        create_gridfinity_base,
    )
    from utils.params import default_preset, group, param
except ImportError:
    import sys

    for _p in Path(__file__).resolve().parents:
        if (_p / "utils").is_dir():
            sys.path.insert(0, str(_p))
            break
    from components.gridfinity_base import (
        GRIDFINITY_CORNER_RADIUS,
        GRIDFINITY_FOOT_HEIGHT,
        GridfinityBaseParams,
        compute_gridfinity_footprint,
        create_gridfinity_base,
    )
    from utils.params import default_preset, group, param

MODEL_NAME: str = "RC Tire Caddy"

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False      # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False     # Save .step to repo-root exports/ (default: False)


# Nominal RC tire profiles: (rear_od, rear_width, front_od, front_width) in mm
TIRE_PROFILES: dict[str, tuple[float, float, float, float]] = {
    # 1/10 2WD Carpet (3DP, Fuzz Bite, Pin Swag Slim on 2.2" slim front / std rear)
    "buggy_2wd_carpet_slim": (84.0, 41.0, 76.0, 24.0),
    # 1/10 2WD Carpet with wide front wheels (Fuzz Bite Wide, Pin Swag Wide, Cactus Fusion)
    "buggy_2wd_carpet_wide": (84.0, 41.0, 78.0, 29.0),
    # 1/10 4WD Carpet Buggy (XRAY XB4, Schumacher L1R, B74)
    "buggy_4wd_carpet": (84.0, 41.0, 78.0, 31.0),
    # 1/10 2WD Dirt / Clay Buggy (slightly taller tread carcass)
    "buggy_2wd_dirt": (85.0, 42.0, 80.0, 28.0),
    # 1/10 Stadium Truck (2.2" truck wheels)
    "stadium_truck": (106.0, 52.0, 106.0, 52.0),
}

# Hardware threaded-rod / hex-nut specs: (rod_d, nut_across_flats, nut_depth) in mm
ROD_SPECS: dict[str, tuple[float, float, float]] = {
    "m4_rod": (4.0, 7.3, 3.6),   # ISO 4032 M4 nut (7.0 mm AF + 0.3 mm fit)
    "m5_rod": (5.0, 8.3, 4.4),   # ISO 4032 M5 nut (8.0 mm AF + 0.3 mm fit)
}


@dataclass(frozen=True)
class _StackSpec:
    """Computed placement and dimensions for a single vertical tire stack."""

    cx: float
    cy: float
    well_od: float
    stack_height: float
    is_front: bool = False


@dataclass
class TireParams:
    """Tire class profile, custom dimensions, and clearance margins."""

    tire_profile: Literal[
        "buggy_2wd_carpet_slim",
        "buggy_2wd_carpet_wide",
        "buggy_4wd_carpet",
        "buggy_2wd_dirt",
        "stadium_truck",
        "custom",
    ] = param(
        "buggy_2wd_carpet_slim",
        label="Tire Profile",
        desc="Standard 1/10 RC tire size preset (2WD Carpet Slim fits 3DP, Fuzz Bite, Pin Swag on LD2/XB2)",
    )
    rear_od: float = param(
        84.0,
        label="Rear Outer Diameter",
        desc="Rear tire outer diameter including tread",
        unit="mm", min=40.0, max=160.0, step=1.0,
        when={"tire_profile": "custom"},
    )
    rear_width: float = param(
        41.0,
        label="Rear Tire Width",
        desc="Rear tire overall width",
        unit="mm", min=15.0, max=80.0, step=0.5,
        when={"tire_profile": "custom"},
    )
    front_od: float = param(
        76.0,
        label="Front Outer Diameter",
        desc="Front tire outer diameter including tread",
        unit="mm", min=40.0, max=160.0, step=1.0,
        when={"tire_profile": "custom"},
    )
    front_width: float = param(
        24.0,
        label="Front Tire Width",
        desc="Front tire overall width",
        unit="mm", min=12.0, max=80.0, step=0.5,
        when={"tire_profile": "custom"},
    )
    radial_clearance: float = param(
        2.5,
        label="Tire Fit Clearance",
        desc="Extra diameter added inside each sleeve around the nominal tire OD",
        unit="mm", min=0.0, max=10.0, step=0.5,
    )
    stack_clearance: float = param(
        4.0,
        label="Vertical Headroom",
        desc="Extra breathing room above the nominal tire stack (inner-plug lids add their plug depth automatically)",
        unit="mm", min=0.0, max=30.0, step=1.0,
    )


@dataclass
class LayoutParams:
    """How tires are grouped into vertical towers and arranged on the base."""

    arrangement: Literal["per_set", "by_axle", "rears_only", "fronts_only"] = param(
        "per_set",
        desc="Per Set stacks 2 rears + 2 fronts per tower; By Axle creates snug-fit dedicated front and rear towers",
    )
    sets: int = param(
        2,
        label="Number of Tire Sets",
        desc="Full sets of 4 tires (2 fronts + 2 rears per set; 2 sets = 8 tires total)",
        min=1, max=6, step=1,
        when={"arrangement": ["per_set", "by_axle"]},
    )
    stacks: int = param(
        2,
        label="Number of Towers",
        desc="Number of vertical tire towers",
        min=1, max=8, step=1,
        when={"arrangement": ["rears_only", "fronts_only"]},
    )
    tires_per_stack: int = param(
        4,
        label="Tires per Tower",
        desc="Number of tires stacked vertically in each tower",
        min=1, max=8, step=1,
        when={"arrangement": ["rears_only", "fronts_only"]},
    )
    columns: Optional[int] = param(
        None,
        label="Grid Columns",
        desc="Towers per row along X (Auto = 1 row up to 3 towers, 2 rows for 4+ towers)",
        min=1, max=6, step=1,
    )
    shared_wall_thickness: float = param(
        4.6,
        label="Shared Inner Wall",
        desc="Center-to-center wall thickness between adjacent tire bores (< 2× sleeve wall merges towers into a shared wall)",
        unit="mm", min=3.0, max=25.0, step=0.2,
    )


@dataclass
class SupportParams:
    """C-sleeve wall geometry, vertical lightening slots, or optional center rod."""

    support_style: Literal["c_sleeve", "m4_rod", "m5_rod", "printed_post"] = param(
        "c_sleeve",
        desc="Continuous C-clip style outer sleeve (recommended), M4/M5 threaded rod, or printed center post",
    )
    # --- C-sleeve parameters ---
    opening_angle: float = param(
        95.0,
        label="Front Opening Angle",
        desc="Front C-opening angle (95° gives a ~64 mm chord on an 86.5 mm sleeve, retaining even slim 2WD fronts)",
        unit="°", min=60.0, max=160.0, step=5.0,
        when={"support_style": "c_sleeve"},
    )
    wall_thickness: float = param(
        3.6,
        label="Sleeve Wall Thickness",
        desc="Radial thickness of the C-sleeve walls",
        unit="mm", min=2.2, max=8.0, step=0.2,
        when={"support_style": "c_sleeve"},
    )
    height_ratio: float = param(
        1.0,
        label="Sleeve Height Ratio",
        desc="Sleeve height as a fraction of full stack + headroom (1.0 supports lids cleanly)",
        min=0.35, max=1.05, step=0.05,
        when={"support_style": "c_sleeve"},
    )
    root_gusset: float = param(
        3.5,
        label="Base Root Chamfer",
        desc="45° external reinforcement ramp where the C-sleeve meets the base plate (0 = none)",
        unit="mm", min=0.0, max=8.0, step=0.5,
        when={"support_style": "c_sleeve"},
    )
    wall_cutouts: bool = param(
        True,
        label="Wall Lightening Cutouts",
        desc="Cut print-friendly windows in the C-sleeve walls to save filament while keeping solid top/bottom bands",
        when={"support_style": "c_sleeve"},
    )
    cutout_count: int = param(
        3,
        label="Cutouts per Tower",
        desc="Number of cutout columns distributed evenly across each tower's clear outer/back arc",
        min=1, max=12, step=1,
        when={"support_style": "c_sleeve", "wall_cutouts": True},
    )
    cutout_rows: int = param(
        2,
        label="Cutout Tiers",
        desc="Vertical tiers of slots separated by a 10 mm horizontal stiffening ring to prevent tall-rib wobble and warping",
        min=1, max=4, step=1,
        when={"support_style": "c_sleeve", "wall_cutouts": True},
    )
    cutout_width: float = param(
        16.0,
        label="Cutout Width",
        desc="Width of each vertical cutout column (auto-clamped to preserve solid vertical ribs)",
        unit="mm", min=4.0, max=28.0, step=1.0,
        when={"support_style": "c_sleeve", "wall_cutouts": True},
    )
    cutout_shape: Literal["crowned_arch", "teardrop", "stadium", "hex_truss"] = param(
        "crowned_arch",
        label="Cutout Shape",
        desc="Crowned Arch (45° shoulders + short flat bridge), smooth Teardrop (<= 45° flanks + rounded crest), Stadium, or stacked Hex Truss",
        when={"support_style": "c_sleeve", "wall_cutouts": True},
    )
    cutout_shared_wall: bool = param(
        False,
        label="Cutout Shared Center Wall",
        desc="Allow cutouts through the shared inner wall between adjacent towers for visual symmetry (off by default to prevent tire pins snagging)",
        when={"support_style": "c_sleeve", "wall_cutouts": True},
    )
    # --- Hardware threaded-rod parameters ---
    rod_clearance: float = param(
        0.4,
        desc="Clearance added to nominal M4/M5 threaded rod diameter for through-holes",
        unit="mm", min=0.1, max=1.0, step=0.05,
        when={"support_style": ["m4_rod", "m5_rod"]},
    )
    # --- Printed center post parameters ---
    post_diameter: float = param(
        4.0,
        desc="Printed center spindle diameter (4.0 mm clears standard 4.5-5.0 mm 1/10 buggy wheel bores)",
        unit="mm", min=3.0, max=12.0, step=0.1,
        when={"support_style": "printed_post"},
    )
    clip_hole: bool = param(
        True,
        label="Body-Clip Retention Hole",
        desc="Cross-drilled hole near top of each printed spindle for an RC body clip (R-clip)",
        when={"support_style": "printed_post"},
    )
    clip_hole_diameter: float = param(
        1.8,
        label="Clip Hole Diameter",
        desc="Diameter of the cross-drilled RC body-clip hole",
        unit="mm", min=1.2, max=3.5, step=0.1,
        when={"support_style": "printed_post", "clip_hole": True},
    )
    # --- Optional bottom wheel-hex centering boss ---
    hex_seat: bool = param(
        False,
        label="12 mm Hex Wheel Seat",
        desc="Optional raised 12 mm hex centering boss on the floor (useful for center-rod modes; not needed with C-sleeve)",
    )
    hex_flat_size: float = param(
        11.6,
        label="Hex Across-Flats",
        desc="Across-flats width of the hex boss (11.6 mm slips cleanly into a 12 mm buggy wheel hex)",
        unit="mm", min=8.0, max=17.5, step=0.1,
        when={"hex_seat": True},
    )
    hex_seat_height: float = param(
        4.0,
        label="Hex Seat Height",
        desc="Height of the hex centering boss above the tire well floor",
        unit="mm", min=2.0, max=10.0, step=0.5,
        when={"hex_seat": True},
    )


@dataclass
class LidParams:
    """Press-fit outer cap or inner plug lid (or M4/M5 knob) and multi-part export layout."""

    output: Literal["both", "caddy", "lid"] = param(
        "both",
        label="Output Parts",
        desc="Generate Caddy + Lid(s) together on one build plate, Caddy only, or Lid/Knob only",
        when={"support.support_style": ["c_sleeve", "m4_rod", "m5_rod"]},
    )
    style: Literal["outer_cap", "inner_plug"] = param(
        "outer_cap",
        label="Lid Style",
        desc="Outer Cap slips over the outside of equal-height towers (zero interior height lost); Inner Plug fits inside each tower individually",
        when={"support.support_style": "c_sleeve", "output": ["both", "lid"]},
    )
    lid_target: Literal["rear", "front"] = param(
        "rear",
        label="Single Lid Size",
        desc="Choose rear or front tower diameter when exporting a single Inner Plug lid for By-Axle layouts",
        when={"support.support_style": "c_sleeve", "output": "lid", "style": "inner_plug"},
    )
    clearance: float = param(
        0.25,
        label="Press-Fit Clearance",
        desc="Radial clearance between lid skirt/plug and sleeve wall (smaller = tighter press fit)",
        unit="mm", min=0.05, max=0.8, step=0.05,
        when={"support.support_style": "c_sleeve", "output": ["both", "lid"]},
    )
    skirt_depth: float = param(
        8.0,
        label="Engagement Depth",
        desc="Overlap depth of the outer cap skirt or inner plug inside/outside the top of the C-sleeve",
        unit="mm", min=5.0, max=16.0, step=1.0,
        when={"support.support_style": "c_sleeve", "output": ["both", "lid"]},
    )
    snap_bead: float = param(
        0.85,
        label="Snap Retention Bead",
        desc="45° interlocking snap-bead height on the rim and lid skirt (0 = friction fit only; 0.85 mm gives a positive snap in PCTG/PETG)",
        unit="mm", min=0.0, max=1.4, step=0.05,
        when={"support.support_style": "c_sleeve", "output": ["both", "lid"]},
    )
    inner_align_lip: bool = param(
        True,
        label="Inner Anti-Warp Lip",
        desc="Add a short 4 mm inner alignment ring inside the outer cap to back up the C-sleeve against the snap bead",
        when={"support.support_style": "c_sleeve", "output": ["both", "lid"], "style": "outer_cap"},
    )
    flexure_slots: bool = param(
        True,
        label="Skirt Flexure Slots",
        desc="Add vertical relief slots around the outer cap skirt so rigid filaments snap smoothly over the rim bead",
        when={"support.support_style": "c_sleeve", "output": ["both", "lid"], "style": "outer_cap"},
    )
    bed_gap: float = param(
        12.0,
        label="Build-Plate Gap",
        desc="Spacing between the caddy and laid-out lid(s) on the build plate when exporting Both",
        unit="mm", min=4.0, max=40.0, step=1.0,
        when={"output": "both"},
    )


@dataclass
class BaseParams:
    """Base plate thickness, contoured skirt margin, and bottom bevel."""

    base_thickness: float = param(
        5.0,
        desc="Solid floor thickness beneath the tire towers (use >= 6 mm for M4/M5 underside nut traps)",
        unit="mm", min=3.0, max=15.0, step=0.5,
    )
    rim_height: float = param(
        0.0,
        label="Extra Base Rim Height",
        desc="Raised recessed-well rim height for center-rod modes (C-sleeve rises directly from the base floor)",
        unit="mm", min=0.0, max=16.0, step=0.5,
        when={"support.support_style": ["m4_rod", "m5_rod", "printed_post"]},
    )
    base_margin: float = param(
        0.5,
        label="Contoured Base Margin",
        desc="Extra radial margin around the base beyond the sleeve + root gusset (0 = flush with gusset)",
        unit="mm", min=0.0, max=10.0, step=0.5,
        when={"gridfinity_base": None},
    )
    bottom_chamfer: float = param(
        1.0,
        desc="Outer bottom perimeter chamfer to reduce elephant's foot",
        unit="mm", min=0.0, max=3.0, step=0.1,
        when={"gridfinity_base": None},
    )


@dataclass
class TestFitParams:
    """Single-tower test-fit mode for fast tire OD and press-fit lid verification."""

    enabled: bool = param(
        False,
        desc="Generate a short single-tower C-sleeve ring (plus matching lid when Output=Both) to verify tire and lid fit fast",
    )
    height: float = param(
        22.0,
        label="Test Section Height",
        desc="Shortened sleeve or spindle height for a fast fit-check print",
        unit="mm", min=12.0, max=60.0, step=1.0,
    )


@default_preset(
    "1/10 2WD Carpet Buggy — 2 Sets C-Sleeve + Lid (8 Tires)",
    desc="Form-fitting twin C-sleeve caddy with shared inner wall, 45° base root gussets, print-friendly vertical slots, and a unified slip-over outer cap lid",
)
@dataclass
class RcTireCaddyParams:
    """Master parameter schema for the RC Tire Storage Caddy generator."""

    tire: TireParams = group(TireParams)
    layout: LayoutParams = group(LayoutParams)
    support: SupportParams = group(SupportParams)
    lid: LidParams = group(LidParams)
    gridfinity_base: GridfinityBaseParams | None = group(
        GridfinityBaseParams,
        enabled=False,
        label="Gridfinity Base",
    )
    base: BaseParams = group(BaseParams)
    test_fit: TestFitParams = group(TestFitParams)


def resolve_tire_dimensions(tire: TireParams) -> tuple[float, float, float, float]:
    """Return nominal (rear_od, rear_width, front_od, front_width) in mm."""
    if tire.tire_profile == "custom":
        return (tire.rear_od, tire.rear_width, tire.front_od, tire.front_width)
    return TIRE_PROFILES[tire.tire_profile]


def _rounded_rect(width: float, height: float, radius: float) -> None:
    """Add a centered rectangle (rounded when radius > 0) inside an active BuildSketch."""
    r = min(radius, width / 2.0 - 0.1, height / 2.0 - 0.1)
    if r > 0.05:
        RectangleRounded(width, height, r)
    else:
        Rectangle(width, height)


def _uses_inner_plug_lid(params: RcTireCaddyParams, stacks: list[_StackSpec]) -> bool:
    """Return True when the active configuration uses inner-plug lids."""
    if params.support.support_style != "c_sleeve":
        return False
    if params.lid.output == "caddy":
        return False
    if params.lid.style == "inner_plug":
        return True
    # Outer unified cap requires equal tower heights; fall back to inner plug if uneven
    heights = {round(s.stack_height, 1) for s in stacks}
    return len(heights) > 1


def _build_stack_specs(params: RcTireCaddyParams) -> list[tuple[float, float, bool]]:
    """Return list of (well_od, stack_height, is_front) for each tower before XY placement."""
    tire = params.tire
    lay = params.layout
    rear_od, rear_w, front_od, front_w = resolve_tire_dimensions(tire)
    rear_well = rear_od + tire.radial_clearance
    front_well = front_od + tire.radial_clearance

    if lay.arrangement == "per_set":
        h = 2.0 * rear_w + 2.0 * front_w + tire.stack_clearance
        od = max(rear_well, front_well)
        return [(od, h, False) for _ in range(lay.sets)]

    if lay.arrangement == "by_axle":
        num_front_stacks = max(1, math.ceil(lay.sets / 2))
        num_rear_stacks = max(1, math.ceil(lay.sets / 2))
        fronts_total = 2 * lay.sets
        rears_total = 2 * lay.sets
        specs: list[tuple[float, float, bool]] = []
        for i in range(num_front_stacks):
            n = fronts_total // num_front_stacks + (1 if i < fronts_total % num_front_stacks else 0)
            specs.append((front_well, n * front_w + tire.stack_clearance, True))
        for i in range(num_rear_stacks):
            n = rears_total // num_rear_stacks + (1 if i < rears_total % num_rear_stacks else 0)
            specs.append((rear_well, n * rear_w + tire.stack_clearance, False))
        return specs

    if lay.arrangement == "rears_only":
        h = lay.tires_per_stack * rear_w + tire.stack_clearance
        return [(rear_well, h, False) for _ in range(lay.stacks)]

    # fronts_only
    h = lay.tires_per_stack * front_w + tire.stack_clearance
    return [(front_well, h, True) for _ in range(lay.stacks)]


def _resolve_layout(
    params: RcTireCaddyParams,
) -> tuple[list[_StackSpec], float, float, int, int, float]:
    """Compute (stacks, outer_x, outer_y, gx, gy, pad_extra_r) for the active config."""
    lay = params.layout
    sup = params.support
    gf = params.gridfinity_base
    bp = params.base
    tf = params.test_fit

    is_sleeve = sup.support_style == "c_sleeve"
    wall_add = sup.wall_thickness if is_sleeve else 3.0
    gusset_add = sup.root_gusset if is_sleeve else 0.0
    pad_extra_r = wall_add + gusset_add + (0.0 if gf is not None else bp.base_margin)

    if tf.enabled:
        if is_sleeve:
            rear_od, _, front_od, _ = resolve_tire_dimensions(params.tire)
            is_front = lay.arrangement == "fronts_only"
            ref_od = front_od if is_front else rear_od
            well_od = ref_od + params.tire.radial_clearance
            puck_d = well_od + 2.0 * pad_extra_r
            return ([_StackSpec(cx=0.0, cy=0.0, well_od=well_od, stack_height=tf.height, is_front=is_front)], puck_d, puck_d, 0, 0, pad_extra_r)
        puck_d = max(36.0, sup.hex_flat_size + 22.0)
        return ([_StackSpec(cx=0.0, cy=0.0, well_od=puck_d - 6.0, stack_height=tf.height)], puck_d, puck_d, 0, 0, 3.0)

    raw_specs = _build_stack_specs(params)
    n_stacks = len(raw_specs)

    if lay.columns is not None:
        cols = min(n_stacks, max(1, lay.columns))
    else:
        cols = n_stacks if n_stacks <= 3 else math.ceil(n_stacks / 2)
    rows = math.ceil(n_stacks / cols)

    col_ods = [0.0] * cols
    row_ods = [0.0] * rows
    for idx, (well_od, _, _) in enumerate(raw_specs):
        r = idx // cols
        c = idx % cols
        col_ods[c] = max(col_ods[c], well_od)
        row_ods[r] = max(row_ods[r], well_od)

    bore_gap = max(lay.shared_wall_thickness, sup.wall_thickness if is_sleeve else 3.0)
    total_bores_x = sum(col_ods) + (cols - 1) * bore_gap
    total_bores_y = sum(row_ods) + (rows - 1) * bore_gap

    col_centers: list[float] = []
    x_cursor = -total_bores_x / 2.0
    for w in col_ods:
        col_centers.append(x_cursor + w / 2.0)
        x_cursor += w + bore_gap

    row_centers: list[float] = []
    y_cursor = -total_bores_y / 2.0
    for d in row_ods:
        row_centers.append(y_cursor + d / 2.0)
        y_cursor += d + bore_gap

    stacks: list[_StackSpec] = []
    for idx, (well_od, stack_h, is_front) in enumerate(raw_specs):
        r = idx // cols
        c = idx % cols
        stacks.append(
            _StackSpec(
                cx=col_centers[c],
                cy=row_centers[r],
                well_od=well_od,
                stack_height=stack_h,
                is_front=is_front,
            )
        )

    min_outer_x = total_bores_x + 2.0 * pad_extra_r
    min_outer_y = total_bores_y + 2.0 * pad_extra_r

    if gf is not None:
        gx, gy, outer_x, outer_y = compute_gridfinity_footprint(
            min_outer_x,
            min_outer_y,
            grid_x=gf.grid_x,
            grid_y=gf.grid_y,
        )
    else:
        gx, gy = 0, 0
        outer_x, outer_y = min_outer_x, min_outer_y

    return (stacks, outer_x, outer_y, gx, gy, pad_extra_r)


def _sketch_c_annulus(
    r_in: float,
    r_out: float,
    opening_angle: float,
    tip_fillet: float,
) -> None:
    """Draw a C-shaped annular cross-section open toward -Y with rounded jaw tips."""
    a0 = math.radians(-90.0 - opening_angle / 2.0)
    a1 = math.radians(-90.0 + opening_angle / 2.0)
    r_cut = r_out * 2.5
    wedge_pts = [
        (0.0, 0.0),
        (r_cut * math.cos(a0), r_cut * math.sin(a0)),
        (0.0, -r_cut * 1.5),
        (r_cut * math.cos(a1), r_cut * math.sin(a1)),
    ]
    Circle(r_out)
    Circle(r_in, mode=Mode.SUBTRACT)
    Polygon(*wedge_pts, align=None, mode=Mode.SUBTRACT)
    if tip_fillet > 0.1:
        fillet(vertices(), radius=tip_fillet)


def _sketch_contoured_footprint(
    stacks: list[_StackSpec],
    extra_r: float,
    waist_fillet: float = 5.0,
) -> None:
    """Sketch the smoothly blended circular/figure-8 union of all towers."""
    for s in stacks:
        with Locations((s.cx, s.cy)):
            Circle(s.well_od / 2.0 + extra_r)
    for i in range(len(stacks)):
        for j in range(i + 1, len(stacks)):
            s1, s2 = stacks[i], stacks[j]
            dist = math.hypot(s2.cx - s1.cx, s2.cy - s1.cy)
            r1 = s1.well_od / 2.0 + extra_r
            r2 = s2.well_od / 2.0 + extra_r
            if dist > (r1 + r2 - 1.0) and dist < (r1 + r2 + 25.0):
                ang = math.degrees(math.atan2(s2.cy - s1.cy, s2.cx - s1.cx))
                mx, my = (s1.cx + s2.cx) / 2.0, (s1.cy + s2.cy) / 2.0
                bridge_w = min(r1, r2) * 0.5
                with Locations((mx, my)):
                    Rectangle(dist, bridge_w, rotation=ang)
    if len(stacks) > 1 and waist_fillet > 0.3:
        all_edges = list(edges())
        corner_verts = []
        min_edge_len = 1e9
        for v in vertices():
            inc = [
                e for e in all_edges
                if any(math.hypot(ev.X - v.X, ev.Y - v.Y) < 1e-4 for ev in e.vertices())
            ]
            if len(inc) == 2:
                corner_verts.append(v)
                min_edge_len = min(min_edge_len, inc[0].length, inc[1].length)
        eff_r = min(waist_fillet, min_edge_len * 0.4)
        if corner_verts and eff_r > 0.3:
            fillet(corner_verts, radius=eff_r)


def _compute_clear_cutout_angles(
    stack: _StackSpec,
    all_stacks: list[_StackSpec],
    r_in: float,
    wall_t: float,
    opening_deg: float,
    count: int,
    allow_shared_wall: bool = False,
) -> tuple[list[float], float]:
    """Compute ``count`` evenly distributed cutout angles on this tower's clear arc.

    Returns ``(angles_deg, max_slot_width_mm)`` so ``cutout_count`` is honored
    even when adjacent towers share an inner wall.
    """
    r_out = r_in + wall_t
    jaw_half = opening_deg / 2.0
    jaw_margin_deg = 22.0
    min_ang = -90.0 + jaw_half + jaw_margin_deg
    max_ang = 270.0 - jaw_half - jaw_margin_deg
    if max_ang <= min_ang:
        return ([], 0.0)

    if allow_shared_wall:
        valid_spans = [(min_ang, max_ang)]
    else:
        # Sample the C-arc at 1° resolution to find contiguous unobstructed spans
        n_samples = max(2, int(round(max_ang - min_ang)) + 1)
        clear_spans: list[tuple[float, float]] = []
        span_start: Optional[float] = None

        for i in range(n_samples):
            theta = min_ang + (max_ang - min_ang) * (i / (n_samples - 1))
            rad = math.radians(theta)
            probe_x = stack.cx + (r_out + 1.0) * math.cos(rad)
            probe_y = stack.cy + (r_out + 1.0) * math.sin(rad)
            blocked = False
            for other in all_stacks:
                if other is stack:
                    continue
                other_r_out = other.well_od / 2.0 + wall_t + 1.5
                if math.hypot(probe_x - other.cx, probe_y - other.cy) < other_r_out:
                    blocked = True
                    break
            if not blocked:
                if span_start is None:
                    span_start = theta
            else:
                if span_start is not None:
                    clear_spans.append((span_start, theta - 1.0))
                    span_start = None
        if span_start is not None:
            clear_spans.append((span_start, max_ang))

        # Keep spans wide enough for at least one slot (>= 14°)
        valid_spans = [(a, b) for a, b in clear_spans if (b - a) >= 14.0]
        if not valid_spans:
            return ([], 0.0)

    # Allocate the requested `count` proportionally across all clear spans
    total_clear_deg = sum(b - a for a, b in valid_spans)
    alloc = [max(1, int(round(count * (b - a) / total_clear_deg))) for a, b in valid_spans]
    while sum(alloc) > count:
        idx = max(range(len(alloc)), key=lambda k: alloc[k])
        if alloc[idx] <= 1:
            break
        alloc[idx] -= 1
    while sum(alloc) < count:
        idx = max(range(len(alloc)), key=lambda k: (valid_spans[k][1] - valid_spans[k][0]) / (alloc[k] + 1))
        alloc[idx] += 1

    angles: list[float] = []
    min_spacing_deg = 360.0
    for (a, b), k in zip(valid_spans, alloc):
        if k == 1:
            angles.append((a + b) / 2.0)
            min_spacing_deg = min(min_spacing_deg, (b - a))
        else:
            # Small margin from span edges so slots stay clear of jaw tips & shared waist
            inset = min(3.0, (b - a) * 0.04)
            sa, sb = a + inset, b - inset
            step = (sb - sa) / (k - 1)
            min_spacing_deg = min(min_spacing_deg, step)
            for j in range(k):
                angles.append(sa + j * step)

    # Preserve at least 4.2 mm of solid vertical rib between neighboring slots
    min_rib = 4.2
    arc_pitch = math.radians(min_spacing_deg) * r_in
    max_slot_w = max(4.0, arc_pitch - min_rib)
    return (angles, max_slot_w)


def _sketch_vertical_slot(
    slot_w: float,
    slot_h: float,
    zc: float,
    shape: Literal["crowned_arch", "teardrop", "stadium"],
) -> None:
    """Draw a print-friendly vertical lightening slot centered at (0, zc)."""
    hw = slot_w / 2.0
    hh = slot_h / 2.0

    if shape == "stadium":
        with Locations((0.0, zc)):
            SlotOverall(slot_h, slot_w, rotation=90.0)
        return

    if shape == "teardrop":
        # Smooth teardrop: rounded bottom semicircle, vertical walls, 45° tangent flanks,
        # and a smoothly rounded top crest (no harsh needle point, <= 45° overhang)
        z_bot_arc = zc - hh + hw
        z_top_shoulder = zc + hh - hw
        with Locations((0.0, z_bot_arc)):
            Circle(hw)
        Polygon(
            (-hw, z_bot_arc),
            (hw, z_bot_arc),
            (hw, z_top_shoulder),
            (0.0, zc + hh),
            (-hw, z_top_shoulder),
            align=None,
        )
        # Round the top apex + both 45° shoulder transitions into a true smooth teardrop
        top_verts = [v for v in vertices() if v.Y >= z_top_shoulder - 0.2]
        if top_verts:
            fillet(top_verts, radius=min(2.6, hw * 0.34))
        return

    # crowned_arch: symmetric 45° chamfered shoulders transitioning to a short flat bridge
    crown_half = hw * 0.35
    chamfer_h = hw - crown_half
    pts = [
        (-crown_half, zc - hh),
        (crown_half, zc - hh),
        (hw, zc - hh + chamfer_h),
        (hw, zc + hh - chamfer_h),
        (crown_half, zc + hh),
        (-crown_half, zc + hh),
        (-hw, zc + hh - chamfer_h),
        (-hw, zc - hh + chamfer_h),
    ]
    Polygon(*pts, align=None)


def _create_c_sleeve(
    stack: _StackSpec,
    sleeve_h: float,
    base_z: float,
    sup: SupportParams,
    lid: LidParams,
    use_inner_plug: bool,
) -> Part:
    """Build a C-sleeve tower with 45° root gusset, top lead-in bevel, and snap-retention rim."""
    r_in = stack.well_od / 2.0
    wall_t = sup.wall_thickness
    r_out = r_in + wall_t
    opening_deg = sup.opening_angle
    tip_r = min(wall_t * 0.45, 1.8)
    top_z = base_z + sleeve_h

    with BuildPart(mode=Mode.PRIVATE) as sleeve_bp:
        # 1. Main C-sleeve vertical wall (starts 0.5 mm into base for clean boolean fusion)
        with BuildSketch(Plane.XY.offset(base_z - 0.5)):
            _sketch_c_annulus(r_in, r_out, opening_deg, tip_r)
        extrude(amount=sleeve_h + 0.5)

        # 2. 45° external base root gusset collar for high cantilever rigidity
        gusset = min(sup.root_gusset, sleeve_h * 0.35)
        if gusset > 0.2:
            with BuildPart(mode=Mode.PRIVATE) as gusset_bp:
                with BuildSketch(Plane.XY.offset(base_z - 0.5)):
                    _sketch_c_annulus(r_in + 0.2, r_out + gusset, opening_deg, min(tip_r, 1.2))
                with BuildSketch(Plane.XY.offset(base_z)):
                    _sketch_c_annulus(r_in + 0.2, r_out + gusset, opening_deg, min(tip_r, 1.2))
                with BuildSketch(Plane.XY.offset(base_z + gusset)):
                    _sketch_c_annulus(r_in + 0.2, r_out, opening_deg, min(tip_r, 1.2))
                loft(ruled=True)
            add(gusset_bp.part)

        # 3. 45° internal top lead-in chamfer for smooth tire drops and lid entry
        lead_in = min(1.5, wall_t * 0.42, sleeve_h * 0.15)
        if lead_in > 0.15:
            overshoot = 0.2
            with BuildPart(mode=Mode.PRIVATE) as bevel_bp:
                with BuildSketch(Plane.XY.offset(top_z - lead_in)):
                    Circle(r_in)
                with BuildSketch(Plane.XY.offset(top_z + overshoot)):
                    Circle(r_in + lead_in + overshoot)
                loft()
            add(bevel_bp.part, mode=Mode.SUBTRACT)

        # 4. 45° snap-retention bead (external ridge for outer_cap, internal groove for inner_plug)
        bead = lid.snap_bead if lid.output != "caddy" else 0.0
        if bead > 0.05 and sleeve_h >= 12.0:
            z_peak = top_z - min(3.5, lid.skirt_depth * 0.45)
            if not use_inner_plug:
                # External 45° triangular snap ridge (100% support-free)
                with BuildPart(mode=Mode.PRIVATE) as bead_bp:
                    with BuildSketch(Plane.XY.offset(z_peak - bead)):
                        _sketch_c_annulus(r_in + 0.3, r_out, opening_deg, min(tip_r, 1.2))
                    with BuildSketch(Plane.XY.offset(z_peak)):
                        _sketch_c_annulus(r_in + 0.3, r_out + bead, opening_deg, min(tip_r, 1.2))
                    with BuildSketch(Plane.XY.offset(z_peak + bead)):
                        _sketch_c_annulus(r_in + 0.3, r_out, opening_deg, min(tip_r, 1.2))
                    loft(ruled=True)
                add(bead_bp.part)
            else:
                # Internal 45° snap groove for inner-plug lid fingers
                g_depth = min(bead * 0.75, wall_t * 0.28)
                with BuildPart(mode=Mode.PRIVATE) as groove_bp:
                    with BuildSketch(Plane.XY.offset(z_peak - g_depth)):
                        Circle(r_in - 0.2)
                    with BuildSketch(Plane.XY.offset(z_peak)):
                        Circle(r_in + g_depth)
                    with BuildSketch(Plane.XY.offset(z_peak + g_depth)):
                        Circle(r_in - 0.2)
                    loft(ruled=True)
                add(groove_bp.part, mode=Mode.SUBTRACT)

    assert sleeve_bp.part is not None, "Failed to generate C-sleeve"
    return sleeve_bp.part


def _cut_wall_window_on_plane(
    cut_plane: Plane,
    cut_depth: float,
    slot_w: float,
    avail_h: float,
    z_bot: float,
    shape: Literal["crowned_arch", "teardrop", "stadium", "hex_truss"],
    rows: int = 2,
) -> None:
    """Subtract vertical slot tier(s) or hex-truss column along ``cut_plane``."""
    if shape == "hex_truss":
        rib_v = 7.0
        n_rows = max(1, min(4, int((avail_h + rib_v) // (slot_w + 8.0 + rib_v))))
        win_h = (avail_h - (n_rows - 1) * rib_v) / n_rows
        peak_h = slot_w / 2.0
        if win_h >= 2.0 * peak_h + 1.5:
            hw = slot_w / 2.0
            hh = win_h / 2.0
            pts = [
                (0.0, -hh),
                (hw, -hh + peak_h),
                (hw, hh - peak_h),
                (0.0, hh),
                (-hw, hh - peak_h),
                (-hw, -hh + peak_h),
            ]
            for r_idx in range(n_rows):
                zc = z_bot + r_idx * (win_h + rib_v) + hh
                with BuildSketch(cut_plane) as sk:
                    with Locations((0.0, zc)):
                        Polygon(*pts, align=None)
                extrude(sk.sketch, amount=cut_depth, mode=Mode.SUBTRACT)
        return

    # Split vertical slots into horizontal stiffening tiers so tall ribs stay rigid
    mid_ring_h = 10.0
    min_tier_h = slot_w + 8.0
    max_fit_rows = max(1, int((avail_h + mid_ring_h) // (min_tier_h + mid_ring_h)))
    n_tiers = max(1, min(rows, max_fit_rows))
    tier_h = (avail_h - (n_tiers - 1) * mid_ring_h) / n_tiers
    for t_idx in range(n_tiers):
        zc = z_bot + t_idx * (tier_h + mid_ring_h) + tier_h / 2.0
        with BuildSketch(cut_plane) as sk:
            _sketch_vertical_slot(slot_w, tier_h, zc, shape)
        extrude(sk.sketch, amount=cut_depth, mode=Mode.SUBTRACT)


def _subtract_sleeve_cutouts(
    stacks: list[_StackSpec],
    sleeve_heights: list[float],
    base_z: float,
    params: RcTireCaddyParams,
) -> None:
    """Subtract configured wall lightening cutouts from the active BuildPart."""
    sup = params.support
    lid = params.lid
    if not sup.wall_cutouts or sup.cutout_count < 1:
        return

    wall_t = sup.wall_thickness
    # Identify adjacent tower pairs that actually share an inner wall
    shared_pairs: list[tuple[int, int]] = []
    shared_angles_per_stack: list[list[float]] = [[] for _ in stacks]
    for i in range(len(stacks)):
        for j in range(i + 1, len(stacks)):
            s1, s2 = stacks[i], stacks[j]
            dist = math.hypot(s2.cx - s1.cx, s2.cy - s1.cy)
            if dist < (s1.well_od / 2.0 + s2.well_od / 2.0 + 2.0 * wall_t + 1.0):
                shared_pairs.append((i, j))
                ang_12 = math.degrees(math.atan2(s2.cy - s1.cy, s2.cx - s1.cx))
                ang_21 = math.degrees(math.atan2(s1.cy - s2.cy, s1.cx - s2.cx))
                # Normalize into [-90, 270) to match C-arc angle range
                if ang_12 < -90.0:
                    ang_12 += 360.0
                if ang_21 < -90.0:
                    ang_21 += 360.0
                shared_angles_per_stack[i].append(ang_12)
                shared_angles_per_stack[j].append(ang_21)

    # 1. Cutouts along each tower's unobstructed outer/back C-arc
    for idx, (stack, sleeve_h) in enumerate(zip(stacks, sleeve_heights)):
        r_in = stack.well_od / 2.0
        gusset = min(sup.root_gusset, sleeve_h * 0.35)
        band_bot = max(gusset + 8.0, 14.0)
        band_top = max(lid.skirt_depth + 6.0, 14.0)
        avail_h = sleeve_h - band_bot - band_top
        if avail_h < 18.0:
            continue

        shared_angs = shared_angles_per_stack[idx]
        if sup.cutout_shared_wall and shared_angs:
            # Anchor uniform spacing directly on the shared-wall angle(s) so the gap
            # next to the shared wall matches the exact pitch of every other cutout!
            jaw_half = sup.opening_angle / 2.0
            min_ang = -90.0 + jaw_half + 22.0
            max_ang = 270.0 - jaw_half - 22.0
            # Clamp C-arc endpoints to any shared wall on the right (~0°) or left (~180°)
            right_shared = [a for a in shared_angs if a < 90.0]
            left_shared = [a for a in shared_angs if a >= 90.0]
            a_start = max(right_shared) if right_shared else min_ang
            a_end = min(left_shared) if left_shared else max_ang

            if sup.cutout_count == 1 or a_end <= a_start + 1.0:
                clear_angles = []
                max_slot_w = sup.cutout_width
            else:
                step = (a_end - a_start) / (sup.cutout_count - 1)
                all_pts = [a_start + k * step for k in range(sup.cutout_count)]
                # Exclude the shared-wall endpoint(s) themselves (cut cleanly below)
                clear_angles = [
                    a for a in all_pts
                    if all(abs(a - sa) > 1.0 for sa in shared_angs)
                ]
                arc_pitch = math.radians(step) * r_in
                max_slot_w = max(4.0, arc_pitch - 4.2)
        else:
            clear_angles, max_slot_w = _compute_clear_cutout_angles(
                stack,
                stacks,
                r_in,
                wall_t,
                sup.opening_angle,
                sup.cutout_count,
                allow_shared_wall=False,
            )

        slot_w = min(sup.cutout_width, max_slot_w, avail_h - 4.0)
        if not clear_angles or slot_w < 4.0:
            continue

        cut_depth = wall_t + 3.0
        for theta in clear_angles:
            rad = math.radians(theta)
            c, s_ang = math.cos(rad), math.sin(rad)
            cut_plane = Plane(
                origin=(stack.cx + (r_in - 1.5) * c, stack.cy + (r_in - 1.5) * s_ang, 0.0),
                x_dir=(-s_ang, c, 0.0),
                z_dir=(c, s_ang, 0.0),
            )
            _cut_wall_window_on_plane(
                cut_plane, cut_depth, slot_w, avail_h, base_z + band_bot, sup.cutout_shape, sup.cutout_rows,
            )

    # 2. Single clean perpendicular cutout dead-center through each shared inner wall
    if sup.cutout_shared_wall:
        for i, j in shared_pairs:
            s1, s2 = stacks[i], stacks[j]
            dx = s2.cx - s1.cx
            dy = s2.cy - s1.cy
            dist = math.hypot(dx, dy)
            if dist < 1e-3:
                continue
            ux, uy = dx / dist, dy / dist
            r1_in = s1.well_od / 2.0
            r2_in = s2.well_od / 2.0
            shared_t = max(wall_t, dist - r1_in - r2_in)
            min_h = min(sleeve_heights[i], sleeve_heights[j])
            gusset = min(sup.root_gusset, min_h * 0.35)
            band_bot = max(gusset + 8.0, 14.0)
            band_top = max(lid.skirt_depth + 6.0, 14.0)
            avail_h = min_h - band_bot - band_top
            if avail_h < 18.0:
                continue

            # Width bounded by the chord of the shared overlap zone so it stays cleanly inside the wall
            min_r = min(r1_in, r2_in)
            slot_w = min(sup.cutout_width, min_r * 0.48, avail_h - 4.0)
            if slot_w < 4.0:
                continue

            # Start 3 mm inside bore 1 and cut straight across perpendicular to the shared wall
            start_d = r1_in - 3.0
            cut_plane = Plane(
                origin=(s1.cx + ux * start_d, s1.cy + uy * start_d, 0.0),
                x_dir=(-uy, ux, 0.0),
                z_dir=(ux, uy, 0.0),
            )
            _cut_wall_window_on_plane(
                cut_plane, shared_t + 6.0, slot_w, avail_h, base_z + band_bot, sup.cutout_shape, sup.cutout_rows,
            )


def _create_outer_cap_lid(
    stacks: list[_StackSpec],
    params: RcTireCaddyParams,
) -> Part:
    """Build a dual-wall snap-on outer cap contoured to equal-height tower(s)."""
    sup = params.support
    lid = params.lid

    bead = lid.snap_bead
    skirt_wall = 2.6 + (0.6 if bead > 0.05 else 0.0)
    cap_top_h = 3.0
    skirt_h = lid.skirt_depth
    inner_extra = sup.wall_thickness + lid.clearance
    outer_extra = inner_extra + skirt_wall
    top_z = cap_top_h + skirt_h

    # Printed upside-down (flat top face on Z=0, outer skirt rising to Z=cap_top_h+skirt_h)
    with BuildPart(mode=Mode.PRIVATE) as cap_bp:
        # 1. Outer solid shell contoured to all towers
        with BuildSketch(Plane.XY):
            _sketch_contoured_footprint(stacks, outer_extra, waist_fillet=5.0)
        extrude(amount=cap_top_h + skirt_h)

        # Bottom perimeter bevel (becomes top edge chamfer when installed)
        bot_edges = cap_bp.faces().sort_by(Axis.Z)[0].edges()
        if bot_edges:
            chamfer(bot_edges, length=0.8)

        # 2. Inner slip-over pocket matching the outer contour of the C-sleeves
        with BuildSketch(Plane.XY.offset(cap_top_h)):
            _sketch_contoured_footprint(stacks, inner_extra, waist_fillet=4.0)
        extrude(amount=skirt_h + 0.5, mode=Mode.SUBTRACT)

        # 3. Matching 45° internal snap-bead pocket groove (100% support-free)
        if bead > 0.05 and skirt_h >= 6.0:
            z_groove = cap_top_h + min(3.5, skirt_h * 0.45)
            g_extra = inner_extra + bead + 0.1
            with BuildPart(mode=Mode.PRIVATE) as groove_bp:
                with BuildSketch(Plane.XY.offset(z_groove - bead - 0.1)):
                    _sketch_contoured_footprint(stacks, inner_extra - 0.2, waist_fillet=4.0)
                with BuildSketch(Plane.XY.offset(z_groove)):
                    _sketch_contoured_footprint(stacks, g_extra, waist_fillet=4.0)
                with BuildSketch(Plane.XY.offset(z_groove + bead + 0.1)):
                    _sketch_contoured_footprint(stacks, inner_extra - 0.2, waist_fillet=4.0)
                loft(ruled=True)
            add(groove_bp.part, mode=Mode.SUBTRACT)

        # 4. 45° internal lead-in chamfer around the skirt mouth for effortless snap-on entry
        lead_in = min(1.5, skirt_wall * 0.45, skirt_h * 0.3)
        if lead_in > 0.15:
            overshoot = 0.2
            with BuildPart(mode=Mode.PRIVATE) as lead_bp:
                with BuildSketch(Plane.XY.offset(top_z - lead_in)):
                    _sketch_contoured_footprint(stacks, inner_extra, waist_fillet=4.0)
                with BuildSketch(Plane.XY.offset(top_z + overshoot)):
                    _sketch_contoured_footprint(stacks, inner_extra + lead_in + overshoot, waist_fillet=4.0)
                loft()
            add(lead_bp.part, mode=Mode.SUBTRACT)

        # 5. Short 4 mm inner anti-warp alignment ring per tower (sandwiches C-sleeve into snap bead)
        if lid.inner_align_lip:
            align_h = min(4.0, skirt_h - 1.5)
            align_wall = 2.0
            for s in stacks:
                r_align_out = s.well_od / 2.0 - max(0.35, lid.clearance + 0.1)
                r_align_in = max(4.0, r_align_out - align_wall)
                with BuildSketch(Plane.XY.offset(cap_top_h - 0.2)):
                    with Locations((s.cx, s.cy)):
                        Circle(r_align_out)
                        Circle(r_align_in, mode=Mode.SUBTRACT)
                extrude(amount=align_h + 0.2)

                # 45° lead-in chamfer on top of inner alignment ring
                a_lead = min(1.0, align_wall * 0.45)
                az_top = cap_top_h + align_h
                with BuildPart(mode=Mode.PRIVATE) as a_bevel:
                    with BuildSketch(Plane.XY.offset(az_top - a_lead)):
                        with Locations((s.cx, s.cy)):
                            Circle(r_align_out + 2.0)
                            Circle(r_align_out, mode=Mode.SUBTRACT)
                    with BuildSketch(Plane.XY.offset(az_top + 0.2)):
                        with Locations((s.cx, s.cy)):
                            Circle(r_align_out + 2.0)
                            Circle(r_align_out - a_lead - 0.2, mode=Mode.SUBTRACT)
                    loft()
                add(a_bevel.part, mode=Mode.SUBTRACT)

        # 6. Optional vertical flexure slots around outer skirt for rigid-filament snap compliance
        if bead > 0.05 and lid.flexure_slots:
            slot_w = 1.6
            slot_z0 = cap_top_h + 1.2
            slot_h = top_z - slot_z0 + 0.5
            for s in stacks:
                r_mid = s.well_od / 2.0 + inner_extra + skirt_wall / 2.0
                for deg in (30.0, 90.0, 150.0, 210.0, 330.0):
                    rad = math.radians(deg)
                    px = s.cx + r_mid * math.cos(rad)
                    py = s.cy + r_mid * math.sin(rad)
                    # Skip slots that would cut into an adjacent tower's waist
                    near_other = any(
                        other is not s
                        and math.hypot(px - other.cx, py - other.cy) < (other.well_od / 2.0 + outer_extra + 3.0)
                        for other in stacks
                    )
                    if near_other:
                        continue
                    with BuildSketch(Plane.XY.offset(slot_z0)):
                        with Locations((px, py)):
                            Rectangle(skirt_wall * 2.5, slot_w, rotation=deg)
                    extrude(amount=slot_h, mode=Mode.SUBTRACT)

    assert cap_bp.part is not None, "Failed to generate outer cap lid"
    return cap_bp.part


def _create_inner_plug_lid_for_well(
    well_od: float,
    params: RcTireCaddyParams,
) -> Part:
    """Build an individual inner-plug press-fit lid with compliant snap fingers."""
    lay = params.layout
    sup = params.support
    lid = params.lid

    well_r = well_od / 2.0
    max_flange = min(sup.wall_thickness - 0.25, lay.shared_wall_thickness / 2.0 - 0.25)
    cap_r = well_r + max(1.2, max_flange)
    cap_h = 3.2
    plug_r_out = well_r - lid.clearance
    plug_wall = 2.4
    plug_r_in = max(4.0, plug_r_out - plug_wall)
    plug_h = lid.skirt_depth
    top_z = cap_h + plug_h

    # Printed upside-down (flat top face on Z=0, plug skirt rising to Z=cap_h+plug_h)
    with BuildPart(mode=Mode.PRIVATE) as lid_bp:
        tab_w = 20.0
        tab_len = 7.0
        with BuildSketch(Plane.XY):
            Circle(cap_r)
            with Locations((0.0, -(cap_r + tab_len * 0.35))):
                RectangleRounded(tab_w, tab_len + 8.0, 3.0)
        extrude(amount=cap_h)

        bot_edges = lid_bp.faces().sort_by(Axis.Z)[0].edges()
        if bot_edges:
            chamfer(bot_edges, length=0.8)

        with BuildSketch(Plane.XY.offset(cap_h - 0.2)):
            Circle(plug_r_out)
            Circle(plug_r_in, mode=Mode.SUBTRACT)
        extrude(amount=plug_h + 0.2)

        # Matching 45° external snap bump on the compliant plug fingers
        if lid.snap_bead > 0.05 and plug_h >= 5.5:
            b_h = min(lid.snap_bead * 0.65, 0.6)
            z_bump = cap_h + min(3.5, plug_h * 0.45)
            with BuildPart(mode=Mode.PRIVATE) as bump_bp:
                with BuildSketch(Plane.XY.offset(z_bump - b_h)):
                    Circle(plug_r_out)
                    Circle(plug_r_in, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.XY.offset(z_bump)):
                    Circle(plug_r_out + b_h)
                    Circle(plug_r_in, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.XY.offset(z_bump + b_h)):
                    Circle(plug_r_out)
                    Circle(plug_r_in, mode=Mode.SUBTRACT)
                loft(ruled=True)
            add(bump_bp.part)

        lead_in = min(1.4, plug_wall * 0.55, plug_h * 0.3)
        if lead_in > 0.15:
            overshoot = 0.2
            with BuildPart(mode=Mode.PRIVATE) as plug_bevel:
                with BuildSketch(Plane.XY.offset(top_z - lead_in)):
                    Circle(plug_r_out + 2.0)
                    Circle(plug_r_out, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.XY.offset(top_z + overshoot)):
                    Circle(plug_r_out + 2.0)
                    Circle(plug_r_out - lead_in - overshoot, mode=Mode.SUBTRACT)
                loft()
            add(plug_bevel.part, mode=Mode.SUBTRACT)

        slot_w = 1.8
        slot_h = max(3.0, plug_h - 1.2)
        for deg in (0.0, 90.0, 180.0, 270.0):
            with BuildSketch(Plane.XY.offset(top_z - slot_h)):
                with Locations((0.0, 0.0)):
                    Rectangle(2.0 * (plug_r_out + 3.0), slot_w, rotation=deg)
            extrude(amount=slot_h + 1.0, mode=Mode.SUBTRACT)

    assert lid_bp.part is not None, "Failed to generate inner-plug lid"
    return lid_bp.part


def _create_top_retention_cap(params: RcTireCaddyParams) -> Part:
    """Build a 3-lobe scalloped M4/M5 retention knob that fits inside a 2.2\" wheel dish."""
    sup = params.support
    rod_d, nut_af, nut_depth = ROD_SPECS[sup.support_style]
    hole_r = (rod_d + sup.rod_clearance) / 2.0

    cap_h = max(12.0, nut_depth + 8.0)
    core_r = 12.0
    lobe_offset = 6.5
    lobe_r = 7.2
    chamfer_len = 1.0

    with BuildPart(mode=Mode.PRIVATE) as cap_bp:
        with BuildSketch(Plane.XY):
            Circle(core_r)
            with PolarLocations(radius=lobe_offset, count=3):
                Circle(lobe_r)
            fillet(vertices(), radius=2.5)
        extrude(amount=cap_h)

        outer_top = cap_bp.faces().sort_by(Axis.Z)[-1].edges()
        outer_bot = cap_bp.faces().sort_by(Axis.Z)[0].edges()
        chamfer(outer_top, length=chamfer_len)
        chamfer(outer_bot, length=chamfer_len)

        with BuildSketch(Plane.XY):
            Circle(hole_r)
        extrude(amount=cap_h + 1.0, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(cap_h)):
            RegularPolygon(radius=nut_af / math.sqrt(3.0), side_count=6)
        extrude(amount=-nut_depth, mode=Mode.SUBTRACT)

    assert cap_bp.part is not None, "Failed to generate top retention cap"
    return cap_bp.part


def _create_spindle_post(
    post_d: float,
    stack_h: float,
    base_z: float,
    clip_hole: bool,
    clip_hole_d: float,
) -> Part:
    """Build a single integral vertical center spindle post with tapered tip and optional R-clip hole."""
    post_r = post_d / 2.0
    tip_h = min(5.0, max(2.0, post_d * 0.8))
    tip_top_r = min(post_r * 0.45, 1.0)
    clip_margin_above_stack = 2.5
    clip_min_below_tip = max(4.5, clip_hole_d * 2.2)

    if clip_hole:
        clip_z = base_z + stack_h + clip_margin_above_stack
        cyl_top_z = clip_z + clip_min_below_tip
    else:
        clip_z = 0.0
        cyl_top_z = base_z + stack_h

    tip_top_z = cyl_top_z + tip_h
    cyl_h = cyl_top_z - base_z

    with BuildPart(mode=Mode.PRIVATE) as post_bp:
        with BuildSketch(Plane.XY.offset(base_z - 0.5)):
            Circle(post_r)
        extrude(amount=cyl_h + 0.5)

        with BuildSketch(Plane.XY.offset(cyl_top_z)):
            Circle(post_r)
        with BuildSketch(Plane.XY.offset(tip_top_z)):
            Circle(tip_top_r)
        loft()

        if clip_hole and clip_hole_d > 0.0:
            hole_r = min(clip_hole_d / 2.0, post_r * 0.72)
            with BuildSketch(Plane.XZ.offset(-post_r - 1.0)):
                with Locations((0.0, clip_z)):
                    Circle(hole_r)
            extrude(amount=2.0 * (post_r + 1.0), mode=Mode.SUBTRACT)

    assert post_bp.part is not None, "Failed to generate spindle post"
    return post_bp.part


def _build_caddy_body(
    params: RcTireCaddyParams,
    stacks: list[_StackSpec],
    outer_x: float,
    outer_y: float,
    gx: int,
    gy: int,
    pad_extra_r: float,
) -> Part:
    """Build the main caddy body solid."""
    sup = params.support
    lid = params.lid
    gf = params.gridfinity_base
    bp = params.base
    tf = params.test_fit

    use_gridfinity = (gf is not None) and not tf.enabled
    is_sleeve = sup.support_style == "c_sleeve"
    use_inner_plug = _uses_inner_plug_lid(params, stacks)
    inner_plug_headroom = lid.skirt_depth if (not tf.enabled and use_inner_plug) else 0.0

    base_z = GRIDFINITY_FOOT_HEIGHT if use_gridfinity else 0.0
    rim_h = 0.0 if (tf.enabled or is_sleeve) else bp.rim_height
    floor_top_z = base_z + bp.base_thickness
    rim_top_z = floor_top_z + rim_h

    with BuildPart() as caddy:
        # 1. Optional Gridfinity modular base feet (z = 0 -> 4.75 mm)
        if use_gridfinity and gf is not None:
            add(create_gridfinity_base(gf, grid_x=gx, grid_y=gy))

        # 2. Main base slab: Gridfinity rectangle OR form-fitting contoured circles
        with BuildSketch(Plane.XY.offset(base_z)):
            if use_gridfinity:
                _rounded_rect(outer_x, outer_y, GRIDFINITY_CORNER_RADIUS)
            elif tf.enabled:
                Circle(outer_x / 2.0)
            else:
                _sketch_contoured_footprint(stacks, pad_extra_r, waist_fillet=5.0)
        extrude(amount=bp.base_thickness + rim_h)

        # 3. Anti-elephant's-foot bottom perimeter chamfer (flat/contoured base only)
        if not use_gridfinity and bp.bottom_chamfer > 0.0:
            bot_chamfer = min(bp.bottom_chamfer, bp.base_thickness * 0.4)
            if bot_chamfer > 0.05:
                bot_edges = caddy.faces().sort_by(Axis.Z)[0].edges()
                if bot_edges:
                    chamfer(bot_edges, length=bot_chamfer)

        # 4. Recessed circular tire wells (center-rod modes with rim_height > 0)
        if rim_h > 0.05:
            lead_in = min(1.2, rim_h * 0.4)
            for s in stacks:
                well_r = s.well_od / 2.0
                with BuildSketch(Plane.XY.offset(floor_top_z)):
                    with Locations((s.cx, s.cy)):
                        Circle(well_r)
                extrude(amount=rim_h + 0.5, mode=Mode.SUBTRACT)

                if lead_in > 0.05:
                    overshoot = 0.2
                    with BuildPart(mode=Mode.PRIVATE) as well_bevel:
                        with BuildSketch(Plane.XY.offset(rim_top_z - lead_in)):
                            with Locations((s.cx, s.cy)):
                                Circle(well_r)
                        with BuildSketch(Plane.XY.offset(rim_top_z + overshoot)):
                            with Locations((s.cx, s.cy)):
                                Circle(well_r + lead_in + overshoot)
                        loft()
                    add(well_bevel.part, mode=Mode.SUBTRACT)

        # 5. Optional 12 mm wheel-hex centering bosses at each stack floor
        hex_top_z = floor_top_z
        if sup.hex_seat and sup.hex_seat_height > 0.0:
            hex_circum_r = sup.hex_flat_size / math.sqrt(3.0)
            hex_chamfer = min(0.6, sup.hex_seat_height * 0.25)
            hex_top_z = floor_top_z + sup.hex_seat_height
            for s in stacks:
                with BuildPart(mode=Mode.PRIVATE) as hex_bp:
                    with BuildSketch(Plane.XY.offset(floor_top_z - 0.5)):
                        with Locations((s.cx, s.cy)):
                            RegularPolygon(radius=hex_circum_r, side_count=6)
                    extrude(amount=sup.hex_seat_height + 0.5)
                    if hex_chamfer > 0.05:
                        top_e = hex_bp.faces().sort_by(Axis.Z)[-1].edges()
                        if top_e:
                            chamfer(top_e, length=hex_chamfer)
                add(hex_bp.part)

        # 6. Tire support structure: C-sleeve, printed post, or M4/M5 threaded rod
        if is_sleeve:
            sleeve_heights: list[float] = []
            max_sleeve_h = 0.0
            for s in stacks:
                sh = tf.height if tf.enabled else max(24.0, s.stack_height * sup.height_ratio + inner_plug_headroom)
                sleeve_heights.append(sh)
                max_sleeve_h = max(max_sleeve_h, sh)
                sleeve_solid = _create_c_sleeve(
                    stack=s,
                    sleeve_h=sh,
                    base_z=floor_top_z,
                    sup=sup,
                    lid=lid,
                    use_inner_plug=use_inner_plug,
                )
                add(Pos(s.cx, s.cy, 0.0) * sleeve_solid)

            if len(stacks) > 1:
                for s in stacks:
                    with BuildSketch(Plane.XY.offset(floor_top_z)):
                        with Locations((s.cx, s.cy)):
                            Circle(s.well_od / 2.0)
                    extrude(amount=max_sleeve_h + 1.0, mode=Mode.SUBTRACT)

            # Subtract lightening cutouts after unioning sleeves so shared-wall cutouts punch cleanly through
            _subtract_sleeve_cutouts(stacks, sleeve_heights, floor_top_z, params)
        elif sup.support_style == "printed_post":
            for s in stacks:
                post_solid = _create_spindle_post(
                    post_d=sup.post_diameter,
                    stack_h=s.stack_height,
                    base_z=floor_top_z,
                    clip_hole=sup.clip_hole,
                    clip_hole_d=sup.clip_hole_diameter,
                )
                add(Pos(s.cx, s.cy, 0.0) * post_solid)
        else:
            rod_d, nut_af, nut_depth = ROD_SPECS[sup.support_style]
            hole_r = (rod_d + sup.rod_clearance) / 2.0
            eff_nut_depth = min(nut_depth, max(2.0, bp.base_thickness - 2.0))
            nut_top_z = base_z + eff_nut_depth
            nut_circum_r = nut_af / math.sqrt(3.0)

            for s in stacks:
                with BuildSketch(Plane.XY.offset(-0.5)):
                    with Locations((s.cx, s.cy)):
                        Circle(hole_r)
                extrude(amount=hex_top_z + 1.5, mode=Mode.SUBTRACT)

                with BuildSketch(Plane.XY.offset(-0.5)):
                    with Locations((s.cx, s.cy)):
                        RegularPolygon(radius=nut_circum_r, side_count=6)
                extrude(amount=nut_top_z + 0.5, mode=Mode.SUBTRACT)

    assert caddy.part is not None, "Failed to generate RC tire caddy"
    return caddy.part


def create_rc_tire_caddy(params: RcTireCaddyParams) -> Part | Compound:
    """Build the RC Tire Storage Caddy, lid/knob only, or combined multi-part plate."""
    sup = params.support
    lid = params.lid
    tf = params.test_fit

    stacks, outer_x, outer_y, gx, gy, pad_extra_r = _resolve_layout(params)
    use_inner_plug = _uses_inner_plug_lid(params, stacks)

    # Lid / retention knob only
    if not tf.enabled and lid.output == "lid":
        if sup.support_style == "c_sleeve":
            if not use_inner_plug:
                return _create_outer_cap_lid(stacks, params)
            rear_od, _, front_od, _ = resolve_tire_dimensions(params.tire)
            if params.layout.arrangement == "fronts_only" or (
                params.layout.arrangement == "by_axle" and lid.lid_target == "front"
            ):
                well_od = front_od + params.tire.radial_clearance
            else:
                well_od = rear_od + params.tire.radial_clearance
            return _create_inner_plug_lid_for_well(well_od, params)
        if sup.support_style in ROD_SPECS:
            return _create_top_retention_cap(params)

    caddy_body = _build_caddy_body(params, stacks, outer_x, outer_y, gx, gy, pad_extra_r)

    wants_both = (lid.output == "both") and (sup.support_style in ("c_sleeve", "m4_rod", "m5_rod"))
    if not wants_both:
        return caddy_body

    caddy_bb = caddy_body.bounding_box()
    parts: list[Shape] = [caddy_body]

    if sup.support_style == "c_sleeve":
        if not use_inner_plug:
            # Single unified outer-skirt cap laid out cleanly in front of the caddy (-Y)
            outer_cap = _create_outer_cap_lid(stacks, params)
            cbb = outer_cap.bounding_box()
            ly = caddy_bb.min.Y - lid.bed_gap - cbb.max.Y
            parts.append(Pos(0.0, ly, 0.0) * outer_cap)
        else:
            # Individual inner-plug lids laid out in front of the caddy (-Y)
            lids = [_create_inner_plug_lid_for_well(s.well_od, params) for s in stacks]
            lid_widths = [p.bounding_box().size.X for p in lids]
            gap = max(6.0, lid.bed_gap * 0.75)
            total_w = sum(lid_widths) + (len(lids) - 1) * gap
            x_cur = -total_w / 2.0
            for lid_part, lw in zip(lids, lid_widths):
                lbb = lid_part.bounding_box()
                lx = x_cur + lw / 2.0
                ly = caddy_bb.min.Y - lid.bed_gap - lbb.max.Y
                parts.append(Pos(lx, ly, 0.0) * lid_part)
                x_cur += lw + gap
    else:
        knob_proto = _create_top_retention_cap(params)
        kbb = knob_proto.bounding_box()
        kw = kbb.size.X
        gap = max(8.0, lid.bed_gap * 0.75)
        total_w = len(stacks) * kw + (len(stacks) - 1) * gap
        x_cur = -total_w / 2.0
        for _ in stacks:
            kx = x_cur + kw / 2.0
            ky = caddy_bb.min.Y - lid.bed_gap - kbb.max.Y
            parts.append(Pos(kx, ky, 0.0) * knob_proto)
            x_cur += kw + gap

    return Compound(children=parts)


def export_filename(params: RcTireCaddyParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    tire = params.tire
    lay = params.layout
    sup = params.support
    lid = params.lid
    gf = params.gridfinity_base
    tf = params.test_fit

    profile_tag = {
        "buggy_2wd_carpet_slim": "2wd_carpet",
        "buggy_2wd_carpet_wide": "2wd_wide",
        "buggy_4wd_carpet": "4wd_carpet",
        "buggy_2wd_dirt": "2wd_dirt",
        "stadium_truck": "st_truck",
        "custom": f"custom_{tire.rear_od:g}x{tire.rear_width:g}mm",
    }[tire.tire_profile]

    if tf.enabled:
        suffix = f"_with_{lid.style}" if (lid.output == "both" and sup.support_style == "c_sleeve") else ""
        return f"rc_tire_caddy_{profile_tag}_{sup.support_style}_test_fit{suffix}"

    if lid.output == "lid":
        if sup.support_style == "c_sleeve":
            if lid.style == "outer_cap":
                return f"rc_tire_caddy_{profile_tag}_outer_cap_lid"
            size_tag = (
                "front"
                if (lay.arrangement == "fronts_only" or (lay.arrangement == "by_axle" and lid.lid_target == "front"))
                else "rear"
            )
            return f"rc_tire_caddy_{profile_tag}_{size_tag}_inner_plug_lid"
        if sup.support_style in ROD_SPECS:
            return f"rc_tire_caddy_{sup.support_style}_top_knob"

    if lay.arrangement == "per_set":
        cap_tag = f"{lay.sets}sets"
    elif lay.arrangement == "by_axle":
        cap_tag = f"{lay.sets}sets_axle"
    elif lay.arrangement == "rears_only":
        cap_tag = f"{lay.stacks}x{lay.tires_per_stack}rears"
    else:
        cap_tag = f"{lay.stacks}x{lay.tires_per_stack}fronts"

    style_tag = sup.support_style
    if gf is not None:
        _, _, _, gx, gy, _ = _resolve_layout(params)
        base_tag = f"gf{gx}x{gy}"
    else:
        base_tag = "contoured"

    both_tag = "_with_lid" if (lid.output == "both" and sup.support_style in ("c_sleeve", "m4_rod", "m5_rod")) else ""
    return f"rc_tire_caddy_{profile_tag}_{cap_tag}_{style_tag}_{base_tag}{both_tag}"


if __name__ == "__main__":
    from utils.runner import run_model

    params = RcTireCaddyParams()
    part = create_rc_tire_caddy(params)
    run_model(part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
