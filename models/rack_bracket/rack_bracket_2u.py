"""
Functional 2U 19-Inch Rackmount Bracket (3D Printable with M4 Thread-In Holes & Stacking Clearance)

Features:
- Total height adjusted to 87.7mm (1.2mm total stack clearance for effortless multi-bracket rack stacking)
- Side M4 thread-in pilot holes (3.3mm diameter for M4 screws to cut threads directly into plastic walls)
- EIA-310-D rack rail slot spacing
- Extended bracket length (150mm) for extra rear material
- Honeycomb window snapped to exact hex pitch multiples for clean 50% half-hex perimeter cuts
- Smooth outer corner fillets (no sharp edges)
"""

import math
from dataclasses import dataclass
from typing import Optional
from build123d import *
from ocp_vscode import show


@dataclass
class RackBracket2UParams:
    """Parameters for 2U 19-inch rackmount L-bracket."""
    
    # Overall Dimensions (Adjusted for multi-unit rack stacking clearance)
    height: float = 87.7                   # 2U height in mm (87.7 mm gives 1.2mm stack margin for clean rack fit)
    length: float = 150.0                  # Extended side plate length in mm (150 mm)
    front_width: float = 20.0              # Front flange width in mm
    thickness: float = 3.0                 # Wall thickness (3.0 mm for sturdy 3D prints)
    inner_bend_radius: float = 1.5         # Inside corner fillet radius
    outer_corner_radius: float = 1.5       # Fillet for sharp outer vertical corners

    # Side Plate M4 Thread-In Pilot Holes (X = 35, 60, 85, 110, 135 mm)
    side_hole_dia: float = 3.3             # M4 thread-in hole diameter (3.3 mm for M4 screws to tap into plastic)
    side_hole_spacing_y: float = 68.3      # Vertical hole spacing (68.3 mm)
    side_hole_spacing_x: float = 25.0      # Horizontal repeating interval between holes in mm
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

    # Front EIA-310-D Rack Rail Mounting Slots
    slot_width: float = 9.5                # Horizontal slot length (9.5 mm)
    slot_height: float = 6.5               # Vertical slot height (6.5 mm)
    slot_z_bottom: float = 5.75            # Center Z of bottom slot (EIA-310 standard offset)
    slot_z_top: float = 81.95              # Center Z of top slot (EIA-310 standard offset)
    slot_x_center: float = 10.0            # Center X on 20mm front flange


def create_2u_bracket(params: RackBracket2UParams) -> Part:
    """Generates a 2U rackmount L-bracket solid body."""
    
    with BuildPart() as bracket:
        # 1. Base L-profile sketch on XY plane
        with BuildSketch(Plane.XY) as profile:
            with BuildLine():
                p0 = (0, 0)
                p1 = (params.length, 0)
                p2 = (params.length, params.thickness)
                p3 = (params.thickness, params.thickness)
                p4 = (params.thickness, params.front_width)
                p5 = (0, params.front_width)
                Polyline(p0, p1, p2, p3, p4, p5, p0)
            make_face()
            
            all_verts = profile.vertices()
            inner_vert = all_verts.filter_by(lambda v: abs(v.X - params.thickness) < 0.01 and abs(v.Y - params.thickness) < 0.01)
            outer_verts = all_verts.filter_by(lambda v: (abs(v.X - params.length) < 0.01 and abs(v.Y) < 0.01) or (abs(v.X) < 0.01 and abs(v.Y - params.front_width) < 0.01))
            
            if params.inner_bend_radius > 0 and len(inner_vert) > 0:
                fillet(inner_vert, radius=params.inner_bend_radius)
            if params.outer_corner_radius > 0 and len(outer_verts) > 0:
                fillet(outer_verts, radius=params.outer_corner_radius)

        extrude(amount=params.height)

        # 2. Front Flange EIA-310 Mounting Slots
        with BuildSketch(Plane.YZ):
            with Locations((params.slot_x_center, params.slot_z_bottom)):
                SlotOverall(params.slot_width, params.slot_height, rotation=0)
            with Locations((params.slot_x_center, params.slot_z_top)):
                SlotOverall(params.slot_width, params.slot_height, rotation=0)
        extrude(amount=params.thickness * 4, dir=(1, 0, 0), mode=Mode.SUBTRACT)

        # 3. Center Window Cutout (Snapped to Hex Cell Midpoints)
        flat_to_flat = math.sqrt(3) * params.hex_radius
        pitch_x = flat_to_flat + params.hex_wall_thickness
        pitch_z = 1.5 * params.hex_radius + params.hex_wall_thickness * (math.sqrt(3) / 2.0)

        # Snap window width to exact integer multiple of pitch_x for clean 50% half-hex perimeter cuts
        window_width = params.hex_pitch_count * pitch_x                  # 102.24 mm
        window_center_x = 85.0                                            # Middle screw column (X = 85.0 mm)
        window_center_z = params.height / 2.0                              # Z = 43.85 mm
        window_height = params.height - (params.cutout_margin_z * 2.0)

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
                
                # Intersect hex array with snapped window frame
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

        # 4. Dynamic Side Plate M4 Thread-In Pilot Holes (X = 35, 60, 85, 110, 135 mm, Dia 3.3mm)
        rear_x = params.length - params.side_hole_rear_offset
        min_x = params.thickness + params.min_front_clearance
        
        x_columns = []
        cur_x = rear_x
        while cur_x >= min_x:
            x_columns.append(cur_x)
            cur_x -= params.side_hole_spacing_x

        bottom_z = (params.height - params.side_hole_spacing_y) / 2.0  # 9.7 mm
        top_z = bottom_z + params.side_hole_spacing_y                 # 78.0 mm
        
        with BuildSketch(Plane.XZ):
            for h_x in x_columns:
                for h_z in [bottom_z, top_z]:
                    with Locations((h_x, h_z)):
                        Circle(radius=params.side_hole_dia / 2.0)
        extrude(amount=params.thickness * 4, dir=(0, 1, 0), mode=Mode.SUBTRACT)

    assert bracket.part is not None, "Bracket generation failed"
    return bracket.part


if __name__ == "__main__":
    params = RackBracket2UParams(cutout_style="hex")
    bracket = create_2u_bracket(params)
    export_step(bracket, "rack_bracket_2u.step")
    export_stl(bracket, "rack_bracket_2u.stl")
    print(f"2U Rack Bracket (M4 Thread-In & Stacking Clearance) successfully generated & exported!")
    show(bracket)
