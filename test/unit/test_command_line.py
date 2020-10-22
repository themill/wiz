# :coding: utf-8

import datetime
import os
import tempfile

import click
import pytest
from click.testing import CliRunner
from six.moves import reload_module

import wiz.command_line
import wiz.config
import wiz.definition
import wiz.exception
import wiz.filesystem
import wiz.history
import wiz.package
import wiz.registry
import wiz.spawn
import wiz.symbol
import wiz.utility


@pytest.fixture(autouse=True)
def reset_configuration(mocker):
    """Ensure that no personal configuration is fetched during tests."""
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.command_line._CONFIG = wiz.config.fetch(refresh=True)
    reload_module(wiz.command_line)


@pytest.fixture()
def mock_datetime_now(mocker):
    """Return mocked 'wiz.fetch_definition_mapping' function."""
    _date = mocker.Mock(**{"isoformat.return_value": "NOW"})
    return mocker.patch.object(
        datetime, "datetime", **{"now.return_value": _date}
    )


@pytest.fixture()
def mocked_click_edit(mocker):
    """Return mocked 'click.edit' function."""
    return mocker.patch.object(click, "edit")


@pytest.fixture()
def mocked_click_prompt(mocker):
    """Return mocked 'click.prompt' function."""
    return mocker.patch.object(click, "prompt")


@pytest.fixture()
def mocked_click_confirm(mocker):
    """Return mocked 'click.confirm' function."""
    return mocker.patch.object(click, "confirm")


@pytest.fixture()
def mocked_fetch_definition_mapping(mocker):
    """Return mocked 'wiz.fetch_definition_mapping' function."""
    return mocker.patch.object(wiz, "fetch_definition_mapping")


@pytest.fixture()
def mocked_load_definition(mocker):
    """Return mocked 'wiz.load_definition' function."""
    return mocker.patch.object(wiz, "load_definition")


@pytest.fixture()
def mocked_resolve_context(mocker):
    """Return mocked 'wiz.resolve_context' function."""
    return mocker.patch.object(wiz, "resolve_context")


@pytest.fixture()
def mocked_resolve_command(mocker):
    """Return mocked 'wiz.resolve_command' function."""
    return mocker.patch.object(wiz, "resolve_command")


@pytest.fixture()
def mocked_fetch_package_request_from_command(mocker):
    """Return mocked 'wiz.fetch_package_request_from_command' function."""
    return mocker.patch.object(wiz, "fetch_package_request_from_command")


@pytest.fixture()
def mocked_export_definition(mocker):
    """Return mocked 'wiz.export_definition' function."""
    return mocker.patch.object(wiz, "export_definition")


@pytest.fixture()
def mocked_export_script(mocker):
    """Return mocked 'wiz.export_script' function."""
    return mocker.patch.object(wiz, "export_script")


@pytest.fixture()
def mocked_definition_discover(mocker):
    """Return mocked 'wiz.definition.discover' function."""
    return mocker.patch.object(wiz.definition, "discover")


@pytest.fixture()
def mocked_history_start_recording(mocker):
    """Return mocked 'wiz.history.start_recording' function."""
    return mocker.patch.object(wiz.history, "start_recording")


@pytest.fixture()
def mocked_history_record_action(mocker):
    """Return mocked 'wiz.history.record_action' function."""
    return mocker.patch.object(wiz.history, "record_action")


@pytest.fixture()
def mocked_history_get(mocker):
    """Return mocked 'wiz.history.get' function."""
    return mocker.patch.object(wiz.history, "get")


@pytest.fixture()
def mocked_spawn_execute(mocker):
    """Return mocked 'wiz.spawn.execute' function."""
    return mocker.patch.object(wiz.spawn, "execute")


@pytest.fixture()
def mocked_spawn_shell(mocker):
    """Return mocked 'wiz.spawn.shell' function."""
    return mocker.patch.object(wiz.spawn, "shell")


@pytest.fixture()
def mocked_filesystem_export(mocker):
    """Return mocked 'wiz.filesystem.export' function."""
    return mocker.patch.object(wiz.filesystem, "export")


@pytest.fixture()
def mocked_system_query(mocker):
    """Return mocked 'wiz.system.query' function."""
    return mocker.patch.object(wiz.system, "query")


@pytest.fixture()
def mocked_registry_fetch(mocker):
    """Return mocked 'wiz.registry.fetch' function."""
    return mocker.patch.object(wiz.registry, "fetch")


@pytest.fixture()
def mocked_registry_install_to_path(mocker):
    """Return mocked 'wiz.registry.install_to_path' function."""
    return mocker.patch.object(wiz.registry, "install_to_path")


@pytest.fixture()
def definitions():
    """Return mocked definitions."""
    return [
        wiz.definition.Definition(
            {
                "identifier": "foo",
                "version": "0.2.0",
                "description": "This is Foo 0.2.0.",
                "command": {
                    "fooExe": "fooExe -X"
                },
                "system": {
                    "platform": "linux",
                }
            },
            registry_path="/registry1"
        ),
        wiz.definition.Definition(
            {
                "identifier": "foo",
                "version": "0.2.0",
                "description": "This is Foo 0.2.0.",
                "command": {
                    "fooExe": "fooExe -X"
                },
                "system": {
                    "platform": "mac",
                }
            },
            registry_path="/registry1"
        ),
        wiz.definition.Definition(
            {
                "identifier": "foo",
                "version": "0.1.0",
                "description": "This is Foo 0.1.0.",
                "command": {
                    "fooExe": "fooExe -X"
                },
                "system": {
                    "platform": "linux",
                },
                "environ": {
                    "PATH": "/path/to/bin:${PATH}",
                    "PYTHONPATH": "/path/to/lib:${PYTHONPATH}",
                },
                "requirements": [
                    "bim >= 0.1.0, < 1"
                ]
            },
            registry_path="/registry1"
        ),
        wiz.definition.Definition(
            {
                "identifier": "bar",
                "version": "0.1.0",
                "description": "This is Bar 0.1.0.",
                "environ": {
                    "PATH": "/path/to/bin:${PATH}",
                },
                "variants": [
                    {
                        "identifier": "Variant1",
                        "environ": {
                            "PYTHONPATH": "/path/to/lib/1:${PYTHONPATH}",
                        }
                    },
                    {
                        "identifier": "Variant2",
                        "environ": {
                            "PYTHONPATH": "/path/to/lib/2:${PYTHONPATH}",
                        }
                    },
                ],
                "requirements": [
                    "bim >= 0.1.0, < 1"
                ]
            },
            registry_path="/registry2"
        ),
        wiz.definition.Definition(
            {
                "identifier": "bim",
                "version": "0.1.1",
                "description": "This is Bim 0.1.1.",
                "command": {
                    "bimExe": "bimExe -X"
                },
                "variants": [
                    {
                        "identifier": "Variant1",
                        "environ": {
                            "PYTHONPATH": "/path/to/lib/1:${PYTHONPATH}",
                        }
                    },
                ],
            },
            registry_path="/registry2"
        ),
        wiz.definition.Definition(
            {
                "identifier": "bim",
                "version": "0.1.0",
                "description": "This is Bim 0.1.0.",
                "command": {
                    "bimExe": "bimExe -X"
                },
            },
            registry_path="/registry2"
        )
    ]


@pytest.fixture()
def definition_mapping():
    """Return mocked definition mapping."""
    return {
        "command": {
            "fooExe": "foo",
            "bimExe": "bim",
        },
        "package": {
            "foo": {
                "0.2.0": wiz.definition.Definition(
                    {
                        "identifier": "foo",
                        "version": "0.2.0",
                        "description": "This is Foo 0.2.0.",
                    },
                    path="/registry1/foo-0.2.0.json",
                    registry_path="/registry1",
                ),
                "0.1.0": wiz.definition.Definition(
                    {
                        "identifier": "foo",
                        "version": "0.1.0",
                        "description": "This is Foo 0.1.0.",
                        "environ": {
                            "PATH": "/path/to/bin:${PATH}",
                            "PYTHONPATH": "/path/to/lib:${PYTHONPATH}",
                        },
                        "requirements": [
                            "bim >= 0.1.0, < 1"
                        ]
                    },
                    path="/registry1/foo-0.1.0.json",
                    registry_path="/registry1",
                ),
            },
            "bar": {
                "0.1.0": wiz.definition.Definition(
                    {
                        "identifier": "bar",
                        "version": "0.1.0",
                        "description": "This is Bar 0.1.0.",
                        "environ": {
                            "PATH": "/path/to/bin:${PATH}",
                        },
                        "variants": [
                            {
                                "identifier": "Variant1",
                                "environ": {
                                    "PYTHONPATH": (
                                        "/path/to/lib/1:${PYTHONPATH}"
                                    ),
                                }
                            },
                            {
                                "identifier": "Variant2",
                                "environ": {
                                    "PYTHONPATH": (
                                        "/path/to/lib/2:${PYTHONPATH}"
                                    ),
                                }
                            },
                        ],
                        "requirements": [
                            "bim >= 0.1.0, < 1"
                        ]
                    },
                    path="/registry1/bar-0.1.0.json",
                    registry_path="/registry2",
                ),
            },
            "bim": {
                "0.1.1": wiz.definition.Definition(
                    {
                        "identifier": "bim",
                        "version": "0.1.1",
                        "description": "This is Bim 0.1.1.",
                        "variants": [
                            {
                                "identifier": "Variant1",
                                "environ": {
                                    "PYTHONPATH": (
                                        "/path/to/lib/1:${PYTHONPATH}"
                                    ),
                                }
                            },
                        ],
                    },
                    path="/registry1/bim-0.1.1.json",
                    registry_path="/registry2",
                ),
                "0.1.0": wiz.definition.Definition(
                    {
                        "identifier": "bim",
                        "version": "0.1.0",
                        "description": "This is Bim 0.1.0.",
                    },
                    path="/registry1/bim-0.1.0.json",
                    registry_path="/registry2",
                ),
            }
        },
        "registries": ["/registry1", "/registry2"]
    }


@pytest.fixture()
def wiz_context():
    """Return mocked context."""
    foo_definition = wiz.definition.Definition(
        {
            "identifier": "foo",
            "version": "0.1.0",
            "description": "This is Foo 0.1.0.",
            "environ": {
                "PATH": "/path/to/foo/bin:${PATH}",
                "PYTHONPATH": "/path/to/foo/lib:${PYTHONPATH}",
            },
            "requirements": [
                "bim >= 0.1.0, < 1"
            ]
        },
        registry_path="/registry1"
    )

    bim_definition = wiz.definition.Definition(
        {
            "identifier": "bim",
            "version": "0.1.1",
            "description": "This is Bim 0.1.1.",
            "environ": {
                "PATH": "/path/to/bim/bin:${PATH}",
                "PYTHONPATH": "/path/to/bim/lib:${PYTHONPATH}",
                "LICENSE_ENV": "license@bim.com:2000"
            },
            "variants": [
                {
                    "identifier": "Variant1",
                    "environ": {
                        "PYTHONPATH": "/path/to/bim/lib:${PYTHONPATH}",
                    }
                }
            ]
        },
        registry_path="/registry2"
    )

    return {
        "command": {
            "fooExe": "foo",
            "fooExeDebug": "foo --debug",
        },
        "environ": {
            "KEY1": "value1",
            "KEY2": "value2",
        },
        "packages": [
            wiz.package.create(foo_definition),
            wiz.package.create(
                bim_definition, variant_identifier="Variant1"
            ),
        ],
        "registries": ["/registry1", "/registry2"]
    }


def test_empty_arguments(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, mocked_system_query,
    mocked_registry_fetch, mocked_fetch_definition_mapping
):
    """Do not raise error for empty arguments."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main)
    assert result.exit_code == 0
    assert not result.exception

    mocked_history_start_recording.assert_not_called()
    mocked_history_get.assert_not_called()
    mocked_filesystem_export.assert_not_called()
    mocked_system_query.assert_not_called()
    mocked_registry_fetch.assert_not_called()
    mocked_fetch_definition_mapping.assert_not_called()


@pytest.mark.parametrize(
    "options, platform, architecture, os_name, os_version", [
        ([], None, None, None, None),
        (["--platform", "linux"], "linux", None, None, None),
        (["--architecture", "x86_64"], None, "x86_64", None, None),
        (["--os-name", "centos"], None, None, "centos", None),
        (["--os-version", "7.4.1708"], None, None, None, "7.4.1708"),
    ], ids=[
        "no-options",
        "override-platform",
        "override-architecture",
        "override-os-name",
        "override-os-version",
    ]
)
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_query_system(
    mocked_system_query, options, platform, architecture, os_name, os_version
):
    """Override system with options."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["list", "package"])
    assert result.exit_code == 0
    assert not result.exception

    mocked_system_query.assert_called_once_with(
        platform=platform,
        architecture=architecture,
        os_name=os_name,
        os_version=os_version,
    )


@pytest.mark.parametrize(
    "options, paths, depth, include_local, include_cwd", [
        ([], None, None, True, True),
        (
            ["-r", "/path1", "-r", "/path2"],
            ["/path1", "/path2"], None, True, True
        ),
        (["-rd", "2"], None, 2, True, True),
        (
            ["-add", "/path2", "-r", "/path1"],
            ["/path1", "/path2"], None, True, True
        ),
        (["--no-local"], None, None, False, True),
        (["--no-cwd"], None, None, True, False),
    ], ids=[
        "no-options",
        "change-search-paths",
        "change-search-depth",
        "add-search-path",
        "skip-local",
        "skip-cwd",
    ]
)
def test_fetch_registry(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    options, paths, depth, include_local, include_cwd
):
    """Override registries with options."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["list", "package"])
    assert result.exit_code == 0
    assert not result.exception

    mocked_registry_fetch.assert_called_once_with(
        tuple(paths or wiz.registry.get_defaults()),
        include_local=include_local,
        include_working_directory=include_cwd
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__",
        max_depth=depth
    )


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_list_packages_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, options, recorded
):
    """Record history when displaying list of available packages."""
    mocked_history_get.return_value = "__HISTORY__"
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["list", "package"])
    print(options + ["list", "package"])
    print(result.output)
    assert result.exit_code == 0
    assert not result.exception

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["list", "package"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


def test_list_packages_empty(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover
):
    """Display list of packages when no packages are available."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = []

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["list", "package"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries\n"
        "----------\n"
        "No registries to display.\n"
        "\n"
        "\n"
        "Package   Version   Registry   Description\n"
        "-------   -------   --------   -----------\n"
        "No packages to display.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        [], system_mapping="__SYSTEM__", max_depth=None
    )


def test_list_packages(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    definitions
):
    """Display list of available packages."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["list", "package", "--no-arch"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Package          Version   System   Registry   Description       \n"
        "--------------   -------   ------   --------   ------------------\n"
        "bar [Variant1]   0.1.0     noarch   1          This is Bar 0.1.0.\n"
        "bar [Variant2]   0.1.0     noarch   1          This is Bar 0.1.0.\n"
        "bim [Variant1]   0.1.1     noarch   1          This is Bim 0.1.1.\n"
        "foo              0.2.0     linux    0          This is Foo 0.2.0.\n"
        "foo              0.2.0     mac      0          This is Foo 0.2.0.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping=None, max_depth=None
    )


def test_list_packages_with_versions(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    definitions
):
    """Display list of available packages with versions."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["list", "package", "--no-arch", "--all"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Package          Version   System   Registry   Description       \n"
        "--------------   -------   ------   --------   ------------------\n"
        "bar [Variant1]   0.1.0     noarch   1          This is Bar 0.1.0.\n"
        "bar [Variant2]   0.1.0     noarch   1          This is Bar 0.1.0.\n"
        "bim [Variant1]   0.1.1     noarch   1          This is Bim 0.1.1.\n"
        "bim              0.1.0     noarch   1          This is Bim 0.1.0.\n"
        "foo              0.2.0     linux    0          This is Foo 0.2.0.\n"
        "foo              0.2.0     mac      0          This is Foo 0.2.0.\n"
        "foo              0.1.0     linux    0          This is Foo 0.1.0.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping=None, max_depth=None
    )


@pytest.mark.parametrize("options", [
    ["--", "--incorrect"],
    ["--incorrect"],
], ids=[
    "extra-arguments",
    "unknown-arguments",
])
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_list_packages_error(options):
    """Fail to list available packages."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["list", "package"] + options)
    assert result.exit_code == 2
    assert result.exception


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_list_commands_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, options, recorded
):
    """Record history when displaying list of available commands."""
    mocked_history_get.return_value = "__HISTORY__"

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["list", "command"])
    print(result.output)
    assert result.exit_code == 0
    assert not result.exception

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["list", "command"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


def test_list_commands_empty(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover
):
    """Display list of commands when no commands are available."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = []

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["list", "command"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries\n"
        "----------\n"
        "No registries to display.\n"
        "\n"
        "\n"
        "Command   Version   Registry   Description\n"
        "-------   -------   --------   -----------\n"
        "No commands to display.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        [], system_mapping="__SYSTEM__", max_depth=None
    )


@pytest.mark.usefixtures("mocked_system_query")
def test_list_commands(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    definitions
):
    """Display list of available commands."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["list", "command", "--no-arch"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Command             Version   System   Registry   Description       \n"
        "-----------------   -------   ------   --------   ------------------\n"
        "bimExe [Variant1]   0.1.1     noarch   1          This is Bim 0.1.1.\n"
        "fooExe              0.2.0     linux    0          This is Foo 0.2.0.\n"
        "fooExe              0.2.0     mac      0          This is Foo 0.2.0.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping=None, max_depth=None
    )


def test_list_commands_with_versions(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    definitions
):
    """Display list of available commands with versions."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["list", "command", "--all", "--no-arch"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Command             Version   System   Registry   Description       \n"
        "-----------------   -------   ------   --------   ------------------\n"
        "bimExe [Variant1]   0.1.1     noarch   1          This is Bim 0.1.1.\n"
        "bimExe              0.1.0     noarch   1          This is Bim 0.1.0.\n"
        "fooExe              0.2.0     linux    0          This is Foo 0.2.0.\n"
        "fooExe              0.2.0     mac      0          This is Foo 0.2.0.\n"
        "fooExe              0.1.0     linux    0          This is Foo 0.1.0.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping=None, max_depth=None
    )


@pytest.mark.parametrize("options", [
    ["--", "--incorrect"],
    ["--incorrect"],
], ids=[
    "extra-arguments",
    "unknown-arguments",
])
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_list_commands_error(options):
    """Fail to list available commands."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["list", "command"] + options)
    assert result.exit_code == 2
    assert result.exception


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_search_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, options, recorded
):
    """Record history when searching packages and commands."""
    mocked_history_get.return_value = "__HISTORY__"

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["search", "foo"])
    assert result.exit_code == 0
    assert not result.exception

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["search", "foo"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


def test_search_empty(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    logger
):
    """Display empty list of searched commands and packages."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = []

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["search", "foo"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries\n"
        "----------\n"
        "No registries to display.\n"
        "\n"
    )

    logger.warning.assert_called_once_with("No results found.\n")

    mocked_definition_discover.assert_called_once_with(
        [], system_mapping="__SYSTEM__", max_depth=None
    )


@pytest.mark.parametrize("options", [
    [], ["--type", "all"]
], ids=[
    "default",
    "with-option",
])
def test_search(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    logger, definitions, options
):
    """Display searched available commands and packages."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["search", "bim"] + options
    )
    assert not result.exception
    assert result.exit_code == 0
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Command             Version   Registry   Description       \n"
        "-----------------   -------   --------   ------------------\n"
        "bimExe [Variant1]   0.1.1     1          This is Bim 0.1.1.\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "bim [Variant1]   0.1.1     1          This is Bim 0.1.1.\n"
        "\n"
    )

    logger.warning.assert_not_called()

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__",
        max_depth=None
    )


@pytest.mark.parametrize("options", [
    [], ["--type", "all"]
], ids=[
    "default",
    "with-option",
])
def test_search_filtered_command(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    logger, definitions, options
):
    """Display searched available commands and packages."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["search", "Exe", "--no-arch"] + options
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Command             Version   System   Registry   Description       \n"
        "-----------------   -------   ------   --------   ------------------\n"
        "bimExe [Variant1]   0.1.1     noarch   1          This is Bim 0.1.1.\n"
        "fooExe              0.2.0     linux    0          This is Foo 0.2.0.\n"
        "fooExe              0.2.0     mac      0          This is Foo 0.2.0.\n"
        "\n"
        "\n"
        "Package          Version   System   Registry   Description       \n"
        "--------------   -------   ------   --------   ------------------\n"
        "bim [Variant1]   0.1.1     noarch   1          This is Bim 0.1.1.\n"
        "foo              0.2.0     linux    0          This is Foo 0.2.0.\n"
        "foo              0.2.0     mac      0          This is Foo 0.2.0.\n"
        "\n"
    )

    logger.warning.assert_not_called()

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping=None,
        max_depth=None
    )


def test_search_with_versions(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    logger, definitions
):
    """Display searched commands and packages with all versions."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["search", "bim", "--all", "--no-arch"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Command             Version   System   Registry   Description       \n"
        "-----------------   -------   ------   --------   ------------------\n"
        "bimExe [Variant1]   0.1.1     noarch   1          This is Bim 0.1.1.\n"
        "bimExe              0.1.0     noarch   1          This is Bim 0.1.0.\n"
        "\n"
        "\n"
        "Package          Version   System   Registry   Description       \n"
        "--------------   -------   ------   --------   ------------------\n"
        "bim [Variant1]   0.1.1     noarch   1          This is Bim 0.1.1.\n"
        "bim              0.1.0     noarch   1          This is Bim 0.1.0.\n"
        "\n"
    )

    logger.warning.assert_not_called()

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping=None,
        max_depth=None
    )


def test_search_packages(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    definitions
):
    """Display searched list of available packages."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["search", "bim", "-t", "package"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "bim [Variant1]   0.1.1     1          This is Bim 0.1.1.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__",
        max_depth=None
    )


def test_search_packages_with_versions(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    definitions
):
    """Display searched available packages with all versions."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["search", "bim", "-t", "package", "--all"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "bim [Variant1]   0.1.1     1          This is Bim 0.1.1.\n"
        "bim              0.1.0     1          This is Bim 0.1.0.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__",
        max_depth=None
    )


def test_search_commands(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    definitions
):
    """Display searched list of available commands."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["search", "bim", "-t", "command"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Command             Version   Registry   Description       \n"
        "-----------------   -------   --------   ------------------\n"
        "bimExe [Variant1]   0.1.1     1          This is Bim 0.1.1.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__",
        max_depth=None
    )


def test_search_commands_with_versions(
    mocked_system_query, mocked_registry_fetch, mocked_definition_discover,
    definitions
):
    """Display searched available commands with all versions."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_definition_discover.return_value = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["search", "bim", "-t", "command", "--all"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Command             Version   Registry   Description       \n"
        "-----------------   -------   --------   ------------------\n"
        "bimExe [Variant1]   0.1.1     1          This is Bim 0.1.1.\n"
        "bimExe              0.1.0     1          This is Bim 0.1.0.\n"
        "\n"
    )

    mocked_definition_discover.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__",
        max_depth=None
    )


@pytest.mark.parametrize("options", [
    ["--", "--incorrect"],
    ["--incorrect"],
], ids=[
    "extra-arguments",
    "unknown-arguments",
])
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_search_error(options):
    """Fail to search available packages and commands."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["search", "foo"] + options)
    assert result.exit_code == 2
    assert result.exception


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_view_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, options, recorded
):
    """Record history when viewing a definition."""
    mocked_history_get.return_value = "__HISTORY__"

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["view", "foo"])
    assert result.exit_code == 0
    assert not result.exception

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["view", "foo"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


def test_view_not_found(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    logger
):
    """Fail to view definition when request cannot be found."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = {
        "command": {},
        "package": {}
    }

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["view", "foo"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    logger.warning.assert_called_once_with("No definition found.\n")

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )


def test_view_definition(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    definition_mapping, logger
):
    """Display definition from identifier."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["view", "bar"])
    assert not result.exception
    assert result.exit_code == 0
    assert result.output == (
        "path: /registry1/bar-0.1.0.json\n"
        "registry: /registry2\n"
        "identifier: bar\n"
        "version: 0.1.0\n"
        "description: This is Bar 0.1.0.\n"
        "environ:\n"
        "    PATH: /path/to/bin:${PATH}\n"
        "requirements:\n"
        "    bim >= 0.1.0, < 1\n"
        "variants:\n"
        "    identifier: Variant1\n"
        "        environ:\n"
        "            PYTHONPATH: /path/to/lib/1:${PYTHONPATH}\n"
        "    identifier: Variant2\n"
        "        environ:\n"
        "            PYTHONPATH: /path/to/lib/2:${PYTHONPATH}\n"
    )

    logger.info.assert_called_once_with("View definition: bar==0.1.0")
    logger.warning.assert_not_called()

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )


def test_view_definition_json(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    definition_mapping, logger
):
    """Display definition from identifier in JSON format."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["view", "bar", "--json"])
    assert not result.exception
    assert result.exit_code == 0
    assert result.output == (
        "{\n"
        "    \"identifier\": \"bar\",\n"
        "    \"version\": \"0.1.0\",\n"
        "    \"description\": \"This is Bar 0.1.0.\",\n"
        "    \"environ\": {\n"
        "        \"PATH\": \"/path/to/bin:${PATH}\"\n"
        "    },\n"
        "    \"requirements\": [\n"
        "        \"bim >= 0.1.0, < 1\"\n"
        "    ],\n"
        "    \"variants\": [\n"
        "        {\n"
        "            \"identifier\": \"Variant1\",\n"
        "            \"environ\": {\n"
        "                \"PYTHONPATH\": \"/path/to/lib/1:${PYTHONPATH}\"\n"
        "            }\n"
        "        },\n"
        "        {\n"
        "            \"identifier\": \"Variant2\",\n"
        "            \"environ\": {\n"
        "                \"PYTHONPATH\": \"/path/to/lib/2:${PYTHONPATH}\"\n"
        "            }\n"
        "        }\n"
        "    ]\n"
        "}\n"
    )

    logger.info.assert_called_once_with("View definition: bar==0.1.0")
    logger.warning.assert_not_called()

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )


def test_view_definition_from_command(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    definition_mapping, logger
):
    """Indicate that identifier is referring to a definition."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["view", "fooExe"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    logger.info.assert_called_once_with(
        "Command found in definition: foo==0.2.0"
    )
    logger.warning.assert_not_called()

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )


@pytest.mark.parametrize("options", [
    ["--", "--incorrect"],
    ["--incorrect"],
], ids=[
    "extra-arguments",
    "unknown-arguments",
])
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
def test_view_error(options):
    """Fail to view definitions."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["view", "foo"] + options)
    assert result.exit_code == 2
    assert result.exception


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
@pytest.mark.usefixtures("mocked_resolve_context")
@pytest.mark.usefixtures("mocked_resolve_command")
@pytest.mark.usefixtures("mocked_spawn_execute")
@pytest.mark.usefixtures("mocked_spawn_shell")
@pytest.mark.usefixtures("mocked_history_record_action")
def test_use_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, options, recorded
):
    """Record history when using a resolved context."""
    mocked_history_get.return_value = "__HISTORY__"

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["use", "foo"])
    assert result.exit_code == 0
    assert not result.exception

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["use", "foo"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_use_spawn_shell(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_resolve_command, mocked_spawn_execute,
    mocked_spawn_shell, mocked_history_record_action, wiz_context, logger,
    options, max_combinations, max_attempts
):
    """Use a resolved context."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["use", "foo"] + options)
    assert result.output == ""
    assert result.exit_code == 0
    assert not result.exception

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_spawn_shell.assert_called_once_with({
        "KEY1": "value1",
        "KEY2": "value2"
    }, {
        "fooExe": "foo",
        "fooExeDebug": "foo --debug",
    })

    mocked_resolve_command.assert_not_called()
    mocked_spawn_execute.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_use_spawn_shell_view(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_resolve_command, mocked_spawn_execute,
    mocked_spawn_shell, mocked_history_record_action, wiz_context, logger,
    options, max_combinations, max_attempts
):
    """View a resolved context."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["use", "foo", "--view"] + options
    )
    assert not result.exception
    assert result.exit_code == 0
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "foo              0.1.0     0          This is Foo 0.1.0.\n"
        "bim [Variant1]   0.1.1     1          This is Bim 0.1.1.\n"
        "\n"
        "\n"
        "Command       Value      \n"
        "-----------   -----------\n"
        "fooExe        foo        \n"
        "fooExeDebug   foo --debug\n"
        "\n"
        "\n"
        "Environment Variable   Environment Value\n"
        "--------------------   -----------------\n"
        "KEY1                   value1           \n"
        "KEY2                   value2           \n"
        "\n"
    )

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_spawn_shell.assert_not_called()
    mocked_resolve_command.assert_not_called()
    mocked_spawn_execute.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_use_spawn_shell_view_empty(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_resolve_command, mocked_spawn_execute,
    mocked_spawn_shell, mocked_history_record_action, logger,
    options, max_combinations, max_attempts
):
    """View an empty resolved context."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = {
        "command": {},
        "environ": {},
        "packages": [],
        "registries": ["/registry1", "/registry2"]
    }

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["use", "foo", "--view"] + options
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Package   Version   Registry   Description\n"
        "-------   -------   --------   -----------\n"
        "No packages to display.\n"
        "\n"
        "\n"
        "Command   Value\n"
        "-------   -----\n"
        "No commands to display.\n"
        "\n"
        "\n"
        "Environment Variable   Environment Value\n"
        "--------------------   -----------------\n"
        "No environment variables to display.\n"
        "\n"
    )

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_spawn_shell.assert_not_called()
    mocked_resolve_command.assert_not_called()
    mocked_spawn_execute.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_use_execute_command(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_resolve_command, mocked_spawn_execute,
    mocked_spawn_shell, mocked_history_record_action, wiz_context, logger,
    options, max_combinations, max_attempts
):
    """Execute a command within a resolved context."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_resolve_command.return_value = "__RESOLVED_COMMAND__"

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["use", "foo"] + options + [
            "--", "fooExeDebug", "-t", "/path/to/script.foo"
        ]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_resolve_command.assert_called_once_with(
        ["fooExeDebug", "-t", "/path/to/script.foo"],
        {
            "fooExe": "foo",
            "fooExeDebug": "foo --debug",
        }
    )

    mocked_spawn_execute.assert_called_once_with(
        "__RESOLVED_COMMAND__",
        {
            "KEY1": "value1",
            "KEY2": "value2"
        }
    )

    mocked_spawn_shell.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_use_with_resolution_error(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_resolve_command, mocked_spawn_execute,
    mocked_spawn_shell, mocked_history_record_action, logger,
    options, max_combinations, max_attempts
):
    """Fail to resolve a context."""
    exception = wiz.exception.WizError("Oh Shit!")
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.side_effect = exception

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["use", "foo", "bim==0.1.*"] + options
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo", "bim==0.1.*"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_spawn_shell.assert_not_called()
    mocked_resolve_command.assert_not_called()
    mocked_spawn_execute.assert_not_called()

    mocked_history_record_action.assert_called_once_with(
        "RAISE_EXCEPTION", error=exception
    )

    logger.error.assert_called_once_with("Oh Shit!")


@pytest.mark.parametrize("options", [
    ["--incorrect"],
], ids=[
    "unknown-arguments",
])
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
@pytest.mark.usefixtures("mocked_resolve_context")
@pytest.mark.usefixtures("mocked_resolve_command")
@pytest.mark.usefixtures("mocked_spawn_execute")
@pytest.mark.usefixtures("mocked_spawn_shell")
@pytest.mark.usefixtures("mocked_history_record_action")
def test_use_error(options):
    """Fail to view definitions."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["use", "foo"] + options)
    assert result.exit_code == 2
    assert result.exception


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_use_initial_environment(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_resolve_command, mocked_spawn_execute,
    wiz_context, options, max_combinations, max_attempts
):
    """Executing a command to extend an initial environment."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_resolve_command.return_value = "__RESOLVED_COMMAND__"

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        [
            "--init", "PATH=/path", "--init", "PYTHONPATH=/other-path",
            "use", "foo"
        ] + options + ["--", "fooExeDebug", "-t", "/path/to/script.foo"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__", ignore_implicit=False,
        environ_mapping={"PATH": "/path", "PYTHONPATH": "/other-path"},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_spawn_execute.assert_called_once_with(
        "__RESOLVED_COMMAND__", {"KEY1": "value1", "KEY2": "value2"}
    )


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
@pytest.mark.usefixtures("mocked_fetch_package_request_from_command")
@pytest.mark.usefixtures("mocked_resolve_context")
@pytest.mark.usefixtures("mocked_spawn_execute")
@pytest.mark.usefixtures("mocked_history_record_action")
def test_run_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, mocked_resolve_command, options, recorded
):
    """Record history when running command within a resolved context."""
    mocked_history_get.return_value = "__HISTORY__"
    mocked_resolve_command.return_value = "__RESOLVED_COMMAND__"

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["run", "fooExe"])
    assert result.exit_code == 0
    assert not result.exception

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["run", "fooExe"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_run(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_fetch_package_request_from_command, mocked_resolve_context,
    mocked_resolve_command, mocked_spawn_execute, mocked_history_record_action,
    wiz_context, logger, options, max_combinations, max_attempts
):
    """Execute a command within a resolved context."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_fetch_package_request_from_command.return_value = "__PACKAGE__"
    mocked_resolve_command.return_value = "__RESOLVED_COMMAND__"

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["run", "fooExe"] + options)
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_fetch_package_request_from_command.assert_called_once_with(
        "fooExe", "__MAPPING__"
    )

    mocked_resolve_context.assert_called_once_with(
        ["__PACKAGE__"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_resolve_command.assert_called_once_with(
        ["fooExe"],
        {
            "fooExe": "foo",
            "fooExeDebug": "foo --debug",
        }
    )

    mocked_spawn_execute.assert_called_once_with(
        "__RESOLVED_COMMAND__",
        {
            "KEY1": "value1",
            "KEY2": "value2"
        }
    )

    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_run_view(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_fetch_package_request_from_command, mocked_resolve_context,
    mocked_resolve_command, mocked_spawn_execute, mocked_history_record_action,
    wiz_context, logger, options, max_combinations, max_attempts
):
    """View a resolved context from a command execution."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_fetch_package_request_from_command.return_value = "__PACKAGE__"
    mocked_resolve_command.return_value = "__RESOLVED_COMMAND__"

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["run", "fooExe", "--view"] + options
    )
    assert not result.exception
    assert result.exit_code == 0
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "foo              0.1.0     0          This is Foo 0.1.0.\n"
        "bim [Variant1]   0.1.1     1          This is Bim 0.1.1.\n"
        "\n"
        "\n"
        "Command       Value      \n"
        "-----------   -----------\n"
        "fooExe        foo        \n"
        "fooExeDebug   foo --debug\n"
        "\n"
        "\n"
        "Environment Variable   Environment Value\n"
        "--------------------   -----------------\n"
        "KEY1                   value1           \n"
        "KEY2                   value2           \n"
        "\n"
    )

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_fetch_package_request_from_command.assert_called_once_with(
        "fooExe", "__MAPPING__"
    )

    mocked_resolve_context.assert_called_once_with(
        ["__PACKAGE__"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_resolve_command.assert_not_called()
    mocked_spawn_execute.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_run_view_empty(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_fetch_package_request_from_command, mocked_resolve_context,
    mocked_resolve_command, mocked_spawn_execute, mocked_history_record_action,
    logger, options, max_combinations, max_attempts
):
    """View an empty resolved context from a command execution."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = {
        "command": {},
        "environ": {},
        "packages": [],
        "registries": ["/registry1", "/registry2"]
    }
    mocked_fetch_package_request_from_command.return_value = "__PACKAGE__"
    mocked_resolve_command.return_value = "__RESOLVED_COMMAND__"

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["run", "fooExe", "--view"] + options
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries    \n"
        "--------------\n"
        "[0] /registry1\n"
        "[1] /registry2\n"
        "\n"
        "\n"
        "Package   Version   Registry   Description\n"
        "-------   -------   --------   -----------\n"
        "No packages to display.\n"
        "\n"
        "\n"
        "Command   Value\n"
        "-------   -----\n"
        "No commands to display.\n"
        "\n"
        "\n"
        "Environment Variable   Environment Value\n"
        "--------------------   -----------------\n"
        "No environment variables to display.\n"
        "\n"
    )

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_fetch_package_request_from_command.assert_called_once_with(
        "fooExe", "__MAPPING__"
    )

    mocked_resolve_context.assert_called_once_with(
        ["__PACKAGE__"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_resolve_command.assert_not_called()
    mocked_spawn_execute.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_run_with_resolution_error(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_fetch_package_request_from_command, mocked_resolve_context,
    mocked_resolve_command, mocked_spawn_execute, mocked_history_record_action,
    logger, options, max_combinations, max_attempts
):
    """Fail to resolve a context."""
    exception = wiz.exception.WizError("Oh Shit!")
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_fetch_package_request_from_command.return_value = "__PACKAGE__"
    mocked_resolve_context.side_effect = exception

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["run", "fooExe"] + options)
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["__PACKAGE__"], "__MAPPING__",
        ignore_implicit=False,
        environ_mapping={},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_fetch_package_request_from_command.assert_called_once_with(
        "fooExe", "__MAPPING__"
    )

    mocked_resolve_command.assert_not_called()
    mocked_spawn_execute.assert_not_called()

    mocked_history_record_action.assert_called_once_with(
        "RAISE_EXCEPTION", error=exception
    )

    logger.error.assert_called_once_with("Oh Shit!")


@pytest.mark.parametrize("options, max_combinations, max_attempts", [
    ([], 10, 15),
    (["-mc", "1"], 1, 15),
    (["-ma", "1"], 10, 1),
], ids=[
    "simple",
    "with-maximum-combinations",
    "with-maximum-attempts",
])
def test_run_initial_environment(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_fetch_package_request_from_command, mocked_resolve_context,
    mocked_resolve_command, mocked_spawn_execute, wiz_context, options,
    max_combinations, max_attempts
):
    """Execute a command to extend an initial environment."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_fetch_package_request_from_command.return_value = "__PACKAGE__"
    mocked_resolve_command.return_value = "__RESOLVED_COMMAND__"

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, [
            "--init", "PATH=/path", "--init", "PYTHONPATH=/other-path",
            "run", "fooExe"
        ] + options
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_resolve_context.assert_called_once_with(
        ["__PACKAGE__"], "__MAPPING__", ignore_implicit=False,
        environ_mapping={"PATH": "/path", "PYTHONPATH": "/other-path"},
        maximum_combinations=max_combinations,
        maximum_attempts=max_attempts,
    )

    mocked_spawn_execute.assert_called_once_with(
        "__RESOLVED_COMMAND__", {"KEY1": "value1", "KEY2": "value2"}
    )


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
@pytest.mark.usefixtures("mocked_resolve_context")
@pytest.mark.usefixtures("mocked_export_definition")
@pytest.mark.usefixtures("mocked_export_script")
@pytest.mark.usefixtures("mocked_history_record_action")
def test_freeze_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, mocked_click_prompt, options, recorded
):
    """Record history when freezing a resolved environment."""
    mocked_history_get.return_value = "__HISTORY__"
    mocked_click_prompt.side_effect = ["foo", "This is a description", "0.1.0"]

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        options + ["freeze", "foo", "-o", "/output/path"],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(
                ["wiz"] + options + ["freeze", "foo", "-o", "/output/path"]
            )
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


@pytest.mark.parametrize("options", [
    [], ["--format", "wiz"]
], ids=[
    "default",
    "with-option",
])
def test_freeze(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_export_definition, mocked_export_script,
    mocked_history_record_action, logger, mocked_click_prompt, wiz_context,
    options
):
    """Freeze a resolved environment."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_click_prompt.side_effect = ["foo", "This is a description.", "0.1.0"]

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["freeze", "foo", "-o", "/output/path"] + options,
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__", ignore_implicit=False, environ_mapping={},
    )

    mocked_export_definition.assert_called_once_with(
        "/output/path",
        {
            "identifier": "foo",
            "version": "0.1.0",
            "description": "This is a description.",
            "command": {
                "fooExe": "foo",
                "fooExeDebug": "foo --debug"
            },
            "environ": {
                "KEY1": "value1",
                "KEY2": "value2",
            }
        }
    )

    mocked_export_script.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()


@pytest.mark.parametrize("options", [
    [], ["--format", "wiz"]
], ids=[
    "default",
    "with-option",
])
def test_freeze_empty(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_export_definition, mocked_export_script,
    mocked_history_record_action, logger, mocked_click_prompt, options
):
    """Freeze an empty resolved environment."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = {}
    mocked_click_prompt.side_effect = ["foo", "This is a description.", "0.1.0"]

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["freeze", "foo", "-o", "/output/path"] + options,
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__", ignore_implicit=False, environ_mapping={},
    )

    mocked_export_definition.assert_called_once_with(
        "/output/path",
        {
            "identifier": "foo",
            "version": "0.1.0",
            "description": "This is a description."
        }
    )

    mocked_export_script.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()


@pytest.mark.parametrize("format_name, options, command", [
    ("tcsh", ["--format", "tcsh"], None),
    ("tcsh", ["--format", "tcsh"], "fooExe"),
    ("bash", ["--format", "bash"], None),
    ("bash", ["--format", "bash"], "fooExe"),
], ids=[
    "tcsh",
    "tcsh-with-command",
    "bash",
    "bash-with-command",
])
def test_freeze_as_script(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_export_definition, mocked_export_script,
    mocked_history_record_action, logger, mocked_click_prompt, wiz_context,
    format_name, options, command
):
    """Freeze a resolved environment as a script."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_click_prompt.side_effect = ["foo", command]

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["freeze", "foo", "-o", "/output/path"] + options,
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "Available aliases:\n"
        "- foo\n"
        "- foo --debug\n"
    )

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__", ignore_implicit=False, environ_mapping={},
    )

    mocked_export_script.assert_called_once_with(
        "/output/path", format_name, "foo",
        environ={"KEY1": "value1", "KEY2": "value2"},
        command=command,
        packages=wiz_context["packages"]
    )

    mocked_export_definition.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()


@pytest.mark.parametrize("format_name, options, command", [
    ("tcsh", ["--format", "tcsh"], None),
    ("tcsh", ["--format", "tcsh"], "fooExe"),
    ("bash", ["--format", "bash"], None),
    ("bash", ["--format", "bash"], "fooExe"),
], ids=[
    "tcsh",
    "tcsh-with-command",
    "bash",
    "bash-with-command",
])
def test_freeze_as_script_without_commands(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_export_definition, mocked_export_script,
    mocked_history_record_action, logger, mocked_click_prompt, wiz_context,
    format_name, options, command
):
    """Freeze a resolved environment as a script."""
    wiz_context["command"] = {}

    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_click_prompt.side_effect = ["foo", command]

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["freeze", "foo", "-o", "/output/path"] + options,
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__", ignore_implicit=False, environ_mapping={},
    )

    mocked_export_script.assert_called_once_with(
        "/output/path", format_name, "foo",
        environ={"KEY1": "value1", "KEY2": "value2"},
        command=command,
        packages=wiz_context["packages"]
    )

    mocked_export_definition.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()


def test_freeze_with_resolution_error(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, mocked_export_definition, mocked_export_script,
    mocked_history_record_action, logger, mocked_click_prompt
):
    """Fail to resolve a context."""
    exception = wiz.exception.WizError("Oh Shit!")
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_fetch_package_request_from_command.return_value = "__PACKAGE__"
    mocked_resolve_context.side_effect = exception

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["freeze", "foo", "-o", "/output/path"],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        system_mapping="__SYSTEM__", max_depth=None
    )

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__", ignore_implicit=False, environ_mapping={},
    )

    mocked_click_prompt.assert_not_called()
    mocked_export_definition.assert_not_called()
    mocked_export_script.assert_not_called()

    mocked_history_record_action.assert_called_once_with(
        "RAISE_EXCEPTION", error=exception
    )

    logger.error.assert_called_once_with("Oh Shit!")
    logger.warning.assert_not_called()


@pytest.mark.parametrize("options", [
    ["--", "--incorrect"],
    ["--incorrect"],
], ids=[
    "extra-arguments",
    "unknown-arguments",
])
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
@pytest.mark.usefixtures("mocked_resolve_context")
@pytest.mark.usefixtures("mocked_export_definition")
@pytest.mark.usefixtures("mocked_export_script")
@pytest.mark.usefixtures("mocked_history_record_action")
def test_freeze_error(options):
    """Fail to freeze resolved environment."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["freeze", "foo"] + options)
    assert result.exit_code == 2
    assert result.exception


@pytest.mark.usefixtures("mocked_export_definition")
def test_freeze_initial_environment(
    mocked_system_query, mocked_registry_fetch, mocked_fetch_definition_mapping,
    mocked_resolve_context, wiz_context, mocked_click_prompt
):
    """Freeze a resolved environment with initial environment."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_fetch_definition_mapping.return_value = "__MAPPING__"
    mocked_resolve_context.return_value = wiz_context
    mocked_click_prompt.side_effect = ["foo", "This is a description.", "0.1.0"]

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, [
           "--init", "PATH=/path", "--init", "PYTHONPATH=/other-path",
           "freeze", "foo", "-o", "/output/path"
        ],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_resolve_context.assert_called_once_with(
        ["foo"], "__MAPPING__", ignore_implicit=False,
        environ_mapping={"PATH": "/path", "PYTHONPATH": "/other-path"},
    )


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
@pytest.mark.usefixtures("mocked_registry_install_to_path")
@pytest.mark.usefixtures("mocked_click_confirm")
@pytest.mark.usefixtures("mocked_history_record_action")
def test_install_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, options, recorded
):
    """Record history when installing definition(s)."""
    mocked_history_get.return_value = "__HISTORY__"

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        options + ["install", "/path/to/foo.json", "-o", "/somewhere"],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(
                ["wiz"] + options + [
                    "install", "/path/to/foo.json", "-o", "/somewhere"
                ]
            )
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


@pytest.mark.parametrize("options, definitions", [
    (["/foo.json"], ("/foo.json",)),
    (["/foo.json", "/bar.json"], ("/foo.json", "/bar.json"))
], ids=[
    "one-definition",
    "several-definitions"
])
def test_install_to_path(
    mocked_system_query, mocked_registry_fetch, mocked_load_definition,
    mocked_registry_install_to_path, mocked_click_confirm,
    mocked_history_record_action, logger, options, definitions
):
    """Install definition in registry using default plugin."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_load_definition.side_effect = definitions

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["install"] + options + ["--output", "/registry"],
    )
    assert not result.exception
    assert result.exit_code == 0
    assert result.output == ""

    assert mocked_load_definition.call_count == len(definitions)
    for definition in definitions:
        mocked_load_definition.assert_any_call(definition)

    mocked_registry_install_to_path.assert_called_once_with(
        list(definitions), "/registry", overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.warning.assert_not_called()
    logger.error.assert_not_called()


def test_install_overwrite_existing(
    mocked_system_query, mocked_registry_fetch, mocked_load_definition,
    mocked_registry_install_to_path, mocked_click_confirm,
    mocked_history_record_action, logger
):
    """Overwrite definition in registry."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_registry_install_to_path.side_effect = (
        wiz.exception.DefinitionsExist(["'foo' [0.1.0]"]),
        None
    )
    mocked_click_confirm.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["install", "/foo.json", "--output", "/registry"],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    assert mocked_load_definition.call_count == 2
    mocked_load_definition.assert_any_call("/foo.json")

    assert mocked_registry_install_to_path.call_count == 2
    mocked_registry_install_to_path.assert_any_call(
        [mocked_load_definition.return_value], "/registry",
        overwrite=False
    )
    mocked_registry_install_to_path.assert_any_call(
        [mocked_load_definition.return_value], "/registry",
        overwrite=True
    )

    mocked_click_confirm.assert_called_once_with(
        "1 definition(s) already exist in registry.\n"
        "- 'foo' [0.1.0]\n"
        "Overwrite?"
    )

    mocked_history_record_action.assert_not_called()
    logger.warning.assert_not_called()
    logger.error.assert_not_called()


def test_install_skip_existing(
    mocked_system_query, mocked_registry_fetch, mocked_load_definition,
    mocked_registry_install_to_path, mocked_click_confirm,
    mocked_history_record_action, logger
):
    """Skip definition in registry."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_registry_install_to_path.side_effect = (
        wiz.exception.DefinitionsExist(["'foo' [0.1.0]"]),
    )
    mocked_click_confirm.return_value = False

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["install", "/foo.json", "--output", "/registry"],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/foo.json")

    mocked_registry_install_to_path.assert_called_once_with(
        [mocked_load_definition.return_value], "/registry",
        overwrite=False
    )

    mocked_click_confirm.assert_called_once_with(
        "1 definition(s) already exist in registry.\n"
        "- 'foo' [0.1.0]\n"
        "Overwrite?"
    )

    mocked_history_record_action.assert_not_called()
    logger.warning.assert_not_called()
    logger.error.assert_not_called()


def test_install_no_change(
    mocked_system_query, mocked_registry_fetch, mocked_load_definition,
    mocked_registry_install_to_path, mocked_click_confirm,
    mocked_history_record_action, logger
):
    """Installation to registry with no changes."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_registry_install_to_path.side_effect = (
        wiz.exception.InstallNoChanges()
    )

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["install", "/foo.json", "--output", "/registry"],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/foo.json")

    mocked_registry_install_to_path.assert_called_once_with(
        [mocked_load_definition.return_value], "/registry",
        overwrite=False
    )

    logger.warning.assert_called_once_with("No changes detected in release.")

    mocked_click_confirm.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()


def test_install_local_error(
    mocked_system_query, mocked_registry_fetch, mocked_load_definition,
    mocked_registry_install_to_path, mocked_click_confirm,
    mocked_history_record_action, logger
):
    """Fail to install definition to local registry."""
    exception = wiz.exception.WizError("Oh Shit!")
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_registry_fetch.return_value = ["/registry1", "/registry2"]
    mocked_registry_install_to_path.side_effect = exception

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["install", "/foo.json", "--output", "/registry"],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/foo.json")

    mocked_registry_install_to_path.assert_called_once_with(
        [mocked_load_definition.return_value], "/registry",
        overwrite=False
    )

    logger.error.assert_called_once_with(exception)

    mocked_history_record_action.assert_called_once_with(
        "RAISE_EXCEPTION", error=exception
    )

    mocked_click_confirm.assert_not_called()
    logger.warning.assert_not_called()


@pytest.mark.parametrize("options", [
    ["--", "--incorrect"],
    ["--incorrect"],
], ids=[
    "extra-arguments",
    "unknown-arguments",
])
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
@pytest.mark.usefixtures("mocked_load_definition")
@pytest.mark.usefixtures("mocked_registry_install_to_path")
@pytest.mark.usefixtures("mocked_click_confirm")
@pytest.mark.usefixtures("mocked_history_record_action")
def test_install_local_command_error(options):
    """Fail to install definition to local registry."""
    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["install"] + options + ["/foo.json", "--output", "/registry"],
    )
    assert result.exit_code == 2
    assert result.exception


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", tempfile.gettempdir()], True)
], ids=[
    "normal",
    "recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
@pytest.mark.usefixtures("mocked_load_definition")
@pytest.mark.usefixtures("mocked_click_confirm")
@pytest.mark.usefixtures("mocked_click_edit")
@pytest.mark.usefixtures("mocked_history_record_action")
def test_edit_recorded(
    mocked_history_start_recording, mocked_history_get,
    mocked_filesystem_export, options, recorded
):
    """Record history when editing definition(s)."""
    mocked_history_get.return_value = "__HISTORY__"

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        options + ["edit", "/path/to/foo.json"],
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(
                ["wiz"] + options + ["edit", "/path/to/foo.json"]
            )
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            tempfile.gettempdir() + "/wiz-NOW.dump", "__HISTORY__",
            compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with editor."""
    definition = wiz.definition.Definition(
        {"identifier": "foo"},
        registry_path="/path",
        path="/path/to/foo.json"
    )

    mocked_load_definition.return_value = definition
    mocked_click_edit.return_value = (
        "{\"identifier\": \"foo\",\"version\": \"0.1.0\"}"
    )
    mocked_click_confirm.return_value = True
    mocked_filesystem_export.side_effect = [
        wiz.exception.FileExists("/path"), None
    ]

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["edit", "/path/to/foo.json"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")
    mocked_click_edit.assert_called_once_with(
        "{\n"
        "    \"identifier\": \"foo\"\n"
        "}",
        extension=".json"
    )

    mocked_click_confirm.assert_called_once_with("Overwrite 'foo'?")

    assert mocked_filesystem_export.call_count == 2
    mocked_filesystem_export.assert_any_call(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"version\": \"0.1.0\"\n"
            "}"
        ),
        overwrite=False
    )
    mocked_filesystem_export.assert_any_call(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"version\": \"0.1.0\"\n"
            "}"
        ),
        overwrite=True
    )

    mocked_history_record_action.assert_not_called()

    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_non_saved(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Skip definition editing when updated data is unsaved in editor."""
    definition = wiz.definition.Definition(
        {"identifier": "foo"},
        registry_path="/path",
        path="/path/to/foo.json"
    )

    mocked_load_definition.return_value = definition
    mocked_click_edit.return_value = None

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["edit", "/path/to/foo.json"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")
    mocked_click_edit.assert_called_once_with(
        "{\n"
        "    \"identifier\": \"foo\"\n"
        "}",
        extension=".json"
    )

    mocked_click_confirm.assert_not_called()
    mocked_filesystem_export.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()

    logger.info.assert_called_once_with("Edit 'foo'.")
    logger.warning.assert_called_once_with("Skip edition for 'foo'.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_overwrite_existing(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with editor by overwriting original."""
    definition = wiz.definition.Definition(
        {"identifier": "foo"},
        registry_path="/path",
        path="/path/to/foo.json"
    )

    mocked_load_definition.return_value = definition
    mocked_click_edit.return_value = (
        "{\"identifier\": \"foo\", \"version\": \"0.1.0\"}"
    )

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["edit", "/path/to/foo.json", "--overwrite"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")
    mocked_click_edit.assert_called_once_with(
        "{\n"
        "    \"identifier\": \"foo\"\n"
        "}",
        extension=".json"
    )

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"version\": \"0.1.0\"\n"
            "}"
        ),
        overwrite=True
    )

    mocked_click_confirm.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_skip_existing(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Abort definition edition by skipping overwriting."""
    definition = wiz.definition.Definition(
        {"identifier": "foo"},
        registry_path="/path",
        path="/path/to/foo.json"
    )

    mocked_load_definition.return_value = definition
    mocked_click_edit.return_value = (
        "{\"identifier\": \"foo\", \"version\": \"0.1.0\"}"
    )

    mocked_click_confirm.return_value = False
    mocked_filesystem_export.side_effect = wiz.exception.FileExists("/path")

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["edit", "/path/to/foo.json"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")
    mocked_click_edit.assert_called_once_with(
        "{\n"
        "    \"identifier\": \"foo\"\n"
        "}",
        extension=".json"
    )

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"version\": \"0.1.0\"\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_called_once_with("Overwrite 'foo'?")

    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()

    logger.warning.assert_called_once_with("Skip edition for 'foo'.")
    logger.info.assert_called_once_with("Edit 'foo'.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_with_output(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with editor and save in different output path."""
    definition = wiz.definition.Definition(
        {"identifier": "foo"},
        registry_path="/path",
        path="/path/to/foo.json"
    )

    mocked_load_definition.return_value = definition
    mocked_click_edit.return_value = (
        "{\"identifier\": \"foo\",\"version\": \"0.1.0\"}"
    )

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        ["edit", "/path/to/foo.json", "--output", "/path/to/target"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")
    mocked_click_edit.assert_called_once_with(
        "{\n"
        "    \"identifier\": \"foo\"\n"
        "}",
        extension=".json"
    )

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/target/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"version\": \"0.1.0\"\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/target/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_with_operation_set(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with operation 'set'."""
    definition = wiz.definition.Definition(
        {"identifier": "foo"},
        registry_path="/path",
        path="/path/to/foo.json"
    )

    mocked_load_definition.return_value = definition

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        [
            "edit", "/path/to/foo.json",
            "--set", "install-location", "/path/to/data"
        ]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"install-location\": \"/path/to/data\"\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_click_edit.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_with_operation_update(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with operation 'update'."""
    definition = wiz.definition.Definition(
        {
            "identifier": "foo",
            "environ": {
                "KEY1": "VALUE1"
            },
        },
        path="/path/to/foo.json",
        registry_path="/path"
    )

    mocked_load_definition.return_value = definition

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        [
            "edit", "/path/to/foo.json",
            "--update", "environ", "{\"KEY1\": \"VALUE2\"}"
        ]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"environ\": {\n"
            "        \"KEY1\": \"VALUE2\"\n"
            "    }\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_click_edit.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_with_operation_extend(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with operation 'extend'."""
    definition = wiz.definition.Definition(
        {
            "identifier": "foo",
            "requirements": [
                "bar >= 0.1.0, < 1"
            ],
        },
        path="/path/to/foo.json",
        registry_path="/path"
    )

    mocked_load_definition.return_value = definition

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        [
            "edit", "/path/to/foo.json",
            "--extend", "requirements", "[\"bim >= 2.5, < 3\", \"baz\"]"
        ]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"requirements\": [\n"
            "        \"bar >= 0.1.0, < 1\",\n"
            "        \"bim >= 2.5, < 3\",\n"
            "        \"baz\"\n"
            "    ]\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_click_edit.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_with_operation_insert(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with operation 'insert'."""
    definition = wiz.definition.Definition(
        {
            "identifier": "foo",
            "requirements": [
                "bar >= 0.1.0, < 1",
                "bim >= 2.5, < 3"
            ],
        },
        path="/path/to/foo.json",
        registry_path="/path"
    )

    mocked_load_definition.return_value = definition

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        [
            "edit", "/path/to/foo.json",
            "--insert", "requirements", "baz", "1"
        ]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"requirements\": [\n"
            "        \"bar >= 0.1.0, < 1\",\n"
            "        \"baz\",\n"
            "        \"bim >= 2.5, < 3\"\n"
            "    ]\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_click_edit.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_with_operation_remove(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with operation 'remove'."""
    definition = wiz.definition.Definition(
        {
            "identifier": "foo",
            "requirements": [
                "bar >= 0.1.0, < 1",
                "bim >= 2.5, < 3"
            ],
        },
        path="/path/to/foo.json",
        registry_path="/path"
    )

    mocked_load_definition.return_value = definition

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        [
            "edit", "/path/to/foo.json",
            "--remove", "requirements"
        ]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\"\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_click_edit.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_with_operation_remove_key(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with operation 'remove-key'."""
    definition = wiz.definition.Definition(
        {
            "identifier": "foo",
            "environ": {
                "KEY1": "VALUE1",
                "KEY2": "VALUE2",
            },
        },
        path="/path/to/foo.json",
        registry_path="/path"
    )

    mocked_load_definition.return_value = definition

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        [
            "edit", "/path/to/foo.json",
            "--remove-key", "environ", "KEY2"
        ]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"environ\": {\n"
            "        \"KEY1\": \"VALUE1\"\n"
            "    }\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_click_edit.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_with_operation_remove_index(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Edit definition with operation 'remove-index'."""
    definition = wiz.definition.Definition(
        {
            "identifier": "foo",
            "requirements": [
                "bar >= 0.1.0, < 1",
                "bim >= 2.5, < 3"
            ],
        },
        path="/path/to/foo.json",
        registry_path="/path"

    )

    mocked_load_definition.return_value = definition

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main,
        [
            "edit", "/path/to/foo.json",
            "--remove-index", "requirements", "0"
        ]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")

    mocked_filesystem_export.assert_called_once_with(
        "/path/to/foo.json",
        (
            "{\n"
            "    \"identifier\": \"foo\",\n"
            "    \"requirements\": [\n"
            "        \"bim >= 2.5, < 3\"\n"
            "    ]\n"
            "}"
        ),
        overwrite=False
    )

    mocked_click_confirm.assert_not_called()
    mocked_click_edit.assert_not_called()
    mocked_history_record_action.assert_not_called()
    logger.error.assert_not_called()
    logger.warning.assert_not_called()

    assert logger.info.call_count == 2
    logger.info.assert_any_call("Edit 'foo'.")
    logger.info.assert_any_call("Saved 'foo' in /path/to/foo.json.")


@pytest.mark.usefixtures("mocked_system_query")
@pytest.mark.usefixtures("mocked_registry_fetch")
def test_edit_error_raised(
    mocked_load_definition, mocked_click_confirm, mocked_click_edit,
    mocked_history_record_action, mocked_filesystem_export, logger
):
    """Fail to edit definition when error is saved."""
    exception = Exception("Oh Shit!")
    mocked_load_definition.side_effect = exception

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["edit", "/path/to/foo.json"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == ""

    mocked_load_definition.assert_called_once_with("/path/to/foo.json")

    mocked_click_edit.assert_not_called()
    mocked_click_confirm.assert_not_called()
    mocked_filesystem_export.assert_not_called()

    logger.info.assert_not_called()
    logger.warning.assert_not_called()

    logger.error.assert_called_once_with("Oh Shit!")

    mocked_history_record_action.assert_called_once_with(
        "RAISE_EXCEPTION", error=exception
    )
