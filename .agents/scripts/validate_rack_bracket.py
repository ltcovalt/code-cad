"""
Comprehensive validation script for parametric rack_bracket.py
Tests 1U, 2U, 3U, 4U brackets, different cutout styles, and custom parameters.
"""

import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "rack_bracket")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from rack_bracket import (
    RackBracketParams,
    create_rack_bracket,
)


def validate():
    print("Beginning validation of unified rack_bracket...")

    # Test 1: 1U Bracket
    p1 = RackBracketParams(u_count=1, cutout_style="none")
    b1 = create_rack_bracket(p1)
    bbox1 = b1.bounding_box()
    expected_h1 = 1 * 44.45 - 1.2
    assert abs(bbox1.size.Z - expected_h1) < 0.05, f"1U height mismatch: {bbox1.size.Z} vs {expected_h1}"
    assert b1.is_valid, "1U bracket solid is invalid"
    print(f"✓ 1U Bracket passed: height={bbox1.size.Z:.2f}mm, valid={b1.is_valid}")

    # Test 2: 2U Bracket with hex cutout (default)
    p2 = RackBracketParams(u_count=2, cutout_style="hex")
    b2 = create_rack_bracket(p2)
    bbox2 = b2.bounding_box()
    expected_h2 = 2 * 44.45 - 1.2  # 87.7 mm
    assert abs(bbox2.size.Z - expected_h2) < 0.05, f"2U height mismatch: {bbox2.size.Z} vs {expected_h2}"
    assert b2.is_valid, "2U bracket solid is invalid"
    print(f"✓ 2U Hex Bracket passed: height={bbox2.size.Z:.2f}mm, valid={b2.is_valid}")

    # Test 4: 3U Bracket with hex cutout
    p3 = RackBracketParams(u_count=3, cutout_style="hex")
    b3 = create_rack_bracket(p3)
    bbox3 = b3.bounding_box()
    expected_h3 = 3 * 44.45 - 1.2  # 132.15 mm
    assert abs(bbox3.size.Z - expected_h3) < 0.05, f"3U height mismatch: {bbox3.size.Z} vs {expected_h3}"
    assert b3.is_valid, "3U bracket solid is invalid"
    print(f"✓ 3U Hex Bracket passed: height={bbox3.size.Z:.2f}mm, valid={b3.is_valid}")

    # Test 5: 4U Bracket with window cutout
    p4 = RackBracketParams(u_count=4, cutout_style="window")
    b4 = create_rack_bracket(p4)
    bbox4 = b4.bounding_box()
    expected_h4 = 4 * 44.45 - 1.2  # 176.60 mm
    assert abs(bbox4.size.Z - expected_h4) < 0.05, f"4U height mismatch: {bbox4.size.Z} vs {expected_h4}"
    assert b4.is_valid, "4U bracket solid is invalid"
    print(f"✓ 4U Window Bracket passed: height={bbox4.size.Z:.2f}mm, valid={b4.is_valid}")

    # Test 6: Custom length and thickness
    p_custom = RackBracketParams(u_count=2, bracket_length=120.0, thickness=4.0, cutout_style="none")
    b_custom = create_rack_bracket(p_custom)
    bbox_custom = b_custom.bounding_box()
    assert abs(bbox_custom.size.X - 120.0) < 0.05
    assert b_custom.is_valid
    print(f"✓ Custom length & thickness passed: length={bbox_custom.size.X:.2f}mm, valid={b_custom.is_valid}")

    print("All validation tests passed successfully!")


if __name__ == "__main__":
    validate()
