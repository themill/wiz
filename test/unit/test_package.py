# :coding: utf-8

import itertools

import pytest
from packaging.requirements import Requirement

import wiz.package
import wiz.definition
import wiz.exception


@pytest.mark.parametrize("environment, variant_name, expected", [
    (
        wiz.definition.Environment({
            "identifier": "env1",
            "version": "0.3.4",
        }),
        None,
        "env1==0.3.4"
    ),
    (
        wiz.definition.Environment({
            "identifier": "env1",
            "version": "0.3.4",
        }),
        "Variant",
        "env1[Variant]==0.3.4"
    )
], ids=[
    "without-variant",
    "with-variant",
])
def test_generate_identifier(environment, variant_name, expected):
    """Generate the package identifier."""
    assert (
        wiz.package.generate_identifier(environment, variant_name) == expected
    )


@pytest.fixture()
def mocked_environment_getter(mocker):
    """Return mocked environment getter."""
    return mocker.patch.object(wiz.environment, "get")


@pytest.fixture()
def mocked_package(mocker):
    """Return mocked Package constructor."""
    return mocker.patch.object(wiz.package, "Package", return_value="PACKAGE")


def test_extract_without_variant(mocked_environment_getter, mocked_package):
    """Extract one Package from environment."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        }
    })

    mocked_environment_getter.return_value = environment

    requirement = Requirement("env1")
    result = wiz.package.extract(requirement, {})
    mocked_environment_getter.assert_called_once_with(requirement, {})

    mocked_package.assert_called_once_with(environment)
    assert result == ["PACKAGE"]


def test_extract_with_all_variants(mocked_environment_getter, mocked_package):
    """Extract all variant Packages from environment."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "variant": [
            {
                "identifier": "Variant1",
                "data": {"KEY1": "VALUE1"}
            },
            {
                "identifier": "Variant2",
                "data": {"KEY2": "VALUE2"}
            },
            {
                "identifier": "Variant3",
                "data": {"KEY3": "VALUE3"}
            }
        ]
    })

    mocked_environment_getter.return_value = environment

    requirement = Requirement("env1")
    result = wiz.package.extract(requirement, {})
    mocked_environment_getter.assert_called_once_with(requirement, {})

    assert mocked_package.call_count == 3
    mocked_package.assert_any_call(environment, {
        "identifier": "Variant1",
        "data": {"KEY1": "VALUE1"}
    })
    mocked_package.assert_any_call(environment, {
        "identifier": "Variant2",
        "data": {"KEY2": "VALUE2"}
    })
    mocked_package.assert_any_call(environment, {
        "identifier": "Variant3",
        "data": {"KEY3": "VALUE3"}
    })

    assert result == ["PACKAGE", "PACKAGE", "PACKAGE"]


def test_extract_with_one_requested_variant(
    mocked_environment_getter, mocked_package
):
    """Extract one requested variant Package from environment."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "variant": [
            {
                "identifier": "Variant1",
                "data": {"KEY1": "VALUE1"}
            },
            {
                "identifier": "Variant2",
                "data": {"KEY2": "VALUE2"}
            },
            {
                "identifier": "Variant3",
                "data": {"KEY3": "VALUE3"}
            }
        ]
    })

    mocked_environment_getter.return_value = environment

    requirement = Requirement("env1[Variant2]")
    result = wiz.package.extract(requirement, {})
    mocked_environment_getter.assert_called_once_with(requirement, {})

    mocked_package.assert_called_once_with(environment, {
        "identifier": "Variant2",
        "data": {"KEY2": "VALUE2"}
    })

    assert result == ["PACKAGE"]


def test_extract_error(mocked_environment_getter, mocked_package):
    """Fail to extract Package from environment."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        }
    })

    mocked_environment_getter.return_value = environment

    requirement = Requirement("env1[Incorrect]")

    with pytest.raises(wiz.exception.RequestNotFound) as error:
        wiz.package.extract(requirement, {})

    mocked_environment_getter.assert_called_once_with(requirement, {})
    mocked_package.assert_not_called()

    assert (
        "The variant 'Incorrect' could not been resolved "
        "for 'env1' [0.3.4]." in str(error)
    )


def test_minimal_package_without_variant():
    """Create minimal package instance created with no variant."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
    })

    package = wiz.package.Package(environment)
    assert package.identifier == "env1==unknown"
    assert package.description == "unknown"
    assert package.alias == {}
    assert package.data == {}
    assert package.requirement == []

    assert len(package) == 5
    assert sorted(package) == [
        "alias", "data", "description", "identifier", "requirement"
    ]


def test_full_package_without_variant():
    """Create full package instance created with no variant."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "description": "Test environment",
        "alias": {
            "app1": "App1",
            "app2": "App2",
        },
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        },
        "requirement": [
            "env1 >= 2",
            "env2"
        ]
    })

    package = wiz.package.Package(environment)
    assert package.identifier == "env1==0.3.4"
    assert package.description == "Test environment"
    assert package.alias == {"app1": "App1", "app2": "App2"}
    assert package.data == {"KEY1": "VALUE1", "KEY2": "VALUE2"}

    for requirement_data, requirement in itertools.izip_longest(
        ["env1 >= 2", "env2"], package.requirement
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(requirement_data))


def test_package_with_variant():
    """Create full package instance created with no variant."""
    environment = wiz.definition.Environment({
        "identifier": "env1",
        "version": "0.3.4",
        "description": "Test environment",
        "alias": {
            "app1": "App1",
            "app2": "App2",
        },
        "data": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
        },
        "requirement": [
            "env1 >= 2",
            "env2"
        ]
    })

    variant = wiz.definition._EnvironmentVariant({
        "identifier": "Variant",
        "alias": {
            "app1": "App1XX",
        },
        "data": {
            "KEY2": "VALUE20",
        },
        "requirement": [
            "env3"
        ]
    }, "env1")

    package = wiz.package.Package(environment, variant)
    assert package.identifier == "env1[Variant]==0.3.4"
    assert package.description == "Test environment"
    assert package.alias == {"app1": "App1XX", "app2": "App2"}
    assert package.data == {"KEY1": "VALUE1", "KEY2": "VALUE20"}

    for requirement_data, requirement in itertools.izip_longest(
        ["env1 >= 2", "env2", "env3"], package.requirement
    ):
        assert isinstance(requirement, Requirement)
        assert str(requirement) == str(Requirement(requirement_data))
