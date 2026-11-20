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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from build123d import *

# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False                # Save .stl file on execution (default: False)
EXPORT_STEP: bool = False               # Save .step file on execution (default: False)
OUTPUT_DIR: str = "exports"             # Output folder (relative to this script's directory)


@dataclass
class CoreParams:
    """Shaft / bore and collar sleeve dimensions."""

    shaft_diameter: float = 12.0           # Nominal shaft/rod diameter in mm (12.7 mm = 1/2 inch)
    fit_clearance: float = 0.2             # Diametral press-fit clearance in mm (bore dia = shaft_diameter + fit_clearance)
    collar_length: float = 18.0            # Length of collar sleeve pressing onto shaft (mm)
    collar_wall_thickness: float = 2.4     # Wall thickness of collar cylinder (mm)
    lead_in_chamfer: float = 1.0           # Internal chamfer at collar mouth for effortless sliding onto rod (mm)


@dataclass
class FlangeParams:
    """Retaining flange (spool stop) dimensions."""

    diameter: float = 40.0                 # Outer diameter of retaining flange (mm)
    thickness: float = 4.0                 # Axial thickness of flange disc (mm)
    fillet: float = 2.0                    # Stress-relief fillet radius between collar body and flange underside (mm)
    front_radius: float = 2.0              # Outer rim fillet radius on front / tip side of flange (mm, 0.0 for crisp edge)
    rear_radius: float = 2.0               # Outer rim fillet radius on rear / collar side of flange (mm, 0.0 for crisp edge)


@dataclass
class CapTipParams:
    """End cap tip style & geometry."""

    style: Literal["round", "dome", "flat", "chamfer"] = "round"  # End cap style
    dome_height: Optional[float] = 0.0     # Height of dome above flange (mm). None/0 defaults to full hemisphere
    chamfer_length: float = 2.5            # Axial length of 45-deg bevel when style is 'chamfer' (mm)


@dataclass
class VentHoleParams:
    """Coaxial air-relief through-hole."""

    enabled: bool = False                  # Enable coaxial air-relief through-hole
    diameter: float = 2.0                  # Coaxial air-relief vent hole diameter in mm


@dataclass
class VentChannelParams:
    """Internal axial air-relief vent channel along collar bore."""

    enabled: bool = True                   # Enable invisible internal axial vent channel
    width: float = 1.0                     # Width of internal axial vent channel along collar bore in mm
    depth: float = 0.6                     # Radial depth of internal vent channel into collar wall in mm


@dataclass
class GripGroovesParams:
    """Perimeter scalloped finger grip grooves."""

    enabled: bool = False                  # Enable perimeter scalloped finger grip grooves
    count: int = 12                        # Number of perimeter grip grooves for finger twisting
    radius: float = 1.2                    # Radius of scalloped finger grip cuts around flange perimeter (mm)


@dataclass
class ShaftEndCapParams:
    """Parameters for the parametric shaft end cap."""

    core: CoreParams = field(default_factory=CoreParams)
    flange: FlangeParams = field(default_factory=FlangeParams)
    cap: CapTipParams = field(default_factory=CapTipParams)
    vent_hole: VentHoleParams = field(default_factory=VentHoleParams)
    vent_channel: VentChannelParams = field(default_factory=VentChannelParams)
    grip_grooves: GripGroovesParams = field(default_factory=GripGroovesParams)

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


if __name__ == "__main__":
    # Generates model using the parameters configured in ShaftEndCapParams
    params = ShaftEndCapParams()
    cap_part = create_shaft_end_cap(params)

    # Standardized exports to the exports/ directory alongside this script
    if EXPORT_STEP or EXPORT_STL:
        exports_path = Path(__file__).resolve().parent / OUTPUT_DIR
        exports_path.mkdir(parents=True, exist_ok=True)

        safe_style = params.cap.style.lower().replace(" ", "_")
        stem = f"shaft_end_cap_{params.core.shaft_diameter:.1f}mm_{safe_style}"

        if EXPORT_STL:
            stl_file = exports_path / f"{stem}.stl"
            export_stl(cap_part, str(stl_file))
            print(f"Exported STL:  {stl_file}")

        if EXPORT_STEP:
            step_file = exports_path / f"{stem}.step"
            export_step(cap_part, str(step_file))
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

    show(cap_part)
