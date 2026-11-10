"""
Validation script for models/gridfinity_bin/gridfinity_bin.py
Validates each standalone component function (base feet, body, stacking lip,
compartment scoops, Pred label holders) and the composed bin across multiple
parametric configurations, including large overhangs with scoops.
"""

import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "gridfinity_bin")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from build123d import GeomType, Plane, section
from gridfinity_bin import (
    EXPORT_STEP,
    EXPORT_STL,
    OUTPUT_DIR,
    GridfinityBinParams,
    create_base_feet,
    create_bin_body,
    create_compartment_scoops,
    create_gridfinity_bin,
    create_label_holders,
    create_stacking_lip,
)


def validate():
    print("Beginning validation of modular gridfinity_bin generator...")

    # 1. Verify export flags exist and are booleans
    assert isinstance(EXPORT_STL, bool), "EXPORT_STL must be a bool"
    assert isinstance(EXPORT_STEP, bool), "EXPORT_STEP must be a bool"
    assert OUTPUT_DIR == "exports", "OUTPUT_DIR must default to 'exports'"
    print("✓ Export configuration flags verified")

    # 2. Test individual standalone components on default 1x1x3 bin
    p1 = GridfinityBinParams()
    feet = create_base_feet(p1)
    body = create_bin_body(p1)
    lip = create_stacking_lip(p1)
    scoops = create_compartment_scoops(p1)
    labels = create_label_holders(p1)

    assert feet.is_valid, "Base feet component is not valid"
    assert body.is_valid, "Bin body component is not valid"
    assert lip is not None and lip.is_valid, "Stacking lip component is not valid"
    assert scoops is not None and scoops.is_valid and scoops.volume > 10.0, "Scoops component is not valid"
    assert labels is not None and labels.is_valid and labels.volume > 10.0, "Label holders component is not valid"

    # Verify the scoop face is a true cylindrical surface of radius == p1.scoop_front_radius (6.0mm)
    cyl_faces = scoops.faces().filter_by(GeomType.CYLINDER)
    radii = [round(f.radius, 4) for f in cyl_faces if f.radius is not None]
    assert any(abs(r - p1.scoop_front_radius) < 1e-3 for r in radii), (
        f"Expected cylindrical face of radius {p1.scoop_front_radius}, found radii={radii}"
    )
    print(f"✓ Confirmed scoop surface is an exact cylinder with radii={radii}mm")

    # Verify independent front and back scoops (including master scoop_enabled=False and both=0 disabled)
    assert create_compartment_scoops(GridfinityBinParams(scoop_enabled=False)) is None, (
        "Expected None when scoop_enabled is False"
    )
    p_none = GridfinityBinParams(scoop_enabled=True, scoop_front_radius=0.0, scoop_back_radius=0.0)
    assert create_compartment_scoops(p_none) is None, "Expected None when both scoop radii are 0.0"

    p_single = GridfinityBinParams(scoop_enabled=True, scoop_front_radius=6.0, scoop_back_radius=0.0)
    scoops_single = create_compartment_scoops(p_single)
    p_both_sym = GridfinityBinParams(scoop_enabled=True, scoop_front_radius=6.0, scoop_back_radius=6.0)
    scoops_both = create_compartment_scoops(p_both_sym)
    assert scoops_single is not None and scoops_both is not None and scoops_both.is_valid
    assert abs(scoops_both.volume - 2.0 * scoops_single.volume) < 1.0, (
        f"Expected symmetric front+back scoop volume ({scoops_both.volume:.1f}) == 2x single scoop ({scoops_single.volume:.1f})"
    )

    p_asym = GridfinityBinParams(
        scoop_enabled=True,
        scoop_style="directional",
        scoop_front_radius=6.0,
        scoop_back_radius=10.0,
        scoop_left_radius=8.0,
        scoop_right_radius=5.0,
    )
    scoops_asym = create_compartment_scoops(p_asym)
    assert scoops_asym is not None and scoops_asym.is_valid
    asym_radii = [round(f.radius, 4) for f in scoops_asym.faces().filter_by(GeomType.CYLINDER) if f.radius is not None]
    for expected_r in (5.0, 6.0, 8.0, 10.0):
        assert any(abs(r - expected_r) < 1e-3 for r in asym_radii), (
            f"Expected {expected_r}mm cylindrical scoop face, found {asym_radii}"
        )

    # Verify 360° "bowl" scoop style
    p_bowl = GridfinityBinParams(
        grid_x=2,
        grid_y=1,
        grid_z=3,
        scoop_enabled=True,
        scoop_style="bowl",
        scoop_bowl_radius=8.0,
    )
    scoops_bowl = create_compartment_scoops(p_bowl)
    assert scoops_bowl is not None and scoops_bowl.is_valid and scoops_bowl.volume > 100.0
    bowl_bin = create_gridfinity_bin(p_bowl)
    assert bowl_bin.is_valid and len(bowl_bin.solids()) == 1, "Bowl-mode bin must be a single valid solid"
    print(
        f"✓ Confirmed directional 4-wall scoop radii (radii={sorted(set(asym_radii))}mm) "
        f"& 360° 'bowl' mode (r={p_bowl.scoop_bowl_radius}mm)"
    )

    # Verify auto-calculated label fins vs manual override on a 1u bin
    labels_auto_3 = create_label_holders(GridfinityBinParams(grid_x=1, grid_y=1, label_fin_count=None, label_fin_max_span=12.0))
    labels_manual_3 = create_label_holders(GridfinityBinParams(grid_x=1, grid_y=1, label_fin_count=3))
    labels_manual_0 = create_label_holders(GridfinityBinParams(grid_x=1, grid_y=1, label_fin_count=0))
    assert labels_auto_3 is not None and labels_manual_3 is not None and labels_manual_0 is not None
    assert abs(labels_auto_3.volume - labels_manual_3.volume) < 1e-3, (
        "Expected auto fin calculation with max_span=12.0 on 1u bin to equal manual label_fin_count=3"
    )
    assert labels_auto_3.volume > labels_manual_0.volume + 10.0, "Expected fins to add volume over 0-fin deck"
    print("✓ Confirmed label_fin_count auto-calculation (via label_fin_max_span) and manual override")

    # 3. Test full composed default bin
    expected_x1 = p1.grid_x * p1.unit_size - p1.grid_clearance
    expected_y1 = p1.grid_y * p1.unit_size - p1.grid_clearance
    expected_top_z = p1.grid_z * p1.unit_z + p1.lip_height
    bin1 = create_gridfinity_bin(p1)
    bbox1 = bin1.bounding_box()
    assert bin1.is_valid and len(bin1.solids()) == 1, "Default bin must be a single valid solid"
    assert abs(bbox1.size.X - expected_x1) < 0.05, f"Expected X={expected_x1}, got {bbox1.size.X}"
    assert abs(bbox1.size.Y - expected_y1) < 0.05, f"Expected Y={expected_y1}, got {bbox1.size.Y}"
    assert abs(bbox1.size.Z - expected_top_z) < 0.05, f"Expected Z={expected_top_z}, got {bbox1.size.Z}"

    # Verify the undercut tab slot and 0.6mm retention roof on a 2x1 bin across placement modes:
    for placement in ("center", "left", "right", "per_column"):
        p_placement = GridfinityBinParams(
            grid_x=2,
            grid_y=1,
            grid_z=3,
            dividers_enabled=False,
            label_placement=placement,
            label_units=1,
        )
        lh_part = create_label_holders(p_placement)
        assert lh_part is not None and lh_part.is_valid, f"Label holder invalid for placement={placement}"

        # Cross-section through the 0.6mm retention roof (z = body_h - 0.3mm) vs undercut slot (z = body_h - 1.1mm):
        # The roof section must have MORE material (larger area) than the undercut slot section below it,
        # proving the 0.6mm retention roof overhangs the side tab slots!
        z_top = p_placement.grid_z * p_placement.unit_z
        sec_roof = section(lh_part, Plane.XY.offset(z_top - 0.3))
        sec_slot = section(lh_part, Plane.XY.offset(z_top - 1.1))
        area_roof = sum(f.area for f in sec_roof.faces())
        area_slot = sum(f.area for f in sec_slot.faces())
        assert area_roof > area_slot + 5.0, (
            f"Expected retention roof area ({area_roof:.1f}) > undercut slot area ({area_slot:.1f}) for placement={placement}"
        )

    # Verify label_units (1u vs 2u) and specific label_column indexing on a 3x1 bin
    lh_3u_col2 = create_label_holders(
        GridfinityBinParams(grid_x=3, grid_y=1, label_units=1, label_column=2)
    )
    assert lh_3u_col2 is not None and lh_3u_col2.is_valid

    lh_3u_col1 = create_label_holders(
        GridfinityBinParams(grid_x=3, grid_y=1, label_units=1, label_column=1)
    )
    lh_3u_left = create_label_holders(
        GridfinityBinParams(grid_x=3, grid_y=1, label_units=1, label_placement="left")
    )
    assert abs(lh_3u_col1.volume - lh_3u_left.volume) < 1e-3, (
        "Expected label_column=1 to match label_placement='left'"
    )

    lh_3u_col3 = create_label_holders(
        GridfinityBinParams(grid_x=3, grid_y=1, label_units=1, label_column=3)
    )
    lh_3u_right = create_label_holders(
        GridfinityBinParams(grid_x=3, grid_y=1, label_units=1, label_placement="right")
    )
    assert abs(lh_3u_col3.volume - lh_3u_right.volume) < 1e-3, (
        "Expected label_column=3 to match label_placement='right'"
    )

    # Verify label_shelf_full_width toggle (compact 1U shelf vs full-width shelf on 3x1 bin)
    lh_compact_left = create_label_holders(
        GridfinityBinParams(grid_x=3, grid_y=1, label_units=1, label_placement="left", label_shelf_full_width=False)
    )
    lh_full_left = create_label_holders(
        GridfinityBinParams(grid_x=3, grid_y=1, label_units=1, label_placement="left", label_shelf_full_width=True)
    )
    assert lh_compact_left is not None and lh_full_left is not None
    bbox_compact = lh_compact_left.bounding_box()
    bbox_full = lh_full_left.bounding_box()
    assert bbox_compact.size.X < 45.0, (
        f"Expected compact 1U shelf deck width < 45mm, got {bbox_compact.size.X:.2f}mm"
    )
    assert bbox_full.size.X > 115.0, (
        f"Expected full-width shelf deck width > 115mm on 3x1 bin, got {bbox_full.size.X:.2f}mm"
    )

    # Verify composed full bin with compact shelf is a single solid
    bin_compact = create_gridfinity_bin(
        GridfinityBinParams(grid_x=3, grid_y=1, grid_z=3, label_units=1, label_placement="center", label_shelf_full_width=False)
    )
    assert bin_compact.is_valid and len(bin_compact.solids()) == 1, (
        f"Expected 1 valid solid for bin with compact center label, got {len(bin_compact.solids())}"
    )

    # Verify 2U center label on 2x1 bin
    lh_2u_center = create_label_holders(
        GridfinityBinParams(grid_x=2, grid_y=1, label_placement="center", label_units=2)
    )
    assert lh_2u_center is not None and lh_2u_center.is_valid
    bbox_2u = lh_2u_center.bounding_box()
    assert bbox_2u.size.X > 75.0, f"Expected 2U label width > 75mm, got {bbox_2u.size.X:.2f}mm"
    print(
        f"✓ Test 1 Passed: Default {p1.grid_x}x{p1.grid_y}x{p1.grid_z}u bin "
        f"({bbox1.size.X:.2f}x{bbox1.size.Y:.2f}x{bbox1.size.Z:.2f}mm) + verified 0.6mm undercut retention roof, "
        f"label_placement modes, label_units sizing, and label_column indexing"
    )

    # 4. Test large overhang on scooped wall (reproducing & verifying fix for user screenshot)
    p_ov = GridfinityBinParams(
        grid_x=1,
        grid_y=1,
        grid_z=3,
        dividers_enabled=False,
        overhang_enabled=True,
        overhang_front=12.0,
        scoop_enabled=True,
        scoop_front_radius=10.0,
        scoop_back_radius=6.0,
    )
    bin_ov = create_gridfinity_bin(p_ov)
    assert bin_ov.is_valid, "Overhang bin is not valid"
    assert len(bin_ov.solids()) == 1, (
        f"Expected single connected solid for overhang bin, got {len(bin_ov.solids())} solids"
    )
    # Check horizontal cross-section through the angled overhang wall (z = 10.0mm):
    # must be a single closed hollow ring face (1 face with 1 outer wire and 1 inner wire = 2 wires),
    # proving there is no hole punched through the angled overhang wall and no floating scoop!
    sec = section(bin_ov, Plane.XY.offset(10.0))
    sec_faces = sec.faces()
    assert len(sec_faces) == 1 and len(sec_faces[0].wires()) == 2, (
        f"Expected 1 continuous ring face (2 wires) at z=10mm, got {len(sec_faces)} faces, "
        f"wires={[len(f.wires()) for f in sec_faces]}"
    )
    print(
        f"✓ Test 2 Passed: 1x1x3 bin with 12mm front overhang + dual scoops is a single "
        f"watertight solid with unbroken angled walls (z=10mm ring faces={len(sec_faces)}, wires=2)"
    )

    # 5. Test custom unit_z, dual scoops, and multi-compartment dividers (2x2x4)
    p2 = GridfinityBinParams(
        grid_x=2,
        grid_y=2,
        grid_z=4,
        unit_z=8.0,
        scoop_enabled=True,
        scoop_front_radius=8.0,
        scoop_back_radius=5.0,
        dividers_enabled=True,
        dividers_x=1,
        dividers_y=1,
        overhang_enabled=True,
        overhang_front=5.0,
        overhang_right=3.0,
    )
    bin2 = create_gridfinity_bin(p2)
    bbox2 = bin2.bounding_box()
    assert bin2.is_valid and len(bin2.solids()) == 1, "2x2x4 subdivided overhang bin must be 1 valid solid"
    expected_x2 = 2 * 42.0 - 0.5 + 3.0
    expected_y2 = 2 * 42.0 - 0.5 + 5.0
    expected_z2 = 4 * 8.0 + p2.lip_height
    assert abs(bbox2.size.X - expected_x2) < 0.05, f"Expected X={expected_x2}, got {bbox2.size.X}"
    assert abs(bbox2.size.Y - expected_y2) < 0.05, f"Expected Y={expected_y2}, got {bbox2.size.Y}"
    assert abs(bbox2.size.Z - expected_z2) < 0.05, f"Expected Z={expected_z2}, got {bbox2.size.Z}"
    print(
        f"✓ Test 3 Passed: 2x2x4 custom unit_z=8mm + scoop_wall='both' + dividers + overhangs "
        f"({bbox2.size.X:.2f}x{bbox2.size.Y:.2f}x{bbox2.size.Z:.2f}mm, solids={len(bin2.solids())})"
    )

    print("\nAll Gridfinity bin validation checks passed!")


if __name__ == "__main__":
    validate()
