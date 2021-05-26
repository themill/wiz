# :coding: utf-8

import re

import six
from packaging.version import VERSION_PATTERN

import wiz.exception

_REGEXP_VERSION = re.compile(
    "^{}$".format(VERSION_PATTERN), re.VERBOSE | re.IGNORECASE
)


def validate_definition(data):
    """Validate *data* mapping used to create a definition.

    An error will be raised if the *data* mapping cannot be used to create an
    instance of :class:`wiz.definition.Definition`..

    :param data: Mapping to validate.

    :raise: :exc:`wiz.exception.IncorrectDefinition` if the *data* mapping
        is incorrect.

    """
    keywords = {
        "identifier", "version", "namespace", "description", "auto-use",
        "disabled", "install-root", "install-location", "system", "command",
        "environ", "requirements", "conditions", "variants"
    }

    try:
        validate_type(data, dict)
        validate_keywords(data, keywords)

        validate_identifier_keyword(data)
        validate_version_keyword(data)
        validate_namespace_keyword(data)
        validate_description_keyword(data)
        validate_auto_use_keyword(data)
        validate_disabled_keyword(data)
        validate_install_root_keyword(data)
        validate_install_location_keyword(data)
        validate_system_keyword(data)
        validate_command_keyword(data)
        validate_environ_keyword(data)
        validate_requirements_keyword(data)
        validate_conditions_keyword(data)
        validate_variants_keyword(data)

    except ValueError as error:
        raise wiz.exception.DefinitionError(str(error))


def validate_identifier_keyword(data, variant_index=None):
    """Validate 'identifier' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "identifier": "foo"
        }

    :param data: Mapping to validate.

    :param variant_index: Index number of the variant mapping if applicable.
        Default is None.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("identifier")

    name = "'identifier'"
    if variant_index is not None:
        name = "'variants/{}/identifier'".format(variant_index)

    validate_required(data, label=name)
    validate_type(data, six.string_types, label=name)


def validate_version_keyword(data):
    """Validate 'version' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "version": "0.1.0"
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("version")
    validate_type(data, six.string_types, label="'version'")

    if data is not None:
        match = _REGEXP_VERSION.match(data)
        if not match:
            raise ValueError("Invalid version: '{}'".format(data))


def validate_namespace_keyword(data):
    """Validate 'namespace' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "namespace": "foo"
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("namespace")
    validate_type(data, six.string_types, label="'namespace'")


def validate_description_keyword(data):
    """Validate 'description' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "description": "This is a description"
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("description")
    validate_type(data, six.string_types, label="'description'")


def validate_auto_use_keyword(data):
    """Validate 'auto-use' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "auto-use": true
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("auto-use")
    validate_type(data, bool, label="'auto-use'")


def validate_disabled_keyword(data):
    """Validate 'disabled' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "disabled": true
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("disabled")
    validate_type(data, bool, label="'disabled'")


def validate_install_root_keyword(data):
    """Validate 'install-root' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "install-root": "/path/to/install/root"
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("install-root")
    validate_type(data, six.string_types, label="'install-root'")


def validate_install_location_keyword(data, variant_index=None):
    """Validate 'install-location' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "install-location": "/path/to/install/location"
        }

    :param data: Mapping to validate.

    :param variant_index: Index number of the variant mapping if applicable.
        Default is None.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("install-location")

    name = "'install-location'"
    if variant_index is not None:
        name = "'variants/{}/install-location'".format(variant_index)

    validate_type(data, six.string_types, label=name)


def validate_system_keyword(data):
    """Validate 'system' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "system": {
                "platform": "linux"
            }
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    _data = data.get("system")
    validate_type(_data, dict, label="'system'")
    validate_not_empty(_data, label="'system'")

    _data = data.get("system", {})
    validate_keywords(_data, {"platform", "os", "arch"}, label="'system'")

    _data = data.get("system", {}).get("platform")
    validate_type(_data, six.string_types, label="'system/platform'")

    _data = data.get("system", {}).get("os")
    validate_type(_data, six.string_types, label="'system/os'")

    _data = data.get("system", {}).get("arch")
    validate_type(_data, six.string_types, label="'system/arch'")


def validate_command_keyword(data, variant_index=None):
    """Validate 'command' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "command": {
                "foo": "FooExe"
            }
        }

    :param data: Mapping to validate.

    :param variant_index: Index number of the variant mapping if applicable.
        Default is None.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("command")

    name = "'command'"
    if variant_index is not None:
        name = "'variants/{}/command'".format(variant_index)

    validate_type(data, dict, label=name)
    validate_not_empty(data, label=name)


def validate_environ_keyword(data, variant_index=None):
    """Validate 'environ' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "environ": {
                "KEY": "VALUE"
            }
        }

    :param data: Mapping to validate.

    :param variant_index: Index number of the variant mapping if applicable.
        Default is None.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("environ")

    name = "'environ'"
    if variant_index is not None:
        name = "'variants/{}/environ'".format(variant_index)

    validate_type(data, dict, label=name)
    validate_not_empty(data, label=name)


def validate_requirements_keyword(data, variant_index=None):
    """Validate 'requirements' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "requirements": [
                "foo == 1.0.0",
                "bar >= 1, < 2"
            ]
        }

    :param data: Mapping to validate.

    :param variant_index: Index number of the variant mapping if applicable.
        Default is None.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("requirements")

    name = "'requirements'"
    if variant_index is not None:
        name = "'variants/{}/requirements'".format(variant_index)

    validate_type(data, list, label=name)
    validate_not_empty(data, label=name)


def validate_conditions_keyword(data):
    """Validate 'conditions' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "conditions": [
                "bim >= 3.0.0"
            ]
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("conditions")
    validate_type(data, list, label="'conditions'")
    validate_not_empty(data, label="'conditions'")


def validate_variants_keyword(data):
    """Validate 'variants' keyword within *data* mapping.

    A correct *data* mapping should be in the form of::

        {
            "variants": [
                {
                    "identifier": "foo",
                    "install-location": "/path/to/install/location",
                    "requirements": [
                        "bar >= 1, < 2"
                    ]
                }
            ]
        }

    :param data: Mapping to validate.

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    data = data.get("variants")
    validate_type(data, list, label="'variants'")
    validate_not_empty(data, label="'variants'")

    keywords = {
        "identifier", "install-location", "command", "environ", "requirements"
    }

    for index, data in enumerate(data or []):
        validate_type(data, dict, label="'variants/{}'".format(index))
        validate_keywords(data, keywords, label="'variants/{}'".format(index))

        validate_identifier_keyword(data, variant_index=index)
        validate_install_location_keyword(data, variant_index=index)
        validate_command_keyword(data, variant_index=index)
        validate_environ_keyword(data, variant_index=index)
        validate_requirements_keyword(data, variant_index=index)


def validate_keywords(data, keywords, label="Data"):
    """Ensure that no invalid keywords are in *data* mapping.

    :param data: Mapping to validate.

    :param keywords: Set of authorized keywords.

    :param label: String to describe *data* if an error is raised. Default is
        "Data".

    :raise: :exc:`ValueError` if the *data* mapping is incorrect.

    """
    remaining_keywords = set(data.keys()).difference(keywords)
    if remaining_keywords != set():
        raise ValueError(
            "{} contains invalid keywords: {}"
            .format(label, ", ".join(remaining_keywords))
        )


def validate_required(data, label="Data"):
    """Ensure that *data* exists.

    :param data: Content to validate.

    :param label: String to describe *data* if an error is raised. Default is
        "Data".

    :raise: :exc:`ValueError` if *data* is incorrect.

    """
    if data is None:
        raise ValueError("{} is required.".format(label))


def validate_type(data, data_type, label="Data"):
    """Ensure that *data* has correct type.

    :param data: Content to validate.

    :param data_type: Type expected for *data*. It can be a tuple if several
        types are authorized.

    :param label: String to describe *data* if an error is raised. Default is
        "Data".

    :raise: :exc:`ValueError` if *data* is incorrect.

    """
    if data is not None and not isinstance(data, data_type):
        raise ValueError("{} has incorrect type.".format(label))


def validate_not_empty(data, label="Data"):
    """Ensure that *data* container is not empty.

    :param data: Content to validate. It could be a list or a mapping.

    :param label: String to describe *data* if an error is raised. Default is
        "Data".

    :raise: :exc:`ValueError` if *data* is incorrect.

    """
    if data is not None and not len(data):
        raise ValueError("{} should not be empty.".format(label))
