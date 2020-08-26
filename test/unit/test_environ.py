# :coding: utf-8

import getpass
import os
import socket

import pytest

import wiz.config
import wiz.environ


@pytest.fixture()
def initial_environment(mocker):
    """Mock environment to use when fetching config."""
    mocker.patch.object(socket, "gethostname", return_value="__HOSTNAME__")
    mocker.patch.object(getpass, "getuser", return_value="__USER__")
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


@pytest.mark.usefixtures("initial_environment")
def test_initiate():
    """Return initial data mapping."""
    assert wiz.environ.initiate() == {
        "USER": "__USER__",
        "HOME": "__HOME__",
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
def test_initiate_with_config_passthrough(monkeypatch):
    """Return initial data mapping with passthrough environment variables."""
    monkeypatch.setenv("ENVIRON_TEST1", "VALUE")
    monkeypatch.delenv("ENVIRON_TEST2", raising=False)

    # Add passthrough list in config.
    config = wiz.config.fetch()
    config["environ"]["passthrough"] = ["ENVIRON_TEST1", "ENVIRON_TEST2"]

    assert wiz.environ.initiate() == {
        "ENVIRON_TEST1": "VALUE",
        "USER": "__USER__",
        "HOME": "__HOME__",
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
def test_initiate_with_config_initial():
    """Return initial data mapping with passthrough environment variables."""
    # Add initial mapping in config.
    config = wiz.config.fetch()
    config["environ"]["initial"] = {"ENVIRON_TEST1": "VALUE"}

    assert wiz.environ.initiate() == {"ENVIRON_TEST1": "VALUE"}


@pytest.mark.usefixtures("initial_environment")
def test_initiate_with_mapping():
    """Return mapping with initial data mapping."""
    assert wiz.environ.initiate(
        mapping={
            "HOSTNAME": "__OTHER_HOSTNAME__",
            "KEY": "VALUE"
        }
    ) == {
        "USER": "__USER__",
        "HOME": "__HOME__",
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


def test_sanitize():
    """Return sanitized environment mapping"""
    assert wiz.environ.sanitize({
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

    assert wiz.environ.sanitize({
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
