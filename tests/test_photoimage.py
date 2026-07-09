"""Tests for the PhotoImage transform backend and composed view.

These need a live Tk root; they skip automatically where no display is available.
"""

import tkinter as tk

import pytest

from skeleton.transform import scale
from transforms import Image, operations as ops


@pytest.fixture
def root():
    try:
        r = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available")
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def tkimage_cls():
    from transforms.backends.photoimage import TkImage

    return TkImage


def test_tkimage_satisfies_protocol(root, tkimage_cls):
    assert isinstance(tkimage_cls.solid(4, 4, (0, 0, 0)), Image)


def test_solid_size_and_color(root, tkimage_cls):
    img = tkimage_cls.solid(40, 30, (200, 80, 80))
    assert img.size == (40, 30)
    assert img.photo.get(0, 0)[:3] == (200, 80, 80)


def test_scale_zoom_and_subsample(root, tkimage_cls):
    img = tkimage_cls.solid(40, 30, (10, 20, 30))
    assert ops.scale(img, factor=2).size == (80, 60)
    assert ops.scale(img, factor=0.5).size == (20, 15)


def test_crop_and_center_crop(root, tkimage_cls):
    img = tkimage_cls.solid(40, 30, (10, 20, 30))
    assert ops.crop(img, box=(5, 5, 25, 20)).size == (20, 15)
    assert ops.center_crop(img, width=20, height=10).size == (20, 10)


def test_rotate_and_flip_unsupported(root, tkimage_cls):
    img = tkimage_cls.solid(4, 4, (0, 0, 0))
    with pytest.raises(NotImplementedError):
        ops.rotate(img, degrees=90)
    with pytest.raises(NotImplementedError):
        ops.flip_horizontal(img)


def test_blank_and_paste(root, tkimage_cls):
    canvas = tkimage_cls.solid(4, 4, (0, 0, 0)).blank(20, 10)
    assert canvas.size == (20, 10)
    patch = tkimage_cls.solid(6, 6, (200, 50, 50))
    out = canvas.paste(patch, 5, 2)
    assert out.size == (20, 10)  # paste keeps the canvas size
    assert out.photo.get(7, 4)[:3] == (200, 50, 50)  # pasted region present
    assert canvas.photo.get(7, 4)[:3] != (200, 50, 50)  # original untouched


def test_skeleton_compose_returns_one_image(root):
    from viewer.__main__ import build_images, figure_skeleton

    skel = figure_skeleton()
    for name, image in build_images(skel).items():
        skel.set_image(name, image)

    before = skel.compose()
    assert before.size[0] > 0 and before.size[1] > 0

    skel.transform("left_arm", scale(2))
    assert skel.transformed_size("left_arm") == (18 * 2, 70 * 2)
    grown = skel.compose()
    assert grown.size != before.size  # composition reflows around the bigger part

    skel.reset()
    assert skel.compose().size == before.size  # non-destructive revert


def test_composed_view_renders(root):
    from viewer.compose import ComposedView
    from viewer.__main__ import build_images, figure_skeleton

    skel = figure_skeleton()
    for name, image in build_images(skel).items():
        skel.set_image(name, image)
    view = ComposedView(root, skel)
    view.selected.set("left_arm")
    view._transform(scale(2))  # records on the skeleton and re-renders
    assert skel.transformed_size("left_arm") == (18 * 2, 70 * 2)
    view._reset(None)
    assert skel.transformed_size("left_arm") == (18, 70)