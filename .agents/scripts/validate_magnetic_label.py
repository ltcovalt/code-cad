import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "magnetic_label")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from magnetic_label import (
    MagneticLabelParams,
    build_magnetic_label,
    batch_generate,
    export_label_files,
    TextMode,
)

def test_all_variations():
    print("Running comprehensive validation tests...")

    # Test 1: Auto-size embossed with border rim
    p1 = MagneticLabelParams(
        text="METRIC BOLTS",
        font_size=10.0,
        text_mode="embossed",
        auto_size=True,
        border_rim=True,
        border_width=1.2,
    )
    res1 = build_magnetic_label(p1)
    assert res1.base_part.is_valid
    assert len(res1.magnet_positions) >= 2
    print(f"✓ Test 1 Passed: Embossed + Border Rim ({res1.actual_width:.1f}x{res1.actual_height:.1f}mm)")

    # Test 2: Static dimensions debossed with left alignment
    p2 = MagneticLabelParams(
        text="DRAWER 1",
        font_size=8.0,
        text_align="left",
        text_offset_y=0.5,
        text_mode="debossed",
        auto_size=False,
        width=60.0,
        height=20.0,
        corner_radius=2.0,
        magnet_count=2,
    )
    res2 = build_magnetic_label(p2)
    assert res2.base_part.is_valid
    assert res2.actual_width == 60.0
    assert res2.actual_height == 20.0
    print(f"✓ Test 2 Passed: Static Debossed with Left Alignment ({res2.actual_width}x{res2.actual_height}mm)")

    # Test 2b: Static dimensions with right alignment
    p2b = MagneticLabelParams(
        text="VOLTAGE",
        font_size=8.0,
        text_align="right",
        text_mode="embossed",
        auto_size=False,
        width=70.0,
        height=20.0,
    )
    res2b = build_magnetic_label(p2b)
    assert res2b.base_part.is_valid
    print(f"✓ Test 2b Passed: Static Embossed with Right Alignment ({res2b.actual_width}x{res2b.actual_height}mm)")

    # Test 3: Flush / Inlay multi-color mode with 8mm magnets
    p3 = MagneticLabelParams(
        text="RESISTORS",
        font_size=11.0,
        text_mode="flush",
        magnet_diameter=8.0,
        magnet_thickness=3.0,
        magnet_clearance=0.2,
    )
    res3 = build_magnetic_label(p3)
    assert res3.base_part.is_valid
    assert res3.text_part is not None
    assert res3.text_part.is_valid
    print(f"✓ Test 3 Passed: Flush Inlay (Base vol: {res3.base_part.volume:.1f}, Inlay vol: {res3.text_part.volume:.1f})")

    # Test 4: Single magnet small label
    p4 = MagneticLabelParams(
        text="OFF",
        font_size=8.0,
        min_width=25.0,
        min_height=15.0,
        magnet_count=1,
    )
    res4 = build_magnetic_label(p4)
    assert len(res4.magnet_positions) == 1
    assert res4.magnet_positions[0] == (0.0, 0.0)
    print("✓ Test 4 Passed: Single Centered Magnet")

    # Test 5: Exporting STEP & STL
    temp_dir = "/tmp/cad_label_test"
    files = export_label_files(res3, output_dir=temp_dir, do_export_step=True, do_export_stl=True)
    assert len(files) == 5  # base.step, base.stl, text.step, multibody.step, text.stl
    for f in files:
        assert os.path.exists(f)
        os.remove(f)
    os.rmdir(temp_dir)
    print("✓ Test 5 Passed: Exporting STEP and STL files")

    # Test 6: Batch Generation with shared defaults
    batch_items = ["M3 SCREWS", "M4 SCREWS", ("CUSTOM OVERRIDE", {"font_size": 14.0})]
    batch_results = batch_generate(
        labels=batch_items,
        defaults=p1,
        output_dir="/tmp/batch_test",
        do_export_stl=False,
        preview_grid=False,
    )
    assert len(batch_results) == 3
    assert batch_results[0].params.text == "M3 SCREWS"
    assert batch_results[2].params.font_size == 14.0
    print(f"✓ Test 6 Passed: Batch Generation ({len(batch_results)} labels)")

    print("\nALL VALIDATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all_variations()
