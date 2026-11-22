"""
Parametric C-Clip (build123d Model)

Snap-on C-clip for cylindrical rods and shafts—usable as a retaining clip
(e.g., filament spool keeper, shaft collar) or axial spacer without requiring
disassembly.

Features:
- Parametric clip thickness (axial width along the shaft).
- Parametric inside diameter (rod/shaft size) with optional 3D-print fit clearance.
- Parametric outside diameter.
- Snap-on C-opening with configurable opening angle and smooth rounded jaw tips.
- Smooth inside-edge removal cutout bordering the shaft (spine pry/grab pocket)
  for easy removal with a fingernail, finger, or small tool without creating sharp
  stress risers, with optional G1-tangent outer wall reinforcement for large
  finger-pull cutouts.
- Optional subtle top/bottom edge chamfer to eliminate print-bed elephant's foot
  and sharp edges.
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from build123d import *

try:
    from utils.params import default_preset, group, param
except ImportError:
    import sys

    for _p in Path(__file__).resolve().parents:
        if (_p / "utils").is_dir():
            sys.path.insert(0, str(_p))
            break
    from utils.params import default_preset, group, param

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = True      # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False     # Save .step to repo-root exports/ (default: False)


@dataclass
class CoreParams:
    """Primary C-clip dimensions."""

    thickness: float = param(
        12.0,
        desc="Axial thickness along shaft",
        unit="mm", min=2.0, max=60.0, step=0.1,
    )
    inside_diameter: float = param(
        44.0,
        desc="Nominal rod/shaft diameter",
        unit="mm", min=6.0, max=120.0, step=0.1,
    )
    outside_diameter: float = param(
        64.0,
        desc="Outer clip diameter",
        unit="mm", min=12.0, max=180.0, step=0.1,
    )
    fit_clearance: float = param(
        0.2,
        desc="Added to inside diameter for bore fit",
        unit="mm", min=-0.5, max=1.0, step=0.01,
    )


@dataclass
class JawParams:
    """Snap-on C-opening jaw geometry."""

    opening_angle: float = param(
        120.0,
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
        unit="mm", min=1.0, max=35.0, step=0.5,
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
    reinforce_outer: bool = param(
        False,
        label="Reinforce Outer Wall",
        desc="Smoothly expand outer profile behind cutout to preserve spine wall thickness",
    )
    spine_wall: Optional[float] = param(
        None,
        label="Spine Wall",
        desc="Minimum outer wall thickness behind cutout (Auto = match ring wall)",
        unit="mm", min=1.5, max=30.0, step=0.5,
        when={"reinforce_outer": True},
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


@default_preset("Prusa Core One Spool", desc="44 mm spool hub retaining clip")
@dataclass
class CClipParams:
    """Parameters for the parametric snap-on C-clip."""

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


def _solve_reinforced_lobe(
    r_in: float,
    r_out: float,
    notch_width: float,
    notch_depth: float,
    spine_wall: float,
) -> dict[str, float | tuple[float, float] | list[tuple[float, float]]] | None:
    """Solve G1-tangent reinforced outer lobe geometry in notch-local coordinates.

    Computes the exact outward ``spine_wall`` offset of the right half-ellipse
    removal notch (extending along ``+X``) joined by common external tangent
    lines to the outer circle of radius ``r_out``. Returns ``None`` when the
    notch offset already fits inside ``r_out``.
    """
    b = notch_width / 2.0
    x_e = math.sqrt(r_in * r_in - b * b)
    a = (r_in + notch_depth) - x_e
    t = spine_wall

    # Already fits strictly inside r_out: no outer expansion needed
    if r_in + notch_depth + t <= r_out + 1e-3 and r_in + t <= r_out + 1e-3:
        return None

    r_prime = r_out - t

    # Solve exact common external tangent between circle(0, r_out) and the
    # t-offset of ellipse((x_e, 0), a, b):
    #   sqrt(a^2 u^2 + b^2 (1 - u^2)) = (r_out - t) - x_e * u,   u = cos(phi)
    a_q = a * a - b * b - x_e * x_e
    b_q = 2.0 * r_prime * x_e
    c_q = b * b - r_prime * r_prime

    candidates: list[float] = []
    if abs(a_q) < 1e-12:
        if abs(b_q) > 1e-12:
            candidates.append(-c_q / b_q)
    else:
        disc = b_q * b_q - 4.0 * a_q * c_q
        if disc >= 0.0:
            sq = math.sqrt(max(0.0, disc))
            candidates.append((-b_q + sq) / (2.0 * a_q))
            candidates.append((-b_q - sq) / (2.0 * a_q))

    valid_u: float | None = None
    for u_cand in candidates:
        if 1e-6 < u_cand < 1.0 - 1e-9:
            rhs = r_prime - x_e * u_cand
            if rhs > 1e-9:
                lhs = math.sqrt(max(0.0, a * a * u_cand * u_cand + b * b * (1.0 - u_cand * u_cand)))
                if abs(lhs - rhs) < 1e-5:
                    valid_u = u_cand
                    break

    if valid_u is not None:
        u = valid_u
        v = math.sqrt(max(0.0, 1.0 - u * u))
        phi = math.acos(u)
        s = r_prime - x_e * u
        cos_th = max(-1.0, min(1.0, a * u / s))
        sin_th = max(-1.0, min(1.0, b * v / s))
        theta_1 = math.atan2(sin_th, cos_th)

        x1 = x_e + a * cos_th + t * u
        y1 = b * sin_th + t * v
        xc = r_out * u
        yc = r_out * v

        if theta_1 <= 1e-4 or math.hypot(x1 - xc, y1 - yc) <= 1e-3:
            return None

        n_pts = 33
        pts: list[tuple[float, float]] = []
        for i in range(n_pts):
            th = -theta_1 + (2.0 * theta_1) * i / (n_pts - 1)
            ct, st = math.cos(th), math.sin(th)
            nx, ny = b * ct, a * st
            nlen = math.hypot(nx, ny)
            nx /= nlen
            ny /= nlen
            pts.append((x_e + a * ct + t * nx, b * st + t * ny))

        return {
            "phi_deg": math.degrees(phi),
            "p_c_neg": (xc, -yc),
            "p_c_pos": (xc, yc),
            "p_lobe_neg": (x1, -y1),
            "p_lobe_pos": (x1, y1),
            "pts": pts,
            "t_start": (v, u),
            "t_end": (-v, u),
            "cap_sweep_deg": 0.0,
            "cap_radius": t,
            "cap_center_neg": (x_e, -b),
            "cap_center_pos": (x_e, b),
        }

    # When spine_wall >= r_out - b, the tangent touches the circular radius-t
    # offset cap around the notch entry corner (x_e, ±b).
    ratio = r_prime / r_in
    if ratio <= -1.0 + 1e-6 or ratio >= 1.0 - 1e-6:
        raise ValueError(
            f"removal_notch.spine_wall ({spine_wall}mm) is too large to blend "
            f"into outside_diameter ({2.0 * r_out:g}mm)"
        )
    alpha = math.atan2(b, x_e)
    phi = alpha + math.acos(ratio)
    if phi >= math.pi - 1e-3:
        raise ValueError(
            f"removal_notch.spine_wall ({spine_wall}mm) causes the reinforced lobe "
            f"to engulf the outer perimeter"
        )

    u, v = math.cos(phi), math.sin(phi)
    xc, yc = r_out * u, r_out * v
    x1, y1 = x_e + t * u, b + t * v

    n_ell = 33
    pts = []
    for i in range(n_ell):
        th = -math.pi / 2.0 + math.pi * i / (n_ell - 1)
        ct, st = math.cos(th), math.sin(th)
        nx, ny = b * ct, a * st
        nlen = math.hypot(nx, ny)
        nx /= nlen
        ny /= nlen
        pts.append((x_e + a * ct + t * nx, b * st + t * ny))

    cap_sweep_deg = max(0.0, math.degrees(phi) - 90.0)
    return {
        "phi_deg": math.degrees(phi),
        "p_c_neg": (xc, -yc),
        "p_c_pos": (xc, yc),
        "p_lobe_neg": (x1, -y1),
        "p_lobe_pos": (x1, y1),
        "pts": pts,
        "t_start": (1.0, 0.0),
        "t_end": (-1.0, 0.0),
        "cap_sweep_deg": cap_sweep_deg,
        "cap_radius": t,
        "cap_center_neg": (x_e, -b),
        "cap_center_pos": (x_e, b),
    }


def _rotate_2d(pt: tuple[float, float], angle_rad: float) -> tuple[float, float]:
    """Rotate a 2D point or vector counter-clockwise by ``angle_rad``."""
    ca, sa = math.cos(angle_rad), math.sin(angle_rad)
    return (pt[0] * ca - pt[1] * sa, pt[0] * sa + pt[1] * ca)


def create_c_clip(params: CClipParams) -> Part:
    """Generate a parametric snap-on C-clip solid body."""
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
    target_spine_wall = wall_thickness
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
        if notch.reinforce_outer:
            if notch.spine_wall is not None and notch.spine_wall <= 0:
                raise ValueError(
                    f"removal_notch.spine_wall must be positive, got {notch.spine_wall}"
                )
            target_spine_wall = (
                wall_thickness if notch.spine_wall is None else notch.spine_wall
            )
        elif notch.depth >= wall_thickness * 0.85:
            raise ValueError(
                f"removal_notch.depth ({notch.depth}mm) must be less than "
                f"85% of radial wall thickness ({wall_thickness * 0.85:.2f}mm) to preserve spine strength "
                f"(or enable removal_notch.reinforce_outer)"
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
        outer_arc_start_deg = math.degrees(float(nose_sol["outer_tan_rad"]))
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
        outer_arc_start_deg = math.degrees(math.atan2(y_out, x_out))
    outer_arc_end_deg = 360.0 - outer_arc_start_deg

    # Solve optional reinforced outer lobe behind the removal cutout
    lobe_sol = None
    lobe_start_deg = 0.0
    lobe_end_deg = 0.0
    notch_angle_norm = notch.angle % 360.0
    if notch.enabled and notch.reinforce_outer:
        lobe_sol = _solve_reinforced_lobe(
            r_in=r_in,
            r_out=r_out,
            notch_width=notch.width,
            notch_depth=notch.depth,
            spine_wall=target_spine_wall,
        )
        if lobe_sol is not None:
            phi_deg = float(lobe_sol["phi_deg"])
            lobe_start_deg = notch_angle_norm - phi_deg
            lobe_end_deg = notch_angle_norm + phi_deg
            if (
                lobe_start_deg <= outer_arc_start_deg + 0.5
                or lobe_end_deg >= outer_arc_end_deg - 0.5
            ):
                raise ValueError(
                    f"Reinforced outer lobe ([{lobe_start_deg:.1f}°, {lobe_end_deg:.1f}°]) "
                    f"extends into the C-opening jaws ([{outer_arc_start_deg:.1f}°, "
                    f"{outer_arc_end_deg:.1f}°]); move removal_notch.angle closer to 180°, "
                    f"reduce spine_wall/width/depth, or narrow opening_angle"
                )

    remaining_spine = wall_thickness
    if notch.enabled:
        if notch.reinforce_outer:
            remaining_spine = max(wall_thickness - notch.depth, target_spine_wall)
        else:
            remaining_spine = wall_thickness - notch.depth

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
            remaining_spine * 0.45,
            wall_thickness * 0.45,
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

    with BuildPart() as clip:
        with BuildSketch(Plane.XY) as profile:
            # 1. Base C-clip perimeter with tangent rounded outer nose & curved/straight jaws
            half_open_deg = jaw.opening_angle / 2.0
            with BuildLine():
                # Outer perimeter: either plain circular arc or G1-tangent reinforced lobe
                if lobe_sol is not None:
                    ang_rad = math.radians(notch_angle_norm)
                    p_c1 = _rotate_2d(lobe_sol["p_c_neg"], ang_rad)  # type: ignore[arg-type]
                    p_l1 = _rotate_2d(lobe_sol["p_lobe_neg"], ang_rad)  # type: ignore[arg-type]
                    p_l2 = _rotate_2d(lobe_sol["p_lobe_pos"], ang_rad)  # type: ignore[arg-type]
                    p_c2 = _rotate_2d(lobe_sol["p_c_pos"], ang_rad)  # type: ignore[arg-type]
                    lobe_pts = [_rotate_2d(p, ang_rad) for p in lobe_sol["pts"]]  # type: ignore[union-attr]
                    t1 = _rotate_2d(lobe_sol["t_start"], ang_rad)  # type: ignore[arg-type]
                    t2 = _rotate_2d(lobe_sol["t_end"], ang_rad)  # type: ignore[arg-type]
                    cap_sweep_deg = float(lobe_sol["cap_sweep_deg"])
                    cap_radius = float(lobe_sol["cap_radius"])

                    CenterArc((0.0, 0.0), r_out, outer_arc_start_deg, lobe_start_deg - outer_arc_start_deg)
                    if cap_sweep_deg > 1e-3:
                        cap_c1 = _rotate_2d(lobe_sol["cap_center_neg"], ang_rad)  # type: ignore[arg-type]
                        cap_c2 = _rotate_2d(lobe_sol["cap_center_pos"], ang_rad)  # type: ignore[arg-type]
                        Line(p_c1, p_l1)
                        CenterArc(cap_c1, cap_radius, lobe_start_deg, cap_sweep_deg)
                        Spline(lobe_pts, tangents=(t1, t2))
                        CenterArc(cap_c2, cap_radius, notch_angle_norm + 90.0, cap_sweep_deg)
                        Line(p_l2, p_c2)
                    else:
                        Line(p_c1, lobe_pts[0])
                        Spline(lobe_pts, tangents=(t1, t2))
                        Line(lobe_pts[-1], p_c2)
                    CenterArc((0.0, 0.0), r_out, lobe_end_deg, outer_arc_end_deg - lobe_end_deg)
                else:
                    CenterArc((0.0, 0.0), r_out, outer_arc_start_deg, 360.0 - 2.0 * outer_arc_start_deg)

                if nose_sol is not None:
                    px_tan, py_tan = nose_sol["p_tan"]  # type: ignore[misc]
                    mx_nose, my_nose = nose_sol["nose_mid"]  # type: ignore[misc]
                    tx, ty = nose_sol["p_tan_jaw"]  # type: ignore[misc]
                    mx_jaw, my_jaw = nose_sol["jaw_mid"]  # type: ignore[misc]

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

        # 5. Extrude axially to clip thickness (Z = 0 to thickness)
        extrude(amount=core.thickness)

        # 6. Subtle top & bottom perimeter edge chamfer for clean bed release and burr-free handling
        if chamf.enabled and chamf.size > 0:
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
                top_face = clip.faces().sort_by(Axis.Z)[-1]
                bot_face = clip.faces().sort_by(Axis.Z)[0]
                chamfer(top_face.edges() + bot_face.edges(), length=eff_chamfer)

    assert clip.part is not None, "C-clip generation failed"
    return clip.part


def export_filename(params: CClipParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    if not params.removal_notch.enabled:
        variant = "plain"
    elif params.removal_notch.reinforce_outer:
        variant = "reinforced"
    else:
        variant = "notch"
    return (
        f"c_clip_{params.core.inside_diameter:g}x"
        f"{params.core.outside_diameter:g}x{params.core.thickness:g}mm_{variant}"
    )


if __name__ == "__main__":
    from utils.runner import run_model

    # Single source of truth: dataclass defaults take effect directly
    params = CClipParams()
    clip_part = create_c_clip(params)
    run_model(clip_part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
