# :coding: utf-8

import os
import re

import mlog

from wiz import __version__
import wiz.graph
import wiz.symbol
import wiz.exception


def get(requirement, environment_mapping):
    """Get best matching environment version for *requirement*.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *environment_mapping* is a mapping regrouping all available environment
    associated with their unique identifier.

    :exc:`wiz.exception.RequestNotFound` is raised if the
    requirement can not be resolved.

    """
    if requirement.name not in environment_mapping:
        raise wiz.exception.RequestNotFound(requirement)

    environment = None

    # Sort the environment versions so that the highest one is first.
    versions = sorted(
        environment_mapping[requirement.name].keys(), reverse=True
    )

    # Get the best matching environment.
    for version in versions:
        _environment = environment_mapping[requirement.name][version]
        if _environment.version in requirement.specifier:
            environment = _environment
            break

    if environment is None:
        raise wiz.exception.RequestNotFound(requirement)

    return environment


def resolve(requirements, environment_mapping):
    """Return resolved environments from *requirements*.

    The returned :class:`~wiz.definition.Environment` instances list should be
    ordered from the least important to the most important.

    *requirements* should be a list of
    class:`packaging.requirements.Requirement` instances.

    *environment_mapping* is a mapping regrouping all available environments
    associated with their unique identifier.

    Raise :exc:`wiz.exception.GraphResolutionError` if the graph cannot be
    resolved.

    """
    logger = mlog.Logger(__name__ + ".resolve")
    logger.info(
        "Resolve environment: {}".format(
            ", ".join([str(requirement) for requirement in requirements])
        )
    )
    resolver = wiz.graph.Resolver(environment_mapping)
    return resolver.compute_environments(requirements)


def extract_context(environments, data_mapping=None):
    """Return combined mapping extracted from *environments*.

    A context mapping should look as follow::

        >>> extract_context(environments)
        {
            "alias": {
                "app": "AppExe"
                ...
            },
            "data": {
                "KEY1": "value1",
                "KEY2": "value2",
                ...
            }
        }

    *environments* should be a list of :class:`Environment` instances. it should
    be ordered from the less important to the most important so that the later
    are prioritized over the first.

    *data_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    def _combine(mapping1, mapping2):
        """Return intermediate context combining both extracted results."""
        _alias = combine_alias(mapping1, mapping2)
        _data = combine_data(mapping1, mapping2)
        return dict(alias=_alias, data=_data)

    mapping = reduce(_combine, environments, dict(data=data_mapping or {}))

    # Clean up any possible reference to the same variable key for each value
    # (e.g. {"PATH": "/path/to/somewhere:${PATH}") and resolve any missing
    # references from within data mapping.
    for key, value in mapping["data"].items():
        _value = re.sub(
            "(\${{{0}}}:?|:?\${{{0}}})".format(key), lambda m: "", value
        )
        _value = re.sub(
            "\${(\w+)}",
            lambda m: mapping["data"].get(m.group(1)) or m.group(0), _value
        )
        mapping["data"][key] = _value

    return mapping


def combine_data(environment1, environment2):
    """Return combined data mapping from *environment1* and *environment2*.

    *environment1* and *environment2* must be valid :class:`Environment`
    instances.

    Each variable name from both environment's "data" mappings will be
    gathered so that a final value can be set. If a variable is only
    contained in one of the "data" mapping, its value will be kept in the
    combined environment.

    If the variable exists in both "data" mappings, the value from
    *environment2* must reference the variable name for the value from
    *environment1* to be included in the combined environment::

        >>> combine_data(
        ...     wiz.definition.Environment({"data": {"key": "value2"})
        ...     wiz.definition.Environment({"data": {"key": "value1:${key}"}})
        ... )

        {"key": "value1:value2"}

    Otherwise the value from *environment2* will override the value from
    *environment1*::

        >>> combine_data(
        ...     wiz.definition.Environment({"data": {"key": "value2"})
        ...     wiz.definition.Environment({"data": {"key": "value1"}})
        ... )

        {"key": "value1"}

    If other variables from *environment1* are referenced in the value fetched
    from *environment2*, they will be replaced as well::

        >>> combine_data(
        ...     wiz.definition.Environment({
        ...         "data": {
        ...             "PLUGIN_PATH": "/path/to/settings",
        ...             "HOME": "/usr/people/me"
        ...        }
        ...     }),
        ...     wiz.definition.Environment({
        ...         "data": {
        ...             "PLUGIN_PATH": "${HOME}/.app:${PLUGIN_PATH}"
        ...         }
        ...     })
        ... )

        {
            "HOME": "/usr/people/me",
            "PLUGIN_PATH": "/usr/people/me/.app:/path/to/settings"
        }

    .. warning::

        This process will stringify all variable values.

    """
    logger = mlog.Logger(__name__ + ".combine_data")

    mapping = {}

    mapping1 = environment1.get("data", {})
    mapping2 = environment2.get("data", {})

    for key in set(mapping1.keys() + mapping2.keys()):
        value1 = mapping1.get(key)
        value2 = mapping2.get(key)

        if value2 is None:
            mapping[key] = str(value1)

        else:
            if value1 is not None and "${{{}}}".format(key) not in value2:
                logger.warning(
                    "The '{key}' variable is being overridden in "
                    "environment {environment}".format(
                        key=key, environment=environment2
                    )
                )

            mapping[key] = re.sub(
                "\${(\w+)}", lambda m: mapping1.get(m.group(1)) or m.group(0),
                str(value2)
            )

    return mapping


def combine_alias(environment1, environment2):
    """Return combined command mapping from *environment1* and *environment2*.

    *environment1* and *environment2* must be valid :class:`Environment`
    instances.

    If a key exists in both "command" mappings, the value from
    *environment2* will have priority over elements from *environment1*.::

        >>> combine_alias(
        ...     wiz.definition.Environment({"alias": {"app": "App1.1 --run"})
        ...     wiz.definition.Environment({"alias": {"app": "App2.1"}})
        ... )

        {"app": "App2.1"}

    """
    logger = mlog.Logger(__name__ + ".extract_alias")

    mapping = {}

    mapping1 = environment1.get("alias", {})
    mapping2 = environment2.get("alias", {})

    for command in set(mapping1.keys() + mapping2.keys()):
        value1 = mapping1.get(command)
        value2 = mapping2.get(command)

        if value1 is not None and value2 is not None:
            logger.warning(
                "The '{key}' alias is being overridden in "
                "environment {environment}".format(
                    key=command, environment=environment2
                )
            )
            mapping[command] = str(value2)

        else:
            mapping[command] = str(value1 or value2)

    return mapping


def initiate_data(data_mapping=None):
    """Return the initiate environment data to augment.

    The initial environment contains basic variables from the external
    environment that can be used by the resolved environment, such as
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
        "WIZ_VERSION": __version__,
        "USER": os.environ.get("USER"),
        "LOGNAME": os.environ.get("LOGNAME"),
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

    if data_mapping is not None:
        environ.update(**data_mapping)

    return environ
