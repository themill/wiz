# :coding: utf-8

import pytest
import six

import wiz.validator


def test_minimal_definition():
    """Validate a minimal definition data."""
    data = {"identifier": "test"}
    assert list(wiz.validator.yield_definition_errors(data)) == []
    assert list(wiz.validator.yield_definition_errors({})) == [
        {
            "message": "{!r} is a required property".format(
                six.text_type("identifier")
            ),
            "path": "/",
        }
    ]


def test_unexpected_property():
    """Fail to validate a definition with unexpected property."""
    data = {"other": "test"}

    assert sorted(
        list(wiz.validator.yield_definition_errors(data)),
        key=lambda error: error["message"]
    ) == [
        {
            "message": "{!r} is a required property".format(
                six.text_type("identifier")
            ),
            "path": "/",
        },
        {
            "message": (
                "Additional properties are not allowed ('other' was unexpected)"
            ),
            "path": "/",
        },
    ]


@pytest.mark.parametrize("value", [
    2,
    True,
    ["element1", "element2"],
    {"key": "value"}
], ids=[
    "number",
    "boolean",
    "list",
    "object"
])
def test_incorrect_identifier_type(value):
    """Raise an error when identifier type is incorrect."""
    data = {"identifier": value}

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("string")
            ),
            "path": "/identifier",
        }
    ]


@pytest.mark.parametrize("value", [
    "0.1.0",
    "2018",
    "A",
    "123a"
], ids=[
    "semantic-versioning",
    "number-version",
    "alphabetical-version",
    "other"
])
def test_definition_with_version(value):
    """Validate a definition data with a version."""
    data = {
        "identifier": "test",
        "version": value,
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    2018,
    True,
    ["element1", "element2"],
    {"key": "value"}
], ids=[
    "number",
    "boolean",
    "list",
    "object"
])
def test_incorrect_version_type(value):
    """Raise an error when version type is incorrect."""
    data = {
        "identifier": "test",
        "version": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": (
                "{!r} is not valid under any of the given schemas".format(value)
            ),
            "path": "/version",
        }
    ]


def test_definition_with_description():
    """Validate a definition data with a description."""
    data = {
        "identifier": "test",
        "description": "This is a definition"
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    42,
    True,
    ["A description", "Another description"],
    {"key": "value"}
], ids=[
    "number",
    "boolean",
    "list",
    "object"
])
def test_incorrect_description_type(value):
    """Raise an error when description type is incorrect."""
    data = {
        "identifier": "test",
        "description": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("string")
            ),
            "path": "/description",
        }
    ]


def test_definition_with_disabled():
    """Validate a definition data with a disabled keyword."""
    data = {
        "identifier": "test",
        "disabled": True
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    42,
    "True",
    ["True", "False"],
    {"key": "value"}
], ids=[
    "number",
    "string",
    "list",
    "object"
])
def test_incorrect_disabled_type(value):
    """Raise an error when disabled type is incorrect."""
    data = {
        "identifier": "test",
        "disabled": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("boolean")
            ),
            "path": "/disabled",
        }
    ]


def test_definition_with_definition_location():
    """Validate a definition data with an definition-location keyword."""
    data = {
        "identifier": "test",
        "definition-location": "/path/to/definition.json"
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    42,
    True,
    ["True", "False"],
    {"key": "value"}
], ids=[
    "number",
    "boolean",
    "list",
    "object"
])
def test_incorrect_definition_location_type(value):
    """Raise an error when definition-location type is incorrect."""
    data = {
        "identifier": "test",
        "definition-location": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("string")
            ),
            "path": "/definition-location",
        }
    ]


def test_definition_with_registry():
    """Validate a definition data with a registry keyword."""
    data = {
        "identifier": "test",
        "registry": "/path/to/registry"
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    42,
    True,
    ["True", "False"],
    {"key": "value"}
], ids=[
    "number",
    "boolean",
    "list",
    "object"
])
def test_incorrect_registry_type(value):
    """Raise an error when registry type is incorrect."""
    data = {
        "identifier": "test",
        "registry": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("string")
            ),
            "path": "/registry",
        }
    ]


def test_definition_with_system():
    """Validate a definition data with a system mapping."""
    data = {
        "identifier": "test",
        "system": {
            "platform": "linux",
            "os": "el >=7, <8",
            "arch": "x86_64"
        }
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    "a-system",
    42,
    True,
    ["linux", "mac"],
], ids=[
    "string",
    "number",
    "boolean",
    "list"
])
def test_incorrect_system_type(value):
    """Raise an error when system type is incorrect."""
    data = {
        "identifier": "test",
        "system": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("object")
            ),
            "path": "/system",
        }
    ]


def test_incorrect_unexpected_system_property():
    """Raise an error when unexpected system property is found."""
    data = {
        "identifier": "test",
        "system": {
            "key": "value"
        },
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": (
                "Additional properties are not allowed ('key' was unexpected)"
            ),
            "path": "/system",
        }
    ]


def test_incorrect_system_values():
    """Raise an error when system values are incorrect."""
    data = {
        "identifier": "test",
        "system": {
            "platform": 42,
            "os": False,
            "arch": ["64"]
        },
    }

    assert sorted(
        list(wiz.validator.yield_definition_errors(data)),
        key=lambda error: error["path"]
    ) == [
        {
            "message": "['64'] is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/system/arch",
        },
        {
            "message": "False is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/system/os",
        },
        {
            "message": "42 is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/system/platform",
        }
    ]


def test_system_empty():
    """Raise an error when system object is empty."""
    data = {
        "identifier": "test",
        "system": {},
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{} does not have enough properties",
            "path": "/system",
        }
    ]


def test_definition_with_environ():
    """Validate a definition data with environment mapping."""
    data = {
        "identifier": "test",
        "environ": {
            "KEY1": "VALUE1",
            "KEY2": "VALUE2",
            "KEY3": "PATH1:PATH2:PATH3"
        }
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    "an-environment",
    42,
    True,
    ["env1", "env2"],
], ids=[
    "string",
    "number",
    "boolean",
    "list"
])
def test_incorrect_environ_type(value):
    """Raise an error when environ type is incorrect."""
    data = {
        "identifier": "test",
        "environ": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("object")
            ),
            "path": "/environ",
        }
    ]


def test_incorrect_environ_value_type():
    """Raise an error when an environ value is not a string."""
    data = {
        "identifier": "test",
        "environ": {
            "KEY1": 42,
            "KEY2": True,
            "KEY3": {"env1": "something"},
            "KEY4": ["env1", "env2"]
        }
    }
    assert sorted(
        list(wiz.validator.yield_definition_errors(data)),
        key=lambda error: error["path"]
    ) == [
        {
            "message": "42 is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/environ/KEY1",
        },
        {
            "message": "True is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/environ/KEY2",
        },
        {
            "message": "{{'env1': 'something'}} is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/environ/KEY3",
        },
        {
            "message": "['env1', 'env2'] is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/environ/KEY4",
        }
    ]


def test_environ_empty():
    """Raise an error when environ object is empty."""
    data = {
        "identifier": "test",
        "environ": {},
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{} does not have enough properties",
            "path": "/environ",
        }
    ]


def test_definition_with_command():
    """Validate a definition data with command mapping."""
    data = {
        "identifier": "test",
        "command": {
            "app": "App0.1",
            "appX": "App0.1 --option value"
        }
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    "a-command",
    42,
    True,
    ["app1", "app2"],
], ids=[
    "string",
    "number",
    "boolean",
    "list"
])
def test_incorrect_command_type(value):
    """Raise an error when command type is incorrect."""
    data = {
        "identifier": "test",
        "command": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("object")
            ),
            "path": "/command",
        }
    ]


def test_incorrect_command_value_type():
    """Raise an error when a command value is not a string."""
    data = {
        "identifier": "test",
        "command": {
            "app1": 42,
            "app2": True,
            "app3": {"app": "something"},
            "app4": ["app1", "app2"]
        }
    }
    assert sorted(
        list(wiz.validator.yield_definition_errors(data)),
        key=lambda error: error["path"]
    ) == [
        {
            "message": "42 is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/command/app1",
        },
        {
            "message": "True is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/command/app2",
        },
        {
            "message": "{{'app': 'something'}} is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/command/app3",
        },
        {
            "message": "['app1', 'app2'] is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/command/app4",
        }
    ]


def test_command_empty():
    """Raise an error when command object is empty."""
    data = {
        "identifier": "test",
        "command": {},
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{} does not have enough properties",
            "path": "/command",
        }
    ]


def test_definition_with_requirements():
    """Validate a definition data with requirements list."""
    data = {
        "identifier": "test",
        "requirements": [
            "envA >= 1.0.0",
            "envB >= 3.4.2, < 4",
            "envC"
        ]
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    "package",
    42,
    True,
    {"package1": "version"}
], ids=[
    "string",
    "number",
    "boolean",
    "object"
])
def test_incorrect_requirements_type(value):
    """Raise an error when requirements type is incorrect."""
    data = {
        "identifier": "test",
        "requirements": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("array")
            ),
            "path": "/requirements",
        }
    ]


def test_incorrect_requirement_item_type():
    """Raise an error when a requirement item is not a string."""
    data = {
        "identifier": "test",
        "requirements": [
            42,
            True,
            {"package1": "version"},
            ["package1", "package2"]
        ],
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "42 is not valid under any of the given schemas",
            "path": "/requirements/0",
        },
        {
            "message": "True is not valid under any of the given schemas",
            "path": "/requirements/1",
        },
        {
            "message": (
                "{'package1': 'version'} is not valid under any of the "
                "given schemas"
            ),
            "path": "/requirements/2",
        },
        {
            "message": (
                "['package1', 'package2'] is not valid under any of the "
                "given schemas"
            ),
            "path": "/requirements/3",
        },
    ]


def test_requirements_empty():
    """Raise an error when requirement array is empty."""
    data = {
        "identifier": "test",
        "requirements": [],
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "[] is too short",
            "path": "/requirements",
        }
    ]


def test_definition_with_variants():
    """Validate a definition data with variants list."""
    data = {
        "identifier": "test",
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
        ]
    }
    assert list(wiz.validator.yield_definition_errors(data)) == []


@pytest.mark.parametrize("value", [
    "variant",
    42,
    True,
    {"test": "variant"}
], ids=[
    "string",
    "number",
    "boolean",
    "object"
])
def test_incorrect_variants_type(value):
    """Raise an error when variants type is incorrect."""
    data = {
        "identifier": "test",
        "variants": value,
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("array")
            ),
            "path": "/variants",
        }
    ]


def test_incorrect_variant_item_type():
    """Raise an error when a variant item is not a string."""
    data = {
        "identifier": "test",
        "variants": [
            42,
            True,
            "a-variant",
            ["variant1", "variant2"]
        ],
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "42 is not of type {!r}".format(six.text_type("object")),
            "path": "/variants/0",
        },
        {
            "message": "True is not of type {!r}".format(
                six.text_type("object")
            ),
            "path": "/variants/1",
        },
        {
            "message": "'a-variant' is not of type {!r}".format(
                six.text_type("object")
            ),
            "path": "/variants/2",
        },
        {
            "message": "['variant1', 'variant2'] is not of type {!r}".format(
                six.text_type("object")
            ),
            "path": "/variants/3",
        },
    ]


def test_incorrect_minimal_variant():
    """Validate a minimal variant definition."""
    data = {
        "identifier": "test",
        "variants": [
            {}
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is a required property".format(
                six.text_type("identifier")
            ),
            "path": "/variants/0",
        }
    ]


def test_unexpected_variant_property():
    """Fail to validate a definition with unexpected variant property."""
    data = {
        "identifier": "test",
        "variants": [
            {"other": "test"}
        ]
    }

    assert sorted(
        list(wiz.validator.yield_definition_errors(data)),
        key=lambda error: error["message"]
    ) == [
        {
            "message": "{!r} is a required property".format(
                six.text_type("identifier")
            ),
            "path": "/variants/0",
        },
        {
            "message": (
                "Additional properties are not allowed ('other' was unexpected)"
            ),
            "path": "/variants/0",
        },
    ]


def test_variants_empty():
    """Raise an error when variant array is empty."""
    data = {
        "identifier": "test",
        "variants": [],
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "[] is too short",
            "path": "/variants",
        }
    ]


@pytest.mark.parametrize("value", [
    2,
    True,
    ["element1", "element2"],
    {"key": "value"}
], ids=[
    "number",
    "boolean",
    "list",
    "object"
])
def test_incorrect_variant_identifier_type(value):
    """Raise an error when variant identifier type is incorrect."""
    data = {
        "identifier": "test",
        "variants": [
            {"identifier": value}
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("string")
            ),
            "path": "/variants/0/identifier",
        }
    ]


@pytest.mark.parametrize("value", [
    "a-command",
    42,
    True,
    ["app1", "app2"],
], ids=[
    "string",
    "number",
    "boolean",
    "list"
])
def test_incorrect_variant_command_type(value):
    """Raise an error when variant command type is incorrect."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "command": value
            }
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("object")
            ),
            "path": "/variants/0/command",
        }
    ]


def test_incorrect_variant_command_value_type():
    """Raise an error when a variant command value is not a string."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "command": {
                    "app1": 42,
                    "app2": True,
                    "app3": {"app": "something"},
                    "app4": ["app1", "app2"]
                }
            }
        ]
    }

    assert sorted(
        list(wiz.validator.yield_definition_errors(data)),
        key=lambda error: error["path"]
    ) == [
        {
            "message": "42 is not of type {!r}".format(six.text_type("string")),
            "path": "/variants/0/command/app1",
        },
        {
            "message": "True is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/variants/0/command/app2",
        },
        {
            "message": "{{'app': 'something'}} is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/variants/0/command/app3",
        },
        {
            "message": "['app1', 'app2'] is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/variants/0/command/app4",
        }
    ]


def test_variant_command_empty():
    """Raise an error when variant command object is empty."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "command": {}
            }
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{} does not have enough properties",
            "path": "/variants/0/command",
        }
    ]


@pytest.mark.parametrize("value", [
    "an-environment",
    42,
    True,
    ["env1", "env2"],
], ids=[
    "string",
    "number",
    "boolean",
    "list"
])
def test_incorrect_variant_environ_type(value):
    """Raise an error when variant environ type is incorrect."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "environ": value
            }
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("object")
            ),
            "path": "/variants/0/environ",
        }
    ]


def test_incorrect_variant_environ_value_type():
    """Raise an error when a variant environ value is not a string."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "environ": {
                    "KEY1": 42,
                    "KEY2": True,
                    "KEY3": {"env1": "something"},
                    "KEY4": ["env1", "env2"]
                }
            }
        ]
    }

    assert sorted(
        list(wiz.validator.yield_definition_errors(data)),
        key=lambda error: error["path"]
    ) == [
        {
            "message": "42 is not of type {!r}".format(six.text_type("string")),
            "path": "/variants/0/environ/KEY1",
        },
        {
            "message": "True is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/variants/0/environ/KEY2",
        },
        {
            "message": "{{'env1': 'something'}} is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/variants/0/environ/KEY3",
        },
        {
            "message": "['env1', 'env2'] is not of type {!r}".format(
                six.text_type("string")
            ),
            "path": "/variants/0/environ/KEY4",
        }
    ]


def test_variant_environ_empty():
    """Raise an error when variant environ object is empty."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "environ": {}
            }
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{} does not have enough properties",
            "path": "/variants/0/environ",
        }
    ]


@pytest.mark.parametrize("value", [
    "package",
    42,
    True,
    {"package1": "version"}
], ids=[
    "string",
    "number",
    "boolean",
    "object"
])
def test_incorrect_variant_requirements_type(value):
    """Raise an error when variant requirements type is incorrect."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "requirements": value
            }
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "{!r} is not of type {!r}".format(
                value, six.text_type("array")
            ),
            "path": "/variants/0/requirements",
        }
    ]


def test_incorrect_variant_requirement_item_type():
    """Raise an error when a variant requirement item is not a string."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "requirements": [
                    42,
                    True,
                    {"package1": "version"},
                    ["package1", "package2"]
                ]
            }
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "42 is not valid under any of the given schemas",
            "path": "/variants/0/requirements/0",
        },
        {
            "message": "True is not valid under any of the given schemas",
            "path": "/variants/0/requirements/1",
        },
        {
            "message": (
                "{'package1': 'version'} is not valid under any of the "
                "given schemas"
            ),
            "path": "/variants/0/requirements/2",
        },
        {
            "message": (
                "['package1', 'package2'] is not valid under any of the "
                "given schemas"
            ),
            "path": "/variants/0/requirements/3",
        },
    ]


def test_variant_requirements_empty():
    """Raise an error when variant requirement array is empty."""
    data = {
        "identifier": "test",
        "variants": [
            {
                "identifier": "test",
                "requirements": []
            }
        ]
    }

    assert list(wiz.validator.yield_definition_errors(data)) == [
        {
            "message": "[] is too short",
            "path": "/variants/0/requirements",
        }
    ]
