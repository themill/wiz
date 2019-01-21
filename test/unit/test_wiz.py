# :coding: utf-8

import os

import pytest
from packaging.requirements import Requirement

from wiz._version import __version__
import wiz
import wiz.definition
import wiz.package
import wiz.environ
import wiz.system
import wiz.graph
import wiz.utility
import wiz.exception


@pytest.fixture()
def mocked_registry_defaults(mocker):
    """Return mocked 'wiz.registry.get_default' function."""
    return mocker.patch.object(wiz.registry, "get_defaults")


@pytest.fixture()
def mocked_registry_install_to_path(mocker):
    """Return mocked 'wiz.registry.install_to_path' function."""
    return mocker.patch.object(wiz.registry, "install_to_path")


@pytest.fixture()
def mocked_registry_install_to_vcs(mocker):
    """Return mocked 'wiz.registry.install_to_vcs' function."""
    return mocker.patch.object(wiz.registry, "install_to_vcs")


@pytest.fixture()
def mocked_fetch_definition_mapping(mocker):
    """Return mocked 'wiz.fetch_definition_mapping' function."""
    return mocker.patch.object(wiz, "fetch_definition_mapping")


@pytest.fixture()
def mocked_fetch_package(mocker):
    """Return mocked 'wiz.fetch_package' function."""
    return mocker.patch.object(wiz, "fetch_package")


@pytest.fixture()
def mocked_load_definition(mocker):
    """Return mocked 'wiz.load_definition' function."""
    return mocker.patch.object(wiz, "load_definition")


@pytest.fixture()
def mocked_definition_fetch(mocker):
    """Return mocked 'wiz.definition.fetch' function."""
    return mocker.patch.object(wiz.definition, "fetch")


@pytest.fixture()
def mocked_definition_query(mocker):
    """Return mocked 'wiz.definition.query' function."""
    return mocker.patch.object(wiz.definition, "query")


@pytest.fixture()
def mocked_definition_load(mocker):
    """Return mocked 'wiz.definition.load' function."""
    return mocker.patch.object(wiz.definition, "load")


@pytest.fixture()
def mocked_definition_export(mocker):
    """Return mocked 'wiz.definition.export' function."""
    return mocker.patch.object(wiz.definition, "export")


@pytest.fixture()
def mocked_package_extract(mocker):
    """Return mocked 'wiz.package.extract' function."""
    return mocker.patch.object(wiz.package, "extract")


@pytest.fixture()
def mocked_environ_initiate(mocker):
    """Return mocked 'wiz.environ.initiate' function."""
    return mocker.patch.object(wiz.environ, "initiate")


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
        paths,
        max_depth=options.get("max_depth"),
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
    mocked_registry_defaults, mocked_fetch_definition_mapping,
    mocked_graph_resolver, mocked_environ_initiate,
    mocked_package_extract_context, mocked_utility_encode, mocker, options
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
    mocked_environ_initiate.return_value = "__INITIAL_ENVIRON__"
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

    mocked_registry_defaults.assert_not_called()
    mocked_fetch_definition_mapping.assert_not_called()

    mocked_graph_resolver.assert_called_once_with(
        "__PACKAGE_DEFINITIONS__", 300
    )
    mocked_resolver.compute_packages.assert_called_once_with([
        Requirement(request) for request in requests
    ])

    mocked_environ_initiate.assert_called_once_with(
        options.get("environ_mapping")
    )

    mocked_package_extract_context.assert_called_once_with(
        packages, environ_mapping="__INITIAL_ENVIRON__"
    )


@pytest.mark.parametrize("options", [
    {},
    {"environ_mapping": "__ENVIRON__"},
], ids=[
    "without-environ",
    "with-environ",
])
def test_resolve_context_with_default_definition_mapping(
    mocked_registry_defaults, mocked_fetch_definition_mapping,
    mocked_graph_resolver, mocked_environ_initiate,
    mocked_package_extract_context, mocked_utility_encode, mocker, options
):
    """Get resolved context mapping with default definition mapping."""
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
    mocked_environ_initiate.return_value = "__INITIAL_ENVIRON__"
    mocked_package_extract_context.return_value = context
    mocked_utility_encode.return_value = "__ENCODED_CONTEXT__"
    mocked_registry_defaults.return_value = paths
    mocked_fetch_definition_mapping.return_value = {
        "package": "__PACKAGE_DEFINITIONS__",
        "registries": paths
    }

    result = wiz.resolve_context(requests, **options)

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

    mocked_registry_defaults.asset_called_once()
    mocked_fetch_definition_mapping.asset_called_once_with(paths)

    mocked_graph_resolver.assert_called_once_with(
        "__PACKAGE_DEFINITIONS__", 300
    )
    mocked_resolver.compute_packages.assert_called_once_with([
        Requirement(request) for request in requests
    ])

    mocked_environ_initiate.assert_called_once_with(
        options.get("environ_mapping")
    )

    mocked_package_extract_context.assert_called_once_with(
        packages, environ_mapping="__INITIAL_ENVIRON__"
    )


@pytest.mark.parametrize("options", [
    {},
    {"environ_mapping": "__ENVIRON__"},
], ids=[
    "without-environ",
    "with-environ",
])
def test_resolve_context_with_implicit_packages(
    mocked_registry_defaults, mocked_fetch_definition_mapping,
    mocked_graph_resolver, mocked_environ_initiate,
    mocked_package_extract_context, mocked_utility_encode, mocker, options
):
    """Get resolved context mapping with implicit packages."""
    requests = ["test1 >=10, < 11", "test2", "test3[variant]"]
    implicit = ["foo==0.1.0", "bar==5.2.1"]
    paths = ["/path/to/registry1", "/path/to/registry2"]

    context = {"environ": {"KEY": "VALUE"}, "command": {"app": "APP"}}
    packages = [
        mocker.Mock(identifier="test1"),
        mocker.Mock(identifier="test2"),
        mocker.Mock(identifier="test3")
    ]

    mocked_resolver = mocker.Mock(**{"compute_packages.return_value": packages})
    mocked_graph_resolver.return_value = mocked_resolver
    mocked_environ_initiate.return_value = "__INITIAL_ENVIRON__"
    mocked_package_extract_context.return_value = context
    mocked_utility_encode.return_value = "__ENCODED_CONTEXT__"

    definition_mapping = {
        "package": "__PACKAGE_DEFINITIONS__",
        "registries": paths,
        "implicit-packages": implicit
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

    mocked_registry_defaults.asset_called_once()
    mocked_fetch_definition_mapping.asset_called_once_with(paths)

    mocked_graph_resolver.assert_called_once_with(
        "__PACKAGE_DEFINITIONS__", 300
    )
    mocked_resolver.compute_packages.assert_called_once_with([
        Requirement(request) for request in requests + implicit
    ])

    mocked_environ_initiate.assert_called_once_with(
        options.get("environ_mapping")
    )

    mocked_package_extract_context.assert_called_once_with(
        packages, environ_mapping="__INITIAL_ENVIRON__"
    )


@pytest.mark.parametrize("options", [
    {},
    {"environ_mapping": "__ENVIRON__"},
], ids=[
    "without-environ",
    "with-environ",
])
def test_resolve_context_with_implicit_packages_ignored(
    mocked_registry_defaults, mocked_fetch_definition_mapping,
    mocked_graph_resolver, mocked_environ_initiate,
    mocked_package_extract_context, mocked_utility_encode, mocker, options
):
    """Get resolved context mapping with implicit packages ignored."""
    requests = ["test1 >=10, < 11", "test2", "test3[variant]"]
    implicit = ["foo==0.1.0", "bar==5.2.1"]
    paths = ["/path/to/registry1", "/path/to/registry2"]

    context = {"environ": {"KEY": "VALUE"}, "command": {"app": "APP"}}
    packages = [
        mocker.Mock(identifier="test1"),
        mocker.Mock(identifier="test2"),
        mocker.Mock(identifier="test3")
    ]

    mocked_resolver = mocker.Mock(**{"compute_packages.return_value": packages})
    mocked_graph_resolver.return_value = mocked_resolver
    mocked_environ_initiate.return_value = "__INITIAL_ENVIRON__"
    mocked_package_extract_context.return_value = context
    mocked_utility_encode.return_value = "__ENCODED_CONTEXT__"

    definition_mapping = {
        "package": "__PACKAGE_DEFINITIONS__",
        "registries": paths,
        "implicit-packages": implicit
    }

    options["ignore_implicit"] = True
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

    mocked_registry_defaults.asset_called_once()
    mocked_fetch_definition_mapping.asset_called_once_with(paths)

    mocked_graph_resolver.assert_called_once_with(
        "__PACKAGE_DEFINITIONS__", 300
    )
    mocked_resolver.compute_packages.assert_called_once_with([
        Requirement(request) for request in requests
    ])

    mocked_environ_initiate.assert_called_once_with(
        options.get("environ_mapping")
    )

    mocked_package_extract_context.assert_called_once_with(
        packages, environ_mapping="__INITIAL_ENVIRON__"
    )


def test_resolve_command():
    """Resolve a command from command mapping."""
    elements = ["app", "--option", "value", "/path/to/script"]
    result = wiz.resolve_command(elements, {})
    assert result == elements

    result = wiz.resolve_command(elements, {"app": "App0.1 --modeX"})
    assert result == [
        "App0.1", "--modeX", "--option", "value", "/path/to/script"
    ]


def test_discover_context(
    monkeypatch, mocked_utility_decode, mocked_fetch_definition_mapping,
    mocked_fetch_package, mocked_environ_initiate,
    mocked_package_extract_context,
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
    mocked_environ_initiate.return_value = {"KEY": "VALUE"}
    mocked_package_extract_context.return_value = {
        "command": {},
        "environ": {"KEY": "VALUE"},
    }

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

    mocked_package_extract_context.assert_called_once_with(
        [{"identifier": "package1==0.1.2"}, {"identifier": "package2==1.0.2"}],
        environ_mapping={"KEY": "VALUE"}
    )


def test_discover_context_error(monkeypatch):
    """Fail to discover context from environment variable."""
    monkeypatch.delenv("WIZ_CONTEXT", raising=False)

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.discover_context()


def test_load_definition(mocked_definition_load):
    """Load a definition."""
    wiz.load_definition("/path/to/definition.json")
    mocked_definition_load.assert_called_once_with("/path/to/definition.json")


def test_export_definition(mocked_definition_export):
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
    wiz.export_definition("/path/to/output", definition_data)
    mocked_definition_export.assert_called_once_with(
        "/path/to/output", definition_data, overwrite=False
    )


@pytest.mark.parametrize("options, install_options", [
    (
        {},
        {"overwrite": False}
    ),
    (
        {"overwrite": True},
        {"overwrite": True}
    ),
], ids=[
    "no-options",
    "with-overwrite",
])
def test_install_definitions_to_path(
    mocked_load_definition, mocked_registry_install_to_path,
    options, install_options
):
    """Install definitions to a path registry."""
    definitions = [
        wiz.definition.Definition({"identifier": "foo"}),
        wiz.definition.Definition({"identifier": "bar"})
    ]
    mocked_load_definition.side_effect = definitions

    wiz.install_definitions(
        ["/path/to/foo.json", "/path/to/bar.json"],
        "/path/to/registry", **options
    )

    mocked_registry_install_to_path.assert_called_once_with(
        definitions, "/path/to/registry", **install_options
    )


def test_install_definitions_to_path_with_install_location(
    mocked_load_definition, mocked_registry_install_to_path,
):
    """Install definitions to a path registry with install location."""
    definitions = [
        wiz.definition.Definition({"identifier": "foo"}),
        wiz.definition.Definition({"identifier": "bar"})
    ]
    mocked_load_definition.side_effect = definitions

    wiz.install_definitions(
        ["/path/to/foo.json", "/path/to/bar.json"],
        "/path/to/registry",
    )

    _definitions = [
        wiz.definition.Definition({
            "identifier": "foo"
        }),
        wiz.definition.Definition({
            "identifier": "bar"
        })
    ]

    mocked_registry_install_to_path.assert_called_once_with(
        _definitions, "/path/to/registry", overwrite=False
    )


@pytest.mark.parametrize("options, install_options", [
    (
        {},
        {"overwrite": False}
    ),
    (
        {"overwrite": True},
        {"overwrite": True}
    ),
], ids=[
    "no-options",
    "with-overwrite",
])
def test_install_definitions_to_vcs(
    mocked_load_definition, mocked_registry_install_to_vcs,
    options, install_options
):
    """Install definitions to a vcs registry."""
    definitions = [
        wiz.definition.Definition({"identifier": "foo"}),
        wiz.definition.Definition({"identifier": "bar"})
    ]
    mocked_load_definition.side_effect = definitions

    wiz.install_definitions(
        ["/path/to/foo.json", "/path/to/bar.json"],
        "wiz://registry-id", **options
    )

    mocked_registry_install_to_vcs.assert_called_once_with(
        definitions, "wiz://registry-id", **install_options
    )


def test_install_definitions_to_vcs_with_install_location(
    mocked_load_definition, mocked_registry_install_to_vcs,
):
    """Install definitions to a vcs registry with install location."""
    definitions = [
        wiz.definition.Definition({"identifier": "foo"}),
        wiz.definition.Definition({"identifier": "bar"})
    ]
    mocked_load_definition.side_effect = definitions

    wiz.install_definitions(
        ["/path/to/foo.json", "/path/to/bar.json"],
        "wiz://registry-id",
    )

    _definitions = [
        wiz.definition.Definition({
            "identifier": "foo"
        }),
        wiz.definition.Definition({
            "identifier": "bar"
        })
    ]

    mocked_registry_install_to_vcs.assert_called_once_with(
        _definitions, "wiz://registry-id", overwrite=False
    )


@pytest.fixture()
def packages(request, mocker):
    """Return mocked packages as specified by *request.param*."""
    if request.param is None:
        return

    return [
        mocker.Mock(identifier=identifier) for identifier
        in request.param
    ]


@pytest.mark.parametrize("options, packages, expected", [
    (
        {"environ": {"KEY": "VALUE"}},
        None,
        (
            "#!/bin/tcsh -f\n"
            "setenv KEY \"VALUE\"\n"
        )
    ),
    (
        {"environ": {"PATH": "/path/to/bin"}},
        None,
        (
            "#!/bin/tcsh -f\n"
            "setenv PATH \"/path/to/bin:${PATH}\"\n"
        )
    ),
    (
        {"environ": {"KEY": "VALUE"}, "command": "App0.1"},
        None,
        (
            "#!/bin/tcsh -f\n"
            "setenv KEY \"VALUE\"\n"
            "App0.1 $argv:q\n"
        )
    ),
    (
        {"environ": {"KEY": "VALUE"}},
        ["package1", "package2", "package3"],
        (
            "#!/bin/tcsh -f\n"
            "#\n"
            "# Generated by wiz with the following environments:\n"
            "# - package1\n"
            "# - package2\n"
            "# - package3\n"
            "#\n"
            "setenv KEY \"VALUE\"\n"
        )
    ),
    (
        {"environ": {"KEY": "VALUE"}, "command": "App -x"},
        ["packageA", "packageB"],
        (
            "#!/bin/tcsh -f\n"
            "#\n"
            "# Generated by wiz with the following environments:\n"
            "# - packageA\n"
            "# - packageB\n"
            "#\n"
            "setenv KEY \"VALUE\"\n"
            "App -x $argv:q\n"
        )
    )
], ids=[
    "minimal",
    "with-path",
    "with-command",
    "with-packages",
    "with-command-and-packages",
], indirect=[
    "packages"
])
def test_export_csh_script(temporary_directory, options, packages, expected):
    """Export CSH script."""
    options.update({"packages": packages})

    wiz.export_script(
        temporary_directory, "tcsh", "foo", **options
    )

    file_path = os.path.join(temporary_directory, "foo")
    assert os.path.isfile(file_path) is True

    with open(file_path, "r") as stream:
        assert stream.read() == expected


def test_export_csh_script_environ_error(temporary_directory):
    """Fail to export CSH script with empty environment mapping."""
    with pytest.raises(ValueError) as error:
        wiz.export_script(temporary_directory, "tcsh", "foo", {})

    assert "The environment mapping should not be empty." in str(error)


@pytest.mark.parametrize("options, packages, expected", [
    (
        {"environ": {"KEY": "VALUE"}},
        None,
        (
            "#!/bin/bash\n"
            "export KEY=\"VALUE\"\n"
        )
    ),
    (
        {"environ": {"PATH": "/path/to/bin"}},
        None,
        (
            "#!/bin/bash\n"
            "export PATH=\"/path/to/bin:${PATH}\"\n"
        )
    ),
    (
        {"environ": {"KEY": "VALUE"}, "command": "App0.1"},
        None,
        (
            "#!/bin/bash\n"
            "export KEY=\"VALUE\"\n"
            "App0.1 $@\n"
        )
    ),
    (
        {"environ": {"KEY": "VALUE"}},
        ["package1", "package2", "package3"],
        (
            "#!/bin/bash\n"
            "#\n"
            "# Generated by wiz with the following environments:\n"
            "# - package1\n"
            "# - package2\n"
            "# - package3\n"
            "#\n"
            "export KEY=\"VALUE\"\n"
        )
    ),
    (
        {"environ": {"KEY": "VALUE"}, "command": "App -x"},
        ["packageA", "packageB"],
        (
            "#!/bin/bash\n"
            "#\n"
            "# Generated by wiz with the following environments:\n"
            "# - packageA\n"
            "# - packageB\n"
            "#\n"
            "export KEY=\"VALUE\"\n"
            "App -x $@\n"
        )
    )
], ids=[
    "minimal",
    "with-path",
    "with-command",
    "with-packages",
    "with-command-and-packages",
], indirect=[
    "packages"
])
def test_export_bash_script(temporary_directory, options, packages, expected):
    """Export Bash script."""
    options.update({"packages": packages})

    wiz.export_script(
        temporary_directory, "bash", "foo", **options
    )

    file_path = os.path.join(temporary_directory, "foo")
    assert os.path.isfile(file_path) is True

    with open(file_path, "r") as stream:
        assert stream.read() == expected


def test_export_bash_script_environ_error(temporary_directory):
    """Fail to export Bash script with empty environment mapping."""
    with pytest.raises(ValueError) as error:
        wiz.export_script(temporary_directory, "bash", "foo", {})

    assert "The environment mapping should not be empty." in str(error)


def test_export_script_error(temporary_directory):
    """Fail to export script with incorrect type."""
    with pytest.raises(ValueError) as error:
        wiz.export_script(
            temporary_directory, "duh", "foo",
            {"KEY": "VALUE"}
        )

    assert "'duh' is not a valid script type." in str(error)
