# :coding: utf-8

import pytest
import mock
import types
import itertools
import re

from wiz.utility import Requirement
import wiz.graph
import wiz.package
import wiz.exception


@pytest.fixture()
def mocked_queue(mocker):
    """Return mocked Queue constructor."""
    instance = mocker.Mock()
    try:
        import queue
        mocker.patch("queue.Queue", return_value=instance)

    except ImportError:
        import Queue
        mocker.patch("Queue.Queue", return_value=instance)

    return instance


@pytest.fixture()
def mocked_graph(mocker):
    """Return mocked Graph."""
    graph = mocker.patch.object(wiz.graph, "Graph")
    graph.ROOT = "root"
    return graph


@pytest.fixture()
def mocked_resolver(mocker):
    """Return mocked Resolver."""
    resolver = mocker.patch.object(wiz.graph, "Resolver")
    resolver.definition_mapping = "DEFINITION_MAPPING"
    return resolver


@pytest.fixture()
def mocked_graph_remove_node(mocker):
    """Return mocked Graph.remove_node method."""
    return mocker.patch.object(wiz.graph.Graph, "remove_node")


@pytest.fixture()
def mocked_extract_requirement(mocker):
    """Return mocked extract_requirement method."""
    return mocker.patch.object(wiz.graph, "extract_requirement")


@pytest.fixture()
def mocked_package_extract(mocker):
    """Return mocked wiz.package.extract method."""
    return mocker.patch.object(wiz.package, "extract")


def test_resolver():
    """Create a resolver."""
    definition_mapping = {"defA": ["nodeA"], "defB": ["nodeB"]}
    resolver = wiz.graph.Resolver(definition_mapping)
    assert resolver.definition_mapping == definition_mapping
    assert id(resolver.definition_mapping) == id(definition_mapping)


@pytest.mark.parametrize("mapping, expected", [
    (
        {"root": []},
        {"root": {"distance": 0, "parent": "root"}}
    ),
    (
        {"root": ["A"], "A": []},
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"}
        }
    ),
    (
        {"root": ["A", "B"], "A": [], "B": []},
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"}
        }
    ),
    (
        {"root": ["A", "B", "C"], "A": [], "B": [], "C": []},
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"},
            "C": {"distance": 3, "parent": "root"}
        }
    ),
    (
        {"root": ["A"], "A": ["B"], "B": []},
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "A"}
        }
    ),
    (
        {"root": ["A"], "A": ["B"], "B": ["C"], "C": []},
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "A"},
            "C": {"distance": 3, "parent": "B"}
        }
    ),
    (
        {"root": ["A", "B"], "A": ["B"], "B": ["A"]},
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"}
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
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"},
            "C": {"distance": 2, "parent": "A"},
            "D": {"distance": 3, "parent": "A"},
            "E": {"distance": 4, "parent": "D"},
            "F": {"distance": 4, "parent": "B"},
            "G": {"distance": 5, "parent": "B"},
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
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": None, "parent": None},
            "C": {"distance": 2, "parent": "A"},
            "D": {"distance": None, "parent": None},
            "E": {"distance": 3, "parent": "A"},
            "F": {"distance": 4, "parent": "A"},
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
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"},
            "C": {"distance": 2, "parent": "A"},
            "D": {"distance": 3, "parent": "A"},
            "E": {"distance": 4, "parent": "D"},
            "F": {"distance": 3, "parent": "root"},
            "G": {"distance": 3, "parent": "C"},
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
def test_compute_distance_mapping(mocker, mocked_graph, mapping, expected):
    """Compute distance mapping from Graph."""
    nodes = [mocker.Mock(identifier=_id) for _id in mapping.keys()]
    mocked_graph.nodes.return_value = nodes
    mocked_graph.outcoming = lambda x: mapping[x]
    mocked_graph.link_weight = lambda x, y: mapping[y].index(x) + 1
    assert wiz.graph.compute_distance_mapping(mocked_graph) == expected


@pytest.mark.parametrize("variant_groups, expected", [
    (
        [["foo[V2]", "foo[V1]"]],
        [("foo[V1]",), ("foo[V2]",)]
    ),
    (
        [["foo[V3]", "foo[V2]", "foo[V1]"]],
        [
            ("foo[V2]", "foo[V1]"),
            ("foo[V3]", "foo[V1]"),
            ("foo[V3]", "foo[V2]")
        ]
    ),
    (
        [["foo[V4]", "foo[V3]", "foo[V2]", "foo[V1]"]],
        [
            ("foo[V3]", "foo[V2]", "foo[V1]"),
            ("foo[V4]", "foo[V2]", "foo[V1]"),
            ("foo[V4]", "foo[V3]", "foo[V1]"),
            ("foo[V4]", "foo[V3]", "foo[V2]")
        ]
    ),
    (
        [["foo[V3]==1", "foo[V2]==1", "foo[V1]==1", "foo[V1]==2"]],
        [
            ("foo[V2]==1", "foo[V1]==1", "foo[V1]==2"),
            ("foo[V3]==1", "foo[V1]==1", "foo[V1]==2"),
            ("foo[V3]==1", "foo[V2]==1")
        ]
    ),
    (
        [["foo[V3]", "foo[V2]", "foo[V1]"], ["bar[V1]", "bar[V2]"]],
        [
            ("foo[V2]", "foo[V1]", "bar[V2]"),
            ("foo[V2]", "foo[V1]", "bar[V1]"),
            ("foo[V3]", "foo[V1]", "bar[V2]"),
            ("foo[V3]", "foo[V1]", "bar[V1]"),
            ("foo[V3]", "foo[V2]", "bar[V2]"),
            ("foo[V3]", "foo[V2]", "bar[V1]")
        ]
    ),
    (
        [
            ["foo[V3]", "foo[V2]", "foo[V1]"],
            ["bar[V4]", "bar[V3]", "bar[V2]", "bar[V1]"],
            ["bim[V2]", "bim[V1]"]
        ],
        [
            ("foo[V2]", "foo[V1]", "bar[V3]", "bar[V2]", "bar[V1]", "bim[V1]"),
            ("foo[V2]", "foo[V1]", "bar[V3]", "bar[V2]", "bar[V1]", "bim[V2]"),
            ("foo[V2]", "foo[V1]", "bar[V4]", "bar[V2]", "bar[V1]", "bim[V1]"),
            ("foo[V2]", "foo[V1]", "bar[V4]", "bar[V2]", "bar[V1]", "bim[V2]"),
            ("foo[V2]", "foo[V1]", "bar[V4]", "bar[V3]", "bar[V1]", "bim[V1]"),
            ("foo[V2]", "foo[V1]", "bar[V4]", "bar[V3]", "bar[V1]", "bim[V2]"),
            ("foo[V2]", "foo[V1]", "bar[V4]", "bar[V3]", "bar[V2]", "bim[V1]"),
            ("foo[V2]", "foo[V1]", "bar[V4]", "bar[V3]", "bar[V2]", "bim[V2]"),
            ("foo[V3]", "foo[V1]", "bar[V3]", "bar[V2]", "bar[V1]", "bim[V1]"),
            ("foo[V3]", "foo[V1]", "bar[V3]", "bar[V2]", "bar[V1]", "bim[V2]"),
            ("foo[V3]", "foo[V1]", "bar[V4]", "bar[V2]", "bar[V1]", "bim[V1]"),
            ("foo[V3]", "foo[V1]", "bar[V4]", "bar[V2]", "bar[V1]", "bim[V2]"),
            ("foo[V3]", "foo[V1]", "bar[V4]", "bar[V3]", "bar[V1]", "bim[V1]"),
            ("foo[V3]", "foo[V1]", "bar[V4]", "bar[V3]", "bar[V1]", "bim[V2]"),
            ("foo[V3]", "foo[V1]", "bar[V4]", "bar[V3]", "bar[V2]", "bim[V1]"),
            ("foo[V3]", "foo[V1]", "bar[V4]", "bar[V3]", "bar[V2]", "bim[V2]"),
            ("foo[V3]", "foo[V2]", "bar[V3]", "bar[V2]", "bar[V1]", "bim[V1]"),
            ("foo[V3]", "foo[V2]", "bar[V3]", "bar[V2]", "bar[V1]", "bim[V2]"),
            ("foo[V3]", "foo[V2]", "bar[V4]", "bar[V2]", "bar[V1]", "bim[V1]"),
            ("foo[V3]", "foo[V2]", "bar[V4]", "bar[V2]", "bar[V1]", "bim[V2]"),
            ("foo[V3]", "foo[V2]", "bar[V4]", "bar[V3]", "bar[V1]", "bim[V1]"),
            ("foo[V3]", "foo[V2]", "bar[V4]", "bar[V3]", "bar[V1]", "bim[V2]"),
            ("foo[V3]", "foo[V2]", "bar[V4]", "bar[V3]", "bar[V2]", "bim[V1]"),
            ("foo[V3]", "foo[V2]", "bar[V4]", "bar[V3]", "bar[V2]", "bim[V2]")
        ]
    ),
    (
        [
            ["A[V2]==1", "A[V1]==1", "A[V1]==2"],
            ["B[V3]==1", "B[V2]==1", "B[V1]==1", "B[V2]==2"]
        ],
        [
            ("A[V1]==1", "A[V1]==2", "B[V2]==1", "B[V1]==1", "B[V2]==2"),
            ("A[V1]==1", "A[V1]==2", "B[V3]==1", "B[V1]==1"),
            ("A[V1]==1", "A[V1]==2", "B[V3]==1", "B[V2]==1", "B[V2]==2"),
            ("A[V2]==1", "B[V2]==1", "B[V1]==1", "B[V2]==2"),
            ("A[V2]==1", "B[V3]==1", "B[V1]==1"),
            ("A[V2]==1", "B[V3]==1", "B[V2]==1", "B[V2]==2")
        ]
    ),
], ids=[
    "one-group-of-2",
    "one-group-of-3",
    "one-group-of-4",
    "one-group-with-conflicts",
    "two-groups",
    "three-groups",
    "multiple-groups-with-conflicts",
])
def test_generate_variant_combinations(
    mocker, mocked_graph, variant_groups, expected
):
    """Return list of node trimming combinations from variants."""
    # Suppose that variants are always between square brackets in identifier.
    mocked_graph.node = lambda _id: mocker.Mock(
        identifier=_id, variant_name=re.search("(?<=\[).+(?=\])", _id).group(0)
    )

    results = wiz.graph.generate_variant_combinations(
        mocked_graph, variant_groups
    )
    assert isinstance(results, types.GeneratorType) is True
    for combination, _expected in itertools.izip_longest(results, expected):
        assert combination[0] == mocked_graph
        assert combination[1] == _expected


def test_trim_unreachable_from_graph(
    mocker, mocked_graph, mocked_graph_remove_node
):
    """Remove unreachable nodes from graph based on distance mapping."""
    mocked_graph.nodes.return_value = [
        mocker.Mock(identifier="A"),
        mocker.Mock(identifier="B"),
        mocker.Mock(identifier="C"),
        mocker.Mock(identifier="D"),
        mocker.Mock(identifier="E"),
        mocker.Mock(identifier="F"),
    ]

    distance_mapping = {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": None, "parent": None},
        "C": {"distance": 2, "parent": "A"},
        "D": {"distance": None, "parent": None},
        "E": {"distance": 3, "parent": "A"},
        "F": {"distance": 4, "parent": "A"},
    }

    wiz.graph.trim_unreachable_from_graph(mocked_graph, distance_mapping)

    assert mocked_graph_remove_node.call_count == 2
    mocked_graph_remove_node.assert_any_call("B")
    mocked_graph_remove_node.assert_any_call("D")


@pytest.mark.parametrize("distance_mapping, nodes_removed", [
    (
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"},
            "C": {"distance": 3, "parent": "root"},
            "D": {"distance": None, "parent": None},
        },
        ["B"]
    ),
    (
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"},
            "C": {"distance": 3, "parent": "root"},
            "D": {"distance": 4, "parent": "A"},
        },
        []
    ),
], ids=[
    "true",
    "false",
])
def test_trim_invalid_from_graph(
    mocker, mocked_graph, mocked_graph_remove_node, distance_mapping,
    nodes_removed
):
    """Remove invalid nodes from graph based on distance mapping."""
    mocked_graph.nodes.return_value = [
        mocker.Mock(identifier="A", conditioned_by=["B", "C"]),
        mocker.Mock(identifier="B", conditioned_by=["C", "D"]),
        mocker.Mock(identifier="C", conditioned_by=[]),
        mocker.Mock(identifier="D", conditioned_by=[]),
    ]

    result = wiz.graph.trim_invalid_from_graph(mocked_graph, distance_mapping)
    assert result == (len(nodes_removed) > 0)

    assert mocked_graph_remove_node.call_count == len(nodes_removed)
    for node in nodes_removed:
        mocked_graph_remove_node.assert_any_call(node)


def test_trim_invalid_from_graph_not_found(
    mocker, mocked_graph, mocked_graph_remove_node
):
    """Remove invalid nodes from graph based on distance mapping."""
    mocked_graph.nodes.return_value = [
        mocker.Mock(identifier="A", conditioned_by=["B", "C"]),
        mocker.Mock(identifier="B", conditioned_by=["C", "D"]),
        mocker.Mock(identifier="C", conditioned_by=[]),
        mocker.Mock(identifier="D", conditioned_by=[]),
    ]

    distance_mapping = {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "root"},
        "C": {"distance": 3, "parent": "root"},
        "D": {"distance": None, "parent": None},
        "E": {"distance": 3, "parent": "A"},
        "F": {"distance": 4, "parent": "A"},
    }

    result = wiz.graph.trim_invalid_from_graph(mocked_graph, distance_mapping)
    assert result is True

    assert mocked_graph_remove_node.call_count == 1
    mocked_graph_remove_node.assert_any_call("B")


def test_updated_by_distance():
    """Update nodes based on distance mapping."""
    identifiers = ["F", "E", "D", "C", "B", "A"]

    distance_mapping = {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": None, "parent": None},
        "C": {"distance": 2, "parent": "A"},
        "D": {"distance": None, "parent": None},
        "E": {"distance": 3, "parent": "A"},
        "F": {"distance": 4, "parent": "A"},
    }

    result = wiz.graph.updated_by_distance(identifiers, distance_mapping)
    assert result == ["A", "C", "E", "F"]


def test_extract_conflicting_nodes(mocker, mocked_graph):
    """Extract conflicting nodes for a specific node."""
    node_mapping = {
        "A": mocker.Mock(identifier="A", definition="defB"),
        "B": mocker.Mock(identifier="B", definition="defB"),
        "C": mocker.Mock(identifier="C", definition="defB"),
        "D": mocker.Mock(identifier="D", definition="defA"),
        "E": mocker.Mock(identifier="E", definition="defA"),
        "F": mocker.Mock(identifier="F", definition="defA")
    }

    mocked_graph.node = lambda _id: node_mapping[_id]
    mocked_graph.conflicts.return_value = sorted(node_mapping.keys())

    assert wiz.graph.extract_conflicting_nodes(
        mocked_graph, node_mapping["F"]
    ) == [node_mapping["D"], node_mapping["E"]]

    assert wiz.graph.extract_conflicting_nodes(
        mocked_graph, node_mapping["E"]
    ) == [node_mapping["D"], node_mapping["F"]]

    assert wiz.graph.extract_conflicting_nodes(
        mocked_graph, node_mapping["C"]
    ) == [node_mapping["A"], node_mapping["B"]]


def test_combined_requirements(mocker, mocked_graph):
    """Combine nodes requirements."""
    requirements = [
        Requirement("A >= 1"),
        Requirement("A >= 1, < 2"),
        Requirement("A == 1.2.3")
    ]

    nodes = [
        mocker.Mock(identifier="A==3"),
        mocker.Mock(identifier="A==1.9"),
        mocker.Mock(identifier="A==1.2.3")
    ]

    distance_mapping = {
        "A==3": {"distance": 1, "parent": "B"},
        "A==1.9": {"distance": 2, "parent": "C"},
        "A==1.2.3": {"distance": 3, "parent": "D"},
    }

    mocked_graph.link_requirement.side_effect = requirements

    requirement = wiz.graph.combined_requirements(
        mocked_graph, nodes, distance_mapping
    )

    assert str(requirement) == "A >=1, ==1.2.3, <2"

    assert mocked_graph.link_requirement.call_count == 3
    mocked_graph.link_requirement.assert_any_call("A==3", "B")
    mocked_graph.link_requirement.assert_any_call("A==1.9", "C")
    mocked_graph.link_requirement.assert_any_call("A==1.2.3", "D")


def test_combined_requirements_error(mocker, mocked_graph):
    """Fail to combine nodes requirements from different definition name."""
    requirements = [
        Requirement("A >= 1"),
        Requirement("Z >= 1, < 2"),
        Requirement("A == 1.2.3")
    ]

    nodes = [
        mocker.Mock(identifier="A==3"),
        mocker.Mock(identifier="Z==1.9"),
        mocker.Mock(identifier="A==1.2.3")
    ]

    distance_mapping = {
        "A==3": {"distance": 1, "parent": "B"},
        "Z==1.9": {"distance": 2, "parent": "C"},
        "A==1.2.3": {"distance": 3, "parent": "D"},
    }

    mocked_graph.link_requirement.side_effect = requirements

    with pytest.raises(wiz.exception.GraphResolutionError):
        wiz.graph.combined_requirements(
            mocked_graph, nodes, distance_mapping
        )

    assert mocked_graph.link_requirement.call_count == 2
    mocked_graph.link_requirement.assert_any_call("A==3", "B")
    mocked_graph.link_requirement.assert_any_call("Z==1.9", "C")


def test_extract_parents(mocker, mocked_graph):
    """Extract parent identifiers from nodes."""
    nodes = [
        mocker.Mock(identifier="A", parent_identifiers=["E", "F"]),
        mocker.Mock(identifier="B", parent_identifiers=["F", "G"]),
        mocker.Mock(identifier="C", parent_identifiers=["root"]),
        mocker.Mock(identifier="D", parent_identifiers=["H"])
    ]

    mocked_graph.node.side_effect = [
        mocker.Mock(identifier="E"),
        mocker.Mock(identifier="F"),
        mocker.Mock(identifier="F"),
        mocker.Mock(identifier="G"),
        None
    ]

    parents = wiz.graph.extract_parents(mocked_graph, nodes)
    assert isinstance(parents, set) is True
    assert sorted(parents) == ["E", "F", "G"]


def test_remove_node_and_relink(mocker, mocked_graph):
    """Remove node and relink node's parents."""
    node = mocker.Mock(
        identifier="foo", parent_identifiers=["parent1", "parent2", "parent3"]
    )

    mocked_graph.exists.side_effect = [True, False, True]
    mocked_graph.link_weight.side_effect = [1, 2]

    wiz.graph.remove_node_and_relink(
        mocked_graph, node, ["bar", "baz", "bim"], "__REQUIREMENT__"
    )

    mocked_graph.remove_node.assert_called_once_with("foo")

    assert mocked_graph.exists.call_count == 3
    mocked_graph.exists.assert_any_call("parent1")
    mocked_graph.exists.assert_any_call("parent2")
    mocked_graph.exists.assert_any_call("parent3")

    assert mocked_graph.link_weight.call_count == 2
    mocked_graph.link_weight.assert_any_call("foo", "parent1")
    mocked_graph.link_weight.assert_any_call("foo", "parent3")

    assert mocked_graph.create_link.call_count == 6
    mocked_graph.create_link.assert_any_call(
        "bar", "parent1", "__REQUIREMENT__", weight=1
    )
    mocked_graph.create_link.assert_any_call(
        "baz", "parent1", "__REQUIREMENT__", weight=1
    )
    mocked_graph.create_link.assert_any_call(
        "bim", "parent1", "__REQUIREMENT__", weight=1
    )
    mocked_graph.create_link.assert_any_call(
        "bar", "parent3", "__REQUIREMENT__", weight=2
    )
    mocked_graph.create_link.assert_any_call(
        "baz", "parent3", "__REQUIREMENT__", weight=2
    )
    mocked_graph.create_link.assert_any_call(
        "bim", "parent3", "__REQUIREMENT__", weight=2
    )


@pytest.mark.parametrize("identifiers, distance_mapping, expected", [
    (
        [],
        {"root": {"distance": 0, "parent": "root"}},
        []
    ),
    (
        ["A"],
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"}
        },
        ["A"]
    ),
    (
        ["A", "B"],
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"}
        },
        ["B", "A"],
    ),
    (
        ["A", "B", "C"],
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"},
            "C": {"distance": 3, "parent": "root"}
        },
        ["C", "B", "A"]
    ),
    (
        ["A", "B", "C", "D", "E", "F", "G"],
        {
            "root": {"distance": 0, "parent": "root"},
            "A": {"distance": 1, "parent": "root"},
            "B": {"distance": 2, "parent": "root"},
            "C": {"distance": 2, "parent": "A"},
            "D": {"distance": 3, "parent": "A"},
            "E": {"distance": 4, "parent": "D"},
            "F": {"distance": 4, "parent": "B"},
            "G": {"distance": 5, "parent": "B"},
        },
        ["G", "E", "F", "D", "B", "C", "A"]
    ),
], ids=[
    "no-node",
    "one-node",
    "two-nodes",
    "three-nodes",
    "multi-levels"
])
def test_extract_ordered_packages(
    mocker, mocked_graph, identifiers, distance_mapping, expected
):
    """Extract ordered packages from graph."""
    package_mapping = {
        _id: mocker.Mock(identifier="_" + _id)
        for _id in identifiers
    }

    nodes = [
        mocker.Mock(identifier=_id, package=package_mapping[_id])
        for _id in identifiers
    ]
    mocked_graph.nodes.return_value = nodes

    result = wiz.graph.extract_ordered_packages(mocked_graph, distance_mapping)
    assert result == [package_mapping[_id] for _id in expected]


def test_graph_node():
    """Return node from graph via identifier."""
    graph = wiz.graph.Graph(None)
    graph._node_mapping = {"A": "_nodeA"}

    assert graph.node("A") == "_nodeA"
    assert graph.node("B") is None


def test_graph_nodes():
    """Return nodes from graph."""
    graph = wiz.graph.Graph(None)
    graph._node_mapping = {"A": "_nodeA", "B": "_nodeB", "C": "_nodeC"}

    assert sorted(graph.nodes()) == ["_nodeA", "_nodeB", "_nodeC"]


def test_graph_exists():
    """Indicate whether node exists in graph."""
    graph = wiz.graph.Graph(None)
    graph._node_mapping = {"A": "_nodeA"}

    assert graph.exists("A") is True
    assert graph.exists("B") is False


def test_graph_variant_mapping(mocker):
    """Extract variants from graph."""
    graph = wiz.graph.Graph(None)
    assert graph.variant_mapping() == {}

    graph = wiz.graph.Graph(None)
    graph._node_mapping = {
        "A[V1]==0.1.0": mocker.Mock(variant_name="V1"),
        "A[V2]==0.1.0": mocker.Mock(variant_name="V2"),
        "B[V1]==0.1.0": mocker.Mock(variant_name="V1"),
        "B[V1]==0.2.0": mocker.Mock(variant_name="V1"),
        "B[V2]==0.1.0": mocker.Mock(variant_name="V2"),
        "C[V1]==0.1.0": mocker.Mock(variant_name="V1"),
        "D[V1]==0.1.0": mocker.Mock(variant_name="V1"),
        "D[V1]==0.2.0": mocker.Mock(variant_name="V1")
    }
    graph._variants_per_definition = {
        "A": ["A[V1]==0.1.0", "A[V2]==0.1.0"],
        "B": ["B[V1]==0.1.0", "B[V2]==0.1.0", "B[V1]==0.2.0"],
        "C": ["C[V1]==0.1.0"],
        "D": ["D[V1]==0.1.0", "D[V1]==0.2.0"]
    }
    assert graph.variant_mapping() == {
        "A": ["A[V1]==0.1.0", "A[V2]==0.1.0"],
        "B": ["B[V1]==0.1.0", "B[V2]==0.1.0", "B[V1]==0.2.0"]
    }


def test_graph_outcoming():
    """Fetch outcoming nodes from node identifier."""
    graph = wiz.graph.Graph(None)
    assert graph.outcoming("A") == []

    graph = wiz.graph.Graph(None)
    graph._link_mapping = {"A": {"B": "LINK"}}
    assert graph.outcoming("A") == []

    graph = wiz.graph.Graph(None)
    graph._node_mapping = {"A": "_A"}
    graph._link_mapping = {"A": {"B": "LINK"}}
    assert graph.outcoming("A") == []

    graph = wiz.graph.Graph(None)
    graph._node_mapping = {"A": "_A", "B": "_B"}
    graph._link_mapping = {"A": {"B": "LINK"}}
    assert graph.outcoming("A") == ["B"]


def test_graph_link_weight():
    """Fetch weight from nodes link."""
    graph = wiz.graph.Graph(None)
    graph._link_mapping = {
        "A": {
            "B": {"requirement": Requirement("A"), "weight": 3},
            "C": {"requirement": Requirement("A>2"), "weight": 2}
        }
    }
    assert graph.link_weight("B", "A") == 3
    assert graph.link_weight("C", "A") == 2


def test_graph_requirement_weight():
    """Fetch requirement from nodes link."""
    requirements = [
        Requirement("A"), Requirement("A>2")
    ]

    graph = wiz.graph.Graph(None)
    graph._link_mapping = {
        "A": {
            "B": {"requirement": requirements[0], "weight": 3},
            "C": {"requirement": requirements[1], "weight": 2}
        }
    }

    assert graph.link_requirement("B", "A") == requirements[0]
    assert graph.link_requirement("C", "A") == requirements[1]


@pytest.mark.parametrize("definition_mapping, node_mapping, expected", [
    (
        {"defA": ["nodeA"], "defB": ["nodeB"]},
        {"nodeA": "_nodeA", "nodeB": "_nodeB"},
        []
    ),
    (
        {"defA": ["nodeA1", "nodeA2"], "defB": ["nodeB"]},
        {"nodeA1": "_nodeA1", "nodeA2": "_nodeA2", "nodeB": "_nodeB"},
        ["nodeA1", "nodeA2"]
    ),
    (
        {"defA": ["nodeA1", "nodeA2"], "defB": ["nodeB"]},
        {"nodeA1": "_nodeA1", "nodeB": "_nodeB"},
        []
    )
], ids=[
    "without-conflicts",
    "with-two-conflicts",
    "with-conflicting-node-removed"
])
def test_graph_conflicts(definition_mapping, node_mapping, expected):
    """Extract conflicting nodes from graph."""
    graph = wiz.graph.Graph(None)
    graph._node_mapping = node_mapping
    graph._identifiers_per_definition = definition_mapping

    assert graph.conflicts() == expected


def test_graph_update_from_requirements(
    mocked_resolver, mocked_package_extract
):
    """Update graph from requirements."""
    graph = wiz.graph.Graph(mocked_resolver)

    _mapping = {
        "A==0.2.0": wiz.package.Package({
            "identifier": "A==0.2.0",
            "definition-identifier": "A"
        }),
        "B==2.1.1": wiz.package.Package({
            "identifier": "B==2.1.1",
            "definition-identifier": "B"
        }),
    }

    mocked_package_extract.side_effect = [
        [_mapping["A==0.2.0"]],
        [_mapping["B==2.1.1"]]
    ]

    graph.update_from_requirements([Requirement("A"), Requirement("B>=2")])

    assert graph.to_dict() == {
        "identifier": mock.ANY,
        "node_mapping": {
            "A==0.2.0": {
                "package": {
                    "identifier": "A==0.2.0",
                    "definition-identifier": "A"
                },
                "parents": ["root"]
            },
            "B==2.1.1": {
                "package": {
                    "identifier": "B==2.1.1",
                    "definition-identifier": "B"
                },
                "parents": ["root"]
            }
        },
        "link_mapping": {
            "root": {
                "A==0.2.0": {"requirement": Requirement("A"), "weight": 1},
                "B==2.1.1": {"requirement": Requirement("B >=2"), "weight": 2}
            }
        },
        "identifiers_per_definition": {
            "A": ["A==0.2.0"],
            "B": ["B==2.1.1"],
        },
        "variants_per_definition": {},
        "constraint_mapping": {},
        "condition_mapping": {}
    }


def test_graph_update_from_requirements_with_dependencies(
    mocked_resolver, mocked_package_extract
):
    """Update graph from requirements with dependency requirements."""
    graph = wiz.graph.Graph(mocked_resolver)

    _mapping = {
        "A==0.1.0": wiz.package.Package({
            "identifier": "A==0.1.0",
            "definition-identifier": "A",
            "requirements": [Requirement("B>=2"), Requirement("C")],
        }),
        "B==3.0.0": wiz.package.Package({
            "identifier": "B==3.0.0",
            "definition-identifier": "B",
        }),
        "C==1.2.3": wiz.package.Package({
            "identifier": "C==1.2.3",
            "definition-identifier": "C",
            "requirements": [Requirement("D")],
        }),
        "D==0.1.0": wiz.package.Package({
            "identifier": "D==0.1.0",
            "definition-identifier": "D",
            "requirements": [Requirement("E")],
        }),
        "E==0.2.0": wiz.package.Package({
            "identifier": "E==0.2.0",
            "definition-identifier": "E",
        }),
    }

    mocked_package_extract.side_effect = [
        [_mapping["A==0.1.0"]],
        [_mapping["B==3.0.0"]],
        [_mapping["C==1.2.3"]],
        [_mapping["D==0.1.0"]],
        [_mapping["E==0.2.0"]],
    ]

    graph.update_from_requirements([Requirement("A")])

    assert graph.to_dict() == {
        "identifier": mock.ANY,
        "node_mapping": {
            "A==0.1.0": {
                "package": {
                    "identifier": "A==0.1.0",
                    "definition-identifier": "A",
                    "requirements": ["B >=2", "C"],
                },
                "parents": ["root"]
            },
            "B==3.0.0": {
                "package": {
                    "identifier": "B==3.0.0",
                    "definition-identifier": "B",
                },
                "parents": ["A==0.1.0"]
            },
            "C==1.2.3": {
                "package": {
                    "identifier": "C==1.2.3",
                    "definition-identifier": "C",
                    "requirements": ["D"],
                },
                "parents": ["A==0.1.0"]
            },
            "D==0.1.0": {
                "package": {
                    "identifier": "D==0.1.0",
                    "definition-identifier": "D",
                    "requirements": ["E"],
                },
                "parents": ["C==1.2.3"]
            },
            "E==0.2.0": {
                "package": {
                    "identifier": "E==0.2.0",
                    "definition-identifier": "E",
                },
                "parents": ["D==0.1.0"]
            }
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("A"), "weight": 1}
            },
            "A==0.1.0": {
                "B==3.0.0": {"requirement": Requirement("B>=2"), "weight": 1},
                "C==1.2.3": {"requirement": Requirement("C"), "weight": 2}
            },
            "C==1.2.3": {
                "D==0.1.0": {"requirement": Requirement("D"), "weight": 1},
            },
            "D==0.1.0": {
                "E==0.2.0": {"requirement": Requirement("E"), "weight": 1},
            }
        },
        "identifiers_per_definition": {
            "A": ["A==0.1.0"],
            "B": ["B==3.0.0"],
            "C": ["C==1.2.3"],
            "D": ["D==0.1.0"],
            "E": ["E==0.2.0"]
        },
        "variants_per_definition": {},
        "constraint_mapping": {},
        "condition_mapping": {}
    }


def test_graph_update_from_requirements_with_variants(
    mocked_resolver, mocked_package_extract
):
    """Update graph from requirements with variants of definition."""
    graph = wiz.graph.Graph(mocked_resolver)

    _mapping = {
        "A[V1]==0.2.0": wiz.package.Package({
            "identifier": "A[V1]==0.2.0",
            "variant-name": "V1",
            "definition-identifier": "A",
        }),
        "A[V2]==0.2.0": wiz.package.Package({
            "identifier": "A[V2]==0.2.0",
            "variant-name": "V2",
            "definition-identifier": "A",
        }),
        "A[V3]==0.2.0": wiz.package.Package({
            "identifier": "A[V3]==0.2.0",
            "variant-name": "V3",
            "definition-identifier": "A",
        }),
    }

    mocked_package_extract.side_effect = [
        [
            _mapping["A[V1]==0.2.0"],
            _mapping["A[V2]==0.2.0"],
            _mapping["A[V3]==0.2.0"],
        ],
    ]

    graph.update_from_requirements([Requirement("A")])

    assert graph.to_dict() == {
        "identifier": mock.ANY,
        "node_mapping": {
            "A[V1]==0.2.0": {
                "package": {
                    "identifier": "A[V1]==0.2.0",
                    "variant-name": "V1",
                    "definition-identifier": "A",
                },
                "parents": ["root"]
            },
            "A[V2]==0.2.0": {
                "package": {
                    "identifier": "A[V2]==0.2.0",
                    "variant-name": "V2",
                    "definition-identifier": "A",
                },
                "parents": ["root"]
            },
            "A[V3]==0.2.0": {
                "package": {
                    "identifier": "A[V3]==0.2.0",
                    "variant-name": "V3",
                    "definition-identifier": "A",
                },
                "parents": ["root"]
            },
        },
        "link_mapping": {
            "root": {
                "A[V1]==0.2.0": {"requirement": Requirement("A"), "weight": 1},
                "A[V2]==0.2.0": {"requirement": Requirement("A"), "weight": 1},
                "A[V3]==0.2.0": {"requirement": Requirement("A"), "weight": 1},
            },
        },
        "identifiers_per_definition": {
            "A": ["A[V1]==0.2.0", "A[V2]==0.2.0", "A[V3]==0.2.0"],
        },
        "variants_per_definition": {
            "A": ["A[V1]==0.2.0", "A[V2]==0.2.0", "A[V3]==0.2.0"]
        },
        "constraint_mapping": {},
        "condition_mapping": {}
    }


def test_graph_update_from_requirements_with_unused_constraints(
    mocked_resolver, mocked_package_extract
):
    """Update graph from requirements with un-used package constraints."""
    graph = wiz.graph.Graph(mocked_resolver)

    _mapping = {
        "A==0.2.0": wiz.package.Package({
            "identifier": "A==0.2.0",
            "definition-identifier": "A",
        }),
        "B==2.1.1": wiz.package.Package({
            "identifier": "B==2.1.1",
            "definition-identifier": "B",
            "constraints": [Requirement("C==2.0.4")],
        }),
    }

    mocked_package_extract.side_effect = [
        [_mapping["A==0.2.0"]],
        [_mapping["B==2.1.1"]]
    ]

    graph.update_from_requirements([Requirement("A"), Requirement("B>=2")])

    assert graph.to_dict() == {
        "identifier": mock.ANY,
        "node_mapping": {
            "A==0.2.0": {
                "package": {
                    "identifier": "A==0.2.0",
                    "definition-identifier": "A",
                },
                "parents": ["root"]
            },
            "B==2.1.1": {
                "package": {
                    "identifier": "B==2.1.1",
                    "definition-identifier": "B",
                    "constraints": ["C ==2.0.4"],
                },
                "parents": ["root"]
            }
        },
        "link_mapping": {
            "root": {
                "A==0.2.0": {"requirement": Requirement("A"), "weight": 1},
                "B==2.1.1": {"requirement": Requirement("B >=2"), "weight": 2}
            }
        },
        "identifiers_per_definition": {
            "A": ["A==0.2.0"],
            "B": ["B==2.1.1"],
        },
        "constraint_mapping": {
            "C": [
                {
                    "requirement": Requirement("C==2.0.4"),
                    "package": None,
                    "parent_identifier": "B==2.1.1",
                    "weight": 1
                }
            ]
        },
        "condition_mapping": {},
        "variants_per_definition": {}
    }


def test_graph_update_from_requirements_with_used_constraints(
    mocked_resolver, mocked_package_extract
):
    """Update graph from requirements with used package constraints."""
    graph = wiz.graph.Graph(mocked_resolver)

    _mapping = {
        "A==0.2.0": wiz.package.Package({
            "identifier": "A==0.2.0",
            "definition-identifier": "A",
        }),
        "B==2.1.1": wiz.package.Package({
            "identifier": "B==2.1.1",
            "definition-identifier": "B",
            "constraints": [Requirement("C==2.0.4")],
        }),
        "C==2.0.4": wiz.package.Package({
            "identifier": "C==2.0.4",
            "definition-identifier": "C",
        }),
        "C==3.0.0": wiz.package.Package({
            "identifier": "C==3.0.0",
            "definition-identifier": "C",
        }),
    }

    mocked_package_extract.side_effect = [
        [_mapping["A==0.2.0"]],
        [_mapping["B==2.1.1"]],
        [_mapping["C==3.0.0"]],
        [_mapping["C==2.0.4"]]
    ]

    graph.update_from_requirements([
        Requirement("A"), Requirement("B>=2"), Requirement("C")
    ])

    assert graph.to_dict() == {
        "identifier": mock.ANY,
        "node_mapping": {
            "A==0.2.0": {
                "package": {
                    "identifier": "A==0.2.0",
                    "definition-identifier": "A",
                },
                "parents": ["root"]
            },
            "B==2.1.1": {
                "package": {
                    "identifier": "B==2.1.1",
                    "definition-identifier": "B",
                    "constraints": ["C ==2.0.4"],
                },
                "parents": ["root"]
            },
            "C==2.0.4": {
                "package": {
                    "identifier": "C==2.0.4",
                    "definition-identifier": "C",
                },
                "parents": ["B==2.1.1"]
            },
            "C==3.0.0": {
                "package": {
                    "identifier": "C==3.0.0",
                    "definition-identifier": "C",
                },
                "parents": ["root"]
            }
        },
        "link_mapping": {
            "root": {
                "A==0.2.0": {"requirement": Requirement("A"), "weight": 1},
                "B==2.1.1": {"requirement": Requirement("B >=2"), "weight": 2},
                "C==3.0.0": {"requirement": Requirement("C"), "weight": 3}
            },
            "B==2.1.1": {
                "C==2.0.4": {
                    "requirement": Requirement("C==2.0.4"), "weight": 1
                },
            }
        },
        "identifiers_per_definition": {
            "A": ["A==0.2.0"],
            "B": ["B==2.1.1"],
            "C": ["C==2.0.4", "C==3.0.0"]
        },
        "constraint_mapping": {},
        "condition_mapping": {},
        "variants_per_definition": {},
    }


def test_graph_update_from_requirements_with_skipped_conditional_packages(
    mocked_resolver, mocked_package_extract
):
    """Update graph from requirements with skipped conditional packages."""
    graph = wiz.graph.Graph(mocked_resolver)

    _mapping = {
        "A==0.2.0": wiz.package.Package({
            "identifier": "A==0.2.0",
            "definition-identifier": "A",
        }),
        "B==2.1.1": wiz.package.Package({
            "identifier": "B==2.1.1",
            "definition-identifier": "B",
            "conditions": [Requirement("C > 2")]
        }),
        "C==2.0.4": wiz.package.Package({
            "identifier": "C==2.0.4",
            "definition-identifier": "C",
        }),
    }

    mocked_package_extract.side_effect = [
        [_mapping["A==0.2.0"]],
        [_mapping["B==2.1.1"]],
        # Extract conditional package
        [_mapping["C==2.0.4"]]
    ]

    graph.update_from_requirements([Requirement("A"), Requirement("B>=2")])

    assert graph.to_dict() == {
        "identifier": mock.ANY,
        "node_mapping": {
            "A==0.2.0": {
                "package": {
                    "identifier": "A==0.2.0",
                    "definition-identifier": "A",
                },
                "parents": ["root"]
            }
        },
        "link_mapping": {
            "root": {
                "A==0.2.0": {"requirement": Requirement("A"), "weight": 1}
            }
        },
        "identifiers_per_definition": {
            "A": ["A==0.2.0"]
        },
        "constraint_mapping": {},
        "condition_mapping": {
            ("C >2",): {
                "requirement": Requirement("B >=2"),
                "package": mock.ANY,
                "parent_identifier": None,
                "weight": 2
            }
        },
        "variants_per_definition": {}
    }


def test_graph_update_from_requirements_with_used_conditional_packages(
    mocked_resolver, mocked_package_extract
):
    """Update graph from requirements with used conditional packages."""
    graph = wiz.graph.Graph(mocked_resolver)

    _mapping = {
        "A==0.2.0": wiz.package.Package({
            "identifier": "A==0.2.0",
            "definition-identifier": "A"
        }),
        "B==2.1.1": wiz.package.Package({
            "identifier": "B==2.1.1",
            "definition-identifier": "B",
            "conditions": [Requirement("A")],
        })
    }

    mocked_package_extract.side_effect = [
        [_mapping["A==0.2.0"]],
        [_mapping["B==2.1.1"]],
        # Extract package from condition
        [_mapping["A==0.2.0"]]
    ]

    graph.update_from_requirements([Requirement("A"), Requirement("B>=2")])

    assert graph.to_dict() == {
        "identifier": mock.ANY,
        "node_mapping": {
            "A==0.2.0": {
                "package": {
                    "identifier": "A==0.2.0",
                    "definition-identifier": "A"
                },
                "parents": ["root"]
            },
            "B==2.1.1": {
                "package": {
                    "identifier": "B==2.1.1",
                    "definition-identifier": "B",
                    "conditioned-by": ["A==0.2.0"],
                },
                "parents": ["root"]
            }
        },
        "link_mapping": {
            "root": {
                "A==0.2.0": {"requirement": Requirement("A"), "weight": 1},
                "B==2.1.1": {"requirement": Requirement("B >=2"), "weight": 2}
            }
        },
        "identifiers_per_definition": {
            "A": ["A==0.2.0"],
            "B": ["B==2.1.1"]
        },
        "constraint_mapping": {},
        "condition_mapping": {},
        "variants_per_definition": {}
    }


@pytest.mark.parametrize("options", [
    {},
    {"parent_identifier": "foo"},
    {"weight": 5},
    {"parent_identifier": "bar", "weight": 42}
], ids=[
    "simple",
    "with-parent",
    "with-weight",
    "with-parent-and-weight",
])
def test_graph_update_from_requirement_existing(
    mocker, mocked_resolver, mocked_package_extract, mocked_queue, options
):
    """Update graph from requirement."""
    package = wiz.package.Package(identifier="A==0.1.0")
    node = mocker.Mock(identifier="_A==0.1.0")
    requirement = Requirement("A")

    mocked_package_extract.return_value = [package]

    graph = wiz.graph.Graph(mocked_resolver)
    graph.create_link = mocker.Mock()
    graph._create_node_from_package = mocker.Mock()
    graph._node_mapping = {"A==0.1.0": node}
    graph.exists = mocker.Mock(return_value=True)

    graph._update_from_requirement(requirement, mocked_queue, **options)

    graph._create_node_from_package.assert_not_called()
    graph.create_link.assert_called_once_with(
        "_A==0.1.0",
        options.get("parent_identifier", "root"),
        requirement,
        weight=options.get("weight", 1)
    )

    node.add_parent.assert_called_once_with(
        options.get("parent_identifier", "root")
    )

    mocked_queue.put.assert_not_called()


@pytest.mark.parametrize("options", [
    {},
    {"parent_identifier": "foo"},
    {"weight": 5},
    {"parent_identifier": "bar", "weight": 42}
], ids=[
    "simple",
    "with-parent",
    "with-weight",
    "with-parent-and-weight",
])
def test_graph_update_from_requirement_non_existing(
    mocker, mocked_resolver, mocked_package_extract, mocked_queue, options
):
    """Update graph from requirement."""
    package = wiz.package.Package(identifier="A==0.1.0")
    node = mocker.Mock(identifier="_A==0.1.0")
    requirement = Requirement("A")

    mocked_package_extract.return_value = [package]

    graph = wiz.graph.Graph(mocked_resolver)
    graph.create_link = mocker.Mock()
    graph._create_node_from_package = mocker.Mock()
    graph._node_mapping = {"A==0.1.0": node}
    graph.exists = mocker.Mock(return_value=False)

    graph._update_from_requirement(requirement, mocked_queue, **options)

    graph._create_node_from_package.assert_called_once_with(package)
    graph.create_link.assert_called_once_with(
        "_A==0.1.0",
        options.get("parent_identifier", "root"),
        requirement,
        weight=options.get("weight", 1)
    )

    node.add_parent.assert_called_once_with(
        options.get("parent_identifier", "root")
    )

    mocked_queue.put.assert_not_called()


@pytest.mark.parametrize("options", [
    {},
    {"parent_identifier": "foo"},
    {"weight": 5},
    {"parent_identifier": "bar", "weight": 42}
], ids=[
    "simple",
    "with-parent",
    "with-weight",
    "with-parent-and-weight",
])
def test_graph_update_from_requirement_non_existing_with_requirements(
    mocker, mocked_resolver, mocked_package_extract, mocked_queue, options
):
    """Update graph from requirement."""
    package = wiz.package.Package(
        identifier="A==0.1.0",
        requirements=[
            Requirement("B"),
            Requirement("C"),
            Requirement("D")
        ],
    )
    node = mocker.Mock(identifier="_A==0.1.0")
    requirement = Requirement("A")

    mocked_package_extract.return_value = [package]

    graph = wiz.graph.Graph(mocked_resolver)
    graph.create_link = mocker.Mock()
    graph._create_node_from_package = mocker.Mock()
    graph._node_mapping = {"A==0.1.0": node}
    graph.exists = mocker.Mock(return_value=False)

    graph._update_from_requirement(requirement, mocked_queue, **options)

    graph._create_node_from_package.assert_called_once_with(package)
    graph.create_link.assert_called_once_with(
        "_A==0.1.0",
        options.get("parent_identifier", "root"),
        requirement,
        weight=options.get("weight", 1)
    )

    node.add_parent.assert_called_once_with(
        options.get("parent_identifier", "root")
    )

    assert mocked_queue.put.call_count == 3
    mocked_queue.put.assert_any_call({
        "requirement": Requirement("B"),
        "parent_identifier": "A==0.1.0",
        "weight": 1
    })
    mocked_queue.put.assert_any_call({
        "requirement": Requirement("C"),
        "parent_identifier": "A==0.1.0",
        "weight": 2
    })
    mocked_queue.put.assert_any_call({
        "requirement": Requirement("D"),
        "parent_identifier": "A==0.1.0",
        "weight": 3
    })


@pytest.mark.parametrize("options", [
    {},
    {"parent_identifier": "foo"},
    {"weight": 5},
    {"parent_identifier": "bar", "weight": 42}
], ids=[
    "simple",
    "with-parent",
    "with-weight",
    "with-parent-and-weight",
])
def test_graph_update_from_requirement_multi_packages(
    mocker, mocked_resolver, mocked_package_extract, mocked_queue, options
):
    """Update graph from requirement."""
    packages = [
        wiz.package.Package(identifier="A[variant1]==0.1.0"),
        wiz.package.Package(identifier="A[variant2]==0.1.0"),
        wiz.package.Package(identifier="A[variant3]==0.1.0")
    ]

    nodes = [
        mocker.Mock(identifier="_A[variant1]==0.1.0"),
        mocker.Mock(identifier="_A[variant2]==0.1.0"),
        mocker.Mock(identifier="_A[variant3]==0.1.0"),
    ]

    requirement = Requirement("A")

    mocked_package_extract.return_value = packages

    graph = wiz.graph.Graph(mocked_resolver)
    graph.create_link = mocker.Mock()
    graph._create_node_from_package = mocker.Mock()
    graph._node_mapping = {
        "A[variant1]==0.1.0": nodes[0],
        "A[variant2]==0.1.0": nodes[1],
        "A[variant3]==0.1.0": nodes[2]
    }
    graph.exists = mocker.Mock(return_value=False)

    graph._update_from_requirement(requirement, mocked_queue, **options)

    assert graph._create_node_from_package.call_count == 3
    for package in packages:
        graph._create_node_from_package.assert_any_call(package)

    assert graph.create_link.call_count == 3
    for node in nodes:
        graph.create_link.assert_any_call(
            node.identifier,
            options.get("parent_identifier", "root"),
            requirement,
            weight=options.get("weight", 1)
        )

    for node in nodes:
        node.add_parent.assert_called_once_with(
            options.get("parent_identifier", "root")
        )

    mocked_queue.put.assert_not_called()


def test_graph_create_node_from_package():
    """Create node in graph from package."""
    package = wiz.package.Package({
        "identifier": "A==0.1.0",
        "definition-identifier": "defA"
    })

    graph = wiz.graph.Graph(None)
    graph._create_node_from_package(package)

    assert graph._identifiers_per_definition == {"defA": {"A==0.1.0"}}
    assert graph._node_mapping.keys() == ["A==0.1.0"]
    assert isinstance(graph._node_mapping["A==0.1.0"], wiz.graph.Node)


@pytest.mark.parametrize("options", [
    {},
    {"weight": 5},
], ids=[
    "simple",
    "with-weight",
])
def test_graph_create_link(options):
    """Create link between two nodes."""
    requirement = Requirement("A")

    graph = wiz.graph.Graph(None)
    graph.create_link("child", "parent", requirement, **options)

    assert graph._link_mapping == {
        "parent": {
            "child": {
                "requirement": requirement,
                "weight": options.get("weight", 1)
            }
        }
    }


def test_graph_create_link_error():
    """Fail to create link between two nodes when one already exists."""
    requirement = Requirement("A")

    graph = wiz.graph.Graph(None)
    graph._link_mapping = {
        "parent": {"child": {"requirement": requirement, "weight": 1}}
    }

    with pytest.raises(wiz.exception.IncorrectDefinition):
        graph.create_link("child", "parent", Requirement("A"))


def test_graph_remove_node():
    """Remove nodes from graph."""
    graph = wiz.graph.Graph(None)
    graph._node_mapping = {"A1": "_A1", "A2": "_A2", "B": "B"}
    graph._identifiers_per_definition = {"defA": ["A1", "A2"], "defB": ["B"]}
    graph._variants_per_definition = {"_id": ["A1", "A2"]}
    graph._link_mapping = {"A1": {"B": "LINK"}}

    graph.remove_node("A1")

    assert graph._node_mapping == {"A2": "_A2", "B": "B"}
    assert graph._identifiers_per_definition == {
        "defA": ["A1", "A2"], "defB": ["B"]
    }
    assert graph._variants_per_definition == {"_id": ["A1", "A2"]}
    assert graph._link_mapping == {"A1": {"B": "LINK"}}


def test_graph_reset_variants():
    """Reset variant groups in graph."""
    graph = wiz.graph.Graph(None)
    graph._variants_per_definition = {"_id": ["A1", "A2"]}
    assert graph._variants_per_definition == {"_id": ["A1", "A2"]}

    graph.reset_variants()

    assert graph._variants_per_definition == {}


def test_node():
    """Create and use node."""
    package = wiz.package.Package({
        "identifier": "A[V1]==0.1.0",
        "variant-name": "V1",
        "definition-identifier": "defA"
    })

    node = wiz.graph.Node(package)
    assert node.identifier == "A[V1]==0.1.0"
    assert node.definition == "defA"
    assert node.variant_name == "V1"
    assert node.package == package
    assert node.parent_identifiers == set()

    node.add_parent("parent1")
    node.add_parent("parent1")
    node.add_parent("parent2")

    assert node.parent_identifiers == {"parent1", "parent2"}


def test_distance_queue():
    """Create and use distance queue."""
    queue = wiz.graph._DistanceQueue()
    assert queue.empty() is True

    # Add element to the queue. This will also be pushed to the heap.
    queue["A"] = 2
    queue["B"] = 1
    queue["C"] = 4
    queue["D"] = 3
    queue["E"] = 6
    queue["F"] = 5
    assert len(queue) == 6
    assert len(queue._heap) == 6
    assert queue.empty() is False

    # Modify all elements. This will override the dictionary items, but
    # it will be pushed to the heap and double its size.
    queue["A"] = 20
    queue["B"] = 10
    queue["C"] = 40
    queue["D"] = 30
    queue["E"] = 60
    queue["F"] = 50
    assert len(queue) == 6
    assert len(queue._heap) == 12

    # By asking the smallest item, half of the heap need to be "popped" as
    # The smallest element is 1 from a previous version of "B". It will then
    # check all elements from the heap until one that also exist in the
    # dictionary is found.
    assert queue.pop_smallest() == "B"
    assert len(queue) == 5
    assert len(queue._heap) == 5

    queue["A"] = 200
    queue["C"] = 400
    queue["D"] = 300
    queue["E"] = 600
    queue["F"] = 500
    assert len(queue) == 5
    assert len(queue._heap) == 10

    # Augment the heap so that it get more than twice the size of the
    # dictionary to force a rebuild.
    queue["A"] = 2000
    assert len(queue) == 5
    assert len(queue._heap) == 5

    # Empty the dictionary.
    assert queue.pop_smallest() == "D"
    assert queue.pop_smallest() == "C"
    assert queue.pop_smallest() == "F"
    assert queue.pop_smallest() == "E"
    assert queue.pop_smallest() == "A"
    assert queue.empty() is True
