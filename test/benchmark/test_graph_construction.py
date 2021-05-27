# :coding: utf-8

import os

import pytest

import wiz.config
import wiz.graph
import wiz.definition
from wiz.utility import Requirement


@pytest.fixture(autouse=True)
def reset_configuration(mocker):
    """Ensure that no personal configuration is fetched during tests."""
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


def test_100_nodes(benchmark):
    """Build a graph with 100 nodes."""
    definition_mapping = {
        "foo{}".format(index-1): {
            "-":  wiz.definition.Definition({
                "identifier": "foo{}".format(index-1),
                "requirements": ["foo{}".format(index)]
            })
        }
        for index in range(2, 102)
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    def _build_graph():
        """Build graph."""
        graph = wiz.graph.Graph(resolver)
        graph.update_from_requirements([Requirement("foo1")], graph.ROOT)
        assert len(graph.nodes()) == 100

    benchmark(_build_graph)


def test_1000_nodes(benchmark):
    """Build a graph with 1000 nodes."""
    definition_mapping = {
        "foo{}".format(index-1): {
            "-":  wiz.definition.Definition({
                "identifier": "foo{}".format(index-1),
                "requirements": ["foo{}".format(index)]
            })
        }
        for index in range(2, 1002)
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    def _build_graph():
        """Build graph."""
        graph = wiz.graph.Graph(resolver)
        graph.update_from_requirements([Requirement("foo1")], graph.ROOT)
        assert len(graph.nodes()) == 1000

    benchmark(_build_graph)


def test_5000_nodes(benchmark):
    """Build a graph with 5000 nodes."""
    definition_mapping = {
        "foo{}".format(index-1): {
            "-":  wiz.definition.Definition({
                "identifier": "foo{}".format(index-1),
                "requirements": ["foo{}".format(index)]
            })
        }
        for index in range(2, 5002)
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    def _build_graph():
        """Build graph."""
        graph = wiz.graph.Graph(resolver)
        graph.update_from_requirements([Requirement("foo1")], graph.ROOT)
        assert len(graph.nodes()) == 5000

    benchmark(_build_graph)


def test_10000_nodes(benchmark):
    """Build a graph with 10000 nodes."""
    definition_mapping = {
        "foo{}".format(index-1): {
            "-":  wiz.definition.Definition({
                "identifier": "foo{}".format(index-1),
                "requirements": ["foo{}".format(index)]
            })
        }
        for index in range(2, 10002)
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    def _build_graph():
        """Build graph."""
        graph = wiz.graph.Graph(resolver)
        graph.update_from_requirements([Requirement("foo1")], graph.ROOT)
        assert len(graph.nodes()) == 10000

    benchmark(_build_graph)
