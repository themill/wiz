# :coding: utf-8

import os

import pytest

import wiz.command_line
import wiz.registry


@pytest.fixture()
def mock_fetch_registry(mocker):
    """Return mocked 'wiz.registry.fetch' function."""
    return mocker.patch.object(
        wiz.registry, "fetch",
        return_value=["/path/to/registry1", "/path/to/registry2"]
    )


@pytest.fixture()
def mock_fetch_definition_mapping(mocker):
    """Mock fetched definition mapping."""
    test1_020_item = {
        "registry": "/path/to/registry1"
    }
    test1_020 = mocker.Mock(
        identifier="test1",
        description="This is test1.",
        version="0.2.0",
        registry="/path/to/registry1",
        variants=[],
        **{"get": lambda key: test1_020_item[key]}
    )

    test1_010_item = {
        "registry": "/path/to/registry1"
    }
    test1_010 = mocker.Mock(
        identifier="test1",
        description="This is test1.",
        version="0.1.0",
        registry="/path/to/registry1",
        variants=[],
        **{"get": lambda key: test1_010_item[key]}
    )

    test2_010_item = {
        "registry": "/path/to/registry2"
    }
    test2_010 = mocker.Mock(
        identifier="test2",
        description="This is test2.",
        version="0.1.0",
        registry="/path/to/registry2",
        variants=[
            mocker.Mock(identifier="variant2"),
            mocker.Mock(identifier="variant1"),
        ],
        **{"get": lambda key: test2_010_item[key]}
    )

    test3_011_item = {
        "registry": "/path/to/registry2"
    }
    test3_011 = mocker.Mock(
        identifier="test3",
        description="This is test3.",
        version="0.1.1",
        registry="/path/to/registry2",
        variants=[],
        **{"get": lambda key: test3_011_item[key]}
    )

    test3_010_item = {
        "registry": "/path/to/registry1"
    }
    test3_010 = mocker.Mock(
        identifier="test3",
        description="This is test3.",
        version="0.1.0",
        registry="/path/to/registry1",
        variants=[],
        **{"get": lambda key: test3_010_item[key]}
    )

    mocker.patch.object(
        wiz, "fetch_definition_mapping",
        return_value={
            "command": {
                "app1": "test1",
                "app3": "test3",
            },
            "package": {
                "test1": {
                    "0.2.0": test1_020,
                    "0.1.0": test1_010,
                },
                "test2": {
                    "0.1.0": test2_010,
                },
                "test3": {
                    "0.1.1": test3_011,
                    "0.1.0": test3_010,
                }
            },
            "registries": ["/path/to/registry1", "/path/to/registry2"]
        }
    )


@pytest.fixture()
def mock_query_identifier(mocker):
    """Return mocked 'wiz.command_line._query_identifier' function."""
    mocker.patch.object(
        wiz.command_line, "_query_identifier", return_value="foo"
    )


@pytest.fixture()
def mock_query_description(mocker):
    """Return mocked 'wiz.command_line.mock_query_description' function."""
    mocker.patch.object(
        wiz.command_line, "_query_description", return_value="This is a test"
    )


@pytest.fixture()
def mock_query_command(mocker):
    """Return mocked 'wiz.command_line._query_command' function."""
    mocker.patch.object(
        wiz.command_line, "_query_command", return_value="AppExe"
    )


@pytest.fixture()
def mock_query_version(mocker):
    """Return mocked 'wiz.command_line._query_version' function."""
    mocker.patch.object(
        wiz.command_line, "_query_version", return_value="0.1.0"
    )


@pytest.fixture()
def mocked_resolve_context(mocker):
    """Return mocked 'wiz.resolve_context' function."""
    return mocker.patch.object(wiz, "resolve_context")


@pytest.fixture()
def mocked_fetch_definition_mapping(mocker):
    """Return mocked 'wiz.fetch_definition_mapping' function."""
    return mocker.patch.object(wiz, "fetch_definition_mapping")


def test_empty_arguments(capsys):
    """Raise error for empty arguments."""
    with pytest.raises(SystemExit):
        wiz.command_line.main()

    _, stderror_message = capsys.readouterr()
    assert "wiz: error: too few arguments" in stderror_message


@pytest.mark.usefixtures("mock_fetch_registry")
@pytest.mark.usefixtures("mock_fetch_definition_mapping")
def test_list_packages(capsys):
    """Display list of available packages."""
    wiz.command_line.main(["list", "package"])

    stdout_message, stderror_message = capsys.readouterr()
    assert stderror_message == ""
    assert stdout_message == (
        "\nRegistries            "
        "\n----------------------"
        "\n[0] /path/to/registry1"
        "\n[1] /path/to/registry2"
        "\n"
        "\n"
        "\nPackage            Version   Registry   Description   "
        "\n----------------   -------   --------   --------------"
        "\ntest1              0.2.0     0          This is test1."
        "\ntest2 [variant2]   0.1.0     1          This is test2."
        "\ntest2 [variant1]   0.1.0     1          This is test2."
        "\ntest3              0.1.1     1          This is test3."
        "\n\n"
    )


@pytest.mark.usefixtures("mock_fetch_registry")
@pytest.mark.usefixtures("mock_fetch_definition_mapping")
def test_list_packages_all(capsys):
    """Display list of available packages versions."""
    wiz.command_line.main(["list", "package", "--all"])

    stdout_message, stderror_message = capsys.readouterr()
    assert stderror_message == ""
    assert stdout_message == (
        "\nRegistries            "
        "\n----------------------"
        "\n[0] /path/to/registry1"
        "\n[1] /path/to/registry2"
        "\n"
        "\n"
        "\nPackage            Version   Registry   Description   "
        "\n----------------   -------   --------   --------------"
        "\ntest1              0.2.0     0          This is test1."
        "\ntest1              0.1.0     0          This is test1."
        "\ntest2 [variant2]   0.1.0     1          This is test2."
        "\ntest2 [variant1]   0.1.0     1          This is test2."
        "\ntest3              0.1.1     1          This is test3."
        "\ntest3              0.1.0     0          This is test3."
        "\n\n"
    )


@pytest.mark.usefixtures("mock_fetch_registry")
@pytest.mark.usefixtures("mock_fetch_definition_mapping")
def test_list_commands(capsys):
    """Display list of available commands."""
    wiz.command_line.main(["list", "command"])

    stdout_message, stderror_message = capsys.readouterr()
    assert stderror_message == ""
    assert stdout_message == (
        "\nRegistries            "
        "\n----------------------"
        "\n[0] /path/to/registry1"
        "\n[1] /path/to/registry2"
        "\n"
        "\n"
        "\nCommand   Version   Registry   Description   "
        "\n-------   -------   --------   --------------"
        "\napp1      0.2.0     0          This is test1."
        "\napp3      0.1.1     1          This is test3."
        "\n\n"
    )


@pytest.mark.usefixtures("mock_fetch_registry")
@pytest.mark.usefixtures("mock_fetch_definition_mapping")
def test_list_commands_all(capsys):
    """Display list of available commands versions."""
    wiz.command_line.main(["list", "command", "--all"])

    stdout_message, stderror_message = capsys.readouterr()
    assert stderror_message == ""
    assert stdout_message == (
        "\nRegistries            "
        "\n----------------------"
        "\n[0] /path/to/registry1"
        "\n[1] /path/to/registry2"
        "\n"
        "\n"
        "\nCommand   Version   Registry   Description   "
        "\n-------   -------   --------   --------------"
        "\napp1      0.2.0     0          This is test1."
        "\napp1      0.1.0     0          This is test1."
        "\napp3      0.1.1     1          This is test3."
        "\napp3      0.1.0     0          This is test3."
        "\n\n"
    )


@pytest.mark.usefixtures("mock_query_identifier")
@pytest.mark.usefixtures("mock_query_description")
@pytest.mark.usefixtures("mock_query_version")
def test_freeze_definition(
    temporary_directory,
    mocked_fetch_definition_mapping,
    mocked_resolve_context
):
    """Freeze a Wiz definition."""
    mocked_fetch_definition_mapping.return_value = "__DEFINITION_MAPPING__"
    mocked_resolve_context.return_value = {
        "command": {"app": "AppExe"},
        "environ": {"KEY": "VALUE"},
    }

    wiz.command_line.main(["freeze", "bim", "bar", "-o", temporary_directory])

    mocked_resolve_context.assert_called_once_with(
        ["bim", "bar"], "__DEFINITION_MAPPING__", ignore_implicit=False
    )

    file_path = os.path.join(temporary_directory, "foo-0.1.0.json")
    assert os.path.isfile(file_path) is True

    with open(file_path, "r") as stream:
        assert stream.read() == (
             "{\n"
             "    \"identifier\": \"foo\",\n"
             "    \"version\": \"0.1.0\",\n"
             "    \"description\": \"This is a test\",\n"
             "    \"command\": {\n"
             "        \"app\": \"AppExe\"\n"
             "    },\n"
             "    \"environ\": {\n"
             "        \"KEY\": \"VALUE\"\n"
             "    }\n"
             "}"
        )


@pytest.mark.usefixtures("mock_query_identifier")
@pytest.mark.usefixtures("mock_query_command")
def test_freeze_definition_csh(
    temporary_directory, mocker,
    mocked_fetch_definition_mapping,
    mocked_resolve_context
):
    """Freeze a Wiz definition into a CSH script."""
    mocked_fetch_definition_mapping.return_value = "__DEFINITION_MAPPING__"
    mocked_resolve_context.return_value = {
        "command": {"app": "AppExe"},
        "environ": {"KEY": "VALUE"},
        "packages": [
            mocker.Mock(identifier="test1==1.1.0", version="1.1.0"),
            mocker.Mock(identifier="test2==0.3.0", version="0.3.0"),
        ]
    }

    wiz.command_line.main([
        "freeze", "bim", "bar", "--format", "tcsh", "-o", temporary_directory
    ])

    mocked_resolve_context.assert_called_once_with(
        ["bim", "bar"], "__DEFINITION_MAPPING__", ignore_implicit=False
    )

    file_path = os.path.join(temporary_directory, "foo")
    assert os.path.isfile(file_path) is True

    with open(file_path, "r") as stream:
        assert stream.read() == (
            "#!/bin/tcsh -f\n"
            "#\n"
            "# Generated by wiz with the following environments:\n"
            "# - test1==1.1.0\n"
            "# - test2==0.3.0\n"
            "#\n"
            "setenv KEY \"VALUE\"\n"
            "AppExe $argv:q\n"
        )


@pytest.mark.usefixtures("mock_query_identifier")
@pytest.mark.usefixtures("mock_query_command")
def test_freeze_definition_bash(
    temporary_directory, mocker,
    mocked_fetch_definition_mapping,
    mocked_resolve_context
):
    """Freeze a Wiz definition into a Bash script."""
    mocked_fetch_definition_mapping.return_value = "__DEFINITION_MAPPING__"
    mocked_resolve_context.return_value = {
        "command": {"app": "AppExe"},
        "environ": {"KEY": "VALUE"},
        "packages": [
            mocker.Mock(identifier="test1==1.1.0", version="1.1.0"),
            mocker.Mock(identifier="test2==0.3.0", version="0.3.0"),
        ]
    }

    wiz.command_line.main([
        "freeze", "bim", "bar", "--format", "bash", "-o", temporary_directory
    ])

    mocked_resolve_context.assert_called_once_with(
        ["bim", "bar"], "__DEFINITION_MAPPING__", ignore_implicit=False
    )

    file_path = os.path.join(temporary_directory, "foo")
    assert os.path.isfile(file_path) is True

    with open(file_path, "r") as stream:
        assert stream.read() == (
            "#!/bin/bash\n"
            "#\n"
            "# Generated by wiz with the following environments:\n"
            "# - test1==1.1.0\n"
            "# - test2==0.3.0\n"
            "#\n"
            "export KEY=\"VALUE\"\n"
            "AppExe $@\n"
        )
