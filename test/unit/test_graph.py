# :coding: utf-8

import os
import collections
import copy
import itertools

import pytest

import wiz.config
import wiz.graph
import wiz.package
import wiz.utility
from wiz.utility import Requirement


@pytest.fixture(autouse=True)
def reset_configuration(mocker):
    """Ensure that no personal configuration is fetched during tests."""
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


@pytest.fixture()
def mocked_deepcopy(mocker):
    """Return mocked copy.deepcopy function."""
    return mocker.patch.object(copy, "deepcopy")


@pytest.fixture()
def mocked_check_conflicting_requirements(mocker):
    """Return mocked wiz.utility.check_conflicting_requirements function."""
    return mocker.patch.object(wiz.utility, "check_conflicting_requirements")


@pytest.fixture()
def mocked_resolver(mocker):
    """Return mocked Resolver."""
    return mocker.Mock()


@pytest.fixture()
def mocked_combined_requirements(mocker):
    """Return mocked wiz.graph._combined_requirements function."""
    return mocker.patch.object(wiz.graph, "_combined_requirements")


@pytest.fixture()
def mocked_compute_distance_mapping(mocker):
    """Return mocked wiz.graph._compute_distance_mapping function."""
    return mocker.patch.object(wiz.graph, "_compute_distance_mapping")


@pytest.fixture()
def mocked_generate_variant_permutations(mocker):
    """Return mocked wiz.graph._generate_variant_permutations function."""
    return mocker.patch.object(wiz.graph, "_generate_variant_permutations")


@pytest.fixture()
def mocked_compute_conflicting_matrix(mocker):
    """Return mocked wiz.graph._compute_conflicting_matrix function."""
    return mocker.patch.object(wiz.graph, "_compute_conflicting_matrix")


@pytest.fixture()
def mocked_extract_conflicting_requirements(mocker):
    """Return mocked wiz.graph._extract_conflicting_requirements function."""
    return mocker.patch.object(wiz.graph, "_extract_conflicting_requirements")


@pytest.fixture()
def mocked_graph(mocker):
    """Return mocked Graph."""
    graph = mocker.MagicMock(ROOT="root")
    mocker.patch.object(wiz.graph, "Graph", return_value=graph)
    return graph


@pytest.fixture()
def mocked_combination(mocker):
    """Return mocked Combination."""
    return mocker.patch.object(wiz.graph, "Combination")


@pytest.fixture()
def mocked_extract_combinations(mocker):
    """Return mocked wiz.graph.Resolver.extract_combinations method."""
    return mocker.patch.object(wiz.graph.Resolver, "extract_combinations")


@pytest.fixture()
def mocked_fetch_next_combination(mocker):
    """Return mocked wiz.graph.Resolver.fetch_next_combination method."""
    return mocker.patch.object(wiz.graph.Resolver, "fetch_next_combination")


@pytest.fixture()
def mocked_discover_combinations(mocker):
    """Return mocked wiz.graph.Resolver.discover_combinations method."""
    return mocker.patch.object(wiz.graph.Resolver, "discover_combinations")


@pytest.fixture()
def mocked_prune_graph(mocker):
    """Return mocked wiz.graph.VariantCombination.prune_graph method."""
    return mocker.patch.object(wiz.graph.Combination, "prune_graph")


@pytest.fixture()
def mocked_fetch_distance_mapping(mocker):
    """Return mocked wiz.graph.VariantCombination._fetch_distance_mapping."""
    return mocker.patch.object(wiz.graph.Combination, "_fetch_distance_mapping")


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
    """Returned package mapping for testings Graph"""
    mapping = {
        "single": _simple_package(),
        "single-with-namespace": _simple_package_with_namespace(),
        "many": _several_packages(),
        "many-with-namespaces": _packages_with_namespace(),
        "many-with-conditions": _packages_with_conditions(),
        "conflicting-versions": _packages_with_conflicting_versions(),
        "conflicting-variants": _packages_with_conflicting_variants(),
        "combination-resolution": _packages_for_combination_resolution()
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
        "E==0.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "E",
                "version": "0.1.0",
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
        "B==1.2.2": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "B",
                "version": "1.2.2",
                "requirements": [
                    "C",
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

    definition3 = wiz.definition.Definition({
        "identifier": "B",
        "version": "2.5.0",
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
        "B[V2]==2.5.0": wiz.package.Package(
            definition3, variant_index=0
        ),
        "B[V1]==2.5.0": wiz.package.Package(
            definition3, variant_index=1
        ),
        "C": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "C",
            }),
        ),

    }


def _packages_for_combination_resolution():
    """Create several packages for testing combination resolution."""
    return {
        "A==1.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "version": "1.1.0"
            })
        ),
        "A==1.2.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "version": "1.2.0"
            })
        ),
        "A==1.4.8": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "A",
                "version": "1.4.8"
            })
        ),
        "B==0.1.0": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "B",
                "version": "0.1.0"
            })
        ),
        "B==1.2.3": wiz.package.Package(
            wiz.definition.Definition({
                "identifier": "B",
                "version": "1.2.3"
            })
        ),
    }


def test_resolver_empty():
    """Create empty resolver."""
    resolver = wiz.graph.Resolver("__MAPPING__")
    assert resolver.definition_mapping == "__MAPPING__"
    assert resolver.conflicting_variants == set()
    assert resolver._conflicting_combinations == collections.deque()

    assert isinstance(resolver._iterator, collections.Iterable)
    assert list(resolver._iterator) == []


@pytest.mark.parametrize(
    "combination_number", [1, 2, 3, 4, 5, 10],
    ids=[
        "first-combination",
        "second-combination",
        "third-combination",
        "forth-combination",
        "fifth-combination",
        "tenth-combination",
    ]
)
def test_resolver_compute_packages(
    mocker, mocked_graph, mocked_combination, mocked_extract_combinations,
    mocked_fetch_next_combination, combination_number
):
    """Resolve packages."""
    index = combination_number - 1
    combinations = [mocker.Mock() for _ in range(combination_number)]
    mocked_fetch_next_combination.side_effect = combinations
    mocked_extract_combinations.return_value = False

    for combination in combinations[:-1]:
        combination.extract_packages.side_effect = (
            wiz.exception.GraphResolutionError("Error!")
        )

    resolver = wiz.graph.Resolver("__MAPPING__")
    result = resolver.compute_packages("__REQS__")
    assert result == combinations[index].extract_packages.return_value
    assert resolver._conflicting_combinations == collections.deque()

    for combination in combinations:
        combination.resolve_conflicts.assert_called_once_with()
        combination.validate.assert_called_once_with()
        combination.extract_packages.assert_called_once_with()

    mocked_graph.update_from_requirements.assert_called_once_with("__REQS__")

    assert mocked_fetch_next_combination.call_count == combination_number
    mocked_extract_combinations.assert_called_once_with(mocked_graph)
    mocked_combination.assert_called_once_with(mocked_graph, copy_data=False)


@pytest.mark.parametrize(
    "combination_number", [1, 2, 3, 4, 5, 10],
    ids=[
        "first-combination",
        "second-combination",
        "third-combination",
        "forth-combination",
        "fifth-combination",
        "tenth-combination",
    ]
)
def test_resolver_compute_packages_with_initial_variants(
    mocker, mocked_graph, mocked_combination, mocked_extract_combinations,
    mocked_fetch_next_combination, combination_number
):
    """Resolve packages with initial variants."""
    index = combination_number - 1
    combinations = [mocker.Mock() for _ in range(combination_number)]
    mocked_fetch_next_combination.side_effect = combinations
    mocked_extract_combinations.return_value = True

    for combination in combinations[:-1]:
        combination.extract_packages.side_effect = (
            wiz.exception.GraphResolutionError("Error!")
        )

    resolver = wiz.graph.Resolver("__MAPPING__")
    result = resolver.compute_packages("__REQS__")
    assert result == combinations[index].extract_packages.return_value
    assert resolver._conflicting_combinations == collections.deque()

    for combination in combinations:
        combination.resolve_conflicts.assert_called_once_with()
        combination.validate.assert_called_once_with()
        combination.extract_packages.assert_called_once_with()

    mocked_graph.update_from_requirements.assert_called_once_with("__REQS__")

    assert mocked_fetch_next_combination.call_count == combination_number
    mocked_extract_combinations.assert_called_once_with(mocked_graph)
    mocked_combination.assert_not_called()


@pytest.mark.parametrize(
    "combination_number", [1, 2, 3, 4, 5, 10],
    ids=[
        "first-combination",
        "second-combination",
        "third-combination",
        "forth-combination",
        "fifth-combination",
        "tenth-combination",
    ]
)
def test_resolver_compute_packages_with_variant_division(
    mocker, mocked_graph, mocked_extract_combinations,
    mocked_fetch_next_combination, combination_number
):
    """Resolve packages with variant division in previous combination."""
    index = combination_number - 1
    combinations = [mocker.Mock() for _ in range(combination_number)]
    mocked_fetch_next_combination.side_effect = combinations

    for combination in combinations[:-1]:
        combination.extract_packages.side_effect = (
            wiz.exception.GraphVariantsError()
        )

    resolver = wiz.graph.Resolver("__MAPPING__")
    result = resolver.compute_packages("__REQS__")
    assert result == combinations[index].extract_packages.return_value
    assert resolver._conflicting_combinations == collections.deque()

    for combination in combinations:
        combination.resolve_conflicts.assert_called_once_with()
        combination.validate.assert_called_once_with()
        combination.extract_packages.assert_called_once_with()

    mocked_graph.update_from_requirements.assert_called_once_with("__REQS__")

    assert mocked_fetch_next_combination.call_count == combination_number
    assert mocked_extract_combinations.call_count == combination_number

    calls = [mocker.call(mocked_graph)]
    for combination in combinations[:-1]:
        calls.append(mocker.call(combination.graph))

    assert mocked_extract_combinations.call_args_list == calls


@pytest.mark.parametrize(
    "combination_number", [1, 2, 3, 4, 5, 10],
    ids=[
        "first-combination",
        "second-combination",
        "third-combination",
        "forth-combination",
        "fifth-combination",
        "tenth-combination",
    ]
)
def test_resolver_compute_packages_fail(
    mocker, mocked_graph, mocked_extract_combinations,
    mocked_fetch_next_combination, combination_number
):
    """Fail to resolve packages."""
    combinations = [mocker.Mock() for _ in range(combination_number)]
    mocked_fetch_next_combination.side_effect = combinations + [None]

    for combination in combinations:
        combination.extract_packages.side_effect = (
            wiz.exception.GraphResolutionError("Error!")
        )

    resolver = wiz.graph.Resolver("__MAPPING__")

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        resolver.compute_packages("__REQS__")

    assert (
        "Failed to resolve graph at combination #{}:\n\n"
        "Error!".format(combination_number)
    ) in str(error.value)

    assert resolver._conflicting_combinations == collections.deque()

    for combination in combinations:
        combination.resolve_conflicts.assert_called_once_with()
        combination.validate.assert_called_once_with()
        combination.extract_packages.assert_called_once_with()

    mocked_graph.update_from_requirements.assert_called_once_with("__REQS__")

    assert mocked_fetch_next_combination.call_count == combination_number + 1
    mocked_extract_combinations.assert_called_once_with(mocked_graph)


@pytest.mark.parametrize(
    "combination_number", [1, 2, 3, 4, 5, 10],
    ids=[
        "first-combination",
        "second-combination",
        "third-combination",
        "forth-combination",
        "fifth-combination",
        "tenth-combination",
    ]
)
def test_resolver_compute_packages_fail_from_conflicts(
    mocker, mocked_graph, mocked_extract_combinations,
    mocked_fetch_next_combination, combination_number
):
    """Fail to resolve packages because of conflicts."""
    combinations = [mocker.Mock() for _ in range(combination_number)]
    mocked_fetch_next_combination.side_effect = combinations + [None]

    for index, combination in enumerate(combinations):
        combination.extract_packages.side_effect = (
            wiz.exception.GraphConflictsError({
                Requirement("bar > 1"): {"foo{}".format(index)},
                Requirement("bar < 1"): {"bim{}".format(index)}
            })
        )

    resolver = wiz.graph.Resolver("__MAPPING__")

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        resolver.compute_packages("__REQS__")

    assert (
        "Failed to resolve graph at combination #{0}:\n\n"
        "The dependency graph could not be resolved due to the following "
        "requirement conflicts:\n"
        "  * bar <1 \t[bim{1}]\n"
        "  * bar >1 \t[foo{1}]\n".format(
            combination_number, combination_number-1
        )
    ) in str(error.value)

    assert resolver.conflicting_variants == set()

    queue = collections.deque()
    for index, combination in enumerate(combinations):
        queue.extend([
            (combination, {"bim{}".format(index)}),
            (combination, {"foo{}".format(index)}),
        ])

    assert resolver._conflicting_combinations == queue

    for combination in combinations:
        combination.resolve_conflicts.assert_called_once_with()
        combination.validate.assert_called_once_with()
        combination.extract_packages.assert_called_once_with()

    mocked_graph.update_from_requirements.assert_called_once_with("__REQS__")

    assert mocked_fetch_next_combination.call_count == combination_number + 1
    mocked_extract_combinations.assert_called_once_with(mocked_graph)


def test_resolver_compute_packages_reach_maximum(
    mocker, mocked_graph, mocked_extract_combinations,
    mocked_fetch_next_combination
):
    """Fail to resolve packages as maximum attempts is reached."""
    combinations = [mocker.Mock() for _ in range(10)]
    mocked_fetch_next_combination.side_effect = combinations

    for combination in combinations:
        combination.extract_packages.side_effect = (
            wiz.exception.GraphResolutionError("Error!")
        )

    resolver = wiz.graph.Resolver("__MAPPING__", maximum_attempts=5)

    with pytest.raises(wiz.exception.GraphResolutionError) as error:
        resolver.compute_packages("__REQS__")

    assert (
        "Failed to resolve graph at combination #5:\n\n"
        "Error!"
    ) in str(error.value)

    assert resolver._conflicting_combinations == collections.deque()

    for combination in combinations[:5]:
        combination.resolve_conflicts.assert_called_once_with()
        combination.validate.assert_called_once_with()
        combination.extract_packages.assert_called_once_with()

    for combination in combinations[5:]:
        combination.resolve_conflicts.assert_not_called()
        combination.validate.assert_not_called()
        combination.extract_packages.assert_not_called()

    mocked_graph.update_from_requirements.assert_called_once_with("__REQS__")

    assert mocked_fetch_next_combination.call_count == 6
    mocked_extract_combinations.assert_called_once_with(mocked_graph)


@pytest.mark.parametrize("combinations", [
    [],
    ["__COMB1__", "__COMB2__", "__COMB3__"],
], ids=[
    "simple",
    "with-initial-combinations"
])
def test_resolver_extract_combinations_empty(
    mocked_graph, mocked_combination, mocked_generate_variant_permutations,
    combinations
):
    """No new combinations to extract from conflicting variants"""
    mocked_graph.conflicting_variant_groups.return_value = set()

    resolver = wiz.graph.Resolver("__MAPPING__")
    resolver._iterator = iter(combinations)

    assert resolver.extract_combinations(mocked_graph) is False

    mocked_generate_variant_permutations.assert_not_called()
    mocked_combination.assert_not_called()

    assert isinstance(resolver._iterator, collections.Iterable)
    assert list(resolver._iterator) == combinations


@pytest.mark.parametrize("combinations", [
    [],
    ["__COMB1__", "__COMB2__", "__COMB3__"],
], ids=[
    "simple",
    "with-initial-combinations"
])
def test_resolver_extract_combinations(
    mocker, mocked_graph, mocked_combination,
    mocked_generate_variant_permutations, combinations
):
    """Extract new combinations from conflicting variants"""
    mocked_graph.conflicting_variant_groups.return_value = {
        (("B[V3]",), ("B[V2]",), ("B[V1]",)),
        (("A[V2]==2", "A[V2]==1"), ("A[V1]==1",))
    }
    mocked_combination.side_effect = [
        "__COMB4__", "__COMB5__", "__COMB6__",
        "__COMB7__", "__COMB8__", "__COMB9__",
    ]
    mocked_generate_variant_permutations.return_value = iter([
        (("B[V3]",), ("A[V2]==2", "A[V2]==1")),
        (("B[V3]",), ("A[V1]==1",)),
        (("B[V2]",), ("A[V2]==2", "A[V2]==1")),
        (("B[V2]",), ("A[V1]==1",)),
        (("B[V1]",), ("A[V2]==2", "A[V2]==1")),
        (("B[V1]",), ("A[V1]==1",)),
    ])

    resolver = wiz.graph.Resolver("__MAPPING__", maximum_combinations=10)
    resolver._iterator = iter(combinations)

    assert resolver.extract_combinations(mocked_graph) is True

    assert isinstance(resolver._iterator, collections.Iterable)
    assert list(resolver._iterator) == (
        [
            "__COMB4__", "__COMB5__", "__COMB6__",
            "__COMB7__", "__COMB8__", "__COMB9__"
        ] + combinations
    )

    assert mocked_combination.call_args_list == [
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V2]", "B[V1]", "A[V1]==1"}
        ),
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V2]", "B[V1]", "A[V2]==2", "A[V2]==1"}
        ),
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V3]", "B[V1]", "A[V1]==1"}
        ),
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V3]", "B[V1]", "A[V2]==2", "A[V2]==1"}
        ),
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V3]", "B[V2]", "A[V1]==1"}
        ),
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V3]", "B[V2]", "A[V2]==2", "A[V2]==1"}
        ),
    ]

    mocked_generate_variant_permutations.assert_called_once_with(
        mocked_graph, {
            (("B[V3]",), ("B[V2]",), ("B[V1]",)),
            (("A[V2]==2", "A[V2]==1"), ("A[V1]==1",))
        }
    )


@pytest.mark.parametrize("combinations", [
    [],
    ["__COMB1__", "__COMB2__", "__COMB3__"],
], ids=[
    "simple",
    "with-initial-combinations"
])
def test_resolver_extract_combinations_reach_maximum(
    mocker, mocked_graph, mocked_combination,
    mocked_generate_variant_permutations, combinations
):
    """Extract truncated combinations list from conflicting variants"""
    mocked_graph.conflicting_variant_groups.return_value = {
        (("B[V3]",), ("B[V2]",), ("B[V1]",)),
        (("A[V2]==2", "A[V2]==1"), ("A[V1]==1",))
    }
    mocked_combination.side_effect = [
        "__COMB4__", "__COMB5__", "__COMB6__",
        "__COMB7__", "__COMB8__", "__COMB9__",
    ]
    mocked_generate_variant_permutations.return_value = iter([
        (("B[V3]",), ("A[V2]==2", "A[V2]==1")),
        (("B[V3]",), ("A[V1]==1",)),
        (("B[V2]",), ("A[V2]==2", "A[V2]==1")),
        (("B[V2]",), ("A[V1]==1",)),
        (("B[V1]",), ("A[V2]==2", "A[V2]==1")),
        (("B[V1]",), ("A[V1]==1",)),
    ])

    resolver = wiz.graph.Resolver("__MAPPING__", maximum_combinations=3)
    resolver._iterator = iter(combinations)

    assert resolver.extract_combinations(mocked_graph) is True

    assert isinstance(resolver._iterator, collections.Iterable)
    assert list(resolver._iterator) == (
        ["__COMB4__", "__COMB5__", "__COMB6__"] + combinations
    )

    assert mocked_combination.call_args_list == [
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V2]", "B[V1]", "A[V1]==1"}
        ),
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V2]", "B[V1]", "A[V2]==2", "A[V2]==1"}
        ),
        mocker.call(
            mocked_graph,
            nodes_to_remove={"B[V3]", "B[V1]", "A[V1]==1"}
        ),
    ]

    mocked_generate_variant_permutations.assert_called_once_with(
        mocked_graph, {
            (("B[V3]",), ("B[V2]",), ("B[V1]",)),
            (("A[V2]==2", "A[V2]==1"), ("A[V1]==1",))
        }
    )


def test_resolver_fetch_next_combination(mocked_discover_combinations):
    """Return next combination from the iterator."""
    mocked_discover_combinations.return_value = False

    resolver = wiz.graph.Resolver("__MAPPING__")
    resolver._iterator = iter(["__COMB1__", "__COMB2__", "__COMB3__"])

    assert resolver.fetch_next_combination() == "__COMB1__"
    mocked_discover_combinations.assert_not_called()

    assert resolver.fetch_next_combination() == "__COMB2__"
    mocked_discover_combinations.assert_not_called()

    assert resolver.fetch_next_combination() == "__COMB3__"
    mocked_discover_combinations.assert_not_called()

    assert resolver.fetch_next_combination() is None
    mocked_discover_combinations.assert_called_once()


def test_resolver_fetch_next_combination_with_discovery():
    """Return next combination from the iterator with new combinations
    discovered.
    """
    resolver = wiz.graph.Resolver("__MAPPING__")
    resolver._iterator = iter(["__COMB1__", "__COMB2__", "__COMB3__"])

    def _discover_combinations():
        """Mock combination discovery"""
        resolver._iterator = iter(["__COMB4__", "__COMB5__"])
        return True

    resolver.discover_combinations = _discover_combinations

    assert resolver.fetch_next_combination() == "__COMB1__"
    assert resolver.fetch_next_combination() == "__COMB2__"
    assert resolver.fetch_next_combination() == "__COMB3__"
    assert resolver.fetch_next_combination() == "__COMB4__"
    assert resolver.fetch_next_combination() == "__COMB5__"


@pytest.mark.parametrize(
    "combination_number", [1, 2, 3, 4, 5, 10],
    ids=[
        "first-combination",
        "second-combination",
        "third-combination",
        "forth-combination",
        "fifth-combination",
        "tenth-combination",
    ]
)
def test_resolver_discover_combinations(
    mocker, mocked_deepcopy, mocked_extract_combinations, combination_number
):
    """Discover new combinations from unsolvable conflicts recorded."""
    successful_graph_index = combination_number - 1

    combinations = [
        mocker.Mock(
            graph=mocker.Mock(**{"downgrade_versions.return_value": (
                index == successful_graph_index
            )})
        )
        for index in range(combination_number)
    ]

    resolver = wiz.graph.Resolver("__MAPPING__")
    resolver._conflicting_combinations = collections.deque([
        ("COMBINATION{}".format(index), {"N{}".format(index)})
        for index in range(combination_number)
    ])
    mocked_deepcopy.side_effect = combinations
    assert resolver.discover_combinations() is True

    assert mocked_deepcopy.call_args_list == [
        mocker.call("COMBINATION{}".format(index))
        for index in range(combination_number)
    ]

    for index, combination in enumerate(combinations):
        expected = {"N{}".format(index)}
        combination.graph.downgrade_versions.assert_called_once_with(expected)

    mocked_extract_combinations.assert_called_once_with(
        combinations[successful_graph_index].graph
    )


@pytest.mark.parametrize(
    "combination_number", [1, 2, 3, 4, 5, 10],
    ids=[
        "first-combination",
        "second-combination",
        "third-combination",
        "forth-combination",
        "fifth-combination",
        "tenth-combination",
    ]
)
def test_resolver_discover_combinations_fail(
    mocker, mocked_deepcopy, mocked_extract_combinations, combination_number
):
    """Fail to discover new combinations from unsolvable conflicts recorded."""
    combinations = [
        mocker.Mock(
            graph=mocker.Mock(**{"downgrade_versions.return_value": False})
        )
        for _ in range(combination_number)
    ]

    resolver = wiz.graph.Resolver("__MAPPING__")
    resolver._conflicting_combinations = collections.deque([
        ("COMBINATION{}".format(index), {"N{}".format(index)})
        for index in range(combination_number)
    ])
    mocked_deepcopy.side_effect = combinations

    assert resolver.discover_combinations() is False

    assert mocked_deepcopy.call_args_list == [
        mocker.call("COMBINATION{}".format(index))
        for index in range(combination_number)
    ]

    for index, combination in enumerate(combinations):
        expected = {"N{}".format(index)}
        combination.graph.downgrade_versions.assert_called_once_with(expected)

    mocked_extract_combinations.assert_not_called()


def test_compute_distance_mapping_empty(mocked_graph):
    """Compute distance mapping from empty graph."""
    mocked_graph.outcoming.return_value = []
    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
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

    assert wiz.graph._compute_distance_mapping(mocked_graph) == {
        "root": {"distance": 0, "parent": "root"},
        "A": {"distance": 1, "parent": "root"},
        "B": {"distance": 2, "parent": "root"},
        "C": {"distance": 2, "parent": "A"},
        "D": {"distance": 3, "parent": "A"},
        "E": {"distance": 4, "parent": "D"},
        "F": {"distance": 3, "parent": "root"},
        "G": {"distance": 3, "parent": "C"},
    }


def test_generate_variant_permutations_none_conflicting(
    mocked_graph, mocked_compute_distance_mapping,
    mocked_compute_conflicting_matrix
):
    """Yield all variant groups permutations if no groups are conflicting.
    """
    variant_groups = {
        (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",))
    }
    mocked_compute_distance_mapping.return_value = {
        "A[V3]": {"distance": 3},
        "A[V2]": {"distance": 3},
        "A[V1]": {"distance": 3},
        "B[V2]==2": {"distance": 2},
        "B[V2]==1": {"distance": 2},
        "B[V1]==1": {"distance": 1},
    }
    mocked_compute_conflicting_matrix.return_value = {
        "A[V3]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
        "A[V2]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
        "A[V1]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
        "B[V2]==2": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
        "B[V2]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
        "B[V1]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
    }

    result = wiz.graph._generate_variant_permutations(
        mocked_graph, variant_groups
    )

    assert isinstance(result, collections.Iterable)
    assert list(result) == [
        (("B[V1]==1",), ("A[V3]",)),
        (("B[V1]==1",), ("A[V2]",)),
        (("B[V1]==1",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("A[V3]",)),
        (("B[V2]==2", "B[V2]==1"), ("A[V2]",)),
        (("B[V2]==2", "B[V2]==1"), ("A[V1]",)),
    ]

    mocked_compute_conflicting_matrix.assert_called_once_with(
        mocked_graph, variant_groups
    )


def test_generate_variant_permutations_all_conflicting(
    mocked_graph, mocked_compute_distance_mapping,
    mocked_compute_conflicting_matrix
):
    """Yield all variant groups permutations if all groups are conflicting.
    """
    variant_groups = {
        (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",))
    }
    mocked_compute_distance_mapping.return_value = {
        "A[V3]": {"distance": 3},
        "A[V2]": {"distance": 3},
        "A[V1]": {"distance": 3},
        "B[V2]==2": {"distance": 2},
        "B[V2]==1": {"distance": 2},
        "B[V1]==1": {"distance": 1},
    }
    mocked_compute_conflicting_matrix.return_value = {
        "A[V3]": {"B[V2]==2": True, "B[V2]==1": True, "B[V1]==1": True},
        "A[V2]": {"B[V2]==2": True, "B[V2]==1": True, "B[V1]==1": True},
        "A[V1]": {"B[V2]==2": True, "B[V2]==1": True, "B[V1]==1": True},
        "B[V2]==2": {"A[V3]": True, "A[V2]": True, "A[V1]": True},
        "B[V2]==1": {"A[V3]": True, "A[V2]": True, "A[V1]": True},
        "B[V1]==1": {"A[V3]": True, "A[V2]": True, "A[V1]": True},
    }

    result = wiz.graph._generate_variant_permutations(
        mocked_graph, variant_groups
    )

    assert isinstance(result, collections.Iterable)
    assert list(result) == [
        (("B[V1]==1",), ("A[V3]",)),
    ]

    mocked_compute_conflicting_matrix.assert_called_once_with(
        mocked_graph, variant_groups
    )


def test_generate_variant_permutations_optimized_two_groups(
    mocked_graph, mocked_compute_distance_mapping,
    mocked_compute_conflicting_matrix
):
    """Yield optimized permutations for two groups."""
    variant_groups = {
        (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",))
    }
    mocked_compute_distance_mapping.return_value = {
        "A[V3]": {"distance": 3},
        "A[V2]": {"distance": 3},
        "A[V1]": {"distance": 3},
        "B[V2]==2": {"distance": 2},
        "B[V2]==1": {"distance": 2},
        "B[V1]==1": {"distance": 1},
    }
    mocked_compute_conflicting_matrix.return_value = {
        "A[V3]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": True},
        "A[V2]": {"B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": True},
        "A[V1]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
        "B[V2]==2": {"A[V3]": False, "A[V2]": True, "A[V1]": False},
        "B[V2]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
        "B[V1]==1": {"A[V3]": True, "A[V2]": True, "A[V1]": False},
    }

    result = wiz.graph._generate_variant_permutations(
        mocked_graph, variant_groups
    )

    assert isinstance(result, collections.Iterable)
    assert list(result) == [
        (("B[V1]==1",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("A[V3]",)),
        (("B[V2]==2", "B[V2]==1"), ("A[V1]",)),
        (("B[V2]==1",), ("A[V2]",)),
    ]

    mocked_compute_conflicting_matrix.assert_called_once_with(
        mocked_graph, variant_groups
    )


def test_generate_variant_permutations_optimized_three_groups(
    mocked_graph, mocked_compute_distance_mapping,
    mocked_compute_conflicting_matrix
):
    """Yield optimized permutations for three groups."""
    variant_groups = {
        (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",)),
        (("C[V2]",), ("C[V1]",)),
    }
    mocked_compute_distance_mapping.return_value = {
        "A[V3]": {"distance": 3},
        "A[V2]": {"distance": 3},
        "A[V1]": {"distance": 3},
        "B[V2]==2": {"distance": 2},
        "B[V2]==1": {"distance": 2},
        "B[V1]==1": {"distance": 1},
        "C[V2]": {"distance": 1},
        "C[V1]": {"distance": 1},
    }
    mocked_compute_conflicting_matrix.return_value = {
        "A[V3]": {
            "B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": True,
            "C[V2]": False, "C[V1]": False,
        },
        "A[V2]": {
            "B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": True,
            "C[V2]": False, "C[V1]": True,
        },
        "A[V1]": {
            "B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False,
            "C[V2]": False, "C[V1]": True,
        },
        "B[V2]==2": {
            "A[V3]": False, "A[V2]": True, "A[V1]": False,
            "C[V2]": False, "C[V1]": True,
        },
        "B[V2]==1": {
            "A[V3]": False, "A[V2]": False, "A[V1]": False,
            "C[V2]": False, "C[V1]": False,
        },
        "B[V1]==1": {
            "A[V3]": True, "A[V2]": True, "A[V1]": False,
            "C[V2]": False, "C[V1]": False,
        },
        "C[V2]": {
            "A[V3]": False, "A[V2]": False, "A[V1]": False,
            "B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False,
        },
        "C[V1]": {
            "A[V3]": False, "A[V2]": True, "A[V1]": True,
            "B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": False,
        }
    }

    result = wiz.graph._generate_variant_permutations(
        mocked_graph, variant_groups
    )

    assert isinstance(result, collections.Iterable)
    assert list(result) == [
        (("B[V1]==1",), ("C[V2]",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("C[V2]",), ("A[V3]",)),
        (("B[V2]==2", "B[V2]==1"), ("C[V2]",), ("A[V1]",)),
        (("B[V1]==1",), ("C[V2]",), ("A[V3]",)),
        (("B[V2]==2", "B[V2]==1"), ("C[V2]",), ("A[V2]",)),
        (("B[V2]==1",), ("C[V2]",), ("A[V3]",)),
        (("B[V2]==1",), ("C[V2]",), ("A[V2]",)),
        (("B[V2]==1",), ("C[V2]",), ("A[V1]",)),
        (("B[V2]==1",), ("C[V1]",), ("A[V3]",))
    ]

    mocked_compute_conflicting_matrix.assert_called_once_with(
        mocked_graph, variant_groups
    )


@pytest.mark.parametrize("variant_groups, expected", [
    (set(), ()),
    (
        {(("B[V2]==2", "B[V2]==1"), ("B[V1]==1",))},
        ((("B[V1]==1",), ("B[V2]==2", "B[V2]==1")),)
    ),
    (
        {(("B[V1]==1",), ("B[V2]==2", "B[V2]==1"))},
        ((("B[V1]==1",), ("B[V2]==2", "B[V2]==1")),)
    ),
    (
        {
            (("A[V3]",), ("A[V2]",), ("A[V1]",)),
            (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",))
        },
        (
            (("B[V1]==1",), ("B[V2]==2", "B[V2]==1")),
            (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        )
    )
], ids=[
    "empty",
    "one-group",
    "one-group-unchanged",
    "two-groups",
])
def test_sorted_variant_groups(variant_groups, expected):
    """Return sorted variant groups using the distance mapping."""
    mapping = {
        "A[V3]": {"distance": 3},
        "A[V2]": {"distance": 3},
        "A[V1]": {"distance": 3},
        "B[V2]==2": {"distance": 2},
        "B[V2]==1": {"distance": 2},
        "B[V1]==1": {"distance": 1},
    }

    assert wiz.graph._sorted_variant_groups(variant_groups, mapping) == expected


@pytest.mark.parametrize("variant_groups, expected", [
    ((), [()]),
    (
        ((("A[V3]",), ("A[V2]",), ("A[V1]",)),),
        [((("A[V3]",), ("A[V2]",), ("A[V1]",)),)]
    ),
], ids=[
    "empty",
    "one-group",
])
def test_extract_optimized_variant_groups_no_effect(variant_groups, expected):
    """Extract list of optimized variant groups for less than 2 groups."""
    result = wiz.graph._extract_optimized_variant_groups(
        variant_groups, {}
    )
    assert result == expected


def test_extract_optimized_variant_groups_without_conflict():
    """Extract list of optimized variant groups without conflict."""
    variant_groups = (
        (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        (("C[V2]",), ("C[V1]",))
    )

    conflicting = {
        "A[V3]": {"C[V2]": False, "C[V1]": False},
        "A[V2]": {"C[V2]": False, "C[V1]": False},
        "A[V1]": {"C[V2]": False, "C[V1]": False},
        "C[V2]": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
        "C[V1]": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
    }

    result = wiz.graph._extract_optimized_variant_groups(
        variant_groups, conflicting
    )

    assert result == [
        ((("A[V3]",),), (("C[V2]",), ("C[V1]",))),
        ((("A[V2]",),), (("C[V2]",), ("C[V1]",))),
        ((("A[V1]",),), (("C[V2]",), ("C[V1]",))),
        ((("A[V3]",), ("A[V2]",), ("A[V1]",)), (("C[V2]",),)),
        ((("A[V3]",), ("A[V2]",), ("A[V1]",)), (("C[V1]",),)),
    ]


def test_extract_optimized_variant_groups_with_node_conflicts():
    """Extract optimized variant groups with few nodes conflicting."""
    variant_groups = (
        (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",))
    )

    conflicting = {
        "A[V3]": {"B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": False},
        "A[V2]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
        "A[V1]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
        "B[V2]==2": {"A[V3]": True, "A[V2]": False, "A[V1]": False},
        "B[V2]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
        "B[V1]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
    }

    result = wiz.graph._extract_optimized_variant_groups(
        variant_groups, conflicting
    )

    assert result == [
        ((("A[V3]",),), (("B[V2]==1",), ("B[V1]==1",))),
        ((("A[V2]",),), (("B[V2]==2", "B[V2]==1",), ("B[V1]==1",))),
        ((("A[V1]",),), (("B[V2]==2", "B[V2]==1",), ("B[V1]==1",))),
        ((("A[V2]",), ("A[V1]",)), (("B[V2]==2", "B[V2]==1",),)),
        ((("A[V3]",), ("A[V2]",), ("A[V1]",)), (("B[V1]==1",),)),
    ]


def test_extract_optimized_variant_groups_with_definition_conflicts():
    """Extract optimized variant groups with definition group conflicting."""
    variant_groups = (
        (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",)),
        (("C[V2]",), ("C[V1]",))
    )

    conflicting = {
        "B[V2]==2": {"C[V2]": False, "C[V1]": False},
        "B[V2]==1": {"C[V2]": False, "C[V1]": False},
        "B[V1]==1": {"C[V2]": True, "C[V1]": True},
        "C[V2]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": True},
        "C[V1]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": True},
    }

    result = wiz.graph._extract_optimized_variant_groups(
        variant_groups, conflicting
    )

    assert result == [
        ((("B[V2]==2", "B[V2]==1"),), (("C[V2]",), ("C[V1]",))),
        ((("B[V2]==2", "B[V2]==1"),), (("C[V2]",),)),
        ((("B[V2]==2", "B[V2]==1"),), (("C[V1]",),)),
    ]


def test_extract_optimized_variant_groups_with_three_groups():
    """Extract optimized variant groups for three definitions group conflicting.
    """
    variant_groups = (
        (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",)),
        (("C[V2]",), ("C[V1]",))
    )

    conflicting = {
        "A[V3]": {
            "B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": False,
            "C[V2]": False, "C[V1]": False,
        },
        "A[V2]": {
            "B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False,
            "C[V2]": False, "C[V1]": False,
        },
        "A[V1]": {
            "B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False,
            "C[V2]": False, "C[V1]": False,
        },
        "B[V2]==2": {
            "A[V3]": True, "A[V2]": False, "A[V1]": False,
            "C[V2]": False, "C[V1]": False,
        },
        "B[V2]==1": {
            "A[V3]": False, "A[V2]": False, "A[V1]": False,
            "C[V2]": False, "C[V1]": False,
        },
        "B[V1]==1": {
            "A[V3]": False, "A[V2]": False, "A[V1]": False,
            "C[V2]": True, "C[V1]": True,
        },
        "C[V2]": {
            "A[V3]": False, "A[V2]": False, "A[V1]": False,
            "B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": True,
        },
        "C[V1]": {
            "A[V3]": False, "A[V2]": False, "A[V1]": False,
            "B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": True,
        }
    }

    result = wiz.graph._extract_optimized_variant_groups(
        variant_groups, conflicting
    )

    assert result == [
        ((("A[V3]",),), (("B[V2]==1",),), (("C[V2]",), ("C[V1]",))),
        ((("A[V2]",),), (("B[V2]==2", "B[V2]==1",),), (("C[V2]",), ("C[V1]",))),
        ((("A[V1]",),), (("B[V2]==2", "B[V2]==1",),), (("C[V2]",), ("C[V1]",))),
        (
            (("A[V2]",), ("A[V1]",)),
            (("B[V2]==2", "B[V2]==1",),),
            (("C[V2]",), ("C[V1]",))
        ),
        ((("A[V3]",), ("A[V2]",), ("A[V1]",)), (("B[V2]==1",),), (("C[V2]",),)),
        ((("A[V2]",), ("A[V1]",)), (("B[V2]==2", "B[V2]==1",),), (("C[V2]",),)),
        ((("A[V3]",), ("A[V2]",), ("A[V1]",)), (("B[V2]==1",),), (("C[V1]",),)),
        ((("A[V2]",), ("A[V1]",)), (("B[V2]==2", "B[V2]==1",),), (("C[V1]",),)),
    ]


def test_filtered_variant_groups():
    """Return filtered variant group using callback."""
    variant_groups = (
        (("A[V1]=1", "A[V1]=2"), ("A[V2]",)),
        (("B[V2]",), ("B[V1]",))
    )

    result = wiz.graph._filtered_variant_groups(
        variant_groups, callback=lambda _, _id: _id not in ("A[V1]=2", "B[V1]")
    )
    assert result == ((("A[V1]=1",), ("A[V2]",)), (("B[V2]",),))

    result = wiz.graph._filtered_variant_groups(
        variant_groups, callback=lambda _index, _id: (
            _index == 0 and _id not in ("A[V1]=1", "A[V1]=2")
        )
    )
    assert result == ((("A[V2]",),),)


def test_compute_conflicting_matrix_empty(
    mocked_graph, mocked_check_conflicting_requirements
):
    """Compute conflicting matrix for empty variant group."""
    assert wiz.graph._compute_conflicting_matrix(mocked_graph, set()) == {}

    mocked_check_conflicting_requirements.assert_not_called()


def test_compute_conflicting_matrix_one_group(
    mocked_graph, mocked_check_conflicting_requirements
):
    """Compute conflicting matrix for one variant group."""
    groups = {(("A[V3]",), ("A[V2]",))}
    assert wiz.graph._compute_conflicting_matrix(mocked_graph, groups) == {}

    mocked_check_conflicting_requirements.assert_not_called()


@pytest.mark.parametrize("conflicts, expected", [
    (
        [False] * 9,
        {
            "A[V3]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
            "A[V2]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
            "A[V1]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": False},
            "B[V2]==2": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
            "B[V2]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
            "B[V1]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
        }
    ),
    (
        [True] * 9,
        {
            "A[V3]": {"B[V2]==2": True, "B[V2]==1": True, "B[V1]==1": True},
            "A[V2]": {"B[V2]==2": True, "B[V2]==1": True, "B[V1]==1": True},
            "A[V1]": {"B[V2]==2": True, "B[V2]==1": True, "B[V1]==1": True},
            "B[V2]==2": {"A[V3]": True, "A[V2]": True, "A[V1]": True},
            "B[V2]==1": {"A[V3]": True, "A[V2]": True, "A[V1]": True},
            "B[V1]==1": {"A[V3]": True, "A[V2]": True, "A[V1]": True},
        }
    ),
    (
        [True, False, True, True, False, True, False, False, True],
        {
            "A[V3]": {"B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": True},
            "A[V2]": {"B[V2]==2": True, "B[V2]==1": False, "B[V1]==1": True},
            "A[V1]": {"B[V2]==2": False, "B[V2]==1": False, "B[V1]==1": True},
            "B[V2]==2": {"A[V3]": True, "A[V2]": True, "A[V1]": False},
            "B[V2]==1": {"A[V3]": False, "A[V2]": False, "A[V1]": False},
            "B[V1]==1": {"A[V3]": True, "A[V2]": True, "A[V1]": True},
        }
    ),
], ids=[
    "none-conflicting",
    "all-conflicting",
    "mixed-conflicting",
])
def test_compute_conflicting_matrix_two_groups(
    mocker, mocked_graph, mocked_check_conflicting_requirements,
    conflicts, expected
):
    """Compute conflicting matrix for two variant groups."""
    # Use groups as a list instead of a set to make tests deterministic.
    groups = [
        (("A[V3]",), ("A[V2]",), ("A[V1]",)),
        (("B[V2]==2", "B[V2]==1"), ("B[V1]==1",))
    ]

    def _fetch_mocked_node(_id, raising):
        """Fetched mocked node from identifier"""
        return mocker.Mock(package="__" + _id, raising=raising)

    mocked_graph.node = _fetch_mocked_node
    mocked_check_conflicting_requirements.side_effect = conflicts

    result = wiz.graph._compute_conflicting_matrix(mocked_graph, groups)
    assert result == expected

    assert mocked_check_conflicting_requirements.call_args_list == [
        mocker.call("__A[V3]", "__B[V2]==2"),
        mocker.call("__A[V3]", "__B[V2]==1"),
        mocker.call("__A[V3]", "__B[V1]==1"),
        mocker.call("__A[V2]", "__B[V2]==2"),
        mocker.call("__A[V2]", "__B[V2]==1"),
        mocker.call("__A[V2]", "__B[V1]==1"),
        mocker.call("__A[V1]", "__B[V2]==2"),
        mocker.call("__A[V1]", "__B[V2]==1"),
        mocker.call("__A[V1]", "__B[V1]==1"),
    ]


@pytest.mark.parametrize("conflicts, expected", [
    (
        [False] * 12,
        {
            "A[V2]": {
                "B[V2]": False, "B[V1]": False,
                "C[V2]": False, "C[V1]": False
            },
            "A[V1]": {
                "B[V2]": False, "B[V1]": False,
                "C[V2]": False, "C[V1]": False
            },
            "B[V2]": {
                "A[V2]": False, "A[V1]": False,
                "C[V2]": False, "C[V1]": False
            },
            "B[V1]": {
                "A[V2]": False, "A[V1]": False,
                "C[V2]": False, "C[V1]": False
            },
            "C[V2]": {
                "A[V2]": False, "A[V1]": False,
                "B[V2]": False, "B[V1]": False
            },
            "C[V1]": {
                "A[V2]": False, "A[V1]": False,
                "B[V2]": False, "B[V1]": False
            },
        }
    ),
    (
        [True] * 12,
        {
            "A[V2]": {
                "B[V2]": True, "B[V1]": True,
                "C[V2]": True, "C[V1]": True
            },
            "A[V1]": {
                "B[V2]": True, "B[V1]": True,
                "C[V2]": True, "C[V1]": True
            },
            "B[V2]": {
                "A[V2]": True, "A[V1]": True,
                "C[V2]": True, "C[V1]": True
            },
            "B[V1]": {
                "A[V2]": True, "A[V1]": True,
                "C[V2]": True, "C[V1]": True
            },
            "C[V2]": {
                "A[V2]": True, "A[V1]": True,
                "B[V2]": True, "B[V1]": True
            },
            "C[V1]": {
                "A[V2]": True, "A[V1]": True,
                "B[V2]": True, "B[V1]": True
            },
        }
    ),
    (
        [
            True, False, True, True, False, True,
            False, False, True, False, True, False
        ],
        {
            "A[V2]": {
                "B[V2]": True, "B[V1]": False,
                "C[V2]": False, "C[V1]": True
            },
            "A[V1]": {
                "B[V2]": True, "B[V1]": True,
                "C[V2]": False, "C[V1]": False
            },
            "B[V2]": {
                "A[V2]": True, "A[V1]": True,
                "C[V2]": True, "C[V1]": False
            },
            "B[V1]": {
                "A[V2]": False, "A[V1]": True,
                "C[V2]": True, "C[V1]": False
            },
            "C[V2]": {
                "A[V2]": False, "A[V1]": False,
                "B[V2]": True, "B[V1]": True
            },
            "C[V1]": {
                "A[V2]": True, "A[V1]": False,
                "B[V2]": False, "B[V1]": False
            },
        }
    ),
], ids=[
    "none-conflicting",
    "all-conflicting",
    "mixed-conflicting",
])
def test_compute_conflicting_matrix_three_groups(
    mocker, mocked_graph, mocked_check_conflicting_requirements,
    conflicts, expected
):
    """Compute conflicting matrix for three variant groups."""
    # Use groups as a list instead of a set to make tests deterministic.
    groups = [
        (("A[V2]",), ("A[V1]",)),
        (("B[V2]",), ("B[V1]",)),
        (("C[V2]",), ("C[V1]",))
    ]

    def _fetch_mocked_node(_id, raising):
        """Fetched mocked node from identifier"""
        return mocker.Mock(package="__" + _id, raising=raising)

    mocked_graph.node = _fetch_mocked_node
    mocked_check_conflicting_requirements.side_effect = conflicts

    result = wiz.graph._compute_conflicting_matrix(mocked_graph, groups)
    assert result == expected

    assert mocked_check_conflicting_requirements.call_args_list == [
        mocker.call("__A[V2]", "__B[V2]"),
        mocker.call("__A[V2]", "__B[V1]"),
        mocker.call("__A[V1]", "__B[V2]"),
        mocker.call("__A[V1]", "__B[V1]"),
        mocker.call("__A[V2]", "__C[V2]"),
        mocker.call("__A[V2]", "__C[V1]"),
        mocker.call("__A[V1]", "__C[V2]"),
        mocker.call("__A[V1]", "__C[V1]"),
        mocker.call("__B[V2]", "__C[V2]"),
        mocker.call("__B[V2]", "__C[V1]"),
        mocker.call("__B[V1]", "__C[V2]"),
        mocker.call("__B[V1]", "__C[V1]"),
    ]


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

    assert wiz.graph._combined_requirements(mocked_graph, nodes) == (
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
        wiz.graph._combined_requirements(mocked_graph, nodes)

    assert (
        "Impossible to combine requirements with different names "
        "[foo, incorrect]."
    ) in str(error.value)


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

    conflicting = wiz.graph._extract_conflicting_requirements(
        mocked_graph, nodes
    )

    assert conflicting == {
        Requirement("foo >=4, <5"): {"G", "H"},
        Requirement("foo ==3.0.0"): {"root"},
        Requirement("foo ==3.*"): {"F"}
    }


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

    with pytest.raises(ValueError) as error:
        wiz.graph._extract_conflicting_requirements(mocked_graph, nodes)

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
    assert graph.conflicting_variant_groups() == set()
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

    with pytest.raises(ValueError):
        graph.node("whatever", raising=True)

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

    with pytest.raises(ValueError):
        graph.node("whatever", raising=True)

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

    with pytest.raises(ValueError):
        graph.node("whatever", raising=True)

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
    assert "No link recorded for node: 'whatever'" in str(error.value)

    with pytest.raises(ValueError) as error:
        graph.link_requirement("whatever", "root")
    assert "No link recorded for node: 'whatever'" in str(error.value)


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
    assert "No link recorded for node: 'whatever'" in str(error.value)

    with pytest.raises(ValueError) as error:
        graph.link_weight("whatever", "root")
    assert "No link recorded for node: 'whatever'" in str(error.value)


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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {
        "root": [wiz.exception.RequestNotFound("Error")]
    }

    # Check full data.
    assert graph.data() == {
        "node_mapping": {},
        "link_mapping": {},
        "error_mapping": {"root": [wiz.exception.RequestNotFound("Error")]},
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
            namespace_counter=collections.Counter({})
        ),
        mocker.call(
            Requirement("D > 3"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 1})
        ),
        mocker.call(
            Requirement("bar::B"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 1})
        ),
        mocker.call(
            Requirement("foo::C"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 1, "bar": 1})
        ),
        mocker.call(
            Requirement("D > 1"), mocked_resolver.definition_mapping,
            namespace_counter=collections.Counter({"foo": 2, "bar": 1})
        )
    ]

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == set()
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {
        "B==1.2.3": [wiz.exception.RequestNotFound("Error")]
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
        "error_mapping": {"B==1.2.3": [wiz.exception.RequestNotFound("Error")]},
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == {
        (("A[V3]",), ("A[V2]",), ("A[V1]",))
    }
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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

    assert "Node can not be removed: A==0.1.0" in str(error.value)


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
    assert graph.conflicting_variant_groups() == set()
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


@pytest.mark.parametrize("packages", ["conflicting-variants"], indirect=True)
def test_graph_relink_parents_error(
    mocked_resolver, mocked_package_extract, packages
):
    """Fail to relink parents after removing a node."""
    requirements = [Requirement("A"), Requirement("A[V1]")]
    mocked_package_extract.side_effect = [
        [packages["A[V3]"],  packages["A[V2]"], packages["A[V1]"]],
        [packages["A[V1]"]],
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    # Remove a node.
    node = graph.node("A[V1]")
    graph.remove_node("A[V1]")

    # Relink parent from removed node.
    graph.relink_parents(node)

    # Check whether the graph has conflicts, conditions or/and errors.
    assert graph.conflicting() == {"A[V2]", "A[V3]"}
    assert graph.conflicting_variant_groups() == {(("A[V3]",), ("A[V2]",))}
    assert graph.conditioned_nodes() == []
    assert graph.errors() == {
        "root": [
            wiz.exception.GraphConflictsError({
                Requirement("::A"): {"root"},
                Requirement("::A[V1]"): {"root"},
            })
        ]
    }

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "A[V2]": wiz.graph.Node(
                packages["A[V2]"], parent_identifiers={"root"}
            ),
            "A[V3]": wiz.graph.Node(
                packages["A[V3]"], parent_identifiers={"root"}
            ),
        },
        "link_mapping": {
            "root": {
                "A[V3]": {"requirement": Requirement("::A"), "weight": 1},
                "A[V2]": {"requirement": Requirement("::A"), "weight": 1},
                "A[V1]": {"requirement": Requirement("::A[V1]"), "weight": 1},
            },
        },
        "error_mapping": {
            "root": [
                wiz.exception.GraphConflictsError({
                    Requirement("::A"): {"root"},
                    Requirement("::A[V1]"): {"root"},
                })
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
    assert graph.conflicting_variant_groups() == set()
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
    assert graph.conflicting_variant_groups() == set()
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


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_downgrade_versions(
    mocked_resolver, mocked_package_extract, packages
):
    """Downgrade node versions in the graph."""
    requirements = [Requirement("B")]
    mocked_package_extract.side_effect = [
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==3.2.0"]],
        [packages["B==1.2.2"]], [packages["C"]]
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    assert graph.downgrade_versions({"B==1.2.3", "incorrect"}) is True

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.2", "B==1.2.3"}
            ),
            "D==3.2.0": wiz.graph.Node(
                packages["D==3.2.0"], parent_identifiers={"B==1.2.3"}
            ),
            "B==1.2.2": wiz.graph.Node(
                packages["B==1.2.2"], parent_identifiers={"root"}
            ),
        },
        "link_mapping": {
            "root": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1},
                "B==1.2.2": {"requirement": Requirement("::B"), "weight": 1},
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.2.0": {
                    "requirement": Requirement("::D >=3, <4"), "weight": 2
                },
            },
            "B==1.2.2": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
            },
        },
        "error_mapping": {},
        "conditioned_nodes": [],
    }


@pytest.mark.parametrize("packages", ["conflicting-versions"], indirect=True)
def test_graph_downgrade_versions_fail(
    mocked_resolver, mocked_package_extract, packages
):
    """Fail to downgrade node versions in the graph."""
    requirements = [Requirement("B")]
    mocked_package_extract.side_effect = [
        [packages["B==1.2.3"]], [packages["C"]], [packages["D==3.2.0"]],
        wiz.exception.RequestNotFound("Error!")
    ]

    # Create graph.
    graph = wiz.graph.Graph(mocked_resolver)
    graph.update_from_requirements(requirements)

    assert graph.downgrade_versions({"C"}) is False
    assert graph.downgrade_versions({"incorrect"}) is False
    assert graph.downgrade_versions({"D==3.2.0"}) is False

    # Check full data.
    assert graph.data() == {
        "node_mapping": {
            "C": wiz.graph.Node(
                packages["C"], parent_identifiers={"B==1.2.3"}
            ),
            "D==3.2.0": wiz.graph.Node(
                packages["D==3.2.0"], parent_identifiers={"B==1.2.3"}
            ),
            "B==1.2.3": wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"root"}
            ),
        },
        "link_mapping": {
            "root": {
                "B==1.2.3": {"requirement": Requirement("::B"), "weight": 1},
            },
            "B==1.2.3": {
                "C": {"requirement": Requirement("::C"), "weight": 1},
                "D==3.2.0": {
                    "requirement": Requirement("::D >=3, <4"), "weight": 2
                },
            }
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


@pytest.mark.parametrize("options, copy_data", [
    ({}, True),
    ({"copy_data": False}, False),
], ids=[
    "simple",
    "without-copy"
])
def test_combination(
    mocked_graph, mocked_deepcopy, mocked_prune_graph, options, copy_data
):
    """Create a graph combination."""
    combination = wiz.graph.Combination(mocked_graph, **options)

    if copy_data:
        mocked_deepcopy.assert_called_once_with(mocked_graph)
        _graph = mocked_deepcopy.return_value
    else:
        mocked_deepcopy.assert_not_called()
        _graph = mocked_graph

    assert combination.graph == _graph

    _graph.nodes.assert_not_called()
    _graph.remove_node.assert_not_called()
    _graph.relink_parents.assert_not_called()

    mocked_prune_graph.assert_not_called()


@pytest.mark.parametrize("options, copy_data", [
    ({}, True),
    ({"copy_data": False}, False),
], ids=[
    "simple",
    "without-copy"
])
def test_combination_with_removed_nodes(
    mocked_graph, mocked_deepcopy, mocked_prune_graph, options, copy_data
):
    """Create a graph combination with node identifiers to remove."""
    combination = wiz.graph.Combination(
        mocked_graph, nodes_to_remove={"foo[V2]", "foo[V1]", "bar[V1]"},
        **options
    )

    if copy_data:
        mocked_deepcopy.assert_called_once_with(mocked_graph)
        _graph = mocked_deepcopy.return_value
    else:
        mocked_deepcopy.assert_not_called()
        _graph = mocked_graph

    assert combination.graph == _graph

    assert _graph.node.call_count == 3
    _graph.node.assert_any_call("foo[V2]")
    _graph.node.assert_any_call("foo[V1]")
    _graph.node.assert_any_call("bar[V1]")

    assert _graph.remove_node.call_count == 3
    _graph.remove_node.assert_any_call("foo[V2]")
    _graph.remove_node.assert_any_call("foo[V1]")
    _graph.remove_node.assert_any_call("bar[V1]")

    assert _graph.relink_parents.call_count == 3
    _graph.relink_parents.assert_any_call(_graph.node.return_value)

    mocked_prune_graph.assert_called_once_with()


def test_combination_resolve_conflicts_empty(
    mocked_graph, mocked_combined_requirements, mocked_package_extract,
    mocked_fetch_distance_mapping, mocked_prune_graph
):
    """No conflicts to resolve in a graph combination."""
    mocked_graph.conflicting.return_value = set()

    combination = wiz.graph.Combination(mocked_graph)
    combination.resolve_conflicts()

    mocked_package_extract.assert_not_called()
    mocked_combined_requirements.assert_not_called()

    mocked_graph.node.assert_not_called()
    mocked_graph.nodes.assert_not_called()
    mocked_graph.remove_node.assert_not_called()
    mocked_graph.relink_parents.assert_not_called()
    mocked_graph.conflicting_variant_groups.assert_not_called()
    mocked_graph.update_from_package.assert_not_called()

    mocked_fetch_distance_mapping.assert_not_called()
    mocked_prune_graph.assert_not_called()


@pytest.mark.parametrize("packages", ["combination-resolution"], indirect=True)
def test_combination_resolve_conflicts_simple(
    mocker, mocked_graph, packages, mocked_combined_requirements,
    mocked_package_extract, mocked_fetch_distance_mapping, mocked_prune_graph,
    mocked_extract_conflicting_requirements
):
    """Resolve simple conflict with two nodes.

    First node analyzed is removed, second one is kept.

    Root
     |
     |--(A==1.2.*): A==1.2.0
     |
     `--(B): B
         |
         `--(A>1): A==1.4.8

    """
    # Mock nodes.
    nodes = {
        "A==1.4.8": wiz.graph.Node(
            packages["A==1.4.8"], parent_identifiers={"B"}
        ),
        "A==1.2.0": wiz.graph.Node(
            packages["A==1.2.0"], parent_identifiers={"root"}
        ),
    }

    # Mock graph and side logic.
    mocked_graph.node.side_effect = [nodes["A==1.4.8"], nodes["A==1.2.0"]]
    mocked_graph.nodes.side_effect = [
        [nodes["A==1.4.8"], nodes["A==1.2.0"]], [nodes["A==1.2.0"]]
    ]
    mocked_graph.conflicting.side_effect = [{"A==1.2.0", "A==1.4.8"}]
    mocked_combined_requirements.side_effect = [Requirement("::A >1, ==1.2.*")]
    mocked_package_extract.side_effect = [[packages["A==1.2.0"]]]

    # Mocked distance mapping is used to sort 'A==1.4.8' before 'A==1.2.0'.
    mocked_fetch_distance_mapping.return_value = {
        "A==1.2.0": {"distance": 1}, "A==1.4.8": {"distance": 3},
    }

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.resolve_conflicts()

    combined_requirement = Requirement("::A >1, ==1.2.*")

    mocked_package_extract.assert_called_once_with(
        combined_requirement, mocked_graph.resolver.definition_mapping
    )
    mocked_combined_requirements.assert_called_once_with(
        mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]]
    )
    mocked_extract_conflicting_requirements.assert_not_called()
    mocked_fetch_distance_mapping.assert_called_once()

    assert mocked_graph.node.call_args_list == [
        mocker.call("A==1.4.8"),
        mocker.call("A==1.2.0")
    ]
    assert mocked_graph.nodes.call_args_list == [
        mocker.call(definition_identifier="A"),
        mocker.call(definition_identifier="A"),
    ]

    mocked_graph.remove_node.assert_called_once_with("A==1.4.8")
    mocked_graph.relink_parents.assert_called_once_with(
        nodes["A==1.4.8"], requirement=combined_requirement
    )
    mocked_graph.conflicting_variant_groups.assert_not_called()
    mocked_graph.update_from_package.assert_not_called()
    mocked_prune_graph.assert_called_once()


@pytest.mark.parametrize("packages", ["combination-resolution"], indirect=True)
def test_combination_resolve_conflicts_simple_inverted_order(
    mocker, mocked_graph, packages, mocked_combined_requirements,
    mocked_package_extract, mocked_fetch_distance_mapping, mocked_prune_graph,
    mocked_extract_conflicting_requirements
):
    """Resolve simple conflict with two nodes treated in inverted order.

    First node analyzed is kept, second one is removed.

    Root
     |
     |--(A>1): A==1.4.8
     |
     `--(B): B
         |
         `--(A==1.2.*): A==1.2.0

    """
    # Mock nodes.
    nodes = {
        "A==1.4.8": wiz.graph.Node(
            packages["A==1.4.8"], parent_identifiers={"root"}
        ),
        "A==1.2.0": wiz.graph.Node(
            packages["A==1.2.0"], parent_identifiers={"B"}
        ),
    }

    # Mock graph and side logic.
    mocked_graph.node.side_effect = [nodes["A==1.2.0"], nodes["A==1.4.8"]]
    mocked_graph.nodes.side_effect = [
        [nodes["A==1.4.8"], nodes["A==1.2.0"]],
        [nodes["A==1.4.8"], nodes["A==1.2.0"]]
    ]
    mocked_graph.conflicting.side_effect = [{"A==1.2.0", "A==1.4.8"}]
    mocked_combined_requirements.side_effect = [
        Requirement("::A >1, ==1.2.*"),
        Requirement("::A >1, ==1.2.*")
    ]
    mocked_package_extract.side_effect = [
        [packages["A==1.2.0"]], [packages["A==1.2.0"]],
    ]

    # Mocked distance mapping is used to sort 'A==1.2.0' before 'A==1.4.8'.
    mocked_fetch_distance_mapping.return_value = {
        "A==1.4.8": {"distance": 1}, "A==1.2.0": {"distance": 3},
    }

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.resolve_conflicts()

    mapping = mocked_graph.resolver.definition_mapping
    combined_requirement = Requirement("::A >1, ==1.2.*")

    assert mocked_package_extract.call_args_list == [
        mocker.call(combined_requirement, mapping),
        mocker.call(combined_requirement, mapping),
    ]
    assert mocked_combined_requirements.call_args_list == [
        mocker.call(mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]]),
        mocker.call(mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]])
    ]
    mocked_extract_conflicting_requirements.assert_not_called()
    mocked_fetch_distance_mapping.assert_called_once()

    assert mocked_graph.node.call_args_list == [
        mocker.call("A==1.2.0"),
        mocker.call("A==1.4.8"),
    ]
    assert mocked_graph.nodes.call_args_list == [
        mocker.call(definition_identifier="A"),
        mocker.call(definition_identifier="A"),
    ]

    mocked_graph.remove_node.assert_called_once_with("A==1.4.8")
    mocked_graph.relink_parents.assert_called_once_with(
        nodes["A==1.4.8"], requirement=combined_requirement
    )
    mocked_graph.conflicting_variant_groups.assert_not_called()
    mocked_graph.update_from_package.assert_not_called()
    mocked_prune_graph.assert_called_once()


@pytest.mark.parametrize("packages", ["combination-resolution"], indirect=True)
def test_combination_resolve_conflicts_simple_fail(
    mocked_graph, packages, mocked_combined_requirements,
    mocked_package_extract, mocked_fetch_distance_mapping, mocked_prune_graph,
    mocked_extract_conflicting_requirements
):
    """Fail to resolve simple conflict with two nodes.

    Requirements of nodes are incompatible.

    Root
     |
     |--(A==1.2.*): A==1.2.0
     |
     `--(B): B
         |
         `--(A==1.4.*): A==1.4.8

    """
    # Mock nodes.
    nodes = {
        "A==1.4.8": wiz.graph.Node(
            packages["A==1.4.8"], parent_identifiers={"B"}
        ),
        "A==1.2.0": wiz.graph.Node(
            packages["A==1.2.0"], parent_identifiers={"root"}
        ),
    }

    # Mock graph and side logic.
    mocked_graph.node.side_effect = [nodes["A==1.4.8"], nodes["A==1.2.0"]]
    mocked_graph.nodes.side_effect = [[nodes["A==1.4.8"], nodes["A==1.2.0"]]]
    mocked_graph.conflicting.side_effect = [{"A==1.2.0", "A==1.4.8"}]
    mocked_combined_requirements.side_effect = [
        Requirement("::A ==1.4.*, ==1.2.*")
    ]
    mocked_package_extract.side_effect = wiz.exception.RequestNotFound("Error")

    # Mocked distance mapping is used to sort 'A==1.4.8' before 'A==1.2.0'.
    mocked_fetch_distance_mapping.return_value = {
        "A==1.2.0": {"distance": 1}, "A==1.4.8": {"distance": 3},
    }

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)

    with pytest.raises(wiz.exception.GraphConflictsError):
        combination.resolve_conflicts()

    combined_requirement = Requirement("::A ==1.4.*, ==1.2.*")

    mocked_package_extract.assert_called_once_with(
        combined_requirement, mocked_graph.resolver.definition_mapping
    )
    mocked_combined_requirements.assert_called_once_with(
        mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]]
    )
    mocked_extract_conflicting_requirements.assert_called_once_with(
        mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]]
    )
    mocked_fetch_distance_mapping.assert_called_once()

    mocked_graph.node.assert_called_once_with("A==1.4.8")
    mocked_graph.nodes.assert_called_once_with(definition_identifier="A")

    mocked_graph.remove_node.assert_not_called()
    mocked_graph.relink_parents.assert_not_called()
    mocked_graph.conflicting_variant_groups.assert_not_called()
    mocked_graph.update_from_package.assert_not_called()
    mocked_prune_graph.assert_not_called()


@pytest.mark.parametrize("packages", ["combination-resolution"], indirect=True)
def test_combination_resolve_conflicts_new_package(
    mocker, mocked_graph, packages, mocked_combined_requirements,
    mocked_package_extract, mocked_fetch_distance_mapping, mocked_prune_graph,
    mocked_extract_conflicting_requirements
):
    """Resolve conflict with new package added.

    Combining the two requirements lead to a new package (A==1.1.0).

    Root
     |
     |--(A<=1.2.0): A==1.2.0
     |
     `--(B): B
         |
         `--(A !=1.2.0): A==1.4.8

    """
    # Mock nodes.
    nodes = {
        "A==1.4.8": wiz.graph.Node(
            packages["A==1.4.8"], parent_identifiers={"B"}
        ),
        "A==1.1.0": wiz.graph.Node(
            packages["A==1.1.0"], parent_identifiers={"B"}
        ),
        "A==1.2.0": wiz.graph.Node(
            packages["A==1.2.0"], parent_identifiers={"root"}
        ),
    }

    # Mock graph and side logic.
    mocked_graph.node.side_effect = [
        nodes["A==1.4.8"], nodes["A==1.2.0"], nodes["A==1.1.0"]
    ]
    mocked_graph.nodes.side_effect = [
        [nodes["A==1.4.8"], nodes["A==1.2.0"]],
        [nodes["A==1.1.0"], nodes["A==1.2.0"]],
        [nodes["A==1.1.0"], nodes["A==1.2.0"]]
    ]
    mocked_graph.conflicting.side_effect = [
        {"A==1.2.0", "A==1.4.8"}, {"A==1.1.0", "A==1.2.0"}
    ]
    mocked_graph.conflicting_variant_groups.return_value = []
    mocked_combined_requirements.side_effect = [
        Requirement("::A <=1.2.0, !=1.2.0"),
        Requirement("::A <=1.2.0, !=1.2.0"),
        Requirement("::A <=1.2.0, !=1.2.0"),
    ]
    mocked_package_extract.side_effect = [
        [packages["A==1.1.0"]], [packages["A==1.1.0"]], [packages["A==1.1.0"]],
    ]

    # Mocked distance mapping is used to sort 'A==1.4.8' before 'A==1.2.0',
    # then 'A==1.1.0' before 'A==1.2.0'.
    mocked_fetch_distance_mapping.side_effect = [
        {"A==1.2.0": {"distance": 1}, "A==1.4.8": {"distance": 3}},
        {"A==1.2.0": {"distance": 1}, "A==1.1.0": {"distance": 3}},
    ]

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.resolve_conflicts()

    mapping = mocked_graph.resolver.definition_mapping
    combined_requirement = Requirement("::A <=1.2.0, !=1.2.0")

    assert mocked_package_extract.call_args_list == [
        mocker.call(combined_requirement, mapping),
        mocker.call(combined_requirement, mapping),
        mocker.call(combined_requirement, mapping),
    ]
    assert mocked_combined_requirements.call_args_list == [
        mocker.call(mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]]),
        mocker.call(mocked_graph, [nodes["A==1.1.0"], nodes["A==1.2.0"]]),
        mocker.call(mocked_graph, [nodes["A==1.1.0"], nodes["A==1.2.0"]])
    ]

    mocked_extract_conflicting_requirements.assert_not_called()
    assert mocked_fetch_distance_mapping.call_count == 2

    assert mocked_graph.node.call_args_list == [
        mocker.call("A==1.4.8"),
        mocker.call("A==1.1.0"),
        mocker.call("A==1.2.0")
    ]
    assert mocked_graph.nodes.call_args_list == [
        mocker.call(definition_identifier="A"),
        mocker.call(definition_identifier="A"),
        mocker.call(definition_identifier="A")
    ]

    assert mocked_graph.remove_node.call_args_list == [
        mocker.call("A==1.4.8"),
        mocker.call("A==1.2.0"),
    ]
    assert mocked_graph.relink_parents.call_args_list == [
        mocker.call(nodes["A==1.4.8"], requirement=combined_requirement),
        mocker.call(nodes["A==1.2.0"], requirement=combined_requirement),
    ]
    mocked_graph.conflicting_variant_groups.assert_called_once()
    mocked_graph.update_from_package.assert_called_once_with(
        getattr(nodes["A==1.1.0"], "package"),
        Requirement("::A <=1.2.0, !=1.2.0"),
        detached=True
    )
    assert mocked_prune_graph.call_count == 2


@pytest.mark.parametrize("packages", ["combination-resolution"], indirect=True)
def test_combination_resolve_conflicts_new_variant(
    mocked_graph, packages, mocked_combined_requirements,
    mocked_package_extract, mocked_fetch_distance_mapping, mocked_prune_graph,
    mocked_extract_conflicting_requirements
):
    """Resolve conflict with new package added which lead to graph division.

    Combining the two requirements lead to a new package (A==1.1.0), which
    pulls new package variants into the graph (C[V1], C[V2]).

    Root
     |
     |--(A<=1.2.0): A==1.2.0
     |
     `--(B): B
         |
         `--(A !=1.2.0): A==1.4.8

    """
    # Mock nodes.
    nodes = {
        "A==1.4.8": wiz.graph.Node(
            packages["A==1.4.8"], parent_identifiers={"B"}
        ),
        "A==1.1.0": wiz.graph.Node(
            packages["A==1.1.0"], parent_identifiers={"B"}
        ),
        "A==1.2.0": wiz.graph.Node(
            packages["A==1.2.0"], parent_identifiers={"root"}
        ),
    }

    # Mock graph and side logic.
    mocked_graph.node.side_effect = [nodes["A==1.4.8"]]
    mocked_graph.nodes.side_effect = [[nodes["A==1.4.8"], nodes["A==1.2.0"]]]
    mocked_graph.conflicting.side_effect = [{"A==1.2.0", "A==1.4.8"}]
    mocked_graph.conflicting_variant_groups.return_value = [["C[V2]", "C[V1]"]]
    mocked_combined_requirements.side_effect = [
        Requirement("::A <=1.2.0, !=1.2.0")
    ]
    mocked_package_extract.side_effect = [
        [packages["A==1.1.0"]],
    ]

    # Mocked distance mapping is used to sort 'A==1.4.8' before 'A==1.2.0',
    # then 'A==1.1.0' before 'A==1.2.0'.
    mocked_fetch_distance_mapping.side_effect = [
        {"A==1.2.0": {"distance": 1}, "A==1.4.8": {"distance": 3}},
        {"A==1.2.0": {"distance": 1}, "A==1.1.0": {"distance": 3}},
    ]

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)

    with pytest.raises(wiz.exception.GraphVariantsError):
        combination.resolve_conflicts()

    mapping = mocked_graph.resolver.definition_mapping
    combined_requirement = Requirement("::A <=1.2.0, !=1.2.0")

    mocked_package_extract.assert_called_once_with(
        combined_requirement, mapping
    )
    mocked_combined_requirements.assert_called_once_with(
        mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]]
    )

    mocked_extract_conflicting_requirements.assert_not_called()
    mocked_fetch_distance_mapping.assert_called_once()

    mocked_graph.node.assert_called_once_with("A==1.4.8")
    mocked_graph.nodes.assert_called_once_with(definition_identifier="A")

    mocked_graph.remove_node.assert_called_once_with("A==1.4.8")
    mocked_graph.relink_parents.assert_called_once_with(
        nodes["A==1.4.8"], requirement=combined_requirement
    )

    mocked_graph.conflicting_variant_groups.assert_called_once()
    mocked_graph.update_from_package.assert_called_once_with(
        packages["A==1.1.0"], combined_requirement, detached=True
    )
    mocked_prune_graph.assert_not_called()


@pytest.mark.parametrize("packages", ["combination-resolution"], indirect=True)
def test_combination_resolve_conflicts_circular(
    mocker, mocked_graph, packages, mocked_combined_requirements,
    mocked_package_extract, mocked_fetch_distance_mapping, mocked_prune_graph,
    mocked_extract_conflicting_requirements
):
    """Resolve circular conflicts.

    Requirement 'A==1.4.*' and 'A==1.2.*' are incompatible, but as 'A==1.4.8'
    has been pulled by 'B==1.2.3' which is itself conflicting, the graph is
    resolved by resolving this parent conflict.

    Root
     |
     |--(A==1.2.*): A==1.2.0
     |   |
     |   `--(B<1): B==0.1.0
     |
     `--(B): B==1.2.3
         |
         `--(A==1.4.*): A==1.4.8

    """
    # Mock nodes.
    nodes = {
        "A==1.4.8": wiz.graph.Node(
            packages["A==1.4.8"], parent_identifiers={"B==1.2.3"}
        ),
        "A==1.2.0": wiz.graph.Node(
            packages["A==1.2.0"], parent_identifiers={"root"}
        ),
        "B==1.2.3": wiz.graph.Node(
            packages["B==1.2.3"], parent_identifiers={"root"}
        ),
        "B==0.1.0": wiz.graph.Node(
            packages["B==0.1.0"], parent_identifiers={"A==1.2.0"}
        ),
    }

    # Mock graph and side logic.
    mocked_graph.node.side_effect = [
        nodes["A==1.4.8"], nodes["B==1.2.3"],
        nodes["B==0.1.0"], nodes["A==1.2.0"], None,
    ]
    mocked_graph.nodes.side_effect = [
        [nodes["A==1.4.8"], nodes["A==1.2.0"]],
        [nodes["B==0.1.0"], nodes["B==1.2.3"]],
        [nodes["B==0.1.0"], nodes["B==1.2.3"]],
        [nodes["A==1.2.0"]],
    ]
    mocked_graph.conflicting.side_effect = [
        {"A==1.2.0", "A==1.4.8", "B==0.1.0", "B==1.2.3"}
    ]
    mocked_combined_requirements.side_effect = [
        Requirement("::A ==1.2.*, ==1.4.*"),
        Requirement("::B <1"),
        Requirement("::B <1"),
    ]
    mocked_package_extract.side_effect = [
        wiz.exception.RequestNotFound("Error"),
        [packages["B==0.1.0"]],
        [packages["B==0.1.0"]]
    ]

    # Mock conflict mappings indicating that conflicting parents.
    mocked_extract_conflicting_requirements.return_value = {
        Requirement("A==1.2.*"): {"root"},
        Requirement("A==1.4.*"): {"B==1.2.3"},
    }

    # Mocked distance mapping is used to sort nodes.
    mocked_fetch_distance_mapping.side_effect = [
        {
            "A==1.2.0": {"distance": 1},
            "B==0.1.0": {"distance": 2},
            "B==1.2.3": {"distance": 2},
            "A==1.4.8": {"distance": 3}
        },
    ]

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.resolve_conflicts()

    mapping = mocked_graph.resolver.definition_mapping
    assert mocked_package_extract.call_args_list == [
        mocker.call(Requirement("::A ==1.2.*, ==1.4.*"), mapping),
        mocker.call(Requirement("::B <1"), mapping),
        mocker.call(Requirement("::B <1"), mapping),
    ]
    assert mocked_combined_requirements.call_args_list == [
        mocker.call(mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]]),
        mocker.call(mocked_graph, [nodes["B==0.1.0"], nodes["B==1.2.3"]]),
        mocker.call(mocked_graph, [nodes["B==0.1.0"], nodes["B==1.2.3"]]),
    ]
    mocked_extract_conflicting_requirements.assert_called_once_with(
        mocked_graph, [nodes["A==1.4.8"], nodes["A==1.2.0"]]
    )
    mocked_fetch_distance_mapping.assert_called_once()

    assert mocked_graph.node.call_args_list == [
        mocker.call("A==1.4.8"),
        mocker.call("B==1.2.3"),
        mocker.call("B==0.1.0"),
        mocker.call("A==1.2.0"),
        mocker.call("A==1.4.8"),
    ]
    assert mocked_graph.nodes.call_args_list == [
        mocker.call(definition_identifier="A"),
        mocker.call(definition_identifier="B"),
        mocker.call(definition_identifier="B"),
        mocker.call(definition_identifier="A"),
    ]

    mocked_graph.remove_node.assert_called_once_with("B==1.2.3")
    mocked_graph.relink_parents.assert_called_once_with(
        nodes["B==1.2.3"], requirement=Requirement("::B <1")
    )

    mocked_graph.conflicting_variant_groups.assert_not_called()
    mocked_graph.update_from_package.assert_not_called()
    mocked_prune_graph.assert_called_once()


def test_combination_validate(mocked_graph):
    """Ensure that graph does not contain any error."""
    mocked_graph.errors.return_value = {}

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.validate()

    mocked_graph.errors.assert_called_once()


def test_combination_validate_raise(mocked_graph):
    """Raise when the graph contains an error."""
    mocked_graph.errors.return_value = {"foo": "Error!"}

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)

    with pytest.raises(wiz.exception.GraphInvalidNodesError):
        combination.validate()

    mocked_graph.errors.assert_called_once()


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_combination_extract_packages(
    mocked_graph, mocked_compute_distance_mapping, packages
):
    """Extract extracted packages."""
    mocked_compute_distance_mapping.return_value = {
        "A==0.1.0": {"distance": 1},
        "B==1.2.3": {"distance": 2},
        "C": {"distance": None},
        "D==4.1.0": {"distance": 5},
        "E==0.1.0": {"distance": 2},
    }

    mocked_graph.nodes.return_value = [
        wiz.graph.Node(packages["A==0.1.0"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}),
        wiz.graph.Node(packages["C"], parent_identifiers={"B==1.2.3"}),
        wiz.graph.Node(packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}),
        wiz.graph.Node(packages["E==0.1.0"], parent_identifiers={"root"}),
    ]

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    assert combination.extract_packages() == [
        packages["D==4.1.0"],
        packages["E==0.1.0"],
        packages["B==1.2.3"],
        packages["A==0.1.0"],
    ]


def test_prune_graph_empty(mocked_graph, mocked_compute_distance_mapping):
    """Prune empty graph."""
    mocked_graph.nodes.return_value = []
    mocked_graph.conditioned_nodes.return_value = []

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.prune_graph()

    mocked_compute_distance_mapping.assert_called_once()
    mocked_graph.remove_node.assert_not_called()
    mocked_graph.exists.assert_not_called()
    mocked_graph.find.assert_not_called()


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_prune_graph_none(
    mocked_graph, mocked_compute_distance_mapping, packages
):
    """Prune graph without any nodes to remove."""
    mocked_compute_distance_mapping.return_value = {
        "A==0.1.0": {"distance": 1},
        "B==1.2.3": {"distance": 2},
        "C": {"distance": 4},
        "D==4.1.0": {"distance": 5},
        "E==0.1.0": {"distance": 2},
    }

    mocked_graph.nodes.return_value = [
        wiz.graph.Node(packages["A==0.1.0"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}),
        wiz.graph.Node(packages["C"], parent_identifiers={"B==1.2.3"}),
        wiz.graph.Node(packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}),
        wiz.graph.Node(packages["E==0.1.0"], parent_identifiers={"root"}),
    ]
    mocked_graph.conditioned_nodes.return_value = []

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.prune_graph()

    mocked_compute_distance_mapping.assert_called_once()
    mocked_graph.remove_node.assert_not_called()
    mocked_graph.exists.assert_not_called()
    mocked_graph.find.assert_not_called()


@pytest.mark.parametrize("packages", ["many"], indirect=True)
def test_prune_graph_one_unreachable(
    mocked_graph, mocked_compute_distance_mapping, packages
):
    """Prune graph with one unreachable node to remove."""
    mocked_compute_distance_mapping.return_value = {
        "A==0.1.0": {"distance": 1},
        "B==1.2.3": {"distance": 2},
        "C": {"distance": None},
        "D==4.1.0": {"distance": 5},
        "E==0.1.0": {"distance": 2},
    }

    mocked_graph.nodes.return_value = [
        wiz.graph.Node(packages["A==0.1.0"], parent_identifiers={"root"}),
        wiz.graph.Node(packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}),
        wiz.graph.Node(packages["C"], parent_identifiers={"B==1.2.3"}),
        wiz.graph.Node(packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}),
        wiz.graph.Node(packages["E==0.1.0"], parent_identifiers={"root"}),
    ]
    mocked_graph.conditioned_nodes.return_value = []

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.prune_graph()

    mocked_compute_distance_mapping.assert_called_once()
    mocked_graph.remove_node.assert_called_once_with("C")
    mocked_graph.exists.assert_not_called()
    mocked_graph.find.assert_not_called()


@pytest.mark.parametrize("packages", ["many-with-conditions"], indirect=True)
def test_prune_graph_unfulfilled_conditions_one(
    mocker, mocked_graph, mocked_compute_distance_mapping, packages
):
    """Prune graph with one unfulfilled conditioned node to remove."""
    mocked_compute_distance_mapping.side_effect = [
        {
            "A==0.1.0": {"distance": 1},
            "B==1.2.3": {"distance": 2},
            "C": {"distance": 4},
            "D==4.1.0": {"distance": None},
            "E": {"distance": 2},
            "F==13": {"distance": 3},
            "G": {"distance": 3},
        },
        {
            "A==0.1.0": {"distance": 1},
            "B==1.2.3": {"distance": 2},
            "C": {"distance": 4},
            "D==4.1.0": {"distance": None},
            "E": {"distance": 2},
            "F==13": {"distance": 3},
            "G": {"distance": None},
        },
    ]

    mocked_graph.nodes.side_effect = [
        [
            wiz.graph.Node(packages["A==0.1.0"], parent_identifiers={"root"}),
            wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            wiz.graph.Node(packages["C"], parent_identifiers={"B==1.2.3"}),
            wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            ),
            wiz.graph.Node(packages["E"], parent_identifiers={"root"}),
            wiz.graph.Node(packages["F==13"], parent_identifiers={"E"}),
            wiz.graph.Node(packages["G"], parent_identifiers={"root"}),
        ],
        [
            wiz.graph.Node(packages["A==0.1.0"], parent_identifiers={"root"}),
            wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            wiz.graph.Node(packages["C"], parent_identifiers={"B==1.2.3"}),
            wiz.graph.Node(packages["E"], parent_identifiers={"root"}),
            wiz.graph.Node(packages["F==13"], parent_identifiers={"E"}),
        ],
    ]
    mocked_graph.conditioned_nodes.return_value = [
        wiz.graph.StoredNode(Requirement("::A"), packages["A==0.1.0"], "root"),
        wiz.graph.StoredNode(Requirement("::G"), packages["G"], "root"),
    ]

    mocked_graph.exists.side_effect = [True, True, True, False]
    mocked_graph.find.side_effect = [["E"], ["F==13"], [], ["E"]]

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.prune_graph()

    assert mocked_compute_distance_mapping.call_count == 2

    assert mocked_graph.remove_node.call_args_list == [
        mocker.call("D==4.1.0"),
        mocker.call("G"),
    ]
    assert mocked_graph.exists.call_args_list == [
        mocker.call("A==0.1.0"),
        mocker.call("G"),
        mocker.call("A==0.1.0"),
        mocker.call("G")
    ]
    assert mocked_graph.find.call_args_list == [
        mocker.call(Requirement("E")),
        mocker.call(Requirement("F")),
        mocker.call(Requirement("D")),
        mocker.call(Requirement("E")),
    ]


@pytest.mark.parametrize("packages", ["many-with-conditions"], indirect=True)
def test_prune_graph_unfulfilled_conditions_two(
    mocker, mocked_graph, mocked_compute_distance_mapping, packages
):
    """Prune graph with two unfulfilled conditioned nodes to remove."""
    mocked_compute_distance_mapping.side_effect = [
        {
            "A==0.1.0": {"distance": 1},
            "B==1.2.3": {"distance": 2},
            "C": {"distance": 4},
            "D==4.1.0": {"distance": 5},
            "E": {"distance": None},
            "F==13": {"distance": None},
            "G": {"distance": 3},
        },
        {
            "A==0.1.0": {"distance": None},
            "B==1.2.3": {"distance": None},
            "C": {"distance": None},
            "D==4.1.0": {"distance": None},
            "E": {"distance": None},
            "F==13": {"distance": None},
            "G": {"distance": None},
        },
    ]

    mocked_graph.nodes.side_effect = [
        [
            wiz.graph.Node(packages["A==0.1.0"], parent_identifiers={"root"}),
            wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            wiz.graph.Node(packages["C"], parent_identifiers={"B==1.2.3"}),
            wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            ),
            wiz.graph.Node(packages["E"], parent_identifiers={"root"}),
            wiz.graph.Node(packages["F==13"], parent_identifiers={"E"}),
            wiz.graph.Node(packages["G"], parent_identifiers={"root"}),
        ],
        [
            wiz.graph.Node(
                packages["B==1.2.3"], parent_identifiers={"A==0.1.0"}
            ),
            wiz.graph.Node(packages["C"], parent_identifiers={"B==1.2.3"}),
            wiz.graph.Node(
                packages["D==4.1.0"], parent_identifiers={"B==1.2.3"}
            ),
        ],
    ]
    mocked_graph.conditioned_nodes.return_value = [
        wiz.graph.StoredNode(Requirement("::A"), packages["A==0.1.0"], "root"),
        wiz.graph.StoredNode(Requirement("::G"), packages["G"], "root"),
    ]

    mocked_graph.exists.side_effect = [True, True, False, False, False, False]
    mocked_graph.find.side_effect = [[], []]

    combination = wiz.graph.Combination(mocked_graph, copy_data=False)
    combination.prune_graph()

    assert mocked_compute_distance_mapping.call_count == 2

    assert mocked_graph.remove_node.call_args_list == [
        mocker.call("E"),
        mocker.call("F==13"),
        mocker.call("A==0.1.0"),
        mocker.call("G"),
        mocker.call("B==1.2.3"),
        mocker.call("C"),
        mocker.call("D==4.1.0"),
    ]
    assert mocked_graph.exists.call_args_list == [
        mocker.call("A==0.1.0"),
        mocker.call("G"),
        mocker.call("A==0.1.0"),
        mocker.call("G"),
        mocker.call("A==0.1.0"),
        mocker.call("G"),
    ]
    assert mocked_graph.find.call_args_list == [
        mocker.call(Requirement("E")),
        mocker.call(Requirement("F")),
    ]


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
