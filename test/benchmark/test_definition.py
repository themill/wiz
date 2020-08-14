# :coding: utf-8

import os
import json

import pytest

import wiz
import wiz.config
import wiz.definition


@pytest.fixture(autouse=True)
def reset_configuration(mocker):
    """Ensure that no personal configuration is fetched during tests."""
    mocker.patch.object(os.path, "expanduser", return_value="__HOME__")

    # Reset configuration.
    wiz.config.fetch(refresh=True)


def test_load_simple(temporary_directory, benchmark):
    """Load a simple definition."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "environ": {
            "Key": "Value"
        }
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        json.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_100_variables(temporary_directory, benchmark):
    """Load a big definition."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "environ": {
            "KEY{}".format(index): "VALUE{}".format(index)
            for index in range(100)
        }
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        json.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_1000_variables(temporary_directory, benchmark):
    """Load a big definition."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "environ": {
            "KEY{}".format(index): "VALUE{}".format(index)
            for index in range(1000)
        }
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        json.dump(data, stream)

    benchmark(wiz.definition.load, path)
