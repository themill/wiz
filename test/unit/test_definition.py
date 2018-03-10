# :coding: utf-8

import os
import types
import copy
from collections import OrderedDict
import itertools

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

import wiz.definition
import wiz.exception


@pytest.fixture()
def definitions():
    """Return list of mocked definitions."""
    return [
        wiz.definition.Environment({
            "identifier": "env-test1",
            "version": "0.1.0",
            "description": "A test env for foo."
        }),
        wiz.definition.Environment({
            "identifier": "env-test1",
            "version": "1.1.0",
            "description": "Another test env for foo."
        }),
        wiz.definition.Environment({
            "identifier": "env-test2",
            "version": "1.0.0",
            "description": "A test env for bar.",
        }),
        wiz.definition.Environment({
            "identifier": "env-test3",
            "version": "0.1.1",
            "description": "A test env for baz."
        }),
        wiz.definition.Environment({
            "identifier": "env-test4",
            "version": "0.1.1",
            "description": "A 4th test env."
        }),
        wiz.definition.Environment({
            "identifier": "env-test4",
            "version": "0.1.1",
            "description": "A 4th test env."
        }),
        wiz.definition.Environment({
            "identifier": "env-test4",
            "version": "0.1.0",
            "description": "A 4th test env."
        }),
        wiz.definition.Application({
            "identifier": "app2",
            "command": "app_exe",
            "description": "A cool application.",
            "requirement": [
                "env-test1 >=0.1.0, <1",
                "env-test2 >=1"
            ]
        }),
        wiz.definition.Application({
            "identifier": "app1",
            "command": "app_exe",
            "description": "A cooler application.",
            "requirement": [
                "env-test3"
            ]
        }),
        wiz.definition.Application({
            "identifier": "app3",
            "command": "app_exe",
            "description": "The best application.",
            "requirement": [
                "env-test2"
            ]
        })
    ]


@pytest.fixture()
def registries(temporary_directory):
    """Return mocked registry paths."""
    mapping = {
        "registry1": {
            "__files__": ["defA.json"],
            "level1": {
                "__files__": ["defB.jee-son"],
                "level2": {
                    "__files__": ["defC.json", "defD"],
                    "level3": {
                        "__files__": ["defE.json", "defF.json"],
                    }
                }
            }
        },
        "registry2": {
            "__files__": ["defG.yml", "defH.json", "defI.json"],
        }
    }

    def _create_structure(root, _mapping):
        """Create the mocked registry structure *_mapping* in *root*."""
        for key, value in _mapping.items():
            if key == "__files__":
                for _file in value:
                    path = os.path.join(root, _file)
                    with open(path, "w") as stream:
                        stream.write("")

            else:
                path = os.path.join(root, key)
                os.makedirs(path)
                _create_structure(path, value)

    _create_structure(temporary_directory, mapping)

    return [
        os.path.join(temporary_directory, "registry1"),
        os.path.join(temporary_directory, "registry2"),
        " "
    ]


@pytest.fixture()
def mocked_discover(mocker):
    """Return mocked discovery function."""
    return mocker.patch.object(wiz.definition, "discover")


@pytest.fixture()
def mocked_load(mocker):
    """Return mocked load function."""
    return mocker.patch.object(wiz.definition, "load")


@pytest.fixture()
def mocked_create(mocker):
    """Return mocked create function."""
    return mocker.patch.object(wiz.definition, "create")


@pytest.fixture()
def mocked_environment(mocker):
    """Return mocked Environment class."""
    return mocker.patch.object(
        wiz.definition, "Environment", return_value="Environment"
    )


@pytest.fixture()
def mocked_application(mocker):
    """Return mocked Application class."""
    return mocker.patch.object(
        wiz.definition, "Application", return_value="Application"
    )


@pytest.mark.parametrize("options", [
    {}, {"max_depth": 4}
], ids=[
    "without-max-depth",
    "with-max-depth"
])
def test_fetch(mocked_discover, definitions, options):
    """Fetch all definition within *paths*."""
    mocked_discover.return_value = definitions
    result = wiz.definition.fetch(
        ["/path/to/registry-1", "/path/to/registry-2"], **options
    )

    mocked_discover.assert_called_once_with(
        ["/path/to/registry-1", "/path/to/registry-2"],
        max_depth=options.get("max_depth")
    )

    assert result == {
        "environment": {
            "env-test1": {
                "0.1.0": definitions[0],
                "1.1.0": definitions[1]
            },
            "env-test2": {
                "1.0.0": definitions[2]
            },
            "env-test3": {
                "0.1.1": definitions[3]
            },
            "env-test4": {
                # The 4th definition in the incoming list is overridden by the
                # 5th one which has the same identifier and version.
                "0.1.1": definitions[5],
                "0.1.0": definitions[6]
            }
        },
        "application": {
            "app1": definitions[8],
            "app2": definitions[7],
            "app3": definitions[9]
        }
    }


@pytest.mark.parametrize("options", [
    {}, {"max_depth": 4}
], ids=[
    "without-max-depth",
    "with-max-depth"
])
def test_search(mocked_discover, definitions, options):
    """Search a specific definition."""
    mocked_discover.return_value = definitions

    # Search application via identifier and description
    result = wiz.definition.search(
        ["app", "best"],
        ["/path/to/registry-1", "/path/to/registry-2"],
        **options
    )

    assert result == {
        "environment": {},
        "application": {
            "app3": definitions[9]
        }
    }

    # Search environment via identifier and version
    result = wiz.definition.search(
        ["test1<1"],
        ["/path/to/registry-1", "/path/to/registry-2"],
        **options
    )

    assert result == {
        "environment": {
            "env-test1": {
                "0.1.0": definitions[0]
            }
        },
        "application": {}
    }

    # Incorrect request
    result = wiz.definition.search(
        ["!!!"],
        ["/path/to/registry-1", "/path/to/registry-2"],
        **options
    )

    assert result == {
        "environment": {},
        "application": {}
    }


def test_discover(mocked_load, registries, definitions):
    """Discover and yield *definitions*."""
    mocked_load.side_effect = definitions

    result = wiz.definition.discover(registries)
    assert isinstance(result, types.GeneratorType)
    assert mocked_load.call_count == 0

    discovered = list(result)
    assert len(discovered) == 6
    assert mocked_load.call_count == 6

    mocked_load.assert_any_call(
        os.path.join(registries[0], "defA.json"),
        mapping={"registry": registries[0]}
    )
    mocked_load.assert_any_call(
        os.path.join(registries[0], "level1", "level2", "defC.json"),
        mapping={"registry": registries[0]}
    )
    mocked_load.assert_any_call(
        os.path.join(registries[0], "level1", "level2", "level3", "defF.json"),
        mapping={"registry": registries[0]}
    )
    mocked_load.assert_any_call(
        os.path.join(registries[0], "level1", "level2", "level3", "defE.json"),
        mapping={"registry": registries[0]}
    )
    mocked_load.assert_any_call(
        os.path.join(registries[1], "defH.json"),
        mapping={"registry": registries[1]}
    )
    mocked_load.assert_any_call(
        os.path.join(registries[1], "defI.json"),
        mapping={"registry": registries[1]}
    )

    assert discovered == definitions[:6]


def test_discover_with_max_depth(mocked_load, registries, definitions):
    """Discover and yield definitions with maximum depth."""
    mocked_load.side_effect = definitions

    result = wiz.definition.discover(registries, max_depth=2)
    assert isinstance(result, types.GeneratorType)
    assert mocked_load.call_count == 0

    discovered = list(result)
    assert len(discovered) == 4
    assert mocked_load.call_count == 4

    mocked_load.assert_any_call(
        os.path.join(registries[0], "defA.json"),
        mapping={"registry": registries[0]}
    )
    mocked_load.assert_any_call(
        os.path.join(registries[0], "level1", "level2", "defC.json"),
        mapping={"registry": registries[0]}
    )
    mocked_load.assert_any_call(
        os.path.join(registries[1], "defH.json"),
        mapping={"registry": registries[1]}
    )
    mocked_load.assert_any_call(
        os.path.join(registries[1], "defI.json"),
        mapping={"registry": registries[1]}
    )

    assert discovered == definitions[:4]


def test_discover_without_disabled(mocked_load, registries, definitions):
    """Discover and yield definitions without disabled definition."""
    definitions[2] = wiz.definition.Environment(
        disabled=True, **definitions[2].to_mapping()
    )
    definitions[4] = wiz.definition.Environment(
        disabled=True, **definitions[4].to_mapping()
    )
    mocked_load.side_effect = definitions

    result = wiz.definition.discover(registries)
    assert isinstance(result, types.GeneratorType)
    assert mocked_load.call_count == 0

    discovered = list(result)
    assert len(discovered) == 4
    assert mocked_load.call_count == 6

    assert discovered == [
        definitions[0],
        definitions[1],
        definitions[3],
        definitions[5]
    ]


@pytest.mark.parametrize("exception", [
    IOError,
    ValueError,
    TypeError,
    wiz.exception.WizError,
    wiz.exception.IncorrectApplication,
    wiz.exception.IncorrectEnvironment
], ids=[
    "io-error",
    "value-error",
    "type-error",
    "generic-wiz-error",
    "incorrect-application",
    "incorrect-environment",
])
def test_discover_skip_error(mocked_load, registries, exception):
    """Discover and yield definitions without definition with error."""
    mocked_load.side_effect = exception

    result = wiz.definition.discover(registries)
    assert isinstance(result, types.GeneratorType)
    assert mocked_load.call_count == 0

    discovered = list(result)
    assert len(discovered) == 0
    assert mocked_load.call_count == 6


@pytest.mark.parametrize("exception", [
    RuntimeError,
    Exception
], ids=[
    "runtime-error",
    "generic-error"
])
def test_discover_error(mocked_load, registries, exception):
    """Fail to discover and yield definitions."""
    mocked_load.side_effect = exception

    with pytest.raises(exception):
        list(wiz.definition.discover(registries))


def test_load(mocked_create, temporary_file):
    """Load a definition from a path."""
    with open(temporary_file, "w") as stream:
        stream.write("{\"identifier\": \"test_definition\"}")

    mocked_create.return_value = "DEFINITION"
    result = wiz.definition.load(temporary_file)
    assert result == "DEFINITION"
    mocked_create.assert_called_once_with({"identifier": "test_definition"})


def test_load_with_mapping(mocked_create, temporary_file):
    """Load a definition from a path and a mapping."""
    with open(temporary_file, "w") as stream:
        stream.write("{\"identifier\": \"test_definition\"}")

    mocked_create.return_value = "DEFINITION"
    result = wiz.definition.load(temporary_file, mapping={"key": "value"})
    assert result == "DEFINITION"
    mocked_create.assert_called_once_with(
        {"identifier": "test_definition", "key": "value"}
    )


def test_create_environment(mocked_environment, mocked_application):
    """Create an environment definition from *data*."""
    data = {
        "identifier": "test-env",
        "version": "0.1.0",
        "type": "environment"
    }

    definition = wiz.definition.create(data)
    mocked_environment.assert_called_once_with(**data)
    mocked_application.assert_not_called()
    assert definition == "Environment"


def test_create_application(mocked_environment, mocked_application):
    """Create an application definition from *data*."""
    data = {
        "identifier": "test-app",
        "type": "application"
    }

    definition = wiz.definition.create(data)
    mocked_application.assert_called_once_with(**data)
    mocked_environment.assert_not_called()
    assert definition == "Application"


def test_create_error(mocked_environment, mocked_application):
    """Fail to create a definition from *data*."""
    data = {
        "identifier": "test",
        "type": "incorrect"
    }

    with pytest.raises(wiz.exception.IncorrectDefinition):
        wiz.definition.create(data)

    mocked_application.assert_not_called()
    mocked_environment.assert_not_called()


def test_environment_definition():
    """Create basic environment definition."""
    data = {
        "identifier": "test-environment",
        "description": "This is an environment",
        "data": {
            "KEY1": "VALUE1"
        }
    }

    environment = wiz.definition.Environment(data)

    assert environment.to_mapping() == {
        "identifier": "test-environment",
        "type": "environment",
        "description": "This is an environment",
        "data": {
            "KEY1": "VALUE1",
        }
    }

    assert environment.encode() == (
        "{\n"
        "    \"identifier\": \"test-environment\",\n"
        "    \"type\": \"environment\",\n"
        "    \"description\": \"This is an environment\",\n"
        "    \"data\": {\n"
        "        \"KEY1\": \"VALUE1\"\n"
        "    }\n"
        "}"
    )

    data["type"] = "environment"
    assert len(environment) == len(data)
    assert sorted(environment) == sorted(data)


def test_application_definition():
    """Create basic application definition."""
    data = {
        "identifier": "test-application",
        "description": "This is an application",
        "command": "app --test",
        "requirement": [
            "envA >= 1.0.0",
            "envB >= 3.4, < 4",
        ]
    }

    application = wiz.definition.Application(data)

    assert application.to_mapping() == {
        "identifier": "test-application",
        "type": "application",
        "description": "This is an application",
        "command": "app --test",
        "requirement": [
            "envA >= 1.0.0",
            "envB >= 3.4, < 4"
        ]
    }

    assert application.encode() == (
        "{\n"
        "    \"identifier\": \"test-application\",\n"
        "    \"type\": \"application\",\n"
        "    \"description\": \"This is an application\",\n"
        "    \"command\": \"app --test\",\n"
        "    \"requirement\": [\n"
        "        \"envA >= 1.0.0\",\n"
        "        \"envB >= 3.4, < 4\"\n"
        "    ]\n"
        "}"
    )

    data["type"] = "application"
    assert len(application) == len(data)
    assert sorted(application) == sorted(data)


def test_environment():
    """Create an environment definition."""
    data = {"identifier": "test-environment"}

    environment = wiz.definition.Environment(data)
    assert environment.identifier == "test-environment"
    assert environment.version == "unknown"
    assert environment.description == "unknown"
    assert environment.type == "environment"
    assert environment.data == {}
    assert environment.requirement == []
    assert environment.alias == {}
    assert environment.system == {}
    assert environment.variant == []

    assert environment.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-environment"),
        ("type", "environment")
    ])


def test_environment_with_version():
    """Create an environment definition with version."""
    data = {
        "identifier": "test-environment",
        "version": "0.1.0",
    }

    environment = wiz.definition.Environment(data)
    assert environment.identifier == "test-environment"
    assert environment.version == Version("0.1.0")
    assert environment.description == "unknown"
    assert environment.type == "environment"
    assert environment.data == {}
    assert environment.requirement == []
    assert environment.alias == {}
    assert environment.system == {}
    assert environment.variant == []

    assert environment.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-environment"),
        ("version", "0.1.0"),
        ("type", "environment"),
    ])


def test_environment_with_description():
    """Create an environment definition with description."""
    data = {
        "identifier": "test-environment",
        "version": "0.1.0",
        "description": "This is an environment"
    }

    environment = wiz.definition.Environment(data)
    assert environment.identifier == "test-environment"
    assert environment.version == Version("0.1.0")
    assert environment.description == "This is an environment"
    assert environment.type == "environment"
    assert environment.data == {}
    assert environment.requirement == []
    assert environment.alias == {}
    assert environment.system == {}
    assert environment.variant == []

    assert environment.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-environment"),
        ("version", "0.1.0"),
        ("type", "environment"),
        ("description", "This is an environment")
    ])


def test_environment_with_data():
    """Create an environment definition with data."""
    data = {
        "identifier": "test-environment",
        "version": "0.1.0",
        "description": "This is an environment",
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
            "KEY3": "PATH1:PATH2:PATH3"
        }
    }

    environment = wiz.definition.Environment(data)
    assert environment.identifier == "test-environment"
    assert environment.version == Version("0.1.0")
    assert environment.description == "This is an environment"
    assert environment.type == "environment"
    assert environment.requirement == []
    assert environment.alias == {}
    assert environment.system == {}
    assert environment.variant == []

    assert environment.data == {
        "KEY1": "VALUE1",
        "KEY2": "VALUE2",
        "KEY3": "PATH1:PATH2:PATH3"
    }

    assert environment.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-environment"),
        ("version", "0.1.0"),
        ("type", "environment"),
        ("description", "This is an environment"),
        ("data", {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
            "KEY3": "PATH1:PATH2:PATH3"
        })
    ])


def test_environment_with_requirements():
    """Create an environment definition with requirements."""
    data = {
        "identifier": "test-environment",
        "version": "0.1.0",
        "description": "This is an environment",
        "requirement": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }

    environment = wiz.definition.Environment(data)
    assert environment.identifier == "test-environment"
    assert environment.version == Version("0.1.0")
    assert environment.description == "This is an environment"
    assert environment.type == "environment"
    assert environment.data == {}
    assert environment.alias == {}
    assert environment.system == {}
    assert environment.variant == []

    for expected_requirement, requirement in itertools.izip_longest(
        data["requirement"], environment.requirement
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(expected_requirement))

    assert environment.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-environment"),
        ("version", "0.1.0"),
        ("type", "environment"),
        ("description", "This is an environment"),
        ("requirement", [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ])
    ])


def test_environment_with_aliases():
    """Create an environment definition with aliases."""
    data = {
        "identifier": "test-environment",
        "version": "0.1.0",
        "description": "This is an environment",
        "alias": {
            "app": "App0.1",
            "appX": "App0.1 --option value"
        }
    }

    environment = wiz.definition.Environment(data)
    assert environment.identifier == "test-environment"
    assert environment.version == Version("0.1.0")
    assert environment.description == "This is an environment"
    assert environment.type == "environment"
    assert environment.data == {}
    assert environment.requirement == []
    assert environment.system == {}
    assert environment.variant == []

    assert environment.alias == {
        "app": "App0.1",
        "appX": "App0.1 --option value"
    }

    assert environment.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-environment"),
        ("version", "0.1.0"),
        ("type", "environment"),
        ("description", "This is an environment"),
        ("alias", {
            "app": "App0.1",
            "appX": "App0.1 --option value"
        })
    ])


def test_environment_with_system():
    """Create an environment definition with system constraint."""
    data = {
        "identifier": "test-environment",
        "version": "0.1.0",
        "description": "This is an environment",
        "system": {
            "arch": "x86_64",
            "platform": "linux"
        }
    }

    environment = wiz.definition.Environment(data)
    assert environment.identifier == "test-environment"
    assert environment.version == Version("0.1.0")
    assert environment.description == "This is an environment"
    assert environment.type == "environment"
    assert environment.data == {}
    assert environment.alias == {}
    assert environment.requirement == []
    assert environment.variant == []

    assert environment.system == {
        "arch": "x86_64",
        "platform": "linux"
    }

    assert environment.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-environment"),
        ("version", "0.1.0"),
        ("type", "environment"),
        ("description", "This is an environment"),
        ("system", {
            "arch": "x86_64",
            "platform": "linux"
        })
    ])


def test_environment_with_variant():
    """Create an environment definition with variant."""
    data = {
        "identifier": "test-environment",
        "version": "0.1.0",
        "description": "This is an environment",
        "variant": [
            {
                "identifier": "1.0",
                "data": {
                    "VERSION": "1.0"
                },
                "requirement": [
                    "envA >= 1.0, < 2"
                ]
            },
            {
                "identifier": "2.0",
                "data": {
                    "VERSION": "2.0"
                },
                "alias": {
                    "app": "App2.0",
                },
                "requirement": [
                    "envA >= 2.0, < 3"
                ]
            },
            {
                "identifier": "XXX",
                "alias": {
                    "app": "AppXXX",
                },
            }
        ]
    }

    environment = wiz.definition.Environment(copy.deepcopy(data))
    assert environment.identifier == "test-environment"
    assert environment.version == Version("0.1.0")
    assert environment.description == "This is an environment"
    assert environment.type == "environment"
    assert environment.data == {}
    assert environment.requirement == []
    assert environment.alias == {}
    assert environment.system == {}

    for variant_data, variant in itertools.izip_longest(
        data["variant"], environment.variant
    ):
        assert variant_data["identifier"] == variant.identifier
        assert variant_data.get("data", {}) == variant.data
        assert variant_data.get("alias", {}) == variant.alias

        for requirement_data, requirement in itertools.izip_longest(
            variant_data.get("requirement", []), variant.requirement
        ):
            assert isinstance(requirement, Requirement)
            assert str(requirement) == str(Requirement(requirement_data))

    assert environment.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-environment"),
        ("version", "0.1.0"),
        ("type", "environment"),
        ("description", "This is an environment"),
        ("variant", [
            OrderedDict([
                ("identifier", "1.0"),
                ("data", {"VERSION": "1.0"}),
                ("requirement", ["envA >= 1.0, < 2"])
            ]),
            OrderedDict([
                ("identifier", "2.0"),
                ("alias", {"app": "App2.0"}),
                ("data", {"VERSION": "2.0"}),
                ("requirement", ["envA >= 2.0, < 3"])
            ]),
            OrderedDict([
                ("identifier", "XXX"),
                ("alias", {"app": "AppXXX"}),
            ])
        ])
    ])


def test_environment_with_version_error():
    """Fail to create an application definition with incorrect version."""
    data = {
        "identifier": "test-environment",
        "version": "!!!"
    }

    with pytest.raises(wiz.exception.IncorrectEnvironment) as error:
        wiz.definition.Environment(data)

    assert (
        "IncorrectEnvironment: The environment 'test-environment' is "
        "incorrect: Invalid version: '!!!'"
    ) in str(error)


def test_environment_with_requirement_error():
    """Fail to create an environment definition with incorrect requirement."""
    data = {
        "identifier": "test-environment",
        "requirement": [
            "envA -!!!",
        ]
    }

    with pytest.raises(wiz.exception.IncorrectEnvironment) as error:
        wiz.definition.Environment(data)

    assert (
        "IncorrectEnvironment: The environment 'test-environment' is "
        "incorrect: Invalid requirement, parse error at \"'-!!!'\""
    ) in str(error)


def test_application():
    """Create an application definition."""
    data = {
        "identifier": "test-application",
        "command": "app --test",
        "requirement": [
            "envA >= 1.0.0",
            "envB >= 3.4, < 4",
        ]
    }

    application = wiz.definition.Application(data)
    assert application.identifier == "test-application"
    assert application.description == "unknown"
    assert application.type == "application"
    assert application.command == "app --test"

    for expected_requirement, requirement in itertools.izip_longest(
        data["requirement"], application.requirement
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(expected_requirement))

    assert application.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-application"),
        ("type", "application"),
        ("command", "app --test"),
        ("requirement", [
            "envA >= 1.0.0",
            "envB >= 3.4, < 4"
        ])
    ])


def test_application_with_description():
    """Create an application definition with description."""
    data = {
        "identifier": "test-application",
        "description": "This is an application",
        "command": "app --test",
        "requirement": [
            "envA >= 1.0.0",
            "envB >= 3.4, < 4",
        ]
    }

    application = wiz.definition.Application(data)
    assert application.identifier == "test-application"
    assert application.description == "This is an application"
    assert application.type == "application"
    assert application.command == "app --test"

    for expected_requirement, requirement in itertools.izip_longest(
        data["requirement"], application.requirement
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(expected_requirement))

    assert application.to_ordered_mapping() == OrderedDict([
        ("identifier", "test-application"),
        ("type", "application"),
        ("description", "This is an application"),
        ("command", "app --test"),
        ("requirement", [
            "envA >= 1.0.0",
            "envB >= 3.4, < 4"
        ])
    ])


def test_application_with_requirement_error():
    """Fail to create an application definition with incorrect requirement."""
    data = {
        "identifier": "test-application",
        "command": "app --test",
        "requirement": [
            "envA -!!!",
        ]
    }

    with pytest.raises(wiz.exception.IncorrectApplication) as error:
        wiz.definition.Application(data)

    assert (
        "IncorrectApplication: The application 'test-application' is "
        "incorrect: Invalid requirement, parse error at \"'-!!!'\""
    ) in str(error)
