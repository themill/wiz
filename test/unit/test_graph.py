# :coding: utf-8

import collections
import copy
import itertools

import pytest

import wiz.graph
import wiz.package
from wiz.utility import Requirement


@pytest.fixture()
def mocked_resolver(mocker):
    """Return mocked Resolver."""
    return mocker.Mock(definition_mapping={"__namespace__": {}})


@pytest.fixture()
def mocked_graph(mocker):
    """Return mocked Graph."""
    graph = mocker.patch.object(wiz.graph, "Graph")
    graph.ROOT = "root"
    return graph


@pytest.fixture()
def mocked_package_extract(mocker):
    """Return mocked 'wiz.package.extract' function.

    Ensure that 'namespace_counter' option is copied to better analyze state
    evolution.

    .. seealso::

        https://docs.python.org/3/library/unittest.mock-examples.html
        #coping-with-mutable-arguments

    """
    class _MagicMock(mocker.MagicMock):
        """Extended mocker to copy namespace counter on each call."""

        def __call__(self, *args, **kwargs):
            option = kwargs.get("namespace_counter")
            if option is not None:
                kwargs["namespace_counter"] = copy.deepcopy(option)
            return super(_MagicMock, self).__call__(*args, **kwargs)

    return mocker.patch.object(wiz.package, "extract", _MagicMock())


@pytest.fixture()
def packages(request):
    """Returned package mapping for testings"""
    mapping = {
        "single": _simple_package(),
        "single-with-namespace": _simple_package_with_namespace(),
        "many": _several_packages(),
        "many-with-namespaces": _packages_with_namespace(),
        "many-with-conditions": _packages_with_conditions(),
        "conflicting-versions": _packages_with_conflicting_versions(),
        "conflicting-variants": _packages_with_conflicting_variants(),
    }

    return mapping[request.param]


def _simple_package():
    """Create one simple package."""
    return {
        "A==0.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
            }),
        )
    }


def _simple_package_with_namespace():
    """Create one simple package with namespace."""
    return {
        "foo::A==0.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "namespace": "foo",
                "version": "0.1.0",
            }),
        )
    }


def _several_packages():
    """Create several packages with dependencies."""
    return {
        "A==0.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "requirements": ["B"]
            }),
        ),
        "B==1.2.3": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "B",
                "version": "1.2.3",
                "requirements": ["C", "D >1"]
            }),
        ),
        "C": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "C",
            }),
        ),
        "D==4.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "D",
                "version": "4.1.0",
            }),
        ),
    }


def _packages_with_namespace():
    """Create several packages with dependencies and namespaces."""
    return {
        "foo::A==0.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "namespace": "foo",
                "version": "0.1.0",
                "requirements": ["bar::B"]
            }),
        ),
        "bar::B==1.2.3": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "B",
                "namespace": "bar",
                "version": "1.2.3",
                "requirements": ["foo::C", "D >1"]
            }),
        ),
        "foo::C": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "C",
                "namespace": "foo",
            }),
        ),
        "D==4.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "D",
                "version": "4.1.0",
            }),
        ),
    }


def _packages_with_conditions():
    """Create several packages with dependencies and conditions."""
    return {
        "A==0.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "requirements": ["B"],
                "conditions": ["E"]
            }),
        ),
        "B==1.2.3": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "B",
                "version": "1.2.3",
                "requirements": ["C", "D >1"]
            }),
        ),
        "C": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "C",
            }),
        ),
        "D==4.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "D",
                "version": "4.1.0",
            }),
        ),
        "E": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "E",
                "requirements": ["F"],
            }),
        ),
        "F==13": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "F",
                "version": "13",
            }),
        ),
        "G": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "G",
                "conditions": ["F", "D"]
            }),
        ),
        "H": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "H",
                "conditions": ["incorrect"]
            }),
        ),
    }


def _packages_with_conflicting_versions():
    """Create several packages with conflicting versions."""
    return {
        "A==0.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "requirements": ["B"]
            }),
        ),
        "B==1.2.3": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "B",
                "version": "1.2.3",
                "requirements": [
                    "C",
                    "D >= 3, <4"
                ]
            }),
        ),
        "C": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "C",
            }),
        ),
        "D==3.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "D",
                "version": "3.1.0",
            }),
        ),
        "D==3.2.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "D",
                "version": "3.2.0",
            }),
        ),
        "D==4.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "D",
                "version": "4.1.0",
            }),
        )
    }


def _packages_with_conflicting_variants():
    """Create several packages with conflicting variants."""
    definition1 = wiz.definition.Definition({
        "identifier": "A",
        "variants": [
            {"identifier": "V3"},
            {"identifier": "V2"},
            {"identifier": "V1"},
        ]
    })

    definition2 = wiz.definition.Definition({
        "identifier": "B",
        "version": "1.2.3",
        "variants": [
            {"identifier": "V2"},
            {"identifier": "V1"},
        ],
        "requirements": [
            "C",
        ]
    })

    return {
        "A[V3]": wiz.package.Package(
            definition1, variant_index=0
        ),
        "A[V2]": wiz.package.Package(
            definition1, variant_index=1
        ),
        "A[V1]": wiz.package.Package(
            definition1, variant_index=2
        ),
        "B[V2]==1.2.3": wiz.package.Package(
            definition2, variant_index=0
        ),
        "B[V1]==1.2.3": wiz.package.Package(
            definition2, variant_index=1
        ),
        "C": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "C",
            }),
        )
    }


def test_compute_distance_mapping_empty(mocked_graph):
    """Compute distance mapping from empty graph."""
    mocked_graph.outcoming.return_value = []
    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"}
    }


def test_compute_distance_mapping_one_node(mocker, mocked_graph):
    """Compute distance mapping from graph with one node."""
    identifiers = ["root", "A"]
    weights = {"root": {"A": 1}}

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"}
    }


def test_compute_distance_mapping_two_nodes(mocker, mocked_graph):
    """Compute distance mapping from graph with two nodes."""
    identifiers = ["root", "A", "B"]
    weights = {"root": {"A": 1, "B": 2}}

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "root"}
    }


def test_compute_distance_mapping_three_nodes(mocker, mocked_graph):
    """Compute distance mapping from graph with three nodes."""
    identifiers = ["root", "A", "B", "C"]
    weights = {"root": {"A": 1, "B": 2, "C": 3}}

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "root"},
        "C": {"distance": 3, "parent": "root"}
    }


def test_compute_distance_mapping_two_levels(mocker, mocked_graph):
    """Compute distance mapping from graph with two levels of dependency."""
    identifiers = ["root", "A", "B"]
    weights = {"root": {"A": 1}, "A": {"B": 1}}

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "A"}
    }


def test_compute_distance_mapping_three_levels(mocker, mocked_graph):
    """Compute distance mapping from graph with three levels of dependency."""
    identifiers = ["root", "A", "B", "C"]
    weights = {"root": {"A": 1}, "A": {"B": 1}, "B": {"C": 1}}

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "A"},
        "C": {"distance": 3, "parent": "B"}
    }


def test_compute_distance_mapping_circular_dependency(mocker, mocked_graph):
    """Compute distance mapping from graph with circular dependency."""
    identifiers = ["root", "A", "B"]
    weights = {"root": {"A": 1, "B": 2}, "A": {"B": 1}, "B": {"A": 1}}

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "root"}
    }


def test_compute_distance_mapping_multi_levels(mocker, mocked_graph):
    """Compute distance mapping from graph with multi levels of dependency."""
    identifiers = ["root", "A", "B", "C", "D", "E", "F", "G"]
    weights = {
        "root": {"A": 1, "B": 2},
        "A": {"C": 1, "D": 2},
        "B": {"D": 1, "F": 2, "G": 3},
        "D": {"E": 1}
    }

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "root"},
        "C": {"distance": 2, "parent": "A"},
        "D": {"distance": 3, "parent": "A"},
        "E": {"distance": 4, "parent": "D"},
        "F": {"distance": 4, "parent": "B"},
        "G": {"distance": 5, "parent": "B"},
    }


def test_compute_distance_mapping_unreachable_nodes(mocker, mocked_graph):
    """Compute distance mapping from graph with unreachable nodes."""
    identifiers = ["root", "A", "B", "C", "D", "E", "F"]
    weights = {
        "root": {"A": 1},
        "A": {"C": 1, "E": 2, "F": 3},
        "B": {"F": 1, "D": 2},
    }

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": None, "parent": None},
        "C": {"distance": 2, "parent": "A"},
        "D": {"distance": None, "parent": None},
        "E": {"distance": 3, "parent": "A"},
        "F": {"distance": 4, "parent": "A"},
    }


def test_compute_distance_mapping_complex(mocker, mocked_graph):
    """Compute distance mapping from graph with complex graph."""
    identifiers = ["root", "A", "B", "C", "D", "E", "F", "G"]
    weights = {
        "root": {"A": 1, "B": 2, "F": 3},
        "A": {"C": 1, "D": 2},
        "B": {"D": 1, "F": 2, "G": 3},
        "C": {"G": 1},
        "D": {"E": 1},
        "E": {"A": 1},
        "G": {"B": 1}
    }

    # mock nodes in the graph.
    nodes = [mocker.Mock(identifier=_id) for _id in identifiers]
    mocked_graph.nodes.return_value = nodes

    # mock graph traversal.
    mocked_graph.outcoming = lambda _id: weights.get(_id, {}).keys()
    mocked_graph.link_weight = lambda _id1, _id2: weights[_id2][_id1]

    assert wiz.graph.compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "root"},
        "C": {"distance": 2, "parent": "A"},
        "D": {"distance": 3, "parent": "A"},
        "E": {"distance": 4, "parent": "D"},
        "F": {"distance": 3, "parent": "root"},
        "G": {"distance": 3, "parent": "C"},
    }


def test_combined_requirements(mocked_graph):
    """Combine nodes requirements."""
    versions = ["1.2.3", "1.9.2", "3.0.0"]
    parents_sets = [{"D"}, {"C"}, {"B"}]

    # mock parents requirements check.
    requirements = {
        "B": {"foo==3.0.0": Requirement("foo >= 1")},
        "C": {"foo==1.9.2": Requirement("foo >= 1, < 2")},
        "D": {"foo==1.2.3": Requirement("foo == 1.2.3")},
    }
    mocked_graph.link_requirement = lambda _id1, _id2: requirements[_id2][_id1]

    # Compute nodes.
    nodes = [
        wiz.graph.Node(
            wiz.package.Package(
                wiz.definition.Definition({
                    "identifier": "foo", "version": version
                })
            ),
            parent_identifiers=parents
        )
        for version, parents in zip(versions, parents_sets)
    ]

    assert wiz.graph.combined_requirements(mocked_graph, nodes) == (
        Requirement("foo >=1, ==1.2.3, <2")
    )


def test_combined_requirements_error(mocked_graph):
    """Fail to combine nodes requirements from different definition name."""
    versions = ["1.2.3", "1.9.2", "3.0.0"]
    parents_sets = [{"D"}, {"C"}, {"B"}]

    # mock parents requirements check.
    requirements = {
        "B": {"foo==3.0.0": Requirement("incorrect")},
        "C": {"foo==1.9.2": Requirement("foo >= 1, < 2")},
        "D": {"foo==1.2.3": Requirement("foo == 1.2.3")},
    }
    mocked_graph.link_requirement = lambda _id1, _id2: requirements[_id2][_id1]

    # Compute nodes.
    nodes = [
        wiz.graph.Node(
            wiz.package.Package(
                wiz.definition.Definition({
                    "identifier": "foo", "version": version
                })
            ),
            parent_identifiers=parents
        )
        for version, parents in zip(versions, parents_sets)
    ]

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        wiz.graph.combined_requirements(mocked_graph, nodes)

    assert (
        "Impossible to combine requirements with different names "
        "[foo, incorrect]."
    ) in str(error)


def test_extract_conflicting_requirements(mocked_graph):
    """Extract conflicting requirements from nodes."""
    versions = ["3.0.0", "3.2.1", "4.0.0"]
    parents_sets = [{"root"}, {"E", "F"}, {"G", "H", "I"}]

    # mock nodes existence check.
    existences = {"E": False, "F": True, "G": True, "H": True, "I": True}
    mocked_graph.exists = lambda _id: existences[_id]

    # mock parents requirements check.
    requirements = {
        "root": {"foo==3.0.0": Requirement("foo==3.0.0")},
        "F": {"foo==3.2.1": Requirement("foo ==3.*")},
        "G": {"foo==4.0.0": Requirement("foo >=4, <5")},
        "H": {"foo==4.0.0": Requirement("foo >=4, <5")},
        "I": {"foo==4.0.0": Requirement("foo")},
    }
    mocked_graph.link_requirement = lambda _id1, _id2: requirements[_id2][_id1]

    # Compute nodes.
    nodes = [
        wiz.graph.Node(
            wiz.package.Package(
                wiz.definition.Definition({
                    "identifier": "foo", "version": version
                })
            ),
            parent_identifiers=parents
        )
        for version, parents in zip(versions, parents_sets)
    ]

    conflicts = wiz.graph.extract_conflicting_requirements(mocked_graph, nodes)

    assert conflicts == [
        {
            "graph": mocked_graph,
            "requirement": Requirement("foo >=4, <5"),
            "identifiers": {"G", "H"},
            "conflicts": {"F", "root"}
        },
        {
            "graph": mocked_graph,
            "requirement": Requirement("foo ==3.0.0"),
            "identifiers": {"root"},
            "conflicts": {"G", "H"}
        },
        {
            "graph": mocked_graph,
            "requirement": Requirement("foo ==3.*"),
            "identifiers": {"F"},
            "conflicts": {"G", "H"}
        }
    ]


def test_extract_conflicting_requirements_error(mocked_graph):
    """Fail to extract conflicting requirements from nodes."""
    nodes = [
        wiz.graph.Node(
            wiz.package.Package(
                wiz.definition.Definition({
                    "identifier": "foo", "version": "3.1.2"
                })
            ),
            parent_identifiers={"root"}
        ),
        wiz.graph.Node(
            wiz.package.Package(
                wiz.definition.Definition({
                    "identifier": "bar", "version": "0.1.0"
                })
            ),
            parent_identifiers={"E"}
        )
    ]

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        wiz.graph.extract_conflicting_requirements(mocked_graph, nodes)

    assert (
        "All nodes should have the same definition identifier when "
        "attempting to extract conflicting requirements from parent "
        "nodes [bar, foo]"
    ) in str(error.value)

    mocked_graph.exists.assert_not_called()
    mocked_graph.link_requirement.assert_not_called()


def test_graph_empty(mocked_resolver):
    """Create an empty graph."""
    graph = wiz.graph.Graph(mocked_resolver)

    assert graph.resolver == mocked_resolver
    assert graph.nodes() == []
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}
    assert graph.data() == {
        "node_mapping": {},
        "link_mapping": {},
        "error_mapping": {},
        "conditioned_nodes": [],
    }


def test_graph_copy():
    """Copy a graph while referencing the same resolver instance."""
    resolver = wiz.graph.Resolver({})

    graph = wiz.graph.Graph(resolver)
    assert graph.resolver == resolver

    _graph = copy.deepcopy(graph)
    assert _graph.resolver == resolver


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_nodes(mocked_resolver, mocked_package_extract, packages):
    """Retrieve nodes within a simple graph."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]], [packages["B==1.2.3"]], [packages["C"]],
        [packages["D==4.1.0"]]
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    nodes = [
        wiz.graph.Node(packages["A==0.1.0"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}),
        wiz.graph.Node(packages["C"], parent_identifiers={"B==1.2.3"}),
        wiz.graph.Node(packages["D==4.1.0"], parent_identifiers={"B==1.2.3"})
    ]

    assert graph.node("A==0.1.0") == nodes[0]
    assert graph.exists("A==0.1.0") is True

    assert graph.node("B==1.2.3") == nodes[1]
    assert graph.exists("B==1.2.3") is True

    assert graph.node("C") == nodes[2]
    assert graph.exists("C") is True

    assert graph.node("D==4.1.0") == nodes[3]
    assert graph.exists("D==4.1.0") is True

    assert graph.node("whatever") is None
    assert graph.exists("whatever") is False

    assert sorted(graph.nodes(), key=lambda n: n.identifier) == nodes
    assert graph.nodes(definition_identifier="A") == [nodes[0]]
    assert graph.nodes(definition_identifier="B") == [nodes[1]]
    assert graph.nodes(definition_identifier="C") == [nodes[2]]
    assert graph.nodes(definition_identifier="D") == [nodes[3]]
    assert graph.nodes(definition_identifier="whatever") == []


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_nodes_with_version_conflicts(
    mocked_resolver, mocked_package_extract, packages
):
    """Retrieve nodes within a simple graph with conflicting versions."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("D"), Requirement("D==3.*"), Requirement("C")]
    mocked_package_extract.side_effect = [
        [packages["D==4.1.0"]], [packages["D==3.2.0"]], [packages["C"]]
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    nodes = [
        wiz.graph.Node(packages["C"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["D==3.2.0"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["D==4.1.0"], parent_identifiers={"root"}),
    ]

    assert graph.node("C") == nodes[0]
    assert graph.exists("C") is True

    assert graph.node("D==3.2.0") == nodes[1]
    assert graph.exists("D==3.2.0") is True

    assert graph.node("D==4.1.0") == nodes[2]
    assert graph.exists("D==4.1.0") is True

    assert graph.node("whatever") is None
    assert graph.exists("whatever") is False

    assert sorted(graph.nodes(), key=lambda n: n.identifier) == nodes
    assert graph.nodes(definition_identifier="C") == [nodes[0]]
    assert sorted(
        graph.nodes(definition_identifier="D"), key=lambda n: n.identifier
    ) == [nodes[1], nodes[2]]
    assert graph.nodes(definition_identifier="whatever") == []


@pytest.mark.parametrize("packages", ["conflicting-variants"], indirect=True)
def test_graph_nodes_with_variant_conflicts(
    mocked_resolver, mocked_package_extract, packages
):
    """Retrieve nodes within a simple graph with conflicting variants."""
    requirements = [Requirement("A"), Requirement("B[V1]")]
    mocked_package_extract.side_effect = [
        [packages["A[V3]"],  packages["A[V2]"], packages["A[V1]"]],
        [packages["B[V1]==1.2.3"]], [packages["C"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    nodes = [
        wiz.graph.Node(packages["A[V1]"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["A[V2]"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["A[V3]"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["B[V1]==1.2.3"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["C"], parent_identifiers={"B[V1]==1.2.3"}),
    ]

    assert graph.node("A[V1]") == nodes[0]
    assert graph.exists("A[V1]") is True

    assert graph.node("A[V2]") == nodes[1]
    assert graph.exists("A[V2]") is True

    assert graph.node("A[V3]") == nodes[2]
    assert graph.exists("A[V3]") is True

    assert graph.node("B[V1]==1.2.3") == nodes[3]
    assert graph.exists("B[V1]==1.2.3") is True

    assert graph.node("C") == nodes[4]
    assert graph.exists("C") is True

    assert graph.node("whatever") is None
    assert graph.exists("whatever") is False

    assert sorted(graph.nodes(), key=lambda n: n.identifier) == nodes
    assert sorted(
        graph.nodes(definition_identifier="A"), key=lambda n: n.identifier
    ) == [nodes[0], nodes[1], nodes[2]]
    assert graph.nodes(definition_identifier="B") == [nodes[3]]
    assert graph.nodes(definition_identifier="C") == [nodes[4]]
    assert graph.nodes(definition_identifier="whatever") == []


@pytest.mark.parametrize(
    "packages, identifier, requirement", [
        ("single", "A==0.1.0", Requirement("::A==0.1.*")),
        ("single-with-namespace", "foo::A==0.1.0", Requirement("foo::A==0.1.*"))
    ],
    ids=["single", "single-with-namespace"],
    indirect=["packages"]
)
def test_graph_link_requirement(
    mocked_resolver, mocked_package_extract, packages, identifier, requirement
):
    """Retrieve link requirements within a simple graph."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A==0.1.*")]
    mocked_package_extract.side_effect = [[packages[identifier]]]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    assert graph.link_requirement(identifier, "root") == requirement

    with pytest.raises(ValueError) as error:
        graph.link_requirement(identifier, "whatever")
    assert "No link recorded for node: 'whatever'" in str(error)

    with pytest.raises(ValueError) as error:
        graph.link_requirement("whatever", "root")
    assert "No link recorded for node: 'whatever'" in str(error)


@pytest.mark.parametrize(
    "packages, identifier", [
        ("single", "A==0.1.0"),
        ("single-with-namespace", "foo::A==0.1.0")
    ],
    ids=["single", "single-with-namespace"],
    indirect=["packages"]
)
def test_graph_link_weight(
    mocked_resolver, mocked_package_extract, packages, identifier
):
    """Retrieve link weights within a simple graph."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A")]
    mocked_package_extract.side_effect = [[packages[identifier]]]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    assert graph.link_weight(identifier, "root") == 1

    with pytest.raises(ValueError) as error:
        graph.link_weight(identifier, "whatever")
    assert "No link recorded for node: 'whatever'" in str(error)

    with pytest.raises(ValueError) as error:
        graph.link_weight("whatever", "root")
    assert "No link recorded for node: 'whatever'" in str(error)


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_outcoming(mocked_resolver, mocked_package_extract, packages):
    """Retrieve outcoming of nodes within a simple graph."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A==0.1.0")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]], [packages["B==1.2.3"]], [packages["C"]],
        [packages["D==4.1.0"]]
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    assert graph.outcoming("A==0.1.0") == ["B==1.2.3"]
    assert graph.outcoming("B==1.2.3") == ["C", "D==4.1.0"]
    assert graph.outcoming("C") == []
    assert graph.outcoming("D==4.1.0") == []
    assert graph.outcoming("whatever") == []


@pytest.mark.parametrize("packages", ["single"], indirect=True)
def test_graph_find(mocked_resolver, mocked_package_extract, packages):
    """Find nodes from requirement."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A")]
    mocked_package_extract.side_effect = [[packages["A==0.1.0"]]]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    assert graph.find(Requirement("A")) == {"A==0.1.0"}
    assert graph.find(Requirement("::A < 3")) == {"A==0.1.0"}
    assert graph.find(Requirement("A > 99")) == set()
    assert graph.find(Requirement("foo::A")) == set()
    assert graph.find(Requirement("A[V1]")) == set()


@pytest.mark.parametrize("packages", ["conflicting-variants"], indirect=True)
def test_graph_find_with_variants(
    mocked_resolver, mocked_package_extract, packages
):
    """Find nodes from requirement."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A"), Requirement("B")]
    mocked_package_extract.side_effect = [
        [packages["A[V3]"],  packages["A[V2]"], packages["A[V1]"]],
        [packages["B[V2]==1.2.3"], packages["B[V1]==1.2.3"]], [packages["C"]],
        [packages["C"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    assert graph.find(Requirement("A")) == {"A[V1]", "A[V2]", "A[V3]"}
    assert graph.find(Requirement("A[V1]")) == {"A[V1]"}
    assert graph.find(Requirement("B")) == {"B[V2]==1.2.3", "B[V1]==1.2.3"}
    assert graph.find(Requirement("B>2")) == set()
    assert graph.find(Requirement("B[V2]")) == {"B[V2]==1.2.3"}


@pytest.mark.parametrize("packages", ["single"], indirect=True)
def test_graph_update_from_requirements_single(
    mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with one request."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A")]
    mocked_package_extract.side_effect = [[packages["A==0.1.0"]]]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    mocked_package_extract.assert_called_once_with(
        Requirement("A"), mocked_resolver.definition_mapping,
        namespace_counter=collections.Counter()
    )

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            )
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1}
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["single"], indirect=True)
def test_graph_update_from_requirements_single_detached(
    mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with one request detached from the root node."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A")]
    mocked_package_extract.side_effect = [[packages["A==0.1.0"]]]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements, detached=True)

    # Check call to extract packages from requirement.
    mocked_package_extract.assert_called_once_with(
        Requirement("A"), mocked_resolver.definition_mapping,
        namespace_counter=collections.Counter()
    )

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={}
            )
        },
        "link_mapping": {},
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["single-with-namespace"], indirect=True)
def test_graph_update_from_requirements_single_with_namespace(
    mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with one request extracting a package with namespace."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A")]
    mocked_package_extract.side_effect = [[packages["foo::A==0.1.0"]]]
    mocked_resolver.definition_mapping["__namespace__"]["A"] = {"foo"}

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    mocked_package_extract.assert_called_once_with(
        Requirement("A"), mocked_resolver.definition_mapping,
        namespace_counter=collections.Counter({"foo": 1})
    )

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "foo::A==0.1.0": wiz.graph.Node(
                packages["foo::A==0.1.0"], parent_identifiers={"root"}
            )
        },
        "link_mapping": {
            "root": {
                "foo::A==0.1.0": {
                    "requirement": Requirement("foo::A"), "weight": 1
                }
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


def test_graph_update_from_requirements_single_with_error(
    mocked_resolver, mocked_package_extract
):
    """Create an graph with one request failing to extract package."""
    mocked_package_extract.side_effect = wiz.exception.RequestNotFound("Error")

    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements([Requirement("A")])

    # Check call to extract packages from requirement.
    mocked_package_extract.assert_called_once_with(
        Requirement("A"), mocked_resolver.definition_mapping,
        namespace_counter=collections.Counter()
    )

    assert graph.nodes() == []
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {
        "root": ["Error"]
    }

    # Check full data.
    assert graph.data() == {
        "node_mapping": {},
        "link_mapping": {},
        "error_mapping": {"root": ["Error"]},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_requirements_many(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with several requests leading to more requests."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A"), Requirement("D>3")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]],  [packages["D==4.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==4.1.0"]]
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D > 3"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D > 1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        )
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3", "root"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>3"), "weight": 2},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_requirements_many_detached(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with several requests detached from the root node."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A"), Requirement("D>3")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]],  [packages["D==4.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==4.1.0"]]
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements, detached=True)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D > 3"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D > 1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        )
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            ),
        },
        "link_mapping": {
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many-with-namespaces"], indirect=True)
def test_graph_update_from_requirements_many_with_namespaces(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with several requests leading to more requests."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("foo::A"), Requirement("D>3")]
    mocked_package_extract.side_effect = [
        [packages["foo::A==0.1.0"]],  [packages["D==4.1.0"]],
        [packages["bar::B==1.2.3"]], [packages["foo::C"]],
        [packages["D==4.1.0"]]
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("foo::A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 1})
        ),
        mocker.call(
            Requirement("D > 3"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 2})
        ),
        mocker.call(
            Requirement("bar::B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 2})
        ),
        mocker.call(
            Requirement("foo::C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 2, "bar": 1})
        ),
        mocker.call(
            Requirement("D > 1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 3, "bar": 1})
        )
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "foo::A==0.1.0": wiz.graph.Node(
                packages["foo::A==0.1.0"], parent_identifiers={"root"}
            ),
            "bar::B==1.2.3": wiz.graph.Node(
                packages["bar::B==1.2.3"], parent_identifiers={"foo::A==0.1.0"}
            ),
            "foo::C": wiz.graph.Node(
                packages["foo::C"], parent_identifiers={"bar::B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"],
                parent_identifiers={"bar::B==1.2.3", "root"}
            ),
        },
        "link_mapping": {
            "root": {
                "foo::A==0.1.0": {
                    "requirement": Requirement("foo::A"), "weight": 1
                },
                "D==4.1.0": {"requirement": Requirement("::D>3"), "weight": 2},
            },
            "foo::A==0.1.0": {
                "bar::B==1.2.3": {
                    "requirement": Requirement("bar::B"), "weight": 1
                }
            },
            "bar::B==1.2.3": {
                "foo::C": {"requirement": Requirement("foo::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_requirements_many_with_error(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with several requests and one of them is failing."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A"), Requirement("C")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]],  [packages["C"]], [packages["B==1.2.3"]],
        [packages["C"]], wiz.exception.RequestNotFound("Error")
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D > 1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        )
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {"B==1.2.3": ["Error"]}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3", "root"}
            )
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "C": {"requirement": Requirement("::C"), "weight": 2},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
            }
        },
        "error_mapping": {"B==1.2.3": ["Error"]},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_update_from_requirements_several_times(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with several requests several times."""
    # Set requirements and expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==3.2.0"]], [packages["D==4.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements([Requirement("A")])
    graph.update_from_requirements([Requirement("D>4")])

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D >= 3, <4"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D > 4"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == {"D==4.1.0", "D==3.2.0"}
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==3.2.0": wiz.graph.Node(
                packages["D==3.2.0"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"root"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>4"), "weight": 2},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.2.0": {
                    "requirement": Requirement("::D>=3,<4"), "weight": 2
                },
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_requirements_several_times_same(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with same requests several times."""
    # Set requirements and expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==4.1.0"]], [packages["A==0.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements([Requirement("A")])
    graph.update_from_requirements([Requirement("A")])

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D>1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_requirements_several_times_different_parent(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with same requests several times with different parent.
    """
    # Set requirements and expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==4.1.0"]], [packages["A==0.1.0"]],
        [packages["A==0.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements([Requirement("A")], detached=True)
    graph.update_from_requirements([Requirement("A")])
    graph.update_from_requirements([Requirement("A")], detached=True)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D>1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many-with-conditions"], indirect=True)
def test_graph_update_from_requirements_unfulfilled_conditions(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with several unfulfilled conditions."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A"), Requirement("G"), Requirement("H")]
    mocked_package_extract.side_effect = [
        # Extract required packages.
        [packages["A==0.1.0"]],  [packages["G"]], [packages["H"]],

        # Check remaining conditions.
        [packages["E"]], [packages["F==13"]], [packages["D==4.1.0"]],
        wiz.exception.RequestNotFound("Error")
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("G"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("H"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("E"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("F"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("incorrect"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        )
    ]

    # Check that conditions are recorded.
    stored_nodes = [
        wiz.graph.StoredNode(
            requirement=Requirement("::A"),
            package=packages["A==0.1.0"],
            parent_identifier="root",
            weight=1
        ),
        wiz.graph.StoredNode(
            requirement=Requirement("::G"),
            package=packages["G"],
            parent_identifier="root",
            weight=2
        ),
        wiz.graph.StoredNode(
            requirement=Requirement("::H"),
            package=packages["H"],
            parent_identifier="root",
            weight=3
        )
    ]
    assert graph.conditioned_nodes() == stored_nodes

    # Check whether the graph has conflicts, or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {},
        "link_mapping": {},
        "error_mapping": {},
        "conditioned_nodes": stored_nodes
    }


@pytest.mark.parametrize("packages", ["many-with-conditions"], indirect=True)
def test_graph_update_from_requirements_fulfilled_conditions(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with several fulfilled conditions."""
    # Set requirements and expected package extraction for test.
    requirements = [
        Requirement("A"), Requirement("G"), Requirement("H"), Requirement("E")
    ]
    mocked_package_extract.side_effect = [
        # Extract required packages.
        [packages["A==0.1.0"]],  [packages["G"]], [packages["H"]],
        [packages["E"]], [packages["F==13"]],

        # Check remaining conditions.
        [packages["E"]], [packages["F==13"]], [packages["D==4.1.0"]],
        wiz.exception.RequestNotFound("Error"),

        # Conditions are fulfilled for A, adding it with dependencies.
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==4.1.0"]],

        # Check remaining conditions.
        [packages["F==13"]], [packages["D==4.1.0"]],
        wiz.exception.RequestNotFound("Error"),

        # Check remaining conditions.
        wiz.exception.RequestNotFound("Error"),
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("G"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("H"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("E"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("F"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("E"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("F"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("incorrect"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D>1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("F"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("incorrect"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("incorrect"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        )
    ]

    # Check that conditions are recorded.
    stored_nodes = [
        wiz.graph.StoredNode(
            requirement=Requirement("::A"),
            package=packages["A==0.1.0"],
            parent_identifier="root",
            weight=1
        ),
        wiz.graph.StoredNode(
            requirement=Requirement("::G"),
            package=packages["G"],
            parent_identifier="root",
            weight=2
        ),
        wiz.graph.StoredNode(
            requirement=Requirement("::H"),
            package=packages["H"],
            parent_identifier="root",
            weight=3
        )
    ]
    assert graph.conditioned_nodes() == stored_nodes

    # Check whether the graph has conflicts, or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            ),
            "E": wiz.graph.Node(
                packages["E"], parent_identifiers={"root"}
            ),
            "F==13": wiz.graph.Node(
                packages["F==13"], parent_identifiers={"E"}
            ),
            "G": wiz.graph.Node(
                packages["G"], parent_identifiers={"root"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "G": {"requirement": Requirement("::G"), "weight": 2},
                "E": {"requirement": Requirement("::E"), "weight": 4},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            },
            "E": {
                "F==13": {"requirement": Requirement("::F"), "weight": 1}
            },

        },
        "error_mapping": {},
        "conditioned_nodes": stored_nodes
    }


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_update_from_requirements_with_version_conflicts(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with conflicting package version."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A"), Requirement("D")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]],  [packages["D==4.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==3.2.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D >= 3, <4"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        )
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == {"D==4.1.0", "D==3.2.0"}
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==3.2.0": wiz.graph.Node(
                packages["D==3.2.0"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"root"}
            )
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D"), "weight": 2},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.2.0": {
                    "requirement": Requirement("::D>=3,<4"), "weight": 2
                },
            },
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["conflicting-variants"], indirect=True)
def test_graph_update_from_requirements_with_variant_conflicts(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph with conflicting package version."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A"), Requirement("B[V1]")]
    mocked_package_extract.side_effect = [
        [packages["A[V3]"],  packages["A[V2]"], packages["A[V1]"]],
        [packages["B[V1]==1.2.3"]], [packages["C"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("A"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("B[V1]"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == {"A[V3]", "A[V2]", "A[V1]"}
    assert graph.conflicting_variant_groups() == [["A[V3]", "A[V2]", "A[V1]"]]
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A[V3]": wiz.graph.Node(
                packages["A[V3]"], parent_identifiers={"root"}
            ),
            "A[V2]": wiz.graph.Node(
                packages["A[V2]"], parent_identifiers={"root"}
            ),
            "A[V1]": wiz.graph.Node(
                packages["A[V1]"], parent_identifiers={"root"}
            ),
            "B[V1]==1.2.3": wiz.graph.Node(
                packages["B[V1]==1.2.3"], parent_identifiers={"root"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B[V1]==1.2.3"}
            )
        },
        "link_mapping": {
            "root": {
                "A[V3]": {"requirement": Requirement("::A"), "weight": 1},
                "A[V2]": {"requirement": Requirement("::A"), "weight": 1},
                "A[V1]": {"requirement": Requirement("::A"), "weight": 1},
                "B[V1]==1.2.3": {
                    "requirement": Requirement("::B[V1]"), "weight": 2
                },
            },
            "B[V1]==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
            },
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_package(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph from one package."""
    # Set expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==4.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_package(packages["A==0.1.0"], Requirement("A"))

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D>1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            )
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1},
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_package_detached(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph from one package detached from the root node."""
    # Set expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==4.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_package(
        packages["A==0.1.0"], Requirement("A"), detached=True
    )

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D>1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers=set()
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            )
        },
        "link_mapping": {
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1},
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_update_from_package_several_times(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph from packages several times."""
    # Set expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==3.2.0"]],
        [packages["D==4.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_package(packages["A==0.1.0"], Requirement("A"))
    graph.update_from_package(packages["D==4.1.0"], Requirement("D"))

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D >= 3, <4"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == {"D==4.1.0", "D==3.2.0"}
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==3.2.0": wiz.graph.Node(
                packages["D==3.2.0"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"root"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D"), "weight": 2},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1},
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.2.0": {
                    "requirement": Requirement("::D>=3,<4"), "weight": 2
                },
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_package_several_times_same(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph from the same package several times."""
    # Set expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==4.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_package(packages["A==0.1.0"], Requirement("A"))
    graph.update_from_package(packages["A==0.1.0"], Requirement("A"))

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D>1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            )
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1},
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_package_several_times_different_requirement(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph from the same package several times with different
    requirement.
    """
    # Set expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==4.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_package(packages["A==0.1.0"], Requirement("A"))
    graph.update_from_package(packages["A==0.1.0"], Requirement("A<1"))

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D>1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            )
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A<1"), "weight": 1},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1},
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_graph_update_from_package_several_times_different_parent(
    mocker, mocked_resolver, mocked_package_extract, packages
):
    """Create an graph from the same package several times with different
    parent.
    """
    # Set expected package extraction for test.
    mocked_package_extract.side_effect = [
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==4.1.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_package(
        packages["A==0.1.0"], Requirement("A"), detached=True
    )
    graph.update_from_package(packages["A==0.1.0"], Requirement("A"))

    # Check call to extract packages from requirement.
    assert mocked_package_extract.call_args_list == [
        mocker.call(
            Requirement("B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
        mocker.call(
            Requirement("D>1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter()
        ),
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==4.1.0": wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            )
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1},
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==4.1.0": {"requirement": Requirement("::D>1"), "weight": 2},
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["single"], indirect=True)
def test_graph_remove(mocked_resolver, mocked_package_extract, packages):
    """Remove one node from graph."""
    # Set requirements and expected package extraction for test.
    requirements = [Requirement("A")]
    mocked_package_extract.side_effect = [[packages["A==0.1.0"]]]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)
    graph.remove_node("A==0.1.0")

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {},
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1}
            }
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


def test_graph_remove_error(mocked_resolver):
    """Fail to remove one node from graph."""
    graph = wiz.graph.Graph(mocked_resolver)

    with pytest.raises(ValueError) as error:
        graph.remove_node("A==0.1.0")

    assert "Node can not be removed: A==0.1.0" in str(error)


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_relink_parents(
    mocked_resolver, mocked_package_extract, packages
):
    """Relink parents after removing a node."""
    requirements = [Requirement("A"), Requirement("D==3.1.0")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]],  [packages["D==3.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==3.2.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Remove a node.
    node = graph.node("D==3.2.0")
    graph.remove_node("D==3.2.0")

    # Relink parent from removed node.
    graph.relink_parents(node)

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==3.1.0": wiz.graph.Node(
                packages["D==3.1.0"], parent_identifiers={"B==1.2.3", "root"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "D==3.1.0": {
                    "requirement": Requirement("::D ==3.1.0"), "weight": 2
                }
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.1.0": {
                    "requirement": Requirement("::D >=3, <4"), "weight": 2
                },
                "D==3.2.0": {
                    "requirement": Requirement("::D >=3, <4"), "weight": 2
                },
            },
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_relink_parents_error(
    mocked_resolver, mocked_package_extract, packages
):
    """Fail to relink parents after removing a node."""
    requirements = [Requirement("A"), Requirement("D==3.1.0")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]],  [packages["D==3.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==3.2.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Remove a node.
    node = graph.node("D==3.1.0")
    graph.remove_node("D==3.1.0")

    # Relink parent from removed node.
    graph.relink_parents(node)

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {
        "root": [
            "Requirement '::D ==3.1.0' can not be satisfied once 'D==3.1.0' is "
            "removed from the graph."
        ]
    }

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==3.2.0": wiz.graph.Node(
                packages["D==3.2.0"], parent_identifiers={"B==1.2.3"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "D==3.1.0": {
                    "requirement": Requirement("::D ==3.1.0"), "weight": 2
                }
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.2.0": {
                    "requirement": Requirement("::D >=3, <4"), "weight": 2
                },
            },
        },
        "error_mapping": {
            "root": [
                "Requirement '::D ==3.1.0' can not be satisfied once 'D==3.1.0'"
                " is removed from the graph."
            ]
        },
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_relink_parents_with_requirement(
    mocked_resolver, mocked_package_extract, packages
):
    """Relink parents after removing a node with new requirement."""
    requirements = [Requirement("A"), Requirement("D==3.1.0")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]],  [packages["D==3.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==3.2.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Remove a node.
    node = graph.node("D==3.2.0")
    graph.remove_node("D==3.2.0")

    # Relink parent from removed node.
    graph.relink_parents(node, requirement=Requirement("::D >3"))

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==3.1.0": wiz.graph.Node(
                packages["D==3.1.0"], parent_identifiers={"B==1.2.3", "root"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "D==3.1.0": {
                    "requirement": Requirement("::D ==3.1.0"), "weight": 2
                }
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.1.0": {
                    "requirement": Requirement("::D >3"), "weight": 2
                },
                "D==3.2.0": {
                    "requirement": Requirement("::D >=3, <4"), "weight": 2
                },
            },
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_relink_parents_unnecessary(
    mocked_resolver, mocked_package_extract, packages
):
    """No need to relink parent when parent does not exist in graph anymore."""
    requirements = [Requirement("A"), Requirement("D==3.1.0")]
    mocked_package_extract.side_effect = [
        [packages["A==0.1.0"]],  [packages["D==3.1.0"]], [packages["B==1.2.3"]],
        [packages["C"]], [packages["D==3.2.0"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Remove a node.
    node = graph.node("D==3.2.0")
    graph.remove_node("D==3.2.0")
    graph.remove_node("B==1.2.3")

    # Relink parent from removed node.
    graph.relink_parents(node)

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == []
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {}

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A==0.1.0": wiz.graph.Node(
                packages["A==0.1.0"], parent_identifiers={"root"}
            ),
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==3.1.0": wiz.graph.Node(
                packages["D==3.1.0"], parent_identifiers={"root"}
            ),
        },
        "link_mapping": {
            "root": {
                "A==0.1.0": {"requirement": Requirement("::A"), "weight": 1},
                "D==3.1.0": {
                    "requirement": Requirement("::D ==3.1.0"), "weight": 2
                }
            },
            "A==0.1.0": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1}
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.2.0": {
                    "requirement": Requirement("::D >=3, <4"), "weight": 2
                },
            },
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("options, parent_identifiers", [
    ({}, set()),
    ({"parent_identifiers": {"foo"}}, {"foo"}),
], ids=[
    "simple",
    "with-parents"
])
def test_node(mocker, options, parent_identifiers):
    """Create and use Node instance."""
    package = mocker.Mock()

    node = wiz.graph.Node(package, **options)
    assert node.identifier == package.identifier
    assert node.definition == package.definition
    assert node.package == package
    assert node.parent_identifiers == parent_identifiers
    assert node.data() == {
        "package": package,
        "parents": sorted(parent_identifiers)
    }

    node.add_parent("parent1")
    node.add_parent("parent1")
    node.add_parent("parent2")

    assert node.parent_identifiers == set(
        itertools.chain(parent_identifiers, {"parent1", "parent2"})
    )
    assert node.data() == {
        "package": package,
        "parents": sorted(
            itertools.chain(parent_identifiers, ["parent1", "parent2"])
        )
    }

    assert node != 42
    assert node != wiz.graph.Node(package, **options)
    assert node == wiz.graph.Node(
        package, parent_identifiers=set(
            itertools.chain(parent_identifiers, {"parent1", "parent2"})
        )
    )


@pytest.mark.parametrize("options, weight", [
    ({}, 1),
    ({"weight": 10}, 10),
], ids=[
    "simple",
    "with-weight"
])
def test_stored_node(mocker, options, weight):
    """Create and use StoredNode instance."""
    package = mocker.Mock()

    stored_node = wiz.graph.StoredNode(
        "__REQUIREMENT__", package, "__PARENT_ID__", **options
    )
    assert stored_node.identifier == package.identifier
    assert stored_node.requirement == "__REQUIREMENT__"
    assert stored_node.package == package
    assert stored_node.parent_identifier == "__PARENT_ID__"
    assert stored_node.weight == weight

    assert stored_node.data() == {
        "requirement": "__REQUIREMENT__",
        "package": package,
        "parent_identifier": "__PARENT_ID__",
        "weight": weight
    }

    assert stored_node != 42
    assert stored_node != wiz.graph.StoredNode(
        "__OTHER_REQUIREMENT__", package, "__PARENT_ID__", **options
    )
    assert stored_node == wiz.graph.StoredNode(
        "__REQUIREMENT__", package, "__PARENT_ID__", **options
    )


def test_distance_queue():
    """Create and use _DistanceQueue instance."""
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
