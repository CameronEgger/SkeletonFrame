"""One image and the named points defined on it."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .point import Coords, Point


@dataclass
class Part:
    """One image and the named points defined on it.

    ``image`` is opaque: a ``pygame.Surface``, a file path, an ``ndarray``, an
    id, ``None`` — whatever. The skeleton stores it and never inspects it.
    """

    name: str
    image: Any = None
    points: dict[str, Point] = field(default_factory=dict)
    data: Any = None

    def add_point(self, name: str, coords: Coords = (), data: Any = None) -> Point:
        """Define (or replace) a named point on this part and return it."""
        point = Point(name, coords, data)
        self.points[name] = point
        return point

    def point(self, name: str) -> Point:
        return self.points[name]

    def has_point(self, name: str) -> bool:
        return name in self.points

    def copy(self) -> "Part":
        return Part(
            self.name,
            self.image,
            {n: p.copy() for n, p in self.points.items()},
            self.data,
        )