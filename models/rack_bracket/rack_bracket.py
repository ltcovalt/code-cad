"""
19-Inch Rackmount L-Bracket (Parametric build123d Model with M4 Thread-In Holes & Stacking Clearance)

Fully parameterized L-bracket supporting 1U, 2U, 3U+ heights, custom lengths,
automatic repeating side M4 thread-in hole arrays, and selectable cutout styles ('hex', 'window', 'none').
"""

import math
from dataclasses import dataclass
from build123d import *
from ocp_vscode import set_defaults, show

set_defaults(orbit_control=True)

@dataclass
class RackBracketParams:
    """Parameters for 19-inch rackmount L-bracket."""
    
    # Rack Unit & Dimension parameters (Extended length for extra rear support)
    u_count: int = 2                       # Number of Rack Units (1U, 2U, 3U, 4U, etc.)
    u_height_unit: float = 44.45           # Nominal 1U height (1.75 in / 44.45 mm)
    height_margin: float = 1.2             # Subtracted margin for clean rack stacking fit (1.2mm total clearance)
    bracket_length: float = 150.0          # Extended side plate length in mm (150 mm)
    front_flange_width: float = 20.0       # Front flange width in mm
    thickness: float = 3.0                 # Wall thickness in mm (3.0mm for strong 3D prints)
    inner_bend_radius: float = 1.5         # Inside corner fillet radius
    outer_corner_radius: float = 1.5       # Fillet for sharp outer vertical corners

    # Side M4 thread-in pilot hole parameters (X = 35, 60, 85, 110, 135 mm)
    side_hole_dia: float = 3.3             # M4 thread-in hole diameter in mm (3.3 mm for M4 screws to tap into plastic)
    side_hole_spacing_x: float = 25.0      # Horizontal repeating interval between hole columns in mm
    side_hole_rear_offset: float = 15.0    # Offset from rear edge to first hole column (15 mm)
    min_front_clearance: float = 10.0      # Minimum clearance before front bend

    # Center Cutout Window Options (Snapped to hex cell centers)
    cutout_style: str = "hex"              # Cutout style: 'hex' (honeycomb grill), 'window' (single cutout), or 'none'
    cutout_margin_z: float = 15.7          # Top & bottom margin reserved along Z axis
    cutout_corner_radius: float = 1.0      # Minimal 1mm corner radius for sharp rectangular window
    hex_pitch_count: int = 11              # Number of horizontal hex cell pitches to snap window width

    # Honeycomb Mesh Parameters (Flat top/bottom faces horizontal)
    hex_radius: float = 4.5                # Circumradius of hex cell cutouts (mm)
    hex_wall_thickness: float = 1.5        # Uniform wall thickness between flat edges (mm)

    # Front EIA-310 Rack Slot parameters
    rack_slot_width: float = 9.5           # Slot width in mm
    rack_slot_height: float = 6.5          # Slot height in mm
    rack_slot_x_center: float = 10.0       # Center of slot on 20mm front flange


def create_rack_bracket(params: RackBracketParams) -> Part:
    """Generates a parametric 19-inch rackmount L-bracket solid body."""
    
    total_height = params.u_count * params.u_height_unit - params.height_margin

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
            inner_vert = all_verts.filter_by(lambda v: abs(v.X - params.thickness) < 0.01 and abs(v.Y - params.thickness) < 0.01)
            outer_verts = all_verts.filter_by(lambda v: (abs(v.X - params.bracket_length) < 0.01 and abs(v.Y) < 0.01) or (abs(v.X) < 0.01 and abs(v.Y - params.front_flange_width) < 0.01))
            
            if params.inner_bend_radius > 0 and len(inner_vert) > 0:
                fillet(inner_vert, radius=params.inner_bend_radius)
            if params.outer_corner_radius > 0 and len(outer_verts) > 0:
                fillet(outer_verts, radius=params.outer_corner_radius)

        extrude(amount=total_height)

        # 2. Front Flange EIA-310 Mounting Slots (Scales automatically with u_count)
        slot_z_positions = []
        slot_offset_end = 5.75
        if params.u_count == 1:
            slot_z_positions = [total_height / 2.0]
        else:
            slot_z_positions = [slot_offset_end, total_height - slot_offset_end]
            # Intermediate slots for 3U, 4U, etc.
            for u in range(1, params.u_count - 1):
                slot_z_positions.append((u + 0.5) * params.u_height_unit - (params.height_margin / 2.0))

        with BuildSketch(Plane.YZ):
            for z_pos in slot_z_positions:
                with Locations((params.rack_slot_x_center, z_pos)):
                    SlotOverall(params.rack_slot_width, params.rack_slot_height, rotation=0)
        extrude(amount=params.thickness * 4, dir=(1, 0, 0), mode=Mode.SUBTRACT)

        # 3. Center Window Cutout (Snapped to Hex Cell Midpoints)
        flat_to_flat = math.sqrt(3) * params.hex_radius
        pitch_x = flat_to_flat + params.hex_wall_thickness
        pitch_z = 1.5 * params.hex_radius + params.hex_wall_thickness * (math.sqrt(3) / 2.0)

        window_width = params.hex_pitch_count * pitch_x                  # 102.24 mm
        window_center_x = 85.0                                            # Middle screw column (X = 85.0 mm)
        window_center_z = total_height / 2.0
        window_height = total_height - (params.cutout_margin_z * 2.0)

        if window_width > 15.0 and window_height > 15.0:
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
        rear_x = params.bracket_length - params.side_hole_rear_offset
        min_x = params.thickness + params.min_front_clearance
        
        x_columns = []
        cur_x = rear_x
        while cur_x >= min_x:
            x_columns.append(cur_x)
            cur_x -= params.side_hole_spacing_x

        # Calculate Z positions for hole rows per Rack Unit
        z_positions = []
        if params.u_count == 1:
            z_positions = [total_height / 2.0]
        else:
            # Place top and bottom hole rows centered in each outer U, plus intermediate U centers for 3U+
            for u in range(params.u_count):
                u_center_z = (u + 0.5) * params.u_height_unit - (params.height_margin / 2.0)
                # For 2U: top hole row and bottom hole row at Z = 9.7mm and Z = 78.0mm
                if params.u_count == 2:
                    z_positions = [9.7, 78.0]
                    break
                else:
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
    # Change u_count here to generate 1U, 2U, 3U, 4U, etc.
    params = RackBracketParams()
    bracket = create_rack_bracket(params)
    
    step_filename = f"rack_bracket_{params.u_count}u.step"
    stl_filename = f"rack_bracket_{params.u_count}u.stl"
    
    export_step(bracket, step_filename)
    export_stl(bracket, stl_filename)
    print(f"{params.u_count}U Parametric Rack Bracket generated & exported to {step_filename} / {stl_filename}!")
    show(bracket)
