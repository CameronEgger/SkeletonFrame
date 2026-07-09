"""A ``tkinter.PhotoImage``-backed :class:`~transforms.protocol.Image`.

Standard-library only. Transforms map onto Tk's native photo operations:

* ``scale`` -> ``zoom`` (integer magnify) and/or ``subsample`` (integer shrink),
* ``crop`` -> the photo ``copy -from`` subcommand.

Tk's ``PhotoImage`` has no rotation or mirroring, so ``rotate`` and ``flip``
raise :class:`NotImplementedError` — the viewer simply doesn't offer them.

Constructing any image needs a live ``Tk`` root (Tk's default image store), so
use this backend from inside a running GUI.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from ..protocol import Box, Size


@dataclass(frozen=True)
class TkImage:
    """Adapter binding a ``tkinter.PhotoImage`` to the transforms protocol."""

    photo: tk.PhotoImage

    @property
    def size(self) -> Size:
        return (self.photo.width(), self.photo.height())

    def scale(self, factor_x: float, factor_y: float) -> "TkImage":
        photo = self.photo
        zx, zy = max(1, round(factor_x)), max(1, round(factor_y))
        if zx > 1 or zy > 1:
            photo = photo.zoom(zx, zy)
        sx = max(1, round(1 / factor_x)) if 0 < factor_x < 1 else 1
        sy = max(1, round(1 / factor_y)) if 0 < factor_y < 1 else 1
        if sx > 1 or sy > 1:
            photo = photo.subsample(sx, sy)
        return TkImage(photo)

    def crop(self, box: Box) -> "TkImage":
        left, top, right, bottom = box
        dest = tk.PhotoImage(width=right - left, height=bottom - top)
        dest.tk.call(
            dest.name, "copy", self.photo.name,
            "-from", left, top, right, bottom, "-to", 0, 0,
        )
        return TkImage(dest)

    def rotate(self, degrees: float) -> "TkImage":
        raise NotImplementedError("PhotoImage backend cannot rotate")

    def flip(self, horizontal: bool = False, vertical: bool = False) -> "TkImage":
        raise NotImplementedError("PhotoImage backend cannot flip")

    def copy(self) -> "TkImage":
        return TkImage(self.photo.copy())

    def blank(self, width: int, height: int) -> "TkImage":
        # A fresh PhotoImage is fully transparent.
        return TkImage(tk.PhotoImage(width=width, height=height))

    def paste(self, other: "TkImage", x: int, y: int) -> "TkImage":
        dest = self.photo.copy()
        # Tk's default compositing rule ("overlay") respects source transparency.
        dest.tk.call(dest.name, "copy", other.photo.name, "-to", int(x), int(y))
        return TkImage(dest)

    # --- constructors -------------------------------------------------
    @classmethod
    def open(cls, path: str) -> "TkImage":
        """Load a PNG/GIF file (formats Tk's PhotoImage supports natively)."""
        return cls(tk.PhotoImage(file=path))

    @classmethod
    def solid(cls, width: int, height: int, color: tuple[int, int, int]) -> "TkImage":
        """A ``width`` x ``height`` block of a single RGB colour."""
        photo = tk.PhotoImage(width=width, height=height)
        photo.put("#%02x%02x%02x" % color, to=(0, 0, width, height))
        return cls(photo)