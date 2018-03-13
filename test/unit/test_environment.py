# :coding: utf-8

import os
import pytest

from packaging.requirements import Requirement

from wiz import __version__
import wiz.definition
import wiz.environment
import wiz.graph
import wiz.exception


@pytest.fixture()
def environment_mapping():
    """Return mocked environment mapping."""
    return {
        "env1": {
            "0.3.4": wiz.definition.Environment({
                "identifier": "env1",
                "version": "0.3.4",
                "description": "A test environment named 'env1'."
            }),
            "0.3.0": wiz.definition.Environment({
                "identifier": "env1",
                "version": "0.3.0",
                "description": "A test environment named 'env1'."
            }),
            "0.2.0": wiz.definition.Environment({
                "identifier": "env1",
                "version": "0.2.0",
                "description": "A test environment named 'env1'."
            }),
            "0.1.0": wiz.definition.Environment({
                "identifier": "env1",
                "version": "0.1.0",
                "description": "A test environment named 'env1'."
            }),
        },
        "env2": {
            "0.3.0": wiz.definition.Environment({
                "identifier": "env2",
                "version": "0.3.0",
                "description": "A test environment named 'env2'."
            }),
            "0.1.5": wiz.definition.Environment({
                "identifier": "env2",
                "version": "0.1.5",
                "description": "A test environment named 'env2'."
            }),
            "0.1.0": wiz.definition.Environment({
                "identifier": "env2",
                "version": "0.1.0",
                "description": "A test environment named 'env2'."
            }),
        },
    }


def test_get_environment(environment_mapping):
    """Return best matching environment environment from requirement."""
    requirement = Requirement("env1")
    assert (
        wiz.environment.get(requirement, environment_mapping) ==
        environment_mapping["env1"]["0.3.4"]
    )

    requirement = Requirement("env2")
    assert (
        wiz.environment.get(requirement, environment_mapping) ==
        environment_mapping["env2"]["0.3.0"]
    )

    requirement = Requirement("env1<0.2")
    assert (
        wiz.environment.get(requirement, environment_mapping) ==
        environment_mapping["env1"]["0.1.0"]
    )

    requirement = Requirement("env2==0.1.5")
    assert (
        wiz.environment.get(requirement, environment_mapping) ==
        environment_mapping["env2"]["0.1.5"]
    )


def test_get_environment_name_error(environment_mapping):
    """Fails to get the environment name."""
    requirement = Requirement("incorrect")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.environment.get(requirement, environment_mapping)


def test_get_environment_version_error(environment_mapping):
    """Fails to get the environment version."""
    requirement = Requirement("env1>10")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.environment.get(requirement, environment_mapping)


def test_resolve(mocker, environment_mapping):
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

    result = wiz.environment.resolve(requirements, environment_mapping)
    assert result == "ENVIRONMENTS"

    resolver.assert_called_once_with(environment_mapping)
    mocked_process.compute_environments.assert_called_once_with(requirements)


@pytest.fixture()
def mocked_combine_data(mocker):
    """Return mocked combine_data function."""
    return mocker.patch.object(
        wiz.environment, "combine_data", return_value={"_KEY": "_VALUE"}
    )


@pytest.fixture()
def mocked_combine_alias(mocker):
    """Return mocked combine_alias function."""
    return mocker.patch.object(
        wiz.environment, "combine_alias", return_value={"_APP": "_APP_X"}
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
    assert wiz.environment.extract_context(environments) == expected
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

    assert wiz.environment.extract_context(
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

    assert wiz.environment.extract_context([{}]) == {
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
    assert wiz.environment.combine_data(environment1, environment2) == expected
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
    assert wiz.environment.combine_alias(environment1, environment2) == expected
    if warning is None:
        logger.warning.assert_not_called()
    else:
        logger.warning.assert_called_once_with(warning)


def test_initiate_data(monkeypatch):
    """Return initial data mapping."""
    monkeypatch.setenv("USER", "someone")
    monkeypatch.setenv("LOGNAME", "someone")
    monkeypatch.setenv("HOME", "/path/to/somewhere")
    monkeypatch.setenv("DISPLAY", "localhost:0.0")

    assert wiz.environment.initiate_data() == {
        "WIZ_VERSION": __version__,
        "USER": "someone",
        "LOGNAME": "someone",
        "HOME": "/path/to/somewhere",
        "DISPLAY": "localhost:0.0",
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }


def test_initiate_data_with_initial_data(monkeypatch):
    """Return initial data mapping with initial data mapping."""
    monkeypatch.setenv("USER", "someone")
    monkeypatch.setenv("LOGNAME", "someone")
    monkeypatch.setenv("HOME", "/path/to/somewhere")
    monkeypatch.setenv("DISPLAY", "localhost:0.0")

    assert wiz.environment.initiate_data(
        data_mapping={
            "LOGNAME": "someone-else",
            "KEY": "VALUE"
        }
    ) == {
        "WIZ_VERSION": __version__,
        "USER": "someone",
        "LOGNAME": "someone-else",
        "HOME": "/path/to/somewhere",
        "DISPLAY": "localhost:0.0",
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ]),
        "KEY": "VALUE"
    }
