"""Tests for the pure-Python graph layout (no GUI required)."""

from viewer import spring_layout


def _adjacency():
    return {
        "head": {"torso"},
        "torso": {"head", "legs"},
        "legs": {"torso"},
        "balloon": set(),  # isolated
    }


def test_empty_graph():
    assert spring_layout({}) == {}


def test_single_node_is_centered():
    pos = spring_layout({"only": set()}, 800, 600)
    assert pos == {"only": (400.0, 300.0)}


def test_all_nodes_placed_within_frame():
    w, h, pad = 800, 600, 40
    pos = spring_layout(_adjacency(), w, h, padding=pad)
    assert set(pos) == set(_adjacency())
    for x, y in pos.values():
        assert pad <= x <= w - pad
        assert pad <= y <= h - pad


def test_deterministic_for_same_seed():
    adj = _adjacency()
    assert spring_layout(adj, seed=7) == spring_layout(adj, seed=7)


def test_connected_nodes_end_up_closer_than_isolated_one():
    pos = spring_layout(_adjacency(), 800, 600, seed=1)

    def dist(a, b):
        return ((pos[a][0] - pos[b][0]) ** 2 + (pos[a][1] - pos[b][1]) ** 2) ** 0.5

    # The spring pulls the connected chain together; the isolated balloon is
    # only repelled, so it should sit farther from the torso than the head does.
    assert dist("head", "torso") < dist("balloon", "torso")