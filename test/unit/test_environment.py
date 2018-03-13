# :coding: utf-8

import os
import pytest

from packaging.requirements import Requirement

from wiz import __version__
import wiz.definition
import wiz.environment
import wiz.graph
import wiz.exception


@pytest.fixture()
def environment_mapping():
    """Return mocked environment mapping."""
    return {
        "env1": {
            "0.3.4": wiz.definition.Environment({
                "identifier": "env1",
                "version": "0.3.4",
                "description": "A test environment named 'env1'."
            }),
            "0.3.0": wiz.definition.Environment({
                "identifier": "env1",
                "version": "0.3.0",
                "description": "A test environment named 'env1'."
            }),
            "0.2.0": wiz.definition.Environment({
                "identifier": "env1",
                "version": "0.2.0",
                "description": "A test environment named 'env1'."
            }),
            "0.1.0": wiz.definition.Environment({
                "identifier": "env1",
                "version": "0.1.0",
                "description": "A test environment named 'env1'."
            }),
        },
        "env2": {
            "0.3.0": wiz.definition.Environment({
                "identifier": "env2",
                "version": "0.3.0",
                "description": "A test environment named 'env2'."
            }),
            "0.1.5": wiz.definition.Environment({
                "identifier": "env2",
                "version": "0.1.5",
                "description": "A test environment named 'env2'."
            }),
            "0.1.0": wiz.definition.Environment({
                "identifier": "env2",
                "version": "0.1.0",
                "description": "A test environment named 'env2'."
            }),
        },
    }


def test_get_environment(environment_mapping):
    """Return best matching environment environment from requirement."""
    requirement = Requirement("env1")
    assert (
        wiz.environment.get(requirement, environment_mapping) ==
        environment_mapping["env1"]["0.3.4"]
    )

    requirement = Requirement("env2")
    assert (
        wiz.environment.get(requirement, environment_mapping) ==
        environment_mapping["env2"]["0.3.0"]
    )

    requirement = Requirement("env1<0.2")
    assert (
        wiz.environment.get(requirement, environment_mapping) ==
        environment_mapping["env1"]["0.1.0"]
    )

    requirement = Requirement("env2==0.1.5")
    assert (
        wiz.environment.get(requirement, environment_mapping) ==
        environment_mapping["env2"]["0.1.5"]
    )


def test_get_environment_name_error(environment_mapping):
    """Fails to get the environment name."""
    requirement = Requirement("incorrect")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.environment.get(requirement, environment_mapping)


def test_get_environment_version_error(environment_mapping):
    """Fails to get the environment version."""
    requirement = Requirement("env1>10")

    with pytest.raises(wiz.exception.RequestNotFound):
        wiz.environment.get(requirement, environment_mapping)


def test_initiate_data(monkeypatch):
    """Return initial data mapping."""
    monkeypatch.setenv("USER", "someone")
    monkeypatch.setenv("LOGNAME", "someone")
    monkeypatch.setenv("HOME", "/path/to/somewhere")
    monkeypatch.setenv("DISPLAY", "localhost:0.0")

    assert wiz.environment.initiate_data() == {
        "WIZ_VERSION": __version__,
        "USER": "someone",
        "LOGNAME": "someone",
        "HOME": "/path/to/somewhere",
        "DISPLAY": "localhost:0.0",
        "PATH": os.pathsep.join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }


def test_initiate_data_with_initial_data(monkeypatch):
    """Return initial data mapping with initial data mapping."""
    monkeypatch.setenv("USER", "someone")
    monkeypatch.setenv("LOGNAME", "someone")
    monkeypatch.setenv("HOME", "/path/to/somewhere")
    monkeypatch.setenv("DISPLAY", "localhost:0.0")

    assert wiz.environment.initiate_data(
        data_mapping={
            "LOGNAME": "someone-else",
            "KEY": "VALUE"
        }
    ) == {
        "WIZ_VERSION": __version__,
        "USER": "someone",
        "LOGNAME": "someone-else",
        "HOME": "/path/to/somewhere",
        "DISPLAY": "localhost:0.0",
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
