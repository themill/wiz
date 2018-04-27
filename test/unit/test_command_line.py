# :coding: utf-8

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
def mock_definition_mapping(mocker):
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
            }
        }
    )


@pytest.mark.usefixtures("mock_fetch_registry")
@pytest.mark.usefixtures("mock_definition_mapping")
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
@pytest.mark.usefixtures("mock_definition_mapping")
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
@pytest.mark.usefixtures("mock_definition_mapping")
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
@pytest.mark.usefixtures("mock_definition_mapping")
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
