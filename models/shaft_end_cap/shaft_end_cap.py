"""
Parametric Shaft End Cap (build123d Model)

Designed for cylindrical rods/shafts (e.g. 1/2" rod shelving used for filament spool storage)
to retain spools and prevent them from sliding off.

Features:
- Parametric shaft diameter and 3D-print press-fit clearance.
- Customizable collar sleeve length and wall thickness.
- Wide retention flange with customizable diameter, thickness, and fillet transition.
- Multiple selectable end cap styles:
    * 'dome' (or 'semi-spherical'): smooth spherical dome for bump protection.
    * 'flat': clean flat face with filleted or chamfered outer edge.
    * 'chamfer': conical beveled face.
    * 'round': flat face with prominent rounded front rim.
- Internal lead-in chamfer for easy push-on installation.
- Optional air-relief vent hole to prevent trapped air resistance during press-fit.
- Optional perimeter grip flutes/grooves for easy twist-off removal.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

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
    """Shaft / bore and collar sleeve dimensions."""

    shaft_diameter: float = param(
        12.0,
        desc="Nominal shaft/rod diameter (12.7 mm = 1/2 in)",
        unit="mm", min=4.0, max=60.0, step=0.1,
    )
    fit_clearance: float = param(
        0.2,
        desc="Diametral press-fit clearance added to bore",
        unit="mm", min=-0.5, max=1.0, step=0.05,
    )
    collar_length: float = param(
        18.0,
        desc="Sleeve length pressing onto shaft",
        unit="mm", min=5.0, max=60.0, step=1.0,
    )
    collar_wall_thickness: float = param(
        2.4,
        desc="Collar cylinder wall thickness",
        unit="mm", min=1.2, max=8.0, step=0.2,
    )
    lead_in_chamfer: float = param(
        1.0,
        desc="Internal mouth bevel for easy push-on",
        unit="mm", min=0.0, max=3.0, step=0.1,
    )


@dataclass
class FlangeParams:
    """Retaining flange (spool stop) dimensions."""

    diameter: float = param(
        40.0,
        desc="Outer diameter of retaining flange",
        unit="mm", min=12.0, max=100.0, step=1.0,
    )
    thickness: float = param(
        4.0,
        desc="Axial thickness of flange disc",
        unit="mm", min=1.5, max=12.0, step=0.5,
    )
    fillet: float = param(
        2.0,
        desc="Stress-relief fillet between collar and flange",
        unit="mm", min=0.0, max=8.0, step=0.2,
    )
    front_radius: float = param(
        2.0,
        desc="Front outer rim fillet (0 = crisp edge)",
        unit="mm", min=0.0, max=8.0, step=0.2, when={"cap.style": ["round", "flat"]},
    )
    rear_radius: float = param(
        2.0,
        desc="Rear outer rim fillet (0 = crisp edge)",
        unit="mm", min=0.0, max=8.0, step=0.2,
    )


@dataclass
class CapTipParams:
    """End cap tip style & geometry."""

    style: Literal["round", "dome", "flat", "chamfer"] = param(
        "round",
        desc="End cap tip profile",
    )
    dome_height: Optional[float] = param(
        0.0,
        desc="Height above flange (0 / Auto = full hemisphere)",
        unit="mm", min=0.0, max=40.0, step=0.5, when={"style": "dome"},
    )
    chamfer_length: float = param(
        2.5,
        desc="Axial length of 45° bevel",
        unit="mm", min=0.5, max=15.0, step=0.5, when={"style": "chamfer"},
    )


@dataclass
class VentHoleParams:
    """Coaxial air-relief through-hole."""

    enabled: bool = param(
        False,
        desc="Cut coaxial air-relief through-hole",
    )
    diameter: float = param(
        2.0,
        desc="Air-relief vent hole diameter",
        unit="mm", min=1.0, max=10.0, step=0.2,
    )


@dataclass
class VentChannelParams:
    """Internal axial air-relief vent channel along collar bore."""

    enabled: bool = param(
        True,
        desc="Cut invisible internal axial vent channel",
    )
    width: float = param(
        1.0,
        desc="Channel width along collar bore",
        unit="mm", min=0.4, max=4.0, step=0.1,
    )
    depth: float = param(
        0.6,
        desc="Radial depth into collar wall",
        unit="mm", min=0.2, max=2.0, step=0.1,
    )


@dataclass
class GripGroovesParams:
    """Perimeter scalloped finger grip grooves."""

    enabled: bool = param(
        False,
        desc="Add scalloped perimeter grip grooves",
    )
    count: int = param(
        12,
        desc="Number of grip grooves around perimeter",
        min=4, max=36, step=1,
    )
    radius: float = param(
        1.2,
        desc="Scalloped groove cutter radius",
        unit="mm", min=0.5, max=5.0, step=0.1,
    )


@default_preset("12 mm Rod Cap", desc="12 mm metric shaft end cap with rounded flange")
@dataclass
class ShaftEndCapParams:
    """Parameters for the parametric shaft end cap."""

    core: CoreParams = group(CoreParams)
    flange: FlangeParams = group(FlangeParams)
    cap: CapTipParams = group(CapTipParams)
    vent_hole: VentHoleParams = group(VentHoleParams)
    vent_channel: VentChannelParams = group(VentChannelParams)
    grip_grooves: GripGroovesParams = group(GripGroovesParams)

    @property
    def bore_radius(self) -> float:
        """Internal bore radius including fit clearance."""
        return (self.core.shaft_diameter + self.core.fit_clearance) / 2.0

    @property
    def collar_outer_radius(self) -> float:
        """Outer radius of the collar sleeve."""
        return self.bore_radius + self.core.collar_wall_thickness

    @property
    def flange_radius(self) -> float:
        """Outer radius of the retention flange."""
        return self.flange.diameter / 2.0

    @property
    def effective_dome_height(self) -> float:
        """Resolved dome height above the front face of the flange."""
        if self.cap.dome_height is not None and self.cap.dome_height > 0.0:
            return self.cap.dome_height
        return self.flange_radius


def create_shaft_end_cap(params: ShaftEndCapParams) -> Part:
    """Generates a parametric shaft end cap solid body."""
    core = params.core
    flange = params.flange
    tip = params.cap

    # Input validation
    if core.shaft_diameter <= 0:
        raise ValueError(f"shaft_diameter must be positive, got {core.shaft_diameter}")
    if core.collar_length <= 0:
        raise ValueError(f"collar_length must be positive, got {core.collar_length}")
    if flange.diameter < 2.0 * params.collar_outer_radius:
        raise ValueError(
            f"flange.diameter ({flange.diameter}mm) must be >= collar outer diameter "
            f"({2.0 * params.collar_outer_radius:.2f}mm)"
        )
    if flange.thickness <= 0:
        raise ValueError(f"flange.thickness must be positive, got {flange.thickness}")

    r_bore = params.bore_radius
    r_collar = params.collar_outer_radius
    r_flange = params.flange_radius
    l_collar = core.collar_length
    t_flange = flange.thickness
    z_flange_front = l_collar + t_flange
    style = tip.style.lower().strip()

    with BuildPart() as cap:
        # 1. Base Collar Sleeve (Z = 0 to l_collar)
        Cylinder(
            radius=r_collar,
            height=l_collar,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        # 2. Retaining Flange Disc (Z = l_collar to z_flange_front)
        with Locations((0, 0, l_collar)):
            Cylinder(
                radius=r_flange,
                height=t_flange,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # 3. Structural Fillet between collar outer diameter and flange underside
        if flange.fillet > 0 and (r_flange - r_collar) > flange.fillet:
            collar_flange_edges = cap.edges().filter_by(
                lambda e: e.geom_type == GeomType.CIRCLE
                and abs(e.center().Z - l_collar) < 1e-2
                and abs(e.radius - r_collar) < 1e-2
            )
            if collar_flange_edges:
                fillet(collar_flange_edges, radius=flange.fillet)

        # 4. Cap Style Feature (extending forward from Z = z_flange_front)
        if style in ("dome", "semi-spherical", "spherical", "hemisphere"):
            h_dome = params.effective_dome_height
            # R^2 = r_flange^2 + (R - h_dome)^2  =>  R = (r_flange^2 + h_dome^2) / (2 * h_dome)
            R = (r_flange**2 + h_dome**2) / (2.0 * h_dome)
            z_sphere_center = z_flange_front + h_dome - R

            with BuildPart() as dome_builder:
                with Locations((0, 0, z_sphere_center)):
                    Sphere(radius=R)
                split(bisect_by=Plane.XY.offset(z_flange_front), keep=Keep.TOP)

                if h_dome < r_flange - 1e-4:
                    with Locations((0, 0, z_flange_front)):
                        Cylinder(
                            radius=r_flange,
                            height=h_dome + 1.0,
                            align=(Align.CENTER, Align.CENTER, Align.MIN),
                            mode=Mode.INTERSECT,
                        )
            add(dome_builder.part)

        elif style in ("chamfer", "cone", "tapered"):
            c_len = min(tip.chamfer_length, r_flange - 1.0)
            if c_len > 0:
                with Locations((0, 0, z_flange_front)):
                    Cone(
                        bottom_radius=r_flange,
                        top_radius=r_flange - c_len,
                        height=c_len,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.ADD,
                    )

        elif style in ("round", "flat"):
            if flange.front_radius > 0:
                front_rim_edges = cap.edges().filter_by(
                    lambda e: e.geom_type == GeomType.CIRCLE
                    and abs(e.center().Z - z_flange_front) < 1e-2
                    and abs(e.radius - r_flange) < 1e-2
                )
                r_front = min(flange.front_radius, t_flange - 0.2)
                if front_rim_edges and r_front > 0:
                    fillet(front_rim_edges, radius=r_front)
        else:
            raise ValueError(
                f"Unknown cap.style: '{tip.style}'. Supported styles are: "
                f"'dome', 'flat', 'chamfer', 'round'"
            )

        # 5. Flange Rear Rim Edge Fillet (Collar / Spool side) - applied across all styles
        if flange.rear_radius > 0:
            under_rim_edges = cap.edges().filter_by(
                lambda e: e.geom_type == GeomType.CIRCLE
                and abs(e.center().Z - l_collar) < 1e-2
                and abs(e.radius - r_flange) < 1e-2
            )
            front_r = flange.front_radius if style in ("round", "flat") else 0.0
            max_rear_r = min(t_flange - front_r - 0.1, r_flange - r_collar - flange.fillet - 0.1)
            r_rear = min(flange.rear_radius, max_rear_r)
            if under_rim_edges and r_rear > 0:
                fillet(under_rim_edges, radius=r_rear)

        # 6. Optional Scalloped Grip Grooves around Flange Perimeter
        if params.grip_grooves.enabled and params.grip_grooves.count > 0 and params.grip_grooves.radius > 0:
            with PolarLocations(radius=r_flange, count=params.grip_grooves.count):
                Cylinder(
                    radius=params.grip_grooves.radius,
                    height=t_flange * 3.0,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                    mode=Mode.SUBTRACT,
                )

        # 7. Internal Shaft Bore (Z = 0 to l_collar)
        with Locations((0, 0, 0)):
            Cylinder(
                radius=r_bore,
                height=l_collar,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # 8. Lead-In Chamfer at Collar Bore Mouth (Z = 0)
        if core.lead_in_chamfer > 0 and core.lead_in_chamfer < core.collar_wall_thickness:
            mouth_edges = cap.edges().filter_by(
                lambda e: e.geom_type == GeomType.CIRCLE
                and abs(e.center().Z) < 1e-2
                and abs(e.radius - r_bore) < 1e-2
            )
            if mouth_edges:
                chamfer(mouth_edges, length=core.lead_in_chamfer)

        # 9. Coaxial Air-Relief Vent Hole (Z = 0 through full top of cap, optional)
        if params.vent_hole.enabled and params.vent_hole.diameter > 0:
            r_vent = params.vent_hole.diameter / 2.0
            with Locations((0, 0, l_collar - 1.0)):
                Cylinder(
                    radius=r_vent,
                    height=t_flange + params.effective_dome_height + 10.0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

        # 10. Internal Axial Vent Channel along Collar Bore Wall (Invisible from outside)
        if params.vent_channel.enabled and params.vent_channel.width > 0.0 and params.vent_channel.depth > 0.0:
            with Locations((r_bore, 0, 0)):
                Box(
                    params.vent_channel.depth * 2.0,
                    params.vent_channel.width,
                    l_collar * 1.01,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    assert cap.part is not None, "Shaft end cap generation failed"
    return cap.part


def export_filename(params: ShaftEndCapParams) -> str:
    """Return standardized lowercase filename stem (without extension) for exports."""
    safe_style = params.cap.style.lower().replace(" ", "_")
    return f"shaft_end_cap_{params.core.shaft_diameter:.1f}mm_{safe_style}"


if __name__ == "__main__":
    from utils.runner import run_model

    # Generates model using the parameters configured in ShaftEndCapParams
    params = ShaftEndCapParams()
    cap_part = create_shaft_end_cap(params)
    run_model(cap_part, export_filename(params), stl=EXPORT_STL, step=EXPORT_STEP)
