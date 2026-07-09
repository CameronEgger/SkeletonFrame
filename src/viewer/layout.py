"""Force-directed graph layout — pure Python, no GUI dependency.

Positions the parts of a relationship graph for display using a small
Fruchterman-Reingold spring model: every node repels every other, connected
nodes attract, and a mild pull toward the centre keeps disconnected components
in frame. Deterministic for a given ``seed`` so a skeleton always draws the
same way.
"""

from __future__ import annotations

import math
import random

Pos = tuple[float, float]


def _edges(adjacency: dict[str, set[str]]) -> list[tuple[str, str]]:
    seen: set[frozenset[str]] = set()
    edges: list[tuple[str, str]] = []
    for node, nbrs in adjacency.items():
        for other in nbrs:
            key = frozenset((node, other))
            if len(key) == 2 and key not in seen:
                seen.add(key)
                edges.append((node, other))
    return edges


def spring_layout(
    adjacency: dict[str, set[str]],
    width: float = 800.0,
    height: float = 600.0,
    *,
    iterations: int = 300,
    seed: int = 0,
    padding: float = 40.0,
) -> dict[str, Pos]:
    """Lay out ``adjacency`` nodes within ``width`` x ``height``.

    Returns ``{node: (x, y)}`` with every node kept inside the padded frame.
    """
    nodes = list(adjacency)
    if not nodes:
        return {}
    if len(nodes) == 1:
        return {nodes[0]: (width / 2, height / 2)}

    rng = random.Random(seed)
    pos: dict[str, list[float]] = {
        n: [rng.uniform(padding, width - padding), rng.uniform(padding, height - padding)]
        for n in nodes
    }
    edges = _edges(adjacency)
    center = (width / 2, height / 2)

    area = (width - 2 * padding) * (height - 2 * padding)
    k = math.sqrt(area / len(nodes))  # ideal edge length
    temp = (width + height) / 20.0  # max displacement per step, cools over time
    cooling = temp / (iterations + 1)

    for _ in range(iterations):
        disp: dict[str, list[float]] = {n: [0.0, 0.0] for n in nodes}

        # Repulsion between every pair.
        for i, u in enumerate(nodes):
            for v in nodes[i + 1 :]:
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = math.hypot(dx, dy) or 0.01
                force = (k * k) / dist
                ux, uy = dx / dist * force, dy / dist * force
                disp[u][0] += ux
                disp[u][1] += uy
                disp[v][0] -= ux
                disp[v][1] -= uy

        # Attraction along edges.
        for u, v in edges:
            dx = pos[u][0] - pos[v][0]
            dy = pos[u][1] - pos[v][1]
            dist = math.hypot(dx, dy) or 0.01
            force = (dist * dist) / k
            ux, uy = dx / dist * force, dy / dist * force
            disp[u][0] -= ux
            disp[u][1] -= uy
            disp[v][0] += ux
            disp[v][1] += uy

        # Mild gravity toward the centre so lone components stay on screen.
        for n in nodes:
            disp[n][0] += (center[0] - pos[n][0]) * 0.01
            disp[n][1] += (center[1] - pos[n][1]) * 0.01

        # Apply, capped by temperature, and clamp inside the frame.
        for n in nodes:
            dx, dy = disp[n]
            dist = math.hypot(dx, dy) or 0.01
            step = min(dist, temp)
            pos[n][0] = min(width - padding, max(padding, pos[n][0] + dx / dist * step))
            pos[n][1] = min(height - padding, max(padding, pos[n][1] + dy / dist * step))

        temp = max(temp - cooling, 0.0)

    return {n: (xy[0], xy[1]) for n, xy in pos.items()}