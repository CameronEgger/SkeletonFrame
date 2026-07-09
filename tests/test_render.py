"""Tests for the pure placement math (no GUI, no display required)."""

from skeleton import Point, Skeleton
from viewer import initial_coords, solve_offsets


def _two_part_skeleton() -> Skeleton:
    s = Skeleton()
    s.add_part("a", points=[Point("p", (30, 20))])
    s.add_part("b", points=[Point("q", (10, 20))])
    s.connect("a", "p", "b", "q")
    return s


def test_initial_coords_snapshots_points():
    s = _two_part_skeleton()
    assert initial_coords(s) == {"a": {"p": (30.0, 20.0)}, "b": {"q": (10.0, 20.0)}}


def test_offsets_align_shared_points():
    s = _two_part_skeleton()
    sizes = {"a": (40, 40), "b": (40, 40)}
    off = solve_offsets(s, sizes)
    # a.p (30,20) must land on b.q (10,20): off[a]+(30,20) == off[b]+(10,20).
    ax, ay = off["a"]
    bx, by = off["b"]
    assert (ax + 30, ay + 20) == (bx + 10, by + 20)


def test_offsets_fit_in_normalized_frame():
    s = _two_part_skeleton()
    sizes = {"a": (40, 40), "b": (40, 40)}
    off = solve_offsets(s, sizes)
    # a at x0..40, b shifted +20 -> x20..60; normalised so min is 0.
    assert min(off["a"][0], off["b"][0]) == 0
    assert off == {"a": (0, 0), "b": (20, 0)}


def test_transformed_coords_keep_joint_aligned():
    # Scaling part b's image ×2 scales its point coords too, so the join holds.
    s = _two_part_skeleton()
    coords = initial_coords(s)
    coords["b"] = {p: (x * 2, y * 2) for p, (x, y) in coords["b"].items()}
    sizes = {"a": (40, 40), "b": (80, 80)}
    off = solve_offsets(s, sizes, coords)
    ax, ay = off["a"]
    bx, by = off["b"]
    assert (ax + 30, ay + 20) == (bx + 20, by + 40)  # b.q now at (20,40)


def test_separate_components_are_stacked():
    s = Skeleton()
    s.add_part("solo1")
    s.add_part("solo2")
    off = solve_offsets(s, {"solo1": (30, 30), "solo2": (30, 30)}, spacing=10)
    # Two lone parts -> stacked vertically with the spacing between them.
    ys = sorted(y for _x, y in off.values())
    assert ys == [0, 40]