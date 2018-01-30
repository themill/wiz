# :coding: utf-8

import os
import re

import mlog

import wiz.definition
import wiz.graph
import wiz.exception


def resolve(requirements, definition_mapping):
    """Return resolved definitions list corresponding to *requirements*.

    The definition list should be :class:`~wiz.definition.Definition` instances
    ordered from the less important to the most important.

    *requirements* should be a list of
    class:`packaging.requirements.Requirement` instances.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier. It is used to
    resolve dependent definition specifiers.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    Raise :exc:`wiz.exception.GraphResolutionError` if the graph cannot be
    resolved.

    """
    logger = mlog.Logger(__name__ + ".resolve")
    logger.info(
        "Resolve environment: {}".format(
            ", ".join([str(requirement) for requirement in requirements])
        )
    )

    resolver = wiz.graph.Resolver(definition_mapping)
    return resolver.compute_definitions(requirements)


def extract_mapping(definitions, environ_mapping=None):
    """Return resolved mapping extracted from *definitions*.

    A mapping should look as follow::

        >>> extract_mapping(definitions)
        {
            "command": {
                "app": "AppExe"
                ...
            },
            "environ": {
                "KEY1": "value1",
                "KEY2": "value2",
                ...
            }
        }

    *definitions* should be a list of :class:`~wiz.definition.Definition`
    instances. it should be ordered from the less important to the most
    important so that the later are prioritized over the first.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    # Compute initial environment mapping to augment.
    environ_mapping = initiate(environ_mapping)

    def _combine(definition1, definition2):
        """Return intermediate definition combining both extracted data."""
        _command = dict(
            definition1.get("command", {}),
            **definition2.get("command", {})
        )
        _environ = wiz.definition.combine_environment(definition1, definition2)

        definition2["command"] = _command
        definition2["environ"] = _environ
        return definition2

    mapping = reduce(_combine, definitions, dict(environ=environ_mapping))

    # Clean all values from possible key references.
    for key, value in mapping["environ"].items():
        _value = re.sub(":?\${{{}}}:?".format(key), lambda x: "", value)
        mapping["environ"][key] = _value

    return mapping


def initiate(environ_mapping=None):
    """Return the initiate environment to augment.

    The initial environment contains basic variables from the external
    environment that can be used in the environment definitions, such as
    the *USER* or the *HOME* variables.

    The other variable added are:

    * DISPLAY:
        This variable is necessary to open user interface within the current
        X display name.

    * PATH:
        This variable is initialised with default values to have access to the
        basic UNIX commands.

    *environ_mapping* can be a custom environment mapping which will be added
    to the initial environment.

    """
    environ = {
        "USER": os.environ.get("USER"),
        "HOME": os.environ.get("HOME"),
        "DISPLAY": os.environ.get("DISPLAY"),
        "PATH": os.pathsep.join([
            "/usr/get_local/sbin",
            "/usr/get_local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }

    if environ_mapping is not None:
        environ.update(**environ_mapping)

    return environ
