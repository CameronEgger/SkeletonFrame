"""A set of images (parts) and the declared relationships between them.

A :class:`Skeleton` is a collection of :class:`~skeleton.part.Part`\\ s connected
by explicitly declared :class:`~skeleton.connection.Connection`\\ s. The model
makes no assumptions about *what* the images are, how many there are, what
their points mean, or how they are laid out — it only records each part (an
opaque image plus named points) and each connection (a declaration that one
point on part *A* corresponds to one point on part *B*).

From the parts and connections it derives how the images relate: neighbours,
the full adjacency graph, and the transitively-related groups (connected
components) across *all* images provided. The core is pure Python — no
rendering, no coordinate math, no domain knowledge.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .connection import Connection
from .part import Part
from .placement import point_xy, solve_offsets
from .point import Point

if TYPE_CHECKING:
    from transforms.protocol import Image

    from .placement import Coords
    from .transform import PartTransform


@dataclass
class Skeleton:
    """A set of images (parts) and the declared relationships between them."""

    parts: dict[str, Part] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    # Recorded, non-destructive transforms per part (applied at compose time).
    _transforms: dict[str, list["PartTransform"]] = field(
        default_factory=dict, repr=False, compare=False
    )

    # --- construction -------------------------------------------------
    def add_part(
        self,
        name: str,
        image: Any = None,
        points: dict[str, Point] | Iterable[Point] | None = None,
        data: Any = None,
    ) -> Part:
        """Add a part (image). Raises if a part of that name already exists."""
        if name in self.parts:
            raise ValueError(f"part {name!r} already exists")
        if points is None:
            pts: dict[str, Point] = {}
        elif isinstance(points, dict):
            pts = dict(points)
        else:
            pts = {p.name: p for p in points}
        part = Part(name, image, pts, data)
        self.parts[name] = part
        return part

    def connect(
        self,
        part_a: str,
        point_a: str,
        part_b: str,
        point_b: str,
        *,
        label: str | None = None,
    ) -> Connection:
        """Declare that ``point_a`` on ``part_a`` links to ``point_b`` on ``part_b``.

        Both parts and both named points must already exist, and a part cannot
        connect to itself.
        """
        if part_a == part_b:
            raise ValueError(f"cannot connect part {part_a!r} to itself")
        self._require_point(part_a, point_a)
        self._require_point(part_b, point_b)
        conn = Connection(part_a, point_a, part_b, point_b, label)
        self.connections.append(conn)
        return conn

    def _require_point(self, part: str, point: str) -> None:
        if part not in self.parts:
            raise KeyError(f"no such part {part!r}")
        if point not in self.parts[part].points:
            raise KeyError(f"part {part!r} has no point {point!r}")

    # --- lookup -------------------------------------------------------
    def part(self, name: str) -> Part:
        return self.parts[name]

    def point(self, part: str, point: str) -> Point:
        return self.parts[part].points[point]

    def __iter__(self) -> Iterator[Part]:
        return iter(self.parts.values())

    def __len__(self) -> int:
        return len(self.parts)

    def __contains__(self, part: str) -> bool:
        return part in self.parts

    # --- relationships (derived from all parts + connections) ---------
    def connections_of(self, part: str) -> list[Connection]:
        """Every connection that touches ``part``."""
        return [c for c in self.connections if c.involves(part)]

    def neighbors(self, part: str) -> set[str]:
        """Parts directly connected to ``part``."""
        if part not in self.parts:
            raise KeyError(f"no such part {part!r}")
        return {c.other(part)[0] for c in self.connections_of(part)}

    def adjacency(self) -> dict[str, set[str]]:
        """The full relationship graph over every image provided.

        Keys cover *all* parts; unconnected parts map to an empty set.
        """
        adj: dict[str, set[str]] = {name: set() for name in self.parts}
        for c in self.connections:
            adj[c.part_a].add(c.part_b)
            adj[c.part_b].add(c.part_a)
        return adj

    def components(self) -> list[set[str]]:
        """Groups of parts that are transitively related, across all images.

        A lone image with no connections is its own single-part component.
        """
        adj = self.adjacency()
        seen: set[str] = set()
        groups: list[set[str]] = []
        for start in self.parts:
            if start in seen:
                continue
            group: set[str] = set()
            stack = [start]
            while stack:
                node = stack.pop()
                if node in group:
                    continue
                group.add(node)
                stack.extend(adj[node] - group)
            seen |= group
            groups.append(group)
        return groups

    def related(self, part: str) -> set[str]:
        """Every part transitively related to ``part`` (excluding itself)."""
        if part not in self.parts:
            raise KeyError(f"no such part {part!r}")
        for group in self.components():
            if part in group:
                return group - {part}
        return set()  # unreachable: every part is in some component

    def is_connected(self) -> bool:
        """True if all images form a single related group."""
        return len(self.parts) > 0 and len(self.components()) == 1

    # --- imaging: attach images, transform, compose (all non-destructive) ---
    def set_image(self, part: str, image: "Image") -> None:
        """Attach ``part``'s original image. Transforms never mutate it."""
        if part not in self.parts:
            raise KeyError(f"no such part {part!r}")
        self.parts[part].image = image

    def transform(self, part: str, transform: "PartTransform") -> None:
        """Record a transform for ``part``, layered over any earlier ones.

        Non-destructive: the original image and points are untouched. The
        transform is applied only when composing, and undone by :meth:`reset`.
        """
        if part not in self.parts:
            raise KeyError(f"no such part {part!r}")
        self._transforms.setdefault(part, []).append(transform)

    def reset(self, part: str | None = None) -> None:
        """Drop recorded transforms — for one part, or all — back to originals."""
        if part is None:
            self._transforms.clear()
        else:
            self._transforms.pop(part, None)

    def transformed_size(self, part: str) -> tuple[int, int]:
        """Size of ``part``'s image after its recorded transforms."""
        return self._transformed(part)[0].size

    def _transformed(self, part: str) -> "tuple[Image, dict[str, tuple[float, float]]]":
        """A part's image and points with its transform stack applied to both."""
        p = self.parts[part]
        image = p.image
        coords = {n: point_xy(pt.coords) for n, pt in p.points.items()}
        for t in self._transforms.get(part, ()):
            image = t.image(image)
            coords = {n: t.point(xy) for n, xy in coords.items()}
        return image, coords

    def compose(self) -> "Image":
        """Render every part's image, placed by its joints, into one image.

        Applies each part's recorded transforms (to image *and* points, so the
        joints stay aligned), positions the parts so connected points coincide,
        and flattens them onto one canvas. Non-destructive — call it freely.
        """
        missing = [n for n, p in self.parts.items() if p.image is None]
        if missing:
            raise ValueError(f"parts have no image: {missing}")

        images: dict[str, Image] = {}
        coords: "Coords" = {}
        for name in self.parts:
            images[name], coords[name] = self._transformed(name)

        sizes = {n: img.size for n, img in images.items()}
        offsets = solve_offsets(self, sizes, coords)
        width = max((offsets[n][0] + sizes[n][0] for n in sizes), default=1)
        height = max((offsets[n][1] + sizes[n][1] for n in sizes), default=1)

        canvas = next(iter(images.values())).blank(max(1, width), max(1, height))
        for name, img in images.items():
            x, y = offsets[name]
            canvas = canvas.paste(img, x, y)
        return canvas

    def copy(self) -> "Skeleton":
        """Deep copy of parts; connections are immutable and shared."""
        return Skeleton(
            {n: p.copy() for n, p in self.parts.items()},
            list(self.connections),
        )