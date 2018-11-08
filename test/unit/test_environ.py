# :coding: utf-8

import os
import socket

import pytest

import wiz.environ


@pytest.fixture()
def mocked_socket_gethostname(mocker):
    """Return mocked 'socket.gethostname' getter."""
    return mocker.patch.object(socket, "gethostname")


def test_initiate(monkeypatch, mocked_socket_gethostname):
    """Return initial data mapping."""
    monkeypatch.setenv("USER", "someone")
    monkeypatch.setenv("LOGNAME", "someone")
    monkeypatch.setenv("HOME", "/path/to/somewhere")
    monkeypatch.setenv("DISPLAY", "localhost:0.0")
    monkeypatch.setenv("XAUTHORITY", "/run/gdm/auth/database")
    mocked_socket_gethostname.return_value = "__HOSTNAME__"

    assert wiz.environ.initiate() == {
        "USER": "someone",
        "LOGNAME": "someone",
        "HOME": "/path/to/somewhere",
        "HOSTNAME": "__HOSTNAME__",
        "DISPLAY": "localhost:0.0",
        "XAUTHORITY": "/run/gdm/auth/database",
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }


def test_initiate_with_mapping(
    monkeypatch, mocked_socket_gethostname
):
    """Return mapping with initial data mapping."""
    monkeypatch.setenv("USER", "someone")
    monkeypatch.setenv("LOGNAME", "someone")
    monkeypatch.setenv("HOME", "/path/to/somewhere")
    monkeypatch.setenv("DISPLAY", "localhost:0.0")
    monkeypatch.setenv("XAUTHORITY", "/run/gdm/auth/database")
    mocked_socket_gethostname.return_value = "__HOSTNAME__"

    assert wiz.environ.initiate(
        mapping={
            "LOGNAME": "someone-else",
            "KEY": "VALUE"
        }
    ) == {
        "USER": "someone",
        "LOGNAME": "someone-else",
        "HOME": "/path/to/somewhere",
        "HOSTNAME": "__HOSTNAME__",
        "DISPLAY": "localhost:0.0",
        "XAUTHORITY": "/run/gdm/auth/database",
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
