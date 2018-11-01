# :coding: utf-8

import datetime

import pytest
from click.testing import CliRunner

import wiz.command_line
import wiz.registry
import wiz.symbol
import wiz.definition
import wiz.package
import wiz.spawn
import wiz.exception
import wiz.filesystem
import wiz.history
import wiz.utility


@pytest.fixture()
def mock_datetime_now(mocker):
    """Return mocked 'wiz.fetch_definition_mapping' function."""
    _date = mocker.Mock(**{"isoformat.return_value": "NOW"})
    return mocker.patch.object(
        datetime, "datetime", **{"now.return_value": _date}
    )


@pytest.fixture()
def mocked_fetch_definition_mapping(mocker):
    """Return mocked 'wiz.fetch_definition_mapping' function."""
    return mocker.patch.object(wiz, "fetch_definition_mapping")


@pytest.fixture()
def mocked_history_start_recording(mocker):
    """Return mocked 'wiz.history.start_recording' function."""
    return mocker.patch.object(wiz.history, "start_recording")


@pytest.fixture()
def mocked_history_get(mocker):
    """Return mocked 'wiz.history.get' function."""
    return mocker.patch.object(wiz.history, "get")


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
def definition_mapping():
    """Return mocked definition mapping."""
    return {
        "command": {
            "fooExe": "foo",
            "bimExe": "bim",
        },
        "package": {
            "foo": {
                "0.2.0": wiz.definition.Definition({
                    "identifier": "foo",
                    "version": "0.2.0",
                    "description": "This is Foo 0.2.0.",
                    "registry": "/path/to/registry1",
                }),
                "0.1.0": wiz.definition.Definition({
                    "identifier": "foo",
                    "version": "0.1.0",
                    "description": "This is Foo 0.1.0.",
                    "registry": "/path/to/registry1",
                }),
            },
            "bar": {
                "0.1.0": wiz.definition.Definition({
                    "identifier": "bar",
                    "version": "0.1.0",
                    "description": "This is Bar 0.1.0.",
                    "registry": "/path/to/registry2",
                    "variants": [
                        {"identifier": "Variant1"},
                        {"identifier": "Variant2"},
                    ]
                }),
            },
            "bim": {
                "0.1.1": wiz.definition.Definition({
                    "identifier": "bim",
                    "version": "0.1.1",
                    "description": "This is Bim 0.1.1.",
                    "registry": "/path/to/registry2",
                }),
                "0.1.0": wiz.definition.Definition({
                    "identifier": "bim",
                    "version": "0.1.0",
                    "description": "This is Bim 0.1.0.",
                    "registry": "/path/to/registry2",
                }),
            }
        },
        "registries": ["/path/to/registry1", "/path/to/registry2"]
    }


def test_empty_arguments(
    mocked_fetch_definition_mapping, mocked_history_start_recording,
    mocked_history_get, mocked_filesystem_export, mocked_system_query,
    mocked_registry_fetch
):
    """Do not raise error for empty arguments."""
    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main)
    assert result.exit_code == 0
    assert not result.exception

    mocked_fetch_definition_mapping.assert_not_called()
    mocked_history_start_recording.assert_not_called()
    mocked_history_get.assert_not_called()
    mocked_filesystem_export.assert_not_called()
    mocked_system_query.assert_not_called()
    mocked_registry_fetch.assert_not_called()


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
@pytest.mark.usefixtures("mocked_fetch_definition_mapping")
@pytest.mark.usefixtures("mocked_registry_fetch")
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
            ["-dsp", "/path1", "-dsp", "/path2"],
            ["/path1", "/path2"], None, True, True
        ),
        (["-dsd", "2"], None, 2, True, True),
        (["--no-local"], None, None, False, True),
        (["--no-cwd"], None, None, True, False),
    ], ids=[
        "no-options",
        "change-search-paths",
        "change-search-depth",
        "skip-local",
        "skip-cwd",
    ]
)
def test_fetch_registry(
    mocked_fetch_definition_mapping, mocked_system_query, mocked_registry_fetch,
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

    mocked_fetch_definition_mapping.assert_called_once_with(
        ["/registry1", "/registry2"],
        requests=None,
        system_mapping="__SYSTEM__",
        max_depth=depth
    )


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", "/path"], True)
], ids=[
    "normal",
    "history-recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
def test_list_packages_empty(
    mocked_fetch_definition_mapping, mocked_history_start_recording,
    mocked_history_get, mocked_filesystem_export, mocked_system_query,
    mocked_registry_fetch, options, recorded
):
    """Display empty list of packages."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_history_get.return_value = "__HISTORY__"
    mocked_registry_fetch.return_value = []
    mocked_fetch_definition_mapping.return_value = {
        "command": {},
        "package": {}
    }

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["list", "package"])
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

    mocked_fetch_definition_mapping.assert_called_once_with(
        [], requests=None, system_mapping="__SYSTEM__", max_depth=None
    )

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["list", "package"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            "/path/wiz-NOW.dump", "__HISTORY__", compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


@pytest.mark.usefixtures("mocked_system_query")
def test_list_packages(
    mocked_fetch_definition_mapping, mocked_registry_fetch, definition_mapping
):
    """Display list of available packages."""
    mocked_registry_fetch.return_value = [
        "/path/to/registry1",
        "/path/to/registry2",
    ]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["list", "package"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries            \n"
        "----------------------\n"
        "[0] /path/to/registry1\n"
        "[1] /path/to/registry2\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "bar [Variant1]   0.1.0     1          This is Bar 0.1.0.\n"
        "bar [Variant2]   0.1.0     1          This is Bar 0.1.0.\n"
        "bim              0.1.1     1          This is Bim 0.1.1.\n"
        "foo              0.2.0     0          This is Foo 0.2.0.\n"
        "\n"
    )


@pytest.mark.usefixtures("mocked_system_query")
def test_list_packages_with_versions(
    mocked_fetch_definition_mapping, mocked_registry_fetch, definition_mapping
):
    """Display list of available packages with versions."""
    mocked_registry_fetch.return_value = [
        "/path/to/registry1",
        "/path/to/registry2",
    ]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["list", "package", "--all"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries            \n"
        "----------------------\n"
        "[0] /path/to/registry1\n"
        "[1] /path/to/registry2\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "bar [Variant1]   0.1.0     1          This is Bar 0.1.0.\n"
        "bar [Variant2]   0.1.0     1          This is Bar 0.1.0.\n"
        "bim              0.1.1     1          This is Bim 0.1.1.\n"
        "bim              0.1.0     1          This is Bim 0.1.0.\n"
        "foo              0.2.0     0          This is Foo 0.2.0.\n"
        "foo              0.1.0     0          This is Foo 0.1.0.\n"
        "\n"
    )


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", "/path"], True)
], ids=[
    "normal",
    "history-recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
def test_list_commands_empty(
    mocked_fetch_definition_mapping, mocked_history_start_recording,
    mocked_history_get, mocked_filesystem_export, mocked_system_query,
    mocked_registry_fetch, options, recorded
):
    """Display empty list of commands."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_history_get.return_value = "__HISTORY__"
    mocked_registry_fetch.return_value = []
    mocked_fetch_definition_mapping.return_value = {
        "command": {},
        "package": {}
    }

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["list", "command"])
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

    mocked_fetch_definition_mapping.assert_called_once_with(
        [], requests=None, system_mapping="__SYSTEM__", max_depth=None
    )

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["list", "command"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            "/path/wiz-NOW.dump", "__HISTORY__", compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


@pytest.mark.usefixtures("mocked_system_query")
def test_list_commands(
    mocked_fetch_definition_mapping, mocked_registry_fetch, definition_mapping
):
    """Display list of available commands."""
    mocked_registry_fetch.return_value = [
        "/path/to/registry1",
        "/path/to/registry2",
    ]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["list", "command"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries            \n"
        "----------------------\n"
        "[0] /path/to/registry1\n"
        "[1] /path/to/registry2\n"
        "\n"
        "\n"
        "Command   Version   Registry   Description       \n"
        "-------   -------   --------   ------------------\n"
        "bimExe    0.1.1     1          This is Bim 0.1.1.\n"
        "fooExe    0.2.0     0          This is Foo 0.2.0.\n"
        "\n"
    )


@pytest.mark.usefixtures("mocked_system_query")
def test_list_commands_with_versions(
    mocked_fetch_definition_mapping, mocked_registry_fetch, definition_mapping
):
    """Display list of available commands with versions."""
    mocked_registry_fetch.return_value = [
        "/path/to/registry1",
        "/path/to/registry2",
    ]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, ["list", "command", "--all"])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries            \n"
        "----------------------\n"
        "[0] /path/to/registry1\n"
        "[1] /path/to/registry2\n"
        "\n"
        "\n"
        "Command   Version   Registry   Description       \n"
        "-------   -------   --------   ------------------\n"
        "bimExe    0.1.1     1          This is Bim 0.1.1.\n"
        "bimExe    0.1.0     1          This is Bim 0.1.0.\n"
        "fooExe    0.2.0     0          This is Foo 0.2.0.\n"
        "fooExe    0.1.0     0          This is Foo 0.1.0.\n"
        "\n"
    )


@pytest.mark.parametrize("options, recorded", [
    ([], False),
    (["--record", "/path"], True)
], ids=[
    "normal",
    "history-recorded",
])
@pytest.mark.usefixtures("mock_datetime_now")
def test_search_empty(
    mocked_fetch_definition_mapping, mocked_history_start_recording,
    mocked_history_get, mocked_filesystem_export, mocked_system_query,
    mocked_registry_fetch, logger, options, recorded
):
    """Display empty list of searched commands and packages."""
    mocked_system_query.return_value = "__SYSTEM__"
    mocked_history_get.return_value = "__HISTORY__"
    mocked_registry_fetch.return_value = []
    mocked_fetch_definition_mapping.return_value = {
        "command": {},
        "package": {}
    }

    runner = CliRunner()
    result = runner.invoke(wiz.command_line.main, options + ["search", "foo"])
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

    mocked_fetch_definition_mapping.assert_called_once_with(
        [], requests=["foo"], system_mapping="__SYSTEM__", max_depth=None
    )

    if recorded:
        mocked_history_start_recording.assert_called_once_with(
            command=" ".join(["wiz"] + options + ["search", "foo"])
        )
        mocked_history_get.assert_called_once_with(serialized=True)
        mocked_filesystem_export.assert_called_once_with(
            "/path/wiz-NOW.dump", "__HISTORY__", compressed=True
        )

    else:
        mocked_history_start_recording.assert_not_called()
        mocked_history_get.assert_not_called()
        mocked_filesystem_export.assert_not_called()


@pytest.mark.parametrize("options", [
    [], ["--type", "all"]
], ids=[
    "default",
    "with-option",
])
@pytest.mark.usefixtures("mocked_system_query")
def test_search_all(
    mocked_fetch_definition_mapping, mocked_registry_fetch, definition_mapping,
    options
):
    """Display searched list of available commands and packages."""
    mocked_registry_fetch.return_value = [
        "/path/to/registry1",
        "/path/to/registry2",
    ]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["search", "bim", "bar", "foo"] + options
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries            \n"
        "----------------------\n"
        "[0] /path/to/registry1\n"
        "[1] /path/to/registry2\n"
        "\n"
        "\n"
        "Command   Version   Registry   Description       \n"
        "-------   -------   --------   ------------------\n"
        "bimExe    0.1.1     1          This is Bim 0.1.1.\n"
        "fooExe    0.2.0     0          This is Foo 0.2.0.\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "bar [Variant1]   0.1.0     1          This is Bar 0.1.0.\n"
        "bar [Variant2]   0.1.0     1          This is Bar 0.1.0.\n"
        "bim              0.1.1     1          This is Bim 0.1.1.\n"
        "foo              0.2.0     0          This is Foo 0.2.0.\n"
        "\n"
    )


@pytest.mark.usefixtures("mocked_system_query")
def test_search_packages(
    mocked_fetch_definition_mapping, mocked_registry_fetch, definition_mapping
):
    """Display searched list of available packages."""
    mocked_registry_fetch.return_value = [
        "/path/to/registry1",
        "/path/to/registry2",
    ]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["search", "bim", "bar", "foo", "-t", "package"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries            \n"
        "----------------------\n"
        "[0] /path/to/registry1\n"
        "[1] /path/to/registry2\n"
        "\n"
        "\n"
        "Package          Version   Registry   Description       \n"
        "--------------   -------   --------   ------------------\n"
        "bar [Variant1]   0.1.0     1          This is Bar 0.1.0.\n"
        "bar [Variant2]   0.1.0     1          This is Bar 0.1.0.\n"
        "bim              0.1.1     1          This is Bim 0.1.1.\n"
        "foo              0.2.0     0          This is Foo 0.2.0.\n"
        "\n"
    )


@pytest.mark.usefixtures("mocked_system_query")
def test_search_commands(
    mocked_fetch_definition_mapping, mocked_registry_fetch, definition_mapping
):
    """Display searched list of available commands."""
    mocked_registry_fetch.return_value = [
        "/path/to/registry1",
        "/path/to/registry2",
    ]
    mocked_fetch_definition_mapping.return_value = definition_mapping

    runner = CliRunner()
    result = runner.invoke(
        wiz.command_line.main, ["search", "bim", "bar", "foo", "-t", "command"]
    )
    assert result.exit_code == 0
    assert not result.exception
    assert result.output == (
        "\n"
        "Registries            \n"
        "----------------------\n"
        "[0] /path/to/registry1\n"
        "[1] /path/to/registry2\n"
        "\n"
        "\n"
        "Command   Version   Registry   Description       \n"
        "-------   -------   --------   ------------------\n"
        "bimExe    0.1.1     1          This is Bim 0.1.1.\n"
        "fooExe    0.2.0     0          This is Foo 0.2.0.\n"
        "\n"
    )


# @pytest.fixture()
# def mock_fetch_registry(mocker):
#     """Return mocked 'wiz.registry.fetch' function."""
#     return mocker.patch.object(
#         wiz.registry, "fetch",
#         return_value=["/path/to/registry1", "/path/to/registry2"]
#     )
#
#
# @pytest.fixture()
# def mock_fetch_definition_mapping(mocker):
#     """Mock fetched definition mapping."""
#     mocker.patch.object(
#         wiz, "fetch_definition_mapping",
#         return_value={
#             "command": {
#                 "fooExe": "foo",
#                 "bimExe": "bim",
#             },
#             "package": {
#                 "foo": {
#                     "0.2.0": wiz.definition.Definition({
#                         "identifier": "foo",
#                         "version": "0.2.0",
#                         "description": "This is Foo 0.2.0.",
#                         "registry": "/path/to/registry1",
#                     }),
#                     "0.1.0": wiz.definition.Definition({
#                         "identifier": "foo",
#                         "version": "0.1.0",
#                         "description": "This is Foo 0.1.0.",
#                         "registry": "/path/to/registry1",
#                     }),
#                 },
#                 "bar": {
#                     "0.1.0": wiz.definition.Definition({
#                         "identifier": "bar",
#                         "version": "0.1.0",
#                         "description": "This is Bar 0.1.0.",
#                         "registry": "/path/to/registry2",
#                         "variants": [
#                             {"identifier": "Variant1"},
#                             {"identifier": "Variant2"},
#                         ]
#                     }),
#                 },
#                 "bim": {
#                     "0.1.1": wiz.definition.Definition({
#                         "identifier": "bim",
#                         "version": "0.1.1",
#                         "description": "This is Bim 0.1.1.",
#                         "registry": "/path/to/registry2",
#                     }),
#                     "0.1.0": wiz.definition.Definition({
#                         "identifier": "bim",
#                         "version": "0.1.0",
#                         "description": "This is Bim 0.1.0.",
#                         "registry": "/path/to/registry2",
#                     }),
#                 }
#             },
#             "registries": ["/path/to/registry1", "/path/to/registry2"]
#         }
#     )





#
# @pytest.fixture()
# def mock_query_identifier(mocker):
#     """Return mocked 'wiz.command_line._query_identifier' function."""
#     mocker.patch.object(
#         wiz.command_line, "_query_identifier", return_value="foo"
#     )
#
#
# @pytest.fixture()
# def mock_query_description(mocker):
#     """Return mocked 'wiz.command_line.mock_query_description' function."""
#     mocker.patch.object(
#         wiz.command_line, "_query_description", return_value="This is a test"
#     )
#
#
# @pytest.fixture()
# def mock_query_command(mocker):
#     """Return mocked 'wiz.command_line._query_command' function."""
#     mocker.patch.object(
#         wiz.command_line, "_query_command", return_value="AppExe"
#     )
#
#
# @pytest.fixture()
# def mock_query_version(mocker):
#     """Return mocked 'wiz.command_line._query_version' function."""
#     mocker.patch.object(
#         wiz.command_line, "_query_version", return_value="0.1.0"
#     )
#
#
# @pytest.fixture()
# def mocked_resolve_context(mocker):
#     """Return mocked 'wiz.resolve_context' function."""
#     return mocker.patch.object(wiz, "resolve_context")
#
#
# @pytest.fixture()
# def mocked_fetch_definition_mapping(mocker):
#     """Return mocked 'wiz.fetch_definition_mapping' function."""
#     return mocker.patch.object(wiz, "fetch_definition_mapping")
#
#
#
# @pytest.mark.usefixtures("mock_fetch_registry")
# @pytest.mark.usefixtures("mock_fetch_definition_mapping")
# def test_list_packages(capsys):
#     """Display list of available packages."""
#     wiz.command_line.main(["list", "package"])
#
#     stdout_message, stderror_message = capsys.readouterr()
#     assert stderror_message == ""
#     assert stdout_message == (
#         "\nRegistries            "
#         "\n----------------------"
#         "\n[0] /path/to/registry1"
#         "\n[1] /path/to/registry2"
#         "\n"
#         "\n"
#         "\nPackage            Version   Registry   Description   "
#         "\n----------------   -------   --------   --------------"
#         "\ntest1              0.2.0     0          This is test1."
#         "\ntest2 [variant2]   0.1.0     1          This is test2."
#         "\ntest2 [variant1]   0.1.0     1          This is test2."
#         "\ntest3              0.1.1     1          This is test3."
#         "\n\n"
#     )
#
#
# @pytest.mark.usefixtures("mock_fetch_registry")
# @pytest.mark.usefixtures("mock_fetch_definition_mapping")
# def test_list_packages_all(capsys):
#     """Display list of available packages versions."""
#     wiz.command_line.main(["list", "package", "--all"])
#
#     stdout_message, stderror_message = capsys.readouterr()
#     assert stderror_message == ""
#     assert stdout_message == (
#         "\nRegistries            "
#         "\n----------------------"
#         "\n[0] /path/to/registry1"
#         "\n[1] /path/to/registry2"
#         "\n"
#         "\n"
#         "\nPackage            Version   Registry   Description   "
#         "\n----------------   -------   --------   --------------"
#         "\ntest1              0.2.0     0          This is test1."
#         "\ntest1              0.1.0     0          This is test1."
#         "\ntest2 [variant2]   0.1.0     1          This is test2."
#         "\ntest2 [variant1]   0.1.0     1          This is test2."
#         "\ntest3              0.1.1     1          This is test3."
#         "\ntest3              0.1.0     0          This is test3."
#         "\n\n"
#     )
#
#
# @pytest.mark.usefixtures("mock_fetch_registry")
# @pytest.mark.usefixtures("mock_fetch_definition_mapping")
# def test_list_commands(capsys):
#     """Display list of available commands."""
#     wiz.command_line.main(["list", "command"])
#
#     stdout_message, stderror_message = capsys.readouterr()
#     assert stderror_message == ""
#     assert stdout_message == (
#         "\nRegistries            "
#         "\n----------------------"
#         "\n[0] /path/to/registry1"
#         "\n[1] /path/to/registry2"
#         "\n"
#         "\n"
#         "\nCommand   Version   Registry   Description   "
#         "\n-------   -------   --------   --------------"
#         "\napp1      0.2.0     0          This is test1."
#         "\napp3      0.1.1     1          This is test3."
#         "\n\n"
#     )
#
#
# @pytest.mark.usefixtures("mock_fetch_registry")
# @pytest.mark.usefixtures("mock_fetch_definition_mapping")
# def test_list_commands_all(capsys):
#     """Display list of available commands versions."""
#     wiz.command_line.main(["list", "command", "--all"])
#
#     stdout_message, stderror_message = capsys.readouterr()
#     assert stderror_message == ""
#     assert stdout_message == (
#         "\nRegistries            "
#         "\n----------------------"
#         "\n[0] /path/to/registry1"
#         "\n[1] /path/to/registry2"
#         "\n"
#         "\n"
#         "\nCommand   Version   Registry   Description   "
#         "\n-------   -------   --------   --------------"
#         "\napp1      0.2.0     0          This is test1."
#         "\napp1      0.1.0     0          This is test1."
#         "\napp3      0.1.1     1          This is test3."
#         "\napp3      0.1.0     0          This is test3."
#         "\n\n"
#     )
#
#
# @pytest.mark.usefixtures("mock_query_identifier")
# @pytest.mark.usefixtures("mock_query_description")
# @pytest.mark.usefixtures("mock_query_version")
# def test_freeze_definition(
#     temporary_directory,
#     mocked_fetch_definition_mapping,
#     mocked_resolve_context
# ):
#     """Freeze a Wiz definition."""
#     mocked_fetch_definition_mapping.return_value = "__DEFINITION_MAPPING__"
#     mocked_resolve_context.return_value = {
#         "command": {"app": "AppExe"},
#         "environ": {"KEY": "VALUE"},
#     }
#
#     wiz.command_line.main(["freeze", "bim", "bar", "-o", temporary_directory])
#
#     mocked_resolve_context.assert_called_once_with(
#         ["bim", "bar"], "__DEFINITION_MAPPING__", ignore_implicit=False
#     )
#
#     file_path = os.path.join(temporary_directory, "foo-0.1.0.json")
#     assert os.path.isfile(file_path) is True
#
#     with open(file_path, "r") as stream:
#         assert stream.read() == (
#              "{\n"
#              "    \"identifier\": \"foo\",\n"
#              "    \"version\": \"0.1.0\",\n"
#              "    \"description\": \"This is a test\",\n"
#              "    \"command\": {\n"
#              "        \"app\": \"AppExe\"\n"
#              "    },\n"
#              "    \"environ\": {\n"
#              "        \"KEY\": \"VALUE\"\n"
#              "    }\n"
#              "}"
#         )
#
#
# @pytest.mark.usefixtures("mock_query_identifier")
# @pytest.mark.usefixtures("mock_query_command")
# def test_freeze_definition_csh(
#     temporary_directory, mocker,
#     mocked_fetch_definition_mapping,
#     mocked_resolve_context
# ):
#     """Freeze a Wiz definition into a CSH script."""
#     mocked_fetch_definition_mapping.return_value = "__DEFINITION_MAPPING__"
#     mocked_resolve_context.return_value = {
#         "command": {"app": "AppExe"},
#         "environ": {"KEY": "VALUE"},
#         "packages": [
#             mocker.Mock(identifier="test1==1.1.0", version="1.1.0"),
#             mocker.Mock(identifier="test2==0.3.0", version="0.3.0"),
#         ]
#     }
#
#     wiz.command_line.main([
#         "freeze", "bim", "bar", "--format", "tcsh", "-o", temporary_directory
#     ])
#
#     mocked_resolve_context.assert_called_once_with(
#         ["bim", "bar"], "__DEFINITION_MAPPING__", ignore_implicit=False
#     )
#
#     file_path = os.path.join(temporary_directory, "foo")
#     assert os.path.isfile(file_path) is True
#
#     with open(file_path, "r") as stream:
#         assert stream.read() == (
#             "#!/bin/tcsh -f\n"
#             "#\n"
#             "# Generated by wiz with the following environments:\n"
#             "# - test1==1.1.0\n"
#             "# - test2==0.3.0\n"
#             "#\n"
#             "setenv KEY \"VALUE\"\n"
#             "AppExe $argv:q\n"
#         )
#
#
# @pytest.mark.usefixtures("mock_query_identifier")
# @pytest.mark.usefixtures("mock_query_command")
# def test_freeze_definition_bash(
#     temporary_directory, mocker,
#     mocked_fetch_definition_mapping,
#     mocked_resolve_context
# ):
#     """Freeze a Wiz definition into a Bash script."""
#     mocked_fetch_definition_mapping.return_value = "__DEFINITION_MAPPING__"
#     mocked_resolve_context.return_value = {
#         "command": {"app": "AppExe"},
#         "environ": {"KEY": "VALUE"},
#         "packages": [
#             mocker.Mock(identifier="test1==1.1.0", version="1.1.0"),
#             mocker.Mock(identifier="test2==0.3.0", version="0.3.0"),
#         ]
#     }
#
#     wiz.command_line.main([
#         "freeze", "bim", "bar", "--format", "bash", "-o", temporary_directory
#     ])
#
#     mocked_resolve_context.assert_called_once_with(
#         ["bim", "bar"], "__DEFINITION_MAPPING__", ignore_implicit=False
#     )
#
#     file_path = os.path.join(temporary_directory, "foo")
#     assert os.path.isfile(file_path) is True
#
#     with open(file_path, "r") as stream:
#         assert stream.read() == (
#             "#!/bin/bash\n"
#             "#\n"
#             "# Generated by wiz with the following environments:\n"
#             "# - test1==1.1.0\n"
#             "# - test2==0.3.0\n"
#             "#\n"
#             "export KEY=\"VALUE\"\n"
#             "AppExe $@\n"
#         )
