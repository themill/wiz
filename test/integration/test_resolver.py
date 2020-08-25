# :coding: utf-8

import os

import pytest

import wiz.config
import wiz.definition
import wiz.graph
from wiz.utility import Requirement

#: Indicate whether spied call should be tested.
_CHECK_SPIED_CALL = True


@pytest.fixture(autouse=True)
def reset_configuration(mocker):
    """Ensure that no personal configuration is fetched during tests."""
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


@pytest.fixture()
def spied_fetch_next_combination(mocker):
    """Return spy mocker on 'wiz.graph.Resolver._fetch_next_combination'."""
    return mocker.spy(wiz.graph.Resolver, "_fetch_next_combination")


@pytest.fixture()
def spied_compute_combination(mocker):
    """Return spy mocker on 'wiz.graph.Resolver._compute_combination'."""
    return mocker.spy(wiz.graph.Resolver, "_compute_combination")


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
def spied_trim_invalid_from_graph(mocker):
    """Return spy mocker on 'wiz.graph.trim_invalid_from_graph'.
    """
    return mocker.spy(wiz.graph, "trim_invalid_from_graph")


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
def spied_extract_conflicting_requirements(mocker):
    """Return spy mocker on 'wiz.graph.extract_conflicting_requirements'."""
    return mocker.spy(wiz.graph, "extract_conflicting_requirements")


@pytest.fixture()
def spied_relink_parents(mocker):
    """Return spy mocker on 'wiz.graph.relink_parents'."""
    return mocker.spy(wiz.graph, "relink_parents")


@pytest.fixture()
def spied_extract_ordered_packages(mocker):
    """Return spy mocker on 'wiz.graph.extract_ordered_packages'."""
    return mocker.spy(wiz.graph, "extract_ordered_packages")


def test_scenario_1(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 6
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 3
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 1
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 2
        assert spied_combined_requirements.call_count == 1
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 1
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_2(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
        "The dependency graph could not be resolved due to the "
        "following requirement conflicts:\n"
        "  * D >0.1.0 \t[B==0.1.0]\n"
        "  * D ==0.1.0 \t[C==0.3.2]"
    ) in str(error.value)

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 2
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 1
        assert spied_combined_requirements.call_count == 3
        assert spied_extract_conflicting_requirements.call_count == 1
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 0


def test_scenario_3(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 10
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 3
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 1
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 3
        assert spied_extract_conflicting_nodes.call_count == 4
        assert spied_combined_requirements.call_count == 3
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 1
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_4(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 5
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 3
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 1
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 3
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_5(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_6(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 3
        assert spied_compute_combination.call_count == 3
        assert spied_fetch_distance_mapping.call_count == 13
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 3
        assert spied_compute_distance_mapping.call_count == 7
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 3
        assert spied_trim_invalid_from_graph.call_count == 3
        assert spied_updated_by_distance.call_count == 2
        assert spied_extract_conflicting_nodes.call_count == 2
        assert spied_combined_requirements.call_count == 2
        assert spied_extract_conflicting_requirements.call_count == 2
        assert spied_relink_parents.call_count == 9
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_7(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    The combined requirement of packages can lead to the addition of a different
    package version to the graph during the conflict resolution process.

    Root
     |
     |--(A<=0.3.0): A==0.3.0
     |
     |--(B): B==0.1.0
     |   |
     |   `--(A !=0.3.0): A==1.0.0
     |
     `--(C): C==0.1.0
         |
         `--(A <1): A==0.9.0

    Expected: C==0.1.0, B==0.1.0, A==0.2.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0"
            }),
            "0.9.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.9.0"
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
        },
        "C": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.1.0",
                "requirements": ["A <1"]
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A<=0.3.0"), Requirement("B"), Requirement("C")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "C==0.1.0"
    assert packages[1].identifier == "B==0.1.0"
    assert packages[2].identifier == "A==0.2.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 12
        assert spied_extract_combinations.call_count == 2
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 4
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 3
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 3
        assert spied_extract_conflicting_nodes.call_count == 4
        assert spied_combined_requirements.call_count == 4
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 3
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_8(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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

    Expected: A==0.9.0, C==0.9.0, B==0.1.0

    The position of 'C==0.9.0' / 'B==0.1.0' can vary as they have similar
    priority numbers.

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

    assert packages[0].identifier in ["C==0.9.0", "B==0.1.0"]
    assert packages[1].identifier in ["C==0.9.0", "B==0.1.0"]
    assert packages[0] != packages[1]

    assert packages[2].identifier == "A==0.9.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 9
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 3
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 1
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 4
        assert spied_extract_conflicting_nodes.call_count == 4
        assert spied_combined_requirements.call_count == 4
        assert spied_extract_conflicting_requirements.call_count == 2
        assert spied_relink_parents.call_count == 1
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_9(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 8
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 3
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 1
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 2
        assert spied_extract_conflicting_nodes.call_count == 4
        assert spied_combined_requirements.call_count == 2
        assert spied_extract_conflicting_requirements.call_count == 1
        assert spied_relink_parents.call_count == 1
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_10(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 2
        assert spied_compute_combination.call_count == 2
        assert spied_fetch_distance_mapping.call_count == 10
        assert spied_extract_combinations.call_count == 2
        assert spied_resolve_conflicts.call_count == 2
        assert spied_compute_distance_mapping.call_count == 4
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 2
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 3
        assert spied_extract_conflicting_nodes.call_count == 3
        assert spied_combined_requirements.call_count == 3
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 4
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_11(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
            "-": wiz.definition.Definition({
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 5
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 3
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 1
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 2
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_12(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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

    Expected: C, B==3.0.0, A[V3]==0.5.0

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
            "-": wiz.definition.Definition({
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
    assert packages[2].identifier == "A[V3]==0.5.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 10
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 4
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 2
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 2
        assert spied_extract_conflicting_nodes.call_count == 2
        assert spied_combined_requirements.call_count == 2
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 5
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_13(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When computing a graph combination, all variant nodes that should not be
    included are removed from the graph. During the removal process, parents
    are relinked to ensure that all requirements are still respected. If a
    parent cannot be linked to any existing nodes in the graph, the combination
    cannot be resolved.

    In this example, "A[V3]==0.1.0" is being computed first so all other nodes
    belonging to the definition identifier "A" are removed, which makes it
    impossible for "C"'s requirement to be fulfilled.

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

    Expected: C, B==1.0.0, A[V1]==0.5.0

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
            "-": wiz.definition.Definition({
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
    assert packages[1].identifier == "B==1.0.0"
    assert packages[2].identifier == "A[V1]==0.5.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 3
        assert spied_compute_combination.call_count == 3
        assert spied_fetch_distance_mapping.call_count == 10
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 4
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 2
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 2
        assert spied_extract_conflicting_nodes.call_count == 2
        assert spied_combined_requirements.call_count == 2
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 9
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_14(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
            "-": wiz.definition.Definition({
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
            "-": wiz.definition.Definition({
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
            "-": wiz.definition.Definition({
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 4
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 2
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 1
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 6
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_15(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    If a definition variant contains an error, the graph combinations list will
    be optimized to only keep it once and drop all other combinations which
    attempt to use it.

    Root
     |
     |--(A): A[V1]
     |
     |--(A): A[V2]
     |
     |--(A): A[V3]
     |   |
     |   `--(incorrect): ERROR!
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

    Expected: C[V2], B[V4], A[V2]

    """
    definition_mapping = {
        "A": {
            "-": wiz.definition.Definition({
                "identifier": "A",
                "variants": [
                    {
                        "identifier": "V3",
                        "requirements": ["incorrect"]
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
            "-": wiz.definition.Definition({
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
            "-": wiz.definition.Definition({
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
    assert packages[2].identifier == "A[V2]"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 9
        assert spied_compute_combination.call_count == 9
        assert spied_fetch_distance_mapping.call_count == 21
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 2
        assert spied_compute_distance_mapping.call_count == 10
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 9
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 54
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_16(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    For the same example as scenario 15, if the package 'A[V3]' has a
    conflicting requirement instead of an error, all other combinations which
    include this package would be preserved.

    Root
     |
     |--(A): A[V1]
     |
     |--(A): A[V2]
     |
     |--(A): A[V3]
     |   |
     |   `--(D>=1): D==1.0.0
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
     |--(C): C[V2]
     |
     `--(D<1): D==0.1.0

    Expected: C[V2], B[V4], A[V2], D==0.1.0

    """
    definition_mapping = {
        "A": {
            "-": wiz.definition.Definition({
                "identifier": "A",
                "variants": [
                    {
                        "identifier": "V3",
                        "requirements": ["D>=1"]
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
            "-": wiz.definition.Definition({
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
            "-": wiz.definition.Definition({
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
        },
        "D": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "D",
                "version": "1.0.0"
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "D",
                "version": "0.1.0"
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("A"), Requirement("B"), Requirement("C"), Requirement("D<1")
    ])

    assert len(packages) == 4
    assert packages[0].identifier == "D==0.1.0"
    assert packages[1].identifier == "C[V2]"
    assert packages[2].identifier == "B[V4]"
    assert packages[3].identifier == "A[V2]"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 9
        assert spied_compute_combination.call_count == 9
        assert spied_fetch_distance_mapping.call_count == 22
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 2
        assert spied_compute_distance_mapping.call_count == 11
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 9
        assert spied_trim_invalid_from_graph.call_count == 1
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 1
        assert spied_combined_requirements.call_count == 1
        assert spied_extract_conflicting_requirements.call_count == 1
        assert spied_relink_parents.call_count == 54
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_17(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_18(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_19(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_20(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    For the same example as the scenario 19, if the condition can not be
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
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_21(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    A package which has been added to the graph when its conditions were
    fulfilled will be removed once conflict resolution has resulted in the
    removal of a node the package is conditioned by.

    Root
     |
     |--(A): A==0.2.0 (Condition: E)
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

    Expected: F==1.0.0, D==0.1.0, B==0.1.0, G==2.0.2

    """
    definition_mapping = {
        "A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "requirements": ["C>=0.3.2, <1"],
                "conditions": ["E"]
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

    assert len(packages) == 4
    assert packages[0].identifier == "F==1.0.0"
    assert packages[1].identifier == "D==0.1.0"
    assert packages[2].identifier == "B==0.1.0"
    assert packages[3].identifier == "G==2.0.2"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 8
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 5
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 2
        assert spied_trim_invalid_from_graph.call_count == 3
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 2
        assert spied_combined_requirements.call_count == 1
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 1
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_22(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Fail to compute packages for the following graph.

    Root
     |
     `--(A): Namespace1::A==0.1.0 || Namespace2::A==0.2.0

    Expected: Unable to guess default namespace for 'A'

    """
    definition_mapping = {
        "__namespace__": {
            "A": ["Namespace1", "Namespace2"]
        },
        "Namespace1::A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "namespace": "Namespace1"
            })
        },
        "Namespace2::A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "namespace": "Namespace2"
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        resolver.compute_packages([Requirement("A")])

    assert (
        "The dependency graph could not be resolved due to the following "
        "error(s):\n"
        "  * root: Cannot guess default namespace for 'A' [available: "
        "Namespace1, Namespace2]."
    ) in str(error.value)

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 2
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 0


def test_scenario_23(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When a definition is found, its namespace is used to give hint when looking
    for default namespace belonging to the other definitions.

    Root
     |
     |--(A): Namespace1::A
     |
     |--(B): Namespace1::B==0.1.0 || Namespace2::B==0.2.0
     |
     |--(C): Namespace3::C==0.1.0 || Namespace4::C==0.2.0
     |
     `--(D): Namespace4::D

    Expected:
    Namespace4::D, Namespace4::C==0.2.0, Namespace1::B==0.1.0,  Namespace1::A

    """
    definition_mapping = {
        "__namespace__": {
            "A": ["Namespace1"],
            "B": ["Namespace1", "Namespace2"],
            "C": ["Namespace3", "Namespace4"],
            "D": ["Namespace4"],
        },
        "Namespace1::A": {
            "-": wiz.definition.Definition({
                "identifier": "A",
                "namespace": "Namespace1"
            })
        },
        "Namespace1::B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "namespace": "Namespace1"
            })
        },
        "Namespace2::B": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.2.0",
                "namespace": "Namespace2"
            })
        },
        "Namespace3::C": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.1.0",
                "namespace": "Namespace3"
            })
        },
        "Namespace4::C": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.2.0",
                "namespace": "Namespace4"
            })
        },
        "Namespace4::D": {
            "-": wiz.definition.Definition({
                "identifier": "D",
                "namespace": "Namespace4"
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    packages = resolver.compute_packages([
        Requirement("A"), Requirement("B"), Requirement("C"), Requirement("D")
    ])
    assert len(packages) == 4
    assert packages[0].identifier == "Namespace4::D"
    assert packages[1].identifier == "Namespace4::C==0.2.0"
    assert packages[2].identifier == "Namespace1::B==0.1.0"
    assert packages[3].identifier == "Namespace1::A"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_24(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When a definition exists with and without a namespace, the one without a
    namespace is selected automatically by default.

    Root
     |
     `--(A): A==0.1.0 || Namespace1::A==0.2.0

    Expected: A==0.1.0

    """
    definition_mapping = {
        "__namespace__": {
            "A": ["Namespace1"]
        },
        "A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0"
            })
        },
        "Namespace1::A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "namespace": "Namespace1"
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    packages = resolver.compute_packages([Requirement("A")])

    assert len(packages) == 1
    assert packages[0].identifier == "A==0.1.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_25(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When a definition exists with and without a namespace, other definitions
    using the same namespace within the request will lead to the selection of
    the one with the namespace.

    Root
     |
     |--(A): A==0.1.0 || Namespace1::A==0.2.0
     |
     `--(B): Namespace1::B==0.1.0

    Expected: Namespace1::B==0.1.0, Namespace1::A==0.1.0

    """
    definition_mapping = {
        "__namespace__": {
            "A": ["Namespace1"],
            "B": ["Namespace1"]
        },
        "A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0"
            })
        },
        "Namespace1::A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "namespace": "Namespace1"
            })
        },
        "Namespace1::B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "namespace": "Namespace1"
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    packages = resolver.compute_packages([Requirement("A"), Requirement("B")])

    assert len(packages) == 2
    assert packages[0].identifier == "Namespace1::B==0.1.0"
    assert packages[1].identifier == "Namespace1::A==0.2.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_26(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    When a definition exists with and without a namespace, the one without a
    namespace can be explicitly called.

    Root
     |
     |--(::A): A==0.1.0 || Namespace1::A==0.2.0
     |
     `--(B): Namespace1::B==0.1.0

    Expected: Namespace1::B==0.1.0, A==0.1.0

    """
    definition_mapping = {
        "__namespace__": {
            "A": ["Namespace1"],
            "B": ["Namespace1"]
        },
        "A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0"
            })
        },
        "Namespace1::A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "namespace": "Namespace1"
            })
        },
        "Namespace1::B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "namespace": "Namespace1"
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    packages = resolver.compute_packages([Requirement("::A"), Requirement("B")])

    assert len(packages) == 2
    assert packages[0].identifier == "Namespace1::B==0.1.0"
    assert packages[1].identifier == "A==0.1.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_27(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    A package which has been added to the graph when its conditions were
    fulfilled will be kept when conflict resolution has resulted in the
    removal of a node the package is conditioned as long as another node which
    fulfill the same condition remains in the graph.

    Root
     |
     |--(A): A==0.1.0 (Condition: B)
     |   |
     |   `--(B >= 0.1.0, < 1) B==0.1.0
     |
     `--(B): B==1.0.0

    Expected: B==0.1.0, A==0.1.0

    """
    definition_mapping = {
        "A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "conditions": ["B"],
                "requirements": ["B >= 0.1.0, < 1"],
            })
        },
        "B": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.0.0"
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0"
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    packages = resolver.compute_packages([Requirement("A"), Requirement("B")])

    assert len(packages) == 2
    assert packages[0].identifier == "B==0.1.0"
    assert packages[1].identifier == "A==0.1.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 6
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 2
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 1
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 2
        assert spied_extract_conflicting_nodes.call_count == 2
        assert spied_combined_requirements.call_count == 2
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 1
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_28(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    Like for the scenario 22, the package "A" has several namespaces available.
    But as one of the namespace is identical to the definition identifier, it
    will be selected by default.

    Root
     |
     `--(A): Namespace1::A==0.1.0 || A::A==0.2.0

    Expected: A::A==0.2.0

    """
    definition_mapping = {
        "__namespace__": {
            "A": ["Namespace1", "A"]
        },
        "Namespace1::A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "namespace": "Namespace1"
            })
        },
        "A::A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "namespace": "A"
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    packages = resolver.compute_packages([Requirement("A")])

    assert len(packages) == 1
    assert packages[0].identifier == "A::A==0.2.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 1
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 0
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_29(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    Like for the scenario 7, the combined requirement of packages can lead to
    the addition of a different package version to the graph during the conflict
    resolution process. But when it happens with a definition with variant, all
    variants must be added.

    Root
     |
     |--(B): B==0.1.0
     |   |
     |   |--(A !=0.3.0): A[V1]==1.0.0
     |   |
     |   `--(A !=0.3.0): A[V2]==1.0.0
     |
     `--(C): C==0.1.0
         |
         |--(A <=0.3.0): A[V3]==0.3.0
         |
         |--(A <=0.3.0): A[V2]==0.3.0
         |
         `--(A <=0.3.0): A[V1]==0.3.0

    Expected: C==0.1.0, A[V1]==0.2.0, B==0.1.0

    """
    definition_mapping = {
        "A": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.0.0",
                "variants": [
                    {
                        "identifier": "V2"
                    },
                    {
                        "identifier": "V1"
                    }
                ]
            }),
            "0.3.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.3.0",
                "variants": [
                    {
                        "identifier": "V3"
                    },
                    {
                        "identifier": "V2"
                    },
                    {
                        "identifier": "V1"
                    }
                ]
            }),
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "variants": [
                    {
                        "identifier": "V2",
                        "requirements": ["incorrect"]
                    },
                    {
                        "identifier": "V1",
                    }
                ]
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
            "0.1.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.1.0",
                "requirements": ["A <=0.3.0"]
            })
        }
    }

    resolver = wiz.graph.Resolver(definition_mapping)
    packages = resolver.compute_packages([
        Requirement("B"), Requirement("C")
    ])

    assert len(packages) == 3
    assert packages[0].identifier == "C==0.1.0"
    assert packages[1].identifier == "A[V1]==0.2.0"
    assert packages[2].identifier == "B==0.1.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 3
        assert spied_compute_combination.call_count == 3
        assert spied_fetch_distance_mapping.call_count == 10
        assert spied_extract_combinations.call_count == 2
        assert spied_resolve_conflicts.call_count == 2
        assert spied_compute_distance_mapping.call_count == 5
        assert spied_generate_variant_combinations.call_count == 2
        assert spied_trim_unreachable_from_graph.call_count == 3
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 1
        assert spied_combined_requirements.call_count == 1
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 7
        assert spied_extract_ordered_packages.call_count == 1


def test_scenario_30(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Fail to compute packages for the following graph.

    If a definition contains an error, it will lead to the failure of the graph
    when no other possible combinations are available.

    Root
     |
     |--(A): A==0.1.0
     |   |
     |   `--(incorrect): ERROR!
     |
     `--(B): B==0.1.0

    Expected: The requirement 'incorrect' could not be resolved.

    """
    definition_mapping = {
        "A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "requirements": ["incorrect"]
            }),
        },
        "B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        resolver.compute_packages([Requirement("A"), Requirement("B")])

    assert (
        "The dependency graph could not be resolved due to the following "
        "error(s):\n"
        "  * A==0.1.0: The requirement 'incorrect' could not be resolved."
    ) in str(error.value)

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 2
        assert spied_compute_combination.call_count == 1
        assert spied_fetch_distance_mapping.call_count == 1
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 1
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 0
        assert spied_extract_ordered_packages.call_count == 0


def test_scenario_31(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Fail to compute packages for the following graph.

    Like scenario 15, when a definition variant contains an error, the next
    combination will try to detect and raise when this erroneous node is
    encountered again. However, when there are no combination that can be
    resolved, it will still fail.

    Root
     |
     |--(A): A[V1]==0.1.0
     |   |
     |   `--(C): C==0.1.0
     |       |
     |       `--(incorrect): ERROR!
     |
     |--(A): A[V2]==0.1.0
     |   |
     |   `--(C): C==0.1.0
     |       |
     |       `--(incorrect): ERROR!
     |
     `--(B): B==0.1.0

    Expected: The requirement 'incorrect' could not be resolved.

    """
    definition_mapping = {
        "A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "variants": [
                    {
                        "identifier": "V2",
                        "requirements": ["C"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["C"]

                    },
                ]
            }),
        },
        "B": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
            })
        },
        "C": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.1.0",
                "requirements": ["incorrect"]
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        resolver.compute_packages([Requirement("A"), Requirement("B")])

    assert (
        "The dependency graph could not be resolved due to the following "
        "error(s):\n"
        "  * C==0.1.0: The requirement 'incorrect' could not be resolved."
    ) in str(error.value)

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 3
        assert spied_compute_combination.call_count == 2
        assert spied_fetch_distance_mapping.call_count == 6
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 3
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 2
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 0
        assert spied_combined_requirements.call_count == 0
        assert spied_extract_conflicting_requirements.call_count == 0
        assert spied_relink_parents.call_count == 2
        assert spied_extract_ordered_packages.call_count == 0


def test_scenario_32(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Fail to compute packages for the following graph.

    When a conflict is detected, it is being stored to prevent resolving a
    combination graph which involve the same conflict. However, when there are
    no combination that can be resolved, it will still fail.

    Root
     |
     |--(A): A[V1]==0.1.0
     |   |
     |   `--(C): C==0.1.0
     |       |
     |       `--(B<1): B==0.1.0
     |
     |--(A): A[V2]==0.1.0
     |   |
     |   `--(C): C==0.1.0
     |       |
     |       `--(B<1): B==0.1.0
     |
     `--(B>1): B==1.1.0

    Expected: Unable to compute due to requirement compatibility between
    'B<1' and 'B>1'.

    """
    definition_mapping = {
        "A": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.1.0",
                "variants": [
                    {
                        "identifier": "V2",
                        "requirements": ["C"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["C"]

                    },
                ]
            }),
        },
        "B": {
            "1.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.1.0",
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
            })
        },
        "C": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.1.0",
                "requirements": ["B<1"]
            })
        },
    }

    resolver = wiz.graph.Resolver(definition_mapping)

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        resolver.compute_packages([Requirement("A"), Requirement("B>1")])

    assert (
        "The dependency graph could not be resolved due to the "
        "following requirement conflicts:\n"
        "  * B >1 \t[root]\n"
        "  * B <1 \t[C==0.1.0]"
    ) in str(error.value)

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 3
        assert spied_compute_combination.call_count == 2
        assert spied_fetch_distance_mapping.call_count == 6
        assert spied_extract_combinations.call_count == 1
        assert spied_resolve_conflicts.call_count == 1
        assert spied_compute_distance_mapping.call_count == 3
        assert spied_generate_variant_combinations.call_count == 1
        assert spied_trim_unreachable_from_graph.call_count == 2
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 1
        assert spied_extract_conflicting_nodes.call_count == 1
        assert spied_combined_requirements.call_count == 2
        assert spied_extract_conflicting_requirements.call_count == 1
        assert spied_relink_parents.call_count == 2
        assert spied_extract_ordered_packages.call_count == 0


def test_scenario_33(
    spied_fetch_next_combination,
    spied_compute_combination,
    spied_fetch_distance_mapping,
    spied_extract_combinations,
    spied_resolve_conflicts,
    spied_compute_distance_mapping,
    spied_generate_variant_combinations,
    spied_trim_unreachable_from_graph,
    spied_trim_invalid_from_graph,
    spied_updated_by_distance,
    spied_extract_conflicting_nodes,
    spied_combined_requirements,
    spied_extract_conflicting_requirements,
    spied_relink_parents,
    spied_extract_ordered_packages
):
    """Compute packages for the following graph.

    Like scenario 2, the graph resolution will fail with the all node versions
    fetched in the graph. However, it can drop down the version of package
    with conflicting requirement to a version which does not conflict.

    Root
     |
     |--(A): A==0.2.0
     |   |
     |   `--(C >=0.3.0, <1): C==0.3.2
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

    Expected: F==1.0.0, E==2.3.0, D==0.1.4, B==0.1.0, G==2.0.2, C==0.3.0
    A==0.2.0

    The position of 'C==0.3.0' / 'G==2.0.2' and 'F==1.0.0' / 'E==2.3.0' can
    vary as they have similar priority numbers.

    """
    definition_mapping = {
        "A": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "0.2.0",
                "requirements": ["C>=0.3.0, <1"]
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
            "0.3.2": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.3.2",
                "requirements": ["D==0.1.0"]
            }),
            "0.3.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.3.0"
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

    assert len(packages) == 7

    # Order can vary cause both have priority of 5
    assert packages[0].identifier in ["F==1.0.0", "E==2.3.0"]
    assert packages[1].identifier in ["F==1.0.0", "E==2.3.0"]
    assert packages[0] != packages[1]

    assert packages[2].identifier == "D==0.1.4"

    # Order can vary cause both have priority of 2
    assert packages[3].identifier in ["G==2.0.2", "B==0.1.0"]
    assert packages[4].identifier in ["G==2.0.2", "B==0.1.0"]
    assert packages[3] != packages[4]

    assert packages[5].identifier == "C==0.3.0"
    assert packages[6].identifier == "A==0.2.0"

    # Check spied functions / methods
    if _CHECK_SPIED_CALL:
        assert spied_fetch_next_combination.call_count == 2
        assert spied_compute_combination.call_count == 2
        assert spied_fetch_distance_mapping.call_count == 4
        assert spied_extract_combinations.call_count == 2
        assert spied_resolve_conflicts.call_count == 2
        assert spied_compute_distance_mapping.call_count == 2
        assert spied_generate_variant_combinations.call_count == 0
        assert spied_trim_unreachable_from_graph.call_count == 0
        assert spied_trim_invalid_from_graph.call_count == 0
        assert spied_updated_by_distance.call_count == 2
        assert spied_extract_conflicting_nodes.call_count == 2
        assert spied_combined_requirements.call_count == 4
        assert spied_extract_conflicting_requirements.call_count == 1
        assert spied_relink_parents.call_count == 1
        assert spied_extract_ordered_packages.call_count == 1
