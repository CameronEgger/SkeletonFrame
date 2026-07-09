"""Tests for Skeleton compose / transform / reset — headless via a fake backend.

A tiny in-memory Image records the compose sequence (blank canvas + pastes), so
we can assert placement, non-destructiveness, and reset without a display.
"""

from dataclasses import dataclass, field

import pytest

from skeleton import Point, Skeleton
from skeleton.transform import crop, scale


@dataclass(frozen=True)
class FakeImg:
    w: int
    h: int
    pastes: tuple = field(default_factory=tuple)  # (name-less) (x, y) records

    @property
    def size(self):
        return (self.w, self.h)

    def scale(self, factor_x, factor_y):
        return FakeImg(max(1, round(self.w * factor_x)), max(1, round(self.h * factor_y)))

    def crop(self, box):
        left, top, right, bottom = box
        return FakeImg(right - left, bottom - top)

    def blank(self, width, height):
        return FakeImg(width, height)

    def paste(self, other, x, y):
        return FakeImg(self.w, self.h, self.pastes + ((x, y, other.size),))


def _skeleton():
    s = Skeleton()
    s.add_part("a", points=[Point("p", (30, 20))])
    s.add_part("b", points=[Point("q", (10, 20))])
    s.connect("a", "p", "b", "q")
    s.set_image("a", FakeImg(40, 40))
    s.set_image("b", FakeImg(40, 40))
    return s


def test_compose_flattens_to_expected_canvas_and_offsets():
    s = _skeleton()
    out = s.compose()
    assert out.size == (60, 40)  # a: x0..40, b shifted +20 -> x20..60
    assert out.pastes == ((0, 0, (40, 40)), (20, 0, (40, 40)))


def test_compose_requires_all_parts_have_images():
    s = _skeleton()
    s.add_part("c")  # no image
    with pytest.raises(ValueError):
        s.compose()


def test_transform_changes_composition():
    s = _skeleton()
    s.transform("a", scale(2))
    out = s.compose()
    # a is now 80x80 with p at (60,40); b.q (10,20) aligns -> canvas grows.
    assert s.transformed_size("a") == (80, 80)
    assert out.size == (90, 80)


def test_transform_is_non_destructive_to_originals():
    s = _skeleton()
    s.transform("a", scale(2))
    s.compose()
    # Original image and point coords are untouched.
    assert s.part("a").image.size == (40, 40)
    assert s.point("a", "p").coords == (30.0, 20.0)


def test_reset_part_and_all():
    s = _skeleton()
    baseline = s.compose().size
    s.transform("a", scale(2))
    s.transform("b", crop((5, 5, 35, 35)))
    assert s.compose().size != baseline
    s.reset("a")
    s.reset("b")
    assert s.compose().size == baseline


def test_transforms_stack_in_order():
    s = _skeleton()
    s.transform("a", scale(2))          # 40 -> 80
    s.transform("a", crop((0, 0, 20, 20)))  # 80 -> 20
    assert s.transformed_size("a") == (20, 20)