"""
Parametric C-Clip Spacer (build123d Model)

Snap-on C-clip shaft spacer designed to add precise axial spacing along a
cylindrical rod or shaft without requiring disassembly.

Features:
- Parametric spacer thickness (axial space added along the shaft).
- Parametric inside diameter (rod/shaft size) with optional 3D-print fit clearance.
- Parametric outside diameter.
- Snap-on C-opening with configurable opening angle and smooth rounded jaw tips.
- Smooth inside-edge removal cutout bordering the shaft (spine pry/grab pocket)
  for easy removal with a fingernail, pick, or small tool without creating sharp
  stress risers.
- Optional subtle top/bottom edge chamfer to eliminate print-bed elephant's foot
  and sharp edges.
"""

import math
from dataclasses import dataclass
from pathlib import Path

from build123d import *

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False      # Enable/disable STL file export (default: False)
EXPORT_STEP: bool = False     # Enable/disable STEP file export (default: False)
OUTPUT_DIR: str = "exports"   # Relative subfolder alongside the script


@dataclass
class CClipSpacerParams:
    """Parameters for the parametric snap-on C-clip spacer."""

    # Primary Spacer Dimensions
    thickness: float = 5.0                 # Axial thickness / space added by spacer in mm (Z height)
    inside_diameter: float = 44.0          # Nominal diameter of the rod/shaft to fit in mm
    outside_diameter: float = 72.0         # Outer diameter of the spacer in mm
    fit_clearance: float = 0.2             # Diametral bore clearance in mm (bore = inside_diameter + fit_clearance)

    # Snap-On C-Opening Geometry
    opening_angle: float = 90.0           # Angular width of the C-opening in degrees (< 180 for shaft retention)
    tip_fillet: float = 4.0                # Rounding radius on the C-opening jaw tips in mm (0.0 for crisp tips)

    # Inside-Edge Removal Cutout (bordering the shaft)
    removal_notch_enabled: bool = True     # Master toggle for the inside-edge grab/remove cutout
    removal_notch_width: float = 24.0       # Tangential width of the inside-edge cutout in mm
    removal_notch_depth: float = 6.0       # Radial depth of cutout extending outward from inner bore in mm
    removal_notch_angle: float = 180.0     # Angular position of cutout in degrees (180 = spine opposite C-opening)
    removal_notch_fillet: float = 0.6      # Transition fillet where cutout meets inner bore in mm (0.0 for crisp edge)

    # Top & Bottom Edge Treatment
    edge_chamfer_enabled: bool = True      # Master toggle for subtle top/bottom perimeter bevel
    edge_chamfer: float = 0.3              # Chamfer size on top and bottom edges in mm


def _shortest_angle_diff_deg(a: float, b: float) -> float:
    """Return absolute shortest angular distance in degrees in [0, 180]."""
    diff = (a - b) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return abs(diff)


def create_c_clip_spacer(params: CClipSpacerParams) -> Part:
    """Generate a parametric snap-on C-clip spacer solid body."""
    if params.thickness <= 0:
        raise ValueError(f"thickness must be positive, got {params.thickness}")
    if params.inside_diameter <= 0:
        raise ValueError(f"inside_diameter must be positive, got {params.inside_diameter}")

    bore_diameter = params.inside_diameter + params.fit_clearance
    if bore_diameter <= 0:
        raise ValueError(
            f"Effective bore diameter ({bore_diameter:.3f}mm) must be positive "
            f"(inside_diameter={params.inside_diameter}, fit_clearance={params.fit_clearance})"
        )
    if params.outside_diameter <= bore_diameter:
        raise ValueError(
            f"outside_diameter ({params.outside_diameter}mm) must be greater than "
            f"effective bore diameter ({bore_diameter:.3f}mm)"
        )
    if not (0.0 < params.opening_angle < 180.0):
        raise ValueError(
            f"opening_angle must be strictly between 0 and 180 degrees for shaft retention, "
            f"got {params.opening_angle}"
        )
    if params.tip_fillet < 0:
        raise ValueError(f"tip_fillet must be non-negative, got {params.tip_fillet}")
    if params.edge_chamfer < 0:
        raise ValueError(f"edge_chamfer must be non-negative, got {params.edge_chamfer}")

    r_in = bore_diameter / 2.0
    r_out = params.outside_diameter / 2.0
    wall_thickness = r_out - r_in
    half_open_rad = math.radians(params.opening_angle / 2.0)

    # Validate removal notch geometry before constructing CAD shapes
    notch_half_w = params.removal_notch_width / 2.0
    notch_x_entry = 0.0
    if params.removal_notch_enabled:
        if params.removal_notch_width <= 0:
            raise ValueError(f"removal_notch_width must be positive, got {params.removal_notch_width}")
        if params.removal_notch_depth <= 0:
            raise ValueError(f"removal_notch_depth must be positive, got {params.removal_notch_depth}")
        if params.removal_notch_fillet < 0:
            raise ValueError(f"removal_notch_fillet must be non-negative, got {params.removal_notch_fillet}")
        if params.removal_notch_width >= bore_diameter * 0.9:
            raise ValueError(
                f"removal_notch_width ({params.removal_notch_width}mm) must be smaller than "
                f"90% of bore diameter ({bore_diameter * 0.9:.2f}mm)"
            )
        if params.removal_notch_depth >= wall_thickness * 0.85:
            raise ValueError(
                f"removal_notch_depth ({params.removal_notch_depth}mm) must be less than "
                f"85% of radial wall thickness ({wall_thickness * 0.85:.2f}mm) to preserve spine strength"
            )

        notch_half_angle_deg = math.degrees(math.asin(notch_half_w / r_in))
        angular_sep = _shortest_angle_diff_deg(params.removal_notch_angle, 0.0)
        min_required_sep = params.opening_angle / 2.0 + notch_half_angle_deg + 5.0
        if angular_sep < min_required_sep:
            raise ValueError(
                f"removal_notch_angle ({params.removal_notch_angle} deg) overlaps or is too close to "
                f"the C-opening ({params.opening_angle} deg centered at 0 deg)"
            )
        notch_x_entry = math.sqrt(r_in * r_in - notch_half_w * notch_half_w)

    # Resolve safe 2D corner fillet radii
    eff_tip_fillet = min(params.tip_fillet, wall_thickness * 0.45) if params.tip_fillet > 0 else 0.0
    eff_notch_fillet = 0.0
    if params.removal_notch_enabled and params.removal_notch_fillet > 0:
        eff_notch_fillet = min(
            params.removal_notch_fillet,
            params.removal_notch_depth * 0.45,
            (wall_thickness - params.removal_notch_depth) * 0.45,
            params.removal_notch_width * 0.25,
        )

    # Build trimmed inside-edge notch cutter outside main sketch so it never crosses bore center
    notch_cutter = None
    if params.removal_notch_enabled:
        x_radius = (r_in + params.removal_notch_depth) - notch_x_entry
        with BuildSketch(Plane.XY) as notch_sk:
            with Locations((notch_x_entry, 0.0)):
                Ellipse(x_radius=x_radius, y_radius=notch_half_w)
            clip_w = r_in + params.removal_notch_depth + 1.0
            with Locations((clip_w / 2.0, 0.0)):
                Rectangle(width=clip_w, height=params.removal_notch_width + 1.0, mode=Mode.INTERSECT)
        notch_cutter = notch_sk.sketch.rotate(Axis.Z, params.removal_notch_angle)

    with BuildPart() as spacer:
        with BuildSketch(Plane.XY) as profile:
            # 1. Base ring
            Circle(radius=r_out)
            Circle(radius=r_in, mode=Mode.SUBTRACT)

            # 2. C-opening wedge centered on +X (multi-segment arc clearance up to 179 deg)
            r_cut = r_out * 1.5
            wedge_angles = [
                -half_open_rad,
                -half_open_rad * 0.5,
                0.0,
                half_open_rad * 0.5,
                half_open_rad,
            ]
            wedge_pts = [(0.0, 0.0)] + [
                (r_cut * math.cos(a), r_cut * math.sin(a)) for a in wedge_angles
            ]
            Polygon(*wedge_pts, mode=Mode.SUBTRACT)

            # 3. Inside-edge grab/removal cutout bordering the shaft
            if notch_cutter is not None:
                add(notch_cutter, mode=Mode.SUBTRACT)

                # Smoothly fillet the two entry corners where the notch meets the inner bore
                if eff_notch_fillet > 1e-3:
                    angle_rad = math.radians(params.removal_notch_angle)
                    expected_entry_pts = []
                    for sign in (-1.0, 1.0):
                        lx = notch_x_entry
                        ly = sign * notch_half_w
                        gx = lx * math.cos(angle_rad) - ly * math.sin(angle_rad)
                        gy = lx * math.sin(angle_rad) + ly * math.cos(angle_rad)
                        expected_entry_pts.append((gx, gy))

                    notch_verts = profile.vertices().filter_by(
                        lambda v: any(
                            math.hypot(v.X - px, v.Y - py) < 0.05
                            for px, py in expected_entry_pts
                        )
                    )
                    if len(notch_verts) > 0:
                        fillet(notch_verts, radius=eff_notch_fillet)

            # 4. Round the four C-opening jaw tips (inner glide corners & outer handling corners)
            if eff_tip_fillet > 1e-3:
                expected_tip_pts = []
                for r_pt in (r_in, r_out):
                    for sign in (-1.0, 1.0):
                        a = sign * half_open_rad
                        expected_tip_pts.append((r_pt * math.cos(a), r_pt * math.sin(a)))

                tip_verts = profile.vertices().filter_by(
                    lambda v: any(
                        math.hypot(v.X - px, v.Y - py) < 0.05
                        for px, py in expected_tip_pts
                    )
                )
                if len(tip_verts) > 0:
                    fillet(tip_verts, radius=eff_tip_fillet)

        # 5. Extrude axially to spacer thickness (Z = 0 to thickness)
        extrude(amount=params.thickness)

        # 6. Subtle top & bottom perimeter edge chamfer for clean bed release and burr-free handling
        if params.edge_chamfer_enabled and params.edge_chamfer > 0:
            remaining_spine = (
                wall_thickness - params.removal_notch_depth
                if params.removal_notch_enabled
                else wall_thickness
            )
            max_safe_chamfer = min(
                params.thickness * 0.35,
                wall_thickness * 0.3,
                remaining_spine * 0.35,
            )
            if eff_tip_fillet > 0:
                max_safe_chamfer = min(max_safe_chamfer, eff_tip_fillet * 0.8)
            if eff_notch_fillet > 0:
                max_safe_chamfer = min(max_safe_chamfer, eff_notch_fillet * 0.8)

            eff_chamfer = min(params.edge_chamfer, max_safe_chamfer)
            if eff_chamfer > 1e-3:
                top_face = spacer.faces().sort_by(Axis.Z)[-1]
                bot_face = spacer.faces().sort_by(Axis.Z)[0]
                chamfer(top_face.edges() + bot_face.edges(), length=eff_chamfer)

    assert spacer.part is not None, "C-clip spacer generation failed"
    return spacer.part


if __name__ == "__main__":
    # Single source of truth: dataclass defaults take effect directly
    params = CClipSpacerParams()
    spacer_part = create_c_clip_spacer(params)

    # Standardized exports to the exports/ directory alongside this script
    if EXPORT_STEP or EXPORT_STL:
        exports_path = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_path.mkdir(parents=True, exist_ok=True)

        variant = "notch" if params.removal_notch_enabled else "plain"
        stem = (
            f"c_clip_spacer_{params.inside_diameter:g}x"
            f"{params.outside_diameter:g}x{params.thickness:g}mm_{variant}"
        )

        if EXPORT_STL:
            stl_file = exports_path / f"{stem}.stl"
            export_stl(spacer_part, str(stl_file))
            print(f"Exported STL:  {stl_file}")

        if EXPORT_STEP:
            step_file = exports_path / f"{stem}.step"
            export_step(spacer_part, str(step_file))
            print(f"Exported STEP: {step_file}")

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

    show(spacer_part)
