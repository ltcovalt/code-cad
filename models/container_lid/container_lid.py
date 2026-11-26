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
- Verified Pyrex and Anchor Hocking container size presets in `presets.json`
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional
from build123d import *

try:
    from components.pull_tab import (
        PullTabParams,
        build_pull_tab,
        pull_tab_angular_clearance,
    )
    from utils.params import group, param
except ImportError:
    import sys

    for _p in Path(__file__).resolve().parents:
        if (_p / "utils").is_dir():
            sys.path.insert(0, str(_p))
            break
    from components.pull_tab import (
        PullTabParams,
        build_pull_tab,
        pull_tab_angular_clearance,
    )
    from utils.params import group, param

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False                # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False               # Save .step to repo-root exports/ (default: False)


@dataclass
class CoreParams:
    """Container shape, rim dimensions, and fit tolerance."""

    shape: Literal["round", "rectangular"] = param(
        "round",
        desc="Round or rectangular/square container",
    )
    rim_style: Literal["beaded", "smooth"] = param(
        "beaded",
        desc="Beaded glass rim lip vs smooth straight wall",
    )
    friction_ribs: bool = param(
        False,
        desc="Add wiper gasket ribs for grip on smooth glass",
    )
    diameter: float = param(
        150.0,
        desc="Outer rim lip diameter (Pyrex 4-cup ≈ 150 mm)",
        unit="mm", min=40.0, max=350.0, step=1.0, when={"shape": "round"},
    )
    length: float = param(
        182.0,
        desc="Outer rim lip length (Pyrex 3-cup ≈ 182 mm)",
        unit="mm", min=60.0, max=400.0, step=1.0, when={"shape": "rectangular"},
    )
    width: float = param(
        132.0,
        desc="Outer rim lip width (Pyrex 3-cup ≈ 132 mm)",
        unit="mm", min=60.0, max=350.0, step=1.0, when={"shape": "rectangular"},
    )
    corner_radius: float = param(
        20.0,
        desc="Outer corner radius of glass dish",
        unit="mm", min=2.0, max=60.0, step=1.0, when={"shape": "rectangular"},
    )
    test_ring: bool = param(
        False,
        desc="Hollow center for quick fit-check test ring",
    )
    rim_lip_height: float = param(
        5.0,
        desc="Vertical thickness of glass rim bead",
        unit="mm", min=2.0, max=15.0, step=0.2, when={"rim_style": "beaded"},
    )
    glass_wall_thickness: float = param(
        4.0,
        desc="Glass thickness at container rim",
        unit="mm", min=1.5, max=10.0, step=0.2,
    )
    fit_tolerance: float = param(
        -0.2,
        desc="Added to container size (negative = tighter stretch fit, positive = looser)",
        unit="mm", min=-2.0, max=2.0, step=0.05,
    )


@dataclass
class LidStructureParams:
    """Lid top plate and downward skirt wall dimensions."""

    top_thickness: float = param(
        1.8,
        desc="Solid top plate thickness",
        unit="mm", min=0.8, max=5.0, step=0.2,
    )
    skirt_height: float = param(
        10.0,
        desc="Vertical depth of outer downward skirt",
        unit="mm", min=5.0, max=25.0, step=0.5,
    )
    skirt_wall_thickness: float = param(
        1.8,
        desc="Outer skirt side wall thickness",
        unit="mm", min=1.0, max=5.0, step=0.2,
    )
    skirt_taper: float = param(
        0.0,
        desc="Inward radial taper at bottom of skirt (for tapered bowls)",
        unit="mm", min=0.0, max=5.0, step=0.1,
    )
    outer_fillet: float = param(
        1.2,
        desc="Top exterior perimeter edge fillet",
        unit="mm", min=0.0, max=4.0, step=0.2,
    )
    lead_in_chamfer: float = param(
        0.8,
        desc="Inside bottom rim bevel for easy mounting",
        unit="mm", min=0.0, max=3.0, step=0.1,
    )
    pull_tab_location: Literal["auto", "corner", "edge"] = param(
        "auto",
        label="Pull Tab Placement",
        desc="Corner for rectangular, edge for round",
        when={"core.shape": "rectangular"},
    )


@dataclass
class SnapBeadParams:
    """Inward retention snap bead under container glass lip."""

    enabled: bool = param(
        True,
        desc="Add inward protruding snap ridge",
    )
    depth: float = param(
        0.8,
        desc="Inward protrusion under container rim",
        unit="mm", min=0.1, max=2.5, step=0.05,
    )
    height: float = param(
        1.5,
        desc="Vertical height of retention bead profile",
        unit="mm", min=0.5, max=5.0, step=0.1,
    )
    offset: Optional[float] = param(
        None,
        desc="Distance below lid underside (Auto = rim lip + 0.2)",
        unit="mm", min=1.0, max=15.0, step=0.2,
    )


@dataclass
class InnerSealParams:
    """Inner seal plug ring sitting inside the container wall."""

    enabled: bool = param(
        True,
        desc="Add downward inner seal tongue",
    )
    height: float = param(
        3.5,
        desc="Downward depth of seal ring",
        unit="mm", min=1.0, max=10.0, step=0.5,
    )
    thickness: float = param(
        1.2,
        desc="Seal ring wall thickness",
        unit="mm", min=0.6, max=3.0, step=0.1,
    )
    clearance: float = param(
        0.6,
        desc="Radial gap between glass inner wall and seal",
        unit="mm", min=0.0, max=3.0, step=0.1,
    )


@dataclass
class StackingRimParams:
    """Raised top nesting rim for stacked containers."""

    enabled: bool = param(
        False,
        desc="Add raised stacking rim on top surface",
    )
    height: float = param(
        1.5,
        desc="Stacking rim height",
        unit="mm", min=0.5, max=5.0, step=0.2,
    )
    thickness: float = param(
        1.5,
        desc="Stacking rim wall thickness",
        unit="mm", min=0.8, max=4.0, step=0.2,
    )
    inset: float = param(
        4.0,
        desc="Inward distance from lid edge",
        unit="mm", min=1.0, max=15.0, step=0.5,
    )


@dataclass
class FlexSlotsParams:
    """Rigid flexure relief slots (for PCTG / PETG / rigid plastics)."""

    enabled: bool = param(
        False,
        desc="Add vertical skirt relief slots for rigid plastics",
    )
    slot_width: float = param(
        1.5,
        desc="Vertical skirt relief cutout width",
        unit="mm", min=0.5, max=4.0, step=0.1,
    )
    round_slot_count: int = param(
        6,
        desc="Relief slots around round circumference",
        min=0, max=16, step=1, when={"core.shape": "round"},
    )
    rect_slots_long_side: int = param(
        2,
        desc="Relief slots along each long side",
        min=0, max=8, step=1, when={"core.shape": "rectangular"},
    )
    rect_slots_short_side: int = param(
        1,
        desc="Relief slots along each short side",
        min=0, max=6, step=1, when={"core.shape": "rectangular"},
    )


@dataclass
class ContainerLidParams:
    """Parameters for container lid generation."""

    core: CoreParams = group(CoreParams)
    structure: LidStructureParams = group(LidStructureParams, label="Lid Structure")
    snap_bead: SnapBeadParams = group(SnapBeadParams, when={"core.rim_style": "beaded"})
    inner_seal: InnerSealParams = group(InnerSealParams)
    stacking_rim: StackingRimParams = group(StackingRimParams)
    pull_tab: PullTabParams | None = group(PullTabParams)
    flex_slots: FlexSlotsParams = group(FlexSlotsParams)

    def get_effective_params(self) -> "ContainerLidParams":
        """Return a copy of params with auto-resolved defaults based on rim style."""
        p = copy.deepcopy(self)
        is_smooth = p.core.rim_style.lower() in ("smooth", "straight", "flat", "no_rim", "no_lip")

        if is_smooth:
            p.snap_bead.enabled = False
            if not self.core.friction_ribs:
                p.core.friction_ribs = True

        if p.snap_bead.offset is None:
            p.snap_bead.offset = p.core.rim_lip_height + 0.2
        return p


def export_filename(params: ContainerLidParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    p_eff = params.get_effective_params()
    if p_eff.core.shape.lower() == "round":
        dim_str = f"{p_eff.core.diameter:.0f}mm"
    else:
        dim_str = f"{p_eff.core.length:.0f}x{p_eff.core.width:.0f}mm"
    variant = p_eff.core.shape.lower()
    if p_eff.core.test_ring:
        variant = f"{variant}_test_ring"
    return f"container_lid_{dim_str}_{variant}"


def build_round_lid(p: ContainerLidParams) -> Solid:
    """Build a round container lid using build123d."""
    c, st, bead, seal, stack, tab, flex = (
        p.core, p.structure, p.snap_bead, p.inner_seal, p.stacking_rim, p.pull_tab, p.flex_slots
    )
    r_inner = (c.diameter + c.fit_tolerance) / 2.0
    r_outer = r_inner + st.skirt_wall_thickness
    taper = max(0.0, min(st.skirt_taper, r_inner - 2.0))

    def r_in_at(z: float) -> float:
        return r_inner - taper * (-z / st.skirt_height)

    def r_out_at(z: float) -> float:
        return r_outer - taper * (-z / st.skirt_height)

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
        z_b0 = -bead.offset
        z_b1 = -bead.offset - 0.3
        z_b2 = -bead.offset - bead.height + 0.6
        z_b3 = -bead.offset - bead.height
        pts.extend([
            (r_in_at(z_b0), z_b0),
            (r_in_at(z_b1) - bead.depth, z_b1),
            (r_in_at(z_b2) - bead.depth, z_b2),
            (r_in_at(z_b3), z_b3),
        ])
    elif c.friction_ribs:
        for z_rib in [-3.0, -6.5]:
            if abs(z_rib) + 0.6 < st.skirt_height - st.lead_in_chamfer:
                pts.extend([
                    (r_in_at(z_rib + 0.5), z_rib + 0.5),
                    (r_in_at(z_rib) - 0.3, z_rib),
                    (r_in_at(z_rib - 0.5), z_rib - 0.5),
                ])

    if st.lead_in_chamfer > 0:
        z_chamf = -st.skirt_height + st.lead_in_chamfer
        pts.extend([
            (r_in_at(z_chamf), z_chamf),
            (r_in_at(-st.skirt_height) + st.lead_in_chamfer, -st.skirt_height),
        ])
    else:
        pts.append((r_in_at(-st.skirt_height), -st.skirt_height))

    pts.append((r_out_at(-st.skirt_height), -st.skirt_height))
    if taper > 0:
        pts.append((r_outer, 0.0))

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

        if tab is not None:
            eff_gusset_depth = min(tab.gusset_depth, max(0.0, st.skirt_height - st.lead_in_chamfer))
            round_trim_solid = None
            round_trim_radius = None
            if eff_gusset_depth > 0.2:
                if taper > 0:
                    z_cut_bot = -eff_gusset_depth - 1.0
                    z_cut_top = 1.0
                    with BuildPart() as g_trim:
                        with BuildSketch(Plane.XY.offset(z_cut_bot)) as g_cut_bot:
                            Circle(radius=max(1.0, r_in_at(z_cut_bot) + st.skirt_wall_thickness * 0.5))
                        with BuildSketch(Plane.XY.offset(z_cut_top)) as g_cut_top:
                            Circle(radius=r_in_at(z_cut_top) + st.skirt_wall_thickness * 0.5)
                        loft([g_cut_bot.sketch, g_cut_top.sketch], ruled=True)
                    round_trim_solid = g_trim.part
                else:
                    round_trim_radius = r_inner + st.skirt_wall_thickness * 0.5

            tab_add, tab_cut = build_pull_tab(
                tab,
                x_attach=r_outer,
                top_thickness=st.top_thickness,
                max_gusset_depth=eff_gusset_depth,
                outer_bevel=st.outer_fillet,
                rim_radius=r_outer,
                trim_solid=round_trim_solid,
                trim_radius=round_trim_radius,
                print_orientation=False,
            )
            add(tab_add, mode=Mode.ADD)
            if tab_cut is not None:
                add(tab_cut, mode=Mode.SUBTRACT)

        if flex.enabled and flex.round_slot_count > 0:
            slot_h = st.skirt_height - 1.5
            slot_root_r = flex.slot_width
            slot_radial_len = st.skirt_wall_thickness * 4 + taper * 2
            slot_center_r = r_outer - taper / 2.0
            tab_clear_deg = pull_tab_angular_clearance(tab, r_outer)
            for i in range(flex.round_slot_count):
                ang = i * (360.0 / flex.round_slot_count)
                if tab is not None and (ang < tab_clear_deg or ang > 360.0 - tab_clear_deg):
                    continue
                rot = Rotation(0, 0, ang)
                with Locations(rot):
                    with Locations((slot_center_r, 0, -st.skirt_height + slot_h / 2.0)):
                        Box(slot_radial_len, flex.slot_width, slot_h, mode=Mode.SUBTRACT)
                    with Locations((slot_center_r, 0, -st.skirt_height + slot_h)):
                        Cylinder(radius=slot_root_r, height=slot_radial_len, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

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
    taper = max(0.0, min(st.skirt_taper, min(l_inner, w_inner) / 2.0 - 2.0))

    def rect_in_at(z: float) -> tuple[float, float, float]:
        t = taper * (-z / st.skirt_height)
        return (l_inner - 2 * t, w_inner - 2 * t, max(1.0, r_inner - t))

    def rect_out_at(z: float) -> tuple[float, float, float]:
        t = taper * (-z / st.skirt_height)
        return (l_outer - 2 * t, w_outer - 2 * t, max(1.0, r_outer - t))

    with BuildPart() as rect_part:
        with BuildSketch(Plane.XY):
            RectangleRounded(l_outer, w_outer, radius=r_outer)
        extrude(amount=st.top_thickness, mode=Mode.ADD)
        if taper > 0:
            l_out_bot, w_out_bot, r_out_bot = rect_out_at(-st.skirt_height)
            with BuildSketch(Plane.XY) as sk_out_top:
                RectangleRounded(l_outer, w_outer, radius=r_outer)
            with BuildSketch(Plane.XY.offset(-st.skirt_height)) as sk_out_bot:
                RectangleRounded(l_out_bot, w_out_bot, radius=r_out_bot)
            loft([sk_out_top.sketch, sk_out_bot.sketch], ruled=True, mode=Mode.ADD)
        else:
            with BuildSketch(Plane.XY):
                RectangleRounded(l_outer, w_outer, radius=r_outer)
            extrude(amount=-st.skirt_height, mode=Mode.ADD)

        if st.outer_fillet > 0:
            outer_top_edges = [e for e in rect_part.edges() if abs(e.center().Z - st.top_thickness) < 1e-3]
            if outer_top_edges:
                fillet(outer_top_edges, radius=min(st.outer_fillet, st.skirt_wall_thickness * 0.7))

        if taper > 0:
            z_in_bot = -st.skirt_height - 0.1
            l_in_bot, w_in_bot, r_in_bot = rect_in_at(z_in_bot)
            with BuildSketch(Plane.XY) as sk_in_top:
                RectangleRounded(l_inner, w_inner, radius=r_inner)
            with BuildSketch(Plane.XY.offset(z_in_bot)) as sk_in_bot:
                RectangleRounded(l_in_bot, w_in_bot, radius=r_in_bot)
            loft([sk_in_top.sketch, sk_in_bot.sketch], ruled=True, mode=Mode.SUBTRACT)
        else:
            with BuildSketch(Plane.XY):
                RectangleRounded(l_inner, w_inner, radius=r_inner)
            extrude(amount=-st.skirt_height, mode=Mode.SUBTRACT)

        if st.lead_in_chamfer > 0:
            if taper > 0:
                l_in_bot, w_in_bot, r_in_bot = rect_in_at(-st.skirt_height)
                l_in_ch, w_in_ch, r_in_ch = rect_in_at(-st.skirt_height + st.lead_in_chamfer)
                ch_ext = st.lead_in_chamfer + 0.1
                with BuildSketch(Plane.XY.offset(-st.skirt_height - 0.1)) as ch_bot:
                    RectangleRounded(
                        l_in_bot + 2 * ch_ext,
                        w_in_bot + 2 * ch_ext,
                        radius=r_in_bot + ch_ext,
                    )
                with BuildSketch(Plane.XY.offset(-st.skirt_height + st.lead_in_chamfer)) as ch_top:
                    RectangleRounded(l_in_ch, w_in_ch, radius=r_in_ch)
                loft([ch_bot.sketch, ch_top.sketch], ruled=True, mode=Mode.SUBTRACT)
            else:
                with BuildSketch(Plane.XY.offset(-st.skirt_height)):
                    RectangleRounded(l_inner + 2 * st.lead_in_chamfer, w_inner + 2 * st.lead_in_chamfer, radius=r_inner + st.lead_in_chamfer)
                    RectangleRounded(l_inner, w_inner, radius=r_inner, mode=Mode.SUBTRACT)
                extrude(amount=st.lead_in_chamfer, mode=Mode.SUBTRACT)

        if bead.enabled and bead.depth > 0:
            bead_flat_height = bead.height * 0.4
            z_b0 = -bead.offset
            z_b1 = -bead.offset - bead_flat_height
            z_b2 = -bead.offset - bead.height

            if taper > 0:
                l0, w0, r0 = rect_in_at(z_b0)
                l1, w1, r1 = rect_in_at(z_b1)
                l2, w2, r2 = rect_in_at(z_b2)
                with BuildSketch(Plane.XY.offset(z_b0)) as s0:
                    RectangleRounded(l0 + 0.2, w0 + 0.2, radius=r0)
                    RectangleRounded(l0 - 2 * bead.depth, w0 - 2 * bead.depth, radius=max(1.0, r0 - bead.depth), mode=Mode.SUBTRACT)
                with BuildSketch(Plane.XY.offset(z_b1)) as s1:
                    RectangleRounded(l1 + 0.2, w1 + 0.2, radius=r1)
                    RectangleRounded(l1 - 2 * bead.depth, w1 - 2 * bead.depth, radius=max(1.0, r1 - bead.depth), mode=Mode.SUBTRACT)
                loft([s0.sketch, s1.sketch], ruled=True, mode=Mode.ADD)
                with BuildSketch(Plane.XY.offset(z_b1)) as s1b:
                    RectangleRounded(l1 + 0.2, w1 + 0.2, radius=r1)
                    RectangleRounded(l1 - 2 * bead.depth, w1 - 2 * bead.depth, radius=max(1.0, r1 - bead.depth), mode=Mode.SUBTRACT)
                with BuildSketch(Plane.XY.offset(z_b2)) as s2:
                    RectangleRounded(l2 + 0.2, w2 + 0.2, radius=r2)
                    RectangleRounded(l2, w2, radius=r2, mode=Mode.SUBTRACT)
                loft([s1b.sketch, s2.sketch], ruled=True, mode=Mode.ADD)
            else:
                l_bead = l_inner - 2 * bead.depth
                w_bead = w_inner - 2 * bead.depth
                r_bead = max(1.0, r_inner - bead.depth)

                with BuildSketch(Plane.XY.offset(z_b0)):
                    RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                    RectangleRounded(l_bead, w_bead, radius=r_bead, mode=Mode.SUBTRACT)
                extrude(amount=-bead_flat_height, mode=Mode.ADD)

                with BuildSketch(Plane.XY.offset(z_b1)) as s1:
                    RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                    RectangleRounded(l_bead, w_bead, radius=r_bead, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.XY.offset(z_b2)) as s2:
                    RectangleRounded(l_inner + 0.2, w_inner + 0.2, radius=r_inner)
                    RectangleRounded(l_inner, w_inner, radius=r_inner, mode=Mode.SUBTRACT)
                loft([s1.sketch, s2.sketch], ruled=True, mode=Mode.ADD)
        elif c.friction_ribs:
            for z_rib in [-3.0, -6.5]:
                if abs(z_rib) + 0.6 < st.skirt_height - st.lead_in_chamfer:
                    lr, wr, rr = rect_in_at(z_rib)
                    with BuildSketch(Plane.XY.offset(z_rib - 0.4)):
                        RectangleRounded(lr + 0.2, wr + 0.2, radius=rr)
                        RectangleRounded(lr - 0.6, wr - 0.6, radius=max(1.0, rr - 0.3), mode=Mode.SUBTRACT)
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

        if tab is not None:
            is_corner = (st.pull_tab_location == "corner") or (st.pull_tab_location == "auto")
            eff_gusset_depth = min(tab.gusset_depth, max(0.0, st.skirt_height - st.lead_in_chamfer))
            wall_mid = st.skirt_wall_thickness * 0.5
            rect_trim_solid = None
            if eff_gusset_depth > 0.2:
                z_cut_bot = -eff_gusset_depth - 1.0
                z_cut_top = 1.0
                with BuildPart() as g_trim:
                    if taper > 0:
                        l_in_gbot, w_in_gbot, r_in_gbot = rect_in_at(z_cut_bot)
                        l_in_gtop, w_in_gtop, r_in_gtop = rect_in_at(z_cut_top)
                        with BuildSketch(Plane.XY.offset(z_cut_bot)) as g_cut_bot:
                            RectangleRounded(l_in_gbot + 2 * wall_mid, w_in_gbot + 2 * wall_mid, radius=r_in_gbot + wall_mid)
                        with BuildSketch(Plane.XY.offset(z_cut_top)) as g_cut_top:
                            RectangleRounded(l_in_gtop + 2 * wall_mid, w_in_gtop + 2 * wall_mid, radius=r_in_gtop + wall_mid)
                        loft([g_cut_bot.sketch, g_cut_top.sketch], ruled=True)
                    else:
                        with BuildSketch(Plane.XY.offset(z_cut_bot)):
                            RectangleRounded(l_inner + 2 * wall_mid, w_inner + 2 * wall_mid, radius=r_inner + wall_mid)
                        extrude(amount=eff_gusset_depth + 2.0)
                rect_trim_solid = g_trim.part

            rect_bevel = min(st.outer_fillet, st.skirt_wall_thickness * 0.7) if st.outer_fillet > 0 else 0.0
            if is_corner:
                corner_cx = l_outer / 2.0 - r_outer
                corner_cy = w_outer / 2.0 - r_outer
                tab_loc = Location((corner_cx, corner_cy, 0), (0, 0, 45.0))
                tab_add, tab_cut = build_pull_tab(
                    tab,
                    x_attach=r_outer,
                    top_thickness=st.top_thickness,
                    max_gusset_depth=eff_gusset_depth,
                    outer_bevel=rect_bevel,
                    rim_radius=r_outer,
                    trim_solid=rect_trim_solid,
                    print_orientation=False,
                    location=tab_loc,
                )
            else:
                tab_add, tab_cut = build_pull_tab(
                    tab,
                    x_attach=l_outer / 2.0,
                    top_thickness=st.top_thickness,
                    max_gusset_depth=eff_gusset_depth,
                    outer_bevel=rect_bevel,
                    rim_radius=None,
                    trim_solid=rect_trim_solid,
                    print_orientation=False,
                )
            add(tab_add, mode=Mode.ADD)
            if tab_cut is not None:
                add(tab_cut, mode=Mode.SUBTRACT)

        if flex.enabled:
            slot_h = st.skirt_height - 1.5
            slot_root_r = flex.slot_width
            slot_depth = st.skirt_wall_thickness * 4 + taper * 2

            flat_x_half = (l_inner - 2 * r_inner) / 2.0
            if flat_x_half > 10.0 and flex.rect_slots_long_side > 0:
                step_x = (2 * flat_x_half * 0.7) / max(1, flex.rect_slots_long_side)
                x_offsets = [-flat_x_half * 0.35 + i * step_x for i in range(flex.rect_slots_long_side)]
                for y_sign in [-1, 1]:
                    y_pos = y_sign * (w_outer / 2.0 - taper / 2.0)
                    for x_pos in x_offsets:
                        with Locations((x_pos, y_pos, -st.skirt_height + slot_h / 2.0)):
                            Box(flex.slot_width, slot_depth, slot_h, mode=Mode.SUBTRACT)
                        with Locations((x_pos, y_pos, -st.skirt_height + slot_h)):
                            Cylinder(radius=slot_root_r, height=slot_depth, rotation=(90, 0, 0), mode=Mode.SUBTRACT)

            flat_y_half = (w_inner - 2 * r_inner) / 2.0
            if flat_y_half > 10.0 and flex.rect_slots_short_side > 0:
                step_y = (2 * flat_y_half * 0.7) / max(1, flex.rect_slots_short_side)
                y_offsets = [-flat_y_half * 0.35 + i * step_y for i in range(flex.rect_slots_short_side)]
                for x_sign in [-1, 1]:
                    x_pos = x_sign * (l_outer / 2.0 - taper / 2.0)
                    for y_pos in y_offsets:
                        with Locations((x_pos, y_pos, -st.skirt_height + slot_h / 2.0)):
                            Box(slot_depth, flex.slot_width, slot_h, mode=Mode.SUBTRACT)
                        with Locations((x_pos, y_pos, -st.skirt_height + slot_h)):
                            Cylinder(radius=slot_root_r, height=slot_depth, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

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
        lid = build_round_lid(p)
    elif shape_lower in ("rectangular", "square", "rect"):
        lid = build_rectangular_lid(p)
    else:
        raise ValueError(f"Unsupported shape: {p.core.shape}. Choose 'round' or 'rectangular'.")

    # Orient upside-down for 3D printing and rest the lowest surface flush on Z = 0
    lid = lid.rotate(Axis.X, 180)
    return lid.translate((0, 0, -lid.bounding_box().min.Z))


if __name__ == "__main__":
    from utils.runner import run_model

    params = ContainerLidParams()
    lid = create_container_lid(params)
    run_model(lid, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
