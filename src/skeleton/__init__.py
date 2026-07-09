"""skeleton — relate arbitrary images by shared data points, and compose them.

Define each image as a :class:`Part` (an image plus named data points), declare
:class:`Connection`\\ s between the points, and the :class:`Skeleton` derives how
all the images relate. Attach real images with :meth:`Skeleton.set_image`,
record non-destructive per-part transforms with :meth:`Skeleton.transform`
(see :mod:`skeleton.transform`), and :meth:`Skeleton.compose` renders them —
placed so connected points coincide — into a single image. :meth:`Skeleton.reset`
reverts to the original, untransformed images.
"""

from . import transform
from .connection import Connection
from .part import Part
from .placement import initial_coords, solve_offsets
from .point import Coords, Point
from .skeleton import Skeleton
from .transform import PartTransform

__all__ = [
    "Connection",
    "Coords",
    "Part",
    "PartTransform",
    "Point",
    "Skeleton",
    "initial_coords",
    "solve_offsets",
    "transform",
]

__version__ = "0.1.0"