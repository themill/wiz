# :coding: utf-8

import pytest

import wiz.graph
import wiz.definition
from wiz.utility import Requirement


def test_scenario_1():
    """Test graph resolution for the following graph.

    Root
     |
     |--(A)-- A==0.2.0
     |        |
     |        `--(C>=0.3.2, <1)-- C==0.3.2
     |                            |
     |                            `--(D==0.1.0)-- D==0.1.0
     |
     `--(G)-- G==2.0.2
              |
              `--(B<0.2.0)-- B==0.1.0
                             |
                             |--(D>=0.1.0)-- D==0.1.4
                             |               |
                             |               `--(E>=2)-- E==2.3.0
                             |                           |
                             |                           `--(F>=0.2)-- F==1.0.0
                             |
                             `--(F>=1)-- F==1.0.0

    Expected: F==1.0.0, D==0.1.0, B==0.1.0, C==0.3.2, G==2.0.2, A==0.2.0

    The order of 'D==0.1.0' / 'B==0.1.0' and 'C==0.3.2' / 'G==2.0.2' can
    vary as they have similar priority number.

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
    """Test graph resolution for the following graph.

    Root
     |
     |--(A)-- A==0.2.0
     |        |
     |        `--(C>=0.3.2, <1)-- C==0.3.2
     |                            |
     |                            `--(D==0.1.0)-- D==0.1.0
     |
     `--(G)-- G==2.0.2
              |
              `--(B<0.2.0)-- B==0.1.0
                             |
                             |--(D>0.1.0)-- D==0.1.4
                             |               |
                             |               `--(E>=2)-- E==2.3.0
                             |                           |
                             |                           `--(F>=0.2)-- F==1.0.0
                             |
                             `--(F>=1)-- F==1.0.0

    Expected: Unable to compute to to requirement compatibility.

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
        "A requirement conflict has been detected for 'D==0.1.4'"
    ) in str(error)


def test_scenario_3():
    """Test graph resolution for the following graph.

    Root
     |
     |--(A)-- A==1.0.0
     |        |
     |        `--(B<1)-- B==0.9.0
     |
     `--(B)-- B==1.0.0
              |
              `--(A<1)-- A==0.9.0

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
    """Test graph resolution for the following graph.

    Root
     |
     |--(A)-- A[V1]==1.0.0
     |        |
     |        `--(B >=1, <2)-- B==1.0.0
     |
     |--(A)-- A[V2]==1.0.0
     |        |
     |        `--(B >=2, <3)-- B==2.0.0
     |
     |--(A)-- A[V3]==1.0.0
     |        |
     |        `--(B >=3, <4)-- B==3.0.0
     |
     `--(A)-- A[V4]==1.0.0
              |
              `--(B >=4, <5)-- B==4.0.0

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
