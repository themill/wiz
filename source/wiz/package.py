# :coding: utf-8

import collections
import re

import mlog

import wiz.environment
import wiz.graph
import wiz.exception


def generate_identifier(environment, variant_name=None):
    """Generate a unique identifier for *environment*.

    *environment* must be an :class:`~wiz.definition.Environment` instance.

    *variant_name* could be the identifier of a variant mapping.

    """
    if variant_name is not None:
        variant_name = "[{}]".format(variant_name)

    return "{environment}{variant}=={version}".format(
        environment=environment.identifier,
        version=environment.version,
        variant=variant_name or ""
    )


def resolve(requirements, environment_mapping):
    """Return resolved packages from *requirements*.

    The returned :class:`~wiz.package.Package` instances list should be
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


def extract(requirement, environment_mapping):
    """Extract list of :class:`Package` instances from *requirement*.

    The best matching :class:`~wiz.definition.Environment` version instances
    corresponding to the *requirement* will be used.

    If this environment contains variants, a :class:`Package` instance will be
    returned for each combined variant.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *environment_mapping* is a mapping regrouping all available environment
    associated with their unique identifier.

    """
    environment = wiz.environment.get(requirement, environment_mapping)

    # Extract variants from environment if available.
    variants = environment.variant

    # Extract and return the requested variant if necessary.
    if len(requirement.extras) > 0:
        variant_identifier = next(iter(requirement.extras))
        variant_mapping = reduce(
            lambda res, mapping: dict(res, **{mapping["identifier"]: mapping}),
            variants, {}
        )

        if variant_identifier not in variant_mapping.keys():
            raise wiz.exception.RequestNotFound(
                "The variant '{}' could not been resolved for {}.".format(
                    variant_identifier, environment
                )
            )

        return [Package(environment, variant_mapping[variant_identifier])]

    # Simply return the main environment if no variants is available.
    elif len(variants) == 0:
        return [Package(environment)]

    # Otherwise, extract and return all possible variants.
    else:
        return map(lambda variant: Package(environment, variant), variants)


def extract_context(packages, data_mapping=None):
    """Return combined mapping extracted from *environments*.

    A context mapping should look as follow::

        >>> extract_context(packages)
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

    *packages* should be a list of :class:`wiz.package.Package` instances. it
    should be ordered from the less important to the most important so that the
    later are prioritized over the first.

    *data_mapping* can be a mapping of environment variables which would
    be augmented by the resolved environment.

    """
    def _combine(mapping1, mapping2):
        """Return intermediate context combining both extracted results."""
        _alias = combine_alias(mapping1, mapping2)
        _data = combine_data(mapping1, mapping2)
        return dict(alias=_alias, data=_data)

    mapping = reduce(_combine, packages, dict(data=data_mapping or {}))

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


class Package(collections.Mapping):
    """Package object."""

    def __init__(self, environment, variant=None):
        """Initialise Package from *environment*.

        *environment* must be a valid :class:`wiz.definition.Environment`
        instance.

        *variant* could be a valid variant mapping which should have at least
        an 'identifier' keyword.

        In case of conflicted elements in both mappings, the elements from the
        *variant* will have priority over elements from *environment*.

        """
        self._mapping = dict()

        variant_mapping = {}

        if variant is not None:
            variant_mapping = {
                "identifier": variant.identifier,
                "data": combine_data(environment, variant),
                "alias": combine_alias(environment, variant),
                "requirement": (
                    environment.requirement + variant.requirement
                )
            }

        self._mapping = {
            "identifier": generate_identifier(
                environment, variant_name=variant_mapping.get("identifier")
            ),
            "environment": environment.identifier,
            "description": environment.description,
            "alias": variant_mapping.get("alias") or environment.alias,
            "data": variant_mapping.get("data") or environment.data,
            "requirement": (
                variant_mapping.get("requirement") or environment.requirement
            ),
        }

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def environment(self):
        """Return environment identifier."""
        return self.get("environment")

    @property
    def description(self):
        """Return name."""
        return self.get("description", "unknown")

    @property
    def alias(self):
        """Return alias mapping."""
        return self.get("alias", {})

    @property
    def data(self):
        """Return data mapping."""
        return self.get("data", {})

    @property
    def requirement(self):
        """Return requirement list."""
        return self.get("requirement", [])

    def __str__(self):
        """Return string representation."""
        return "'{}'".format(self.identifier)

    def __getitem__(self, key):
        """Return value for *key*."""
        return self._mapping[key]

    def __iter__(self):
        """Iterate over all keys."""
        for key in self._mapping:
            yield key

    def __len__(self):
        """Return count of keys."""
        return len(self._mapping)
