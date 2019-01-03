# :coding: utf-8

import pytest

import wiz.graph
import wiz.definition
from wiz.utility import Requirement


@pytest.fixture()
def spied_fetch_next_graph(mocker):
    """Return spy mocker on 'wiz.graph.Resolver._fetch_next_graph'."""
    return mocker.spy(wiz.graph.Resolver, "_fetch_next_graph")


@pytest.fixture()
def spied_fetch_distance_mapping(mocker):
    """Return spy mocker on 'wiz.graph.Resolver._fetch_distance_mapping'."""
    return mocker.spy(wiz.graph.Resolver, "_fetch_distance_mapping")


@pytest.fixture()
def spied_extract_combinations(mocker):
    """Return spy mocker on 'wiz.graph.Resolver._extract_combinations'."""
    return mocker.spy(wiz.graph.Resolver, "_extract_combinations")


@pytest.fixture()
def spied_resolve_conflicts(mocker):
    """Return spy mocker on 'wiz.graph.Resolver._resolve_conflicts'."""
    return mocker.spy(wiz.graph.Resolver, "_resolve_conflicts")


@pytest.fixture()
def spied_compute_distance_mapping(mocker):
    """Return spy mocker on 'wiz.graph.compute_distance_mapping'."""
    return mocker.spy(wiz.graph, "compute_distance_mapping")


@pytest.fixture()
def spied_generate_variant_combinations(mocker):
    """Return spy mocker on 'wiz.graph.generate_variant_combinations'.
    """
    return mocker.spy(wiz.graph, "generate_variant_combinations")


@pytest.fixture()
def spied_trim_unreachable_from_graph(mocker):
    """Return spy mocker on 'wiz.graph.trim_unreachable_from_graph'.
    """
    return mocker.spy(wiz.graph, "trim_unreachable_from_graph")


@pytest.fixture()
def spied_updated_by_distance(mocker):
    """Return spy mocker on 'wiz.graph.updated_by_distance'."""
    return mocker.spy(wiz.graph, "updated_by_distance")


@pytest.fixture()
def spied_extract_conflicting_nodes(mocker):
    """Return spy mocker on 'wiz.graph.extract_conflicting_nodes'."""
    return mocker.spy(wiz.graph, "extract_conflicting_nodes")


@pytest.fixture()
def spied_combined_requirements(mocker):
    """Return spy mocker on 'wiz.graph.combined_requirements'."""
    return mocker.spy(wiz.graph, "combined_requirements")


@pytest.fixture()
def spied_extract_parents(mocker):
    """Return spy mocker on 'wiz.graph.extract_parents'."""
    return mocker.spy(wiz.graph, "extract_parents")


@pytest.fixture()
def spied_remove_node_and_relink(mocker):
    """Return spy mocker on 'wiz.graph.remove_node_and_relink'."""
    return mocker.spy(wiz.graph, "remove_node_and_relink")


@pytest.fixture()
def spied_extract_ordered_packages(mocker):
    """Return spy mocker on 'wiz.graph.extract_ordered_packages'."""
    return mocker.spy(wiz.graph, "extract_ordered_packages")


def test_scenario_1(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    Root
     |
     |--(A): A==0.2.0
     |   |
     |   `--(C >=0.3.2, <1): C==0.3.2
     |       |
     |       `--(D==0.1.0): D==0.1.0
     |
     `--(G): G==2.0.2
         |
         `--(B<0.2.0): B==0.1.0
             |
             |--(D>=0.1.0): D==0.1.4
             |   |
             |   `--(E>=2): E==2.3.0
             |       |
             |       `--(F>=0.2): F==1.0.0
             |
             `--(F>=1): F==1.0.0

    Expected: F==1.0.0, D==0.1.0, B==0.1.0, C==0.3.2, G==2.0.2, A==0.2.0

    The position of 'D==0.1.0' / 'B==0.1.0' and 'C==0.3.2' / 'G==2.0.2' can
    vary as they have similar priority numbers.

    """
    definition_mapping = {
        "A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "requirements": ["C>=0.3.2, <1"]
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0"
            })
        },
        "B": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.2.0"
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["D>=0.1.0", "F>=1"]
            })
        },
        "C": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "1.0.0"
            }),
            "0.3.2": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.3.2",
                "requirements": ["D==0.1.0"]
            })
        },
        "D": {
            "0.1.4": wiz.definition.Definition({
                "identifier": "D",
                "version": "0.1.4",
                "requirements": ["E>=2"]
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "D",
                "version": "0.1.0"
            })
        },
        "E": {
            "2.3.0": wiz.definition.Definition({
                "identifier": "E",
                "version": "2.3.0",
                "requirements": ["F>=0.2"]
            })
        },
        "F": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "F",
                "version": "1.0.0"
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "F",
                "version": "0.9.0"
            })
        },
        "G": {
            "2.0.2": wiz.definition.Definition({
                "identifier": "G",
                "version": "2.0.2",
                "requirements": ["B<0.2.0"]
            }),
            "2.0.1": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.1"
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([Requirement("A"), Requirement("G")])

    assert len(packages) == 6
    assert packages[0].identifier == "F==1.0.0"

    # Order can vary cause both have priority of 3
    assert packages[1].identifier in ["D==0.1.0", "B==0.1.0"]
    assert packages[2].identifier in ["D==0.1.0", "B==0.1.0"]
    assert packages[2] != packages[1]

    # Order can vary cause both have priority of 2
    assert packages[3].identifier in ["C==0.3.2", "G==2.0.2"]
    assert packages[4].identifier in ["C==0.3.2", "G==2.0.2"]
    assert packages[4] != packages[3]

    assert packages[5].identifier == "A==0.2.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 4
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 2
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 2
    assert spied_updated_by_distance.call_count == 2
    assert spied_extract_conflicting_nodes.call_count == 2
    assert spied_combined_requirements.call_count == 2
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 1
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_2(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Fail to compute packages for the following graph.

    Root
     |
     |--(A): A==0.2.0
     |   |
     |   `--(C >=0.3.2, <1): C==0.3.2
     |       |
     |       `--(D==0.1.0): D==0.1.0
     |
     `--(G): G==2.0.2
         |
         `--(B<0.2.0): B==0.1.0
             |
             |--(D>0.1.0): D==0.1.4
             |   |
             |   `--(E>=2): E==2.3.0
             |       |
             |       `--(F>=0.2): F==1.0.0
             |
             `--(F>=1): F==1.0.0

    Expected: Unable to compute due to requirement compatibility between
    'D>0.1.0' and 'D==0.1.0'.

    """
    definition_mapping = {
        "A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "requirements": ["C>=0.3.2, <1"]
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0"
            })
        },
        "B": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.2.0"
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["D>0.1.0", "F>=1"]
            })
        },
        "C": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "1.0.0"
            }),
            "0.3.2": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.3.2",
                "requirements": ["D==0.1.0"]
            })
        },
        "D": {
            "0.1.4": wiz.definition.Definition({
                "identifier": "D",
                "version": "0.1.4",
                "requirements": ["E>=2"]
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "D",
                "version": "0.1.0"
            })
        },
        "E": {
            "2.3.0": wiz.definition.Definition({
                "identifier": "E",
                "version": "2.3.0",
                "requirements": ["F>=0.2"]
            })
        },
        "F": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "F",
                "version": "1.0.0"
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "F",
                "version": "0.9.0"
            })
        },
        "G": {
            "2.0.2": wiz.definition.Definition({
                "identifier": "G",
                "version": "2.0.2",
                "requirements": ["B<0.2.0"]
            }),
            "2.0.1": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.1"
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        resolver.compute_packages([Requirement("A"), Requirement("G")])

    assert (
        "The combined requirement 'D >0.1.0, ==0.1.0' could not be resolved "
        "from the following packages: ['B==0.1.0', 'C==0.3.2']."
    ) in str(error)

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 2
    assert spied_fetch_distance_mapping.call_count == 1
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 1
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 1
    assert spied_updated_by_distance.call_count == 1
    assert spied_extract_conflicting_nodes.call_count == 1
    assert spied_combined_requirements.call_count == 1
    assert spied_extract_parents.call_count == 1
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 0


def test_scenario_3(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    In a situation with several solutions, the solution which guaranty the
    conservation of the node nearest to the top level is chosen

    Root
     |
     |--(A): A==1.0.0
     |   |
     |   `--(B<1): B==0.9.0
     |
     `--(B): B==1.0.0
         |
         `--(A<1): A==0.9.0

    Expected: B==0.9.0, A==1.0.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "requirements": ["B<1"]
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.9.0"
            })
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0",
                "requirements": ["A<1"]
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.9.0"
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([Requirement("A"), Requirement("B")])

    assert len(packages) == 2
    assert packages[0].identifier == "B==0.9.0"
    assert packages[1].identifier == "A==1.0.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 6
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 2
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 2
    assert spied_updated_by_distance.call_count == 2
    assert spied_extract_conflicting_nodes.call_count == 4
    assert spied_combined_requirements.call_count == 4
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 1
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_4(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When only the identifier of a definition with several variants is required,
    all variants are added to the graph which is then divided into as many
    graphs as there are variants. The graph are ordered following the order of
    the variants and the first graph to resolve is the solution.

    Root
     |
     |--(A): A[V1]==1.0.0
     |   |
     |   `--(B >=1, <2): B==1.0.0
     |
     |--(A): A[V2]==1.0.0
     |   |
     |   `--(B >=2, <3): B==2.0.0
     |
     |--(A): A[V3]==1.0.0
     |   |
     |   `--(B >=3, <4): B==3.0.0
     |
     `--(A): A[V4]==1.0.0
         |
         `--(B >=4, <5): B==4.0.0

    Expected: B==4.0.0, A[V4]==1.0.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "variants": [
                    {
                        "identifier": "V4",
                        "requirements": ["B >=4, <5"]
                    },
                    {
                        "identifier": "V3",
                        "requirements": ["B >=3, <4"]
                    },
                    {
                        "identifier": "V2",
                        "requirements": ["B >=2, <3"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["B >=1, <2"]
                    }
                ]
            }),
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
            "4.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "4.0.0"
            }),
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([Requirement("A")])

    assert len(packages) == 2
    assert packages[0].identifier == "B==4.0.0"
    assert packages[1].identifier == "A[V4]==1.0.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 4
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 2
    assert spied_generate_variant_combinations.call_count == 1
    assert spied_trim_unreachable_from_graph.call_count == 1
    assert spied_updated_by_distance.call_count == 1
    assert spied_extract_conflicting_nodes.call_count == 1
    assert spied_combined_requirements.call_count == 1
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_5(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When a specific variant of a definition is required, only one graph with
    this exact variant is added to the graph.

    Root
     |
     `--(A[V1]): A[V1]==1.0.0
         |
         `--(B >=1, <2): B==1.0.0

    Expected: B==1.0.0, A[V1]==1.0.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "variants": [
                    {
                        "identifier": "V4",
                        "requirements": ["B >=4, <5"]
                    },
                    {
                        "identifier": "V3",
                        "requirements": ["B >=3, <4"]
                    },
                    {
                        "identifier": "V2",
                        "requirements": ["B >=2, <3"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["B >=1, <2"]
                    }
                ]
            }),
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
            "4.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "4.0.0"
            }),
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([Requirement("A[V1]")])

    assert len(packages) == 2
    assert packages[0].identifier == "B==1.0.0"
    assert packages[1].identifier == "A[V1]==1.0.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 1
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 1
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 0
    assert spied_updated_by_distance.call_count == 0
    assert spied_extract_conflicting_nodes.call_count == 0
    assert spied_combined_requirements.call_count == 0
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_6(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    Like the scenario 4, we end up with as many graph as there are variants. But
    the additional requirement makes the 2 first graphs fail so that only the
    3rd graph is resolved.

    Root
     |
     |--(A): A[V1]==1.0.0
     |   |
     |   `--(B >=1, <2): B==1.0.0
     |
     |--(A): A[V2]==1.0.0
     |   |
     |   `--(B >=2, <3): B==2.0.0
     |
     |--(A): A[V3]==1.0.0
     |   |
     |   `--(B >=3, <4): B==3.0.0
     |
     |--(A): A[V4]==1.0.0
     |   |
     |   `--(B >=4, <5): B==4.0.0
     |
     `--(B==2.*): B==2.0.0

    Expected: B==2.0.0, A[V2]==1.0.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "variants": [
                    {
                        "identifier": "V4",
                        "requirements": ["B >=4, <5"]
                    },
                    {
                        "identifier": "V3",
                        "requirements": ["B >=3, <4"]
                    },
                    {
                        "identifier": "V2",
                        "requirements": ["B >=2, <3"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["B >=1, <2"]
                    }
                ]
            }),
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
            "4.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "4.0.0"
            }),
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("B==2.*")
    ])

    assert len(packages) == 2
    assert packages[0].identifier == "B==2.0.0"
    assert packages[1].identifier == "A[V2]==1.0.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 3
    assert spied_fetch_distance_mapping.call_count == 6
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 3
    assert spied_compute_distance_mapping.call_count == 4
    assert spied_generate_variant_combinations.call_count == 1
    assert spied_trim_unreachable_from_graph.call_count == 3
    assert spied_updated_by_distance.call_count == 3
    assert spied_extract_conflicting_nodes.call_count == 3
    assert spied_combined_requirements.call_count == 3
    assert spied_extract_parents.call_count == 2
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_7(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    The combined requirement of packages can lead to the addition of a different
    package version to the graph during the conflict resolution process.

    Root
     |
     |--(A<=0.3.0): A==0.3.0
     |
     `--(B): B==0.1.0
         |
         `--(A !=0.3.0): A==1.0.0

    Expected: B==0.1.0, A==0.2.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0"
            }),
            "0.3.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.3.0"
            }),
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0"
            })
        },
        "B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["A !=0.3.0"]
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A<=0.3.0"), Requirement("B")
    ])

    assert len(packages) == 2
    assert packages[0].identifier == "B==0.1.0"
    assert packages[1].identifier == "A==0.2.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 5
    assert spied_extract_combinations.call_count == 2
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 3
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 3
    assert spied_updated_by_distance.call_count == 3
    assert spied_extract_conflicting_nodes.call_count == 3
    assert spied_combined_requirements.call_count == 3
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 2
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_8(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When conflicts parents are themselves conflicting, they should be discarded
    so that the next conflict is taken care of first.

    Root
     |
     |--(A): A==1.0.0
     |   |
     |   `--(C>=1): C== 1.0.0
     |
     `--(B): B==0.1.0
         |
         `--(A <1): A== 0.9.0
             |
             `--(C <1): C== 0.9.0

    Expected: C==0.9.0, A==0.9.0, B==0.1.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "requirements": ["C>=1"]
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.9.0",
                "requirements": ["C<1"]
            })
        },
        "B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["A<1"],

            })
        },
        "C": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "1.0.0"
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.9.0"
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("B")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "C==0.9.0"
    assert packages[1].identifier == "A==0.9.0"
    assert packages[2].identifier == "B==0.1.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 6
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 2
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 2
    assert spied_updated_by_distance.call_count == 2
    assert spied_extract_conflicting_nodes.call_count == 4
    assert spied_combined_requirements.call_count == 4
    assert spied_extract_parents.call_count == 2
    assert spied_remove_node_and_relink.call_count == 1
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_9(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    Like the scenario 8 with different order in the graph.

    Root
     |
     |--(A <1): A== 0.9.0
     |   |
     |   `--(C <1): C== 0.9.0
     |
     `--(B): B==0.1.0
         |
         `--(A): A== 1.0.0
             |
             `--(C>=1): C== 1.0.0

    Expected: C==0.9.0, B==0.1.0, A==0.9.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "requirements": ["C>=1"]
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.9.0",
                "requirements": ["C<1"]
            })
        },
        "B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["A"],

            })
        },
        "C": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "1.0.0"
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.9.0"
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A <1"), Requirement("B")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "B==0.1.0"
    assert packages[1].identifier == "C==0.9.0"
    assert packages[2].identifier == "A==0.9.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 6
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 2
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 2
    assert spied_updated_by_distance.call_count == 2
    assert spied_extract_conflicting_nodes.call_count == 4
    assert spied_combined_requirements.call_count == 4
    assert spied_extract_parents.call_count == 1
    assert spied_remove_node_and_relink.call_count == 1
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_10(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    Like the scenario 7, a new node is added to the graph during the conflict
    resolution process, but this time the new node leads to a division of the
    graph.

    Root
     |
     |--(A<=0.3.0): A==0.3.0
     |
     `--(B): B==0.1.0
         |
         `--(A !=0.3.0): A==1.0.0

    Expected: B==0.1.0, C[V3]==1.0.0, A==0.2.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0"
            }),
            "0.3.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.3.0"
            }),
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "requirements": ["C"]
            })
        },
        "B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["A !=0.3.0"]
            })
        },
        "C": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "1.0.0",
                "variants": [
                    {
                        "identifier": "V3",
                    },
                    {
                        "identifier": "V2",
                    },
                    {
                        "identifier": "V1",
                    }
                ]
            }),
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A<=0.3.0"), Requirement("B")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "B==0.1.0"
    assert packages[1].identifier == "C[V3]==1.0.0"
    assert packages[2].identifier == "A==0.2.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 2
    assert spied_fetch_distance_mapping.call_count == 6
    assert spied_extract_combinations.call_count == 2
    assert spied_resolve_conflicts.call_count == 2
    assert spied_compute_distance_mapping.call_count == 4
    assert spied_generate_variant_combinations.call_count == 1
    assert spied_trim_unreachable_from_graph.call_count == 3
    assert spied_updated_by_distance.call_count == 3
    assert spied_extract_conflicting_nodes.call_count == 3
    assert spied_combined_requirements.call_count == 3
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 2
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_11(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When a definition variant is present more than other variants from the same
    definition in the graph, it has priority.

    Root
     |
     |--(A): A[V1]==1.0.0
     |   |
     |   `--(B >=1, <2): B==1.0.0
     |
     |--(A): A[V2]==1.0.0
     |   |
     |   `--(B >=2, <3): B==2.0.0
     |
     |--(A): A[V3]==1.0.0
     |   |
     |   `--(B >=3, <4): B==3.0.0
     |
     `--(C): C
         |
         `--(A[V2]): A[V2]==1.0.0
             |
             `--(B >=2, <3): B==2.0.0

    Expected: C, B==2.0.0, A[V2]==1.0.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "variants": [
                    {
                        "identifier": "V3",
                        "requirements": ["B >=3, <4"]
                    },
                    {
                        "identifier": "V2",
                        "requirements": ["B >=2, <3"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["B >=1, <2"]
                    }
                ]
            })
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
        },
        "C": {
            "unknown": wiz.definition.Definition({
                "identifier": "C",
                "requirements": ["A[V2]"]
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("C")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "C"
    assert packages[1].identifier == "B==2.0.0"
    assert packages[2].identifier == "A[V2]==1.0.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 4
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 2
    assert spied_generate_variant_combinations.call_count == 1
    assert spied_trim_unreachable_from_graph.call_count == 1
    assert spied_updated_by_distance.call_count == 1
    assert spied_extract_conflicting_nodes.call_count == 1
    assert spied_combined_requirements.call_count == 1
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_12(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When two versions of a definition are added to the graph with all their
    respective variants, the conflict is resolved for the variant with the
    highest priority.

    Root
     |
     |--(A): A[V1]==1.0.0
     |   |
     |   `--(B >=1, <2): B==1.0.0
     |
     |--(A): A[V2]==1.0.0
     |   |
     |   `--(B >=2, <3): B==2.0.0
     |
     |--(A): A[V3]==1.0.0
     |   |
     |   `--(B >=3, <4): B==3.0.0
     |
     `--(C): C
         |
         |--(A==0.5.0): A[V1]==0.5.0
         |   |
         |   `--(B >=1, <2): B==1.0.0
         |
         |--(A==0.5.0): A[V2]==0.5.0
         |   |
         |   `--(B >=1, <2): B==1.0.0
         |
         `--(A==0.5.0): A[V3]==0.5.0
             |
             `--(B >=1, <2): B==1.0.0

    Expected: B==3.0.0, A[V3]==0.5.0, C

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "variants": [
                    {
                        "identifier": "V3",
                        "requirements": ["B >=3, <4"]
                    },
                    {
                        "identifier": "V2",
                        "requirements": ["B >=2, <3"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["B >=1, <2"]
                    }
                ]
            }),
            "0.5.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.5.0",
                "variants": [
                    {
                        "identifier": "V3",
                        "requirements": ["B >=3, <4"]
                    },
                    {
                        "identifier": "V2",
                        "requirements": ["B >=2, <3"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["B >=1, <2"]
                    }
                ]
            }),
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
        },
        "C": {
            "unknown": wiz.definition.Definition({
                "identifier": "C",
                "requirements": ["A==0.5.0"]
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("C")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "B==3.0.0"
    assert packages[1].identifier == "A[V3]==0.5.0"
    assert packages[2].identifier == "C"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 6
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 3
    assert spied_generate_variant_combinations.call_count == 1
    assert spied_trim_unreachable_from_graph.call_count == 2
    assert spied_updated_by_distance.call_count == 2
    assert spied_extract_conflicting_nodes.call_count == 3
    assert spied_combined_requirements.call_count == 3
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 1
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_13(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    Variant has priority over version. When a package is added with all its
    variants, if this package is required a second time in the tree for a
    different version, this requirement will be ignored if the variant with
    the highest priority does not have this version.

    Root
     |
     |--(A): A[V1]==1.0.0
     |   |
     |   `--(B >=1, <2): B==1.0.0
     |
     |--(A): A[V2]==1.0.0
     |   |
     |   `--(B >=2, <3): B==2.0.0
     |
     |--(A): A[V3]==1.0.0
     |   |
     |   `--(B >=3, <4): B==3.0.0
     |
     `--(C): C
         |
         `--(A==0.5.0): A[V1]==0.5.0
             |
             `--(B >=1, <2): B==1.0.0

    Expected: C, B==3.0.0, A[V3]==1.0.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "variants": [
                    {
                        "identifier": "V3",
                        "requirements": ["B >=3, <4"]
                    },
                    {
                        "identifier": "V2",
                        "requirements": ["B >=2, <3"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["B >=1, <2"]
                    }
                ]
            }),
            "0.5.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.5.0",
                "variants": [
                    {
                        "identifier": "V1",
                        "requirements": ["B >=1, <2"]
                    }
                ]
            }),
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
        },
        "C": {
            "unknown": wiz.definition.Definition({
                "identifier": "C",
                "requirements": ["A==0.5.0"]
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("C")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "C"
    assert packages[1].identifier == "B==3.0.0"
    assert packages[2].identifier == "A[V3]==1.0.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 4
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 2
    assert spied_generate_variant_combinations.call_count == 1
    assert spied_trim_unreachable_from_graph.call_count == 1
    assert spied_updated_by_distance.call_count == 1
    assert spied_extract_conflicting_nodes.call_count == 1
    assert spied_combined_requirements.call_count == 1
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_14(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When several packages with variants are added to the graph, the variant
    with the highest priority is returned for each package if no conflict
    appear.

    Root
     |
     |--(A): A[V1]
     |
     |--(A): A[V2]
     |
     |--(A): A[V3]
     |
     |--(B): B[V1]
     |
     |--(B): B[V2]
     |
     |--(B): B[V3]
     |
     |--(B): B[V4]
     |
     |--(C): C[V1]
     |
     `--(C): C[V2]

    Expected: C[V2], B[V4], A[V3]

    """
    definition_mapping = {
        "A": {
            "unknown": wiz.definition.Definition({
                "identifier": "A",
                "variants": [
                    {
                        "identifier": "V3",
                    },
                    {
                        "identifier": "V2",
                    },
                    {
                        "identifier": "V1",
                    }
                ]
            })
        },
        "B": {
            "unknown": wiz.definition.Definition({
                "identifier": "B",
                "variants": [
                    {
                        "identifier": "V4",
                    },
                    {
                        "identifier": "V3",
                    },
                    {
                        "identifier": "V2",
                    },
                    {
                        "identifier": "V1",
                    }
                ]
            })
        },
        "C": {
            "unknown": wiz.definition.Definition({
                "identifier": "C",
                "variants": [
                    {
                        "identifier": "V2",
                    },
                    {
                        "identifier": "V1",
                    }
                ]
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("B"), Requirement("C")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "C[V2]"
    assert packages[1].identifier == "B[V4]"
    assert packages[2].identifier == "A[V3]"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 2
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 2
    assert spied_generate_variant_combinations.call_count == 1
    assert spied_trim_unreachable_from_graph.call_count == 0
    assert spied_updated_by_distance.call_count == 0
    assert spied_extract_conflicting_nodes.call_count == 0
    assert spied_combined_requirements.call_count == 0
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_15(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When a package has a condition which is not fulfilled, it is not included
    in the resolved packages.

    Root
     |
     |--(A): A==1.1.0
     |
     `--(B): B==1.0.0 (Condition: A < 1)
         |
         `--(C > 0.1.0): C==0.5.0

    Expected: A==0.2.0

    """
    definition_mapping = {
        "A": {
            "1.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.1.0",
            }),
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
            }),
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0",
                "conditions": ["A < 1"],
                "requirements": ["C > 0.1.0"],
            })
        },
        "C": {
            "0.5.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.5.0"
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("B")
    ])

    assert len(packages) == 1
    assert packages[0].identifier == "A==1.1.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 1
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 1
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 0
    assert spied_updated_by_distance.call_count == 0
    assert spied_extract_conflicting_nodes.call_count == 0
    assert spied_combined_requirements.call_count == 0
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_16(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When a package has a condition which is fulfilled, it is properly included
    in the resolved packages with expected distance priority.

    Root
     |
     |--(A): A==1.1.0
     |
     `--(B): B==1.0.0 (Condition: A > 1)
         |
         `--(C > 0.1.0): C==0.5.0

    Expected: A==0.2.0, B==1.0.0, C==0.5.0

    """
    definition_mapping = {
        "A": {
            "1.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.1.0",
            }),
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
            }),
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0",
                "conditions": ["A > 1"],
                "requirements": ["C > 0.1.0"],

            })
        },
        "C": {
            "0.5.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.5.0"
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("B")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "C==0.5.0"
    assert packages[1].identifier == "B==1.0.0"
    assert packages[2].identifier == "A==1.1.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 1
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 1
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 0
    assert spied_updated_by_distance.call_count == 0
    assert spied_extract_conflicting_nodes.call_count == 0
    assert spied_combined_requirements.call_count == 0
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_17(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    A package condition can be fulfilled by packages deep in the graph.

    Root
     |
     |--(A): A==0.2.0 (Condition: E)
     |   |
     |   `--(C >=0.3.2, <1): C==0.3.2
     |
     `--(G): G==2.0.2
         |
         `--(B<0.2.0): B==0.1.0
             |
             `--(D>=0.1.0): D==0.1.4
                 |
                 `--(E>=2): E==2.3.0

    Expected: E==2.3.0, D==0.1.4, B==0.1.0, C==0.3.2, G==2.0.2, A==0.2.0

    The position of 'C==0.3.2' / 'G==2.0.2' can vary as they have similar
    priority numbers.

    """
    definition_mapping = {
        "A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "conditions": ["E"],
                "requirements": ["C >=0.3.2, <1"]
            }),
        },
        "B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["D >=0.1.0"],
            })
        },
        "C": {
            "0.3.2": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.3.2"
            })
        },
        "D": {
            "0.1.4": wiz.definition.Definition({
                "identifier": "D",
                "version": "0.1.4",
                "requirements": ["E >=2"]
            })
        },
        "E": {
            "2.3.0": wiz.definition.Definition({
                "identifier": "E",
                "version": "2.3.0"
            })
        },
        "G": {
            "2.0.2": wiz.definition.Definition({
                "identifier": "G",
                "version": "2.0.2",
                "requirements": ["B <0.2.0"]
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("G")
    ])

    assert len(packages) == 6
    assert packages[0].identifier == "E==2.3.0"
    assert packages[1].identifier == "D==0.1.4"
    assert packages[2].identifier == "B==0.1.0"

    # Order can vary cause both have priority of 2
    assert packages[3].identifier in ["C==0.3.2", "G==2.0.2"]
    assert packages[4].identifier in ["C==0.3.2", "G==2.0.2"]
    assert packages[4] != packages[3]

    assert packages[5].identifier == "A==0.2.0"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 1
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 1
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 0
    assert spied_updated_by_distance.call_count == 0
    assert spied_extract_conflicting_nodes.call_count == 0
    assert spied_combined_requirements.call_count == 0
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1


def test_scenario_18(
    spied_fetch_next_graph,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_parents,
    spied_remove_node_and_relink,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    For the same example as the scenario 17, if the condition can not be
    fulfilled, the package is not included in the resolved packages.

    Root
     |
     |--(A): A==0.2.0 (Condition: E, F)
     |   |
     |   `--(C >=0.3.2, <1): C==0.3.2
     |
     `--(G): G==2.0.2
         |
         `--(B<0.2.0): B==0.1.0
             |
             `--(D>=0.1.0): D==0.1.4
                 |
                 `--(E>=2): E==2.3.0

    Expected: E==2.3.0, D==0.1.4, B==0.1.0, G==2.0.2

    """
    definition_mapping = {
        "A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "conditions": ["E", "F"],
                "requirements": ["C >=0.3.2, <1"]
            }),
        },
        "B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["D >=0.1.0"],
            })
        },
        "C": {
            "0.3.2": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.3.2"
            })
        },
        "D": {
            "0.1.4": wiz.definition.Definition({
                "identifier": "D",
                "version": "0.1.4",
                "requirements": ["E >=2"]
            })
        },
        "E": {
            "2.3.0": wiz.definition.Definition({
                "identifier": "E",
                "version": "2.3.0"
            }),
        },
        "F": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "F",
                "version": "0.1.0"
            }),
        },
        "G": {
            "2.0.2": wiz.definition.Definition({
                "identifier": "G",
                "version": "2.0.2",
                "requirements": ["B <0.2.0"]
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("G")
    ])

    assert len(packages) == 4
    assert packages[0].identifier == "E==2.3.0"
    assert packages[1].identifier == "D==0.1.4"
    assert packages[2].identifier == "B==0.1.0"
    assert packages[3].identifier == "G==2.0.2"

    # Check spied functions / methods
    assert spied_fetch_next_graph.call_count == 1
    assert spied_fetch_distance_mapping.call_count == 1
    assert spied_extract_combinations.call_count == 1
    assert spied_resolve_conflicts.call_count == 1
    assert spied_compute_distance_mapping.call_count == 1
    assert spied_generate_variant_combinations.call_count == 0
    assert spied_trim_unreachable_from_graph.call_count == 0
    assert spied_updated_by_distance.call_count == 0
    assert spied_extract_conflicting_nodes.call_count == 0
    assert spied_combined_requirements.call_count == 0
    assert spied_extract_parents.call_count == 0
    assert spied_remove_node_and_relink.call_count == 0
    assert spied_extract_ordered_packages.call_count == 1
