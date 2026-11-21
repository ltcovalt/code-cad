"""
Validation script for models/c_clip/c_clip.py
Validates parametric C-clip generation across dimensions, inside-edge
removal cutout configurations, reinforced outer lobes, thin-wall/thin-height
clamping, shaft clearance, input validation guards, and STL/STEP exports.
"""

import os
import sys
import tempfile

from build123d import Align, Axis, Cylinder, GeomType, export_step, export_stl

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "c_clip")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from c_clip import (
    CClipParams,
    CoreParams,
    EdgeChamferParams,
    JawParams,
    RemovalNotchParams,
    create_c_clip,
)


def validate():
    print("Beginning validation of c_clip generator...")

    # Test 1: Default Shaft C-Clip with Inside Removal Cutout
    p_default = CClipParams()
    part_default = create_c_clip(p_default)
    bbox = part_default.bounding_box()
    assert part_default.is_valid, "Default C-clip is invalid"
    assert len(part_default.solids()) == 1, f"Expected 1 solid, got {len(part_default.solids())}"
    assert abs(bbox.size.Z - p_default.core.thickness) < 1e-4, (
        f"Thickness mismatch: {bbox.size.Z} vs {p_default.core.thickness}"
    )
    assert abs(bbox.size.Y - p_default.core.outside_diameter) < 1e-3, (
        f"OD mismatch along Y: {bbox.size.Y} vs {p_default.core.outside_diameter}"
    )
    assert abs(bbox.min.X + p_default.core.outside_diameter / 2.0) < 1e-3, (
        f"Spine X min mismatch: {bbox.min.X} vs {-p_default.core.outside_diameter / 2.0}"
    )

    # Verify nominal shaft fits cleanly inside bore without intersection
    shaft = Cylinder(
        radius=p_default.core.inside_diameter / 2.0,
        height=p_default.core.thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    interference = part_default & shaft
    assert interference.volume < 1e-6, f"Spacer interferes with nominal shaft: vol={interference.volume}"

    # Verify removal notch removed material compared to plain variant
    p_plain = CClipParams(removal_notch=RemovalNotchParams(enabled=False))
    part_plain = create_c_clip(p_plain)
    assert part_plain.is_valid, "Plain C-clip is invalid"
    assert part_default.volume < part_plain.volume - 1.0, (
        f"Notched volume ({part_default.volume:.2f}) should be noticeably smaller than plain ({part_plain.volume:.2f})"
    )

    # Verify notch pocket probe at spine (-X) does NOT intersect solid
    r_in = (p_default.core.inside_diameter + p_default.core.fit_clearance) / 2.0
    probe_x = -(r_in + p_default.removal_notch.depth * 0.5)
    probe = Cylinder(radius=0.25, height=p_default.core.thickness, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(
        (probe_x, 0.0, 0.0)
    )
    assert (part_default & probe).volume < 1e-6, "Expected open space inside spine removal cutout"
    assert (part_plain & probe).volume > 0.5, "Expected solid material at spine when removal cutout is disabled"

    p_radial = CClipParams(jaw=JawParams(jaw_flare_angle=p_default.jaw.opening_angle / 2.0))
    part_radial = create_c_clip(p_radial)
    assert part_radial.is_valid, "Radial jaw C-clip is invalid"
    assert bbox.max.X > part_radial.bounding_box().max.X + 3.0, (
        f"Expected closed outer rim max.X ({bbox.max.X:.2f}) > radial max.X ({part_radial.bounding_box().max.X:.2f})"
    )

    p_parallel = CClipParams(jaw=JawParams(jaw_flare_angle=0.0))
    part_parallel = create_c_clip(p_parallel)
    assert part_parallel.is_valid, "Parallel jaw (0 deg flare) C-clip is invalid"

    p_inward = CClipParams(jaw=JawParams(jaw_flare_angle=-5.0))
    part_inward = create_c_clip(p_inward)
    assert part_inward.is_valid, "Inward jaw (-5 deg flare) C-clip is invalid"

    p_straight_jaw = CClipParams(jaw=JawParams(jaw_curve_depth=0.0))
    part_straight_jaw = create_c_clip(p_straight_jaw)
    assert part_straight_jaw.is_valid, "Straight jaw (jaw_curve_depth=0) C-clip is invalid"
    assert part_default.volume < part_straight_jaw.volume - 10.0, (
        f"Curved jaw volume ({part_default.volume:.2f}) should be smaller than straight jaw ({part_straight_jaw.volume:.2f})"
    )

    p_deep_curve = CClipParams(jaw=JawParams(jaw_curve_depth=10.0, outer_tip_fillet=8.0))
    part_deep_curve = create_c_clip(p_deep_curve)
    assert part_deep_curve.is_valid, "Large clamped jaw_curve_depth C-clip is invalid"

    p_large_outer = CClipParams(jaw=JawParams(outer_tip_fillet=20.0))
    part_large_outer = create_c_clip(p_large_outer)
    assert part_large_outer.is_valid, "Large clamped outer_tip_fillet C-clip is invalid"

    print(
        f"✓ Test 1 Passed: Default {p_default.core.inside_diameter:g}x{p_default.core.outside_diameter:g}x"
        f"{p_default.core.thickness:g}mm spacer (valid={part_default.is_valid})"
    )

    # Test 2: Thin Spacer & Thin Chamfer/Fillet Auto-Clamping
    p_thin = CClipParams(
        core=CoreParams(thickness=0.8, inside_diameter=8.0, outside_diameter=14.0),
        jaw=JawParams(inner_tip_fillet=2.0, outer_tip_fillet=4.0),
        removal_notch=RemovalNotchParams(width=3.0, depth=1.0, fillet=2.0),
        edge_chamfer=EdgeChamferParams(size=0.5),
    )
    part_thin = create_c_clip(p_thin)
    bbox_thin = part_thin.bounding_box()
    assert part_thin.is_valid, "Thin clamped C-clip is invalid"
    assert abs(bbox_thin.size.Z - 0.8) < 1e-4, f"Thin Z mismatch: {bbox_thin.size.Z}"
    print(f"✓ Test 2 Passed: Thin 0.8mm spacer with auto-clamped fillets/chamfers (valid={part_thin.is_valid})")

    # Test 3: Small Shaft with Thick Wall & Deep Notch
    p_deep = CClipParams(
        core=CoreParams(thickness=8.0, inside_diameter=5.0, outside_diameter=24.0, fit_clearance=0.0),
        jaw=JawParams(opening_angle=135.0),
        removal_notch=RemovalNotchParams(width=2.5, depth=3.5, angle=180.0),
    )
    part_deep = create_c_clip(p_deep)
    assert part_deep.is_valid, "Deep-notch thick-wall spacer is invalid"
    assert len(part_deep.solids()) == 1, "Expected single solid for deep-notch spacer"
    print(f"✓ Test 3 Passed: Small-ID thick-wall deep-notch 5x24x8mm spacer (valid={part_deep.is_valid})")

    # Test 4: Rotated Cutout & Wide Snap Opening (160 deg) without Chamfer
    p_rot = CClipParams(
        core=CoreParams(thickness=3.5, inside_diameter=12.7, outside_diameter=25.4),
        jaw=JawParams(opening_angle=160.0, inner_tip_fillet=0.8, outer_tip_fillet=1.5),
        removal_notch=RemovalNotchParams(width=4.0, depth=1.5, angle=135.0),
        edge_chamfer=EdgeChamferParams(enabled=False),
    )
    part_rot = create_c_clip(p_rot)
    assert part_rot.is_valid, "Rotated notch wide-opening spacer is invalid"
    assert abs(part_rot.bounding_box().size.Z - 3.5) < 1e-4
    print(f"✓ Test 4 Passed: 1/2in rod spacer with 160 deg opening & 135 deg notch (valid={part_rot.is_valid})")

    # Test 5: Parameter Validation Guards
    invalid_cases = [
        CClipParams(core=CoreParams(thickness=0.0)),
        CClipParams(core=CoreParams(inside_diameter=12.0, outside_diameter=12.0)),
        CClipParams(jaw=JawParams(opening_angle=180.0)),
        CClipParams(jaw=JawParams(jaw_flare_angle=90.0)),
        CClipParams(jaw=JawParams(jaw_curve_depth=-1.0)),
        CClipParams(jaw=JawParams(jaw_flare_angle=-40.0, opening_angle=20.0)),
        CClipParams(
            core=CoreParams(inside_diameter=12.0, outside_diameter=22.0),
            removal_notch=RemovalNotchParams(width=4.0, depth=4.9),
        ),
        CClipParams(removal_notch=RemovalNotchParams(angle=10.0)),
    ]
    for case in invalid_cases:
        raised = False
        try:
            create_c_clip(case)
        except ValueError:
            raised = True
        assert raised, f"Expected ValueError for invalid params: {case}"
    print(f"✓ Test 5 Passed: All {len(invalid_cases)} invalid parameter guards raised ValueError")

    # Test 6: STL and STEP Export Verification
    with tempfile.TemporaryDirectory() as tmpdir:
        stl_path = os.path.join(tmpdir, "c_clip_test.stl")
        step_path = os.path.join(tmpdir, "c_clip_test.step")
        export_stl(part_default, stl_path)
        export_step(part_default, step_path)
        assert os.path.getsize(stl_path) > 100, "STL export file is unexpectedly small"
        assert os.path.getsize(step_path) > 100, "STEP export file is unexpectedly small"
    print("✓ Test 6 Passed: STL and STEP export succeeded")

    # Test 7: Exact Outer Tip Nose Fillet & Sharp-Tip Mode
    part_no_chamf = create_c_clip(CClipParams(edge_chamfer=EdgeChamferParams(enabled=False)))
    top_edges = part_no_chamf.faces().sort_by(Axis.Z)[-1].edges()
    nose_arcs = [
        e
        for e in top_edges
        if e.geom_type == GeomType.CIRCLE and abs(e.radius - p_default.jaw.outer_tip_fillet) < 0.01
    ]
    assert len(nose_arcs) == 2, (
        f"Expected 2 outer nose arcs of radius {p_default.jaw.outer_tip_fillet}mm, found {len(nose_arcs)}"
    )
    for curve_depth in (0.0, 2.5):
        part_sharp = create_c_clip(
            CClipParams(jaw=JawParams(outer_tip_fillet=0.0, jaw_curve_depth=curve_depth))
        )
        assert part_sharp.is_valid and len(part_sharp.solids()) == 1
    print(
        f"✓ Test 7 Passed: Verified {len(nose_arcs)} exact r={p_default.jaw.outer_tip_fillet}mm "
        f"tangent outer nose arcs and crisp outer_tip_fillet=0.0 modes"
    )

    # Test 8: Reinforced Outer Lobe (Large Cutouts, Custom Spine Wall, Rotated Angle, Crisp Tips)
    # 8a: Compact spool-holder clip where notch depth exceeds radial wall thickness
    p_spool = CClipParams(
        core=CoreParams(thickness=10.0, inside_diameter=25.0, outside_diameter=37.0),
        removal_notch=RemovalNotchParams(
            enabled=True, width=19.0, depth=14.0, angle=180.0, reinforce_outer=True
        ),
    )
    part_spool = create_c_clip(p_spool)
    assert part_spool.is_valid and len(part_spool.solids()) == 1
    r_in_spool = (25.0 + 0.2) / 2.0
    wall_spool = 37.0 / 2.0 - r_in_spool
    expected_min_x = -(r_in_spool + 14.0 + wall_spool)
    assert abs(part_spool.bounding_box().min.X - expected_min_x) < 0.05, (
        f"Reinforced spine reach mismatch: {part_spool.bounding_box().min.X:.3f} vs {expected_min_x:.3f}"
    )

    # 8b: Explicit spine_wall smaller than wall_thickness and larger than wall_thickness
    p_custom_small = CClipParams(
        core=CoreParams(thickness=12.0, inside_diameter=44.0, outside_diameter=76.0),
        removal_notch=RemovalNotchParams(
            width=32.0, depth=12.0, reinforce_outer=True, spine_wall=10.0
        ),
    )
    part_custom_small = create_c_clip(p_custom_small)
    assert part_custom_small.is_valid and len(part_custom_small.solids()) == 1
    expected_small_x = -((44.0 + 0.2) / 2.0 + 12.0 + 10.0)
    assert abs(part_custom_small.bounding_box().min.X - expected_small_x) < 0.05

    p_custom_beefy = CClipParams(
        core=CoreParams(thickness=10.0, inside_diameter=30.0, outside_diameter=40.0),
        removal_notch=RemovalNotchParams(
            width=22.0, depth=16.0, reinforce_outer=True, spine_wall=9.5
        ),
    )
    part_custom_beefy = create_c_clip(p_custom_beefy)
    assert part_custom_beefy.is_valid and len(part_custom_beefy.solids()) == 1

    # 8c: No-op when cutout + spine_wall already fits inside outside_diameter
    p_noop_reinf = CClipParams(
        core=CoreParams(thickness=10.0, inside_diameter=40.0, outside_diameter=80.0),
        removal_notch=RemovalNotchParams(
            width=16.0, depth=4.0, reinforce_outer=True, spine_wall=8.0
        ),
    )
    p_noop_plain = CClipParams(
        core=CoreParams(thickness=10.0, inside_diameter=40.0, outside_diameter=80.0),
        removal_notch=RemovalNotchParams(
            width=16.0, depth=4.0, reinforce_outer=False
        ),
    )
    part_noop_reinf = create_c_clip(p_noop_reinf)
    part_noop_plain = create_c_clip(p_noop_plain)
    assert part_noop_reinf.is_valid
    assert abs(part_noop_reinf.volume - part_noop_plain.volume) < 1e-3, (
        "Expected reinforce_outer to be a no-op when notch + spine_wall fits inside OD"
    )

    # 8d: Rotated angle + crisp outer tips (outer_tip_fillet=0.0) + straight jaws
    p_rot_reinf = CClipParams(
        core=CoreParams(thickness=8.0, inside_diameter=25.0, outside_diameter=38.0),
        jaw=JawParams(outer_tip_fillet=0.0, jaw_curve_depth=0.0),
        removal_notch=RemovalNotchParams(
            width=18.0, depth=12.0, angle=135.0, reinforce_outer=True
        ),
    )
    part_rot_reinf = create_c_clip(p_rot_reinf)
    assert part_rot_reinf.is_valid and len(part_rot_reinf.solids()) == 1

    # 8e: Tiny protrusion boundary stability
    p_tiny_prot = CClipParams(
        core=CoreParams(thickness=8.0, inside_diameter=40.0, outside_diameter=60.0, fit_clearance=0.0),
        removal_notch=RemovalNotchParams(
            width=16.0, depth=5.02, reinforce_outer=True, spine_wall=5.0
        ),
    )
    part_tiny_prot = create_c_clip(p_tiny_prot)
    assert part_tiny_prot.is_valid and len(part_tiny_prot.solids()) == 1

    # 8f: Invalid reinforced cases (negative spine_wall, lobe colliding with jaws)
    for bad_reinf in (
        CClipParams(
            removal_notch=RemovalNotchParams(reinforce_outer=True, spine_wall=0.0)
        ),
        CClipParams(
            core=CoreParams(inside_diameter=25.0, outside_diameter=37.0),
            jaw=JawParams(opening_angle=120.0),
            removal_notch=RemovalNotchParams(
                width=16.0, depth=14.0, angle=110.0, reinforce_outer=True
            ),
        ),
    ):
        raised = False
        try:
            create_c_clip(bad_reinf)
        except ValueError:
            raised = True
        assert raised, f"Expected ValueError for invalid reinforced params: {bad_reinf}"

    print("✓ Test 8 Passed: Reinforced outer lobe (deep pull, custom spine_wall, no-op, rotated, crisp tips, guards)")

    print("\nALL C-CLIP VALIDATION CHECKS PASSED!")


if __name__ == "__main__":
    validate()
