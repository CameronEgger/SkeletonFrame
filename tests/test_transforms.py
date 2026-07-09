"""Tests for the backend-agnostic transforms, driven by a fake Image backend."""

from dataclasses import dataclass, field
from functools import partial

import pytest

from transforms import Image, Transform, compose, operations as ops


@dataclass(frozen=True)
class FakeImage:
    """A minimal in-memory backend implementing the Image protocol.

    Tracks its size through size-changing ops and logs every op applied, so
    tests can assert both the resulting geometry and the operation sequence.
    """

    width: int
    height: int
    log: tuple[str, ...] = field(default_factory=tuple)

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def rotate(self, degrees: float) -> "FakeImage":
        return FakeImage(self.width, self.height, self.log + (f"rotate({degrees})",))

    def scale(self, factor_x: float, factor_y: float) -> "FakeImage":
        return FakeImage(
            round(self.width * factor_x),
            round(self.height * factor_y),
            self.log + (f"scale({factor_x},{factor_y})",),
        )

    def crop(self, box) -> "FakeImage":
        left, top, right, bottom = box
        return FakeImage(right - left, bottom - top, self.log + (f"crop{box}",))

    def flip(self, horizontal: bool = False, vertical: bool = False) -> "FakeImage":
        return FakeImage(
            self.width, self.height, self.log + (f"flip({horizontal},{vertical})",)
        )

    def blank(self, width: int, height: int) -> "FakeImage":
        return FakeImage(width, height)

    def paste(self, other: "FakeImage", x: int, y: int) -> "FakeImage":
        return FakeImage(self.width, self.height, self.log + (f"paste({x},{y})",))


def test_fake_image_satisfies_protocol():
    assert isinstance(FakeImage(10, 10), Image)


# --- operations --------------------------------------------------------
def test_rotate_preserves_size_and_logs():
    out = ops.rotate(FakeImage(10, 20), degrees=90)
    assert out.size == (10, 20)
    assert out.log == ("rotate(90)",)


def test_scale_uniform():
    assert ops.scale(FakeImage(10, 20), factor=2).size == (20, 40)


def test_scale_xy():
    assert ops.scale_xy(FakeImage(10, 20), factor_x=2, factor_y=0.5).size == (20, 10)


def test_resize_to_exact_size():
    assert ops.resize(FakeImage(10, 20), width=5, height=5).size == (5, 5)


def test_resize_rejects_nonpositive():
    with pytest.raises(ValueError):
        ops.resize(FakeImage(10, 10), width=0, height=5)


def test_fit_within_preserves_aspect_ratio():
    # 40x20 into a 10x10 box -> limited by width, factor 0.25 -> 10x5.
    assert ops.fit_within(FakeImage(40, 20), max_width=10, max_height=10).size == (10, 5)


def test_fit_within_rejects_nonpositive():
    with pytest.raises(ValueError):
        ops.fit_within(FakeImage(10, 10), max_width=10, max_height=0)


def test_flip_horizontal_and_vertical():
    assert ops.flip_horizontal(FakeImage(4, 4)).log == ("flip(True,False)",)
    assert ops.flip_vertical(FakeImage(4, 4)).log == ("flip(False,True)",)


def test_crop():
    out = ops.crop(FakeImage(10, 10), box=(1, 2, 6, 9))
    assert out.size == (5, 7)


def test_center_crop():
    out = ops.center_crop(FakeImage(10, 10), width=4, height=4)
    assert out.size == (4, 4)
    assert out.log == ("crop(3, 3, 7, 7)",)


def test_center_crop_rejects_oversize():
    with pytest.raises(ValueError):
        ops.center_crop(FakeImage(10, 10), width=20, height=4)


# --- composition -------------------------------------------------------
def test_transform_applies_in_order():
    pipe = Transform(partial(ops.scale, factor=2), partial(ops.rotate, degrees=90))
    out = pipe(FakeImage(10, 10))
    assert out.size == (20, 20)
    assert out.log == ("scale(2,2)", "rotate(90)")


def test_transform_then_and_or_chain():
    a = Transform(partial(ops.scale, factor=2))
    b = Transform(ops.flip_horizontal)
    via_then = a.then(b)(FakeImage(5, 5))
    via_or = (a | ops.flip_horizontal)(FakeImage(5, 5))
    assert via_then.log == via_or.log == ("scale(2,2)", "flip(True,False)")


def test_compose_equivalent_to_transform():
    pipe = compose(partial(ops.resize, width=8, height=8), ops.flip_vertical)
    out = pipe(FakeImage(4, 4))
    assert out.size == (8, 8)
    assert out.log == ("scale(2.0,2.0)", "flip(False,True)")


def test_empty_transform_is_identity():
    img = FakeImage(3, 3)
    assert Transform()(img) is img