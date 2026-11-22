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
EXPORT_STL: bool = False                # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False               # Save .step to repo-root exports/ (default: False)


@dataclass
class CoreParams:
    """Primary rack unit and L-bracket structural dimensions."""

    u_count: int = param(
        2,
        label="Rack Units",
        desc="Number of rack units (1U, 2U, 3U, ...)",
        unit="U", min=1, max=6, step=1,
    )
    u_height_unit: float = param(
        44.45,
        label="1U Height",
        desc="Nominal 1U pitch (1.75 in)",
        unit="mm",
    )
    height_margin: float = param(
        1.2,
        desc="Subtracted clearance for clean rack stacking",
        unit="mm", min=0.0, max=4.0, step=0.1,
    )
    bracket_length: float = param(
        150.0,
        desc="Side plate depth along rack",
        unit="mm", min=40.0, max=300.0, step=5.0,
    )
    front_flange_width: float = param(
        20.0,
        desc="Front mounting ear width",
        unit="mm", min=15.0, max=40.0, step=1.0,
    )
    thickness: float = param(
        3.0,
        desc="Bracket wall thickness",
        unit="mm", min=1.5, max=8.0, step=0.5,
    )
    inner_bend_radius: float = param(
        1.5,
        desc="Inside L-corner fillet radius",
        unit="mm", min=0.0, max=5.0, step=0.5,
    )
    outer_corner_radius: float = param(
        1.5,
        desc="Outer vertical corner fillet radius",
        unit="mm", min=0.0, max=5.0, step=0.5,
    )


@dataclass
class SideHolesParams:
    """Side M4 thread-in pilot hole array."""

    enabled: bool = param(
        True,
        desc="Cut side M4 pilot hole array",
    )
    diameter: float = param(
        3.3,
        desc="M4 thread-in pilot hole diameter",
        unit="mm", min=2.0, max=6.0, step=0.1,
    )
    spacing_x: float = param(
        25.0,
        label="Column Spacing (X)",
        desc="Horizontal spacing between hole columns",
        unit="mm", min=10.0, max=60.0, step=1.0,
    )
    rear_offset: float = param(
        15.0,
        desc="Offset from rear edge to first column",
        unit="mm", min=5.0, max=40.0, step=1.0,
    )
    min_front_clearance: float = param(
        10.0,
        desc="Minimum clearance before front bend",
        unit="mm", min=5.0, max=30.0, step=1.0,
    )
    edge_offset: float = param(
        9.7,
        desc="Offset from top/bottom edges to outer rows",
        unit="mm", min=5.0, max=20.0, step=0.5,
    )
    include_intermediate: bool = param(
        False,
        desc="Add hole rows at intermediate U centers",
        when={"cutout.style": "none"},
    )
    rows: Optional[List[float]] = param(
        None,
        desc="Explicit Z heights for side hole rows (Auto = calculated)",
        item_label="Row",
        unit="mm", step=0.5,
    )


@dataclass
class CutoutParams:
    """Center cutout window options (snapped to hex cell centers)."""

    style: Literal["hex", "window", "none"] = param(
        "hex",
        desc="Ventilation cutout style",
    )
    margin_z: float = param(
        15.7,
        label="Z Margin",
        desc="Solid margin reserved at top & bottom",
        unit="mm", min=6.0, max=30.0, step=0.5, when={"style": ["hex", "window"]},
    )
    corner_radius: float = param(
        1.0,
        desc="Corner radius of cutout window",
        unit="mm", min=0.0, max=10.0, step=0.5, when={"style": ["hex", "window"]},
    )
    hex_pitch_count: int = param(
        11,
        desc="Horizontal hex pitches to snap window width",
        min=1, max=25, step=1, when={"style": ["hex", "window"]},
    )
    hex_radius: float = param(
        4.5,
        desc="Circumradius of hex cutouts",
        unit="mm", min=2.0, max=12.0, step=0.5, when={"style": "hex"},
    )
    hex_wall_thickness: float = param(
        1.5,
        desc="Wall thickness between hex flats",
        unit="mm", min=0.8, max=5.0, step=0.1, when={"style": "hex"},
    )


@dataclass
class RackSlotsParams:
    """Front EIA-310 rack mounting slots."""

    width: float = param(
        9.5,
        desc="Mounting slot width",
        unit="mm", min=5.0, max=15.0, step=0.5,
    )
    height: float = param(
        6.5,
        desc="Mounting slot height",
        unit="mm", min=4.0, max=10.0, step=0.5,
    )
    x_center: float = param(
        10.0,
        label="Slot X Center",
        desc="Center position on front flange",
        unit="mm", min=5.0, max=25.0, step=0.5,
    )
    offset_end: float = param(
        5.75,
        desc="EIA-310 offset from outer edge to slot center",
        unit="mm", min=3.0, max=12.0, step=0.25,
    )
    single_slot_1u: bool = param(
        False,
        label="Single Slot (1U)",
        desc="Center 1 slot for 1U instead of 2 EIA-310 end slots",
        when={"core.u_count": 1},
    )
    z_positions: Optional[List[float]] = param(
        None,
        label="Z Positions",
        desc="Explicit Z heights for rack slots (Auto = EIA-310)",
        item_label="Slot Z",
        unit="mm", step=0.5,
    )


@default_preset("2U Hex Bracket", desc="2U 19-inch rackmount L-bracket with honeycomb ventilation")
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


def _clip_poly_axis(
    poly: list[tuple[float, float]],
    is_inside,
    intersect_edge,
) -> list[tuple[float, float]]:
    """Sutherland-Hodgman clip of a 2D polygon against a single half-plane."""
    if not poly:
        return []
    out: list[tuple[float, float]] = []
    prev = poly[-1]
    prev_in = is_inside(prev)
    for curr in poly:
        curr_in = is_inside(curr)
        if curr_in:
            if not prev_in:
                out.append(intersect_edge(prev, curr))
            out.append(curr)
        elif prev_in:
            out.append(intersect_edge(prev, curr))
        prev = curr
        prev_in = curr_in
    return out


def _clip_poly_rect(
    poly: list[tuple[float, float]],
    x_min: float,
    x_max: float,
    z_min: float,
    z_max: float,
) -> list[tuple[float, float]]:
    """Exact clip of a 2D convex polygon against [x_min, x_max] x [z_min, z_max]."""
    p = _clip_poly_axis(
        poly,
        lambda pt: pt[0] >= x_min,
        lambda a, b: (x_min, a[1] + (b[1] - a[1]) * (x_min - a[0]) / (b[0] - a[0])),
    )
    p = _clip_poly_axis(
        p,
        lambda pt: pt[0] <= x_max,
        lambda a, b: (x_max, a[1] + (b[1] - a[1]) * (x_max - a[0]) / (b[0] - a[0])),
    )
    p = _clip_poly_axis(
        p,
        lambda pt: pt[1] >= z_min,
        lambda a, b: (a[0] + (b[0] - a[0]) * (z_min - a[1]) / (b[1] - a[1]), z_min),
    )
    p = _clip_poly_axis(
        p,
        lambda pt: pt[1] <= z_max,
        lambda a, b: (a[0] + (b[0] - a[0]) * (z_max - a[1]) / (b[1] - a[1]), z_max),
    )
    cleaned: list[tuple[float, float]] = []
    for pt in p:
        if not cleaned or math.hypot(pt[0] - cleaned[-1][0], pt[1] - cleaned[-1][1]) > 1e-6:
            cleaned.append(pt)
    if len(cleaned) > 1 and math.hypot(cleaned[0][0] - cleaned[-1][0], cleaned[0][1] - cleaned[-1][1]) <= 1e-6:
        cleaned.pop()
    return cleaned


def _poly_area(poly: list[tuple[float, float]]) -> float:
    """Compute unsigned area of a 2D polygon via the shoelace formula."""
    area = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def _build_hex_wires(
    window_center_x: float,
    window_center_z: float,
    window_width: float,
    window_height: float,
    corner_radius: float,
    hex_radius: float,
    hex_wall_thickness: float,
) -> list[Wire]:
    """Build exact clipped honeycomb wires on Y=0 (Plane.XZ) without quadratic 2D booleans."""
    flat_to_flat = math.sqrt(3) * hex_radius
    pitch_x = flat_to_flat + hex_wall_thickness
    pitch_z = 1.5 * hex_radius + hex_wall_thickness * (math.sqrt(3) / 2.0)

    half_w = window_width / 2.0
    half_h = window_height / 2.0
    half_w_grid = half_w + pitch_x
    half_h_grid = half_h + pitch_z

    angles = [math.radians(30 + 60 * i) for i in range(6)]
    hex_offsets = [(hex_radius * math.cos(a), hex_radius * math.sin(a)) for a in angles]
    hex_half_x = flat_to_flat / 2.0
    hex_half_z = hex_radius

    x_min = window_center_x - half_w
    x_max = window_center_x + half_w
    z_min = window_center_z - half_h
    z_max = window_center_z + half_h
    cr = max(0.0, min(corner_radius, half_w, half_h))

    wires: list[Wire] = []
    corner_hex_2d: list[list[tuple[float, float]]] = []

    z_row = 0
    z_pos = -half_h_grid
    while z_pos <= half_h_grid:
        x_offset = (pitch_x / 2.0) if (z_row % 2 == 1) else 0.0
        x_pos = -half_w_grid + x_offset
        hz = window_center_z + z_pos
        while x_pos <= half_w_grid:
            hx = window_center_x + x_pos
            if (
                hx + hex_half_x <= x_min + 1e-6
                or hx - hex_half_x >= x_max - 1e-6
                or hz + hex_half_z <= z_min + 1e-6
                or hz - hex_half_z >= z_max - 1e-6
            ):
                x_pos += pitch_x
                continue

            poly = [(hx + dx, hz + dz) for dx, dz in hex_offsets]

            # Hexes overlapping a rounded corner square use exact OCCT face intersection;
            # all interior and straight-edge hexes clip directly in pure Python.
            touches_corner = False
            if cr > 0:
                near_x = (hx - hex_half_x < x_min + cr) or (hx + hex_half_x > x_max - cr)
                near_z = (hz - hex_half_z < z_min + cr) or (hz + hex_half_z > z_max - cr)
                touches_corner = near_x and near_z

            if touches_corner:
                corner_hex_2d.append(poly)
            else:
                clipped = _clip_poly_rect(poly, x_min, x_max, z_min, z_max)
                if len(clipped) >= 3 and _poly_area(clipped) > 1e-4:
                    wires.append(Wire.make_polygon([(px, 0.0, pz) for px, pz in clipped]))

            x_pos += pitch_x
        z_pos += pitch_z
        z_row += 1

    if corner_hex_2d:
        with BuildSketch() as win_sk:
            with Locations((window_center_x, window_center_z)):
                RectangleRounded(window_width, window_height, radius=cr)
        win_face_xy = win_sk.face()
        for poly in corner_hex_2d:
            hf_xy = Face(Wire.make_polygon([(px, pz, 0.0) for px, pz in poly]))
            res = hf_xy.intersect(win_face_xy)
            if res is not None:
                for f in res.faces():
                    if f.area > 1e-4:
                        wires.append(Plane.XZ.from_local_coords(f.outer_wire()))

    return wires


def _build_l_profile_solid(
    core: CoreParams,
    x_end: float,
    total_height: float,
) -> Solid:
    """Extrude the L-bracket base profile from X=0 to X=x_end."""
    with BuildSketch(Plane.XY) as profile:
        with BuildLine():
            Polyline(
                (0, 0),
                (x_end, 0),
                (x_end, core.thickness),
                (core.thickness, core.thickness),
                (core.thickness, core.front_flange_width),
                (0, core.front_flange_width),
                (0, 0),
            )
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

    return extrude(profile.face(), amount=total_height)


def create_rack_bracket(params: RackBracketParams) -> Part:
    """Generates a parametric 19-inch rackmount L-bracket solid body."""
    core = params.core
    side = params.side_holes
    cutout = params.cutout
    slots = params.rack_slots
    total_height = params.total_height

    # 1. Front Flange EIA-310 Mounting Slot Z Positions (Scales with u_count)
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

    # 2. Center Window Cutout Wires (Honeycomb grill or open window on Y=0)
    flat_to_flat = math.sqrt(3) * cutout.hex_radius
    pitch_x = flat_to_flat + cutout.hex_wall_thickness

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

    cutout_wires: list[Wire] = []
    has_cutout = window_width > 15.0 and window_height > 15.0 and cutout.style.lower() != "none"
    if has_cutout:
        if cutout.style.lower() == "hex":
            cutout_wires = _build_hex_wires(
                window_center_x,
                window_center_z,
                window_width,
                window_height,
                cutout.corner_radius,
                cutout.hex_radius,
                cutout.hex_wall_thickness,
            )
        elif cutout.style.lower() == "window":
            with BuildSketch() as win_sk:
                with Locations((window_center_x, window_center_z)):
                    if cutout.corner_radius > 0:
                        RectangleRounded(window_width, window_height, radius=cutout.corner_radius)
                    else:
                        Rectangle(window_width, window_height)
            cutout_wires = [Plane.XZ.from_local_coords(win_sk.face().outer_wire())]

    # 3. Dynamic Side Plate Mounting Hole Wires (Scales automatically with u_count)
    x_columns: list[float] = []
    z_positions: list[float] = []
    side_hole_wires: list[Wire] = []
    if side.enabled and side.diameter > 0:
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

        hole_radius = side.diameter / 2.0
        for h_x in x_columns:
            for h_z in z_positions:
                circle_edge = Edge.make_circle(
                    hole_radius,
                    plane=Plane(origin=(h_x, 0.0, h_z), x_dir=(1, 0, 0), z_dir=(0, -1, 0)),
                )
                side_hole_wires.append(Wire([circle_edge]))

    # 4. Decide whether all side plate perforations can be extruded directly as a single
    #    planar Face(outer, inner_wires) (avoids costly 3D boolean cuts on 100+ faces).
    all_inner_wires = cutout_wires + side_hole_wires
    seam_x0 = core.thickness + core.inner_bend_radius + 0.5
    can_use_fast_slab = len(all_inner_wires) > 0 and seam_x0 < core.bracket_length - 1.0

    if can_use_fast_slab and side_hole_wires:
        hole_r = side.diameter / 2.0
        # Ensure side holes don't overlap each other
        sorted_x = sorted(x_columns)
        sorted_z = sorted(z_positions)
        if any(sorted_x[i + 1] - sorted_x[i] <= side.diameter + 0.1 for i in range(len(sorted_x) - 1)):
            can_use_fast_slab = False
        if any(sorted_z[i + 1] - sorted_z[i] <= side.diameter + 0.1 for i in range(len(sorted_z) - 1)):
            can_use_fast_slab = False
        # Ensure side holes don't overlap the cutout window
        if can_use_fast_slab and cutout_wires:
            win_x0 = window_center_x - window_width / 2.0
            win_x1 = window_center_x + window_width / 2.0
            win_z0 = window_center_z - window_height / 2.0
            win_z1 = window_center_z + window_height / 2.0
            for h_x in x_columns:
                for h_z in z_positions:
                    in_wx = (h_x + hole_r > win_x0 - 0.05) and (h_x - hole_r < win_x1 + 0.05)
                    in_wz = (h_z + hole_r > win_z0 - 0.05) and (h_z - hole_r < win_z1 + 0.05)
                    if in_wx and in_wz:
                        can_use_fast_slab = False
                        break
                if not can_use_fast_slab:
                    break

    if can_use_fast_slab:
        for w in all_inner_wires:
            bb = w.bounding_box()
            if (
                bb.min.X <= seam_x0 + 0.1
                or bb.max.X >= core.bracket_length - 0.1
                or bb.min.Z <= 0.1
                or bb.max.Z >= total_height - 0.1
            ):
                can_use_fast_slab = False
                break

    if can_use_fast_slab:
        # Fast path: extrude perforated side slab in one shot and fuse with front L-bend
        front_solid = _build_l_profile_solid(core, seam_x0, total_height)
        if slot_z_positions:
            with BuildSketch(Plane.YZ) as slots_sk:
                with Locations([(slots.x_center, z_pos) for z_pos in slot_z_positions]):
                    SlotOverall(slots.width, slots.height, rotation=0)
            if len(slots_sk.faces()) > 0:
                slot_cut = extrude(slots_sk.sketch, amount=core.thickness * 4, dir=(1, 0, 0))
                front_solid = front_solid - slot_cut

        slab_outer = Wire.make_polygon(
            [
                (seam_x0, 0.0, 0.0),
                (core.bracket_length, 0.0, 0.0),
                (core.bracket_length, 0.0, total_height),
                (seam_x0, 0.0, total_height),
            ]
        )
        slab_face = Face(slab_outer, inner_wires=all_inner_wires)
        slab_solid = extrude(slab_face, amount=core.thickness, dir=(0, 1, 0))

        fused = front_solid.fuse(slab_solid)
        return Part(children=[fused])

    # General fallback path (no side holes/cutouts, or overlapping/edge-clipping user parameters)
    bracket_solid = _build_l_profile_solid(core, core.bracket_length, total_height)
    if slot_z_positions:
        with BuildSketch(Plane.YZ) as slots_sk:
            with Locations([(slots.x_center, z_pos) for z_pos in slot_z_positions]):
                SlotOverall(slots.width, slots.height, rotation=0)
        if len(slots_sk.faces()) > 0:
            slot_cut = extrude(slots_sk.sketch, amount=core.thickness * 4, dir=(1, 0, 0))
            bracket_solid = bracket_solid - slot_cut

    if cutout_wires:
        cut_solids = [extrude(Face(w), amount=core.thickness * 4, dir=(0, 1, 0)) for w in cutout_wires]
        bracket_solid = bracket_solid - Compound(children=cut_solids)

    if side_hole_wires:
        hole_solids = [extrude(Face(w), amount=core.thickness * 4, dir=(0, 1, 0)) for w in side_hole_wires]
        bracket_solid = bracket_solid - Compound(children=hole_solids)

    return Part(children=[bracket_solid])


def export_filename(params: RackBracketParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    style = "solid" if params.cutout.style.lower() == "none" else params.cutout.style.lower()
    return f"rack_bracket_{params.core.u_count}u_{style}"


if __name__ == "__main__":
    from utils.runner import run_model

    params = RackBracketParams()
    bracket = create_rack_bracket(params)
    run_model(bracket, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
