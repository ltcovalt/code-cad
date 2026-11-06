"""
Gridfinity Drawer Gap Spacer Generator (build123d)

Generates precision drawer gap spacers designed to sit on top of Gridfinity
baseplate padding to prevent bins from shifting and stop small parts or fasteners
from falling down into the gaps between the bins and drawer walls.

Clean, Unified Leg Architecture:
- Setting both `leg_x_length > 0` and `leg_y_length > 0` generates an L-shaped corner piece.
- Setting `leg_y_length = 0` generates a straight front/back spacer (Leg X).
- Setting `leg_x_length = 0` generates a straight side spacer (Leg Y).
- Each leg has independent length and width (e.g. 15.5mm front vs 15.0mm side).
- Height (Z) is shared across both legs.
- Pre-calibrated R4 inner corner radius matching standard Gridfinity bin profiles.
- Optional hollow underside mode (saves filament and print time).
- Optional top finger-lift scoop for effortless removal from tight drawers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from build123d import *

try:
    from ocp_vscode import set_defaults, show
    set_defaults(orbit_control=True)
    HAS_OCP_VIEWER = True
except Exception:
    HAS_OCP_VIEWER = False
    def show(*args, **kwargs):
        pass

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STEP: bool = False     # Save .step file on execution (default: False)
EXPORT_STL: bool = False      # Save .stl file on execution (default: False)
OUTPUT_DIR: str = "exports"   # Relative subfolder alongside this script


@dataclass
class SpacerParams:
    """Single source of truth parameters for Gridfinity drawer gap spacers."""

    # --------------------------------------------------------------------------
    # Shared Height (Z)
    # --------------------------------------------------------------------------
    height: float = 3.0                # Spacer height above baseplate padding in mm (Z dimension)

    # --------------------------------------------------------------------------
    # Leg X (e.g. Front / Back drawer wall)
    # Set leg_y_length = 0 to generate a straight Leg X spacer!
    # --------------------------------------------------------------------------
    leg_x_length: float = 100.0         # Length along X wall in mm (set 0 to omit)
    leg_x_width: float = 15.0           # Width / gap thickness of X leg in mm (e.g. front spacer gap)

    # --------------------------------------------------------------------------
    # Leg Y (e.g. Side drawer wall)
    # Set leg_x_length = 0 to generate a straight Leg Y spacer!
    # --------------------------------------------------------------------------
    leg_y_length: float = 100.0          # Length along Y wall in mm (set 0 to omit)
    leg_y_width: float = 15.0           # Width / gap thickness of Y leg in mm (e.g. side spacer gap)

    # --------------------------------------------------------------------------
    # Corner Radii & Top Edge Treatment
    # --------------------------------------------------------------------------
    corner_radius: float = 2.0          # General vertical corner radius in mm (XY profile corners)
    outer_corner_radius: Optional[float] = None  # Outer drawer corner radius in mm (None = corner_radius)
    inner_corner_radius: Optional[float] = 4.0   # Inner corner radius facing Gridfinity bin in mm (Gridfinity R4; None = corner_radius)
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
    # Optional / Backwards Compatibility Aliases
    # --------------------------------------------------------------------------
    spacer_type: Optional[str] = None   # Optional override: "straight" or "corner" (auto-inferred if None)
    straight_leg: Optional[str] = None  # Optional: "x" or "y" if spacer_type="straight" and both lengths > 0
    x: Optional[float] = None           # Legacy alias: sets leg_x_length
    y: Optional[float] = None           # Legacy alias: sets leg_x_width
    z: Optional[float] = None           # Legacy alias: sets height

    def __post_init__(self):
        """Handle legacy or convenience aliases."""
        if self.z is not None:
            self.height = self.z
        if self.x is not None:
            self.leg_x_length = self.x
        if self.y is not None:
            self.leg_x_width = self.y

        # Handle explicit spacer_type="straight" when user didn't zero out a leg
        if self.spacer_type is not None:
            st = self.spacer_type.strip().lower()
            if st in ("straight", "linear", "line", "bar"):
                if self.leg_x_length > 0 and self.leg_y_length > 0:
                    if self.straight_leg and self.straight_leg.lower() == "y":
                        self.leg_x_length = 0.0
                    else:
                        self.leg_y_length = 0.0


# Type alias
GridfinitySpacerParams = SpacerParams


def create_spacer(params: SpacerParams) -> Solid:
    """
    Decoupled generator function for Gridfinity drawer gap spacers.

    - leg_x_length > 0 and leg_y_length > 0: generates L-shaped corner piece.
    - leg_x_length > 0 and leg_y_length <= 0: generates straight Leg X spacer.
    - leg_x_length <= 0 and leg_y_length > 0: generates straight Leg Y spacer.
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

    is_corner = (lx > 0 and ly > 0)

    # Validation checks
    if is_corner:
        if wx <= 0 or wy <= 0:
            raise ValueError(f"Both leg widths must be positive: got leg_x_width={wx}, leg_y_width={wy}")
        if lx <= wy:
            raise ValueError(f"leg_x_length ({lx}mm) must be strictly greater than leg_y_width ({wy}mm)")
        if ly <= wx:
            raise ValueError(f"leg_y_length ({ly}mm) must be strictly greater than leg_x_width ({wx}mm)")
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
            if is_corner:
                # Union of the two perpendicular arms
                Rectangle(lx, wx, align=(Align.MIN, Align.MIN))
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
            min_dim = min(wx, wy) if is_corner else (wx if lx > 0 else wy)
            eff_wall = min(params.wall_thickness, min_dim / 2.0 - 0.5)
            if eff_wall > 0.5:
                with BuildSketch(Plane.XY) as sk_inner:
                    offset(sk.sketch, amount=-eff_wall)
                extrude(sk_inner.sketch, amount=h - params.top_thickness, mode=Mode.SUBTRACT)

        # Vertical corner fillets for corner piece
        if is_corner:
            eff_rout = max(0.0, min(r_outer, min(lx, ly) * 0.45))
            eff_rin = max(0.0, min(r_inner, min(wx, wy) * 0.85, (lx - wy) * 0.85, (ly - wx) * 0.85))

            if eff_rout > 0.05:
                outer_e = builder.edges().filter_by(Axis.Z).sort_by(
                    lambda e: e.center().X**2 + e.center().Y**2
                )[0]
                fillet(outer_e, radius=eff_rout)

            if eff_rin > 0.05:
                inner_e = builder.edges().filter_by(Axis.Z).sort_by(
                    lambda e: (e.center().X - wy)**2 + (e.center().Y - wx)**2
                )[0]
                fillet(inner_e, radius=eff_rin)

            if r_end > 0.05:
                end_edges = [
                    e for e in builder.edges().filter_by(Axis.Z)
                    if abs(e.center().X - lx) < 1e-2 or abs(e.center().Y - ly) < 1e-2
                ]
                if end_edges:
                    fillet(end_edges, radius=r_end)

        # Top perimeter edge treatment (fillet or chamfer)
        if r_top > 0.05 and h > r_top:
            min_edge = min(wx, wy) if is_corner else (wx if lx > 0 else wy)
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
            if is_corner:
                cx = wy / 2.0
                cy = wx / 2.0
            elif lx > 0:
                cx = lx / 2.0
                cy = wx / 2.0
            else:
                cx = wy / 2.0
                cy = ly / 2.0
            cz = h + fn_r - fn_d
            with Locations((cx, cy, cz)):
                Sphere(radius=fn_r, mode=Mode.SUBTRACT)

    assert builder.part is not None, "Failed to generate spacer solid"
    return builder.part


# Generator alias
create_gridfinity_spacer = create_spacer


if __name__ == "__main__":
    # Single source of truth: dataclass defaults take effect directly
    params = SpacerParams()
    spacer = create_spacer(params)

    # Standardized exports to the exports/ directory alongside this script
    if EXPORT_STEP or EXPORT_STL:
        exports_path = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_path.mkdir(parents=True, exist_ok=True)
        kind_name = "corner" if (params.leg_x_length > 0 and params.leg_y_length > 0) else "straight"
        base_name = f"gridfinity_{kind_name}_spacer"

        if EXPORT_STEP:
            step_file = exports_path / f"{base_name}.step"
            export_step(spacer, str(step_file))
            print(f"Exported STEP: {step_file}")

        if EXPORT_STL:
            stl_file = exports_path / f"{base_name}.stl"
            export_stl(spacer, str(stl_file))
            print(f"Exported STL:  {stl_file}")

    # Display in ocp_vscode viewer if available
    show(spacer)
