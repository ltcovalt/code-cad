"""
Validation script for models/c_clip_spacer/c_clip_spacer.py
Validates parametric C-clip spacer generation across dimensions, inside-edge
removal cutout configurations, thin-wall/thin-height clamping, shaft clearance,
input validation guards, and STL/STEP exports.
"""

import os
import sys
import tempfile

from build123d import Align, Cylinder, export_step, export_stl

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "c_clip_spacer")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from c_clip_spacer import CClipSpacerParams, create_c_clip_spacer


def validate():
    print("Beginning validation of c_clip_spacer generator...")

    # --------------------------------------------------------------------------
    # Test 1: Default 12mm Shaft C-Clip Spacer with Inside Removal Cutout
    # --------------------------------------------------------------------------
    p_default = CClipSpacerParams()
    part_default = create_c_clip_spacer(p_default)
    bbox = part_default.bounding_box()
    assert part_default.is_valid, "Default C-clip spacer is invalid"
    assert len(part_default.solids()) == 1, f"Expected 1 solid, got {len(part_default.solids())}"
    assert abs(bbox.size.Z - p_default.thickness) < 1e-4, (
        f"Thickness mismatch: {bbox.size.Z} vs {p_default.thickness}"
    )
    assert abs(bbox.size.Y - p_default.outside_diameter) < 1e-3, (
        f"OD mismatch along Y: {bbox.size.Y} vs {p_default.outside_diameter}"
    )
    assert abs(bbox.min.X + p_default.outside_diameter / 2.0) < 1e-3, (
        f"Spine X min mismatch: {bbox.min.X} vs {-p_default.outside_diameter / 2.0}"
    )

    # Verify nominal shaft fits cleanly inside bore without intersection
    shaft = Cylinder(
        radius=p_default.inside_diameter / 2.0,
        height=p_default.thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    interference = part_default & shaft
    assert interference.volume < 1e-6, f"Spacer interferes with nominal shaft: vol={interference.volume}"

    # Verify removal notch removed material compared to plain variant
    p_plain = CClipSpacerParams(removal_notch_enabled=False)
    part_plain = create_c_clip_spacer(p_plain)
    assert part_plain.is_valid, "Plain C-clip spacer is invalid"
    assert part_default.volume < part_plain.volume - 1.0, (
        f"Notched volume ({part_default.volume:.2f}) should be noticeably smaller than plain ({part_plain.volume:.2f})"
    )

    # Verify notch pocket probe at spine (-X) does NOT intersect solid
    r_in = (p_default.inside_diameter + p_default.fit_clearance) / 2.0
    probe_x = -(r_in + p_default.removal_notch_depth * 0.5)
    probe = Cylinder(radius=0.25, height=p_default.thickness, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(
        (probe_x, 0.0, 0.0)
    )
    assert (part_default & probe).volume < 1e-6, "Expected open space inside spine removal cutout"
    assert (part_plain & probe).volume > 0.5, "Expected solid material at spine when removal cutout is disabled"
    print(
        f"✓ Test 1 Passed: Default {p_default.inside_diameter:g}x{p_default.outside_diameter:g}x"
        f"{p_default.thickness:g}mm spacer (valid={part_default.is_valid}, "
        f"notched_vol={part_default.volume:.2f} < plain_vol={part_plain.volume:.2f})"
    )

    # --------------------------------------------------------------------------
    # Test 2: Thin Spacer & Thin Chamfer/Fillet Auto-Clamping
    # --------------------------------------------------------------------------
    p_thin = CClipSpacerParams(
        thickness=0.8,
        inside_diameter=8.0,
        outside_diameter=14.0,
        removal_notch_width=3.0,
        removal_notch_depth=1.0,
        tip_fillet=2.0,
        removal_notch_fillet=2.0,
        edge_chamfer=0.5,
    )
    part_thin = create_c_clip_spacer(p_thin)
    bbox_thin = part_thin.bounding_box()
    assert part_thin.is_valid, "Thin clamped C-clip spacer is invalid"
    assert abs(bbox_thin.size.Z - 0.8) < 1e-4, f"Thin Z mismatch: {bbox_thin.size.Z}"
    print(f"✓ Test 2 Passed: Thin 0.8mm spacer with auto-clamped fillets/chamfers (valid={part_thin.is_valid})")

    # --------------------------------------------------------------------------
    # Test 3: Small Shaft with Thick Wall & Deep Notch (Checks Bore Center Trim)
    # --------------------------------------------------------------------------
    p_deep = CClipSpacerParams(
        thickness=8.0,
        inside_diameter=5.0,
        outside_diameter=24.0,
        fit_clearance=0.0,
        opening_angle=135.0,
        removal_notch_width=2.5,
        removal_notch_depth=3.5,
        removal_notch_angle=180.0,
    )
    part_deep = create_c_clip_spacer(p_deep)
    assert part_deep.is_valid, "Deep-notch thick-wall spacer is invalid"
    assert len(part_deep.solids()) == 1, "Expected single solid for deep-notch spacer"
    print(f"✓ Test 3 Passed: Small-ID thick-wall deep-notch 5x24x8mm spacer (valid={part_deep.is_valid})")

    # --------------------------------------------------------------------------
    # Test 4: Rotated Cutout & Wide Snap Opening (160 deg) without Chamfer
    # --------------------------------------------------------------------------
    p_rot = CClipSpacerParams(
        thickness=3.5,
        inside_diameter=12.7,
        outside_diameter=25.4,
        opening_angle=160.0,
        tip_fillet=0.8,
        removal_notch_width=4.0,
        removal_notch_depth=1.5,
        removal_notch_angle=135.0,
        edge_chamfer_enabled=False,
    )
    part_rot = create_c_clip_spacer(p_rot)
    assert part_rot.is_valid, "Rotated notch wide-opening spacer is invalid"
    assert abs(part_rot.bounding_box().size.Z - 3.5) < 1e-4
    print(f"✓ Test 4 Passed: 1/2in rod spacer with 160 deg opening & 135 deg notch (valid={part_rot.is_valid})")

    # --------------------------------------------------------------------------
    # Test 5: Parameter Validation Guards
    # --------------------------------------------------------------------------
    invalid_cases = [
        dict(thickness=0.0),
        dict(inside_diameter=12.0, outside_diameter=12.0),
        dict(opening_angle=180.0),
        dict(inside_diameter=12.0, outside_diameter=22.0, removal_notch_width=4.0, removal_notch_depth=4.9),
        dict(removal_notch_angle=10.0),
    ]
    for kwargs in invalid_cases:
        raised = False
        try:
            create_c_clip_spacer(CClipSpacerParams(**kwargs))
        except ValueError:
            raised = True
        assert raised, f"Expected ValueError for invalid params: {kwargs}"
    print(f"✓ Test 5 Passed: All {len(invalid_cases)} invalid parameter guards raised ValueError")

    # --------------------------------------------------------------------------
    # Test 6: STL and STEP Export Verification
    # --------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        stl_path = os.path.join(tmpdir, "c_clip_spacer_test.stl")
        step_path = os.path.join(tmpdir, "c_clip_spacer_test.step")
        export_stl(part_default, stl_path)
        export_step(part_default, step_path)
        assert os.path.getsize(stl_path) > 100, "STL export file is unexpectedly small"
        assert os.path.getsize(step_path) > 100, "STEP export file is unexpectedly small"
    print("✓ Test 6 Passed: STL and STEP export succeeded")

    print("\nALL C-CLIP SPACER VALIDATION CHECKS PASSED!")


if __name__ == "__main__":
    validate()
