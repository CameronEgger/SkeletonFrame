"""Where each part's image goes so connected points coincide — pure math.

The skeleton records, per part, named points in that part's own image space, and
declares which point on one part meets which point on another. Placing the parts
is then: pick a root per connected component, and translate each neighbour so its
shared point lands on the parent's shared point. This is the "relativeness"
logic that keeps images glued at their joints; :meth:`skeleton.Skeleton.compose`
uses it. GUI-free and unit-testable without a display.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .skeleton import Skeleton

XY = tuple[float, float]
# part name -> point name -> (x, y) in that part's image space.
Coords = dict[str, dict[str, XY]]


def point_xy(coords: tuple[float, ...]) -> XY:
    """First two components of a point's coordinates (missing axes -> 0)."""
    x = coords[0] if len(coords) > 0 else 0.0
    y = coords[1] if len(coords) > 1 else 0.0
    return (x, y)


def initial_coords(skeleton: "Skeleton") -> Coords:
    """Snapshot every part's point coordinates from the model."""
    return {
        part.name: {name: point_xy(pt.coords) for name, pt in part.points.items()}
        for part in skeleton
    }


def _connection_between(skeleton: "Skeleton", a: str, b: str):
    return next(c for c in skeleton.connections if c.involves(a) and c.involves(b))


def _shared_points(conn, a: str, b: str) -> tuple[str, str]:
    """Return ``(point_on_a, point_on_b)`` for a connection linking a and b."""
    if conn.part_a == a:
        return conn.point_a, conn.point_b
    return conn.point_b, conn.point_a


def solve_offsets(
    skeleton: "Skeleton",
    sizes: dict[str, tuple[int, int]],
    coords: Coords | None = None,
    *,
    spacing: int = 20,
) -> dict[str, tuple[int, int]]:
    """Where each part's image top-left goes, as ``{part: (x, y)}``.

    ``sizes`` gives each part's ``(width, height)``; ``coords`` overrides the
    model's point coordinates (e.g. after transforming a part). Connected parts
    are aligned at their shared points; separate components are stacked
    vertically with ``spacing`` between them.
    """
    if coords is None:
        coords = initial_coords(skeleton)
    adj = skeleton.adjacency()

    # Relative placement within each component: walk the connection graph.
    rel: dict[str, XY] = {}
    for component in skeleton.components():
        root = next(iter(component))
        rel[root] = (0.0, 0.0)
        queue = [root]
        seen = {root}
        while queue:
            a = queue.pop(0)
            for b in adj[a]:
                if b in seen:
                    continue
                conn = _connection_between(skeleton, a, b)
                pa, pb = _shared_points(conn, a, b)
                (ax, ay), (bx, by) = coords[a][pa], coords[b][pb]
                rel[b] = (rel[a][0] + ax - bx, rel[a][1] + ay - by)
                seen.add(b)
                queue.append(b)

    # Normalise each component to its own bounding box and stack them.
    offsets: dict[str, tuple[int, int]] = {}
    cursor_y = 0.0
    for component in skeleton.components():
        xs, ys = [], []
        for p in component:
            x, y = rel[p]
            w, h = sizes[p]
            xs += [x, x + w]
            ys += [y, y + h]
        min_x, min_y, max_y = min(xs), min(ys), max(ys)
        for p in component:
            x, y = rel[p]
            offsets[p] = (round(x - min_x), round(y - min_y + cursor_y))
        cursor_y += (max_y - min_y) + spacing
    return offsets