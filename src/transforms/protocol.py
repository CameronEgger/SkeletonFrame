"""The ``Image`` protocol every backend adapts to.

Transform functions are written against this interface, so any concrete image
type (a ``pygame.Surface``, a ``PIL.Image``, a NumPy array, …) can be driven by
the same code as long as a thin adapter provides these primitives. Every
operation returns a *new* image rather than mutating in place.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

# (width, height)
Size = tuple[int, int]
# (left, top, right, bottom)
Box = tuple[int, int, int, int]


@runtime_checkable
class Image(Protocol):
    """The minimal set of primitives a backend must provide.

    Higher-level operations in :mod:`transforms.operations` are composed purely
    from these; a backend only implements this handful of atoms.
    """

    @property
    def size(self) -> Size:
        """``(width, height)`` in pixels."""
        ...

    def rotate(self, degrees: float) -> "Image":
        """Rotate counter-clockwise by ``degrees`` about the image centre."""
        ...

    def scale(self, factor_x: float, factor_y: float) -> "Image":
        """Scale width by ``factor_x`` and height by ``factor_y``."""
        ...

    def crop(self, box: Box) -> "Image":
        """Cut out the ``(left, top, right, bottom)`` region."""
        ...

    def flip(self, horizontal: bool = False, vertical: bool = False) -> "Image":
        """Mirror across the given axes."""
        ...

    def blank(self, width: int, height: int) -> "Image":
        """A new, fully transparent image of the same backend and given size.

        A sibling factory (like ``numpy.empty_like``): used to build a canvas to
        composite onto, without the caller needing to know the concrete type.
        """
        ...

    def paste(self, other: "Image", x: int, y: int) -> "Image":
        """Overlay ``other`` onto a copy of this image at ``(x, y)``; return it."""
        ...