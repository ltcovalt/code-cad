"""
Comprehensive test and validation script for the parametric lid generator.
Tests:
1. Round TPU lid with snap bead, inner seal ring, stacking rim, and pull tab.
2. Rectangular TPU lid with corner pull tab and inner seal.
3. Round PCTG lid with compliant flexure relief slots.
4. Rectangular PCTG lid with flexure relief slots on all sides.
5. Square lid (equal length and width).
6. Custom dimension overrides (custom diameter, custom skirt height, disabled inner seal).
7. STEP and STL export functionality.
"""

import os
import sys
import tempfile

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
models_dir = os.path.join(repo_root, "models", "container_lid")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from build123d import export_step, export_stl
from container_lid import (
    LidParams,
    PYREX_PRESETS,
    ANCHOR_PRESETS,
    CONTAINER_PRESETS,
    create_lid,
    build_lid,
)


def run_lid_validation():
    print("==================================================")
    print("Running Parametric Lid Generator Validation Suite")
    print("==================================================")

    # Test 1: Round TPU Lid (Pyrex 4-cup preset)
    print("\n[Test 1] Round TPU Lid (Pyrex 4-Cup)...")
    p1 = PYREX_PRESETS["pyrex_round_4_cup"]
    p1.material = "tpu"
    lid1 = build_lid(p1)
    assert lid1.is_valid, "Round TPU lid is invalid"
    assert lid1.volume > 20000, f"Unexpected volume: {lid1.volume}"
    print(f"✓ Passed! Volume = {lid1.volume:.1f} mm^3")

    # Test 2: Rectangular TPU Lid (Pyrex 3-cup preset)
    print("\n[Test 2] Rectangular TPU Lid (Pyrex 3-Cup with Corner Tab)...")
    p2 = PYREX_PRESETS["pyrex_rect_3_cup"]
    p2.material = "tpu"
    lid2 = build_lid(p2)
    assert lid2.is_valid, "Rectangular TPU lid is invalid"
    assert lid2.volume > 30000, f"Unexpected volume: {lid2.volume}"
    print(f"✓ Passed! Volume = {lid2.volume:.1f} mm^3")

    # Test 3: Round PCTG Lid with Flex Slots
    print("\n[Test 3] Round PCTG Lid with Compliant Flexure Slots...")
    p3 = LidParams(
        shape="round",
        diameter=150.0,
        rim_lip_height=5.2,
        glass_wall_thickness=4.2,
        skirt_height=10.5,
        material="pctg",
    )
    lid3 = build_lid(p3)
    eff_p3 = p3.get_effective_params()
    assert lid3.is_valid, "Round PCTG lid is invalid"
    assert eff_p3.flex_slots is True
    assert eff_p3.fit_tolerance == 0.2
    assert eff_p3.retention_bead_depth == 0.35
    print(f"✓ Passed! Volume = {lid3.volume:.1f} mm^3 (PCTG flex relief active)")

    # Test 4: Rectangular PCTG Lid with Flex Slots
    print("\n[Test 4] Rectangular PCTG Lid with Cantilever Flex Slots...")
    p4 = LidParams(
        shape="rectangular",
        length=182.0,
        width=132.0,
        corner_radius=20.0,
        rim_lip_height=5.0,
        glass_wall_thickness=4.0,
        skirt_height=10.0,
        material="pctg",
    )
    lid4 = build_lid(p4)
    eff_p4 = p4.get_effective_params()
    assert lid4.is_valid, "Rectangular PCTG lid is invalid"
    assert eff_p4.flex_slots is True
    print(f"✓ Passed! Volume = {lid4.volume:.1f} mm^3")

    # Test 5: Square Container Lid (Length == Width)
    print("\n[Test 5] Square Container Lid...")
    p5 = LidParams(
        shape="rectangular",
        material="tpu",
        length=140.0,
        width=140.0,
        corner_radius=15.0,
        rim_lip_height=5.0,
    )
    lid5 = build_lid(p5)
    assert lid5.is_valid, "Square lid is invalid"
    print(f"✓ Passed! Volume = {lid5.volume:.1f} mm^3")

    # Test 6: Custom Dimension Overrides (Minimal lid, no seal ring, no stacking rim)
    print("\n[Test 6] Minimal Flat Custom Round Lid...")
    p6 = LidParams(
        shape="round",
        material="tpu",
        diameter=80.0,
        inner_seal_ring=False,
        stacking_rim=False,
        skirt_height=7.0,
        pull_tab=True,
    )
    lid6 = build_lid(p6)
    assert lid6.is_valid, "Minimal custom lid is invalid"
    print(f"✓ Passed! Volume = {lid6.volume:.1f} mm^3")

    # Test 7: Export STEP and STL
    print("\n[Test 7] Verifying STEP and STL file export...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        step_f = os.path.join(tmp_dir, "test_lid_export.step")
        stl_f = os.path.join(tmp_dir, "test_lid_export.stl")
        export_step(lid1, step_f)
        export_stl(lid1, stl_f)
        assert os.path.exists(step_f), "STEP file was not created"
        assert os.path.exists(stl_f), "STL file was not created"
        step_size = os.path.getsize(step_f)
        stl_size = os.path.getsize(stl_f)
        assert step_size > 1000, f"STEP file too small: {step_size} bytes"
        assert stl_size > 1000, f"STL file too small: {stl_size} bytes"
        print(f"✓ Export verified! STEP: {step_size:,} bytes, STL: {stl_size:,} bytes")

    # Test 8: Anchor Hocking Preset
    print("\n[Test 8] Anchor Hocking 4-Cup Round Preset...")
    p8 = ANCHOR_PRESETS["anchor_round_4_cup"]
    lid8 = build_lid(p8)
    assert lid8.is_valid, "Anchor Hocking lid is invalid"
    print(f"✓ Passed! Volume = {lid8.volume:.1f} mm^3")

    # Test 9: Inch inputs (e.g. 6.0 inch diameter)
    print("\n[Test 9] Inch inputs conversion...")
    p9 = LidParams(shape="round", diameter_in=6.0)
    eff9 = p9.get_effective_params()
    assert abs(eff9.diameter - 152.4) < 1e-4, f"Expected 152.4mm, got {eff9.diameter}"
    lid9 = build_lid(p9)
    assert lid9.is_valid, "Inch-specified lid is invalid"
    print(f"✓ Passed! 6.0 in -> {eff9.diameter:.1f} mm, Volume = {lid9.volume:.1f} mm^3")

    # Test 10: Test Ring Gauge Mode (low filament fit-check)
    print("\n[Test 10] Test Ring Gauge Mode (8-minute fit-check)...")
    p10 = LidParams(shape="round", diameter=150.0, test_ring=True)
    lid10 = build_lid(p10)
    assert lid10.is_valid, "Test ring is invalid"
    assert lid10.volume < lid1.volume * 0.45, "Test ring volume should be significantly lower than full lid"
    print(f"✓ Passed! Full lid volume = {lid1.volume:.1f} mm^3 vs Test ring = {lid10.volume:.1f} mm^3 (uses ~65% less filament!)")

    # Test 11: Smooth Round Container Lid (No rim lip, uses friction wiper ribs)
    print("\n[Test 11] Smooth Round Container Lid (rim_style='smooth')...")
    p11 = LidParams(
        shape="round",
        diameter=110.0,
        rim_style="smooth",
        material="tpu",
    )
    eff11 = p11.get_effective_params()
    assert eff11.snap_ridge is False, "Snap ridge should be disabled for smooth rim"
    assert eff11.friction_ribs is True, "Friction ribs should be auto-enabled for smooth rim"
    lid11 = build_lid(p11)
    assert lid11.is_valid, "Smooth round lid is invalid"
    print(f"✓ Passed! Volume = {lid11.volume:.1f} mm^3 (Wiper friction seal active)")

    # Test 12: Smooth Rectangular Container Lid (No rim lip)
    print("\n[Test 12] Smooth Rectangular Container Lid (rim_style='smooth')...")
    p12 = LidParams(
        shape="rectangular",
        length=160.0,
        width=110.0,
        corner_radius=15.0,
        rim_style="smooth",
        material="tpu",
    )
    lid12 = build_lid(p12)
    assert lid12.is_valid, "Smooth rectangular lid is invalid"
    print(f"✓ Passed! Volume = {lid12.volume:.1f} mm^3 (Wiper friction seal active)")

    print("\n==================================================")
    print("ALL 12 VALIDATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_lid_validation()
