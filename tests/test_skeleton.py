"""Tests for the abstract skeleton: parts, points, connections, relationships."""

import pytest

from skeleton import Connection, Part, Point, Skeleton


# --- Point -------------------------------------------------------------
def test_point_normalizes_coords_to_floats():
    p = Point("neck", (100, 70))
    assert p.coords == (100.0, 70.0)
    assert all(isinstance(c, float) for c in p.coords)


def test_point_dim_is_arbitrary():
    assert Point("a").dim == 0
    assert Point("b", (1, 2)).dim == 2
    assert Point("c", (1, 2, 3)).dim == 3


def test_point_copy_is_independent():
    p = Point("neck", (1, 2), data={"k": "v"})
    q = p.copy()
    assert q == p and q is not p


# --- Part --------------------------------------------------------------
def test_part_holds_opaque_image():
    sentinel = object()
    part = Part("head", image=sentinel)
    assert part.image is sentinel


def test_part_add_and_get_point():
    part = Part("head")
    pt = part.add_point("neck", (100, 70))
    assert part.point("neck") is pt
    assert part.has_point("neck")
    assert not part.has_point("missing")


def test_part_copy_is_deep_for_points():
    part = Part("head", points={"neck": Point("neck", (1, 2))})
    clone = part.copy()
    clone.point("neck").coords = (9, 9)
    assert part.point("neck").coords == (1.0, 2.0)


# --- Connection --------------------------------------------------------
def test_connection_other_and_involves():
    c = Connection("head", "neck", "torso", "neck", label="spine")
    assert c.involves("head") and c.involves("torso")
    assert not c.involves("legs")
    assert c.other("head") == ("torso", "neck")
    assert c.other("torso") == ("head", "neck")


def test_connection_other_rejects_uninvolved_part():
    c = Connection("head", "neck", "torso", "neck")
    with pytest.raises(ValueError):
        c.other("legs")


def test_connection_endpoints():
    c = Connection("a", "p", "b", "q")
    assert c.endpoints() == (("a", "p"), ("b", "q"))


# --- Skeleton fixture --------------------------------------------------
@pytest.fixture
def humanoid() -> Skeleton:
    s = Skeleton()
    s.add_part("head", "head.png", [Point("neck", (100, 70))])
    s.add_part("torso", "torso.png", [Point("neck", (100, 70)), Point("hip", (100, 180))])
    s.add_part("legs", "legs.png", [Point("hip", (100, 180))])
    s.connect("head", "neck", "torso", "neck", label="spine")
    s.connect("torso", "hip", "legs", "hip")
    return s


# --- Skeleton construction / validation --------------------------------
def test_add_part_rejects_duplicate():
    s = Skeleton()
    s.add_part("head")
    with pytest.raises(ValueError):
        s.add_part("head")


def test_add_part_accepts_dict_or_iterable_of_points():
    s = Skeleton()
    a = s.add_part("a", points=[Point("p", (1, 1))])
    b = s.add_part("b", points={"q": Point("q", (2, 2))})
    assert a.has_point("p") and b.has_point("q")


def test_connect_rejects_self_loop():
    s = Skeleton()
    s.add_part("head", points=[Point("p")])
    with pytest.raises(ValueError):
        s.connect("head", "p", "head", "p")


def test_connect_rejects_missing_part():
    s = Skeleton()
    s.add_part("head", points=[Point("p")])
    with pytest.raises(KeyError):
        s.connect("head", "p", "ghost", "q")


def test_connect_rejects_missing_point():
    s = Skeleton()
    s.add_part("head", points=[Point("p")])
    s.add_part("torso", points=[Point("q")])
    with pytest.raises(KeyError):
        s.connect("head", "nope", "torso", "q")


# --- Skeleton relationships --------------------------------------------
def test_neighbors(humanoid):
    assert humanoid.neighbors("torso") == {"head", "legs"}
    assert humanoid.neighbors("head") == {"torso"}


def test_related_is_transitive(humanoid):
    assert humanoid.related("head") == {"torso", "legs"}


def test_adjacency_covers_all_parts_including_unconnected():
    s = Skeleton()
    s.add_part("a", points=[Point("p")])
    s.add_part("b", points=[Point("q")])
    s.add_part("lonely")
    s.connect("a", "p", "b", "q")
    adj = s.adjacency()
    assert adj == {"a": {"b"}, "b": {"a"}, "lonely": set()}


def test_components_groups_related_and_isolates_lonely(humanoid):
    humanoid.add_part("balloon", "balloon.png")
    comps = sorted(sorted(g) for g in humanoid.components())
    assert comps == [["balloon"], ["head", "legs", "torso"]]


def test_is_connected(humanoid):
    assert humanoid.is_connected()
    humanoid.add_part("balloon")
    assert not humanoid.is_connected()


def test_empty_skeleton_is_not_connected():
    assert not Skeleton().is_connected()


def test_connections_of(humanoid):
    labels = {c.label for c in humanoid.connections_of("torso")}
    assert labels == {"spine", None}
    assert humanoid.connections_of("head")[0].label == "spine"


# --- dunders / lookup / copy -------------------------------------------
def test_container_dunders(humanoid):
    assert len(humanoid) == 3
    assert "torso" in humanoid and "ghost" not in humanoid
    assert {p.name for p in humanoid} == {"head", "torso", "legs"}


def test_point_lookup(humanoid):
    assert humanoid.point("torso", "hip").coords == (100.0, 180.0)


def test_copy_is_independent(humanoid):
    clone = humanoid.copy()
    clone.point("torso", "hip").coords = (0, 0)
    assert humanoid.point("torso", "hip").coords == (100.0, 180.0)
    assert clone.connections == humanoid.connections