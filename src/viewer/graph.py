"""Render a skeleton's relationship graph on a Tkinter canvas.

Nodes are parts, edges are connections; each connected component gets its own
colour, and isolated images show up as lone nodes. Uses only the skeleton's
derived ``adjacency()`` / ``components()`` — no images or coordinates required,
so it works on any skeleton.
"""

from __future__ import annotations

import tkinter as tk

from skeleton import Skeleton

from .layout import spring_layout

# A small qualitative palette; components cycle through it.
_PALETTE = [
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759",
    "#b07aa1", "#76b7b2", "#edc948", "#ff9da7",
]
_NODE_RADIUS = 26
_BG = "#1e1e24"
_EDGE = "#8a8a99"
_TEXT = "#ffffff"


class SkeletonGraph:
    """Draws a :class:`~skeleton.Skeleton` onto a Tkinter canvas."""

    def __init__(
        self,
        skeleton: Skeleton,
        canvas: tk.Canvas,
        *,
        show_labels: bool = True,
        seed: int = 0,
    ) -> None:
        self.skeleton = skeleton
        self.canvas = canvas
        self.show_labels = show_labels
        self.seed = seed
        canvas.bind("<Configure>", lambda _e: self.draw())

    def _component_colors(self) -> dict[str, str]:
        colors: dict[str, str] = {}
        for i, group in enumerate(self.skeleton.components()):
            for part in group:
                colors[part] = _PALETTE[i % len(_PALETTE)]
        return colors

    def draw(self) -> None:
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), 1)
        h = max(c.winfo_height(), 1)

        pos = spring_layout(self.skeleton.adjacency(), w, h, seed=self.seed)
        colors = self._component_colors()

        # Edges first, so nodes sit on top.
        for conn in self.skeleton.connections:
            x1, y1 = pos[conn.part_a]
            x2, y2 = pos[conn.part_b]
            c.create_line(x1, y1, x2, y2, fill=_EDGE, width=2)
            if self.show_labels:
                label = conn.label or f"{conn.point_a}↔{conn.point_b}"
                c.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2, text=label,
                    fill=_EDGE, font=("TkDefaultFont", 8),
                )

        # Nodes.
        for part, (x, y) in pos.items():
            r = _NODE_RADIUS
            c.create_oval(
                x - r, y - r, x + r, y + r,
                fill=colors.get(part, _PALETTE[0]), outline=_TEXT, width=2,
            )
            c.create_text(x, y, text=part, fill=_TEXT, font=("TkDefaultFont", 9, "bold"))


def show(
    skeleton: Skeleton,
    *,
    title: str = "skeleton",
    width: int = 800,
    height: int = 600,
    show_labels: bool = True,
    seed: int = 0,
) -> None:
    """Open a window showing ``skeleton``'s relationship graph (blocks until closed)."""
    root = tk.Tk()
    root.title(title)
    canvas = tk.Canvas(root, width=width, height=height, bg=_BG, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    SkeletonGraph(skeleton, canvas, show_labels=show_labels, seed=seed)
    root.mainloop()