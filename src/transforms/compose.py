"""Compose several transforms into one."""

from __future__ import annotations

from collections.abc import Callable

from .protocol import Image

# A single-argument transform step: image in, image out.
Op = Callable[[Image], Image]


class Transform:
    """An ordered pipeline of transform steps, itself a transform.

    Build one from any callables that map ``Image -> Image`` (use
    ``functools.partial`` to bind an operation's extra arguments), then apply it
    like a function. Pipelines chain with :meth:`then` or the ``|`` operator.

    >>> from functools import partial
    >>> from transforms import operations as ops
    >>> pipe = Transform(partial(ops.fit_within, max_width=100, max_height=100))
    >>> pipe = pipe | partial(ops.rotate, degrees=90)
    """

    def __init__(self, *ops: Op) -> None:
        self._ops: tuple[Op, ...] = ops

    def __call__(self, image: Image) -> Image:
        for op in self._ops:
            image = op(image)
        return image

    def then(self, other: "Transform | Op") -> "Transform":
        """Return a new pipeline that runs ``self`` then ``other``."""
        tail = other._ops if isinstance(other, Transform) else (other,)
        return Transform(*self._ops, *tail)

    def __or__(self, other: "Transform | Op") -> "Transform":
        return self.then(other)


def compose(*ops: Op) -> Transform:
    """Build a :class:`Transform` from ``ops`` applied left to right."""
    return Transform(*ops)