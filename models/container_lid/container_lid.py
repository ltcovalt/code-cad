"""
Parametric Container Lid Generator (build123d) [DRAFT / WIP]

NOTE: This model is currently in DRAFT / WORK-IN-PROGRESS status.

Generates replacement lids for round and rectangular containers (e.g., Pyrex glass bowls
and baking dishes). Supports flexible materials (TPU) with continuous stretch-fit retention beads,
as well as rigid food-safe materials (PCTG / PETG) featuring compliant cantilever flexure slots.

Features:
- Shapes: Round, Rectangular, and Square containers
- Under-lip snap-fit retention bead (airtight stretch seal for TPU, snap clips for PCTG)
- Inner seal plug ring (prevents liquid slosh and leakage)
- Stacking nesting rim on top surface
- Ergonomic pull tab (corner tab on rectangular lids, edge tab on round lids)
  with non-slip grip ridges and hanging/drying peg hole
- Built-in verified presets for popular Pyrex container sizes
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict
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
class ContainerLidParams:
    """Parameters for container lid generation."""

    # Material & Primary Fit Mode
    material: str = "tpu"               # "tpu" (flexible stretch) or "pctg" / "petg" / "rigid" (compliant flex slots)
    shape: str = "round"                # "round" or "rectangular" (square is handled as rectangular with equal length/width)
    rim_style: str = "beaded"           # "beaded" (container has outward rim lip/ring) or "smooth" (straight glass wall)
    friction_ribs: bool = False         # If True, adds wiper gasket ribs for high friction/vacuum grip on smooth glass

    # Container Rim Dimensions (Measured at widest point of glass rim lip)
    diameter: float = 150.0             # Round: outer diameter of rim lip in mm (e.g. Pyrex 4-cup = ~150 mm)
    length: float = 182.0               # Rectangular: outer length of rim lip in mm (e.g. Pyrex 3-cup = ~182 mm)
    width: float = 132.0                # Rectangular: outer width of rim lip in mm (e.g. Pyrex 3-cup = ~132 mm)
    corner_radius: float = 20.0         # Rectangular: corner radius of the glass dish in mm

    # Convenience inch inputs (if provided, overrides mm values automatically)
    diameter_in: Optional[float] = None # Round: diameter in inches (e.g. 5.9 for ~150 mm)
    length_in: Optional[float] = None   # Rectangular: length in inches (e.g. 7.16 for ~182 mm)
    width_in: Optional[float] = None    # Rectangular: width in inches (e.g. 5.2 for ~132 mm)

    # Test Print / Gauge Ring Mode
    test_ring: bool = False             # If True, hollows out center to print an 8-minute fit-check test ring

    # Container Lip Profile
    rim_lip_height: float = 5.0         # Vertical height/thickness of the glass rim bead in mm
    glass_wall_thickness: float = 4.0   # Thickness of glass at the container rim in mm

    # Fit Clearance / Tolerance
    fit_tolerance: Optional[float] = None  # mm added to container dimension. None = auto (-0.2 for TPU stretch, +0.2 for PCTG)

    # Lid Structure & Walls
    top_thickness: float = 1.8          # Thickness of the solid top plate in mm (4-6 perimeters for watertightness)
    skirt_height: float = 10.0          # Total vertical depth of outer downward skirt in mm
    skirt_wall_thickness: float = 1.8   # Thickness of the outer side skirt wall in mm
    outer_fillet: float = 1.2           # Fillet/chamfer radius on top exterior perimeter edge in mm
    lead_in_chamfer: float = 0.8        # Chamfer on inside bottom rim of skirt for smooth mounting

    # Retention Snap Bead
    snap_ridge: bool = True             # Inward protruding ridge that locks under container glass bead
    retention_bead_depth: Optional[float] = None  # Inward protrusion (None = auto: 0.8mm for TPU, 0.35mm for PCTG)
    retention_bead_height: float = 1.5  # Vertical height of the retention bead profile in mm
    retention_bead_offset: Optional[float] = None # Distance from underside to top of bead (None = rim_lip_height + 0.2mm)

    # Inner Seal Plug Ring (Prevents liquid sloshing into rim gap)
    inner_seal_ring: bool = True        # Downward tongue sitting just inside container wall
    inner_seal_height: float = 3.5      # Downward depth of seal ring in mm
    inner_seal_thickness: float = 1.2   # Thickness of the seal ring wall in mm
    inner_seal_clearance: float = 0.6   # Radial gap between glass inner wall and seal ring in mm

    # Stacking Nesting Rim
    stacking_rim: bool = True           # Raised rim on top surface to nest stacked containers
    stacking_rim_height: float = 1.5    # Height of stacking rim in mm
    stacking_rim_thickness: float = 1.5 # Wall thickness of stacking rim in mm
    stacking_rim_inset: float = 4.0     # Inward distance from lid edge to stacking rim in mm

    # Ergonomic Pull Tab
    pull_tab: bool = True               # Outer peel tab for effortless lid removal
    tab_location: str = "auto"          # "auto" (corner for rect, edge for round), "corner", or "edge"
    tab_length: float = 8.5             # Compact protrusion length beyond skirt in mm (default 8.5 mm)
    tab_width: float = 22.0             # Width of the tab in mm
    tab_root_overlap: float = 6.0       # Deep root overlap into top plate/skirt in mm (prevents tear-off)
    tab_gusset_depth: float = 2.5       # Depth of under-tab structural gusset down the skirt wall in mm
    tab_thickness: float = 2.0          # Thickness of the tab plate in mm
    tab_grip_ribs: bool = True          # Raised non-slip traction ribs on tab surface
    tab_hanging_hole: bool = False      # Pegboard / dish-rack drying hole (default False for compact tabs)
    tab_hole_diameter: float = 4.0      # Diameter of hanging hole in mm (if enabled)

    # Rigid Flexure Relief Slots (for PCTG / PETG / Rigid Plastics)
    flex_slots: Optional[bool] = None   # None = auto (True if material is pctg/petg/rigid, False for tpu)
    slot_width: float = 1.5             # Width of vertical cutouts through skirt in mm
    round_slot_count: int = 6           # Number of relief slots around round circumference
    rect_slots_long_side: int = 2       # Number of relief slots along each long side
    rect_slots_short_side: int = 1      # Number of relief slots along each short side

    def get_effective_params(self) -> "ContainerLidParams":
        """Return a copy of params with auto-resolved defaults based on active material, rim style, and units."""
        is_rigid = self.material.lower() in ("pctg", "petg", "rigid", "pla")
        is_smooth = self.rim_style.lower() in ("smooth", "straight", "flat", "no_rim", "no_lip")
        p = ContainerLidParams(**self.__dict__)

        # Convert inch measurements to mm if provided
        if p.diameter_in is not None:
            p.diameter = p.diameter_in * 25.4
        if p.length_in is not None:
            p.length = p.length_in * 25.4
        if p.width_in is not None:
            p.width = p.width_in * 25.4

        # For smooth containers, disable undercut snap bead and enable tighter friction fit
        if is_smooth:
            p.snap_ridge = False
            # Default friction ribs to True for smooth containers unless explicitly set to False
            if not self.__dict__.get("friction_ribs", False):
                p.friction_ribs = True

        if p.fit_tolerance is None:
            if is_smooth:
                p.fit_tolerance = 0.1 if is_rigid else -0.35
            else:
                p.fit_tolerance = 0.2 if is_rigid else -0.2

        if p.retention_bead_depth is None:
            p.retention_bead_depth = 0.35 if is_rigid else 0.8
        if p.retention_bead_offset is None:
            p.retention_bead_offset = p.rim_lip_height + 0.2
        if p.flex_slots is None:
            p.flex_slots = is_rigid and not is_smooth
        return p


# Verified Presets for Popular Pyrex Food Storage Containers
PYREX_PRESETS: Dict[str, ContainerLidParams] = {
    "pyrex_round_1_cup": ContainerLidParams(
        shape="round",
        diameter=98.0,
        rim_lip_height=4.5,
        glass_wall_thickness=3.8,
        skirt_height=9.0,
    ),
    "pyrex_round_2_cup": ContainerLidParams(
        shape="round",
        diameter=120.0,
        rim_lip_height=5.0,
        glass_wall_thickness=4.0,
        skirt_height=10.0,
    ),
    "pyrex_round_4_cup": ContainerLidParams(
        shape="round",
        diameter=150.0,
        rim_lip_height=5.2,
        glass_wall_thickness=4.2,
        skirt_height=10.5,
    ),
    "pyrex_round_7_cup": ContainerLidParams(
        shape="round",
        diameter=185.0,
        rim_lip_height=5.5,
        glass_wall_thickness=4.5,
        skirt_height=11.5,
    ),
    "pyrex_rect_3_cup": ContainerLidParams(
        shape="rectangular",
        length=182.0,
        width=132.0,
        corner_radius=20.0,
        rim_lip_height=5.0,
        glass_wall_thickness=4.0,
        skirt_height=10.0,
    ),
    "pyrex_rect_6_cup": ContainerLidParams(
        shape="rectangular",
        length=225.0,
        width=175.0,
        corner_radius=25.0,
        rim_lip_height=5.5,
        glass_wall_thickness=4.5,
        skirt_height=11.0,
    ),
    "pyrex_rect_11_cup": ContainerLidParams(
        shape="rectangular",
        length=280.0,
        width=200.0,
        corner_radius=30.0,
        rim_lip_height=6.0,
        glass_wall_thickness=5.0,
        skirt_height=12.0,
    ),
}

# Verified Presets for Anchor Hocking (TrueSeal / SnugFit) Food Storage Containers
ANCHOR_PRESETS: Dict[str, ContainerLidParams] = {
    "anchor_round_1_cup": ContainerLidParams(
        shape="round",
        diameter=96.0,
        rim_lip_height=4.5,
        glass_wall_thickness=3.8,
        skirt_height=9.0,
    ),
    "anchor_round_2_cup": ContainerLidParams(
        shape="round",
        diameter=122.0,
        rim_lip_height=4.8,
        glass_wall_thickness=4.0,
        skirt_height=10.0,
    ),
    "anchor_round_4_cup": ContainerLidParams(
        shape="round",
        diameter=152.0,
        rim_lip_height=5.2,
        glass_wall_thickness=4.2,
        skirt_height=10.5,
    ),
    "anchor_round_7_cup": ContainerLidParams(
        shape="round",
        diameter=186.0,
        rim_lip_height=5.5,
        glass_wall_thickness=4.5,
        skirt_height=11.5,
    ),
    "anchor_rect_4_75_cup": ContainerLidParams(
        shape="rectangular",
        length=195.0,
        width=148.0,
        corner_radius=22.0,
        rim_lip_height=5.2,
        glass_wall_thickness=4.2,
        skirt_height=10.5,
    ),
}

# Combined dictionary of all container presets
CONTAINER_PRESETS: Dict[str, ContainerLidParams] = {**PYREX_PRESETS, **ANCHOR_PRESETS}


def build_round_lid(p: ContainerLidParams) -> Solid:
    """Build a round container lid using build123d."""
    r_inner = (p.diameter + p.fit_tolerance) / 2.0
    r_outer = r_inner + p.skirt_wall_thickness

    # Inner seal ring radii
    r_seal_outer = r_inner - p.glass_wall_thickness - p.inner_seal_clearance
    r_seal_inner = r_seal_outer - p.inner_seal_thickness
    has_seal = p.inner_seal_ring and (r_seal_inner > 2.0)

    # Stacking rim radii
    r_stack_outer = r_outer - p.stacking_rim_inset
    r_stack_inner = r_stack_outer - p.stacking_rim_thickness
    has_stack = p.stacking_rim and (r_stack_inner > 2.0)

    # 1. Generate 2D revolved cross-section polygon on Plane.XZ
    pts = [(0.0, 0.0)]

    # Underside to inner seal ring
    if has_seal:
        pts.extend([
            (r_seal_inner, 0.0),
            (r_seal_inner, -p.inner_seal_height + 0.5),
            (r_seal_inner + 0.5, -p.inner_seal_height),
            (r_seal_outer - 0.5, -p.inner_seal_height),
            (r_seal_outer, -p.inner_seal_height + 0.5),
            (r_seal_outer, 0.0),
        ])

    pts.append((r_inner, 0.0))

    # Inner skirt wall & retention bead or friction wiper ribs
    if p.snap_ridge and p.retention_bead_depth > 0:
        pts.extend([
            (r_inner, -p.retention_bead_offset),
            (r_inner - p.retention_bead_depth, -p.retention_bead_offset - 0.3),
            (r_inner - p.retention_bead_depth, -p.retention_bead_offset - p.retention_bead_height + 0.6),
            (r_inner, -p.retention_bead_offset - p.retention_bead_height),
        ])
    elif p.friction_ribs:
        # Dual wiper gasket ribs for smooth-walled glass containers
        for z_rib in [-3.0, -6.5]:
            if abs(z_rib) + 0.6 < p.skirt_height - p.lead_in_chamfer:
                pts.extend([
                    (r_inner, z_rib + 0.5),
                    (r_inner - 0.3, z_rib),
                    (r_inner, z_rib - 0.5),
                ])

    # Bottom lead-in chamfer
    pts.extend([
        (r_inner, -p.skirt_height + p.lead_in_chamfer),
        (r_inner + p.lead_in_chamfer, -p.skirt_height),
        (r_outer, -p.skirt_height),
    ])

    # Outer wall up to top deck with outer fillet
    if p.outer_fillet > 0:
        pts.extend([
            (r_outer, p.top_thickness - p.outer_fillet),
            (r_outer - p.outer_fillet, p.top_thickness),
        ])
    else:
        pts.append((r_outer, p.top_thickness))

    # Stacking rim
    if has_stack:
        pts.extend([
            (r_stack_outer, p.top_thickness),
            (r_stack_outer, p.top_thickness + p.stacking_rim_height),
            (r_stack_inner, p.top_thickness + p.stacking_rim_height),
            (r_stack_inner, p.top_thickness),
        ])

    # Close at center top surface
    pts.extend([
        (0.0, p.top_thickness),
        (0.0, 0.0),
    ])

    with BuildPart() as round_part:
        with BuildSketch(Plane.XZ):
            Polygon(pts)
        revolve(axis=Axis.Z)

        # 2. Add Pull Tab (Structurally rooted into top deck and skirt with under-tab gusset)
        if p.pull_tab:
            tab_total_len = p.tab_length + p.tab_root_overlap
            tab_center_x = (r_outer - p.tab_root_overlap) + tab_total_len / 2.0

            # Main tab plate (fused with top deck)
            with BuildSketch(Plane.XY):
                with Locations((tab_center_x, 0)):
                    RectangleRounded(tab_total_len, p.tab_width, radius=4.0)
                if p.tab_hanging_hole:
                    with Locations((r_outer + p.tab_length - (p.tab_hole_diameter / 2.0 + 2.0), 0)):
                        Circle(radius=p.tab_hole_diameter / 2.0, mode=Mode.SUBTRACT)
            extrude(amount=p.top_thickness, mode=Mode.ADD)

            # Structural under-tab gusset reaching down the skirt wall
            if p.tab_gusset_depth > 0:
                with BuildSketch(Plane.XY.offset(-p.tab_gusset_depth)):
                    with Locations(((r_outer - p.tab_root_overlap) + (p.tab_root_overlap + p.tab_length * 0.4) / 2.0, 0)):
                        RectangleRounded(p.tab_root_overlap + p.tab_length * 0.4, p.tab_width * 0.75, radius=3.0)
                with BuildSketch(Plane.XY):
                    with Locations(((r_outer - p.tab_root_overlap) + (p.tab_root_overlap + p.tab_length * 0.8) / 2.0, 0)):
                        RectangleRounded(p.tab_root_overlap + p.tab_length * 0.8, p.tab_width, radius=3.5)
                loft(ruled=True, mode=Mode.ADD)

            # Compact traction grip ridges on pull tab
            if p.tab_grip_ribs:
                for i in range(3):
                    rib_x = r_outer + 2.0 + i * 2.2
                    if rib_x + 0.8 < (r_outer + p.tab_length - 1.0):
                        with BuildSketch(Plane.XY.offset(p.top_thickness)):
                            with Locations((rib_x, 0)):
                                RectangleRounded(1.0, p.tab_width - 8.0, radius=0.4)
                        extrude(amount=0.6, mode=Mode.ADD)

        # 3. Flexure Relief Slots (for rigid plastics)
        if p.flex_slots and p.round_slot_count > 0:
            slot_h = p.skirt_height - 1.5
            slot_root_r = p.slot_width
            for i in range(p.round_slot_count):
                ang = i * (360.0 / p.round_slot_count)
                # Keep pull tab clean: skip slot if near tab (angle near 0)
                if p.pull_tab and (ang < 25.0 or ang > 335.0):
                    continue
                rot = Rotation(0, 0, ang)
                with Locations(rot):
                    with Locations((r_outer, 0, -p.skirt_height + slot_h / 2.0)):
                        Box(p.skirt_wall_thickness * 4, p.slot_width, slot_h, mode=Mode.SUBTRACT)
                    with Locations((r_outer, 0, -p.skirt_height + slot_h)):
                        Cylinder(radius=slot_root_r, height=p.skirt_wall_thickness * 4, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        # 4. Test Ring Gauge Mode: hollow out center to save filament and test fit fast
        if p.test_ring:
            gauge_inner_r = max(5.0, (r_seal_inner - 2.0) if has_seal else (r_inner - 6.0))
            with BuildSketch(Plane.XY):
                Circle(radius=gauge_inner_r)
            extrude(amount=p.top_thickness * 4, both=True, mode=Mode.SUBTRACT)

    assert round_part.part is not None, "Failed to generate round lid"
    return round_part.part


def build_rectangular_lid(p: ContainerLidParams) -> Solid:
    """Build a rectangular or square container lid using build123d."""
    l_inner = p.length + p.fit_tolerance
    w_inner = p.width + p.fit_tolerance
    r_inner = max(2.0, p.corner_radius + p.fit_tolerance / 2.0)

    l_outer = l_inner + 2 * p.skirt_wall_thickness
    w_outer = w_inner + 2 * p.skirt_wall_thickness
    r_outer = r_inner + p.skirt_wall_thickness

    with BuildPart() as rect_part:
        # 1. Main outer body block (top deck + downward skirt)
        with BuildSketch(Plane.XY):
            RectangleRounded(l_outer, w_outer, radius=r_outer)
        extrude(amount=p.top_thickness, mode=Mode.ADD)
        with BuildSketch(Plane.XY):
            RectangleRounded(l_outer, w_outer, radius=r_outer)
        extrude(amount=-p.skirt_height, mode=Mode.ADD)

        # Outer fillet on top perimeter edge
        if p.outer_fillet > 0:
            top_edges = rect_part.edges().filter_by(Axis.Z, reverse=True)
            # Find the top outer perimeter edges
            outer_top_edges = [e for e in rect_part.edges() if abs(e.center().Z - p.top_thickness) < 1e-3]
            if outer_top_edges:
                fillet(outer_top_edges, radius=min(p.outer_fillet, p.skirt_wall_thickness * 0.7))

        # 2. Main cavity cutout
        with BuildSketch(Plane.XY):
            RectangleRounded(l_inner, w_inner, radius=r_inner)
        extrude(amount=-p.skirt_height, mode=Mode.SUBTRACT)

        # Bottom inside lead-in chamfer
        if p.lead_in_chamfer > 0:
            with BuildSketch(Plane.XY.offset(-p.skirt_height)):
                RectangleRounded(l_inner + 2 * p.lead_in_chamfer, w_inner + 2 * p.lead_in_chamfer, radius=r_inner + p.lead_in_chamfer)
                RectangleRounded(l_inner, w_inner, radius=r_inner, mode=Mode.SUBTRACT)
            extrude(amount=p.lead_in_chamfer, mode=Mode.SUBTRACT)

        # 3. Retention Snap Bead or Friction Wiper Ribs
        if p.snap_ridge and p.retention_bead_depth > 0:
            l_bead = l_inner - 2 * p.retention_bead_depth
            w_bead = w_inner - 2 * p.retention_bead_depth
            r_bead = max(1.0, r_inner - p.retention_bead_depth)

            bead_flat_height = p.retention_bead_height * 0.4
            # Flat bead upper section
            with BuildSketch(Plane.XY.offset(-p.retention_bead_offset)):
                RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                RectangleRounded(l_bead, w_bead, radius=r_bead, mode=Mode.SUBTRACT)
            extrude(amount=-bead_flat_height, mode=Mode.ADD)

            # Chamfered lead-in lower section (loft)
            with BuildSketch(Plane.XY.offset(-p.retention_bead_offset - bead_flat_height)) as s1:
                RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                RectangleRounded(l_bead, w_bead, radius=r_bead, mode=Mode.SUBTRACT)
            with BuildSketch(Plane.XY.offset(-p.retention_bead_offset - p.retention_bead_height)) as s2:
                RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                RectangleRounded(l_inner, w_inner, radius=r_inner, mode=Mode.SUBTRACT)
            loft([s1.sketch, s2.sketch], ruled=True, mode=Mode.ADD)
        elif p.friction_ribs:
            # Dual wiper gasket ribs for smooth-walled glass containers
            for z_rib in [-3.0, -6.5]:
                if abs(z_rib) + 0.6 < p.skirt_height - p.lead_in_chamfer:
                    with BuildSketch(Plane.XY.offset(z_rib - 0.4)):
                        RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                        RectangleRounded(l_inner - 0.6, w_inner - 0.6, radius=max(1.0, r_inner - 0.3), mode=Mode.SUBTRACT)
                    extrude(amount=0.8, mode=Mode.ADD)

        # 4. Inner Seal Plug Ring
        if p.inner_seal_ring:
            l_seal_out = l_inner - 2 * (p.glass_wall_thickness + p.inner_seal_clearance)
            w_seal_out = w_inner - 2 * (p.glass_wall_thickness + p.inner_seal_clearance)
            r_seal_out = max(1.0, r_inner - (p.glass_wall_thickness + p.inner_seal_clearance))
            l_seal_in = l_seal_out - 2 * p.inner_seal_thickness
            w_seal_in = w_seal_out - 2 * p.inner_seal_thickness
            r_seal_in = max(0.5, r_seal_out - p.inner_seal_thickness)

            if l_seal_in > 5.0 and w_seal_in > 5.0:
                with BuildSketch(Plane.XY):
                    RectangleRounded(l_seal_out, w_seal_out, radius=r_seal_out)
                    RectangleRounded(l_seal_in, w_seal_in, radius=r_seal_in, mode=Mode.SUBTRACT)
                extrude(amount=-p.inner_seal_height, mode=Mode.ADD)

        # 5. Stacking Rim
        if p.stacking_rim:
            l_stack_out = l_outer - 2 * p.stacking_rim_inset
            w_stack_out = w_outer - 2 * p.stacking_rim_inset
            r_stack_out = max(1.0, r_outer - p.stacking_rim_inset)
            l_stack_in = l_stack_out - 2 * p.stacking_rim_thickness
            w_stack_in = w_stack_out - 2 * p.stacking_rim_thickness
            r_stack_in = max(0.5, r_stack_out - p.stacking_rim_thickness)

            if l_stack_in > 5.0 and w_stack_in > 5.0:
                with BuildSketch(Plane.XY.offset(p.top_thickness)):
                    RectangleRounded(l_stack_out, w_stack_out, radius=r_stack_out)
                    RectangleRounded(l_stack_in, w_stack_in, radius=r_stack_in, mode=Mode.SUBTRACT)
                extrude(amount=p.stacking_rim_height, mode=Mode.ADD)

        # 6. Ergonomic Pull Tab (Default corner tab for rectangular lids)
        if p.pull_tab:
            is_corner = (p.tab_location == "corner") or (p.tab_location == "auto")
            tab_len = p.tab_length
            tab_w = p.tab_width
            tab_overlap = p.tab_root_overlap
            tab_total_len = tab_len + tab_overlap

            if is_corner:
                # Placed at top-right corner along 45 degree angle
                corner_cx = l_outer / 2.0 - r_outer
                corner_cy = w_outer / 2.0 - r_outer
                tab_loc = Location((corner_cx, corner_cy, 0), (0, 0, 45.0))
                tab_center_dist = (r_outer - tab_overlap) + tab_total_len / 2.0

                with BuildSketch(Plane.XY):
                    with Locations(tab_loc):
                        with Locations((tab_center_dist, 0)):
                            RectangleRounded(tab_total_len, tab_w, radius=4.0)
                        if p.tab_hanging_hole:
                            with Locations((r_outer + tab_len - (p.tab_hole_diameter / 2.0 + 2.0), 0)):
                                Circle(radius=p.tab_hole_diameter / 2.0, mode=Mode.SUBTRACT)
                extrude(amount=p.top_thickness, mode=Mode.ADD)

                # Structural under-tab gusset along the corner skirt
                if p.tab_gusset_depth > 0:
                    with BuildSketch(Plane.XY.offset(-p.tab_gusset_depth)):
                        with Locations(tab_loc):
                            with Locations(((r_outer - tab_overlap) + (tab_overlap + tab_len * 0.4) / 2.0, 0)):
                                RectangleRounded(tab_overlap + tab_len * 0.4, tab_w * 0.75, radius=3.0)
                    with BuildSketch(Plane.XY):
                        with Locations(tab_loc):
                            with Locations(((r_outer - tab_overlap) + (tab_overlap + tab_len * 0.8) / 2.0, 0)):
                                RectangleRounded(tab_overlap + tab_len * 0.8, tab_w, radius=3.5)
                    loft(ruled=True, mode=Mode.ADD)

                # Compact traction grip ridges on corner tab
                if p.tab_grip_ribs:
                    for i in range(3):
                        rx = r_outer + 2.0 + i * 2.2
                        if rx + 0.8 < (r_outer + tab_len - 1.0):
                            with BuildSketch(Plane.XY.offset(p.top_thickness)):
                                with Locations(tab_loc):
                                    with Locations((rx, 0)):
                                        RectangleRounded(1.0, tab_w - 8.0, radius=0.4)
                            extrude(amount=0.6, mode=Mode.ADD)
            else:
                # Placed at right edge center (+X)
                tab_center_x = (l_outer / 2.0 - tab_overlap) + tab_total_len / 2.0
                with BuildSketch(Plane.XY):
                    with Locations((tab_center_x, 0)):
                        RectangleRounded(tab_total_len, tab_w, radius=4.0)
                    if p.tab_hanging_hole:
                        with Locations((l_outer / 2.0 + tab_len - (p.tab_hole_diameter / 2.0 + 2.0), 0)):
                            Circle(radius=p.tab_hole_diameter / 2.0, mode=Mode.SUBTRACT)
                extrude(amount=p.top_thickness, mode=Mode.ADD)

                # Structural under-tab gusset along straight skirt
                if p.tab_gusset_depth > 0:
                    with BuildSketch(Plane.XY.offset(-p.tab_gusset_depth)):
                        with Locations(((l_outer / 2.0 - tab_overlap) + (tab_overlap + tab_len * 0.4) / 2.0, 0)):
                            RectangleRounded(tab_overlap + tab_len * 0.4, tab_w * 0.75, radius=3.0)
                    with BuildSketch(Plane.XY):
                        with Locations(((l_outer / 2.0 - tab_overlap) + (tab_overlap + tab_len * 0.8) / 2.0, 0)):
                            RectangleRounded(tab_overlap + tab_len * 0.8, tab_w, radius=3.5)
                    loft(ruled=True, mode=Mode.ADD)

                if p.tab_grip_ribs:
                    for i in range(3):
                        rx = l_outer / 2.0 + 2.0 + i * 2.2
                        if rx + 0.8 < (l_outer / 2.0 + tab_len - 1.0):
                            with BuildSketch(Plane.XY.offset(p.top_thickness)):
                                with Locations((rx, 0)):
                                    RectangleRounded(1.0, tab_w - 8.0, radius=0.4)
                            extrude(amount=0.6, mode=Mode.ADD)

        # 7. Rigid Flexure Relief Slots (for PCTG / PETG)
        if p.flex_slots:
            slot_h = p.skirt_height - 1.5
            slot_root_r = p.slot_width

            # Long sides (parallel to X axis)
            flat_x_half = (l_inner - 2 * r_inner) / 2.0
            if flat_x_half > 10.0 and p.rect_slots_long_side > 0:
                step_x = (2 * flat_x_half * 0.7) / max(1, p.rect_slots_long_side)
                x_offsets = [-flat_x_half * 0.35 + i * step_x for i in range(p.rect_slots_long_side)]
                for y_sign in [-1, 1]:
                    y_pos = y_sign * (w_outer / 2.0)
                    for x_pos in x_offsets:
                        with Locations((x_pos, y_pos, -p.skirt_height + slot_h / 2.0)):
                            Box(p.slot_width, p.skirt_wall_thickness * 4, slot_h, mode=Mode.SUBTRACT)
                        with Locations((x_pos, y_pos, -p.skirt_height + slot_h)):
                            Cylinder(radius=slot_root_r, height=p.skirt_wall_thickness * 4, rotation=(90, 0, 0), mode=Mode.SUBTRACT)

            # Short sides (parallel to Y axis)
            flat_y_half = (w_inner - 2 * r_inner) / 2.0
            if flat_y_half > 10.0 and p.rect_slots_short_side > 0:
                step_y = (2 * flat_y_half * 0.7) / max(1, p.rect_slots_short_side)
                y_offsets = [-flat_y_half * 0.35 + i * step_y for i in range(p.rect_slots_short_side)]
                for x_sign in [-1, 1]:
                    x_pos = x_sign * (l_outer / 2.0)
                    for y_pos in y_offsets:
                        with Locations((x_pos, y_pos, -p.skirt_height + slot_h / 2.0)):
                            Box(p.skirt_wall_thickness * 4, p.slot_width, slot_h, mode=Mode.SUBTRACT)
                        with Locations((x_pos, y_pos, -p.skirt_height + slot_h)):
                            Cylinder(radius=slot_root_r, height=p.skirt_wall_thickness * 4, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        # 8. Test Ring Gauge Mode: hollow out center to save filament and test fit fast
        if p.test_ring:
            cutout_l = max(10.0, l_inner - 14.0)
            cutout_w = max(10.0, w_inner - 14.0)
            cutout_r = max(2.0, r_inner - 7.0)
            with BuildSketch(Plane.XY):
                RectangleRounded(cutout_l, cutout_w, radius=cutout_r)
            extrude(amount=p.top_thickness * 4, both=True, mode=Mode.SUBTRACT)

    assert rect_part.part is not None, "Failed to generate rectangular lid"
    return rect_part.part


def create_container_lid(params: ContainerLidParams) -> Solid:
    """Standalone generator function returning container lid CAD solid without side effects."""
    p = params.get_effective_params()
    shape_lower = p.shape.lower()
    if shape_lower == "round":
        return build_round_lid(p)
    elif shape_lower in ("rectangular", "square", "rect"):
        return build_rectangular_lid(p)
    else:
        raise ValueError(f"Unsupported shape: {p.shape}. Choose 'round' or 'rectangular'.")


if __name__ == "__main__":
    # Instantiate with no overrides so dataclass defaults take effect directly
    params = ContainerLidParams()
    lid = create_container_lid(params)

    # Standardized exports
    if EXPORT_STEP or EXPORT_STL:
        exports_dir = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_dir.mkdir(parents=True, exist_ok=True)
        p_eff = params.get_effective_params()
        if p_eff.shape.lower() == "round":
            dim_str = f"{p_eff.diameter:.0f}mm"
        else:
            dim_str = f"{p_eff.length:.0f}x{p_eff.width:.0f}mm"
        variant = f"{p_eff.shape.lower()}_{p_eff.material.lower()}"
        stem = f"container_lid_{dim_str}_{variant}"

        if EXPORT_STL:
            stl_file = exports_dir / f"{stem}.stl"
            export_stl(lid, str(stl_file))
            print(f"Exported STL: {stl_file}")

        if EXPORT_STEP:
            step_file = exports_dir / f"{stem}.step"
            export_step(lid, str(step_file))
            print(f"Exported STEP: {step_file}")

    show(lid)
