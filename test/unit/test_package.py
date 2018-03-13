# :coding: utf-8

import itertools

import pytest
from packaging.requirements import Requirement

import wiz.package
import wiz.graph
import wiz.definition
import wiz.exception


@pytest.mark.parametrize("environment, variant_name, expected", [
    (
        wiz.definition.Environment({
            "identifier": "env1",
            "version": "0.3.4",
        }),
        None,
        "env1==0.3.4"
    ),
    (
        wiz.definition.Environment({
            "identifier": "env1",
            "version": "0.3.4",
        }),
        "Variant",
        "env1[Variant]==0.3.4"
    )
], ids=[
    "without-variant",
    "with-variant",
])
def test_generate_identifier(environment, variant_name, expected):
    """Generate the package identifier."""
    assert (
        wiz.package.generate_identifier(environment, variant_name) == expected
    )


def test_resolve(mocker):
    """Return resolved environments from requirement."""
    mocked_process = mocker.Mock(
        **{"compute_environments.return_value": "ENVIRONMENTS"}
    )
    resolver = mocker.patch.object(
        wiz.graph, "Resolver", return_value=mocked_process
    )

    requirements = [
        Requirement("env1"),
        Requirement("env2==0.1.5")
    ]

    result = wiz.package.resolve(requirements, {})
    assert result == "ENVIRONMENTS"

    resolver.assert_called_once_with({})
    mocked_process.compute_environments.assert_called_once_with(requirements)


@pytest.fixture()
def mocked_environment_getter(mocker):
    """Return mocked environment getter."""
    return mocker.patch.object(wiz.environment, "get")


@pytest.fixture()
def mocked_package(mocker):
    """Return mocked Package constructor."""
    return mocker.patch.object(wiz.package, "Package", return_value="PACKAGE")


def test_extract_without_variant(mocked_environment_getter, mocked_package):
    """Extract one Package from environment."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        }
    })

    mocked_environment_getter.return_value = environment

    requirement = Requirement("env1")
    result = wiz.package.extract(requirement, {})
    mocked_environment_getter.assert_called_once_with(requirement, {})

    mocked_package.assert_called_once_with(environment)
    assert result == ["PACKAGE"]


def test_extract_with_all_variants(mocked_environment_getter, mocked_package):
    """Extract all variant Packages from environment."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "variant": [
            {
                "identifier": "Variant1",
                "data": {"KEY1": "VALUE1"}
            },
            {
                "identifier": "Variant2",
                "data": {"KEY2": "VALUE2"}
            },
            {
                "identifier": "Variant3",
                "data": {"KEY3": "VALUE3"}
            }
        ]
    })

    mocked_environment_getter.return_value = environment

    requirement = Requirement("env1")
    result = wiz.package.extract(requirement, {})
    mocked_environment_getter.assert_called_once_with(requirement, {})

    assert mocked_package.call_count == 3
    mocked_package.assert_any_call(environment, {
        "identifier": "Variant1",
        "data": {"KEY1": "VALUE1"}
    })
    mocked_package.assert_any_call(environment, {
        "identifier": "Variant2",
        "data": {"KEY2": "VALUE2"}
    })
    mocked_package.assert_any_call(environment, {
        "identifier": "Variant3",
        "data": {"KEY3": "VALUE3"}
    })

    assert result == ["PACKAGE", "PACKAGE", "PACKAGE"]


def test_extract_with_one_requested_variant(
    mocked_environment_getter, mocked_package
):
    """Extract one requested variant Package from environment."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "variant": [
            {
                "identifier": "Variant1",
                "data": {"KEY1": "VALUE1"}
            },
            {
                "identifier": "Variant2",
                "data": {"KEY2": "VALUE2"}
            },
            {
                "identifier": "Variant3",
                "data": {"KEY3": "VALUE3"}
            }
        ]
    })

    mocked_environment_getter.return_value = environment

    requirement = Requirement("env1[Variant2]")
    result = wiz.package.extract(requirement, {})
    mocked_environment_getter.assert_called_once_with(requirement, {})

    mocked_package.assert_called_once_with(environment, {
        "identifier": "Variant2",
        "data": {"KEY2": "VALUE2"}
    })

    assert result == ["PACKAGE"]


def test_extract_error(mocked_environment_getter, mocked_package):
    """Fail to extract Package from environment."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        }
    })

    mocked_environment_getter.return_value = environment

    requirement = Requirement("env1[Incorrect]")

    with pytest.raises(wiz.exception.RequestNotFound) as error:
        wiz.package.extract(requirement, {})

    mocked_environment_getter.assert_called_once_with(requirement, {})
    mocked_package.assert_not_called()

    assert (
        "The variant 'Incorrect' could not been resolved "
        "for 'env1' [0.3.4]." in str(error)
    )


@pytest.fixture()
def mocked_combine_data(mocker):
    """Return mocked combine_data function."""
    return mocker.patch.object(
        wiz.package, "combine_data", return_value={"_KEY": "_VALUE"}
    )


@pytest.fixture()
def mocked_combine_alias(mocker):
    """Return mocked combine_alias function."""
    return mocker.patch.object(
        wiz.package, "combine_alias", return_value={"_APP": "_APP_X"}
    )


@pytest.mark.parametrize("environments, arguments, expected", [
    (
        [], [], {"data": {}}
    ),
    (
        [{}], [({"data": {}}, {})],
        {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}}
    ),
    (
        [
            wiz.definition.Environment({
                "alias": {"app1": "App1"}, "data": {"KEY1": "VALUE1"}
            })
        ],
        [
            (
                {"data": {}},
                wiz.definition.Environment({
                    "alias": {"app1": "App1"}, "data": {"KEY1": "VALUE1"}
                })
            )
        ],
        {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}}
    ),
    (
        [
            wiz.definition.Environment({
                "alias": {"app1": "App1"}, "data": {"KEY1": "VALUE1"}
            }),
            wiz.definition.Environment({
                "alias": {"app2": "App2"}, "data": {"KEY2": "VALUE2"}
            })
        ],
        [
            (
                {"data": {}},
                wiz.definition.Environment({
                    "alias": {"app1": "App1"}, "data": {"KEY1": "VALUE1"}
                })
            ),
            (
                {"data": {"_KEY": "_VALUE"}, "alias": {"_APP": "_APP_X"}},
                wiz.definition.Environment({
                    "alias": {"app2": "App2"}, "data": {"KEY2": "VALUE2"}
                })
            )
        ],
        {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}}
    ),
    (
        [
            wiz.definition.Environment({"data": {"KEY1": "VALUE1"}}),
            wiz.definition.Environment({
                "alias": {"app1": "App1"}, "data": {"KEY2": "VALUE2"}
            }),
            wiz.definition.Environment({
                "alias": {"app2": "App2"}, "data": {"KEY3": "VALUE3"}
            }),
            wiz.definition.Environment({"data": {"KEY4": "PATH1:PATH2:PATH3"}}),
            wiz.definition.Environment({
                "alias": {"app1": "AppX"}, "data": {"KEY5": "VALUE5"}
            })
        ],
        [
            (
                {"data": {}},
                wiz.definition.Environment({"data": {"KEY1": "VALUE1"}})
            ),
            (
                {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}},
                wiz.definition.Environment({
                    "alias": {"app1": "App1"}, "data": {"KEY2": "VALUE2"}
                })
            ),
            (
                {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}},
                wiz.definition.Environment({
                    "alias": {"app2": "App2"}, "data": {"KEY3": "VALUE3"}
                })
            ),
            (
                {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}},
                wiz.definition.Environment({
                    "data": {"KEY4": "PATH1:PATH2:PATH3"}
                })
            ),
            (
                {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}},
                wiz.definition.Environment({
                    "alias": {"app1": "AppX"}, "data": {"KEY5": "VALUE5"}
                })
            ),
        ],
        {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}}
    )
], ids=[
    "no-environment",
    "empty-environment",
    "one-environment",
    "two-environments",
    "five-environments"
])
def test_extract_context(
    mocked_combine_data, mocked_combine_alias, environments, arguments, expected
):
    """Return extracted context."""
    assert wiz.package.extract_context(environments) == expected
    assert mocked_combine_data.call_count == len(arguments)
    assert mocked_combine_alias.call_count == len(arguments)

    print mocked_combine_alias.call_args_list

    for _arguments in arguments:
        mocked_combine_data.assert_any_call(*_arguments)
        mocked_combine_alias.assert_any_call(*_arguments)


@pytest.mark.usefixtures("mocked_combine_alias")
def test_extract_context_with_initial_data(mocked_combine_data):
    """Return extracted context with initial data mapping."""
    environments = [
        wiz.definition.Environment({"data": {"KEY1": "VALUE1"}}),
        wiz.definition.Environment({
            "alias": {"app1": "App1"}, "data": {"KEY2": "VALUE2"}
        }),
        wiz.definition.Environment({
            "alias": {"app2": "App2"}, "data": {"KEY3": "VALUE3"}
        })
    ]

    assert wiz.package.extract_context(
        environments, data_mapping={"INITIAL_KEY": "INITIAL_VALUE"}
    ) == {"alias": {"_APP": "_APP_X"}, "data": {"_KEY": "_VALUE"}}

    mocked_combine_data.assert_any_call(
        {"data": {"INITIAL_KEY": "INITIAL_VALUE"}},
        wiz.definition.Environment({"data": {"KEY1": "VALUE1"}})
    )


@pytest.mark.usefixtures("mocked_combine_alias")
def test_extract_context_and_clean_data(mocked_combine_data):
    """Return extracted context after cleaning data."""
    mocked_combine_data.return_value = {
        "PLUGINS_A": "/path/to/plugin1:/path/to/plugin2:${PLUGINS_A}",
        "PLUGINS_B": "${PLUGINS_B}:/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_C": "/path/to/plugin1:${PLUGINS_C}:/path/to/plugin2",
        "KEY1": "HELLO",
        "KEY2": "${KEY1} WORLD!",
        "KEY3": "${UNKNOWN}"
    }

    assert wiz.package.extract_context([{}]) == {
        "alias": {"_APP": "_APP_X"},
        "data": {
            "PLUGINS_A": "/path/to/plugin1:/path/to/plugin2",
            "PLUGINS_B": "/path/to/plugin1:/path/to/plugin2",
            "PLUGINS_C": "/path/to/plugin1:/path/to/plugin2",
            "KEY1": "HELLO",
            "KEY2": "HELLO WORLD!",
            "KEY3": "${UNKNOWN}"
        }
    }


@pytest.mark.parametrize("environment1, environment2, expected, warning", [
    (
        wiz.definition.Environment({"data": {"KEY": "HELLO"}}),
        wiz.definition.Environment({"data": {"KEY": "${KEY} WORLD!"}}),
        {"KEY": "HELLO WORLD!"},
        None
    ),
    (
        wiz.definition.Environment({"data": {"KEY": "VALUE1"}}),
        wiz.definition.Environment({
            "identifier": "ENV",
            "version": "0.1.0",
            "data": {"KEY": "VALUE2"}
        }),
        {"KEY": "VALUE2"},
        (
            "The 'KEY' variable is being overridden in "
            "environment 'ENV' [0.1.0]"
        )
    ),
    (
        wiz.definition.Environment({"data": {"KEY": "VALUE1"}}),
        wiz.definition._EnvironmentVariant({
            "identifier": "Variant",
            "data": {"KEY": "VALUE2"}
        }, "ENV"),
        {"KEY": "VALUE2"},
        (
            "The 'KEY' variable is being overridden in "
            "environment 'ENV' [Variant]"
        )
    ),
    (
        wiz.definition.Environment({
            "data": {"PLUGIN": "/path/to/settings", "HOME": "/usr/people/me"}
        }),
        wiz.definition.Environment({
            "data": {"PLUGIN": "${HOME}/.app:${PLUGIN}"}
        }),
        {
            "HOME": "/usr/people/me",
            "PLUGIN": "/usr/people/me/.app:/path/to/settings"
        },
        None
    )
], ids=[
    "combine-key",
    "override-key",
    "override-variant-key",
    "mixed-combination"
])
def test_combine_data(logger, environment1, environment2, expected, warning):
    """Return combined data from *environment1* and *environment2*."""
    assert wiz.package.combine_data(environment1, environment2) == expected
    if warning is None:
        logger.warning.assert_not_called()
    else:
        logger.warning.assert_called_once_with(warning)


@pytest.mark.parametrize("environment1, environment2, expected, warning", [
    (
        wiz.definition.Environment({"alias": {"app1": "App1"}}),
        wiz.definition.Environment({"alias": {"app2": "App2"}}),
        {"app1": "App1", "app2": "App2"},
        None
    ),
    (
        wiz.definition.Environment({"alias": {"app1": "App1.0"}}),
        wiz.definition.Environment({
            "identifier": "ENV",
            "version": "0.1.0",
            "alias": {"app1": "App1.5"}
        }),
        {"app1": "App1.5"},
        (
            "The 'app1' alias is being overridden in "
            "environment 'ENV' [0.1.0]"
        )
    ),
    (
        wiz.definition.Environment({"alias": {"app1": "App1.0"}}),
        wiz.definition._EnvironmentVariant({
            "identifier": "Variant",
            "alias": {"app1": "App1.5"}
        }, "ENV"),
        {"app1": "App1.5"},
        (
            "The 'app1' alias is being overridden in "
            "environment 'ENV' [Variant]"
        )
    ),
], ids=[
    "combine-key",
    "override-key",
    "override-variant-key",
])
def test_combine_alias(logger, environment1, environment2, expected, warning):
    """Return combined alias from *environment1* and *environment2*."""
    assert wiz.package.combine_alias(environment1, environment2) == expected
    if warning is None:
        logger.warning.assert_not_called()
    else:
        logger.warning.assert_called_once_with(warning)


def test_minimal_package_without_variant():
    """Create minimal package instance created with no variant."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
    })

    package = wiz.package.Package(environment)
    assert package.identifier == "env1==unknown"
    assert package.description == "unknown"
    assert package.alias == {}
    assert package.data == {}
    assert package.requirement == []

    assert len(package) == 6
    assert sorted(package) == [
        "alias", "data", "description", "environment", "identifier",
        "requirement"
    ]


def test_full_package_without_variant():
    """Create full package instance created with no variant."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "description": "Test environment",
        "alias": {
            "app1": "App1",
            "app2": "App2",
        },
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        },
        "requirement": [
            "env1 >= 2",
            "env2"
        ]
    })

    package = wiz.package.Package(environment)
    assert package.identifier == "env1==0.3.4"
    assert package.description == "Test environment"
    assert package.alias == {"app1": "App1", "app2": "App2"}
    assert package.data == {"KEY1": "VALUE1", "KEY2": "VALUE2"}

    for requirement_data, requirement in itertools.izip_longest(
        ["env1 >= 2", "env2"], package.requirement
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(requirement_data))


def test_package_with_variant():
    """Create full package instance created with no variant."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "description": "Test environment",
        "alias": {
            "app1": "App1",
            "app2": "App2",
        },
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        },
        "requirement": [
            "env1 >= 2",
            "env2"
        ]
    })

    variant = wiz.definition._EnvironmentVariant({
        "identifier": "Variant",
        "alias": {
            "app1": "App1XX",
        },
        "data": {
            "KEY2": "VALUE20",
        },
        "requirement": [
            "env3"
        ]
    }, "env1")

    package = wiz.package.Package(environment, variant)
    assert package.identifier == "env1[Variant]==0.3.4"
    assert package.description == "Test environment"
    assert package.alias == {"app1": "App1XX", "app2": "App2"}
    assert package.data == {"KEY1": "VALUE1", "KEY2": "VALUE20"}

    for requirement_data, requirement in itertools.izip_longest(
        ["env1 >= 2", "env2", "env3"], package.requirement
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(requirement_data))
