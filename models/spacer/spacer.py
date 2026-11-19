"""
Parametric Spacer Generator (build123d)

Generates precision straight, L-corner, T-shape, and cross (+) spacers for filling
gaps in drawers, enclosures, trays, and shelving.

Clean, Unified Leg Architecture:
- Setting both `leg_x_length > 0` and `leg_y_length > 0` generates an L-corner, T-shape, or Cross (+).
- Setting `leg_y_length = 0` generates a straight Leg X spacer.
- Setting `leg_x_length = 0` generates a straight Leg Y spacer.
- Each leg has independent length, width, and junction alignment/offset.
- Height (Z) is shared across both legs.
- Customizable outer, inner, and end corner radii plus top edge fillet/chamfer.
- Flexible notches, pockets, and pass-through cutouts with rounded or chamfered entries.
- Optional hollow underside mode and top finger-lift scoop.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from build123d import *

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False      # Save .stl file on execution (default: False)
EXPORT_STEP: bool = False     # Save .step file on execution (default: False)
OUTPUT_DIR: str = "exports"   # Relative subfolder alongside this script


@dataclass
class SpacerCutout:
    """Defines a notch, step-down, pocket, or through-hole cutout along one leg of the spacer."""

    leg: str = "x"                      # Which leg to cut: "x" or "y"
    align: str = "start"                # Anchor along the leg: "start" (corner), "center", or "end" (far end)
    offset: float = 0.0                 # Distance inward from "start"/"end", or +/- shift from "center" in mm
    v_align: str = "top"                # Vertical anchor: "top", "center", or "bottom"
    v_offset: float = 0.0               # Distance inward from "top"/"bottom" (0 = edge notch; > 0 = closed hole), or +/- shift from "center" in mm
    length: float = 50.0                # Length of the cutout along the leg in mm
    height: float = 20.0                # Vertical height of the cutout in mm
    shape: str = "rectangle"            # "rectangle" ("square"), "circle" ("arc"), or "chamfer" ("trapezoid")
    radius: float = 0.0                 # mm: inside corner fillet (rectangle), circle radius (circle; 0=auto), or ramp width (chamfer; 0=45 deg)
    entry_radius: float = 0.0           # mm: rounds/bevels the 90-deg corners where an edge cutout meets the top or bottom border
    entry_treatment: str = "fillet"     # "fillet" (rounded) or "chamfer" (45-deg bevel) for entry_radius
    depth: Optional[float] = None       # Cut depth through spacer thickness in mm (None = full through-cut)
    side: str = "outer"                 # Face to cut from when depth is set: "outer" (wall side) or "inner" (bin side)


@dataclass
class SpacerParams:
    """Single source of truth parameters for parametric spacers."""

    # --------------------------------------------------------------------------
    # Shared Height (Z)
    # --------------------------------------------------------------------------
    height: float = 56.0                # Spacer height in mm (Z dimension)

    # --------------------------------------------------------------------------
    # Leg X (e.g. Front / Back wall)
    # Set leg_y_length = 0 to generate a straight Leg X spacer!
    # --------------------------------------------------------------------------
    leg_x_length: float = 180.0         # Length along X wall in mm (set 0 to omit)
    leg_x_width: float = 15.0           # Width / thickness of X leg in mm

    # --------------------------------------------------------------------------
    # Leg Y (e.g. Side wall)
    # Set leg_x_length = 0 to generate a straight Leg Y spacer!
    # --------------------------------------------------------------------------
    leg_y_length: float = 246.0         # Length along Y wall in mm (set 0 to omit)
    leg_y_width: float = 15.0           # Width / thickness of Y leg in mm

    # --------------------------------------------------------------------------
    # Orientation & Junction Position (Inverse L, T-Shape, Cross)
    # --------------------------------------------------------------------------
    mirror_x: bool = False               # Mirror left <-> right (inverts L-shape for opposite corner)
    mirror_y: bool = False              # Mirror front <-> back
    leg_y_align: str = "start"          # Anchor for Leg Y along X: "start", "center" (T-shape), or "end"
    leg_y_offset: float = 0.0           # Fine-tune shift of Leg Y from leg_y_align in mm (+ or -)
    leg_x_align: str = "start"          # Anchor for Leg X along Y: "start", "center" (sideways T), or "end"
    leg_x_offset: float = 0.0           # Fine-tune shift of Leg X from leg_x_align in mm (+ or -)

    # --------------------------------------------------------------------------
    # Corner Radii & Top Edge Treatment
    # --------------------------------------------------------------------------
    corner_radius: float = 2.0          # General vertical corner radius in mm (XY profile corners)
    outer_corner_radius: Optional[float] = None  # Outer junction corner radius in mm (None = corner_radius)
    inner_corner_radius: Optional[float] = 4.0   # Inside junction corner radius in mm (None = corner_radius)
    end_corner_radius: float = 0.0               # Radius on mating arm ends in mm (0.0 for flush butt-joints)

    edge_radius: float = 1.0            # Top perimeter edge radius/bevel in mm (smooth touch & prevents snagging)
    edge_treatment: str = "fillet"      # "fillet" (smooth curve) or "chamfer" (beveled 45-deg edge)

    # --------------------------------------------------------------------------
    # Hollow / Shell Options (Saves filament and print time on thick spacers)
    # --------------------------------------------------------------------------
    hollow: bool = False                # If True, hollows out the bottom with an open underside
    wall_thickness: float = 2.0         # Side wall thickness when hollow=True in mm
    top_thickness: float = 2.0          # Top solid roof thickness when hollow=True in mm

    # --------------------------------------------------------------------------
    # Ergonomic Finger-Lift Scoop (Optional removal aid)
    # --------------------------------------------------------------------------
    finger_notch: bool = False          # If True, adds a recessed scoop on the top face for easy prying/removal
    finger_notch_radius: float = 12.0   # Radius of spherical scoop cutter in mm
    finger_notch_depth: float = 2.5     # Depth of scoop recess from top surface in mm

    # --------------------------------------------------------------------------
    # Notches & Cutouts (For drawer locks, latches, handle bolts, etc.)
    # --------------------------------------------------------------------------
    cutouts_enabled: bool = False       # Master toggle to enable/disable all cutouts below
    cutouts: List[SpacerCutout] = field(default_factory=lambda: [
        SpacerCutout(
            leg="x",
            align="end",
            offset=12.0,
            length=42.0,
            height=16.0,
            shape="rectangle",
            radius=2.0,
            entry_radius=2.0,
        ),
    ])


def _apply_cutout(
    cutout: SpacerCutout,
    lx: float,
    wx: float,
    ly: float,
    wy: float,
    h: float,
    x0: float = 0.0,
    y0: float = 0.0,
) -> None:
    """Subtract a single SpacerCutout inside an active BuildPart context."""
    leg = cutout.leg.strip().lower()
    if leg == "x":
        if lx <= 0:
            raise ValueError("Cannot apply cutout to leg 'x' when leg_x_length is 0.")
        leg_len = lx
        leg_w = wx
        leg_base = y0
    elif leg == "y":
        if ly <= 0:
            raise ValueError("Cannot apply cutout to leg 'y' when leg_y_length is 0.")
        leg_len = ly
        leg_w = wy
        leg_base = x0
    else:
        raise ValueError(f"Invalid cutout leg '{cutout.leg}'. Expected 'x' or 'y'.")

    if cutout.length <= 0:
        raise ValueError(f"Cutout length must be positive: got {cutout.length}")
    if cutout.height <= 0:
        raise ValueError(f"Cutout height must be positive: got {cutout.height}")

    shape = cutout.shape.strip().lower()
    if shape not in ("rectangle", "rect", "square", "circle", "round", "arc", "chamfer", "trapezoid", "ramp"):
        raise ValueError(
            f"Invalid cutout shape '{cutout.shape}'. "
            "Expected 'rectangle', 'circle', or 'chamfer'."
        )

    side = cutout.side.strip().lower()
    if side not in ("outer", "inner"):
        raise ValueError(f"Invalid cutout side '{cutout.side}'. Expected 'outer' or 'inner'.")

    # Resolve horizontal position along leg from align + offset
    h_align = cutout.align.strip().lower()
    if h_align == "start":
        u0 = cutout.offset
    elif h_align == "center":
        u0 = (leg_len - cutout.length) / 2.0 + cutout.offset
    elif h_align == "end":
        u0 = leg_len - cutout.offset - cutout.length
    else:
        raise ValueError(f"Invalid cutout align '{cutout.align}'. Expected 'start', 'center', or 'end'.")
    u1 = u0 + cutout.length
    u_mid = (u0 + u1) / 2.0

    # Resolve vertical bounds from v_align + v_offset
    v_align = cutout.v_align.strip().lower()
    if v_align == "top":
        z_top = h - cutout.v_offset
        z_bot = z_top - cutout.height
    elif v_align == "bottom":
        z_bot = cutout.v_offset
        z_top = z_bot + cutout.height
    elif v_align == "center":
        z_mid = h / 2.0 + cutout.v_offset
        z_bot = z_mid - cutout.height / 2.0
        z_top = z_mid + cutout.height / 2.0
    else:
        raise ValueError(f"Invalid cutout v_align '{cutout.v_align}'. Expected 'top', 'center', or 'bottom'.")

    open_top = z_top >= h - 1e-3
    open_bottom = z_bot <= 1e-3

    # Extrusion range across spacer thickness (overshoot by 1mm to avoid coplanar faces)
    overshoot = 1.0
    if cutout.depth is None or cutout.depth >= leg_w:
        d_start = leg_base - overshoot
        d_end = leg_base + leg_w + overshoot
    else:
        if cutout.depth <= 0:
            raise ValueError(f"Cutout depth must be positive or None: got {cutout.depth}")
        if side == "outer":
            d_start = leg_base - overshoot
            d_end = leg_base + cutout.depth
        else:
            d_start = leg_base + leg_w - cutout.depth
            d_end = leg_base + leg_w + overshoot

    extrude_amount = d_end - d_start

    # Construct side-elevation sketch plane where:
    #   sketch X (u) = distance along the leg
    #   sketch Y (v) = vertical Z height
    #   sketch +Z    = extrusion direction across spacer thickness
    if leg == "x":
        sketch_plane = Plane(origin=(0.0, d_end, 0.0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    else:
        sketch_plane = Plane(origin=(d_start, 0.0, 0.0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))

    z_pad = max(2.0, cutout.radius + 1.0, cutout.entry_radius + 1.0)
    mouth_u0: Optional[float] = None
    mouth_u1: Optional[float] = None
    avail_entry_h = 0.0

    with BuildSketch(sketch_plane) as sk_cut:
        if shape in ("rectangle", "rect", "square"):
            if open_top and open_bottom:
                rect_h = h + 2.0 * z_pad
                v_center = h / 2.0
                eff_r = 0.0
            elif open_top:
                eff_r = (
                    max(0.0, min(cutout.radius, cutout.length / 2.0 - 0.05, (h - z_bot) - 0.05))
                    if cutout.radius > 0
                    else 0.0
                )
                rect_h = (h - z_bot) + z_pad
                v_center = z_bot + rect_h / 2.0
                mouth_u0, mouth_u1 = u0, u1
                avail_entry_h = max(0.0, (h - z_bot) - eff_r - 0.05)
            elif open_bottom:
                eff_r = (
                    max(0.0, min(cutout.radius, cutout.length / 2.0 - 0.05, z_top - 0.05))
                    if cutout.radius > 0
                    else 0.0
                )
                rect_h = z_top + z_pad
                v_center = z_top - rect_h / 2.0
                mouth_u0, mouth_u1 = u0, u1
                avail_entry_h = max(0.0, z_top - eff_r - 0.05)
            else:
                # Closed interior window/slot
                eff_r = (
                    max(0.0, min(cutout.radius, cutout.length / 2.0 - 0.05, cutout.height / 2.0 - 0.05))
                    if cutout.radius > 0
                    else 0.0
                )
                rect_h = cutout.height
                v_center = (z_bot + z_top) / 2.0

            with Locations((u_mid, v_center)):
                if eff_r > 0.05:
                    RectangleRounded(cutout.length, rect_h, radius=eff_r)
                else:
                    Rectangle(cutout.length, rect_h)

        elif shape in ("circle", "round", "arc"):
            if open_top and not open_bottom:
                r = cutout.radius if cutout.radius > 0 else cutout.length / 2.0
                eff_h = h - z_bot
                v_c = z_bot + r
                with Locations((u_mid, v_c)):
                    Circle(radius=r)
                if eff_h > r:
                    slot_top = h + z_pad
                    slot_h = slot_top - v_c
                    with Locations((u_mid, v_c + slot_h / 2.0)):
                        Rectangle(2.0 * r, slot_h)
                    mouth_u0, mouth_u1 = u_mid - r, u_mid + r
                    avail_entry_h = max(0.0, eff_h - r - 0.05)
            elif open_bottom and not open_top:
                r = cutout.radius if cutout.radius > 0 else cutout.length / 2.0
                eff_h = z_top
                v_c = z_top - r
                with Locations((u_mid, v_c)):
                    Circle(radius=r)
                if eff_h > r:
                    slot_bot = -z_pad
                    slot_h = v_c - slot_bot
                    with Locations((u_mid, slot_bot + slot_h / 2.0)):
                        Rectangle(2.0 * r, slot_h)
                    mouth_u0, mouth_u1 = u_mid - r, u_mid + r
                    avail_entry_h = max(0.0, eff_h - r - 0.05)
            else:
                # Closed interior circular hole (or full-height)
                r = cutout.radius if cutout.radius > 0 else min(cutout.length, cutout.height) / 2.0
                with Locations((u_mid, (z_bot + z_top) / 2.0)):
                    Circle(radius=r)

        else:  # chamfer / trapezoid / ramp
            raw_c = cutout.radius if cutout.radius > 0 else cutout.height
            if open_top and not open_bottom:
                eff_h = h - z_bot
                c = max(0.0, min(raw_c, cutout.length / 2.0 - 0.05))
                pts = [
                    (u0, h + 2.0),
                    (u1, h + 2.0),
                    (u1, h),
                    (u1 - c, z_bot),
                    (u0 + c, z_bot),
                    (u0, h),
                ]
            elif open_bottom and not open_top:
                c = max(0.0, min(raw_c, cutout.length / 2.0 - 0.05))
                pts = [
                    (u0, -2.0),
                    (u1, -2.0),
                    (u1, 0.0),
                    (u1 - c, z_top),
                    (u0 + c, z_top),
                    (u0, 0.0),
                ]
            else:
                # Closed interior chamfered octagon/window
                c = max(0.0, min(raw_c, cutout.length / 2.0 - 0.05, cutout.height / 2.0 - 0.05))
                pts = [
                    (u0 + c, z_bot),
                    (u1 - c, z_bot),
                    (u1, z_bot + c),
                    (u1, z_top - c),
                    (u1 - c, z_top),
                    (u0 + c, z_top),
                    (u0, z_top - c),
                    (u0, z_bot + c),
                ]
            Polygon(*pts, align=None)

        # Optional mouth/entry rounding or chamfer where an edge cutout meets top or bottom border
        if cutout.entry_radius > 0.05 and mouth_u0 is not None and mouth_u1 is not None and avail_entry_h > 0.05:
            r_e = min(cutout.entry_radius, avail_entry_h)
            is_entry_chamfer = cutout.entry_treatment.strip().lower() == "chamfer"
            if open_top and not open_bottom:
                if is_entry_chamfer:
                    Polygon(
                        (mouth_u0 - r_e, h + z_pad),
                        (mouth_u0, h + z_pad),
                        (mouth_u0, h - r_e),
                        (mouth_u0 - r_e, h),
                        align=None,
                    )
                    Polygon(
                        (mouth_u1, h + z_pad),
                        (mouth_u1 + r_e, h + z_pad),
                        (mouth_u1 + r_e, h),
                        (mouth_u1, h - r_e),
                        align=None,
                    )
                else:
                    flare_h = r_e + z_pad
                    flare_v = h - r_e + flare_h / 2.0
                    with Locations((mouth_u0 - r_e / 2.0, flare_v), (mouth_u1 + r_e / 2.0, flare_v)):
                        Rectangle(r_e, flare_h)
                    with Locations((mouth_u0 - r_e, h - r_e), (mouth_u1 + r_e, h - r_e)):
                        Circle(radius=r_e, mode=Mode.SUBTRACT)
            elif open_bottom and not open_top:
                if is_entry_chamfer:
                    Polygon(
                        (mouth_u0 - r_e, -z_pad),
                        (mouth_u0, -z_pad),
                        (mouth_u0, r_e),
                        (mouth_u0 - r_e, 0.0),
                        align=None,
                    )
                    Polygon(
                        (mouth_u1, -z_pad),
                        (mouth_u1 + r_e, -z_pad),
                        (mouth_u1 + r_e, 0.0),
                        (mouth_u1, r_e),
                        align=None,
                    )
                else:
                    flare_h = r_e + z_pad
                    flare_v = r_e - flare_h / 2.0
                    with Locations((mouth_u0 - r_e / 2.0, flare_v), (mouth_u1 + r_e / 2.0, flare_v)):
                        Rectangle(r_e, flare_h)
                    with Locations((mouth_u0 - r_e, r_e), (mouth_u1 + r_e, r_e)):
                        Circle(radius=r_e, mode=Mode.SUBTRACT)

    extrude(sk_cut.sketch, amount=extrude_amount, mode=Mode.SUBTRACT)


def _resolve_leg_position(
    align: str,
    offset: float,
    span: float,
    width: float,
    leg_name: str,
) -> float:
    """Resolve a leg's junction position along the perpendicular leg from align + offset."""
    max_pos = span - width
    mode = align.strip().lower()
    if mode == "start":
        base = 0.0
    elif mode == "center":
        base = max_pos / 2.0
    elif mode == "end":
        base = max_pos
    else:
        raise ValueError(f"Invalid {leg_name}_align '{align}'. Expected 'start', 'center', or 'end'.")

    pos = base + offset
    if pos < -1e-6 or pos > max_pos + 1e-6:
        raise ValueError(
            f"Resolved {leg_name} position ({pos:.2f}mm from align='{align}', offset={offset}mm) "
            f"must be between 0 and {max_pos:.2f}mm."
        )
    return max(0.0, min(pos, max_pos))


def create_spacer(params: SpacerParams) -> Solid:
    """
    Decoupled generator function for parametric spacers.

    - leg_x_length > 0 and leg_y_length > 0: generates an L-corner, T-shape, or Cross (+) spacer
      depending on `leg_y_align` / `leg_y_offset` and `leg_x_align` / `leg_x_offset`.
    - leg_x_length > 0 and leg_y_length <= 0: generates straight Leg X spacer.
    - leg_x_length <= 0 and leg_y_length > 0: generates straight Leg Y spacer.
    - `mirror_x` / `mirror_y`: mirrors the finished spacer for opposite corners.
    """
    lx = max(0.0, params.leg_x_length)
    wx = params.leg_x_width
    ly = max(0.0, params.leg_y_length)
    wy = params.leg_y_width
    h = params.height

    if lx <= 0 and ly <= 0:
        raise ValueError(
            "At least one of leg_x_length or leg_y_length must be strictly greater than 0."
        )
    if h <= 0:
        raise ValueError(f"Height must be positive: got height={h}")

    is_junction = (lx > 0 and ly > 0)
    x0 = 0.0
    y0 = 0.0

    # Validation checks
    if is_junction:
        if wx <= 0 or wy <= 0:
            raise ValueError(f"Both leg widths must be positive: got leg_x_width={wx}, leg_y_width={wy}")
        if lx <= wy:
            raise ValueError(f"leg_x_length ({lx}mm) must be strictly greater than leg_y_width ({wy}mm)")
        if ly <= wx:
            raise ValueError(f"leg_y_length ({ly}mm) must be strictly greater than leg_x_width ({wx}mm)")
        x0 = _resolve_leg_position(params.leg_y_align, params.leg_y_offset, lx, wy, "leg_y")
        y0 = _resolve_leg_position(params.leg_x_align, params.leg_x_offset, ly, wx, "leg_x")
    elif lx > 0 and wx <= 0:
        raise ValueError(f"leg_x_width must be positive: got {wx}")
    elif ly > 0 and wy <= 0:
        raise ValueError(f"leg_y_width must be positive: got {wy}")

    # Radii
    r_outer = params.outer_corner_radius if params.outer_corner_radius is not None else params.corner_radius
    r_inner = params.inner_corner_radius if params.inner_corner_radius is not None else params.corner_radius
    r_end = params.end_corner_radius
    r_top = params.edge_radius

    with BuildPart() as builder:
        # Base 2D profile
        with BuildSketch(Plane.XY) as sk:
            if is_junction:
                # Union of the two perpendicular arms (L, T, or Cross depending on offsets)
                with Locations((0.0, y0)):
                    Rectangle(lx, wx, align=(Align.MIN, Align.MIN))
                with Locations((x0, 0.0)):
                    Rectangle(wy, ly, align=(Align.MIN, Align.MIN))
            elif lx > 0:
                # Straight Leg X
                eff_cr = max(0.0, min(params.corner_radius, min(lx, wx) / 2.0 - 0.05)) if params.corner_radius > 0 else 0.0
                if eff_cr > 0.05:
                    RectangleRounded(lx, wx, radius=eff_cr, align=(Align.MIN, Align.MIN))
                else:
                    Rectangle(lx, wx, align=(Align.MIN, Align.MIN))
            else:
                # Straight Leg Y
                eff_cr = max(0.0, min(params.corner_radius, min(ly, wy) / 2.0 - 0.05)) if params.corner_radius > 0 else 0.0
                if eff_cr > 0.05:
                    RectangleRounded(wy, ly, radius=eff_cr, align=(Align.MIN, Align.MIN))
                else:
                    Rectangle(wy, ly, align=(Align.MIN, Align.MIN))
        extrude(amount=h)

        # Hollow underside pocket (if enabled)
        if params.hollow and h > params.top_thickness + 1.0:
            min_dim = min(wx, wy) if is_junction else (wx if lx > 0 else wy)
            eff_wall = min(params.wall_thickness, min_dim / 2.0 - 0.5)
            if eff_wall > 0.5:
                with BuildSketch(Plane.XY) as sk_inner:
                    offset(sk.sketch, amount=-eff_wall)
                extrude(sk_inner.sketch, amount=h - params.top_thickness, mode=Mode.SUBTRACT)

        # Vertical corner fillets for L / T / Cross junction pieces
        if is_junction:
            eps = 1e-3
            outer_pts = []
            if x0 < eps and y0 < eps:
                outer_pts.append((0.0, 0.0))
            if abs((x0 + wy) - lx) < eps and y0 < eps:
                outer_pts.append((lx, 0.0))
            if x0 < eps and abs((y0 + wx) - ly) < eps:
                outer_pts.append((0.0, ly))
            if abs((x0 + wy) - lx) < eps and abs((y0 + wx) - ly) < eps:
                outer_pts.append((lx, ly))

            inner_pts = []
            if x0 > eps and y0 > eps:
                inner_pts.append((x0, y0))
            if (lx - (x0 + wy)) > eps and y0 > eps:
                inner_pts.append((x0 + wy, y0))
            if x0 > eps and (ly - (y0 + wx)) > eps:
                inner_pts.append((x0, y0 + wx))
            if (lx - (x0 + wy)) > eps and (ly - (y0 + wx)) > eps:
                inner_pts.append((x0 + wy, y0 + wx))

            def _edge_matches(edge, pts):
                c = edge.center()
                return any(abs(c.X - px) < 1e-2 and abs(c.Y - py) < 1e-2 for px, py in pts)

            arm_spans = [d for d in (x0, lx - (x0 + wy), y0, ly - (y0 + wx)) if d > eps]
            min_span = min(arm_spans) if arm_spans else min(lx, ly)

            eff_rout = max(0.0, min(r_outer, min(lx, ly) * 0.45))
            eff_rin = max(0.0, min(r_inner, min(wx, wy) * 0.85, min_span * 0.85))
            eff_rend = max(0.0, min(r_end, min(wx, wy) * 0.45))

            if eff_rout > 0.05 and outer_pts:
                outer_edges = [e for e in builder.edges().filter_by(Axis.Z) if _edge_matches(e, outer_pts)]
                if outer_edges:
                    fillet(outer_edges, radius=eff_rout)

            if eff_rin > 0.05 and inner_pts:
                inner_edges = [e for e in builder.edges().filter_by(Axis.Z) if _edge_matches(e, inner_pts)]
                if inner_edges:
                    fillet(inner_edges, radius=eff_rin)

            if eff_rend > 0.05:
                skip_pts = outer_pts + inner_pts
                end_edges = [
                    e for e in builder.edges().filter_by(Axis.Z)
                    if not _edge_matches(e, skip_pts)
                    and (
                        abs(e.center().X) < 1e-2
                        or abs(e.center().X - lx) < 1e-2
                        or abs(e.center().Y) < 1e-2
                        or abs(e.center().Y - ly) < 1e-2
                    )
                ]
                if end_edges:
                    fillet(end_edges, radius=eff_rend)

        # Top perimeter edge treatment (fillet or chamfer)
        if r_top > 0.05 and h > r_top:
            min_edge = min(wx, wy) if is_junction else (wx if lx > 0 else wy)
            max_er = min(h * 0.8, min_edge * 0.45)
            if params.hollow:
                max_er = min(max_er, params.wall_thickness * 0.8)
            er = min(r_top, max_er)

            if er > 0.05:
                top_face = builder.faces().sort_by(Axis.Z)[-1]
                top_outer_edges = top_face.outer_wire().edges()
                if params.edge_treatment.lower() == "chamfer":
                    chamfer(top_outer_edges, length=er)
                else:
                    fillet(top_outer_edges, radius=er)

        # Finger-lift scoop (if enabled)
        if params.finger_notch and params.finger_notch_radius > 0:
            fn_r = params.finger_notch_radius
            fn_d = min(params.finger_notch_depth, h * 0.5)
            if is_junction:
                cx = x0 + wy / 2.0
                cy = y0 + wx / 2.0
            elif lx > 0:
                cx = lx / 2.0
                cy = wx / 2.0
            else:
                cx = wy / 2.0
                cy = ly / 2.0
            cz = h + fn_r - fn_d
            with Locations((cx, cy, cz)):
                Sphere(radius=fn_r, mode=Mode.SUBTRACT)

        # Notches & cutouts (if enabled)
        if params.cutouts_enabled and params.cutouts:
            for cutout in params.cutouts:
                _apply_cutout(cutout, lx, wx, ly, wy, h, x0=x0, y0=y0)

    assert builder.part is not None, "Failed to generate spacer solid"
    part = builder.part

    # Optional mirroring (e.g. invert L-shape for opposite drawer corner)
    if params.mirror_x:
        part = part.mirror(Plane.YZ)
    if params.mirror_y:
        part = part.mirror(Plane.XZ)
    if params.mirror_x or params.mirror_y:
        bb = part.bounding_box()
        part = part.translate((-bb.min.X, -bb.min.Y, -bb.min.Z))

    return part


if __name__ == "__main__":
    # Single source of truth: dataclass defaults take effect directly
    params = SpacerParams()
    spacer = create_spacer(params)

    # Standardized exports to the exports/ directory alongside this script
    if EXPORT_STEP or EXPORT_STL:
        exports_path = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_path.mkdir(parents=True, exist_ok=True)
        is_junction = (params.leg_x_length > 0 and params.leg_y_length > 0)
        if is_junction:
            dim_str = f"{int(params.leg_x_length)}x{int(params.leg_y_length)}x{int(params.height)}mm"
            x0 = _resolve_leg_position(
                params.leg_y_align, params.leg_y_offset, params.leg_x_length, params.leg_y_width, "leg_y"
            )
            y0 = _resolve_leg_position(
                params.leg_x_align, params.leg_x_offset, params.leg_y_length, params.leg_x_width, "leg_x"
            )
            mid_x = 1e-3 < x0 < (params.leg_x_length - params.leg_y_width - 1e-3)
            mid_y = 1e-3 < y0 < (params.leg_y_length - params.leg_x_width - 1e-3)
            if mid_x and mid_y:
                variant = "cross"
            elif mid_x or mid_y:
                variant = "t_shape"
            else:
                variant = "corner"
        elif params.leg_x_length > 0:
            dim_str = f"{int(params.leg_x_length)}x{int(params.leg_x_width)}x{int(params.height)}mm"
            variant = "straight_x"
        else:
            dim_str = f"{int(params.leg_y_length)}x{int(params.leg_y_width)}x{int(params.height)}mm"
            variant = "straight_y"

        if params.mirror_x and params.mirror_y:
            variant += "_mirrored_xy"
        elif params.mirror_x:
            variant += "_mirrored_x"
        elif params.mirror_y:
            variant += "_mirrored_y"

        stem = f"spacer_{dim_str}_{variant}"

        if EXPORT_STL:
            stl_file = exports_path / f"{stem}.stl"
            export_stl(spacer, str(stl_file))
            print(f"Exported STL:  {stl_file}")

        if EXPORT_STEP:
            step_file = exports_path / f"{stem}.step"
            export_step(spacer, str(step_file))
            print(f"Exported STEP: {step_file}")

    # Display in ocp_viewer / ocp_vscode viewer if available
    try:
        from ocp_viewer import set_defaults, show
        set_defaults(orbit_control=True)
    except ImportError:
        try:
            from ocp_vscode import set_defaults, show
            set_defaults(orbit_control=True)
        except Exception:
            def show(*args, **kwargs):
                pass

    show(spacer)
