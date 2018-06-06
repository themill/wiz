# :coding: utf-8

import os

import pytest
from packaging.requirements import Requirement

from wiz._version import __version__
import wiz
import wiz.definition
import wiz.package
import wiz.system
import wiz.graph
import wiz.utility
import wiz.exception


@pytest.fixture()
def mocked_fetch_definition_mapping(mocker):
    """Return mocked 'wiz.fetch_definition_mapping' function."""
    return mocker.patch.object(wiz, "fetch_definition_mapping")


@pytest.fixture()
def mocked_fetch_package(mocker):
    """Return mocked 'wiz.fetch_package' function."""
    return mocker.patch.object(wiz, "fetch_package")


@pytest.fixture()
def mocked_definition_fetch(mocker):
    """Return mocked 'wiz.definition.fetch' function."""
    return mocker.patch.object(wiz.definition, "fetch")


@pytest.fixture()
def mocked_definition_query(mocker):
    """Return mocked 'wiz.definition.query' function."""
    return mocker.patch.object(wiz.definition, "query")


@pytest.fixture()
def mocked_package_extract(mocker):
    """Return mocked 'wiz.package.extract' function."""
    return mocker.patch.object(wiz.package, "extract")


@pytest.fixture()
def mocked_package_initiate_environ(mocker):
    """Return mocked 'wiz.package.initiate_environ' function."""
    return mocker.patch.object(wiz.package, "initiate_environ")


@pytest.fixture()
def mocked_package_extract_context(mocker):
    """Return mocked 'wiz.package.extract_context' function."""
    return mocker.patch.object(wiz.package, "extract_context")


@pytest.fixture()
def mocked_system_query(mocker):
    """Return mocked 'wiz.definition.fetch' function."""
    return mocker.patch.object(wiz.system, "query")


@pytest.fixture()
def mocked_graph_resolver(mocker):
    """Return mocked 'wiz.graph.Resolver' class constructor."""
    return mocker.patch.object(wiz.graph, "Resolver")


@pytest.fixture()
def mocked_utility_encode(mocker):
    """Return mocked 'wiz.utility.encode' function."""
    return mocker.patch.object(wiz.utility, "encode")


@pytest.fixture()
def mocked_utility_decode(mocker):
    """Return mocked 'wiz.utility.decode' function."""
    return mocker.patch.object(wiz.utility, "decode")


@pytest.mark.parametrize("options", [
    {},
    {"max_depth": 2},
    {"system_mapping": "__CUSTOM_SYSTEM_MAPPING__"}
], ids=[
    "paths-only",
    "with-max-depth",
    "with-system-mapping",
])
def test_fetch_definition_mapping(
    mocked_definition_fetch, mocked_system_query, options
):
    """Fetch mapping from all definitions available."""
    paths = ["/path/to/registry1", "/path/to/registry2"]
    default_system_mapping = "__SYSTEM_MAPPING__"
    definition_mapping = {"command": {}, "package": {}}

    mocked_system_query.return_value = default_system_mapping
    mocked_definition_fetch.return_value = definition_mapping

    result = wiz.fetch_definition_mapping(paths, **options)

    definition_mapping.update({"registries": paths})
    assert result == definition_mapping

    mocked_definition_fetch.assert_called_once_with(
        paths, max_depth=options.get("max_depth"),
        system_mapping=options.get("system_mapping", default_system_mapping)
    )

    if options.get("system_mapping"):
        mocked_system_query.assert_not_called()
    else:
        mocked_system_query.assert_called_once()


def test_fetch_definition(mocked_definition_query):
    """Fetch definition."""
    request = "test >= 10"
    definition_mapping = {
        "command": "__COMMAND_MAPPING__",
        "package": "__PACKAGE_MAPPING__"
    }

    wiz.fetch_definition(request, definition_mapping)
    mocked_definition_query.assert_called_once_with(
        Requirement(request), "__PACKAGE_MAPPING__"
    )


def test_fetch_package(mocked_package_extract):
    """Fetch package."""
    request = "test[variant] >= 10"
    definition_mapping = {
        "command": "__COMMAND_MAPPING__",
        "package": "__PACKAGE_MAPPING__"
    }

    wiz.fetch_package(request, definition_mapping)
    mocked_package_extract.assert_called_once_with(
        Requirement(request), "__PACKAGE_MAPPING__"
    )


def test_fetch_package_request_from_command():
    """Fetch package request corresponding to command."""
    definition_mapping = {
        "command": {"app": "test"},
        "package": {
            "test": {
                "0.1.0": "__PACKAGE_DEFINITION__"
            }
        }
    }

    assert wiz.fetch_package_request_from_command(
        "app", definition_mapping
    ) == "test"

    assert wiz.fetch_package_request_from_command(
        "app >=10", definition_mapping
    ) == "test >=10"

    assert wiz.fetch_package_request_from_command(
        "app[variant]", definition_mapping
    ) == "test[variant]"

    assert wiz.fetch_package_request_from_command(
        "app[variant] ==10.0.*", definition_mapping
    ) == "test[variant] ==10.0.*"

    assert wiz.fetch_package_request_from_command(
        "app[variant] >1, <2", definition_mapping
    ) == "test[variant] >1, <2"


def test_fetch_package_request_from_command_error():
    """Fail to fetch package request corresponding to command."""
    definition_mapping = {
        "command": {},
    }

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.fetch_package_request_from_command("app", definition_mapping)


@pytest.mark.parametrize("options", [
    {},
    {"environ_mapping": "__ENVIRON__"},
], ids=[
    "without-environ",
    "with-environ",
])
def test_resolve_context(
    mocked_graph_resolver, mocked_package_initiate_environ,
    mocked_package_extract_context, mocked_utility_encode,
    mocker, options
):
    """Get resolved context mapping."""
    requests = ["test1 >=10, < 11", "test2", "test3[variant]"]
    paths = ["/path/to/registry1", "/path/to/registry2"]

    context = {"environ": {"KEY": "VALUE"}, "command": {"app": "APP"}}
    packages = [
        mocker.Mock(identifier="test1"),
        mocker.Mock(identifier="test2"),
        mocker.Mock(identifier="test3")
    ]

    mocked_resolver = mocker.Mock(**{"compute_packages.return_value": packages})
    mocked_graph_resolver.return_value = mocked_resolver
    mocked_package_initiate_environ.return_value = "__INITIAL_ENVIRON__"
    mocked_package_extract_context.return_value = context
    mocked_utility_encode.return_value = "__ENCODED_CONTEXT__"

    definition_mapping = {
        "package": "__PACKAGE_DEFINITIONS__",
        "registries": paths
    }

    result = wiz.resolve_context(requests, definition_mapping, **options)

    assert result == {
        "environ": {
            "KEY": "VALUE",
            "WIZ_VERSION": __version__,
            "WIZ_CONTEXT": "__ENCODED_CONTEXT__"
        },
        "command": {"app": "APP"},
        "packages": packages,
        "registries": paths
    }

    mocked_graph_resolver.assert_called_once_with("__PACKAGE_DEFINITIONS__")
    mocked_resolver.compute_packages.assert_called_once_with([
        Requirement(request) for request in requests
    ])

    mocked_package_initiate_environ.assert_called_once_with(
        options.get("environ_mapping")
    )

    mocked_package_extract_context.assert_called_once_with(
        packages, environ_mapping="__INITIAL_ENVIRON__"
    )


def test_resolve_command():
    """Resolve a command from command mapping."""
    command = "app --option value /path/to/script"
    result = wiz.resolve_command(command, {})
    assert result == command

    result = wiz.resolve_command(command, {"app": "App0.1 --modeX"})
    assert result == "App0.1 --modeX --option value /path/to/script"


def test_discover_context(
    monkeypatch, mocked_utility_decode, mocked_fetch_definition_mapping,
    mocked_fetch_package, mocked_package_initiate_environ
):
    """Discover context from environment variable."""
    monkeypatch.setenv("WIZ_CONTEXT", "__CONTEXT__")

    paths = ["/path/to/registry1", "/path/to/registry2"]
    package_identifiers = ["package1==0.1.2", "package2==1.0.2"]
    mocked_utility_decode.return_value = [package_identifiers, paths]
    mocked_fetch_definition_mapping.return_value = "__DEFINITION_MAPPING__"
    mocked_fetch_package.side_effect = [
        {"identifier": "package1==0.1.2"}, {"identifier": "package2==1.0.2"}
    ]
    mocked_package_initiate_environ.return_value = {"KEY": "VALUE"}

    result = wiz.discover_context()
    assert result == {
        "registries": paths,
        "command": {},
        "environ": {"KEY": "VALUE"},
        "packages": [
            {"identifier": "package1==0.1.2"},
            {"identifier": "package2==1.0.2"}
        ]
    }

    mocked_utility_decode.assert_called_once_with("__CONTEXT__")
    mocked_fetch_definition_mapping.assert_called_once_with(paths)

    assert mocked_fetch_package.call_count == 2
    mocked_fetch_package.assert_any_call(
        package_identifiers[0], "__DEFINITION_MAPPING__"
    )
    mocked_fetch_package.assert_any_call(
        package_identifiers[1], "__DEFINITION_MAPPING__"
    )


def test_discover_context_error(monkeypatch):
    """Fail to discover context from environment variable."""
    monkeypatch.delenv("WIZ_CONTEXT", raising=False)

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.discover_context()


def test_export_definition(temporary_directory):
    """Export a definition to file."""
    definition_data = {
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
    wiz.export_definition(temporary_directory, definition_data)

    file_path = os.path.join(temporary_directory, "foo.json")
    assert os.path.isfile(file_path) is True

    with open(file_path, "r") as stream:
        assert stream.read() == (
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


def test_export_definition_with_version(temporary_directory):
    """Export a definition to file with version."""
    definition_data = {
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
    wiz.export_definition(temporary_directory, definition_data)

    file_path = os.path.join(temporary_directory, "foo-0.1.0.json")
    assert os.path.isfile(file_path) is True

    with open(file_path, "r") as stream:
        assert stream.read() == (
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


def test_export_definition_path_error():
    """Fail to export definition when path is incorrect."""
    definition_data = {
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

    with pytest.raises(OSError):
        wiz.export_definition("/incorrect", definition_data)


def test_export_definition_data_error():
    """Fail to export definition when data is incorrect."""
    definition_data = {
        "identifier": "foo",
        "other": "boo!"
    }

    with pytest.raises(wiz.exception.IncorrectDefinition):
        wiz.export_definition("/incorrect", definition_data)


def test_export_csh_script(temporary_directory):
    """Export CSH script."""
    wiz.export_script(temporary_directory, "csh", "foo", {"KEY": "VALUE"})

    file_path = os.path.join(temporary_directory, "foo")
    assert os.path.isfile(file_path) is True

    with open(file_path, "r") as stream:
        assert stream.read() == (
            "#!/bin/tcsh -f\n"
            "setenv KEY \"VALUE\"\n"
        )
