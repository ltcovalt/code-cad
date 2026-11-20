"""
Parametric Magnetic Label Generator using build123d.

Features:
- Configurable dimensions: Auto-sized to text (+ padding) or fixed static width/height.
- Font customization: Font family, font size, and font style (regular, bold, italic, bold_italic).
- Text rendering modes:
    * 'embossed': Raised text protruding from the front surface.
    * 'debossed': Recessed/engraved text cut into the front surface.
    * 'flush': Flush inlay text with separate bodies for multi-color 3D printing (e.g. Bambu AMS).
- Press-fit magnet pockets:
    * Round magnets (e.g. 6x2mm, 6x3mm, 8x2mm, 10x2mm, etc.).
    * Auto-spaced along the width or manual magnet count/positions.
    * Calibrated press-fit clearance and sub-flush pocket depth.
    * Automatic plate thickness verification to guarantee solid floor behind magnets.
- Visual display: Integrated ocp_viewer / ocp_vscode viewer preview with contrasting part colors
  and semi-transparent magnets inside the pockets.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

# Handle local repo folder shadowing the installed build123d site-package
if os.path.isdir("build123d") and sys.path and sys.path[0] in ("", "."):
    sys.path.pop(0)

from build123d import *


def _get_viewer():
    """Lazily import ocp_viewer or ocp_vscode only when interactive preview is requested."""
    try:
        from ocp_viewer import Camera, set_defaults, show
        return Camera, set_defaults, show
    except ImportError:
        try:
            from ocp_vscode import Camera, set_defaults, show
            return Camera, set_defaults, show
        except ImportError:
            return None


# ==============================================================================
# Standardized Export Configuration
# ==============================================================================
EXPORT_STL: bool = False              # Save .stl files on execution (default: False)
EXPORT_STEP: bool = False             # Save .step files on execution (default: False)
OUTPUT_DIR: str = "exports"           # Output folder (relative to this script's directory)

# Optional batch generation list:
# Leave empty to generate/preview a single label defined by MagneticLabelParams defaults.
# Or populate with strings e.g. ["FASTENERS", "3D PRINTING"] to batch-generate multiple labels.
BATCH_LABELS: list[str | tuple[str, dict]] = []


# ==============================================================================
# PARAMETER DATA STRUCTURES & ENUMS
# ==============================================================================

class TextMode(str, Enum):
    EMBOSSED = "embossed"
    DEBOSSED = "debossed"
    FLUSH = "flush"

    @classmethod
    def from_str(cls, val: str) -> TextMode:
        norm = val.strip().lower()
        for member in cls:
            if member.value == norm:
                return member
        raise ValueError(f"Unknown TextMode: '{val}'. Expected one of: {[m.value for m in cls]}")


def _resolve_font_style(style_input: Union[str, FontStyle]) -> FontStyle:
    """Converts string name or FontStyle enum into build123d FontStyle."""
    if isinstance(style_input, FontStyle):
        return style_input
    norm = style_input.strip().lower()
    mapping = {
        "regular": FontStyle.REGULAR,
        "bold": FontStyle.BOLD,
        "italic": FontStyle.ITALIC,
        "bold_italic": FontStyle.BOLDITALIC,
        "bolditalic": FontStyle.BOLDITALIC,
    }
    if norm in mapping:
        return mapping[norm]
    raise ValueError(f"Unknown font style '{style_input}'. Expected one of {list(mapping.keys())}")


@dataclass
class TextParams:
    """Text content, typography, and rendering mode."""

    content: str = "FASTENERS"
    font_size: float = 12.0                # Font height in mm
    font: str = "Arial"                    # Font family (e.g. 'Arial', 'FreeSans', 'Helvetica')
    font_style: Literal["regular", "bold", "italic", "bold_italic"] = "bold"  # Font weight/slant
    align: Literal["center", "left", "right"] = "center"  # Horizontal text alignment
    offset_y: float = 0.0                  # Fine vertical offset adjustment in mm
    mode: Literal["embossed", "debossed", "flush"] = "embossed"  # Text rendering style
    depth: float = 1.2                     # Height of raised letters or depth of engraving (mm)


@dataclass
class SizingParams:
    """Plate dimensions and auto-sizing margins."""

    auto_size: bool = False                # Adaptive text sizing (True) or static dimensions (False)
    width: float = 100.0                   # Used when auto_size is False (mm)
    height: float = 16.0                   # Used when auto_size is False (mm)
    padding_x: float = 4.0                 # Margin around text in auto-size mode (mm)
    padding_y: float = 4.0                 # Margin around text in auto-size mode (mm)
    min_width: float = 30.0                # Minimum plate width limit (mm)
    min_height: float = 16.0               # Minimum plate height limit (mm)


@dataclass
class PlateParams:
    """Base plate thickness and edge styling."""

    base_thickness: float = 3.0            # Overall plate thickness (mm)
    corner_radius: float = 3.0             # Corner fillet radius (mm; 0 for square)
    top_chamfer: float = 0.6               # 45-degree bevel on front perimeter (mm; 0 to disable)
    min_floor_thickness: float = 0.8       # Minimum solid plastic floor thickness behind magnets (mm)


@dataclass
class BorderRimParams:
    """Optional raised border frame around front face."""

    enabled: bool = True                   # Enable raised border frame around face
    width: float = 1.2                     # Width of raised border frame (mm)


@dataclass
class MagnetParams:
    """Rear press-fit magnet pockets."""

    enabled: bool = True                   # Enable/disable rear magnet pockets
    diameter: float = 10.0                 # Nominal magnet diameter in mm
    thickness: float = 2.0                 # Nominal magnet thickness in mm
    clearance: float = 0.0                 # Press-fit diameter tolerance for 3D printing (mm)
    pocket_depth_offset: float = 0.2       # Extra depth allowance to keep magnets sub-flush (mm)
    count: Optional[int] = None            # Specific magnet count, or None for automatic spacing
    edge_margin: float = 8.0               # Distance from ends to magnet centers (mm)
    positions: Optional[List[Tuple[float, float]]] = None


@dataclass
class MagneticLabelParams:
    """Configuration parameters for the parametric magnetic label generator."""

    text: TextParams = field(default_factory=TextParams)
    sizing: SizingParams = field(default_factory=SizingParams)
    plate: PlateParams = field(default_factory=PlateParams)
    border: BorderRimParams = field(default_factory=BorderRimParams)
    magnets: MagnetParams = field(default_factory=MagnetParams)


@dataclass
class GeneratedLabel:
    """Holds the generated solid geometry and metadata."""
    base_part: Compound | Solid
    text_part: Optional[Compound | Solid]
    magnet_solids: List[Solid]
    actual_width: float
    actual_height: float
    actual_thickness: float
    magnet_positions: List[Tuple[float, float]]
    params: MagneticLabelParams


# ==============================================================================
# GEOMETRY GENERATOR
# ==============================================================================

def calculate_dimensions(params: MagneticLabelParams) -> Tuple[float, float, float]:
    """
    Computes effective width, height, and thickness of the label plate.
    Automatically factors in text bounding box (if auto_size is enabled)
    and enforces minimum floor thickness behind press-fit magnet pockets.
    """
    style = _resolve_font_style(params.text.font_style)

    # Calculate text bounding dimensions with exact geometric centering
    with BuildSketch() as probe:
        Text(
            txt=params.text.content,
            font_size=params.text.font_size,
            font=params.text.font,
            font_style=style,
            align=(Align.CENTER, Align.CENTER),
        )
    text_bb = probe.sketch.bounding_box()
    text_w = text_bb.size.X
    text_h = text_bb.size.Y

    if params.sizing.auto_size:
        plate_w = max(params.sizing.min_width, text_w + 2 * params.sizing.padding_x)
        plate_h = max(params.sizing.min_height, text_h + 2 * params.sizing.padding_y)
    else:
        plate_w = params.sizing.width
        plate_h = params.sizing.height

    # Ensure base thickness is sufficient for magnet pocket + floor thickness
    pocket_depth = (
        (params.magnets.thickness + params.magnets.pocket_depth_offset)
        if params.magnets.enabled
        else 0.0
    )
    mode = TextMode.from_str(params.text.mode) if isinstance(params.text.mode, str) else params.text.mode

    # In debossed mode, letters cut into top face, requiring extra safety margin
    extra_recess = params.text.depth if mode == TextMode.DEBOSSED else 0.0
    required_min_thick = pocket_depth + extra_recess + params.plate.min_floor_thickness
    plate_thick = max(params.plate.base_thickness, required_min_thick)

    return plate_w, plate_h, plate_thick


def calculate_magnet_positions(
    plate_width: float,
    plate_height: float,
    params: MagneticLabelParams,
) -> List[Tuple[float, float]]:
    """
    Calculates symmetrical press-fit magnet center coordinates (X, Y).
    Supports custom positions, explicit count, or automatic aspect-ratio spacing.
    """
    mag = params.magnets
    if not mag.enabled:
        return []

    if mag.positions is not None:
        return list(mag.positions)

    if mag.count is not None:
        count = max(1, mag.count)
    else:
        if plate_width < 36.0:
            count = 1
        elif plate_width <= 75.0:
            count = 2
        else:
            span = plate_width - 2 * mag.edge_margin
            count = max(2, round(span / 40.0) + 1)

    if count == 1:
        return [(0.0, 0.0)]

    x_left = -plate_width / 2.0 + mag.edge_margin
    x_right = plate_width / 2.0 - mag.edge_margin
    step = (x_right - x_left) / (count - 1)

    return [(round(x_left + i * step, 3), 0.0) for i in range(count)]


def build_magnetic_label(params: MagneticLabelParams) -> GeneratedLabel:
    """
    Parametrically builds the 3D magnetic label model using build123d.
    Returns a GeneratedLabel containing the base solid, text solid (for flush mode),
    and visualization magnet bodies.
    """
    txt = params.text
    sizing = params.sizing
    plate = params.plate
    border = params.border
    mag = params.magnets

    mode = TextMode.from_str(txt.mode) if isinstance(txt.mode, str) else txt.mode
    font_style = _resolve_font_style(txt.font_style)

    width, height, thickness = calculate_dimensions(params)
    magnet_coords = calculate_magnet_positions(width, height, params)

    pocket_radius = (mag.diameter + mag.clearance) / 2.0
    pocket_depth = mag.thickness + mag.pocket_depth_offset

    effective_corner_radius = min(plate.corner_radius, (height / 2.0) - 0.5)

    # 1. Main Base Plate
    with BuildPart() as base_builder:
        with BuildSketch():
            if effective_corner_radius > 0:
                RectangleRounded(width, height, radius=effective_corner_radius)
            else:
                Rectangle(width, height)
        extrude(amount=thickness)

        if (not border.enabled) and plate.top_chamfer > 0.0:
            top_face = base_builder.faces().sort_by(Axis.Z)[-1]
            max_chamfer = min(plate.top_chamfer, effective_corner_radius * 0.8, 1.5)
            if max_chamfer > 0.05:
                chamfer(top_face.edges(), length=max_chamfer)

        if magnet_coords:
            with Locations(magnet_coords):
                Cylinder(
                    radius=pocket_radius,
                    height=pocket_depth,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

        if border.enabled and border.width > 0:
            with BuildSketch(Plane.XY.offset(thickness)):
                if effective_corner_radius > 0:
                    RectangleRounded(width, height, radius=effective_corner_radius)
                    inner_r = max(0.5, effective_corner_radius - border.width)
                    RectangleRounded(
                        width - 2 * border.width,
                        height - 2 * border.width,
                        radius=inner_r,
                        mode=Mode.SUBTRACT,
                    )
                else:
                    Rectangle(width, height)
                    Rectangle(
                        width - 2 * border.width,
                        height - 2 * border.width,
                        mode=Mode.SUBTRACT,
                    )
            extrude(amount=txt.depth, mode=Mode.ADD)

            if plate.top_chamfer > 0.0:
                rim_top_face = base_builder.faces().sort_by(Axis.Z)[-1]
                outer_edges = rim_top_face.outer_wire().edges()
                max_rim_chamfer = min(plate.top_chamfer, border.width * 0.45, 1.2)
                if max_rim_chamfer > 0.05:
                    chamfer(outer_edges, length=max_rim_chamfer)

        align_norm = txt.align.strip().lower()
        margin_x = sizing.padding_x + (border.width if border.enabled else 0.0)

        if align_norm in ("left", "start"):
            pos_x = -width / 2.0 + margin_x
            align_x = Align.MIN
        elif align_norm in ("right", "end"):
            pos_x = width / 2.0 - margin_x
            align_x = Align.MAX
        else:
            pos_x = 0.0
            align_x = Align.CENTER

        pos_y = txt.offset_y
        align_y = Align.CENTER

        with BuildSketch(Plane.XY.offset(thickness)):
            with Locations([(pos_x, pos_y)]):
                Text(
                    txt=txt.content,
                    font_size=txt.font_size,
                    font=txt.font,
                    font_style=font_style,
                    align=(align_x, align_y),
                )

        if mode == TextMode.EMBOSSED:
            extrude(amount=txt.depth, mode=Mode.ADD)
        elif mode in (TextMode.DEBOSSED, TextMode.FLUSH):
            extrude(amount=-txt.depth, mode=Mode.SUBTRACT)

    # 2. Text Inlay Body (for Flush / Multi-Color 3D Printing)
    text_inlay_part: Optional[Compound | Solid] = None
    if mode == TextMode.FLUSH:
        with BuildPart() as inlay_builder:
            with BuildSketch(Plane.XY.offset(thickness - txt.depth)):
                with Locations([(pos_x, pos_y)]):
                    Text(
                        txt=txt.content,
                        font_size=txt.font_size,
                        font=txt.font,
                        font_style=font_style,
                        align=(align_x, align_y),
                    )
            extrude(amount=txt.depth)
        text_inlay_part = inlay_builder.part

    # 3. Magnet Solids (for visual preview and fit verification)
    magnet_solids: List[Solid] = []
    nominal_mag_radius = mag.diameter / 2.0
    for mx, my in magnet_coords:
        mag_solid = Solid.make_cylinder(
            nominal_mag_radius,
            mag.thickness,
        ).locate(Location((mx, my, 0.0)))
        magnet_solids.append(mag_solid)

    return GeneratedLabel(
        base_part=base_builder.part,
        text_part=text_inlay_part,
        magnet_solids=magnet_solids,
        actual_width=width,
        actual_height=height,
        actual_thickness=thickness,
        magnet_positions=magnet_coords,
        params=params,
    )


def create_magnetic_label(params: MagneticLabelParams) -> Compound | Part | Solid:
    """
    Decoupled generator function returning CAD geometry without side effects.
    Returns Part/Solid for single-body labels, or Compound if multi-body flush text is present.
    """
    label = build_magnetic_label(params)
    if label.text_part is not None:
        return Compound(children=[label.base_part, label.text_part])
    return label.base_part


# ==============================================================================
# EXPORT HELPERS
# ==============================================================================

def export_label_files(
    label: GeneratedLabel,
    output_dir: Union[str, Path] = "exports",
    prefix: str = "magnetic_label",
    do_export_stl: bool = False,
    do_export_step: bool = False,
    stl_tolerance: float = 0.001,
) -> List[str]:
    """
    Exports generated label parts to STL and/or STEP formats.
    Relative paths in output_dir are automatically anchored relative
    to this script's directory, ensuring files never spill into the repo root.
    """
    out_path = Path(output_dir)
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parent / out_path
    out_path.mkdir(parents=True, exist_ok=True)
    saved_files: List[str] = []

    safe_text = "".join(c if c.isalnum() else "_" for c in label.params.text.content).strip("_").lower()
    dim_str = f"{label.actual_width:.0f}x{label.actual_height:.0f}mm"
    base_stem = f"{prefix}_{dim_str}_{safe_text}_{label.params.text.mode}"

    # Export base part
    if do_export_stl:
        stl_base = out_path / f"{base_stem}_base.stl"
        export_stl(label.base_part, str(stl_base), angular_tolerance=0.1, tolerance=stl_tolerance)
        saved_files.append(str(stl_base))

    if do_export_step:
        step_base = out_path / f"{base_stem}_base.step"
        export_step(label.base_part, str(step_base))
        saved_files.append(str(step_base))

    # Export flush text inlay if present
    if label.text_part is not None:
        if do_export_stl:
            stl_text = out_path / f"{base_stem}_text_inlay.stl"
            export_stl(label.text_part, str(stl_text), angular_tolerance=0.1, tolerance=stl_tolerance)
            saved_files.append(str(stl_text))

        if do_export_step:
            step_text = out_path / f"{base_stem}_text_inlay.step"
            export_step(label.text_part, str(step_text))
            saved_files.append(str(step_text))

            # Export unified multi-body assembly (loads into slicers with 1-click filament assignment)
            step_multi = out_path / f"{base_stem}_multibody_assembly.step"
            export_step(Compound([label.base_part, label.text_part]), str(step_multi))
            saved_files.append(str(step_multi))

    return saved_files


# ==============================================================================
# BATCH GENERATION HELPERS
# ==============================================================================

def batch_generate(
    labels: list[Union[str, Tuple[str, dict]]],
    defaults: Optional[MagneticLabelParams] = None,
    output_dir: Union[str, Path] = "exports",
    do_export_stl: bool = False,
    do_export_step: bool = False,
    preview_grid: bool = True,
    grid_gap: float = 6.0,
) -> List[GeneratedLabel]:
    """
    Generates multiple magnetic labels from a list of text strings using shared defaults.

    Args:
        labels: List of label strings e.g. ["M3 BOLTS", "M4 BOLTS"], or tuples with
                per-label override dictionaries e.g. [("BIG ITEM", {"font_size": 16.0})].
        defaults: Base MagneticLabelParams template. If None, uses default configuration.
        output_dir: Directory where exported STL/STEP files will be stored.
        do_export_stl: Whether to export STL files for all generated labels.
        do_export_step: Whether to export STEP files for all generated labels.
        preview_grid: Whether to arrange and preview all generated labels in the viewer.
        grid_gap: Vertical gap between labels when displayed in the 3D viewer (mm).

    Returns:
        List of GeneratedLabel objects.
    """
    if defaults is None:
        defaults = MagneticLabelParams()

    results: List[GeneratedLabel] = []

    print("=" * 65)
    print(f" BATCH GENERATING {len(labels)} MAGNETIC LABELS")
    print("=" * 65)

    for idx, item in enumerate(labels, start=1):
        if isinstance(item, tuple):
            text_val, overrides = item
            text_overrides = {k: v for k, v in overrides.items() if hasattr(defaults.text, k)}
            top_overrides = {k: v for k, v in overrides.items() if not hasattr(defaults.text, k)}
            item_params = replace(
                defaults,
                text=replace(defaults.text, content=str(text_val), **text_overrides),
                **top_overrides,
            )
        else:
            item_params = replace(defaults, text=replace(defaults.text, content=str(item)))

        label = build_magnetic_label(item_params)
        results.append(label)

        print(f" [{idx:02d}/{len(labels):02d}] '{label.params.text.content}': "
              f"{label.actual_width:.1f} x {label.actual_height:.1f} x {label.actual_thickness:.1f} mm "
              f"({len(label.magnet_positions)} magnets)")

        if do_export_stl or do_export_step:
            files = export_label_files(
                label,
                output_dir=output_dir,
                do_export_step=do_export_step,
                do_export_stl=do_export_stl,
            )
            for f in files:
                print(f"       -> Saved: {f}")

    # Arrange and show all labels in ocp_viewer / ocp_vscode viewer
    viewer = _get_viewer() if preview_grid and results else None
    if viewer is not None:
        Camera, set_defaults, show = viewer
        set_defaults(orbit_control=True)
        print(f"\nArranging {len(results)} labels in viewer...")

        display_items = []
        current_y = 0.0

        for i, gen in enumerate(results):
            # Offset along Y so labels do not overlap in the viewer
            loc = Location((0.0, current_y, 0.0))
            offset_base = gen.base_part.locate(loc)

            color_base = (240, 240, 245) if gen.params.text.mode == "flush" else (65, 70, 75)
            display_items.append((offset_base, f"Label {i+1}: {gen.params.text.content}", color_base))

            if gen.text_part is not None:
                offset_text = gen.text_part.locate(loc)
                display_items.append((offset_text, f"Text {i+1}: {gen.params.text.content}", (230, 80, 20)))

            for j, mag in enumerate(gen.magnet_solids):
                display_items.append((mag.locate(loc), f"Mag_{i+1}_{j+1}", (190, 195, 200)))

            current_y += gen.actual_height + grid_gap

        show(
            *[item[0] for item in display_items],
            names=[item[1] for item in display_items],
            colors=[item[2] for item in display_items],
            reset_camera=Camera.KEEP,
        )
        print("All batch labels displayed in viewer!")

    print("=" * 65)
    return results


# ==============================================================================
# MAIN PREVIEW & EXECUTION
# ==============================================================================

def main():
    """Generates the label based on MagneticLabelParams defaults and previews it."""
    params = MagneticLabelParams()

    # If BATCH_LABELS has items, run in batch mode!
    if BATCH_LABELS:
        batch_generate(
            labels=BATCH_LABELS,
            defaults=params,
            output_dir=OUTPUT_DIR,
            do_export_stl=EXPORT_STL,
            do_export_step=EXPORT_STEP,
            preview_grid=True,
        )
        return

    print("=" * 65)
    print(" PARAMETRIC BUILD123D MAGNETIC LABEL GENERATOR")
    print("=" * 65)
    print(f" Text:              '{params.text.content}'")
    print(f" Font:              {params.text.font} ({params.text.font_style}), Size: {params.text.font_size} mm")
    print(f" Alignment:         {params.text.align.upper()} (Y offset: {params.text.offset_y:+.2f} mm)")
    print(f" Rendering Mode:    {params.text.mode.upper()} (depth: {params.text.depth} mm)")

    # Build the label model
    label = build_magnetic_label(params)

    pocket_dia = params.magnets.diameter + params.magnets.clearance
    pocket_depth = params.magnets.thickness + params.magnets.pocket_depth_offset
    floor_thick = label.actual_thickness - pocket_depth

    print(f" Plate Dimensions:  {label.actual_width:.2f} x {label.actual_height:.2f} x {label.actual_thickness:.2f} mm")
    print(f" Magnet Pockets:    {len(label.magnet_positions)} x [Ø{pocket_dia:.2f} mm x {pocket_depth:.2f} mm deep]")
    print(f" Magnet Centers X:  {[x for x, y in label.magnet_positions]} mm")
    print(f" Floor Thickness:   {floor_thick:.2f} mm (behind magnets)")
    print(f" Base Volume:       {label.base_part.volume:.2f} mm³")
    if label.text_part is not None:
        print(f" Text Inlay Volume: {label.text_part.volume:.2f} mm³")

    # Export if requested
    if EXPORT_STL or EXPORT_STEP:
        files = export_label_files(
            label,
            output_dir=OUTPUT_DIR,
            do_export_stl=EXPORT_STL,
            do_export_step=EXPORT_STEP,
        )
        print(f" Exported files:    {files}")

    # Preview in ocp_viewer / ocp_vscode
    viewer = _get_viewer()
    if viewer is not None:
        Camera, set_defaults, show = viewer
        set_defaults(orbit_control=True)
        print("\nSending 3D model to viewer...")

        display_items = []
        
        # Color styling
        if params.text.mode == "flush" and label.text_part is not None:
            # Multi-color contrast for flush inlay
            display_items.append((label.base_part, "Label Base (Body)", (240, 240, 245)))
            display_items.append((label.text_part, "Text Inlay", (230, 80, 20)))
        elif params.text.mode == "embossed":
            display_items.append((label.base_part, "Magnetic Label (Embossed)", (60, 60, 65)))
        else:
            display_items.append((label.base_part, "Magnetic Label (Debossed)", (70, 75, 80)))

        # Magnets shown inside pockets in metallic silver
        for i, mag in enumerate(label.magnet_solids):
            display_items.append((mag, f"Magnet {i+1} (Press-fit)", (190, 195, 200)))

        # Show in viewer
        show(
            *[item[0] for item in display_items],
            names=[item[1] for item in display_items],
            colors=[item[2] for item in display_items],
            reset_camera=Camera.KEEP,
        )
        print("Model displayed in viewer!")
    else:
        print("\nNote: ocp_viewer / ocp_vscode is not installed; skipping interactive 3D preview.")

    print("=" * 65)


if __name__ == "__main__":
    main()
