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
- Visual display: Integrated ocp_vscode viewer preview with contrasting part colors
  and semi-transparent magnets inside the pockets.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union

# Handle local repo folder shadowing the installed build123d site-package
if os.path.isdir("build123d") and sys.path and sys.path[0] in ("", "."):
    sys.path.pop(0)

from build123d import *

try:
    from ocp_vscode import Camera, set_defaults, show, show_object
    HAS_OCP_VSCODE = True
except ImportError:
    HAS_OCP_VSCODE = False


# ==============================================================================
# USER-EDITABLE CONFIGURATION (Quick-Change Variables)
# ==============================================================================
# Modify these top-level settings and run this script to preview in ocp_vscode.

# Label Text:
# - Set LABEL_TEXT for single label generation.
# - OR populate BATCH_LABELS to batch-generate multiple labels at once using these shared defaults!
LABEL_TEXT: str = "FASTENERS"

# Batch label list: Just list your text strings here to generate all of them at once.
# Supports simple strings e.g. ["M3 BOLTS", "M4 BOLTS", "WASHERS", "NUTS"]
# or tuples with custom per-label overrides: [("SPECIAL", {"font_size": 16.0})]
BATCH_LABELS: list[str | tuple[str, dict]] = []

FONT_SIZE: float = 11.0               # Font height in mm
FONT_NAME: str = "FreeSans"              # Font family (e.g. 'Arial', 'FreeSans', 'Helvetica')
FONT_STYLE: str = "bold"              # 'regular', 'bold', 'italic', 'bold_italic'

# Text Alignment: 'center', 'left', or 'right'
TEXT_ALIGN: str = "center"
TEXT_OFFSET_Y: float = 0.0            # Fine vertical offset adjustment in mm (0.0 = perfectly centered)

# Text rendering style: 'embossed' (raised), 'debossed' (engraved), or 'flush' (multi-color inlay)
TEXT_MODE: str = "embossed"
TEXT_DEPTH: float = 1.2               # Height of raised letters or depth of engraving (mm)

# Sizing: Set AUTO_SIZE = True for text-adaptive dimensions, or False for static dimensions
AUTO_SIZE: bool = False
STATIC_WIDTH: float = 80.0            # Used when AUTO_SIZE is False (mm)
STATIC_HEIGHT: float = 24.0           # Used when AUTO_SIZE is False (mm)
PADDING_X: float = 10.0               # Left & right margin around text in auto-size mode (mm)
PADDING_Y: float = 6.0                # Top & bottom margin around text in auto-size mode (mm)

# Plate & Edge Styling
BASE_THICKNESS: float = 3.6           # Overall plate thickness (mm)
CORNER_RADIUS: float = 3.0            # Corner fillet radius (mm; set 0 for square corners)
TOP_EDGE_CHAMFER: float = 0.6         # 45-degree bevel on front perimeter (mm; 0 to disable)
BORDER_RIM: bool = True              # Add an optional raised border frame around the face
BORDER_WIDTH: float = 1.2             # Width of raised border frame (mm)

# Magnet Specifications (Round press-fit magnets, e.g. 6x2mm or 6x3mm)
MAGNET_DIAMETER: float = 10.0          # Nominal magnet diameter in mm
MAGNET_THICKNESS: float = 3.0         # Nominal magnet thickness in mm
MAGNET_CLEARANCE: float = 0.15        # Press-fit diameter tolerance for 3D printing (mm)
POCKET_DEPTH_OFFSET: float = 0.1      # Pocket depth allowance to keep magnets sub-flush (mm)

# Magnet Placement
# Set MAGNET_COUNT = None for automatic spacing, or an integer (1, 2, 3...) to override
MAGNET_COUNT: Optional[int] = None
MAGNET_EDGE_MARGIN: float = 8.0       # Distance from plate ends to magnet centers (mm)

# Export Settings
EXPORT_STL: bool = False              # Save .stl files on execution
EXPORT_STEP: bool = False             # Save .step files on execution
OUTPUT_DIR: str = "."                 # Output directory for exported files


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
class MagneticLabelParams:
    """Configuration parameters for the parametric magnetic label generator."""

    # Text Settings
    text: str = "WORKSHOP"
    font_size: float = 12.0
    font: str = "Arial"
    font_style: Union[str, FontStyle] = "bold"
    text_align: str = "center"             # 'center', 'left', or 'right'
    text_offset_y: float = 0.0             # Fine vertical offset adjustment in mm
    text_mode: Union[str, TextMode] = "embossed"
    text_depth: float = 0.8

    # Sizing
    auto_size: bool = True
    width: float = 90.0
    height: float = 24.0
    padding_x: float = 10.0
    padding_y: float = 6.0
    min_width: float = 30.0
    min_height: float = 16.0

    # Plate & Edge Styling
    base_thickness: float = 3.6
    corner_radius: float = 3.0
    top_chamfer: float = 0.6
    border_rim: bool = False
    border_width: float = 1.2
    min_floor_thickness: float = 0.8

    # Magnet Pocket Settings
    magnet_diameter: float = 6.0
    magnet_thickness: float = 2.0
    magnet_clearance: float = 0.15
    pocket_depth_offset: float = 0.1
    magnet_count: Optional[int] = None
    magnet_edge_margin: float = 8.0
    magnet_positions: Optional[List[Tuple[float, float]]] = None


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
    style = _resolve_font_style(params.font_style)

    # Calculate text bounding dimensions with exact geometric centering
    with BuildSketch() as probe:
        Text(
            txt=params.text,
            font_size=params.font_size,
            font=params.font,
            font_style=style,
            align=(Align.CENTER, Align.CENTER),
        )
    text_bb = probe.sketch.bounding_box()
    text_w = text_bb.size.X
    text_h = text_bb.size.Y

    if params.auto_size:
        plate_w = max(params.min_width, text_w + 2 * params.padding_x)
        plate_h = max(params.min_height, text_h + 2 * params.padding_y)
    else:
        plate_w = params.width
        plate_h = params.height

    # Ensure base thickness is sufficient for magnet pocket + floor thickness
    pocket_depth = params.magnet_thickness + params.pocket_depth_offset
    mode = TextMode.from_str(params.text_mode) if isinstance(params.text_mode, str) else params.text_mode
    
    # In debossed mode, letters cut into top face, requiring extra safety margin
    extra_recess = params.text_depth if mode == TextMode.DEBOSSED else 0.0
    required_min_thick = pocket_depth + extra_recess + params.min_floor_thickness
    plate_thick = max(params.base_thickness, required_min_thick)

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
    # 1. User supplied custom coordinates
    if params.magnet_positions is not None:
        return list(params.magnet_positions)

    # 2. Determine count if not specified
    if params.magnet_count is not None:
        count = max(1, params.magnet_count)
    else:
        # Automatic spacing rule based on width:
        # < 36 mm: 1 centered magnet
        # 36 mm - 75 mm: 2 magnets
        # > 75 mm: 3 or more magnets spaced roughly every 35-45 mm
        if plate_width < 36.0:
            count = 1
        elif plate_width <= 75.0:
            count = 2
        else:
            span = plate_width - 2 * params.magnet_edge_margin
            count = max(2, round(span / 40.0) + 1)

    # 3. Calculate coordinate array along horizontal centerline (Y = 0)
    if count == 1:
        return [(0.0, 0.0)]

    x_left = -plate_width / 2.0 + params.magnet_edge_margin
    x_right = plate_width / 2.0 - params.magnet_edge_margin
    step = (x_right - x_left) / (count - 1)
    
    return [(round(x_left + i * step, 3), 0.0) for i in range(count)]


def build_magnetic_label(params: MagneticLabelParams) -> GeneratedLabel:
    """
    Parametrically builds the 3D magnetic label model using build123d.
    Returns a GeneratedLabel containing the base solid, text solid (for flush mode),
    and visualization magnet bodies.
    """
    mode = TextMode.from_str(params.text_mode) if isinstance(params.text_mode, str) else params.text_mode
    font_style = _resolve_font_style(params.font_style)

    # Calculate dimensions and magnet layout
    width, height, thickness = calculate_dimensions(params)
    magnet_coords = calculate_magnet_positions(width, height, params)

    pocket_radius = (params.magnet_diameter + params.magnet_clearance) / 2.0
    pocket_depth = params.magnet_thickness + params.pocket_depth_offset

    # Ensure corner radius does not exceed half the plate height
    effective_corner_radius = min(params.corner_radius, (height / 2.0) - 0.5)

    # --------------------------------------------------------------------------
    # 1. Main Base Plate
    # --------------------------------------------------------------------------
    with BuildPart() as base_builder:
        # 1a. Base plate extrusion from Z=0 to Z=thickness
        with BuildSketch():
            if effective_corner_radius > 0:
                RectangleRounded(width, height, radius=effective_corner_radius)
            else:
                Rectangle(width, height)
        extrude(amount=thickness)

        # 1b. Chamfer top perimeter of base plate (only if border rim is NOT used)
        # When border rim is enabled, chamfer is placed on the rim's top crown instead
        # to prevent creating an awkward stepped notch at the base of the rim wall.
        if (not params.border_rim) and params.top_chamfer > 0.0:
            top_face = base_builder.faces().sort_by(Axis.Z)[-1]
            max_chamfer = min(params.top_chamfer, effective_corner_radius * 0.8, 1.5)
            if max_chamfer > 0.05:
                chamfer(top_face.edges(), length=max_chamfer)

        # 1c. Rear magnet press-fit pockets (cut from Z=0 upwards)
        with Locations(magnet_coords):
            Cylinder(
                radius=pocket_radius,
                height=pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # 1d. Optional raised border rim
        if params.border_rim and params.border_width > 0:
            with BuildSketch(Plane.XY.offset(thickness)):
                if effective_corner_radius > 0:
                    RectangleRounded(width, height, radius=effective_corner_radius)
                    inner_r = max(0.5, effective_corner_radius - params.border_width)
                    RectangleRounded(
                        width - 2 * params.border_width,
                        height - 2 * params.border_width,
                        radius=inner_r,
                        mode=Mode.SUBTRACT,
                    )
                else:
                    Rectangle(width, height)
                    Rectangle(
                        width - 2 * params.border_width,
                        height - 2 * params.border_width,
                        mode=Mode.SUBTRACT,
                    )
            extrude(amount=params.text_depth, mode=Mode.ADD)

            # Apply chamfer to the outer top edge of the rim
            if params.top_chamfer > 0.0:
                rim_top_face = base_builder.faces().sort_by(Axis.Z)[-1]
                outer_edges = rim_top_face.outer_wire().edges()
                max_rim_chamfer = min(params.top_chamfer, params.border_width * 0.45, 1.2)
                if max_rim_chamfer > 0.05:
                    chamfer(outer_edges, length=max_rim_chamfer)

        # 1e. Text application on front face (with true geometric centering and alignment)
        align_norm = params.text_align.strip().lower()
        margin_x = params.padding_x + (params.border_width if params.border_rim else 0.0)

        if align_norm in ("left", "start"):
            pos_x = -width / 2.0 + margin_x
            align_x = Align.MIN
        elif align_norm in ("right", "end"):
            pos_x = width / 2.0 - margin_x
            align_x = Align.MAX
        else:  # "center"
            pos_x = 0.0
            align_x = Align.CENTER

        pos_y = params.text_offset_y
        align_y = Align.CENTER

        with BuildSketch(Plane.XY.offset(thickness)):
            with Locations([(pos_x, pos_y)]):
                Text(
                    txt=params.text,
                    font_size=params.font_size,
                    font=params.font,
                    font_style=font_style,
                    align=(align_x, align_y),
                )

        if mode == TextMode.EMBOSSED:
            extrude(amount=params.text_depth, mode=Mode.ADD)
        elif mode in (TextMode.DEBOSSED, TextMode.FLUSH):
            extrude(amount=-params.text_depth, mode=Mode.SUBTRACT)

    # --------------------------------------------------------------------------
    # 2. Text Inlay Body (for Flush / Multi-Color 3D Printing)
    # --------------------------------------------------------------------------
    text_inlay_part: Optional[Compound | Solid] = None
    if mode == TextMode.FLUSH:
        with BuildPart() as inlay_builder:
            with BuildSketch(Plane.XY.offset(thickness - params.text_depth)):
                with Locations([(pos_x, pos_y)]):
                    Text(
                        txt=params.text,
                        font_size=params.font_size,
                        font=params.font,
                        font_style=font_style,
                        align=(align_x, align_y),
                    )
            extrude(amount=params.text_depth)
        text_inlay_part = inlay_builder.part

    # --------------------------------------------------------------------------
    # 3. Magnet Solids (for visual preview and fit verification)
    # --------------------------------------------------------------------------
    magnet_solids: List[Solid] = []
    nominal_mag_radius = params.magnet_diameter / 2.0
    for mx, my in magnet_coords:
        mag = Solid.make_cylinder(
            nominal_mag_radius,
            params.magnet_thickness,
        ).locate(Location((mx, my, 0.0)))
        magnet_solids.append(mag)

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


# ==============================================================================
# EXPORT HELPERS
# ==============================================================================

def export_label_files(
    label: GeneratedLabel,
    output_dir: str = ".",
    prefix: str = "magnetic_label",
    do_export_step: bool = False,
    do_export_stl: bool = False,
    stl_tolerance: float = 0.001,
) -> List[str]:
    """Exports generated label parts to STEP and/or STL formats."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    saved_files: List[str] = []

    safe_text = "".join(c if c.isalnum() else "_" for c in label.params.text).strip("_").lower()
    base_stem = f"{prefix}_{safe_text}_{label.params.text_mode}"

    # Export base part
    if do_export_step:
        step_base = out_path / f"{base_stem}_base.step"
        export_step(label.base_part, str(step_base))
        saved_files.append(str(step_base))

    if do_export_stl:
        stl_base = out_path / f"{base_stem}_base.stl"
        export_stl(label.base_part, str(stl_base), angular_tolerance=0.1, tolerance=stl_tolerance)
        saved_files.append(str(stl_base))

    # Export flush text inlay if present
    if label.text_part is not None:
        if do_export_step:
            step_text = out_path / f"{base_stem}_text_inlay.step"
            export_step(label.text_part, str(step_text))
            saved_files.append(str(step_text))

            # Export unified multi-body assembly (loads into slicers with 1-click filament assignment)
            step_multi = out_path / f"{base_stem}_multibody_assembly.step"
            export_step(Compound([label.base_part, label.text_part]), str(step_multi))
            saved_files.append(str(step_multi))

        if do_export_stl:
            stl_text = out_path / f"{base_stem}_text_inlay.stl"
            export_stl(label.text_part, str(stl_text), angular_tolerance=0.1, tolerance=stl_tolerance)
            saved_files.append(str(stl_text))

    return saved_files


# ==============================================================================
# BATCH GENERATION HELPERS
# ==============================================================================

def batch_generate(
    labels: list[Union[str, Tuple[str, dict]]],
    defaults: Optional[MagneticLabelParams] = None,
    output_dir: str = "./output_labels",
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
        preview_grid: Whether to arrange and preview all generated labels in ocp_vscode.
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
            item_params = replace(defaults, text=str(text_val), **overrides)
        else:
            item_params = replace(defaults, text=str(item))

        label = build_magnetic_label(item_params)
        results.append(label)

        print(f" [{idx:02d}/{len(labels):02d}] '{label.params.text}': "
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

    # Arrange and show all labels in ocp_vscode viewer
    if preview_grid and HAS_OCP_VSCODE and results:
        set_defaults(orbit_control=True)
        print(f"\nArranging {len(results)} labels in ocp_vscode viewer...")

        display_items = []
        current_y = 0.0

        for i, gen in enumerate(results):
            # Offset along Y so labels do not overlap in the viewer
            loc = Location((0.0, current_y, 0.0))
            offset_base = gen.base_part.locate(loc)

            color_base = (240, 240, 245) if gen.params.text_mode == "flush" else (65, 70, 75)
            display_items.append((offset_base, f"Label {i+1}: {gen.params.text}", color_base))

            if gen.text_part is not None:
                offset_text = gen.text_part.locate(loc)
                display_items.append((offset_text, f"Text {i+1}: {gen.params.text}", (230, 80, 20)))

            for j, mag in enumerate(gen.magnet_solids):
                display_items.append((mag.locate(loc), f"Mag_{i+1}_{j+1}", (190, 195, 200)))

            current_y += gen.actual_height + grid_gap

        show(
            *[item[0] for item in display_items],
            names=[item[1] for item in display_items],
            colors=[item[2] for item in display_items],
            reset_camera=Camera.KEEP,
        )
        print("All batch labels displayed in ocp_vscode!")

    print("=" * 65)
    return results


# ==============================================================================
# MAIN PREVIEW & EXECUTION
# ==============================================================================

def main():
    """Generates the label based on top-level user configuration and previews it."""
    params = MagneticLabelParams(
        text=LABEL_TEXT,
        font_size=FONT_SIZE,
        font=FONT_NAME,
        font_style=FONT_STYLE,
        text_align=TEXT_ALIGN,
        text_offset_y=TEXT_OFFSET_Y,
        text_mode=TEXT_MODE,
        text_depth=TEXT_DEPTH,
        auto_size=AUTO_SIZE,
        width=STATIC_WIDTH,
        height=STATIC_HEIGHT,
        padding_x=PADDING_X,
        padding_y=PADDING_Y,
        base_thickness=BASE_THICKNESS,
        corner_radius=CORNER_RADIUS,
        top_chamfer=TOP_EDGE_CHAMFER,
        border_rim=BORDER_RIM,
        border_width=BORDER_WIDTH,
        magnet_diameter=MAGNET_DIAMETER,
        magnet_thickness=MAGNET_THICKNESS,
        magnet_clearance=MAGNET_CLEARANCE,
        pocket_depth_offset=POCKET_DEPTH_OFFSET,
        magnet_count=MAGNET_COUNT,
        magnet_edge_margin=MAGNET_EDGE_MARGIN,
    )

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
    print(f" Text:              '{params.text}'")
    print(f" Font:              {params.font} ({params.font_style}), Size: {params.font_size} mm")
    print(f" Alignment:         {params.text_align.upper()} (Y offset: {params.text_offset_y:+.2f} mm)")
    print(f" Rendering Mode:    {params.text_mode.upper()} (depth: {params.text_depth} mm)")

    # Build the label model
    label = build_magnetic_label(params)

    pocket_dia = params.magnet_diameter + params.magnet_clearance
    pocket_depth = params.magnet_thickness + params.pocket_depth_offset
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
            do_export_step=EXPORT_STEP,
            do_export_stl=EXPORT_STL,
        )
        print(f" Exported files:    {files}")

    # Preview in ocp_vscode
    if HAS_OCP_VSCODE:
        set_defaults(orbit_control=True)
        print("\nSending 3D model to ocp_vscode viewer...")

        display_items = []
        
        # Color styling
        if params.text_mode == "flush" and label.text_part is not None:
            # Multi-color contrast for flush inlay
            display_items.append((label.base_part, "Label Base (Body)", (240, 240, 245)))
            display_items.append((label.text_part, "Text Inlay", (230, 80, 20)))
        elif params.text_mode == "embossed":
            display_items.append((label.base_part, "Magnetic Label (Embossed)", (60, 60, 65)))
        else:
            display_items.append((label.base_part, "Magnetic Label (Debossed)", (70, 75, 80)))

        # Magnets shown inside pockets in metallic silver
        for i, mag in enumerate(label.magnet_solids):
            display_items.append((mag, f"Magnet {i+1} (Press-fit)", (190, 195, 200)))

        # Show in ocp_vscode
        show(
            *[item[0] for item in display_items],
            names=[item[1] for item in display_items],
            colors=[item[2] for item in display_items],
            reset_camera=Camera.KEEP,
        )
        print("Model displayed in ocp_vscode!")
    else:
        print("\nNote: ocp_vscode is not installed; skipping interactive 3D preview.")

    print("=" * 65)


if __name__ == "__main__":
    main()
