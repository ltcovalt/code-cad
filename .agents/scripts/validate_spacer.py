"""
Validation script for models/spacer/spacer.py
Validates length=0 straight spacer generation, independent leg dimensions,
corner/T/cross pieces, cutouts, hollow underside mode, and error handling.
"""

import math
import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "spacer")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from spacer import (
    CoreParams,
    CutoutsParams,
    EdgeTreatmentParams,
    FingerNotchParams,
    HollowParams,
    JunctionParams,
    SpacerCutout,
    SpacerParams,
    create_spacer,
)


def validate():
    print("Beginning validation of spacer generator...")

    # Test 1: Corner Spacer
    p1 = SpacerParams(
        core=CoreParams(leg_x_length=100.0, leg_x_width=15.5, leg_y_length=80.0, leg_y_width=15.0, height=12.0),
        edges=EdgeTreatmentParams(corner_radius=2.5, inner_corner_radius=4.0, edge_radius=1.0),
        cutouts=CutoutsParams(enabled=False),
    )
    s1 = create_spacer(p1)
    bbox1 = s1.bounding_box()
    assert s1.is_valid, "Corner spacer is invalid"
    assert abs(bbox1.size.X - 100.0) < 0.05
    assert abs(bbox1.size.Y - 80.0) < 0.05
    assert abs(bbox1.size.Z - 12.0) < 0.05
    print("[PASS] Test 1: Corner spacer with independent leg widths passed")

    # Test 2: Straight Front Spacer (leg_y_length = 0)
    p2 = SpacerParams(
        core=CoreParams(leg_x_length=150.0, leg_x_width=15.5, leg_y_length=0.0, height=12.0),
        edges=EdgeTreatmentParams(corner_radius=2.0, edge_radius=1.0),
        cutouts=CutoutsParams(enabled=False),
    )
    s2 = create_spacer(p2)
    bbox2 = s2.bounding_box()
    assert s2.is_valid
    assert abs(bbox2.size.X - 150.0) < 0.05 and abs(bbox2.size.Y - 15.5) < 0.05 and abs(bbox2.size.Z - 12.0) < 0.05
    print("[PASS] Test 2: Straight front spacer passed")

    # Test 3: Straight Side Spacer (leg_x_length = 0)
    p3 = SpacerParams(
        core=CoreParams(leg_x_length=0.0, leg_y_length=120.0, leg_y_width=15.0, height=12.0),
        edges=EdgeTreatmentParams(corner_radius=2.0, edge_radius=1.0),
        cutouts=CutoutsParams(enabled=False),
    )
    s3 = create_spacer(p3)
    bbox3 = s3.bounding_box()
    assert s3.is_valid
    assert abs(bbox3.size.X - 15.0) < 0.05 and abs(bbox3.size.Y - 120.0) < 0.05 and abs(bbox3.size.Z - 12.0) < 0.05
    print("[PASS] Test 3: Straight side spacer passed")

    # Test 4: Hollow Underside Mode
    p4 = SpacerParams(
        core=CoreParams(leg_x_length=90.0, leg_x_width=18.0, leg_y_length=90.0, leg_y_width=18.0, height=16.0),
        hollow=HollowParams(enabled=True, wall_thickness=2.0, top_thickness=2.0),
        cutouts=CutoutsParams(enabled=False),
    )
    s4 = create_spacer(p4)
    assert s4.is_valid
    print(f"[PASS] Test 4: Hollow corner spacer passed (volume={s4.volume:.1f} mm^3)")

    # Test 5: Chamfer Edge Treatment & Finger Notch
    p5 = SpacerParams(
        core=CoreParams(leg_x_length=100.0, leg_x_width=15.5, leg_y_length=0.0, height=14.0),
        edges=EdgeTreatmentParams(edge_treatment="chamfer", edge_radius=1.2),
        finger_notch=FingerNotchParams(enabled=True),
        cutouts=CutoutsParams(enabled=False),
    )
    s5 = create_spacer(p5)
    assert s5.is_valid
    print("[PASS] Test 5: Chamfered straight spacer with finger notch passed")

    # Test 6: Sharp Corner Piece (Zero radii)
    p6 = SpacerParams(
        core=CoreParams(leg_x_length=70.0, leg_x_width=20.0, leg_y_length=60.0, leg_y_width=15.0, height=10.0),
        edges=EdgeTreatmentParams(corner_radius=0.0, outer_corner_radius=0.0, inner_corner_radius=0.0, edge_radius=0.0),
        cutouts=CutoutsParams(enabled=False),
    )
    s6 = create_spacer(p6)
    assert s6.is_valid
    expected_vol6 = (70.0 * 20.0 + 15.0 * 40.0) * 10.0
    assert abs(s6.volume - expected_vol6) < 0.1
    print(f"[PASS] Test 6: Sharp corner piece passed (volume={s6.volume:.1f} mm^3)")

    # Test 7 & 8: Error Handling
    for bad in (
        SpacerParams(core=CoreParams(leg_x_length=0.0, leg_y_length=0.0)),
        SpacerParams(core=CoreParams(leg_x_length=15.0, leg_y_width=20.0, leg_y_length=50.0)),
    ):
        try:
            create_spacer(bad)
            assert False, "Expected ValueError"
        except ValueError:
            pass
    print("[PASS] Test 7 & 8: Input validation and error handling passed")

    # Test 9: Sharp Rectangular Through-Cutout
    p9_base = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        edges=EdgeTreatmentParams(corner_radius=0.0, edge_radius=0.0),
        cutouts=CutoutsParams(enabled=False),
    )
    p9_cut = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        edges=EdgeTreatmentParams(corner_radius=0.0, edge_radius=0.0),
        cutouts=CutoutsParams(
            enabled=True,
            items=[SpacerCutout(leg="x", align="center", offset=0.0, length=50.0, height=20.0, shape="rectangle", radius=0.0)],
        ),
    )
    s9_base = create_spacer(p9_base)
    s9_cut = create_spacer(p9_cut)
    assert s9_cut.is_valid
    removed_vol = s9_base.volume - s9_cut.volume
    assert abs(removed_vol - 50.0 * 20.0 * 15.0) < 0.5
    print(f"[PASS] Test 9: Rectangular through-cutout exact volume verified (removed={removed_vol:.1f} mm^3)")

    # Test 10: Corner Spacer with Rounded Cutouts on Both Legs
    p10 = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=280.0, leg_y_width=15.0, height=56.0),
        cutouts=CutoutsParams(
            enabled=True,
            items=[
                SpacerCutout(leg="x", align="center", offset=0.0, length=50.0, height=20.0, shape="rectangle", radius=4.0),
                SpacerCutout(leg="y", align="start", offset=100.0, length=40.0, height=15.0, shape="rectangle", radius=3.0),
            ],
        ),
    )
    assert create_spacer(p10).is_valid
    print("[PASS] Test 10: Corner spacer with rounded rectangle cutouts passed")

    # Test 11: Circular Cutouts
    p11 = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        cutouts=CutoutsParams(
            enabled=True,
            items=[
                SpacerCutout(leg="x", align="start", offset=10.0, length=30.0, height=15.0, shape="circle", radius=0.0),
                SpacerCutout(leg="x", align="start", offset=60.0, length=30.0, height=8.0, shape="circle", radius=20.0),
                SpacerCutout(leg="x", align="start", offset=120.0, length=24.0, height=25.0, shape="circle", radius=12.0),
            ],
        ),
    )
    assert create_spacer(p11).is_valid
    print("[PASS] Test 11: Circular cutouts passed")

    # Test 12: Chamfer / Trapezoid Cutouts
    p12 = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        cutouts=CutoutsParams(
            enabled=True,
            items=[
                SpacerCutout(leg="x", align="start", offset=20.0, length=50.0, height=18.0, shape="chamfer", radius=10.0, v_align="top"),
                SpacerCutout(leg="x", align="start", offset=100.0, length=50.0, height=12.0, shape="chamfer", radius=0.0, v_align="bottom"),
            ],
        ),
    )
    assert create_spacer(p12).is_valid
    print("[PASS] Test 12: Chamfer/trapezoid cutouts passed")

    # Test 13: Partial-Depth Pocket Cutouts
    p13 = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        edges=EdgeTreatmentParams(corner_radius=0.0, edge_radius=0.0),
        cutouts=CutoutsParams(
            enabled=True,
            items=[
                SpacerCutout(leg="x", align="start", offset=20.0, length=50.0, height=20.0, depth=6.0, side="outer"),
                SpacerCutout(leg="x", align="start", offset=100.0, length=40.0, height=15.0, depth=5.0, side="inner"),
            ],
        ),
    )
    s13 = create_spacer(p13)
    assert s13.is_valid
    assert abs((s9_base.volume - s13.volume) - 9000.0) < 0.5
    print("[PASS] Test 13: Partial-depth pockets exact volume verified")

    # Test 14: Cutout Error Handling
    for bad in (
        SpacerParams(
            core=CoreParams(leg_x_length=100.0, leg_y_length=0.0),
            cutouts=CutoutsParams(enabled=True, items=[SpacerCutout(leg="y", align="start", offset=10.0, length=20.0, height=10.0)]),
        ),
        SpacerParams(
            core=CoreParams(leg_x_length=100.0, leg_y_length=0.0),
            cutouts=CutoutsParams(enabled=True, items=[SpacerCutout(leg="x", shape="hexagon")]),
        ),
    ):
        try:
            create_spacer(bad)
            assert False, "Expected ValueError"
        except ValueError:
            pass
    print("[PASS] Test 14: Cutout input validation passed")

    # Test 15: Mirrored L-Shape
    p15_orig = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=280.0, leg_y_width=15.0, height=56.0),
        junction=JunctionParams(mirror_x=False),
        cutouts=CutoutsParams(enabled=True, items=[SpacerCutout(leg="x", align="start", offset=40.0, length=50.0, height=20.0, radius=3.0)]),
    )
    p15_inv = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=280.0, leg_y_width=15.0, height=56.0),
        junction=JunctionParams(mirror_x=True),
        cutouts=CutoutsParams(enabled=True, items=[SpacerCutout(leg="x", align="start", offset=40.0, length=50.0, height=20.0, radius=3.0)]),
    )
    s15_orig = create_spacer(p15_orig)
    s15_inv = create_spacer(p15_inv)
    bb15 = s15_inv.bounding_box()
    assert s15_inv.is_valid and abs(s15_inv.volume - s15_orig.volume) < 0.5
    assert abs(bb15.min.X) < 0.05 and abs(bb15.min.Y) < 0.05 and abs(bb15.min.Z) < 0.05
    print("[PASS] Test 15: Mirrored L-shape passed")

    # Test 16 & 17: T-Shape & Cross
    p16 = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=120.0, leg_y_width=15.0, height=40.0),
        junction=JunctionParams(leg_y_align="center", leg_y_offset=-10.0),
        edges=EdgeTreatmentParams(inner_corner_radius=4.0, edge_radius=1.0),
        cutouts=CutoutsParams(enabled=True, items=[SpacerCutout(leg="y", align="start", offset=40.0, length=30.0, height=15.0, shape="rectangle", radius=2.0)]),
    )
    assert create_spacer(p16).is_valid
    p17 = SpacerParams(
        core=CoreParams(leg_x_length=120.0, leg_x_width=15.0, leg_y_length=120.0, leg_y_width=15.0, height=30.0),
        junction=JunctionParams(leg_x_align="center", leg_y_align="center"),
        edges=EdgeTreatmentParams(inner_corner_radius=4.0, edge_radius=1.0),
        cutouts=CutoutsParams(enabled=False),
    )
    assert create_spacer(p17).is_valid
    print("[PASS] Test 16 & 17: T-shape and Cross (+) spacers passed")

    # Test 18: End-Aligned L-Shape & Validation
    p18_end = SpacerParams(
        core=CoreParams(leg_x_length=100.0, leg_x_width=15.0, leg_y_length=100.0, leg_y_width=15.0, height=20.0),
        junction=JunctionParams(leg_y_align="end"),
        cutouts=CutoutsParams(enabled=False),
    )
    assert create_spacer(p18_end).is_valid
    for bad in (
        SpacerParams(core=CoreParams(leg_x_length=100.0, leg_x_width=15.0, leg_y_length=100.0, leg_y_width=15.0), junction=JunctionParams(leg_y_offset=90.0)),
        SpacerParams(core=CoreParams(leg_x_length=100.0, leg_x_width=15.0, leg_y_length=100.0, leg_y_width=15.0), junction=JunctionParams(leg_y_align="middle")),
    ):
        try:
            create_spacer(bad)
            assert False, "Expected ValueError"
        except ValueError:
            pass
    print("[PASS] Test 18: End alignment & junction validation passed")

    # Test 19: Cutout Entry Rounding & Chamfering
    p19_sharp = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        edges=EdgeTreatmentParams(corner_radius=0.0, edge_radius=0.0),
        cutouts=CutoutsParams(enabled=True, items=[SpacerCutout(leg="x", align="end", offset=15.0, length=50.0, height=16.0, radius=3.0, entry_radius=0.0)]),
    )
    p19_fillet = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        edges=EdgeTreatmentParams(corner_radius=0.0, edge_radius=0.0),
        cutouts=CutoutsParams(enabled=True, items=[SpacerCutout(leg="x", align="end", offset=15.0, length=50.0, height=16.0, radius=3.0, entry_radius=3.0, entry_treatment="fillet")]),
    )
    p19_chamfer = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        edges=EdgeTreatmentParams(corner_radius=0.0, edge_radius=0.0),
        cutouts=CutoutsParams(enabled=True, items=[SpacerCutout(leg="x", align="end", offset=15.0, length=50.0, height=16.0, radius=3.0, entry_radius=3.0, entry_treatment="chamfer")]),
    )
    s19_sharp = create_spacer(p19_sharp)
    s19_fillet = create_spacer(p19_fillet)
    s19_chamfer = create_spacer(p19_chamfer)
    r_e = 3.0
    assert abs((s19_sharp.volume - s19_fillet.volume) - 2.0 * (r_e**2 - math.pi * r_e**2 / 4.0) * 15.0) < 0.2
    assert abs((s19_sharp.volume - s19_chamfer.volume) - 2.0 * (0.5 * r_e**2) * 15.0) < 0.2
    assert create_spacer(SpacerParams()).is_valid
    print("[PASS] Test 19: Cutout entry fillet & chamfer verified")

    # Test 20: Closed Interior Windows & Bolt-Hole Pass-Throughs
    p20 = SpacerParams(
        core=CoreParams(leg_x_length=180.0, leg_x_width=15.0, leg_y_length=0.0, height=56.0),
        edges=EdgeTreatmentParams(corner_radius=0.0, edge_radius=0.0),
        cutouts=CutoutsParams(
            enabled=True,
            items=[
                SpacerCutout(leg="x", align="start", offset=20.0, v_align="top", v_offset=15.0, length=30.0, height=16.0, shape="rectangle", radius=0.0),
                SpacerCutout(leg="x", align="center", offset=0.0, v_align="center", v_offset=0.0, length=12.0, height=12.0, shape="circle", radius=6.0),
                SpacerCutout(leg="x", align="end", offset=20.0, v_align="bottom", v_offset=10.0, length=24.0, height=14.0, shape="chamfer", radius=3.0),
            ],
        ),
    )
    s20 = create_spacer(p20)
    assert s20.is_valid
    expected_removed_20 = (30.0 * 16.0 * 15.0) + (math.pi * 6.0**2 * 15.0) + ((24.0 * 14.0 - 2.0 * 3.0**2) * 15.0)
    assert abs((s9_base.volume - s20.volume) - expected_removed_20) < 0.5
    print("[PASS] Test 20: Closed interior windows & bolt-hole pass-throughs verified")
    print("\nAll Spacer validation tests passed successfully!")


if __name__ == "__main__":
    validate()
