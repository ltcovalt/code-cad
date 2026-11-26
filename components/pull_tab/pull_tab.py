"""
Reusable Flared Pull Tab Component (build123d)

Provides a shared `PullTabParams` dataclass, `build_pull_tab(...)` two-pass
geometry builder for lid models (e.g. `can_lid`, `container_lid`), and a
standalone `create_pull_tab(params)` preview generator for Code CAD Studio.

Features:
- Smooth G1-tangent concave root fillets where the tab meets a circular or straight rim
  (eliminates sharp stress-riser corners and replaces the "slapped-on rectangle" look)
- Optional lofted under-tab gusset trimmed cleanly to the lid wall
- Optional recessed non-slip traction grooves on the flat outer face
- Optional through-cut hanging / drying peg hole (cuts cleanly through tab + gusset)
- Supports both print orientation (flat face at Z = 0, gusset rising in +Z) and
  upright orientation (top face at Z = top_thickness, gusset dropping in -Z)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from build123d import *

try:
    from utils.params import default_preset, param
except ImportError:
    import sys

    for _p in Path(__file__).resolve().parents:
        if (_p / "utils").is_dir():
            sys.path.insert(0, str(_p))
            break
    from utils.params import default_preset, param

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False      # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False     # Save .step to repo-root exports/ (default: False)


@default_preset(
    "Standard Flared (6 × 16 mm)",
    desc="Compact flared pull tab with grip ribs and 2 mm structural gusset",
)
@dataclass
class PullTabParams:
    """Configurable outer pull tab for easy lid removal."""

    length: float = param(
        6.0,
        desc="Protrusion length beyond outer skirt",
        unit="mm", min=3.0, max=25.0, step=0.5,
    )
    width: float = param(
        16.0,
        desc="Tab width",
        unit="mm", min=8.0, max=50.0, step=1.0,
    )
    root_fillet: float = param(
        4.0,
        desc="Concave flare radius blending tab sides into the lid rim (0 = straight)",
        unit="mm", min=0.0, max=15.0, step=0.5,
    )
    gusset_depth: float = param(
        2.0,
        desc="Under-tab structural gusset depth",
        unit="mm", min=0.0, max=8.0, step=0.5,
    )
    grip_ribs: bool = param(
        True,
        desc="Add recessed non-slip traction grooves on the outer face",
    )
    hanging_hole: bool = param(
        False,
        desc="Add hanging / drying peg through-hole in tab",
    )
    hole_diameter: float = param(
        3.5,
        desc="Hanging hole diameter",
        unit="mm", min=2.0, max=10.0, step=0.5, when={"hanging_hole": True},
    )


def _flared_tab_sketch(
    *,
    x_attach: float,
    length: float,
    width: float,
    root_fillet: float,
    rim_radius: Optional[float],
    inward_offset: float = 0.0,
) -> Face:
    """Build a 2D flared pull-tab face protruding along +X from `x_attach`.

    When `rim_radius` is provided, the concave root fillets are computed to be
    G1-tangent to the circular rim of radius `rim_radius` centered at `(0, 0)`
    (with `x_attach == rim_radius`). When `rim_radius` is `None`, they are
    computed to be G1-tangent to a straight vertical rim at `x = x_attach`.

    `inward_offset` shrinks the outer contour uniformly inward by that distance
    while preserving the exact concave fillet centers `(x_c, y_c)`, so lofting
    from `inward_offset=b` to `inward_offset=0` produces a seamless 45° bevel
    that blends flush into a lid's outer perimeter chamfer.
    """
    b = max(0.0, inward_offset)
    half_w = width / 2.0
    x_tip = x_attach + length
    # Internal boolean overlap inside the lid wall/deck (not user-visible)
    internal_overlap = min(4.0, max(1.5, x_attach * 0.2))
    x_back = max(0.0, x_attach - internal_overlap)
    tip_r = min(3.5, half_w * 0.85, max(0.5, length * 0.45))

    use_flare = False
    if root_fillet > 0.15:
        if rim_radius is not None:
            r_rim = rim_radius
            r_f = root_fillet
            y_c = half_w + r_f
            if half_w < r_rim - 0.5:
                x_c = math.sqrt((r_rim + r_f) ** 2 - y_c ** 2)
                if x_c < x_tip - tip_r - 0.1:
                    r_rim_eff = r_rim - b
                    r_f_eff = r_f + b
                    half_w_eff = half_w - b
                    tx = x_c * r_rim_eff / (r_rim_eff + r_f_eff)
                    ty = y_c * r_rim_eff / (r_rim_eff + r_f_eff)
                    a1 = math.atan2(ty - y_c, tx - x_c)
                    a2 = -math.pi / 2.0
                    a_mid = (a1 + a2) / 2.0
                    mx = x_c + r_f_eff * math.cos(a_mid)
                    my = y_c + r_f_eff * math.sin(a_mid)
                    x_side_start = x_c
                    use_flare = True
        else:
            r_f = min(root_fillet, max(0.0, length - tip_r - 0.2))
            if r_f > 0.15:
                r_f_eff = r_f + b
                half_w_eff = half_w - b
                tx = x_attach - b
                ty = half_w + r_f
                x_side_start = x_attach + r_f
                if x_side_start < x_tip - tip_r - 0.1:
                    mx = x_side_start - r_f_eff * math.cos(math.pi / 4.0)
                    my = (half_w + r_f) - r_f_eff * math.sin(math.pi / 4.0)
                    use_flare = True

    with BuildSketch(Plane.XY) as sk:
        if not use_flare:
            eff_w = max(0.5, width - 2.0 * b)
            eff_x_tip = x_tip - b
            eff_tip_r = max(0.2, min(tip_r - b, eff_w * 0.45))
            total_len = max(0.5, eff_x_tip - x_back)
            with Locations((x_back + total_len / 2.0, 0.0)):
                RectangleRounded(total_len, eff_w, radius=eff_tip_r)
        else:
            eff_x_tip = x_tip - b
            eff_tip_r = max(0.2, min(tip_r - b, half_w_eff * 0.85))
            x_t = eff_x_tip - eff_tip_r
            y_t = half_w_eff - eff_tip_r
            c45 = math.cos(math.pi / 4.0)
            s45 = math.sin(math.pi / 4.0)
            top_tip_mid = (x_t + eff_tip_r * c45, y_t + eff_tip_r * s45)
            bot_tip_mid = (x_t + eff_tip_r * c45, -(y_t + eff_tip_r * s45))
            x_root_back = min(x_back, tx - 0.5) if rim_radius is None else max(0.0, min(x_back, tx - 0.5))

            with BuildLine():
                Line((x_root_back, ty), (tx, ty))
                ThreePointArc((tx, ty), (mx, my), (x_side_start, half_w_eff))
                Line((x_side_start, half_w_eff), (x_t, half_w_eff))
                ThreePointArc((x_t, half_w_eff), top_tip_mid, (eff_x_tip, y_t))
                if y_t > 1e-4:
                    Line((eff_x_tip, y_t), (eff_x_tip, -y_t))
                ThreePointArc((eff_x_tip, -y_t), bot_tip_mid, (x_t, -half_w_eff))
                Line((x_t, -half_w_eff), (x_side_start, -half_w_eff))
                ThreePointArc((x_side_start, -half_w_eff), (mx, -my), (tx, -ty))
                Line((tx, -ty), (x_root_back, -ty))
                Line((x_root_back, -ty), (x_root_back, ty))
            make_face()

    assert sk.sketch is not None
    return sk.face()


def pull_tab_angular_clearance(
    tab: Optional[PullTabParams],
    r_outer: float,
    margin: float = 3.0,
) -> float:
    """Return half-angle (degrees) around +X occupied by the tab including its root flare."""
    if tab is None:
        return 0.0
    half_span = tab.width / 2.0 + tab.root_fillet + margin
    return math.degrees(math.atan2(half_span, max(1.0, r_outer)))


def build_pull_tab(
    tab: PullTabParams,
    *,
    x_attach: float,
    top_thickness: float,
    max_gusset_depth: float,
    outer_bevel: float = 0.0,
    rim_radius: Optional[float] = None,
    trim_solid: Optional[Solid] = None,
    trim_radius: Optional[float] = None,
    print_orientation: bool = True,
    location: Optional[Location] = None,
) -> tuple[Solid, Optional[Solid]]:
    """Build a flared pull tab + optional gusset and return `(add_solid, cut_solid)`.

    - `add_solid`: The tab plate + gusset to union (`Mode.ADD`) onto the lid.
    - `cut_solid`: Optional combined through-hanging-hole + recessed grip-rib cutters
      to subtract (`Mode.SUBTRACT`) after unioning `add_solid`.

    Coordinate conventions:
    - `print_orientation=True`: Flat outer face sits at `Z = 0`, tab spans `[0, top_thickness]`,
      outer perimeter bevel runs from `Z = 0` to `Z = outer_bevel`, gusset rises in `+Z`
      from `top_thickness` to `top_thickness + eff_gusset_depth`, grip ribs cut into `Z = 0`.
    - `print_orientation=False`: Top outer face sits at `Z = top_thickness`, tab spans `[0, top_thickness]`,
      outer perimeter bevel runs from `Z = top_thickness - outer_bevel` to `Z = top_thickness`,
      gusset drops in `-Z` from `0` to `-eff_gusset_depth`, grip ribs cut into `Z = top_thickness`.
    """
    eff_gusset_depth = min(tab.gusset_depth, max(0.0, max_gusset_depth))
    eff_bevel = min(
        max(0.0, outer_bevel),
        top_thickness * 0.85,
        tab.width * 0.35,
        tab.length * 0.4,
    )

    with BuildPart() as add_part:
        tab_face = _flared_tab_sketch(
            x_attach=x_attach,
            length=tab.length,
            width=tab.width,
            root_fillet=tab.root_fillet,
            rim_radius=rim_radius,
            inward_offset=0.0,
        )
        if eff_bevel > 0.05:
            bevel_face = _flared_tab_sketch(
                x_attach=x_attach,
                length=tab.length,
                width=tab.width,
                root_fillet=tab.root_fillet,
                rim_radius=rim_radius,
                inward_offset=eff_bevel,
            )
            if print_orientation:
                with BuildSketch(Plane.XY) as sk_bev_lo:
                    add(bevel_face)
                with BuildSketch(Plane.XY.offset(eff_bevel)) as sk_bev_hi:
                    add(tab_face)
                loft([sk_bev_lo.sketch, sk_bev_hi.sketch], ruled=True, mode=Mode.ADD)
                with BuildSketch(Plane.XY.offset(eff_bevel)):
                    add(tab_face)
                extrude(amount=top_thickness - eff_bevel, mode=Mode.ADD)
            else:
                with BuildSketch(Plane.XY):
                    add(tab_face)
                extrude(amount=top_thickness - eff_bevel, mode=Mode.ADD)
                with BuildSketch(Plane.XY.offset(top_thickness - eff_bevel)) as sk_bev_lo:
                    add(tab_face)
                with BuildSketch(Plane.XY.offset(top_thickness)) as sk_bev_hi:
                    add(bevel_face)
                loft([sk_bev_lo.sketch, sk_bev_hi.sketch], ruled=True, mode=Mode.ADD)
        else:
            with BuildSketch(Plane.XY):
                add(tab_face)
            extrude(amount=top_thickness, mode=Mode.ADD)

        if eff_gusset_depth > 0.2:
            z_base = top_thickness if print_orientation else 0.0
            z_peak = (top_thickness + eff_gusset_depth) if print_orientation else -eff_gusset_depth
            base_face = _flared_tab_sketch(
                x_attach=x_attach,
                length=tab.length * 0.75,
                width=tab.width * 0.95,
                root_fillet=tab.root_fillet * 0.9,
                rim_radius=rim_radius,
            )
            peak_face = _flared_tab_sketch(
                x_attach=x_attach,
                length=tab.length * 0.35,
                width=tab.width * 0.75,
                root_fillet=tab.root_fillet * 0.5,
                rim_radius=rim_radius,
            )
            with BuildPart() as gusset:
                with BuildSketch(Plane.XY.offset(z_base)):
                    add(base_face)
                with BuildSketch(Plane.XY.offset(z_peak)):
                    add(peak_face)
                loft(ruled=True)
                if trim_radius is not None:
                    z_trim_start = (z_base - 0.5) if print_orientation else (z_peak - 0.5)
                    with BuildSketch(Plane.XY.offset(z_trim_start)):
                        Circle(radius=trim_radius)
                    extrude(amount=eff_gusset_depth + 1.5, mode=Mode.SUBTRACT)
            if gusset.part is not None:
                gusset_solid = gusset.part
                if location is not None:
                    gusset_solid = gusset_solid.moved(location)
                if trim_solid is not None:
                    gusset_solid = gusset_solid - trim_solid
                if location is not None:
                    gusset_solid = gusset_solid.moved(location.inverse())
                add(gusset_solid, mode=Mode.ADD)

    assert add_part.part is not None, "Failed to generate pull tab"
    tab_add = add_part.part
    if location is not None:
        tab_add = tab_add.moved(location)

    # Build combined subtraction cutters (hanging through-hole + grip ribs)
    cut_solids: list[Solid] = []

    if tab.hanging_hole:
        hole_x = x_attach + tab.length - (tab.hole_diameter / 2.0 + 1.8)
        if hole_x > x_attach + tab.hole_diameter / 2.0:
            z_lo = -0.5 if print_orientation else (-eff_gusset_depth - 0.5)
            cut_h = top_thickness + eff_gusset_depth + 1.5
            with BuildPart() as hole_part:
                with BuildSketch(Plane.XY.offset(z_lo)):
                    with Locations((hole_x, 0.0)):
                        Circle(radius=tab.hole_diameter / 2.0)
                extrude(amount=cut_h)
            if hole_part.part is not None:
                cut_solids.append(hole_part.part)

    if tab.grip_ribs:
        rib_depth = min(0.55, top_thickness * 0.35)
        rib_span = max(3.0, tab.width - 6.0)
        for i in range(3):
            rib_x = x_attach + 1.8 + i * 2.1
            if rib_x + 0.7 < (x_attach + tab.length - 0.8):
                with BuildPart() as rib_part:
                    if print_orientation:
                        with BuildSketch(Plane.XY.offset(-0.1)):
                            with Locations((rib_x, 0.0)):
                                RectangleRounded(0.95, rib_span, radius=0.35)
                        extrude(amount=rib_depth + 0.1)
                    else:
                        with BuildSketch(Plane.XY.offset(top_thickness + 0.1)):
                            with Locations((rib_x, 0.0)):
                                RectangleRounded(0.95, rib_span, radius=0.35)
                        extrude(amount=-(rib_depth + 0.1))
                if rib_part.part is not None:
                    cut_solids.append(rib_part.part)

    tab_cut: Optional[Solid] = None
    if cut_solids:
        with BuildPart() as combined_cut:
            for s in cut_solids:
                add(s, mode=Mode.ADD)
        if combined_cut.part is not None:
            tab_cut = combined_cut.part
            if location is not None:
                tab_cut = tab_cut.moved(location)

    return tab_add, tab_cut


def export_filename(params: PullTabParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    style = "hanging" if params.hanging_hole else ("ribbed" if params.grip_ribs else "smooth")
    return f"pull_tab_{params.length:g}x{params.width:g}mm_{style}"


def create_pull_tab(params: PullTabParams) -> Part:
    """Generate a standalone preview of the pull tab mounted on a reference rim stub."""
    x_attach = 6.0
    top_thickness = 2.0
    outer_bevel = 0.8
    stub_height = top_thickness + max(params.gusset_depth, 2.5) + 1.5
    stub_width = params.width + 2.0 * params.root_fillet + 8.0

    with BuildPart() as trim_part:
        with Locations((2.0, 0.0, stub_height / 2.0)):
            Box(5.0, stub_width + 4.0, stub_height + 2.0)

    tab_add, tab_cut = build_pull_tab(
        params,
        x_attach=x_attach,
        top_thickness=top_thickness,
        max_gusset_depth=stub_height - top_thickness,
        outer_bevel=outer_bevel,
        rim_radius=None,
        trim_solid=trim_part.part,
        print_orientation=True,
    )

    with BuildPart() as preview:
        # Reference straight rim stub so root flares, bevel, and gusset are clearly visible
        with BuildSketch(Plane.XY):
            with Locations((x_attach - 2.0, 0.0)):
                Rectangle(4.0, stub_width)
        extrude(amount=stub_height)
        add(tab_add, mode=Mode.ADD)
        if tab_cut is not None:
            add(tab_cut, mode=Mode.SUBTRACT)

    assert preview.part is not None, "Failed to generate pull tab preview"
    return preview.part.moved(Location((-(x_attach + params.length / 2.0), 0.0, 0.0)))


if __name__ == "__main__":
    from utils.runner import run_model

    params = PullTabParams()
    part = create_pull_tab(params)
    run_model(part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
