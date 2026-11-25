"""
Reusable Gridfinity Base Feet Component (build123d)

Provides standard 42 mm-pitch 3-stage Gridfinity base feet (z = 0 to 4.75 mm)
with optional corner magnet pockets so any organizer or caddy model can offer
a drop-in Gridfinity-compatible base.
"""

from __future__ import annotations

import math
from typing import Optional

from build123d import *

GRIDFINITY_UNIT_XY: float = 42.0
GRIDFINITY_CLEARANCE: float = 0.5
GRIDFINITY_FOOT_HEIGHT: float = 4.75
GRIDFINITY_CORNER_RADIUS: float = 3.75


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


def build_gridfinity_feet(
    grid_x: int,
    grid_y: int,
    *,
    unit_size: float = GRIDFINITY_UNIT_XY,
    clearance: float = GRIDFINITY_CLEARANCE,
    corner_radius: float = GRIDFINITY_CORNER_RADIUS,
    magnets: bool = True,
    magnet_diameter: float = 6.1,
    magnet_depth: float = 2.2,
    magnet_offset: float = 13.0,
) -> Part:
    """Build an N × M array of standard 3-stage Gridfinity feet from z = 0 to 4.75 mm."""
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

        if magnets and magnet_depth > 0.0 and magnet_diameter > 0.0:
            mo = magnet_offset
            hole_locs = [(-mo, -mo), (mo, -mo), (-mo, mo), (mo, mo)]
            with BuildSketch(Plane.XY):
                with Locations(hole_locs):
                    Circle(magnet_diameter / 2.0)
            extrude(amount=magnet_depth, mode=Mode.SUBTRACT)

    with BuildPart() as feet_grid:
        with GridLocations(unit_size, unit_size, grid_x, grid_y):
            add(single_foot.part)

    return feet_grid.part
