"""
Comprehensive test and validation script for the parametric lid generator.
"""

import copy
import os
import sys
import tempfile

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
models_dir = os.path.join(repo_root, "models", "container_lid")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from build123d import export_step, export_stl
from container_lid import (
    ANCHOR_PRESETS,
    ContainerLidParams,
    CoreParams,
    InnerSealParams,
    LidStructureParams,
    PYREX_PRESETS,
    PullTabParams,
    StackingRimParams,
    create_container_lid,
)


def run_lid_validation():
    print("Running Parametric Lid Generator Validation Suite")

    # Test 1: Round TPU Lid (Pyrex 4-cup preset)
    p1 = copy.deepcopy(PYREX_PRESETS["pyrex_round_4_cup"])
    p1.core.material = "tpu"
    lid1 = create_container_lid(p1)
    assert lid1.is_valid and lid1.volume > 20000
    print(f"✓ Test 1 Passed! Volume = {lid1.volume:.1f} mm^3")

    # Test 2: Rectangular TPU Lid (Pyrex 3-cup preset)
    p2 = copy.deepcopy(PYREX_PRESETS["pyrex_rect_3_cup"])
    p2.core.material = "tpu"
    lid2 = create_container_lid(p2)
    assert lid2.is_valid and lid2.volume > 30000
    print(f"✓ Test 2 Passed! Volume = {lid2.volume:.1f} mm^3")

    # Test 3: Round PCTG Lid with Flex Slots
    p3 = ContainerLidParams(
        core=CoreParams(shape="round", diameter=150.0, rim_lip_height=5.2, glass_wall_thickness=4.2, material="pctg"),
        structure=LidStructureParams(skirt_height=10.5),
    )
    lid3 = create_container_lid(p3)
    eff_p3 = p3.get_effective_params()
    assert lid3.is_valid and eff_p3.flex_slots.enabled is True
    assert eff_p3.core.fit_tolerance == 0.2 and eff_p3.snap_bead.depth == 0.35
    print(f"✓ Test 3 Passed! Volume = {lid3.volume:.1f} mm^3")

    # Test 4: Rectangular PCTG Lid with Flex Slots
    p4 = ContainerLidParams(
        core=CoreParams(shape="rectangular", length=182.0, width=132.0, corner_radius=20.0, rim_lip_height=5.0, glass_wall_thickness=4.0, material="pctg"),
        structure=LidStructureParams(skirt_height=10.0),
    )
    lid4 = create_container_lid(p4)
    assert lid4.is_valid and p4.get_effective_params().flex_slots.enabled is True
    print(f"✓ Test 4 Passed! Volume = {lid4.volume:.1f} mm^3")

    # Test 5: Square Container Lid
    p5 = ContainerLidParams(
        core=CoreParams(shape="rectangular", material="tpu", length=140.0, width=140.0, corner_radius=15.0, rim_lip_height=5.0),
    )
    lid5 = create_container_lid(p5)
    assert lid5.is_valid
    print(f"✓ Test 5 Passed! Volume = {lid5.volume:.1f} mm^3")

    # Test 6: Minimal Flat Custom Round Lid
    p6 = ContainerLidParams(
        core=CoreParams(shape="round", material="tpu", diameter=80.0),
        structure=LidStructureParams(skirt_height=7.0),
        inner_seal=InnerSealParams(enabled=False),
        stacking_rim=StackingRimParams(enabled=False),
        pull_tab=PullTabParams(enabled=True),
    )
    lid6 = create_container_lid(p6)
    assert lid6.is_valid
    print(f"✓ Test 6 Passed! Volume = {lid6.volume:.1f} mm^3")

    # Test 7: Export STEP and STL
    with tempfile.TemporaryDirectory() as tmp_dir:
        step_f = os.path.join(tmp_dir, "test_lid_export.step")
        stl_f = os.path.join(tmp_dir, "test_lid_export.stl")
        export_step(lid1, step_f)
        export_stl(lid1, stl_f)
        assert os.path.getsize(step_f) > 1000 and os.path.getsize(stl_f) > 1000
    print("✓ Test 7 Passed! STEP and STL export verified")

    # Test 8: Anchor Hocking Preset
    lid8 = create_container_lid(ANCHOR_PRESETS["anchor_round_4_cup"])
    assert lid8.is_valid
    print(f"✓ Test 8 Passed! Volume = {lid8.volume:.1f} mm^3")

    # Test 9: Inch inputs conversion
    p9 = ContainerLidParams(core=CoreParams(shape="round", diameter_in=6.0))
    eff9 = p9.get_effective_params()
    assert abs(eff9.core.diameter - 152.4) < 1e-4
    assert create_container_lid(p9).is_valid
    print(f"✓ Test 9 Passed! 6.0 in -> {eff9.core.diameter:.1f} mm")

    # Test 10: Test Ring Gauge Mode
    p10 = ContainerLidParams(core=CoreParams(shape="round", diameter=150.0, test_ring=True))
    lid10 = create_container_lid(p10)
    assert lid10.is_valid and lid10.volume < lid1.volume * 0.45
    print(f"✓ Test 10 Passed! Test ring volume = {lid10.volume:.1f} mm^3")

    # Test 11: Smooth Round Container Lid
    p11 = ContainerLidParams(core=CoreParams(shape="round", diameter=110.0, rim_style="smooth", material="tpu"))
    eff11 = p11.get_effective_params()
    assert eff11.snap_bead.enabled is False and eff11.core.friction_ribs is True
    assert create_container_lid(p11).is_valid
    print("✓ Test 11 Passed! Smooth round lid verified")

    # Test 12: Smooth Rectangular Container Lid
    p12 = ContainerLidParams(core=CoreParams(shape="rectangular", length=160.0, width=110.0, corner_radius=15.0, rim_style="smooth", material="tpu"))
    assert create_container_lid(p12).is_valid
    print("✓ Test 12 Passed! Smooth rectangular lid verified")

    print("\nALL 12 VALIDATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_lid_validation()
