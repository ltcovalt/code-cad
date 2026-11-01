# build123d Reference: Compounds, Joints & Assemblies

---

## 1. Compounds

A `Compound` groups multiple `Solid`, `Shell`, `Face`, or `Wire` objects into an assembly structure.

```python
part1 = Box(10, 10, 10)
part2 = Cylinder(4, 20).locate(Location((0, 0, 10)))
assembly = Compound(children=[part1, part2])
```

---

## 2. Joints

Joints allow kinematic relationships and placement points for components.

### Joint Types
- **`RigidJoint(name, to_part, joint_location)`**: Fixed 6-DOF joint attachment.
- **`RevoluteJoint(name, to_part, axis)`**: Rotational 1-DOF joint.
- **`LinearJoint(name, to_part, axis)`**: Translational 1-DOF joint.

### Connecting Joints
```python
joint1 = RigidJoint("mount", part1, Location((0, 0, 10)))
joint2 = RigidJoint("base", part2, Location((0, 0, 0)))

part1.joints["mount"].connect_to(part2.joints["base"])
```
