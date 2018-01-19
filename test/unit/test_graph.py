# :coding: utf-8

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

import wiz.graph
import wiz.definition


@pytest.fixture()
def definition_mapping():
    """Return a mocked definition mapping.
    """
    return {
        "envA": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "envA",
                "version": Version("0.2.0"),
                "requirement": {
                    Requirement("envC >= 0.3.2, <1")
                }
            }),
        },
        "envB": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "envB",
                "version": Version("0.1.0"),
                "requirement": [
                    Requirement("envD >= 0.1.0"),
                    Requirement("envF >= 1")
                ]
            })
        },
        "envC": {
            "0.3.2": wiz.definition.Definition({
                "identifier": "envC",
                "version": Version("0.3.2"),
                "requirement": [
                    Requirement("envD == 0.1.0")
                ]
            })
        },
        "envD": {
            "0.1.1": wiz.definition.Definition({
                "identifier": "envD",
                "version": Version("0.1.1"),
                "requirement": [
                    Requirement("envE >= 2")
                ]
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "envD",
                "version": Version("0.1.0")
            })
        },
        "envE": {
            "2.3.0": wiz.definition.Definition({
                "identifier": "envE",
                "version": Version("2.3.0"),
                "requirement": [
                    Requirement("envF >= 0.2")
                ]
            }),
        },
        "envF": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "envF",
                "version": Version("1.0.0")
            }),
            "0.2.0": wiz.definition.Definition({
                "identifier": "envF",
                "version": Version("0.2.0")
            })
        },
        "envG": {
            "2.0.2": wiz.definition.Definition({
                "identifier": "envG",
                "version": Version("2.0.2"),
                "requirement": [
                    Requirement("envB < 0.2.0")
                ]
            })
        },
        "envH": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "envH",
                "version": Version("1.0.0"),
                "requirement": [
                    Requirement("envI < 1")
                ]
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "envH",
                "version": Version("0.9.0"),
            })
        },
        "envI": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "envI",
                "version": Version("1.0.0"),
                "requirement": [
                    Requirement("envH < 1")
                ]
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "envI",
                "version": Version("0.9.0"),
            })
        },
    }


@pytest.mark.parametrize("requirements, expected_nodes", [
    ([], []),
    (
        [Requirement("envF")],
        ["envF==1.0.0"]
    ),
    (
        [Requirement("envA")],
        ["envA==0.2.0", "envC==0.3.2", "envD==0.1.0"]
    ),
    (
        [Requirement("envA"), Requirement("envG")],
        [
            "envA==0.2.0",
            "envB==0.1.0",
            "envC==0.3.2",
            "envD==0.1.0",
            "envD==0.1.1",
            "envE==2.3.0",
            "envF==1.0.0",
            "envG==2.0.2"
        ]
    ),
    (
        [Requirement("envA"), Requirement("envF==0.2.0"), Requirement("envG")],
        [
            "envA==0.2.0",
            "envB==0.1.0",
            "envC==0.3.2",
            "envD==0.1.0",
            "envD==0.1.1",
            "envE==2.3.0",
            "envF==0.2.0",
            "envF==1.0.0",
            "envG==2.0.2"
        ]
    )
], ids=[
    "no-requirements",
    "one-requirement-no-dependencies",
    "one-requirement-with-dependencies",
    "two-requirements-with-dependencies",
    "three-requirements-with-conflicts",
])
def test_graph_creation(requirements, expected_nodes, definition_mapping):
    """Create a graph from a specific definition mapping."""
    graph = wiz.graph.Graph(definition_mapping)
    graph.update_from_requirements(requirements)
    assert sorted(graph.node_identifiers()) == expected_nodes


def test_graph_conflict_resolution(definition_mapping):
    """Resolve conflicts from graph."""
    graph = wiz.graph.Graph(definition_mapping)
    graph.update_from_requirements([
        Requirement("envA"), Requirement("envG")
    ])
    assert sorted(graph.node_identifiers()) == [
        "envA==0.2.0",
        "envB==0.1.0",
        "envC==0.3.2",
        "envD==0.1.0",
        "envD==0.1.1",
        "envE==2.3.0",
        "envF==1.0.0",
        "envG==2.0.2"
    ]

    wiz.graph.resolve_conflicts(graph, definition_mapping)
    assert sorted(graph.node_identifiers()) == [
        "envA==0.2.0",
        "envB==0.1.0",
        "envC==0.3.2",
        "envD==0.1.0",
        "envF==1.0.0",
        "envG==2.0.2"
    ]


def test_graph_conflict_resolution_error(definition_mapping):
    """Fail to resolve conflicts from graph."""
    graph = wiz.graph.Graph(definition_mapping)
    graph.update_from_requirements([
        Requirement("envA"), Requirement("envF==0.2.0"), Requirement("envG")
    ])
    assert sorted(graph.node_identifiers()) == [
        "envA==0.2.0",
        "envB==0.1.0",
        "envC==0.3.2",
        "envD==0.1.0",
        "envD==0.1.1",
        "envE==2.3.0",
        "envF==0.2.0",
        "envF==1.0.0",
        "envG==2.0.2"
    ]

    with pytest.raises(RuntimeError) as exception:
        wiz.graph.resolve_conflicts(graph, definition_mapping)

    assert str(exception.value) == (
        "A requirement conflict has been detected for 'envF'\n"
        " - envF>=1 [from envB==0.1.0]\n"
        " - envF==0.2.0 [from root]\n"
    )


def test_graph_conflict_resolution_from_priority(definition_mapping):
    """Fail to resolve conflicts from graph."""
    graph = wiz.graph.Graph(definition_mapping)
    graph.update_from_requirements([
        Requirement("envH"), Requirement("envI")
    ])
    assert sorted(graph.node_identifiers()) == [
        "envH==0.9.0",
        "envH==1.0.0",
        "envI==0.9.0",
        "envI==1.0.0",
    ]

    wiz.graph.resolve_conflicts(graph, definition_mapping)
    assert sorted(graph.node_identifiers()) == [
        "envH==1.0.0", "envI==0.9.0"
    ]


def test_graph_extract_ordered_definitions(definition_mapping):
    """Return sorted definitions from graph."""
    graph = wiz.graph.Graph(definition_mapping)
    graph.update_from_requirements([
        Requirement("envA"), Requirement("envG")
    ])
    assert wiz.graph.extract_ordered_definitions(graph) == [
        definition_mapping["envF"]["1.0.0"],
        definition_mapping["envE"]["2.3.0"],
        definition_mapping["envD"]["0.1.1"],
        definition_mapping["envB"]["0.1.0"],
        definition_mapping["envD"]["0.1.0"],
        definition_mapping["envG"]["2.0.2"],
        definition_mapping["envC"]["0.3.2"],
        definition_mapping["envA"]["0.2.0"],
    ]

    wiz.graph.resolve_conflicts(graph, definition_mapping)
    assert wiz.graph.extract_ordered_definitions(graph) == [
        definition_mapping["envF"]["1.0.0"],
        definition_mapping["envB"]["0.1.0"],
        definition_mapping["envD"]["0.1.0"],
        definition_mapping["envG"]["2.0.2"],
        definition_mapping["envC"]["0.3.2"],
        definition_mapping["envA"]["0.2.0"],

    ]
