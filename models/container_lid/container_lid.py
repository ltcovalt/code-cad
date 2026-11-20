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

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Literal, Optional
from build123d import *

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False                # Save .stl file on execution (default: False)
EXPORT_STEP: bool = False               # Save .step file on execution (default: False)
OUTPUT_DIR: str = "exports"             # Output folder (relative to this script's directory)


@dataclass
class CoreParams:
    """Material, container shape, rim dimensions, and fit tolerance."""

    material: Literal["tpu", "pctg", "petg", "rigid"] = "tpu"  # Flexible stretch vs rigid compliant flex
    shape: Literal["round", "rectangular"] = "round"           # Round or rectangular/square container
    rim_style: Literal["beaded", "smooth"] = "beaded"          # Beaded glass rim lip vs smooth straight wall
    friction_ribs: bool = False         # Adds wiper gasket ribs for grip on smooth glass
    diameter: float = 150.0             # Round: outer diameter of rim lip in mm (Pyrex 4-cup = ~150 mm)
    length: float = 182.0               # Rectangular: outer length of rim lip in mm (Pyrex 3-cup = ~182 mm)
    width: float = 132.0                # Rectangular: outer width of rim lip in mm (Pyrex 3-cup = ~132 mm)
    corner_radius: float = 20.0         # Rectangular: corner radius of glass dish in mm
    diameter_in: Optional[float] = None # Round: diameter in inches (overrides diameter if set)
    length_in: Optional[float] = None   # Rectangular: length in inches (overrides length if set)
    width_in: Optional[float] = None    # Rectangular: width in inches (overrides width if set)
    test_ring: bool = False             # Hollows center for quick fit-check test ring
    rim_lip_height: float = 5.0         # Vertical height/thickness of glass rim bead in mm
    glass_wall_thickness: float = 4.0   # Thickness of glass at container rim in mm
    fit_tolerance: Optional[float] = None  # mm added to container dim (None = auto: -0.2 TPU, +0.2 PCTG)


@dataclass
class LidStructureParams:
    """Lid top plate and downward skirt wall dimensions."""

    top_thickness: float = 1.8          # Solid top plate thickness in mm
    skirt_height: float = 10.0          # Total vertical depth of outer downward skirt in mm
    skirt_wall_thickness: float = 1.8   # Outer side skirt wall thickness in mm
    outer_fillet: float = 1.2           # Fillet radius on top exterior perimeter edge in mm
    lead_in_chamfer: float = 0.8        # Chamfer on inside bottom rim of skirt for smooth mounting


@dataclass
class SnapBeadParams:
    """Inward retention snap bead under container glass lip."""

    enabled: bool = True                # Enable inward protruding snap ridge
    depth: Optional[float] = None       # Inward protrusion (None = auto: 0.8mm TPU, 0.35mm PCTG)
    height: float = 1.5                 # Vertical height of retention bead profile in mm
    offset: Optional[float] = None      # Distance from underside to top of bead (None = rim_lip_height + 0.2mm)


@dataclass
class InnerSealParams:
    """Inner seal plug ring sitting inside the container wall."""

    enabled: bool = True                # Enable downward inner seal tongue
    height: float = 3.5                 # Downward depth of seal ring in mm
    thickness: float = 1.2              # Thickness of seal ring wall in mm
    clearance: float = 0.6              # Radial gap between glass inner wall and seal ring in mm


@dataclass
class StackingRimParams:
    """Raised top nesting rim for stacked containers."""

    enabled: bool = True                # Enable raised stacking rim on top surface
    height: float = 1.5                 # Height of stacking rim in mm
    thickness: float = 1.5              # Wall thickness of stacking rim in mm
    inset: float = 4.0                  # Inward distance from lid edge to stacking rim in mm


@dataclass
class PullTabParams:
    """Ergonomic outer pull tab for lid removal."""

    enabled: bool = True                # Enable outer peel tab
    location: Literal["auto", "corner", "edge"] = "auto"  # Corner for rect, edge for round
    length: float = 8.5                 # Protrusion length beyond skirt in mm
    width: float = 22.0                 # Width of tab in mm
    root_overlap: float = 6.0           # Root overlap into top plate/skirt in mm
    gusset_depth: float = 2.5           # Under-tab structural gusset depth down skirt wall in mm
    thickness: float = 2.0              # Thickness of tab plate in mm
    grip_ribs: bool = True              # Raised non-slip traction ribs on tab surface
    hanging_hole: bool = False          # Pegboard / dish-rack drying hole
    hole_diameter: float = 4.0          # Diameter of hanging hole in mm


@dataclass
class FlexSlotsParams:
    """Rigid flexure relief slots (for PCTG / PETG / rigid plastics)."""

    enabled: Optional[bool] = None      # None = auto (True for rigid beaded lids, False for TPU)
    slot_width: float = 1.5             # Width of vertical cutouts through skirt in mm
    round_slot_count: int = 6           # Number of relief slots around round circumference
    rect_slots_long_side: int = 2       # Number of relief slots along each long side
    rect_slots_short_side: int = 1      # Number of relief slots along each short side


@dataclass
class ContainerLidParams:
    """Parameters for container lid generation."""

    core: CoreParams = field(default_factory=CoreParams)
    structure: LidStructureParams = field(default_factory=LidStructureParams)
    snap_bead: SnapBeadParams = field(default_factory=SnapBeadParams)
    inner_seal: InnerSealParams = field(default_factory=InnerSealParams)
    stacking_rim: StackingRimParams = field(default_factory=StackingRimParams)
    pull_tab: PullTabParams = field(default_factory=PullTabParams)
    flex_slots: FlexSlotsParams = field(default_factory=FlexSlotsParams)

    def get_effective_params(self) -> "ContainerLidParams":
        """Return a copy of params with auto-resolved defaults based on active material, rim style, and units."""
        p = copy.deepcopy(self)
        is_rigid = p.core.material.lower() in ("pctg", "petg", "rigid", "pla")
        is_smooth = p.core.rim_style.lower() in ("smooth", "straight", "flat", "no_rim", "no_lip")

        if p.core.diameter_in is not None:
            p.core.diameter = p.core.diameter_in * 25.4
        if p.core.length_in is not None:
            p.core.length = p.core.length_in * 25.4
        if p.core.width_in is not None:
            p.core.width = p.core.width_in * 25.4

        if is_smooth:
            p.snap_bead.enabled = False
            if not self.core.friction_ribs:
                p.core.friction_ribs = True

        if p.core.fit_tolerance is None:
            if is_smooth:
                p.core.fit_tolerance = 0.1 if is_rigid else -0.35
            else:
                p.core.fit_tolerance = 0.2 if is_rigid else -0.2

        if p.snap_bead.depth is None:
            p.snap_bead.depth = 0.35 if is_rigid else 0.8
        if p.snap_bead.offset is None:
            p.snap_bead.offset = p.core.rim_lip_height + 0.2
        if p.flex_slots.enabled is None:
            p.flex_slots.enabled = is_rigid and not is_smooth
        return p


# Verified Presets for Popular Pyrex Food Storage Containers
PYREX_PRESETS: Dict[str, ContainerLidParams] = {
    "pyrex_round_1_cup": ContainerLidParams(
        core=CoreParams(shape="round", diameter=98.0, rim_lip_height=4.5, glass_wall_thickness=3.8),
        structure=LidStructureParams(skirt_height=9.0),
    ),
    "pyrex_round_2_cup": ContainerLidParams(
        core=CoreParams(shape="round", diameter=120.0, rim_lip_height=5.0, glass_wall_thickness=4.0),
        structure=LidStructureParams(skirt_height=10.0),
    ),
    "pyrex_round_4_cup": ContainerLidParams(
        core=CoreParams(shape="round", diameter=150.0, rim_lip_height=5.2, glass_wall_thickness=4.2),
        structure=LidStructureParams(skirt_height=10.5),
    ),
    "pyrex_round_7_cup": ContainerLidParams(
        core=CoreParams(shape="round", diameter=185.0, rim_lip_height=5.5, glass_wall_thickness=4.5),
        structure=LidStructureParams(skirt_height=11.5),
    ),
    "pyrex_rect_3_cup": ContainerLidParams(
        core=CoreParams(shape="rectangular", length=182.0, width=132.0, corner_radius=20.0, rim_lip_height=5.0, glass_wall_thickness=4.0),
        structure=LidStructureParams(skirt_height=10.0),
    ),
    "pyrex_rect_6_cup": ContainerLidParams(
        core=CoreParams(shape="rectangular", length=225.0, width=175.0, corner_radius=25.0, rim_lip_height=5.5, glass_wall_thickness=4.5),
        structure=LidStructureParams(skirt_height=11.0),
    ),
    "pyrex_rect_11_cup": ContainerLidParams(
        core=CoreParams(shape="rectangular", length=280.0, width=200.0, corner_radius=30.0, rim_lip_height=6.0, glass_wall_thickness=5.0),
        structure=LidStructureParams(skirt_height=12.0),
    ),
}

# Verified Presets for Anchor Hocking (TrueSeal / SnugFit) Food Storage Containers
ANCHOR_PRESETS: Dict[str, ContainerLidParams] = {
    "anchor_round_1_cup": ContainerLidParams(
        core=CoreParams(shape="round", diameter=96.0, rim_lip_height=4.5, glass_wall_thickness=3.8),
        structure=LidStructureParams(skirt_height=9.0),
    ),
    "anchor_round_2_cup": ContainerLidParams(
        core=CoreParams(shape="round", diameter=122.0, rim_lip_height=4.8, glass_wall_thickness=4.0),
        structure=LidStructureParams(skirt_height=10.0),
    ),
    "anchor_round_4_cup": ContainerLidParams(
        core=CoreParams(shape="round", diameter=152.0, rim_lip_height=5.2, glass_wall_thickness=4.2),
        structure=LidStructureParams(skirt_height=10.5),
    ),
    "anchor_round_7_cup": ContainerLidParams(
        core=CoreParams(shape="round", diameter=186.0, rim_lip_height=5.5, glass_wall_thickness=4.5),
        structure=LidStructureParams(skirt_height=11.5),
    ),
    "anchor_rect_4_75_cup": ContainerLidParams(
        core=CoreParams(shape="rectangular", length=195.0, width=148.0, corner_radius=22.0, rim_lip_height=5.2, glass_wall_thickness=4.2),
        structure=LidStructureParams(skirt_height=10.5),
    ),
}

CONTAINER_PRESETS: Dict[str, ContainerLidParams] = {**PYREX_PRESETS, **ANCHOR_PRESETS}


def build_round_lid(p: ContainerLidParams) -> Solid:
    """Build a round container lid using build123d."""
    c, st, bead, seal, stack, tab, flex = (
        p.core, p.structure, p.snap_bead, p.inner_seal, p.stacking_rim, p.pull_tab, p.flex_slots
    )
    r_inner = (c.diameter + c.fit_tolerance) / 2.0
    r_outer = r_inner + st.skirt_wall_thickness

    r_seal_outer = r_inner - c.glass_wall_thickness - seal.clearance
    r_seal_inner = r_seal_outer - seal.thickness
    has_seal = seal.enabled and (r_seal_inner > 2.0)

    r_stack_outer = r_outer - stack.inset
    r_stack_inner = r_stack_outer - stack.thickness
    has_stack = stack.enabled and (r_stack_inner > 2.0)

    pts = [(0.0, 0.0)]

    if has_seal:
        pts.extend([
            (r_seal_inner, 0.0),
            (r_seal_inner, -seal.height + 0.5),
            (r_seal_inner + 0.5, -seal.height),
            (r_seal_outer - 0.5, -seal.height),
            (r_seal_outer, -seal.height + 0.5),
            (r_seal_outer, 0.0),
        ])

    pts.append((r_inner, 0.0))

    if bead.enabled and bead.depth > 0:
        pts.extend([
            (r_inner, -bead.offset),
            (r_inner - bead.depth, -bead.offset - 0.3),
            (r_inner - bead.depth, -bead.offset - bead.height + 0.6),
            (r_inner, -bead.offset - bead.height),
        ])
    elif c.friction_ribs:
        for z_rib in [-3.0, -6.5]:
            if abs(z_rib) + 0.6 < st.skirt_height - st.lead_in_chamfer:
                pts.extend([
                    (r_inner, z_rib + 0.5),
                    (r_inner - 0.3, z_rib),
                    (r_inner, z_rib - 0.5),
                ])

    pts.extend([
        (r_inner, -st.skirt_height + st.lead_in_chamfer),
        (r_inner + st.lead_in_chamfer, -st.skirt_height),
        (r_outer, -st.skirt_height),
    ])

    if st.outer_fillet > 0:
        pts.extend([
            (r_outer, st.top_thickness - st.outer_fillet),
            (r_outer - st.outer_fillet, st.top_thickness),
        ])
    else:
        pts.append((r_outer, st.top_thickness))

    if has_stack:
        pts.extend([
            (r_stack_outer, st.top_thickness),
            (r_stack_outer, st.top_thickness + stack.height),
            (r_stack_inner, st.top_thickness + stack.height),
            (r_stack_inner, st.top_thickness),
        ])

    pts.extend([
        (0.0, st.top_thickness),
        (0.0, 0.0),
    ])

    with BuildPart() as round_part:
        with BuildSketch(Plane.XZ):
            Polygon(pts)
        revolve(axis=Axis.Z)

        if tab.enabled:
            tab_total_len = tab.length + tab.root_overlap
            tab_center_x = (r_outer - tab.root_overlap) + tab_total_len / 2.0

            with BuildSketch(Plane.XY):
                with Locations((tab_center_x, 0)):
                    RectangleRounded(tab_total_len, tab.width, radius=4.0)
                if tab.hanging_hole:
                    with Locations((r_outer + tab.length - (tab.hole_diameter / 2.0 + 2.0), 0)):
                        Circle(radius=tab.hole_diameter / 2.0, mode=Mode.SUBTRACT)
            extrude(amount=st.top_thickness, mode=Mode.ADD)

            if tab.gusset_depth > 0:
                with BuildSketch(Plane.XY.offset(-tab.gusset_depth)):
                    with Locations(((r_outer - tab.root_overlap) + (tab.root_overlap + tab.length * 0.4) / 2.0, 0)):
                        RectangleRounded(tab.root_overlap + tab.length * 0.4, tab.width * 0.75, radius=3.0)
                with BuildSketch(Plane.XY):
                    with Locations(((r_outer - tab.root_overlap) + (tab.root_overlap + tab.length * 0.8) / 2.0, 0)):
                        RectangleRounded(tab.root_overlap + tab.length * 0.8, tab.width, radius=3.5)
                loft(ruled=True, mode=Mode.ADD)

            if tab.grip_ribs:
                for i in range(3):
                    rib_x = r_outer + 2.0 + i * 2.2
                    if rib_x + 0.8 < (r_outer + tab.length - 1.0):
                        with BuildSketch(Plane.XY.offset(st.top_thickness)):
                            with Locations((rib_x, 0)):
                                RectangleRounded(1.0, tab.width - 8.0, radius=0.4)
                        extrude(amount=0.6, mode=Mode.ADD)

        if flex.enabled and flex.round_slot_count > 0:
            slot_h = st.skirt_height - 1.5
            slot_root_r = flex.slot_width
            for i in range(flex.round_slot_count):
                ang = i * (360.0 / flex.round_slot_count)
                if tab.enabled and (ang < 25.0 or ang > 335.0):
                    continue
                rot = Rotation(0, 0, ang)
                with Locations(rot):
                    with Locations((r_outer, 0, -st.skirt_height + slot_h / 2.0)):
                        Box(st.skirt_wall_thickness * 4, flex.slot_width, slot_h, mode=Mode.SUBTRACT)
                    with Locations((r_outer, 0, -st.skirt_height + slot_h)):
                        Cylinder(radius=slot_root_r, height=st.skirt_wall_thickness * 4, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        if c.test_ring:
            gauge_inner_r = max(5.0, (r_seal_inner - 2.0) if has_seal else (r_inner - 6.0))
            with BuildSketch(Plane.XY):
                Circle(radius=gauge_inner_r)
            extrude(amount=st.top_thickness * 4, both=True, mode=Mode.SUBTRACT)

    assert round_part.part is not None, "Failed to generate round lid"
    return round_part.part


def build_rectangular_lid(p: ContainerLidParams) -> Solid:
    """Build a rectangular or square container lid using build123d."""
    c, st, bead, seal, stack, tab, flex = (
        p.core, p.structure, p.snap_bead, p.inner_seal, p.stacking_rim, p.pull_tab, p.flex_slots
    )
    l_inner = c.length + c.fit_tolerance
    w_inner = c.width + c.fit_tolerance
    r_inner = max(2.0, c.corner_radius + c.fit_tolerance / 2.0)

    l_outer = l_inner + 2 * st.skirt_wall_thickness
    w_outer = w_inner + 2 * st.skirt_wall_thickness
    r_outer = r_inner + st.skirt_wall_thickness

    with BuildPart() as rect_part:
        with BuildSketch(Plane.XY):
            RectangleRounded(l_outer, w_outer, radius=r_outer)
        extrude(amount=st.top_thickness, mode=Mode.ADD)
        with BuildSketch(Plane.XY):
            RectangleRounded(l_outer, w_outer, radius=r_outer)
        extrude(amount=-st.skirt_height, mode=Mode.ADD)

        if st.outer_fillet > 0:
            outer_top_edges = [e for e in rect_part.edges() if abs(e.center().Z - st.top_thickness) < 1e-3]
            if outer_top_edges:
                fillet(outer_top_edges, radius=min(st.outer_fillet, st.skirt_wall_thickness * 0.7))

        with BuildSketch(Plane.XY):
            RectangleRounded(l_inner, w_inner, radius=r_inner)
        extrude(amount=-st.skirt_height, mode=Mode.SUBTRACT)

        if st.lead_in_chamfer > 0:
            with BuildSketch(Plane.XY.offset(-st.skirt_height)):
                RectangleRounded(l_inner + 2 * st.lead_in_chamfer, w_inner + 2 * st.lead_in_chamfer, radius=r_inner + st.lead_in_chamfer)
                RectangleRounded(l_inner, w_inner, radius=r_inner, mode=Mode.SUBTRACT)
            extrude(amount=st.lead_in_chamfer, mode=Mode.SUBTRACT)

        if bead.enabled and bead.depth > 0:
            l_bead = l_inner - 2 * bead.depth
            w_bead = w_inner - 2 * bead.depth
            r_bead = max(1.0, r_inner - bead.depth)

            bead_flat_height = bead.height * 0.4
            with BuildSketch(Plane.XY.offset(-bead.offset)):
                RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                RectangleRounded(l_bead, w_bead, radius=r_bead, mode=Mode.SUBTRACT)
            extrude(amount=-bead_flat_height, mode=Mode.ADD)

            with BuildSketch(Plane.XY.offset(-bead.offset - bead_flat_height)) as s1:
                RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                RectangleRounded(l_bead, w_bead, radius=r_bead, mode=Mode.SUBTRACT)
            with BuildSketch(Plane.XY.offset(-bead.offset - bead.height)) as s2:
                RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                RectangleRounded(l_inner, w_inner, radius=r_inner, mode=Mode.SUBTRACT)
            loft([s1.sketch, s2.sketch], ruled=True, mode=Mode.ADD)
        elif c.friction_ribs:
            for z_rib in [-3.0, -6.5]:
                if abs(z_rib) + 0.6 < st.skirt_height - st.lead_in_chamfer:
                    with BuildSketch(Plane.XY.offset(z_rib - 0.4)):
                        RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                        RectangleRounded(l_inner - 0.6, w_inner - 0.6, radius=max(1.0, r_inner - 0.3), mode=Mode.SUBTRACT)
                    extrude(amount=0.8, mode=Mode.ADD)

        if seal.enabled:
            l_seal_out = l_inner - 2 * (c.glass_wall_thickness + seal.clearance)
            w_seal_out = w_inner - 2 * (c.glass_wall_thickness + seal.clearance)
            r_seal_out = max(1.0, r_inner - (c.glass_wall_thickness + seal.clearance))
            l_seal_in = l_seal_out - 2 * seal.thickness
            w_seal_in = w_seal_out - 2 * seal.thickness
            r_seal_in = max(0.5, r_seal_out - seal.thickness)

            if l_seal_in > 5.0 and w_seal_in > 5.0:
                with BuildSketch(Plane.XY):
                    RectangleRounded(l_seal_out, w_seal_out, radius=r_seal_out)
                    RectangleRounded(l_seal_in, w_seal_in, radius=r_seal_in, mode=Mode.SUBTRACT)
                extrude(amount=-seal.height, mode=Mode.ADD)

        if stack.enabled:
            l_stack_out = l_outer - 2 * stack.inset
            w_stack_out = w_outer - 2 * stack.inset
            r_stack_out = max(1.0, r_outer - stack.inset)
            l_stack_in = l_stack_out - 2 * stack.thickness
            w_stack_in = w_stack_out - 2 * stack.thickness
            r_stack_in = max(0.5, r_stack_out - stack.thickness)

            if l_stack_in > 5.0 and w_stack_in > 5.0:
                with BuildSketch(Plane.XY.offset(st.top_thickness)):
                    RectangleRounded(l_stack_out, w_stack_out, radius=r_stack_out)
                    RectangleRounded(l_stack_in, w_stack_in, radius=r_stack_in, mode=Mode.SUBTRACT)
                extrude(amount=stack.height, mode=Mode.ADD)

        if tab.enabled:
            is_corner = (tab.location == "corner") or (tab.location == "auto")
            tab_len = tab.length
            tab_w = tab.width
            tab_overlap = tab.root_overlap
            tab_total_len = tab_len + tab_overlap

            if is_corner:
                corner_cx = l_outer / 2.0 - r_outer
                corner_cy = w_outer / 2.0 - r_outer
                tab_loc = Location((corner_cx, corner_cy, 0), (0, 0, 45.0))
                tab_center_dist = (r_outer - tab_overlap) + tab_total_len / 2.0

                with BuildSketch(Plane.XY):
                    with Locations(tab_loc):
                        with Locations((tab_center_dist, 0)):
                            RectangleRounded(tab_total_len, tab_w, radius=4.0)
                        if tab.hanging_hole:
                            with Locations((r_outer + tab_len - (tab.hole_diameter / 2.0 + 2.0), 0)):
                                Circle(radius=tab.hole_diameter / 2.0, mode=Mode.SUBTRACT)
                extrude(amount=st.top_thickness, mode=Mode.ADD)

                if tab.gusset_depth > 0:
                    with BuildSketch(Plane.XY.offset(-tab.gusset_depth)):
                        with Locations(tab_loc):
                            with Locations(((r_outer - tab_overlap) + (tab_overlap + tab_len * 0.4) / 2.0, 0)):
                                RectangleRounded(tab_overlap + tab_len * 0.4, tab_w * 0.75, radius=3.0)
                    with BuildSketch(Plane.XY):
                        with Locations(tab_loc):
                            with Locations(((r_outer - tab_overlap) + (tab_overlap + tab_len * 0.8) / 2.0, 0)):
                                RectangleRounded(tab_overlap + tab_len * 0.8, tab_w, radius=3.5)
                    loft(ruled=True, mode=Mode.ADD)

                if tab.grip_ribs:
                    for i in range(3):
                        rx = r_outer + 2.0 + i * 2.2
                        if rx + 0.8 < (r_outer + tab_len - 1.0):
                            with BuildSketch(Plane.XY.offset(st.top_thickness)):
                                with Locations(tab_loc):
                                    with Locations((rx, 0)):
                                        RectangleRounded(1.0, tab_w - 8.0, radius=0.4)
                            extrude(amount=0.6, mode=Mode.ADD)
            else:
                tab_center_x = (l_outer / 2.0 - tab_overlap) + tab_total_len / 2.0
                with BuildSketch(Plane.XY):
                    with Locations((tab_center_x, 0)):
                        RectangleRounded(tab_total_len, tab_w, radius=4.0)
                    if tab.hanging_hole:
                        with Locations((l_outer / 2.0 + tab_len - (tab.hole_diameter / 2.0 + 2.0), 0)):
                            Circle(radius=tab.hole_diameter / 2.0, mode=Mode.SUBTRACT)
                extrude(amount=st.top_thickness, mode=Mode.ADD)

                if tab.gusset_depth > 0:
                    with BuildSketch(Plane.XY.offset(-tab.gusset_depth)):
                        with Locations(((l_outer / 2.0 - tab_overlap) + (tab_overlap + tab_len * 0.4) / 2.0, 0)):
                            RectangleRounded(tab_overlap + tab_len * 0.4, tab_w * 0.75, radius=3.0)
                    with BuildSketch(Plane.XY):
                        with Locations(((l_outer / 2.0 - tab_overlap) + (tab_overlap + tab_len * 0.8) / 2.0, 0)):
                            RectangleRounded(tab_overlap + tab_len * 0.8, tab_w, radius=3.5)
                    loft(ruled=True, mode=Mode.ADD)

                if tab.grip_ribs:
                    for i in range(3):
                        rx = l_outer / 2.0 + 2.0 + i * 2.2
                        if rx + 0.8 < (l_outer / 2.0 + tab_len - 1.0):
                            with BuildSketch(Plane.XY.offset(st.top_thickness)):
                                with Locations((rx, 0)):
                                    RectangleRounded(1.0, tab_w - 8.0, radius=0.4)
                            extrude(amount=0.6, mode=Mode.ADD)

        if flex.enabled:
            slot_h = st.skirt_height - 1.5
            slot_root_r = flex.slot_width

            flat_x_half = (l_inner - 2 * r_inner) / 2.0
            if flat_x_half > 10.0 and flex.rect_slots_long_side > 0:
                step_x = (2 * flat_x_half * 0.7) / max(1, flex.rect_slots_long_side)
                x_offsets = [-flat_x_half * 0.35 + i * step_x for i in range(flex.rect_slots_long_side)]
                for y_sign in [-1, 1]:
                    y_pos = y_sign * (w_outer / 2.0)
                    for x_pos in x_offsets:
                        with Locations((x_pos, y_pos, -st.skirt_height + slot_h / 2.0)):
                            Box(flex.slot_width, st.skirt_wall_thickness * 4, slot_h, mode=Mode.SUBTRACT)
                        with Locations((x_pos, y_pos, -st.skirt_height + slot_h)):
                            Cylinder(radius=slot_root_r, height=st.skirt_wall_thickness * 4, rotation=(90, 0, 0), mode=Mode.SUBTRACT)

            flat_y_half = (w_inner - 2 * r_inner) / 2.0
            if flat_y_half > 10.0 and flex.rect_slots_short_side > 0:
                step_y = (2 * flat_y_half * 0.7) / max(1, flex.rect_slots_short_side)
                y_offsets = [-flat_y_half * 0.35 + i * step_y for i in range(flex.rect_slots_short_side)]
                for x_sign in [-1, 1]:
                    x_pos = x_sign * (l_outer / 2.0)
                    for y_pos in y_offsets:
                        with Locations((x_pos, y_pos, -st.skirt_height + slot_h / 2.0)):
                            Box(st.skirt_wall_thickness * 4, flex.slot_width, slot_h, mode=Mode.SUBTRACT)
                        with Locations((x_pos, y_pos, -st.skirt_height + slot_h)):
                            Cylinder(radius=slot_root_r, height=st.skirt_wall_thickness * 4, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        if c.test_ring:
            cutout_l = max(10.0, l_inner - 14.0)
            cutout_w = max(10.0, w_inner - 14.0)
            cutout_r = max(2.0, r_inner - 7.0)
            with BuildSketch(Plane.XY):
                RectangleRounded(cutout_l, cutout_w, radius=cutout_r)
            extrude(amount=st.top_thickness * 4, both=True, mode=Mode.SUBTRACT)

    assert rect_part.part is not None, "Failed to generate rectangular lid"
    return rect_part.part


def create_container_lid(params: ContainerLidParams) -> Solid:
    """Standalone generator function returning container lid CAD solid without side effects."""
    p = params.get_effective_params()
    shape_lower = p.core.shape.lower()
    if shape_lower == "round":
        return build_round_lid(p)
    elif shape_lower in ("rectangular", "square", "rect"):
        return build_rectangular_lid(p)
    else:
        raise ValueError(f"Unsupported shape: {p.core.shape}. Choose 'round' or 'rectangular'.")


if __name__ == "__main__":
    params = ContainerLidParams()
    lid = create_container_lid(params)

    if EXPORT_STEP or EXPORT_STL:
        exports_dir = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_dir.mkdir(parents=True, exist_ok=True)
        p_eff = params.get_effective_params()
        if p_eff.core.shape.lower() == "round":
            dim_str = f"{p_eff.core.diameter:.0f}mm"
        else:
            dim_str = f"{p_eff.core.length:.0f}x{p_eff.core.width:.0f}mm"
        variant = f"{p_eff.core.shape.lower()}_{p_eff.core.material.lower()}"
        stem = f"container_lid_{dim_str}_{variant}"

        if EXPORT_STL:
            stl_file = exports_dir / f"{stem}.stl"
            export_stl(lid, str(stl_file))
            print(f"Exported STL: {stl_file}")

        if EXPORT_STEP:
            step_file = exports_dir / f"{stem}.step"
            export_step(lid, str(step_file))
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

    show(lid)
