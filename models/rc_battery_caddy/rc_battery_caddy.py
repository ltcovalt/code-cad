"""
Storage rack and pit caddy for RC LiPo hardcase batteries.

Builds a sturdy, 100% support-free 3D-printable pit caddy and storage rack
for RC car LiPo hardcase batteries—pre-configured for standard 2S Shorty packs
(used in 1/10 scale 2WD buggies like the Schumacher Cougar LD2 and XRAY XB2)
with built-in profiles for LCG shorty, ULCG/slim shorty, standard 2S stick
packs, and custom dimensions.

Features:
- Built-in RC LiPo hardcase profiles (Standard 2S Shorty, LCG, ULCG/Slim,
  Standard 2S Stick) plus custom dimensions
- Three layout patterns:
  - `grid`: configurable columns × rows with optional 90° slot rotation
  - `pinwheel`: compact 4-pack pinwheel (fits 4 shorties in 2×2 Gridfinity)
  - `auto_pack`: maximizes battery count inside a target Gridfinity footprint
    by mixing 0°/90° rows or pinwheel (e.g. 6 packs in 3×2)
- Flat pit-table base or auto-sized Gridfinity-compatible 42 mm modular base
  with optional 6×2 mm corner magnet pockets
- Configurable wall height, XY fit clearance, wall/divider/floor thicknesses,
  pocket corner radius, top lead-in chamfer, and anti-elephant's-foot base bevel
- Optional U-shaped finger-grip & label-viewing cutouts and bottom drain holes
- Single-section Test Fit mode to quickly print a 1×1 collar/cup and verify
  battery clearance before printing the full caddy
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from build123d import *

try:
    from components.gridfinity_base import (
        GRIDFINITY_CLEARANCE,
        GRIDFINITY_CORNER_RADIUS,
        GRIDFINITY_FOOT_HEIGHT,
        GRIDFINITY_UNIT_XY,
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
        GRIDFINITY_CLEARANCE,
        GRIDFINITY_CORNER_RADIUS,
        GRIDFINITY_FOOT_HEIGHT,
        GRIDFINITY_UNIT_XY,
        GridfinityBaseParams,
        compute_gridfinity_footprint,
        create_gridfinity_base,
    )
    from utils.params import default_preset, group, param

MODEL_NAME: str = "RC LiPo Battery Caddy"

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False      # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False     # Save .step to repo-root exports/ (default: False)


# Nominal ROAR/EFRA hardcase LiPo dimensions: (length, width, thickness) in mm
BATTERY_PROFILES: dict[str, tuple[float, float, float]] = {
    "shorty_standard": (96.0, 47.0, 25.1),   # Standard full-height 2S Shorty
    "shorty_lcg": (96.0, 47.0, 22.5),        # Low Center of Gravity (LCG) 2S Shorty
    "shorty_ulcg": (96.0, 47.0, 18.5),       # Ultra-LCG / Slim 2S Shorty
    "stick_standard": (139.0, 47.0, 25.1),   # Full-length 2S Stick hardcase
}


@dataclass(frozen=True)
class _Pocket:
    """Single battery pocket placement in XY (centered at origin)."""

    cx: float
    cy: float
    sx: float
    sy: float
    is_center_cubby: bool = False


@dataclass
class BatteryParams:
    """Battery pack type, orientation, and pocket fit clearance."""

    battery_type: Literal[
        "shorty_standard",
        "shorty_lcg",
        "shorty_ulcg",
        "stick_standard",
        "custom",
    ] = param(
        "shorty_standard",
        label="Battery Type",
        desc="Standard RC LiPo hardcase profile (or choose custom dimensions)",
    )
    custom_length: float = param(
        96.0,
        label="Custom Length",
        desc="Battery pack length",
        unit="mm", min=20.0, max=200.0, step=0.5,
        when={"battery_type": "custom"},
    )
    custom_width: float = param(
        47.0,
        label="Custom Width",
        desc="Battery pack width",
        unit="mm", min=15.0, max=120.0, step=0.5,
        when={"battery_type": "custom"},
    )
    custom_thickness: float = param(
        25.1,
        label="Custom Thickness",
        desc="Battery pack thickness / height",
        unit="mm", min=10.0, max=80.0, step=0.1,
        when={"battery_type": "custom"},
    )
    orientation: Literal["upright", "on_edge", "flat"] = param(
        "upright",
        desc="Upright on narrow end (compact), on long edge (low CG), or lying flat",
    )
    clearance: float = param(
        1.0,
        label="XY Fit Clearance",
        desc="Total clearance added to pocket length and width (split equally per side)",
        unit="mm", min=0.0, max=4.0, step=0.1,
    )


@dataclass
class LayoutParams:
    """Grid arrangement or space-optimized packing of battery slots."""

    pattern: Literal["grid", "pinwheel", "auto_pack"] = param(
        "grid",
        desc="Uniform grid, 4-pack pinwheel (fits 2×2 Gridfinity), or auto-pack to maximize slots in a target Gridfinity footprint",
    )
    columns: int = param(
        4,
        desc="Number of battery slots per row (along X)",
        min=1, max=12, step=1,
        when={"pattern": "grid"},
    )
    rows: int = param(
        1,
        desc="Number of rows (along Y)",
        min=1, max=6, step=1,
        when={"pattern": "grid"},
    )
    rotate_90: bool = param(
        False,
        label="Rotate Slots 90°",
        desc="Rotate all battery slots 90° in XY (e.g. for slim 3×1 Gridfinity strips)",
        when={"pattern": "grid"},
    )
    pack_grid_x: int = param(
        3,
        label="Target Grid X",
        desc="Target Gridfinity width in 42 mm units for auto-packing",
        unit="U", min=1, max=8, step=1,
        when={"pattern": "auto_pack"},
    )
    pack_grid_y: int = param(
        2,
        label="Target Grid Y",
        desc="Target Gridfinity depth in 42 mm units for auto-packing",
        unit="U", min=1, max=8, step=1,
        when={"pattern": "auto_pack"},
    )
    pinwheel_center: Literal["cubby", "pull_loop", "none"] = param(
        "cubby",
        label="Pinwheel Center",
        desc="Center square feature: recessed storage cubby, vertical finger pull loop, or solid",
        when={"pattern": ["pinwheel", "auto_pack"]},
    )
    pinwheel_cubby_depth: Optional[float] = param(
        None,
        label="Center Cubby Depth",
        desc="Depth of center cubby from the top rim (Auto = full wall height)",
        unit="mm", min=5.0, max=120.0, step=1.0,
        when={"pattern": ["pinwheel", "auto_pack"], "pinwheel_center": "cubby"},
    )
    pull_loop_height: float = param(
        55.0,
        label="Pull Loop Height",
        desc="Height of pull loop above caddy rim (55 mm ≈ flush with upright shorty tops)",
        unit="mm", min=30.0, max=110.0, step=2.0,
        when={"pattern": ["pinwheel", "auto_pack"], "pinwheel_center": "pull_loop"},
    )


@dataclass
class StructureParams:
    """Wall height, thicknesses, corner radii, and chamfers."""

    wall_height: float = param(
        45.0,
        desc="Interior pocket wall height above the floor",
        unit="mm", min=10.0, max=120.0, step=1.0,
    )
    outer_wall_thickness: float = param(
        3.0,
        desc="Minimum exterior perimeter wall thickness",
        unit="mm", min=1.6, max=8.0, step=0.2,
    )
    divider_thickness: float = param(
        2.4,
        desc="Interior divider wall thickness between adjacent pockets",
        unit="mm", min=1.2, max=6.0, step=0.2,
    )
    floor_thickness: float = param(
        3.0,
        desc="Solid floor thickness above the base",
        unit="mm", min=1.2, max=8.0, step=0.2,
    )
    outer_corner_radius: float = param(
        5.0,
        desc="Outer vertical corner fillet radius (Gridfinity uses standard 3.75 mm)",
        unit="mm", min=0.0, max=15.0, step=0.5,
        when={"gridfinity": None},
    )
    pocket_corner_radius: float = param(
        2.0,
        desc="Inner pocket corner radius to match hardcase LiPo corners",
        unit="mm", min=0.0, max=8.0, step=0.25,
    )
    top_lead_in_chamfer: float = param(
        1.2,
        label="Top Lead-In Chamfer",
        desc="Internal bevel around each pocket opening for smooth battery insertion",
        unit="mm", min=0.0, max=3.0, step=0.1,
    )
    bottom_chamfer: float = param(
        1.0,
        desc="Outer bottom perimeter chamfer to reduce elephant's foot",
        unit="mm", min=0.0, max=3.0, step=0.1,
        when={"gridfinity": None},
    )


@dataclass
class CutoutsParams:
    """Support-free grip/viewing notches and floor drainage/push-out holes."""

    enabled: bool = param(
        True,
        desc="Add finger-grip cutouts and floor push-out/drainage holes",
    )
    side_notches: bool = param(
        True,
        desc="U-shaped finger grip and label viewing cutouts on outer walls",
    )
    side_notch_width_ratio: float = param(
        0.55,
        label="Notch Width Ratio",
        desc="Side notch width as a fraction of pocket width",
        min=0.25, max=0.80, step=0.05,
        when={"side_notches": True},
    )
    side_notch_depth_ratio: float = param(
        0.55,
        label="Notch Depth Ratio",
        desc="Side notch depth as a fraction of wall height from the top rim",
        min=0.20, max=0.75, step=0.05,
        when={"side_notches": True},
    )
    floor_holes: bool = param(
        True,
        desc="Centered bottom cutouts for finger push-out, airflow, and dirt drainage (flat base)",
        when={"gridfinity": None},
    )
    floor_ledge_width: float = param(
        5.0,
        desc="Solid floor ledge width retained around each pocket perimeter",
        unit="mm", min=3.0, max=12.0, step=0.5,
        when={"gridfinity": None, "floor_holes": True},
    )


@dataclass
class TestFitParams:
    """Single-section test-fit mode for fast clearance verification."""

    enabled: bool = param(
        False,
        desc="Generate a single 1×1 pocket section to test battery fit before printing the full caddy",
    )
    height: float = param(
        15.0,
        label="Test Section Height",
        desc="Reduced wall height for a fast fit-check print",
        unit="mm", min=6.0, max=60.0, step=1.0,
    )
    open_bottom: bool = param(
        True,
        desc="Omit the floor so the test collar prints faster and slides along the full battery length",
    )


@default_preset(
    "2S Shorty 4-Pack (Upright)",
    desc="4×1 upright pit caddy for standard 2S shorty LiPo hardcase packs (96 × 47 × 25.1 mm)",
)
@dataclass
class RcBatteryCaddyParams:
    """Master parameter schema for the RC LiPo Battery Caddy generator."""

    battery: BatteryParams = group(BatteryParams)
    layout: LayoutParams = group(LayoutParams)
    gridfinity: GridfinityBaseParams | None = group(
        GridfinityBaseParams,
        enabled=False,
        label="Gridfinity Base",
    )
    structure: StructureParams = group(StructureParams)
    cutouts: CutoutsParams = group(CutoutsParams)
    test_fit: TestFitParams = group(TestFitParams)


def resolve_battery_dimensions(battery: BatteryParams) -> tuple[float, float, float]:
    """Return nominal (length, width, thickness) in mm for the selected battery type."""
    if battery.battery_type == "custom":
        return (battery.custom_length, battery.custom_width, battery.custom_thickness)
    return BATTERY_PROFILES[battery.battery_type]


def resolve_pocket_xy(battery: BatteryParams) -> tuple[float, float]:
    """Return interior pocket (size_x, size_y) in mm including XY fit clearance."""
    length, width, thickness = resolve_battery_dimensions(battery)
    if battery.orientation == "upright":
        base_x, base_y = thickness, width
    elif battery.orientation == "on_edge":
        base_x, base_y = thickness, length
    else:  # "flat"
        base_x, base_y = width, length
    return (base_x + battery.clearance, base_y + battery.clearance)


def _build_grid_pockets(
    px: float,
    py: float,
    cols: int,
    rows: int,
    divider: float,
) -> list[_Pocket]:
    """Return a centered uniform cols × rows list of pockets."""
    pitch_x = px + divider
    pitch_y = py + divider
    pockets: list[_Pocket] = []
    for r in range(rows):
        cy = -((rows - 1) * pitch_y) / 2.0 + r * pitch_y
        for c in range(cols):
            cx = -((cols - 1) * pitch_x) / 2.0 + c * pitch_x
            pockets.append(_Pocket(cx=cx, cy=cy, sx=px, sy=py))
    return pockets


def _build_pinwheel_pockets(
    px: float,
    py: float,
    span: float,
    divider: float,
    include_center: bool,
) -> list[_Pocket]:
    """Return 4 pinwheel pockets inside a centered square of side ``span``."""
    long_s = max(px, py)
    short_s = min(px, py)
    half = span / 2.0
    pockets = [
        # Top-left (horizontal)
        _Pocket(cx=-half + long_s / 2.0, cy=+half - short_s / 2.0, sx=long_s, sy=short_s),
        # Top-right (vertical)
        _Pocket(cx=+half - short_s / 2.0, cy=+half - long_s / 2.0, sx=short_s, sy=long_s),
        # Bottom-right (horizontal)
        _Pocket(cx=+half - long_s / 2.0, cy=-half + short_s / 2.0, sx=long_s, sy=short_s),
        # Bottom-left (vertical)
        _Pocket(cx=-half + short_s / 2.0, cy=-half + long_s / 2.0, sx=short_s, sy=long_s),
    ]
    if include_center:
        center_s = span - 2.0 * short_s - 2.0 * divider
        if center_s >= 8.0:
            pockets.append(_Pocket(cx=0.0, cy=0.0, sx=center_s, sy=center_s, is_center_cubby=True))
    return pockets


def _auto_pack_pockets(
    px: float,
    py: float,
    avail_x: float,
    avail_y: float,
    divider: float,
    include_center: bool,
) -> tuple[list[_Pocket], bool]:
    """Find the highest-capacity pocket layout fitting inside (avail_x, avail_y).

    Evaluates pinwheel, mixed horizontal strips (0° + 90° rows), and mixed
    vertical strips (0° + 90° columns). Returns ``(pockets, is_pinwheel)``.
    """
    eps = 1e-6
    long_s = max(px, py)
    short_s = min(px, py)

    # Candidate score tuple: (battery_count, uniform_bonus, symmetry_bonus)
    best_score: tuple[int, int, float] = (-1, -1, -1.0)
    best_pockets: list[_Pocket] = []
    best_is_pinwheel = False

    def _fit_count(avail: float, item: float) -> int:
        if avail + eps < item:
            return 0
        return int(math.floor((avail + divider + eps) / (item + divider)))

    # 1. Pinwheel (4 packs)
    min_pin_span = long_s + short_s + divider
    if min(avail_x, avail_y) + eps >= min_pin_span:
        span = min(avail_x, avail_y)
        cand = _build_pinwheel_pockets(px, py, span, divider, include_center)
        # Prefer pinwheel when it ties on 4 packs in a square-ish footprint
        score = (4, 1, -abs(avail_x - avail_y))
        if score > best_score:
            best_score = score
            best_pockets = cand
            best_is_pinwheel = True

    # 2. Horizontal strips (rows stacked along Y; each row is either A=(px,py) or B=(py,px))
    cols_a = _fit_count(avail_x, px)
    cols_b = _fit_count(avail_x, py)
    max_ra = _fit_count(avail_y, py) if cols_a > 0 else 0
    max_rb = _fit_count(avail_y, px) if cols_b > 0 else 0

    for ra in range(max_ra + 1):
        for rb in range(max_rb + 1):
            total_rows = ra + rb
            if total_rows == 0:
                continue
            used_y = ra * py + rb * px + (total_rows - 1) * divider
            if used_y > avail_y + eps:
                continue
            count = ra * cols_a + rb * cols_b
            uniform_bonus = 1 if (ra == 0 or rb == 0) else 0
            score = (count, uniform_bonus, 0.0)
            if score > best_score:
                best_score = score
                best_is_pinwheel = False
                pockets: list[_Pocket] = []
                # Stack A-rows then B-rows centered in Y
                y_cursor = -used_y / 2.0
                for _ in range(ra):
                    cy = y_cursor + py / 2.0
                    pitch_x = px + divider
                    for c in range(cols_a):
                        cx = -((cols_a - 1) * pitch_x) / 2.0 + c * pitch_x
                        pockets.append(_Pocket(cx=cx, cy=cy, sx=px, sy=py))
                    y_cursor += py + divider
                for _ in range(rb):
                    cy = y_cursor + px / 2.0
                    pitch_x = py + divider
                    for c in range(cols_b):
                        cx = -((cols_b - 1) * pitch_x) / 2.0 + c * pitch_x
                        pockets.append(_Pocket(cx=cx, cy=cy, sx=py, sy=px))
                    y_cursor += px + divider
                best_pockets = pockets

    # 3. Vertical strips (columns stacked along X; each col is either A=(px,py) or B=(py,px))
    rows_a = _fit_count(avail_y, py)
    rows_b = _fit_count(avail_y, px)
    max_ca = _fit_count(avail_x, px) if rows_a > 0 else 0
    max_cb = _fit_count(avail_x, py) if rows_b > 0 else 0

    for ca in range(max_ca + 1):
        for cb in range(max_cb + 1):
            total_cols = ca + cb
            if total_cols == 0:
                continue
            used_x = ca * px + cb * py + (total_cols - 1) * divider
            if used_x > avail_x + eps:
                continue
            count = ca * rows_a + cb * rows_b
            uniform_bonus = 1 if (ca == 0 or cb == 0) else 0
            score = (count, uniform_bonus, -0.1)
            if score > best_score:
                best_score = score
                best_is_pinwheel = False
                pockets = []
                x_cursor = -used_x / 2.0
                for _ in range(ca):
                    cx = x_cursor + px / 2.0
                    pitch_y = py + divider
                    for r in range(rows_a):
                        cy = -((rows_a - 1) * pitch_y) / 2.0 + r * pitch_y
                        pockets.append(_Pocket(cx=cx, cy=cy, sx=px, sy=py))
                    x_cursor += px + divider
                for _ in range(cb):
                    cx = x_cursor + py / 2.0
                    pitch_y = px + divider
                    for r in range(rows_b):
                        cy = -((rows_b - 1) * pitch_y) / 2.0 + r * pitch_y
                        pockets.append(_Pocket(cx=cx, cy=cy, sx=py, sy=px))
                    x_cursor += py + divider
                best_pockets = pockets

    # Fallback: if target grid is too small for even 1 battery, return 1 centered pocket
    if not best_pockets:
        best_pockets = [_Pocket(cx=0.0, cy=0.0, sx=px, sy=py)]
        best_is_pinwheel = False

    return (best_pockets, best_is_pinwheel)


def _build_pinwheel_pull_loop(
    center_clear: float,
    lead_in: float,
    total_h: float,
    loop_height: float,
) -> Optional[Part]:
    """Build a smoothly blended, ergonomic center finger pull loop for pinwheel layouts.

    Starts strictly inside the flat center square (clear of all 4 pocket top
    lead-in chamfers), lofts smoothly into a 45°-aligned rounded handle stem,
    and finishes with a smooth round finger hole and generous edge fillets.
    """
    # Keep the loft footprint strictly inside the flat center square between the 4 lead-in chamfers
    flat_s = center_clear - 2.0 * lead_in
    base_s = flat_s - 0.4
    safe_s = center_clear - 1.0
    loop_t = min(8.5, flat_s * 0.36)
    ring_wall = 4.0
    fillet_r = min(1.8, loop_t * 0.22, ring_wall * 0.42)
    # Rounded rectangle W×T (corner r) rotated 45° has max X/Y extent:
    # (W + T - 4r) / (2*sqrt(2)) + r <= safe_s / 2
    max_w = (safe_s / 2.0 - fillet_r) * (2.0 * math.sqrt(2.0)) - loop_t + 4.0 * fillet_r
    loop_w = min(28.0, max_w)
    hole_w = loop_w - 2.0 * ring_wall
    if base_s < 8.0 or hole_w < 14.0 or loop_t < 5.0:
        return None

    hole_r = hole_w / 2.0
    hole_h = min(hole_w + 3.0, max(hole_w, loop_height - 20.0))
    min_height = hole_h + ring_wall + 10.0
    eff_h = max(loop_height, min_height)

    top_z = total_h + eff_h
    hole_top_z = top_z - ring_wall
    hole_bot_z = hole_top_z - hole_h

    # Smooth sculpted transition from flat center square into handle cross-section
    trans_h = min(14.0, max(6.0, hole_bot_z - total_h - 2.0))
    trans_top_z = total_h + trans_h
    z_base = total_h - 0.2  # shallow overlap inside flat center square (never touches pocket chamfers)

    # 1. Sculpted base transition: square center pillar -> 45° handle cross-section
    with BuildPart(mode=Mode.PRIVATE) as stem_bp:
        with BuildSketch(Plane.XY.offset(z_base)):
            RectangleRounded(base_s, base_s, min(3.5, base_s * 0.2))
        with BuildSketch(Plane.XY.offset(trans_top_z).rotated((0, 0, 45))):
            RectangleRounded(loop_w, loop_t, fillet_r)
        loft()

    # 2. Upper ring body (tombstone arch in XZ from trans_top_z to top_z, rotated 45° around Z)
    arch_r = loop_w / 2.0
    arch_center_z = top_z - arch_r

    # Smoothly rounded flat-crowned finger hole: rounded shoulders transitioning
    # tangentially into a short straight horizontal bridge (comfortable & clean to print)
    flat_w = min(8.0, hole_w * 0.42)
    flat_half = flat_w / 2.0
    top_corner_r = hole_r - flat_half
    straight_h = max(2.0, hole_h - hole_r - top_corner_r)
    eff_hole_h = hole_r + straight_h + top_corner_r
    hole_bot_z = hole_top_z - eff_hole_h
    z_arc_center = hole_bot_z + hole_r
    z_top_arc_center = z_arc_center + straight_h
    diag = top_corner_r * math.sqrt(0.5)

    with BuildPart(mode=Mode.PRIVATE) as ring_bp:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Line((-arch_r, trans_top_z), (arch_r, trans_top_z))
                Line((arch_r, trans_top_z), (arch_r, arch_center_z))
                ThreePointArc((arch_r, arch_center_z), (0.0, top_z), (-arch_r, arch_center_z))
                Line((-arch_r, arch_center_z), (-arch_r, trans_top_z))
            make_face()
        extrude(amount=loop_t / 2.0, both=True)

        # Round outer arch & sides (flush with stem_bp's fillet_r) before cutting hole
        if fillet_r > 0.3:
            outer_edges = ring_bp.edges().filter_by(lambda e: e.center().Z > trans_top_z + 0.2)
            if outer_edges:
                fillet(outer_edges, radius=fillet_r)

        # Smooth rounded-shoulder flat-crowned finger hole
        with BuildSketch(Plane.XZ):
            with BuildLine():
                ThreePointArc((-hole_r, z_arc_center), (0.0, hole_bot_z), (hole_r, z_arc_center))
                Line((hole_r, z_arc_center), (hole_r, z_top_arc_center))
                ThreePointArc(
                    (hole_r, z_top_arc_center),
                    (flat_half + diag, z_top_arc_center + diag),
                    (flat_half, hole_top_z),
                )
                Line((flat_half, hole_top_z), (-flat_half, hole_top_z))
                ThreePointArc(
                    (-flat_half, hole_top_z),
                    (-flat_half - diag, z_top_arc_center + diag),
                    (-hole_r, z_top_arc_center),
                )
                Line((-hole_r, z_top_arc_center), (-hole_r, z_arc_center))
            make_face()
        extrude(amount=loop_t / 2.0 + 1.0, both=True, mode=Mode.SUBTRACT)

        # 45° comfort chamfer on inner hole rims (prints cleanly on overhangs, unlike a fillet)
        hole_chamfer = min(1.2, loop_t * 0.16, ring_wall * 0.30)
        if hole_chamfer > 0.2:
            hole_rim_edges = ring_bp.edges().filter_by(
                lambda e: abs(abs(e.center().Y) - loop_t / 2.0) < 0.15
                and (hole_bot_z - 0.5) <= e.center().Z <= (hole_top_z + 0.5)
                and abs(e.center().X) <= (hole_r + 0.5)
            )
            if hole_rim_edges:
                chamfer(hole_rim_edges, length=hole_chamfer)

    with BuildPart(mode=Mode.PRIVATE) as combined_bp:
        add(stem_bp.part)
        add(ring_bp.part.rotate(Axis.Z, 45.0))

    return combined_bp.part


def _rounded_rect(width: float, height: float, radius: float) -> None:
    """Add a centered rectangle (rounded when radius > 0) inside an active BuildSketch."""
    r = min(radius, width / 2.0 - 0.1, height / 2.0 - 0.1)
    if r > 0.05:
        RectangleRounded(width, height, r)
    else:
        Rectangle(width, height)


def _make_lead_in_tool(
    sx: float,
    sy: float,
    pocket_r: float,
    lead_in: float,
    total_h: float,
) -> Part:
    """Build a single frustum subtraction solid for a pocket's top lead-in chamfer."""
    top_overshoot = 0.2
    top_expand = lead_in + top_overshoot
    r_bot = min(pocket_r, sx / 2.0 - 0.1, sy / 2.0 - 0.1)
    with BuildPart(mode=Mode.PRIVATE) as lead_bp:
        with BuildSketch(Plane.XY.offset(total_h - lead_in)):
            _rounded_rect(sx, sy, r_bot)
        with BuildSketch(Plane.XY.offset(total_h + top_overshoot)):
            _rounded_rect(
                sx + 2.0 * top_expand,
                sy + 2.0 * top_expand,
                r_bot + top_expand if r_bot > 0.05 else 0.0,
            )
        loft()
    return lead_bp.part


def _resolve_layout(
    params: RcBatteryCaddyParams,
) -> tuple[list[_Pocket], float, float, int, int, bool]:
    """Compute (pockets, outer_x, outer_y, gx, gy, is_pinwheel) for the active config."""
    bat = params.battery
    lay = params.layout
    gf = params.gridfinity
    st = params.structure
    tf = params.test_fit

    px, py = resolve_pocket_xy(bat)
    use_gridfinity = (gf is not None) and not tf.enabled

    if tf.enabled:
        pockets = [_Pocket(cx=0.0, cy=0.0, sx=px, sy=py)]
        return (
            pockets,
            px + 2.0 * st.outer_wall_thickness,
            py + 2.0 * st.outer_wall_thickness,
            0,
            0,
            False,
        )

    if lay.pattern == "pinwheel":
        long_s = max(px, py)
        short_s = min(px, py)
        min_span = long_s + short_s + st.divider_thickness
        min_outer = min_span + 2.0 * st.outer_wall_thickness
        if use_gridfinity and gf is not None:
            gx, gy, outer_x, outer_y = compute_gridfinity_footprint(
                min_outer, min_outer, grid_x=gf.grid_x, grid_y=gf.grid_y,
            )
            span = min(outer_x, outer_y) - 2.0 * st.outer_wall_thickness
        else:
            gx, gy = 0, 0
            outer_x = outer_y = min_outer
            span = min_span
        pockets = _build_pinwheel_pockets(
            px, py, span, st.divider_thickness, lay.pinwheel_center == "cubby",
        )
        return (pockets, outer_x, outer_y, gx, gy, True)

    if lay.pattern == "auto_pack":
        target_gx = lay.pack_grid_x
        target_gy = lay.pack_grid_y
        if use_gridfinity and gf is not None:
            if gf.grid_x is not None:
                target_gx = max(target_gx, gf.grid_x)
            if gf.grid_y is not None:
                target_gy = max(target_gy, gf.grid_y)
        outer_x = target_gx * GRIDFINITY_UNIT_XY - GRIDFINITY_CLEARANCE
        outer_y = target_gy * GRIDFINITY_UNIT_XY - GRIDFINITY_CLEARANCE
        avail_x = outer_x - 2.0 * st.outer_wall_thickness
        avail_y = outer_y - 2.0 * st.outer_wall_thickness
        pockets, is_pinwheel = _auto_pack_pockets(
            px, py, avail_x, avail_y, st.divider_thickness, lay.pinwheel_center == "cubby",
        )
        # Ensure outer footprint encloses fallback pocket if target grid was tiny
        req_x = max(p.cx + p.sx / 2.0 for p in pockets) - min(p.cx - p.sx / 2.0 for p in pockets) + 2.0 * st.outer_wall_thickness
        req_y = max(p.cy + p.sy / 2.0 for p in pockets) - min(p.cy - p.sy / 2.0 for p in pockets) + 2.0 * st.outer_wall_thickness
        if use_gridfinity:
            gx, gy, outer_x, outer_y = compute_gridfinity_footprint(
                max(outer_x, req_x), max(outer_y, req_y), grid_x=target_gx, grid_y=target_gy,
            )
        else:
            gx, gy = 0, 0
            outer_x = max(outer_x, req_x)
            outer_y = max(outer_y, req_y)
        return (pockets, outer_x, outer_y, gx, gy, is_pinwheel)

    # Default: uniform grid
    slot_x, slot_y = (py, px) if lay.rotate_90 else (px, py)
    pockets = _build_grid_pockets(slot_x, slot_y, lay.columns, lay.rows, st.divider_thickness)
    min_outer_x = lay.columns * slot_x + (lay.columns - 1) * st.divider_thickness + 2.0 * st.outer_wall_thickness
    min_outer_y = lay.rows * slot_y + (lay.rows - 1) * st.divider_thickness + 2.0 * st.outer_wall_thickness
    if use_gridfinity and gf is not None:
        gx, gy, outer_x, outer_y = compute_gridfinity_footprint(
            min_outer_x, min_outer_y, grid_x=gf.grid_x, grid_y=gf.grid_y,
        )
    else:
        gx, gy = 0, 0
        outer_x, outer_y = min_outer_x, min_outer_y
    return (pockets, outer_x, outer_y, gx, gy, False)


def _has_neighbor(pk: _Pocket, all_pockets: list[_Pocket], side: Literal["-Y", "+Y", "-X", "+X"]) -> bool:
    """Return True if another battery pocket lies between ``pk`` and the given outer wall."""
    eps = 0.5
    x0, x1 = pk.cx - pk.sx / 2.0, pk.cx + pk.sx / 2.0
    y0, y1 = pk.cy - pk.sy / 2.0, pk.cy + pk.sy / 2.0
    for other in all_pockets:
        if other is pk or other.is_center_cubby:
            continue
        ox0, ox1 = other.cx - other.sx / 2.0, other.cx + other.sx / 2.0
        oy0, oy1 = other.cy - other.sy / 2.0, other.cy + other.sy / 2.0
        if side == "-Y" and oy1 <= y0 + eps and min(x1, ox1) - max(x0, ox0) > eps:
            return True
        if side == "+Y" and oy0 >= y1 - eps and min(x1, ox1) - max(x0, ox0) > eps:
            return True
        if side == "-X" and ox1 <= x0 + eps and min(y1, oy1) - max(y0, oy0) > eps:
            return True
        if side == "+X" and ox0 >= x1 - eps and min(y1, oy1) - max(y0, oy0) > eps:
            return True
    return False


def create_rc_battery_caddy(params: RcBatteryCaddyParams) -> Part:
    """Build the RC LiPo battery caddy solid."""
    gf = params.gridfinity
    st = params.structure
    cut = params.cutouts
    tf = params.test_fit

    pockets, outer_x, outer_y, gx, gy, is_pinwheel = _resolve_layout(params)
    use_gridfinity = (gf is not None) and not tf.enabled
    open_bottom = tf.enabled and tf.open_bottom

    base_z = GRIDFINITY_FOOT_HEIGHT if use_gridfinity else 0.0
    floor_h = 0.0 if open_bottom else st.floor_thickness
    wall_h = tf.height if tf.enabled else st.wall_height
    body_h = floor_h + wall_h
    floor_top_z = base_z + floor_h
    total_h = base_z + body_h

    outer_r = (
        GRIDFINITY_CORNER_RADIUS
        if use_gridfinity
        else min(st.outer_corner_radius, outer_x / 2.0 - 0.5, outer_y / 2.0 - 0.5)
    )

    min_edge_wall = min(
        min(outer_x / 2.0 - (pk.cx + pk.sx / 2.0) for pk in pockets),
        min(outer_x / 2.0 + (pk.cx - pk.sx / 2.0) for pk in pockets),
        min(outer_y / 2.0 - (pk.cy + pk.sy / 2.0) for pk in pockets),
        min(outer_y / 2.0 + (pk.cy - pk.sy / 2.0) for pk in pockets),
    )
    min_edge_wall = max(0.8, min_edge_wall)

    max_lead_in = min(
        min_edge_wall * 0.42,
        st.divider_thickness * 0.42 if len(pockets) > 1 else min_edge_wall * 0.42,
        wall_h * 0.35,
    )
    lead_in = min(st.top_lead_in_chamfer, max_lead_in)

    # Cache lead-in frustum tools by rounded pocket size
    lead_in_tools: dict[tuple[float, float], Part] = {}
    if lead_in > 0.05:
        for pk in pockets:
            key = (round(pk.sx, 4), round(pk.sy, 4))
            if key not in lead_in_tools:
                lead_in_tools[key] = _make_lead_in_tool(
                    pk.sx, pk.sy, st.pocket_corner_radius, lead_in, total_h,
                )

    with BuildPart() as caddy:
        # 1. Outer solid shell (starting above Gridfinity feet when enabled)
        with BuildSketch(Plane.XY.offset(base_z)):
            _rounded_rect(outer_x, outer_y, outer_r)
        extrude(amount=body_h)

        # 2. Outer bottom chamfer (flat base only) and subtle top rim bevel
        if not use_gridfinity and st.bottom_chamfer > 0.05:
            max_bot_ch = min(
                st.bottom_chamfer,
                (floor_h * 0.65 if not open_bottom else wall_h * 0.2),
                min_edge_wall * 0.42,
            )
            if max_bot_ch > 0.05:
                bottom_edges = caddy.faces().sort_by(Axis.Z)[0].outer_wire().edges()
                chamfer(bottom_edges, length=max_bot_ch)

        top_outer_bevel = min(0.5, min_edge_wall * 0.25, wall_h * 0.1)
        if top_outer_bevel > 0.05:
            top_edges = caddy.faces().sort_by(Axis.Z)[-1].outer_wire().edges()
            chamfer(top_edges, length=top_outer_bevel)

        # 3. Standard Gridfinity 3-stage feet fused underneath
        if use_gridfinity and gf is not None:
            feet = create_gridfinity_base(gf, grid_x=gx, grid_y=gy)
            add(feet)

        # 4. Battery pockets (and optional pinwheel center cubby)
        battery_pockets = [pk for pk in pockets if not pk.is_center_cubby]
        cubby_pockets = [pk for pk in pockets if pk.is_center_cubby]

        with BuildSketch(Plane.XY.offset(floor_top_z)):
            for pk in battery_pockets:
                with Locations((pk.cx, pk.cy)):
                    _rounded_rect(pk.sx, pk.sy, st.pocket_corner_radius)
        extrude(amount=wall_h + 1.0, mode=Mode.SUBTRACT)

        # Subtle internal pocket floor fillet to strengthen wall roots & soften the floor-to-wall hull line
        if not open_bottom and wall_h >= 12.0:
            floor_fillet_r = min(1.0, wall_h * 0.15)
            inner_floor_edges = caddy.edges().filter_by(
                lambda e: abs(e.center().Z - floor_top_z) < 0.05
                and abs(e.center().X) < (outer_x / 2.0 - 0.5)
                and abs(e.center().Y) < (outer_y / 2.0 - 0.5)
            )
            if inner_floor_edges:
                fillet(inner_floor_edges, radius=floor_fillet_r)

        cubby_depth = (
            wall_h
            if params.layout.pinwheel_cubby_depth is None
            else min(params.layout.pinwheel_cubby_depth, wall_h)
        )
        if cubby_pockets and cubby_depth > 0.1:
            cubby_floor_z = total_h - cubby_depth
            with BuildSketch(Plane.XY.offset(cubby_floor_z)):
                for pk in cubby_pockets:
                    with Locations((pk.cx, pk.cy)):
                        _rounded_rect(pk.sx, pk.sy, st.pocket_corner_radius)
            extrude(amount=cubby_depth + 1.0, mode=Mode.SUBTRACT)

        # 5. Internal top lead-in chamfers around each pocket opening
        if lead_in_tools:
            for pk in pockets:
                key = (round(pk.sx, 4), round(pk.sy, 4))
                with Locations((pk.cx, pk.cy)):
                    add(lead_in_tools[key], mode=Mode.SUBTRACT)

        # 6. Floor push-out / drainage / cooling cutouts (flat base only; keep center cubby floor solid)
        if cut.enabled and cut.floor_holes and not open_bottom and not use_gridfinity:
            hole_specs: list[tuple[float, float, float, float, float]] = []
            for pk in pockets:
                if pk.is_center_cubby:
                    continue
                hole_x = pk.sx - 2.0 * cut.floor_ledge_width
                hole_y = pk.sy - 2.0 * cut.floor_ledge_width
                if hole_x >= 8.0 and hole_y >= 8.0:
                    hole_r = min(st.pocket_corner_radius + 1.0, hole_x / 2.0 - 0.5, hole_y / 2.0 - 0.5)
                    hole_specs.append((pk.cx, pk.cy, hole_x, hole_y, hole_r))
            if hole_specs:
                with BuildSketch(Plane.XY.offset(-0.5)):
                    for cx, cy, hx, hy, hr in hole_specs:
                        with Locations((cx, cy)):
                            _rounded_rect(hx, hy, hr)
                extrude(amount=floor_h + 1.0, mode=Mode.SUBTRACT)

        # 7. Support-free U-shaped outer wall finger-grip / label viewing notches
        if cut.enabled and cut.side_notches and not tf.enabled and wall_h >= 20.0:
            notch_d = min(wall_h * cut.side_notch_depth_ratio, wall_h - 8.0)
            if notch_d >= 5.0:
                top_clearance = 4.0
                sketch_h = notch_d + top_clearance
                center_z = total_h - notch_d + sketch_h / 2.0

                for pk in pockets:
                    if pk.is_center_cubby:
                        continue

                    if is_pinwheel:
                        # Each pinwheel pack gets a notch on its long outer wall
                        if pk.sx >= pk.sy:
                            sides_y = ["+Y"] if pk.cy > 0 else ["-Y"]
                            sides_x: list[str] = []
                        else:
                            sides_y = []
                            sides_x = ["+X"] if pk.cx > 0 else ["-X"]
                    else:
                        sides_y = [s for s in ("-Y", "+Y") if not _has_neighbor(pk, pockets, s)]
                        sides_x = []

                    # Front (-Y) and Back (+Y) wall notches (Plane.XZ normal = -Y)
                    for side in sides_y:
                        nw = pk.sx * cut.side_notch_width_ratio
                        if nw < 6.0:
                            continue
                        nr = min(nw * 0.45, notch_d * 0.45, 5.0)
                        if side == "+Y":
                            y_inner = pk.cy + pk.sy / 2.0
                            y_outer = outer_y / 2.0
                        else:
                            y_inner = -outer_y / 2.0
                            y_outer = pk.cy - pk.sy / 2.0
                        y_mid = (y_inner + y_outer) / 2.0
                        half_t = abs(y_outer - y_inner) / 2.0 + 1.0
                        with BuildSketch(Plane.XZ.offset(-y_mid)):
                            with Locations((pk.cx, center_z)):
                                _rounded_rect(nw, sketch_h, nr)
                        extrude(amount=half_t, both=True, mode=Mode.SUBTRACT)

                    # Left (-X) and Right (+X) wall notches (Plane.YZ normal = +X; local X = +Y, local Y = +Z)
                    for side in sides_x:
                        nw = pk.sy * cut.side_notch_width_ratio
                        if nw < 6.0:
                            continue
                        nr = min(nw * 0.45, notch_d * 0.45, 5.0)
                        if side == "+X":
                            x_inner = pk.cx + pk.sx / 2.0
                            x_outer = outer_x / 2.0
                        else:
                            x_inner = -outer_x / 2.0
                            x_outer = pk.cx - pk.sx / 2.0
                        x_mid = (x_inner + x_outer) / 2.0
                        half_t = abs(x_outer - x_inner) / 2.0 + 1.0
                        with BuildSketch(Plane.YZ.offset(x_mid)):
                            with Locations((pk.cy, center_z)):
                                _rounded_rect(nw, sketch_h, nr)
                        extrude(amount=half_t, both=True, mode=Mode.SUBTRACT)

        # 8. Optional center finger pull loop for pinwheel layouts
        if is_pinwheel and not tf.enabled and params.layout.pinwheel_center == "pull_loop":
            px, py = resolve_pocket_xy(params.battery)
            short_s = min(px, py)
            span = min(outer_x, outer_y) - 2.0 * st.outer_wall_thickness
            center_clear = span - 2.0 * short_s
            pull_loop = _build_pinwheel_pull_loop(
                center_clear=center_clear,
                lead_in=lead_in,
                total_h=total_h,
                loop_height=params.layout.pull_loop_height,
            )
            if pull_loop is not None:
                add(pull_loop)

    return caddy.part


def export_filename(params: RcBatteryCaddyParams) -> str:
    """Return standardized lowercase snake_case export filename stem."""
    bat = params.battery
    if bat.battery_type == "custom":
        length, width, thickness = resolve_battery_dimensions(bat)
        bat_tag = f"custom_{length:g}x{width:g}x{thickness:g}mm"
    else:
        bat_tag = bat.battery_type

    if params.test_fit.enabled:
        return f"rc_battery_caddy_{bat_tag}_{bat.orientation}_test_fit"

    lay = params.layout
    if lay.pattern == "pinwheel":
        layout_tag = "pinwheel_4x"
    elif lay.pattern == "auto_pack":
        layout_tag = f"pack_{lay.pack_grid_x}x{lay.pack_grid_y}u"
    else:
        rot_tag = "_rot90" if lay.rotate_90 else ""
        layout_tag = f"{lay.columns}x{lay.rows}{rot_tag}"

    base_tag = "_gridfinity" if params.gridfinity is not None else ""
    return f"rc_battery_caddy_{bat_tag}_{layout_tag}_{bat.orientation}{base_tag}"


if __name__ == "__main__":
    from utils.runner import run_model

    params = RcBatteryCaddyParams()
    part = create_rc_battery_caddy(params)
    run_model(part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
