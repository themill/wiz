# :coding: utf-8

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

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
        {"root": {"priority": 0, "parent": "root"}}
    ),
    (
        {"root": ["A"], "A": []},
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"}
        }
    ),
    (
        {"root": ["A", "B"], "A": [], "B": []},
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "root"}
        }
    ),
    (
        {"root": ["A", "B", "C"], "A": [], "B": [], "C": []},
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "root"},
            "C": {"priority": 3, "parent": "root"}
        }
    ),
    (
        {"root": ["A"], "A": ["B"], "B": []},
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "A"}
        }
    ),
    (
        {"root": ["A"], "A": ["B"], "B": ["C"], "C": []},
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "A"},
            "C": {"priority": 3, "parent": "B"}
        }
    ),
    (
        {"root": ["A", "B"], "A": ["B"], "B": ["A"]},
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "root"}
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
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "root"},
            "C": {"priority": 2, "parent": "A"},
            "D": {"priority": 3, "parent": "A"},
            "E": {"priority": 4, "parent": "D"},
            "F": {"priority": 4, "parent": "B"},
            "G": {"priority": 5, "parent": "B"},
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
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": None, "parent": None},
            "C": {"priority": 2, "parent": "A"},
            "D": {"priority": None, "parent": None},
            "E": {"priority": 3, "parent": "A"},
            "F": {"priority": 4, "parent": "A"},
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
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "root"},
            "C": {"priority": 2, "parent": "A"},
            "D": {"priority": 3, "parent": "A"},
            "E": {"priority": 4, "parent": "D"},
            "F": {"priority": 3, "parent": "root"},
            "G": {"priority": 3, "parent": "C"},
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
def test_compute_priority_mapping(mocker, mocked_graph, mapping, expected):
    """Compute priority mapping from Graph."""
    nodes = [mocker.Mock(identifier=_id) for _id in mapping.keys()]
    mocked_graph.nodes.return_value = nodes
    mocked_graph.outcoming = lambda x: mapping[x]
    mocked_graph.link_weight = lambda x, y: mapping[y].index(x) + 1
    assert wiz.graph.compute_priority_mapping(mocked_graph) == expected


def test_trim_unreachable_from_graph(
    mocker, mocked_graph, mocked_graph_remove_node
):
    """Remove unreachable nodes from graph based on priority mapping."""
    identifiers = ["A", "B", "C", "D", "E", "F"]
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    priority_mapping = {
        "root": {"priority": 0, "parent": "root"},
        "A": {"priority": 1, "parent": "root"},
        "B": {"priority": None, "parent": None},
        "C": {"priority": 2, "parent": "A"},
        "D": {"priority": None, "parent": None},
        "E": {"priority": 3, "parent": "A"},
        "F": {"priority": 4, "parent": "A"},
    }

    wiz.graph.trim_unreachable_from_graph(mocked_graph, priority_mapping)

    assert mocked_graph_remove_node.call_count == 2
    mocked_graph_remove_node.assert_any_call("B")
    mocked_graph_remove_node.assert_any_call("D")


def test_sorted_from_priority():
    """Sort node based on priority mapping."""
    identifiers = ["F", "E", "D", "C", "B", "A"]

    priority_mapping = {
        "root": {"priority": 0, "parent": "root"},
        "A": {"priority": 1, "parent": "root"},
        "B": {"priority": None, "parent": None},
        "C": {"priority": 2, "parent": "A"},
        "D": {"priority": None, "parent": None},
        "E": {"priority": 3, "parent": "A"},
        "F": {"priority": 4, "parent": "A"},
    }

    result = wiz.graph.sorted_from_priority(identifiers, priority_mapping)
    assert result == ["A", "C", "E", "F"]


def test_extract_conflicted_nodes(mocker, mocked_graph):
    """Extract conflicted nodes for a specific node."""
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

    assert wiz.graph.extract_conflicted_nodes(
        mocked_graph, node_mapping["F"]
    ) == [node_mapping["D"], node_mapping["E"]]

    assert wiz.graph.extract_conflicted_nodes(
        mocked_graph, node_mapping["E"]
    ) == [node_mapping["D"], node_mapping["F"]]

    assert wiz.graph.extract_conflicted_nodes(
        mocked_graph, node_mapping["C"]
    ) == [node_mapping["A"], node_mapping["B"]]


@pytest.mark.parametrize("mapping, conflict_mappings, error", [
    (
        {"_ver": Version("1.1.0"), "_req": {Requirement("A"): "B"}},
        [
            {"_ver": Version("1.1.0"), "_req": {Requirement("A>1"): "C"}},
            {"_ver": Version("1.1.0"), "_req": {Requirement("A==1.1.0"): "D"}},
        ],
        None
    ),
    (
        {"_ver": "unknown", "_req": {Requirement("A"): "B"}},
        [
            {"_ver": "unknown", "_req": {Requirement("A"): "C"}},
            {"_ver": "unknown", "_req": {Requirement("A"): "D"}},
        ],
        None
    ),
    (
        {"_ver": Version("1.1.1"), "_req": {Requirement("A == 1.1.1"): "B"}},
        [
            {"_ver": Version("1.1.0"), "_req": {Requirement("A>1"): "C"}},
            {"_ver": Version("1.1.0"), "_req": {Requirement("A==1.1.0"): "D"}},
        ],
        wiz.exception.GraphResolutionError
    ),
    (
        {"_ver": Version("1.1.0"), "_req": {Requirement("A"): "B"}},
        [
            {"_ver": Version("1.1.0"), "_req": {Requirement("A[var]"): "C"}},
            {"_ver": Version("1.1.0"), "_req": {Requirement("A==1.1.0"): "D"}},
        ],
        wiz.exception.GraphResolutionError
    ),
], ids=[
    "without-conflicts",
    "with-no-version",
    "with-version-conflict",
    "with-extra-conflict",
])
def test_validate_requirements(
    mocker, mocked_extract_requirement, mapping, conflict_mappings, error
):
    """Validate node requirements with other nodes in graph."""
    node = mocker.Mock(
        package=mocker.Mock(identifier="A", version=mapping["_ver"])
    )

    conflicted_nodes = [
        mocker.Mock(package=mocker.Mock(version=_mapping["_ver"]))
        for _mapping in conflict_mappings
    ]

    mocked_extract_requirement.side_effect = (
        [mapping["_req"]] + [_mapping["_req"] for _mapping in conflict_mappings]
    )

    if error is None:
        wiz.graph.validate_requirements("GRAPH", node, conflicted_nodes)

        assert mocked_extract_requirement.call_count == 3
        mocked_extract_requirement.assert_any_call("GRAPH", node)
        for _node in conflicted_nodes:
            mocked_extract_requirement.assert_any_call("GRAPH", _node)

    else:
        with pytest.raises(error):
            wiz.graph.validate_requirements("GRAPH", node, conflicted_nodes)

        assert mocked_extract_requirement.call_count <= 3
        mocked_extract_requirement.assert_any_call("GRAPH", node)


def test_extract_requirement(mocker, mocked_graph):
    """Extract node requirement mapping."""
    node = mocker.Mock(identifier="A", parent_identifiers=["B", "C"])

    requirements = [
        Requirement("A > 1"),
        Requirement("A == 1.5.0")
    ]

    mocked_graph.node.side_effect = [
        mocker.Mock(identifier="B"),
        mocker.Mock(identifier="C")
    ]

    mocked_graph.link_requirement.side_effect = requirements

    assert wiz.graph.extract_requirement(mocked_graph, node) == {
        requirements[0]: "B",
        requirements[1]: "C"
    }

    assert mocked_graph.link_requirement.call_count == 2
    mocked_graph.link_requirement.assert_any_call("A", "B")
    mocked_graph.link_requirement.assert_any_call("A", "C")


def test_extract_requirement_with_missing_parent(mocker, mocked_graph):
    """Extract node requirement mapping with missing parent."""
    node = mocker.Mock(identifier="A", parent_identifiers=["B", "C"])

    requirements = [
        Requirement("A > 1"),
        Requirement("A == 1.5.0")
    ]

    # The node B doesn't exist in the graph.
    mocked_graph.node.side_effect = [
        None, mocker.Mock(identifier="C")
    ]

    mocked_graph.link_requirement.side_effect = requirements[1:]

    assert wiz.graph.extract_requirement(mocked_graph, node) == {
        requirements[1]: "C"
    }

    assert mocked_graph.link_requirement.call_count == 1
    mocked_graph.link_requirement.assert_any_call("A", "C")


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

    priority_mapping = {
        "A==3": {"priority": 1, "parent": "B"},
        "A==1.9": {"priority": 2, "parent": "C"},
        "A==1.2.3": {"priority": 3, "parent": "D"},
    }

    mocked_graph.link_requirement.side_effect = requirements

    requirement = wiz.graph.combined_requirements(
        mocked_graph, nodes, priority_mapping
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

    priority_mapping = {
        "A==3": {"priority": 1, "parent": "B"},
        "Z==1.9": {"priority": 2, "parent": "C"},
        "A==1.2.3": {"priority": 3, "parent": "D"},
    }

    mocked_graph.link_requirement.side_effect = requirements

    with pytest.raises(wiz.exception.GraphResolutionError):
        wiz.graph.combined_requirements(
            mocked_graph, nodes, priority_mapping
        )

    assert mocked_graph.link_requirement.call_count == 2
    mocked_graph.link_requirement.assert_any_call("A==3", "B")
    mocked_graph.link_requirement.assert_any_call("Z==1.9", "C")


@pytest.mark.parametrize("identifiers, priority_mapping, expected", [
    (
        [],
        {"root": {"priority": 0, "parent": "root"}},
        []
    ),
    (
        ["A"],
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"}
        },
        ["A"]
    ),
    (
        ["A", "B"],
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "root"}
        },
        ["B", "A"],
    ),
    (
        ["A", "B", "C"],
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "root"},
            "C": {"priority": 3, "parent": "root"}
        },
        ["C", "B", "A"]
    ),
    (
        ["A", "B", "C", "D", "E", "F", "G"],
        {
            "root": {"priority": 0, "parent": "root"},
            "A": {"priority": 1, "parent": "root"},
            "B": {"priority": 2, "parent": "root"},
            "C": {"priority": 2, "parent": "A"},
            "D": {"priority": 3, "parent": "A"},
            "E": {"priority": 4, "parent": "D"},
            "F": {"priority": 4, "parent": "B"},
            "G": {"priority": 5, "parent": "B"},
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
    mocker, mocked_graph, identifiers, priority_mapping, expected
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

    result = wiz.graph.extract_ordered_packages(mocked_graph, priority_mapping)
    assert result == [package_mapping[_id] for _id in expected]


def test_graph_copy():
    """Copy a graph."""
    graph = wiz.graph.Graph(
        "RESOLVER",
        node_mapping={"A1": "_A1", "A2": "_A2", "B": "B"},
        definition_mapping={"defA": ["A1", "A2"], "defB": ["B"]},
        variant_mapping={"_id": ["A1", "A2"]},
        link_mapping={"A1": {"B": "LINK"}}
    )

    _graph = graph.copy()

    assert graph._resolver == _graph._resolver
    assert id(graph._resolver) == id(_graph._resolver)

    assert graph._node_mapping == _graph._node_mapping
    assert id(graph._node_mapping) != id(_graph._node_mapping)

    assert graph._definition_mapping == _graph._definition_mapping
    assert id(graph._definition_mapping) != id(_graph._definition_mapping)

    assert graph._variant_mapping == _graph._variant_mapping
    assert id(graph._variant_mapping) != id(_graph._variant_mapping)

    assert graph._link_mapping == _graph._link_mapping
    assert id(graph._link_mapping) != id(_graph._link_mapping)


def test_graph_node():
    """Return node from graph via identifier."""
    graph = wiz.graph.Graph(
        None, node_mapping={"A": "_nodeA"},
    )

    assert graph.node("A") == "_nodeA"
    assert graph.node("B") is None


def test_graph_nodes():
    """Return nodes from graph."""
    graph = wiz.graph.Graph(
        None, node_mapping={"A": "_nodeA", "B": "_nodeB", "C": "_nodeC"},
    )

    assert sorted(graph.nodes()) == ["_nodeA", "_nodeB", "_nodeC"]


def test_graph_exists():
    """Indicate whether node exists in graph."""
    graph = wiz.graph.Graph(
        None, node_mapping={"A": "_nodeA"},
    )

    assert graph.exists("A") is True
    assert graph.exists("B") is False


def test_graph_variant_groups():
    """Extract variants from graph."""
    graph = wiz.graph.Graph(None)
    assert graph.variant_groups() == []

    graph = wiz.graph.Graph(
        None, variant_mapping={
            "_idA": ["A1", "A2"],
            "_idB": ["B1", "B2"],
        }
    )
    assert sorted(graph.variant_groups()) == [["A1", "A2"], ["B1", "B2"]]


def test_graph_outcoming():
    """Fetch outcoming nodes from node identifier."""
    graph = wiz.graph.Graph(None)
    assert graph.outcoming("A") == []

    graph = wiz.graph.Graph(
        None,
        link_mapping={"A": {"B": "LINK"}}
    )
    assert graph.outcoming("A") == []

    graph = wiz.graph.Graph(
        None,
        node_mapping={"A": "_A"},
        link_mapping={"A": {"B": "LINK"}}
    )
    assert graph.outcoming("A") == []

    graph = wiz.graph.Graph(
        None,
        node_mapping={"A": "_A", "B": "_B"},
        link_mapping={"A": {"B": "LINK"}}
    )
    assert graph.outcoming("A") == ["B"]


def test_graph_link_weight():
    """Fetch weight from nodes link."""
    graph = wiz.graph.Graph(
        None,
        link_mapping={
            "A": {
                "B": {"requirement": Requirement("A"), "weight": 3},
                "C": {"requirement": Requirement("A>2"), "weight": 2}
            }
        }
    )

    assert graph.link_weight("B", "A") == 3
    assert graph.link_weight("C", "A") == 2


def test_graph_requirement_weight():
    """Fetch requirement from nodes link."""
    requirements = [
        Requirement("A"), Requirement("A>2")
    ]

    graph = wiz.graph.Graph(
        None,
        link_mapping={
            "A": {
                "B": {"requirement": requirements[0], "weight": 3},
                "C": {"requirement": requirements[1], "weight": 2}
            }
        }
    )

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
    "with-conflicted-node-removed"
])
def test_graph_conflicts(definition_mapping, node_mapping, expected):
    """Extract conflicted nodes from graph."""
    graph = wiz.graph.Graph(
        None,
        node_mapping=node_mapping,
        definition_mapping=definition_mapping
    )

    assert graph.conflicts() == expected


def test_graph_update_from_requirements(mocker, mocked_queue):
    """Update graph from requirements."""
    graph = wiz.graph.Graph(None)
    graph._update_from_requirement = mocker.Mock()

    requirements = [
        Requirement("A"),
        Requirement("B>=2,<3"),
        Requirement("C==1.2.3")
    ]

    mocked_queue.empty.side_effect = [False, False, False, True]
    mocked_queue.get.side_effect = [
        {"requirement": requirements[0], "weight": 1},
        {"requirement": requirements[1], "weight": 2},
        {"requirement": requirements[2], "weight": 3},
    ]

    graph.update_from_requirements(requirements)

    assert mocked_queue.put.call_count == 3
    assert graph._update_from_requirement.call_count == 3
    graph._update_from_requirement.assert_any_call(
        requirements[0], mocked_queue, parent_identifier=None, weight=1
    )
    graph._update_from_requirement.assert_any_call(
        requirements[1], mocked_queue, parent_identifier=None, weight=2
    )
    graph._update_from_requirement.assert_any_call(
        requirements[2], mocked_queue, parent_identifier=None, weight=3
    )


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
    package = mocker.Mock(identifier="A==0.1.0")
    node = mocker.Mock(identifier="_A==0.1.0")
    requirement = Requirement("A")

    mocked_package_extract.return_value = [package]

    graph = wiz.graph.Graph(mocked_resolver)
    graph.create_link = mocker.Mock()
    graph._create_node_from_package = mocker.Mock()
    graph.node = mocker.Mock(return_value=node)
    graph.exists = mocker.Mock(return_value=True)

    graph._update_from_requirement(requirement, mocked_queue, **options)

    graph._create_node_from_package.assert_not_called()
    graph.create_link.assert_called_once_with(
        "_A==0.1.0",
        options.get("parent_identifier", "root"),
        requirement,
        weight=options.get("weight", 1)
    )

    graph.node.assert_called_once_with("A==0.1.0")
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
    package = mocker.Mock(identifier="A==0.1.0", requirements=[])
    node = mocker.Mock(identifier="_A==0.1.0")
    requirement = Requirement("A")

    mocked_package_extract.return_value = [package]

    graph = wiz.graph.Graph(mocked_resolver)
    graph.create_link = mocker.Mock()
    graph._create_node_from_package = mocker.Mock()
    graph.node = mocker.Mock(return_value=node)
    graph.exists = mocker.Mock(return_value=False)

    graph._update_from_requirement(requirement, mocked_queue, **options)

    graph._create_node_from_package.assert_called_once_with(package)
    graph.create_link.assert_called_once_with(
        "_A==0.1.0",
        options.get("parent_identifier", "root"),
        requirement,
        weight=options.get("weight", 1)
    )

    graph.node.assert_called_once_with("A==0.1.0")
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
    package = mocker.Mock(identifier="A==0.1.0", requirements=["B", "C", "D"])
    node = mocker.Mock(identifier="_A==0.1.0")
    requirement = Requirement("A")

    mocked_package_extract.return_value = [package]

    graph = wiz.graph.Graph(mocked_resolver)
    graph.create_link = mocker.Mock()
    graph._create_node_from_package = mocker.Mock()
    graph.node = mocker.Mock(return_value=node)
    graph.exists = mocker.Mock(return_value=False)

    graph._update_from_requirement(requirement, mocked_queue, **options)

    graph._create_node_from_package.assert_called_once_with(package)
    graph.create_link.assert_called_once_with(
        "_A==0.1.0",
        options.get("parent_identifier", "root"),
        requirement,
        weight=options.get("weight", 1)
    )

    graph.node.assert_called_once_with("A==0.1.0")
    node.add_parent.assert_called_once_with(
        options.get("parent_identifier", "root")
    )

    assert mocked_queue.put.call_count == 3
    mocked_queue.put.assert_any_call({
        "requirement": "B", "parent_identifier": "A==0.1.0", "weight": 1
    })
    mocked_queue.put.assert_any_call({
        "requirement": "C", "parent_identifier": "A==0.1.0", "weight": 2
    })
    mocked_queue.put.assert_any_call({
        "requirement": "D", "parent_identifier": "A==0.1.0", "weight": 3
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
        mocker.Mock(identifier="A[variant1]==0.1.0", requirements=[]),
        mocker.Mock(identifier="A[variant2]==0.1.0", requirements=[]),
        mocker.Mock(identifier="A[variant3]==0.1.0", requirements=[])
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
    graph.node = mocker.Mock(side_effect=nodes)
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

    assert graph.node.call_count == 3
    for package in packages:
        graph.node.assert_any_call(package.identifier)

    for node in nodes:
        node.add_parent.assert_called_once_with(
            options.get("parent_identifier", "root")
        )

    mocked_queue.put.assert_not_called()


def test_graph_create_node_from_package(mocker):
    """Create node in graph from package."""
    package = mocker.Mock(
        identifier="A==0.1.0",
        requirements=[],
        definition_identifier="defA"
    )

    graph = wiz.graph.Graph(None)
    graph._create_node_from_package(package)

    assert graph._definition_mapping == {"defA": {"A==0.1.0"}}
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

    graph = wiz.graph.Graph(
        None, link_mapping={
            "parent": {"child": {"requirement": requirement, "weight": 1}}
        }
    )

    with pytest.raises(wiz.exception.IncorrectDefinition):
        graph.create_link("child", "parent", Requirement("A"))


def test_graph_remove_node():
    """Remove nodes from graph."""
    graph = wiz.graph.Graph(
        None,
        node_mapping={"A1": "_A1", "A2": "_A2", "B": "B"},
        definition_mapping={"defA": ["A1", "A2"], "defB": ["B"]},
        variant_mapping={"_id": ["A1", "A2"]},
        link_mapping={"A1": {"B": "LINK"}}
    )

    graph.remove_node("A1")

    assert graph._node_mapping == {"A2": "_A2", "B": "B"}
    assert graph._definition_mapping == {"defA": ["A1", "A2"], "defB": ["B"]}
    assert graph._variant_mapping == {"_id": ["A1", "A2"]}
    assert graph._link_mapping == {"A1": {"B": "LINK"}}


def test_graph_reset_variants():
    """Reset variant groups in graph."""
    graph = wiz.graph.Graph(
        None,
        variant_mapping={"_id": ["A1", "A2"]},
    )

    assert graph._variant_mapping == {"_id": ["A1", "A2"]}

    graph.reset_variants()

    assert graph._variant_mapping == {}


def test_node(mocker):
    """Create and use node."""
    package = mocker.Mock(
        identifier="A==0.1.0",
        definition_identifier="defA"
    )

    node = wiz.graph.Node(package)
    assert node.identifier == "A==0.1.0"
    assert node.definition == "defA"
    assert node.package == package
    assert node.parent_identifiers == set()

    node.add_parent("parent1")
    node.add_parent("parent1")
    node.add_parent("parent2")

    assert node.parent_identifiers == {"parent1", "parent2"}


def test_priority_queue():
    """Create and use priority queue."""
    queue = wiz.graph._PriorityQueue()
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
