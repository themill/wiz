# :coding: utf-8

import getpass
import os
import socket

import pytest

import wiz.config
import wiz.environ


@pytest.fixture()
def initial_environment(mocker, monkeypatch):
    """Set mocked initial environment."""
    monkeypatch.delenv("WIZ_CONFIG_PATHS", raising=False)
    monkeypatch.delenv("WIZ_PLUGIN_PATHS", raising=False)

    mocker.patch.object(socket, "gethostname", return_value="__HOSTNAME__")
    mocker.patch.object(getpass, "getuser", return_value="someone")
    mocker.patch.object(os.path, "expanduser", return_value="/home")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


@pytest.mark.usefixtures("initial_environment")
def test_initiate():
    """Return initial data mapping."""
    assert wiz.environ.initiate() == {
        "USER": "someone",
        "HOME": "/home",
        "HOSTNAME": "__HOSTNAME__",
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }


@pytest.mark.usefixtures("initial_environment")
def test_initiate_with_mapping():
    """Return mapping with initial data mapping."""
    assert wiz.environ.initiate(
        mapping={
            "HOSTNAME": "__OTHER_HOSTNAME__",
            "KEY": "VALUE"
        }
    ) == {
        "USER": "someone",
        "HOME": "/home",
        "HOSTNAME": "__OTHER_HOSTNAME__",
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ]),
        "KEY": "VALUE"
    }


def test_sanitise():
    """Return sanitised environment mapping"""
    assert wiz.environ.sanitise({
        "PLUGINS_A": "/path/to/plugin1:/path/to/plugin2:${PLUGINS_A}",
        "PLUGINS_B": "${PLUGINS_B}:/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_C": "/path/to/plugin1:${PLUGINS_C}:/path/to/plugin2",
        "PLUGINS_D": "${PLUGINS_C}:${PLUGINS_D}",
        "KEY1": "HELLO",
        "KEY2": "${KEY1} WORLD!",
        "KEY3": "${UNKNOWN}"
    }) == {
        "PLUGINS_A": "/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_B": "/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_C": "/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_D": "/path/to/plugin1:/path/to/plugin2",
        "KEY1": "HELLO",
        "KEY2": "HELLO WORLD!",
        "KEY3": "${UNKNOWN}"
    }

    assert wiz.environ.sanitise({
        "PLUGINS_A": "/path/to/plugin1:/path/to/plugin2:$PLUGINS_A",
        "PLUGINS_B": "$PLUGINS_B:/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_C": "/path/to/plugin1:$PLUGINS_C:/path/to/plugin2",
        "PLUGINS_D": "$PLUGINS_C:$PLUGINS_D",
        "KEY1": "HELLO",
        "KEY2": "$KEY1 WORLD!",
        "KEY3": "$UNKNOWN"
    }) == {
        "PLUGINS_A": "/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_B": "/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_C": "/path/to/plugin1:/path/to/plugin2",
        "PLUGINS_D": "/path/to/plugin1:/path/to/plugin2",
        "KEY1": "HELLO",
        "KEY2": "HELLO WORLD!",
        "KEY3": "$UNKNOWN"
    }


def test_contains():
    """Indicate whether *text* contains a reference to variable."""
    assert wiz.environ.contains("$HOME/to/data", "HOME") is True
    assert wiz.environ.contains("${HOME}/to/data", "HOME") is True
    assert wiz.environ.contains("$PATH/to/data", "HOME") is False


@pytest.mark.parametrize("text, expected", [
    ("$HOME/to/data", "/usr/people/me/to/data"),
    ("${HOME}/to/data", "/usr/people/me/to/data"),
    ("$HOME/to/$OS/data", "/usr/people/me/to/centos/data"),
    ("$HOME/to/${OS}/data", "/usr/people/me/to/centos/data"),
], ids=[
    "one-variable",
    "one-variable-with-curly-brackets",
    "several-variables",
    "several-variables-mixed",
])
def test_substitute(text, expected):
    """Substitute all environment variables in *text* from environment."""
    environment = {
        "HOME": "/usr/people/me",
        "OS": "centos"
    }
    assert wiz.environ.substitute(text, environment) == expected
