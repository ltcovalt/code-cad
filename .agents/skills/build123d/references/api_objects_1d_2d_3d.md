# build123d API Reference: 1D, 2D & 3D Geometric Objects


1.22.1 Geometric Objects
The geometric classes defined by build123d are defined below. This parameters to the CAD objects described in the
following section are frequently of these types.




Vector

PlaneMeta

Plane

OrientedBoundBox

NotAllLocationLikeError

Matrix
Pos
Location
Rotation

JSONEncoder

GeomEncoder

Color

BoundBox

AxisMeta

Axis

class Axis(*args: Any, **kwargs: Any)
Axis defined by point and direction or by two points
Parameters
• origin (VectorLike) – start point
• direction (VectorLike) – direction
• end_point (VectorLike) – point used with origin to define direction
• edge (Edge) – origin & direction defined by start of edge
• location (Location) – location to convert to axis
1.22. Direct API Reference



Variables
• position (Vector) – the global position of the axis origin
• direction (Vector) – the normalized direction vector
• wrapped (gp_Ax1) – the OCP axis object
__copy__() → Axis
Return copy of self
__deepcopy__(_memo) → Axis
Return deepcopy of self
__neg__() → Axis
Flip direction operator angle_between(other: Axis) → float
calculate angle between axes
Computes the angular value, in degrees, between the direction of self and other between 0° and 360°.
Parameters
other (Axis) – axis to compare to
Returns
angle between axes
Return type
float
build123d_type:

ClassVar[str] = 'Axis'

property direction: Vector
The normalized direction of the Axis
intersect(*args, **kwargs)
Find intersection of axis and geometric object or shape
is_coaxial(other: Axis, angular_tolerance: float = 1e-05, linear_tolerance: float = 1e-05) → bool
are axes coaxial
True if the angle between self and other is lower or equal to angular_tolerance and the distance between
self and other is lower or equal to linear_tolerance.
Parameters
• other (Axis) – axis to compare to
• angular_tolerance (float, optional) – max angular deviation. Defaults to 1e-5.
• linear_tolerance (float, optional) – max linear deviation. Defaults to 1e-5.
Returns
axes are coaxial
Return type
bool
is_normal(other: Axis, angular_tolerance: float = 1e-05) → bool
are axes normal
Returns True if the direction of this and another axis are normal to each other. That is, if the angle between
the two axes is equal to 90° within the angular_tolerance.



Parameters
• other (Axis) – axis to compare to
• angular_tolerance (float, optional) – max angular deviation. Defaults to 1e-5.
Returns
axes are normal
Return type
bool
is_opposite(other: Axis, angular_tolerance: float = 1e-05) → bool
are axes opposite
Returns True if the direction of this and another axis are parallel with opposite orientation. That is, if the
angle between the two axes is equal to 180° within the angular_tolerance.
Parameters
• other (Axis) – axis to compare to
• angular_tolerance (float, optional) – max angular deviation. Defaults to 1e-5.
Returns
axes are opposite
Return type
bool
is_parallel(other: Axis, angular_tolerance: float = 1e-05) → bool
are axes parallel
Returns True if the direction of this and another axis are parallel with same orientation or opposite orientation. That is, if the angle between the two axes is equal to 0° or 180° within the angular_tolerance.
Parameters
• other (Axis) – axis to compare to
• angular_tolerance (float, optional) – max angular deviation. Defaults to 1e-5.
Returns
axes are parallel
Return type
bool
is_skew(other: Axis, tolerance: float = 1e-05) → bool
are axes skew
Returns True if this axis and another axis are skew, meaning they are neither parallel nor coplanar. Two
axes are skew if they do not lie in the same plane and never intersect.
Mathematically, this means:
• The axes are not parallel (the cross product of their direction vectors is nonzero).
• The axes are not coplanar (the vector between their positions is not aligned with the plane spanned
by their directions).
If either condition is false (i.e., the axes are parallel or coplanar), they are not skew.
Parameters
• other (Axis) – axis to compare to

1.22. Direct API Reference



• tolerance (float, optional) – max deviation. Defaults to 1e-5.
Returns
axes are skew
Return type
bool
located(new_location: Location)
relocates self to a new location possibly changing position and direction
property location:

Location

Return self as Location
property position:

Vector

The position or origin of the Axis
reverse() → Axis
Return a copy of self with the direction reversed
property wrapped
OCP object
class BoundBox(*args, **kwargs)
A BoundingBox for a Shape
add(obj: tuple[float, float, float] | Vector | BoundBox, tol: float | None = None) → BoundBox
Returns a modified (expanded) bounding box
obj can be one of several things:
1. a 3-tuple corresponding to x,y, and z amounts to add
2. a vector, containing the x,y,z values to add
3. another bounding box, where a new box will be created that encloses both.
This bounding box is not changed.
Parameters
• obj – tuple[float, float, float] | Vector | BoundBox]:
• tol – float: (Default value = None)
Returns:
center() → Vector
Return center of the bounding box
property diagonal:

float

body diagonal length (i.e. object maximum size)
static find_outside_box_2d(bb1: BoundBox, bb2: BoundBox) → BoundBox | None
Compares bounding boxes
Compares bounding boxes. Returns none if neither is inside the other. Returns the outer one if either is
outside the other.
BoundBox.is_inside works in 3d, but this is a 2d bounding box, so it doesn’t work correctly plus, there was
all kinds of rounding error in the built-in implementation i do not understand.
Parameters




• bb1 – BoundBox:
• bb2 – BoundBox:
Returns:
classmethod from_topo_ds(shape: TopoDS_Shape, tolerance: float | None = None, optimal: bool = True)
→ BoundBox
Constructs a bounding box from a TopoDS_Shape
Parameters
• shape – TopoDS_Shape:
• tolerance – float: (Default value = None)
• optimal – bool: This algorithm builds precise bounding box (Default value = True)
Returns:
is_inside(second_box: BoundBox) → bool
Is the provided bounding box inside this one?
Parameters
b2 – BoundBox:
Returns:
property measure:

float

Return the overall Lebesgue measure of the bounding box.
• For 1D objects: length
• For 2D objects: area
• For 3D objects: volume
overlaps(other: BoundBox, tolerance: float = 1e-06) → bool
Check if this bounding box overlaps with another.
Parameters
• other – BoundBox to check overlap with
• tolerance – Distance tolerance for overlap detection
Returns
True if bounding boxes overlap (share any volume), False otherwise
to_align_offset(align: Align | None | tuple[Align | None, Align | None] | tuple[Align | None, Align | None,
Align | None]) → Vector
Amount to move object to achieve the desired alignment
class Color(*args, **kwargs)
Color object based on OCCT Quantity_ColorRGBA.
Variables
wrapped (Quantity_ColorRGBA) – the OCP color object
__copy__() → Color
Return copy of self
__deepcopy__(_memo) → Color
Return deepcopy of self

1.22. Direct API Reference



classmethod categorical_set(color_count: int, starting_hue: str | tuple[str, float | int] | tuple[float | int,
float | int, float | int] | tuple[float | int, float | int, float | int, float | int] | int |
tuple[int, int] | Color | Quantity_ColorRGBA | float = 0.0, alpha: float |
Iterable[float] = 1.0) → list[Color]
Generate a palette of evenly spaced colors.
Creates a list of visually distinct colors suitable for representing discrete categories (such as different parts,
assemblies, or data series). Colors are evenly spaced around the hue circle and share consistent lightness
and saturation levels, resulting in balanced perceptual contrast across all hues.
Produces palettes similar in appearance to the Tableau 10 and D3 Category10 color sets—both widely
recognized standards in data visualization for their clarity and accessibility. These values have been empirically chosen to maintain consistent perceived brightness across hues while avoiding overly vivid or dark
colors.
Parameters
• color_count (int) – Number of colors to generate.
• starting_hue (ColorLike | float) – Either a Color-like object or a hue value in the
range [0.0, 1.0] that defines the starting color.
• alpha (float | Iterable[float]) – Alpha value(s) for the colors. Can be a single
float or an iterable of length color_count.
Returns
List of generated colors.
Return type
list[Color]
Raises
ValueError – If starting_hue is out of range or alpha length mismatch.
class Location(*args: Any, **kwargs: Any)
Location in 3D space. Depending on usage can be absolute or relative.
This class wraps the TopLoc_Location class from OCCT. It can be used to move Shape objects in both relative
and absolute manner. It is the preferred type to locate objects in build123d.
Variables
wrapped (TopLoc_Location) – the OCP location object
__copy__() → Location
Lib/copy.py shallow copy
__deepcopy__(_memo) → Location
Lib/copy.py deep copy
__eq__(other: object) → bool
Compare Locations
__mul__(other: Location | Iterable[Location]) → Location | list[Location]
Combine locations
__neg__() → Location
Flip the orientation without changing the position operator __pow__(exponent: int) → Location
build123d_type:


ClassVar[str] = 'Location'



center() → Vector
Return center of the location - useful for sorting
intersect(*args, **kwargs)
Find intersection of location and geometric object or shape
inverse() → Location
Inverted location
mirror(mirror_plane: Plane) → Location
Return a new Location mirrored across the given plane.
This method reflects both the position and orientation of the current Location across the specified mirror_plane using affine vector mathematics.
Due to the mathematical properties of reflection:
• The true mirror of a right-handed coordinate system is a left-handed one.
However, build123d requires all coordinate systems to be right-handed. Therefore, this implementation: Reflects the X and Z directions across the mirror plane - Recomputes the Y direction as: Y = X × Z
This ensures the resulting Location maintains a valid right-handed frame, while remaining as close as
possible to the geometric mirror.
Parameters
mirror_plane (Plane) – The plane to mirror across.
Returns
A new mirrored Location that preserves right-handedness.
Return type
Location
property orientation:

Vector

Extract orientation/rotation component of self
Returns
orientation part of Location
Return type
Vector
property position:

Vector

Extract Position component of self
Returns
Position part of Location
Return type
Vector
property wrapped:

TopLoc_Location

OCP object
property x_axis:

Axis

Default X axis when used as a plane
property y_axis:

Axis

Default Y axis when used as a plane

1.22. Direct API Reference



property z_axis:

Axis

Default Z axis when used as a plane
class Pos(*args, **kwargs)
A position only sub-class of Location
Rot
alias of Rotation
class Matrix(*args, **kwargs)
A 3d , 4x4 transformation matrix.
Used to move geometry in space.
The provided “matrix” parameter may be None, a gp_GTrsf, or a nested list of values.
If given a nested list, it is expected to be of the form:
[[m11, m12, m13, m14],
[m21, m22, m23, m24], [m31, m32, m33, m34]]
A fourth row may be given, but it is expected to be: [0.0, 0.0, 0.0, 1.0] since this is a transform matrix.
Variables
wrapped (gp_GTrsf ) – the OCP transformation function
__copy__() → Matrix
Return copy of self
__deepcopy__(_memo) → Matrix
Return deepcopy of self
inverse() → Matrix
Invert Matrix
multiply(other)
Matrix multiplication
rotate(axis: Axis, angle: float)
General rotate about axis by angle in degrees
transposed_list() → Sequence[float]
Needed by the cqparts gltf exporter
class Plane(*args: Any, **kwargs: Any)
A plane is positioned in space with a coordinate system such that the plane is defined by the origin, x_dir (X
direction), y_dir (Y direction), and z_dir (Z direction) of this coordinate system, which is the “local coordinate
system” of the plane. The z_dir is a vector normal to the plane. The coordinate system is right-handed.
A plane allows the use of local 2D coordinates, which are later converted to global, 3d coordinates when the
operations are complete.
Planes can be created from faces as workplanes for feature creation on objects.




Name

x_dir

y_dir

z_dir

XY
YZ
ZX
XZ
YX
ZY
front
back
left
right
top
bottom
isometric

+x
+y
+z
+x
+y
+z
+x
-x
-y
+y
+x
+x
+x+y

+y
+z
+x
+z
+x
+y
+z
+z
+z
+z
+y
-y
-x+y+z

+z
+x
+y
-y
-z
-x
-y
+y
-x
+x
+z
-z
+x+y-z

Parameters
• gp_pln (gp_Pln) – an OCCT plane object
• origin (tuple[float, float, float] | Vector) – the origin in global coordinates
• x_dir (tuple[float, float, float] | Vector | None) – an optional vector representing the X Direction. Defaults to None.
• y_dir (tuple[float, float, float] | Vector | None) – optional Y direction.
Mutually exclusive with z_dir. Requires x_dir.
• z_dir (tuple[float, float, float] | Vector | None) – the normal direction for
the plane. Defaults to (0, 0, 1).
Variables
• origin (Vector) – global position of local (0,0,0) point
• x_dir (Vector) – x direction
• y_dir (Vector) – y direction
• z_dir (Vector) – z direction
• forward_transform (Matrix) – forward location transformation matrix
• reverse_transform (Matrix) – reverse location transformation matrix
• wrapped (gp_Pln) – the OCP plane object
Raises
• ValueError – z_dir must be non null
• ValueError – y_dir must be non null
• ValueError – x_dir must be non null
• ValueError – the specified x_dir is not orthogonal to the provided normal
• ValueError – x_dir and y_dir must not be parallel
• ValueError – the specified x_dir is not orthogonal to the provided normal
Returns
A plane

1.22. Direct API Reference



Return type
Plane
__copy__() → Plane
Return copy of self
__deepcopy__(_memo) → Plane
Return deepcopy of self
__eq__(other: object)
Are planes equal operator ==
__mul__(other: Location | Plane | Iterable[Location | Plane]) → Location | list[Location]
__neg__() → Plane
Reverse z direction of plane operator build123d_type:

ClassVar[str] = 'Plane'

contains(obj: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float] | Axis, tolerance: float =
1e-06) → bool
Is this point or Axis fully contained in this plane?
Parameters
• obj (VectorLike | Axis) – point or Axis to evaluate
• tolerance (float, optional) – comparison tolerance. Defaults to TOLERANCE.
Returns
self contains point or Axis
Return type
bool
property forward_transform
forward location transformation matrix
from_local_coords(obj: tuple | Vector | Any | BoundBox)
Reposition the object relative from this plane
Parameters
• obj – VectorLike | Shape | BoundBox an object to reposition. Note that
• classes. (type Any refers to all topological)
Returns
an object of the same type, but repositioned to world coordinates
static get_topods_face_normal(face: TopoDS_Face) → Vector
Find the normal at the center of a TopoDS_Face
intersect(*args, **kwargs)
Find intersection of plane and geometric object or shape
property location: Location
Return Location representing the origin and z direction
location_between(other: Plane) → Location
Return a location representing the translation from self to other




move(loc: Location | Plane) → Plane
Change the position & orientation of self by applying a relative location
Parameters
loc (Location | Plane) – relative change
Returns
relocated self
Return type
Plane
moved(loc: Location | Plane) → Plane
Change the position & orientation of a copy of self by applying a relative location
Parameters
loc (Location | Plane) – relative change
Returns
relocated plane
Return type
Plane
offset(amount: float) → Plane
Move the Plane by amount in the direction of z_dir
property origin: Vector
global position of local (0,0,0) point
reverse() → Plane
Reverse z direction of plane
property reverse_transform
reverse location transformation matrix
rotated(rotation: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float] = (0, 0, 0), ordering:
Extrinsic | Intrinsic | None = None) → Plane
Returns a copy of this plane, rotated about the specified axes
The origin of the workplane is unaffected by the rotation.
Rotations are done in order x, y, z. If you need a different order, specify ordering. e.g. Intrinsic.ZYX
changes rotation to (z angle, y angle, x angle) and rotates in that order.
Parameters
• rotation (VectorLike, optional) – (x angle, y angle, z angle). Defaults to (0, 0, 0)
• ordering (Intrinsic | Extrinsic, optional) – order of rotations in Intrinsic or
Extrinsic rotation mode. Defaults to Intrinsic.XYZ
Returns
a copy of this plane rotated as requested.
Return type
Plane
shift_origin(locator: Axis | VectorLike | Vertex) → Plane
shift plane origin
Creates a new plane with the origin moved within the plane to the point of intersection of the axis or at the
given Vertex. The plane’s x_dir and z_dir are unchanged.
1.22. Direct API Reference



Parameters
locator (Axis | VectorLike | Vertex) – Either Axis that intersects the new plane origin or Vertex within Plane.
Raises
• ValueError – Vertex isn’t within plane
• ValueError – Point isn’t within plane
• ValueError – Axis doesn’t intersect plane
Returns
plane with new origin
Return type
Plane
to_gp_ax2() → gp_Ax2
Return gp_Ax2 version of the plane
to_gp_ax3() → gp_Ax3
Return gp_Ax3 version of the plane
to_local_coords(obj: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float] | Any |
BoundBox)
Reposition the object relative to this plane
Parameters
• obj – VectorLike | Shape | BoundBox an object to reposition. Note that
• classes. (type Any refers to all topological)
Returns
an object of the same type, but repositioned to local coordinates
property wrapped:

gp_Pln

The OCP object
property x_dir:

Vector

Local X direction of the plane.
property y_dir:

Vector

Local Y direction of the plane.
property z_dir:

Vector

Local Z direction normal to the plane.
class Rotation(*args, **kwargs)
Subclass of Location used only for object rotation
Variables
• X (float) – rotation in degrees about X axis
• Y (float) – rotation in degrees about Y axis
• Z (float) – rotation in degrees about Z axis
• enums,
(optionally specify rotation ordering with Intrinsic or
Extrinsic) – defaults to Intrinsic.XYZ




class Vector(*args, **kwargs)
Create a 3-dimensional vector
Parameters
• x (float) – x component
• y (float) – y component
• z (float) – z component
• vec (Vector | Sequence(float) | gp_Vec | gp_Pnt | gp_Dir | gp_XYZ)
vector representations

–

Note that if no z value is provided it’s assumed to be zero. If no values are provided the returned Vector has the
value of 0, 0, 0.
Variables
wrapped (gp_Vec) – the OCP vector object
property X: float
Get x value
property Y: float
Get y value
property Z: float
Get z value
__abs__() → float
Vector length operator abs()
__add__(vec: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]) → Vector
Mathematical addition operator +
__copy__() → Vector
Return copy of self
__deepcopy__(_memo) → Vector
Return deepcopy of self
__eq__(other: object) → bool
Vectors equal operator ==
__mul__(scale: float) → Vector
Mathematical multiply operator *
__neg__() → Vector
Flip direction of vector operator __rmul__(scale: float) → Vector
Mathematical multiply operator *
__sub__(vec: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]) → Vector
Mathematical subtraction operator __truediv__(denom: float) → Vector
Mathematical division operator /
add(vec: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]) → Vector
Mathematical addition function

1.22. Direct API Reference



build123d_type:

ClassVar[str] = 'Vector'

center() → Vector
Returns
The center of myself is myself. Provided so that vectors, vertices, and other shapes all support
a common interface, when center() is requested for all objects on the stack.
cross(vec: Vector) → Vector
Mathematical cross function
distance_to_plane(plane: Plane) → float
Minimum unsigned distance between vector and plane
dot(vec: Vector) → float
Mathematical dot function
get_angle(vec: Vector) → float
Unsigned angle between vectors
get_signed_angle(vec: Vector, normal: Vector | None = None) → float
Signed Angle Between Vectors
Return the signed angle in degrees between two vectors with the given normal based on this math: angle =
atan2((Va × Vb) Vn, Va Vb)
Parameters
• v (Vector) – Second Vector
• normal (Vector, optional) – normal direction. Defaults to None.
Returns
Angle between vectors
Return type
float
intersect(*args, **kwargs)
Find intersection of vector and geometric object or shape
property length:

float

Vector length
multiply(scale: float) → Vector
Mathematical multiply function
normalized() → Vector
Scale to length of 1
project_to_line(line: Vector) → Vector
Returns a new vector equal to the projection of this Vector onto the line represented by Vector <line>
Parameters
line (Vector) – project to this line
Returns
Returns the projected vector.
Return type
Vector




project_to_plane(plane: Plane) → Vector
Vector is projected onto the plane provided as input.
Parameters
args – Plane object
Returns the projected vector.
plane: Plane:
Returns:
reverse() → Vector
Return a vector with the same magnitude but pointing in the opposite direction
rotate(axis: Axis, angle: float) → Vector
Rotate about axis
Rotate about the given Axis by an angle in degrees
Parameters
• axis (Axis) – Axis of rotation
• angle (float) – angle in degrees
Returns
rotated vector
Return type
Vector
signed_distance_from_plane(plane: Plane) → float
Signed distance from plane to point vector.
sub(vec: Vector | tuple[float, float] | tuple[float, float, float] | Sequence[float]) → Vector
Mathematical subtraction function
to_dir() → gp_Dir
Convert to OCCT gp_Dir object
to_pnt() → gp_Pnt
Convert to OCCT gp_Pnt object
transform(affine_transform: Matrix, is_direction: bool = False) → Vector
Apply affine transformation
Parameters
• affine_transform (Matrix) – affine transformation matrix
• is_direction (bool, optional) – Should self be transformed as a vector or direction?
Defaults to False (vector)
Returns
transformed vector
Return type
Vector
property wrapped:

gp_Vec

OCCT object

1.22. Direct API Reference

