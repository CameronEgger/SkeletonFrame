"""Demos:

    uv run python -m viewer            # composed view (default)
    uv run python -m viewer compose
    uv run python -m viewer graph      # relationship graph

The composed demo builds a little figure from solid-colour part images whose
connection points are defined in each image's own pixel space, then lets you
transform any part and watch the composition update.
"""

from __future__ import annotations

import argparse

from skeleton import Point, Skeleton

# (width, height, color) and local point coords per part.
_PARTS = {
    "head": (50, 50, (0xE1, 0x57, 0x59), {"neck": (25, 48)}),
    "torso": (60, 120, (0x4E, 0x79, 0xA7), {
        "neck": (30, 5), "l_shoulder": (5, 20), "r_shoulder": (55, 20), "hip": (30, 115),
    }),
    "left_arm": (18, 70, (0x59, 0xA1, 0x4F), {"shoulder": (9, 5)}),
    "right_arm": (18, 70, (0x59, 0xA1, 0x4F), {"shoulder": (9, 5)}),
    "legs": (60, 90, (0xF2, 0x8E, 0x2B), {"hip": (30, 5)}),
}
_CONNECTIONS = [
    ("head", "neck", "torso", "neck", "spine"),
    ("torso", "l_shoulder", "left_arm", "shoulder", None),
    ("torso", "r_shoulder", "right_arm", "shoulder", None),
    ("torso", "hip", "legs", "hip", None),
]


def figure_skeleton() -> Skeleton:
    s = Skeleton()
    for name, (_w, _h, _c, points) in _PARTS.items():
        s.add_part(name, points=[Point(p, xy) for p, xy in points.items()])
    for a, pa, b, pb, label in _CONNECTIONS:
        s.connect(a, pa, b, pb, label=label)
    return s


def build_images(skeleton):
    # Imported here so `graph` mode needs no GUI backend.
    from transforms.backends.photoimage import TkImage

    return {
        name: TkImage.solid(w, h, color)
        for name, (w, h, color, _points) in _PARTS.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="viewer")
    parser.add_argument("mode", nargs="?", default="compose", choices=["compose", "graph"])
    mode = parser.parse_args().mode

    skeleton = figure_skeleton()
    if mode == "graph":
        from . import show

        show(skeleton, title="skeleton — relationship graph")
    else:
        from .compose import show_composed

        show_composed(skeleton, build_images)


if __name__ == "__main__":
    main()