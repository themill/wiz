# :coding: utf-8

import pytest

import wiz.graph


@pytest.fixture()
def mocked_graph(mocker):
    """Return mocked Graph."""
    graph = mocker.patch.object(wiz.graph, "Graph")
    graph.ROOT = "root"
    return graph


@pytest.fixture()
def mocked_graph_remove_node(mocker):
    """Return mocked Graph.remove_node method."""
    return mocker.patch.object(wiz.graph.Graph, "remove_node")


@pytest.mark.parametrize("mapping, expected", [
    (
        {"root": []},
        {"root": wiz.graph.NodeAttribute(0, "root")}
    ),
    (
        {"root": ["A"], "A": []},
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root")
        }
    ),
    (
        {"root": ["A", "B"], "A": [], "B": []},
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root"),
            "B": wiz.graph.NodeAttribute(2, "root")
        }
    ),
    (
        {"root": ["A", "B", "C"], "A": [], "B": [], "C": []},
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root"),
            "B": wiz.graph.NodeAttribute(2, "root"),
            "C": wiz.graph.NodeAttribute(3, "root")
        }
    ),
    (
        {"root": ["A"], "A": ["B"], "B": []},
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root"),
            "B": wiz.graph.NodeAttribute(2, "A")
        }
    ),
    (
        {"root": ["A"], "A": ["B"], "B": ["C"], "C": []},
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root"),
            "B": wiz.graph.NodeAttribute(2, "A"),
            "C": wiz.graph.NodeAttribute(3, "B")
        }
    ),
    (
        {"root": ["A", "B"], "A": ["B"], "B": ["A"]},
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root"),
            "B": wiz.graph.NodeAttribute(2, "root")
        }
    ),
    (
        {
            "root": ["A", "B"],
            "A": ["C", "D"],
            "B": ["D", "F", "G"],
            "C": [],
            "D": ["E"],
            "E": [],
            "F": [],
            "G": []
        },
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root"),
            "B": wiz.graph.NodeAttribute(2, "root"),
            "C": wiz.graph.NodeAttribute(2, "A"),
            "D": wiz.graph.NodeAttribute(3, "A"),
            "E": wiz.graph.NodeAttribute(4, "D"),
            "F": wiz.graph.NodeAttribute(4, "B"),
            "G": wiz.graph.NodeAttribute(5, "B"),
        }
    ),
    (
        {
            "root": ["A"],
            "A": ["C", "E", "F"],
            "B": ["F", "D"],
            "C": [],
            "D": [],
            "E": [],
            "F": []
        },
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root"),
            "B": wiz.graph.NodeAttribute(None, None),
            "C": wiz.graph.NodeAttribute(2, "A"),
            "D": wiz.graph.NodeAttribute(None, None),
            "E": wiz.graph.NodeAttribute(3, "A"),
            "F": wiz.graph.NodeAttribute(4, "A"),
        }

    ),
    (
        {
            "root": ["A", "B", "F"],
            "A": ["C", "D"],
            "B": ["D", "F", "G"],
            "C": ["G"],
            "D": ["E"],
            "E": ["A"],
            "F": [],
            "G": ["B"],
        },
        {
            "root": wiz.graph.NodeAttribute(0, "root"),
            "A": wiz.graph.NodeAttribute(1, "root"),
            "B": wiz.graph.NodeAttribute(2, "root"),
            "C": wiz.graph.NodeAttribute(2, "A"),
            "D": wiz.graph.NodeAttribute(3, "A"),
            "E": wiz.graph.NodeAttribute(4, "D"),
            "F": wiz.graph.NodeAttribute(3, "root"),
            "G": wiz.graph.NodeAttribute(3, "C"),
        }
    )
], ids=[
    "no-node",
    "one-node",
    "two-nodes",
    "three-nodes",
    "two-levels",
    "three-levels",
    "with-cycle",
    "multi-levels",
    "multi-levels-with-unreachable-nodes",
    "complex-multi-levels"
])
def test_compute_priority_mapping(mocked_graph, mapping, expected):
    """Compute priority mapping from Graph."""
    mocked_graph.node_identifiers.return_value = mapping.keys()
    mocked_graph.outcoming = lambda x: mapping[x]
    mocked_graph.link_weight = lambda x, y: mapping[y].index(x) + 1
    assert wiz.graph.compute_priority_mapping(mocked_graph) == expected


def test_remove_unreachable_nodes(mocked_graph, mocked_graph_remove_node):
    """Remove unreachable nodes from graph based on priority mapping."""
    identifiers = ["A", "B", "C", "D", "E", "F"]
    mocked_graph.node_identifiers.return_value = identifiers

    priority_mapping = {
        "root": wiz.graph.NodeAttribute(0, "root"),
        "A": wiz.graph.NodeAttribute(1, "root"),
        "B": wiz.graph.NodeAttribute(None, None),
        "C": wiz.graph.NodeAttribute(2, "A"),
        "D": wiz.graph.NodeAttribute(None, None),
        "E": wiz.graph.NodeAttribute(3, "A"),
        "F": wiz.graph.NodeAttribute(4, "A"),
    }

    wiz.graph.remove_unreachable_nodes(mocked_graph, priority_mapping)

    assert mocked_graph_remove_node.call_count == 2
    mocked_graph_remove_node.assert_any_call("B")
    mocked_graph_remove_node.assert_any_call("D")


def test_sorted_identifiers():
    """Sort node identifiers based on priority mapping."""
    identifiers = ["F", "E", "D", "C", "B", "A"]

    priority_mapping = {
        "root": wiz.graph.NodeAttribute(0, "root"),
        "A": wiz.graph.NodeAttribute(1, "root"),
        "B": wiz.graph.NodeAttribute(None, None),
        "C": wiz.graph.NodeAttribute(2, "A"),
        "D": wiz.graph.NodeAttribute(None, None),
        "E": wiz.graph.NodeAttribute(3, "A"),
        "F": wiz.graph.NodeAttribute(4, "A"),
    }

    result = wiz.graph.sorted_identifiers(identifiers, priority_mapping)
    assert result == ["A", "C", "E", "F"]
