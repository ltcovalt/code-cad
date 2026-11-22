"""
Comprehensive validation script for parametric rack_bracket.py
Tests default 2U Hex Bracket, 1U Solid Bracket preset, 3U/4U brackets,
cutout styles, and EIA-310 mounting slot counts/positions.
"""

import json
import os
import sys
import time

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path = [p for p in sys.path if p not in ("", ".")]
models_dir = os.path.join(repo_root, "models", "rack_bracket")
if models_dir not in sys.path:
    sys.path.append(models_dir)

from build123d import Axis, GeomType
from rack_bracket import (
    CoreParams,
    CutoutParams,
    RackBracketParams,
    RackSlotsParams,
    SideHolesParams,
    create_rack_bracket,
    export_filename,
)


def _front_flange_slot_z_centers(part, thickness: float) -> list[float]:
    """Return sorted Z centers of through-slots on the front flange (X in [0, thickness])."""
    front_face = part.faces().filter_by(Axis.X).sort_by(Axis.X)[0]
    inner_wires = front_face.inner_wires()
    return sorted(round(w.bounding_box().center().Z, 2) for w in inner_wires)


def _side_hole_z_centers(part) -> list[float]:
    """Return sorted unique Z centers of cylindrical side holes."""
    cyl_faces = [
        f
        for f in part.faces().filter_by(GeomType.CYLINDER)
        if abs(f.axis_of_rotation.direction.Y) > 0.99
    ]
    return sorted({round(f.bounding_box().center().Z, 2) for f in cyl_faces})


def validate():
    print("Beginning validation of unified rack_bracket...")

    # Test 1: Default preset is 2U Hex Bracket
    p_default = RackBracketParams()
    assert p_default.core.u_count == 2, f"Expected default u_count=2, got {p_default.core.u_count}"
    assert p_default.cutout.style == "hex", f"Expected default cutout.style='hex', got {p_default.cutout.style}"
    assert p_default.rack_slots.single_slot_1u is False, "Expected single_slot_1u=False by default"
    assert export_filename(p_default) == "rack_bracket_2u_hex", f"Unexpected default filename: {export_filename(p_default)}"

    t0 = time.perf_counter()
    b_default = create_rack_bracket(p_default)
    t_default_ms = (time.perf_counter() - t0) * 1000.0
    bbox_default = b_default.bounding_box()
    expected_h2 = 2 * 44.45 - 1.2  # 87.7 mm
    assert abs(bbox_default.size.Z - expected_h2) < 0.05, f"2U height mismatch: {bbox_default.size.Z} vs {expected_h2}"
    assert b_default.is_valid, "Default 2U Hex bracket solid is invalid"
    assert abs(b_default.volume - 31266.639) < 0.1, f"Unexpected 2U Hex volume: {b_default.volume:.4f}"
    default_slots = _front_flange_slot_z_centers(b_default, p_default.core.thickness)
    assert len(default_slots) == 2, f"Expected 2 front slots on 2U, got {default_slots}"
    print(
        f"✓ Default 2U Hex Bracket passed: height={bbox_default.size.Z:.2f}mm, "
        f"vol={b_default.volume:.2f}mm³, slots={default_slots}, time={t_default_ms:.0f}ms, valid={b_default.is_valid}"
    )

    # Test 2: 1U Solid Bracket preset from presets.json
    presets_path = os.path.join(models_dir, "presets.json")
    with open(presets_path, "r", encoding="utf-8") as f:
        presets = json.load(f)
    assert "1u_solid" in presets, f"Expected '1u_solid' in presets.json, got {list(presets.keys())}"
    assert "2u_hex" not in presets, "'2u_hex' should now be the canonical default, not in presets.json"
    p1_cfg = presets["1u_solid"]["params"]
    p1 = RackBracketParams(
        core=CoreParams(**p1_cfg.get("core", {})),
        cutout=CutoutParams(**p1_cfg.get("cutout", {})),
    )
    assert export_filename(p1) == "rack_bracket_1u_solid", f"Unexpected 1U filename: {export_filename(p1)}"
    b1 = create_rack_bracket(p1)
    bbox1 = b1.bounding_box()
    expected_h1 = 1 * 44.45 - 1.2  # 43.25 mm
    assert abs(bbox1.size.Z - expected_h1) < 0.05, f"1U height mismatch: {bbox1.size.Z} vs {expected_h1}"
    assert b1.is_valid, "1U bracket solid is invalid"

    slots_1u = _front_flange_slot_z_centers(b1, p1.core.thickness)
    assert len(slots_1u) == 2, f"Expected 2 front EIA-310 slots on 1U, got {slots_1u}"
    assert abs((slots_1u[1] - slots_1u[0]) - 31.75) < 0.05, f"Expected 31.75mm EIA-310 spacing, got {slots_1u}"
    side_z_1u = _side_hole_z_centers(b1)
    assert len(side_z_1u) == 1 and abs(side_z_1u[0] - expected_h1 / 2.0) < 0.05, (
        f"Expected centered side holes on 1U at {expected_h1 / 2.0:.2f}mm, got {side_z_1u}"
    )
    print(f"✓ 1U Solid Bracket preset passed: height={bbox1.size.Z:.2f}mm, slots={slots_1u}, side_z={side_z_1u}, valid={b1.is_valid}")

    # Test 3: 1U Bracket with single_slot_1u=True opt-in
    p1_single = RackBracketParams(
        core=CoreParams(u_count=1),
        cutout=CutoutParams(style="none"),
        rack_slots=RackSlotsParams(single_slot_1u=True),
    )
    b1_single = create_rack_bracket(p1_single)
    assert b1_single.is_valid
    slots_1u_single = _front_flange_slot_z_centers(b1_single, p1_single.core.thickness)
    assert len(slots_1u_single) == 1, f"Expected 1 centered slot when single_slot_1u=True, got {slots_1u_single}"
    print(f"✓ 1U Single-Slot opt-in passed: slots={slots_1u_single}, valid={b1_single.is_valid}")

    # Test 4: 3U Bracket with hex cutout
    p3 = RackBracketParams(core=CoreParams(u_count=3), cutout=CutoutParams(style="hex"))
    b3 = create_rack_bracket(p3)
    bbox3 = b3.bounding_box()
    expected_h3 = 3 * 44.45 - 1.2  # 132.15 mm
    assert abs(bbox3.size.Z - expected_h3) < 0.05, f"3U height mismatch: {bbox3.size.Z} vs {expected_h3}"
    assert b3.is_valid, "3U bracket solid is invalid"
    print(f"✓ 3U Hex Bracket passed: height={bbox3.size.Z:.2f}mm, valid={b3.is_valid}")

    # Test 5: 4U Bracket with window cutout
    p4 = RackBracketParams(core=CoreParams(u_count=4), cutout=CutoutParams(style="window"))
    b4 = create_rack_bracket(p4)
    bbox4 = b4.bounding_box()
    expected_h4 = 4 * 44.45 - 1.2  # 176.60 mm
    assert abs(bbox4.size.Z - expected_h4) < 0.05, f"4U height mismatch: {bbox4.size.Z} vs {expected_h4}"
    assert b4.is_valid, "4U bracket solid is invalid"
    print(f"✓ 4U Window Bracket passed: height={bbox4.size.Z:.2f}mm, valid={b4.is_valid}")

    # Test 6: Custom length and thickness
    p_custom = RackBracketParams(
        core=CoreParams(u_count=2, bracket_length=120.0, thickness=4.0),
        cutout=CutoutParams(style="none"),
    )
    b_custom = create_rack_bracket(p_custom)
    bbox_custom = b_custom.bounding_box()
    assert abs(bbox_custom.size.X - 120.0) < 0.05
    assert b_custom.is_valid
    print(f"✓ Custom length & thickness passed: length={bbox_custom.size.X:.2f}mm, valid={b_custom.is_valid}")

    # Test 7: Sharp window corners (corner_radius=0) and no side holes
    p_sharp = RackBracketParams(
        core=CoreParams(u_count=2),
        side_holes=SideHolesParams(enabled=False),
        cutout=CutoutParams(style="hex", corner_radius=0.0),
    )
    b_sharp = create_rack_bracket(p_sharp)
    assert b_sharp.is_valid, "Sharp corner hex bracket is invalid"
    print(f"✓ Sharp-corner hex (no side holes) passed: vol={b_sharp.volume:.2f}mm³, valid={b_sharp.is_valid}")

    # Test 8: Fallback path (side holes intentionally overlapping cutout window)
    p_overlap = RackBracketParams(
        core=CoreParams(u_count=2),
        cutout=CutoutParams(style="window", margin_z=6.0),
    )
    b_overlap = create_rack_bracket(p_overlap)
    assert b_overlap.is_valid, "Overlapping window/holes fallback bracket is invalid"
    print(f"✓ Overlapping window/holes fallback passed: vol={b_overlap.volume:.2f}mm³, valid={b_overlap.is_valid}")

    # Test 9: Solid plate with no side holes at all
    p_plain = RackBracketParams(
        core=CoreParams(u_count=1),
        side_holes=SideHolesParams(enabled=False),
        cutout=CutoutParams(style="none"),
    )
    b_plain = create_rack_bracket(p_plain)
    assert b_plain.is_valid, "Plain solid bracket without side holes is invalid"
    print(f"✓ Plain solid bracket (no side holes) passed: vol={b_plain.volume:.2f}mm³, valid={b_plain.is_valid}")

    print("All validation tests passed successfully!")


if __name__ == "__main__":
    validate()
