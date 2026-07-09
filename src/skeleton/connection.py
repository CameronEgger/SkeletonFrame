"""An explicit, undirected link between a point on two different parts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Connection:
    """An explicit, undirected link between a point on two different parts.

    Declares that ``point_a`` on ``part_a`` corresponds to ``point_b`` on
    ``part_b`` (e.g. they should coincide when the images are assembled).
    ``label`` is an optional tag for the relationship.
    """

    part_a: str
    point_a: str
    part_b: str
    point_b: str
    label: str | None = None

    @property
    def parts(self) -> tuple[str, str]:
        return (self.part_a, self.part_b)

    def involves(self, part: str) -> bool:
        return part in (self.part_a, self.part_b)

    def endpoints(self) -> tuple[tuple[str, str], tuple[str, str]]:
        """``((part_a, point_a), (part_b, point_b))``."""
        return ((self.part_a, self.point_a), (self.part_b, self.point_b))

    def other(self, part: str) -> tuple[str, str]:
        """The ``(part, point)`` on the far side of ``part``."""
        if part == self.part_a:
            return (self.part_b, self.point_b)
        if part == self.part_b:
            return (self.part_a, self.point_a)
        raise ValueError(f"connection does not involve part {part!r}")