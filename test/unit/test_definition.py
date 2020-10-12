# :coding: utf-8

import copy
import os
import types
from collections import OrderedDict, Counter

import pytest

import wiz.definition
import wiz.exception
import wiz.filesystem
import wiz.system
from wiz.utility import Requirement, Version


@pytest.fixture()
def definitions():
    """Return list of mocked definitions."""
    return [
        wiz.definition.Definition({
            "identifier": "foo",
            "namespace": "test",
            "version": "0.1.0",
        }),
        wiz.definition.Definition({
            "identifier": "foo",
            "namespace": "test",
            "version": "1.1.0",
            "command": {
                "foo": "Foo1.1",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bar",
            "version": "1.0.0",
            "command": {
                "bar": "Bar1.0",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bar",
            "version": "0.9.2",
            "command": {
                "bar": "Bar0.9",
            }
        }),
        wiz.definition.Definition({
            "identifier": "baz",
            "version": "0.1.1",
            "command": {
                "baz": "Baz0.1",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bim",
            "version": "0.2.1",
            "command": {
                "bim": "Bim0.2",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bim",
            "version": "0.2.1",
            "command": {
                "bim-test": "Bim0.2 --test",
            }
        }),
        wiz.definition.Definition({
            "identifier": "bim",
            "version": "0.1.0",
            "command": {
                "bim": "Bim0.1",
            }
        }),
        wiz.definition.Definition({
            "identifier": "foo",
            "namespace": "other"
        }),
        wiz.definition.Definition({
            "identifier": "foo",
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
def mocked_system_validate(mocker):
    """Return mocked system.validate function."""
    return mocker.patch.object(wiz.system, "validate")


@pytest.fixture()
def mocked_filesystem_export(mocker):
    """Return mocked filesystem.export function."""
    return mocker.patch.object(wiz.filesystem, "export")


@pytest.fixture()
def mocked_system_validate(mocker):
    """Return mocked validate function."""
    return mocker.patch.object(wiz.system, "validate")


@pytest.fixture()
def mocked_discover(mocker):
    """Return mocked discovery function."""
    return mocker.patch.object(wiz.definition, "discover")


@pytest.fixture()
def mocked_load(mocker):
    """Return mocked load function."""
    return mocker.patch.object(wiz.definition, "load")


@pytest.fixture()
def mocked_fetch(mocker):
    """Return mocked fetch function."""
    return mocker.patch.object(wiz.definition, "fetch")


@pytest.fixture()
def mocked_query(mocker):
    """Return mocked query function."""
    return mocker.patch.object(wiz.definition, "query")


@pytest.fixture()
def mocked_definition(mocker):
    """Return mocked Definition class."""
    return mocker.patch.object(
        wiz.definition, "Definition", return_value="DEFINITION"
    )


@pytest.fixture()
def mocked_registry_install(mocker):
    """Return mocked load function."""
    return mocker.patch.object(wiz.registry, "install")


@pytest.mark.parametrize("options", [
    {},
    {"max_depth": 4},
    {"system_mapping": "__SYSTEM__"}
], ids=[
    "without-option",
    "with-max-depth",
    "with-system"
])
def test_fetch(mocked_discover, definitions, options):
    """Fetch all definition within *paths*."""
    mocked_discover.return_value = definitions
    result = wiz.definition.fetch(
        ["/path/to/registry-1", "/path/to/registry-2"], **options
    )

    mocked_discover.assert_called_once_with(
        ["/path/to/registry-1", "/path/to/registry-2"],
        max_depth=options.get("max_depth"),
        system_mapping=options.get("system_mapping")
    )

    assert result == {
        "package": {
            "__namespace__": {
                "foo": {"test", "other"}
            },
            "test::foo": {
                "0.1.0": definitions[0],
                "1.1.0": definitions[1]
            },
            "bar": {
                "1.0.0": definitions[2],
                "0.9.2": definitions[3]
            },
            "baz": {
                "0.1.1": definitions[4]
            },
            "bim": {
                # The 5th definition in the incoming list is overridden by the
                # 6th one which has the same identifier and version.
                "0.2.1": definitions[6],
                "0.1.0": definitions[7]
            },
            "other::foo": {
                "-": definitions[8]
            },
            "foo": {
                "-": definitions[9]
            }
        },
        "command": {
            "foo": "test::foo",
            "bar": "bar",
            "baz": "baz",
            "bim-test": "bim",
            "bim": "bim"
        },
        "implicit-packages": []
    }


@pytest.mark.parametrize("options", [
    {},
    {"max_depth": 4},
    {"system_mapping": "__SYSTEM__"}
], ids=[
    "without-option",
    "with-max-depth",
    "with-system"
])
def test_fetch_with_implicit_packages(mocked_discover, definitions, options):
    """Fetch all definition within *paths*."""
    definitions[0] = definitions[0].set("auto-use", True)
    definitions[1] = definitions[1].set("auto-use", True)
    definitions[3] = definitions[3].set("auto-use", True)
    definitions[8] = definitions[8].set("auto-use", True)

    mocked_discover.return_value = definitions
    result = wiz.definition.fetch(
        ["/path/to/registry-1", "/path/to/registry-2"], **options
    )

    mocked_discover.assert_called_once_with(
        ["/path/to/registry-1", "/path/to/registry-2"],
        max_depth=options.get("max_depth"),
        system_mapping=options.get("system_mapping"),
    )

    assert result == {
        "package": {
            "__namespace__": {
                "foo": {"test", "other"}
            },
            "test::foo": {
                "0.1.0": definitions[0],
                "1.1.0": definitions[1]
            },
            "bar": {
                "1.0.0": definitions[2],
                "0.9.2": definitions[3]
            },
            "baz": {
                "0.1.1": definitions[4]
            },
            "bim": {
                # The 5th definition in the incoming list is overridden by the
                # 6th one which has the same identifier and version.
                "0.2.1": definitions[6],
                "0.1.0": definitions[7]
            },
            "other::foo": {
                "-": definitions[8]
            },
            "foo": {
                "-": definitions[9]
            }
        },
        "command": {
            "foo": "test::foo",
            "bar": "bar",
            "baz": "baz",
            "bim-test": "bim",
            "bim": "bim"
        },
        "implicit-packages": [
            "other::foo",
            "bar==0.9.2",
            "test::foo==1.1.0"
        ]
    }


def test_query_definition():
    """Return best matching definition from requirement."""
    package_mapping = {
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
        "foo": {
            "1.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "1.1.0",
            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
            }),
        }
    }

    requirement = Requirement("bar")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["bar"]["0.3.0"]
    )

    requirement = Requirement("foo<0.2")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["foo"]["0.1.0"]
    )

    requirement = Requirement("bar==0.1.5")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["bar"]["0.1.5"]
    )


def test_query_definition_explicit_namespace():
    """Explicitly query package identifier with or without namespace."""
    package_mapping = {
        "__namespace__": {
            "foo": {"namespace"},
        },
        "foo": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
            }),
        },
        "namespace::foo": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
                "namespace": "namespace"
            }),
        },
    }

    requirement = Requirement("::foo")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["foo"]["0.1.0"]
    )

    requirement = Requirement("namespace::foo")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["namespace::foo"]["0.1.0"]
    )


def test_query_definition_guess_default_one_namespace():
    """Guess namespace when only one namespace is available for identifier."""
    package_mapping = {
        "__namespace__": {
            "foo": {"namespace"},
        },
        "namespace::foo": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
                "namespace": "namespace"
            }),
        },
    }

    requirement = Requirement("foo")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["namespace::foo"]["0.1.0"]
    )


def test_query_definition_guess_default_namespace_identifier():
    """Guess namespace when only one namespace is equal to identifier."""
    package_mapping = {
        "__namespace__": {
            "foo": {"namespace", "foo"},
        },
        "foo::foo": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
                "namespace": "foo"
            }),
        },
        "namespace::foo": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.2.0",
                "namespace": "namespace"
            }),
        },
    }

    requirement = Requirement("foo")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["foo::foo"]["0.1.0"]
    )


def test_query_definition_guess_default_namespace_counter():
    """Guess namespace from namespace counter."""
    package_mapping = {
        "__namespace__": {
            "foo": {"namespace1", "namespace2"},
        },
        "namespace1::foo": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
                "namespace": "namespace1"
            }),
        },
        "namespace2::foo": {
            "0.2.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.2.0",
                "namespace": "namespace2"
            }),
        },
    }

    requirement = Requirement("foo")

    # No counter
    with pytest.raises(wiz.exception.RequestNotFound) as error:
        wiz.definition.query(requirement, package_mapping)

    assert (
        "Cannot guess default namespace for 'foo' "
        "[available: namespace1, namespace2]"
    ) in str(error)

    # Counter with "namespace1"
    assert (
        wiz.definition.query(
            requirement, package_mapping,
            namespace_counter=Counter(["namespace1", "namespace1"])
        ) ==
        package_mapping["namespace1::foo"]["0.1.0"]
    )

    assert (
        wiz.definition.query(
            requirement, package_mapping,
            namespace_counter=Counter(["namespace1"])
        ) ==
        package_mapping["namespace1::foo"]["0.1.0"]
    )

    # Counter with "namespace1" and "namespace2"
    with pytest.raises(wiz.exception.RequestNotFound) as error:
        wiz.definition.query(
            requirement, package_mapping,
            namespace_counter=Counter([
                "namespace1", "namespace2", "namespace1", "namespace2"
            ])
        )

    assert (
        "Cannot guess default namespace for 'foo' "
        "[available: namespace1, namespace2]"
    ) in str(error)


def test_query_definition_with_variant_identifier():
    """Query definition version from variant identifier."""
    package_mapping = {
        "foo": {
            "0.1.1": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.1",
                "variants": [
                    {
                        "identifier": "V2"
                    }
                ]

            }),
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
                "variants": [
                    {
                        "identifier": "V1"
                    }
                ]
            }),
        },
    }

    requirement = Requirement("foo[V1]")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["foo"]["0.1.0"]
    )

    requirement = Requirement("foo[V2]")
    assert (
        wiz.definition.query(requirement, package_mapping) ==
        package_mapping["foo"]["0.1.1"]
    )


def test_query_definition_name_error():
    """Fails to query the definition name."""
    package_mapping = {}

    requirement = Requirement("incorrect")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.definition.query(requirement, package_mapping)


def test_query_definition_version_error():
    """Fails to query the definition version."""
    package_mapping = {
        "foo": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
            }),
        },
    }

    requirement = Requirement("foo>10")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.definition.query(requirement, package_mapping)


def test_query_definition_mixed_version_error():
    """Fails to query definition from non-versioned and versioned definitions.
    """
    package_mapping = {
        "foo": {
            "0.1.0": wiz.definition.Definition({
                "identifier": "foo",
                "version": "0.1.0",
            }),
            "-": wiz.definition.Definition({
                "identifier": "foo",
            }),
        },
    }

    requirement = Requirement("foo")

    with pytest.raises(wiz.exception.RequestNotFound) as error:
        wiz.definition.query(requirement, package_mapping)

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
        ), overwrite=False
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
        ), overwrite=False
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
        ), overwrite=False
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
        ), overwrite=False
    )


def test_discover(mocked_load, mocked_system_validate, registries, definitions):
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
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defF.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defE.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(
        path, registry_path=r2
    )

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(
        path, registry_path=r2
    )

    assert discovered == definitions[:6]
    mocked_system_validate.assert_not_called()


def test_discover_with_max_depth(
    mocked_load, mocked_system_validate, registries, definitions
):
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
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(
        path, registry_path=r2
    )

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(
        path, registry_path=r2
    )

    assert discovered == definitions[:4]
    mocked_system_validate.assert_not_called()


def test_discover_with_system_valid(
    mocked_load, mocked_system_validate, registries, definitions
):
    """Discover and yield definitions with valid system."""
    mocked_load.side_effect = definitions
    mocked_system_validate.return_value = True

    result = wiz.definition.discover(registries, system_mapping="__SYSTEM__")
    assert isinstance(result, types.GeneratorType)
    assert mocked_load.call_count == 0

    discovered = list(result)
    assert len(discovered) == 6
    assert mocked_load.call_count == 6

    r1 = registries[0]
    r2 = registries[1]

    path = os.path.join(r1, "defA.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defF.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defE.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(
        path, registry_path=r2
    )

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(
        path, registry_path=r2
    )

    assert discovered == definitions[:6]


def test_discover_with_system_invalid(
    mocked_load, mocked_system_validate, registries, definitions
):
    """Discover and yield definitions with invalid system."""
    mocked_load.side_effect = definitions
    mocked_system_validate.return_value = False

    result = wiz.definition.discover(registries, system_mapping="__SYSTEM__")
    assert isinstance(result, types.GeneratorType)
    assert mocked_load.call_count == 0

    discovered = list(result)
    assert len(discovered) == 0
    assert mocked_load.call_count == 6

    r1 = registries[0]
    r2 = registries[1]

    path = os.path.join(r1, "defA.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defF.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defE.json")
    mocked_load.assert_any_call(
        path, registry_path=r1
    )

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(
        path, registry_path=r2
    )

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(
        path, registry_path=r2
    )

    assert discovered == []


def test_discover_without_disabled(mocked_load, registries, definitions):
    """Discover and yield definitions without disabled definition."""
    data = definitions[2].data()
    data["disabled"] = True
    definitions[2] = wiz.definition.Definition(data)

    data = definitions[4].data()
    data["disabled"] = True
    definitions[4] = wiz.definition.Definition(data)

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
    wiz.exception.DefinitionError
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
    mocked_definition.assert_called_once_with(
        {"identifier": "test_definition"},
        path=temporary_file,
        registry_path=None,
        copy_data=False
    )


def test_load_with_mapping(mocked_definition, temporary_file):
    """Load a definition from a path and a mapping."""
    with open(temporary_file, "w") as stream:
        stream.write("{\"identifier\": \"test_definition\"}")

    mocked_definition.return_value = "DEFINITION"
    result = wiz.definition.load(temporary_file, mapping={"key": "value"})
    assert result == "DEFINITION"
    mocked_definition.assert_called_once_with(
        {"identifier": "test_definition", "key": "value"},
        path=temporary_file,
        registry_path=None,
        copy_data=False
    )


def test_minimal_definition():
    """Create a minimal definition."""
    data = {"identifier": "test"}

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\"\n"
        "}"
    )


def test_minimal_definition_with_paths():
    """Create a minimal definition with paths."""
    data = {"identifier": "test"}

    definition = wiz.definition.Definition(
        data,
        path="/path/to/definition.json",
        registry_path="/path/to/registry",
    )
    assert definition.path == "/path/to/definition.json"
    assert definition.registry_path == "/path/to/registry"
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\"\n"
        "}"
    )


def test_minimal_definition_with_namespace():
    """Create a minimal definition with namespace."""
    data = {
        "identifier": "test",
        "namespace": "foo",
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "foo::test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "foo::test"
    assert definition.description is None
    assert definition.namespace == "foo"
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("namespace", "foo"),
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"namespace\": \"foo\"\n"
        "}"
    )


def test_definition_with_version():
    """Create a definition with version."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test==0.1.0"
    assert definition.qualified_version_identifier == "test==0.1.0"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"version\": \"0.1.0\"\n"
        "}"
    )


def test_definition_with_version_and_namespace():
    """Create a definition with version and namespace."""
    data = {
        "identifier": "test",
        "namespace": "foo",
        "version": "0.1.0",
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.qualified_identifier == "foo::test"
    assert definition.version_identifier == "test==0.1.0"
    assert definition.qualified_version_identifier == "foo::test==0.1.0"
    assert definition.description is None
    assert definition.namespace == "foo"
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
        ("namespace", "foo"),
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"version\": \"0.1.0\",\n"
        "    \"namespace\": \"foo\"\n"
        "}"
    )


def test_definition_with_description():
    """Create a definition with description."""
    data = {
        "identifier": "test",
        "description": "This is a definition"
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description == "This is a definition"
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("description", "This is a definition")
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"description\": \"This is a definition\"\n"
        "}"
    )


def test_definition_with_install_keywords():
    """Create a definition with installation keywords."""
    data = {
        "identifier": "test",
        "install-root": "/path/to/root",
        "install-location": "${INSTALL_ROOT}/install"
    }
    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root == "/path/to/root"
    assert definition.install_location == "${INSTALL_ROOT}/install"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("install-root", "/path/to/root"),
        ("install-location", "${INSTALL_ROOT}/install")
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"install-root\": \"/path/to/root\",\n"
        "    \"install-location\": \"${INSTALL_ROOT}/install\"\n"
        "}"
    )


def test_definition_with_auto_use():
    """Create a definition with 'auto-use' value."""
    data = {
        "identifier": "test",
        "auto-use": True
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is True
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("auto-use", True)
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"auto-use\": true\n"
        "}"
    )


def test_definition_with_disabled():
    """Create a definition with 'disabled' value."""
    data = {
        "identifier": "test",
        "disabled": True
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is True
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("disabled", True)
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"disabled\": true\n"
        "}"
    )


def test_definition_with_system():
    """Create a definition with system constraint."""
    data = {
        "identifier": "test",
        "system": {
            "arch": "x86_64",
            "platform": "linux"
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {
        "arch": "x86_64",
        "platform": "linux"
    }
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("system", OrderedDict([
            ("platform", "linux"),
            ("arch", "x86_64"),
        ]))
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"system\": {\n"
        "        \"platform\": \"linux\",\n"
        "        \"arch\": \"x86_64\"\n"
        "    }\n"
        "}"
    )


def test_definition_with_command():
    """Create a definition with command."""
    data = {
        "identifier": "test",
        "command": {
            "app1": "App1",
            "app3": "App3",
            "app2": "App2",
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {
        "app1": "App1",
        "app3": "App3",
        "app2": "App2",
    }
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("command", OrderedDict([
            ("app1", "App1"),
            ("app2", "App2"),
            ("app3", "App3"),
        ]))
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"command\": {\n"
        "        \"app1\": \"App1\",\n"
        "        \"app2\": \"App2\",\n"
        "        \"app3\": \"App3\"\n"
        "    }\n"
        "}"
    )


def test_definition_with_environ():
    """Create a definition with environment mapping."""
    data = {
        "identifier": "test",
        "environ": {
            "KEY1": "VALUE1",
            "KEY3": "VALUE3",
            "KEY2": "VALUE2",
        }
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {
        "KEY1": "VALUE1",
        "KEY3": "VALUE3",
        "KEY2": "VALUE2",
    }
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("environ", OrderedDict([
            ("KEY1", "VALUE1"),
            ("KEY2", "VALUE2"),
            ("KEY3", "VALUE3"),
        ]))
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"environ\": {\n"
        "        \"KEY1\": \"VALUE1\",\n"
        "        \"KEY2\": \"VALUE2\",\n"
        "        \"KEY3\": \"VALUE3\"\n"
        "    }\n"
        "}"
    )


def test_definition_with_requirements():
    """Create a definition with requirements."""
    data = {
        "identifier": "test",
        "requirements": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == [
        Requirement("envA >= 1.0.0"),
        Requirement("envB >= 3.4.2, < 4"),
        Requirement("envC")
    ]
    assert definition.conditions == []
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("requirements", [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ])
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"requirements\": [\n"
        "        \"envA >= 1.0.0\",\n"
        "        \"envB >= 3.4.2, < 4\",\n"
        "        \"envC\"\n"
        "    ]\n"
        "}"
    )


def test_definition_with_conditions():
    """Create a definition with conditions."""
    data = {
        "identifier": "test",
        "conditions": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == [
        Requirement("envA >= 1.0.0"),
        Requirement("envB >= 3.4.2, < 4"),
        Requirement("envC")
    ]
    assert definition.variants == []

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("conditions", [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ])
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"conditions\": [\n"
        "        \"envA >= 1.0.0\",\n"
        "        \"envB >= 3.4.2, < 4\",\n"
        "        \"envC\"\n"
        "    ]\n"
        "}"
    )


def test_definition_with_variants():
    """Create a definition with variants."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "V2",
                "install-location": "/path/to/V2",
                "environ": {
                    "KEY21": "VALUE21",
                    "KEY23": "VALUE23",
                    "KEY22": "VALUE22",
                },
                "command": {
                    "appXV2": "AppXV2",
                    "appV2": "AppV2",
                },
                "requirements": [
                    "envA >= 2, < 3"
                ]
            },
            {
                "identifier": "V1",
                "install-location": "/path/to/V1",
                "environ": {
                    "KEY11": "VALUE11",
                    "KEY13": "VALUE13",
                    "KEY12": "VALUE12",
                },
                "command": {
                    "appXV1": "AppXV1",
                    "appV1": "AppV1",
                },
                "requirements": [
                    "envA >= 1, < 2"
                ]
            }
        ]
    }

    definition = wiz.definition.Definition(data)
    assert definition.path is None
    assert definition.registry_path is None
    assert definition.identifier == "test"
    assert definition.version is None
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.description is None
    assert definition.namespace is None
    assert definition.auto_use is False
    assert definition.disabled is False
    assert definition.install_root is None
    assert definition.install_location is None
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.requirements == []
    assert definition.conditions == []

    assert len(definition.variants) == 2
    assert definition.variants[0].definition_identifier == "test"
    assert definition.variants[0].identifier == "V2"
    assert definition.variants[0].install_location == "/path/to/V2"
    assert definition.variants[0].environ == {
        "KEY21": "VALUE21",
        "KEY23": "VALUE23",
        "KEY22": "VALUE22",
    }
    assert definition.variants[0].command == {
        "appXV2": "AppXV2",
        "appV2": "AppV2",
    }
    assert definition.variants[0].requirements == [Requirement("envA >=2, <3")]

    assert definition.variants[1].definition_identifier == "test"
    assert definition.variants[1].identifier == "V1"
    assert definition.variants[1].install_location == "/path/to/V1"
    assert definition.variants[1].environ == {
        "KEY11": "VALUE11",
        "KEY13": "VALUE13",
        "KEY12": "VALUE12",
    }
    assert definition.variants[1].command == {
        "appXV1": "AppXV1",
        "appV1": "AppV1",
    }
    assert definition.variants[1].requirements == [Requirement("envA >=1, <2")]

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("variants", [
            OrderedDict([
                ("identifier", "V2"),
                ("install-location", "/path/to/V2"),
                ("command", OrderedDict([
                    ("appV2", "AppV2"),
                    ("appXV2", "AppXV2"),
                 ])),
                ("environ", OrderedDict([
                    ("KEY21", "VALUE21"),
                    ("KEY22", "VALUE22"),
                    ("KEY23", "VALUE23"),
                 ])),
                ("requirements", ["envA >= 2, < 3"])
            ]),
            OrderedDict([
                ("identifier", "V1"),
                ("install-location", "/path/to/V1"),
                ("command", OrderedDict([
                    ("appV1", "AppV1"),
                    ("appXV1", "AppXV1"),
                 ])),
                ("environ", OrderedDict([
                    ("KEY11", "VALUE11"),
                    ("KEY12", "VALUE12"),
                    ("KEY13", "VALUE13"),
                ])),
                ("requirements", ["envA >= 1, < 2"])
            ])
        ])
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"variants\": [\n"
        "        {\n"
        "            \"identifier\": \"V2\",\n"
        "            \"install-location\": \"/path/to/V2\",\n"
        "            \"command\": {\n"
        "                \"appV2\": \"AppV2\",\n"
        "                \"appXV2\": \"AppXV2\"\n"
        "            },\n"
        "            \"environ\": {\n"
        "                \"KEY21\": \"VALUE21\",\n"
        "                \"KEY22\": \"VALUE22\",\n"
        "                \"KEY23\": \"VALUE23\"\n"
        "            },\n"
        "            \"requirements\": [\n"
        "                \"envA >= 2, < 3\"\n"
        "            ]\n"
        "        },\n"
        "        {\n"
        "            \"identifier\": \"V1\",\n"
        "            \"install-location\": \"/path/to/V1\",\n"
        "            \"command\": {\n"
        "                \"appV1\": \"AppV1\",\n"
        "                \"appXV1\": \"AppXV1\"\n"
        "            },\n"
        "            \"environ\": {\n"
        "                \"KEY11\": \"VALUE11\",\n"
        "                \"KEY12\": \"VALUE12\",\n"
        "                \"KEY13\": \"VALUE13\"\n"
        "            },\n"
        "            \"requirements\": [\n"
        "                \"envA >= 1, < 2\"\n"
        "            ]\n"
        "        }\n"
        "    ]\n"
        "}"
    )


def test_definition_complete():
    """Create a definition with as many keywords as possible."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "namespace": "foo",
        "description": "This is a definition",
        "auto-use": True,
        "install-root": "/path/to/root",
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
        "requirements": ["envB"],
        "conditions": ["envC"],
        "variants": [
            {
                "identifier": "V2",
                "install-location": "${INSTALL_ROOT}/V2/install",
                "environ": {"KEY2": "VALUE2"},
                "command": {"appV2": "AppV2"},
                "requirements": [
                    "envA >= 2, < 3"
                ]
            }
        ]
    }

    definition = wiz.definition.Definition(
        data,
        path="/path/to/definition.json",
        registry_path="/path/to/registry",
    )
    assert definition.path == "/path/to/definition.json"
    assert definition.registry_path == "/path/to/registry"
    assert definition.identifier == "test"
    assert definition.version == Version("0.1.0")
    assert definition.qualified_identifier == "foo::test"
    assert definition.version_identifier == "test==0.1.0"
    assert definition.qualified_version_identifier == "foo::test==0.1.0"
    assert definition.description == "This is a definition"
    assert definition.namespace == "foo"
    assert definition.auto_use is True
    assert definition.disabled is False
    assert definition.install_root == "/path/to/root"
    assert definition.install_location is None
    assert definition.environ == {"KEY1": "VALUE1"}
    assert definition.command == {"app": "AppX"}
    assert definition.system == {
        "platform": "linux",
        "os": "el >= 6, < 7",
        "arch": "x86_64"
    }
    assert definition.requirements == [Requirement("envB")]
    assert definition.conditions == [Requirement("envC")]

    assert len(definition.variants) == 1
    assert definition.variants[0].definition_identifier == "test"
    assert definition.variants[0].identifier == "V2"
    assert definition.variants[0].install_location == (
        "${INSTALL_ROOT}/V2/install"
    )
    assert definition.variants[0].environ == {"KEY2": "VALUE2"}
    assert definition.variants[0].command == {"appV2": "AppV2"}
    assert definition.variants[0].requirements == [Requirement("envA >=2, <3")]

    assert definition.data() == data
    assert definition.ordered_data() == OrderedDict([
        ("identifier", "test"),
        ("version", "0.1.0"),
        ("namespace", "foo"),
        ("description", "This is a definition"),
        ("install-root", "/path/to/root"),
        ("auto-use", True),
        ("system", OrderedDict([
            ("platform", "linux"),
            ("os", "el >= 6, < 7"),
            ("arch", "x86_64"),
        ])),
        ("command", {"app": "AppX"}),
        ("environ", {"KEY1": "VALUE1"}),
        ("requirements", ["envB"]),
        ("conditions", ["envC"]),
        ("variants", [
            OrderedDict([
                ("identifier", "V2"),
                ("install-location", "${INSTALL_ROOT}/V2/install"),
                ("command", {"appV2": "AppV2"}),
                ("environ", {"KEY2": "VALUE2"}),
                ("requirements", ["envA >= 2, < 3"])
            ]),
        ])
    ])
    assert definition.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"version\": \"0.1.0\",\n"
        "    \"namespace\": \"foo\",\n"
        "    \"description\": \"This is a definition\",\n"
        "    \"install-root\": \"/path/to/root\",\n"
        "    \"auto-use\": true,\n"
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
        "        \"envB\"\n"
        "    ],\n"
        "    \"conditions\": [\n"
        "        \"envC\"\n"
        "    ],\n"
        "    \"variants\": [\n"
        "        {\n"
        "            \"identifier\": \"V2\",\n"
        "            \"install-location\": \"${INSTALL_ROOT}/V2/install\",\n"
        "            \"command\": {\n"
        "                \"appV2\": \"AppV2\"\n"
        "            },\n"
        "            \"environ\": {\n"
        "                \"KEY2\": \"VALUE2\"\n"
        "            },\n"
        "            \"requirements\": [\n"
        "                \"envA >= 2, < 3\"\n"
        "            ]\n"
        "        }\n"
        "    ]\n"
        "}"
    )


def test_definition_without_data_copy():
    """Create definition with copy input data."""
    data = {"identifier": "test"}
    definition = wiz.definition.Definition(data)

    data["key"] = "other"
    assert data != definition.data()

    data = {"identifier": "test"}
    definition = wiz.definition.Definition(data, copy_data=False)

    data["key"] = "other"
    assert data == definition.data()


def test_definition_data():
    """Fetch data from definition."""
    definition = wiz.definition.Definition({"identifier": "test"})
    data = definition.data()
    data["key"] = "other"

    assert data != definition.data()

    definition = wiz.definition.Definition({"identifier": "test"})
    data = definition.data(copy_data=False)
    data["key"] = "other"

    assert data == definition.data()


def test_definition_with_error():
    """Fail to create a definition with error."""
    data = {}

    with pytest.raises(wiz.exception.DefinitionError) as error:
        wiz.definition.Definition(data)

    assert "'identifier' is required." in str(error)


def test_definition_with_version_error():
    """Fail to create a definition with incorrect version."""
    data = {
        "identifier": "test",
        "version": "!!!"
    }

    with pytest.raises(wiz.exception.DefinitionError) as error:
        wiz.definition.Definition(data)

    assert "Invalid version: '!!!'" in str(error)


def test_definition_with_requirement_error():
    """Fail to create a definition with incorrect requirement."""
    data = {
        "identifier": "test",
        "requirements": [
            "envA -!!!",
        ]
    }

    definition = wiz.definition.Definition(data)

    with pytest.raises(wiz.exception.RequirementError) as error:
        print(definition.requirements)

    assert "The requirement 'envA -!!!' is incorrect" in str(error)


def test_definition_with_condition_error():
    """Fail to create a definition with incorrect condition."""
    data = {
        "identifier": "test",
        "conditions": [
            "envA -!!!",
        ]
    }

    definition = wiz.definition.Definition(data)

    with pytest.raises(wiz.exception.RequirementError) as error:
        print(definition.conditions)

    assert "The requirement 'envA -!!!' is incorrect" in str(error)


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

    definition = wiz.definition.Definition(data)

    with pytest.raises(wiz.exception.RequirementError) as error:
        print(definition.variants[0].requirements)

    assert "The requirement 'envA -!!!' is incorrect" in str(error)


def test_definition_set():
    """Create new definition from existing definition with new element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.data() == {"identifier": "foo"}

    # Change identifier
    definition2 = definition1.set("identifier", "bar")
    assert definition2.data() == {"identifier": "bar"}
    assert definition1.data() == {"identifier": "foo"}

    # Add version
    definition3 = definition2.set("version", "0.1.0")
    assert definition3.data() == {
        "identifier": "bar",
        "version": "0.1.0"
    }
    assert definition2.data() == {"identifier": "bar"}
    assert definition1.data() == {"identifier": "foo"}


def test_definition_update():
    """Create new definition from existing definition with updated element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.data() == {"identifier": "foo"}

    definition2 = definition1.update(
        "environ", {"key1": "value1", "key2": "value2"}
    )
    assert definition2.data() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    assert definition1.data() == {"identifier": "foo"}

    definition3 = definition2.update(
        "environ", {"key1": "VALUE1", "key3": "value3"}
    )
    assert definition3.data() == {
        "identifier": "foo",
        "environ": {
            "key1": "VALUE1",
            "key2": "value2",
            "key3": "value3"
        }
    }
    assert definition2.data() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    assert definition1.data() == {"identifier": "foo"}


def test_definition_update_error():
    """Fail to create new definition with non-dictionary element updated."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.data() == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.update("identifier", {"key1": "value1"})


def test_definition_extend():
    """Create new definition from existing definition with extended element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.data() == {"identifier": "foo"}

    definition2 = definition1.extend(
        "requirements", ["bar", "bim >= 1"]
    )
    assert definition2.data() == {
        "identifier": "foo",
        "requirements": ["bar", "bim >= 1"]
    }
    assert definition1.data() == {"identifier": "foo"}

    definition3 = definition2.extend(
        "requirements", ["test"]
    )
    assert definition3.data() == {
        "identifier": "foo",
        "requirements": ["bar", "bim >= 1", "test"]
    }
    assert definition2.data() == {
        "identifier": "foo",
        "requirements": ["bar", "bim >= 1"]
    }
    assert definition1.data() == {"identifier": "foo"}


def test_definition_extend_error():
    """Fail to create new definition with non-list element extended."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.data() == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.extend("identifier", ["test"])


def test_definition_insert():
    """Create new definition from existing definition with extended element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.data() == {"identifier": "foo"}

    definition2 = definition1.set(
        "requirements", ["bar", "bim >= 1"]
    )
    assert definition2.data() == {
        "identifier": "foo",
        "requirements": ["bar", "bim >= 1"]
    }
    assert definition1.data() == {"identifier": "foo"}

    definition3 = definition2.insert(
        "requirements", "test", 0
    )
    assert definition3.data() == {
        "identifier": "foo",
        "requirements": ["test", "bar", "bim >= 1"]
    }
    assert definition2.data() == {
        "identifier": "foo",
        "requirements": ["bar", "bim >= 1"]
    }
    assert definition1.data() == {"identifier": "foo"}


def test_definition_insert_error():
    """Fail to create new definition with non-list element extended."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.data() == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.insert("identifier", ["test"], 0)


def test_definition_remove():
    """Create new definition from existing definition without element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "version": "0.1.0"
    })

    assert definition1.data() == {
        "identifier": "foo",
        "version": "0.1.0"
    }

    definition2 = definition1.remove("version")
    assert definition2.data() == {"identifier": "foo"}
    assert definition1.data() == {
        "identifier": "foo",
        "version": "0.1.0"
    }


def test_definition_remove_non_existing():
    """Do not raise when removing non existing element."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition.data() == {"identifier": "foo"}

    _definition = definition.remove("error")
    assert _definition == definition


def test_definition_remove_key():
    """Create new definition from existing definition without element key."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    })

    assert definition1.data() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }

    definition2 = definition1.remove_key("environ", "key1")
    assert definition2.data() == {
        "identifier": "foo",
        "environ": {
            "key2": "value2"
        }
    }
    assert definition1.data() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }


def test_definition_remove_last_key():
    """Create new definition from existing definition without element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    })

    assert definition1.data() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    }

    definition2 = definition1.remove_key("environ", "key1")
    assert definition2.data() == {
        "identifier": "foo",
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

    assert definition1.data() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    }

    with pytest.raises(ValueError) as error:
        definition1.remove_key("identifier", "key42")

    assert (
       "Impossible to remove key from 'identifier' as it is not a dictionary."
    ) in str(error)


def test_definition_remove_non_existing_key():
    """Do not raise when removing non existing element key."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    })

    assert definition.data() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    }

    _definition = definition.remove_key("test", "error")
    assert definition == _definition

    _definition = definition.remove_key("environ", "key42")
    assert definition == _definition


def test_definition_remove_index():
    """Create new definition from existing definition without element index."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "requirements": ["test", "bar", "bim >= 1"]
    })

    assert definition1.data() == {
        "identifier": "foo",
        "requirements": ["test", "bar", "bim >= 1"]
    }

    definition2 = definition1.remove_index("requirements", 0)
    assert definition2.data() == {
        "identifier": "foo",
        "requirements": ["bar", "bim >= 1"]
    }
    assert definition1.data() == {
        "identifier": "foo",
        "requirements": ["test", "bar", "bim >= 1"]
    }

    definition3 = definition2.remove_index("requirements", 1)
    assert definition3.data() == {
        "identifier": "foo",
        "requirements": ["bar"]
    }
    assert definition2.data() == {
        "identifier": "foo",
        "requirements": ["bar", "bim >= 1"]
    }
    assert definition1.data() == {
        "identifier": "foo",
        "requirements": ["test", "bar", "bim >= 1"]
    }


def test_definition_remove_last_index():
    """Create new definition from existing definition without element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "requirements": ["test"]
    })

    assert definition1.data() == {
        "identifier": "foo",
        "requirements": ["test"]
    }

    definition2 = definition1.remove_index("requirements", 0)
    assert definition2.data() == {
        "identifier": "foo",
    }


def test_definition_remove_index_error():
    """Fail to create definition without un-existing element or element index.
    """
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "requirements": ["test", "bar", "bim >= 1"]
    })

    assert definition1.data() == {
        "identifier": "foo",
        "requirements": ["test", "bar", "bim >= 1"]
    }

    with pytest.raises(ValueError) as error:
        definition1.remove_index("identifier", 42)

    assert (
       "Impossible to remove index from 'identifier' as it is not a list."
    ) in str(error)


def test_definition_remove_non_existing_index():
    """Do not raise when removing non existing element index."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
        "requirements": ["test"]
    })

    assert definition.data() == {
        "identifier": "foo",
        "requirements": ["test"]
    }

    _definition = definition.remove_index("requirements", 5)
    assert definition == _definition

    _definition = definition.remove_index("test", "error")
    assert definition == _definition


def test_definition_variant_set():
    """Create new definition from existing definition with new variant."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    # Add variant
    definition2 = definition1.set(
        "variants", [
            {
                "identifier": "Variant1",
                "requirements": ["bar"]
            },
        ]
    )
    assert definition2.data() == {
        "identifier": "foo",
        "variants": [
            {
                "identifier": "Variant1",
                "requirements": ["bar"]
            },
        ]
    }
    assert definition1.data() == {"identifier": "foo"}

    # Update variant
    definition3 = definition2.set(
        "variants", [
            {
                "identifier": "Test",
                "requirements": ["bar", "bim > 1"]
            }
        ]
    )

    assert definition3.data() == {
        "identifier": "foo",
        "variants": [
            {
                "identifier": "Test",
                "requirements": ["bar", "bim > 1"]
            }
        ]
    }
    assert definition2.data() == {
        "identifier": "foo",
        "variants": [
            {
                "identifier": "Variant1",
                "requirements": ["bar"]
            }
        ]
    }
    assert definition1.data() == {"identifier": "foo"}


def test_definition_non_mutated_input():
    """Ensure that input mapping isn't mutated when creating definition."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "namespace": "foo",
        "description": "This is a definition",
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
        "conditions": ["baz"],
        "variants": [
            {
                "identifier": "Variant1",
                "command": {
                    "appV1": "AppX --test"
                },
                "environ": {
                    "KEY2": "VALUE2"
                },
                "requirements": ["bim >= 9, < 10"]
            }
        ]
    }

    _data = copy.deepcopy(data)
    wiz.definition.Definition(_data)

    assert data == _data
