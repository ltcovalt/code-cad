"""
19-Inch Rackmount L-Bracket (Parametric build123d Model with M4 Thread-In Holes & Stacking Clearance)

Fully parameterized L-bracket supporting arbitrary rack unit counts (1U, 2U, 3U, 4U, etc.),
custom lengths, repeating M4 thread-in side hole arrays, EIA-310 standard mounting slots,
and selectable ventilation styles ('hex', 'window', 'none').
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional
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
EXPORT_STL: bool = False                # Save .stl file on execution (default: False)
EXPORT_STEP: bool = False               # Save .step file on execution (default: False)
OUTPUT_DIR: str = "exports"             # Output folder (relative to this script's directory)


@dataclass
class CoreParams:
    """Primary rack unit and L-bracket structural dimensions."""

    u_count: int = param(1, min=1, max=6, step=1, label="Rack Units", unit="U", desc="Number of rack units (1U, 2U, 3U, ...)")
    u_height_unit: float = param(44.45, label="1U Height", unit="mm", desc="Nominal 1U pitch (1.75 in)")
    height_margin: float = param(1.2, min=0.0, max=4.0, step=0.1, unit="mm", desc="Subtracted clearance for clean rack stacking")
    bracket_length: float = param(150.0, min=40.0, max=300.0, step=5.0, unit="mm", desc="Side plate depth along rack")
    front_flange_width: float = param(20.0, min=15.0, max=40.0, step=1.0, unit="mm", desc="Front mounting ear width")
    thickness: float = param(3.0, min=1.5, max=8.0, step=0.5, unit="mm", desc="Bracket wall thickness")
    inner_bend_radius: float = param(1.5, min=0.0, max=5.0, step=0.5, unit="mm", desc="Inside L-corner fillet radius")
    outer_corner_radius: float = param(1.5, min=0.0, max=5.0, step=0.5, unit="mm", desc="Outer vertical corner fillet radius")


@dataclass
class SideHolesParams:
    """Side M4 thread-in pilot hole array."""

    enabled: bool = param(True, desc="Cut side M4 pilot hole array")
    diameter: float = param(3.3, min=2.0, max=6.0, step=0.1, unit="mm", desc="M4 thread-in pilot hole diameter")
    spacing_x: float = param(25.0, min=10.0, max=60.0, step=1.0, label="Column Spacing (X)", unit="mm", desc="Horizontal spacing between hole columns")
    rear_offset: float = param(15.0, min=5.0, max=40.0, step=1.0, unit="mm", desc="Offset from rear edge to first column")
    min_front_clearance: float = param(10.0, min=5.0, max=30.0, step=1.0, unit="mm", desc="Minimum clearance before front bend")
    edge_offset: float = param(9.7, min=5.0, max=20.0, step=0.5, unit="mm", desc="Offset from top/bottom edges to outer rows")
    include_intermediate: bool = param(False, when={"cutout.style": "none"}, desc="Add hole rows at intermediate U centers")
    rows: Optional[List[float]] = param(None, desc="Explicit Z heights for side hole rows (Auto = calculated)")


@dataclass
class CutoutParams:
    """Center cutout window options (snapped to hex cell centers)."""

    style: Literal["hex", "window", "none"] = param("hex", desc="Ventilation cutout style")
    margin_z: float = param(15.7, min=6.0, max=30.0, step=0.5, label="Z Margin", unit="mm", when={"style": ["hex", "window"]}, desc="Solid margin reserved at top & bottom")
    corner_radius: float = param(1.0, min=0.0, max=10.0, step=0.5, unit="mm", when={"style": ["hex", "window"]}, desc="Corner radius of cutout window")
    hex_pitch_count: int = param(11, min=1, max=25, step=1, when={"style": ["hex", "window"]}, desc="Horizontal hex pitches to snap window width")
    hex_radius: float = param(4.5, min=2.0, max=12.0, step=0.5, unit="mm", when={"style": "hex"}, desc="Circumradius of hex cutouts")
    hex_wall_thickness: float = param(1.5, min=0.8, max=5.0, step=0.1, unit="mm", when={"style": "hex"}, desc="Wall thickness between hex flats")


@dataclass
class RackSlotsParams:
    """Front EIA-310 rack mounting slots."""

    width: float = param(9.5, min=5.0, max=15.0, step=0.5, unit="mm", desc="Mounting slot width")
    height: float = param(6.5, min=4.0, max=10.0, step=0.5, unit="mm", desc="Mounting slot height")
    x_center: float = param(10.0, min=5.0, max=25.0, step=0.5, label="Slot X Center", unit="mm", desc="Center position on front flange")
    offset_end: float = param(5.75, min=3.0, max=12.0, step=0.25, unit="mm", desc="EIA-310 offset from outer edge to slot center")
    single_slot_1u: bool = param(True, label="Single Slot (1U)", when={"core.u_count": 1}, desc="Center 1 slot for 1U instead of 2 end slots")
    z_positions: Optional[List[float]] = param(None, label="Z Positions", desc="Explicit Z heights for rack slots (Auto = EIA-310)")


@dataclass
class RackBracketParams:
    """Parameters for 19-inch rackmount L-bracket."""

    core: CoreParams = group(CoreParams)
    side_holes: SideHolesParams = group(SideHolesParams)
    cutout: CutoutParams = group(CutoutParams)
    rack_slots: RackSlotsParams = group(RackSlotsParams)

    @property
    def total_height(self) -> float:
        """Total bracket height including stacking margin deduction."""
        return self.core.u_count * self.core.u_height_unit - self.core.height_margin


def create_rack_bracket(params: RackBracketParams) -> Part:
    """Generates a parametric 19-inch rackmount L-bracket solid body."""
    core = params.core
    side = params.side_holes
    cutout = params.cutout
    slots = params.rack_slots
    total_height = params.total_height

    with BuildPart() as bracket:
        # 1. Base L-profile sketch on XY plane
        with BuildSketch(Plane.XY) as profile:
            with BuildLine():
                p0 = (0, 0)
                p1 = (core.bracket_length, 0)
                p2 = (core.bracket_length, core.thickness)
                p3 = (core.thickness, core.thickness)
                p4 = (core.thickness, core.front_flange_width)
                p5 = (0, core.front_flange_width)
                Polyline(p0, p1, p2, p3, p4, p5, p0)
            make_face()

            all_verts = profile.vertices()
            inner_vert = all_verts.filter_by(
                lambda v: abs(v.X - core.thickness) < 0.01 and abs(v.Y - core.thickness) < 0.01
            )
            outer_verts = all_verts.filter_by(
                lambda v: (abs(v.X - core.bracket_length) < 0.01 and abs(v.Y) < 0.01)
                or (abs(v.X) < 0.01 and abs(v.Y - core.front_flange_width) < 0.01)
            )

            if core.inner_bend_radius > 0 and len(inner_vert) > 0:
                fillet(inner_vert, radius=core.inner_bend_radius)
            if core.outer_corner_radius > 0 and len(outer_verts) > 0:
                fillet(outer_verts, radius=core.outer_corner_radius)

        extrude(amount=total_height)

        # 2. Front Flange EIA-310 Mounting Slots (Scales with u_count)
        if slots.z_positions:
            slot_z_positions = [float(z) for z in slots.z_positions]
        elif core.u_count == 1:
            if slots.single_slot_1u:
                slot_z_positions = [total_height / 2.0]
            else:
                slot_z_positions = [slots.offset_end, total_height - slots.offset_end]
        else:
            slot_z_positions = [slots.offset_end, total_height - slots.offset_end]
            for u in range(1, core.u_count - 1):
                slot_z_positions.append((u + 0.5) * core.u_height_unit - (core.height_margin / 2.0))

        if slot_z_positions:
            with BuildSketch(Plane.YZ) as slots_sk:
                for z_pos in slot_z_positions:
                    with Locations((slots.x_center, z_pos)):
                        SlotOverall(slots.width, slots.height, rotation=0)
            if len(slots_sk.faces()) > 0:
                extrude(amount=core.thickness * 4, dir=(1, 0, 0), mode=Mode.SUBTRACT)

        # 3. Center Window Cutout (Honeycomb grill or open window)
        flat_to_flat = math.sqrt(3) * cutout.hex_radius
        pitch_x = flat_to_flat + cutout.hex_wall_thickness
        pitch_z = 1.5 * cutout.hex_radius + cutout.hex_wall_thickness * (math.sqrt(3) / 2.0)

        rear_x = core.bracket_length - side.rear_offset
        min_x = core.thickness + side.min_front_clearance
        window_center_x = (rear_x + min_x) / 2.0

        window_width = cutout.hex_pitch_count * pitch_x
        max_available_w = max(10.0, rear_x - min_x)
        if window_width > max_available_w:
            fit_pitches = max(1, int(max_available_w // pitch_x))
            window_width = fit_pitches * pitch_x

        window_center_z = total_height / 2.0
        window_height = total_height - (cutout.margin_z * 2.0)

        if window_width > 15.0 and window_height > 15.0 and cutout.style.lower() != "none":
            if cutout.style.lower() == "hex":
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

                with BuildSketch(Plane.XZ) as hex_sk:
                    with Locations((window_center_x, window_center_z)):
                        if cutout.corner_radius > 0:
                            RectangleRounded(window_width, window_height, radius=cutout.corner_radius)
                        else:
                            Rectangle(window_width, window_height)
                    with BuildSketch(mode=Mode.INTERSECT):
                        for hx, hz in hex_locs:
                            with Locations((hx, hz)):
                                RegularPolygon(radius=cutout.hex_radius, side_count=6, rotation=30)
                if len(hex_sk.faces()) > 0:
                    extrude(amount=core.thickness * 4, dir=(0, 1, 0), mode=Mode.SUBTRACT)

            elif cutout.style.lower() == "window":
                with BuildSketch(Plane.XZ):
                    with Locations((window_center_x, window_center_z)):
                        if cutout.corner_radius > 0:
                            RectangleRounded(window_width, window_height, radius=cutout.corner_radius)
                        else:
                            Rectangle(window_width, window_height)
                extrude(amount=core.thickness * 4, dir=(0, 1, 0), mode=Mode.SUBTRACT)

        # 4. Dynamic Side Plate Mounting Holes (Scales automatically with u_count)
        if side.enabled and side.diameter > 0:
            x_columns = []
            cur_x = rear_x
            while cur_x >= min_x:
                x_columns.append(cur_x)
                cur_x -= side.spacing_x

            if side.rows:
                z_positions = [float(z) for z in side.rows]
            elif core.u_count == 1:
                z_positions = [total_height / 2.0]
            else:
                bottom_z = side.edge_offset
                top_z = total_height - side.edge_offset
                z_positions = [bottom_z, top_z]

                if side.include_intermediate or (
                    cutout.style.lower() == "none" and core.u_count >= 3
                ):
                    for u in range(1, core.u_count - 1):
                        u_center_z = (u + 0.5) * core.u_height_unit - (core.height_margin / 2.0)
                        z_positions.append(u_center_z)

            if x_columns and z_positions:
                with BuildSketch(Plane.XZ):
                    for h_x in x_columns:
                        for h_z in z_positions:
                            with Locations((h_x, h_z)):
                                Circle(radius=side.diameter / 2.0)
                extrude(amount=core.thickness * 4, dir=(0, 1, 0), mode=Mode.SUBTRACT)

    assert bracket.part is not None, "Bracket generation failed"
    return bracket.part


def export_filename(params: RackBracketParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    return f"rack_bracket_{params.core.u_count}u_{params.cutout.style.lower()}"


if __name__ == "__main__":
    params = RackBracketParams()
    bracket = create_rack_bracket(params)

    if EXPORT_STEP or EXPORT_STL:
        exports_path = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_path.mkdir(parents=True, exist_ok=True)

        stem = export_filename(params)

        if EXPORT_STL:
            stl_file = exports_path / f"{stem}.stl"
            export_stl(bracket, str(stl_file))
            print(f"Exported STL:  {stl_file}")

        if EXPORT_STEP:
            step_file = exports_path / f"{stem}.step"
            export_step(bracket, str(step_file))
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

    show(bracket)
