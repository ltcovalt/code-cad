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
    from ocp_viewer import set_defaults, show
    set_defaults(orbit_control=True)
except ImportError:
    try:
        from ocp_vscode import set_defaults, show
        set_defaults(orbit_control=True)
    except ImportError:
        def show(*args, **kwargs):
            pass

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False      # Save .stl file on execution (default: False)
EXPORT_STEP: bool = False     # Save .step file on execution (default: False)
OUTPUT_DIR: str = "exports"   # Relative subfolder alongside this script


@dataclass
class GridfinityBinParams:
    """Single source of truth parameters for the parametric Gridfinity bin."""

    # --------------------------------------------------------------------------
    # Grid Units & Pitch
    # --------------------------------------------------------------------------
    grid_x: int = 2                     # Number of grid units along X (width)
    grid_y: int = 2                     # Number of grid units along Y (length/depth)
    grid_z: int = 4                     # Number of height units along Z
    unit_size: float = 42.0             # Base XY grid pitch in mm (standard Gridfinity = 42.0mm)
    unit_z: float = 7.0                 # Height Z unit pitch in mm (standard Gridfinity = 7.0mm)
    grid_clearance: float = 0.5         # Total XY clearance gap between bins in mm (0.25mm per side)

    # --------------------------------------------------------------------------
    # Bin Walls, Floor & Corners
    # --------------------------------------------------------------------------
    wall_thickness: float = 1.2         # Exterior wall thickness in mm (3 perimeters w/ 0.4mm nozzle)
    floor_thickness: float = 2.0        # Solid floor thickness above the 4.75mm base feet in mm
    corner_radius: float = 3.75         # Outer vertical corner radius in mm (4.0mm grid R - 0.25mm inset)

    # --------------------------------------------------------------------------
    # Base Foot & Hardware Mounting
    # --------------------------------------------------------------------------
    magnet_holes: bool = False           # If True, cuts 4 corner pockets per foot cell for 6x2mm magnets
    magnet_diameter: float = 6.5        # Magnet pocket diameter in mm
    magnet_depth: float = 2.4           # Magnet pocket depth in mm
    magnet_offset: float = 13.0         # Distance from unit cell center to magnet centers (26mm spacing)
    screw_holes: bool = False           # If True, cuts through-holes for M3 mounting screws
    screw_diameter: float = 3.2         # Through-hole diameter in mm

    # --------------------------------------------------------------------------
    # Top Stacking Lip
    # --------------------------------------------------------------------------
    stackable: bool = True              # If True, adds standard continuous top stacking rim
    lip_height: float = 3.8             # Printable stacking lip height above body_h in mm (standard 3.8mm)
    lip_top_flat: float = 0.6           # Width of flat top rim edge in mm (prevents fragile knife-edge)

    # --------------------------------------------------------------------------
    # Pred-Compatible Printable Label Holder
    # --------------------------------------------------------------------------
    label_enabled: bool = True          # If True, adds Pred-style printable label shelf & recessed socket
    label_wall: Literal["back", "front"] = "back"  # Wall inside compartment where label shelf is mounted
    label_style: Literal["per_column", "full_width"] = "per_column"  # Slot per X column or full width
    label_height: float = 11.5          # Label plate depth (Y) in mm (fits ~11.3mm Pred label)
    label_thickness: float = 1.0        # Recessed pocket & tab slot height (Z) in mm (fits ~0.87mm tab)
    label_shelf_depth: float = 13.5     # Total inward depth (Y) of the supporting shelf overhang in mm
    label_shelf_thickness: float = 1.8  # Vertical thickness of the horizontal shelf deck in mm
    label_fin_count: Optional[int] = None  # Manual fin count override per compartment (None = auto-calculate)
    label_fin_max_span: float = 12.0    # Max unsupported bridge span in mm when label_fin_count is None
    label_fin_thickness: float = 1.2    # Thickness (X) of each diagonal support fin in mm
    label_overhang_angle: float = 35.0  # Support fin angle underneath the label shelf in degrees
    label_width_margin: float = 5.6     # Margin subtracted from unit width (42 - 5.6 = 36.4mm pocket)
    label_tab_width: float = 6.5        # Width (Y) of side snap-in retention tab slots in mm (fits ~5.9mm tab)
    label_tab_extension: float = 0.8    # Extension (X) of side retention tab notches per side in mm

    # --------------------------------------------------------------------------
    # Ergonomic Finger Scoops
    # --------------------------------------------------------------------------
    scoop_enabled: bool = True          # Master toggle to enable/disable all finger scoops
    scoop_front_radius: float = 12.0    # Radius of front (-Y) finger scoop in mm (0.0 to disable)
    scoop_back_radius: float = 6.0      # Radius of back (+Y) finger scoop in mm (0.0 to disable)

    # --------------------------------------------------------------------------
    # Interior Dividers
    # --------------------------------------------------------------------------
    dividers_enabled: bool = True      # Master toggle to enable/disable interior dividing walls
    dividers_x: int = 1                 # Number of interior divider walls along X (0 = undivided)
    dividers_y: int = 0                 # Number of interior divider walls along Y (0 = undivided)
    divider_thickness: float = 1.2      # Wall thickness of internal dividing walls in mm

    # --------------------------------------------------------------------------
    # Drawer Spacer Gap Overhangs (Fills dead space above baseplate padding)
    # --------------------------------------------------------------------------
    overhang_enabled: bool = False      # Master toggle to enable/disable drawer spacer overhangs
    overhang_front: float = 0.0         # Body extension past front (-Y) grid boundary in mm
    overhang_back: float = 0.0          # Body extension past back (+Y) grid boundary in mm
    overhang_left: float = 0.0          # Body extension past left (-X) grid boundary in mm
    overhang_right: float = 0.0         # Body extension past right (+X) grid boundary in mm
    overhang_chamfer_angle: float = 45.0 # Print-safe underside transition angle in degrees


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
    floor_y_front: float
    floor_y_back: float
    top_y_front: float
    top_y_back: float
    # Compartment grid at top
    comp_w: float
    comp_l: float
    cx_count: int
    cy_count: int


def _compute_envelope(params: GridfinityBinParams) -> _BinEnvelope:
    """Computes derived dimensions for the bin, overhangs, and compartments."""
    gx = max(1, params.grid_x)
    gy = max(1, params.grid_y)
    gz = max(1, params.grid_z)
    pitch_xy = params.unit_size
    pitch_z = params.unit_z
    clr = params.grid_clearance

    foot_h = 4.75
    body_h = gz * pitch_z
    floor_z = foot_h + params.floor_thickness

    base_w = gx * pitch_xy - clr
    base_l = gy * pitch_xy - clr

    if params.overhang_enabled:
        ov_f = max(0.0, params.overhang_front)
        ov_b = max(0.0, params.overhang_back)
        ov_l = max(0.0, params.overhang_left)
        ov_r = max(0.0, params.overhang_right)
    else:
        ov_f = ov_b = ov_l = ov_r = 0.0
    max_ov = max(ov_f, ov_b, ov_l, ov_r)
    has_overhang = max_ov > 0.0

    if has_overhang:
        angle_rad = math.radians(max(15.0, min(75.0, params.overhang_chamfer_angle)))
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

    r_corner = max(0.5, min(params.corner_radius, min(base_w, base_l) / 2.0 - 0.1))

    t_wall = params.wall_thickness
    t_div = params.divider_thickness
    if params.dividers_enabled:
        cx_count = max(0, params.dividers_x) + 1
        cy_count = max(0, params.dividers_y) + 1
    else:
        cx_count = 1
        cy_count = 1

    inner_w = top_w - 2.0 * t_wall
    inner_l = top_l - 2.0 * t_wall
    comp_w = (inner_w - (cx_count - 1) * t_div) / cx_count
    comp_l = (inner_l - (cy_count - 1) * t_div) / cy_count
    r_inner = max(0.5, min(r_corner - t_wall, min(comp_w, comp_l) / 2.0 - 0.1))

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

        in_x_min_fl = out_x_min_fl + inset_l
        in_x_max_fl = out_x_max_fl - inset_r
        floor_y_front = out_y_min_fl + inset_f
        floor_y_back = out_y_max_fl - inset_b

        floor_inner_w = max(4.0, in_x_max_fl - in_x_min_fl)
        floor_inner_l = max(4.0, floor_y_back - floor_y_front)
        floor_inner_cx = (in_x_min_fl + in_x_max_fl) / 2.0
        floor_inner_cy = (floor_y_front + floor_y_back) / 2.0
    else:
        floor_inner_w = inner_w
        floor_inner_l = inner_l
        floor_inner_cx = top_cx
        floor_inner_cy = top_cy
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
        floor_y_front=floor_y_front,
        floor_y_back=floor_y_back,
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
    unit_w = env.pitch_xy - params.grid_clearance  # 41.5mm standard

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
        if params.magnet_holes or params.screw_holes:
            mo = params.magnet_offset
            hole_locs = [(-mo, -mo), (mo, -mo), (-mo, mo), (mo, mo)]

            if params.magnet_holes and params.magnet_depth > 0:
                with BuildSketch(Plane.XY) as mag_sk:
                    with Locations(hole_locs):
                        Circle(params.magnet_diameter / 2.0)
                extrude(amount=params.magnet_depth, mode=Mode.SUBTRACT)

            if params.screw_holes:
                with BuildSketch(Plane.XY) as screw_sk:
                    with Locations(hole_locs):
                        Circle(params.screw_diameter / 2.0)
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
        t_div = params.divider_thickness
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

    return body_builder.part


# ==============================================================================
# Component 3: Complete Concentric Top Stacking Lip
# ==============================================================================
def create_stacking_lip(params: GridfinityBinParams) -> Optional[Part]:
    """
    Generates the continuous Gridfinity stacking lip around the entire top perimeter.

    Constructed via concentric outer-minus-inner ruled lofts of RectangleRounded profiles,
    guaranteeing a 100% uniform, unbroken top rim along all 4 straight walls and all
    4 rounded corners without corner pinching or triangular artifacts.
    """
    if not params.stackable:
        return None

    env = _compute_envelope(params)
    t_wall = params.wall_thickness
    lip_depth = 2.6
    support_h = max(0.2, lip_depth - t_wall)

    lip_h = max(2.6, params.lip_height)
    top_flat = max(0.4, min(1.2, params.lip_top_flat))

    z_bot = max(env.floor_z, env.body_h - support_h)
    z0 = env.body_h
    z1 = env.body_h + 0.7
    z2 = env.body_h + 2.5
    z3 = env.body_h + lip_h

    def _inset_rect(inset_d: float) -> tuple[float, float, float]:
        w = env.top_w - 2.0 * inset_d
        l = env.top_l - 2.0 * inset_d
        r = max(0.3, env.r_corner - inset_d)
        return w, l, r

    with BuildPart() as lip_builder:
        # 1. Outer sleeve from z_bot to z3 (flush with outer bin perimeter)
        with BuildSketch(Plane.XY.offset(z_bot)) as sk_out:
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(env.top_w, env.top_l, env.r_corner)
        extrude(amount=z3 - z_bot)

        # 2. Subtract lower support taper (z_bot -> z0: inset from t_wall to 2.6mm)
        w_b, l_b, r_b = _inset_rect(t_wall)
        w_0, l_0, r_0 = _inset_rect(lip_depth)
        with BuildSketch(Plane.XY.offset(z_bot)) as sk_in_b:
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(w_b, l_b, r_b)
        with BuildSketch(Plane.XY.offset(z0)) as sk_in_0:
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(w_0, l_0, r_0)
        loft(ruled=True, mode=Mode.SUBTRACT)

        # 3. Subtract lower 45° lip chamfer (z0 -> z1: inset from 2.6mm to 1.9mm)
        w_1, l_1, r_1 = _inset_rect(1.9)
        with BuildSketch(Plane.XY.offset(z0)) as sk_in_0b:
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(w_0, l_0, r_0)
        with BuildSketch(Plane.XY.offset(z1)) as sk_in_1:
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(w_1, l_1, r_1)
        loft(ruled=True, mode=Mode.SUBTRACT)

        # 4. Subtract middle vertical section (z1 -> z2: constant inset 1.9mm)
        with BuildSketch(Plane.XY.offset(z1)) as sk_in_1b:
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(w_1, l_1, r_1)
        extrude(amount=z2 - z1, mode=Mode.SUBTRACT)

        # 5. Subtract upper 45° lip bevel (z2 -> z3: inset from 1.9mm to top_flat)
        w_3, l_3, r_3 = _inset_rect(top_flat)
        with BuildSketch(Plane.XY.offset(z2)) as sk_in_2:
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(w_1, l_1, r_1)
        with BuildSketch(Plane.XY.offset(z3)) as sk_in_3:
            with Locations([(env.top_cx, env.top_cy)]):
                RectangleRounded(w_3, l_3, r_3)
        loft(ruled=True, mode=Mode.SUBTRACT)

        # 6. Clear out label pocket & side tab slots from the lower support bevel (z < z0)
        #    so the stacking lip's 45° underside bevel never pinches the vertical tab slot height
        if params.label_enabled:
            slot_cutout = _create_label_slot_cutouts(params, env)
            if slot_cutout is not None:
                add(slot_cutout, mode=Mode.SUBTRACT)

    return lip_builder.part


# ==============================================================================
# Component 4: Ergonomic Compartment Finger Scoops
# ==============================================================================
def create_compartment_scoops(params: GridfinityBinParams) -> Optional[Part]:
    """
    Generates true circular finger-scoop ramps along the bottom front and/or back
    interior edge(s) of every compartment using `scoop_front_radius` and
    `scoop_back_radius` (set either to 0.0 to disable that side).

    Automatically adapts to both vertical walls (90° corner) and angled overhang walls
    (using exact tangent circular arcs between the horizontal floor and the sloped
    interior overhang wall), and clips strictly to the tapered interior cavity so
    a scoop never protrudes outside an overhang.
    """
    if not params.scoop_enabled:
        return None
    r_front = max(0.0, params.scoop_front_radius)
    r_back = max(0.0, params.scoop_back_radius)
    if r_front <= 0.0 and r_back <= 0.0:
        return None

    env = _compute_envelope(params)
    cavity_h = env.body_h - env.floor_z
    if cavity_h <= 1.0:
        return None

    active_scoops: list[tuple[Literal["front", "back"], float]] = []
    if r_front > 0.0:
        active_scoops.append(("front", r_front))
    if r_back > 0.0:
        active_scoops.append(("back", r_back))

    max_len_fraction = 0.45 if len(active_scoops) == 2 else 0.65

    t_div = params.divider_thickness
    inner_env_part = _create_tapered_inner_envelope(env)
    scoop_solids = []

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

            # Determine the floor Y-boundaries of this compartment
            comp_y_front_top = ccy - env.comp_l / 2.0
            comp_y_back_top = ccy + env.comp_l / 2.0

            comp_y_front_floor = (
                env.floor_y_front if icy == 0 else comp_y_front_top
            )
            comp_y_back_floor = (
                env.floor_y_back if icy == env.cy_count - 1 else comp_y_back_top
            )
            comp_floor_l = comp_y_back_floor - comp_y_front_floor
            if comp_floor_l <= 2.0:
                continue

            for wall_side, req_radius in active_scoops:
                if wall_side == "front":
                    s = 1.0  # Interior is in +Y direction from front wall
                    y_corner = comp_y_front_floor
                    # Check if this wall is sloped due to front overhang
                    dy_slope = max(0.0, comp_y_front_floor - comp_y_front_top)
                else:
                    s = -1.0  # Interior is in -Y direction from back wall
                    y_corner = comp_y_back_floor
                    # Check if this wall is sloped due to back overhang
                    dy_slope = max(0.0, comp_y_back_top - comp_y_back_floor)

                if dy_slope > 1e-4 and env.z_trans > env.floor_z:
                    dz_slope = env.z_trans - env.floor_z
                    alpha = math.atan2(dz_slope, dy_slope)  # Wall angle in (0, pi/2)
                    wall_seg_len = math.hypot(dy_slope, dz_slope)
                else:
                    alpha = math.pi / 2.0  # Standard 90° vertical wall
                    wall_seg_len = cavity_h - 1.0

                tan_half = math.tan(alpha / 2.0)
                if tan_half <= 1e-4:
                    continue

                # Constrain scoop radius so tangent length fits both floor and wall segment
                max_tan_len = min(comp_floor_l * max_len_fraction, wall_seg_len * 0.95)
                sr = min(req_radius, max_tan_len / tan_half)
                if sr <= 0.5:
                    continue

                l_tan = sr * tan_half

                # Exact tangent points and arc midpoint for any wall angle alpha in (0, pi/2]
                p_corner = Vector(y_corner, env.floor_z)
                p_floor = Vector(y_corner + s * l_tan, env.floor_z)
                p_top = Vector(
                    y_corner - s * l_tan * math.cos(alpha),
                    env.floor_z + l_tan * math.sin(alpha),
                )
                arc_mid = Vector(
                    y_corner + s * (l_tan - sr * math.sin(alpha / 2.0)),
                    env.floor_z + sr * (1.0 - math.cos(alpha / 2.0)),
                )

                with BuildPart() as comp_scoop:
                    with BuildSketch(Plane.YZ.offset(ccx)) as sk_yz:
                        with BuildLine() as bl:
                            Line(p_top, p_corner)
                            Line(p_corner, p_floor)
                            ThreePointArc(p_floor, arc_mid, p_top)
                        make_face()
                    extrude(amount=env.comp_w / 2.0, both=True)

                    # Clip to the compartment's rounded XY footprint
                    with BuildSketch(Plane.XY.offset(env.floor_z)) as sk_clip:
                        with Locations([(ccx, ccy)]):
                            RectangleRounded(env.comp_w, env.comp_l, env.r_inner)
                    extrude(amount=cavity_h, mode=Mode.INTERSECT)

                    # Clip to the tapered interior cavity so it never protrudes past any overhang
                    add(inner_env_part, mode=Mode.INTERSECT)

                scoop_solids.append(comp_scoop.part)

    if not scoop_solids:
        return None

    with BuildPart() as all_scoops:
        add(scoop_solids)

    return all_scoops.part


# ==============================================================================
# Component 5: Pred-Compatible Printable Label Holder (Bridged Support Fins)
# ==============================================================================
def _create_label_slot_cutouts(
    params: GridfinityBinParams, env: _BinEnvelope
) -> Optional[Part]:
    """
    Builds the negative cutout solid for all Pred label pockets and side snap-tab
    slots (from z = body_h - label_thickness up to z = body_h). Shared between
    `create_label_holders` and `create_stacking_lip` so the stacking lip's lower
    45° support bevel never intrudes into the tab slots.
    """
    if not params.label_enabled or params.label_thickness <= 0:
        return None

    shelf_d = min(params.label_shelf_depth, env.comp_l * 0.75)
    if shelf_d <= 4.0:
        return None

    t_div = params.divider_thickness
    z_top = env.body_h
    recess_z = params.label_thickness
    lh = min(params.label_height, shelf_d - 1.5)
    tab_w = min(params.label_tab_width, lh - 1.0)
    tab_ext = params.label_tab_extension

    pocket_x_specs = []
    if env.cx_count > 1:
        for icx in range(env.cx_count):
            ccx = (
                env.top_cx
                - env.inner_w / 2.0
                + env.comp_w / 2.0
                + icx * (env.comp_w + t_div)
            )
            pw = max(8.0, env.comp_w - params.label_width_margin + 2.0 * params.wall_thickness)
            pocket_x_specs.append((ccx, pw))
    elif params.label_style == "per_column":
        pw = max(8.0, env.pitch_xy - params.label_width_margin)
        for ix in range(env.gx):
            scx = (ix - (env.gx - 1) / 2.0) * env.pitch_xy
            pocket_x_specs.append((scx, pw))
    else:
        pw = max(8.0, env.gx * env.pitch_xy - params.label_width_margin)
        pocket_x_specs.append((env.top_cx, pw))

    with BuildPart() as cutout_builder:
        with BuildSketch(Plane.XY.offset(z_top)) as sk_pocket:
            for icy in range(env.cy_count):
                ccy = (
                    env.top_cy
                    - env.inner_l / 2.0
                    + env.comp_l / 2.0
                    + icy * (env.comp_l + t_div)
                )
                if params.label_wall == "back":
                    y_wall = ccy + env.comp_l / 2.0
                    y_pocket_center = y_wall - shelf_d / 2.0
                else:
                    y_wall = ccy - env.comp_l / 2.0
                    y_pocket_center = y_wall + shelf_d / 2.0

                for scx, sw in pocket_x_specs:
                    with Locations([(scx, y_pocket_center)]):
                        RectangleRounded(sw, lh, min(1.0, lh / 4.0))
                        if tab_ext > 0 and tab_w > 0:
                            RectangleRounded(sw + 2.0 * tab_ext, tab_w, min(0.25, tab_w / 8.0))
        extrude(amount=-recess_z)

    return cutout_builder.part


def create_label_holders(params: GridfinityBinParams) -> Optional[Part]:
    """
    Generates the Pred-compatible printable label holder shelf and recessed snap-in socket:
    - Thin horizontal shelf deck at z = body_h extending inward from the compartment wall.
    - Evenly spaced diagonal 45° support fins underneath the shelf deck (instead of a solid
      block) that bridge effortlessly during printing while preserving interior bin volume.
    - Recessed pocket on top of the shelf matching standard 3D-printable Pred labels
      (default 11.5mm deep x 0.8mm recessed), complete with side snap-in retention tab notches.
    """
    if not params.label_enabled:
        return None

    env = _compute_envelope(params)
    t_div = params.divider_thickness
    shelf_d = min(params.label_shelf_depth, env.comp_l * 0.75)
    if shelf_d <= 4.0:
        return None

    deck_t = max(params.label_thickness + 0.6, params.label_shelf_thickness)
    angle_rad = math.radians(max(25.0, min(65.0, params.label_overhang_angle)))
    fin_drop_h = shelf_d * math.tan(angle_rad)

    # Top of the label shelf aligns with z = body_h
    z_top = env.body_h
    z_deck_bot = z_top - deck_t
    z_fin_bot = max(env.floor_z, z_deck_bot - fin_drop_h)

    inner_env_part = _create_tapered_inner_envelope(env)
    shelf_solids = []

    # Number of support fins per X compartment (manual override or auto-calculated from max bridge span)
    if params.label_fin_count is not None:
        fins_per_comp = max(0, params.label_fin_count)
    else:
        max_span = max(2.0, params.label_fin_max_span)
        fins_per_comp = max(0, math.ceil(env.comp_w / max_span) - 1)
    fin_t = max(0.8, params.label_fin_thickness)

    # Build a horizontal shelf deck + evenly spaced diagonal support fins in each compartment
    for icy in range(env.cy_count):
        ccy = (
            env.top_cy
            - env.inner_l / 2.0
            + env.comp_l / 2.0
            + icy * (env.comp_l + t_div)
        )

        if params.label_wall == "back":
            # Attached to back wall of compartment (y_wall = ccy + comp_l/2), overhanging toward -Y
            y_wall = ccy + env.comp_l / 2.0
            y_tip = y_wall - shelf_d
        else:
            # Attached to front wall of compartment (y_wall = ccy - comp_l/2), overhanging toward +Y
            y_wall = ccy - env.comp_l / 2.0
            y_tip = y_wall + shelf_d

        for icx in range(env.cx_count):
            ccx = (
                env.top_cx
                - env.inner_w / 2.0
                + env.comp_w / 2.0
                + icx * (env.comp_w + t_div)
            )

            with BuildPart() as comp_shelf:
                # 1A. Horizontal shelf deck spanning full compartment width
                with BuildSketch(Plane.YZ.offset(ccx)) as sk_deck:
                    Polygon(
                        (y_wall, z_top),
                        (y_tip, z_top),
                        (y_tip, z_deck_bot),
                        (y_wall, z_deck_bot),
                        align=None,
                    )
                extrude(amount=env.comp_w / 2.0, both=True)

                # 1B. Evenly spaced diagonal support fins underneath the deck
                if fins_per_comp > 0 and z_deck_bot > z_fin_bot + 0.5:
                    bay_span = env.comp_w / (fins_per_comp + 1)
                    for i_fin in range(1, fins_per_comp + 1):
                        fin_x = (ccx - env.comp_w / 2.0) + i_fin * bay_span
                        with BuildSketch(Plane.YZ.offset(fin_x)) as sk_fin:
                            Polygon(
                                (y_wall, z_deck_bot),
                                (y_tip, z_deck_bot),
                                (y_wall, z_fin_bot),
                                align=None,
                            )
                        extrude(amount=fin_t / 2.0, both=True)

                # Clip deck + fins to the rounded XY boundary of the compartment
                with BuildSketch(Plane.XY.offset(z_fin_bot - 0.1)) as sk_clip:
                    with Locations([(ccx, ccy)]):
                        RectangleRounded(env.comp_w, env.comp_l, env.r_inner)
                extrude(amount=(z_top - z_fin_bot) + 0.5, mode=Mode.INTERSECT)

                # Also clip to the tapered interior cavity so fins follow any overhang slope
                add(inner_env_part, mode=Mode.INTERSECT)

            shelf_solids.append(comp_shelf.part)

    # Combine all shelf decks + fins and cut the recessed Pred snap-in label sockets
    with BuildPart() as label_builder:
        add(shelf_solids)
        slot_cutout = _create_label_slot_cutouts(params, env)
        if slot_cutout is not None:
            add(slot_cutout, mode=Mode.SUBTRACT)

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

    with BuildPart() as final_bin:
        add(feet)
        add(body)
        if scoops is not None:
            add(scoops)
        if labels is not None:
            add(labels)
        if lip is not None:
            add(lip)

    return final_bin.part


# ==============================================================================
# Model Execution & Export
# ==============================================================================
if __name__ == "__main__":
    # Instantiate default parameters directly from dataclass definitions
    params = GridfinityBinParams()

    # Generate part geometry
    part = create_gridfinity_bin(params)

    # Standardized export handling
    if EXPORT_STL or EXPORT_STEP:
        output_dir = Path(__file__).resolve().parent / OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        dims = f"{params.grid_x}x{params.grid_y}x{params.grid_z}u"
        style = f"pred_label_{params.label_style}" if params.label_enabled else "standard"
        base_filename = f"gridfinity_bin_{dims}_{style}"

        if EXPORT_STL:
            stl_path = output_dir / f"{base_filename}.stl"
            export_stl(part, str(stl_path))
            print(f"Exported STL: {stl_path}")

        if EXPORT_STEP:
            step_path = output_dir / f"{base_filename}.step"
            export_step(part, str(step_path))
            print(f"Exported STEP: {step_path}")

    # Visualize model in viewer
    show(part)
