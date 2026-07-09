"""A named data point on a part."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

Coords = tuple[float, ...]


@dataclass
class Point:
    """A named data point on a part.

    ``coords`` is a tuple of floats of arbitrary dimension (2-D, 3-D, …); it is
    the shared anchor a :class:`~skeleton.connection.Connection` refers to.
    ``data`` carries any extra payload you want to attach and is never
    interpreted here.
    """

    name: str
    coords: Coords = ()
    data: Any = None

    def __post_init__(self) -> None:
        self.coords = tuple(float(c) for c in self.coords)

    @property
    def dim(self) -> int:
        return len(self.coords)

    def copy(self) -> "Point":
        return Point(self.name, self.coords, self.data)