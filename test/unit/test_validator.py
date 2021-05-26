# :coding: utf-8

import pytest
import six

import wiz.validator
import wiz.exception


def test_validate_definition_minimal():
    """Validate minimal definition data mapping."""
    wiz.validator.validate_definition({"identifier": "foo"})


def test_validate_definition_with_version():
    """Validate definition data mapping with 'version' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "version": "0.1.0"
    })


def test_validate_definition_with_description():
    """Validate definition data mapping with 'description' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "description": "This is a definition",
    })


def test_validate_definition_with_disabled():
    """Validate definition data mapping with 'disabled' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "disabled": True,
    })


def test_validate_definition_with_auto_use():
    """Validate definition data mapping with 'auto-use' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "auto-use": True,
    })


def test_validate_definition_with_system():
    """Validate definition data mapping with 'system' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition",
        "system": {
            "platform": "linux",
            "os": "el >=7, <8",
            "arch": "x86_64"
        },
    })


def test_validate_definition_with_environ():
    """Validate definition data mapping with 'environ' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition",
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
            "KEY3": "PATH1:PATH2:PATH3"
        },
    })


def test_validate_definition_with_command():
    """Validate definition data mapping with 'command' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition",
        "command": {
            "app": "App0.1",
            "appX": "App0.1 --option value"
        },
    })


def test_validate_definition_with_requirements():
    """Validate definition data mapping with 'requirements' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition",
        "requirements": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ],
    })


def test_validate_definition_with_conditions():
    """Validate definition data mapping with 'conditions' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition",
        "conditions": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ],
    })


def test_validate_definition_with_variants():
    """Validate definition data mapping with 'variants' keyword."""
    wiz.validator.validate_definition({
        "identifier": "foo",
        "version": "0.1.0",
        "description": "This is a definition",
        "variants": [
            {
                "identifier": "1.0",
                "environ": {
                    "VERSION": "1.0"
                },
                "requirements": [
                    "envA >= 1.0, < 2"
                ]
            },
            {
                "identifier": "2.0",
                "environ": {
                    "VERSION": "2.0"
                },
                "command": {
                    "app": "App2.0",
                },
                "requirements": [
                    "envA >= 2.0, < 3"
                ]
            },
            {
                "identifier": "XXX",
                "command": {
                    "app": "AppXXX",
                },
            }
        ],
    })


@pytest.mark.parametrize("value, message", [
    (42, "Data has incorrect type."),
    ({"test": "foo"}, "Data contains invalid keywords: test"),
    ({}, "'identifier' is required."),
    ({"identifier": 0}, "'identifier' has incorrect type."),
    ({"identifier": "foo", "version": 0}, "'version' has incorrect type."),
    (
        {"identifier": "foo", "description": 0},
        "'description' has incorrect type."
    ),
    ({"identifier": "foo", "disabled": 0}, "'disabled' has incorrect type."),
    ({"identifier": "foo", "system": 0}, "'system' has incorrect type."),
    ({"identifier": "foo", "environ": 0}, "'environ' has incorrect type."),
    ({"identifier": "foo", "command": 0}, "'command' has incorrect type."),
    (
        {"identifier": "foo", "requirements": 0},
        "'requirements' has incorrect type."
    ),
    (
        {"identifier": "foo", "conditions": 0},
        "'conditions' has incorrect type."
    ),
    ({"identifier": "foo", "variants": 0}, "'variants' has incorrect type."),
], ids=[
    "incorrect-type",
    "invalid-keywords",
    "identifier-missing",
    "identifier-incorrect",
    "version-incorrect",
    "description-incorrect",
    "disabled-incorrect",
    "system-incorrect",
    "environ-incorrect",
    "command-incorrect",
    "requirements-incorrect",
    "conditions-incorrect",
    "variants-incorrect",
])
def test_validate_definition_failed(value, message):
    """Raise error when data is incorrect."""
    with pytest.raises(wiz.exception.DefinitionError) as error:
        wiz.validator.validate_definition(value)

    assert message in str(error)


def test_validate_identifier_keyword():
    """Validate 'identifier' keyword within data."""
    wiz.validator.validate_identifier_keyword({"identifier": "foo"})


@pytest.mark.parametrize("value, options, message", [
    ({}, {}, "'identifier' is required."),
    ({"identifier": 42}, {}, "'identifier' has incorrect type."),
    ({}, {"variant_index": 1}, "'variants/1/identifier' is required."),
], ids=[
    "required",
    "incorrect-type",
    "variant-index",
])
def test_validate_identifier_keyword_failed(value, options, message):
    """Raise error when 'identifier' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_identifier_keyword(value, **options)

    assert message in str(error)


def test_validate_version_keyword():
    """Validate 'version' keyword within data."""
    wiz.validator.validate_version_keyword({})
    wiz.validator.validate_version_keyword({"version": "0.1.0"})


@pytest.mark.parametrize("value, message", [
    ({"version": 42}, "'version' has incorrect type."),
    ({"version": "_"}, "Invalid version: '_'"),
    ({"version": "abc"}, "Invalid version: 'abc'"),
    ({"version": "test0.1.0"}, "Invalid version: 'test0.1.0'"),
    ({"version": "0.1.*"}, "Invalid version: '0.1.*'"),
    ({"version": "0.1."}, "Invalid version: '0.1.'"),
    ({"version": "#@;"}, "Invalid version: '#@;'"),
], ids=[
    "incorrect-type",
    "incorrect-version-1",
    "incorrect-version-2",
    "incorrect-version-3",
    "incorrect-version-4",
    "incorrect-version-5",
    "incorrect-version-6",
])
def test_validate_version_keyword_failed(value, message):
    """Raise error when 'version' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_version_keyword(value)

    assert message in str(error)


def test_validate_namespace_keyword():
    """Validate 'namespace' keyword within data."""
    wiz.validator.validate_namespace_keyword({})
    wiz.validator.validate_namespace_keyword({"namespace": "foo"})


def test_validate_namespace_keyword_failed():
    """Raise error when 'namespace' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_namespace_keyword({"namespace": True})

    assert "'namespace' has incorrect type." in str(error)


def test_validate_description_keyword():
    """Validate 'description' keyword within data."""
    wiz.validator.validate_description_keyword({})
    wiz.validator.validate_description_keyword({"description": "test"})


def test_validate_description_keyword_failed():
    """Raise error when 'description' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_description_keyword({"description": True})

    assert "'description' has incorrect type." in str(error)


def test_validate_auto_use_keyword():
    """Validate 'auto-use' keyword within data."""
    wiz.validator.validate_auto_use_keyword({})
    wiz.validator.validate_auto_use_keyword({"auto-use": True})


def test_validate_auto_use_keyword_failed():
    """Raise error when 'auto-use' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_auto_use_keyword({"auto-use": "foo"})

    assert "'auto-use' has incorrect type." in str(error)


def test_validate_disabled_keyword():
    """Validate 'disabled' keyword within data."""
    wiz.validator.validate_disabled_keyword({})
    wiz.validator.validate_disabled_keyword({"disabled": True})


def test_validate_disabled_keyword_failed():
    """Raise error when 'disabled' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_disabled_keyword({"disabled": "foo"})

    assert "'disabled' has incorrect type." in str(error)


def test_validate_install_root_keyword():
    """Validate 'install-root' keyword within data."""
    wiz.validator.validate_install_root_keyword({})
    wiz.validator.validate_install_root_keyword({
        "install-root": "/path/to/install/root"
    })


def test_validate_install_root_keyword_failed():
    """Raise error when 'install-root' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_install_root_keyword({"install-root": False})

    assert "'install-root' has incorrect type." in str(error)


def test_validate_install_location_keyword():
    """Validate 'install-location' keyword within data."""
    wiz.validator.validate_install_location_keyword({})
    wiz.validator.validate_install_location_keyword({
        "install-location": "/path/to/install/location"
    })


def test_validate_install_location_keyword_failed():
    """Raise error when 'install-location' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_install_location_keyword({"install-location": 0})

    assert "'install-location' has incorrect type." in str(error)


def test_validate_system_keyword():
    """Validate 'system' keyword within data."""
    wiz.validator.validate_system_keyword({})
    wiz.validator.validate_system_keyword({"system": {"platform": "linux"}})
    wiz.validator.validate_system_keyword({"system": {"os": "el >= 7.4"}})
    wiz.validator.validate_system_keyword({"system": {"arch": "x86_64"}})


@pytest.mark.parametrize("value, message", [
    ({"system": {}}, "'system' should not be empty."),
    ({"system": 42}, "'system' has incorrect type."),
    ({"system": {"test": "foo"}}, "'system' contains invalid keywords: test"),
    ({"system": {"platform": 42}}, "system/platform' has incorrect type."),
    ({"system": {"os": 42}}, "system/os' has incorrect type."),
    ({"system": {"arch": 42}}, "system/arch' has incorrect type."),
], ids=[
    "empty",
    "incorrect-type",
    "invalid-keywords",
    "incorrect-platform",
    "incorrect-os",
    "incorrect-arch",
])
def test_validate_system_keyword_failed(value, message):
    """Raise error when 'identifier' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_system_keyword(value)

    assert message in str(error)


def test_validate_command_keyword():
    """Validate 'command' keyword within data."""
    wiz.validator.validate_command_keyword({})
    wiz.validator.validate_command_keyword({"command": {"foo": "FooExe"}})


@pytest.mark.parametrize("value, options, message", [
    ({"command": {}}, {}, "'command' should not be empty."),
    ({"command": 42}, {}, "'command' has incorrect type."),
    (
        {"command": 42}, {"variant_index": 1},
        "'variants/1/command' has incorrect type."
    ),
], ids=[
    "empty",
    "incorrect-type",
    "variant-index",
])
def test_validate_command_keyword_failed(value, options, message):
    """Raise error when 'command' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_command_keyword(value, **options)

    assert message in str(error)


def test_validate_environ_keyword():
    """Validate 'environ' keyword within data."""
    wiz.validator.validate_environ_keyword({})
    wiz.validator.validate_environ_keyword({"environ": {"key": "value"}})


@pytest.mark.parametrize("value, options, message", [
    ({"environ": {}}, {}, "'environ' should not be empty."),
    ({"environ": 42}, {}, "'environ' has incorrect type."),
    (
        {"environ": 42}, {"variant_index": 1},
        "'variants/1/environ' has incorrect type."
    ),
], ids=[
    "empty",
    "incorrect-type",
    "variant-index",
])
def test_validate_environ_keyword_failed(value, options, message):
    """Raise error when 'environ' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_environ_keyword(value, **options)

    assert message in str(error)


def test_validate_requirements_keyword():
    """Validate 'requirements' keyword within data."""
    wiz.validator.validate_requirements_keyword({})
    wiz.validator.validate_requirements_keyword({"requirements": ["foo"]})


@pytest.mark.parametrize("value, options, message", [
    ({"requirements": []}, {}, "'requirements' should not be empty."),
    ({"requirements": 42}, {}, "'requirements' has incorrect type."),
    (
        {"requirements": 42}, {"variant_index": 1},
        "'variants/1/requirements' has incorrect type."
    ),
], ids=[
    "empty",
    "incorrect-type",
    "variant-index",
])
def test_validate_requirements_keyword_failed(value, options, message):
    """Raise error when 'requirements' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_requirements_keyword(value, **options)

    assert message in str(error)


def test_validate_conditions_keyword():
    """Validate 'conditions' keyword within data."""
    wiz.validator.validate_conditions_keyword({})
    wiz.validator.validate_conditions_keyword({"conditions": ["foo"]})


@pytest.mark.parametrize("value, message", [
    ({"conditions": []}, "'conditions' should not be empty."),
    ({"conditions": 42}, "'conditions' has incorrect type."),
], ids=[
    "empty",
    "incorrect-type",
])
def test_validate_conditions_keyword_failed(value, message):
    """Raise error when 'conditions' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_conditions_keyword(value)

    assert message in str(error)


def test_validate_variants_keyword():
    """Validate 'variants' keyword within data."""
    wiz.validator.validate_variants_keyword({})
    wiz.validator.validate_variants_keyword(
        {
            "variants": [
                {
                    "identifier": "foo",
                    "install-location": "/path/to/install/location",
                    "command": {"foo": "FooExe"},
                    "environ": {"key": "value"},
                    "requirements": ["foo >= 0.1.0"]
                }
            ]
        }
    )


@pytest.mark.parametrize("value, message", [
    ({"variants": []}, "'variants' should not be empty."),
    ({"variants": 42}, "'variants' has incorrect type."),
    ({"variants": [42]}, "'variants/0' has incorrect type."),
    ({"variants": [{"A": "foo"}]}, "'variants/0' contains invalid keywords: A"),
    ({"variants": [{}]}, "'variants/0/identifier' is required."),
    (
        {"variants": [{"identifier": 42}]},
        "'variants/0/identifier' has incorrect type."
    ),
    (
        {"variants": [{"identifier": "foo", "install-location": 42}]},
        "'variants/0/install-location' has incorrect type."
    ),
    (
        {"variants": [{"identifier": "foo", "command": 42}]},
        "'variants/0/command' has incorrect type."
    ),
    (
        {"variants": [{"identifier": "foo", "environ": 42}]},
        "'variants/0/environ' has incorrect type."
    ),
    (
        {"variants": [{"identifier": "foo", "requirements": 42}]},
        "'variants/0/requirements' has incorrect type."
    ),
], ids=[
    "empty",
    "incorrect-type",
    "variant-incorrect-type",
    "variant-invalid-keywords",
    "variant-identifier-missing",
    "variant-identifier-incorrect",
    "variant-install-location-incorrect",
    "variant-command-incorrect",
    "variant-environ-incorrect",
    "variant-requirements-incorrect",
])
def test_validate_variants_keyword_failed(value, message):
    """Raise error when 'variants' keyword is incorrect."""
    with pytest.raises(ValueError) as error:
        wiz.validator.validate_variants_keyword(value)

    assert message in str(error)


def test_validate_keywords():
    """Ensure that no invalid keywords are in data mapping."""
    keywords = {"A", "B"}

    wiz.validator.validate_keywords({}, keywords)
    wiz.validator.validate_keywords({"A": "foo"}, keywords)
    wiz.validator.validate_keywords({"A": "foo", "B": "bar"}, keywords)

    with pytest.raises(ValueError) as error:
        wiz.validator.validate_keywords({"A": "foo", "C": "bar"}, keywords)

    assert "Data contains invalid keywords: C" in str(error)

    with pytest.raises(ValueError) as error:
        wiz.validator.validate_keywords({"C": "bar"}, keywords, label="'test'")

    assert "'test' contains invalid keywords: C" in str(error)


def test_validate_required():
    """Ensure that data exists."""
    wiz.validator.validate_required("")
    wiz.validator.validate_required("foo")
    wiz.validator.validate_required(0)
    wiz.validator.validate_required(42)
    wiz.validator.validate_required(False)
    wiz.validator.validate_required(True)
    wiz.validator.validate_required([])
    wiz.validator.validate_required([1, 2, 3])
    wiz.validator.validate_required({})
    wiz.validator.validate_required({"A": "foo"})
    wiz.validator.validate_required({1, 2, 3})

    with pytest.raises(ValueError) as error:
        wiz.validator.validate_required(None)

    assert "Data is required." in str(error)

    with pytest.raises(ValueError) as error:
        wiz.validator.validate_required(None, label="'test'")

    assert "'test' is required." in str(error)


def test_validate_type():
    """Ensure that data has correct type."""
    wiz.validator.validate_type("foo", six.string_types)
    wiz.validator.validate_type("0.1.0", six.string_types)
    wiz.validator.validate_type(42, int)
    wiz.validator.validate_type([1, 2, 3], list)
    wiz.validator.validate_type({"A": "foo"}, dict)
    wiz.validator.validate_type(True, bool)

    with pytest.raises(ValueError) as error:
        wiz.validator.validate_type(42, six.string_types)

    assert "Data has incorrect type." in str(error)

    with pytest.raises(ValueError) as error:
        wiz.validator.validate_type(42, six.string_types, label="'test'")

    assert "'test' has incorrect type." in str(error)


def test_validate_not_empty():
    """Ensure that data container is not empty."""
    wiz.validator.validate_not_empty({"A": "foo"})
    wiz.validator.validate_not_empty([1, 2, 3])

    with pytest.raises(ValueError) as error:
        wiz.validator.validate_not_empty({})

    assert "Data should not be empty." in str(error)

    with pytest.raises(ValueError) as error:
        wiz.validator.validate_not_empty([], label="'test'")

    assert "'test' should not be empty." in str(error)
