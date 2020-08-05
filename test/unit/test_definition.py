# :coding: utf-8

import copy
import itertools
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
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defF.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defE.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r2}
    )

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r2}
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
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r2}
    )

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r2}
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
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defF.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defE.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r2}
    )

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r2}
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
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "defC.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defF.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r1, "level1", "level2", "level3", "defE.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r1}
    )

    path = os.path.join(r2, "defH.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r2}
    )

    path = os.path.join(r2, "defI.json")
    mocked_load.assert_any_call(
        path, mapping={"registry": r2}
    )

    assert discovered == []


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
    mocked_definition.assert_called_once_with(
        **{
            "definition-location": temporary_file,
            "identifier": "test_definition"
        }
    )


def test_load_with_mapping(mocked_definition, temporary_file):
    """Load a definition from a path and a mapping."""
    with open(temporary_file, "w") as stream:
        stream.write("{\"identifier\": \"test_definition\"}")

    mocked_definition.return_value = "DEFINITION"
    result = wiz.definition.load(temporary_file, mapping={"key": "value"})
    assert result == "DEFINITION"
    mocked_definition.assert_called_once_with(
        **{
            "definition-location": temporary_file,
            "identifier": "test_definition",
            "key": "value"
        }
    )


def test_definition_mapping():
    """Create definition and return mapping and serialized mapping."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "namespace": "foo",
        "description": "This is a definition",
        "registry": "/path/to/registry",
        "definition-location": "/path/to/registry/test-0.1.0.json",
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

    environment = wiz.definition.Definition(data)

    assert environment.to_dict() == {
        "identifier": "test",
        "version": Version("0.1.0"),
        "namespace": "foo",
        "description": "This is a definition",
        "registry": "/path/to/registry",
        "definition-location": "/path/to/registry/test-0.1.0.json",
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
        "conditions": [Requirement("baz")],
        "variants": [
            {
                "identifier": "Variant1",
                "command": {
                    "appV1": "AppX --test"
                },
                "environ": {
                    "KEY2": "VALUE2"
                },
                "requirements": [Requirement("bim >= 9, < 10")]
            }
        ]
    }

    assert environment.encode() == (
        "{\n"
        "    \"identifier\": \"test\",\n"
        "    \"version\": \"0.1.0\",\n"
        "    \"namespace\": \"foo\",\n"
        "    \"description\": \"This is a definition\",\n"
        "    \"registry\": \"/path/to/registry\",\n"
        "    \"definition-location\": \"/path/to/registry/test-0.1.0.json\",\n"
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
        "        \"foo\"\n"
        "    ],\n"
        "    \"conditions\": [\n"
        "        \"baz\"\n"
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
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.version == "-"
    assert definition.namespace is None
    assert definition.description == "-"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_dict() == OrderedDict([
        ("identifier", "test"),
    ])


def test_minimal_definition_with_namespace():
    """Create a minimal definition with namespace."""
    data = {
        "identifier": "test",
        "namespace": "foo",
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.qualified_identifier == "foo::test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "foo::test"
    assert definition.version == "-"
    assert definition.namespace == "foo"
    assert definition.description == "-"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_dict() == OrderedDict([
        ("identifier", "test"),
        ("namespace", "foo"),
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
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test==0.1.0"
    assert definition.qualified_version_identifier == "test==0.1.0"
    assert definition.version == Version("0.1.0")
    assert definition.namespace is None
    assert definition.description == "-"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_dict(**options) == OrderedDict([
        ("identifier", "test"),
        ("version", expected_version),
    ])


@pytest.mark.parametrize("options, expected_version", [
    ({}, Version("0.1.0")),
    ({"serialize_content": True}, "0.1.0")
], ids=[
    "non-serialized",
    "serialized",
])
def test_definition_with_version_and_namespace(options, expected_version):
    """Create a definition with version and namespace."""
    data = {
        "identifier": "test",
        "namespace": "foo",
        "version": "0.1.0",
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.qualified_identifier == "foo::test"
    assert definition.version_identifier == "test==0.1.0"
    assert definition.qualified_version_identifier == "foo::test==0.1.0"
    assert definition.version == Version("0.1.0")
    assert definition.namespace == "foo"
    assert definition.description == "-"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.conditions == []
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []

    assert definition.to_ordered_dict(**options) == OrderedDict([
        ("identifier", "test"),
        ("version", expected_version),
        ("namespace", "foo"),
    ])


def test_definition_with_description():
    """Create a definition with description."""
    data = {
        "identifier": "test",
        "description": "This is a definition"
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.version == "-"
    assert definition.namespace is None
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.conditions == []
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
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.version == "-"
    assert definition.namespace is None
    assert definition.description == "This is a definition"
    assert definition.requirements == []
    assert definition.conditions == []
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
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.version == "-"
    assert definition.namespace is None
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []
    assert definition.conditions == []
    assert definition.requirements == [
        Requirement("envA >= 1.0.0"),
        Requirement("envB >= 3.4.2, < 4"),
        Requirement("envC")
    ]

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


def test_definition_with_conditions():
    """Create a definition with conditions."""
    data = {
        "identifier": "test",
        "description": "This is a definition",
        "conditions": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }

    definition = wiz.definition.Definition(data)
    assert definition.identifier == "test"
    assert definition.version == "-"
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.system == {}
    assert definition.variants == []
    assert definition.conditions == [
        Requirement("envA >= 1.0.0"),
        Requirement("envB >= 3.4.2, < 4"),
        Requirement("envC")
    ]
    assert definition.requirements == []

    assert definition.to_ordered_dict(serialize_content=True) == OrderedDict([
        ("identifier", "test"),
        ("description", "This is a definition"),
        ("conditions", [
            "envA >=1.0.0",
            "envB >=3.4.2, <4",
            "envC"
        ])
    ])

    for requirement in definition.to_ordered_dict()["conditions"]:
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
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.version == "-"
    assert definition.namespace is None
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.requirements == []
    assert definition.conditions == []
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
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.version == "-"
    assert definition.namespace is None
    assert definition.description == "This is a definition"
    assert definition.environ == {}
    assert definition.command == {}
    assert definition.requirements == []
    assert definition.conditions == []
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
    assert definition.qualified_identifier == "test"
    assert definition.version_identifier == "test"
    assert definition.qualified_version_identifier == "test"
    assert definition.version == "-"
    assert definition.namespace is None
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
        assert variant.requirements == [
            Requirement(req) for req in variant_data.get("requirements", [])
        ]

    assert definition.to_ordered_dict(serialize_content=True) == OrderedDict([
        ("identifier", "test"),
        ("description", "This is a definition"),
        ("variants", [
            OrderedDict([
                ("identifier", "1.0"),
                ("environ", {"VERSION": "1.0"}),
                ("requirements", ["envA >=1.0, <2"])
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


def test_definition_with_error():
    """Fail to create a definition with error."""
    data = {}

    with pytest.raises(wiz.exception.IncorrectDefinition) as error:
        wiz.definition.Definition(data)

    assert (
        "IncorrectDefinition: u'identifier' is a required property (/)"
    ) in str(error)


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


def test_definition_with_condition_error():
    """Fail to create a definition with incorrect condition."""
    data = {
        "identifier": "test",
        "conditions": [
            "envA -!!!",
        ]
    }

    with pytest.raises(wiz.exception.IncorrectDefinition) as error:
        wiz.definition.Definition(data)

    assert (
        "IncorrectDefinition: The definition 'test' contains an incorrect "
        "package condition [The requirement 'envA -!!!' is incorrect]"
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


def test_definition_with_variant_condition_error():
    """Fail to create a definition with incorrect variant condition."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "1.0",
                "conditions": [
                    "envA -!!!"
                ]
            }
        ]
    }

    with pytest.raises(wiz.exception.IncorrectDefinition) as error:
        wiz.definition.Definition(data)

    assert (
        "IncorrectDefinition: Additional properties are not allowed "
        "('conditions' was unexpected) (/variants/0)"
    ) in str(error)


def test_definition_set():
    """Create new definition from existing definition with new element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict() == {"identifier": "foo"}

    # Change identifier
    definition2 = definition1.set("identifier", "bar")
    assert definition2.to_dict() == {"identifier": "bar"}
    assert definition1.to_dict() == {"identifier": "foo"}

    # Add version
    definition3 = definition2.set("version", "0.1.0")
    assert definition3.to_dict() == {
        "identifier": "bar",
        "version": Version("0.1.0")
    }
    assert definition2.to_dict() == {"identifier": "bar"}
    assert definition1.to_dict() == {"identifier": "foo"}


def test_definition_update():
    """Create new definition from existing definition with updated element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict() == {"identifier": "foo"}

    definition2 = definition1.update(
        "environ", {"key1": "value1", "key2": "value2"}
    )
    assert definition2.to_dict() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    assert definition1.to_dict() == {"identifier": "foo"}

    definition3 = definition2.update(
        "environ", {"key1": "VALUE1", "key3": "value3"}
    )
    assert definition3.to_dict() == {
        "identifier": "foo",
        "environ": {
            "key1": "VALUE1",
            "key2": "value2",
            "key3": "value3"
        }
    }
    assert definition2.to_dict() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    assert definition1.to_dict() == {"identifier": "foo"}


def test_definition_update_error():
    """Fail to create new definition with non-dictionary element updated."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict() == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.update("identifier", {"key1": "value1"})


def test_definition_extend():
    """Create new definition from existing definition with extended element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict() == {"identifier": "foo"}

    definition2 = definition1.extend(
        "requirements", ["bar", "bim>=1"]
    )
    assert definition2.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert definition1.to_dict() == {"identifier": "foo"}

    definition3 = definition2.extend(
        "requirements", ["test"]
    )
    assert definition3.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1"),
            Requirement("test")
        ]
    }
    assert definition2.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert definition1.to_dict() == {"identifier": "foo"}


def test_definition_extend_error():
    """Fail to create new definition with non-list element extended."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict() == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.extend("identifier", ["test"])


def test_definition_insert():
    """Create new definition from existing definition with extended element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict() == {"identifier": "foo"}

    definition2 = definition1.set(
        "requirements", ["bar", "bim>=1"]
    )
    assert definition2.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert definition1.to_dict() == {"identifier": "foo"}

    definition3 = definition2.insert(
        "requirements", "test", 0
    )
    assert definition3.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert definition2.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert definition1.to_dict() == {"identifier": "foo"}


def test_definition_insert_error():
    """Fail to create new definition with non-list element extended."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition1.to_dict() == {"identifier": "foo"}

    with pytest.raises(ValueError):
        definition1.insert("identifier", ["test"], 0)


def test_definition_remove():
    """Create new definition from existing definition without element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "version": "0.1.0"
    })

    assert definition1.to_dict() == {
        "identifier": "foo",
        "version": Version("0.1.0")
    }

    definition2 = definition1.remove("version")
    assert definition2.to_dict() == {"identifier": "foo"}
    assert definition1.to_dict() == {
        "identifier": "foo",
        "version": Version("0.1.0")
    }


def test_definition_remove_non_existing():
    """Do not raise when removing non existing element."""
    definition = wiz.definition.Definition({
        "identifier": "foo",
    })

    assert definition.to_dict() == {"identifier": "foo"}

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

    assert definition1.to_dict() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
            "key2": "value2"
        }
    }

    definition2 = definition1.remove_key("environ", "key1")
    assert definition2.to_dict() == {
        "identifier": "foo",
        "environ": {
            "key2": "value2"
        }
    }
    assert definition1.to_dict() == {
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

    assert definition1.to_dict() == {
        "identifier": "foo",
        "environ": {
            "key1": "value1",
        }
    }

    definition2 = definition1.remove_key("environ", "key1")
    assert definition2.to_dict() == {
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

    assert definition1.to_dict() == {
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

    assert definition.to_dict() == {
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
        "requirements": [
            "test",
            "bar",
            "bim >=1"
        ]
    })

    assert definition1.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }

    definition2 = definition1.remove_index("requirements", 0)
    assert definition2.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert definition1.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }

    definition3 = definition2.remove_index("requirements", 1)
    assert definition3.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("bar"),
        ]
    }
    assert definition2.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }
    assert definition1.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
    }


def test_definition_remove_last_index():
    """Create new definition from existing definition without element."""
    definition1 = wiz.definition.Definition({
        "identifier": "foo",
        "requirements": [
            "test",
        ]
    })

    assert definition1.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("test"),
        ]
    }

    definition2 = definition1.remove_index("requirements", 0)
    assert definition2.to_dict() == {
        "identifier": "foo",
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

    assert definition1.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("test"),
            Requirement("bar"),
            Requirement("bim >=1")
        ]
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
        "requirements": [
            "test",
        ]
    })

    assert definition.to_dict() == {
        "identifier": "foo",
        "requirements": [
            Requirement("test"),
        ]
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
                "requirements": [
                    Requirement("bar")
                ]
            },
        ]
    )
    assert definition2.to_dict() == {
        "identifier": "foo",
        "variants": [
            {
                "identifier": "Variant1",
                "requirements": [
                    Requirement("bar")
                ]
            },
        ]
    }
    assert definition1.to_dict() == {"identifier": "foo"}

    # Update variant
    variant = definition2.variants[0].extend("requirements", ["bim > 1"])
    variant = variant.set("identifier", "Test")

    definition3 = definition2.set(
        "variants", [variant]
    )
    assert definition3.to_dict() == {
        "identifier": "foo",
        "variants": [
            {
                "identifier": "Test",
                "requirements": [
                    Requirement("bar"),
                    Requirement("bim > 1")
                ]
            },
        ]
    }
    assert definition2.to_dict() == {
        "identifier": "foo",
        "variants": [
            {
                "identifier": "Variant1",
                "requirements": [
                    Requirement("bar")
                ]
            },
        ]
    }
    assert definition1.to_dict() == {"identifier": "foo"}


def test_definition_non_mutated_input():
    """Ensure that input mapping isn't mutated when creating definition."""
    data = {
        "identifier": "test",
        "version": "0.1.0",
        "namespace": "foo",
        "description": "This is a definition",
        "registry": "/path/to/registry",
        "definition-location": "/path/to/registry/test-0.1.0.json",
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
