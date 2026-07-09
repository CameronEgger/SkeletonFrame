"""Part transforms — an image transform paired with its effect on points.

A :class:`PartTransform` bundles two things that must move together to keep a
skeleton's joints aligned: how a part's *image* changes, and how that same
geometry moves the part's *points*. The image side delegates to
:mod:`transforms.operations`; the point side is the matching coordinate map.

    from skeleton.transform import scale, crop
    skeleton.transform("left_arm", scale(2))

Only the operations the image backends actually support are provided (Tk's
``PhotoImage`` backend can scale and crop, but not rotate or flip).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from transforms import operations as ops
from transforms.protocol import Box, Image

XY = tuple[float, float]


@dataclass(frozen=True)
class PartTransform:
    """An image transform and the matching point transform, applied together."""

    image: Callable[[Image], Image]
    point: Callable[[XY], XY]
    name: str = ""

    def __repr__(self) -> str:
        return f"PartTransform({self.name!r})"


def scale(factor: float) -> PartTransform:
    """Scale a part's image and its points uniformly by ``factor``."""
    return PartTransform(
        image=lambda im: ops.scale(im, factor=factor),
        point=lambda p: (p[0] * factor, p[1] * factor),
        name=f"scale x{factor}",
    )


def crop(box: Box) -> PartTransform:
    """Crop a part's image to ``(left, top, right, bottom)`` and shift its points."""
    left, top, _right, _bottom = box
    return PartTransform(
        image=lambda im: ops.crop(im, box=box),
        point=lambda p: (p[0] - left, p[1] - top),
        name=f"crop{tuple(box)}",
    )
