"""
Reusable Gridfinity Base Feet Component (build123d)

Provides standard 42 mm-pitch 3-stage Gridfinity base feet (z = 0 to 4.75 mm)
with optional corner magnet pockets so any organizer or caddy model can offer
a drop-in Gridfinity-compatible base, and a standalone `create_gridfinity_base`
entrypoint for Code CAD Studio preview and preset management.
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

GRIDFINITY_UNIT_XY: float = 42.0
GRIDFINITY_CLEARANCE: float = 0.5
GRIDFINITY_FOOT_HEIGHT: float = 4.75
GRIDFINITY_CORNER_RADIUS: float = 3.75


@default_preset(
    "Standard 6×2 mm Magnets",
    desc="42 mm-pitch Gridfinity base feet with 6.1 × 2.2 mm corner magnet pockets",
)
@dataclass
class GridfinityBaseParams:
    """Standard 42 mm Gridfinity-compatible modular base feet."""

    grid_x: Optional[int] = param(
        None,
        label="Gridfinity X Override",
        desc="Gridfinity units along X (Auto = smallest grid that fits, or 1U standalone)",
        unit="U", min=1, max=12, step=1,
    )
    grid_y: Optional[int] = param(
        None,
        label="Gridfinity Y Override",
        desc="Gridfinity units along Y (Auto = smallest grid that fits, or 1U standalone)",
        unit="U", min=1, max=12, step=1,
    )
    magnets: bool = param(
        True,
        label="Base Magnet Pockets",
        desc="Cut 4 corner magnet pockets per Gridfinity foot cell",
    )
    magnet_diameter: float = param(
        6.1,
        desc="Magnet pocket diameter",
        unit="mm", min=4.0, max=12.0, step=0.1,
        when={"magnets": True},
    )
    magnet_depth: float = param(
        2.2,
        desc="Magnet pocket depth",
        unit="mm", min=1.0, max=4.0, step=0.1,
        when={"magnets": True},
    )


def compute_gridfinity_footprint(
    min_x: float,
    min_y: float,
    *,
    unit_size: float = GRIDFINITY_UNIT_XY,
    clearance: float = GRIDFINITY_CLEARANCE,
    grid_x: Optional[int] = None,
    grid_y: Optional[int] = None,
) -> tuple[int, int, float, float]:
    """Compute Gridfinity (grid_x, grid_y, outer_x, outer_y) enclosing (min_x, min_y).

    If manual ``grid_x`` or ``grid_y`` overrides are supplied, they are clamped
    to at least the minimum unit count required to enclose ``(min_x, min_y)``.
    """
    auto_gx = max(1, math.ceil((min_x + clearance - 1e-6) / unit_size))
    auto_gy = max(1, math.ceil((min_y + clearance - 1e-6) / unit_size))

    gx = max(auto_gx, grid_x) if grid_x is not None else auto_gx
    gy = max(auto_gy, grid_y) if grid_y is not None else auto_gy

    outer_x = gx * unit_size - clearance
    outer_y = gy * unit_size - clearance
    return (gx, gy, outer_x, outer_y)


def create_gridfinity_base(
    params: GridfinityBaseParams,
    *,
    grid_x: Optional[int] = None,
    grid_y: Optional[int] = None,
    unit_size: float = GRIDFINITY_UNIT_XY,
    clearance: float = GRIDFINITY_CLEARANCE,
    corner_radius: float = GRIDFINITY_CORNER_RADIUS,
    magnet_offset: float = 13.0,
) -> Part:
    """Build an N × M array of standard 3-stage Gridfinity feet from z = 0 to 4.75 mm."""
    gx = grid_x if grid_x is not None else (params.grid_x if params.grid_x is not None else 1)
    gy = grid_y if grid_y is not None else (params.grid_y if params.grid_y is not None else 1)
    gx = max(1, gx)
    gy = max(1, gy)

    unit_w = unit_size - clearance  # 41.5 mm standard
    r_top = corner_radius
    r_mid = max(0.3, r_top - 2.15)
    r_bot = max(0.2, r_top - 2.95)

    with BuildPart(mode=Mode.PRIVATE) as single_foot:
        # Standard 3-stage ruled loft:
        #   z=0.00 -> z=0.80: 45° bottom chamfer (inset 2.95 mm -> 2.15 mm)
        #   z=0.80 -> z=2.60: vertical step (inset 2.15 mm, height 1.80 mm)
        #   z=2.60 -> z=4.75: 45° upper chamfer (inset 2.15 mm -> 0.00 mm)
        with BuildSketch(Plane.XY):
            RectangleRounded(unit_w - 2.0 * 2.95, unit_w - 2.0 * 2.95, r_bot)
        with BuildSketch(Plane.XY.offset(0.8)):
            RectangleRounded(unit_w - 2.0 * 2.15, unit_w - 2.0 * 2.15, r_mid)
        with BuildSketch(Plane.XY.offset(2.6)):
            RectangleRounded(unit_w - 2.0 * 2.15, unit_w - 2.0 * 2.15, r_mid)
        with BuildSketch(Plane.XY.offset(GRIDFINITY_FOOT_HEIGHT)):
            RectangleRounded(unit_w, unit_w, r_top)
        loft(ruled=True)

        if params.magnets and params.magnet_depth > 0.0 and params.magnet_diameter > 0.0:
            mo = magnet_offset
            hole_locs = [(-mo, -mo), (mo, -mo), (-mo, mo), (mo, mo)]
            with BuildSketch(Plane.XY):
                with Locations(hole_locs):
                    Circle(params.magnet_diameter / 2.0)
            extrude(amount=params.magnet_depth, mode=Mode.SUBTRACT)

    with BuildPart() as feet_grid:
        with GridLocations(unit_size, unit_size, gx, gy):
            add(single_foot.part)

    assert feet_grid.part is not None, "Failed to generate Gridfinity base feet"
    return feet_grid.part


def export_filename(params: GridfinityBaseParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    gx = params.grid_x if params.grid_x is not None else 1
    gy = params.grid_y if params.grid_y is not None else 1
    variant = f"mag{params.magnet_diameter:g}x{params.magnet_depth:g}mm" if params.magnets else "solid"
    return f"gridfinity_base_{gx}x{gy}u_{variant}"


if __name__ == "__main__":
    from utils.runner import run_model

    params = GridfinityBaseParams()
    part = create_gridfinity_base(params)
    run_model(part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
