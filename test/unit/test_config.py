# :coding: utf-8

import getpass
import os
import socket

import pytest
import toml

import wiz.config


@pytest.fixture(autouse=True)
def environment(mocker, monkeypatch):
    """Mock environment to use when fetching config."""
    mocker.patch.object(socket, "gethostname", return_value="__HOSTNAME__")
    mocker.patch.object(getpass, "getuser", return_value="__USER__")
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")


@pytest.fixture()
def personal_plugin(mocker, temporary_directory):
    """Mock personal plugin path."""
    path = os.path.join(temporary_directory, ".wiz", "plugins")
    mocker.patch.object(os.path, "expanduser", return_value=temporary_directory)
    os.makedirs(path)

    plugin_path = os.path.join(path, "plugin.py")
    with open(plugin_path, "w") as stream:
        stream.write(
            "IDENTIFIER = \"plugin1\"\n"
            "\n"
            "def register(config):\n"
            "    config[\"KEY1\"] = \"VALUE1\"\n"
        )

    return plugin_path


@pytest.fixture()
def personal_configuration(mocker, temporary_directory):
    """Mock personal configuration."""
    data = {
        "registry": {"paths": ["/registry1"]},
        "environ": {"initial": {"ENVIRON_TEST1": "VALUE"}}
    }

    path = os.path.join(temporary_directory, ".wiz")
    mocker.patch.object(os.path, "expanduser", return_value=temporary_directory)
    os.makedirs(path)

    config_path = os.path.join(path, "config.toml")
    with open(config_path, "w") as stream:
        toml.dump(data, stream)

    return config_path


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
        "resolver": {
            "maximum_combinations": 10,
            "maximum_attempts": 15,
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


@pytest.mark.usefixtures("mocked_discover_plugins")
@pytest.mark.usefixtures("personal_configuration")
def test_fetch_with_personal():
    """Fetch configuration with personal configuration."""
    config = wiz.config.fetch(refresh=True)

    assert config == {
        "registry":  {"paths": ["/registry1"]},
        "environ": {
            "initial": {
                "ENVIRON_TEST1": "VALUE"
            },
            "passthrough": []
        },
        "resolver": {
            "maximum_combinations": 10,
            "maximum_attempts": 15,
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


@pytest.mark.usefixtures("mocked_discover_plugins")
def test_fetch_error(logger, personal_configuration):
    """Fail to fetch a configuration."""
    with open(personal_configuration, "w") as stream:
        stream.write("incorrect")

    wiz.config.fetch(refresh=True)

    logger.warning.assert_called_once_with(
        "Failed to load configuration from \"{0}\" [Key name found without "
        "value. Reached end of file. (line 1 column 10 char 9)]"
        .format(personal_configuration)
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

    assert logger.warning.call_count == 1
    args, _ = logger.warning.call_args
    assert (
       "Failed to register plugin from \"{0}\""
       .format(wiz.__file__)
    ) in args[0]


def test_discover_plugins(mocker):
    """Discover and return plugins."""
    plugins = wiz.config._discover_plugins()

    assert len(plugins) == 2
    assert sorted([p.IDENTIFIER for p in plugins]) == ["environ", "installer"]

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
                "USER": "__USER__",
                "PATH": (
                    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:"
                    "/sbin:/bin"
                )
            }
        }
    }


@pytest.mark.usefixtures("personal_plugin")
def test_discover_plugins_with_personal(mocker):
    """Discover and return plugins with personal plugin path."""
    plugins = wiz.config._discover_plugins()

    assert len(plugins) == 3
    assert sorted([p.IDENTIFIER for p in plugins]) == [
        "environ", "installer", "plugin1"
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
                "USER": "__USER__",
                "PATH": (
                    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:"
                    "/sbin:/bin"
                )
            }
        },
        "KEY1": "VALUE1"
    }


def test_discover_plugin_error(logger, personal_plugin):
    """Fail to register a plugin."""
    with open(personal_plugin, "w") as stream:
        stream.write("incorrect")

    wiz.config.fetch(refresh=True)

    logger.warning.assert_called_once_with(
        "Failed to load plugin from \"{0}\" [name 'incorrect' is not defined]"
        .format(personal_plugin)
    )
