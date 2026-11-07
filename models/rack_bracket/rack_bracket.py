"""
19-Inch Rackmount L-Bracket (Parametric build123d Model with M4 Thread-In Holes & Stacking Clearance)

Fully parameterized L-bracket supporting arbitrary rack unit counts (1U, 2U, 3U, 4U, etc.),
custom lengths, repeating M4 thread-in side hole arrays, EIA-310 standard mounting slots,
and selectable ventilation styles ('hex', 'window', 'none').
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
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
EXPORT_STL: bool = False                # Save .stl file on execution (default: False)
EXPORT_STEP: bool = False               # Save .step file on execution (default: False)
OUTPUT_DIR: str = "exports"            # Output folder (relative to this script's directory)


@dataclass
class RackBracketParams:
    """Parameters for 19-inch rackmount L-bracket."""

    # Rack Unit & Dimension parameters (change u_count to 1, 2, 3, 4, etc.)
    u_count: int = 1                       # Number of Rack Units (1U, 2U, 3U, 4U, etc.)
    u_height_unit: float = 44.45           # Nominal 1U height (1.75 in / 44.45 mm)
    height_margin: float = 1.2             # Subtracted margin for clean rack stacking fit (1.2mm total clearance)
    bracket_length: float = 150.0          # Side plate length in mm (default 150 mm)
    front_flange_width: float = 20.0       # Front flange width in mm
    thickness: float = 3.0                 # Wall thickness in mm (3.0mm for sturdy 3D prints)
    inner_bend_radius: float = 1.5         # Inside corner fillet radius
    outer_corner_radius: float = 1.5       # Fillet for sharp outer vertical corners

    # Side M4 thread-in pilot hole parameters
    side_hole_dia: float = 3.3             # M4 thread-in hole diameter in mm (3.3 mm for tapping into plastic)
    side_hole_spacing_x: float = 25.0      # Horizontal repeating interval between hole columns in mm
    side_hole_rear_offset: float = 15.0    # Offset from rear edge to first hole column (15 mm)
    min_front_clearance: float = 10.0      # Minimum clearance before front bend
    side_hole_edge_offset: float = 9.7     # Offset from top/bottom edges to outer side hole rows (mm)
    include_intermediate_side_holes: bool = False # If True and cutout_style is 'none', adds hole rows at intermediate U centers
    side_hole_rows: Optional[List[float]] = None # Explicit Z heights for side hole rows (overrides auto)

    # Center Cutout Window Options (Snapped to hex cell centers)
    cutout_style: str = "hex"              # Cutout style: 'hex' (honeycomb grill), 'window' (single cutout), or 'none'
    cutout_margin_z: float = 15.7          # Top & bottom solid margin reserved along Z axis
    cutout_corner_radius: float = 1.0      # Corner radius for rectangular cutout window
    hex_pitch_count: int = 11              # Number of horizontal hex cell pitches to snap window width
    hex_radius: float = 4.5                # Circumradius of hex cell cutouts (mm)
    hex_wall_thickness: float = 1.5        # Uniform wall thickness between flat edges (mm)

    # Front EIA-310 Rack Slot parameters
    rack_slot_width: float = 9.5           # Slot width in mm
    rack_slot_height: float = 6.5          # Slot height in mm
    rack_slot_x_center: float = 10.0       # Center of slot on 20mm front flange
    slot_offset_end: float = 5.75          # Standard EIA-310 offset from top/bottom outer edge to slot center
    single_slot_1u: bool = True            # For 1U: if True, center 1 slot; if False, 2 slots at ends
    slot_z_positions: Optional[List[float]] = None # Explicit Z heights for rack slots (overrides auto)

    @property
    def total_height(self) -> float:
        """Total bracket height including stacking margin deduction."""
        return self.u_count * self.u_height_unit - self.height_margin


def create_rack_bracket(params: RackBracketParams) -> Part:
    """Generates a parametric 19-inch rackmount L-bracket solid body."""
    total_height = params.total_height

    with BuildPart() as bracket:
        # 1. Base L-profile sketch on XY plane
        with BuildSketch(Plane.XY) as profile:
            with BuildLine():
                p0 = (0, 0)
                p1 = (params.bracket_length, 0)
                p2 = (params.bracket_length, params.thickness)
                p3 = (params.thickness, params.thickness)
                p4 = (params.thickness, params.front_flange_width)
                p5 = (0, params.front_flange_width)
                Polyline(p0, p1, p2, p3, p4, p5, p0)
            make_face()

            all_verts = profile.vertices()
            inner_vert = all_verts.filter_by(
                lambda v: abs(v.X - params.thickness) < 0.01 and abs(v.Y - params.thickness) < 0.01
            )
            outer_verts = all_verts.filter_by(
                lambda v: (abs(v.X - params.bracket_length) < 0.01 and abs(v.Y) < 0.01)
                or (abs(v.X) < 0.01 and abs(v.Y - params.front_flange_width) < 0.01)
            )

            if params.inner_bend_radius > 0 and len(inner_vert) > 0:
                fillet(inner_vert, radius=params.inner_bend_radius)
            if params.outer_corner_radius > 0 and len(outer_verts) > 0:
                fillet(outer_verts, radius=params.outer_corner_radius)

        extrude(amount=total_height)

        # 2. Front Flange EIA-310 Mounting Slots (Scales with u_count)
        if params.slot_z_positions is not None:
            slot_z_positions = params.slot_z_positions
        elif params.u_count == 1:
            if params.single_slot_1u:
                slot_z_positions = [total_height / 2.0]
            else:
                slot_z_positions = [params.slot_offset_end, total_height - params.slot_offset_end]
        else:
            # Standard multi-U: top & bottom outer slots, plus center slot on each intermediate U
            slot_z_positions = [params.slot_offset_end, total_height - params.slot_offset_end]
            for u in range(1, params.u_count - 1):
                slot_z_positions.append((u + 0.5) * params.u_height_unit - (params.height_margin / 2.0))

        with BuildSketch(Plane.YZ):
            for z_pos in slot_z_positions:
                with Locations((params.rack_slot_x_center, z_pos)):
                    SlotOverall(params.rack_slot_width, params.rack_slot_height, rotation=0)
        extrude(amount=params.thickness * 4, dir=(1, 0, 0), mode=Mode.SUBTRACT)

        # 3. Center Window Cutout (Honeycomb grill or open window)
        flat_to_flat = math.sqrt(3) * params.hex_radius
        pitch_x = flat_to_flat + params.hex_wall_thickness
        pitch_z = 1.5 * params.hex_radius + params.hex_wall_thickness * (math.sqrt(3) / 2.0)

        rear_x = params.bracket_length - params.side_hole_rear_offset
        min_x = params.thickness + params.min_front_clearance
        window_center_x = (rear_x + min_x) / 2.0

        window_width = params.hex_pitch_count * pitch_x
        max_available_w = max(10.0, rear_x - min_x)
        if window_width > max_available_w:
            fit_pitches = max(1, int(max_available_w // pitch_x))
            window_width = fit_pitches * pitch_x

        window_center_z = total_height / 2.0
        window_height = total_height - (params.cutout_margin_z * 2.0)

        if window_width > 15.0 and window_height > 15.0 and params.cutout_style.lower() != "none":
            if params.cutout_style.lower() == "hex":
                half_w_grid = window_width / 2.0 + pitch_x
                half_h_grid = window_height / 2.0 + pitch_z

                hex_locs = []
                z_row = 0
                z_pos = -half_h_grid
                while z_pos <= half_h_grid:
                    x_offset = (pitch_x / 2.0) if (z_row % 2 == 1) else 0.0
                    x_pos = -half_w_grid + x_offset
                    while x_pos <= half_w_grid:
                        hex_locs.append((window_center_x + x_pos, window_center_z + z_pos))
                        x_pos += pitch_x
                    z_pos += pitch_z
                    z_row += 1

                with BuildSketch(Plane.XZ):
                    with Locations((window_center_x, window_center_z)):
                        if params.cutout_corner_radius > 0:
                            RectangleRounded(window_width, window_height, radius=params.cutout_corner_radius)
                        else:
                            Rectangle(window_width, window_height)
                    with BuildSketch(mode=Mode.INTERSECT):
                        for hx, hz in hex_locs:
                            with Locations((hx, hz)):
                                RegularPolygon(radius=params.hex_radius, side_count=6, rotation=30)
                extrude(amount=params.thickness * 4, dir=(0, 1, 0), mode=Mode.SUBTRACT)

            elif params.cutout_style.lower() == "window":
                with BuildSketch(Plane.XZ):
                    with Locations((window_center_x, window_center_z)):
                        if params.cutout_corner_radius > 0:
                            RectangleRounded(window_width, window_height, radius=params.cutout_corner_radius)
                        else:
                            Rectangle(window_width, window_height)
                extrude(amount=params.thickness * 4, dir=(0, 1, 0), mode=Mode.SUBTRACT)

        # 4. Dynamic Side Plate Mounting Holes (Scales automatically with u_count)
        x_columns = []
        cur_x = rear_x
        while cur_x >= min_x:
            x_columns.append(cur_x)
            cur_x -= params.side_hole_spacing_x

        # Calculate Z positions for hole rows
        if params.side_hole_rows is not None:
            z_positions = params.side_hole_rows
        elif params.u_count == 1:
            z_positions = [total_height / 2.0]
        else:
            # Place top and bottom hole rows in solid margins
            bottom_z = params.side_hole_edge_offset
            top_z = total_height - params.side_hole_edge_offset
            z_positions = [bottom_z, top_z]

            # Optional intermediate hole rows (only if solid or explicitly requested)
            if params.include_intermediate_side_holes or (
                params.cutout_style.lower() == "none" and params.u_count >= 3
            ):
                for u in range(1, params.u_count - 1):
                    u_center_z = (u + 0.5) * params.u_height_unit - (params.height_margin / 2.0)
                    z_positions.append(u_center_z)

        with BuildSketch(Plane.XZ):
            for h_x in x_columns:
                for h_z in z_positions:
                    with Locations((h_x, h_z)):
                        Circle(radius=params.side_hole_dia / 2.0)
        extrude(amount=params.thickness * 4, dir=(0, 1, 0), mode=Mode.SUBTRACT)

    assert bracket.part is not None, "Bracket generation failed"
    return bracket.part


if __name__ == "__main__":
    # Generates model using the parameters configured in RackBracketParams at the top of this file
    params = RackBracketParams()
    bracket = create_rack_bracket(params)

    # Standardized exports to the exports/ directory alongside this script
    if EXPORT_STEP or EXPORT_STL:
        exports_path = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_path.mkdir(parents=True, exist_ok=True)

        stem = f"rack_bracket_{params.u_count}u_{params.cutout_style.lower()}"

        if EXPORT_STL:
            stl_file = exports_path / f"{stem}.stl"
            export_stl(bracket, str(stl_file))
            print(f"Exported STL:  {stl_file}")

        if EXPORT_STEP:
            step_file = exports_path / f"{stem}.step"
            export_step(bracket, str(step_file))
            print(f"Exported STEP: {step_file}")

    show(bracket)
