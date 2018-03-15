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
        wiz.definition.Definition({
            "identifier": "foo-package",
            "version": "0.1.0",
            "description": "A test package for foo."
        }),
        wiz.definition.Definition({
            "identifier": "foo-package",
            "version": "1.1.0",
            "description": "Another test package for foo.",
            "command": {
                "foo": "Foo1.1",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bar-package",
            "version": "1.0.0",
            "description": "A test package for bar.",
            "command": {
                "bar": "Bar1.0",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bar-package",
            "version": "0.9.2",
            "description": "Another test package for bar.",
            "command": {
                "bar": "Bar0.9",
            }
        }),
        wiz.definition.Definition({
            "identifier": "baz-package",
            "version": "0.1.1",
            "description": "A test package for baz.",
            "command": {
                "baz": "Baz0.1",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bim-package",
            "version": "0.2.1",
            "description": "A test package for bim.",
            "command": {
                "bim": "Bim0.2",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bim-package",
            "version": "0.2.1",
            "description": "Another test package for bim.",
            "command": {
                "bim-test": "Bim0.2 --test",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bim-package",
            "version": "0.1.0",
            "description": "Yet another test package for bim.",
            "command": {
                "bim": "Bim0.1",
            }
        })
    ]


@pytest.fixture()
def package_definition_mapping():
    """Return mocked package mapping."""
    return {
        "foo": {
            "0.3.4": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.3.4",
            }),
            "0.3.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.3.0",
            }),
            "0.2.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.2.0",
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
            }),
        },
        "bar": {
            "0.3.0": wiz.definition.Definition({
                "identifier": "bar",
                "version": "0.3.0",
            }),
            "0.1.5": wiz.definition.Definition({
                "identifier": "bar",
                "version": "0.1.5",
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "bar",
                "version": "0.1.0",
            }),
        },
    }


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
def mocked_validate(mocker):
    """Return mocked validate function."""
    return mocker.patch.object(wiz.definition, "validate")


@pytest.fixture()
def mocked_discover(mocker):
    """Return mocked discovery function."""
    return mocker.patch.object(wiz.definition, "discover")


@pytest.fixture()
def mocked_load(mocker):
    """Return mocked load function."""
    return mocker.patch.object(wiz.definition, "load")


@pytest.fixture()
def mocked_definition(mocker):
    """Return mocked Definition class."""
    return mocker.patch.object(
        wiz.definition, "Definition", return_value="DEFINITION"
    )


@pytest.mark.parametrize("options", [
    {},
    {"requests": ["something", "test>1"]},
    {"max_depth": 4}
], ids=[
    "without-option",
    "with-requests",
    "with-max-depth"
])
def test_fetch(mocked_discover, mocked_validate, definitions, options):
    """Fetch all definition within *paths*."""
    mocked_discover.return_value = definitions
    result = wiz.definition.fetch(
        ["/path/to/registry-1", "/path/to/registry-2"], **options
    )

    mocked_discover.assert_called_once_with(
        ["/path/to/registry-1", "/path/to/registry-2"],
        max_depth=options.get("max_depth")
    )

    if options.get("requests") is not None:
        assert mocked_validate.call_count == len(definitions)
        for definition in definitions:
            mocked_validate.assert_any_call(definition, options["requests"])
    else:
        mocked_validate.assert_not_called()

    assert result == {
        "package": {
            "foo-package": {
                "0.1.0": definitions[0],
                "1.1.0": definitions[1]
            },
            "bar-package": {
                "1.0.0": definitions[2],
                "0.9.2": definitions[3]
            },
            "baz-package": {
                "0.1.1": definitions[4]
            },
            "bim-package": {
                # The 5th definition in the incoming list is overridden by the
                # 6th one which has the same identifier and version.
                "0.2.1": definitions[6],
                "0.1.0": definitions[7]
            }
        },
        "command": {
            "foo": "foo-package",
            "bar": "bar-package",
            "baz": "baz-package",
            "bim-test": "bim-package",
            "bim": "bim-package"
        }
    }


def test_validation_fail(mocked_discover, mocked_validate, definitions):
    """Fail to fetch definition when requests leads to validation failure."""
    mocked_discover.return_value = definitions
    mocked_validate.return_value = False

    result = wiz.definition.fetch(
        ["/path/to/registry-1", "/path/to/registry-2"], requests=["KABOOM"]
    )

    mocked_discover.assert_called_once_with(
        ["/path/to/registry-1", "/path/to/registry-2"], max_depth=None
    )

    assert mocked_validate.call_count == len(definitions)
    for definition in definitions:
        mocked_validate.assert_any_call(definition, ["KABOOM"])

    assert result == {
        "package": {},
        "command": {}
    }


def test_validate(definitions):
    """Search a specific definition."""
    assert wiz.definition.validate(definitions[0], [""]) is False
    assert wiz.definition.validate(definitions[0], ["foo"]) is True
    assert wiz.definition.validate(definitions[0], ["foo", "best"]) is False
    assert wiz.definition.validate(definitions[0], ["test"]) is True
    assert wiz.definition.validate(definitions[0], ["foo>2"]) is False
    assert wiz.definition.validate(definitions[0], ["foo>=0.1.0"]) is True


def test_get_definition(package_definition_mapping):
    """Return best matching definition from requirement."""
    requirement = Requirement("foo")
    assert (
        wiz.definition.get(requirement, package_definition_mapping) ==
        package_definition_mapping["foo"]["0.3.4"]
    )

    requirement = Requirement("bar")
    assert (
        wiz.definition.get(requirement, package_definition_mapping) ==
        package_definition_mapping["bar"]["0.3.0"]
    )

    requirement = Requirement("foo<0.2")
    assert (
        wiz.definition.get(requirement, package_definition_mapping) ==
        package_definition_mapping["foo"]["0.1.0"]
    )

    requirement = Requirement("bar==0.1.5")
    assert (
        wiz.definition.get(requirement, package_definition_mapping) ==
        package_definition_mapping["bar"]["0.1.5"]
    )


def test_get_definition_name_error(package_definition_mapping):
    """Fails to get the definition name."""
    requirement = Requirement("incorrect")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.definition.get(requirement, package_definition_mapping)


def test_get_definition_version_error(package_definition_mapping):
    """Fails to get the definition version."""
    requirement = Requirement("foo>10")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.definition.get(requirement, package_definition_mapping)


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
    definitions[2] = wiz.definition.Definition(
        disabled=True, **definitions[2].to_mapping()
    )
    definitions[4] = wiz.definition.Definition(
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
    wiz.exception.IncorrectDefinition
], ids=[
    "io-error",
    "value-error",
    "type-error",
    "generic-wiz-error",
    "incorrect-definition",
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


def test_load(mocked_definition, temporary_file):
    """Load a definition from a path."""
    with open(temporary_file, "w") as stream:
        stream.write("{\"identifier\": \"test_definition\"}")

    mocked_definition.return_value = "DEFINITION"
    result = wiz.definition.load(temporary_file)
    assert result == "DEFINITION"
    mocked_definition.assert_called_once_with(identifier="test_definition")


def test_load_with_mapping(mocked_definition, temporary_file):
    """Load a definition from a path and a mapping."""
    with open(temporary_file, "w") as stream:
        stream.write("{\"identifier\": \"test_definition\"}")

    mocked_definition.return_value = "DEFINITION"
    result = wiz.definition.load(temporary_file, mapping={"key": "value"})
    assert result == "DEFINITION"
    mocked_definition.assert_called_once_with(
        identifier="test_definition", key="value"
    )


def test_definition_mapping():
    """Create definition and return mapping and serialized mapping."""
    data = {
        "identifier": "test",
        "description": "This is a definition",
        "environ": {
            "KEY1": "VALUE1"
        }
    }

    environment = wiz.definition.Definition(data)

    assert environment.to_mapping() == {
        "identifier": "test",
        "description": "This is a definition",
        "environ": {
            "KEY1": "VALUE1",
        }
    }

    assert environment.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"description\": \"This is a definition\",\n"
        "    \"environ\": {\n"
        "        \"KEY1\": \"VALUE1\"\n"
        "    }\n"
        "}"
    )

    assert len(environment) == len(data)
    assert sorted(environment) == sorted(data)


def test_minimal_definition():
    """Create a minimal definition."""
    data = {"identifier": "test"}

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == "unknown"
    assert definition.description == "unknown"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_mapping() == OrderedDict([
        ("identifier", "test"),
    ])


def test_definition_with_version():
    """Create a definition with version."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.description == "unknown"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_mapping() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
    ])


def test_definition_with_description():
    """Create a definition with description."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition"
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_mapping() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
        ("description", "This is a definition")
    ])


def test_definition_with_environ():
    """Create a definition with environment mapping."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
            "KEY3": "PATH1:PATH2:PATH3"
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.description == "This is a definition"
    assert definition.requirements == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.environ == {
        "KEY1": "VALUE1",
        "KEY2": "VALUE2",
        "KEY3": "PATH1:PATH2:PATH3"
    }

    assert definition.to_ordered_mapping() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
        ("description", "This is a definition"),
        ("environ", {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
            "KEY3": "PATH1:PATH2:PATH3"
        })
    ])


def test_definition_with_requirements():
    """Create a definition with requirements."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
        "requirements": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    for expected_requirement, requirement in itertools.izip_longest(
        data["requirements"], definition.requirements
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(expected_requirement))

    assert definition.to_ordered_mapping() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
        ("description", "This is a definition"),
        ("requirements", [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ])
    ])


def test_definition_with_command():
    """Create a definition with command."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
        "command": {
            "app": "App0.1",
            "appX": "App0.1 --option value"
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.system == {}
    assert definition.variants == []

    assert definition.command == {
        "app": "App0.1",
        "appX": "App0.1 --option value"
    }

    assert definition.to_ordered_mapping() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
        ("description", "This is a definition"),
        ("command", {
            "app": "App0.1",
            "appX": "App0.1 --option value"
        })
    ])


def test_definition_with_system():
    """Create a definition with system constraint."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
        "system": {
            "arch": "x86_64",
            "platform": "linux"
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.requirements == []
    assert definition.variants == []

    assert definition.system == {
        "arch": "x86_64",
        "platform": "linux"
    }

    assert definition.to_ordered_mapping() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
        ("description", "This is a definition"),
        ("system", {
            "arch": "x86_64",
            "platform": "linux"
        })
    ])


def test_definition_with_variant():
    """Create a definition with variant."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "description": "This is a definition",
        "variants": [
            {
                "identifier": "1.0",
                "environ": {
                    "VERSION": "1.0"
                },
                "requirements": [
                    "envA >= 1.0, < 2"
                ]
            },
            {
                "identifier": "2.0",
                "environ": {
                    "VERSION": "2.0"
                },
                "command": {
                    "app": "App2.0",
                },
                "requirements": [
                    "envA >= 2.0, < 3"
                ]
            },
            {
                "identifier": "XXX",
                "command": {
                    "app": "AppXXX",
                },
            }
        ]
    }

    definition = wiz.definition.Definition(copy.deepcopy(data))
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.command == {}
    assert definition.system == {}

    for variant_data, variant in itertools.izip_longest(
        data["variants"], definition.variants
    ):
        assert variant_data["identifier"] == variant.identifier
        assert variant_data.get("environ", {}) == variant.environ
        assert variant_data.get("command", {}) == variant.command

        for requirement_data, requirement in itertools.izip_longest(
            variant_data.get("requirements", []), variant.requirements
        ):
            assert isinstance(requirement, Requirement)
            assert str(requirement) == str(Requirement(requirement_data))

    assert definition.to_ordered_mapping() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
        ("description", "This is a definition"),
        ("variants", [
            OrderedDict([
                ("identifier", "1.0"),
                ("environ", {"VERSION": "1.0"}),
                ("requirements", ["envA >= 1.0, < 2"])
            ]),
            OrderedDict([
                ("identifier", "2.0"),
                ("command", {"app": "App2.0"}),
                ("environ", {"VERSION": "2.0"}),
                ("requirements", ["envA >= 2.0, < 3"])
            ]),
            OrderedDict([
                ("identifier", "XXX"),
                ("command", {"app": "AppXXX"}),
            ])
        ])
    ])


def test_definition_with_version_error():
    """Fail to create a definition with incorrect version."""
    data = {
        "identifier": "test",
        "version": "!!!"
    }

    with pytest.raises(wiz.exception.IncorrectDefinition) as error:
        wiz.definition.Definition(data)

    assert (
        "IncorrectDefinition: The definition 'test' has an incorrect "
        "version [!!!]"
    ) in str(error)


def test_definition_with_requirement_error():
    """Fail to create a definition with incorrect requirement."""
    data = {
        "identifier": "test",
        "requirements": [
            "envA -!!!",
        ]
    }

    with pytest.raises(wiz.exception.IncorrectDefinition) as error:
        wiz.definition.Definition(data)

    assert (
        "IncorrectDefinition: The definition 'test' contains an incorrect "
        "requirement [Invalid requirement, parse error at \"'-!!!'\"]"
    ) in str(error)


def test_definition_with_variant_requirement_error():
    """Fail to create a definition with incorrect variant requirement."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "1.0",
                "requirements": [
                    "envA -!!!"
                ]
            }
        ]
    }

    with pytest.raises(wiz.exception.IncorrectDefinition) as error:
        wiz.definition.Definition(data)

    assert (
        "IncorrectDefinition: The definition 'test' [1.0] contains an "
        "incorrect requirement [Invalid requirement, parse error at \"'-!!!'\"]"
    ) in str(error)
