# build123d Best Practices, FAQ & Cheat Sheet

# bbox: 0.0 <= x <= 159.0, 0.0 <= y <= 129.0, 0.0 <= z <= 100.0

1.16 Tips, Best Practices and FAQ
Although there are countless ways to create objects with build123d, experience has proven that certain techniques can
assist designers in achieving their goals with the greatest efficiency. The following is a description of these techniques.

1.16. Tips, Best Practices and FAQ



1.16.1 Can’t Get There from Here
Unfortunately, it’s a reality that not all parts described using build123d can be successfully constructed by the underlying
CAD core. Designers may have to explore different design approaches to get the OpenCascade CAD core to successfully
build the target object. For instance, if a multi-section sweep() operation fails, a loft() operation may be a viable
alternative in certain situations. It’s crucial to remember that CAD is a complex field and patience may be required to
achieve the desired results.

1.16.2 2D before 3D
When creating complex 3D objects, it is generally best to start with 2D work before moving on to 3D. This is because
3D structures are much more intricate, and 3D operations can be slower and more prone to failure. For designers
who come from a Constructive Solid Geometry (CSG) background, such as OpenSCAD, this approach may seem
counterintuitive. On the other hand, designers from a GUI BREP CAD background, like Fusion 360 or SolidWorks,
may find this approach more natural.
In practice, this means that 3D objects are often created by applying operations like extrude() or revolve() to 2D
sketches, as shown below:
with BuildPart() as my_part:
with BuildSketch() as part_profile:
...
extrude(amount=some_distance)
...
With this structure part_profile may have many objects that are combined and modified by operations like fillet()
before being extruded to a 3D shape.

1.16.3 Delay Chamfers and Fillets
Chamfers and fillets can add complexity to a design by transforming simple vertices or edges into arcs or non-planar
faces. This can significantly increase the complexity of the design. To avoid unnecessary processing costs and potential
errors caused by a needlessly complicated design, it’s recommended to perform these operations towards the end of the
object’s design. This is especially true for 3D shapes, as it is sometimes necessary to fillet or chamfer in the 2D design
phase. Luckily, these 2D fillets and chamfers are less likely to fail than their 3D counterparts.

1.16.4 Parameterize
One of the most powerful features of build123d is the ability to design fully parameterized parts. While it may be faster
to use a GUI CAD package for the initial iteration of a part, subsequent iterations can prove frustratingly difficult. By
using variables for critical dimensions and deriving other dimensions from these key variables, not only can a single
part be created, but a whole set of parts can be readily available. When inevitable change requests arise, a simple
parameter adjustment may be all that’s required to make necessary modifications.

1.16.5 Use Shallow Copies
As discussed in the Assembly section, a shallow copy of parts that are repeated in your design can make a huge difference
in performance and usability of your end design. Objects like fasteners, bearings, chain links, etc. could be duplicated
tens or even hundreds of times otherwise. Use shallow copies where possible but keep in mind that if one instance of
the object changes all will change.




1.16.6 Object Selection
When selecting features in a design it’s sometimes easier to select an object from higher up in the topology first, then
select the object from there. For example let’s consider a plate with four chamfered holes like this:
When selecting edges to be chamfered one might first select the face that these edges belong to then select the edges as
shown here:
from build123d import *
svg_opts = {"pixel_scale": 5, "show_axes": False, "show_hidden": True}
length, width, thickness = 80.0, 60.0, 10.0
hole_dia = 6.0
with BuildPart() as plate:
Box(length, width, thickness)
with GridLocations(length - 20, width - 20, 2, 2):
Hole(radius=hole_dia / 2)
top_face: Face = plate.faces().sort_by(Axis.Z)[-1]
hole_edges = top_face.edges().filter_by(GeomType.CIRCLE)
chamfer(hole_edges, length=1)

1.16.7 Build123d - CadQuery Integration
As both CadQuery and build123d use a common OpenCascade Python wrapper (OCP) it’s possible to interchange
objects both from CadQuery to build123d and vice-versa by transferring the wrapped objects as follows (first from
CadQuery to build123d):
import build123d as b3d
b3d_solid = b3d.Solid.make_box(1,1,1)
... some cadquery stuff ...
b3d_solid.wrapped = cq_solid.wrapped
Secondly, from build123d to CadQuery as follows:
import build123d as b3d
import cadquery as cq
with b3d.BuildPart() as b123d_box:
b3d.Box(1,2,3)
cq_solid = cq.Solid.makeBox(1,1,1)
cq_solid.wrapped = b123d_box.part.solid().wrapped

1.16.8 Self Intersection
Avoid creating objects that intersect themselves - even if at a single vertex - as these topologies will almost certainly be
invalid (even if is_valid() reports a True value). An example of where this may arise is with the thread of a screw
(or any helical shape) where after one complete revolution the part may contact itself. One is likely be more successful
if the part is split into multiple sections - say 180° of a helix - which are then stored in an assembly.

1.16. Tips, Best Practices and FAQ



1.16.9 Packing Objects on a Plane
When designing independent shapes it’s common to place each at or near the global origin, which can make it tricky to
visualize many shapes at once. pack.pack() will translate the Shape’s passed to it so that they don’t overlap, with an
optional padding/spacing. Here’s the result of packing a bunch of overlapping boxes (left) using some padding (right):

By default, the original Z value of all objects packed using the pack.pack() function is preserved. If you want to align
all objects so that they are “placed” on the zero Z coordinate, the pack() function has an align_z argument. When set
to True, this will align all objects.
This can be useful, for example, when preparing print setups for 3D printing, giving you full control over this alignment
so you don’t have to leave it to the slicer.

1.16.10 Isn’t from build123d import * bad practice?
Glob imports like from build123d import * are generally frowned upon when writing software, and for good
reason. They pollute the global namespace, cause confusing collisions, and are not future-proof, as future changes
to the library being imported could collide with other names. It would be much safer to do something like import
build123d as bd and then reference every item with, for example, bd.BuildPart(). If your goal is to integrate
build123d into a larger piece of software, which many people work on, or where long-term maintainability is a priority,
using this approach is definitely a good idea! Why then, are glob imports so often used in build123d code and official
examples?
build123d is most commonly used not as a library within a larger application, but as a Domain-Specific Language
which, together with something like the OCP CAD Viewer, acts as the user interface for a CAD application. Writing
build123d often involves live coding in a REPL or typing in editors with limited space due to the rest of the CAD
GUI taking up screen space. Scripts are usually centred around build123d usage, with usage of other libraries being
limited enough that naming conflicts are easily avoided. In this context, it’s entirely reasonable to prioritise developer
ergonomics over “correctness” by making build123d’s primitives available in the global namespace.

1.16.11 Why doesn’t BuildSketch(Plane.XZ) work?
When creating a sketch not on the default Plane.XY users may expect that they are drawing directly on the placement
provided. For example:
with BuildSketch(Plane.XZ) as vertical_sketch:
Rectangle(1, 1)
with Locations(vertices().group_by(Axis.X)[-1].sort_by(Axis.Z)[-1]):
Circle(0.2)




In this case the circle is not positioned in the top right as one would expect; in-fact, the position of the circle randomly
switches between the bottom and top corner.
This is because all sketches are created on a local Plane.XY independent of where they will be ultimately placed;
therefore, the sort_by(Axis.Z) is sorting two points that have a Z value of zero as they are located on Plane.XY and
effectively return a random point.

1.16. Tips, Best Practices and FAQ



Why does BuildSketch work this way? Consider an example where the user wants to work on a plane not aligned
with any Axis, as follows (this is often done when creating a sketch on a Face of a 3D part but is simulated here by
rotating a Plane):
with BuildSketch(Plane.YZ.rotated((123, 45, 6))) as custom_plane:
Rectangle(1, 1, align=Align.MIN)
with Locations(vertices().group_by(Axis.X)[-1].sort_by(Axis.Y)[-1]):
Circle(0.2)

Here one can see both sketch_local (with the light fill on Plane.XY) and the sketch (with the darker fill) published
to the user provided placement. As the selectors work off global coordinates, selection of the “top right” of this sketch
would be quite challenging and would likely change if the sketch was ever moved as could happen if the 3D part
changed. For an example of sketching on a 3D part, see Sketching on other Planes.

1.16.12 Why is BuildLine not working as expected within the scope of BuildSketch?
As described above, all sketching is done on a local Plane.XY; however, the following is a common issue:
with BuildSketch() as sketch:
with BuildLine(Plane.XZ):
Polyline(...)
make_face()
Here BuildLine is within the scope of BuildSketch. The line is still constructed in its own local coordinate system, then the Plane.XZ placement is applied when BuildLine exits and publishes the line to the sketch. Since
BuildSketch stores sketch geometry locally on Plane.XY, make_face must reorient the received line back to Plane.




XY before making the face.
Although this isn’t absolutely incorrect, it’s often not what the user intended: the line is first placed to Plane.XZ
and then converted back into the sketch’s local Plane.XY coordinates. Unless there is a good reason and the user
understands this placement/reorientation sequence, BuildLine instances used only to create sketch faces should use
the default placement.

1.16.13 Don’t Builders inherit placements when nested?
Some users expect that nested Builders will inherit the placement or coordinate system from their parent Builder. This
is not true. Each Builder constructs in its own local Plane.XY coordinate system and only applies its own placements
when its output is published.
Having Builders inherit placements from their parents could make the same nested builder behave differently depending
on which scope it is in. Inheriting placements isn’t necessarily incorrect, it was considered for build123d but ultimately
the explicit local-construction and publish-to-placement approach was taken.

1.17 Import/Export
Methods and functions specific to exporting and importing build123d objects are defined below.
For example:
with BuildPart() as box_builder:
Box(1, 1, 1)
export_step(box_builder.part, "box.step")

1.17.1 File Formats
3MF
The 3MF (3D Manufacturing Format) file format is a versatile and modern standard for representing 3D models used in
additive manufacturing, 3D printing, and other applications. Developed by the 3MF Consortium, it aims to overcome
the limitations of traditional 3D file formats by providing a more efficient and feature-rich solution. The 3MF format
supports various advanced features like color information, texture mapping, multi-material definitions, and precise
geometry representation, enabling seamless communication between design software, 3D printers, and other manufacturing devices. Its open and extensible nature makes it an ideal choice for exchanging complex 3D data in a compact
and interoperable manner.
BREP
The BREP (Boundary Representation) file format is a widely used data format in computer-aided design (CAD) and
computer-aided engineering (CAE) applications. BREP represents 3D geometry using topological entities like vertices,
edges, and faces, along with their connectivity information. It provides a precise and comprehensive representation of
complex 3D models, making it suitable for advanced modeling and analysis tasks. BREP files are widely supported
by various CAD software, enabling seamless data exchange between different systems. Its ability to represent both
geometric shapes and their topological relationships makes it a fundamental format for storing and sharing detailed 3D
models.
DXF
The DXF (Drawing Exchange Format) file format is a widely used standard for representing 2D and 3D drawings,
primarily used in computer-aided design (CAD) applications. Developed by Autodesk, DXF files store graphical and
geometric data, such as lines, arcs, circles, and text, as well as information about layers, colors, and line weights. Due to
its popularity, DXF files can be easily exchanged and shared between different CAD software. The format’s simplicity

1.17. Import/Export



and human-readable structure make it a versatile choice for sharing designs, drawings, and models across various CAD
platforms, facilitating seamless collaboration in engineering and architectural projects.
glTF
The glTF (GL Transmission Format) is a royalty-free specification for the efficient transmission and loading of 3D
models and scenes by applications. Developed by the Khronos Group, glTF is designed as a compact, interoperable
format that enables the quick display of assets across various platforms and devices. glTF supports a rich feature set,
including detailed meshes, materials, textures, skeletal animations, and more, facilitating complex 3D visualizations. It
streamlines the process of sharing and deploying 3D content in web applications, game engines, and other visualization
tools, making it the “JPEG of 3D.” glTF’s versatility and efficiency have led to its widespread adoption in the 3D content
industry.
STL
The STL (STereoLithography) file format is a widely used file format in 3D printing and computer-aided design (CAD)
applications. It represents 3D geometry using triangular facets to approximate the surface of a 3D model. STL files
are widely supported and can store both the geometry and color information of the model. They are used for rapid
prototyping and 3D printing, as they provide a simple and efficient way to represent complex 3D objects. The format’s
popularity stems from its ease of use, platform independence, and ability to accurately describe the surface of intricate
3D models with a minimal file size.
STEP
The STEP (Standard for the Exchange of Product model data) file format is a widely used standard for representing 3D
product and manufacturing data in computer-aided design (CAD) and computer-aided engineering (CAE) applications.
It is an ISO standard (ISO 10303) and supports the representation of complex 3D geometry, product structure, and
metadata. STEP files store information in a neutral and standardized format, making them highly interoperable across
different CAD/CAM software systems. They enable seamless data exchange between various engineering disciplines,
facilitating collaboration and data integration throughout the entire product development and manufacturing process.
SVG
The SVG (Scalable Vector Graphics) file format is an XML-based standard used for describing 2D vector graphics.
It is widely supported and can be displayed in modern web browsers, making it suitable for web-based graphics and
interactive applications. SVG files define shapes, paths, text, and images using mathematical equations, allowing for
smooth scalability without loss of quality. The format is ideal for logos, icons, illustrations, and other graphics that
require resolution independence. SVG files are also easily editable in text editors or vector graphic software, making
them a popular choice for designers and developers seeking flexible and versatile graphic representation.

1.17.2 2D Exporters
Exports to DXF (Drawing Exchange Format) and SVG (Scalable Vector Graphics) are provided by the 2D Exporters:
ExportDXF and ExportSVG classes.
DXF is a widely used file format for exchanging CAD (Computer-Aided Design) data between different software applications. SVG is a widely used vector graphics format that is supported by web browsers and various graphic editors.
The core concept to these classes is the creation of a DXF/SVG document with specific properties followed by the
addition of layers and shapes to the documents. Once all of the layers and shapes have been added, the document can
be written to a file.




3D to 2D Projection
There are a couple ways to generate a 2D drawing of a 3D part:
• Generate a section: The section() operation can be used to create a 2D cross section of a 3D part at a given
plane.
• Generate a projection: The project_to_viewport() method can be used to create a 2D projection of a 3D
scene. Similar to a camera, the viewport_origin defines the location of camera, the viewport_up defines
the orientation of the camera, and the look_at parameter defined where the camera is pointed. By default,
viewport_up is the positive z axis and look_up is the center of the shape. The return value is a tuple of lists
of edges, the first the visible edges and the second the hidden edges.
Each of these Edges and Faces can be assigned different line color/types and fill colors as described below (as
project_to_viewport only generates Edges, fill doesn’t apply). The shapes generated from the above steps are
to be added as shapes in one of the exporters described below and written as either a DXF or SVG file as shown in this
example:
view_port_origin=(-100, -50, 30)
visible, hidden = part.project_to_viewport(view_port_origin)
max_dimension = max(*Compound(children=visible + hidden).bounding_box().size)
exporter = ExportSVG(scale=100 / max_dimension)
exporter.add_layer("Visible")
exporter.add_layer("Hidden", line_color=(99, 99, 99), line_type=LineType.ISO_DOT)
exporter.add_shape(visible, layer="Visible")
exporter.add_shape(hidden, layer="Hidden")
exporter.write("part_projection.svg")
LineType
ANSI (American National Standards Institute) and ISO (International Organization for Standardization) standards both
define line types in drawings used in DXF and SVG exported drawings:
• ANSI Standards:
– ANSI/ASME Y14.2 - “Line Conventions and Lettering” is the standard that defines line types, line
weights, and line usage in engineering drawings in the United States.
• ISO Standards:
– ISO 128 - “Technical drawings – General principles of presentation” is the ISO standard that covers
the general principles of technical drawing presentation, including line types and line conventions.
– ISO 13567 - “Technical product documentation (TPD) – Organization and naming of layers for CAD”
provides guidelines for the organization and naming of layers in Computer-Aided Design (CAD) systems, which may include line type information.
These standards help ensure consistency and clarity in technical drawings, making it easier for engineers, designers,
and manufacturers to communicate and interpret the information presented in the drawings.
The line types used by the 2D Exporters are defined by the LineType Enum and are shown in the following diagram:

ExportDXF
class ExportDXF(version: str = 'AC1027', unit: ~build123d.build_enums.Unit = <Unit.MM>, color:
~exporters.ColorIndex | None = None, line_weight: float | None = None, line_type:
~exporters.LineType | None = None)
The ExportDXF class provides functionality for exporting 2D shapes to DXF (Drawing Exchange Format) format.
1.17. Import/Export



DXF is a widely used file format for exchanging CAD (Computer-Aided Design) data between different software
applications.
Parameters
• version (str, optional) – The DXF version to use for the output file. Defaults to
ezdxf.DXF2013.
• unit (Unit, optional) – The unit used for the exported DXF. It should be one of the Unit
enums: Unit.MC, Unit.MM, Unit.CM, Unit.M, Unit.IN, or Unit.FT. Defaults to Unit.MM.
• color (Optional[ColorIndex], optional) – The default color index for shapes. It can
be specified as a ColorIndex enum or None.. Defaults to None.
• line_weight (Optional[float], optional) – The default line weight (stroke width)
for shapes, in millimeters. . Defaults to None.
• line_type (Optional[LineType], optional) – e default line type for shapes. It should
be a LineType enum or None.. Defaults to None.
Example
exporter = ExportDXF(unit=Unit.MM, line_weight=0.5)
exporter.add_layer("Layer 1", color=ColorIndex.RED, line_type=LineType.DASHED)
exporter.add_shape(shape_object, layer="Layer 1")
exporter.write("output.dxf")
Raises
ValueError – unit not supported
METRIC_UNITS = {<Unit.CM>, <Unit.M>, <Unit.MM>}
add_layer(name: str, *, color: ColorIndex | None = None, line_weight: float | None = None, line_type:
LineType | None = None) → Self
Adds a new layer to the DXF export with the given properties.
Parameters
• name (str) – The name of the layer definition. Must be unique among all layers.
• color (Optional[ColorIndex], optional) – The color index for shapes on this layer.
It can be specified as a ColorIndex enum or None. Defaults to None.
• line_weight (Optional[float], optional) – The line weight (stroke width) for
shapes on this layer, in millimeters. Defaults to None.
• line_type (Optional[LineType], optional) – The line type for shapes on this layer.
It should be a LineType enum or None. Defaults to None.
Returns
DXF document with additional layer
Return type
Self
add_shape(shape: Shape | Iterable[Shape], layer: str = '') → Self
Adds a shape to the specified layer.
Parameters
• shape (Shape | Iterable[Shape]) – The shape or collection of shapes to be added. It
can be a single Shape object or an iterable of Shape objects.



• layer (str, optional) – The name of the layer where the shape will be added. If not
specified, the default layer will be used. Defaults to “”.
Returns
Document with additional shape
Return type
Self
write(file_name: PathLike | str | bytes | BytesIO, ascii_format: bool = True)
Writes the DXF data to the specified file name.
Parameters
• file_name (PathLike | str | bytes | BytesIO) – The file name (including path)
where the DXF data will be written.
• ascii_format (bool, optional) – Export the file as ASCII (True) or binary (False)
DXF format. Defaults to True.
ExportSVG
class ExportSVG(unit: ~build123d.build_enums.Unit = <Unit.MM>, scale: float = 1, margin: float = 0,
fit_to_stroke: bool = True, precision: int = 6, fill_color: ~exporters.ColorIndex |
~ezdxf.colors.RGB | ~build123d.geometry.Color | None = None, line_color:
~exporters.ColorIndex | ~ezdxf.colors.RGB | ~build123d.geometry.Color | None =
ColorIndex.BLACK, line_weight: float = 0.09, line_type: ~exporters.LineType =
LineType.CONTINUOUS, dot_length: ~exporters.DotLength | float =
DotLength.INKSCAPE_COMPAT )
SVG file export functionality.
The ExportSVG class provides functionality for exporting 2D shapes to SVG (Scalable Vector Graphics) format.
SVG is a widely used vector graphics format that is supported by web browsers and various graphic editors.
Parameters
• unit (Unit, optional) – The unit used for the exported SVG. It should be one of the Unit
enums: Unit.MM, Unit.CM, or Unit.IN. Defaults to Unit.MM.
• scale (float, optional) – The scaling factor applied to the exported SVG. Defaults to
1.
• margin (float, optional) – The margin added around the exported shapes. Defaults to
0.
• fit_to_stroke (bool, optional) – A boolean indicating whether the SVG view box
should fit the strokes of the shapes. Defaults to True.
• precision (int, optional) – The number of decimal places used for rounding coordinates in the SVG. Defaults to 6.
• fill_color (ColorIndex | RGB | None, optional) – The default fill color for
shapes. It can be specified as a ColorIndex, an RGB tuple, or None. Defaults to None.
• line_color (ColorIndex | RGB | None, optional) – The default line color for
shapes. It can be specified as a ColorIndex or an RGB tuple, or None. Defaults to Export2D.DEFAULT_COLOR_INDEX.
• line_weight (float, optional) – The default line weight (stroke width) for shapes, in
millimeters. Defaults to Export2D.DEFAULT_LINE_WEIGHT.

1.17. Import/Export



• line_type (LineType, optional) – The default line type for shapes. It should be a LineType enum. Defaults to Export2D.DEFAULT_LINE_TYPE.
• dot_length (DotLength | float, optional) – The width of rendered dots in a
Can be either a DotLength enum or a float value in tenths of an inch. Defaults to
DotLength.INKSCAPE_COMPAT.
Example
exporter = ExportSVG(unit=Unit.MM, line_weight=0.5)
exporter.add_layer("Layer 1", fill_color=(255, 0, 0), line_color=(0, 0, 255))
exporter.add_shape(shape_object, layer="Layer 1")
exporter.write("output.svg")
Raises
ValueError – Invalid unit.
add_layer(name: str, *, fill_color: ColorIndex | RGB | Color | None = None, line_color: ColorIndex | RGB |
Color | None = ColorIndex.BLACK, line_weight: float = 0.09, line_type: LineType =
LineType.CONTINUOUS) → Self
Adds a new layer to the SVG export with the given properties.
Parameters
• name (str) – The name of the layer. Must be unique among all layers.
• fill_color (ColorIndex | RGB | Color | None, optional) – The fill color for
shapes on this layer. It can be specified as a ColorIndex, an RGB tuple, a Color, or None.
Defaults to None.
• line_color (ColorIndex | RGB | Color | None, optional) – The line color for
shapes on this layer. It can be specified as a ColorIndex or an RGB tuple, a Color, or None.
Defaults to Export2D.DEFAULT_COLOR_INDEX.
• line_weight (float, optional) – The line weight (stroke width) for shapes on this
layer, in millimeters. Defaults to Export2D.DEFAULT_LINE_WEIGHT.
• line_type (LineType, optional) – The line type for shapes on this layer. It should be
a LineType enum. Defaults to Export2D.DEFAULT_LINE_TYPE.
Raises
• ValueError – Duplicate layer name
• ValueError – Unknown linetype
Returns
Drawing with an additional layer
Return type
Self
add_shape(shape: Shape | Iterable[Shape], layer: str = '', reverse_wires: bool = False)
Adds a shape or a collection of shapes to the specified layer.
Parameters
• shape (Shape | Iterable[Shape]) – The shape or collection of shapes to be added. It
can be a single Shape object or an iterable of Shape objects.




• layer (str, optional) – The name of the layer where the shape(s) will be added. Defaults to “”.
• reverse_wires (bool, optional) – A boolean indicating whether the wires of the
shape(s) should be in reversed direction. Defaults to False.
Raises
ValueError – Undefined layer
write(path: PathLike | str | bytes | BytesIO)
Writes the SVG data to the specified file path.
Parameters
path (PathLike | str | bytes | BytesIO) – The file path where the SVG data will be
written.

1.17.3 3D Exporters
export_brep(to_export: Shape, file_path: PathLike | str | bytes | BytesIO | BinaryIO) → bool
Export this shape to a BREP file
Parameters
• to_export (Shape) – object or assembly
• file_path – Union[PathLike, str, bytes, BytesIO]: brep file path or memory buffer
Returns
write status
Return type
bool
export_gltf(to_export: ~build123d.topology.shape_core.Shape, file_path: ~os.PathLike | str | bytes, unit:
~build123d.build_enums.Unit = <Unit.MM>, binary: bool = False, linear_deflection: float = 0.001,
angular_deflection: float = 0.1) → bool
The glTF (GL Transmission Format) specification primarily focuses on the efficient transmission and loading
of 3D models as a compact, binary format that is directly renderable by graphics APIs like WebGL, OpenGL,
and Vulkan. It’s designed to store detailed 3D model data, including meshes (vertices, normals, textures, etc.),
animations, materials, and scene hierarchy, among other aspects.
Parameters
• to_export (Shape) – object or assembly
• file_path (Union[PathLike, str, bytes]) – glTF file path
• unit (Unit, optional) – shape units. Defaults to Unit.MM.
• binary (bool, optional) – output format. Defaults to False.
• linear_deflection (float, optional) – A linear deflection setting which limits the
distance between a curve and its tessellation. Setting this value too low will result in large
meshes that can consume computing resources. Setting the value too high can result in
meshes with a level of detail that is too low. The default is a good starting point for a range
of cases. Defaults to 1e-3.
• angular_deflection (float, optional) – Angular deflection setting which limits the
angle between subsequent segments in a polyline. Defaults to 0.1.
Raises
RuntimeError – Failed to write glTF file

1.17. Import/Export



Returns
write status
Return type
bool
export_step(to_export: ~build123d.topology.shape_core.Shape, file_path: ~os.PathLike | str | bytes |
~_io.BytesIO | ~typing.BinaryIO, unit: ~build123d.build_enums.Unit = <Unit.MM>, write_pcurves:
bool = True, precision_mode: ~build123d.build_enums.PrecisionMode =
<PrecisionMode.AVERAGE>, *, timestamp: str | ~datetime.datetime | None = None) → bool
Export a build123d Shape or assembly with color and label attributes. Note that if the color of a node in an
assembly isn’t set, it will be assigned the color of its nearest ancestor.
Parameters
• to_export (Shape) – object or assembly
• file_path (Union[PathLike, str, bytes, BytesIO]) – step file path
• unit (Unit, optional) – shape units. Defaults to Unit.MM.
• write_pcurves (bool, optional) – write parametric curves to the STEP file. Defaults
to True.
• precision_mode (PrecisionMode, optional) – geometric data precision. Defaults to
PrecisionMode.AVERAGE.
Raises
RuntimeError – Unknown Compound type
Returns
success
Return type
bool
export_stl(to_export: Shape, file_path: PathLike | str | bytes, tolerance: float = 0.001, angular_tolerance: float =
0.1, ascii_format: bool = False) → bool
Export STL
Exports a shape to a specified STL file.
Parameters
• to_export (Shape) – object or assembly
• file_path (Union[PathLike, str, bytes]) – The path and file name to write the STL
output to.
• tolerance (float, optional) – A linear deflection setting which limits the distance between a curve and its tessellation. Setting this value too low will result in large meshes that
can consume computing resources. Setting the value too high can result in meshes with a
level of detail that is too low. The default is a good starting point for a range of cases. Defaults
to 1e-3.
• angular_tolerance (float, optional) – Angular deflection setting which limits the
angle between subsequent segments in a polyline. Defaults to 0.1.
• ascii_format (bool, optional) – Export the file as ASCII (True) or binary (False) STL
format. Defaults to False (binary).
Returns
Success




Return type
bool
3D Mesh Export
Both 3MF and STL export (and import) are provided with the Mesher class. As mentioned above, the 3MF format it
provides is feature-rich and therefore has a slightly more complex API than the simple Shape exporters.
For example:
# Create the shapes and assign attributes
blue_shape = Solid.make_cone(20, 0, 50)
blue_shape.color = Color("blue")
blue_shape.label = "blue"
blue_uuid = uuid.uuid1()
red_shape = Solid.make_cylinder(5, 50).move(Location((0, -30, 0)))
red_shape.color = Color("red")
red_shape.label = "red"
# Create a Mesher instance as an exporter, add shapes and write
exporter = Mesher()
exporter.add_shape(blue_shape, part_number="blue-1234-5", uuid_value=blue_uuid)
exporter.add_shape(red_shape)
exporter.add_meta_data(
name_space="custom",
name="test_meta_data",
value="hello world",
metadata_type="str",
must_preserve=False,
)
exporter.add_code_to_metadata()
exporter.write("example.3mf")
exporter.write("example.stl")
class Mesher(unit: ~build123d.build_enums.Unit = <Unit.MM>)
Tool for exporting and importing meshed objects stored in 3MF or STL files.
Parameters
unit (Unit, optional) – model units. Defaults to Unit.MM.
add_code_to_metadata()
Add the code calling this method to the 3MF metadata with the custom name space build123d, name equal
to the base file name and the type as python
add_meta_data(name_space: str, name: str, value: str, metadata_type: str, must_preserve: bool)
Add meta data to the models
Parameters
• name_space (str) – categorizer of different metadata entries
• name (str) – metadata label
• value (str) – metadata content
• metadata_type (str) – metadata type
• must_preserve (bool) – metadata must not be removed if unused

1.17. Import/Export



add_shape(shape: ~build123d.topology.shape_core.Shape |
~collections.abc.Iterable[~build123d.topology.shape_core.Shape], linear_deflection: float =
0.001, angular_deflection: float = 0.1, mesh_type: ~build123d.build_enums.MeshType =
<MeshType.MODEL>, part_number: str | None = None, uuid_value: ~uuid.UUID | None =
None)
Add a shape to the 3MF/STL file.
Parameters
• shape (Union[Shape, Iterable[Shape]]) – build123d object
• linear_deflection (float, optional) – mesh control for edges. Defaults to 0.001.
• angular_deflection (float, optional) – mesh control for non-planar surfaces. Defaults to 0.1.
• mesh_type (MeshType, optional) – 3D printing use of mesh.
MeshType.MODEL.

Defaults to

• part_number (str, optional) – part #. Defaults to None.
• uuid_value (uuid, optional) – value from uuid package. Defaults to None.
Raises
• RuntimeError – 3mf mesh is invalid
• Warning – Degenerate shape skipped
• Warning – 3mf mesh is not manifold
get_mesh_properties() → list[dict]
Retrieve the properties from all the meshes
get_meta_data() → list[dict]
Retrieve all of the metadata
get_meta_data_by_key(name_space: str, name: str) → dict
Retrieve the metadata value and type for the provided name space and name
property library_version:

str

3MF Consortium Lib#MF version
property mesh_count:

int

Number of meshes in the model
property model_unit:

Unit

Unit used in the model
read(file_name: PathLike | str | bytes) → list[Shape]
Parameters
• Union[PathLike (file_name) – file path
• str – file path
• bytes] – file path
Raises
ValueError – Unknown file format - must be 3mf or stl
Returns
build123d shapes extracted from mesh file



Return type
list[Shape]
property triangle_counts:

list[int]

Number of triangles in each of the model’s meshes
property vertex_counts:

list[int]

Number of vertices in each of the models’s meshes
write(file_name: PathLike | str | bytes)
Parameters
• Union[Pathlike (file_name) – file path
• str – file path
• bytes] – file path
Raises
ValueError – Unknown file format - must be 3mf or stl
write_stream(stream: BytesIO, file_type: Literal['3mf', 'stl'])
Parameters
• stream (BytesIO) – byte stream
• file_type – output mesh format, either “3mf” or “stl”
Raises
ValueError – Unknown file format - must be 3mf or stl
ò Note
If you need to align multiple components for 3D printing, you can use the pack() function to arrange the objects
side by side and align them on the same plane. This ensures that your components are well-organized and ready for
the printing process.

1.17.4 2D Importers
import_dxf(dxf_file: str | PathLike | TextIO | BinaryIO) → ShapeList
Import shapes from a DXF file
Parameters
dxf_file (str | PathLike | TextIO | BinaryIO) – dxf file path or readable stream
Raises
DXFStructureError – file not found
Returns
build123d objects
Return type
ShapeList
import_svg(svg_file: str | ~pathlib.Path | ~typing.TextIO, *, flip_y: bool = True, align:
~build123d.build_enums.Align | tuple[~build123d.build_enums.Align, ~build123d.build_enums.Align]
| None = <Align.MIN>, ignore_visibility: bool = False, label_by: ~typing.Literal['id', 'class',
'inkscape:label'] | str = 'id') → ShapeList[Wire | Face]

1.17. Import/Export



Parameters
• svg_file (Union[str, Path , TextIO]) – svg file
• flip_y (bool, optional) – flip objects to compensate for svg orientation. Defaults to
True.
• align (Align | tuple[Align, Align] | None, optional) – alignment of the
SVG’s viewbox, if None, the viewbox’s origin will be at (0,0,0). Defaults to Align.MIN.
• ignore_visibility (bool, optional) – Defaults to False.
• label_by (str, optional) – XML attribute to use for imported shapes’ label property.
Defaults to “id”. Use inkscape:label to read labels set from Inkscape’s “Layers and Objects”
panel.
Raises
ValueError – unexpected shape type
Returns
objects contained in svg
Return type
ShapeList[Union[Wire, Face]]
import_svg_as_buildline_code(file_name: PathLike | str | bytes, precision: int = 6) → tuple[str, str]
translate_to_buildline_code
Translate the contents of the given svg file into executable build123d/BuildLine code.
Parameters
• file_name (PathLike | str | bytes]) – svg file name
• precision (int) – # digits to round values to. Defaults to # digits in TOLERANCE
Returns
code, builder instance name
Return type
tuple[str, str]

1.17.5 3D Importers
import_brep(file_name: PathLike | str | bytes) → Shape
Import shape from a BREP file
Parameters
file_name (Union[PathLike, str, bytes]) – brep file
Raises
ValueError – file not found
Returns
build123d object
Return type
Shape
import_step(filename: PathLike | str | bytes) → Compound
Extract shapes from a STEP file and return them as a Compound object.
Parameters
file_name (Union[PathLike, str, bytes]) – file path of STEP file to import



Raises
ValueError – can’t open file
Returns
contents of STEP file
Return type
Compound
import_stl(file_name: ~os.PathLike | str | bytes, model_unit: ~build123d.build_enums.Unit = <Unit.MM>) →
Face
Extract shape from an STL file and return it as a Face reference object.
Note that importing with this method and creating a reference is very fast while creating an editable model (with
Mesher) may take minutes depending on the size of the STL file.
Parameters
• file_name (Union[PathLike, str, bytes]) – file path of STL file to import
• model_unit (Unit, optional) – the default unit used when creating the model. For example, Blender defaults to Unit.M. Defaults to Unit.MM.
Raises
• ValueError – Could not import file
• ValueError – Invalid model_unit
Returns
STL model
Return type
Face
STL Reconstruction
The detect_primitives() helper can be used during STL reconstruction to detect analytic planes, cylinders, and
spheres in a mesh-like shape and generate algebra-mode code fragments to aid manual redesign.
See Tutorial: Reconstructing a Design from an STL for the full workflow and limitations.
detect_primitives(mesh: Shape) → tuple[ShapeList[Face], ShapeList[Face], list[str]]
Detect analytic primitives in a mesh and return faces, leftovers, and code.
This is the user-facing entry point for STL-to-BREP reconstruction. The mesh is indexed first so face geometry
and adjacency can be reused throughout the pipeline.
Detection proceeds in stages:
1. High-confidence planes are found first from cleaned proxy faces.
2. Spheres are found next from broad radius-signature classification, connected or sewn regions, local sphere
fitting, and region growth.
3. Cylinders are detected from area-grouped sewn regions and local cylinder seeds, then grown, refit, and
validated.
4. Remaining coplanar connected components are detected as fallback planes.
Each accepted patch is converted into a build123d Face, unmatched mesh faces are returned as leftovers, and the
generated code strings are sorted in the same order as the returned primitives.

1.17. Import/Export



3D Mesh Import
Both 3MF and STL import (and export) are provided with the Mesher class.
For example:
importer = Mesher()
cone, cyl = importer.read("example.3mf")
print(
f"{importer.mesh_count=}, {importer.vertex_counts=}, {importer.triangle_counts=}"
)
print(f"Imported model unit: {importer.model_unit}")
print(f"{cone.label=}")
print(f"{cone.color.to_tuple()=}")
print(f"{cyl.label=}")
print(f"{cyl.color.to_tuple()=}")
importer.mesh_count=2, importer.vertex_counts=[66, 52], importer.triangle_counts=[128,␣
˓→100]
Imported model unit: Unit.MM
cone.label='blue'
cone.color.to_tuple()=(0.0, 0.0, 1.0, 1.0)
cyl.label='red'
cyl.color.to_tuple()=(1.0, 0.0, 0.0, 1.0)

1.18 Advanced Topics
1.18.1 Performance considerations in algebra mode
Creating lots of Shapes in a loop means for every step fuse and clean will be called. In an example like the below,
both functions get slower and slower the more objects are already fused. Overall it takes on an M1 Mac 4.76 sec.
diam = 80
holes = Sketch()
r = Rectangle(2, 2)
for loc in GridLocations(4, 4, 20, 20):
if loc.position.X**2 + loc.position.Y**2 < (diam / 2 - 1.8) ** 2:
holes += loc * r
c = Circle(diam / 2) - holes
One way to avoid it is to use lazy evaluation for the algebra operations. Just collect all objects and then call fuse (+)
once with all objects and clean once. Overall it takes 0.19 sec.
r = Rectangle(2, 2)
holes = [
loc * r
for loc in GridLocations(4, 4, 20, 20).locations
if loc.position.X**2 + loc.position.Y**2 < (diam / 2 - 1.8) ** 2
]
c = Circle(diam / 2) - holes
Another way to leverage the vectorized algebra operations is to add a list comprehension of objects to an empty Part,
Sketch or Curve:



polygons = Sketch() + [
loc * RegularPolygon(radius=5, side_count=5)
for loc in GridLocations(40, 30, 2, 2)
]
This again ensures one single fuse and clean call.

1.18.2 Location arithmetic for algebra mode
Position a shape relative to the XY plane
For the following use the helper function:
def location_symbol(location: Location, scale: float = 1) -> Compound:
return Compound.make_triad(axes_scale=scale).locate(location)
def plane_symbol(plane: Plane, scale: float = 1) -> Compound:
triad = Compound.make_triad(axes_scale=scale)
circle = Circle(scale * .8).edge()
return (triad + circle).locate(plane.location)
1. Positioning at a location
loc = Location((0.1, 0.2, 0.3), (10, 20, 30))
face = loc * Rectangle(1, 2)
show_object(face, name="face")
show_object(location_symbol(loc), name="location")

2) Positioning on a plane
plane = Plane.XZ
face = plane * Rectangle(1, 2)
show_object(face, name="face")
show_object(plane_symbol(plane), name="plane")

1.18. Advanced Topics



Note: The x-axis and the y-axis of the plane are on the x-axis and the z-axis of the world coordinate system (red and
blue axis).
Relative positioning to a plane
1. Position an object on a plane relative to the plane
loc = Location((0.1, 0.2, 0.3), (10, 20, 30))
face = loc * Rectangle(1,2)
box = Plane(loc) * Pos(0.2, 0.4, 0.1) * Box(0.2, 0.2, 0.2)
# box = Plane(face.location) * Pos(0.2, 0.4, 0.1) * Box(0.2, 0.2, 0.2)
# box = loc * Pos(0.2, 0.4, 0.1) * Box(0.2, 0.2, 0.2)
show_object(face, name="face")
show_object(location_symbol(loc), name="location")
show_object(box, name="box")

The X, Y, Z components of Pos(0.2, 0.4, 0.1) are relative to the x-axis, y-axis or z-axis of the underlying location
loc.
Note: Plane(loc) *, Plane(face.location) * and loc * are equivalent in this example.



2. Rotate an object on a plane relative to the plane
loc = Location((0.1, 0.2, 0.3), (10, 20, 30))
face = loc * Rectangle(1,2)
box = Plane(loc) * Rot(Z=80) * Box(0.2, 0.2, 0.2)
show_object(face, name="face")
show_object(location_symbol(loc), name="location")
show_object(box, name="box")

The box is rotated via Rot(Z=80) around the z-axis of the underlying location (and not of the z-axis of the world).
More general:
loc = Location((0.1, 0.2, 0.3), (10, 20, 30))
face = loc * Rectangle(1,2)
box = loc * Rot(20, 40, 80) * Box(0.2, 0.2, 0.2)
show_object(face, name="face")
show_object(location_symbol(loc), name="location")
show_object(box, name="box")

1.18. Advanced Topics



The box is rotated via Rot(20, 40, 80) around all three axes relative to the plane.
3. Rotate and position an object relative to a location
loc = Location((0.1, 0.2, 0.3), (10, 20, 30))
face = loc * Rectangle(1,2)
box = loc * Rot(20, 40, 80) * Pos(0.2, 0.4, 0.1) * Box(0.2, 0.2, 0.2)
show_object(face, name="face")
show_object(location_symbol(loc), name="location")
show_object(box, name="box")
show_object(location_symbol(loc * Rot(20, 40, 80), 0.5), options=
˓→{"color":(0, 255, 255)}, name="local_location")

The box is positioned via Pos(0.2, 0.4, 0.1) relative to the location loc * Rot(20, 40, 80)
4. Position and rotate an object relative to a location
loc = Location((0.1, 0.2, 0.3), (10, 20, 30))
face = loc * Rectangle(1,2)
(continues on next page)




(continued from previous page)

box = loc * Pos(0.2, 0.4, 0.1) * Rot(20, 40, 80) * Box(0.2, 0.2, 0.2)
show_object(face, name="face")
show_object(location_symbol(loc), name="location")
show_object(box, name="box")
show_object(location_symbol(loc * Pos(0.2, 0.4, 0.1), 0.5), options=
˓→{"color":(0, 255, 255)}, name="local_location")

Note: This is the same as box = loc * Location((0.2, 0.4, 0.1), (20, 40, 80)) * Box(0.2, 0.2, 0.
2)

1.18.3 Algebraic definition
Objects and arithmetic
Set definitions:
𝐶 3 is the set of all Part objects p with p._dim = 3
𝐶 2 is the set of all Sketch objects s with s._dim = 2
𝐶 1 is the set of all Curve objects c with c._dim = 1
Neutral elements:
𝑐30 is the empty Part object p0 = Part() with p0._dim = 3 and p0.wrapped = None
𝑐20 is the empty Sketch object s0 = Sketch() with s0._dim = 2 and s0.wrapped = None
𝑐10 is the empty Curve object c0 = Curve() with c0._dim = 1 and c0.wrapped = None
Sets of predefined basic shapes:
𝐵 3 := { Part, Box, Cylinder, Cone, Sphere, Torus, Wedge, Hole, CounterBoreHole, CounterSinkHole }
𝐵 2 := { Sketch, Rectangle, Circle, Ellipse, Rectangle, Polygon, RegularPolygon, Text, Trapezoid,
SlotArc, SlotCenterPoint, SlotCenterToCenter, SlotOverall }
𝐵 1 := { Curve, Bezier, FilletPolyline, PolarLine, Polyline, Spline, Helix, CenterArc,
EllipticalCenterArc,
ParabolicCenterArc,
HyperbolicCenterArc,
RadiusArc,
SagittaArc,
TangentArc, ThreePointArc, JernArc }

1.18. Advanced Topics



with 𝐵 3 ⊂ 𝐶 3 , 𝐵 2 ⊂ 𝐶 2 and 𝐵 1 ⊂ 𝐶 1
Operations:
+ : 𝐶 𝑛 × 𝐶 𝑛 → 𝐶 𝑛 with (𝑎, 𝑏) ↦→ 𝑎 + 𝑏, for 𝑛 = 1, 2, 3
𝑎 + 𝑏 := a.fuse(b) for each operation
− : 𝐶 𝑛 → 𝐶 𝑛 with 𝑎 ↦→ −𝑎, for 𝑛 = 1, 2, 3
𝑏 + (−𝑎) := b.cut(a) for each operation (implicit definition)
& : 𝐶 𝑛 × 𝐶 𝑛 → 𝐶 𝑛 with (𝑎, 𝑏) ↦→ 𝑎 & 𝑏, for 𝑛 = 2, 3
𝑎 & 𝑏 := a.intersect(b) for each operation
• & is not defined for 𝑛 = 1 in build123d
• The following relationship holds: 𝑎 & 𝑏 = (𝑎 + 𝑏) + −(𝑎 + (−𝑏)) + −(𝑏 + (−𝑎))
Abelian groups
(𝐶 𝑛 , 𝑐𝑛0 , +, −) are abelian groups for 𝑛 = 1, 2, 3.
• The implementation a - b = a.cut(b) needs to be read as 𝑎 + (−𝑏) since the group does not have a binary
- operation. As such, 𝑎 − (𝑏 − 𝑐) = 𝑎 + −(𝑏 + −𝑐)) ̸= 𝑎 − 𝑏 + 𝑐
• This definition also includes that neither - nor & are commutative.
Locations, planes and location arithmetic
Set definitions:
𝐿 := { Location((x, y, z), (a, b, c)) : 𝑥, 𝑦, 𝑧 ∈ 𝑅 ∧ 𝑎, 𝑏, 𝑐 ∈ 𝑅}
with 𝑎, 𝑏, 𝑐 being angles in degrees.
𝑃 := { Plane(o, x, z) : 𝑜, 𝑥, 𝑧𝑅3 ∧ ‖𝑥‖ = ‖𝑧‖ = 1}
with o being the origin and x, z the x- and z-direction of the plane.
Neutral element: 𝑙0 ∈ 𝐿: Location()
Operations:
* : 𝐿 × 𝐿 → 𝐿 with (𝑙1 , 𝑙2 ) ↦→ 𝑙1 * 𝑙2
𝑙1 * 𝑙2 := l1 * l2 (multiply two locations)
* : 𝑃 × 𝐿 → 𝑃 with (𝑝, 𝑙) ↦→ 𝑝 * 𝑙
𝑝 * 𝑙 := Plane(p.location * l) (move plane 𝑝 ∈ 𝑃 to location 𝑙 ∈ 𝐿)
Inverse element: 𝑙−1 ∈ 𝐿: l.inverse()
Placing objects onto planes
* : 𝑃 × 𝐶 𝑛 → 𝐶 𝑛 with (𝑝, 𝑐) ↦→ 𝑝 * 𝑐, for 𝑛 = 1, 2, 3
Locate an object 𝑐 ∈ 𝐶 𝑛 onto plane 𝑝 ∈ 𝑃 , i.e. c.moved(p.location)
Placing objects at locations
* : 𝐿 × 𝐶 𝑛 → 𝐶 𝑛 with (𝑙, 𝑐) ↦→ 𝑙 * 𝑐, for 𝑛 = 1, 2, 3
Locate an object 𝑐 ∈ 𝐶 𝑛 at location 𝑙 ∈ 𝐿, i.e. c.moved(l)




1.18.4 CAD Object Centers
Finding the center of a CAD object is a surprisingly complex operation. To illustrate let’s consider two examples: a
simple isosceles triangle and a curved line (their bounding boxes are shown with dashed lines):
One can see that there is are significant differences between the different types of centers. To allow the designer to
choose the center that makes the most sense for the given shape there are three possible values for the CenterOf
Enum:
CenterOf
CenterOf.BOUNDING_BOX
CenterOf.GEOMETRY
CenterOf.MASS

Symbol

1D

2D

3D

Compound

✓
✓
✓

✓
✓
✓

✓

✓

✓

✓

1.18.5 Debugging & Logging
Debugging problems with your build123d design involves the same techniques one would use to debug any Python
source code; however, there are some specific techniques that might be of assistance. The following sections describe
these techniques.
Python Debugger
Many Python IDEs have step by step debugging systems that can be used to walk through your code monitoring its
operation with full visibility of all Python objects. Here is a screenshot of the Visual Studio Code debugger in action:

This shows that a break-point has been encountered and the code operation has been stopped. From here all of the
Python variables are visible and the system is waiting on input from the user on how to proceed. One can enter the
code that assigns top_face by pressing the down arrow button on the top right. Following code execution like this is
a very powerful debug technique.

1.18. Advanced Topics



Logging
Build123d support standard python logging and generates its own log stream. If one is using cq-editor as a display
system there is a built in Log viewer tab that shows the current log stream - here is an example of a log stream:
[18:43:44.678646] INFO: Entering BuildPart with mode=Mode.ADD which is in different␣
˓→scope as parent
[18:43:44.681751] INFO: BuildPart context requested by Box
[18:43:44.685950] INFO: Completed integrating 1 object(s) into part with Mode=Mode.ADD
[18:43:44.690072] INFO: GridLocations is pushing 4 points: [(p=(-30.00, -20.00, 0.00),␣
˓→o=(-0.00, 0.00, -0.00)), (p=(-30.00, 20.00, 0.00), o=(-0.00, 0.00, -0.00)), (p=(30.00,␣
˓→-20.00, 0.00), o=(-0.00, 0.00, -0.00)), (p=(30.00, 20.00, 0.00), o=(-0.00, 0.00, -0.
˓→00))]
[18:43:44.691604] INFO: BuildPart context requested by Hole
[18:43:44.724628] INFO: Completed integrating 4 object(s) into part with Mode=Mode.
˓→SUBTRACT
[18:43:44.728681] INFO: GridLocations is popping 4 points
[18:43:44.747358] INFO: BuildPart context requested by chamfer
[18:43:44.762429] INFO: Completed integrating 1 object(s) into part with Mode=Mode.
˓→REPLACE
[18:43:44.766729] INFO: Exiting BuildPart
The build123d logger is defined by:
logging.getLogger("build123d").addHandler(logging.NullHandler())
logger = logging.getLogger("build123d")
To export logs to a file, the following configuration is recommended:
logging.basicConfig(
filename="myapp.log",
level=logging.INFO,
format="%(name)s-%(levelname)s %(asctime)s - [%(filename)s:%(lineno)s - \
%(funcName)20s() ] - %(message)s",
)
Logs can be easily placed in your code - here is an example:
logger.info("Exiting %s", type(self).__name__)
Printing
Sometimes the best debugging aid is just placing a print statement in your code. Many of the build123d classes are
setup to provide useful information beyond their class and location in memory, as follows:
plane = Plane.XY.offset(1)
print(f"{plane=}")
plane=Plane(o=(0.00, 0.00, 1.00), x=(1.00, 0.00, 0.00), z=(0.00, 0.00, 1.00))
which shows the origin, x direction, and z direction of the plane.




1.19 Cheat Sheet
Stateful Contexts
BuildLine BuildPart BuildSketch
GridLocations HexLocations Locations PolarLocations
Objects

1D - BuildLine

Airfoil
Bezier
BlendCurve
BSpline
CenterArc
ConstrainedArcs
ConstrainedLines
DoubleTangentArc
EllipticalCenterArc
ParabolicCenterArc
HyperbolicCenterArc
FilletPolyline
Helix
IntersectingLine
JernArc
Line
PolarLine
Polyline
RadiusArc
SagittaArc
Spline
TangentArc
ThreePointArc
2D - BuildSketch
Arrow
ArrowHead
Circle
DimensionLine
Ellipse
ExtensionLine
Polygon
Rectangle
RectangleRounded
RegularPolygon
SlotArc
SlotCenterPoint
SlotCenterToCenter
SlotOverall
Text
TechnicalDrawing
1.19. Cheat Sheet



Trapezoid
Triangle
3D - BuildPart
Box
Cone
ConvexPolyhedron
CounterBoreHole
CounterSinkHole
Cylinder
Hole
Sphere
Torus
Wedge
Operations

1D - BuildLine

add()
bounding_box()
mirror()
offset()
project()
scale()
split()
2D - BuildSketch
add()
chamfer()
fillet()
full_round()
make_face()
make_hull()
mirror()
offset()
project()
scale()
split()
sweep()
trace()
3D - BuildPart
add()
chamfer()
draft()
extrude()
fillet()
loft()
make_brake_formed()
mirror()




offset()
project()
revolve()
scale()
section()
split()
sweep()
Selectors

1D - BuildLine

vertices()
edges()
wires()
2D - BuildSketch
vertices()
edges()
wires()
faces()
3D - BuildPart
vertices()
edges()
wires()
faces()
solids()
Selector Operators
Operator

Operand

Method

>
<
>>
<<
|
[]

Axis, Edge, Wire, SortBy
Axis, Edge, Wire, SortBy
Axis, Edge, Wire, SortBy
Axis, Edge, Wire, SortBy
Axis, Plane, GeomType

sort_by()
sort_by()
group_by()[-1]
group_by()[0]
filter_by()
python indexing / slicing
filter_by_position()

Axis
Edge and Wire Operators
Operator

Operand

Method

Description

@
%
^

0.0 <= float <= 1.0
0.0 <= float <= 1.0
0.0 <= float <= 1.0

position_at()
tangent_at()
location_at()

Position as Vector along object
Tangent as Vector along object
Location along object

Shape Operators

1.19. Cheat Sheet



Operator

Operand

Method

Description

==
+
&

Any
Shape | Iterable[Shape]
Shape | Iterable[Shape]
Shape | Iterable[Shape]

is_same()

Compare CAD objects not including meta data
Add CAD objects
Subtract CAD objects
Intersect CAD objects

Plane Operators
Operator

Operand

Description

==
!=
*

Plane
Plane
Plane
Location | Shape

Check for equality
Check for inequality
Reverse direction of normal
Relocate

Location Operators
Operator

Operand

Description

==
!=
&
*

Location
Location
Location
Axis | Location | Plane | VectorLike | Shape
Shape | Location | Iterable[Location]

Check for equality
Check for inequality
Reverse direction of normal
Intersect
Relocate

Vector Operators
Operator

Operand

Method

Description

+
*
/

Vector
Vector
float
float

add()
sub()
multiply()
multiply()

add
subtract
multiply by scalar
divide by scalar

Operator

Operand

Method

+
-

Vertex
Vertex

add()
sub()

Vertex Operators

Enums




Align
MIN, CENTER, MAX
ApproxOptionARC, NONE, SPLINE
AngularDirection
CLOCKWISE, COUNTER_CLOCKWISE
CenterOf
GEOMETRY, MASS, BOUNDING_BOX
Extrinsic XYZ, XZY, YZX, YXZ, ZXY, ZYX, XYX, XZX, YZY, YXY, ZXZ, ZYZ
FontStyle REGULAR, BOLD, BOLDITALIC, ITALIC
FrameMethodCORRECTED, FRENET
GeomType
BEZIER, BSPLINE, CIRCLE, CONE, CYLINDER, ELLIPSE, EXTRUSION, HYPERBOLA,
LINE, OFFSET, OTHER, PARABOLA, PLANE, REVOLUTION, SPHERE, TORUS
Intrinsic XYZ, XZY, YZX, YXZ, ZXY, ZYX, XYX, XZX, YZY, YXY, ZXZ, ZYZ
HeadType
CURVED, FILLETED, STRAIGHT
Keep
ALL, TOP, BOTTOM, BOTH, INSIDE, OUTSIDE
Kind
ARC, INTERSECTION, TANGENT
LengthMode DIAGONAL, HORIZONTAL, VERTICAL
MeshType
OTHER, MODEL, SUPPORT, SOLIDSUPPORT
Mode
ADD, SUBTRACT, INTERSECT, REPLACE, PRIVATE
NumberDisplay
DECIMAL, FRACTION
PageSize
A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, LEDGER, LEGAL, LETTER
PositionModeLENGTH, PARAMETER
PrecisionMode
LEAST, AVERAGE, GREATEST, SESSION
Select
ALL, LAST, NEW
Side
BOTH, LEFT, RIGHT
SortBy
LENGTH, RADIUS, AREA, VOLUME, DISTANCE
TextAlign BOTTOM, CENTER, LEFT, RIGHT, TOP, TOPFIRSTLINE
Transition RIGHT, ROUND, TRANSFORMED
Unit
MC, MM, CM, M, IN, FT
