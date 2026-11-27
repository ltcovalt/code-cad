"""
Parametric Gridfinity Bin with Pred-Compatible Printable Label Holder (build123d)

A modular, component-based parametric Gridfinity bin generator built with build123d.
Each major geometric feature is implemented as a standalone component function and
composed cleanly in `create_gridfinity_bin(params)`:

1. `create_base_feet(params)`           - Standard Gridfinity 3-stage feet + magnet/screw holes
2. `create_bin_body(params)`            - Outer shell, solid angled drawer-spacer overhangs, and tapered compartments
3. `create_stacking_lip(params)`        - Complete, continuous concentric top stacking rim
4. `create_compartment_scoops(params)`  - True circular finger-scoop ramps (adapts to vertical & overhanging walls)
5. `create_label_holders(params)`       - Pred-compatible horizontal label shelves with recessed
                                          snap-in label sockets, side-tab notches, and bridged support fins
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional
from build123d import *

try:
    from utils.params import group, param
except ImportError:
    import sys

    for _p in Path(__file__).resolve().parents:
        if (_p / "utils").is_dir():
            sys.path.insert(0, str(_p))
            break
    from utils.params import group, param

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False     # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False    # Save .step to repo-root exports/ (default: False)


@dataclass
class CoreParams:
    """Grid units, pitch, walls, floor, and corner radius."""

    grid_x: int = param(
        2,
        label="Grid X (Width)",
        desc="Number of grid units along X",
        min=1, max=8, step=1,
    )
    grid_y: int = param(
        2,
        label="Grid Y (Depth)",
        desc="Number of grid units along Y",
        min=1, max=8, step=1,
    )
    grid_z: int = param(
        6,
        label="Grid Z (Height)",
        desc="Number of 7 mm height units along Z",
        min=2, max=12, step=1,
    )
    unit_size: float = param(
        42.0,
        desc="Base XY grid pitch (standard Gridfinity = 42)",
        unit="mm",
    )
    unit_z: float = param(
        7.0,
        label="Z Unit Pitch",
        desc="Vertical height unit pitch (standard = 7)",
        unit="mm",
    )
    grid_clearance: float = param(
        0.5,
        desc="Total XY clearance gap between adjacent bins",
        unit="mm",
    )
    wall_thickness: float = param(
        1.2,
        desc="Exterior wall thickness",
        unit="mm", min=0.8, max=4.0, step=0.2,
    )
    floor_thickness: float = param(
        2.0,
        desc="Solid floor thickness above base feet",
        unit="mm", min=1.0, max=6.0, step=0.2,
    )
    corner_radius: float = param(
        3.75,
        desc="Outer vertical corner radius",
        unit="mm", min=1.0, max=8.0, step=0.25,
    )


@dataclass
class MagnetHolesParams:
    """Base foot corner magnet pockets."""

    enabled: bool = param(
        False,
        desc="Cut 4 corner pockets per foot cell (6×2 mm magnets)",
    )
    diameter: float = param(
        6.1,
        desc="Magnet pocket diameter",
        unit="mm",
    )
    depth: float = param(
        2.2,
        desc="Magnet pocket depth",
        unit="mm",
    )
    offset: float = param(
        13.0,
        desc="Distance from foot cell center to magnet centers",
        unit="mm",
    )


@dataclass
class ScrewHolesParams:
    """Base foot M3 mounting screw through-holes."""

    enabled: bool = param(
        False,
        desc="Cut through-holes for M3 mounting screws",
    )
    diameter: float = param(
        3.2,
        desc="Through-hole diameter",
        unit="mm",
    )


@dataclass
class StackingLipParams:
    """Continuous top stacking rim."""

    enabled: bool = param(
        True,
        desc="Add continuous top stacking rim",
    )
    height: float = param(
        3.8,
        desc="Stacking lip height above body",
        unit="mm",
    )
    top_flat: float = param(
        0.6,
        desc="Flat top rim width (prevents fragile knife-edge)",
        unit="mm",
    )


@dataclass
class LabelHolderParams:
    """Pred-compatible printable label holder shelf & recessed socket."""

    enabled: bool = param(
        True,
        desc="Add printable label shelf & recessed socket",
    )
    shelf_full_width: bool = param(
        False,
        desc="Span shelf full compartment width instead of sizing to label",
    )
    placement: Literal["center", "left", "right", "per_column"] = param(
        "center",
        desc="Label placement along X",
    )
    units: int = param(
        1,
        desc="Label width in grid units (clamped to Grid X)",
        min=1, max=6, step=1, when={"placement": ["center", "left", "right"]},
    )
    column: Optional[int] = param(
        None,
        desc="1-indexed column start (overrides left/center/right)",
        min=1, max=8, step=1, when={"placement": ["center", "left", "right"]},
    )
    wall: Literal["back", "front"] = param(
        "back",
        desc="Compartment wall for label shelf",
    )
    height: float = param(
        11.5,
        desc="Label plate depth (Y)",
        unit="mm",
    )
    thickness: float = param(
        1.0,
        desc="Recessed pocket & tab slot height (Z)",
        unit="mm",
    )
    shelf_depth: float = param(
        13.5,
        desc="Inward depth (Y) of supporting shelf overhang",
        unit="mm",
    )
    shelf_thickness: float = param(
        2.4,
        desc="Vertical thickness of shelf deck",
        unit="mm",
    )
    fin_count: Optional[int] = param(
        None,
        desc="Manual support fin count per compartment (Auto = calculated)",
        min=0, max=12, step=1,
    )
    fin_max_span: float = param(
        12.0,
        desc="Max unsupported bridge span when fin count is Auto",
        unit="mm", min=4.0, max=30.0, step=1.0, when={"fin_count": None},
    )
    fin_thickness: float = param(
        0.8,
        desc="Thickness of each support fin",
        unit="mm",
    )
    overhang_angle: float = param(
        35.0,
        desc="Support fin angle underneath label shelf",
        unit="°",
    )
    width_margin: float = param(
        5.6,
        desc="Margin subtracted from unit width for pocket",
        unit="mm",
    )
    tab_width: float = param(
        6.5,
        desc="Width (Y) of side snap-in retention tab slots",
        unit="mm",
    )
    tab_extension: float = param(
        0.8,
        desc="Extension (X) of side retention tab notches per side",
        unit="mm",
    )


@dataclass
class ScoopParams:
    """Ergonomic compartment finger scoops."""

    enabled: bool = param(
        True,
        desc="Enable interior finger scoops",
    )
    style: Literal["directional", "bowl"] = param(
        "directional",
        desc="Per-wall scoops or 360° dish bottom",
    )
    bowl_radius: float = param(
        8.0,
        desc="All-around floor fillet radius",
        unit="mm", min=0.0, max=25.0, step=0.5, when={"style": "bowl"},
    )
    front_radius: float = param(
        12.0,
        desc="Front (-Y) finger scoop radius (0 = off)",
        unit="mm", min=0.0, max=25.0, step=0.5, when={"style": "directional"},
    )
    back_radius: float = param(
        6.0,
        desc="Back (+Y) finger scoop radius (0 = off)",
        unit="mm", min=0.0, max=25.0, step=0.5, when={"style": "directional"},
    )
    left_radius: float = param(
        0.0,
        desc="Left (-X) finger scoop radius (0 = off)",
        unit="mm", min=0.0, max=25.0, step=0.5, when={"style": "directional"},
    )
    right_radius: float = param(
        0.0,
        desc="Right (+X) finger scoop radius (0 = off)",
        unit="mm", min=0.0, max=25.0, step=0.5, when={"style": "directional"},
    )


@dataclass
class DividersParams:
    """Interior compartment dividing walls."""

    enabled: bool = param(
        False,
        desc="Add interior dividing walls",
    )
    x: int = param(
        1,
        label="X Dividers",
        desc="Divider walls along X (0 = undivided)",
        min=0, max=6, step=1,
    )
    y: int = param(
        0,
        label="Y Dividers",
        desc="Divider walls along Y (0 = undivided)",
        min=0, max=6, step=1,
    )
    thickness: float = param(
        1.2,
        desc="Dividing wall thickness",
        unit="mm", min=0.8, max=3.0, step=0.2,
    )


@dataclass
class OverhangParams:
    """Drawer spacer gap overhangs (fills dead space above baseplate padding)."""

    enabled: bool = param(
        False,
        desc="Extend upper body over drawer spacer gaps",
    )
    front: float = param(
        0.0,
        desc="Extension past front (-Y) grid boundary",
        unit="mm", min=0.0, max=40.0, step=0.5,
    )
    back: float = param(
        0.0,
        desc="Extension past back (+Y) grid boundary",
        unit="mm", min=0.0, max=40.0, step=0.5,
    )
    left: float = param(
        0.0,
        desc="Extension past left (-X) grid boundary",
        unit="mm", min=0.0, max=40.0, step=0.5,
    )
    right: float = param(
        0.0,
        desc="Extension past right (+X) grid boundary",
        unit="mm", min=0.0, max=40.0, step=0.5,
    )
    chamfer_angle: float = param(
        45.0,
        desc="Print-safe underside transition angle",
        unit="°", min=30.0, max=65.0, step=1.0,
    )


@dataclass
class GridfinityBinParams:
    """Single source of truth parameters for the parametric Gridfinity bin."""

    core: CoreParams = group(CoreParams)
    magnets: MagnetHolesParams = group(MagnetHolesParams)
    screws: ScrewHolesParams = group(ScrewHolesParams)
    stacking_lip: StackingLipParams = group(StackingLipParams)
    label: LabelHolderParams = group(LabelHolderParams, label="Label Holder")
    scoop: ScoopParams = group(ScoopParams)
    dividers: DividersParams = group(DividersParams)
    overhang: OverhangParams = group(OverhangParams)


# ==============================================================================
# Helper: Derived Envelope & Overhang Taper Geometry
# ==============================================================================
@dataclass
class _BinEnvelope:
    """Internal pre-calculated envelope dimensions shared across components."""
    gx: int
    gy: int
    gz: int
    pitch_xy: float
    pitch_z: float
    foot_h: float
    body_h: float
    floor_z: float
    z_trans: float
    has_overhang: bool
    ov_f: float
    ov_b: float
    ov_l: float
    ov_r: float
    base_w: float
    base_l: float
    top_w: float
    top_l: float
    top_cx: float
    top_cy: float
    r_corner: float
    # Inner cavity dimensions at top (z >= z_trans)
    inner_w: float
    inner_l: float
    r_inner: float
    # Inner cavity dimensions at floor level (z = floor_z)
    floor_inner_w: float
    floor_inner_l: float
    floor_inner_cx: float
    floor_inner_cy: float
    floor_x_left: float
    floor_x_right: float
    floor_y_front: float
    floor_y_back: float
    top_x_left: float
    top_x_right: float
    top_y_front: float
    top_y_back: float
    # Compartment grid at top
    comp_w: float
    comp_l: float
    cx_count: int
    cy_count: int


def _compute_envelope(params: GridfinityBinParams) -> _BinEnvelope:
    """Computes derived dimensions for the bin, overhangs, and compartments."""
    c = params.core
    ov = params.overhang
    div = params.dividers

    gx = max(1, c.grid_x)
    gy = max(1, c.grid_y)
    gz = max(1, c.grid_z)
    pitch_xy = c.unit_size
    pitch_z = c.unit_z
    clr = c.grid_clearance

    foot_h = 4.75
    body_h = gz * pitch_z
    floor_z = foot_h + c.floor_thickness

    base_w = gx * pitch_xy - clr
    base_l = gy * pitch_xy - clr

    if ov.enabled:
        ov_f = max(0.0, ov.front)
        ov_b = max(0.0, ov.back)
        ov_l = max(0.0, ov.left)
        ov_r = max(0.0, ov.right)
    else:
        ov_f = ov_b = ov_l = ov_r = 0.0
    max_ov = max(ov_f, ov_b, ov_l, ov_r)
    has_overhang = max_ov > 0.0

    if has_overhang:
        angle_rad = math.radians(max(15.0, min(75.0, ov.chamfer_angle)))
        chamfer_rise = max_ov * math.tan(angle_rad)
        z_trans = min(body_h - 0.5, foot_h + chamfer_rise)
    else:
        z_trans = foot_h

    x_min = -base_w / 2.0 - ov_l
    x_max = base_w / 2.0 + ov_r
    y_min = -base_l / 2.0 - ov_f
    y_max = base_l / 2.0 + ov_b

    top_w = x_max - x_min
    top_l = y_max - y_min
    top_cx = (x_min + x_max) / 2.0
    top_cy = (y_min + y_max) / 2.0

    r_corner = max(0.5, min(c.corner_radius, min(base_w, base_l) / 2.0 - 0.1))

    t_wall = c.wall_thickness
    t_div = div.thickness
    if div.enabled:
        cx_count = max(0, div.x) + 1
        cy_count = max(0, div.y) + 1
    else:
        cx_count = 1
        cy_count = 1

    inner_w = top_w - 2.0 * t_wall
    inner_l = top_l - 2.0 * t_wall
    comp_w = (inner_w - (cx_count - 1) * t_div) / cx_count
    comp_l = (inner_l - (cy_count - 1) * t_div) / cy_count
    r_inner = max(0.5, min(r_corner - t_wall, min(comp_w, comp_l) / 2.0 - 0.1))

    top_x_left = top_cx - inner_w / 2.0
    top_x_right = top_cx + inner_w / 2.0
    top_y_front = top_cy - inner_l / 2.0
    top_y_back = top_cy + inner_l / 2.0

    # Compute inner cavity bounds at z = floor_z so sloped overhang walls stay solid with thickness >= t_wall
    if has_overhang and z_trans > floor_z:
        dz = z_trans - foot_h
        tau_floor = (floor_z - foot_h) / dz

        # Outer bounds at z = floor_z
        out_x_min_fl = -base_w / 2.0 - tau_floor * ov_l
        out_x_max_fl = base_w / 2.0 + tau_floor * ov_r
        out_y_min_fl = -base_l / 2.0 - tau_floor * ov_f
        out_y_max_fl = base_l / 2.0 + tau_floor * ov_b

        # Horizontal inset needed on each sloped side to maintain perpendicular thickness t_wall
        inset_l = t_wall * math.sqrt(1.0 + (ov_l / dz) ** 2)
        inset_r = t_wall * math.sqrt(1.0 + (ov_r / dz) ** 2)
        inset_f = t_wall * math.sqrt(1.0 + (ov_f / dz) ** 2)
        inset_b = t_wall * math.sqrt(1.0 + (ov_b / dz) ** 2)

        floor_x_left = out_x_min_fl + inset_l
        floor_x_right = out_x_max_fl - inset_r
        floor_y_front = out_y_min_fl + inset_f
        floor_y_back = out_y_max_fl - inset_b

        floor_inner_w = max(4.0, floor_x_right - floor_x_left)
        floor_inner_l = max(4.0, floor_y_back - floor_y_front)
        floor_inner_cx = (floor_x_left + floor_x_right) / 2.0
        floor_inner_cy = (floor_y_front + floor_y_back) / 2.0
    else:
        floor_inner_w = inner_w
        floor_inner_l = inner_l
        floor_inner_cx = top_cx
        floor_inner_cy = top_cy
        floor_x_left = top_x_left
        floor_x_right = top_x_right
        floor_y_front = top_y_front
        floor_y_back = top_y_back

    return _BinEnvelope(
        gx=gx,
        gy=gy,
        gz=gz,
        pitch_xy=pitch_xy,
        pitch_z=pitch_z,
        foot_h=foot_h,
        body_h=body_h,
        floor_z=floor_z,
        z_trans=z_trans,
        has_overhang=has_overhang,
        ov_f=ov_f,
        ov_b=ov_b,
        ov_l=ov_l,
        ov_r=ov_r,
        base_w=base_w,
        base_l=base_l,
        top_w=top_w,
        top_l=top_l,
        top_cx=top_cx,
        top_cy=top_cy,
        r_corner=r_corner,
        inner_w=inner_w,
        inner_l=inner_l,
        r_inner=r_inner,
        floor_inner_w=floor_inner_w,
        floor_inner_l=floor_inner_l,
        floor_inner_cx=floor_inner_cx,
        floor_inner_cy=floor_inner_cy,
        floor_x_left=floor_x_left,
        floor_x_right=floor_x_right,
        floor_y_front=floor_y_front,
        floor_y_back=floor_y_back,
        top_x_left=top_x_left,
        top_x_right=top_x_right,
        top_y_front=top_y_front,
        top_y_back=top_y_back,
        comp_w=comp_w,
        comp_l=comp_l,
        cx_count=cx_count,
        cy_count=cy_count,
    )


def _create_tapered_inner_envelope(env: _BinEnvelope) -> Part:
    """
    Builds the overall interior cavity solid (from z = floor_z to z = body_h)
    that tapers inward along any angled overhang walls so exterior walls remain
    100% solid with full perpendicular wall thickness.
    """
    r_fl = max(0.5, min(env.r_inner, min(env.floor_inner_w, env.floor_inner_l) / 2.0 - 0.1))

    with BuildPart() as cav_builder:
        if env.has_overhang and env.z_trans > env.floor_z:
            with BuildSketch(Plane.XY.offset(env.floor_z)) as sk_fl:
                with Locations([(env.floor_inner_cx, env.floor_inner_cy)]):
                    RectangleRounded(env.floor_inner_w, env.floor_inner_l, r_fl)
            with BuildSketch(Plane.XY.offset(env.z_trans)) as sk_tr:
                with Locations([(env.top_cx, env.top_cy)]):
                    RectangleRounded(env.inner_w, env.inner_l, env.r_inner)
            loft(ruled=True)

            if env.body_h > env.z_trans:
                with BuildSketch(Plane.XY.offset(env.z_trans)) as sk_up:
                    with Locations([(env.top_cx, env.top_cy)]):
                        RectangleRounded(env.inner_w, env.inner_l, env.r_inner)
                extrude(amount=env.body_h - env.z_trans)
        else:
            with BuildSketch(Plane.XY.offset(env.floor_z)) as sk_full:
                with Locations([(env.top_cx, env.top_cy)]):
                    RectangleRounded(env.inner_w, env.inner_l, env.r_inner)
            extrude(amount=env.body_h - env.floor_z)

    return cav_builder.part


# ==============================================================================
# Component 1: Standard Gridfinity Base Feet
# ==============================================================================
def create_base_feet(params: GridfinityBinParams) -> Part:
    """
    Generates the N x M array of standard 3-stage Gridfinity base feet (z = 0 to 4.75mm),
    including optional magnet pockets and M3 countersink/through holes.
    """
    env = _compute_envelope(params)
    unit_w = env.pitch_xy - params.core.grid_clearance  # 41.5mm standard

    # Build a single canonical foot centered at (0, 0)
    with BuildPart() as single_foot:
        # 3-stage ruled loft:
        #   z=0.00 -> z=0.80: 45° bottom chamfer (inset 2.95mm -> 2.15mm)
        #   z=0.80 -> z=2.60: vertical step (inset 2.15mm, height 1.8mm)
        #   z=2.60 -> z=4.75: 45° upper chamfer (inset 2.15mm -> 0.0mm)
        r_top = env.r_corner
        r_mid = max(0.3, r_top - 2.15)
        r_bot = max(0.2, r_top - 2.95)

        with BuildSketch(Plane.XY) as sk0:
            RectangleRounded(unit_w - 2.0 * 2.95, unit_w - 2.0 * 2.95, r_bot)
        with BuildSketch(Plane.XY.offset(0.8)) as sk1:
            RectangleRounded(unit_w - 2.0 * 2.15, unit_w - 2.0 * 2.15, r_mid)
        with BuildSketch(Plane.XY.offset(2.6)) as sk2:
            RectangleRounded(unit_w - 2.0 * 2.15, unit_w - 2.0 * 2.15, r_mid)
        with BuildSketch(Plane.XY.offset(env.foot_h)) as sk3:
            RectangleRounded(unit_w, unit_w, r_top)
        loft(ruled=True)

        # Optional corner magnet pockets and screw holes
        if params.magnets.enabled or params.screws.enabled:
            mo = params.magnets.offset
            hole_locs = [(-mo, -mo), (mo, -mo), (-mo, mo), (mo, mo)]

            if params.magnets.enabled and params.magnets.depth > 0:
                with BuildSketch(Plane.XY) as mag_sk:
                    with Locations(hole_locs):
                        Circle(params.magnets.diameter / 2.0)
                extrude(amount=params.magnets.depth, mode=Mode.SUBTRACT)

            if params.screws.enabled:
                with BuildSketch(Plane.XY) as screw_sk:
                    with Locations(hole_locs):
                        Circle(params.screws.diameter / 2.0)
                extrude(amount=env.foot_h, mode=Mode.SUBTRACT)

    foot_template = single_foot.part

    # Array the foot across the grid_x * grid_y footprint
    with BuildPart() as feet_builder:
        placed_feet = []
        for ix in range(env.gx):
            for iy in range(env.gy):
                cx = (ix - (env.gx - 1) / 2.0) * env.pitch_xy
                cy = (iy - (env.gy - 1) / 2.0) * env.pitch_xy
                placed_feet.append(foot_template.moved(Location((cx, cy, 0))))
        add(placed_feet)

    return feet_builder.part


# ==============================================================================
# Component 2: Main Bin Body, Overhangs & Interior Compartments
# ==============================================================================
def create_bin_body(params: GridfinityBinParams) -> Part:
    """
    Generates the main bin body from z = 4.75mm up to z = grid_z * unit_z,
    including solid angled drawer-spacer overhangs and subdivided interior compartments.
    """
    env = _compute_envelope(params)

    with BuildPart() as body_builder:
        # 1. Outer solid body (from foot_h up to body_h)
        if not env.has_overhang:
            with BuildSketch(Plane.XY.offset(env.foot_h)) as sk_body:
                RectangleRounded(env.base_w, env.base_l, env.r_corner)
            extrude(amount=env.body_h - env.foot_h)
        else:
            with BuildSketch(Plane.XY.offset(env.foot_h)) as sk_base:
                RectangleRounded(env.base_w, env.base_l, env.r_corner)
            with BuildSketch(Plane.XY.offset(env.z_trans)) as sk_trans:
                with Locations([(env.top_cx, env.top_cy)]):
                    RectangleRounded(env.top_w, env.top_l, env.r_corner)
            loft(ruled=True)

            if env.body_h > env.z_trans:
                with BuildSketch(Plane.XY.offset(env.z_trans)) as sk_upper:
                    with Locations([(env.top_cx, env.top_cy)]):
                        RectangleRounded(env.top_w, env.top_l, env.r_corner)
                extrude(amount=env.body_h - env.z_trans)

        # 2. Subtract subdivided interior compartments (clipped to the tapered inner envelope)
        t_div = params.dividers.thickness
        cavity_h = env.body_h - env.floor_z
        if cavity_h > 0:
            inner_env_part = _create_tapered_inner_envelope(env)

            if env.cx_count == 1 and env.cy_count == 1:
                add(inner_env_part, mode=Mode.SUBTRACT)
            else:
                with BuildPart() as prisms_builder:
                    with BuildSketch(Plane.XY.offset(env.floor_z)) as comp_sk:
                        locs = []
                        for icx in range(env.cx_count):
                            for icy in range(env.cy_count):
                                ccx = (
                                    env.top_cx
                                    - env.inner_w / 2.0
                                    + env.comp_w / 2.0
                                    + icx * (env.comp_w + t_div)
                                )
                                ccy = (
                                    env.top_cy
                                    - env.inner_l / 2.0
                                    + env.comp_l / 2.0
                                    + icy * (env.comp_l + t_div)
                                )
                                locs.append((ccx, ccy))
                        with Locations(locs):
                            RectangleRounded(env.comp_w, env.comp_l, env.r_inner)
                    extrude(amount=cavity_h)
                    add(inner_env_part, mode=Mode.INTERSECT)

                add(prisms_builder.part, mode=Mode.SUBTRACT)

        # 3. If a label pocket spans across an interior X-divider (e.g. full_width or center_1u),
        #    recess the top of the X-divider for the label socket while keeping the divider
        #    wall underneath as structural support for the shelf deck.
        if params.label.enabled:
            slot_cutout = _create_label_slot_cutouts(params, env)
            if slot_cutout is not None:
                add(slot_cutout, mode=Mode.SUBTRACT)

    return body_builder.part


# ==============================================================================
# Component 3: Complete Concentric Top Stacking Lip
# ==============================================================================
def create_stacking_lip(params: GridfinityBinParams) -> Optional[Part]:
    """
    Generates the continuous Gridfinity stacking lip around the entire top perimeter.

    Constructed as an outer perimeter prism minus a multi-stage ruled inner loft so
    the lip remains 100% valid and self-intersection-free at any corner radius
    (including tight radii smaller than the 2.6 mm lip depth).
    """
    if not params.stacking_lip.enabled:
        return None

    env = _compute_envelope(params)
    t_wall = params.core.wall_thickness
    lip_depth = 2.6
    support_h = max(0.2, lip_depth - t_wall)

    lip_h = max(2.6, params.stacking_lip.height)
    top_flat = max(0.4, min(1.2, params.stacking_lip.top_flat))

    z_bot = max(env.floor_z, env.body_h - support_h)
    z0 = env.body_h
    z1 = env.body_h + 0.7
    z2 = env.body_h + 2.5
    z3 = env.body_h + lip_h

    inner_stages = [
        (z_bot, t_wall),
        (z0, lip_depth),
        (z1, 1.9),
        (z2, 1.9),
        (z3, top_flat),
    ]

    with BuildPart() as inner_cut:
        for z_stage, inset in inner_stages:
            w_s = max(1.0, env.top_w - 2.0 * inset)
            l_s = max(1.0, env.top_l - 2.0 * inset)
            r_s = max(0.2, min(env.r_corner - inset, min(w_s, l_s) / 2.0 - 0.1))
            with BuildSketch(Plane.XY.offset(z_stage)):
                with Locations([(env.top_cx, env.top_cy)]):
                    RectangleRounded(w_s, l_s, r_s)
        loft(ruled=True)

    with BuildPart() as lip_builder:
        with BuildSketch(Plane.XY.offset(z_bot)):
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(env.top_w, env.top_l, env.r_corner)
        extrude(amount=z3 - z_bot)
        add(inner_cut.part, mode=Mode.SUBTRACT)

        # Clear out label pocket & side tab slots from the lower support bevel (z < z0)
        # so the stacking lip's 45° underside bevel never pinches the vertical tab slot height
        if params.label.enabled:
            slot_cutout = _create_label_slot_cutouts(params, env)
            if slot_cutout is not None:
                add(slot_cutout, mode=Mode.SUBTRACT)

    return lip_builder.part


# ==============================================================================
# Component 4: Ergonomic Compartment Finger Scoops
# ==============================================================================
def create_compartment_scoops(params: GridfinityBinParams) -> Optional[Part]:
    """
    Generates ergonomic compartment finger scoops in one of two styles:
      - `scoop.style == "bowl"`: 360° all-around floor fillet of radius `scoop.bowl_radius`.
      - `scoop.style == "directional"`: Independent circular tangent finger-scoop ramps on any
        combination of front (-Y), back (+Y), left (-X), and right (+X) (0.0 to disable).

    Automatically adapts to both vertical walls (90° corner) and angled overhang walls,
    clipping strictly to the tapered interior cavity so a scoop never protrudes outside.
    """
    if not params.scoop.enabled:
        return None

    env = _compute_envelope(params)
    cavity_h = env.body_h - env.floor_z
    if cavity_h <= 1.0:
        return None

    t_div = params.dividers.thickness
    inner_env_part = _create_tapered_inner_envelope(env)
    scoop_solids = []

    if params.scoop.style == "bowl":
        req_bowl_r = max(0.0, params.scoop.bowl_radius)
        if req_bowl_r <= 0.5:
            return None

        for icx in range(env.cx_count):
            for icy in range(env.cy_count):
                ccx = (
                    env.top_cx
                    - env.inner_w / 2.0
                    + env.comp_w / 2.0
                    + icx * (env.comp_w + t_div)
                )
                ccy = (
                    env.top_cy
                    - env.inner_l / 2.0
                    + env.comp_l / 2.0
                    + icy * (env.comp_l + t_div)
                )

                comp_x_left_top = ccx - env.comp_w / 2.0
                comp_x_right_top = ccx + env.comp_w / 2.0
                comp_y_front_top = ccy - env.comp_l / 2.0
                comp_y_back_top = ccy + env.comp_l / 2.0

                comp_x_left_fl = env.floor_x_left if icx == 0 else comp_x_left_top
                comp_x_right_fl = (
                    env.floor_x_right if icx == env.cx_count - 1 else comp_x_right_top
                )
                comp_y_front_fl = env.floor_y_front if icy == 0 else comp_y_front_top
                comp_y_back_fl = (
                    env.floor_y_back if icy == env.cy_count - 1 else comp_y_back_top
                )

                comp_fl_w = comp_x_right_fl - comp_x_left_fl
                comp_fl_l = comp_y_back_fl - comp_y_front_fl
                if min(comp_fl_w, comp_fl_l) <= 2.5:
                    continue

                r_bowl = min(
                    req_bowl_r,
                    min(comp_fl_w, comp_fl_l) * 0.42,
                    cavity_h * 0.75,
                )
                if r_bowl <= 0.5:
                    continue

                # Build the unfilleted lower compartment prism (clipped to tapered inner envelope)
                prism_h = min(cavity_h, r_bowl + 2.0)
                with BuildPart() as unfilleted_cav:
                    with BuildSketch(Plane.XY.offset(env.floor_z)) as sk_c:
                        with Locations([(ccx, ccy)]):
                            RectangleRounded(env.comp_w, env.comp_l, env.r_inner)
                    extrude(amount=prism_h)
                    add(inner_env_part, mode=Mode.INTERSECT)

                # Build the 360° bottom-filleted cavity and subtract from unfilleted prism
                with BuildPart() as filleted_cav:
                    add(unfilleted_cav.part)
                    bot_edges = filleted_cav.faces().sort_by(Axis.Z)[0].edges()
                    fillet(bot_edges, radius=r_bowl)

                with BuildPart() as bowl_scoop:
                    add(unfilleted_cav.part)
                    add(filleted_cav.part, mode=Mode.SUBTRACT)

                scoop_solids.append(bowl_scoop.part)

        if not scoop_solids:
            return None
        with BuildPart() as all_bowl_scoops:
            add(scoop_solids)
        return all_bowl_scoops.part

    # Directional mode: independent front (-Y), back (+Y), left (-X), right (+X) scoops
    r_front = max(0.0, params.scoop.front_radius)
    r_back = max(0.0, params.scoop.back_radius)
    r_left = max(0.0, params.scoop.left_radius)
    r_right = max(0.0, params.scoop.right_radius)
    if r_front <= 0.0 and r_back <= 0.0 and r_left <= 0.0 and r_right <= 0.0:
        return None

    active_y_scoops: list[tuple[Literal["front", "back"], float]] = []
    if r_front > 0.0:
        active_y_scoops.append(("front", r_front))
    if r_back > 0.0:
        active_y_scoops.append(("back", r_back))

    active_x_scoops: list[tuple[Literal["left", "right"], float]] = []
    if r_left > 0.0:
        active_x_scoops.append(("left", r_left))
    if r_right > 0.0:
        active_x_scoops.append(("right", r_right))

    max_y_frac = 0.45 if len(active_y_scoops) == 2 else 0.65
    max_x_frac = 0.45 if len(active_x_scoops) == 2 else 0.65

    for icx in range(env.cx_count):
        for icy in range(env.cy_count):
            ccx = (
                env.top_cx
                - env.inner_w / 2.0
                + env.comp_w / 2.0
                + icx * (env.comp_w + t_div)
            )
            ccy = (
                env.top_cy
                - env.inner_l / 2.0
                + env.comp_l / 2.0
                + icy * (env.comp_l + t_div)
            )

            comp_x_left_top = ccx - env.comp_w / 2.0
            comp_x_right_top = ccx + env.comp_w / 2.0
            comp_y_front_top = ccy - env.comp_l / 2.0
            comp_y_back_top = ccy + env.comp_l / 2.0

            comp_x_left_floor = env.floor_x_left if icx == 0 else comp_x_left_top
            comp_x_right_floor = (
                env.floor_x_right if icx == env.cx_count - 1 else comp_x_right_top
            )
            comp_y_front_floor = env.floor_y_front if icy == 0 else comp_y_front_top
            comp_y_back_floor = (
                env.floor_y_back if icy == env.cy_count - 1 else comp_y_back_top
            )

            comp_floor_w = comp_x_right_floor - comp_x_left_floor
            comp_floor_l = comp_y_back_floor - comp_y_front_floor
            if comp_floor_w <= 2.0 or comp_floor_l <= 2.0:
                continue

            def _build_directional_scoop(
                axis: Literal["y", "x"],
                s: float,
                wall_corner: float,
                d_slope: float,
                comp_floor_span: float,
                max_frac: float,
                req_radius: float,
            ) -> Optional[Part]:
                if d_slope > 1e-4 and env.z_trans > env.floor_z:
                    dz_slope = env.z_trans - env.floor_z
                    alpha = math.atan2(dz_slope, d_slope)
                    wall_seg_len = math.hypot(d_slope, dz_slope)
                else:
                    alpha = math.pi / 2.0
                    wall_seg_len = cavity_h - 1.0

                tan_half = math.tan(alpha / 2.0)
                if tan_half <= 1e-4:
                    return None

                max_tan_len = min(comp_floor_span * max_frac, wall_seg_len * 0.95)
                sr = min(req_radius, max_tan_len / tan_half)
                if sr <= 0.5:
                    return None

                # Avoid exact equal-radius Steinmetz singularity where the horizontal
                # scoop cylinder meets the vertical compartment corner cylinder (r_inner).
                l_tan = sr * tan_half
                if abs(sr - env.r_inner) < 1e-3 or abs(l_tan - env.r_inner) < 1e-3:
                    sr -= 1e-3
                    if sr <= 0.5:
                        return None
                    l_tan = sr * tan_half

                scoop_h = l_tan * math.sin(alpha)
                if scoop_h <= 1e-3:
                    return None

                c_arc = wall_corner + s * l_tan
                cz_arc = env.floor_z + sr
                wall_top = wall_corner - s * l_tan * math.cos(alpha)
                z_top = env.floor_z + scoop_h
                pad = 1.0

                if axis == "y":
                    prof_plane = Plane(origin=(ccx, 0.0, 0.0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
                    half_ext = env.comp_w / 2.0 + pad
                else:
                    prof_plane = Plane(origin=(0.0, ccy, 0.0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
                    half_ext = env.comp_l / 2.0 + pad

                # Build the scoop by clipping the rounded compartment prism with a planar
                # bounding wedge and subtracting the exact tangent fillet cylinder. This
                # avoids OCCT boolean failures on coplanar knife-edge cylinder intersections.
                with BuildPart() as comp_scoop:
                    with BuildSketch(Plane.XY.offset(env.floor_z)):
                        with Locations([(ccx, ccy)]):
                            RectangleRounded(env.comp_w, env.comp_l, env.r_inner)
                    extrude(amount=scoop_h)

                    with BuildSketch(prof_plane):
                        Polygon(
                            (wall_corner - s * pad, env.floor_z - pad),
                            (c_arc, env.floor_z - pad),
                            (c_arc, z_top + pad),
                            (wall_top - s * pad, z_top + pad),
                            align=None,
                        )
                    extrude(amount=half_ext, both=True, mode=Mode.INTERSECT)

                    with BuildSketch(prof_plane):
                        with Locations([(c_arc, cz_arc)]):
                            Circle(sr)
                    extrude(amount=half_ext, both=True, mode=Mode.SUBTRACT)

                    if env.has_overhang and env.z_trans > env.floor_z:
                        add(inner_env_part, mode=Mode.INTERSECT)

                return comp_scoop.part

            # Front (-Y) and Back (+Y) scoops extruded in YZ plane along X
            for wall_side, req_radius in active_y_scoops:
                if wall_side == "front":
                    s = 1.0  # Interior is in +Y direction from front wall
                    y_corner = comp_y_front_floor
                    dy_slope = max(0.0, comp_y_front_floor - comp_y_front_top)
                else:
                    s = -1.0  # Interior is in -Y direction from back wall
                    y_corner = comp_y_back_floor
                    dy_slope = max(0.0, comp_y_back_top - comp_y_back_floor)

                part = _build_directional_scoop(
                    "y", s, y_corner, dy_slope, comp_floor_l, max_y_frac, req_radius
                )
                if part is not None:
                    scoop_solids.append(part)

            # Left (-X) and Right (+X) scoops extruded in XZ plane along Y
            for wall_side, req_radius in active_x_scoops:
                if wall_side == "left":
                    s = 1.0  # Interior is in +X direction from left wall
                    x_corner = comp_x_left_floor
                    dx_slope = max(0.0, comp_x_left_floor - comp_x_left_top)
                else:
                    s = -1.0  # Interior is in -X direction from right wall
                    x_corner = comp_x_right_floor
                    dx_slope = max(0.0, comp_x_right_top - comp_x_right_floor)

                part = _build_directional_scoop(
                    "x", s, x_corner, dx_slope, comp_floor_w, max_x_frac, req_radius
                )
                if part is not None:
                    scoop_solids.append(part)

    if not scoop_solids:
        return None

    with BuildPart() as all_scoops:
        add(scoop_solids)

    return all_scoops.part


# ==============================================================================
# Component 5: Printable Label Holder (Bridged Support Fins & Sized Shelf Decks)
# ==============================================================================
def _compute_label_pocket_specs(
    params: GridfinityBinParams, env: _BinEnvelope
) -> list[tuple[float, float, int]]:
    """
    Computes (center_x, pocket_width, units) for each label pocket along X.
    """
    lbl = params.label
    units = max(1, min(env.gx, lbl.units))
    unit_pw = max(8.0, units * env.pitch_xy - lbl.width_margin)
    t_div = params.dividers.thickness

    specs: list[tuple[float, float, int]] = []

    if lbl.placement == "per_column":
        pw = max(8.0, env.pitch_xy - lbl.width_margin)
        for ix in range(env.gx):
            scx = env.top_cx + (ix - (env.gx - 1) / 2.0) * env.pitch_xy
            specs.append((scx, pw, 1))
    else:  # "center" (default), "left", "right", or column specified
        if lbl.column is not None:
            start_col = max(1, min(env.gx - units + 1, lbl.column))
            col_offset = (start_col - 1) + (units - 1) / 2.0
            scx = env.top_cx + (col_offset - (env.gx - 1) / 2.0) * env.pitch_xy
        elif lbl.placement == "left":
            col_offset = (units - 1) / 2.0
            scx = env.top_cx + (col_offset - (env.gx - 1) / 2.0) * env.pitch_xy
        elif lbl.placement == "right":
            col_offset = (env.gx - units) + (units - 1) / 2.0
            scx = env.top_cx + (col_offset - (env.gx - 1) / 2.0) * env.pitch_xy
        else:  # "center"
            scx = env.top_cx
        specs.append((scx, unit_pw, units))

    return specs


def _compute_label_shelf_intervals(
    params: GridfinityBinParams,
    env: _BinEnvelope,
    specs: list[tuple[float, float, int]],
) -> list[tuple[float, float]]:
    """
    Computes X-span intervals [x_min, x_max] for the horizontal shelf deck.
    If label.shelf_full_width is True, spans the entire row width.
    If False, sizes each shelf segment to the label pocket (U * pitch_xy - 2 * wall_thickness).
    """
    row_x_min = env.top_cx - env.inner_w / 2.0
    row_x_max = env.top_cx + env.inner_w / 2.0

    if params.label.shelf_full_width:
        return [(row_x_min, row_x_max)]

    raw_intervals: list[tuple[float, float]] = []
    for scx, pw, u in specs:
        deck_w = u * env.pitch_xy - 2.0 * params.core.wall_thickness
        deck_w = max(pw + 2.0 * params.label.tab_extension + 1.0, deck_w)
        x0 = max(row_x_min, scx - deck_w / 2.0)
        x1 = min(row_x_max, scx + deck_w / 2.0)
        raw_intervals.append((x0, x1))

    raw_intervals.sort()
    merged: list[tuple[float, float]] = []
    for x0, x1 in raw_intervals:
        if not merged:
            merged.append((x0, x1))
        else:
            prev_x0, prev_x1 = merged[-1]
            if x0 <= prev_x1 + 1.0:
                merged[-1] = (prev_x0, max(prev_x1, x1))
            else:
                merged.append((x0, x1))

    return merged


def _create_label_slot_cutouts(
    params: GridfinityBinParams, env: _BinEnvelope
) -> Optional[Part]:
    """
    Builds the two-tier negative cutout solid for all label pockets and undercut
    side snap-tab slots:
      - Main label window (`sw x lh`): open through the top surface (z = body_h) down to
        the pocket floor (z = body_h - (roof_t + label_thickness)).
      - Side tab slots (`(sw + 2 * tab_ext) x tab_w`): cut as horizontal undercuts from
        the pocket floor up to z = body_h - roof_t, leaving a 0.6mm overhanging retention
        roof flush with z = body_h above every left and right tab (both outer and inner).
    Shared across `create_label_holders`, `create_bin_body`, and `create_stacking_lip`.
    """
    lbl = params.label
    if not lbl.enabled or lbl.thickness <= 0:
        return None

    shelf_d = min(lbl.shelf_depth, env.comp_l * 0.75)
    if shelf_d <= 4.0:
        return None

    t_div = params.dividers.thickness
    z_top = env.body_h
    roof_t = 0.6  # Overhanging retention roof thickness above side tab slots (flush with z_top)
    slot_h = lbl.thickness
    total_recess = roof_t + slot_h

    lh = min(lbl.height, shelf_d - 1.5)
    tab_w = min(lbl.tab_width, lh - 1.0)
    tab_ext = lbl.tab_extension

    specs = _compute_label_pocket_specs(params, env)
    pocket_x_specs = [(scx, pw) for scx, pw, _ in specs]

    y_pocket_centers: list[float] = []
    for icy in range(env.cy_count):
        ccy = (
            env.top_cy
            - env.inner_l / 2.0
            + env.comp_l / 2.0
            + icy * (env.comp_l + t_div)
        )
        if lbl.wall == "back":
            y_wall = ccy + env.comp_l / 2.0
            y_pocket_centers.append(y_wall - shelf_d / 2.0)
        else:
            y_wall = ccy - env.comp_l / 2.0
            y_pocket_centers.append(y_wall + shelf_d / 2.0)

    with BuildPart() as cutout_builder:
        # Tier 1: Main label window open through top surface (z_top down to z_top - total_recess)
        with BuildSketch(Plane.XY.offset(z_top)) as sk_window:
            for y_pc in y_pocket_centers:
                for scx, sw in pocket_x_specs:
                    with Locations([(scx, y_pc)]):
                        RectangleRounded(sw, lh, min(1.0, lh / 4.0))
        extrude(amount=-total_recess)

        # Tier 2: Undercut side snap-tab slots beneath the 0.6mm retention roof
        if tab_ext > 0 and tab_w > 0:
            with BuildSketch(Plane.XY.offset(z_top - roof_t)) as sk_tabs:
                for y_pc in y_pocket_centers:
                    for scx, sw in pocket_x_specs:
                        with Locations([(scx, y_pc)]):
                            RectangleRounded(
                                sw + 2.0 * tab_ext, tab_w, min(0.25, tab_w / 8.0)
                            )
            extrude(amount=-slot_h)

    return cutout_builder.part


def create_label_holders(params: GridfinityBinParams) -> Optional[Part]:
    """
    Generates the printable label holder shelf and recessed snap-in socket:
    - Horizontal shelf deck at z = body_h (sized to the label pocket when
      label_shelf_full_width is False, or full row width when True).
    - Support fins underneath the shelf deck, including automatic outer boundary
      fins at any open edge not touching a wall or divider.
    - Recessed pocket on top of the shelf matching standard 3D-printable labels
      with self-contained undercut side-tab slots and a 0.6mm top retention roof.
    """
    lbl = params.label
    if not lbl.enabled:
        return None

    env = _compute_envelope(params)
    t_div = params.dividers.thickness
    shelf_d = min(lbl.shelf_depth, env.comp_l * 0.75)
    if shelf_d <= 4.0:
        return None

    roof_t = 0.6
    recess_total = lbl.thickness + roof_t
    deck_t = max(recess_total + 0.8, lbl.shelf_thickness)
    angle_rad = math.radians(max(25.0, min(65.0, lbl.overhang_angle)))
    fin_drop_h = shelf_d * math.tan(angle_rad)

    # Top of the label shelf aligns with z = body_h
    z_top = env.body_h
    z_deck_bot = z_top - deck_t
    z_fin_bot = max(env.floor_z, z_deck_bot - fin_drop_h)
    ledge_h = min(0.8, max(0.0, z_deck_bot - env.floor_z))
    fin_tip_h = min(0.8, max(0.0, (z_deck_bot - z_fin_bot) * 0.5))
    fin_t = max(0.8, lbl.fin_thickness)
    max_span = max(2.0, lbl.fin_max_span)

    inner_env_part = _create_tapered_inner_envelope(env)
    shelf_solids = []

    specs = _compute_label_pocket_specs(params, env)
    intervals = _compute_label_shelf_intervals(params, env, specs)

    row_x_min = env.top_cx - env.inner_w / 2.0
    row_x_max = env.top_cx + env.inner_w / 2.0

    # Interior divider boundary positions along X
    divider_x_locs: list[float] = []
    if env.cx_count > 1:
        for icx in range(1, env.cx_count):
            x_div = row_x_min + icx * env.comp_w + (icx - 0.5) * t_div
            divider_x_locs.append(x_div)

    def is_adjacent_to_wall_or_divider(x_val: float) -> bool:
        if abs(x_val - row_x_min) < 1.0 or abs(x_val - row_x_max) < 1.0:
            return True
        for x_div in divider_x_locs:
            if abs(x_val - x_div) < (t_div / 2.0 + 1.0):
                return True
        return False

    for icy in range(env.cy_count):
        ccy = (
            env.top_cy
            - env.inner_l / 2.0
            + env.comp_l / 2.0
            + icy * (env.comp_l + t_div)
        )

        if lbl.wall == "back":
            y_wall = ccy + env.comp_l / 2.0
            y_tip = y_wall - shelf_d
            s_y = -1.0
        else:
            y_wall = ccy - env.comp_l / 2.0
            y_tip = y_wall + shelf_d
            s_y = 1.0

        for x0, x1 in intervals:
            deck_span = x1 - x0
            deck_cx = (x0 + x1) / 2.0

            # 1. Horizontal shelf deck
            with BuildPart() as comp_deck:
                with BuildSketch(Plane.YZ.offset(deck_cx)) as sk_deck:
                    Polygon(
                        (y_wall, z_top),
                        (y_tip, z_top),
                        (y_tip, z_deck_bot),
                        (y_wall, z_deck_bot),
                        align=None,
                    )
                extrude(amount=deck_span / 2.0, both=True)
                add(inner_env_part, mode=Mode.INTERSECT)
            shelf_solids.append(comp_deck.part)

            # 2. Wall-support ledges (under shelf deck at exterior walls)
            if ledge_h > 0.2:
                # Back wall ledge along the shelf interval
                with BuildPart() as b_ledge:
                    with BuildSketch(Plane.YZ.offset(deck_cx)) as sk_bl:
                        Polygon(
                            (y_wall, z_deck_bot),
                            (y_wall + s_y * ledge_h, z_deck_bot),
                            (y_wall, z_deck_bot - ledge_h),
                            align=None,
                        )
                    extrude(amount=deck_span / 2.0, both=True)
                    add(inner_env_part, mode=Mode.INTERSECT)
                shelf_solids.append(b_ledge.part)

                # Left side wall ledge if x0 touches left exterior wall
                if abs(x0 - row_x_min) < 1.0:
                    with BuildPart() as l_ledge:
                        with BuildSketch(Plane.XZ.offset(ccy)) as sk_ll:
                            Polygon(
                                (row_x_min, z_deck_bot),
                                (row_x_min + ledge_h, z_deck_bot),
                                (row_x_min, z_deck_bot - ledge_h),
                                align=None,
                            )
                        extrude(amount=env.comp_l / 2.0, both=True)
                        add(inner_env_part, mode=Mode.INTERSECT)
                    shelf_solids.append(l_ledge.part)

                # Right side wall ledge if x1 touches right exterior wall
                if abs(x1 - row_x_max) < 1.0:
                    with BuildPart() as r_ledge:
                        with BuildSketch(Plane.XZ.offset(ccy)) as sk_rl:
                            Polygon(
                                (row_x_max, z_deck_bot),
                                (row_x_max - ledge_h, z_deck_bot),
                                (row_x_max, z_deck_bot - ledge_h),
                                align=None,
                            )
                        extrude(amount=env.comp_l / 2.0, both=True)
                        add(inner_env_part, mode=Mode.INTERSECT)
                    shelf_solids.append(r_ledge.part)

            # 3. Support fins (including outer boundary fins at open edges)
            left_open = not is_adjacent_to_wall_or_divider(x0)
            right_open = not is_adjacent_to_wall_or_divider(x1)

            fin_positions: list[float] = []
            if left_open:
                fin_positions.append(x0 + fin_t / 2.0)
            if right_open:
                fin_positions.append(x1 - fin_t / 2.0)

            x_anchor_left = (x0 + fin_t / 2.0) if left_open else x0
            x_anchor_right = (x1 - fin_t / 2.0) if right_open else x1
            inner_span = x_anchor_right - x_anchor_left

            if inner_span > 2.0:
                if lbl.fin_count is not None:
                    n_inter = max(0, lbl.fin_count)
                else:
                    n_inter = max(0, math.ceil(inner_span / max_span) - 1)

                if n_inter > 0:
                    step = inner_span / (n_inter + 1)
                    for i in range(1, n_inter + 1):
                        fin_positions.append(x_anchor_left + i * step)

            # Build all fins for this interval
            for fx in fin_positions:
                with BuildPart() as fin_part:
                    with BuildSketch(Plane.YZ.offset(fx)) as sk_fin:
                        Polygon(
                            (y_wall, z_deck_bot),
                            (y_tip, z_deck_bot),
                            (y_tip, z_deck_bot - fin_tip_h),
                            (y_wall, z_fin_bot),
                            align=None,
                        )
                    extrude(amount=fin_t / 2.0, both=True)
                    add(inner_env_part, mode=Mode.INTERSECT)
                shelf_solids.append(fin_part.part)

    with BuildPart() as label_builder:
        add(shelf_solids)
        cutouts = _create_label_slot_cutouts(params, env)
        if cutouts is not None:
            add(cutouts, mode=Mode.SUBTRACT)

    return label_builder.part


# ==============================================================================
# Top-Level Generator: Compose All Standalone Components
# ==============================================================================
def create_gridfinity_bin(params: GridfinityBinParams) -> Part:
    """
    Decoupled generator function for parametric Gridfinity bins with Pred label compatibility.

    Composes standalone feature components:
      1. Base Feet (`create_base_feet`)
      2. Main Bin Body & Compartments (`create_bin_body`)
      3. Compartment Finger Scoops (`create_compartment_scoops`)
      4. Pred Printable Label Holders (`create_label_holders`)
      5. Continuous Top Stacking Lip (`create_stacking_lip`)
    """
    feet = create_base_feet(params)
    body = create_bin_body(params)
    scoops = create_compartment_scoops(params)
    labels = create_label_holders(params)
    lip = create_stacking_lip(params)

    parts = [p for p in (feet, body, scoops, labels, lip) if p is not None]
    solids = []
    for p in parts:
        solids.extend(p.solids())
    if len(solids) == 1:
        return Part(children=[solids[0]])
    fused = solids[0].fuse(*solids[1:])
    return fused if isinstance(fused, Part) else Part(children=[fused])


def export_filename(params: GridfinityBinParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    dims = f"{params.core.grid_x}x{params.core.grid_y}x{params.core.grid_z}u"
    if params.label.enabled:
        if params.label.column is not None:
            placement_str = f"col{params.label.column}_{params.label.units}u"
        elif params.label.placement in ("left", "center", "right"):
            placement_str = f"{params.label.placement}_{params.label.units}u"
        else:
            placement_str = params.label.placement
        label_tag = f"label_{placement_str}"
    else:
        label_tag = "standard"
    return f"gridfinity_bin_{dims}_{label_tag}"


# ==============================================================================
# Model Execution & Export
# ==============================================================================
if __name__ == "__main__":
    from utils.runner import run_model

    # Instantiate default parameters directly from dataclass definitions
    params = GridfinityBinParams()
    part = create_gridfinity_bin(params)
    run_model(part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
