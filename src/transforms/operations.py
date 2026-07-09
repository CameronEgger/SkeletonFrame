"""Backend-agnostic image transformations.

Every function takes an :class:`~transforms.protocol.Image` first and returns a
new one, using only the protocol primitives — so they work against any backend.
The tuning arguments are keyword-only, which keeps direct calls self-describing
(``rotate(img, degrees=90)``) and lets them be pre-bound with
``functools.partial(rotate, degrees=90)`` for a
:class:`~transforms.compose.Transform` pipeline — the free ``image`` argument
stays first.
"""

from __future__ import annotations

from .protocol import Box, Image


def rotate(image: Image, *, degrees: float) -> Image:
    """Rotate counter-clockwise by ``degrees``."""
    return image.rotate(degrees)


def flip_horizontal(image: Image) -> Image:
    return image.flip(horizontal=True)


def flip_vertical(image: Image) -> Image:
    return image.flip(vertical=True)


def scale(image: Image, *, factor: float) -> Image:
    """Uniformly scale both axes by ``factor``."""
    return image.scale(factor, factor)


def scale_xy(image: Image, *, factor_x: float, factor_y: float) -> Image:
    """Scale each axis independently."""
    return image.scale(factor_x, factor_y)


def resize(image: Image, *, width: int, height: int) -> Image:
    """Scale to an exact ``width`` x ``height`` (aspect ratio not preserved)."""
    if width <= 0 or height <= 0:
        raise ValueError("target size must be positive")
    w, h = image.size
    return image.scale(width / w, height / h)


def fit_within(image: Image, *, max_width: int, max_height: int) -> Image:
    """Scale down/up uniformly to fit inside a box, preserving aspect ratio."""
    if max_width <= 0 or max_height <= 0:
        raise ValueError("bounding box must be positive")
    w, h = image.size
    factor = min(max_width / w, max_height / h)
    return image.scale(factor, factor)


def crop(image: Image, *, box: Box) -> Image:
    """Cut out the ``(left, top, right, bottom)`` region."""
    return image.crop(box)


def center_crop(image: Image, *, width: int, height: int) -> Image:
    """Crop a ``width`` x ``height`` region from the image centre."""
    w, h = image.size
    if width > w or height > h:
        raise ValueError("crop size larger than image")
    left = (w - width) // 2
    top = (h - height) // 2
    return image.crop((left, top, left + width, top + height))