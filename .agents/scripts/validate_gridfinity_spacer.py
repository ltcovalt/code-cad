"""
Validation script for models/gridfinity_spacer/spacer.py
Validates length=0 straight spacer generation, independent leg dimensions,
corner pieces, hollow underside mode, and error handling.
"""

import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "gridfinity_spacer")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from spacer import SpacerParams, create_spacer


def validate():
    print("Beginning validation of gridfinity spacer generator...")

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
        inner_corner_radius=4.0,  # Standard Gridfinity R4
        edge_radius=1.0,
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
    print("\nAll Gridfinity Spacer validation tests passed successfully!")


if __name__ == "__main__":
    validate()
