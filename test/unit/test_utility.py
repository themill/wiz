# :coding: utf-8

import pytest

import wiz.definition
import wiz.utility


@pytest.mark.parametrize("element", [
    "This is a string",
    42,
    ["This", "is", "a", "list"],
    {"key": "value"},
    {
        "key1": ["This", "is", "a", "list", 42],
        "key2": {"test": "This is a test"},
        "key3": 1337
    }
], ids=[
    "string",
    "number",
    "list",
    "dict",
    "complex-dict",
])
def test_encode_and_decode(element):
    """Encode *element* and immediately decode it."""
    encoded = wiz.utility.encode(element)
    assert isinstance(encoded, basestring)
    assert element == wiz.utility.decode(encoded)


@pytest.mark.parametrize("definition, expected", [
    (
        wiz.definition.Definition({"identifier": "test"}),
        "'test'"
    ),
    (
        wiz.definition.Definition({
            "identifier": "test",
            "version": "0.1.0"
        }),
        "'test' [0.1.0]"
    ),
    (
        wiz.definition.Definition({
            "identifier": "test",
            "namespace": "foo"
        }),
        "'foo::test'"
    ),
    (
        wiz.definition.Definition({
            "identifier": "test",
            "system": {
                "platform": "linux"
            }
        }),
        "'test' (linux)"
    ),
    (
        wiz.definition.Definition({
            "identifier": "test",
            "version": "0.1.0",
            "namespace": "foo",
            "system": {
                "platform": "linux"
            }
        }),
        "'foo::test' [0.1.0] (linux)"
    )
], ids=[
    "simple",
    "with-version",
    "with-namespace",
    "with-system",
    "with-all",
])
def test_compute_label(definition, expected):
    """Compute definition label."""
    assert wiz.utility.compute_label(definition) == expected
