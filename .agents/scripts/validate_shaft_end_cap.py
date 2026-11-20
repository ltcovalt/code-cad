"""
Validation script for models/shaft_end_cap/shaft_end_cap.py
Validates parametric shaft end cap generation across various shaft sizes,
end cap styles (dome, flat, chamfer, round), custom dome heights, grip grooves,
and bounding box / solid integrity.
"""

import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "shaft_end_cap")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from shaft_end_cap import (
    CapTipParams,
    CoreParams,
    FlangeParams,
    GripGroovesParams,
    ShaftEndCapParams,
    VentChannelParams,
    VentHoleParams,
    create_shaft_end_cap,
)


def validate():
    print("Beginning validation of shaft_end_cap generator...")

    # Test 1: 1/2" (12.7mm) Rod Cap with Semi-Spherical Dome
    p1 = ShaftEndCapParams(
        core=CoreParams(shaft_diameter=12.7),
        flange=FlangeParams(diameter=32.0, thickness=3.5),
        cap=CapTipParams(style="dome", dome_height=None),
    )
    cap1 = create_shaft_end_cap(p1)
    bbox1 = cap1.bounding_box()
    assert cap1.is_valid, "1/2in dome cap is invalid"
    expected_h1 = p1.core.collar_length + p1.flange.thickness + p1.flange_radius
    assert abs(bbox1.size.Z - expected_h1) < 0.1, (
        f"Test 1 height mismatch: {bbox1.size.Z} vs expected {expected_h1}"
    )
    assert abs(bbox1.size.X - p1.flange.diameter) < 0.1, (
        f"Test 1 width mismatch: {bbox1.size.X} vs expected {p1.flange.diameter}"
    )
    print(f"✓ Test 1 Passed: 1/2in dome cap (H={bbox1.size.Z:.2f}mm, Dia={bbox1.size.X:.2f}mm, valid={cap1.is_valid})")

    # Test 2: Custom Low-Profile Dome (6.0mm dome height)
    p2 = ShaftEndCapParams(
        core=CoreParams(shaft_diameter=12.7),
        cap=CapTipParams(style="dome", dome_height=6.0),
    )
    cap2 = create_shaft_end_cap(p2)
    bbox2 = cap2.bounding_box()
    assert cap2.is_valid, "Low-profile dome cap is invalid"
    expected_h2 = p2.core.collar_length + p2.flange.thickness + 6.0
    assert abs(bbox2.size.Z - expected_h2) < 0.1, (
        f"Test 2 height mismatch: {bbox2.size.Z} vs expected {expected_h2}"
    )
    print(f"✓ Test 2 Passed: Custom 6mm dome cap (H={bbox2.size.Z:.2f}mm, valid={cap2.is_valid})")

    # Test 3: Flat End Cap Style
    p3 = ShaftEndCapParams(
        core=CoreParams(shaft_diameter=12.7),
        flange=FlangeParams(front_radius=0.8, rear_radius=1.2),
        cap=CapTipParams(style="flat"),
    )
    cap3 = create_shaft_end_cap(p3)
    bbox3 = cap3.bounding_box()
    assert cap3.is_valid, "Flat cap is invalid"
    expected_h3 = p3.core.collar_length + p3.flange.thickness
    assert abs(bbox3.size.Z - expected_h3) < 0.1, (
        f"Test 3 height mismatch: {bbox3.size.Z} vs expected {expected_h3}"
    )
    print(f"✓ Test 3 Passed: Flat end cap (H={bbox3.size.Z:.2f}mm, valid={cap3.is_valid})")

    # Test 4: Chamfer / Conical End Cap Style
    p4 = ShaftEndCapParams(
        core=CoreParams(shaft_diameter=12.7),
        flange=FlangeParams(rear_radius=1.0),
        cap=CapTipParams(style="chamfer", chamfer_length=3.0),
    )
    cap4 = create_shaft_end_cap(p4)
    bbox4 = cap4.bounding_box()
    assert cap4.is_valid, "Chamfer cap is invalid"
    expected_h4 = p4.core.collar_length + p4.flange.thickness + 3.0
    assert abs(bbox4.size.Z - expected_h4) < 0.1, (
        f"Test 4 height mismatch: {bbox4.size.Z} vs expected {expected_h4}"
    )
    print(f"✓ Test 4 Passed: Chamfer end cap (H={bbox4.size.Z:.2f}mm, valid={cap4.is_valid})")

    # Test 5: Round Edge Cap Style
    p5 = ShaftEndCapParams(
        core=CoreParams(shaft_diameter=12.7),
        flange=FlangeParams(front_radius=1.0, rear_radius=1.8),
        cap=CapTipParams(style="round"),
    )
    cap5 = create_shaft_end_cap(p5)
    bbox5 = cap5.bounding_box()
    assert cap5.is_valid, "Round edge cap is invalid"
    expected_h5 = p5.core.collar_length + p5.flange.thickness
    assert abs(bbox5.size.Z - expected_h5) < 0.1, (
        f"Test 5 height mismatch: {bbox5.size.Z} vs expected {expected_h5}"
    )
    print(f"✓ Test 5 Passed: Round edge cap (H={bbox5.size.Z:.2f}mm, valid={cap5.is_valid})")

    # Test 6: Scalloped Grip Grooves & 1-inch (25.4mm) Rod
    p6 = ShaftEndCapParams(
        core=CoreParams(shaft_diameter=25.4, collar_length=25.0),
        flange=FlangeParams(diameter=48.0, thickness=5.0),
        cap=CapTipParams(style="dome"),
        grip_grooves=GripGroovesParams(enabled=True, count=12, radius=1.5),
    )
    cap6 = create_shaft_end_cap(p6)
    bbox6 = cap6.bounding_box()
    assert cap6.is_valid, "1-inch gripped cap is invalid"
    print(f"✓ Test 6 Passed: 1-inch gripped cap (H={bbox6.size.Z:.2f}mm, Dia={bbox6.size.X:.2f}mm, valid={cap6.is_valid})")

    # Test 7: Small 8mm Rod with No Vent Hole
    p7 = ShaftEndCapParams(
        core=CoreParams(shaft_diameter=8.0, collar_length=14.0),
        flange=FlangeParams(diameter=22.0, thickness=3.0),
        cap=CapTipParams(style="dome"),
        vent_hole=VentHoleParams(enabled=False),
    )
    cap7 = create_shaft_end_cap(p7)
    bbox7 = cap7.bounding_box()
    assert cap7.is_valid, "8mm sealed cap is invalid"
    print(f"✓ Test 7 Passed: 8mm sealed cap (H={bbox7.size.Z:.2f}mm, valid={cap7.is_valid})")

    # Test 8: Internal Axial Vent Channel in Collar
    p8 = ShaftEndCapParams(
        core=CoreParams(shaft_diameter=12.7),
        flange=FlangeParams(diameter=40.0, thickness=4.0),
        cap=CapTipParams(style="round"),
        vent_hole=VentHoleParams(enabled=False),
        vent_channel=VentChannelParams(enabled=True, width=1.0, depth=0.6),
    )
    cap8 = create_shaft_end_cap(p8)
    bbox8 = cap8.bounding_box()
    assert cap8.is_valid, "Internal vent channel cap is invalid"
    print(f"✓ Test 8 Passed: Internal vent channel cap (H={bbox8.size.Z:.2f}mm, valid={cap8.is_valid})")

    print("\nAll 8 validation tests passed successfully!")


if __name__ == "__main__":
    validate()
