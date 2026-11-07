# build123d Reference: Import, Export & Visualization

---

## 1. Exporting Models

### STEP (CAD Exchange)
```python
export_step(part, "model.step")
```

### STL (3D Printing Mesh)
```python
export_stl(part, "model.stl", tolerance=0.001, angular_tolerance=0.1)
```

### 3MF (Multi-material 3D Printing)
```python
export_3mf(part, "model.3mf")
```

### 2D Vector Formats (SVG & DXF)
```python
export_svg(sketch, "drawing.svg")
export_dxf(sketch, "drawing.dxf")
```

---

## 2. Importing Models

```python
imported_part = import_step("component.step")
imported_mesh = import_stl("mesh.stl")
```

---

## 3. Visualization with `ocp_viewer` / `ocp_vscode`

### Standalone (Neovim / Browser) with `ocp_viewer`:
Start the standalone viewer server (`python -m ocp_viewer` at `http://127.0.0.1:3939`), then in your script:

```python
try:
    from ocp_viewer import show, show_object, set_port
except ImportError:
    from ocp_vscode import show, show_object, set_port

show(part, names=["Main Part"])
```

### In VS Code with the OCP CAD Viewer extension:
Open the viewer panel in VS Code, and run the same script.
