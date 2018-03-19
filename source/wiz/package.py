# :coding: utf-8

import collections
import re
import os

import mlog

from wiz import __version__
import wiz.definition
import wiz.exception


def extract(requirement, definition_mapping):
    """Extract list of :class:`Package` instances from *requirement*.

    The best matching :class:`~wiz.definition.Definition` version instances
    corresponding to the *requirement* will be used.

    If this definition contains variants, a :class:`Package` instance will be
    returned for each combined variant.

    *requirement* is an instance of :class:`packaging.requirements.Requirement`.

    *definition_mapping* is a mapping regrouping all available definitions
    associated with their unique identifier.

    """
    definition = wiz.definition.query(requirement, definition_mapping)

    # Extract variants from definition if available.
    variants = definition.variants

    # Extract and return the requested variant if necessary.
    if len(requirement.extras) > 0:
        variant_identifier = next(iter(requirement.extras))
        variant_mapping = reduce(
            lambda res, mapping: dict(res, **{mapping["identifier"]: mapping}),
            variants, {}
        )

        if variant_identifier not in variant_mapping.keys():
            raise wiz.exception.RequestNotFound(
                "The variant '{variant}' could not been resolved for "
                "'{definition}' [{version}].".format(
                    variant=variant_identifier,
                    definition=definition.identifier,
                    version=definition.version
                )
            )

        return [Package(definition, variant_mapping[variant_identifier])]

    # Simply return the package corresponding to the main definition if no
    # variants are available.
    elif len(variants) == 0:
        return [Package(definition)]

    # Otherwise, extract and return all possible variants.
    else:
        return map(lambda variant: Package(definition, variant), variants)


def extract_context(packages, environ_mapping=None):
    """Return combined mapping extracted from *packages*.

    A context mapping should look as follow::

        >>> extract_context(packages)
        {
            "command": {
                "app": "AppExe"
                ...
            },
            "environ": {
                "KEY1": "value1",
                "KEY2": "value2",
                ...
            },
        }

    *packages* should be a list of :class:`Package` instances. it should be
    ordered from the less important to the most important so that the later are
    prioritized over the first.

    *environ_mapping* can be a mapping of environment variables which would
    be augmented.

    """
    def _combine(mapping1, mapping2):
        """Return intermediate context combining both extracted results."""
        identifier = mapping2.get("identifier", "unknown")
        _environ = combine_environ_mapping(
            identifier, mapping1.get("environ", {}), mapping2.get("environ", {})
        )
        _command = combine_command_mapping(
            identifier, mapping1.get("command", {}), mapping2.get("command", {})
        )
        return dict(command=_command, environ=_environ)

    mapping = reduce(_combine, packages, dict(environ=environ_mapping or {}))
    mapping["environ"] = sanitise_environ_mapping(mapping.get("environ", {}))
    return mapping


def combine_environ_mapping(package_identifier, mapping1, mapping2):
    """Return combined environ mapping from *mapping1* and *mapping2*.

    *package_identifier* must be the identifier of the combined package. It will
    be used to indicate whether any variable is overridden in the combination
    process.

    *mapping1* and *mapping2* must be mappings of environment variables.

    Each variable name from both mappings will be combined into a final value.
    If a variable is only contained in one of the mapping, its value will be
    kept in the combined mapping.

    If the variable exists in both mappings, the value from *mapping2* must
    reference the variable name for the value from *mapping1* to be included
    in the combined mapping::

        >>> combine_environ_mapping(
        ...     "combined_package",
        ...     {"key": "value2"},
        ...     {"key": "value1:${key}"}
        ... )

        {"key": "value1:value2"}

    Otherwise the value from *mapping2* will override the value from
    *mapping1*::

        >>> combine_environ_mapping(
        ...     "combined_package",
        ...     {"key": "value2"},
        ...     {"key": "value1"}
        ... )

        warning: The 'key' variable is being overridden in 'combined_package'.
        {"key": "value1"}

    If other variables from *mapping1* are referenced in the value fetched
    from *mapping2*, they will be replaced as well::

        >>> combine_environ_mapping(
        ...     "combined_package",
        ...     {"PLUGIN": "/path/to/settings", "HOME": "/usr/people/me"},
        ...     {"PLUGIN": "${HOME}/.app:${PLUGIN}"}
        ... )

        {
            "HOME": "/usr/people/me",
            "PLUGIN": "/usr/people/me/.app:/path/to/settings"
        }

    .. warning::

        This process will stringify all variable values.

    """
    logger = mlog.Logger(__name__ + ".combine_environ_mapping")

    mapping = {}

    for key in set(mapping1.keys() + mapping2.keys()):
        value1 = mapping1.get(key)
        value2 = mapping2.get(key)

        if value2 is None:
            mapping[key] = str(value1)

        else:
            if value1 is not None and "${{{}}}".format(key) not in value2:
                logger.warning(
                    "The '{key}' variable is being overridden "
                    "in '{identifier}'".format(
                        key=key, identifier=package_identifier
                    )
                )

            mapping[key] = re.sub(
                "\${(\w+)}", lambda m: mapping1.get(m.group(1)) or m.group(0),
                str(value2)
            )

    return mapping


def combine_command_mapping(package_identifier, mapping1, mapping2):
    """Return combined command mapping from *package1* and *package2*.

    *package_identifier* must be the identifier of the combined package. It will
    be used to indicate whether any variable is overridden in the combination
    process.

    *mapping1* and *mapping2* must be mappings of commands.

    If the command exists in both mappings, the value from *mapping2* will have
    priority over elements from *mapping1*::

        >>> combine_command_mapping(
        ...     "combined_package",
        ...     {"app": "App1.1 --run"},
        ...     {"app": "App2.1"}
        ... )

        {"app": "App2.1"}

    """
    logger = mlog.Logger(__name__ + ".combine_command_mapping")

    mapping = {}

    for command in set(mapping1.keys() + mapping2.keys()):
        value1 = mapping1.get(command)
        value2 = mapping2.get(command)

        if value1 is not None and value2 is not None:
            logger.warning(
                "The '{key}' command is being overridden "
                "in '{identifier}'".format(
                    key=command, identifier=package_identifier
                )
            )
            mapping[command] = str(value2)

        else:
            mapping[command] = str(value1 or value2)

    return mapping


def sanitise_environ_mapping(mapping):
    """Return sanitised environment *mapping*.

    Resolve all key references within *mapping* values and remove all
    self-references::

        >>> sanitise_environ_mapping(
        ...     "PLUGIN": "${HOME}/.app:/path/to/somewhere:${PLUGIN}",
        ...     "HOME": "/usr/people/me"
        ... )

        {
            "HOME": "/usr/people/me",
            "PLUGIN": "/usr/people/me/.app:/path/to/somewhere"
        }

    """
    _mapping = {}

    for key, value in mapping.items():
        _value = re.sub(
            "(\${{{0}}}:?|:?\${{{0}}})".format(key), lambda m: "", value
        )
        _value = re.sub(
            "\${(\w+)}", lambda m: mapping.get(m.group(1)) or m.group(0), _value
        )
        _mapping[key] = _value

    return _mapping


def initiate_environ(mapping=None):
    """Return the minimal environment mapping to augment.

    The initial environment mapping contains basic variables from the external
    environment that can be used by the resolved environment, such as
    the *USER* or the *HOME* variables.

    The other variable added are:

    * DISPLAY:
        This variable is necessary to open user interface within the current
        X display name.

    * PATH:
        This variable is initialised with default values to have access to the
        basic UNIX commands.

    *mapping* can be a custom environment mapping which will be added to the
    initial environment.

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

    if mapping is not None:
        environ.update(**mapping)

    return environ


class Package(collections.Mapping):
    """Package object."""

    def __init__(self, definition, variant=None):
        """Initialise Package from *definition*.

        *definition* must be a valid :class:`~wiz.definition.Definition`
        instance.

        *variant* could be a valid variant mapping which should have at least
        an 'identifier' keyword.

        .. note::

            In case of conflicted elements in 'data' or 'command' elements,
            the elements from the *variant* will have priority.

        """
        mapping = definition.to_mapping()
        self._mapping = dict(
            (k, v) for k, v in mapping.items() if k != "variants"
        )

        self._requirements = definition.requirements[:]
        self._version = definition.version

        identifier = "{definition}=={version}".format(
            definition=definition.identifier,
            version=definition.version,
        )

        variant_name = None

        if variant is not None:
            identifier = "{definition}[{variant}]=={version}".format(
                definition=definition.identifier,
                variant=variant.identifier,
                version=definition.version,
            )

            variant_name = variant.identifier

            self._mapping["environ"] = combine_environ_mapping(
                identifier, definition.environ, variant.environ
            )

            self._mapping["command"] = combine_command_mapping(
                identifier, definition.command, variant.command
            )

            if len(variant.get("requirements", [])) > 0:
                self._mapping.setdefault("requirements", [])
                self._mapping["requirements"] += variant.get("requirements", [])
                self._requirements += variant.requirements

        self._mapping["identifier"] = identifier
        self._mapping["definition"] = definition
        self._mapping["variant_name"] = variant_name

    @property
    def identifier(self):
        """Return identifier."""
        return self.get("identifier")

    @property
    def definition(self):
        """Return definition identifier."""
        return self.get("definition")

    @property
    def variant_name(self):
        """Return variant name."""
        return self.get("variant_name")

    @property
    def description(self):
        """Return name."""
        return self.get("description", "unknown")

    @property
    def version(self):
        """Return version."""
        return self._version

    @property
    def command(self):
        """Return command mapping."""
        return self.get("command", {})

    @property
    def environ(self):
        """Return environ mapping."""
        return self.get("environ", {})

    @property
    def requirements(self):
        """Return requirement list."""
        return self._requirements

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
