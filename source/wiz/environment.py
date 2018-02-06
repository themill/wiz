# :coding: utf-8

import os
import re
import copy

import mlog

import wiz.graph
import wiz.symbol
import wiz.exception


def generate_identifier(environment):
    """Generate a unique identifier for *environment*.

    environment must be an :class:`Environment` instance.

    """
    variant_name = environment.get("variant_name")
    if variant_name is not None:
        variant_name = "[{}]".format(variant_name)

    return "{environment}{variant}=={version}".format(
        environment=environment.identifier,
        version=environment.version,
        variant=variant_name or ""
    )


def get(requirement, environment_mapping, divide_variants=True):
    """Get best matching environment version for *requirement*.

    The best matching :class:`~wiz.definition.Environment` version instances
    corresponding to the *requirement* will be returned.

    If this environment contains variants, the ordered list of environment
    combined with each variant will be returned. If one variant is explicitly
    requested, only the corresponding variant combined with the required
    environment will be returned. Otherwise, the required environment will be
    returned

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *environment_mapping* is a mapping regrouping all available environment
    associated with their unique identifier.

    *divide_variants* indicate whether variants should be divided into separate
    environment. Default is true.

    :exc:`wiz.exception.RequestNotFound` is raised if the
    requirement can not be resolved.

    """
    if requirement.name not in environment_mapping:
        raise wiz.exception.RequestNotFound(requirement)

    environment = None

    # Sort the environments so that the highest version is first.
    sorted_environments = sorted(
        environment_mapping[requirement.name], key=lambda _env: _env.version,
        reverse=True
    )

    # Get the best matching environment.
    for _environment in sorted_environments:
        if _environment.version in requirement.specifier:
            environment = _environment
            break

    if environment is None:
        raise wiz.exception.RequestNotFound(requirement)

    # Extract variants from environment if available.
    variants = environment.get("variant", [])

    # Simply return the main environment if no variants is available.
    if len(variants) == 0 or not divide_variants:
        return [environment]

    # Extract and return the requested variant if necessary.
    elif len(requirement.extras) > 0:
        variant_identifier = next(iter(requirement.extras))
        variant_mapping = reduce(
            lambda res, mapping: dict(res, **{mapping["identifier"]: mapping}),
            variants, {}
        )

        if variant_identifier not in variant_mapping.keys():
            raise wiz.exception.RequestNotFound(
                "The variant '{}' could not been resolved for '{}'.".format(
                    variant_identifier, requirement.name
                )
            )

        return [
            _combine_variant(environment, variant_mapping[variant_identifier])
        ]

    # Otherwise, extract and return all possible variants.
    else:
        return map(
            lambda variant: _combine_variant(environment, variant), variants
        )


def resolve(requirements, environment_mapping):
    """Return resolved environment from *requirements*.

    The returned :class:`~wiz.definition.Environment` list should be ordered
    from the least important to the most important.

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


def combine(environments, data_mapping=None):
    """Return combined mapping extracted from *environments*.

    A mapping should look as follow::

        >>> combine(environments)
        {
            "command": {
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
    def _combine(environment1, environment2):
        """Return intermediate environment combining both extracted results."""
        _command = dict(
            environment1.get("command", {}),
            **environment2.get("command", {})
        )
        _environ = _combine_data_mapping(environment1, environment2)

        environment2["command"] = _command
        environment2["data"] = _environ
        return environment2

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

    if data_mapping is not None:
        environ.update(**data_mapping)

    return environ


def _combine_variant(environment, variant_mapping):
    """Return combined environment from *environment* and *variant_mapping*

    *environment* must be a valid :class:`Environment` instance.

    *variant_mapping* must be a valid variant mapping which should have at least
    an 'identifier' keyword.

    In case of conflicted elements in both mappings, the elements from the
    *variant_mapping* will have priority over elements from *environment*.

    The 'identifier' keyword from *variant_mapping* will be set as a
    'variant' keyword of the combined environment.

    """
    env = copy.deepcopy(environment)
    env["variant_name"] = variant_mapping.get("identifier")
    env["system"] = _combine_system_mapping(environment, variant_mapping)
    env["command"] = _combine_command_mapping(environment, variant_mapping)
    env["data"] = _combine_data_mapping(environment, variant_mapping)
    env["requirement"] = (
        environment.get("requirement", []) +
        variant_mapping.get("requirement", [])
    )
    del env["variant"]
    return env


def _combine_command_mapping(environment1, environment2):
    """Return combined command mapping from *environment1* and *environment2*.

    *environment1* and *environment2* must be valid :class:`Environment`
    instances.

    If a key exists in both "command" mappings, the value from
    *environment2* will have priority over elements from *environment1*.::

        >>> _combine_system_mapping(
        ...     wiz.definition.Environment({"command": {"app": "App1.1 --run"})
        ...     wiz.definition.Environment({"command": {"app": "App2.1"}})
        ... )

        {"app": "App2.1"}

    """
    logger = mlog.Logger(__name__ + "._combine_command_mapping")

    mapping = {}

    mapping1 = environment1.get("command", {})
    mapping2 = environment2.get("command", {})

    for command in set(mapping1.keys() + mapping2.keys()):
        value1 = mapping1.get(command)
        value2 = mapping2.get(command)

        if value1 is not None and value2 is not None:
            logger.warning(
                "The '{key}' command is being overridden in "
                "environment '{identifier}' [{version}]".format(
                    key=command,
                    identifier=environment2.identifier,
                    version=environment2.version
                )
            )
            mapping[command] = str(value2)

        else:
            mapping[command] = str(value1 or value2)

    return mapping


def _combine_system_mapping(environment1, environment2):
    """Return combined system mapping from *environment1* and *environment2*.

    *environment1* and *environment2* must be valid :class:`Environment`
    instances.

    If a key exists in both "system" mappings, the value from
    *environment2* will have priority over elements from *environment1*.::

        >>> _combine_system_mapping(
        ...     wiz.definition.Environment({
        ...         "system": {"platform": "linux", "arch": "x86_64"}
        ...     }),
        ...     wiz.definition.Environment({"system": {"platform": "macOS"}})
        ... )

        {"platform": "macOS", "arch": "x86_64"}

    """
    logger = mlog.Logger(__name__ + "._combine_system_mapping")

    mapping = {}

    mapping1 = environment1.get("system", {})
    mapping2 = environment2.get("system", {})

    for key in set(mapping1.keys() + mapping2.keys()):
        value1 = mapping1.get(key)
        value2 = mapping2.get(key)

        if value1 is not None and value2 is not None:
            logger.warning(
                "The '{key}' system is being overridden in "
                "environment '{identifier}' [{version}]".format(
                    key=key,
                    identifier=environment2.identifier,
                    version=environment2.version
                )
            )
            mapping[key] = str(value2)

        else:
            mapping[key] = str(value1 or value2)

    return mapping


def _combine_data_mapping(environment1, environment2):
    """Return combined data mapping from *environment1* and *environment2*.

    *environment1* and *environment2* must be valid :class:`Environment`
    instances.

    Each variable name from both environment's "data" mappings will be
    gathered so that a final value can be set. If the a variable is only
    contained in one of the "data" mapping, its value will be kept in the
    combined environment.

    If the variable exists in both "data" mappings, the value from
    *environment2* must reference the variable name for the value from
    *environment1* to be included in the combined environment::

        >>> _combine_data_mapping(
        ...     wiz.definition.Environment({"data": {"key": "value2"})
        ...     wiz.definition.Environment({"data": {"key": "value1:${key}"}})
        ... )

        {"key": "value1:value2"}

    Otherwise the value from *environment2* will override the value from
    *environment1*::

        >>> _combine_data_mapping(
        ...     wiz.definition.Environment({"data": {"key": "value2"})
        ...     wiz.definition.Environment({"data": {"key": "value1"}})
        ... )

        {"key": "value1"}

    If other variables from *environment1* are referenced in the value fetched
    from *environment2*, they will be replaced as well::

        >>> _combine_data_mapping(
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

        >>> _combine_data_mapping(
        ...    "PLUGIN_PATH",
        ...    {"PLUGIN_PATH": "${HOME}/.app:${PLUGIN_PATH}"},
        ...    {"PLUGIN_PATH": "/path/to/settings", "HOME": "/usr/people/me"}
        ... )

        {
            "HOME": "/usr/people/me",
            "PLUGIN_PATH": "/usr/people/me/.app:/path/to/settings"
        }

    .. warning::

        This process will stringify all variable values.

    """
    logger = mlog.Logger(__name__ + "._combine_data_mapping")

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
                    "environment '{identifier}' [{version}]".format(
                        key=key,
                        identifier=environment2.identifier,
                        version=environment2.version
                    )
                )

            mapping[key] = re.sub(
                "\${(\w+)}", lambda m: mapping1.get(m.group(1)) or m.group(0),
                str(value2)
            )

    return mapping
