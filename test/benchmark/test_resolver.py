# :coding: utf-8

import os

import pytest
import wiz.config
from wiz.utility import Requirement


@pytest.fixture(autouse=True)
def reset_configuration(mocker):
    """Ensure that no personal configuration is fetched during tests."""
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


def test_scenario_1(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("G")])

    benchmark(_resolve)


def test_scenario_2(benchmark):
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

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([Requirement("A"), Requirement("G")])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_3(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("B")])

    benchmark(_resolve)


def test_scenario_4(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A")])

    benchmark(_resolve)


def test_scenario_5(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A[V1]")])

    benchmark(_resolve)


def test_scenario_6(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("B==2.*")])

    benchmark(_resolve)


def test_scenario_7(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([
            Requirement("A<=0.3.0"), Requirement("B"), Requirement("C")
        ])

    benchmark(_resolve)


def test_scenario_8(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("B")])

    benchmark(_resolve)


def test_scenario_9(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A <1"), Requirement("B")])

    benchmark(_resolve)


def test_scenario_10(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A<=0.3.0"), Requirement("B")])

    benchmark(_resolve)


def test_scenario_11(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("C")])

    benchmark(_resolve)


def test_scenario_12(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("C")])

    benchmark(_resolve)


def test_scenario_13(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("C")])

    benchmark(_resolve)


def test_scenario_14(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([
            Requirement("A"), Requirement("B"), Requirement("C")
        ])

    benchmark(_resolve)


def test_scenario_15(benchmark):
    """Compute packages for the following graph.

    If a definition variant contains an error, the combinations containing the
    error are discarded until a variant of the definition without errors is
    picked.

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
     |   |
     |   `--(incorrect): ERROR!
     |
     |--(C): C[V1]
     |
     `--(C): C[V2]

    Expected: C[V2], B[V3], A[V3]

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
                        "requirements": ["incorrect"]
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([
            Requirement("A"), Requirement("B"), Requirement("C")
        ])

    benchmark(_resolve)


def test_scenario_16(benchmark):
    """Compute packages for the following graph.

    For the same example as scenario 15, if the package 'B[V4]' has a
    conflicting requirement instead of an error, the combinations containing the
    conflict are discarded until a variant of the definition without conflicts
    is picked.

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
     |   |
     |   `--(D>=1): D==1.0.0
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
                        "requirements": ["D>=1"]
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([
            Requirement("A"), Requirement("B"), Requirement("C"),
            Requirement("D<1")
        ])

    benchmark(_resolve)


def test_scenario_17(benchmark):
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

    Expected: A==1.1.0

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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("B")])

    benchmark(_resolve)


def test_scenario_18(benchmark):
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

    Expected: A==1.1.0, B==1.0.0, C==0.5.0

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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("B")])

    benchmark(_resolve)


def test_scenario_19(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("G")])

    benchmark(_resolve)


def test_scenario_20(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("G")])

    benchmark(_resolve)


def test_scenario_21(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("G")])

    benchmark(_resolve)


def test_scenario_22(benchmark):
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

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([Requirement("A")])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_23(benchmark):
    """Compute packages for the following graph.

    Initial namespace counter can be used to give hint when looking
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

    def _resolve():
        """Resolve context."""
        requirements = [
            Requirement("A"), Requirement("B"), Requirement("C"),
            Requirement("D")
        ]
        namespace_counter = wiz.utility.compute_namespace_counter(
            requirements, definition_mapping
        )

        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages(
            requirements, namespace_counter=namespace_counter
        )

    benchmark(_resolve)


def test_scenario_24(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A")])

    benchmark(_resolve)


def test_scenario_25(benchmark):
    """Compute packages for the following graph.

    When a definition exists with and without a namespace, other definitions
    using the same namespace within the request will lead to the selection of
    the one with the namespace if an initial counter is being used.

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

    def _resolve():
        """Resolve context."""
        requirements = [Requirement("A"), Requirement("B")]
        namespace_counter = wiz.utility.compute_namespace_counter(
            requirements, definition_mapping
        )

        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages(
            requirements, namespace_counter=namespace_counter
        )

    benchmark(_resolve)


def test_scenario_26(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("::A"), Requirement("B")])

    benchmark(_resolve)


def test_scenario_27(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("B")])

    benchmark(_resolve)


def test_scenario_28(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A")])

    benchmark(_resolve)


def test_scenario_29(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("B"), Requirement("C")])

    benchmark(_resolve)


def test_scenario_30(benchmark):
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

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([Requirement("A"), Requirement("B")])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_31(benchmark):
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

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([Requirement("A"), Requirement("B")])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_32(benchmark):
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

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([Requirement("A"), Requirement("B>1")])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_33(benchmark):
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

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([Requirement("A"), Requirement("G")])

    benchmark(_resolve)


def test_scenario_34(benchmark):
    """Compute packages for the following graph.

    Like scenario 13, parents are relinked when computing a graph combination
    to ensure that all requirements are still respected.

    But in this example, two requirements are explicitly requesting conflicting
    variants: "A[V2]" and "A[V3]".

    Root
     |
     |--(A[V3]): A[V3]==1.0.0
     |   |
     |   `--(B >=3, <4): B==3.0.0
     |
     `--(C): C
         |
         `--(A[V2]): A[V2]==1.0.0
             |
             `--(B >=1, <2): B==1.0.0

    Expected: Unable to compute due to requirement compatibility between
    'A[V2]' and 'A[V3]'.

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
                    }
                ]
            })
        },
        "B": {
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
        },
        "C": {
            "-": wiz.definition.Definition({
                "identifier": "C",
                "requirements": ["A[V2]"]
            })
        }
    }

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([Requirement("A[V3]"), Requirement("C")])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_35(benchmark):
    """Compute packages for the following graph.

    Like scenario 34, two requirements are explicitly requesting conflicting
    variants: "A[V2]" and "A[V3]".

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
     |--(C): C
     |   |
     |   `--(A[V2]): A[V2]==1.0.0
     |       |
     |       `--(B >=1, <2): B==1.0.0
     |
     `--(D): D==0.1.0
         |
         `--(A[V3]): A[V3]==1.0.0

    Expected: Unable to compute due to requirement compatibility between
    'A[V2]' and 'A[V3]'.

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
        },
        "D": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "D",
                "version": "0.1.0",
                "requirements": ["A[V3]"]
            })
        }
    }

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([
                Requirement("A"), Requirement("C"), Requirement("D")
            ])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_36(benchmark):
    """Compute packages for the following graph.

    When parents of conflicting nodes are themselves conflicting, we attempt to
    resolve the conflicting parents before resolving the children. In this
    case, one of the conflicting children disappears while resolving parent
    conflicts.

    Root
     |
     |--(A==1.2.*): A==1.2.0
     |   |
     |   `--(B<1): B==0.1.0
     |
     `--(B): B==1.2.3
         |
         `--(A==1.4.*): A==1.4.8

    Expected: B==0.1.0, A==1.2.0

    """
    definition_mapping = {
        "A": {
            "1.4.8": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.4.8"
            }),
            "1.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.2.0",
                "requirements": ["B<1"]
            })
        },
        "B": {
            "1.2.3": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.2.3",
                "requirements": ["A==1.4.*"]
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
            })
        },
    }

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([
                Requirement("A==1.2.*"), Requirement("B")
            ])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_37(benchmark):
    """Fail to compute packages for the following graph.

    Like scenario 36, when parents of conflicting nodes are themselves
    conflicting, we attempt to resolve the conflicting parents before resolving
    the children. In this case, the parent conflicts does not remove the
    children conflicts.

    Root
     |
     |--(A==1.2.*): A==1.2.0
     |   |
     |   `--(B): B==1.2.3
     |
     `--(B<1): B==0.1.0
         |
         `--(A==1.4.*): A==1.4.8

    Expected: Unable to compute due to requirement compatibility between
    'A==1.4.*' and 'A==1.2.* '.

    """
    definition_mapping = {
        "A": {
            "1.4.8": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.4.8"
            }),
            "1.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.2.0",
                "requirements": ["B"]
            })
        },
        "B": {
            "1.2.3": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.2.3",
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["A==1.4.*"]
            })
        },
    }

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([
                Requirement("A==1.2.*"), Requirement("B<1")
            ])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_38(benchmark):
    """Fail to compute packages for the following graph.

    Like scenario 37, when parents of conflicting nodes are themselves
    conflicting, we attempt to resolve the conflicting parents before resolving
    the children. In this case, the parent conflicts cannot be solved.

    Root
     |
     |--(A==1.2.*): A==1.2.0
     |   |
     |   `--(B>1): B==1.2.3
     |
     `--(B<1): B==0.1.0
         |
         `--(A==1.4.*): A==1.4.8

    Expected: Unable to compute due to requirement compatibility between
    'A==1.4.*' and 'A==1.2.*'.

    """
    definition_mapping = {
        "A": {
            "1.4.8": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.4.8"
            }),
            "1.2.0": wiz.definition.Definition({
                "identifier": "A",
                "version": "1.2.0",
                "requirements": ["B>1"]
            })
        },
        "B": {
            "1.2.3": wiz.definition.Definition({
                "identifier": "B",
                "version": "1.2.3",
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0",
                "requirements": ["A==1.4.*"]
            })
        },
    }

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([
                Requirement("A==1.2.*"), Requirement("B<1")
            ])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)


def test_scenario_39(benchmark):
    """Compute packages for the following graph.

    Like scenario 16, combinations containing conflicts are discarded until
    a combination without conflicts can be resolved. But this time, variant
    permutation can be optimized with requirements from each variants.

    Root
     |
     |--(A): A[V1]
     |   |
     |   `--(B>=1, <2): B==1
     |
     |--(A): A[V2]
     |   |
     |   `--(B>=2, <3): B==2
     |
     |--(A): A[V3]
     |   |
     |   `--(B>=3, <4): B==3
     |
     |--(A): A[V4]
     |   |
     |   `--(B>=4, <5): B==4
     |
     |--(A): A[V5]
     |   |
     |   `--(B>=5, <6): B==5
     |
     |--(A): A[V6]
     |   |
     |   `--(B>=6, <7): B==6
     |
     |--(A): A[V7]
     |   |
     |   `--(B>=7, <8): B==7
     |
     `--(B==7): B==7

    Expected: B==7, A[V7]

    """
    definition_mapping = {
        "A": {
            "-": wiz.definition.Definition({
                "identifier": "A",
                "variants": [
                    {
                        "identifier": "V7",
                        "requirements": ["B>=7, <8"]
                    },
                    {
                        "identifier": "V6",
                        "requirements": ["B>=6, <7"]
                    },
                    {
                        "identifier": "V5",
                        "requirements": ["B>=5, <6"]
                    },
                    {
                        "identifier": "V4",
                        "requirements": ["B>=4, <5"]
                    },
                    {
                        "identifier": "V3",
                        "requirements": ["B>=3, <4"]
                    },
                    {
                        "identifier": "V2",
                        "requirements": ["B>=2, <3"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["B>=1, <2"]
                    }
                ]
            })
        },
        "B": {
            "1": wiz.definition.Definition({
                "identifier": "B",
                "version": "1",
            }),
            "2": wiz.definition.Definition({
                "identifier": "B",
                "version": "2",
            }),
            "3": wiz.definition.Definition({
                "identifier": "B",
                "version": "3",
            }),
            "4": wiz.definition.Definition({
                "identifier": "B",
                "version": "4",
            }),
            "5": wiz.definition.Definition({
                "identifier": "B",
                "version": "5",
            }),
            "6": wiz.definition.Definition({
                "identifier": "B",
                "version": "6",
            }),
            "7": wiz.definition.Definition({
                "identifier": "B",
                "version": "7",
            }),
        },
    }

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([
            Requirement("A"), Requirement("B==7")
        ])

    benchmark(_resolve)


def test_scenario_40(benchmark):
    """Compute packages for the following graph.

    Like scenario 34, a conflict appear when relinking parents as two
    requirements are explicitly requesting conflicting variants: "A[V2]" and
    "A[V3]". But this time, the graph contains a version conflict which will
    be resolved by removing "A[V2]", hence making this conflict irrelevant.

    Root
     |
     |--(A[V3]): A[V3]==1.0.0
     |   |
     |   `--(B >=3, <4): B==3.0.0
     |
     |--(C >=1): C==2.0.0
     |   |
     |   `--(A[V2]): A[V2]==1.0.0
     |       |
     |       `--(B >=2, <3): B==2.0.0
     |
     `--(E): E
         |
         `--(C >=1, <2): C==1.5.0

    Expected: E, C==1.5.0, B==3.0.0, A[V3]==1.0.0

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
                    }
                ]
            })
        },
        "B": {
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
        },
        "C": {
            "2.0.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "2.0.0",
                "requirements": ["A[V2]"]
            }),
            "1.5.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "1.5.0"
            }),
        },
        "E": {
            "-": wiz.definition.Definition({
                "identifier": "E",
                "requirements": ["C >=1, <2"]
            }),
        }
    }

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([
            Requirement("A[V3]"), Requirement("C >=1"), Requirement("E"),
        ])

    benchmark(_resolve)


def test_scenario_41(benchmark):
    """Compute packages for the following graph.

    Like scenario 34, a conflict appear when relinking parents as two
    requirements are explicitly requesting conflicting variants: "A[V2]" and
    "A[V3]". But this time, the resolver can downgrade versions of conflicting
    nodes to find a solution.

    Root
     |
     |--(A[V3]): A[V3]==1.0.0
     |   |
     |   `--(B >=3, <4): B==3.0.0
     |
     `--(C): C==1.0.0
         |
         `--(A[V2]): A[V2]==1.0.0
             |
             `--(B >=2, <3): B==2.0.0

    Expected: C==0.5.0, B==3.0.0, A[V3]==1.0.0

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
                    }
                ]
            })
        },
        "B": {
            "3.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "3.0.0"
            }),
            "2.0.0": wiz.definition.Definition({
                "identifier": "B",
                "version": "2.0.0"
            }),
        },
        "C": {
            "1.0.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "1.0.0",
                "requirements": ["A[V2]"]
            }),
            "0.5.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.5.0",
            })
        }
    }

    def _resolve():
        """Resolve context."""
        resolver = wiz.graph.Resolver(definition_mapping)
        resolver.compute_packages([
            Requirement("A[V3]"), Requirement("C")
        ])

    benchmark(_resolve)


def test_scenario_42(benchmark):
    """Fail to compute packages for the following graph.

    Root
     |
     |--(A): A[V1]
     |   |
     |   `--(C>1): C==1.5.0
     |
     |--(A): A[V2]
     |   |
     |   `--(C>1): C==1.5.0
     |
     |--(B): B[V1]
     |   |
     |   `--(C<1): C==0.5.0
     |
     `--(B): B[V2]
         |
         `--(C<1): C==0.5.0

    Expected: Unable to compute due to requirement compatibility between
    'C <1' and 'C >1'.

    """
    definition_mapping = {
        "A": {
            "-": wiz.definition.Definition({
                "identifier": "A",
                "variants": [
                    {
                        "identifier": "V2",
                        "requirements": ["C>1"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["C>1"]
                    },
                ]
            }),
        },
        "B": {
            "-": wiz.definition.Definition({
                "identifier": "B",
                "variants": [
                    {
                        "identifier": "V2",
                        "requirements": ["C<1"]
                    },
                    {
                        "identifier": "V1",
                        "requirements": ["C<1"]
                    },
                ]
            }),
        },
        "C": {
            "1.5.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "1.5.0"
            }),
            "0.5.0": wiz.definition.Definition({
                "identifier": "C",
                "version": "0.5.0"
            }),
        }
    }

    def _resolve():
        """Resolve context."""
        try:
            resolver = wiz.graph.Resolver(definition_mapping)
            resolver.compute_packages([
                Requirement("A"), Requirement("B")
            ])
        except wiz.exception.GraphResolutionError:
            pass

    benchmark(_resolve)
