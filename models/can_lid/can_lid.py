"""
Parametric Can Lid Generator (build123d)

Generates reusable snap-on storage lids for rolled-rim aluminum beverage cans
(soda, sparkling water, tallboys, slim cans) and steel food/soup cans. Supports
both flexible filaments (TPU stretch-fit) and rigid plastics (PLA / PETG / PCTG
with compliant cantilever flexure slots).

Features:
- Circular rolled-rim retention geometry with under-rim snap bead
- Optional inner splash-guard seal ring for food cans
- Configurable ergonomic pull tab with traction grooves and optional hanging hole
- Rigid-plastic flexure relief slots with circular strain-relief roots
- Optional top stacking rim and quick-print fit-check test ring mode
- Built-in presets for standard beverage and food/soup cans in `presets.json`
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from build123d import *

try:
    from components.pull_tab import PullTabParams, build_pull_tab, pull_tab_angular_clearance
    from utils.params import default_preset, group, param
except ImportError:
    import sys

    for _p in Path(__file__).resolve().parents:
        if (_p / "utils").is_dir():
            sys.path.insert(0, str(_p))
            break
    from components.pull_tab import PullTabParams, build_pull_tab, pull_tab_angular_clearance
    from utils.params import default_preset, group, param

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False      # Save .stl to repo-root exports/ (default: False)
EXPORT_STEP: bool = False     # Save .step to repo-root exports/ (default: False)


@dataclass
class CoreParams:
    """Can rim dimensions and fit tolerance."""

    rim_diameter: float = param(
        54.0,
        desc="Outer diameter of rolled can rim (12/16 oz soda can ≈ 54 mm)",
        unit="mm", min=35.0, max=180.0, step=0.2,
    )
    rim_height: float = param(
        3.0,
        desc="Vertical height of the rolled can rim lip",
        unit="mm", min=1.5, max=8.0, step=0.1,
    )
    rim_thickness: float = param(
        1.8,
        desc="Radial thickness of the rolled can rim",
        unit="mm", min=1.0, max=5.0, step=0.1, when={"inner_seal.enabled": True},
    )
    fit_tolerance: float = param(
        -0.5,
        desc="Added to rim diameter (negative = tighter TPU stretch, positive = rigid clearance)",
        unit="mm", min=-1.5, max=1.5, step=0.05,
    )
    test_ring: bool = param(
        False,
        desc="Hollow center for a quick fit-check test ring",
    )


@dataclass
class LidStructureParams:
    """Lid top plate and outer skirt dimensions."""

    top_thickness: float = param(
        1.8,
        desc="Solid top plate thickness",
        unit="mm", min=0.8, max=5.0, step=0.2,
    )
    skirt_height: float = param(
        6.0,
        desc="Height of outer skirt above inner lid floor",
        unit="mm", min=4.5, max=20.0, step=0.5,
    )
    skirt_wall_thickness: float = param(
        1.8,
        desc="Outer skirt side wall thickness",
        unit="mm", min=1.0, max=4.5, step=0.2,
    )
    outer_bevel: float = param(
        1.0,
        desc="Outer perimeter chamfer on the flat face",
        unit="mm", min=0.0, max=3.0, step=0.2,
    )
    lead_in_chamfer: float = param(
        0.8,
        desc="Inside rim bevel for smooth mounting",
        unit="mm", min=0.0, max=2.5, step=0.1,
    )


@dataclass
class SnapBeadParams:
    """Inward retention snap bead hooking underneath the rolled can rim."""

    enabled: bool = param(
        True,
        desc="Add inward retention ridge under the can rim",
    )
    depth: float = param(
        0.8,
        desc="Inward radial protrusion under the rim",
        unit="mm", min=0.1, max=2.0, step=0.05,
    )
    height: float = param(
        1.6,
        desc="Vertical height of the retention bead profile",
        unit="mm", min=0.6, max=4.0, step=0.1,
    )
    offset: Optional[float] = param(
        None,
        desc="Distance from inner lid floor (Auto = rim height + 0.2)",
        unit="mm", min=1.0, max=12.0, step=0.1,
    )


@dataclass
class InnerSealParams:
    """Optional inner splash-guard ring seating inside the rolled can rim."""

    enabled: bool = param(
        False,
        desc="Add inner countersink splash ring",
    )
    height: float = param(
        2.5,
        desc="Depth inside the can rim countersink",
        unit="mm", min=0.8, max=8.0, step=0.2,
    )
    thickness: float = param(
        1.2,
        desc="Seal ring wall thickness",
        unit="mm", min=0.6, max=3.0, step=0.1,
    )
    clearance: float = param(
        0.4,
        desc="Radial gap between inner rim wall and seal ring",
        unit="mm", min=0.0, max=2.5, step=0.1,
    )


@dataclass
class FlexSlotsParams:
    """Compliant cantilever flexure slots for rigid filaments (PLA / PETG / PCTG)."""

    enabled: bool = param(
        False,
        desc="Add vertical skirt relief slots for rigid plastics",
    )
    slot_width: float = param(
        1.4,
        desc="Vertical skirt relief cutout width",
        unit="mm", min=0.6, max=3.5, step=0.1,
    )
    slot_count: int = param(
        6,
        desc="Number of relief slots around the circumference",
        min=3, max=16, step=1,
    )


@dataclass
class StackingRimParams:
    """Raised top nesting rim for stacking cans."""

    enabled: bool = param(
        False,
        desc="Add raised stacking rim on top surface",
    )
    height: float = param(
        1.5,
        desc="Stacking rim height above top plate",
        unit="mm", min=0.5, max=4.0, step=0.2,
    )
    thickness: float = param(
        1.4,
        desc="Stacking rim wall thickness",
        unit="mm", min=0.8, max=3.5, step=0.2,
    )
    inset: float = param(
        3.5,
        desc="Inward distance from outer lid edge",
        unit="mm", min=1.5, max=12.0, step=0.5,
    )


@default_preset(
    "Beverage Can 12/16 oz (202 End)",
    desc="54 mm rim standard soda, beer, and sparkling water cans (TPU stretch-fit)",
)
@dataclass
class CanLidParams:
    """Parameters for rolled-rim beverage and food can lid generation."""

    core: CoreParams = group(CoreParams)
    structure: LidStructureParams = group(LidStructureParams, label="Lid Structure")
    snap_bead: SnapBeadParams = group(SnapBeadParams)
    inner_seal: InnerSealParams = group(InnerSealParams)
    pull_tab: PullTabParams = group(PullTabParams)
    flex_slots: FlexSlotsParams = group(FlexSlotsParams)
    stacking_rim: StackingRimParams = group(StackingRimParams)


def export_filename(params: CanLidParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    dim_str = f"{params.core.rim_diameter:g}mm"
    variant = "rigid" if params.flex_slots.enabled else "tpu"
    if params.core.test_ring:
        variant = f"{variant}_test_ring"
    return f"can_lid_{dim_str}_{variant}"


def create_can_lid(params: CanLidParams) -> Solid:
    """Generate a parametric rolled-rim can lid solid."""
    c = params.core
    st = params.structure
    bead = params.snap_bead
    seal = params.inner_seal
    tab = params.pull_tab
    flex = params.flex_slots
    stack = params.stacking_rim

    r_inner = (c.rim_diameter + c.fit_tolerance) / 2.0
    if r_inner <= 5.0:
        raise ValueError("Effective inner radius must be greater than 5 mm.")
    r_outer = r_inner + st.skirt_wall_thickness

    eff_lead_in = min(
        st.lead_in_chamfer,
        st.skirt_wall_thickness * 0.75,
        st.skirt_height * 0.4,
    )
    eff_outer_bevel = min(
        st.outer_bevel,
        st.top_thickness * 0.75,
        st.skirt_wall_thickness * 0.8,
    )

    r_seal_outer = r_inner - c.rim_thickness - seal.clearance
    r_seal_inner = r_seal_outer - seal.thickness
    has_seal = seal.enabled and (r_seal_inner > 2.0) and (seal.height > 0.2)

    r_stack_outer = r_outer - stack.inset
    r_stack_inner = r_stack_outer - stack.thickness
    has_stack = (
        stack.enabled
        and (r_stack_inner > 2.0)
        and (r_stack_outer < (r_outer - eff_outer_bevel - 0.1))
    )

    # Build half-cross-section polygon on Plane.XZ to revolve around Axis.Z.
    # Print orientation: Z = 0 is the flat outer face on the build plate,
    # Z = z_deck is the inner lid floor, and the skirt rises to Z = z_rim.
    z_deck = st.top_thickness
    z_rim = z_deck + st.skirt_height
    pts: list[tuple[float, float]] = [(0.0, z_deck)]

    if has_seal:
        seal_bevel = min(0.4, seal.thickness * 0.4, seal.height * 0.4)
        pts.extend([
            (r_seal_inner, z_deck),
            (r_seal_inner, z_deck + seal.height - seal_bevel),
            (r_seal_inner + seal_bevel, z_deck + seal.height),
            (r_seal_outer - seal_bevel, z_deck + seal.height),
            (r_seal_outer, z_deck + seal.height - seal_bevel),
            (r_seal_outer, z_deck),
        ])

    pts.append((r_inner, z_deck))

    bead_offset = bead.offset if bead.offset is not None else (c.rim_height + 0.2)
    z_skirt_usable = z_rim - eff_lead_in - 0.1
    if bead.enabled and bead.depth > 0:
        z_b0 = z_deck + bead_offset
        z_b3 = z_b0 + bead.height
        if z_b0 > z_deck + 0.2 and z_b3 < z_skirt_usable:
            eff_bead_depth = min(bead.depth, r_inner - 2.0)
            z_b1 = z_b0 + bead.height * 0.25
            z_b2 = z_b0 + bead.height * 0.55
            pts.extend([
                (r_inner, z_b0),
                (r_inner - eff_bead_depth, z_b1),
                (r_inner - eff_bead_depth, z_b2),
                (r_inner, z_b3),
            ])

    if eff_lead_in > 0:
        pts.extend([
            (r_inner, z_rim - eff_lead_in),
            (r_inner + eff_lead_in, z_rim),
        ])
    else:
        pts.append((r_inner, z_rim))

    pts.append((r_outer, z_rim))

    if eff_outer_bevel > 0:
        pts.extend([
            (r_outer, eff_outer_bevel),
            (r_outer - eff_outer_bevel, 0.0),
        ])
    else:
        pts.append((r_outer, 0.0))

    if has_stack:
        pts.extend([
            (r_stack_outer, 0.0),
            (r_stack_outer, -stack.height),
            (r_stack_inner, -stack.height),
            (r_stack_inner, 0.0),
        ])

    pts.extend([
        (0.0, 0.0),
        (0.0, z_deck),
    ])

    with BuildPart() as lid_part:
        with BuildSketch(Plane.XZ):
            Polygon(pts)
        revolve(axis=Axis.Z)

        if tab.enabled:
            tab_add, tab_cut = build_pull_tab(
                tab,
                x_attach=r_outer,
                top_thickness=st.top_thickness,
                max_gusset_depth=st.skirt_height - eff_lead_in - 0.5,
                outer_bevel=eff_outer_bevel,
                rim_radius=r_outer,
                trim_radius=r_inner + st.skirt_wall_thickness * 0.5,
                print_orientation=True,
            )
            insert(tab_add, mode=Mode.ADD)
            if tab_cut is not None:
                insert(tab_cut, mode=Mode.SUBTRACT)

        if flex.enabled and flex.slot_count > 0:
            slot_h = max(2.0, st.skirt_height - 1.5)
            slot_root_r = flex.slot_width * 0.8
            slot_radial_len = st.skirt_wall_thickness * 4.0
            slot_root_z = z_rim - slot_h
            tab_clear_deg = pull_tab_angular_clearance(tab, r_outer)
            for i in range(flex.slot_count):
                ang = i * (360.0 / flex.slot_count)
                if tab.enabled and (ang < tab_clear_deg or ang > 360.0 - tab_clear_deg):
                    continue
                with Locations(Rotation(0, 0, ang)):
                    with Locations((r_outer, 0.0, slot_root_z + slot_h / 2.0)):
                        Box(slot_radial_len, flex.slot_width, slot_h, mode=Mode.SUBTRACT)
                    with Locations((r_outer, 0.0, slot_root_z)):
                        Cylinder(
                            radius=slot_root_r,
                            height=slot_radial_len,
                            rotation=(0, 90, 0),
                            mode=Mode.SUBTRACT,
                        )

        if c.test_ring:
            gauge_inner_r = max(5.0, (r_seal_inner - 2.0) if has_seal else (r_inner - 5.0))
            with BuildSketch(Plane.XY):
                Circle(radius=gauge_inner_r)
            extrude(amount=(z_rim + stack.height) * 2.0, both=True, mode=Mode.SUBTRACT)

    assert lid_part.part is not None, "Failed to generate can lid"
    return lid_part.part


if __name__ == "__main__":
    from utils.runner import run_model

    params = CanLidParams()
    part = create_can_lid(params)
    run_model(part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
