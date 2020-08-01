# :coding: utf-8

import getpass
import os
import socket

import pytest
import toml

import wiz.config


@pytest.fixture(autouse=True)
def reset_configuration(mocker, monkeypatch):
    """Ensure that no external configuration is fetched."""
    monkeypatch.delenv("WIZ_CONFIG_PATHS", raising=False)
    monkeypatch.delenv("WIZ_PLUGIN_PATHS", raising=False)

    mocker.patch.object(socket, "gethostname", return_value="__HOSTNAME__")
    mocker.patch.object(getpass, "getuser", return_value="someone")
    mocker.patch.object(os.path, "expanduser", return_value="/home")


@pytest.fixture()
def mock_personal_plugin(mocker, temporary_directory):
    """Mock personal plugin."""
    path = os.path.join(temporary_directory, ".wiz", "plugins")
    mocker.patch.object(os.path, "expanduser", return_value=temporary_directory)
    os.makedirs(path)

    with open(os.path.join(path, "plugin.py"), "w") as stream:
        stream.write(
            "IDENTIFIER = \"plugin1\"\n"
            "\n"
            "def register(config):\n"
            "    config[\"KEY1\"] = \"VALUE\"\n"
        )


@pytest.fixture()
def mock_personal_configuration(mocker, temporary_directory):
    """Mock personal configuration."""
    data = {
        "registry": {"paths": ["/registry1"]},
        "environ": {"initial": {"ENVIRON_TEST1": "VALUE"}}
    }

    path = os.path.join(temporary_directory, ".wiz")
    mocker.patch.object(os.path, "expanduser", return_value=temporary_directory)
    os.makedirs(path)

    with open(os.path.join(path, "config.toml"), "w") as stream:
        toml.dump(data, stream)


@pytest.fixture()
def mock_configurations(monkeypatch, temporary_directory):
    """Mock configurations set via environment variable."""
    config1 = os.path.join(temporary_directory, "config1.toml")
    data1 = {
        "registry": {"paths": ["/registry2"]},
        "environ": {"initial": {"ENVIRON_TEST1": "VALUE1"}}
    }
    with open(config1, "w") as stream:
        toml.dump(data1, stream)

    config2 = os.path.join(temporary_directory, "config2.toml")
    data2 = {
        "registry": {"paths": ["/registry3"]},
        "environ": {"initial": {"ENVIRON_TEST2": "VALUE2"}}
    }
    with open(config2, "w") as stream:
        toml.dump(data2, stream)

    monkeypatch.setenv(
        "WIZ_CONFIG_PATHS", "{}:{}::/dummy".format(config1, config2)
    )


@pytest.fixture()
def mock_plugins(monkeypatch, temporary_directory):
    """Mock plugins set via environment variable."""
    path = os.path.join(temporary_directory, "plugins")
    os.makedirs(path)

    plugin1 = os.path.join(path, "plugin1.py")
    with open(plugin1, "w") as stream:
        stream.write(
            "IDENTIFIER = \"plugin1\"\n"
            "\n"
            "def register(config):\n"
            "    config[\"KEY1\"] = \"VALUE1\"\n"
        )

    plugin2 = os.path.join(path, "plugin2.py")
    with open(plugin2, "w") as stream:
        stream.write(
            "IDENTIFIER = \"plugin2\"\n"
            "\n"
            "def register(config):\n"
            "    config[\"KEY2\"] = \"VALUE2\"\n"
        )

    monkeypatch.setenv("WIZ_PLUGIN_PATHS", "{}::/dummy".format(path))


@pytest.fixture()
def mocked_discover_plugins(mocker):
    """Return mocked 'wiz.config._discover_plugins' function."""
    return mocker.patch.object(wiz.config, "_discover_plugins", return_value=[])


@pytest.mark.usefixtures("mocked_discover_plugins")
def test_fetch():
    """Fetch configuration."""
    config = wiz.config.fetch(refresh=True)

    assert config == {
        "registry":  {"paths": []},
        "environ": {
            "initial": {},
            "passthrough": []
        },
        "command": {
            "max_content_width": 90,
            "verbosity": "info",
            "no_local": False,
            "no_cwd": False,
            "ignore_implicit": False,
            "list": {
                "package": {
                    "all": False,
                    "no_arch": False
                },
                "command": {
                    "all": False,
                    "no_arch": False
                },
            },
            "search": {
                "all": False,
                "no_arch": False,
                "type": "all"
            },
            "view": {
                "json_view": False
            },
            "freeze": {
                "format": "wiz"
            },
            "install": {
                "overwrite": False
            },
            "edit": {
                "overwrite": False
            },
            "analyze": {
                "no_arch": False,
                "verbose": False,
            }
        }
    }

    # The previous config is returned without forcing a 'refreshed' config.
    del config["command"]
    assert wiz.config.fetch().get("command") is None
    assert wiz.config.fetch(refresh=True).get("command") is not None


@pytest.mark.usefixtures("mock_personal_configuration")
@pytest.mark.usefixtures("mock_configurations")
@pytest.mark.usefixtures("mocked_discover_plugins")
def test_fetch_multiples():
    """Fetch multiple configurations."""
    config = wiz.config.fetch(refresh=True)

    assert config["registry"] == {
        "paths": ["/registry3", "/registry2", "/registry1"]
    }
    assert config["environ"] == {
        "initial": {
            "ENVIRON_TEST1": "VALUE",
            "ENVIRON_TEST2": "VALUE2",
        },
        "passthrough": []
    }


@pytest.mark.usefixtures("mocked_discover_plugins")
def test_fetch_error(logger, monkeypatch, temporary_file):
    """Fail to fetch a configuration."""
    with open(temporary_file, "w") as stream:
        stream.write("incorrect")

    monkeypatch.setenv("WIZ_CONFIG_PATHS", temporary_file)

    wiz.config.fetch(refresh=True)

    logger.warning.assert_called_once_with(
        "Failed to load configuration from \"{0}\" [Key name found without "
        "value. Reached end of file. (line 1 column 10 char 9)]"
        .format(temporary_file)
    )


def test_fetch_with_plugin(mocker, mocked_discover_plugins):
    """Register plugin after fetching config."""
    def _register(_config):
        """Register config"""
        _config["registry"] = "__NEW_REGISTRY__"

    plugin = mocker.Mock(register=_register)
    mocked_discover_plugins.return_value = [plugin]

    config = wiz.config.fetch(refresh=True)
    assert config["registry"] == "__NEW_REGISTRY__"


def test_fetch_with_plugin_error(logger, mocked_discover_plugins):
    """Fail to register a plugin."""
    mocked_discover_plugins.return_value = [wiz]

    wiz.config.fetch(refresh=True)

    logger.warning.assert_called_once_with(
        "Failed to register plugin from \"{0}\" ['module' object has no "
        "attribute 'register']"
        .format(wiz.__file__)
    )


@pytest.mark.usefixtures("mock_personal_plugin")
@pytest.mark.usefixtures("mock_plugins")
def test_discover_plugins(mocker):
    """Discover and return plugins."""
    plugins = wiz.config._discover_plugins()

    assert len(plugins) == 4
    assert [p.IDENTIFIER for p in plugins] == [
        "installer", "environ", "plugin2", "plugin1"
    ]

    config = {}
    for plugin in plugins:
        plugin.register(config)

    assert config == {
        "callback": {
            "install": mocker.ANY
        },
        "environ": {
            "initial": {
                "HOME": mocker.ANY,
                "HOSTNAME": "__HOSTNAME__",
                "USER": "someone",
                "PATH": (
                    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:"
                    "/sbin:/bin"
                )
            }
        },
        "KEY1": "VALUE",
        "KEY2": "VALUE2",
    }
