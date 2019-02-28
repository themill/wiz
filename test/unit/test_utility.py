# :coding: utf-8

import pytest

import wiz.definition
import wiz.utility
from wiz.utility import Requirement


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


@pytest.mark.parametrize("requirement, expected", [
    (
        Requirement("foo"),
        [(None, None)]
    ),
    (
        Requirement("foo <=0.1.0"),
        [(None, (0, 1, 0))]
    ),
    (
        Requirement("foo >=0.1.0"),
        [((0, 1, 0), None)]
    ),
    (
        Requirement("foo >=0.1.0, <=1"),
        [((0, 1, 0), (1,))]
    ),
    (
        Requirement("foo <0.1.0"),
        [(None, (0, 0, 9999))]
    ),
    (
        Requirement("foo >0.1.0"),
        [((0, 1, 0, 1), None)]
    ),
    (
        Requirement("foo >0.1.0, <1"),
        [((0, 1, 0, 1), (0, 9999,))]
    ),
    (
        Requirement("foo >=0.1.0, <1"),
        [((0, 1, 0), (0, 9999,))]
    ),
    (
        Requirement("foo ==0.1.0"),
        [((0, 1, 0), (0, 1, 0))]
    ),
    (
        Requirement("foo ==0.1.*"),
        [((0, 1), (0, 1, 9999))]
    ),
    (
        Requirement("foo ~=0.5"),
        [((0, 5), (0, 5, 9999))]
    ),
    (
        Requirement("foo !=0.3.9"),
        [(None, (0, 3, 8, 9999)), ((0, 3, 9, 1), None)]
    ),
    (
        Requirement("foo !=0.3.*"),
        [(None, (0, 2, 9999)), ((0, 4), None)]
    ),
    (
        Requirement("foo >=9, >3, >10, <=100, <19, !=11.*, !=11.0.*"),
        [((10, 1), (10, 9999)), ((12,), (18, 9999))]
    ),
    (
        Requirement("foo !=1.*, !=1.0.0, <2, ==0.1.0"),
        [((0, 1, 0), (0, 1, 0))]
    )
], ids=[
    "none",
    "inclusive-comparison",
    "inclusive-comparison-min",
    "inclusive-comparison",
    "exclusive-comparison-max",
    "exclusive-comparison-min",
    "exclusive-comparison",
    "mixed-comparison",
    "version-matching",
    "version-matching-with-wildcard",
    "compatible-release",
    "version-exclusion",
    "version-exclusion-with-wildcard",
    "mixed-1",
    "mixed-2"
])
def test_extract_version_ranges(requirement, expected):
    """Extract version ranges from requirements."""
    assert wiz.utility.extract_version_ranges(requirement) == expected


@pytest.mark.parametrize("requirement, expected", [
    (
        Requirement("foo ===8"),
        "Operator '===' is not accepted for requirement 'foo ===8'"
    ),
    (
        Requirement("foo >=9, <8"),
        "The requirement is incorrect as minimum value '9' cannot be set"
        "when maximum value is '7.9999'."
    ),
    (
        Requirement("foo ==1, ==2"),
        "The requirement is incorrect as maximum value '1' cannot be set"
        "when minimum value is '2'."
    ),
    (
        Requirement("foo ==1, !=1.*"),
        "The requirement is incorrect as excluded version range '0.9999-2' "
        "makes all other versions unreachable."
    )
], ids=[
    "incorrect-operator",
    "incorrect-comparison-1",
    "incorrect-comparison-2",
    "incorrect-exclusion"
])
def test_extract_version_ranges_error(requirement, expected):
    """Fail to extract version ranges from requirements."""
    with pytest.raises(wiz.exception.InvalidRequirement) as error:
        wiz.utility.extract_version_ranges(requirement)

    assert expected in str(error)


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
