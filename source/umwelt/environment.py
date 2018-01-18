# :coding: utf-8

import os
import re

import mlog

import umwelt.definition
import umwelt.graph


def resolve_environment(requirements, definition_mapping, environ_mapping=None):
    """Return resolved environment mapping corresponding to *requirements*.

    *requirements* should be a list of
    class:`packaging.requirements.Requirement` instances.

    *definition_mapping* is a mapping regrouping all available environment
    definition associated with their unique identifier. It is used to
    resolve dependent definition specifiers.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    Raise :exc:`RuntimeError` if the graph cannot be built.

    """
    logger = mlog.Logger(__name__ + ".resolve_environment")
    logger.info(
        "Resolve environment: {}".format(
            ", ".join([str(requirement) for requirement in requirements])
        )
    )

    # Compute initial environment mapping to augment.
    environ_mapping = initial_environment(environ_mapping)

    # Create a graph with all required definition versions.
    graph = umwelt.graph.Graph(definition_mapping)
    graph.update_from_requirements(requirements)

    # Ensure that only one version is required for each definition in the graph.
    # Otherwise attempt to resolve the possible conflicts.
    umwelt.graph.resolve_conflicts(graph, definition_mapping)

    # Extract all definition versions from the graph from the less important to
    # the most important. The most important being the highest definition
    # versions in the graph.
    definitions = umwelt.graph.extract_ordered_definitions(graph)

    # Combine all environments from each definition version extracted with the
    # initial environment.
    return compute_environment_from_definitions(definitions, environ_mapping)


def compute_environment_from_definitions(definitions, environ_mapping=None):
    """Return environment mapping from combination of *definitions*.

    *definitions* should be a list of :class:`~umwelt.definition.Definition`
    instances. it should be ordered from the less important to the most
    important so that the later are prioritized over the first.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    def _combine(definition1, definition2):
        """Return intermediate definition combining both environments"""
        return {"environ": merge_environments(definition1, definition2)}

    combined_defintion = reduce(
        _combine, definitions, dict(environ=environ_mapping)
    )

    return combined_defintion.get("environ", {})


def merge_environments(definition1, definition2):
    """Return combined environment from *definition1* and *definition2*

    *definition1* and *definition2* must be valie
    :class:`~umwelt.definition.Definition` instances.

    Each variable name from both definition's "environ" mappings will be
    gathered so that a final value can be set. If the a variable is only
    contained in one of the "environ" mapping, its value will be kept in the
    combined environment.

    If the variable exists in both "environ" mappings, the value from
    *definition2* must reference the variable name for the value from
    *definition1* to be included in the combined environment::

        >>> merge_environments(
        ...     Definition({"environ": {"key": "value2"})
        ...     Definition({"environ": {"key": "value1:${key}"}})
        ... )

        {"key": "value1:value2"}

    Otherwise the value from *definition2* will override the value from
    *definition1*::

        >>> merge_environments(
        ...     Definition({"environ": {"key": "value2"})
        ...     Definition({"environ": {"key": "value1"}})
        ... )

        {"key": "value1"}

    If other variables from *definition1* are referenced in the value fetched
    from *definition2*, they will be replaced as well::

        >>> merge_environments(
        ...     Definition({
        ...         "environ": {
        ...             "PLUGIN_PATH": "/path/to/settings",
        ...             "HOME": "/usr/people/me"
        ...        }
        ...     }),
        ...     Definition({
        ...         "environ": {
        ...             "PLUGIN_PATH": "${HOME}/.app:${PLUGIN_PATH}"
        ...         }
        ...     })
        ... )

        >>> compute_variable_value(
        ...    "PLUGIN_PATH",
        ...    {"PLUGIN_PATH": "${HOME}/.app:${PLUGIN_PATH}"},
        ...    {"PLUGIN_PATH": "/path/to/settings", "HOME": "/usr/people/me"}
        ... )

        {
            "HOME": "/usr/people/me",
            "PLUGIN_PATH": "/usr/people/me/.app:/path/to/settings"
        }

    .. warining::

        This process will stringify all variable values.

    """
    logger = mlog.Logger(__name__ + ".merge_environments")

    environ = {}

    environ1 = definition1.get("environ", {})
    environ2 = definition2.get("environ", {})

    for key in set(environ1.keys() + environ2.keys()):
        value1 = environ1.get(key)
        value2 = environ2.get(key)

        if value1 is not None and value2 is not None:
            if "${{{}}}".format(key) not in value2:
                logger.warning(
                    "The '{key}' variable is being overridden in "
                    "definition '{identifier}' [{version}]".format(
                        key=key,
                        identifier=definition1.identifier,
                        version=definition1.version
                    )
                )

            environ[key] = re.sub(
                "\${(\w+)}",
                lambda match: environ1.get(match.group(1)) or match.group(0),
                str(value2)
            )

        else:
            environ[key] = str(value1 or value2)

    return environ


def initial_environment(environ_mapping=None):
    """Return the initial environment to augment.

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
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
        ])
    }

    if environ_mapping is not None:
        environ.update(**environ_mapping)

    return environ
