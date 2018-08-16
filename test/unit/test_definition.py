# :coding: utf-8

import os
import types
import copy
from collections import OrderedDict
import itertools

import pytest

from wiz.utility import Requirement, Version
import wiz.definition
import wiz.filesystem
import wiz.system
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
def definitions_with_auto_use():
    """Return list of mocked definitions with 'auto-use' keyword."""
    return [
        wiz.definition.Definition({
            "identifier": "foo-package",
            "version": "0.1.0",
            "description": "A test package for foo.",
            "auto-use": True
        }),
        wiz.definition.Definition({
            "identifier": "foo-package",
            "version": "1.1.0",
            "description": "Another test package for foo.",
            "auto-use": True,
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
            "auto-use": True,
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
def mocked_system_validate(mocker):
    """Return mocked system.validate function."""
    return mocker.patch.object(wiz.system, "validate")


@pytest.fixture()
def mocked_filesystem_export(mocker):
    """Return mocked filesystem.export function."""
    return mocker.patch.object(wiz.filesystem, "export")


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
        },
        "implicit-packages": []
    }


@pytest.mark.parametrize("options", [
    {},
    {"requests": ["something", "test>1"]},
    {"max_depth": 4}
], ids=[
    "without-option",
    "with-requests",
    "with-max-depth"
])
def test_fetch_with_implicit_packages(
    mocked_discover, mocked_validate, options
):
    """Fetch all definition within *paths*."""
    definitions = [
        wiz.definition.Definition({
            "identifier": "foo",
            "version": "0.1.0",
            "auto-use": True
        }),
        wiz.definition.Definition({
            "identifier": "foo",
            "version": "1.1.0",
            "auto-use": True
        }),
        wiz.definition.Definition({
            "identifier": "bar",
            "version": "1.0.0",
        }),
        wiz.definition.Definition({
            "identifier": "bar",
            "version": "0.9.2",
            "auto-use": True
        }),
        wiz.definition.Definition({
            "identifier": "baz",
        }),
        wiz.definition.Definition({
            "identifier": "bim",
            "auto-use": True
        }),
        wiz.definition.Definition({
            "identifier": "bam",
            "auto-use": True
        }),
    ]

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
            "foo": {
                "0.1.0": definitions[0],
                "1.1.0": definitions[1]
            },
            "bar": {
                "1.0.0": definitions[2],
                "0.9.2": definitions[3]
            },
            "baz": {
                "unknown": definitions[4]
            },
            "bim": {
                "unknown": definitions[5],
            },
            "bam": {
                "unknown": definitions[6],
            }
        },
        "command": {},
        "implicit-packages": [
            "bam",
            "bim",
            "bar==0.9.2",
            "foo==1.1.0"
        ]
    }


def test_fetch_system(mocked_discover, definitions, mocked_system_validate):
    """Fetch all definition within *paths* filtered by system mappings."""
    mocked_discover.return_value = definitions
    mocked_system_validate.return_value = False

    result = wiz.definition.fetch(
        ["/path/to/registry-1", "/path/to/registry-2"],
        system_mapping="SOME_MAPPING"
    )

    mocked_discover.assert_called_once_with(
        ["/path/to/registry-1", "/path/to/registry-2"], max_depth=None
    )

    assert result == {
        "package": {},
        "command": {},
        "implicit-packages": []
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
        "command": {},
        "implicit-packages": []
    }


def test_validate(definitions):
    """Search a specific definition."""
    assert wiz.definition.validate(definitions[0], ["foo"]) is True
    assert wiz.definition.validate(definitions[0], ["foo", "best"]) is False
    assert wiz.definition.validate(definitions[0], ["test"]) is True
    assert wiz.definition.validate(definitions[0], ["foo>2"]) is False
    assert wiz.definition.validate(definitions[0], ["foo>=0.1.0"]) is True


def test_query_definition(package_definition_mapping):
    """Return best matching definition from requirement."""
    requirement = Requirement("foo")
    assert (
        wiz.definition.query(requirement, package_definition_mapping) ==
        package_definition_mapping["foo"]["0.3.4"]
    )

    requirement = Requirement("bar")
    assert (
        wiz.definition.query(requirement, package_definition_mapping) ==
        package_definition_mapping["bar"]["0.3.0"]
    )

    requirement = Requirement("foo<0.2")
    assert (
        wiz.definition.query(requirement, package_definition_mapping) ==
        package_definition_mapping["foo"]["0.1.0"]
    )

    requirement = Requirement("bar==0.1.5")
    assert (
        wiz.definition.query(requirement, package_definition_mapping) ==
        package_definition_mapping["bar"]["0.1.5"]
    )


def test_query_definition_name_error(package_definition_mapping):
    """Fails to query the definition name."""
    requirement = Requirement("incorrect")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.definition.query(requirement, package_definition_mapping)


def test_query_definition_version_error(package_definition_mapping):
    """Fails to query the definition version."""
    requirement = Requirement("foo>10")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.definition.query(requirement, package_definition_mapping)


def test_query_definition_mixed_version_error(package_definition_mapping):
    """Fails to query definition from non-versioned and versioned definitions.
    """
    requirement = Requirement("foo")

    package_definition_mapping["foo"]["unknown"] = (
        wiz.definition.Definition({"identifier": "foo"})
    )

    with pytest.raises(wiz.exception.RequestNotFound) as error:
        wiz.definition.query(requirement, package_definition_mapping)

    assert (
        "RequestNotFound: Impossible to retrieve the best matching definition "
        "for 'foo' as non-versioned and versioned definitions have been "
        "fetched."
    ) in str(error)


def test_export_data(mocked_filesystem_export):
    """Export definition data as a JSON file."""
    data = {
        "identifier": "foo",
        "description": "Test definition",
        "command": {
            "app": "App0.1",
            "appX": "AppX0.1"
        },
        "environ": {
            "KEY": "VALUE"
        }
    }

    wiz.definition.export("/path/to/output", data)

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/output/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"description\": \"Test definition\",\n"
            "    \"command\": {\n"
            "        \"app\": \"App0.1\",\n"
            "        \"appX\": \"AppX0.1\"\n"
            "    },\n"
            "    \"environ\": {\n"
            "        \"KEY\": \"VALUE\"\n"
            "    }\n"
            "}"
        )
    )


def test_export_data_with_version(mocked_filesystem_export):
    """Export a definition data as a JSON file with version."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "Test definition",
        "command": {
            "app": "App0.1",
            "appX": "AppX0.1"
        },
        "environ": {
            "KEY": "VALUE"
        }
    }

    wiz.definition.export("/path/to/output", data)

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/output/foo-0.1.0.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"version\": \"0.1.0\",\n"
            "    \"description\": \"Test definition\",\n"
            "    \"command\": {\n"
            "        \"app\": \"App0.1\",\n"
            "        \"appX\": \"AppX0.1\"\n"
            "    },\n"
            "    \"environ\": {\n"
            "        \"KEY\": \"VALUE\"\n"
            "    }\n"
            "}"
        )
    )


def test_export(mocked_filesystem_export):
    """Export definition as a JSON file."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
        "description": "Test definition",
        "command": {
            "app": "App0.1",
            "appX": "AppX0.1"
        },
        "environ": {
            "KEY": "VALUE"
        }
    })

    wiz.definition.export("/path/to/output", definition)

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/output/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"description\": \"Test definition\",\n"
            "    \"command\": {\n"
            "        \"app\": \"App0.1\",\n"
            "        \"appX\": \"AppX0.1\"\n"
            "    },\n"
            "    \"environ\": {\n"
            "        \"KEY\": \"VALUE\"\n"
            "    }\n"
            "}"
        )
    )


def test_export_with_version(mocked_filesystem_export):
    """Export a definition as a JSON file with version."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
        "version": "0.1.0",
        "description": "Test definition",
        "command": {
            "app": "App0.1",
            "appX": "AppX0.1"
        },
        "environ": {
            "KEY": "VALUE"
        }
    })

    wiz.definition.export("/path/to/output", definition)

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/output/foo-0.1.0.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"version\": \"0.1.0\",\n"
            "    \"description\": \"Test definition\",\n"
            "    \"command\": {\n"
            "        \"app\": \"App0.1\",\n"
            "        \"appX\": \"AppX0.1\"\n"
            "    },\n"
            "    \"environ\": {\n"
            "        \"KEY\": \"VALUE\"\n"
            "    }\n"
            "}"
        )
    )


def test_discover(mocked_load, registries, definitions):
    """Discover and yield *definitions*."""
    mocked_load.side_effect = definitions

    result = wiz.definition.discover(registries)
    assert isinstance(result, types.GeneratorType)
    assert mocked_load.call_count == 0

    discovered = list(result)
    assert len(discovered) == 6
    assert mocked_load.call_count == 6

    r1 = registries[0]
    r2 = registries[1]

    path = os.path.join(r1, "defA.json")
    mocked_load.assert_any_call(path, mapping={"registry": r1, "origin": path})

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(path, mapping={"registry": r1, "origin": path})

    path = os.path.join(r1, "level1", "level2", "level3", "defF.json")
    mocked_load.assert_any_call(path, mapping={"registry": r1, "origin": path})

    path = os.path.join(r1, "level1", "level2", "level3", "defE.json")
    mocked_load.assert_any_call(path, mapping={"registry": r1, "origin": path})

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(path, mapping={"registry": r2, "origin": path})

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(path, mapping={"registry": r2, "origin": path})

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

    r1 = registries[0]
    r2 = registries[1]

    path = os.path.join(r1, "defA.json")
    mocked_load.assert_any_call(path, mapping={"registry": r1, "origin": path})

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(path, mapping={"registry": r1, "origin": path})

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(path, mapping={"registry": r2, "origin": path})

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(path, mapping={"registry": r2, "origin": path})

    assert discovered == definitions[:4]


def test_discover_without_disabled(mocked_load, registries, definitions):
    """Discover and yield definitions without disabled definition."""
    definitions[2] = wiz.definition.Definition(
        disabled=True, **definitions[2].to_dict(serialize_content=True)
    )
    definitions[4] = wiz.definition.Definition(
        disabled=True, **definitions[4].to_dict(serialize_content=True)
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
        "version": "0.1.0",
        "description": "This is a definition",
        "registry": "/path/to/registry",
        "origin": "/path/to/registry/test-0.1.0.json",
        "auto-use": True,
        "system": {
            "platform": "linux",
            "os": "el >= 6, < 7",
            "arch": "x86_64"
        },
        "command": {
            "app": "AppX"
        },
        "environ": {
            "KEY1": "VALUE1"
        },
        "requirements": ["foo"],
        "constraints": ["bar==2.1.0"],
        "variants": [
            {
                "identifier": "Variant1",
                "command": {
                    "appV1": "AppX --test"
                },
                "environ": {
                    "KEY2": "VALUE2"
                },
                "requirements": ["bim >= 9, < 10"],
                "constraints": ["baz==6.3.1"]
            }
        ]
    }

    environment = wiz.definition.Definition(data)

    assert environment.to_dict() == {
        "identifier": "test",
        "version": Version("0.1.0"),
        "description": "This is a definition",
        "registry": "/path/to/registry",
        "origin": "/path/to/registry/test-0.1.0.json",
        "auto-use": True,
        "system": {
            "platform": "linux",
            "os": "el >= 6, < 7",
            "arch": "x86_64"
        },
        "command": {
            "app": "AppX"
        },
        "environ": {
            "KEY1": "VALUE1"
        },
        "requirements": [Requirement("foo")],
        "constraints": [Requirement("bar==2.1.0")],
        "variants": [
            {
                "identifier": "Variant1",
                "command": {
                    "appV1": "AppX --test"
                },
                "environ": {
                    "KEY2": "VALUE2"
                },
                "requirements": [Requirement("bim >= 9, < 10")],
                "constraints": [Requirement("baz==6.3.1")]
            }
        ]
    }

    assert environment.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"version\": \"0.1.0\",\n"
        "    \"description\": \"This is a definition\",\n"
        "    \"registry\": \"/path/to/registry\",\n"
        "    \"origin\": \"/path/to/registry/test-0.1.0.json\",\n"
        "    \"auto-use\": \"true\",\n"
        "    \"system\": {\n"
        "        \"platform\": \"linux\",\n"
        "        \"os\": \"el >= 6, < 7\",\n"
        "        \"arch\": \"x86_64\"\n"
        "    },\n"
        "    \"command\": {\n"
        "        \"app\": \"AppX\"\n"
        "    },\n"
        "    \"environ\": {\n"
        "        \"KEY1\": \"VALUE1\"\n"
        "    },\n"
        "    \"requirements\": [\n"
        "        \"foo\"\n"
        "    ],\n"
        "    \"constraints\": [\n"
        "        \"bar ==2.1.0\"\n"
        "    ],\n"
        "    \"variants\": [\n"
        "        {\n"
        "            \"identifier\": \"Variant1\",\n"
        "            \"command\": {\n"
        "                \"appV1\": \"AppX --test\"\n"
        "            },\n"
        "            \"environ\": {\n"
        "                \"KEY2\": \"VALUE2\"\n"
        "            },\n"
        "            \"requirements\": [\n"
        "                \"bim >=9, <10\"\n"
        "            ],\n"
        "            \"constraints\": [\n"
        "                \"baz ==6.3.1\"\n"
        "            ]\n"
        "        }\n"
        "    ]\n"
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
    assert definition.constraints == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_dict() == OrderedDict([
        ("identifier", "test"),
    ])


@pytest.mark.parametrize("options, expected_version", [
    ({}, Version("0.1.0")),
    ({"serialize_content": True}, "0.1.0")
], ids=[
    "non-serialized",
    "serialized",
])
def test_definition_with_version(options, expected_version):
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
    assert definition.constraints == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_dict(**options) == OrderedDict([
        ("identifier", "test"),
        ("version", expected_version),
    ])


def test_definition_with_description():
    """Create a definition with description."""
    data = {
        "identifier": "test",
        "description": "This is a definition"
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == "unknown"
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.constraints == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_dict() == OrderedDict([
        ("identifier", "test"),
        ("description", "This is a definition")
    ])


def test_definition_with_environ():
    """Create a definition with environment mapping."""
    data = {
        "identifier": "test",
        "description": "This is a definition",
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
            "KEY3": "PATH1:PATH2:PATH3"
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == "unknown"
    assert definition.description == "This is a definition"
    assert definition.requirements == []
    assert definition.constraints == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.environ == {
        "KEY1": "VALUE1",
        "KEY2": "VALUE2",
        "KEY3": "PATH1:PATH2:PATH3"
    }

    assert definition.to_ordered_dict() == OrderedDict([
        ("identifier", "test"),
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
        "description": "This is a definition",
        "requirements": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == "unknown"
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []
    assert definition.constraints == []
    assert definition.requirements == map(Requirement, data["requirements"])

    assert definition.to_ordered_dict(serialize_content=True) == OrderedDict([
        ("identifier", "test"),
        ("description", "This is a definition"),
        ("requirements", [
            "envA >=1.0.0",
            "envB >=3.4.2, <4",
            "envC"
        ])
    ])

    for requirement in definition.to_ordered_dict()["requirements"]:
        assert isinstance(requirement, Requirement)


def test_definition_with_constraints():
    """Create a definition with constraints."""
    data = {
        "identifier": "test",
        "description": "This is a definition",
        "constraints": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == "unknown"
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []
    assert definition.constraints == map(Requirement, data["constraints"])
    assert definition.requirements == []

    assert definition.to_ordered_dict(serialize_content=True) == OrderedDict([
        ("identifier", "test"),
        ("description", "This is a definition"),
        ("constraints", [
            "envA >=1.0.0",
            "envB >=3.4.2, <4",
            "envC"
        ])
    ])

    for requirement in definition.to_ordered_dict()["constraints"]:
        assert isinstance(requirement, Requirement)


def test_definition_with_command():
    """Create a definition with command."""
    data = {
        "identifier": "test",
        "description": "This is a definition",
        "command": {
            "app": "App0.1",
            "appX": "App0.1 --option value"
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == "unknown"
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.constraints == []
    assert definition.system == {}
    assert definition.variants == []

    assert definition.command == {
        "app": "App0.1",
        "appX": "App0.1 --option value"
    }

    assert definition.to_ordered_dict() == OrderedDict([
        ("identifier", "test"),
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
        "description": "This is a definition",
        "system": {
            "arch": "x86_64",
            "platform": "linux"
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == "unknown"
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.requirements == []
    assert definition.constraints == []
    assert definition.variants == []

    assert definition.system == {
        "arch": "x86_64",
        "platform": "linux"
    }

    assert definition.to_ordered_dict() == OrderedDict([
        ("identifier", "test"),
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
        "description": "This is a definition",
        "variants": [
            {
                "identifier": "1.0",
                "environ": {
                    "VERSION": "1.0"
                },
                "requirements": [
                    "envA >= 1.0, < 2"
                ],
                "constraints": [
                    "envB==0.1.0"
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
    assert definition.version == "unknown"
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.command == {}
    assert definition.system == {}

    for variant_data, variant in itertools.izip_longest(
        data["variants"], definition.variants
    ):
        assert variant.identifier == variant_data["identifier"]
        assert variant.environ == variant_data.get("environ", {})
        assert variant.command == variant_data.get("command", {})
        assert variant.requirements == map(
            Requirement, variant_data.get("requirements", [])
        )

    assert definition.to_ordered_dict(serialize_content=True) == OrderedDict([
        ("identifier", "test"),
        ("description", "This is a definition"),
        ("variants", [
            OrderedDict([
                ("identifier", "1.0"),
                ("environ", {"VERSION": "1.0"}),
                ("requirements", ["envA >=1.0, <2"]),
                ("constraints", ["envB ==0.1.0"])
            ]),
            OrderedDict([
                ("identifier", "2.0"),
                ("command", {"app": "App2.0"}),
                ("environ", {"VERSION": "2.0"}),
                ("requirements", ["envA >=2.0, <3"])
            ]),
            OrderedDict([
                ("identifier", "XXX"),
                ("command", {"app": "AppXXX"}),
            ])
        ])
    ])

    for variant in definition.to_ordered_dict()["variants"]:
        for requirement in variant.get("requirements", []):
            assert isinstance(requirement, Requirement)
        for requirement in variant.get("constraints", []):
            assert isinstance(requirement, Requirement)


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
        "package requirement [The requirement 'envA -!!!' is incorrect]"
    ) in str(error)


def test_definition_with_constraint_error():
    """Fail to create a definition with incorrect constraint."""
    data = {
        "identifier": "test",
        "constraints": [
            "envA -!!!",
        ]
    }

    with pytest.raises(wiz.exception.IncorrectDefinition) as error:
        wiz.definition.Definition(data)

    assert (
        "IncorrectDefinition: The definition 'test' contains an incorrect "
        "package constraint [The requirement 'envA -!!!' is incorrect]"
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
        "incorrect package requirement [The requirement 'envA -!!!' "
        "is incorrect]"
    ) in str(error)


def test_definition_with_variant_constraint_error():
    """Fail to create a definition with incorrect variant constraint."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "1.0",
                "constraints": [
                    "envA -!!!"
                ]
            }
        ]
    }

    with pytest.raises(wiz.exception.IncorrectDefinition) as error:
        wiz.definition.Definition(data)

    assert (
        "IncorrectDefinition: The definition 'test' [1.0] contains an "
        "incorrect package constraint [The requirement 'envA -!!!' "
        "is incorrect]"
    ) in str(error)


def test_definition_set():
    """Create new definition from existing definition with new element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    # Change identifier
    definition2 = definition1.set("identifier", "bar")
    assert definition2.to_dict(serialize_content=True) == {"identifier": "bar"}
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    # Add version
    definition3 = definition2.set("version", "0.1.0")
    assert definition3.to_dict(serialize_content=True) == {
        "identifier": "bar",
        "version": "0.1.0"
    }
    assert definition2.to_dict(serialize_content=True) == {"identifier": "bar"}
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}


def test_definition_variant_set():
    """Create new definition from existing definition with new variant."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    # Add variant
    definition2 = definition1.set(
        "variants", [
            {"identifier": "Variant1", "requirements": ["bar"]},
            {"identifier": "Variant2", "requirements": ["bar>1"]}
        ]
    )
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "variants": [
            {"identifier": "Variant1", "requirements": ["bar"]},
            {"identifier": "Variant2", "requirements": ["bar >1"]}
        ]
    }
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    # Overwrite variant
    definition3 = definition2.set(
        "variants", [
            {"identifier": "test"},
        ]
    )
    assert definition3.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "variants": [
            {"identifier": "test"}
        ]
    }
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "variants": [
            {"identifier": "Variant1", "requirements": ["bar"]},
            {"identifier": "Variant2", "requirements": ["bar >1"]}
        ]
    }
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}


def test_definition_update():
    """Create new definition from existing definition with updated element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    definition2 = definition1.update(
        "environ", {"key1": "value1", "key2": "value2"}
    )
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    definition3 = definition2.update(
        "environ", {"key1": "VALUE1", "key3": "value3"}
    )
    assert definition3.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "environ": {
            "key1": "VALUE1",
            "key2": "value2",
            "key3": "value3"
        }
    }
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}


def test_definition_update_error():
    """Fail to create new definition with non-dictionary element updated."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.update("identifier", {"key1": "value1"})


def test_definition_extend():
    """Create new definition from existing definition with extended element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    definition2 = definition1.extend(
        "requirements", ["bar", "bim>=1"]
    )
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "bar",
            "bim >=1"
        ]
    }
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    definition3 = definition2.extend(
        "requirements", ["test"]
    )
    assert definition3.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "bar",
            "bim >=1",
            "test"
        ]
    }
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "bar",
            "bim >=1"
        ]
    }
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}


def test_definition_extend_error():
    """Fail to create new definition with non-list element extended."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.extend("identifier", ["test"])


def test_definition_insert():
    """Create new definition from existing definition with extended element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    definition2 = definition1.set(
        "requirements", ["bar", "bim>=1"]
    )
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "bar",
            "bim >=1"
        ]
    }
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    definition3 = definition2.insert(
        "requirements", "test", 0
    )
    assert definition3.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "test",
            "bar",
            "bim >=1"
        ]
    }
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "bar",
            "bim >=1"
        ]
    }
    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}


def test_definition_insert_error():
    """Fail to create new definition with non-list element extended."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.insert("identifier", ["test"], 0)


def test_definition_remove():
    """Create new definition from existing definition without element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "version": "0.1.0"
    })

    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "version": "0.1.0"
    }

    definition2 = definition1.remove("version")
    assert definition2.to_dict(serialize_content=True) == {"identifier": "foo"}
    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "version": "0.1.0"
    }


def test_definition_remove_error():
    """Fail to create new definition without un-existing element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict(serialize_content=True) == {"identifier": "foo"}

    with pytest.raises(KeyError):
        definition1.remove("error")


def test_definition_remove_key():
    """Create new definition from existing definition without element key."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    })

    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }

    definition2 = definition1.remove_key("environ", "key1")
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "environ": {
            "key2": "value2"
        }
    }
    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }


def test_definition_remove_key_error():
    """Fail to create new definition without un-existing element or element key.
    """
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    })

    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    }

    with pytest.raises(KeyError):
        definition1.remove_key("test", "error")

    with pytest.raises(KeyError):
        definition1.remove_key("environ", "key42")

    with pytest.raises(ValueError):
        definition1.remove_key("identifier", "key42")


def test_definition_remove_index():
    """Create new definition from existing definition without element index."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "requirements": [
            "test",
            "bar",
            "bim >=1"
        ]
    })

    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "test",
            "bar",
            "bim >=1"
        ]
    }

    definition2 = definition1.remove_index("requirements", 0)
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "bar",
            "bim >=1"
        ]
    }
    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "test",
            "bar",
            "bim >=1"
        ]
    }

    definition3 = definition2.remove_index("requirements", 1)
    assert definition3.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "bar",
        ]
    }
    assert definition2.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "bar",
            "bim >=1"
        ]
    }
    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "test",
            "bar",
            "bim >=1"
        ]
    }


def test_definition_remove_index_error():
    """Fail to create definition without un-existing element or element index.
    """
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "requirements": [
            "test",
            "bar",
            "bim >=1"
        ]
    })

    assert definition1.to_dict(serialize_content=True) == {
        "identifier": "foo",
        "requirements": [
            "test",
            "bar",
            "bim >=1"
        ]
    }

    with pytest.raises(KeyError):
        definition1.remove_index("test", "error")

    with pytest.raises(KeyError):
        definition1.remove_index("environ", 42)

    with pytest.raises(ValueError):
        definition1.remove_key("identifier", 42)
