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
    CoreParams,
    DividersParams,
    EXPORT_STEP,
    EXPORT_STL,
    GridfinityBinParams,
    LabelHolderParams,
    OUTPUT_DIR,
    OverhangParams,
    ScoopParams,
    create_base_feet,
    create_bin_body,
    create_compartment_scoops,
    create_gridfinity_bin,
    create_label_holders,
    create_stacking_lip,
)


def validate():
    print("Beginning validation of modular gridfinity_bin generator...")

    # 1. Verify export flags
    assert isinstance(EXPORT_STL, bool)
    assert isinstance(EXPORT_STEP, bool)
    assert OUTPUT_DIR == "exports"
    print("✓ Export configuration flags verified")

    # 2. Test individual standalone components on default bin
    p1 = GridfinityBinParams()
    feet = create_base_feet(p1)
    body = create_bin_body(p1)
    lip = create_stacking_lip(p1)
    scoops = create_compartment_scoops(p1)
    labels = create_label_holders(p1)

    assert feet.is_valid and body.is_valid
    assert lip is not None and lip.is_valid
    assert scoops is not None and scoops.is_valid and scoops.volume > 10.0
    assert labels is not None and labels.is_valid and labels.volume > 10.0

    cyl_faces = scoops.faces().filter_by(GeomType.CYLINDER)
    radii = [round(f.radius, 4) for f in cyl_faces if f.radius is not None]
    assert any(abs(r - p1.scoop.front_radius) < 1e-3 for r in radii)
    print(f"✓ Confirmed scoop surface is an exact cylinder with radii={radii}mm")

    # Verify independent front/back/left/right scoops and bowl mode
    assert create_compartment_scoops(GridfinityBinParams(scoop=ScoopParams(enabled=False))) is None
    assert create_compartment_scoops(GridfinityBinParams(scoop=ScoopParams(enabled=True, front_radius=0.0, back_radius=0.0))) is None

    scoops_single = create_compartment_scoops(GridfinityBinParams(scoop=ScoopParams(enabled=True, front_radius=6.0, back_radius=0.0)))
    scoops_both = create_compartment_scoops(GridfinityBinParams(scoop=ScoopParams(enabled=True, front_radius=6.0, back_radius=6.0)))
    assert scoops_single is not None and scoops_both is not None and scoops_both.is_valid
    assert abs(scoops_both.volume - 2.0 * scoops_single.volume) < 1.0

    p_asym = GridfinityBinParams(
        scoop=ScoopParams(enabled=True, style="directional", front_radius=6.0, back_radius=10.0, left_radius=8.0, right_radius=5.0)
    )
    scoops_asym = create_compartment_scoops(p_asym)
    assert scoops_asym is not None and scoops_asym.is_valid
    asym_radii = [round(f.radius, 4) for f in scoops_asym.faces().filter_by(GeomType.CYLINDER) if f.radius is not None]
    for expected_r in (5.0, 6.0, 8.0, 10.0):
        assert any(abs(r - expected_r) < 1e-3 for r in asym_radii)

    p_bowl = GridfinityBinParams(
        core=CoreParams(grid_x=2, grid_y=1, grid_z=3),
        scoop=ScoopParams(enabled=True, style="bowl", bowl_radius=8.0),
    )
    scoops_bowl = create_compartment_scoops(p_bowl)
    assert scoops_bowl is not None and scoops_bowl.is_valid and scoops_bowl.volume > 100.0
    bowl_bin = create_gridfinity_bin(p_bowl)
    assert bowl_bin.is_valid and len(bowl_bin.solids()) == 1
    print(f"✓ Confirmed directional 4-wall scoop radii & 360° 'bowl' mode (r={p_bowl.scoop.bowl_radius}mm)")

    # Verify auto-calculated label fins vs manual override
    labels_auto_3 = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=1, grid_y=1), label=LabelHolderParams(fin_count=None, fin_max_span=12.0)))
    labels_manual_3 = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=1, grid_y=1), label=LabelHolderParams(fin_count=3)))
    labels_manual_0 = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=1, grid_y=1), label=LabelHolderParams(fin_count=0)))
    assert labels_auto_3 is not None and labels_manual_3 is not None and labels_manual_0 is not None
    assert abs(labels_auto_3.volume - labels_manual_3.volume) < 1e-3
    assert labels_auto_3.volume > labels_manual_0.volume + 10.0
    print("✓ Confirmed fin_count auto-calculation and manual override")

    # 3. Test full composed default bin
    expected_x1 = p1.core.grid_x * p1.core.unit_size - p1.core.grid_clearance
    expected_y1 = p1.core.grid_y * p1.core.unit_size - p1.core.grid_clearance
    expected_top_z = p1.core.grid_z * p1.core.unit_z + p1.stacking_lip.height
    bin1 = create_gridfinity_bin(p1)
    bbox1 = bin1.bounding_box()
    assert bin1.is_valid and len(bin1.solids()) == 1
    assert abs(bbox1.size.X - expected_x1) < 0.05
    assert abs(bbox1.size.Y - expected_y1) < 0.05
    assert abs(bbox1.size.Z - expected_top_z) < 0.05

    for placement in ("center", "left", "right", "per_column"):
        p_placement = GridfinityBinParams(
            core=CoreParams(grid_x=2, grid_y=1, grid_z=3),
            dividers=DividersParams(enabled=False),
            label=LabelHolderParams(placement=placement, units=1),
        )
        lh_part = create_label_holders(p_placement)
        assert lh_part is not None and lh_part.is_valid
        z_top = p_placement.core.grid_z * p_placement.core.unit_z
        area_roof = sum(f.area for f in section(lh_part, Plane.XY.offset(z_top - 0.3)).faces())
        area_slot = sum(f.area for f in section(lh_part, Plane.XY.offset(z_top - 1.1)).faces())
        assert area_roof > area_slot + 5.0

    lh_3u_col1 = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=3, grid_y=1), label=LabelHolderParams(units=1, column=1)))
    lh_3u_left = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=3, grid_y=1), label=LabelHolderParams(units=1, placement="left")))
    assert abs(lh_3u_col1.volume - lh_3u_left.volume) < 1e-3

    lh_3u_col3 = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=3, grid_y=1), label=LabelHolderParams(units=1, column=3)))
    lh_3u_right = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=3, grid_y=1), label=LabelHolderParams(units=1, placement="right")))
    assert abs(lh_3u_col3.volume - lh_3u_right.volume) < 1e-3

    lh_compact = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=3, grid_y=1), label=LabelHolderParams(units=1, placement="left", shelf_full_width=False)))
    lh_full = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=3, grid_y=1), label=LabelHolderParams(units=1, placement="left", shelf_full_width=True)))
    assert lh_compact.bounding_box().size.X < 45.0
    assert lh_full.bounding_box().size.X > 115.0

    bin_compact = create_gridfinity_bin(
        GridfinityBinParams(core=CoreParams(grid_x=3, grid_y=1, grid_z=3), label=LabelHolderParams(units=1, placement="center", shelf_full_width=False))
    )
    assert bin_compact.is_valid and len(bin_compact.solids()) == 1

    lh_2u = create_label_holders(GridfinityBinParams(core=CoreParams(grid_x=2, grid_y=1), label=LabelHolderParams(placement="center", units=2)))
    assert lh_2u.bounding_box().size.X > 75.0
    print(f"✓ Test 1 Passed: Default {p1.core.grid_x}x{p1.core.grid_y}x{p1.core.grid_z}u bin & label modes verified")

    # 4. Large overhang on scooped wall
    p_ov = GridfinityBinParams(
        core=CoreParams(grid_x=1, grid_y=1, grid_z=3),
        dividers=DividersParams(enabled=False),
        overhang=OverhangParams(enabled=True, front=12.0),
        scoop=ScoopParams(enabled=True, front_radius=10.0, back_radius=6.0),
    )
    bin_ov = create_gridfinity_bin(p_ov)
    assert bin_ov.is_valid and len(bin_ov.solids()) == 1
    sec_faces = section(bin_ov, Plane.XY.offset(10.0)).faces()
    assert len(sec_faces) == 1 and len(sec_faces[0].wires()) == 2
    print("✓ Test 2 Passed: 1x1x3 bin with 12mm front overhang + dual scoops verified")

    # 5. Custom unit_z, dual scoops, dividers, overhangs (2x2x4)
    p2 = GridfinityBinParams(
        core=CoreParams(grid_x=2, grid_y=2, grid_z=4, unit_z=8.0),
        scoop=ScoopParams(enabled=True, front_radius=8.0, back_radius=5.0),
        dividers=DividersParams(enabled=True, x=1, y=1),
        overhang=OverhangParams(enabled=True, front=5.0, right=3.0),
    )
    bin2 = create_gridfinity_bin(p2)
    bbox2 = bin2.bounding_box()
    assert bin2.is_valid and len(bin2.solids()) == 1
    assert abs(bbox2.size.X - (2 * 42.0 - 0.5 + 3.0)) < 0.05
    assert abs(bbox2.size.Y - (2 * 42.0 - 0.5 + 5.0)) < 0.05
    assert abs(bbox2.size.Z - (4 * 8.0 + p2.stacking_lip.height)) < 0.05
    print(f"✓ Test 3 Passed: 2x2x4 subdivided overhang bin verified ({bbox2.size.X:.2f}x{bbox2.size.Y:.2f}x{bbox2.size.Z:.2f}mm)")

    print("\nAll Gridfinity bin validation checks passed!")


if __name__ == "__main__":
    validate()
