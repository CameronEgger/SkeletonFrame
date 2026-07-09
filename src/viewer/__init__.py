"""viewer — GUI visualization of a skeleton (Tkinter, standard library only).

Pure visualization: the viewer holds no placement or imaging logic. The skeleton
owns composing and transforming (:meth:`skeleton.Skeleton.compose`); the viewer
just displays the result.

Two views:

* **composed** — show ``skeleton.compose()`` and record per-part transforms live
  (:func:`show_composed`).
* **relationship graph** — parts as nodes, connections as edges, coloured by
  connected component (:func:`show`).
"""

from .layout import spring_layout

__all__ = ["show", "SkeletonGraph", "show_composed", "spring_layout"]


def __getattr__(name: str):
    # Import the Tkinter-backed views lazily so `spring_layout` stays headless.
    if name in ("show", "SkeletonGraph"):
        from . import graph

        return getattr(graph, name)
    if name == "show_composed":
        from .compose import show_composed

        return show_composed
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
