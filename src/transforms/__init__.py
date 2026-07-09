"""transforms — backend-agnostic image transformation methods.

Transforms are written against the :class:`Image` protocol (see
:mod:`transforms.protocol`), so any backend — ``pygame.Surface``, ``PIL.Image``,
NumPy arrays — works once a thin adapter provides the protocol's primitives.
Individual operations live in :mod:`transforms.operations`; chain them with a
:class:`Transform`.
"""

from . import operations
from .compose import Op, Transform, compose
from .protocol import Box, Image, Size

__all__ = [
    "operations",
    "Op",
    "Transform",
    "compose",
    "Box",
    "Image",
    "Size",
]