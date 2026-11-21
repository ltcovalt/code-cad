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
EXPORT_STL: bool = False      # Enable/disable STL file export (default: False)
EXPORT_STEP: bool = False     # Enable/disable STEP file export (default: False)
OUTPUT_DIR: str = "exports"   # Relative subfolder alongside the script


@dataclass
class CoreParams:
    """Primary C-clip spacer dimensions."""

    thickness: float = param(
        12.0,
        desc="Axial height added along shaft",
        unit="mm", min=2.0, max=60.0, step=0.5,
    )
    inside_diameter: float = param(
        44.0,
        desc="Nominal rod/shaft diameter",
        unit="mm", min=6.0, max=120.0, step=0.5,
    )
    outside_diameter: float = param(
        76.0,
        desc="Outer spacer diameter",
        unit="mm", min=12.0, max=180.0, step=0.5,
    )
    fit_clearance: float = param(
        0.2,
        desc="Added to inside diameter for bore fit",
        unit="mm", min=-0.5, max=1.0, step=0.05,
    )


@dataclass
class JawParams:
    """Snap-on C-opening jaw geometry."""

    opening_angle: float = param(
        95.0,
        desc="Inner C-opening angle (< 180° for retention)",
        unit="°", min=20.0, max=165.0, step=1.0,
    )
    jaw_flare_angle: float = param(
        8.0,
        desc="Jaw cut angle (0° = parallel slot)",
        unit="°", min=-20.0, max=45.0, step=1.0,
    )
    jaw_curve_depth: float = param(
        1.2,
        desc="Concave bow depth along jaw face (0 = straight)",
        unit="mm", min=0.0, max=6.0, step=0.1,
    )
    inner_tip_fillet: float = param(
        4.0,
        desc="Rounding where jaw meets inner bore (0 = crisp)",
        unit="mm", min=0.0, max=10.0, step=0.2,
    )
    outer_tip_fillet: float = param(
        2.4,
        desc="Outer jaw tip rounding radius (0 = crisp)",
        unit="mm", min=0.0, max=10.0, step=0.2,
    )


@dataclass
class RemovalNotchParams:
    """Inside-edge removal cutout bordering the shaft."""

    enabled: bool = param(
        True,
        desc="Add inside-edge grab/pry cutout",
    )
    width: float = param(
        32.0,
        desc="Tangential width of cutout",
        unit="mm", min=4.0, max=60.0, step=1.0,
    )
    depth: float = param(
        8.0,
        desc="Radial depth outward from inner bore",
        unit="mm", min=1.0, max=25.0, step=0.5,
    )
    angle: float = param(
        180.0,
        desc="Angular position (180° = opposite opening)",
        unit="°", min=0.0, max=360.0, step=5.0,
    )
    fillet: float = param(
        0.6,
        desc="Transition fillet at inner bore (0 = crisp)",
        unit="mm", min=0.0, max=5.0, step=0.1,
    )


@dataclass
class EdgeChamferParams:
    """Top and bottom perimeter edge bevel."""

    enabled: bool = param(
        True,
        desc="Add subtle top/bottom perimeter bevel",
    )
    size: float = param(
        0.3,
        desc="Top and bottom edge chamfer size",
        unit="mm", min=0.0, max=3.0, step=0.1,
    )


@dataclass
class CClipSpacerParams:
    """Parameters for the parametric snap-on C-clip spacer."""

    core: CoreParams = group(CoreParams)
    jaw: JawParams = group(JawParams)
    removal_notch: RemovalNotchParams = group(RemovalNotchParams)
    edge_chamfer: EdgeChamferParams = group(EdgeChamferParams)


def _shortest_angle_diff_deg(a: float, b: float) -> float:
    """Return absolute shortest angular distance in degrees in [0, 180]."""
    diff = (a - b) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return abs(diff)


def _solve_nose_and_jaw_arc(
    r_out: float,
    x_in: float,
    y_in: float,
    dx: float,
    dy: float,
    flare_rad: float,
    b_dot: float,
    h_jaw: float,
    wall_thickness: float,
    requested_outer_fillet: float,
    requested_jaw_curve: float,
) -> dict[str, float | tuple[float, float]] | None:
    """Solve G1-tangent outer nose circle and concave C-curve jaw arc geometry.

    Returns ``None`` when ``requested_outer_fillet <= 0`` (or cannot fit), in
    which case the caller falls back to a crisp outer jaw tip.
    """
    if requested_outer_fillet <= 0.0:
        return None

    hi_r = min(requested_outer_fillet, (r_out - h_jaw) * 0.45, wall_thickness * 0.65)
    if hi_r <= 1e-3:
        return None

    def _tip_center(r: float) -> tuple[float, float] | None:
        rad_sq = (r_out - r) ** 2 - (h_jaw + r) ** 2
        if rad_sq <= 0.0:
            return None
        u_tip = math.sqrt(rad_sq)
        if u_tip <= b_dot + max(0.5, r * 0.25):
            return None
        return (
            u_tip * dx - (h_jaw + r) * dy,
            u_tip * dy + (h_jaw + r) * dx,
        )

    center = _tip_center(hi_r)
    if center is None:
        lo_r, cur_hi = 0.0, hi_r
        for _ in range(24):
            mid_r = 0.5 * (lo_r + cur_hi)
            if _tip_center(mid_r) is not None:
                lo_r = mid_r
            else:
                cur_hi = mid_r
        r_tip = lo_r
        center = _tip_center(r_tip)
        if center is None or r_tip <= 1e-3:
            return None
    else:
        r_tip = hi_r

    cx, cy = center
    outer_tan_rad = math.atan2(cy, cx)
    px_tan = r_out * math.cos(outer_tan_rad)
    py_tan = r_out * math.sin(outer_tan_rad)
    base_phi = flare_rad - math.pi / 2.0

    def _eval_delta(delta: float) -> dict[str, float | tuple[float, float]] | None:
        phi = base_phi - delta
        nose_sweep = (outer_tan_rad - phi) % (2.0 * math.pi)
        if nose_sweep <= 1e-3 or nose_sweep >= math.radians(225.0):
            return None

        ux, uy = math.cos(phi), math.sin(phi)
        tx, ty = cx + r_tip * ux, cy + r_tip * uy
        vx, vy = x_in - tx, y_in - ty
        chord = math.hypot(vx, vy)
        if chord <= 0.5:
            return None

        mid_nose_rad = outer_tan_rad - 0.5 * nose_sweep
        nose_mid = (
            cx + r_tip * math.cos(mid_nose_rad),
            cy + r_tip * math.sin(mid_nose_rad),
        )

        if delta <= 1e-5:
            return {
                "r_tip": r_tip,
                "outer_tan_rad": outer_tan_rad,
                "p_tan": (px_tan, py_tan),
                "nose_mid": nose_mid,
                "p_tan_jaw": (tx, ty),
                "jaw_mid": (0.5 * (tx + x_in), 0.5 * (ty + y_in)),
                "sag": 0.0,
                "chord": chord,
                "in_dir": (-vx / chord, -vy / chord),
            }

        denom = 2.0 * (vx * ux + vy * uy)
        if denom <= 1e-6:
            return None
        r_jaw = (vx * vx + vy * vy) / denom
        if r_jaw <= 0.5 * chord + 1e-5:
            return None

        sag = r_jaw - math.sqrt(max(0.0, r_jaw * r_jaw - 0.25 * chord * chord))
        cx_jaw = tx + r_jaw * ux
        cy_jaw = ty + r_jaw * uy
        a_start = math.atan2(ty - cy_jaw, tx - cx_jaw)
        a_end = math.atan2(y_in - cy_jaw, x_in - cx_jaw)
        jaw_sweep = (a_end - a_start) % (2.0 * math.pi)
        if jaw_sweep <= 1e-5 or jaw_sweep >= math.radians(150.0):
            return None

        mid_jaw_rad = a_start + 0.5 * jaw_sweep
        jaw_mid = (
            cx_jaw + r_jaw * math.cos(mid_jaw_rad),
            cy_jaw + r_jaw * math.sin(mid_jaw_rad),
        )
        if math.hypot(jaw_mid[0], jaw_mid[1]) >= r_out * 0.96:
            return None

        return {
            "r_tip": r_tip,
            "outer_tan_rad": outer_tan_rad,
            "p_tan": (px_tan, py_tan),
            "nose_mid": nose_mid,
            "p_tan_jaw": (tx, ty),
            "jaw_mid": jaw_mid,
            "sag": sag,
            "chord": chord,
            "in_dir": (math.sin(a_end), -math.cos(a_end)),
        }

    straight = _eval_delta(0.0)
    if straight is None:
        return None
    if requested_jaw_curve <= 1e-4:
        return straight

    target_sag = min(
        requested_jaw_curve,
        straight["chord"] * 0.22,
        wall_thickness * 0.45,
    )
    if target_sag <= 1e-4:
        return straight

    lo_d, hi_d = 0.0, math.radians(70.0)
    best = straight
    for _ in range(30):
        mid_d = 0.5 * (lo_d + hi_d)
        cand = _eval_delta(mid_d)
        if cand is None or cand["sag"] > min(
            target_sag, cand["chord"] * 0.25, wall_thickness * 0.45
        ):
            hi_d = mid_d
        else:
            best = cand
            lo_d = mid_d

    return best


def create_c_clip_spacer(params: CClipSpacerParams) -> Part:
    """Generate a parametric snap-on C-clip spacer solid body."""
    core = params.core
    jaw = params.jaw
    notch = params.removal_notch
    chamf = params.edge_chamfer

    if core.thickness <= 0:
        raise ValueError(f"thickness must be positive, got {core.thickness}")
    if core.inside_diameter <= 0:
        raise ValueError(f"inside_diameter must be positive, got {core.inside_diameter}")

    bore_diameter = core.inside_diameter + core.fit_clearance
    if bore_diameter <= 0:
        raise ValueError(
            f"Effective bore diameter ({bore_diameter:.3f}mm) must be positive "
            f"(inside_diameter={core.inside_diameter}, fit_clearance={core.fit_clearance})"
        )
    if core.outside_diameter <= bore_diameter:
        raise ValueError(
            f"outside_diameter ({core.outside_diameter}mm) must be greater than "
            f"effective bore diameter ({bore_diameter:.3f}mm)"
        )
    if not (0.0 < jaw.opening_angle < 180.0):
        raise ValueError(
            f"opening_angle must be strictly between 0 and 180 degrees for shaft retention, "
            f"got {jaw.opening_angle}"
        )
    if not (-45.0 < jaw.jaw_flare_angle < 90.0):
        raise ValueError(
            f"jaw_flare_angle must be strictly between -45 and 90 degrees, "
            f"got {jaw.jaw_flare_angle}"
        )
    if jaw.jaw_curve_depth < 0:
        raise ValueError(f"jaw_curve_depth must be non-negative, got {jaw.jaw_curve_depth}")
    if jaw.inner_tip_fillet < 0:
        raise ValueError(f"inner_tip_fillet must be non-negative, got {jaw.inner_tip_fillet}")
    if jaw.outer_tip_fillet < 0:
        raise ValueError(f"outer_tip_fillet must be non-negative, got {jaw.outer_tip_fillet}")
    if chamf.size < 0:
        raise ValueError(f"edge_chamfer.size must be non-negative, got {chamf.size}")

    r_in = bore_diameter / 2.0
    r_out = core.outside_diameter / 2.0
    wall_thickness = r_out - r_in
    half_open_rad = math.radians(jaw.opening_angle / 2.0)
    flare_rad = math.radians(jaw.jaw_flare_angle)

    # Inner jaw corner and ray-circle intersection with outer perimeter
    x_in = r_in * math.cos(half_open_rad)
    y_in = r_in * math.sin(half_open_rad)
    dx = math.cos(flare_rad)
    dy = math.sin(flare_rad)
    b_dot = x_in * dx + y_in * dy
    c_val = r_in * r_in - r_out * r_out
    t_out = -b_dot + math.sqrt(b_dot * b_dot - c_val)
    x_out = x_in + t_out * dx
    y_out = y_in + t_out * dy
    if y_out <= 1e-3:
        raise ValueError(
            f"jaw_flare_angle ({jaw.jaw_flare_angle} deg) causes opposing jaws to cross "
            f"before reaching outside_diameter ({core.outside_diameter}mm)"
        )
    jaw_length = t_out

    # Validate removal notch geometry before constructing CAD shapes
    notch_half_w = notch.width / 2.0
    notch_x_entry = 0.0
    if notch.enabled:
        if notch.width <= 0:
            raise ValueError(f"removal_notch.width must be positive, got {notch.width}")
        if notch.depth <= 0:
            raise ValueError(f"removal_notch.depth must be positive, got {notch.depth}")
        if notch.fillet < 0:
            raise ValueError(f"removal_notch.fillet must be non-negative, got {notch.fillet}")
        if notch.width >= bore_diameter * 0.9:
            raise ValueError(
                f"removal_notch.width ({notch.width}mm) must be smaller than "
                f"90% of bore diameter ({bore_diameter * 0.9:.2f}mm)"
            )
        if notch.depth >= wall_thickness * 0.85:
            raise ValueError(
                f"removal_notch.depth ({notch.depth}mm) must be less than "
                f"85% of radial wall thickness ({wall_thickness * 0.85:.2f}mm) to preserve spine strength"
            )

        notch_half_angle_deg = math.degrees(math.asin(notch_half_w / r_in))
        angular_sep = _shortest_angle_diff_deg(notch.angle, 0.0)
        min_required_sep = jaw.opening_angle / 2.0 + notch_half_angle_deg + 5.0
        if angular_sep < min_required_sep:
            raise ValueError(
                f"removal_notch.angle ({notch.angle} deg) overlaps or is too close to "
                f"the C-opening ({jaw.opening_angle} deg centered at 0 deg)"
            )
        notch_x_entry = math.sqrt(r_in * r_in - notch_half_w * notch_half_w)

    # Solve outer nose circle + G1-tangent C-curve jaw geometry (or fall back to sharp outer tip)
    h_jaw_base = -x_in * dy + y_in * dx
    nose_sol = _solve_nose_and_jaw_arc(
        r_out=r_out,
        x_in=x_in,
        y_in=y_in,
        dx=dx,
        dy=dy,
        flare_rad=flare_rad,
        b_dot=b_dot,
        h_jaw=h_jaw_base,
        wall_thickness=wall_thickness,
        requested_outer_fillet=jaw.outer_tip_fillet,
        requested_jaw_curve=jaw.jaw_curve_depth,
    )

    t_in_arc_x, t_in_arc_y = -math.sin(half_open_rad), math.cos(half_open_rad)
    if nose_sol is not None:
        eff_outer_fillet = float(nose_sol["r_tip"])
        eff_jaw_curve = float(nose_sol["sag"])
        jaw_chord_len = float(nose_sol["chord"])
        dx_in_jaw, dy_in_jaw = nose_sol["in_dir"]  # type: ignore[misc]
    else:
        eff_outer_fillet = 0.0
        x_mid = 0.5 * (x_in + x_out)
        y_mid = 0.5 * (y_in + y_out)
        eff_jaw_curve = (
            min(jaw.jaw_curve_depth, jaw_length * 0.22, wall_thickness * 0.45)
            if jaw.jaw_curve_depth > 0
            else 0.0
        )
        while (
            eff_jaw_curve > 1e-3
            and math.hypot(x_mid - eff_jaw_curve * dy, y_mid + eff_jaw_curve * dx)
            >= r_out * 0.96
        ):
            eff_jaw_curve *= 0.8
        x_mid_arc = x_mid - eff_jaw_curve * dy
        y_mid_arc = y_mid + eff_jaw_curve * dx
        alpha_arc = (
            2.0 * math.atan2(2.0 * eff_jaw_curve, jaw_length)
            if eff_jaw_curve > 1e-4
            else 0.0
        )
        jaw_chord_len = jaw_length
        dx_in_jaw = math.cos(flare_rad + alpha_arc)
        dy_in_jaw = math.sin(flare_rad + alpha_arc)

    cos_gamma_in = max(
        -0.999, min(0.999, t_in_arc_x * dx_in_jaw + t_in_arc_y * dy_in_jaw)
    )
    k_in = 1.0 / math.tan(math.acos(cos_gamma_in) / 2.0)
    max_inner_by_jaw = (jaw_chord_len * 0.45) / max(k_in, 1e-6)
    eff_inner_fillet = (
        min(jaw.inner_tip_fillet, wall_thickness * 0.75, max_inner_by_jaw)
        if jaw.inner_tip_fillet > 0 and cos_gamma_in > -0.995
        else 0.0
    )

    eff_notch_fillet = 0.0
    if notch.enabled and notch.fillet > 0:
        eff_notch_fillet = min(
            notch.fillet,
            notch.depth * 0.45,
            (wall_thickness - notch.depth) * 0.45,
            notch.width * 0.25,
        )

    # Build trimmed inside-edge notch cutter outside main sketch so it never crosses bore center
    notch_cutter = None
    if notch.enabled:
        x_radius = (r_in + notch.depth) - notch_x_entry
        with BuildSketch(Plane.XY) as notch_sk:
            with Locations((notch_x_entry, 0.0)):
                Ellipse(x_radius=x_radius, y_radius=notch_half_w)
            clip_w = r_in + notch.depth + 1.0
            with Locations((clip_w / 2.0, 0.0)):
                Rectangle(width=clip_w, height=notch.width + 1.0, mode=Mode.INTERSECT)
        notch_cutter = notch_sk.sketch.rotate(Axis.Z, notch.angle)

    with BuildPart() as spacer:
        with BuildSketch(Plane.XY) as profile:
            # 1. Base C-clip perimeter with tangent rounded outer nose & curved/straight jaws
            half_open_deg = jaw.opening_angle / 2.0
            with BuildLine():
                if nose_sol is not None:
                    px_tan, py_tan = nose_sol["p_tan"]  # type: ignore[misc]
                    mx_nose, my_nose = nose_sol["nose_mid"]  # type: ignore[misc]
                    tx, ty = nose_sol["p_tan_jaw"]  # type: ignore[misc]
                    mx_jaw, my_jaw = nose_sol["jaw_mid"]  # type: ignore[misc]
                    theta_tan_deg = math.degrees(float(nose_sol["outer_tan_rad"]))

                    CenterArc((0.0, 0.0), r_out, theta_tan_deg, 360.0 - 2.0 * theta_tan_deg)
                    ThreePointArc((px_tan, -py_tan), (mx_nose, -my_nose), (tx, -ty))
                    if eff_jaw_curve > 1e-4:
                        ThreePointArc((tx, -ty), (mx_jaw, -my_jaw), (x_in, -y_in))
                    else:
                        Line((tx, -ty), (x_in, -y_in))
                    CenterArc((0.0, 0.0), r_in, half_open_deg, 360.0 - jaw.opening_angle)
                    if eff_jaw_curve > 1e-4:
                        ThreePointArc((x_in, y_in), (mx_jaw, my_jaw), (tx, ty))
                    else:
                        Line((x_in, y_in), (tx, ty))
                    ThreePointArc((tx, ty), (mx_nose, my_nose), (px_tan, py_tan))
                else:
                    theta_out_deg = math.degrees(math.atan2(y_out, x_out))
                    CenterArc((0.0, 0.0), r_out, theta_out_deg, 360.0 - 2.0 * theta_out_deg)
                    if eff_jaw_curve > 1e-4:
                        ThreePointArc((x_out, -y_out), (x_mid_arc, -y_mid_arc), (x_in, -y_in))
                    else:
                        Line((x_out, -y_out), (x_in, -y_in))
                    CenterArc((0.0, 0.0), r_in, half_open_deg, 360.0 - jaw.opening_angle)
                    if eff_jaw_curve > 1e-4:
                        ThreePointArc((x_in, y_in), (x_mid_arc, y_mid_arc), (x_out, y_out))
                    else:
                        Line((x_in, y_in), (x_out, y_out))
            make_face()

            # 3. Inside-edge grab/removal cutout bordering the shaft
            if notch_cutter is not None:
                add(notch_cutter, mode=Mode.SUBTRACT)

                # Smoothly fillet the two entry corners where the notch meets the inner bore
                if eff_notch_fillet > 1e-3:
                    angle_rad = math.radians(notch.angle)
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

            # 4. Round C-opening inner jaw transitions (outer tips already have exact tangent nose arcs)
            if eff_inner_fillet > 1e-3:
                inner_verts = profile.vertices().filter_by(
                    lambda v: any(
                        math.hypot(v.X - px, v.Y - py) < 0.05
                        for px, py in ((x_in, -y_in), (x_in, y_in))
                    )
                )
                if len(inner_verts) > 0:
                    fillet(inner_verts, radius=eff_inner_fillet)

        # 5. Extrude axially to spacer thickness (Z = 0 to thickness)
        extrude(amount=core.thickness)

        # 6. Subtle top & bottom perimeter edge chamfer for clean bed release and burr-free handling
        if chamf.enabled and chamf.size > 0:
            remaining_spine = (
                wall_thickness - notch.depth
                if notch.enabled
                else wall_thickness
            )
            max_safe_chamfer = min(
                core.thickness * 0.35,
                wall_thickness * 0.3,
                remaining_spine * 0.35,
            )
            for r_corner in (eff_inner_fillet, eff_outer_fillet, eff_notch_fillet):
                if r_corner > 0:
                    max_safe_chamfer = min(max_safe_chamfer, r_corner * 0.8)

            eff_chamfer = min(chamf.size, max_safe_chamfer)
            if eff_chamfer > 1e-3:
                top_face = spacer.faces().sort_by(Axis.Z)[-1]
                bot_face = spacer.faces().sort_by(Axis.Z)[0]
                chamfer(top_face.edges() + bot_face.edges(), length=eff_chamfer)

    assert spacer.part is not None, "C-clip spacer generation failed"
    return spacer.part


def export_filename(params: CClipSpacerParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    variant = "notch" if params.removal_notch.enabled else "plain"
    return (
        f"c_clip_spacer_{params.core.inside_diameter:g}x"
        f"{params.core.outside_diameter:g}x{params.core.thickness:g}mm_{variant}"
    )


if __name__ == "__main__":
    # Single source of truth: dataclass defaults take effect directly
    params = CClipSpacerParams()
    spacer_part = create_c_clip_spacer(params)

    # Standardized exports to the exports/ directory alongside this script
    if EXPORT_STEP or EXPORT_STL:
        exports_path = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_path.mkdir(parents=True, exist_ok=True)

        stem = export_filename(params)

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
