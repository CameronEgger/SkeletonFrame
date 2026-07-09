"""Tkinter viewer for the composed skeleton.

Pure visualization: it holds no placement or joint logic of its own. It asks the
skeleton to :meth:`~skeleton.Skeleton.compose` a single image and displays it,
and its buttons just record transforms on the skeleton (``skeleton.transform``)
or reset them — the skeleton owns all the imaging behaviour.
"""

from __future__ import annotations

import tkinter as tk

from skeleton import Skeleton
from skeleton.transform import crop, scale

_BG = "#1e1e24"
_CROP_MARGIN = 0.15


class ComposedView:
    """Displays ``skeleton.compose()`` and drives per-part transforms."""

    def __init__(self, root: tk.Misc, skeleton: Skeleton) -> None:
        self.skeleton = skeleton
        self._photo: tk.PhotoImage | None = None  # keep a live reference

        self.canvas = tk.Canvas(root, width=520, height=520, bg=_BG, highlightthickness=0)
        self.canvas.pack(side="top", fill="both", expand=True)

        controls = tk.Frame(root)
        controls.pack(side="bottom", fill="x")
        self.selected = tk.StringVar(value=next(iter(skeleton.parts)))
        tk.Label(controls, text="part:").pack(side="left")
        tk.OptionMenu(controls, self.selected, *skeleton.parts).pack(side="left")
        for text, cmd in [
            ("Zoom 2x", lambda: self._transform(scale(2))),
            ("Shrink 1/2", lambda: self._transform(scale(0.5))),
            ("Crop", self._crop),
            ("Reset part", lambda: self._reset(self.selected.get())),
            ("Reset all", lambda: self._reset(None)),
        ]:
            tk.Button(controls, text=text, command=cmd).pack(side="left", padx=2, pady=4)

        self.status = tk.Label(root, anchor="w")
        self.status.pack(side="bottom", fill="x")
        self.refresh()

    # --- actions: record on the skeleton, then re-render ---------------
    def _transform(self, part_transform) -> None:
        self.skeleton.transform(self.selected.get(), part_transform)
        self.refresh()

    def _crop(self) -> None:
        w, h = self.skeleton.transformed_size(self.selected.get())
        mx, my = int(w * _CROP_MARGIN), int(h * _CROP_MARGIN)
        self._transform(crop((mx, my, w - mx, h - my)))

    def _reset(self, part: str | None) -> None:
        self.skeleton.reset(part)
        self.refresh()

    def refresh(self) -> None:
        composed = self.skeleton.compose()
        self._photo = composed.photo
        self.canvas.delete("all")
        self.canvas.create_image(10, 10, image=self._photo, anchor="nw")
        sel = self.selected.get()
        self.status.config(text=f"selected: {sel} {self.skeleton.transformed_size(sel)}")


def show_composed(skeleton: Skeleton, build_images, *, title: str = "skeleton — composed") -> None:
    """Open the composed viewer.

    ``build_images(skeleton)`` is called *after* the Tk root exists (PhotoImages
    need a live root) and returns ``{part_name: image}``, which are attached to
    the skeleton before rendering.
    """
    root = tk.Tk()
    root.title(title)
    for name, image in build_images(skeleton).items():
        skeleton.set_image(name, image)
    ComposedView(root, skeleton)
    root.mainloop()