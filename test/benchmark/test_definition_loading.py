# :coding: utf-8

"""
Loading a definition should take around few milliseconds maximum, as the tool
should be able to load >= 5000 definitions in less than a second.

"""

import os

import ujson
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


def test_load_minimal(temporary_directory, benchmark):
    """Load a minimal definition."""
    data = {"identifier": "foo"}

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        ujson.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_simple(temporary_directory, benchmark):
    """Load a simple definition."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "command": {
            "foo": "FooExe"
        },
        "environ": {
            "Key1": "Value1",
            "Key2": "Value2",
            "Key3": "Value3",
        },
        "requirements": [
            "fee >= 0.1.0, < 1",
            "bar >= 2.3, < 3",
            "bim != 6.0.0",
        ]
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        ujson.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_simple_with_variants(temporary_directory, benchmark):
    """Load a simple definition with variants."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "command": {
            "foo": "FooExe"
        },
        "environ": {
            "Key1": "Value1",
            "Key2": "Value2",
            "Key3": "Value3",
        },
        "requirements": [
            "fee >= 0.1.0, < 1",
            "bar >= 2.3, < 3",
            "bim != 6.0.0",
        ],
        "variants": [
            {
                "identifier": "V4",
                "requirements": [
                    "bew >= 4, < 5",
                ]
            },
            {
                "identifier": "V3",
                "requirements": [
                    "bew >= 3, < 4",
                ]
            },
            {
                "identifier": "V2",
                "requirements": [
                    "bew >= 2, < 3",
                ],
            },
            {
                "identifier": "V1",
                "requirements": [
                    "bew >= 1, < 2",
                ]
            }
        ]
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        ujson.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_many_environments(temporary_directory, benchmark):
    """Load a definition with 1000 environment variables."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "command": {
            "foo": "FooExe"
        },
        "environ": {
            "KEY{}".format(index): "VALUE{}".format(index)
            for index in range(1000)
        },
        "requirements": [
            "fee >= 0.1.0, < 1",
            "bar >= 2.3, < 3",
            "bim != 6.0.0",
        ]
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        ujson.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_many_requirements(temporary_directory, benchmark):
    """Load a definition with 100 requirements."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "command": {
            "foo": "FooExe"
        },
        "environ": {
            "Key1": "Value1",
            "Key2": "Value2",
            "Key3": "Value3",
        },
        "requirements": [
            "fee{}".format(index) for index in range(100)
        ]
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        ujson.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_many_variants(temporary_directory, benchmark):
    """Load a definition with 100 variants."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "command": {
            "foo": "FooExe"
        },
        "environ": {
            "Key1": "Value1",
            "Key2": "Value2",
            "Key3": "Value3",
        },
        "requirements": [
            "fee >= 0.1.0, < 1",
            "bar >= 2.3, < 3",
            "bim != 6.0.0",
        ],
        "variants": [
            {"identifier": "V{}".format(index)}
            for index in range(100)
        ]
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        ujson.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_many_complex_variants(temporary_directory, benchmark):
    """Load a definition with 100 complex variants."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "command": {
            "foo": "FooExe"
        },
        "environ": {
            "Key1": "Value1",
            "Key2": "Value2",
            "Key3": "Value3",
        },
        "requirements": [
            "fee >= 0.1.0, < 1",
            "bar >= 2.3, < 3",
            "bim != 6.0.0",
        ],
        "variants": [
            {
                "identifier": "V{}".format(index),
                "requirements": ["bew{}".format(index) for index in range(100)],
                "environ": {
                    "VAR_KEY{}".format(index): "VALUE{}".format(index)
                    for index in range(100)
                }
            }
            for index in range(100)
        ]
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        ujson.dump(data, stream)

    benchmark(wiz.definition.load, path)


def test_load_complex(temporary_directory, benchmark):
    """Load a complex definition."""
    data = {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition.",
        "command": {
            "foo": "FooExe"
        },
        "environ": {
            "KEY{}".format(index): "VALUE{}".format(index)
            for index in range(1000)
        },
        "requirements": [
            "fee{}".format(index) for index in range(100)
        ],
        "variants": [
            {
                "identifier": "V{}".format(index),
                "requirements": ["bew{}".format(index) for index in range(100)],
                "environ": {
                    "VAR_KEY{}".format(index): "VALUE{}".format(index)
                    for index in range(100)
                }
            }
            for index in range(100)
        ]
    }

    path = os.path.join(temporary_directory, "definition.json")
    with open(path, "w") as stream:
        ujson.dump(data, stream)

    benchmark(wiz.definition.load, path)
