# build123d API Reference: Import/Export & Joints

class Sketch(obj: TopoDS_Compound | Iterable[Shape] | None = None, label: str = '', color: Color | None =
None, material: FinishedMaterial | None = None, joints: dict[str, Joint] | None = None, parent:
Compound | None = None, children: Sequence[Shape] | None = None)
A Compound containing 2D objects - aka Faces
build123d_type:

ClassVar[str] = 'Sketch'

1.22.3 Import/Export
Methods and functions specific to exporting and importing build123d objects are defined below.
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
import_svg(svg_file: str | ~pathlib.Path | ~typing.TextIO, *, flip_y: bool = True, align:
~build123d.build_enums.Align | tuple[~build123d.build_enums.Align, ~build123d.build_enums.Align]
| None = <Align.MIN>, ignore_visibility: bool = False, label_by: ~typing.Literal['id', 'class',
'inkscape:label'] | str = 'id') → ShapeList[Wire | Face]
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

1.22. Direct API Reference



1.22.4 Joint Object
Base Joint class which is used to position Solid and Compound objects relative to each other are defined below. The
Joints section contains the class description of the derived Joint classes.
class Joint(label: str, parent: BuildPart | Solid | Compound)
Abstract Base Joint class - used to join two components together
Parameters
parent (Union[Solid, Compound]) – object that joint to bound to
Variables
• label (str) – user assigned label
• parent (Shape) – object joint is bound to
• connected_to (Joint) – joint that is connect to this joint
abstract connect_to(*args, **kwargs)
All derived classes must provide a connect_to method
abstract property location:

Location

Location of joint
abstract relative_to(*args, **kwargs) → Location
Return relative location to another joint
abstract property symbol:

Compound

A CAD object positioned in global space to illustrate the joint

