# :coding: utf-8

import pytest

import wiz.graph
import wiz.definition
from wiz.utility import Requirement


def test_scenario_1():
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


def test_scenario_2():
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
        "from the following packages: ['D==0.1.4', 'D==0.1.0']."
    ) in str(error)


def test_scenario_3():
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


def test_scenario_4():
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


def test_scenario_5():
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


def test_scenario_6():
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


def test_scenario_7():
    """Compute packages for the following graph.

    Root
     |
     |--(A<=0.3.0): A==0.3.0
     |
     `--(B): B==0.1.0
         |
         `--(A !=0.3.0): A==1.0.0

    Expected:

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
