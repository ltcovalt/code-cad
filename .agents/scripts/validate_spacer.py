"""
Validation script for models/spacer/spacer.py
Validates length=0 straight spacer generation, independent leg dimensions,
corner/T/cross pieces, cutouts, hollow underside mode, and error handling.
"""

import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "spacer")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from spacer import SpacerParams, SpacerCutout, create_spacer


def validate():
    print("Beginning validation of spacer generator...")

    # --------------------------------------------------------------------------
    # Test 1: Corner Spacer (Both leg lengths > 0)
    # Front spacer: 15.5mm width, 100mm length
    # Side spacer:  15.0mm width, 80mm length
    # Shared height: 12.0mm
    # --------------------------------------------------------------------------
    p1 = SpacerParams(
        leg_x_length=100.0,
        leg_x_width=15.5,    # Front width: 15.5 mm
        leg_y_length=80.0,
        leg_y_width=15.0,    # Side width: 15.0 mm
        height=12.0,         # Shared height
        corner_radius=2.5,
        inner_corner_radius=4.0,  # Inside corner R4
        edge_radius=1.0,
        cutouts_enabled=False,
    )
    s1 = create_spacer(p1)
    bbox1 = s1.bounding_box()
    assert s1.is_valid, "Corner spacer is invalid"
    assert abs(bbox1.size.X - 100.0) < 0.05, f"X size mismatch: {bbox1.size.X} vs 100.0"
    assert abs(bbox1.size.Y - 80.0) < 0.05, f"Y size mismatch: {bbox1.size.Y} vs 80.0"
    assert abs(bbox1.size.Z - 12.0) < 0.05, f"Z size mismatch: {bbox1.size.Z} vs 12.0"
    print("[PASS] Test 1: Corner spacer with independent leg widths (15.5mm X, 15.0mm Y) passed")

    # --------------------------------------------------------------------------
    # Test 2: Straight Front Spacer by setting leg_y_length = 0
    # --------------------------------------------------------------------------
    p2 = SpacerParams(
        leg_x_length=150.0,
        leg_x_width=15.5,
        leg_y_length=0.0,    # Implies straight spacer along Leg X
        height=12.0,
        corner_radius=2.0,
        edge_radius=1.0,
        cutouts_enabled=False,
    )
    s2 = create_spacer(p2)
    bbox2 = s2.bounding_box()
    assert s2.is_valid, "Straight front spacer is invalid"
    assert abs(bbox2.size.X - 150.0) < 0.05, f"Length mismatch: {bbox2.size.X}"
    assert abs(bbox2.size.Y - 15.5) < 0.05, f"Width mismatch: {bbox2.size.Y}"
    assert abs(bbox2.size.Z - 12.0) < 0.05, f"Height mismatch: {bbox2.size.Z}"
    print("[PASS] Test 2: Straight front spacer (leg_y_length=0 -> 150 x 15.5 x 12 mm) passed")

    # --------------------------------------------------------------------------
    # Test 3: Straight Side Spacer by setting leg_x_length = 0
    # --------------------------------------------------------------------------
    p3 = SpacerParams(
        leg_x_length=0.0,    # Implies straight spacer along Leg Y
        leg_y_length=120.0,
        leg_y_width=15.0,
        height=12.0,
        corner_radius=2.0,
        edge_radius=1.0,
        cutouts_enabled=False,
    )
    s3 = create_spacer(p3)
    bbox3 = s3.bounding_box()
    assert s3.is_valid, "Straight side spacer is invalid"
    assert abs(bbox3.size.X - 15.0) < 0.05, f"Width mismatch: {bbox3.size.X}"
    assert abs(bbox3.size.Y - 120.0) < 0.05, f"Length mismatch: {bbox3.size.Y}"
    assert abs(bbox3.size.Z - 12.0) < 0.05, f"Height mismatch: {bbox3.size.Z}"
    print("[PASS] Test 3: Straight side spacer (leg_x_length=0 -> 15.0 x 120 x 12 mm) passed")

    # --------------------------------------------------------------------------
    # Test 4: Hollow Underside Mode on Corner Piece
    # --------------------------------------------------------------------------
    p4 = SpacerParams(
        leg_x_length=90.0,
        leg_x_width=18.0,
        leg_y_length=90.0,
        leg_y_width=18.0,
        height=16.0,
        hollow=True,
        wall_thickness=2.0,
        top_thickness=2.0,
        cutouts_enabled=False,
    )
    s4 = create_spacer(p4)
    assert s4.is_valid, "Hollow corner spacer is invalid"
    print(f"[PASS] Test 4: Hollow corner spacer passed (volume={s4.volume:.1f} mm^3)")

    # --------------------------------------------------------------------------
    # Test 5: Chamfer Edge Treatment & Finger Notch on Straight Spacer
    # --------------------------------------------------------------------------
    p5 = SpacerParams(
        leg_x_length=100.0,
        leg_x_width=15.5,
        leg_y_length=0.0,
        height=14.0,
        edge_treatment="chamfer",
        edge_radius=1.2,
        finger_notch=True,
        cutouts_enabled=False,
    )
    s5 = create_spacer(p5)
    assert s5.is_valid, "Chamfered straight spacer with finger notch is invalid"
    print(f"[PASS] Test 5: Chamfered straight spacer with finger notch passed")

    # --------------------------------------------------------------------------
    # Test 6: Sharp Corner Piece (Zero radii)
    # --------------------------------------------------------------------------
    p6 = SpacerParams(
        leg_x_length=70.0,
        leg_x_width=20.0,
        leg_y_length=60.0,
        leg_y_width=15.0,
        height=10.0,
        corner_radius=0.0,
        outer_corner_radius=0.0,
        inner_corner_radius=0.0,
        edge_radius=0.0,
        cutouts_enabled=False,
    )
    s6 = create_spacer(p6)
    assert s6.is_valid
    expected_vol6 = (70.0 * 20.0 + 15.0 * 40.0) * 10.0
    assert abs(s6.volume - expected_vol6) < 0.1, f"Volume mismatch: {s6.volume} vs {expected_vol6}"
    print(f"[PASS] Test 6: Sharp corner piece with independent widths passed (volume={s6.volume:.1f} mm^3)")

    # --------------------------------------------------------------------------
    # Test 7: Error Handling when both leg lengths are 0
    # --------------------------------------------------------------------------
    try:
        create_spacer(SpacerParams(leg_x_length=0.0, leg_y_length=0.0))
        assert False, "Should raise ValueError when both leg lengths are 0"
    except ValueError:
        pass

    # --------------------------------------------------------------------------
    # Test 8: Error Handling when leg length <= perpendicular width on corner
    # --------------------------------------------------------------------------
    try:
        create_spacer(SpacerParams(leg_x_length=15.0, leg_y_width=20.0, leg_y_length=50.0))
        assert False, "Should raise ValueError when leg_x_length <= leg_y_width"
    except ValueError:
        pass

    print("[PASS] Test 7 & 8: Input validation and error handling passed")

    # --------------------------------------------------------------------------
    # Test 9: Sharp Rectangular Through-Cutout (Exact Volume Check)
    # 180 x 15 x 56 mm straight spacer with a 50mm x 20mm through-notch
    # --------------------------------------------------------------------------
    p9_base = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=0.0,
        height=56.0,
        corner_radius=0.0,
        edge_radius=0.0,
        cutouts_enabled=False,
    )
    p9_cut = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=0.0,
        height=56.0,
        corner_radius=0.0,
        edge_radius=0.0,
        cutouts_enabled=True,
        cutouts=[
            SpacerCutout(leg="x", align="center", offset=0.0, length=50.0, height=20.0, shape="rectangle", radius=0.0),
        ],
    )
    s9_base = create_spacer(p9_base)
    s9_cut = create_spacer(p9_cut)
    assert s9_cut.is_valid, "Rectangular through-cutout spacer is invalid"
    removed_vol = s9_base.volume - s9_cut.volume
    expected_removed = 50.0 * 20.0 * 15.0  # 15,000 mm^3
    assert abs(removed_vol - expected_removed) < 0.5, f"Removed volume mismatch: {removed_vol} vs {expected_removed}"
    print(f"[PASS] Test 9: Rectangular through-cutout exact volume verified (removed={removed_vol:.1f} mm^3)")

    # --------------------------------------------------------------------------
    # Test 10: Corner Spacer with Rounded Rectangle Cutouts on Both Legs
    # --------------------------------------------------------------------------
    p10 = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=280.0,
        leg_y_width=15.0,
        height=56.0,
        cutouts_enabled=True,
        cutouts=[
            SpacerCutout(leg="x", align="center", offset=0.0, length=50.0, height=20.0, shape="rectangle", radius=4.0),
            SpacerCutout(leg="y", align="start", offset=100.0, length=40.0, height=15.0, shape="rectangle", radius=3.0),
        ],
    )
    s10 = create_spacer(p10)
    assert s10.is_valid, "Corner spacer with rounded cutouts on both legs is invalid"
    print(f"[PASS] Test 10: Corner spacer with rounded rectangle cutouts on X & Y passed")

    # --------------------------------------------------------------------------
    # Test 11: Circular Cutouts (Semicircle, Shallow Arc, Deep U-Slot)
    # --------------------------------------------------------------------------
    p11 = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=0.0,
        height=56.0,
        cutouts_enabled=True,
        cutouts=[
            SpacerCutout(leg="x", align="start", offset=10.0, length=30.0, height=15.0, shape="circle", radius=0.0),   # Semicircle R15
            SpacerCutout(leg="x", align="start", offset=60.0, length=30.0, height=8.0, shape="circle", radius=20.0),   # Shallow arc
            SpacerCutout(leg="x", align="start", offset=120.0, length=24.0, height=25.0, shape="circle", radius=12.0), # Deep U-slot
        ],
    )
    s11 = create_spacer(p11)
    assert s11.is_valid, "Circular cutouts spacer is invalid"
    print(f"[PASS] Test 11: Circular cutouts (semicircle, shallow arc, deep U-slot) passed")

    # --------------------------------------------------------------------------
    # Test 12: Chamfer / Trapezoid Cutouts (Top & Bottom)
    # --------------------------------------------------------------------------
    p12 = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=0.0,
        height=56.0,
        cutouts_enabled=True,
        cutouts=[
            SpacerCutout(leg="x", align="start", offset=20.0, length=50.0, height=18.0, shape="chamfer", radius=10.0, v_align="top"),
            SpacerCutout(leg="x", align="start", offset=100.0, length=50.0, height=12.0, shape="chamfer", radius=0.0, v_align="bottom"),
        ],
    )
    s12 = create_spacer(p12)
    assert s12.is_valid, "Chamfer top/bottom cutouts spacer is invalid"
    print(f"[PASS] Test 12: Chamfer/trapezoid top and bottom cutouts passed")

    # --------------------------------------------------------------------------
    # Test 13: Partial-Depth Pocket Cutouts (Outer Wall Side & Inner Bin Side)
    # --------------------------------------------------------------------------
    p13 = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=0.0,
        height=56.0,
        corner_radius=0.0,
        edge_radius=0.0,
        cutouts_enabled=True,
        cutouts=[
            SpacerCutout(leg="x", align="start", offset=20.0, length=50.0, height=20.0, depth=6.0, side="outer"),
            SpacerCutout(leg="x", align="start", offset=100.0, length=40.0, height=15.0, depth=5.0, side="inner"),
        ],
    )
    s13 = create_spacer(p13)
    assert s13.is_valid, "Partial-depth pocket cutouts spacer is invalid"
    removed_13 = s9_base.volume - s13.volume
    expected_13 = (50.0 * 20.0 * 6.0) + (40.0 * 15.0 * 5.0)  # 6,000 + 3,000 = 9,000 mm^3
    assert abs(removed_13 - expected_13) < 0.5, f"Partial pocket volume mismatch: {removed_13} vs {expected_13}"
    print(f"[PASS] Test 13: Partial-depth outer & inner pockets exact volume verified (removed={removed_13:.1f} mm^3)")

    # --------------------------------------------------------------------------
    # Test 14: Cutout Error Handling
    # --------------------------------------------------------------------------
    try:
        create_spacer(SpacerParams(
            leg_x_length=100.0,
            leg_y_length=0.0,
            cutouts_enabled=True,
            cutouts=[SpacerCutout(leg="y", align="start", offset=10.0, length=20.0, height=10.0)],
        ))
        assert False, "Should raise ValueError when cutting inactive leg 'y'"
    except ValueError:
        pass

    try:
        create_spacer(SpacerParams(
            leg_x_length=100.0,
            leg_y_length=0.0,
            cutouts_enabled=True,
            cutouts=[SpacerCutout(leg="x", shape="hexagon")],
        ))
        assert False, "Should raise ValueError for unknown cutout shape"
    except ValueError:
        pass

    print("[PASS] Test 14: Cutout input validation and error handling passed")

    # --------------------------------------------------------------------------
    # Test 15: Mirrored / Inverted L-Shape (mirror_x=True, with cutout)
    # --------------------------------------------------------------------------
    p15_orig = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=280.0,
        leg_y_width=15.0,
        height=56.0,
        cutouts_enabled=True,
        cutouts=[SpacerCutout(leg="x", align="start", offset=40.0, length=50.0, height=20.0, radius=3.0)],
        mirror_x=False,
    )
    p15_inv = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=280.0,
        leg_y_width=15.0,
        height=56.0,
        cutouts_enabled=True,
        cutouts=[SpacerCutout(leg="x", align="start", offset=40.0, length=50.0, height=20.0, radius=3.0)],
        mirror_x=True,
    )
    s15_orig = create_spacer(p15_orig)
    s15_inv = create_spacer(p15_inv)
    bb15 = s15_inv.bounding_box()
    assert s15_inv.is_valid, "Mirrored L-shape is invalid"
    assert abs(s15_inv.volume - s15_orig.volume) < 0.5, "Mirrored volume should match original"
    assert abs(bb15.min.X) < 0.05 and abs(bb15.min.Y) < 0.05 and abs(bb15.min.Z) < 0.05, "Mirrored bbox should start at origin"
    assert abs(bb15.size.X - 180.0) < 0.05 and abs(bb15.size.Y - 280.0) < 0.05, "Mirrored bbox size mismatch"
    print(f"[PASS] Test 15: Mirrored L-shape (mirror_x=True) with cutout passed (vol={s15_inv.volume:.1f} mm^3)")

    # --------------------------------------------------------------------------
    # Test 16: T-Shape Spacer (leg_y_align="center") + Cutout on shifted Leg Y
    # --------------------------------------------------------------------------
    p16 = SpacerParams(
        leg_x_length=180.0,
        leg_x_width=15.0,
        leg_y_length=120.0,
        leg_y_width=15.0,
        leg_y_align="center",
        leg_y_offset=-10.0,  # 10mm left of center
        height=40.0,
        inner_corner_radius=4.0,
        edge_radius=1.0,
        cutouts_enabled=True,
        cutouts=[SpacerCutout(leg="y", align="start", offset=40.0, length=30.0, height=15.0, shape="rectangle", radius=2.0)],
    )
    s16 = create_spacer(p16)
    bb16 = s16.bounding_box()
    assert s16.is_valid, "T-shape spacer is invalid"
    assert abs(bb16.size.X - 180.0) < 0.05 and abs(bb16.size.Y - 120.0) < 0.05, "T-shape bbox mismatch"
    print(f"[PASS] Test 16: T-shape spacer (align='center', offset=-10mm) with Leg Y cutout passed")

    # --------------------------------------------------------------------------
    # Test 17: Cross (+) Spacer (both leg_x_align and leg_y_align = "center")
    # --------------------------------------------------------------------------
    p17 = SpacerParams(
        leg_x_length=120.0,
        leg_x_width=15.0,
        leg_y_length=120.0,
        leg_y_width=15.0,
        leg_x_align="center",
        leg_y_align="center",
        height=30.0,
        inner_corner_radius=4.0,
        edge_radius=1.0,
        cutouts_enabled=False,
    )
    s17 = create_spacer(p17)
    assert s17.is_valid, "Cross (+) spacer is invalid"
    print(f"[PASS] Test 17: Cross (+) spacer (align='center' on both legs) passed")

    # --------------------------------------------------------------------------
    # Test 18: End-Aligned L-Shape & Alignment/Offset Bounds Error Handling
    # --------------------------------------------------------------------------
    p18_end = SpacerParams(
        leg_x_length=100.0, leg_x_width=15.0, leg_y_length=100.0, leg_y_width=15.0,
        leg_y_align="end", height=20.0, cutouts_enabled=False,
    )
    s18_end = create_spacer(p18_end)
    assert s18_end.is_valid, "End-aligned L-shape is invalid"

    try:
        create_spacer(SpacerParams(
            leg_x_length=100.0, leg_x_width=15.0, leg_y_length=100.0, leg_y_width=15.0, leg_y_offset=90.0
        ))
        assert False, "Should raise ValueError when leg_y_offset > leg_x_length - leg_y_width"
    except ValueError:
        pass

    try:
        create_spacer(SpacerParams(
            leg_x_length=100.0, leg_x_width=15.0, leg_y_length=100.0, leg_y_width=15.0, leg_y_align="middle"
        ))
        assert False, "Should raise ValueError for invalid leg_y_align"
    except ValueError:
        pass

    print("[PASS] Test 18: End alignment & junction align/offset validation passed")

    # --------------------------------------------------------------------------
    # Test 19: Cutout Entry Rounding & Chamfering (Top & Bottom Border Joins)
    # --------------------------------------------------------------------------
    import math
    p19_sharp_entry = SpacerParams(
        leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0,
        corner_radius=0.0, edge_radius=0.0, cutouts_enabled=True,
        cutouts=[SpacerCutout(leg="x", align="end", offset=15.0, length=50.0, height=16.0, radius=3.0, entry_radius=0.0)],
    )
    p19_fillet_entry = SpacerParams(
        leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0,
        corner_radius=0.0, edge_radius=0.0, cutouts_enabled=True,
        cutouts=[SpacerCutout(leg="x", align="end", offset=15.0, length=50.0, height=16.0, radius=3.0, entry_radius=3.0, entry_treatment="fillet")],
    )
    p19_chamfer_entry = SpacerParams(
        leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0,
        corner_radius=0.0, edge_radius=0.0, cutouts_enabled=True,
        cutouts=[SpacerCutout(leg="x", align="end", offset=15.0, length=50.0, height=16.0, radius=3.0, entry_radius=3.0, entry_treatment="chamfer")],
    )
    p19_bottom_entry = SpacerParams(
        leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0,
        corner_radius=0.0, edge_radius=0.0, cutouts_enabled=True,
        cutouts=[
            SpacerCutout(leg="x", align="start", offset=20.0, v_align="bottom", length=40.0, height=14.0, radius=2.0, entry_radius=3.0, entry_treatment="fillet"),
            SpacerCutout(leg="x", align="start", offset=90.0, v_align="bottom", length=40.0, height=14.0, radius=2.0, entry_radius=3.0, entry_treatment="chamfer"),
        ],
    )
    s19_sharp = create_spacer(p19_sharp_entry)
    s19_fillet = create_spacer(p19_fillet_entry)
    s19_chamfer = create_spacer(p19_chamfer_entry)
    s19_bottom = create_spacer(p19_bottom_entry)
    assert s19_fillet.is_valid and s19_chamfer.is_valid and s19_bottom.is_valid

    # Verify exact math for 2 entry fillets (spandrel area = r^2 - pi*r^2/4 each)
    r_e = 3.0
    expected_fillet_diff = 2.0 * (r_e**2 - math.pi * r_e**2 / 4.0) * 15.0
    actual_fillet_diff = s19_sharp.volume - s19_fillet.volume
    assert abs(actual_fillet_diff - expected_fillet_diff) < 0.2, f"Entry fillet diff mismatch: {actual_fillet_diff} vs {expected_fillet_diff}"

    # Verify exact math for 2 entry chamfers (triangle area = 0.5*r^2 each)
    expected_chamfer_diff = 2.0 * (0.5 * r_e**2) * 15.0
    actual_chamfer_diff = s19_sharp.volume - s19_chamfer.volume
    assert abs(actual_chamfer_diff - expected_chamfer_diff) < 0.2, f"Entry chamfer diff mismatch: {actual_chamfer_diff} vs {expected_chamfer_diff}"

    # Verify user's current default params build cleanly too
    s_default = create_spacer(SpacerParams())
    assert s_default.is_valid, "Current default SpacerParams is invalid"

    print(f"[PASS] Test 19: Cutout entry fillet & chamfer (top & bottom) exact volume verified")

    # --------------------------------------------------------------------------
    # Test 20: Closed Interior Windows & Bolt-Hole Pass-Throughs (v_offset > 0 / v_align='center')
    # --------------------------------------------------------------------------
    p20 = SpacerParams(
        leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0,
        corner_radius=0.0, edge_radius=0.0, cutouts_enabled=True,
        cutouts=[
            SpacerCutout(leg="x", align="start", offset=20.0, v_align="top", v_offset=15.0, length=30.0, height=16.0, shape="rectangle", radius=0.0),
            SpacerCutout(leg="x", align="center", offset=0.0, v_align="center", v_offset=0.0, length=12.0, height=12.0, shape="circle", radius=6.0),
            SpacerCutout(leg="x", align="end", offset=20.0, v_align="bottom", v_offset=10.0, length=24.0, height=14.0, shape="chamfer", radius=3.0),
        ],
    )
    s20 = create_spacer(p20)
    assert s20.is_valid, "Closed interior window/bolt-hole cutouts spacer is invalid"
    # Verify volume removed matches exact analytical sum (rect + circle + octagon)
    rect_v = 30.0 * 16.0 * 15.0
    circ_v = math.pi * 6.0**2 * 15.0
    oct_v = (24.0 * 14.0 - 2.0 * 3.0**2) * 15.0
    expected_removed_20 = rect_v + circ_v + oct_v
    actual_removed_20 = s9_base.volume - s20.volume
    assert abs(actual_removed_20 - expected_removed_20) < 0.5, f"Interior holes volume mismatch: {actual_removed_20} vs {expected_removed_20}"
    print(f"[PASS] Test 20: Closed interior window, circular bolt hole, and chamfered slot exact volume verified")
    print("\nAll Spacer validation tests passed successfully!")


if __name__ == "__main__":
    validate()
